"""The app's callbacks. The server is stateless: every settings change recomputes the whole Network State
from the loaded dataset; the browser holds only plain data in dcc.Store components. The only memory is a
small memo of recent layouts (`LAYOUTS`), a pure function of the inputs it is keyed by.

Functions are module-level so background jobs (Removal Sensitivity) can import them in a spawned process.
"""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from collections import OrderedDict
from typing import Any

import dash
import networkx as nx
from dash import ALL, ClientsideFunction, Input, Output, Patch, State, ctx, html, no_update
from dash.exceptions import PreventUpdate

from steamstudy.app import help as H
from steamstudy.app import rs_cache
from steamstudy.app import view as V
from steamstudy.app.export import BuildNotFound, OpenRefused, export_zip, open_export
from steamstudy.app.guide import PANEL_SECTIONS, help_markdown_at
from steamstudy.app.layout import PILLS, SLIDERS, block_styles, root_class
from steamstudy.app.loader import BuildContext, load_build
from steamstudy.app import renderer as R
from steamstudy.app.renderer import cluster_color
from steamstudy.network.cluster import Cluster
from steamstudy.network.graph import filter_games
from steamstudy.network.layout import (REFERENCE_CANVAS, Canvas, Layout, LayoutInput, lay_out, label_width,
                                      layout_input, restore, tidy)
from steamstudy.network.model import Settings, resolution_text
from steamstudy.network.sensitivity import removal_sensitivity
from steamstudy.network.state import compute_state
from steamstudy.network.tables import state_tables
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
    return 0.1 <= value <= 3.0


# ----------------------------------------------------------------------------- 1. dataset change


def on_dataset(dataset: str, build_path: str, pending: dict | None):
    c = load_build(build_path)
    defining = c.dataset(dataset).defining_tag
    options = [{"label": f"hide defining tag ({defining.name})" if defining else "no defining tag", "value": 1,
                "disabled": defining is None}]
    if pending and pending.get("dataset") == dataset:
        return options, pending["defining-hidden"], pending["removed"]
    hidden = c.default_settings(dataset).hidden_tag_ids
    return options, ([1] if defining is not None and defining.id in hidden else []), []


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


