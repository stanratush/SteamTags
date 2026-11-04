"""Validation of one Threshold Pair: the Null Comparison and Subsample Stability.

The scope is the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the Selected Partition
rule), not the Parameter Grid or the choice of pair. Each replicate runs that whole procedure, plus a second arm at the
observed Selected Resolution γ_obs: the best of the replicate's own CHAMP envelope at γ_obs (never past its scan end)
and Leiden runs at exactly γ_obs with the scan seeds, which feed nothing else. A consistent null is analysed
identically [Karrer, Levina & Newman 2008].

Cluster-wise stability is Hennig's Jaccard [Hennig 2007 §2] on the tags that survive in a subsample, beside a
Whole-Cluster Jaccard that counts lost tags. Hennig's 0.5 applies per subsample; calling a Cluster "Dissolved in most
subsamples" when that holds in more than half of the B* assessable subsamples is this study's rule, not Hennig's. The
verdicts are that label (with Not assessable and borderline) and the Null Comparison's three states. The summary is
always derived from the stored records. Never mixed with the Seed-Noise Floor or Neighbour Agreement.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
from sklearn.metrics import adjusted_rand_score

import networkx as nx

from steamstudy.network import champ as C
from steamstudy.network.cluster import leiden_scan
from steamstudy.network.graph import build_network, filter_games, to_graph
from steamstudy.network.model import Game, Settings, TagContext
from steamstudy.network.selection import (
    VALIDATION_METHOD_VERSION,
    GraphResult,
    SelectionSettings,
    clusters_of,
    edge_arrays_of,
    scan_and_select,
)
from steamstudy.network.stability import TRADES_PER_GAME, curveball

METHOD_VERSION = VALIDATION_METHOD_VERSION
DISSOLVED = 0.5  # Hennig 2007 §2: J ≤ 0.5 in one subsample means the Cluster dissolved there (per subsample, not a mean)
RECOVERED = 0.75  # Hennig 2007 §2's own example of good recovery in one subsample ("say")
WILSON_Z = 1.96  # 95% Wilson intervals for the frequencies
ARMS = ("reselected", "at_resolution")


@dataclass(frozen=True)
class Observed:
    """What every replicate is compared with: the pair's Selected Partition and its numbers."""

    nodes: list[int]
    edged: list[int]
    selected: list[int]  # canonical membership in node order
    resolution: float
    q: float  # (Â − γP̂)/2m of the Selected Partition at the Selected Resolution
    width: float
    n_multi: int
    n_edges: int
    scan_length: int
    clusters: list[list[int]]  # Multi-Tag Clusters (label order C1…), the ones Hennig's Jaccard scores
    labels: list[str]

    @classmethod
    def of(cls, result: GraphResult) -> Observed:
        p = result.selected_partition
        if p is None or result.champ is None or result.selected_resolution is None:
            raise ValueError("validation needs a Selected Partition")
        gamma = result.selected_resolution
        multi = [c for c in clusters_of(result.nodes, p["membership"]) if c.size >= 2]
        return cls(result.nodes, result.edged, list(p["membership"]), gamma,
                   (p["a_hat"] - gamma * p["p_hat"]) / result.champ["two_m"], p["b"] - p["a"], p["n_multi"],
                   result.n_edges, result.scan_length, [sorted(c.members) for c in multi], [c.label for c in multi])


@dataclass(frozen=True)
class ReplicateTask:
    kind: str  # null or subsample
    index: int  # 1-based within its kind
    seed: int
    games: list[Game]
    context: TagContext
    settings: Settings  # the pair's
    scan_seeds: tuple[int, ...]
    gamma_step: float
    min_multi_tag_clusters: int
    observed: Observed
    weight: float  # the pair's edges × observed scan length


def validation_tasks(games: list[Game], settings: SelectionSettings, dataset: str, context: TagContext, g: int, s: int,
                     observed: GraphResult, seeds: tuple[list[int], list[int], list[int]]) -> list[ReplicateTask]:
    """R null tasks (stream 4) and S subsample tasks (stream 5), every one with the same 10 scan seeds."""
    scan, null, sub = seeds
    obs = Observed.of(observed)
    pair = settings.for_pair(dataset, context, g, s)
    weight = float(max(1, obs.n_edges) * max(1, obs.scan_length))
    base = ReplicateTask("null", 0, 0, games, context, pair, tuple(scan), settings.gamma_step,
                         settings.min_multi_tag_clusters, obs, weight)
    return ([replace(base, index=i, seed=seed) for i, seed in enumerate(null, start=1)]
            + [replace(base, kind="subsample", index=i, seed=seed) for i, seed in enumerate(sub, start=1)])


