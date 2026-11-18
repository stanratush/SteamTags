"""The Cluster Comparison mode: resolving each dataset's partition, the two memos, and the mode's components.

A dataset on a cell (its pick, or another selected cell) shows the cell's stored Selected Partition, read from the
Parameter Selection cache and never re-clustered. A dataset set by hand, or one with no Automatic Parameter
Selection run under the shared settings, is clustered once with the Build's main seed (`light_partition`).

The layout registers its static words for the relabel callback (`relabel.Labels`); everything `render` returns takes
the Interface Language's translator `tx`. `callbacks.py` wires it.
"""

from __future__ import annotations

import dataclasses
import json
import threading
from collections import OrderedDict
from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from dash import dcc, html

from steamstudy.app import help as H
from steamstudy.app import ps_cache
from steamstudy.app import ps_view as PV
from steamstudy.app.loader import BuildContext
from steamstudy.app.relabel import Labels, msg
from steamstudy.i18n import Text
from steamstudy.network import comparison as CMP
from steamstudy.network import comparison_text as CT
from steamstudy.network import selection as SEL
from steamstudy.network.graph import filter_games
from steamstudy.network.model import Settings
from steamstudy.network.state import light_partition

# ----------------------------------------------------------------------------- resolving a dataset


def shared_defaults(ctx: BuildContext) -> CMP.SharedSettings:
    """The mode's shared settings start from the Parameter Selection settings, never the Workbench's."""
    settings, _ = PV.defaults_of(ctx)
    return CMP.SharedSettings(settings.clustering_weight, settings.algorithm, settings.min_months,
                              settings.genre_hidden, settings.removed_tag_ids)


def selection_settings(ctx: BuildContext, shared: CMP.SharedSettings) -> SEL.SelectionSettings | None:
    """The Parameter Selection settings whose runs feed the comparison: the shared settings with each dataset's
    defining Tag hidden. None when no run can exist for them (Parameter Selection runs Leiden only)."""
    if shared.algorithm != "leiden":
        return None
    settings, _ = PV.defaults_of(ctx)
    return settings.with_(genre_hidden=tuple(shared.genre_hidden), removed_tag_ids=tuple(shared.removed_tag_ids),
                          min_months=shared.min_months, clustering_weight=shared.clustering_weight,
                          hide_defining_tag=True)


@dataclass(frozen=True)
class Request:
    """What the comparison asks of one dataset: its source and, off the pick, its values."""

    dataset: str
    source: str  # pick | cell | hand | no_run
    g: int | None = None  # cell and hand
    s: int | None = None
    resolution: float | None = None  # hand only


@dataclass(frozen=True)
class Resolved:
    """One dataset's resolved partition with the figures its row shows."""

    partition: CMP.Partition
    values: CMP.DatasetValues
    seed_noise_floor: float | None  # the run's stored floor on a cell; its own noise-seed runs otherwise
    neighbour_agreement: float | None  # the cell's; None off a cell
    state_id: str | None  # hand and no run only: rebuilds the dataset in the Workbench's terms
    # Why a dataset asked for on a cell has source no_run: "no_run" (no Automatic Parameter Selection run under the
    # shared settings), "no_pick" (a run, but no qualifying pair under its Pair Constraints) or "run_gone" (the
    # selected cell vanished: cache cleared, run changed). None otherwise.
    fallback: str | None = None

    @property
    def run_gone(self) -> bool:
        return self.fallback == "run_gone"


def resolve(ctx: BuildContext, shared: CMP.SharedSettings, request: Request, constraints: SEL.Constraints,
            cache_root: Path | None = None) -> Resolved:
    """`constraints` are the Pair Constraints set in Parameter Selection for this dataset: they fix its pick."""
    if request.source in ("pick", "cell"):
        on_cell = _on_cell(ctx, shared, request, constraints, cache_root)
        if isinstance(on_cell, Resolved):
            return on_cell
        return _off_cell(ctx, shared, Request(request.dataset, "no_run"), fallback=on_cell)
    return _off_cell(ctx, shared, request)