def recompute(build_path, dataset, min_games, min_shared, min_months, genre_hidden, defining_hidden, weight,
              algorithm, gamma, seed, removed, verify):
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
    meta = {"state_id": state.state_id, "key": settings.key(), "n_nodes": len(state.nodes),
            "clustering_seconds": state.clustering_seconds, "k": k, "gamma": gamma_text, "dataset": dataset,
            "weight": settings.clustering_weight}
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
        "max_shared": max([e.shared for e in state.network.edges] + [1]),
    }
    legend: list[Any] = [html.Span("Key", className="lkey term", tabIndex="0", **H.attrs("legend.key"))] + [
        html.Button([html.Span(className="sw", style={"background": cluster_color(r["cluster"], r["kind"])}),
                     f"{r['cluster']} · {r['size']}"], id={"type": "legend", "cluster": r["cluster"]}, className="lchip",
                    title="Select this cluster")
        for r in tables["clusters.csv"] if r["kind"] == "multi_tag"]
    n_one = sum(r["kind"] == "one_tag" for r in tables["clusters.csv"])
    if n_one:
        legend.append(html.Span([html.Span(className="sw", style={"background": R.ONE_TAG_COLOR}), f"{n_one} one-tag"],
                                className="lchip static term", tabIndex="0", **H.attrs("legend.one_tag")))
    banners = []
    if c.mode == "test":
        banners.append(html.Div("mode: test — this Build comes from a test Snapshot; never publish it.", className="banner"))
    mismatches = version_mismatches(c.build_json.get("software_versions") or {})
    if mismatches:
        banners.append(html.Div("Library versions differ from the ones this Build was made with, so numbers may "
                                "differ from the Build's: " + "; ".join(f"{lib} {then} (Build) vs {now} (installed)"
                                                                        for lib, then, now in mismatches) + ".",
                                className="banner"))
    if c.build_json.get("parse_errors_allowed"):
        banners.append(html.Div(f"parse_errors_allowed — this Build was made with --allow-parse-errors "
                                f"({c.build_json.get('parse_error_count')} errors); never publish it.", className="banner"))
    names = {**{t.id: t.name for t in c.genre_tags}, **state.network.tag_names}
    restore = [{"label": f"{names.get(t, t)} ({t})", "value": t} for t in settings.removed_tag_ids]
    verify_text: Any = no_update
    verify_out: Any = no_update
    if verify and verify.get("expected"):
        ok = state.state_id == verify["expected"]
        verify_text = f"Opened state {verify['expected']}: recomputed state_id {state.state_id} {'✓' if ok else '✗'}"
        verify_out = {"expected": None}
    rows_total = len(c.rows(dataset))
    defining_ref = c.dataset(dataset).defining_tag
    summary = V.state_table(settings.key(), state.state_id, c.dataset(dataset).label, state.network.n_games, rows_total,
                            {**names, **({defining_ref.id: defining_ref.name} if defining_ref else {})})
    filters = html.P(f"Minimum games per tag {settings.min_games_per_tag}, minimum shared games "
                     f"{settings.min_shared_games}, Minimum Months Filter {settings.min_months}. "
                     f"{len(tables['not_in_network.csv'])} tags of the dataset are not in the network; every one is "
                     f"listed below with all its reasons.")
    estimate = (f"Estimate: {len(state.nodes)} tags × {state.clustering_seconds * 1000:.0f} ms (one clustering) "
                f"≈ {len(state.nodes) * state.clustering_seconds:.1f} s, plus about 4 s job start-up")
    export_summary = html.P([html.Span("Export", className="term", tabIndex="0", **H.attrs("export.zip")),
                             f": steamstudy_{dataset}_{state.state_id}_<UTC timestamp>.zip, with every table above, "
                             f"export.json with the full state key and provenance, and Removal Sensitivity results "
                             f"for this exact state if any."])
    defining = c.dataset(dataset).defining_tag
    sentence = V.state_sentence(c.dataset(dataset).label, rows_total, settings,
                                [str(names.get(t, t)) for t in settings.hidden_tag_ids],
                                defining.name if defining else None,
                                [str(names.get(t, t)) for t in settings.removed_tag_ids], state.state_id)
    return (meta, store_tables, base, legend, V.summary_row(q, rows_total, gamma_text, settings.null_replicates), sentence,
            V.quality_boxes(q, gamma_text, k, settings.null_replicates),
            V.grid_rows(tables["not_in_network.csv"]), V.grid_rows(tables["nodes.csv"]), V.grid_rows(edges_view),
            V.grid_rows(tables["clusters.csv"]), V.grid_rows(tables["cluster_connections.csv"]),
            V.grid_rows(tables["null_model.csv"]), V.grid_rows(tables["seed_noise.csv"]),
            banners, restore, verify_text, verify_out, summary, filters, estimate, export_summary, "",
            V.search_options(store_tables, settings.min_games_per_tag))


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
    the canvas the browser reports (exports use the reference canvas)."""
    if not base:
        raise PreventUpdate
    layout = cached_layout(base, layout_mode, relayout_store, canvas)
    regions: list[dict[str, Any]] = []
    positions, zoom = layout.positions, layout.zoom
    if layout_mode == "separated":
        zoom = layout.separated_zoom
        positions = layout.separated
        regions = [dict(r) for r in layout.regions]
        for r in regions:
            r["color"] = R.REGION_COLOR if r["cluster"] == "one_tag_pool" else cluster_color(r["cluster"], "multi_tag")
    return R.payload(base["nodes"], base["edges"], {str(t): list(p) for t, p in positions.items()},
                     dataset=base["dataset"], layout=layout_mode, regions=regions, selection=selection,
                     max_shared=base["max_shared"], basis=base["basis"], zoom=zoom)


def show_selection(selection):
    """Tell the canvas about a new selection without resending the elements; a cluster is also zoomed to."""
    patch = Patch()
    patch["selected"] = R.selection_ref(selection)
    if selection and selection.get("kind") == "cluster":
        patch["view"] = {"cmd": "focus", "cluster": selection["id"], "nonce": time.time()}
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


def select(event, _legend, cluster_rows, rs_rows, node_rows, panels, search=None):
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
    elif isinstance(trigger, dict) and trigger.get("type") == "legend":
        if not ctx.triggered[0]["value"]:
            raise PreventUpdate  # the legend was re-rendered, not clicked
        sel = {"kind": "cluster", "id": trigger["cluster"]}
    elif trigger == "clusters-grid" and cluster_rows:
        sel = {"kind": "cluster", "id": cluster_rows[0]["cluster"]}
    elif trigger in ("rs-grid", "nodes-grid"):
        rows = rs_rows if trigger == "rs-grid" else node_rows
        if rows:
            sel = {"kind": "node", "id": str(rows[0]["tag_id"])}
    if sel is None:
        raise PreventUpdate
    return sel, True  # opens the floating Inspector wherever the Inspector is not docked


def inspect(selection, meta, rs_view, build_path, dataset, min_months):
    """The Inspector for a selection. The request carries only the state's id; its tables stay on the server."""
    tables = tables_of(meta, build_path) if meta else None
    return inspector(selection, tables, rs_view, build_path, dataset, min_months, meta)