# ----------------------------------------------------------------------------- one replicate


def envelope_partition(result: C.ChampResult, gamma: float) -> C.AdmissiblePartition | None:
    """The Admissible Partition with the highest Q at γ (the smallest P̂ on a tie), inside [0, γ_end] only: past the
    scan end nothing is known, so nothing is returned (never an extrapolation of the lines)."""
    if not result.admissible or gamma > result.gamma_end:
        return None
    return max(result.admissible, key=lambda p: (p.a_hat - gamma * p.p_hat, -p.p_hat))


Best = tuple[tuple[int, ...], float]  # a canonical membership in node order, and its Q at γ


def runs_at(graph: nx.Graph, arrays: C.EdgeArrays, gamma: float, seeds: Iterable[int]) -> Best:
    """Leiden at exactly γ with the given seeds (the task's scan seeds): the run with the highest Q at γ, the first
    seed on a tie. Used for the fixed-γ figures only, never in a scan, CHAMP or a Selected Partition."""
    memberships = [C.canonical(r.membership) for r in leiden_scan(graph, [gamma], list(seeds))]
    a_hat, p_hat = C.partition_coefficients(memberships, arrays)
    qs = (a_hat - gamma * p_hat) / arrays.two_m
    best = int(np.argmax(qs))
    return tuple(int(x) for x in memberships[best]), float(qs[best])


@dataclass(frozen=True)
class AtGamma:
    """A network's partition and Q at γ_obs: the envelope's, or the explicit runs' when they find a higher Q."""

    membership: tuple[int, ...] | None
    q_envelope: float | None
    q: float | None
    reason: str | None  # beyond_scan
    changed: bool | None  # whether the runs replaced the envelope's partition


def at_gamma(result: C.ChampResult, gamma: float, runs: Best | None) -> AtGamma:
    """The fixed-γ arm's partition at γ: the best of the scan envelope and the runs at γ (`runs_at`)."""
    top = envelope_partition(result, gamma)
    if top is None:
        return AtGamma(None, None, None, "beyond_scan", None)
    q_env = (top.a_hat - gamma * top.p_hat) / result.two_m
    if runs is not None and runs[1] > q_env + 1e-12 * max(1.0, abs(q_env)):
        return AtGamma(runs[0], q_env, runs[1], None, True)
    return AtGamma(top.membership, q_env, q_env, None, False)


def _procedure(network_games: list[Game], settings: Settings, context: TagContext, task: ReplicateTask) -> dict[str, Any]:
    network = build_network(network_games, settings, context)
    out: dict[str, Any] = {"n_edges": len(network.edges), "scan_length": 0, "capped_runs": 0, "nodes": network.nodes,
                           "edged": [], "champ": None, "reason": "no_edges", "fixed": None}
    if not network.edges:
        return out
    graph = to_graph(network.nodes, network.edges, settings.clustering_weight)
    arrays = edge_arrays_of(network, settings.clustering_weight)
    scan, result = scan_and_select(graph, arrays, task.scan_seeds, task.gamma_step, task.min_multi_tag_clusters)
    # The fixed-γ arm, after the procedure and apart from it: the runs at γ_obs never reach the scan or CHAMP.
    gamma = task.observed.resolution
    runs = runs_at(graph, arrays, gamma, task.scan_seeds) if gamma <= result.gamma_end else None
    out.update({"scan_length": scan.n_runs // max(1, len(task.scan_seeds)), "capped_runs": scan.capped_runs,
                "edged": [t for t, e in zip(network.nodes, arrays.edged.tolist()) if e], "champ": result,
                "reason": result.reason, "fixed": at_gamma(result, gamma, runs)})
    return out


def observed_runs(task: ReplicateTask) -> dict[str, Any]:
    """The observed network's own runs at γ_obs, with the same γ and seeds as every replicate: stored beside the
    Selected Partition's Q, for the observed side of the Null Comparison only (the Selected Partition never moves)."""
    obs = task.observed
    network = build_network(task.games, task.settings, task.context)
    if network.nodes != obs.nodes:
        raise ValueError("the observed network does not match its Selected Partition")
    graph = to_graph(network.nodes, network.edges, task.settings.clustering_weight)
    arrays = edge_arrays_of(network, task.settings.clustering_weight)
    _, q = runs_at(graph, arrays, obs.resolution, task.scan_seeds)
    return {"q_selected": obs.q, "q_runs": q}


