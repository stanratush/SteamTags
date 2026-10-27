"""Automatic Parameter Selection: Selection Settings and keys, the grid of Threshold Pairs, the per-graph procedure,
Neighbour Agreement and choosing the pair.

Dash-free and cache-free: the app (`steamstudy.app.ps_run`) and the bundle maker drive it with an injected `map_fn`.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, field, replace
from typing import Any

import networkx as nx
import numpy as np
from sklearn.metrics import adjusted_rand_score

from steamstudy.config import NetworkDefaults
from steamstudy.network import champ as C
from steamstudy.network import metrics as M
from steamstudy.network.cluster import Cluster, _leiden_graph, _leiden_passes, label_clusters, leiden_scan, membership
from steamstudy.network.graph import TagNetwork, build_network, to_graph
from steamstudy.network.model import Game, Settings, TagContext, canonical_key_json
from steamstudy.network.stability import TRADES_PER_GAME, derive_seeds, noise_seeds, replicate_seeds

METHOD_VERSION = "parameter-selection-1"
VALIDATION_METHOD_VERSION = "ps-validation-1"  # validation.METHOD_VERSION; here so keys need no validation import
SUBSAMPLE_FRACTION = 0.8
SCAN_RULE = "gm22_gamma_max_n_e"
SCAN_STREAM, NULL_SHUFFLE_STREAM, SUBSAMPLE_STREAM = 3, 4, 5
WEIGHT_NAMES = {"lift": "Lift", "shared_games": "Shared games"}


# ----------------------------------------------------------------------------- Selection Settings


@dataclass(frozen=True)
class SelectionSettings:
    """The choices that fix every pair's Selected Partition (one set for all datasets)."""

    build_id: str
    genre_hidden: tuple[int, ...]  # hidden Genre Tag ids
    hide_defining_tag: bool
    removed_tag_ids: tuple[int, ...]
    min_months: int
    clustering_weight: str
    seed: int
    null_replicates: int  # the Workbench's (stream 1); the noise seeds exclude them
    noise_seeds: int
    g_range: tuple[int, int]
    s_range: tuple[int, int]
    gamma_step: float
    scan_seeds: int
    min_multi_tag_clusters: int
    replicates: int  # R, Null Comparison
    subsamples: int  # S, Subsample Stability
    algorithm: str = "leiden"

    def __post_init__(self) -> None:
        object.__setattr__(self, "genre_hidden", tuple(sorted(set(self.genre_hidden))))
        object.__setattr__(self, "removed_tag_ids", tuple(sorted(set(self.removed_tag_ids))))
        object.__setattr__(self, "g_range", tuple(self.g_range))
        object.__setattr__(self, "s_range", tuple(self.s_range))
        if self.algorithm != "leiden":
            raise ValueError("Parameter Selection runs Leiden only")

    def pairs(self) -> list[tuple[int, int]]:
        """The Parameter Grid: (g, s) with s ≤ g, g ascending then s ascending."""
        return [(g, s) for g in range(self.g_range[0], self.g_range[1] + 1)
                for s in range(self.s_range[0], self.s_range[1] + 1) if s <= g]

    def hidden_tag_ids(self, context: TagContext) -> tuple[int, ...]:
        hidden = set(self.genre_hidden)
        if self.hide_defining_tag and context.defining_tag_id is not None:
            hidden.add(context.defining_tag_id)
        return tuple(sorted(hidden))

    def for_pair(self, dataset: str, context: TagContext, g: int, s: int) -> Settings:
        """The pair's Network State settings (γ and seed play no part in the network)."""
        return Settings(build_id=self.build_id, dataset=dataset, min_months=self.min_months, min_games_per_tag=g,
                        min_shared_games=s, hidden_tag_ids=self.hidden_tag_ids(context),
                        removed_tag_ids=self.removed_tag_ids, clustering_weight=self.clustering_weight,
                        algorithm="leiden", resolution=1.0, seed=self.seed, null_replicates=self.null_replicates,
                        noise_seeds=self.noise_seeds)

    def for_dataset(self, dataset: str, context: TagContext) -> Settings:
        return self.for_pair(dataset, context, self.g_range[0], self.s_range[0])

    # -- keys

    def settings_key(self) -> dict[str, Any]:
        """Everything except R and S, without a dataset: names the export zip."""
        return {
            "build_id": self.build_id, "genre_hidden": list(self.genre_hidden),
            "hide_defining_tag": self.hide_defining_tag, "removed_tag_ids": list(self.removed_tag_ids),
            "min_months": self.min_months, "clustering_weight": self.clustering_weight, "algorithm": self.algorithm,
            "seed": self.seed, "null_replicates": self.null_replicates, "noise_seeds": self.noise_seeds,
            "g_range": list(self.g_range), "s_range": list(self.s_range), "gamma_step": self.gamma_step,
            "scan_seeds": self.scan_seeds, "min_multi_tag_clusters": self.min_multi_tag_clusters,
            "method_version": METHOD_VERSION,
        }

    def grid_key(self, dataset: str, context: TagContext) -> dict[str, Any]:
        return {**self.settings_key(), "dataset": dataset, "hidden_tag_ids": list(self.hidden_tag_ids(context))}

    def validation_key(self, dataset: str, context: TagContext, g: int, s: int) -> dict[str, Any]:
        return {"grid_key": self.grid_key(dataset, context), "g": g, "s": s, "replicates": self.replicates,
                "subsamples": self.subsamples, "trades_per_game": TRADES_PER_GAME,
                "subsample_fraction": SUBSAMPLE_FRACTION, "validation_method_version": VALIDATION_METHOD_VERSION}

    def with_(self, **changes: Any) -> SelectionSettings:
        return replace(self, **changes)


