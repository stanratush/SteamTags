"""The app's callbacks. The server is stateless: every settings change recomputes the whole Network State
from the loaded dataset; the browser holds only plain data in dcc.Store components. The only memory is a
small memo of recent layouts (`LAYOUTS`), a pure function of the inputs it is keyed by.

Functions are module-level so background jobs (Removal Sensitivity) can import them in a spawned process.

The Interface Language (the `lang` store) is a view choice. Callbacks that render text take `lang` as an Input, so a
switch re-renders them; callbacks that compute (a Network State, a layout, a job) take it only as State, so a switch
never recomputes anything. Static labels are relabelled by `relabel`, from the layout's registry.
"""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from collections import Counter, OrderedDict
from typing import Any

import dash
import networkx as nx
from dash import ALL, ClientsideFunction, Input, Output, Patch, State, ctx, html, no_update, set_props
from dash.exceptions import PreventUpdate

from steamstudy.app import help as H
from steamstudy.app import app_cache, ps_run, rs_cache
from steamstudy.app import ps_view as PV
from steamstudy.app import view as V
from steamstudy.app.export import REFUSALS, BuildNotFound, OpenRefused, export_zip, open_export
from steamstudy.app.guide import PANEL_SECTIONS, help_markdown_at
from steamstudy.app.layout import (GRIDS, PILLS, RELABEL, SLIDERS, block_styles, grid_options, message_value,
                                   root_class)
from steamstudy.app.layout import defining_options as layout_defining_options
from steamstudy.app.loader import BuildContext, load_build
from steamstudy.app import renderer as R
from steamstudy.app.renderer import cluster_color
from steamstudy.network.cluster import Cluster
from steamstudy.network.graph import filter_games
from steamstudy.network.layout import (REFERENCE_CANVAS, Canvas, Layout, LayoutInput, lay_out, label_width,
                                      layout_input, restore, tidy)
from steamstudy.network import selection as SEL
from steamstudy.network.model import Settings, resolution_text
from steamstudy.network.sensitivity import removal_sensitivity
from steamstudy.network.stability import ari
from steamstudy.network.state import compute_state
from steamstudy.network.tables import cluster_games, state_tables
from steamstudy.i18n import lang_of, text
from steamstudy.versions import version_mismatches

BLOCKS = ["blk-dataset", "blk-filters", "blk-graph", "blk-tabs", "blk-quality", "blk-clusters", "blk-rs",
          "blk-nodes", "blk-edges", "blk-export"]
CONTROL_IDS = ["dataset", "min-games", "min-shared", "min-months", "genre-hidden", "defining-hidden", "weight",
               "algorithm", "gamma", "seed"]


# ----------------------------------------------------------------------------- settings


def settings_from_controls(c: BuildContext, dataset: str, min_games: int, min_shared: int, min_months: int,
                           genre_hidden: list[int], defining_hidden: list[int], weight: str, algorithm: str,
                           gamma: float, seed: int, removed: list[int]) -> Settings:
    defining = c.dataset(dataset).defining_tag
    hidden = set(int(t) for t in genre_hidden or [])
    if defining is not None and defining_hidden:
        hidden.add(defining.id)
    return Settings(build_id=c.build_id, dataset=dataset, min_months=int(min_months),
                    min_games_per_tag=int(min_games), min_shared_games=int(min_shared),
                    hidden_tag_ids=tuple(sorted(hidden)), removed_tag_ids=tuple(sorted(int(t) for t in removed or [])),
                    clustering_weight=weight, algorithm=algorithm, resolution=float(gamma), seed=int(seed),
                    null_replicates=c.network.null_replicates, noise_seeds=c.network.noise_seeds)


def controls_from_settings(c: BuildContext, s: Settings) -> dict[str, Any]:
    genre_ids = {t.id for t in c.genre_tags}
    defining = c.dataset(s.dataset).defining_tag
    return {"dataset": s.dataset, "min-games": s.min_games_per_tag, "min-shared": s.min_shared_games,
            "min-months": s.min_months, "genre-hidden": [t for t in s.hidden_tag_ids if t in genre_ids],
            "defining-hidden": [1] if defining is not None and defining.id in s.hidden_tag_ids else [],
            "weight": s.clustering_weight, "algorithm": s.algorithm, "gamma": s.resolution, "seed": s.seed,
            "removed": list(s.removed_tag_ids)}


def _valid_gamma(gamma: Any) -> bool:
    try:
        value = float(gamma)
    except (TypeError, ValueError):
        return False
    return value >= 0.01  # two decimals, no maximum (the Workbench γ of Parameter Selection)


# ----------------------------------------------------------------------------- 1. dataset change


def on_dataset(dataset: str, build_path: str, pending: dict | None):
    c = load_build(build_path)
    defining = c.dataset(dataset).defining_tag
    if pending and pending.get("dataset") == dataset:
        return pending["defining-hidden"], pending["removed"]
    hidden = c.default_settings(dataset).hidden_tag_ids
    return ([1] if defining is not None and defining.id in hidden else []), []


def defining_options(dataset: str, lang: str | None, build_path: str):
    """The defining-tag checkbox's label, for the dataset and the Interface Language (never its value)."""
    return layout_defining_options(load_build(build_path).dataset(dataset).defining_tag, text(lang_of(lang)))


# ----------------------------------------------------------------------------- 2. recompute


def browser_tables(tables: dict[str, Any]) -> dict[str, Any]:
    """The state's tables as the browser holds them (no AppID lists)."""
    return {"nodes": tables["nodes.csv"], "clusters": tables["clusters.csv"], "quality": tables["cluster_quality.csv"][0],
            "edges": [{k: v for k, v in r.items() if k != "appids"} for r in tables["edges.csv"]],
            "connections": tables["cluster_connections.csv"], "null": tables["null_model.csv"],
            "seed": tables["seed_noise.csv"], "nin": tables["not_in_network.csv"]}


# The tables of recent states by state_id, so a selection's request only names its state. A pure function of the
# state key: a missing entry (a restarted server) is recomputed.
_MEMO_LOCK = threading.Lock()  # guards STATE_TABLES and LAYOUTS (Dash may answer callbacks in threads)
STATE_TABLES: OrderedDict[str, dict[str, Any]] = OrderedDict()
STATE_TABLES_KEPT = 4


def remember_tables(state_id: str, tables: dict[str, Any]) -> None:
    with _MEMO_LOCK:
        STATE_TABLES[state_id] = tables
        STATE_TABLES.move_to_end(state_id)
        while len(STATE_TABLES) > STATE_TABLES_KEPT:
            STATE_TABLES.popitem(last=False)


def tables_of(meta: dict[str, Any], build_path: str) -> dict[str, Any]:
    with _MEMO_LOCK:
        known = STATE_TABLES.get(meta["state_id"])
    if known is not None:
        return known
    c = load_build(build_path)
    settings = Settings.from_key(meta["key"])
    state = compute_state(c.games(settings.dataset), settings, c.context(settings.dataset))
    tables = browser_tables(state_tables(state))
    remember_tables(state.state_id, tables)
    return tables


def applied_line(verify, key, cluster_of, tx):
    """Apply to Workbench's provenance line: checked once, on the first recompute at the applied key, against the
    stored Selected Partition; kept while the key stays, gone as soon as a setting changes. Display only."""
    if verify.get("applied"):
        applied = verify["applied"]
        if key != applied["key"]:
            return no_update, no_update  # the controls are still being set
        stored = dict(zip(applied["nodes"], applied["membership"]))
        same_nodes = set(stored) == set(cluster_of)
        nodes = sorted(stored) if same_nodes else []
        value = ari(nodes, {t: str(stored[t]) for t in nodes}, cluster_of) if same_nodes else 0.0
        reproduced = same_nodes and value == 1.0
        where = {"dataset": applied["dataset"], "g": applied["g"], "s": applied["s"]}
        line = (tx("Applied from Parameter Selection: {dataset}, g={g}, s={s} — Selected Partition reproduced ✓",
                   **where) if reproduced else
                tx("Applied from Parameter Selection: {dataset}, g={g}, s={s} — shows a different partition from the "
                   "Selected Partition: ARI {ari}", **where, ari=tx.fixed(value, ".2f")))
        record = {k: applied[k] for k in ("dataset", "g", "s", "grid_key_hash", "method_version", "workbench_gamma",
                                          "workbench_seed")}
        record.update({"reproduced": reproduced, "ari": None if reproduced else value})
        return line, {"applied_key": applied["key"], "applied_from": record, "text": line}
    if key != verify["applied_key"]:
        return "", None
    return no_update, no_update