def shuffled_games(games: list[Game], tags: Iterable[int], seed: int) -> list[Game]:
    """Curveball over games × the pair's network tags, as the Workbench's null model: every tag keeps its game count
    and every game its tag count. Other tags are dropped (they are not in the network)."""
    visible = set(tags)
    names = {t: n for g in games for t, n in zip(g.tag_ids, g.tags)}
    rows = [frozenset(t for t in g.tag_ids if t in visible) for g in games]
    shuffled = curveball(rows, TRADES_PER_GAME * len(rows), random.Random(seed))
    return [replace(g, tag_ids=tuple(sorted(r)), tags=tuple(names[t] for t in sorted(r))) for g, r in zip(games, shuffled)]


def perturbation_share(before: list[Game], after: list[Game], tags: Iterable[int]) -> float | None:
    """The share of the game × visible-tag table's 1-cells that are 0 after the shuffle (Strona's diagnostic of how
    far the null moved from the observed table), with no threshold."""
    visible = set(tags)
    ones = lost = 0
    for b, a in zip(before, after, strict=True):
        row = {t for t in b.tag_ids if t in visible}
        ones += len(row)
        lost += len(row - set(a.tag_ids))
    return lost / ones if ones else None


def null_replicate(task: ReplicateTask) -> dict[str, Any]:
    obs = task.observed
    games = filter_games(task.games, task.settings.min_months)
    shuffled = shuffled_games(games, obs.nodes, task.seed)
    run = _procedure(shuffled, task.settings, task.context, task)
    result: C.ChampResult | None = run["champ"]
    chosen = None if result is None else result.selected_partition
    fixed: AtGamma | None = run["fixed"]
    return {
        "kind": "null", "index": task.index, "seed": task.seed, "n_edges": run["n_edges"],
        "scan_length": run["scan_length"], "capped_runs": run["capped_runs"], "reason": run["reason"],
        "selected": chosen is not None, "width": None if chosen is None else chosen.width,
        "resolution": None if chosen is None else chosen.midpoint, "n_multi": None if chosen is None else chosen.n_multi,
        "q_envelope": None if fixed is None else fixed.q_envelope, "q_fixed": None if fixed is None else fixed.q,
        "q_reason": "no_edges" if fixed is None else fixed.reason,
        "perturbation_share": perturbation_share(games, shuffled, obs.nodes),
    }


def subsample_thresholds(g: int, s: int, n: int) -> tuple[int, int, int]:
    """m = ⌊0.8·n⌋, g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋), in integer arithmetic."""
    m = (n * 4) // 5  # SUBSAMPLE_FRACTION, kept exact in integers
    return m, (g * m) // n if n else 0, max(2, (s * m) // n) if n else 2


def compare(obs: Observed, nodes: list[int], edged: list[int], labels: list[int] | None) -> dict[str, Any]:
    """On the NA comparison set (tags in both networks with an edge in at least one): ARI, and per observed Multi-Tag
    Cluster C, with C′ its surviving tags:
    - Hennig's Jaccard |C′ ∩ D′| / |C′ ∪ D′|, best match over every subsample Cluster D′ (One-Tag ones included),
      only when |C′| ≥ 2 (else None);
    - the Whole-Cluster Jaccard |C ∩ D′| / |C ∪ D′| with the whole Cluster, 0 when no tag survives, so lost tags count;
    - the surviving-tag count |C′| and the retention share |C′| / |C|.
    `labels` is the subsample partition in `nodes` order; None (a degenerate arm) leaves every figure None."""
    n = len(obs.clusters)
    if labels is None:
        return {"ari": None, "jaccard": [None] * n, "whole_jaccard": [None] * n, "survivors": [None] * n,
                "retention": [None] * n, "edged_share": None}
    present = set(nodes)
    any_edge = set(obs.edged) | set(edged)
    comparison = [t for t in obs.nodes if t in present and t in any_edge]
    keep = set(comparison)
    mine = dict(zip(obs.nodes, obs.selected))
    theirs = dict(zip(nodes, labels))
    ari = (float(adjusted_rand_score([mine[t] for t in comparison], [theirs[t] for t in comparison]))
           if comparison else None)
    groups: dict[int, set[int]] = {}
    for t in comparison:
        groups.setdefault(theirs[t], set()).add(t)
    jaccard: list[float | None] = []
    whole: list[float | None] = []
    survivors: list[int | None] = []
    retention: list[float | None] = []
    for cluster in obs.clusters:
        full = set(cluster)
        restricted = full & keep
        survivors.append(len(restricted))
        retention.append(len(restricted) / len(cluster))
        whole.append(max((len(full & d) / len(full | d) for d in groups.values()), default=0.0))
        # Fewer than two surviving tags: Hennig's Jaccard is not assessable (one tag always matches itself).
        jaccard.append(max(len(restricted & d) / len(restricted | d) for d in groups.values())
                       if len(restricted) >= 2 else None)
    edged_share = len(set(obs.edged) & keep) / len(obs.edged) if obs.edged else None
    return {"ari": ari, "jaccard": jaccard, "whole_jaccard": whole, "survivors": survivors, "retention": retention,
            "edged_share": edged_share}