def key_hash(key: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_key_json(key).encode("utf-8")).hexdigest()


def load_selection_settings(network: NetworkDefaults, genre_tag_ids: Iterable[int], build_id: str) -> SelectionSettings:
    """The configured defaults: `[parameter_selection]` plus the network's hidden-tag defaults and seeds."""
    ps = network.parameter_selection
    return SelectionSettings(
        build_id=build_id, genre_hidden=tuple(genre_tag_ids) if network.hide_genre_tags else (),
        hide_defining_tag=network.hide_defining_tag, removed_tag_ids=(), min_months=ps.min_months,
        clustering_weight=ps.clustering_weight, seed=network.seed, null_replicates=network.null_replicates,
        noise_seeds=network.noise_seeds, g_range=ps.g_range, s_range=ps.s_range, gamma_step=ps.gamma_step,
        scan_seeds=ps.scan_seeds, min_multi_tag_clusters=ps.min_multi_tag_clusters, replicates=ps.null_replicates,
        subsamples=ps.subsamples,
    )


def selection_seeds(settings: SelectionSettings) -> tuple[list[int], list[int], list[int]]:
    """Streams 3 (scan), 4 (null shuffles) and 5 (subsample draws); each excludes every lower stream's seeds."""
    main = settings.seed
    taken = set(replicate_seeds(main, settings.null_replicates))
    taken |= set(noise_seeds(main, settings.noise_seeds, settings.null_replicates))
    scan = derive_seeds(main, SCAN_STREAM, settings.scan_seeds, exclude=taken)
    taken |= set(scan)
    null = derive_seeds(main, NULL_SHUFFLE_STREAM, settings.replicates, exclude=taken)
    taken |= set(null)
    sub = derive_seeds(main, SUBSAMPLE_STREAM, settings.subsamples, exclude=taken)
    return scan, null, sub


# ----------------------------------------------------------------------------- Pair Constraints and labels


@dataclass(frozen=True)
class Constraints:
    """The Pair Constraints and the near-best tolerance (all bounds inclusive)."""

    tolerance: float
    min_retention: float
    max_isolated_share: float
    min_lcc_share: float
    min_comparable_neighbours: int
    max_multi_tag_clusters: int | None  # None = off


def default_constraints(network: NetworkDefaults) -> Constraints:
    ps = network.parameter_selection
    return Constraints(ps.tolerance, ps.min_retention, ps.max_isolated_share, ps.min_lcc_share,
                       ps.min_comparable_neighbours, ps.max_multi_tag_clusters)


@dataclass(frozen=True)
class Label:
    text: str
    changes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def custom(self) -> bool:
        return bool(self.changes)


def _names(ids: Iterable[int], names: Mapping[int, str]) -> str:
    return ", ".join(names.get(t, str(t)) for t in ids)