def _on_cell(ctx: BuildContext, shared: CMP.SharedSettings, request: Request, constraints: SEL.Constraints,
             cache_root: Path | None) -> Resolved | str:
    """The cell's stored Selected Partition, or why there is none (a `Resolved.fallback` code)."""
    settings = selection_settings(ctx, shared)
    if settings is None:
        return "no_run"
    dataset = request.dataset
    view = PV.dataset_view(ctx, settings, dataset, constraints, SEL.default_constraints(ctx.network), cache_root)
    if view.status != "complete":
        return "run_gone" if request.source == "cell" else "no_run"
    if request.source == "pick":
        if view.star is None:
            return "no_pick"
        pair = view.star
    else:
        assert request.g is not None and request.s is not None
        pair = (request.g, request.s)
    result = view.result(pair)
    if result is None or result.selected is None or result.selected_resolution is None:
        return "run_gone"
    g, s = pair
    na = view.na.get(pair)
    partition = CMP.Partition(
        dataset=dataset, clusters=tuple(SEL.clusters_of(result.nodes, result.selected)),
        edged=frozenset(result.edged), hidden=frozenset(settings.hidden_tag_ids(ctx.context(dataset))),
        games=tuple(filter_games(ctx.games(dataset), shared.min_months)), min_games_per_tag=g)
    values = CMP.DatasetValues(dataset, request.source, g, s, result.selected_resolution,
                               selection_key=settings.settings_key())
    return Resolved(partition, values, (result.seed_noise or {}).get("floor"),
                    None if na is None else na.value, None)


def network_settings(ctx: BuildContext, shared: CMP.SharedSettings, dataset: str, g: int, s: int,
                     resolution: float) -> Settings:
    """A hand-set or no-run dataset's Network State settings: the shared settings, its own defining Tag hidden,
    the Build's main seed and seed counts."""
    n = ctx.network
    defining = ctx.context(dataset).defining_tag_id
    hidden = set(shared.genre_hidden) | ({defining} if defining is not None else set())
    return Settings(build_id=ctx.build_id, dataset=dataset, min_months=shared.min_months, min_games_per_tag=g,
                    min_shared_games=s, hidden_tag_ids=tuple(hidden), removed_tag_ids=tuple(shared.removed_tag_ids),
                    clustering_weight=shared.clustering_weight, algorithm=shared.algorithm, resolution=resolution,
                    seed=n.seed, null_replicates=n.null_replicates, noise_seeds=n.noise_seeds)


def _off_cell(ctx: BuildContext, shared: CMP.SharedSettings, request: Request,
              fallback: str | None = None) -> Resolved:
    n = ctx.network
    if request.source == "hand":
        assert request.g is not None and request.s is not None and request.resolution is not None
        g, s, gamma = request.g, request.s, request.resolution
    else:
        g, s, gamma = n.min_games_per_tag, n.min_shared_games, n.resolution
    dataset = request.dataset
    settings = network_settings(ctx, shared, dataset, g, s, gamma)
    light = light_partition(ctx.games(dataset), settings, ctx.context(dataset))
    partition = CMP.Partition(dataset=dataset, clusters=tuple(light.clusters), edged=light.edged,
                              hidden=frozenset(settings.hidden_tag_ids), games=tuple(light.network.games),
                              min_games_per_tag=g)
    values = CMP.DatasetValues(dataset, request.source, g, s, settings.resolution, seed=settings.seed)
    return Resolved(partition, values, light.seed_noise_floor, None, light.state_id, fallback)


# ----------------------------------------------------------------------------- the two memos

T = TypeVar("T")
_MEMO_LOCK = threading.Lock()  # Dash may answer callbacks in threads
# (a) one resolved partition per dataset, keyed by the Build, the dataset, the shared settings, its request, the Pair
# Constraints that fix its pick and the cache's state for its run (a finished run shows on the next resolve).
PARTITIONS: OrderedDict[Hashable, Resolved] = OrderedDict()
PARTITIONS_KEPT = 32
# (b) every pair's results, keyed by `comparison_id` and the partitions themselves (a run that finishes can change a
# dataset's partition and leave its values, so its key, as they were), each unordered pair stored once.
PAIRS: OrderedDict[Hashable, dict[tuple[str, str], CMP.PairResult]] = OrderedDict()
PAIRS_KEPT = 4


def _memo(store: OrderedDict, kept: int, key: Hashable, make: Callable[[], T]) -> T:
    with _MEMO_LOCK:
        if key in store:
            store.move_to_end(key)
            return store[key]
    value = make()
    with _MEMO_LOCK:
        store[key] = value
        store.move_to_end(key)
        while len(store) > kept:
            store.popitem(last=False)
    return value