def inspector(selection, tables, rs_view, build_path, dataset, min_months, meta):
    hide = {"display": "none"}
    if not selection or not tables:
        return [html.P("Click a node, an edge or a cluster (legend or Clusters table) to inspect it.")], hide, hide
    weight = (meta or {}).get("weight", "shared_games")
    if selection["kind"] == "nin":
        row = next((r for r in tables["nin"] if str(r["tag_id"]) == selection["id"]), None)
        if row is not None:
            return V.nin_inspector(row, (meta or {})["key"]["min_games_per_tag"]), hide, hide
        selection = {"kind": "node", "id": selection["id"]}  # it has come back into the network
    if selection["kind"] == "node":
        node = next((r for r in tables["nodes"] if str(r["tag_id"]) == selection["id"]), None)
        if node is None:
            return [html.P("This tag is not in the current network.")], hide, hide
        size = next(r["size"] for r in tables["clusters"] if r["cluster"] == node["cluster"])
        rs_row, stale = None, False
        if rs_view and rs_view.get("rows"):
            rs_row = next((r for r in rs_view["rows"] if str(r["tag_id"]) == selection["id"]), None)
            stale = rs_view.get("state_id") != (meta or {}).get("state_id")
        show = {"display": "inline-block"}
        kind = next(r["kind"] for r in tables["clusters"] if r["cluster"] == node["cluster"])
        games = V.tag_games(load_build(build_path).games(dataset), int(min_months), int(node["tag_id"]))
        return (V.node_inspector(node, weight, rs_row, size, stale, games, V.connected_tags(tables, node["tag_id"]),
                                 cluster_color(node["cluster"], kind)), show, show)
    if selection["kind"] == "edge":
        u, v = int(selection["source"]), int(selection["target"])
        edge = next((r for r in tables["edges"] if r["source_tag_id"] == min(u, v) and r["target_tag_id"] == max(u, v)), None)
        if edge is None:
            return [html.P("This edge is not in the current network.")], hide, hide
        c = load_build(build_path)
        games = [{"appid": g.appid, "name": g.name, "rank": g.rank}
                 for g in filter_games(c.games(dataset), int(min_months)) if u in g.tag_ids and v in g.tag_ids]
        return V.edge_inspector(edge, games), hide, hide
    cluster = next((r for r in tables["clusters"] if r["cluster"] == selection["id"]), None)
    if cluster is None:
        return [html.P("This cluster is not in the current partition.")], hide, hide
    by_id = {r["tag_id"]: r for r in tables["nodes"]}
    members = [by_id[t] for t in cluster["member_tag_ids"] if t in by_id]
    return V.cluster_inspector(cluster, members, weight, cluster_color(cluster["cluster"], cluster["kind"])), hide, hide


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
    set_progress(({"done": 0, "total": total if tags is None else 1}, "starting…"))

    def progress(done: int, todo: int) -> None:
        set_progress(({"done": done, "total": todo}, f"{done} of {todo}"))

    removal_sensitivity(state, tags, skip=skip, progress=progress,
                        on_row=lambda row: rs_cache.add_row(c.app_cache, settings.key(), total, row))
    return request["nonce"]


def progress_display(data, _request, _cancel):
    if ctx.triggered_id in ("rs-request", "rs-cancel") or not data:
        return "0", "1"
    return str(data["done"]), str(max(data["total"], 1))


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


def show_rs(rs_view, beyond, cluster, tables, meta):
    if not meta or not tables:
        raise PreventUpdate
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
    noise = (f"Compare each agreement after removal with the Seed-Noise Floor: ARI min {V.num(q['seed_ari_min'])} "
             f"over K = {meta['k']} noise seeds (all its numbers are in Cluster quality).")
    banner, banner_style = "", {"display": "none"}
    total = (rs_view or {}).get("total") or meta["n_nodes"]
    done = len(rows)
    if rows and not current:
        banner, banner_style = "Stale: these results belong to other settings. Run again for the current state.", {}
    elif rs_view and rs_view.get("from_export"):
        banner, banner_style = "Loaded from export (not rerun).", {}
    elif rows and done < total:
        banner, banner_style = f"Partial result: {done} of {total} tags.", {}
    flagged = sum(1 for r in rows if r["rc_ari_beyond_noise"])
    footer = V.chance_footer(flagged, done, meta["k"]) if rows else "Not run for this state."
    continue_style = {"display": "inline-block"} if current and 0 < done < total else {"display": "none"}
    clusters = sorted({r["cluster"] for r in rows}, key=lambda s: int(s[1:]))
    return (V.grid_rows(view_rows), "" if current or not rows else "stale", banner, banner_style, footer, noise,
            continue_style, f"Continue ({done} of {total} done)", [{"label": c, "value": c} for c in clusters])