def state_views(c: BuildContext, meta: dict[str, Any], tables: dict[str, Any], tx) -> dict[str, Any]:
    """The text a Network State shows, by output id, from its meta and its browser tables: rendered by `recompute`,
    and again by `state_text` when the Interface Language is switched (no recompute)."""
    settings = Settings.from_key(meta["key"])
    dataset, q, gamma_text = settings.dataset, tables["quality"], meta["gamma"]
    names = {int(t): name for t, name in meta["names"].items()}
    legend: list[Any] = [html.Span(tx("Key"), className="lkey term", tabIndex="0", **H.attrs("legend.key", tx))] + [
        html.Button([html.Span(className="sw", style={"background": cluster_color(r["cluster"], r["kind"])}),
                     f"{r['cluster']} · {r['size']}"], id={"type": "legend", "cluster": r["cluster"]}, className="lchip",
                    title=tx("Select this cluster"))
        for r in tables["clusters"] if r["kind"] == "multi_tag"]
    n_one = sum(r["kind"] == "one_tag" for r in tables["clusters"])
    if n_one:
        legend.append(html.Span([html.Span(className="sw", style={"background": R.ONE_TAG_COLOR}),
                                 tx.n(n_one, one="{n} one-tag", other="{n} one-tag")],
                                className="lchip static term", tabIndex="0", **H.attrs("legend.one_tag", tx)))
    banners = []
    if c.mode == "test":
        banners.append(html.Div(tx("mode: test — this Build comes from a test Snapshot; never publish it."),
                                className="banner"))
    mismatches = version_mismatches(c.build_json.get("software_versions") or {})
    if mismatches:
        drift = "; ".join(tx("{lib} {then} (Build) vs {now} (installed)", lib=lib, then=then, now=now)
                          for lib, then, now in mismatches)
        banners.append(html.Div(tx("Library versions differ from the ones this Build was made with, so numbers may "
                                   "differ from the Build's: {drift}.", drift=drift), className="banner"))
    if c.build_json.get("parse_errors_allowed"):
        banners.append(html.Div(tx("parse_errors_allowed — this Build was made with --allow-parse-errors ({n} errors); "
                                   "never publish it.", n=c.build_json.get("parse_error_count")), className="banner"))
    rows_total = c.read(dataset).size
    defining = c.dataset(dataset).defining_tag
    n_missing = len(tables["nin"])
    filters = html.P(tx("Minimum games per tag {g}, minimum shared games {s}, Minimum Months Filter {m}.",
                        g=settings.min_games_per_tag, s=settings.min_shared_games, m=settings.min_months) + " " +
                     tx.n(n_missing, one="{n} tag of the dataset is not in the network; it is listed below with all "
                                         "its reasons.",
                          other="{n} tags of the dataset are not in the network; every one is listed below with all "
                                "its reasons."))
    n_tags, seconds = meta["n_nodes"], meta["clustering_seconds"]
    estimate = tx("Estimate: {n} tags × {ms} ms (one clustering) ≈ {s} s, plus about 4 s job start-up", n=n_tags,
                  ms=tx.fixed(seconds * 1000, ".0f"), s=tx.fixed(n_tags * seconds, ".1f"))
    export_summary = html.P([html.Span(tx("Export"), className="term", tabIndex="0", **H.attrs("export.zip", tx)),
                             tx(": steamstudy_{dataset}_{state_id}_<UTC timestamp>.zip, with every table above, "
                                "export.json with the full state key and provenance, and Removal Sensitivity results "
                                "for this exact state if any.", dataset=dataset, state_id=meta["state_id"])])
    return {
        "legend": legend,
        "summary-row": V.summary_row(q, rows_total, gamma_text, settings.null_replicates, tx=tx),
        "state-sentence": V.state_sentence(c.dataset(dataset).label, rows_total, settings,
                                           [str(names.get(t, t)) for t in settings.hidden_tag_ids],
                                           defining.name if defining else None,
                                           [str(names.get(t, t)) for t in settings.removed_tag_ids], meta["state_id"],
                                           tx=tx),
        "quality-detail": [*V.quality_boxes(q, gamma_text, meta["k"], settings.null_replicates, tx=tx),
                           V.connections_matrix(tables["clusters"], tables["connections"], settings.clustering_weight,
                                                settings.resolution, dataset, tx=tx)],
        "banners": banners,
        "dataset-summary": V.state_table(meta["key"], meta["state_id"], c.dataset(dataset).label, meta["n_games"],
                                         rows_total, names, tx=tx),
        "filters-summary": filters,
        "rs-estimate": estimate,
        "export-summary": export_summary,
        "tag-search": V.search_options(tables, settings.min_games_per_tag, tx=tx),
    }


# The outputs `state_views` fills, in the order `state_text` sends them.
STATE_VIEWS = [("legend", "children"), ("summary-row", "children"), ("state-sentence", "children"),
               ("quality-detail", "children"), ("banners", "children"), ("dataset-summary", "children"),
               ("filters-summary", "children"), ("rs-estimate", "children"), ("export-summary", "children"),
               ("tag-search", "options")]


def state_text(lang, meta, build_path):
    """A language switch: the Network State's text again, in the new language, from the tables already computed."""
    if not meta:
        raise PreventUpdate
    views = state_views(load_build(build_path), meta, tables_of(meta, build_path), text(lang_of(lang)))
    return [views[id_] for id_, _ in STATE_VIEWS]


def recompute(build_path, dataset, min_games, min_shared, min_months, genre_hidden, defining_hidden, weight,
              algorithm, gamma, seed, removed, verify, lang=None):
    tx = text(lang_of(lang))
    if not _valid_gamma(gamma) or seed is None or int(seed) < 0:
        raise PreventUpdate
    c = load_build(build_path)
    settings = settings_from_controls(c, dataset, min_games, min_shared, min_months, genre_hidden, defining_hidden,
                                      weight, algorithm, gamma, seed, removed)
    state = compute_state(c.games(dataset), settings, c.context(dataset))
    tables = state_tables(state)
    inp = layout_input(state)
    q = tables["cluster_quality.csv"][0]
    gamma_text = resolution_text(settings.resolution)
    k = settings.noise_seeds
    names = {**{t.id: t.name for t in c.genre_tags}, **state.network.tag_names}
    defining_ref = c.dataset(dataset).defining_tag
    named = {*settings.hidden_tag_ids, *settings.removed_tag_ids, *([defining_ref.id] if defining_ref else [])}
    # meta["names"]: the hidden, removed and defining tags' names, which the state's text names (`state_views`)
    meta = {"state_id": state.state_id, "key": settings.key(), "n_nodes": len(state.nodes),
            "clustering_seconds": state.clustering_seconds, "k": k, "gamma": gamma_text, "dataset": dataset,
            "weight": settings.clustering_weight, "n_games": state.network.n_games,
            "names": {str(t): names.get(t, str(t)) for t in sorted(named)}}
    if defining_ref:
        meta["names"][str(defining_ref.id)] = defining_ref.name
    store_tables = browser_tables(tables)
    edges_view = store_tables["edges"]
    remember_tables(state.state_id, store_tables)
    kind_of = {r["cluster"]: r["kind"] for r in tables["clusters.csv"]}
    base = {
        "nodes": [{"id": str(r["tag_id"]), "label": r["tag"], "cluster": r["cluster"], "kind": kind_of[r["cluster"]],
                   "n_games": r["n_games"], "center": r["is_center"], "size": inp.sizes[r["tag_id"]]}
                  for r in tables["nodes.csv"]],
        "edges": [{"source": str(e.u), "target": str(e.v), "shared": e.shared, "lift": e.lift,
                   "intra": state.cluster_of[e.u] == state.cluster_of[e.v]} for e in state.network.edges],
        "start": {str(t): list(p) for t, p in inp.start.items()},  # the loose layout: where the layout starts
        "basis": [dataset, settings.min_months, settings.clustering_weight, settings.seed],
        "weight": settings.clustering_weight, "seed": settings.seed, "dataset": dataset,
        "min_shared": settings.min_shared_games,  # named on the Edge appearance card, beside Hide links below
    }
    restore = [{"label": f"{names.get(t, t)} ({t})", "value": t} for t in settings.removed_tag_ids]
    verify_text: Any = no_update
    verify_out: Any = no_update
    if verify and verify.get("expected"):
        ok = state.state_id == verify["expected"]
        verify_text = tx("Opened state {expected}: recomputed state_id {state_id} {mark}",
                         expected=verify["expected"], state_id=state.state_id, mark="✓" if ok else "✗")
        verify_out = {"expected": None}
    elif verify and (verify.get("applied") or verify.get("applied_key")):
        verify_text, verify_out = applied_line(verify, settings.key(), state.cluster_of, tx)
    views = state_views(c, meta, store_tables, tx)
    return (meta, store_tables, base, views["legend"], views["summary-row"], views["state-sentence"],
            views["quality-detail"],
            V.grid_rows(tables["not_in_network.csv"]), V.grid_rows(tables["nodes.csv"]), V.grid_rows(edges_view),
            V.grid_rows(tables["clusters.csv"]), V.grid_rows(tables["cluster_connections.csv"]),
            V.grid_rows(tables["null_model.csv"]), V.grid_rows(tables["seed_noise.csv"]),
            views["banners"], restore, verify_text, verify_out, views["dataset-summary"], views["filters-summary"],
            views["rs-estimate"], views["export-summary"], "", views["tag-search"],
            {"rows": store_tables["connections"], "gamma": settings.resolution,
             "clusters": [{"cluster": r["cluster"], "size": r["size"], "kind": r["kind"]}
                          for r in store_tables["clusters"]]})


# ----------------------------------------------------------------------------- 3. graph


def _graph_from_base(base: dict[str, Any]) -> nx.Graph:
    """The state's graph in the canonical order of `to_graph` (int tag ids), so the app's layouts equal the
    export's."""
    g = nx.Graph()
    g.add_nodes_from(sorted(int(n["id"]) for n in base["nodes"]))
    for e in sorted(base["edges"], key=lambda e: (int(e["source"]), int(e["target"]))):
        g.add_edge(int(e["source"]), int(e["target"]),
                   w=float(e["shared"]) if base["weight"] == "shared_games" else e["lift"])
    return g


def layout_input_from_base(base: dict[str, Any]) -> LayoutInput:
    """The layout's input, rebuilt from the plain data the browser holds (the same as `layout_input(state)`)."""
    by_cluster: dict[str, set[int]] = {}
    centers: dict[str, int | None] = {}
    for n in base["nodes"]:
        by_cluster.setdefault(n["cluster"], set()).add(int(n["id"]))
        if n["center"]:
            centers[n["cluster"]] = int(n["id"])
    clusters = [Cluster(label, frozenset(members)) for label, members in
                sorted(by_cluster.items(), key=lambda kv: int(kv[0][1:]))]
    return LayoutInput(_graph_from_base(base), {int(k): (v[0], v[1]) for k, v in base["start"].items()},
                       {int(n["id"]): n["size"] for n in base["nodes"]},
                       {int(n["id"]): label_width(n["label"]) for n in base["nodes"]}, clusters, centers, base["seed"])


MIN_CANVAS = Canvas(320, 240)  # a canvas still opening or closing a panel is never laid out smaller