def subsample_replicate(task: ReplicateTask) -> dict[str, Any]:
    obs = task.observed
    games = filter_games(task.games, task.settings.min_months)
    rng = random.Random(task.seed)
    m, g2, s2 = subsample_thresholds(task.settings.min_games_per_tag, task.settings.min_shared_games, len(games))
    sample = sorted(rng.sample(games, m), key=lambda g: g.rank)
    settings = task.settings.with_(min_games_per_tag=g2, min_shared_games=s2)
    run = _procedure(sample, settings, task.context, task)
    result: C.ChampResult | None = run["champ"]
    arms: dict[str, dict[str, Any]] = {}
    if result is None:
        for arm in ARMS:
            arms[arm] = {"degenerate": "no_edges", **compare(obs, run["nodes"], run["edged"], None)}
    else:
        chosen = result.selected_partition
        arms["reselected"] = {
            "degenerate": None if chosen is not None else result.reason,
            **compare(obs, run["nodes"], run["edged"], None if chosen is None else list(chosen.membership)),
            "resolution": None if chosen is None else chosen.midpoint,
            "n_multi": None if chosen is None else chosen.n_multi,
        }
        fixed: AtGamma = run["fixed"]
        arms["at_resolution"] = {
            "degenerate": fixed.reason,
            **compare(obs, run["nodes"], run["edged"], None if fixed.membership is None else list(fixed.membership)),
            "q_envelope": fixed.q_envelope, "q": fixed.q, "at_resolution_changed": fixed.changed,
        }
    return {"kind": "subsample", "index": task.index, "seed": task.seed, "m": m, "g": g2, "s": s2,
            "n_edges": run["n_edges"], "scan_length": run["scan_length"], "capped_runs": run["capped_runs"],
            "arms": arms}


def run_replicate(task: ReplicateTask) -> dict[str, Any]:
    return null_replicate(task) if task.kind == "null" else subsample_replicate(task)


def run_validation(tasks: list[ReplicateTask], *, map_fn: Callable[..., Iterable[Any]] = map,
                   on_result: Callable[[dict[str, Any], float], None] | None = None,
                   should_stop: Callable[[], bool] | None = None) -> list[dict[str, Any]] | None:
    """Every replicate's record sorted by kind and index, or None when stopped (all-or-nothing)."""
    stop = should_stop or (lambda: False)
    ordered = sorted(tasks, key=lambda t: (t.kind, t.index))

    def feed() -> Iterator[ReplicateTask]:
        for task in ordered:
            if stop():
                return
            yield task

    records = []
    for record in map_fn(run_replicate, feed()):
        records.append(record)
        if on_result is not None:
            on_result(record, tasks[0].weight)
        if stop():
            return None
    if len(records) < len(tasks):
        return None
    return sorted(records, key=lambda r: (r["kind"], r["index"]))


# ----------------------------------------------------------------------------- summary and verdicts


def _spread(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "min": None, "max": None}
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def _se(values: list[float]) -> float | None:
    """The Monte Carlo standard error of a mean, sd/√n (None under two values)."""
    return statistics.stdev(values) / math.sqrt(len(values)) if len(values) >= 2 else None