def _run_stamp(ctx: BuildContext, shared: CMP.SharedSettings, dataset: str) -> float | None:
    """When the dataset's run under the shared settings last changed (its manifest), or None without one."""
    settings = selection_settings(ctx, shared)
    if settings is None:
        return None
    manifest = ps_cache.grid_dir(ctx.app_cache, settings.grid_key(dataset, ctx.context(dataset))) / "manifest.json"
    return manifest.stat().st_mtime if manifest.is_file() else None


def resolve_memo(ctx: BuildContext, shared: CMP.SharedSettings, request: Request,
                 constraints: SEL.Constraints) -> Resolved:
    on_cell = request.source in ("pick", "cell")
    key = (ctx.build_id, str(ctx.app_cache), request.dataset, json.dumps(shared.key(), sort_keys=True),
           dataclasses.astuple(request), json.dumps(dataclasses.asdict(constraints), sort_keys=True),
           _run_stamp(ctx, shared, request.dataset) if on_cell else None)
    return _memo(PARTITIONS, PARTITIONS_KEPT, key, lambda: resolve(ctx, shared, request, constraints))


def pairs_memo(comparison_id: str, partitions: Sequence[CMP.Partition]) -> dict[tuple[str, str], CMP.PairResult]:
    key = (comparison_id, tuple((p.dataset, p.clusters, p.edged, p.hidden) for p in partitions))
    return _memo(PAIRS, PAIRS_KEPT, key, lambda: CMP.compare_all(partitions))


# ----------------------------------------------------------------------------- resolving the mode


def shared_of(weight: str | None, algorithm: str | None, min_months: Any, genre: Sequence[int] | None,
              removed: Sequence[int] | None) -> CMP.SharedSettings:
    """The header row's controls as shared settings."""
    return CMP.SharedSettings(weight or "lift", algorithm or "leiden", int(min_months or 0), tuple(genre or ()),
                              tuple(removed or ()))


def request_of(dataset: str, data: Mapping[str, Any] | None) -> Request:
    """A dataset's request from the `cc-requests` store; a dataset with no entry is on its pick."""
    if not data:
        return Request(dataset, "pick")
    return Request(dataset, data["source"], data.get("g"), data.get("s"), data.get("resolution"))


def ranked_pairs(pairs: Mapping[tuple[str, str], CMP.PairResult], order: Sequence[str]) -> list[CMP.PairResult]:
    """Every dataset pair by ARI (comparable Tags), highest first; a pair with no ARI last; ties in Build order."""
    rank = {d: i for i, d in enumerate(order)}
    return sorted(pairs.values(), key=lambda p: (p.ari is None, -(p.ari or 0.0), rank[p.dataset_a],
                                                  rank[p.dataset_b]))


def chosen_pair(ranked: Sequence[CMP.PairResult], clicked: Sequence[str] | None) -> CMP.PairResult | None:
    """The pair the user clicked while both its datasets are included, else the top pair."""
    if clicked:
        wanted = set(clicked)
        for p in ranked:
            if {p.dataset_a, p.dataset_b} == wanted:
                return p
    return ranked[0] if ranked else None


@dataclass(frozen=True)
class ComparisonResult:
    """One resolve of the mode: every dataset's partition, the included ones' pairs and the Comparison State's id."""

    resolved: dict[str, Resolved]  # every Top-N Dataset, in the Build's order
    included: list[str]
    comparison_id: str | None  # None below two included datasets
    pairs: dict[tuple[str, str], CMP.PairResult]


def resolve_all(ctx: BuildContext, shared: CMP.SharedSettings, included: Sequence[str],
                requests: Mapping[str, Any] | None, cstore: Mapping[str, Any] | None) -> ComparisonResult:
    """Resolve every dataset (its row shows its source whether included or not), then match the included ones."""
    _, default_constraints = PV.defaults_of(ctx)
    requests = requests or {}
    order = [d.key for d in ctx.datasets]
    resolved = {d: resolve_memo(ctx, shared, request_of(d, requests.get(d)),
                                PV.active_constraints(cstore, d, default_constraints)) for d in order}
    wanted = set(included)
    inc = [d for d in order if d in wanted]
    if len(inc) < 2:
        return ComparisonResult(resolved, inc, None, {})
    key = CMP.comparison_key(ctx.build_id, shared, [resolved[d].values for d in inc])
    cid = CMP.comparison_id(key)
    return ComparisonResult(resolved, inc, cid, pairs_memo(cid, [resolved[d].partition for d in inc]))


# ----------------------------------------------------------------------------- rendering