def canvas_of(reported: dict | None) -> Canvas:
    """The canvas graph.js reports (its free area, in steps), or the reference canvas until it has."""
    if not reported or not reported.get("w") or not reported.get("h"):
        return REFERENCE_CANVAS
    return Canvas(max(float(reported["w"]), MIN_CANVAS.width), max(float(reported["h"]), MIN_CANVAS.height))


def relayout_positions(base: dict[str, Any],
                       relayout_store: dict | None) -> tuple[dict[int, tuple[float, float]], float] | None:
    """Tidy's Global positions and the zoom their labels are spaced for, while the layout basis and the visible
    tags are the ones they were made for. Positions opened from an older export (`restore`) are first brought
    into the reference canvas, clamped and spaced for their labels."""
    if relayout_store and relayout_store.get("basis") == base["basis"]:
        nodes = {int(n["id"]) for n in base["nodes"]}
        kept = {int(k): (v[0], v[1]) for k, v in relayout_store["positions"].items() if int(k) in nodes}
        if set(kept) == nodes:
            if relayout_store.get("restore"):
                return restore(layout_input_from_base(base), kept, REFERENCE_CANVAS)
            return kept, float(relayout_store.get("zoom", 1.0))
    return None


# Recent layouts, newest last: opening and closing a panel (or switching the layout back) costs nothing.
LAYOUTS: OrderedDict[str, Layout] = OrderedDict()
LAYOUTS_KEPT = 12