def settings_label(settings: SelectionSettings, defaults: SelectionSettings,
                   names: Mapping[int, str] | None = None) -> Label:
    """"Default settings", or "Custom settings: …" with each changed editable setting next to its default."""
    names = names or {}
    changes, parts = [], []

    def changed(setting: str, value: Any, default: Any, text: str) -> None:
        changes.append({"setting": setting, "value": value, "default": default})
        parts.append(text)

    if settings.genre_hidden != defaults.genre_hidden:
        changed("genre_hidden", list(settings.genre_hidden), list(defaults.genre_hidden),
                f"hidden Genre Tags {len(settings.genre_hidden)} (default {len(defaults.genre_hidden)})")
    if settings.hide_defining_tag != defaults.hide_defining_tag:
        word = lambda hidden: "hidden" if hidden else "shown"  # noqa: E731
        changed("hide_defining_tag", settings.hide_defining_tag, defaults.hide_defining_tag,
                f"defining tag {word(settings.hide_defining_tag)} (default {word(defaults.hide_defining_tag)})")
    if settings.min_months != defaults.min_months:
        changed("min_months", settings.min_months, defaults.min_months,
                f"Minimum Months {settings.min_months} (default {defaults.min_months})")
    if settings.clustering_weight != defaults.clustering_weight:
        changed("clustering_weight", settings.clustering_weight, defaults.clustering_weight,
                f"Clustering Weight {WEIGHT_NAMES[settings.clustering_weight]} "
                f"(default {WEIGHT_NAMES[defaults.clustering_weight]})")
    if settings.min_multi_tag_clusters != defaults.min_multi_tag_clusters:
        changed("min_multi_tag_clusters", settings.min_multi_tag_clusters, defaults.min_multi_tag_clusters,
                f"minimum Multi-Tag Clusters {settings.min_multi_tag_clusters} "
                f"(default {defaults.min_multi_tag_clusters})")
    if settings.removed_tag_ids != defaults.removed_tag_ids:
        n = len(settings.removed_tag_ids)
        changed("removed_tag_ids", list(settings.removed_tag_ids), list(defaults.removed_tag_ids),
                f"{n} removed tag{'' if n == 1 else 's'} ({_names(settings.removed_tag_ids, names)})"
                if n else "no removed tags")
    return Label("Custom settings: " + ", ".join(parts) if parts else "Default settings", changes)


CONSTRAINT_TEXT = {
    "tolerance": "tolerance {}",
    "min_retention": "Information Retention ≥ {}",
    "max_isolated_share": "isolated share ≤ {}",
    "min_lcc_share": "LCC share ≥ {}",
    "min_comparable_neighbours": "comparable neighbours ≥ {}",
    "max_multi_tag_clusters": "Multi-Tag Clusters ≤ {}",
}


def _constraint_value(value: Any) -> str:
    if value is None:
        return "off"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def constraints_label(constraints: Constraints, defaults: Constraints) -> Label:
    changes, parts = [], []
    for name, template in CONSTRAINT_TEXT.items():
        value, default = getattr(constraints, name), getattr(defaults, name)
        if value != default:
            changes.append({"constraint": name, "value": value, "default": default})
            parts.append(f"{template.format(_constraint_value(value))} (default {_constraint_value(default)})")
    return Label("Custom constraints: " + ", ".join(parts) if parts else "Default constraints", changes)


# ----------------------------------------------------------------------------- pair networks