def _pct(values: list[float], q: float) -> float | None:
    return float(np.percentile(values, q)) if values else None


def wilson(k: int, n: int, z: float = WILSON_Z) -> tuple[float | None, float | None]:
    """The Wilson score interval of k of n [Wilson 1927]; (None, None) when n = 0."""
    if n == 0:
        return None, None
    p = k / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z / denominator * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


def _cluster_summary(label: str, members: list[int], good: list[dict[str, Any]], i: int) -> dict[str, Any]:
    """One Multi-Tag Cluster in one arm, over the S non-degenerate subsamples `good`."""
    survivors = [x["survivors"][i] for x in good]
    hennig = [x["jaccard"][i] for x in good if x["jaccard"][i] is not None]  # the B* subsamples with |C′| ≥ 2
    whole = [x["whole_jaccard"][i] for x in good]
    b = len(hennig)
    dissolved = sum(v <= DISSOLVED for v in hennig)
    recovered = sum(v > RECOVERED for v in hennig)
    low, high = wilson(dissolved, b)
    r_low, r_high = wilson(recovered, b)
    return {
        "label": label, "members": members, "size": len(members), "assessable_subsamples": b,
        "one_tag_left": sum(s == 1 for s in survivors), "absent": sum(s == 0 for s in survivors),
        "mean_retention": statistics.fmean(x["retention"][i] for x in good) if good else None,
        "mean_jaccard": statistics.fmean(hennig) if hennig else None, "mean_jaccard_se": _se(hennig),
        "jaccard_p10": _pct(hennig, 10), "jaccard_p90": _pct(hennig, 90),
        "at_most_half": dissolved, "dissolution_frequency": dissolved / b if b else None,
        "wilson_low": low, "wilson_high": high,
        "recovered": recovered, "recovery_frequency": recovered / b if b else None,
        "recovery_wilson_low": r_low, "recovery_wilson_high": r_high,
        "mean_whole_cluster_jaccard": statistics.fmean(whole) if whole else None,
        "whole_cluster_jaccard_se": _se(whole), "whole_cluster_p10": _pct(whole, 10),
        "whole_cluster_p90": _pct(whole, 90),
        # Statuses: Not assessable, then Dissolved in most subsamples (a strict majority of B*, on the point
        # estimate; exactly half is not labelled), and borderline (the Wilson interval contains ½, labelled or not).
        "assessable": b > 0, "dissolved_in_most": 2 * dissolved > b,
        "borderline": b > 0 and low is not None and high is not None and low <= 0.5 <= high,
        "rarely_assessable": 2 * b < len(good),  # a flag, not a status: B* < S/2
    }