def cached_layout(base: dict[str, Any], layout_mode: str, relayout_store: dict | None, canvas: dict | None) -> Layout:
    """`lay_out` for the browser's graph, memoised on everything it reads (never on the selection)."""
    size = canvas_of(canvas)
    separated = layout_mode == "separated"
    key = hashlib.sha256(json.dumps([base, separated, relayout_store, size.width, size.height], sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()
    with _MEMO_LOCK:
        if key in LAYOUTS:
            LAYOUTS.move_to_end(key)
            return LAYOUTS[key]
    tidied = relayout_positions(base, relayout_store)
    layout = lay_out(layout_input_from_base(base), size, positions=tidied[0] if tidied else None,
                     zoom=tidied[1] if tidied else 1.0, separated=separated)
    with _MEMO_LOCK:
        LAYOUTS[key] = layout
        while len(LAYOUTS) > LAYOUTS_KEPT:
            LAYOUTS.popitem(last=False)
    return layout


def render_graph(base, layout_mode, relayout_store, selection, canvas=None):
    """The `graph-data` payload: every visible node and edge with its target position (no AppIDs), laid out for
    the canvas the browser reports (exports use the reference canvas). Each edge carries its raw values; graph.js
    draws the Edge Appearance from them (the legend's show-shared switch never comes back here)."""
    if not base:
        raise PreventUpdate
    layout = cached_layout(base, layout_mode, relayout_store, canvas)
    regions: list[dict[str, Any]] = []
    positions, zoom = layout.positions, layout.zoom
    if layout_mode == "separated":
        zoom = layout.separated_zoom
        positions = layout.separated
        regions = [dict(r) for r in layout.regions]
        counts = Counter(V.POOL if n["kind"] == "one_tag" else n["cluster"] for n in base["nodes"])
        for r in regions:
            r["color"] = R.REGION_COLOR if r["cluster"] == V.POOL else cluster_color(r["cluster"], "multi_tag")
            r["count"] = counts[r["cluster"]]  # graph.js titles it in the Interface Language (ui-words `map`)
    return R.payload(base["nodes"], base["edges"], {str(t): list(p) for t, p in positions.items()},
                     dataset=base["dataset"], layout=layout_mode, regions=regions, selection=selection,
                     weight=base["weight"], basis=base["basis"], zoom=zoom, min_shared=base.get("min_shared"))


def thickness_legend(base):
    """The legend's show-shared switch, offered only under lift, for the state drawn now (never ahead of a recompute
    still running). Its key's words are graph.js `edgeKey`'s, in the browser."""
    if not base:
        raise PreventUpdate
    return {} if base["weight"] == "lift" else {"display": "none"}


def untick_thickness(_weight):
    """A new Clustering Weight starts on its own thickness: the shared-games switch never carries over."""
    return []


def show_selection(selection):
    """Tell the canvas about a new selection without resending the elements; a cluster is also zoomed to."""
    patch = Patch()
    patch["selected"] = R.selection_ref(selection)
    if selection and selection.get("kind") == "cluster":
        patch["view"] = {"cmd": "focus", "cluster": selection["id"], "nonce": time.time()}
    elif selection and selection.get("kind") == "pair":
        a, _, b = selection["id"].partition("|")
        patch["view"] = {"cmd": "focus_pair", "a": a, "b": b, "nonce": time.time()}
    elif selection and selection.get("pan"):
        patch["view"] = {"cmd": "center", "id": selection["id"], "nonce": time.time()}
    return patch


def do_tidy(_n, base, relayout_store, canvas=None, dragged=None):
    """Tidy: settle the Global layout from what is drawn now, the nodes dragged in it (sent by graph.js under
    the same layout basis) staying where they were dropped."""
    if not base:
        raise PreventUpdate
    inp = layout_input_from_base(base)
    tidied = relayout_positions(base, relayout_store)
    if tidied is None:
        layout = lay_out(inp, canvas_of(canvas), separated=False)
        tidied = layout.positions, layout.zoom
    current, zoom = tidied
    pinned = {}
    if dragged and dragged.get("basis") == base["basis"]:
        pinned = {int(k): (float(v[0]), float(v[1])) for k, v in (dragged.get("positions") or {}).items()
                  if int(k) in current}
    positions, zoom = tidy(inp, {**current, **pinned}, canvas_of(canvas), pinned=pinned, zoom=zoom)
    return {"basis": base["basis"], "positions": {str(k): list(v) for k, v in positions.items()}, "zoom": zoom}


# ----------------------------------------------------------------------------- 4. selection and inspector


def select(event, _legend, cluster_rows, rs_rows, node_rows, panels, search=None, connection_rows=None):
    trigger = ctx.triggered_id
    sel: dict[str, Any] | None = None
    if trigger == "tag-search":
        if not search:
            raise PreventUpdate  # the search was cleared after a pick
        kind, _, tag = str(search).partition(":")
        sel = {"kind": "node", "id": tag, "pan": True} if kind == "node" else {"kind": "nin", "id": tag}
    elif trigger == R.EVENT_ID and event:
        kind = event.get("kind")
        if kind == "background":
            return None, no_update
        if kind == "region":
            cluster = event.get("cluster")
            sel = {"kind": "cluster", "id": cluster} if cluster and cluster != "one_tag_pool" else None
        elif kind == "node":
            sel = {"kind": "node", "id": str(event["id"])}
        elif kind == "edge":  # a link tapped in the graph, or a connected tag's row in the Inspector (pan)
            sel = {"kind": "edge", "id": str(event["id"]), "source": event["source"], "target": event["target"]}
            if event.get("pan"):
                sel["pan"] = True
            if event.get("from_pair"):  # a row of a pair's links: the link view offers the way back
                sel["from_pair"] = str(event["from_pair"])
        elif kind == "pair":  # a Cluster pair: a Connections row, a matrix cell, a map link, "show this pair"
            sel = {"kind": "pair", "id": str(event["id"])}
    elif isinstance(trigger, dict) and trigger.get("type") == "legend":
        if not ctx.triggered[0]["value"]:
            raise PreventUpdate  # the legend was re-rendered, not clicked
        sel = {"kind": "cluster", "id": trigger["cluster"]}
    elif trigger == "clusters-grid" and cluster_rows:
        sel = {"kind": "cluster", "id": cluster_rows[0]["cluster"]}
    elif trigger == "connections-grid" and connection_rows:
        sel = {"kind": "pair", "id": V.pair_id(connection_rows[0]["cluster_a"], connection_rows[0]["cluster_b"])}
    elif trigger in ("rs-grid", "nodes-grid"):
        rows = rs_rows if trigger == "rs-grid" else node_rows
        if rows:
            sel = {"kind": "node", "id": str(rows[0]["tag_id"])}
    if sel is None:
        raise PreventUpdate
    return sel, True  # opens the floating Inspector wherever the Inspector is not docked


def inspect(selection, meta, rs_view, build_path, dataset, min_months, lang=None):
    """The Inspector for a selection. The request carries only the state's id; its tables stay on the server."""
    tables = tables_of(meta, build_path) if meta else None
    return inspector(selection, tables, rs_view, build_path, dataset, min_months, meta, lang)


def inspector(selection, tables, rs_view, build_path, dataset, min_months, meta, lang=None):
    tx = text(lang_of(lang))
    hide = {"display": "none"}
    if not selection or not tables:
        return [html.P(tx("Click a node, an edge or a cluster (legend or Clusters table) to inspect it."))], hide, hide
    weight = (meta or {}).get("weight", "shared_games")
    if selection["kind"] == "nin":
        row = next((r for r in tables["nin"] if str(r["tag_id"]) == selection["id"]), None)
        if row is not None:
            return V.nin_inspector(row, (meta or {})["key"]["min_games_per_tag"], tx=tx), hide, hide
        selection = {"kind": "node", "id": selection["id"]}  # it has come back into the network
    if selection["kind"] == "node":
        node = next((r for r in tables["nodes"] if str(r["tag_id"]) == selection["id"]), None)
        if node is None:
            return [html.P(tx("This tag is not in the current network."))], hide, hide
        size = next(r["size"] for r in tables["clusters"] if r["cluster"] == node["cluster"])
        rs_row, stale = None, False
        if rs_view and rs_view.get("rows"):
            rs_row = next((r for r in rs_view["rows"] if str(r["tag_id"]) == selection["id"]), None)
            stale = rs_view.get("state_id") != (meta or {}).get("state_id")
        show = {"display": "inline-block"}
        kind = next(r["kind"] for r in tables["clusters"] if r["cluster"] == node["cluster"])
        games = V.tag_games(load_build(build_path).games(dataset), int(min_months), int(node["tag_id"]))
        return (V.node_inspector(node, weight, rs_row, size, stale, games, V.connected_tags(tables, node["tag_id"]),
                                 cluster_color(node["cluster"], kind), tx=tx), show, show)
    if selection["kind"] == "edge":
        u, v = int(selection["source"]), int(selection["target"])
        edge = next((r for r in tables["edges"] if r["source_tag_id"] == min(u, v) and r["target_tag_id"] == max(u, v)), None)
        if edge is None:
            return [html.P(tx("This edge is not in the current network."))], hide, hide
        c = load_build(build_path)
        games = [{"appid": g.appid, "name": g.name, "rank": g.rank}
                 for g in filter_games(c.games(dataset), int(min_months)) if u in g.tag_ids and v in g.tag_ids]
        return V.edge_inspector(edge, games, tx=tx, pair=_edge_pair(edge, tables),
                                from_pair=selection.get("from_pair")), hide, hide
    if selection["kind"] == "pair":
        row = next((r for r in tables["connections"] if V.pair_id(r["cluster_a"], r["cluster_b"]) == selection["id"]),
                   None)
        if row is None:
            return [html.P(tx("This pair is not in the current partition."))], hide, hide
        kinds = {r["cluster"]: r["kind"] for r in tables["clusters"]}
        one_tag = {c for c, k in kinds.items() if k != "multi_tag"}
        color = lambda g: R.ONE_TAG_COLOR if g == V.POOL else cluster_color(g, kinds.get(g, "multi_tag"))  # noqa: E731
        links = V.pair_links(row["cluster_a"], row["cluster_b"], tables["edges"], one_tag)
        empty = V.empty_ratio_case(row, tables["nodes"], tables["clusters"], tx)
        return (V.pair_inspector(row, links, (color(row["cluster_a"]), color(row["cluster_b"])), weight,
                                 float(meta["key"]["resolution"]), empty, tx=tx), hide, hide)
    cluster = next((r for r in tables["clusters"] if r["cluster"] == selection["id"]), None)
    if cluster is None:
        return [html.P(tx("This cluster is not in the current partition."))], hide, hide
    by_id = {r["tag_id"]: r for r in tables["nodes"]}
    members = [by_id[t] for t in cluster["member_tag_ids"] if t in by_id]
    kept = filter_games(load_build(build_path).games(dataset), int(min_months))
    games = cluster_games(kept, list(cluster["member_tag_ids"]), set(by_id))
    names = {t: r["tag"] for t, r in by_id.items()}
    section = V.cluster_games_section(cluster, games, len(kept), names, tx=tx)
    links = V.connections_section(cluster["cluster"], tables["connections"], weight, float(meta["key"]["resolution"]),
                                  tx=tx)
    return (V.cluster_inspector(cluster, members, weight, cluster_color(cluster["cluster"], cluster["kind"]), tx=tx,
                                games=section, connections=links), hide, hide)


def _edge_pair(edge: dict[str, Any], tables: dict[str, Any]) -> str | None:
    """The pair a link between two groups belongs to (the pool: every One-Tag Cluster), as its id; None inside one."""
    one_tag = {r["cluster"] for r in tables["clusters"] if r["kind"] != "multi_tag"}
    group = lambda c: V.POOL if c in one_tag else c  # noqa: E731
    a, b = group(edge["source_cluster"]), group(edge["target_cluster"])
    if a == b and a != V.POOL:
        return None
    if a == b == V.POOL and edge["source_cluster"] == edge["target_cluster"]:
        return None
    for r in tables["connections"]:
        if {r["cluster_a"], r["cluster_b"]} == {a, b} and (a != b or r["cluster_a"] == r["cluster_b"]):
            return V.pair_id(r["cluster_a"], r["cluster_b"])
    return None


def nin_act(_n, selection, action, removed, genre_hidden, defining_hidden, build_path, dataset):
    """Restore or Unhide a missing tag from its card: the same control changes as the Restore button or the
    hidden-tag checklists, then the tag is selected."""
    if not selection or selection.get("kind") != "nin":
        raise PreventUpdate
    tag = int(selection["id"])
    removed, genre_hidden, defining_hidden = list(removed or []), list(genre_hidden or []), list(defining_hidden or [])
    if action == "restore":
        removed = [t for t in removed if t != tag]
    elif action == "unhide":
        genre_hidden = [t for t in genre_hidden if t != tag]
        defining = load_build(build_path).dataset(dataset).defining_tag
        if defining is not None and defining.id == tag:
            defining_hidden = []
    else:
        raise PreventUpdate
    return sorted(removed), genre_hidden, defining_hidden, {"kind": "node", "id": str(tag)}


def on_nin_action(clicks, selection, removed, genre_hidden, defining_hidden, build_path, dataset):
    trigger = ctx.triggered_id
    if not isinstance(trigger, dict) or not any(clicks or []):
        raise PreventUpdate
    return nin_act(1, selection, trigger["action"], removed, genre_hidden, defining_hidden, build_path, dataset)


def edit_removed(_remove, _restore, _reset, selection, pick, removed):
    removed = list(removed or [])
    trigger = ctx.triggered_id
    if trigger == "remove-btn" and selection and selection.get("kind") == "node":
        tag = int(selection["id"])
        if tag not in removed:
            removed.append(tag)
    elif trigger == "restore-btn" and pick is not None:
        removed = [t for t in removed if t != int(pick)]
    elif trigger == "reset-btn":
        removed = []
    else:
        raise PreventUpdate
    return sorted(removed)


# ----------------------------------------------------------------------------- 5. modes and panels


def arrange(mode, tab, panels, graph_only):
    """Block order and visibility and the root classes (app.css does the layout). A selection never changes
    them, so it never re-renders the blocks."""
    panels = panels or []
    styles = block_styles(mode, tab, panels)
    return [styles[b] for b in BLOCKS] + [root_class(mode, panels, bool(graph_only))]


def inspector_form(panels, floating_open, selection):
    """The Inspector's form: docked as a pane, or (with a selection to show) a floating card."""
    return ("inspector" + (" docked" if "inspector" in (panels or []) else "")
            + (" has-sel" if floating_open and selection else ""))


def fit_view(_n):
    patch = Patch()
    patch["view"] = {"cmd": "fit", "nonce": time.time()}
    return patch


# ----------------------------------------------------------------------------- 6. Removal Sensitivity


def rs_request(_run, _cont, _tag, selection, meta):
    if not meta:
        raise PreventUpdate
    trigger = ctx.triggered_id
    if trigger == "rs-run-tag":
        if not selection or selection.get("kind") != "node":
            raise PreventUpdate
        return {"kind": "tag", "tag": int(selection["id"]), "key": meta["key"], "nonce": time.time()}
    return {"kind": "all", "tag": None, "key": meta["key"], "nonce": time.time()}


def rs_job(set_progress, request, build_path):
    """Background job: inputs are plain values; each finished row is cached at once, so Cancel keeps a partial run."""
    if not request:
        raise PreventUpdate
    c = load_build(build_path)
    settings = Settings.from_key(request["key"])
    state = compute_state(c.games(settings.dataset), settings, c.context(settings.dataset))
    total = len(state.nodes)
    cached = rs_cache.load(c.app_cache, settings.key())
    skip = set(cached.rows) if cached else set()
    tags = [request["tag"]] if request["kind"] == "tag" else None
    set_progress({"done": 0, "total": total if tags is None else 1, "starting": True})

    def progress(done: int, todo: int) -> None:
        set_progress({"done": done, "total": todo})  # raw numbers: `progress_display` words them

    removal_sensitivity(state, tags, skip=skip, progress=progress,
                        on_row=lambda row: rs_cache.add_row(c.app_cache, settings.key(), total, row))
    return request["nonce"]


def progress_display(data, _request, _cancel, lang=None):
    """The progress bar and its label, in the Interface Language (a running job reports raw numbers only)."""
    if ctx.triggered_id in ("rs-request", "rs-cancel") or not data:
        return "0", "1", no_update
    tx = text(lang_of(lang))
    label = tx("starting…") if data.get("starting") else tx("{done} of {total}", done=data["done"], total=data["total"])
    return str(data["done"]), str(max(data["total"], 1)), label


def refresh_rs_view(meta, _done, rs_view, build_path):
    if not meta:
        raise PreventUpdate
    c = load_build(build_path)
    cached = rs_cache.load(c.app_cache, meta["key"])
    if cached is not None:
        return {"state_id": meta["state_id"], "rows": cached.ordered_rows(), "done": cached.done,
                "total": cached.total, "from_export": False}
    if rs_view and rs_view.get("rows"):
        if rs_view.get("from_export") and rs_view.get("state_id") == meta["state_id"]:
            return no_update
        return {**rs_view, "stale": rs_view.get("state_id") != meta["state_id"]}
    return {"state_id": meta["state_id"], "rows": [], "done": 0, "total": meta["n_nodes"], "from_export": False}


def show_rs(rs_view, beyond, cluster, tables, meta, lang=None):
    if not meta or not tables:
        raise PreventUpdate
    tx = text(lang_of(lang))
    rows = list((rs_view or {}).get("rows") or [])
    current = bool(rs_view) and rs_view.get("state_id") == meta["state_id"]
    stability = {r["tag_id"]: r["membership_stability"] for r in tables["nodes"]} if current else {}
    view_rows = [{**r, "membership_stability": stability.get(r["tag_id"])} for r in rows]
    if beyond:
        view_rows = [r for r in view_rows if r["rc_ari_beyond_noise"]]
    if cluster:
        view_rows = [r for r in view_rows if r["cluster"] == cluster]
    view_rows.sort(key=lambda r: (r["rc_ari"] if r["rc_ari"] is not None else 2.0,
                                  -abs(r["rc_delta_modularity"] or 0.0)))
    q = tables["quality"]
    noise = tx("Compare each agreement after removal with the Seed-Noise Floor: ARI min {ari} over K = {k} noise "
               "seeds (all its numbers are in Cluster quality).", ari=tx.num(q["seed_ari_min"]), k=meta["k"])
    banner, banner_style = "", {"display": "none"}
    total = (rs_view or {}).get("total") or meta["n_nodes"]
    done = len(rows)
    if rows and not current:
        banner, banner_style = tx("Stale: these results belong to other settings. Run again for the current state."), {}
    elif rs_view and rs_view.get("from_export"):
        banner, banner_style = tx("Loaded from export (not rerun)."), {}
    elif rows and done < total:
        banner, banner_style = tx("Partial result: {done} of {total} tags.", done=done, total=total), {}
    flagged = sum(1 for r in rows if r["rc_ari_beyond_noise"])
    footer = V.chance_footer(flagged, done, meta["k"], tx=tx) if rows else tx("Not run for this state.")
    continue_style = {"display": "inline-block"} if current and 0 < done < total else {"display": "none"}
    clusters = sorted({r["cluster"] for r in rows}, key=lambda s: int(s[1:]))
    return (V.grid_rows(view_rows), "" if current or not rows else "stale", banner, banner_style, footer, noise,
            continue_style, tx("Continue ({done} of {total} done)", done=done, total=total),
            [{"label": c, "value": c} for c in clusters])


# ----------------------------------------------------------------------------- 7. export, open, cache, help


def do_export(_a, _b, build_path, meta, relayout_store, base, rs_view, verify=None):
    if not meta:
        raise PreventUpdate
    applied = verify.get("applied_from") if verify and verify.get("applied_key") == meta["key"] else None
    c = load_build(build_path)
    settings = Settings.from_key(meta["key"])
    tidied = relayout_positions(base, relayout_store) if base else None
    positions = tidied[0] if tidied else None
    rows = None
    if rs_view and rs_view.get("rows") and rs_view.get("state_id") == meta["state_id"] and not rs_view.get("stale"):
        rows = rs_view["rows"]  # only results under the exact current key; stale results are never exported
    filename, data = export_zip(c, settings, relayout_positions=positions, removal_rows=rows, applied_from=applied)
    return dash.dcc.send_bytes(data, filename)


def do_open(contents, filename, builds_root, lang=None):
    """Open Network State…: the export's Build is found by identity among the Builds this app can see."""
    if not contents:
        raise PreventUpdate
    tx = text(lang_of(lang))
    data = base64.b64decode(contents.split(",", 1)[1])
    nothing = [no_update] * 16
    try:
        opened = open_export(data, builds_root=builds_root)
    except BuildNotFound as exc:
        return [*nothing, tx("Refused: {reason}.", reason=tx(REFUSALS[exc.reason], **exc.params))]
    except OpenRefused as exc:
        return [*nothing, tx("Refused: {reason}", reason=tx(REFUSALS[exc.reason], **exc.params))]
    c = load_build(opened.build_path)
    values = controls_from_settings(c, opened.settings)
    basis = [opened.settings.dataset, opened.settings.min_months, opened.settings.clustering_weight, opened.settings.seed]
    relayout_store = ({"basis": basis, "positions": {str(k): list(v) for k, v in opened.relayout_positions.items()},
                       "restore": True} if opened.relayout_positions else None)
    rs_view = ({"state_id": opened.recorded_state_id, "rows": opened.removal_rows, "done": len(opened.removal_rows),
                "total": opened.removal_total or len(opened.removal_rows), "from_export": True}
               if opened.removal_rows else None)
    pending = {"dataset": values["dataset"], "defining-hidden": values["defining-hidden"], "removed": values["removed"]}
    message = tx("Opened {filename}: Build {build_id}, state {state_id} (schema_version {version}).",
                 filename=filename, build_id=c.build_id, state_id=opened.recorded_state_id,
                 version=opened.schema_version)
    return [str(opened.build_path), *[values[k] for k in CONTROL_IDS], values["removed"], relayout_store, rs_view,
            pending, {"expected": opened.recorded_state_id}, message]


def clear_cache(_n, build_path, lang=None):
    if not _n:
        raise PreventUpdate
    tx = text(lang_of(lang))
    counts = app_cache.clear_all(load_build(build_path).app_cache)
    rs, ps = counts["removal_sensitivity"], counts["parameter_selection"]
    return tx("Cleared {rs} and {ps}.",
              rs=tx.n(rs, one="{n} cached Removal Sensitivity result", other="{n} cached Removal Sensitivity results"),
              ps=tx.n(ps, one="{n} Parameter Selection result", other="{n} Parameter Selection results")), None


def show_help(_clicks, _close, target=None, _back=None, history=None, lang=None):
    """The help modal: a panel's `?` opens its guide section; a metric or control (workbench.js sets `help-target`
    to `<file>#<anchor>`) opens its own entry. A guide link inside the modal (`follow`) opens its target on top of
    the history, which ← Back walks down and closing clears. The guide is shown in the Interface Language, and an
    open entry is shown again in the new language when it is switched."""
    trigger = ctx.triggered_id
    history = list(history or [])
    if trigger == "lang":
        if not history:
            raise PreventUpdate
    elif trigger == "help-target":
        if not target or not target.get("target"):
            raise PreventUpdate
        if not target.get("follow"):
            history = [target["target"]]
        elif history[-1:] != [target["target"]]:
            history.append(target["target"])
    elif trigger == "help-back":
        if len(history) < 2:
            raise PreventUpdate
        history.pop()
    elif isinstance(trigger, dict):
        if not any(_clicks or []):
            raise PreventUpdate
        history = ["#".join(PANEL_SECTIONS[trigger["panel"]])]
    else:  # help-close
        return {"display": "none"}, "", [], {"display": "none"}
    file, _, anchor = history[-1].partition("#")
    return ({"display": "flex", "width": "560px"}, help_markdown_at(lang_of(lang), file, anchor or None), history,
            {"display": "inline-block" if len(history) > 1 else "none"})


def relabel(lang):
    """A language switch: every static prop the layout registered, in the new language (no recompute)."""
    tx = text(lang_of(lang))
    for id_, prop, message in RELABEL.values():
        set_props(id_, {prop: message_value(message, tx)})


def grid_words(lang):
    """A language switch: every grid's column definitions (header tooltips, the number format) and its own words."""
    tx = text(lang_of(lang))
    return [value for grid in GRIDS.values() for value in (grid(tx), grid_options(tx))]


# ----------------------------------------------------------------------------- registration


# ----------------------------------------------------------------------------- 8. Parameter Selection mode


def _ps_context(build_path, active):
    c = load_build(build_path)
    defaults, default_constraints = PV.defaults_of(c)
    settings = PV.settings_of(active) if active else defaults
    return c, settings, defaults, default_constraints


def _ps_views(c, settings, cstore, default_constraints):
    return [PV.dataset_view(c, settings, d.key, PV.active_constraints(cstore, d.key, default_constraints),
                            default_constraints) for d in c.datasets]


def ps_render(mode, active, cstore, dataset, metric, pair, running, progress, build_path, lang=None):
    """Everything the mode shows, from the cache and the mode's stores (no job). It follows a job through
    `ps-running` and the progress store, never through the job's own output: Dash would hold it until the job ends."""
    if mode != "selection":
        raise PreventUpdate
    progress = progress if running else None
    tx = text(lang_of(lang))
    c, settings, defaults, default_constraints = _ps_context(build_path, active)
    views = _ps_views(c, settings, cstore, default_constraints)
    view = next(v for v in views if v.dataset == dataset)
    names = PV.tag_names(c)
    settings_label = SEL.settings_label(settings, defaults, names, tx=tx)
    labels = {v.dataset: SEL.constraints_label(PV.active_constraints(cstore, v.dataset, default_constraints),
                                               default_constraints, tx=tx) for v in views}
    custom = {d: "; ".join(x.text for x in (settings_label, labels[d]) if x.custom) for d in labels}
    validated = {v.dataset: PV.is_validated(c, settings, v.dataset, v.default_choice.chosen if v.default_choice
                                            else None) for v in views}
    shown_pair = view.default_choice.chosen if view.default_choice else None
    shown = PV.validation_of(c, settings, dataset, shown_pair, view.result(shown_pair) if shown_pair else None)
    inspected = tuple(pair) if pair else view.star
    inspected_validation = (PV.validation_of(c, settings, dataset, inspected, view.result(inspected)) if inspected
                            else None)
    computed = next((v.computed_with for v in views if v.computed_with), None)
    line, banner = PV.provenance(computed, tx=tx)
    key_hash = SEL.key_hash(settings.settings_key())[:12]
    cache_line = tx("Results from the app cache: Build {build_id}, settings key {key}, method v{version}",
                    build_id=c.build_id, key=key_hash, version=SEL.METHOD_VERSION.rsplit("-", 1)[-1])
    partial = [v for v in views if v.status == "partial"]
    continue_style = {"display": "inline-block"} if partial and not progress else {"display": "none"}
    done = sum(v.done for v in partial)
    total = sum(v.total for v in partial)
    running = bool(progress)
    reason = settings_label.text if settings_label.custom else tx("No results for these settings on this computer yet.")
    loading = PV.loading_panel(progress, views, settings, reason, tx=tx) if running else []
    result = view.result(inspected) if inspected else None
    apply_text, apply_class = PV.workbench_line(result, tx=tx) if result else ("", "small")
    can_validate = view.status == "complete" and result is not None and result.selected is not None
    return (
        PV.run_rows(views, progress, validated, tx=tx), cache_line, line,
        banner or "", {} if banner else {"display": "none"},
        continue_style, tx("Continue ({done} of {total} pairs)", done=done, total=total),
        not any(v.status == "complete" for v in views),
        PV.strip(views, dataset, {d: t for d, t in custom.items() if t}, tx=tx), loading,
        PV.heatmap(view, metric or "neighbour_agreement", inspected, tx=tx),
        PV.why(view, inspected, settings_label.text, labels[dataset].text, settings.min_multi_tag_clusters, tx=tx),
        PV.validation_card(view, shown, names, tx=tx),
        PV.inspector(view, inspected, names, tx=tx),
        result is None or result.selected is None, apply_text, apply_class,
        {"display": "inline-block"} if can_validate and inspected_validation is None else {"display": "none"},
        labels[dataset].text, settings_label.text, tx("Run {dataset}", dataset=c.dataset(dataset).label),
        *PV.pill_values(views, running, settings_label.custom, tx=tx),
        PV.inspector_validation(view, inspected, inspected_validation, tx=tx),
    )


def ps_inspector_form(_click, _close):
    """The floating Pair Inspector (medium and narrow) starts closed, opens on a heatmap pick and closes with its ×.
    A dataset switch or new settings change what it shows, never whether it floats."""
    return PV.inspector_form(ctx.triggered_id != "ps-inspector-close")


def ps_run_request(_all, _one, _continue, active, dataset, build_path):
    trigger = ctx.triggered_id
    c = load_build(build_path)
    if trigger == "ps-run-all":
        datasets = [d.key for d in c.datasets]
    elif trigger == "ps-run-one":
        datasets = [dataset]
    else:
        _, settings, _, default_constraints = _ps_context(build_path, active)
        datasets = [v.dataset for v in _ps_views(c, settings, None, default_constraints) if v.status == "partial"]
    if not datasets:
        raise PreventUpdate
    return {"datasets": datasets, "settings": active, "nonce": time.time()}


def ps_job(set_progress, request, build_path, map_fn=None):
    """Background job: Run (grids, then the default-constraint pairs' validation) through one process pool.
    Finished graph files are written at once, so Cancel keeps them."""
    if not request:
        raise PreventUpdate
    c = load_build(build_path)
    settings = PV.settings_of(request["settings"])
    if map_fn is not None:
        ps_run.run(c, settings, request["datasets"], map_fn=map_fn, on_progress=set_progress)
        return request["nonce"]
    import multiprocess as mp

    set_progress(_starting(request["datasets"][0], len(request["datasets"]), "grid", len(settings.pairs())))
    with mp.Pool(ps_run.worker_count(c.network.parameter_selection.workers)) as pool:
        ps_run.run(c, settings, request["datasets"], map_fn=pool.imap_unordered, on_progress=set_progress)
    return request["nonce"]


def _starting(dataset, n_datasets, phase, total):
    """A first progress record while the worker pool starts (several seconds on Windows), so the loading panel
    shows at once."""
    return {"dataset": dataset, "dataset_index": 1, "n_datasets": n_datasets, "phase": phase, "done": 0,
            "total": total, "weight_done": 0.0, "weight_total": 1.0, "elapsed": 0.0}


def _shown_view(c, settings, cstore, dataset, default_constraints):
    """The dataset as the mode shows it: chosen under its active constraints (the Inspector's ★ pair)."""
    return PV.dataset_view(c, settings, dataset, PV.active_constraints(cstore, dataset, default_constraints),
                           default_constraints)


def ps_validate_request(_n, active, dataset, pair, build_path, cstore=None):
    if not _n:
        raise PreventUpdate
    c, settings, _, default_constraints = _ps_context(build_path, active)
    if not pair:
        view = _shown_view(c, settings, cstore, dataset, default_constraints)
        if view.star is None:
            raise PreventUpdate
        pair = list(view.star)
    return {"dataset": dataset, "pair": list(pair), "settings": active, "nonce": time.time()}


def ps_validate_job(set_progress, request, build_path, map_fn=None):
    """Background job: Validate this pair. All-or-nothing: a cancel writes nothing."""
    if not request:
        raise PreventUpdate
    c = load_build(build_path)
    settings = PV.settings_of(request["settings"])
    g, s = request["pair"]
    if map_fn is not None:
        ps_run.validate_pair(c, settings, request["dataset"], g, s, map_fn=map_fn, on_progress=set_progress)
        return request["nonce"]
    import multiprocess as mp

    set_progress(_starting(request["dataset"], 1, "validation", settings.replicates + settings.subsamples))
    with mp.Pool(ps_run.worker_count(c.network.parameter_selection.workers)) as pool:
        ps_run.validate_pair(c, settings, request["dataset"], g, s, map_fn=pool.imap_unordered,
                             on_progress=set_progress)
    return request["nonce"]


def ps_pick_dataset(_clicks):
    trigger = ctx.triggered_id
    if not isinstance(trigger, dict) or not any(_clicks or []):
        raise PreventUpdate
    return trigger["dataset"], None


def ps_pick_cell(click):
    if not click or not click.get("points"):
        raise PreventUpdate
    point = click["points"][0]
    return [int(point["y"]), int(point["x"])]


CONSTRAINT_NAMES = [name for name, *_ in PV.CONSTRAINT_FIELDS]


def _constraints_from_inputs(values, minimum_k):
    data = dict(zip(CONSTRAINT_NAMES, values))
    maximum = data["max_multi_tag_clusters"]
    data["max_multi_tag_clusters"] = None if maximum in (None, "", 0) else max(int(maximum), int(minimum_k))
    data["min_comparable_neighbours"] = int(data["min_comparable_neighbours"] or 0)
    for name in ("tolerance", "min_retention", "max_isolated_share", "min_lcc_share"):
        data[name] = float(data[name] if data[name] is not None else 0.0)
    return SEL.Constraints(**data)


def ps_constraint_marks(*args):
    """The "changed" markers against the defaults, and Confirm only once something differs from the active set."""
    *values, cstore, dataset, active, build_path, lang = args
    tx = text(lang_of(lang))
    c, settings, _, default_constraints = _ps_context(build_path, active)
    current = PV.active_constraints(cstore, dataset, default_constraints)
    staged = _constraints_from_inputs(values, settings.min_multi_tag_clusters)
    marks = [tx("changed") if getattr(staged, n) != getattr(default_constraints, n) else "" for n in CONSTRAINT_NAMES]
    differs = staged != current
    return [*marks, not differs, tx("Unconfirmed changes") if differs else ""]


def ps_constraint_pills(*args):
    """Each constraint pill's value: the field's staged value, in the Interface Language."""
    *values, lang = args
    tx = text(lang_of(lang))
    return [PV.constraint_value(v, n, tx=tx) for v, n in zip(values, CONSTRAINT_NAMES)]


def ps_constraints_store(_confirm, _reset, *args):
    """Confirm re-chooses from the cache (no job); Reset restores the defaults everywhere."""
    *values, scope, cstore, dataset, active, build_path = args
    c, settings, _, default_constraints = _ps_context(build_path, active)
    store = {"shared": (cstore or {}).get("shared") or PV.constraints_data(default_constraints),
             "datasets": dict((cstore or {}).get("datasets") or {})}
    if ctx.triggered_id == "ps-c-reset":
        return {"shared": PV.constraints_data(default_constraints), "datasets": {}}
    data = PV.constraints_data(_constraints_from_inputs(values, settings.min_multi_tag_clusters))
    if scope == "dataset":
        store["datasets"][dataset] = data
    else:
        store = {"shared": data, "datasets": {}}
    return store


def ps_constraint_inputs(cstore, dataset, build_path):
    """The fields show the active constraints of the shown dataset."""
    c = load_build(build_path)
    _, default_constraints = PV.defaults_of(c)
    current = PV.active_constraints(cstore, dataset, default_constraints)
    return [getattr(current, n) for n in CONSTRAINT_NAMES]


def _staged_settings(build_path, genre, defining, removed, min_months, weight, min_multi):
    c = load_build(build_path)
    defaults, _ = PV.defaults_of(c)
    return defaults.with_(genre_hidden=tuple(int(t) for t in genre or []), hide_defining_tag=bool(defining),
                          removed_tag_ids=tuple(int(t) for t in removed or []), min_months=int(min_months or 0),
                          clustering_weight=weight, min_multi_tag_clusters=int(min_multi or 1))


def ps_use_settings(_n, genre, defining, removed, min_months, weight, min_multi, cstore, build_path):
    """Use these settings: switch the mode to the staged settings' key (no job). A minimum above an active
    constraint maximum raises the maximum, which then shows as custom."""
    if not _n:
        raise PreventUpdate
    staged = _staged_settings(build_path, genre, defining, removed, min_months, weight, min_multi)
    store = json.loads(json.dumps(cstore or {}))
    for data in [store.get("shared"), *(store.get("datasets") or {}).values()]:
        if data and data.get("max_multi_tag_clusters") is not None:
            data["max_multi_tag_clusters"] = max(data["max_multi_tag_clusters"], staged.min_multi_tag_clusters)
    return PV.settings_data(staged), store if store else no_update, None


def ps_stage_settings(_reset, _copy, _remove, removed, wb_genre, wb_defining, wb_months, wb_weight, wb_removed,
                      build_path):
    """Reset to defaults, Copy from Workbench (hidden tags, Minimum Months, weight, removed tags) and the
    Inspector's Remove all edit the staged settings only."""
    trigger = ctx.triggered_id
    c = load_build(build_path)
    defaults, _ = PV.defaults_of(c)
    if trigger == "ps-s-reset":
        return (list(defaults.genre_hidden), [1] if defaults.hide_defining_tag else [], [], defaults.min_months,
                defaults.clustering_weight, defaults.min_multi_tag_clusters)
    if trigger == "ps-s-copy":
        return (list(wb_genre or []), [1] if wb_defining else [], list(wb_removed or []), int(wb_months or 0),
                wb_weight, no_update)
    if isinstance(trigger, dict) and trigger.get("type") == "ps-remove" and any(_remove or []):
        tag = int(trigger["tag"])
        return no_update, no_update, sorted({*map(int, removed or []), tag}), no_update, no_update, no_update
    raise PreventUpdate


def ps_apply(_n, dataset, pair, active, build_path, cstore=None):
    """Apply to Workbench: replace every Workbench setting with the pair's, as Open Network State does, then switch.
    The provenance line is checked on the first recompute through the `verify` store."""
    if not _n:
        raise PreventUpdate
    c, settings, defaults, default_constraints = _ps_context(build_path, active)
    view = _shown_view(c, settings, cstore, dataset, default_constraints)
    target = tuple(pair) if pair else view.star
    result = view.result(target) if target else None
    if result is None or result.selected is None:
        raise PreventUpdate
    g, s = target
    wb = result.workbench
    workbench = settings.for_pair(dataset, c.context(dataset), g, s).with_(resolution=wb["gamma"], seed=wb["seed"])
    values = controls_from_settings(c, workbench)
    applied = {"dataset": dataset, "g": g, "s": s, "grid_key_hash": SEL.key_hash(settings.grid_key(
                   dataset, c.context(dataset))), "method_version": SEL.METHOD_VERSION,
               "workbench_gamma": wb["gamma"], "workbench_seed": wb["seed"], "nodes": result.nodes,
               "membership": result.selected, "key": workbench.key()}
    pending = {"dataset": values["dataset"], "defining-hidden": values["defining-hidden"], "removed": values["removed"]}
    return [*[values[k] for k in CONTROL_IDS], values["removed"], None, None, pending, {"applied": applied},
            "workbench"]


def ps_export(_n, active, cstore, build_path):
    if not _n:
        raise PreventUpdate
    from steamstudy.app.ps_export import export_tables

    c, settings, defaults, default_constraints = _ps_context(build_path, active)
    filename, data = export_tables(c, settings, cstore)
    return dash.dcc.send_bytes(data, filename)


def register(app: dash.Dash) -> None:
    cb = app.callback
    # ---- Interface Language: the switch writes the store and the cookie; the tab title follows the words
    app.clientside_callback(ClientsideFunction(namespace="workbench", function_name="language"),
                            Output("lang", "data"), Input("lang-switch", "value"), prevent_initial_call=True)
    app.clientside_callback(ClientsideFunction(namespace="workbench", function_name="uiWords"),
                            Input("ui-words", "data"))
    cb(Input("lang", "data"), prevent_initial_call=True)(relabel)
    cb(*[Output(i, p) for grid in GRIDS for i, p in ((grid, "columnDefs"), (grid, "dashGridOptions"))],
       Input("lang", "data"), prevent_initial_call=True)(grid_words)
    cb(*[Output(i, p, allow_duplicate=True) for i, p in STATE_VIEWS], Input("lang", "data"),
       State("state-meta", "data"), State("build-path", "data"), prevent_initial_call=True)(state_text)
    cb(Output("defining-hidden", "options"), Input("dataset", "value"), Input("lang", "data"),
       State("build-path", "data"))(defining_options)
    cb(Output("defining-hidden", "value", allow_duplicate=True), Output("removed", "data", allow_duplicate=True),
       Input("dataset", "value"), State("build-path", "data"), State("pending-open", "data"),
       prevent_initial_call=True)(on_dataset)
    cb(Output("state-meta", "data"), Output("state-tables", "data"), Output("elements-base", "data"),
       Output("legend", "children"), Output("summary-row", "children"), Output("state-sentence", "children"),
       Output("quality-detail", "children"), Output("nin-grid", "rowData"), Output("nodes-grid", "rowData"),
       Output("edges-grid", "rowData"), Output("clusters-grid", "rowData"), Output("connections-grid", "rowData"),
       Output("null-grid", "rowData"), Output("seed-grid", "rowData"), Output("banners", "children"),
       Output("restore-pick", "options"), Output("verify-result", "children"),
       Output("verify", "data", allow_duplicate=True), Output("dataset-summary", "children"),
       Output("filters-summary", "children"), Output("rs-estimate", "children"), Output("export-summary", "children"),
       Output("error-message", "children"), Output("tag-search", "options"), Output("cluster-connections", "data"),
       Input("build-path", "data"), Input("dataset", "value"), Input("min-games", "value"),
       Input("min-shared", "value"), Input("min-months", "value"), Input("genre-hidden", "value"),
       Input("defining-hidden", "value"), Input("weight", "value"), Input("algorithm", "value"),
       Input("gamma", "value"), Input("seed", "value"), Input("removed", "data"), State("verify", "data"),
       State("lang", "data"), running=[(Output("busy-clustering", "hidden"), False, True)],
       prevent_initial_call="initial_duplicate")(recompute)
    cb(Output(R.DATA_ID, "data"), Input("elements-base", "data"), Input("layout-mode", "value"),
       Input("relayout", "data"), State("selection", "data"), Input(R.CANVAS_ID, "data"),
       running=[(Output("busy-layout", "hidden"), False, True)])(render_graph)
    cb(Output("thickness-shared", "style"), Input("elements-base", "data"))(thickness_legend)
    # The show-shared switch and the key's words: in the browser, no request (graph.js `edgeKey`).
    app.clientside_callback(ClientsideFunction(namespace="tagGraph", function_name="mapData"),
                            Output("cluster-map-body", "data-drawn"), Input("cluster-connections", "data"),
                            Input("ui-words", "data"))
    app.clientside_callback(ClientsideFunction(namespace="tagGraph", function_name="edgeKey"),
                            Output("thickness-label", "children"), Input("thickness-shared", "value"),
                            Input("elements-base", "data"), Input("ui-words", "data"))
    cb(Output("thickness-shared", "value"), Input("weight", "value"), prevent_initial_call=True)(untick_thickness)
    cb(Output(R.DATA_ID, "data", allow_duplicate=True), Input("selection", "data"),
       prevent_initial_call=True)(show_selection)
    app.clientside_callback(R.RENDER, Output(R.ACK_ID, "data"), Input(R.DATA_ID, "data"))
    cb(Output("relayout", "data", allow_duplicate=True), Input("relayout-btn", "n_clicks"),
       State("elements-base", "data"), State("relayout", "data"), State(R.CANVAS_ID, "data"),
       State(R.DRAGGED_ID, "data"), running=[(Output("busy-layout", "hidden"), False, True)],
       prevent_initial_call=True)(do_tidy)
    cb(Output("selection", "data"), Output("floating-open", "data", allow_duplicate=True),
       Input(R.EVENT_ID, "data"),
       Input({"type": "legend", "cluster": ALL}, "n_clicks"), Input("clusters-grid", "selectedRows"),
       Input("rs-grid", "selectedRows"), Input("nodes-grid", "selectedRows"),
       State("panels", "value"), Input("tag-search", "value"), Input("connections-grid", "selectedRows"),
       running=[(Output("busy-selecting", "hidden"), False, True)], prevent_initial_call=True)(select)
    cb(Output("tag-search", "value", allow_duplicate=True), Input("tag-search", "value"),
       prevent_initial_call=True)(lambda v: None if v else no_update)  # ready for the next pick
    cb(Output("removed", "data", allow_duplicate=True), Output("genre-hidden", "value", allow_duplicate=True),
       Output("defining-hidden", "value", allow_duplicate=True), Output("selection", "data", allow_duplicate=True),
       Input({"type": "nin-action", "action": ALL}, "n_clicks"), State("selection", "data"),
       State("removed", "data"), State("genre-hidden", "value"), State("defining-hidden", "value"),
       State("build-path", "data"), State("dataset", "value"), prevent_initial_call=True)(on_nin_action)
    cb(Output("inspector-body", "children"), Output("remove-btn", "style"), Output("rs-run-tag", "style"),
       Input("selection", "data"), Input("state-meta", "data"), Input("rs-view", "data"),
       State("build-path", "data"), State("dataset", "value"), State("min-months", "value"), Input("lang", "data"),
       running=[(Output("busy-inspector", "hidden"), False, True)])(inspect)
    cb(Output("removed", "data", allow_duplicate=True), Input("remove-btn", "n_clicks"),
       Input("restore-btn", "n_clicks"), Input("reset-btn", "n_clicks"), State("selection", "data"),
       State("restore-pick", "value"), State("removed", "data"), prevent_initial_call=True)(edit_removed)
    cb(*[Output(b, "style") for b in BLOCKS], Output("root", "className"),
       Input("mode", "value"), Input("wb-tab", "value"), Input("panels", "value"),
       Input("graph-only-on", "data"))(arrange)
    cb(Output("inspector-panel", "className"), Input("panels", "value"), Input("floating-open", "data"),
       Input("selection", "data"))(inspector_form)
    cb(Output("graph-only-on", "data"), Input("graph-only", "n_clicks"), State("graph-only-on", "data"),
       prevent_initial_call=True)(lambda _n, on: not on)
    cb(Output(R.DATA_ID, "data", allow_duplicate=True), Input("fit-btn", "n_clicks"),
       prevent_initial_call=True)(fit_view)
    app.clientside_callback(
        ClientsideFunction(namespace="workbench", function_name="pills"),
        *[Output(f"{s}-value", "children") for s in SLIDERS], *[Output(f"pill-{p}", "children") for p in PILLS],
        Output("genre-count", "children"),
        Input("dataset", "value"), *[Input(s, prop) for s in SLIDERS for prop in ("value", "drag_value")],
        Input("genre-hidden", "value"), Input("defining-hidden", "value"), Input("weight", "value"),
        Input("algorithm", "value"), Input("gamma", "value"), Input("seed", "value"), Input("ui-words", "data"),
        State("dataset", "options"), State("genre-hidden", "options"))
    cb(Output("floating-open", "data", allow_duplicate=True), Input("inspector-close", "n_clicks"),
       prevent_initial_call=True)(lambda _n: False)
    cb(Output("rs-request", "data"), Input("rs-run", "n_clicks"), Input("rs-continue", "n_clicks"),
       Input("rs-run-tag", "n_clicks"), State("selection", "data"), State("state-meta", "data"),
       prevent_initial_call=True)(rs_request)
    cb(Output("rs-done", "data"), Input("rs-request", "data"), State("build-path", "data"), background=True,
       running=[(Output("rs-run", "disabled"), True, False), (Output("rs-continue", "disabled"), True, False),
                (Output("rs-run-tag", "disabled"), True, False), (Output("rs-cancel", "disabled"), False, True)],
       cancel=[Input("rs-cancel", "n_clicks")],
       progress=[Output("rs-progress-store", "data")], prevent_initial_call=True)(rs_job)
    cb(Output("rs-progress", "value"), Output("rs-progress", "max"), Output("rs-progress-label", "children"),
       Input("rs-progress-store", "data"), Input("rs-request", "data"), Input("rs-cancel", "n_clicks"),
       Input("lang", "data"))(progress_display)
    cb(Output("rs-view", "data", allow_duplicate=True), Input("state-meta", "data"), Input("rs-done", "data"),
       State("rs-view", "data"), State("build-path", "data"), prevent_initial_call="initial_duplicate")(refresh_rs_view)
    cb(Output("rs-grid", "rowData"), Output("rs-grid-wrap", "className"), Output("rs-banner", "children"),
       Output("rs-banner", "style"), Output("rs-footer", "children"), Output("noise-line-rs", "children"),
       Output("rs-continue", "style"), Output("rs-continue", "children"), Output("rs-cluster", "options"),
       Input("rs-view", "data"), Input("rs-beyond", "value"), Input("rs-cluster", "value"),
       Input("state-tables", "data"), Input("state-meta", "data"), Input("lang", "data"))(show_rs)
    cb(Output("download", "data"), Input("export-btn", "n_clicks"), Input("export-btn-report", "n_clicks"),
       State("build-path", "data"), State("state-meta", "data"), State("relayout", "data"),
       State("elements-base", "data"), State("rs-view", "data"), State("verify", "data"),
       prevent_initial_call=True)(do_export)
    cb(Output("build-path", "data"), *[Output(i, "value", allow_duplicate=True) for i in CONTROL_IDS],
       Output("removed", "data", allow_duplicate=True), Output("relayout", "data", allow_duplicate=True),
       Output("rs-view", "data", allow_duplicate=True), Output("pending-open", "data"),
       Output("verify", "data", allow_duplicate=True), Output("open-message", "children"),
       Input("open-upload", "contents"), State("open-upload", "filename"), State("builds-root", "data"),
       State("lang", "data"), prevent_initial_call=True)(do_open)
    cb(Output("cache-message", "children"), Output("rs-view", "data", allow_duplicate=True),
       Input("clear-cache-btn", "n_clicks"), State("build-path", "data"), State("lang", "data"),
       prevent_initial_call=True)(clear_cache)
    cb(Output("help-modal", "style"), Output("help-body", "children"), Output("help-history", "data"),
       Output("help-back", "style"),
       Input({"type": "help", "panel": ALL}, "n_clicks"), Input("help-close", "n_clicks"),
       Input("help-target", "data"), Input("help-back", "n_clicks"), State("help-history", "data"),
       Input("lang", "data"), prevent_initial_call=True)(show_help)
    # ---- Parameter Selection mode
    app.clientside_callback(ClientsideFunction(namespace="workbench", function_name="psPanels"),
                            Output("ps-body", "className"), Input("ps-panels", "value"))
    ps_outputs = [Output("ps-rows", "children"), Output("ps-cache-line", "children"),
                  Output("ps-provenance", "children"), Output("ps-banner", "children"), Output("ps-banner", "style"),
                  Output("ps-continue", "style"), Output("ps-continue", "children"), Output("ps-export", "disabled"),
                  Output("ps-strip", "children"), Output("ps-loading", "children"), Output("ps-heatmap", "figure"),
                  Output("ps-why", "children"), Output("ps-validation", "children"),
                  Output("ps-inspector-body", "children"), Output("ps-apply", "disabled"),
                  Output("ps-apply-line", "children"), Output("ps-apply-line", "className"),
                  Output("ps-validate", "style"), Output("ps-c-label", "children"), Output("ps-s-label", "children"),
                  Output("ps-run-one", "children"), Output("ps-pill-run", "children"),
                  Output("ps-pill-settings", "children"), Output("ps-inspector-validation", "children")]
    cb(*ps_outputs, Input("mode", "value"), Input("ps-active", "data"), Input("ps-constraints", "data"),
       Input("ps-dataset", "data"), Input("ps-metric", "value"), Input("ps-pair", "data"),
       Input("ps-running", "data"), Input("ps-progress", "data"), State("build-path", "data"),
       Input("lang", "data"), running=[(Output("ps-busy", "hidden"), False, True)])(ps_render)
    cb(Output("ps-run-request", "data"), Input("ps-run-all", "n_clicks"), Input("ps-run-one", "n_clicks"),
       Input("ps-continue", "n_clicks"), State("ps-active", "data"), State("ps-dataset", "data"),
       State("build-path", "data"), prevent_initial_call=True)(ps_run_request)
    jobs_running = [(Output("ps-run-all", "disabled"), True, False), (Output("ps-run-one", "disabled"), True, False),
                    (Output("ps-continue", "disabled"), True, False), (Output("ps-validate", "disabled"), True, False),
                    (Output("ps-cancel", "disabled"), False, True), (Output("ps-running", "data"), True, False)]
    cb(Output("ps-run-done", "data"), Input("ps-run-request", "data"), State("build-path", "data"), background=True,
       running=jobs_running, cancel=[Input("ps-cancel", "n_clicks")], progress=[Output("ps-progress", "data")],
       prevent_initial_call=True)(ps_job)
    cb(Output("ps-validate-request", "data"), Input("ps-validate", "n_clicks"), State("ps-active", "data"),
       State("ps-dataset", "data"), State("ps-pair", "data"), State("build-path", "data"),
       State("ps-constraints", "data"), prevent_initial_call=True)(ps_validate_request)
    cb(Output("ps-validate-done", "data"), Input("ps-validate-request", "data"), State("build-path", "data"),
       background=True, running=jobs_running, cancel=[Input("ps-cancel", "n_clicks")],
       progress=[Output("ps-progress", "data", allow_duplicate=True)], prevent_initial_call=True)(ps_validate_job)
    cb(Output("ps-dataset", "data"), Output("ps-pair", "data"),
       Input({"type": "ps-strip", "dataset": ALL}, "n_clicks"), prevent_initial_call=True)(ps_pick_dataset)
    cb(Output("ps-pair", "data", allow_duplicate=True), Input("ps-heatmap", "clickData"),
       prevent_initial_call=True)(ps_pick_cell)
    cb(Output("ps-inspector", "className"), Input("ps-heatmap", "clickData"), Input("ps-inspector-close", "n_clicks"),
       prevent_initial_call=True)(ps_inspector_form)
    c_inputs = [Input(f"ps-c-{n}", "value") for n in CONSTRAINT_NAMES]
    cb(*[Output(f"ps-c-{n}-changed", "children") for n in CONSTRAINT_NAMES], Output("ps-c-confirm", "disabled"),
       Output("ps-c-unconfirmed", "children"), *c_inputs, Input("ps-constraints", "data"),
       Input("ps-dataset", "data"), Input("ps-active", "data"), State("build-path", "data"),
       Input("lang", "data"))(ps_constraint_marks)
    cb(*[Output(f"ps-pill-c-{n}", "children") for n in CONSTRAINT_NAMES], *c_inputs,
       Input("lang", "data"))(ps_constraint_pills)
    cb(Output("ps-constraints", "data", allow_duplicate=True), Input("ps-c-confirm", "n_clicks"),
       Input("ps-c-reset", "n_clicks"), *[State(f"ps-c-{n}", "value") for n in CONSTRAINT_NAMES],
       State("ps-c-scope", "value"), State("ps-constraints", "data"), State("ps-dataset", "data"),
       State("ps-active", "data"), State("build-path", "data"), prevent_initial_call=True)(ps_constraints_store)
    cb(*[Output(f"ps-c-{n}", "value") for n in CONSTRAINT_NAMES], Input("ps-constraints", "data"),
       Input("ps-dataset", "data"), State("build-path", "data"), prevent_initial_call=True)(ps_constraint_inputs)
    staged = [State("ps-s-genre", "value"), State("ps-s-defining", "value"), State("ps-s-removed", "value"),
              State("ps-s-min-months", "value"), State("ps-s-weight", "value"), State("ps-s-min-multi", "value")]
    cb(Output("ps-active", "data"), Output("ps-constraints", "data", allow_duplicate=True),
       Output("ps-pair", "data", allow_duplicate=True), Input("ps-s-use", "n_clicks"), *staged,
       State("ps-constraints", "data"), State("build-path", "data"), prevent_initial_call=True)(ps_use_settings)
    cb(Output("ps-s-genre", "value"), Output("ps-s-defining", "value"), Output("ps-s-removed", "value"),
       Output("ps-s-min-months", "value"), Output("ps-s-weight", "value"), Output("ps-s-min-multi", "value"),
       Input("ps-s-reset", "n_clicks"), Input("ps-s-copy", "n_clicks"),
       Input({"type": "ps-remove", "tag": ALL}, "n_clicks"), State("ps-s-removed", "value"),
       State("genre-hidden", "value"), State("defining-hidden", "value"), State("min-months", "value"),
       State("weight", "value"), State("removed", "data"), State("build-path", "data"),
       prevent_initial_call=True)(ps_stage_settings)
    cb(*[Output(i, "value", allow_duplicate=True) for i in CONTROL_IDS],
       Output("removed", "data", allow_duplicate=True), Output("relayout", "data", allow_duplicate=True),
       Output("rs-view", "data", allow_duplicate=True), Output("pending-open", "data", allow_duplicate=True),
       Output("verify", "data", allow_duplicate=True), Output("mode", "value"), Input("ps-apply", "n_clicks"),
       State("ps-dataset", "data"), State("ps-pair", "data"), State("ps-active", "data"),
       State("build-path", "data"), State("ps-constraints", "data"), prevent_initial_call=True)(ps_apply)
    cb(Output("ps-download", "data"), Input("ps-export", "n_clicks"), State("ps-active", "data"),
       State("ps-constraints", "data"), State("build-path", "data"), prevent_initial_call=True)(ps_export)