# Each dataset's colour, by its place in the Build's order (never the Workbench's Cluster colours).
DATASET_COLOURS = ("#3d4555", "#7a4fb0", "#b0503d", "#2f7d5b", "#2a6fa8", "#a8742a", "#2a8a8a", "#8a2a5c")


def colour_of(ctx: BuildContext, dataset: str) -> str:
    keys = [d.key for d in ctx.datasets]
    return DATASET_COLOURS[keys.index(dataset) % len(DATASET_COLOURS)]


def _term(text_: str, key: str, tx: Text, className: str = "term") -> html.Span:
    return html.Span(text_, className=className, tabIndex="0", **H.attrs(key, tx))


def dataset_name(ctx: BuildContext, dataset: str) -> html.Span:
    return html.Span(ctx.dataset(dataset).label, className="cc-ds", style={"color": colour_of(ctx, dataset)})


def source_view(ctx: BuildContext, r: Resolved, shared: CMP.SharedSettings, tx: Text) -> list[Any]:
    """Under a dataset's name: its source line (by Threshold Pair, with the scan-seeds note on a cell) and
    "Seed-Noise Floor · NA"."""
    v = r.values
    algorithm = "Leiden" if shared.algorithm == "leiden" else "Louvain"
    line = CT.source_line(v.source, g=v.g, s=v.s, algorithm=algorithm, fallback=r.fallback, tx=tx)
    tip = CT.scan_seeds_tip(PV.defaults_of(ctx)[0].scan_seeds, tx)
    aria: dict[str, Any] = {"aria-label": tip}
    note = [html.Span(" ⓘ", className="mute", title=tip, tabIndex="0", **aria)] if v.on_cell else []
    floor, na = CT.figures_parts(r.seed_noise_floor, r.neighbour_agreement, tx)
    return [html.Div([_term(line, f"comparison.source.{v.source}", tx, "term cc-source"), *note]),
            html.Div([_term(floor, "comparison.seed_noise", tx), " · ", _term(na, "comparison.neighbour_agreement", tx)],
                     className="cc-figures mute")]


def _bar(value: float | None) -> html.Span:
    return html.Span(className="cc-bar", style={"width": f"{max(0.0, value or 0.0) * 60:.0f}px"})


def _pct(value: float | None, tx: Text) -> str:
    return "—" if value is None else tx.pct(value, 0)


def pair_rows(ctx: BuildContext, ranked: Sequence[CMP.PairResult], chosen: CMP.PairResult | None,
              tx: Text) -> list[Any]:
    """The Dataset pairs list: one clickable row per pair, ranked by ARI."""
    rows = []
    for p in ranked:
        a, b = ctx.dataset(p.dataset_a).label, ctx.dataset(p.dataset_b).label
        ari = "—" if p.ari is None else tx.num(p.ari, 2)
        coverage = tx.n(p.n_comparable, one="{n} Comparable Tag: {share_a} of {a}'s, {share_b} of {b}'s",
                        other="{n} Comparable Tags: {share_a} of {a}'s, {share_b} of {b}'s",
                        share_a=_pct(p.comparable_share_a, tx), a=a, share_b=_pct(p.comparable_share_b, tx), b=b)
        games = tx.n(p.n_games_in_common, one="{n} game in common", other="{n} games in common")
        on = chosen is not None and (p.dataset_a, p.dataset_b) == (chosen.dataset_a, chosen.dataset_b)
        rows.append(html.Button([
            html.Div([dataset_name(ctx, p.dataset_a), " × ", dataset_name(ctx, p.dataset_b)], className="cc-pair-name"),
            html.Div([_term("ARI", "comparison.ari", tx), " ", _bar(p.ari), html.B(ari)], className="cc-pair-ari"),
            html.Div(_term(coverage, "comparison.comparable_tags", tx), className="small"),
            html.Div(_term(games, "comparison.games_in_common", tx), className="small mute"),
        ], id={"type": "cc-pair", "a": p.dataset_a, "b": p.dataset_b}, className="cc-pair" + (" on" if on else ""),
            n_clicks=0))
    return rows


def main_view(ctx: BuildContext, result: ComparisonResult, chosen: CMP.PairResult | None, tx: Text) -> list[Any]:
    """The main column: the chosen pair's title, or the empty state. The diagram and the match detail follow (issues
    19 and 20)."""
    if result.comparison_id is None:
        return [html.P(tx(CT.FEWER_THAN_TWO), className="cc-empty")]
    if chosen is None:
        return []
    return [html.H3([dataset_name(ctx, chosen.dataset_a), " × ", dataset_name(ctx, chosen.dataset_b)],
                    className="cc-title"),
            html.Div(id="cc-diagram", className="cc-diagram")]