# ----------------------------------------------------------------------------- 7. export, open, cache, help


def do_export(_a, _b, build_path, meta, relayout_store, base, rs_view):
    if not meta:
        raise PreventUpdate
    c = load_build(build_path)
    settings = Settings.from_key(meta["key"])
    tidied = relayout_positions(base, relayout_store) if base else None
    positions = tidied[0] if tidied else None
    rows = None
    if rs_view and rs_view.get("rows") and rs_view.get("state_id") == meta["state_id"] and not rs_view.get("stale"):
        rows = rs_view["rows"]  # only results under the exact current key; stale results are never exported
    filename, data = export_zip(c, settings, relayout_positions=positions, removal_rows=rows)
    return dash.dcc.send_bytes(data, filename)


def do_open(contents, filename, builds_root):
    """Open Network State…: the export's Build is found by identity among the Builds this app can see."""
    if not contents:
        raise PreventUpdate
    data = base64.b64decode(contents.split(",", 1)[1])
    nothing = [no_update] * 16
    try:
        opened = open_export(data, builds_root=builds_root)
    except BuildNotFound as exc:
        return [*nothing, f"Refused: {exc}."]
    except OpenRefused as exc:
        return [*nothing, f"Refused: {exc}"]
    c = load_build(opened.build_path)
    values = controls_from_settings(c, opened.settings)
    basis = [opened.settings.dataset, opened.settings.min_months, opened.settings.clustering_weight, opened.settings.seed]
    relayout_store = ({"basis": basis, "positions": {str(k): list(v) for k, v in opened.relayout_positions.items()},
                       "restore": True} if opened.relayout_positions else None)
    rs_view = ({"state_id": opened.recorded_state_id, "rows": opened.removal_rows, "done": len(opened.removal_rows),
                "total": opened.removal_total or len(opened.removal_rows), "from_export": True}
               if opened.removal_rows else None)
    pending = {"dataset": values["dataset"], "defining-hidden": values["defining-hidden"], "removed": values["removed"]}
    message = (f"Opened {filename}: Build {c.build_id}, state {opened.recorded_state_id} "
               f"(schema_version {opened.schema_version}).")
    return [str(opened.build_path), *[values[k] for k in CONTROL_IDS], values["removed"], relayout_store, rs_view,
            pending, {"expected": opened.recorded_state_id}, message]


def clear_cache(_n, build_path):
    if not _n:
        raise PreventUpdate
    removed = rs_cache.clear(load_build(build_path).app_cache)
    return f"Cleared {removed} cached Removal Sensitivity result(s).", None


def show_help(_clicks, _close, target=None, _back=None, history=None):
    """The help modal: a panel's `?` opens its guide section; a metric or control (workbench.js sets `help-target`
    to `<file>#<anchor>`) opens its own entry. A guide link inside the modal (`follow`) opens its target on top of
    the history, which ← Back walks down and closing clears."""
    trigger = ctx.triggered_id
    history = list(history or [])
    if trigger == "help-target":
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
    return ({"display": "flex", "width": "560px"}, help_markdown_at(file, anchor or None), history,
            {"display": "inline-block" if len(history) > 1 else "none"})


# ----------------------------------------------------------------------------- registration