def _arm_summary(obs: Observed, records: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    rows = [r["arms"][arm] for r in records]
    good = [x for x in rows if x["degenerate"] is None]
    aris = [x["ari"] for x in good if x["ari"] is not None]
    clusters = [_cluster_summary(label, members, good, i)
                for i, (label, members) in enumerate(zip(obs.labels, obs.clusters))]
    shares = [x["edged_share"] for x in good if x["edged_share"] is not None]
    out: dict[str, Any] = {
        "n": len(rows), "degenerate": len(rows) - len(good),
        "reasons": dict(sorted(Counter(x["degenerate"] for x in rows if x["degenerate"] is not None).items())),
        "ari": {"median": statistics.median(aris) if aris else None, "p10": _pct(aris, 10), "p90": _pct(aris, 90),
                "min": min(aris) if aris else None},
        "clusters": clusters, "edged_share_mean": statistics.fmean(shares) if shares else None,
    }
    if arm == "reselected":
        out["resolution"] = _spread([x["resolution"] for x in good])
        out["n_multi"] = _spread([x["n_multi"] for x in good])
    else:
        out["changed"] = sum(bool(x.get("at_resolution_changed")) for x in good)
    return out


def _null_summary(observed: Observed, nulls: list[dict[str, Any]],
                  observed_runs: Mapping[str, Any] | None) -> dict[str, Any]:
    """The Null Comparison over the R nulls: Q over the D with a defined Q at γ_obs, U = R − D with its reasons, and
    width and Multi-Tag Clusters over the K with a Selected Partition."""
    selected = [r for r in nulls if r["selected"]]
    defined = [r["q_fixed"] for r in nulls if r["q_fixed"] is not None]
    q_selected = observed.q
    q_runs = None if observed_runs is None else observed_runs.get("q_runs")
    from_runs = q_runs is not None and q_runs > q_selected + 1e-12 * max(1.0, abs(q_selected))
    q_observed = q_runs if from_runs else q_selected
    reach = sum(q >= q_observed for q in defined)  # reaching means ≥
    undefined = Counter(r.get("q_reason") or "no_edges" for r in nulls if r["q_fixed"] is None)
    edges = [r["n_edges"] for r in nulls]
    shares = [r["perturbation_share"] for r in nulls if r.get("perturbation_share") is not None]
    return {
        "replicates": len(nulls), "selected": len(selected),
        "reasons": dict(sorted(Counter(r["reason"] for r in nulls if not r["selected"]).items())),
        "q_defined": len(defined), "q_undefined": len(nulls) - len(defined),
        "q_undefined_reasons": dict(sorted(undefined.items())), "weak": 2 * len(defined) < len(nulls),
        "width": {"observed": observed.width, **_spread([r["width"] for r in selected]),
                  "wider": sum(r["width"] < observed.width for r in selected),
                  "equal": sum(r["width"] == observed.width for r in selected)},
        "resolution": {"observed": observed.resolution, **_spread([r["resolution"] for r in selected])},
        "n_multi": {"observed": observed.n_multi, **_spread([r["n_multi"] for r in selected])},
        "q": {"observed": q_observed, "observed_selected": q_selected, "observed_runs": q_runs,
              "observed_from_runs": from_runs, **_spread(defined), "reach": reach},
        "edges": {"observed": observed.n_edges, "null_median": statistics.median(edges) if edges else None,
                  "ratio": observed.n_edges / statistics.median(edges) if edges and statistics.median(edges) else None},
        "perturbation_share": _spread(shares),
        "scan_length_total": sum(r["scan_length"] for r in nulls), "capped_total": sum(r["capped_runs"] for r in nulls),
    }


def null_state(null: Mapping[str, Any]) -> str:
    """above_all_defined (D ≥ 1, none reaches), reached (one or more reach), undefined (D = 0)."""
    if not null["q_defined"]:
        return "undefined"
    return "reached" if null["q"]["reach"] else "above_all_defined"


def summarise(observed: Observed, records: list[dict[str, Any]],
              observed_runs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Every reported figure, from the records alone: the Null Comparison and, per arm and Multi-Tag Cluster, both
    Jaccards, the frequencies with Wilson intervals and the statuses; then the verdicts."""
    nulls = [r for r in records if r["kind"] == "null"]
    subs = [r for r in records if r["kind"] == "subsample"]
    null = _null_summary(observed, nulls, observed_runs)
    sub = {arm: _arm_summary(observed, subs, arm) for arm in ARMS}
    first = subs[0] if subs else {"m": None, "g": None, "s": None}

    def labels(arm: str, key: str, value: bool = True) -> list[str]:
        return [c["label"] for c in sub[arm]["clusters"] if c[key] is value]

    return {
        "method_version": METHOD_VERSION, "resolution": observed.resolution, "null": null,
        "subsample": {"subsamples": len(subs), "m": first["m"], "g": first["g"], "s": first["s"],
                      "scan_length_total": sum(r["scan_length"] for r in subs),
                      "capped_total": sum(r["capped_runs"] for r in subs), **sub},
        "verdicts": {"null_q": null_state(null),
                     "dissolved_in_most": {arm: labels(arm, "dissolved_in_most") for arm in ARMS},
                     "borderline": {arm: labels(arm, "borderline") for arm in ARMS},
                     "not_assessable": {arm: labels(arm, "assessable", False) for arm in ARMS},
                     "rarely_assessable": any(c["rarely_assessable"] for arm in ARMS for c in sub[arm]["clusters"])},
    }


def summary_from_records(observed: GraphResult, validation: Mapping[str, Any]) -> dict[str, Any]:
    """The summary every reader shows (card, Inspector, export, report), derived from a validation file's records and
    observed runs, never stored, so a summary-only change needs no version bump."""
    return summarise(Observed.of(observed), validation["records"], validation.get("observed"))


def records_by_kind(records: list[dict[str, Any]]) -> Mapping[str, list[dict[str, Any]]]:
    return {"null": [r for r in records if r["kind"] == "null"],
            "subsample": [r for r in records if r["kind"] == "subsample"]}