RENDER_OUTPUTS = ("sources", "g", "s", "resolution", "pairs", "comparison_id", "main", "pill_datasets", "pill_pairs",
                  "shown")


def render(ctx: BuildContext, shared: CMP.SharedSettings, included: Sequence[str], requests: Mapping[str, Any] | None,
           clicked: Sequence[str] | None, cstore: Mapping[str, Any] | None, *, tx: Text) -> dict[str, Any]:
    """Everything the mode shows, by `RENDER_OUTPUTS` name; the per-dataset lists are in the Build's order."""
    result = resolve_all(ctx, shared, included, requests, cstore)
    order = [d.key for d in ctx.datasets]
    ranked = ranked_pairs(result.pairs, order)
    chosen = chosen_pair(ranked, clicked)
    values = [result.resolved[d].values for d in order]
    return {
        "sources": [source_view(ctx, result.resolved[d], shared, tx) for d in order],
        "g": [v.g for v in values], "s": [v.s for v in values],
        "resolution": [float(f"{v.resolution:.2f}") for v in values],
        "pairs": (pair_rows(ctx, ranked, chosen, tx) if result.comparison_id
                  else [html.P(tx(CT.FEWER_THAN_TWO), className="cc-empty small")]),
        "comparison_id": result.comparison_id or "—",
        "main": main_view(ctx, result, chosen, tx),
        "pill_datasets": tx("{n} of {total}", n=len(result.included), total=len(order)),
        "pill_pairs": ([dataset_name(ctx, chosen.dataset_a), " × ", dataset_name(ctx, chosen.dataset_b)]
                       if chosen else "—"),
        # what the mode shows now, for the issues that follow (diagram, export): the id and the chosen pair
        "shown": {"comparison_id": result.comparison_id,
                  "pair": [chosen.dataset_a, chosen.dataset_b] if chosen else None},
    }


# ----------------------------------------------------------------------------- the layout


def _static_help(L: Labels, key: str) -> html.Span:
    return html.Span("?", className="ps-q term", tabIndex="0", **L.help(key))


def _pill(L: Labels, pill: str, label: str, key: str, section: html.Div) -> html.Div:
    """A sidebar section: inline at wide, a pill with its popover in the pill bar at medium and narrow (the
    Workbench's forms apply: the root keeps the workbench class)."""
    btn_id = f"cc-pill-btn-{pill}"
    attrs: dict[str, Any] = {"data-pill": pill, "data-tip": L.prop(btn_id, "data-tip", lambda tx: H.tip(key, tx))}
    return html.Div([
        html.Button([L.span(label), " ", html.B("", id=f"cc-pill-{pill}", className="num")], id=btn_id,
                    className="pill-btn", **attrs),
        html.Div(section, className="pill-pop"),
    ], className="ctl-item")


def _value_input(field: str, dataset: str, step: float) -> dcc.Input:
    # Read-only until issue 21 (editing in the row).
    return dcc.Input(id={"type": f"cc-{field}", "dataset": dataset}, type="number", step=step, readOnly=True,
                     className="cc-num")


def dataset_rows(L: Labels, ctx: BuildContext) -> html.Div:
    """One row per Top-N Dataset: include, its name in its colour, g, s and γ, then its source and figures."""
    head = html.Div([html.Span(), html.Span(), html.Span("g", className="n"), html.Span("s", className="n"),
                     html.Span("γ", className="n")], className="cc-row cc-row-head small mute")
    rows = [head]
    for d in ctx.datasets:
        rows.append(html.Div([
            dcc.Checklist(id={"type": "cc-include", "dataset": d.key}, options=[{"label": "", "value": d.key}],
                          value=[d.key], className="check cc-include"),
            dataset_name(ctx, d.key),
            _value_input("g", d.key, 1), _value_input("s", d.key, 1), _value_input("resolution", d.key, 0.01),
            html.Div(id={"type": "cc-source", "dataset": d.key}, className="cc-row-source small"),
        ], className="cc-row"))
    return html.Div(rows, className="cc-rows")