def register(app: dash.Dash) -> None:
    cb = app.callback
    cb(Output("defining-hidden", "options"), Output("defining-hidden", "value", allow_duplicate=True),
       Output("removed", "data", allow_duplicate=True),
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
       Output("error-message", "children"), Output("tag-search", "options"),
       Input("build-path", "data"), Input("dataset", "value"), Input("min-games", "value"),
       Input("min-shared", "value"), Input("min-months", "value"), Input("genre-hidden", "value"),
       Input("defining-hidden", "value"), Input("weight", "value"), Input("algorithm", "value"),
       Input("gamma", "value"), Input("seed", "value"), Input("removed", "data"), State("verify", "data"),
       prevent_initial_call="initial_duplicate")(recompute)
    cb(Output(R.DATA_ID, "data"), Input("elements-base", "data"), Input("layout-mode", "value"),
       Input("relayout", "data"), State("selection", "data"), Input(R.CANVAS_ID, "data"))(render_graph)
    cb(Output(R.DATA_ID, "data", allow_duplicate=True), Input("selection", "data"),
       prevent_initial_call=True)(show_selection)
    app.clientside_callback(R.RENDER, Output(R.ACK_ID, "data"), Input(R.DATA_ID, "data"))
    cb(Output("relayout", "data", allow_duplicate=True), Input("relayout-btn", "n_clicks"),
       State("elements-base", "data"), State("relayout", "data"), State(R.CANVAS_ID, "data"),
       State(R.DRAGGED_ID, "data"), prevent_initial_call=True)(do_tidy)
    cb(Output("selection", "data"), Output("floating-open", "data", allow_duplicate=True),
       Input(R.EVENT_ID, "data"),
       Input({"type": "legend", "cluster": ALL}, "n_clicks"), Input("clusters-grid", "selectedRows"),
       Input("rs-grid", "selectedRows"), Input("nodes-grid", "selectedRows"),
       State("panels", "value"), Input("tag-search", "value"), prevent_initial_call=True)(select)
    cb(Output("tag-search", "value", allow_duplicate=True), Input("tag-search", "value"),
       prevent_initial_call=True)(lambda v: None if v else no_update)  # ready for the next pick
    cb(Output("removed", "data", allow_duplicate=True), Output("genre-hidden", "value", allow_duplicate=True),
       Output("defining-hidden", "value", allow_duplicate=True), Output("selection", "data", allow_duplicate=True),
       Input({"type": "nin-action", "action": ALL}, "n_clicks"), State("selection", "data"),
       State("removed", "data"), State("genre-hidden", "value"), State("defining-hidden", "value"),
       State("build-path", "data"), State("dataset", "value"), prevent_initial_call=True)(on_nin_action)
    cb(Output("inspector-body", "children"), Output("remove-btn", "style"), Output("rs-run-tag", "style"),
       Input("selection", "data"), Input("state-meta", "data"), Input("rs-view", "data"),
       State("build-path", "data"), State("dataset", "value"), State("min-months", "value"))(inspect)
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
        Input("algorithm", "value"), Input("gamma", "value"), Input("seed", "value"),
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
       progress=[Output("rs-progress-store", "data"), Output("rs-progress-label", "children")],
       prevent_initial_call=True)(rs_job)
    cb(Output("rs-progress", "value"), Output("rs-progress", "max"), Input("rs-progress-store", "data"),
       Input("rs-request", "data"), Input("rs-cancel", "n_clicks"))(progress_display)
    cb(Output("rs-view", "data", allow_duplicate=True), Input("state-meta", "data"), Input("rs-done", "data"),
       State("rs-view", "data"), State("build-path", "data"), prevent_initial_call="initial_duplicate")(refresh_rs_view)
    cb(Output("rs-grid", "rowData"), Output("rs-grid-wrap", "className"), Output("rs-banner", "children"),
       Output("rs-banner", "style"), Output("rs-footer", "children"), Output("noise-line-rs", "children"),
       Output("rs-continue", "style"), Output("rs-continue", "children"), Output("rs-cluster", "options"),
       Input("rs-view", "data"), Input("rs-beyond", "value"), Input("rs-cluster", "value"),
       Input("state-tables", "data"), Input("state-meta", "data"))(show_rs)
    cb(Output("download", "data"), Input("export-btn", "n_clicks"), Input("export-btn-report", "n_clicks"),
       State("build-path", "data"), State("state-meta", "data"), State("relayout", "data"),
       State("elements-base", "data"), State("rs-view", "data"), prevent_initial_call=True)(do_export)
    cb(Output("build-path", "data"), *[Output(i, "value", allow_duplicate=True) for i in CONTROL_IDS],
       Output("removed", "data", allow_duplicate=True), Output("relayout", "data", allow_duplicate=True),
       Output("rs-view", "data", allow_duplicate=True), Output("pending-open", "data"),
       Output("verify", "data", allow_duplicate=True), Output("open-message", "children"),
       Input("open-upload", "contents"), State("open-upload", "filename"), State("builds-root", "data"),
       prevent_initial_call=True)(do_open)
    cb(Output("cache-message", "children"), Output("rs-view", "data", allow_duplicate=True),
       Input("clear-cache-btn", "n_clicks"), State("build-path", "data"), prevent_initial_call=True)(clear_cache)
    cb(Output("help-modal", "style"), Output("help-body", "children"), Output("help-history", "data"),
       Output("help-back", "style"),
       Input({"type": "help", "panel": ALL}, "n_clicks"), Input("help-close", "n_clicks"),
       Input("help-target", "data"), Input("help-back", "n_clicks"), State("help-history", "data"),
       prevent_initial_call=True)(show_help)
