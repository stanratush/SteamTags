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


# ----------------------------------------------------------------------------- editing a dataset's row


def value_limits(ctx: BuildContext) -> tuple[int, int]:
    """The tops of g and s in a dataset row: the Workbench's sliders' (never the Parameter Grid's); both start at 1,
    and γ takes two decimals from 0.01 up."""
    from steamstudy.app.layout import slider_tops  # layout imports this module

    return slider_tops(ctx)


def valid_values(ctx: BuildContext, g: Any, s: Any, gamma: Any) -> bool:
    """Whether typed values are within the Workbench's limits (refused otherwise, as the Workbench refuses them)."""
    try:
        gi, si, r = int(g), int(s), float(gamma)
    except (TypeError, ValueError):
        return False
    g_top, s_top = value_limits(ctx)
    return gi == float(g) and si == float(s) and 1 <= gi <= g_top and 1 <= si <= s_top and r >= 0.01


def shown_gamma(resolution: float) -> float:
    """γ as a dataset row shows it: two decimals."""
    return float(f"{resolution:.2f}")


def cell_source(ctx: BuildContext, shared: CMP.SharedSettings, dataset: str, constraints: SEL.Constraints, g: int,
                s: int, cache_root: Path | None = None) -> str | None:
    """"pick" when (g, s) is the dataset's pick, "cell" when it is another cell with a Selected Partition, None when
    the run has no Selected Partition there (or there is no run)."""
    settings = selection_settings(ctx, shared)
    if settings is None:
        return None
    view = PV.dataset_view(ctx, settings, dataset, constraints, SEL.default_constraints(ctx.network), cache_root)
    if view.status != "complete":
        return None
    if view.star == (g, s):
        return "pick"
    result = view.result((g, s))
    return "cell" if result is not None and result.selected is not None else None