def shared_row(L: Labels, ctx: BuildContext, shared: CMP.SharedSettings) -> html.Div:
    """The header's one row of shared settings, from the Parameter Selection settings."""
    field = ctx.read(ctx.datasets[0].key).filter_field
    genre = [{"label": t.name, "value": t.id} for t in ctx.genre_tags]
    names = PV.tag_names(ctx)
    months = ([html.Label(L.term(msg("Minimum Months Filter") if field.label == "Minimum Months Filter"
                                 else field.label, "control.min-months"), className="l"),
               dcc.Input(id="cc-s-min-months", type="number", min=int(field.minimum), max=int(field.maximum), step=1,
                         value=shared.min_months, debounce=True, className="cc-num")] if field else
              [html.Div(dcc.Input(id="cc-s-min-months", type="number", value=shared.min_months),
                        style={"display": "none"})])
    return html.Div([
        html.Div([html.Label(L.term(msg("Clustering weight"), "control.weight"), className="l"),
                  dcc.RadioItems(id="cc-s-weight", options=L.options("cc-s-weight", [
                      ("lift", msg("Lift")), ("shared_games", msg("Shared games"))]), value=shared.clustering_weight,
                                 className="seg", inline=True)], className="cc-field"),
        html.Div([html.Label(L.term(msg("Clustering algorithm"), "control.algorithm"), className="l"),
                  dcc.RadioItems(id="cc-s-algorithm", options=[{"label": "Leiden", "value": "leiden"},
                                                               {"label": "Louvain", "value": "louvain"}],
                                 value=shared.algorithm, className="seg", inline=True)], className="cc-field"),
        html.Div(months, className="cc-field"),
        html.Div([html.Label(L.term(msg("Hidden Genre Tags"), "comparison.shared_settings"), className="l"),
                  dcc.Checklist(id="cc-s-genre", options=genre, value=list(shared.genre_hidden), inline=True,
                                className="chips")], className="cc-field cc-genre"),
        html.Div([html.Label(L.term(msg("Removed tags"), "comparison.shared_settings"), className="l"),
                  dcc.Dropdown(id="cc-s-removed", options=[{"label": n, "value": t} for t, n in
                                                           sorted(names.items(), key=lambda x: x[1])],
                               value=list(shared.removed_tag_ids), multi=True, className="cc-removed",
                               placeholder=L.prop("cc-s-removed", "placeholder", msg("no removed tags")))],
                 className="cc-field"),
    ], className="cc-shared")


def mode_layout(ctx: BuildContext, L: Labels) -> html.Div:
    shared = shared_defaults(ctx)
    head = html.Div([
        html.Div([html.B(L.span(msg("Shared settings"))), " ", _static_help(L, "comparison.shared_settings")],
                 className="cc-head-title"),
        shared_row(L, ctx, shared),
        html.Div([html.Span("comparison_id", className="term mute small", tabIndex="0",
                            **L.help("comparison.comparison_id")), " ", html.Code("—", id="cc-comparison-id")],
                 className="cc-id"),
        html.Div(id="cc-export-slot", className="cc-export-slot"),  # Export CSV (issue 23)
    ], className="cc-head")
    sidebar = html.Div([
        html.Div([html.B(L.span(msg("Cluster Comparison"))), " ", _static_help(L, "comparison.mode")],
                 className="ctl-title"),
        _pill(L, "datasets", msg("Datasets"), "comparison.datasets", html.Div([
            html.H4([L.span(msg("Datasets")), " ", _static_help(L, "comparison.datasets")], className="ctl-h"),
            dataset_rows(L, ctx)], className="ctl-section")),
        _pill(L, "pairs", msg("Dataset pairs"), "comparison.pairs", html.Div([
            html.H4([L.span(msg("Dataset pairs")), " ", _static_help(L, "comparison.pairs")], className="ctl-h"),
            html.Div(id="cc-pairs", className="cc-pairs")], className="ctl-section")),
    ], id="cc-sidebar", className="controls cc-sidebar")
    main = html.Div(id="cc-main", className="main cc-main")
    # Over the whole mode while the comparison resolves (callbacks.py `running`): the previous view dims under it.
    busy = html.Div(html.Div(html.Span(L.prop("cc-busy", "children", msg("Comparing Clusters…")), id="cc-busy",
                                       hidden=True), className="busy", role="status"), className="ps-busy cc-busy")
    stores = [dcc.Store(id="cc-requests", data={}), dcc.Store(id="cc-pair"), dcc.Store(id="cc-shown")]
    return html.Div([*stores, head, sidebar, main, busy], id="cc-body", className="cc-body")