def graph_hash(network: TagNetwork, clustering_weight: str) -> str:
    """Sorted nodes and sorted (u, v, shared count, weight): pairs with equal hashes share every result."""
    weight = (lambda e: float(e.shared)) if clustering_weight == "shared_games" else (lambda e: e.lift)
    data = [network.nodes, [[e.u, e.v, e.shared, weight(e)] for e in sorted(network.edges, key=lambda e: (e.u, e.v))]]
    return hashlib.sha256(json.dumps(data, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PairNetwork:
    g: int
    s: int
    settings: Settings
    network: TagNetwork
    graph_hash: str


def pair_networks(games: list[Game], settings: SelectionSettings, dataset: str,
                  context: TagContext) -> list[PairNetwork]:
    """Every grid pair's Tag Network and graph hash, in grid order."""
    out = []
    for g, s in settings.pairs():
        pair = settings.for_pair(dataset, context, g, s)
        network = build_network(games, pair, context)
        out.append(PairNetwork(g, s, pair, network, graph_hash(network, settings.clustering_weight)))
    return out


# ----------------------------------------------------------------------------- the per-graph procedure


@dataclass(frozen=True)
class GraphTask:
    """One distinct graph's work: self-contained and picklable (no Build path, no worker initializer)."""

    graph_hash: str
    games: list[Game]
    context: TagContext
    settings: Settings  # the first pair with this graph (every pair with it gives the same result)
    scan_seeds: tuple[int, ...]
    gamma_step: float
    min_multi_tag_clusters: int
    weight: float  # edges × scan length, for heaviest-first dispatch
    n_pairs: int  # grid pairs with this graph


@dataclass(frozen=True)
class WorkbenchSetting:
    """The Workbench γ and seed that show the Selected Partition, or the fallback with its flag."""

    gamma: float
    seed: int
    seed_kind: str  # "main" or "scan"
    flag: str | None  # None (reproduced), "not_representable" or "not_reproduced"
    ari: float  # 1.0 when reproduced; otherwise the fallback's ARI against the Selected Partition


@dataclass(frozen=True)
class GraphResult:
    """Every per-pair result of one distinct graph (the graph file's contents)."""

    graph_hash: str
    nodes: list[int]
    edged: list[int]
    edges: list[list[int]]  # [u, v], for Edge Overlap
    n_tags: int
    n_edges: int
    n_e: int
    lift_below_1_share: float | None
    gamma_max_n_e: float | None
    gamma_end: float | None
    scan_length: int
    scan_runs: int
    pass_capped_runs: int
    n_unique: int
    n_twins: int
    champ: dict[str, Any] | None  # champ.to_json; None with no edges
    reason: str | None  # no Selected Partition: no_edges, no_stable_partition, too_few_multi_tag_clusters
    selected_resolution: float | None
    workbench: dict[str, Any] | None
    seed_noise: dict[str, Any] | None  # floor (min ARI), mean, exact, runs
    retention: float | None
    retention_status: str | None
    games_with_edged_tag_share: float | None
    n_isolated: int
    isolated_share: float | None
    n_components: int  # with ≥ 2 tags
    lcc_tags: int
    lcc_share: float | None  # of the non-isolated tags
    n_multi: int | None
    n_one_isolated: int | None
    n_one_connected: int | None
    modularity: float | None
    coverage: float | None
    silhouette: float | None
    silhouette_status: str | None
    seconds: float = 0.0  # timing: never compared

    @property
    def selected_partition(self) -> dict[str, Any] | None:
        if self.champ is None or self.champ["selected"] is None:
            return None
        return self.champ["admissible"][self.champ["selected"]]

    @property
    def selected(self) -> list[int] | None:
        """The Selected Partition's canonical membership in node order."""
        p = self.selected_partition
        return None if p is None else list(p["membership"])

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> GraphResult:
        return cls(**data)


def canonical_json(data: Any, drop: Iterable[str] = ()) -> str:
    """Sorted keys, no whitespace; top-level `drop` keys (timings, `computed_with`) left out."""
    if isinstance(data, Mapping):
        data = {k: v for k, v in data.items() if k not in set(drop)}
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def edge_arrays_of(network: TagNetwork, clustering_weight: str) -> C.EdgeArrays:
    index = {t: i for i, t in enumerate(network.nodes)}
    weight = (lambda e: float(e.shared)) if clustering_weight == "shared_games" else (lambda e: e.lift)
    return C.edge_arrays(len(network.nodes), [(index[e.u], index[e.v], weight(e)) for e in network.edges])


def workbench_candidates(a: float, b: float, midpoint: float) -> list[float]:
    """Two-decimal values ≥ 0.01 inside [a, b], nearest the midpoint first, ties to the lower value."""
    lo, hi = max(1, math.ceil(a * 100 - 1e-9)), math.floor(b * 100 + 1e-9)
    values = [round(i / 100, 2) for i in range(lo, hi + 1)]
    return sorted((x for x in values if a <= x <= b), key=lambda x: (abs(x - midpoint), x))


def workbench_setting(graph: nx.Graph, membership: list[int], a: float, b: float, midpoint: float, main_seed: int,
                      scan_seeds: Iterable[int]) -> WorkbenchSetting:
    """The first (two-decimal γ, seed) at which Leiden reproduces the Selected Partition exactly: candidates nearest
    the midpoint first, at each the main seed and then the scan seeds. Otherwise the rounded midpoint, main seed."""
    lg, weights = _leiden_graph(graph)
    target = np.asarray(membership)
    candidates = workbench_candidates(a, b, midpoint)
    seeds = [(main_seed, "main"), *((s, "scan") for s in scan_seeds)]
    for gamma in candidates:
        for seed, kind in seeds:
            labels, _ = _leiden_passes(lg, weights, gamma, seed)
            if np.array_equal(C.canonical(labels), target):
                return WorkbenchSetting(gamma, seed, kind, None, 1.0)
    gamma = max(0.01, round(midpoint, 2))
    labels, _ = _leiden_passes(lg, weights, gamma, main_seed)
    flag = "not_reproduced" if candidates else "not_representable"
    return WorkbenchSetting(gamma, main_seed, "main", flag, float(adjusted_rand_score(target, labels)))


def scan_and_select(graph: nx.Graph, arrays: C.EdgeArrays, scan_seeds: Iterable[int], gamma_step: float,
                    min_multi_tag_clusters: int) -> tuple[C.Scan, C.ChampResult]:
    """The γ scan from 0 to γ_max(n_e), dedup and CHAMP: the procedure every network (observed, null, subsample)
    goes through. The graph needs an edge."""
    gammas = C.scan_gammas(arrays.n_e, gamma_step)
    scan = C.dedup(leiden_scan(graph, gammas, list(scan_seeds)))
    return scan, C.champ(scan, arrays, gammas[-1], min_multi_tag_clusters)


def clusters_of(nodes: list[int], labels: Iterable[int]) -> list[Cluster]:
    groups: dict[int, set[int]] = {}
    for t, label in zip(nodes, labels):
        groups.setdefault(int(label), set()).add(t)
    return label_clusters([frozenset(c) for c in groups.values()])


def run_graph(task: GraphTask) -> GraphResult:
    """Network → γ scan → CHAMP → Workbench γ and seed → Seed-Noise Floor, Retention, Fragmentation, descriptive
    metrics and graph counts."""
    started = time.perf_counter()
    s = task.settings
    network = build_network(task.games, s, task.context)
    if graph_hash(network, s.clustering_weight) != task.graph_hash:
        raise ValueError(f"graph hash mismatch for {s.dataset} g={s.min_games_per_tag} s={s.min_shared_games}")
    nodes = network.nodes
    graph = to_graph(nodes, network.edges, s.clustering_weight)
    arrays = edge_arrays_of(network, s.clustering_weight)
    edged = [t for t, e in zip(nodes, arrays.edged.tolist()) if e]
    n_iso = len(nodes) - len(edged)

    hidden = set(s.hidden_tag_ids) | set(s.removed_tag_ids)
    denominator = sum(network.n(t) for t in network.tag_names if t not in hidden)
    edged_set = set(edged)
    components = [c for c in nx.connected_components(graph) if len(c) >= 2]
    lcc = max((len(c) for c in components), default=0)
    common: dict[str, Any] = {
        "graph_hash": task.graph_hash, "nodes": list(nodes), "edged": edged,
        "edges": [[e.u, e.v] for e in network.edges], "n_tags": len(nodes), "n_edges": len(network.edges),
        "n_e": len(edged),
        "lift_below_1_share": (sum(e.lift < 1 for e in network.edges) / len(network.edges)) if network.edges else None,
        "retention": sum(network.n(t) for t in edged) / denominator if denominator else None,
        "retention_status": None if denominator else "no_visible_tags",
        "games_with_edged_tag_share": (sum(any(t in edged_set for t in g.tag_ids) for g in network.games)
                                       / network.n_games) if network.n_games else None,
        "n_isolated": n_iso, "isolated_share": n_iso / len(nodes) if nodes else None,
        "n_components": len(components), "lcc_tags": lcc, "lcc_share": lcc / len(edged) if edged else None,
    }
    fields: dict[str, Any] = {
        "gamma_max_n_e": None, "gamma_end": None, "scan_length": 0, "scan_runs": 0, "pass_capped_runs": 0,
        "n_unique": 0, "n_twins": 0, "champ": None, "reason": "no_edges", "selected_resolution": None,
        "workbench": None, "seed_noise": None, "n_multi": None, "n_one_isolated": None, "n_one_connected": None,
        "modularity": None, "coverage": None, "silhouette": None, "silhouette_status": None,
    }
    if network.edges:
        scan, result = scan_and_select(graph, arrays, task.scan_seeds, task.gamma_step, task.min_multi_tag_clusters)
        fields.update({
            "gamma_max_n_e": C.gamma_max_K(len(edged)), "gamma_end": result.gamma_end,
            "scan_length": scan.n_runs // max(1, len(task.scan_seeds)), "scan_runs": scan.n_runs,
            "pass_capped_runs": scan.capped_runs, "n_unique": result.n_unique, "n_twins": result.n_twins,
            "champ": C.to_json(result), "reason": result.reason,
        })
        chosen = result.selected_partition
        if chosen is not None:
            fields.update(_selected_metrics(task, network, graph, chosen))
    return GraphResult(**common, **fields, seconds=time.perf_counter() - started)


def _selected_metrics(task: GraphTask, network: TagNetwork, graph: nx.Graph,
                      chosen: C.AdmissiblePartition) -> dict[str, Any]:
    s, nodes = task.settings, network.nodes
    gamma = chosen.midpoint
    target = list(chosen.membership)
    wb = workbench_setting(graph, target, chosen.a, chosen.b, gamma, s.seed, task.scan_seeds)
    runs = leiden_scan(graph, [gamma], noise_seeds(s.seed, s.noise_seeds, s.null_replicates))
    aris = [float(adjusted_rand_score(target, r.membership)) for r in runs]
    exact = sum(bool(np.array_equal(C.canonical(r.membership), np.asarray(target))) for r in runs)
    clusters = clusters_of(nodes, target)
    sil = M.silhouette(nodes, clusters, network.tag_games, M.jaccard_distances(nodes, network.tag_games))
    return {
        "selected_resolution": gamma, "workbench": asdict(wb),
        "seed_noise": {"floor": min(aris), "mean": statistics.fmean(aris), "exact": exact, "runs": len(runs)},
        "n_multi": chosen.n_multi, "n_one_isolated": chosen.n_one_isolated,
        "n_one_connected": chosen.n_one - chosen.n_one_isolated,
        "modularity": M.modularity(graph, clusters, gamma), "coverage": M.coverage(graph, membership(clusters)),
        "silhouette": sil.mean, "silhouette_status": sil.status,
    }


# ----------------------------------------------------------------------------- the grid driver


@dataclass
class GridRun:
    pair_hash: dict[tuple[int, int], str]  # (g, s) -> graph hash
    results: dict[str, GraphResult]  # computed in this run, sorted by hash
    complete: bool  # False when stopped before every task ran


def grid_tasks(games: list[Game], settings: SelectionSettings, dataset: str, context: TagContext,
               skip: Iterable[str] = frozenset()) -> tuple[dict[tuple[int, int], str], list[GraphTask]]:
    """Every pair's graph hash, and one task per distinct graph not in `skip`, heaviest first."""
    scan_seeds, _, _ = selection_seeds(settings)
    pairs = pair_networks(games, settings, dataset, context)
    first: dict[str, PairNetwork] = {}
    count: dict[str, int] = {}
    for p in pairs:
        first.setdefault(p.graph_hash, p)
        count[p.graph_hash] = count.get(p.graph_hash, 0) + 1
    skipped = set(skip)
    tasks = []
    for h, p in sorted(first.items()):
        if h in skipped:
            continue
        n_e = len({t for e in p.network.edges for t in (e.u, e.v)})
        length = len(C.scan_gammas(n_e, settings.gamma_step)) if n_e >= 2 else 1
        tasks.append(GraphTask(h, games, context, p.settings, tuple(scan_seeds), settings.gamma_step,
                               settings.min_multi_tag_clusters, float(max(1, len(p.network.edges)) * length),
                               count[h]))
    tasks.sort(key=lambda t: (-t.weight, t.graph_hash))
    return {(p.g, p.s): p.graph_hash for p in pairs}, tasks


def run_grid(games: list[Game], settings: SelectionSettings, dataset: str, context: TagContext, *,
             map_fn: Callable[..., Iterable[Any]] = map, on_result: Callable[..., None] | None = None,
             should_stop: Callable[[], bool] | None = None, skip: Iterable[str] = frozenset()) -> GridRun:
    """Dedup graphs in the parent, dispatch heaviest first through `map_fn` (unordered is fine), and return the
    results sorted by graph hash. `on_result(hash, result, pairs_ticked, weight)` follows each result."""
    pair_hash, tasks = grid_tasks(games, settings, dataset, context, skip)
    stop = should_stop or (lambda: False)

    def feed() -> Iterator[GraphTask]:
        for task in tasks:
            if stop():
                return
            yield task

    by_hash = {t.graph_hash: t for t in tasks}
    results: dict[str, GraphResult] = {}
    for result in map_fn(run_graph, feed()):
        results[result.graph_hash] = result
        if on_result is not None:
            task = by_hash[result.graph_hash]
            on_result(result.graph_hash, result, task.n_pairs, task.weight)
        if stop():
            break
    return GridRun(pair_hash, dict(sorted(results.items())), len(results) == len(tasks))


# ----------------------------------------------------------------------------- Neighbour Agreement


@dataclass
class Grid:
    """One dataset's complete grid: every pair's graph hash and every distinct graph's result."""

    dataset: str
    pair_hash: dict[tuple[int, int], str]
    results: dict[str, GraphResult]

    @property
    def pairs(self) -> list[tuple[int, int]]:
        return sorted(self.pair_hash)

    def at(self, g: int, s: int) -> GraphResult:
        return self.results[self.pair_hash[(g, s)]]


DIRECTIONS = {"g-": (-1, 0), "g+": (1, 0), "s-": (0, -1), "s+": (0, 1)}


@dataclass(frozen=True)
class Link:
    """One unordered neighbour pair p = (g, s), q = (g + 1, s) or (g, s + 1)."""

    p: tuple[int, int]
    q: tuple[int, int]
    status: str  # ok, neighbour_has_no_selected_partition, too_few_compared_tags
    n_shared: int
    shared_jaccard: float | None
    n_compared: int
    identical_graph: bool
    ari: float | None
    edge_overlap: float | None


def _jaccard(a: set[Any], b: set[Any]) -> float | None:
    union = a | b
    return len(a & b) / len(union) if union else None


def link(grid: Grid, p: tuple[int, int], q: tuple[int, int]) -> Link:
    a, b = grid.at(*p), grid.at(*q)
    nodes_a, nodes_b = set(a.nodes), set(b.nodes)
    shared = sorted(nodes_a & nodes_b)
    edged = set(a.edged) | set(b.edged)
    compared = [t for t in shared if t in edged]
    base = Link(p=p, q=q, status="ok", n_shared=len(shared), shared_jaccard=_jaccard(nodes_a, nodes_b),
                n_compared=len(compared), identical_graph=a.graph_hash == b.graph_hash, ari=None,
                edge_overlap=_jaccard({tuple(e) for e in a.edges}, {tuple(e) for e in b.edges}))
    if a.selected is None or b.selected is None:
        return replace(base, status="neighbour_has_no_selected_partition")
    if len(compared) < 2:
        return replace(base, status="too_few_compared_tags")
    la, lb = dict(zip(a.nodes, a.selected)), dict(zip(b.nodes, b.selected))
    return replace(base, ari=float(adjusted_rand_score([la[t] for t in compared], [lb[t] for t in compared])))


def neighbour_links(grid: Grid) -> list[Link]:
    """One record per unordered neighbour pair inside the grid, in grid order."""
    inside = set(grid.pair_hash)
    return [link(grid, (g, s), q) for g, s in grid.pairs for q in ((g + 1, s), (g, s + 1)) if q in inside]


def pair_links(links: Iterable[Link], g: int, s: int, inside: Iterable[tuple[int, int]]) -> dict[str, Link | None]:
    """The four directions of one pair; None where the neighbour is outside the grid (`outside_grid`)."""
    by_ends = {(x.p, x.q): x for x in links} | {(x.q, x.p): x for x in links}
    grid = set(inside)
    out: dict[str, Link | None] = {}
    for name, (dg, ds) in DIRECTIONS.items():
        q = (g + dg, s + ds)
        out[name] = by_ends.get(((g, s), q)) if q in grid else None
    return out


@dataclass(frozen=True)
class NeighbourAgreement:
    value: float | None  # mean ARI over ok links with a different graph
    status: str  # ok, no_selected_partition, no_comparable_neighbours
    n_in_grid: int
    n_comparable: int
    n_different: int  # comparable with a different graph: the ones counted
    n_identical: int  # comparable with an identical graph: flagged, not counted
    n_missing: int  # the neighbour has no Selected Partition (missing, never 0)
    min_ari: float | None


def neighbour_agreement(grid: Grid, links: Iterable[Link]) -> dict[tuple[int, int], NeighbourAgreement]:
    """Per pair, independent of the Pair Constraints."""
    mine: dict[tuple[int, int], list[Link]] = {p: [] for p in grid.pairs}
    for x in links:
        mine[x.p].append(x)
        mine[x.q].append(x)
    out = {}
    for pair, xs in mine.items():
        ok = [x for x in xs if x.status == "ok"]
        counted = [x.ari for x in ok if not x.identical_graph and x.ari is not None]
        if grid.at(*pair).selected is None:
            status, value = "no_selected_partition", None
        elif not counted:
            status, value = "no_comparable_neighbours", None
        else:
            status, value = "ok", statistics.fmean(counted)
        out[pair] = NeighbourAgreement(
            value=value, status=status, n_in_grid=len(xs), n_comparable=len(ok), n_different=len(counted),
            n_identical=sum(x.identical_graph for x in ok),
            n_missing=sum(x.status == "neighbour_has_no_selected_partition" for x in xs),
            min_ari=min(counted) if counted and status == "ok" else None)
    return out


# ----------------------------------------------------------------------------- choosing the pair


# The Pair Constraints in the table's order: (field, reason code).
CONSTRAINT_ORDER = (
    ("min_retention", "retention_below_min"),
    ("max_isolated_share", "isolated_share_above_max"),
    ("min_lcc_share", "lcc_share_below_min"),
    ("min_comparable_neighbours", "too_few_comparable_neighbours"),
    ("max_multi_tag_clusters", "too_many_clusters"),
)
REASON_ORDER = ("no_selected_partition", "no_neighbour_agreement", "too_few_comparable_neighbours",
                "retention_below_min", "isolated_share_above_max", "lcc_share_below_min", "too_many_clusters")
FLOAT_TOLERANCE = 1e-12


def pair_reasons(result: GraphResult, na: NeighbourAgreement, c: Constraints) -> list[str]:
    """Every failing reason code of one pair, in REASON_ORDER (empty: a Qualifying Pair)."""
    if result.selected is None:
        failing = {"no_selected_partition"}
    else:
        failing = set()
        if na.value is None:
            failing.add("no_neighbour_agreement")
    if na.n_different < c.min_comparable_neighbours:
        failing.add("too_few_comparable_neighbours")
    if result.retention is None or result.retention < c.min_retention:
        failing.add("retention_below_min")
    if result.isolated_share is None or result.isolated_share > c.max_isolated_share:
        failing.add("isolated_share_above_max")
    if result.lcc_share is None or result.lcc_share < c.min_lcc_share:
        failing.add("lcc_share_below_min")
    if c.max_multi_tag_clusters is not None and (result.n_multi or 0) > c.max_multi_tag_clusters:
        failing.add("too_many_clusters")
    return [r for r in REASON_ORDER if r in failing]


@dataclass(frozen=True)
class ConstraintCount:
    constraint: str
    alone: int
    cumulative: int


@dataclass(frozen=True)
class Choice:
    status: str  # ok or no_qualifying_pair
    chosen: tuple[int, int] | None
    max_na: float | None
    best: tuple[int, int] | None  # the pair with the highest NA (smallest g, then s, among equals)
    near_best: list[tuple[int, int]]
    qualifying: list[tuple[int, int]]
    reasons: dict[tuple[int, int], list[str]]
    exclusion: list[ConstraintCount]  # pairs with a Selected Partition and NA, excluded by each constraint
    constraints: Constraints
    n_pairs: int
    n_selected: int  # pairs with a Selected Partition

    @property
    def excluded_none(self) -> list[str]:
        """Constraints (on) that excluded no pair."""
        return [e.constraint for e in self.exclusion if e.alone == 0]


def choose(grid: Grid, na: Mapping[tuple[int, int], NeighbourAgreement], constraints: Constraints) -> Choice:
    """The Qualifying Pairs, the near-best set (NA ≥ max − tolerance) and the pick: smallest g, then smallest s."""
    reasons = {p: pair_reasons(grid.at(*p), na[p], constraints) for p in grid.pairs}
    qualifying = [p for p in grid.pairs if not reasons[p]]
    measurable = [p for p in grid.pairs if grid.at(*p).selected is not None and na[p].value is not None]
    exclusion, gone = [], set()
    for name, code in CONSTRAINT_ORDER:
        if name == "max_multi_tag_clusters" and constraints.max_multi_tag_clusters is None:
            continue
        alone = {p for p in measurable if code in reasons[p]}
        gone |= alone
        exclusion.append(ConstraintCount(name, len(alone), len(gone)))
    choice = Choice(status="no_qualifying_pair", chosen=None, max_na=None, best=None, near_best=[],
                    qualifying=qualifying, reasons=reasons, exclusion=exclusion, constraints=constraints,
                    n_pairs=len(grid.pairs), n_selected=sum(grid.at(*p).selected is not None for p in grid.pairs))
    if not qualifying:
        return choice
    values = {p: na[p].value or 0.0 for p in qualifying}  # every Qualifying Pair has NA
    top = max(values.values())
    near = [p for p in qualifying if values[p] >= top - constraints.tolerance - FLOAT_TOLERANCE]
    best = min(p for p in qualifying if values[p] == top)
    return replace(choice, status="ok", chosen=min(near), max_na=top, best=best, near_best=near)