def edited(ctx: BuildContext, shared: CMP.SharedSettings, dataset: str, constraints: SEL.Constraints,
           current: Sequence[Any], g: Any, s: Any, gamma: Any) -> dict[str, Any] | None:
    """A dataset's new `cc-requests` entry after an edit in its row, or None (nothing changed, or out of limits).

    `current` is the row's (g, s, γ) as shown. Editing γ makes the dataset set by hand (γ as typed); g and s that name
    a cell with a Selected Partition select that cell (γ follows), and any other pair is set by hand."""
    if not valid_values(ctx, g, s, gamma):
        return None
    g, s, gamma = int(g), int(s), round(float(gamma), 2)
    if [g, s, gamma] == [current[0], current[1], current[2]]:
        return None
    if gamma != current[2]:
        return {"source": "hand", "g": g, "s": s, "resolution": gamma}
    source = cell_source(ctx, shared, dataset, constraints, g, s)
    if source == "pick":
        return {"source": "pick"}
    if source == "cell":
        return {"source": "cell", "g": g, "s": s}
    return {"source": "hand", "g": g, "s": s, "resolution": gamma}


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
    # The row's route to Parameter Selection on this dataset (callbacks.py `cc_open_ps`).
    link = html.Button(CT.open_parameter_selection(tx), id={"type": "cc-open-ps", "dataset": v.dataset}, n_clicks=0,
                       className="link small")
    return [html.Div([_term(line, f"comparison.source.{v.source}", tx, "term cc-source"), *note, " · ", link]),
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


# ----------------------------------------------------------------------------- the link diagram

MINIMUM_DEFAULT = 0.10  # the Minimum Match Jaccard when the mode first opens


@dataclass(frozen=True)
class DiagramView:
    """The main column's view choices: never in the Comparison State key, and nothing is recomputed for them.

    `orient` is the chosen pair as shown, A first (⇄). `focus` (the clicked Cluster box) and `match` (the chosen
    Cluster Match) are recorded with the `comparison_id` and the pair, in the Build's order, they were made on, and
    are ignored once either changes; a match is kept in the Build's order of the pair, so ⇄ keeps it."""

    minimum: float = MINIMUM_DEFAULT
    weak: bool = False
    orient: Sequence[str] | None = None
    focus: Mapping[str, Any] | None = None
    match: Mapping[str, Any] | None = None


def oriented(pair: CMP.PairResult, orient: Sequence[str] | None) -> CMP.PairResult:
    """The pair as shown: swapped when ⇄ put its later dataset on the left; the earlier dataset is A by default."""
    return pair.swapped() if orient and list(orient) == [pair.dataset_b, pair.dataset_a] else pair


def _made_on(record: Mapping[str, Any] | None, cid: str, pair: CMP.PairResult) -> bool:
    if not record:
        return False
    return record.get("comparison_id") == cid and record.get("pair") == [pair.dataset_a, pair.dataset_b]


def focus_of(view: DiagramView, cid: str, pair: CMP.PairResult) -> tuple[str, str] | None:
    """The clicked Cluster box as (dataset, label) on this comparison's pair (`pair` in the Build's order)."""
    f = view.focus
    return (f["dataset"], f["cluster"]) if f and _made_on(f, cid, pair) else None


def match_of(view: DiagramView, cid: str, pair: CMP.PairResult) -> tuple[str, str] | None:
    """The chosen Cluster Match as (Cluster of the earlier dataset, Cluster of the later) on this pair."""
    m = view.match
    return (m["a"], m["b"]) if m and _made_on(m, cid, pair) else None


def match_record(cid: str, pair: CMP.PairResult, m: CMP.Match, swapped: bool) -> dict[str, Any]:
    """What a curve click records in `cc-match`: the match in the Build's order of `pair` (`m` as shown)."""
    a, b = (m.cluster_b, m.cluster_a) if swapped else (m.cluster_a, m.cluster_b)
    return {"comparison_id": cid, "pair": [pair.dataset_a, pair.dataset_b], "a": a, "b": b}


def links(ctx: BuildContext, cid: str, pair: CMP.PairResult, view: DiagramView, tx: Text) -> list[dict[str, Any]]:
    """The curves to draw for the pair as shown: one per Cluster Match at or above the minimum and, with "show
    weaker", the weaker ones dashed; with a Cluster box clicked, only that Cluster's. `a` and `b` are the shown
    sides' labels; workbench.js `ccLinks` draws them and a click records `record`."""
    shown = oriented(pair, view.orient)
    swapped = shown is not pair
    focus = focus_of(view, cid, pair)
    chosen = match_of(view, cid, pair)
    name_a, name_b = ctx.dataset(shown.dataset_a).label, ctx.dataset(shown.dataset_b).label
    out = []
    for m in shown.matches:
        strong = m.jaccard >= view.minimum
        if not strong and not view.weak:
            continue
        if focus and focus not in ((shown.dataset_a, m.cluster_a), (shown.dataset_b, m.cluster_b)):
            continue
        record = match_record(cid, pair, m, swapped)
        title = tx.n(m.n_shared, one="{a} ~ {b}: Match Jaccard {j}, {n} shared Tag",
                     other="{a} ~ {b}: Match Jaccard {j}, {n} shared Tags",
                     a=CT.cluster_name(name_a, m.cluster_a), b=CT.cluster_name(name_b, m.cluster_b),
                     j=tx.num(m.jaccard, 2))
        out.append({"a": m.cluster_a, "b": m.cluster_b, "j": m.jaccard, "label": tx.num(m.jaccard, 2),
                    "dashed": not strong, "chosen": chosen == (record["a"], record["b"]), "title": title,
                    "record": record})
    return out


def _badge(flag: CMP.ClusterFlag, other: str, minimum: float, tx: Text) -> list[Any]:
    code = flag.flag_at(minimum)
    if not code:
        return []
    now = (CT.one_tag_counts(flag.n_in_one_tag_clusters, flag.n_not_in_network, other=other, tx=tx)
           if code == "only_one_tag_clusters" else None)
    # The tooltip only: a click on the badge is a click on its box (data-help would open the guide instead).
    tip: dict[str, Any] = {"data-tip": H.tip(f"comparison.flag.{code}", tx, now)}
    return [html.Span(CT.flag_label(code, other=other, minimum=minimum, tx=tx), className=f"cc-flag {code}",
                      tabIndex="0", **tip)]


def _boxes(ctx: BuildContext, p: CMP.Partition, flags: Sequence[CMP.ClusterFlag], other: str, side: str,
           related: set[str] | None, focus: tuple[str, str] | None, minimum: float, names: Mapping[int, str],
           tx: Text) -> list[Any]:
    """One box per Multi-Tag Cluster of one side: label, Tag count, flag badge and Tags, in the dataset's colour."""
    by_label = {c.label: c for c in p.multi}
    out = []
    for f in flags:
        c = by_label[f.cluster]
        classes = ["cc-box"]
        if related is not None and f.cluster not in related:
            classes.append("dim")
        if focus == (p.dataset, f.cluster):
            classes.append("hl")
        tags = ", ".join(sorted((names.get(t, str(t)) for t in c.members), key=str.casefold))
        where: dict[str, Any] = {"data-side": side, "data-cluster": f.cluster}  # workbench.js `ccLinks` measures it
        out.append(html.Div([
            html.Div([html.B(c.label), " ", html.Span(tx.n(c.size, one="{n} Tag", other="{n} Tags"), className="mute"),
                      *_badge(f, other, minimum, tx)], className="cc-box-head"),
            html.Div(tags, className="cc-box-tags", title=tags),
        ], id={"type": "cc-box", "dataset": p.dataset, "cluster": f.cluster}, n_clicks=0, role="button", tabIndex="0",
            className=" ".join(classes), style={"borderLeftColor": colour_of(ctx, p.dataset)},
            **where))
    return out


# ----------------------------------------------------------------------------- the match detail

GAMES_SHOWN = 10  # games in both Clusters listed before "Show all N" (the Cluster Inspector's length)


@dataclass(frozen=True)
class Side:
    """One dataset of the pair as the detail names it: its label and colour."""

    label: str
    colour: str = "inherit"

    def cluster(self, label: str) -> html.Span:
        return html.Span(CT.cluster_name(self.label, label), className="cc-ds", style={"color": self.colour})


def _help(key: str, tx: Text) -> html.Span:
    return html.Span("?", className="ps-q term", tabIndex="0", **H.attrs(key, tx))


def _figure(label: str, value: str, key: str, tx: Text, note: str = "") -> html.Div:
    return html.Div([_term(label, key, tx, "term cc-fig-label"), html.B(value, className="cc-fig-value"),
                     *([html.Span(note, className="small mute")] if note else [])], className="cc-fig")


def _figures(a: Side, b: Side, m: CMP.Match, n_comparable: int, tx: Text) -> list[Any]:
    """Match Jaccard, both shares (with their comparable forms), Jaccard (comparable) with the Comparable Tag counts,
    and the Overlap vs. expected sentence: never a sort column, and no p-value."""
    name_a, name_b = CT.cluster_name(a.label, m.cluster_a), CT.cluster_name(b.label, m.cluster_b)

    def comparable_form(share: float | None) -> str:
        return tx("comparable: {share}", share=_pct(share, tx))

    counts = tx("Comparable Tags: {n_a} in {a}, {n_b} in {b}", n_a=m.n_comparable_a, a=name_a, n_b=m.n_comparable_b,
                b=name_b)
    return [
        html.Div([
            _figure(tx("Match Jaccard"), tx.num(m.jaccard, 2), "comparison.match_jaccard", tx),
            _figure(tx("Shared, % of {cluster}", cluster=name_a), tx.pct(m.share_a, 0), "comparison.share", tx,
                    comparable_form(m.comparable_share_a)),
            _figure(tx("Shared, % of {cluster}", cluster=name_b), tx.pct(m.share_b, 0), "comparison.share", tx,
                    comparable_form(m.comparable_share_b)),
            _figure(tx("Jaccard (comparable)"), "—" if m.comparable_jaccard is None else tx.num(m.comparable_jaccard, 2),
                    "comparison.comparable_jaccard", tx, counts),
        ], className="cc-figs"),
        html.P(_term(CT.overlap_sentence(m.n_shared, m.overlap_vs_expected, m.expected_overlap, n_comparable, tx),
                     "comparison.overlap", tx), className="small cc-overlap"),
    ]


def _place(p: CMP.TagPlace, other: str, names: Mapping[int, str], tx: Text) -> html.Li:
    group = CT.tag_group(p.group, other=other, cluster=p.cluster, n_games=p.n_games, minimum=p.minimum, tx=tx)
    return html.Li([names.get(p.tag_id, str(p.tag_id)), " ", html.Span(group, className=f"cc-group {p.group}")])


def _tag_columns(a: Side, b: Side, m: CMP.Match, names: Mapping[int, str], tx: Text) -> html.Div:
    """Shared · Only in ‹A Cluster› · Only in ‹B Cluster›, each unshared Tag with where it sits in the other
    dataset (a set-aside defining Tag shows as "hidden", in no figure)."""
    def head(*children: Any) -> html.H5:
        return html.H5(list(children), className="cc-tags-head")

    shared = sorted((names.get(t, str(t)) for t in m.shared_tags), key=str.casefold)
    return html.Div([
        html.Div([head(tx("Shared"), " ", _help("comparison.tag_groups", tx)), html.Ul([html.Li(t) for t in shared])],
                 className="cc-tags-col"),
        html.Div([head(tx("Only in"), " ", a.cluster(m.cluster_a)),
                  html.Ul([_place(p, b.label, names, tx) for p in m.only_a])], className="cc-tags-col"),
        html.Div([head(tx("Only in"), " ", b.cluster(m.cluster_b)),
                  html.Ul([_place(p, a.label, names, tx) for p in m.only_b])], className="cc-tags-col"),
    ], className="cc-tags")


def _games_rows(rows: Sequence[CMP.GameRow], m: CMP.Match, names: Mapping[int, str], tx: Text) -> list[html.Tr]:
    out = []
    for r in rows:
        tags: list[Any] = []  # the shared Tags in bold
        for t in r.tags:
            name = names.get(t, str(t))
            tags += [", "] if tags else []
            tags.append(html.B(name) if t in r.shared else name)
        out.append(html.Tr([html.Td(r.rank_a, className="r mute"), html.Td(r.rank_b, className="r mute"),
                            html.Td(r.name, className="name"),
                            html.Td(tx("{matched} / {size}", matched=len(r.matched_a), size=m.n_tags_a), className="r"),
                            html.Td(tx("{matched} / {size}", matched=len(r.matched_b), size=m.n_tags_b), className="r"),
                            html.Td(tags, className="tags")]))
    return out


def _games_table(a: Side, b: Side, rows: Sequence[CMP.GameRow], m: CMP.Match, names: Mapping[int, str],
                 tx: Text) -> html.Table:
    head = html.Tr([html.Th(tx("Rank in {dataset}", dataset=a.label), className="r"),
                    html.Th(tx("Rank in {dataset}", dataset=b.label), className="r"), html.Th(tx("Name")),
                    html.Th(tx("Matched in {dataset}", dataset=a.label), className="r"),
                    html.Th(tx("Matched in {dataset}", dataset=b.label), className="r"), html.Th(tx("Tags"))])
    return html.Table([html.Thead(head), html.Tbody(_games_rows(rows, m, names, tx))], className="cc-games")


def _games(a: Side, b: Side, m: CMP.Match, names: Mapping[int, str], tx: Text) -> list[Any]:
    """Games in both Clusters: the count line, then the first `GAMES_SHOWN` rows and "Show all N" (both datasets'
    games only; shown, never scored)."""
    g = m.games
    heading = html.H4([_term(tx("Games in both Clusters"), "comparison.games", tx)], className="cc-detail-h")
    if not g.rows:
        return [heading, html.P(PV.render([CT.no_games_line(g.n_in_common, tx)])[0].children, className="small")]
    counts = {"in_common": g.n_in_common, "both": len(g.rows), "only_a": g.n_only_a, "only_b": g.n_only_b,
              "neither": g.n_neither}
    line = PV.render([CT.games_count_line(counts, CT.cluster_name(a.label, m.cluster_a),
                                          CT.cluster_name(b.label, m.cluster_b), tx)])[0]
    out: list[Any] = [heading, html.P(line.children, className="small"),
                      _games_table(a, b, g.rows[:GAMES_SHOWN], m, names, tx)]
    if len(g.rows) > GAMES_SHOWN:
        out.append(html.Details([html.Summary(CT.show_all(len(g.rows), tx), className="more"),
                                 _games_table(a, b, g.rows[GAMES_SHOWN:], m, names, tx)], className="cc-more"))
    return out


def match_detail(a: Side, b: Side, m: CMP.Match | None, n_comparable: int, names: Mapping[int, str],
                 tx: Text) -> list[Any]:
    """The chosen Cluster Match as shown (A on the left), or the request to click a curve."""
    if m is None:
        return [html.P(tx(CT.CHOOSE_A_MATCH), className="cc-empty small")]
    heading = html.H3([a.cluster(m.cluster_a), " ~ ", b.cluster(m.cluster_b), " ", _help("comparison.detail", tx)],
                      className="cc-detail-title")
    return [heading, *_figures(a, b, m, n_comparable, tx), _tag_columns(a, b, m, names, tx),
            *_games(a, b, m, names, tx)]


def shown_match(shown: CMP.PairResult, chosen: tuple[str, str] | None, swapped: bool) -> CMP.Match | None:
    """The chosen match (Build order) among the matches as shown."""
    if chosen is None:
        return None
    want = (chosen[1], chosen[0]) if swapped else chosen
    return next((m for m in shown.matches if (m.cluster_a, m.cluster_b) == want), None)


@dataclass(frozen=True)
class MainView:
    """What the main column shows, by `MAIN_OUTPUTS` name."""

    empty: str  # the fewer-than-two empty state, else ""
    pair_style: dict[str, str]  # hides the pair's block when no pair is chosen
    title: Any
    diagram: Any  # the two columns, or the no-match empty state
    links: list[dict[str, Any]]
    one_tag: str
    weak_label: str
    detail: Any  # the chosen match's detail, or the request to click a curve


MAIN_OUTPUTS = tuple(f.name for f in dataclasses.fields(MainView))
_HIDDEN = {"display": "none"}


def main_view(ctx: BuildContext, result: ComparisonResult, chosen: CMP.PairResult | None, view: DiagramView,
              tx: Text) -> MainView:
    """The main column: the chosen pair's title, the link diagram and the One-Tag line, or an empty state."""
    weak_label = tx("hide weaker") if view.weak else tx("show weaker")
    cid = result.comparison_id
    if cid is None or chosen is None:
        return MainView(tx(CT.FEWER_THAN_TWO) if cid is None else "", _HIDDEN, [], [], [], "", weak_label, [])
    shown = oriented(chosen, view.orient)
    A, B = result.resolved[shown.dataset_a].partition, result.resolved[shown.dataset_b].partition
    name_a, name_b = ctx.dataset(A.dataset).label, ctx.dataset(B.dataset).label
    title = [dataset_name(ctx, A.dataset), " × ", dataset_name(ctx, B.dataset)]
    one_tag = CT.one_tag_line(name_a, sum(c.size == 1 for c in A.clusters), name_b,
                              sum(c.size == 1 for c in B.clusters), tx)
    if not shown.matches:
        return MainView("", {}, title, html.P(tx(CT.NO_MATCH), className="cc-empty"), [], one_tag, weak_label, [])
    drawn = links(ctx, cid, chosen, view, tx)
    focus = focus_of(view, cid, chosen)
    names = PV.tag_names(ctx)
    side_a = Side(name_a, colour_of(ctx, A.dataset))
    side_b = Side(name_b, colour_of(ctx, B.dataset))
    match = shown_match(shown, match_of(view, cid, chosen), shown is not chosen)
    detail = match_detail(side_a, side_b, match, shown.n_comparable, names, tx)
    related_a = related_b = None
    if focus:  # the clicked box and the Clusters its drawn curves reach
        related_a = {x["a"] for x in drawn} | ({focus[1]} if focus[0] == A.dataset else set())
        related_b = {x["b"] for x in drawn} | ({focus[1]} if focus[0] == B.dataset else set())

    def column(p: CMP.Partition, flags: Sequence[CMP.ClusterFlag], other: str, side: str,
               related: set[str] | None) -> html.Div:
        head = html.H4([dataset_name(ctx, p.dataset), " · ",
                        tx.n(len(p.multi), one="{n} Multi-Tag Cluster", other="{n} Multi-Tag Clusters")],
                       className="cc-col-head")
        return html.Div([head, *_boxes(ctx, p, flags, other, side, related, focus, view.minimum, names, tx)],
                        className=f"cc-col cc-col-{side}")

    diagram = html.Div([
        column(A, shown.flags_a, name_b, "a", related_a),
        html.Div(html.Div(className="cc-links"), className="cc-link-col"),
        column(B, shown.flags_b, name_a, "b", related_b),
    ], className="cc-diagram-grid")
    return MainView("", {}, title, diagram, drawn, one_tag, weak_label, detail)


def render_main(ctx: BuildContext, shared: CMP.SharedSettings, included: Sequence[str],
                requests: Mapping[str, Any] | None, clicked: Sequence[str] | None, cstore: Mapping[str, Any] | None,
                view: DiagramView, *, tx: Text) -> MainView:
    """The main column for the view choices, read from the two memos `render` filled: nothing is recomputed."""
    result = resolve_all(ctx, shared, included, requests, cstore)
    chosen = chosen_pair(ranked_pairs(result.pairs, [d.key for d in ctx.datasets]), clicked)
    return main_view(ctx, result, chosen, view, tx)


RENDER_OUTPUTS = ("sources", "g", "s", "resolution", "pairs", "comparison_id", "pill_datasets", "pill_pairs", "shown")


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
        "resolution": [shown_gamma(v.resolution) for v in values],
        "pairs": (pair_rows(ctx, ranked, chosen, tx) if result.comparison_id
                  else [html.P(tx(CT.FEWER_THAN_TWO), className="cc-empty small")]),
        "comparison_id": result.comparison_id or "—",
        "pill_datasets": tx("{n} of {total}", n=len(result.included), total=len(order)),
        "pill_pairs": ([dataset_name(ctx, chosen.dataset_a), " × ", dataset_name(ctx, chosen.dataset_b)]
                       if chosen else "—"),
        # what the mode shows now: the main column follows it (`render_main`), and the view stores are checked against it
        "shown": {"comparison_id": result.comparison_id,
                  "pair": [chosen.dataset_a, chosen.dataset_b] if chosen else None,
                  # each row's (g, s, γ, source) as shown: an edit is read against it (`edited`), the row link
                  # opens Parameter Selection on its cell
                  "values": {v.dataset: [v.g, v.s, shown_gamma(v.resolution), v.source] for v in values}},
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


def _value_input(field: str, dataset: str, step: float, lo: float, hi: float | None) -> dcc.Input:
    """g, s or γ in a dataset row, within the Workbench's limits (`value_limits`)."""
    return dcc.Input(id={"type": f"cc-{field}", "dataset": dataset}, type="number", step=step, min=lo, max=hi,
                     debounce=True, className="cc-num")


def dataset_rows(L: Labels, ctx: BuildContext) -> html.Div:
    """One row per Top-N Dataset: include, its name in its colour, g, s and γ, then its source and figures."""
    head = html.Div([html.Span(), html.Span(), html.Span("g", className="n"), html.Span("s", className="n"),
                     html.Span("γ", className="n")], className="cc-row cc-row-head small mute")
    rows = [head]
    g_top, s_top = value_limits(ctx)
    for d in ctx.datasets:
        rows.append(html.Div([
            dcc.Checklist(id={"type": "cc-include", "dataset": d.key}, options=[{"label": "", "value": d.key}],
                          value=[d.key], className="check cc-include"),
            dataset_name(ctx, d.key),
            _value_input("g", d.key, 1, 1, g_top), _value_input("s", d.key, 1, 1, s_top),
            _value_input("resolution", d.key, 0.01, 0.01, None),
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


def pair_block(L: Labels) -> html.Div:
    """The chosen pair's block of the main column: title with ⇄, the Minimum Match Jaccard slider with "show
    weaker", the link diagram, the One-Tag line and the match detail (issue 20). Its controls are static, so the
    slider keeps its value while the diagram re-renders."""
    swap_tip = L.prop("cc-swap", "data-tip", lambda tx: H.tip("comparison.swap", tx))
    minimum_tip = L.prop("cc-minimum-label", "data-tip", lambda tx: H.tip("comparison.minimum", tx))
    return html.Div([
        html.Div([
            html.H3([html.Span(id="cc-title"), " ",
                     html.Button("⇄", id="cc-swap", className="btn cc-swap", n_clicks=0,
                                 **{"data-tip": swap_tip, "aria-label": swap_tip})], className="cc-title"),
            html.Div([
                html.Span(L.prop("cc-minimum-label", "children", msg("Minimum Jaccard")), id="cc-minimum-label",
                          className="term small", tabIndex="0", **{"data-tip": minimum_tip}),
                html.Div(dcc.Slider(id="cc-minimum", min=0, max=1, step=0.01, value=MINIMUM_DEFAULT,
                                    marks={0: "0", 0.1: "0.1", 0.25: "0.25", 0.5: "0.5", 1: "1"},
                                    tooltip={"placement": "bottom", "always_visible": False}),
                         className="cc-slider"),
                html.Button(id="cc-weak-btn", className="link small", n_clicks=0),
                _static_help(L, "comparison.minimum"),
            ], className="cc-minimum"),
        ], className="cc-pair-head"),
        html.Div([L.span(msg("Line width = Match Jaccard. Click a curve for its match, a Cluster to show only its "
                             "curves.")), " ", _static_help(L, "comparison.diagram")],
                 className="small mute cc-hint"),
        html.Div(id="cc-diagram", className="cc-diagram"),
        html.P(id="cc-one-tag", className="small mute cc-one-tag"),
        html.Div(id="cc-detail", className="cc-detail"),
    ], id="cc-pair-view", style=_HIDDEN)


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
        html.Div(id="cc-notice", className="cc-notice small", role="status"),  # a shared-setting change's notice
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
    main = html.Div([html.P(id="cc-main-empty", className="cc-empty"), pair_block(L)], id="cc-main",
                    className="main cc-main")
    # Over the whole mode while the comparison resolves (callbacks.py `running`): the previous view dims under it.
    busy = html.Div(html.Div(html.Span(L.prop("cc-busy", "children", msg("Comparing Clusters…")), id="cc-busy",
                                       hidden=True), className="busy", role="status"), className="ps-busy cc-busy")
    stores = [dcc.Store(id="cc-requests", data={}), dcc.Store(id="cc-pair"), dcc.Store(id="cc-shown"),
              # the view choices (`DiagramView`) and the curves workbench.js `ccLinks` draws
              dcc.Store(id="cc-orient"), dcc.Store(id="cc-weak", data=False), dcc.Store(id="cc-focus"),
              dcc.Store(id="cc-match"), dcc.Store(id="cc-links", data=[]), dcc.Store(id="cc-links-drawn")]
    return html.Div([*stores, head, sidebar, main, busy], id="cc-body", className="cc-body")
