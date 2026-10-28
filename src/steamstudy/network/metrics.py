"""Partition metrics: modularity, coverage, Jaccard silhouette, per-cluster and per-node metrics, centers.

Weighted values use the active Clustering Weight (edge attribute `w`); Jaccard game-set measures
(silhouette, medoid, Membership Stability) and degrees never depend on it.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

import networkx as nx
import numpy as np

from steamstudy.network.cluster import Cluster

FEWER_THAN_2 = "fewer_than_2_multi_tag_clusters"
ONE_TAG = "one_tag_cluster"
TIE_DECIMALS = 12


# ----------------------------------------------------------------------------- Jaccard


def jaccard_distances(tags: list[int], tag_games: dict[int, frozenset[int]]) -> np.ndarray:
    """d(u, v) = 1 - |G_u ∩ G_v| / |G_u ∪ G_v| over the N games, in the given tag order."""
    n = len(tags)
    d = np.zeros((n, n))
    sets = [tag_games[t] for t in tags]
    for i in range(n):
        for j in range(i + 1, n):
            union = len(sets[i] | sets[j])
            value = 1.0 - (len(sets[i] & sets[j]) / union if union else 0.0)
            d[i, j] = d[j, i] = value
    return d


# ----------------------------------------------------------------------------- modularity and coverage


def total_weight(graph: nx.Graph) -> float:
    return math.fsum(d["w"] for _, _, d in graph.edges(data=True))


def modularity(graph: nx.Graph, clusters: list[Cluster], resolution: float) -> float | None:
    """Weighted Q at γ over the whole network (isolated tags contribute 0); None when there are no edges."""
    if graph.number_of_edges() == 0 or total_weight(graph) == 0:
        return None
    return float(nx.community.modularity(graph, [c.members for c in clusters], weight="w", resolution=resolution))


def coverage(graph: nx.Graph, cluster_of: dict[int, str]) -> float | None:
    total = total_weight(graph)
    if total == 0:
        return None
    intra = math.fsum(d["w"] for u, v, d in graph.edges(data=True) if cluster_of[u] == cluster_of[v])
    return intra / total


# ----------------------------------------------------------------------------- silhouette


@dataclass(frozen=True)
class Silhouette:
    per_node: dict[int, float | None]
    node_status: dict[int, str | None]
    per_cluster: dict[str, float | None]
    cluster_status: dict[str, str | None]
    mean: float | None
    status: str | None


def silhouette(tags: list[int], clusters: list[Cluster], tag_games: dict[int, frozenset[int]],
               distances: np.ndarray | None = None) -> Silhouette:
    """Jaccard game-set silhouette on the full partition.

    One-Tag Clusters count as "other clusters" for b(i); their own s = 0 is left out of every mean.
    n/a (`fewer_than_2_multi_tag_clusters`) with fewer than 2 Multi-Tag Clusters.
    """
    from sklearn.metrics import silhouette_samples

    multi = [c for c in clusters if c.size >= 2]
    cluster_of = {t: c for c in clusters for t in c.members}
    if len(multi) < 2:
        na_status: dict[int, str | None] = {t: (ONE_TAG if cluster_of[t].size == 1 else FEWER_THAN_2) for t in tags}
        na_cluster: dict[str, str | None] = {c.label: (ONE_TAG if c.size == 1 else FEWER_THAN_2) for c in clusters}
        return Silhouette({t: None for t in tags}, na_status, {c.label: None for c in clusters}, na_cluster, None,
                          FEWER_THAN_2)
    d = distances if distances is not None else jaccard_distances(tags, tag_games)
    labels = [cluster_of[t].label for t in tags]
    samples = silhouette_samples(d, labels, metric="precomputed")
    per_node: dict[int, float | None] = {}
    node_status: dict[int, str | None] = {}
    for t, s in zip(tags, samples):
        if cluster_of[t].size == 1:
            per_node[t], node_status[t] = None, ONE_TAG
        else:
            per_node[t], node_status[t] = float(s), None
    per_cluster: dict[str, float | None] = {}
    cluster_status: dict[str, str | None] = {}
    for c in clusters:
        if c.size == 1:
            per_cluster[c.label], cluster_status[c.label] = None, ONE_TAG
        else:
            per_cluster[c.label] = math.fsum(per_node[t] for t in c.members) / c.size  # type: ignore[misc]
            cluster_status[c.label] = None
    values = [v for t, v in per_node.items() if v is not None]
    return Silhouette(per_node, node_status, per_cluster, cluster_status, math.fsum(values) / len(values), None)


# ----------------------------------------------------------------------------- per-cluster


@dataclass(frozen=True)
class ClusterMetrics:
    internal_edges: int
    internal_weight: float
    edge_density: float | None
    weighted_density: float | None
    cut_weight: float
    conductance: float | None
    conductance_status: str | None
    connected: bool


def cluster_metrics(graph: nx.Graph, cluster: Cluster) -> ClusterMetrics:
    members = cluster.members
    internal = [(u, v, d["w"]) for u, v, d in graph.edges(members, data=True) if u in members and v in members]
    internal_weight = math.fsum(w for _, _, w in internal)
    cut = math.fsum(d["w"] for u, v, d in graph.edges(members, data=True) if (u in members) != (v in members))
    pairs = cluster.size * (cluster.size - 1) / 2
    vol_c = math.fsum(graph.degree(t, weight="w") for t in members)
    vol_rest = math.fsum(graph.degree(t, weight="w") for t in graph.nodes if t not in members)
    if vol_c == 0:
        conductance, status = None, "isolated_tag"
    elif vol_rest <= 1e-9 * max(vol_c, 1.0):  # zero up to float rounding of summed lift weights
        conductance, status = None, "no_edges_outside_cluster"
    else:
        conductance, status = cut / min(vol_c, vol_rest), None
    connected = cluster.size == 1 or nx.is_connected(graph.subgraph(members))
    return ClusterMetrics(
        internal_edges=len(internal), internal_weight=internal_weight,
        edge_density=len(internal) / pairs if pairs else None,
        weighted_density=internal_weight / pairs if pairs else None,
        cut_weight=cut, conductance=conductance, conductance_status=status, connected=connected,
    )


POOL = "one_tag_pool"


@dataclass(frozen=True)
class Connection:
    """The links between two Clusters (or with the pooled One-Tag Clusters): their count and weight, the shared-game
    total, the Connection Ratio in the Clustering Weight and in shared games, and both Connection Shares. A ratio or
    share is None where its denominator is zero; values are never clamped (ADR 0004)."""

    cluster_a: str
    cluster_b: str
    edge_count: int
    weight: float
    shared_weight: float
    ratio: float | None
    shared_ratio: float | None
    share_of_a: float | None
    share_of_b: float | None


def _strengths(graph: nx.Graph, group: dict[int, str], attr: str) -> tuple[dict[str, float], dict[str, float], float]:
    """Each group's strength k (summed tag strengths), the sum of its tags' squared strengths, and 2m."""
    k: dict[str, float] = {}
    squares: dict[str, float] = {}
    for t, label in group.items():
        kt = float(graph.degree(t, weight=attr)) if t in graph else 0.0
        k[label] = k.get(label, 0.0) + kt
        squares[label] = squares.get(label, 0.0) + kt * kt
    return k, squares, math.fsum(k.values())


def _ratio(w: float, a: str, b: str, k: dict[str, float], squares: dict[str, float], two_m: float) -> float | None:
    """w over the weight the strengths alone predict: k_a·k_b/2m, or over distinct pool pairs (k_p² − Σk_i²)/4m."""
    if two_m <= 0:
        return None
    expected = (k[a] ** 2 - squares[a]) / (2 * two_m) if a == b else k[a] * k[b] / two_m
    return w / expected if expected > 0 else None


def connections(graph: nx.Graph, clusters: list[Cluster]) -> list[Connection]:
    """Every unordered Multi-Tag pair, plus one_tag_pool pairs (spec: "Connection Ratio and Connection Share").

    k_a is a group's strength in the Clustering Weight (attribute `w`; 2·internal + cut for a Cluster) and 2m their
    sum. A Cluster's cut is all its weight to other groups; the pool's is all weight touching its tags with pool-pool
    links once (k_p − w_pp), so every group's shares add up to 1. The shared-game total and ratio use the same sums
    over the `shared` attribute."""
    multi = [c.label for c in clusters if c.size >= 2]
    singles = [c for c in clusters if c.size == 1]
    group = {t: (c.label if c.size >= 2 else POOL) for c in clusters for t in c.members}
    counts: dict[tuple[str, str], list[float]] = {}
    order = {label: i for i, label in enumerate([*multi, POOL])}
    cut: dict[str, float] = {}
    for u, v, d in graph.edges(data=True):
        a, b = group[u], group[v]
        if a != b:
            cut[a] = cut.get(a, 0.0) + d["w"]
            cut[b] = cut.get(b, 0.0) + d["w"]
        elif a == POOL:
            cut[a] = cut.get(a, 0.0) + d["w"]
        if a == b and a != POOL:
            continue
        a, b = sorted((a, b), key=order.__getitem__)
        entry = counts.setdefault((a, b), [0, 0.0, 0.0])
        entry[0] += 1
        entry[1] += d["w"]
        entry[2] += d["shared"]
    pairs = [(a, b) for i, a in enumerate(multi) for b in multi[i + 1:]]
    if singles:
        pairs += [(a, POOL) for a in multi]
        if len(singles) >= 2:
            pairs.append((POOL, POOL))
    k, squares, two_m = _strengths(graph, group, "w")
    ks, squares_s, two_m_s = _strengths(graph, group, "shared")
    out = []
    for a, b in pairs:
        n, w, shared = counts.get((a, b), [0, 0.0, 0.0])
        share = lambda label: w / cut[label] if cut.get(label) else None  # noqa: E731
        out.append(Connection(a, b, int(n), float(w), float(shared), _ratio(w, a, b, k, squares, two_m),
                              _ratio(shared, a, b, ks, squares_s, two_m_s), share(a), share(b)))
    return out


# ----------------------------------------------------------------------------- per-node and centers


@dataclass(frozen=True)
class NodeMetrics:
    degree: int
    degree_intra: int
    strength_shared: float
    strength_lift: float
    strength_shared_intra: float
    strength_lift_intra: float
    within_z: float | None
    participation: float | None


def node_metrics(graph: nx.Graph, clusters: list[Cluster], clustering_weight: str) -> dict[int, NodeMetrics]:
    cluster_of = {t: c for c in clusters for t in c.members}
    active = "shared" if clustering_weight == "shared_games" else "lift"
    out: dict[int, NodeMetrics] = {}
    intra_active: dict[int, float] = {}
    raw: dict[int, dict[str, float | int]] = {}
    for t in graph.nodes:
        members = cluster_of[t].members
        nbrs = graph[t]
        s_shared = math.fsum(d["shared"] for d in nbrs.values())
        s_lift = math.fsum(d["lift"] for d in nbrs.values())
        intra = {u: d for u, d in nbrs.items() if u in members}
        raw[t] = {
            "degree": len(nbrs), "degree_intra": len(intra), "s_shared": s_shared, "s_lift": s_lift,
            "si_shared": math.fsum(d["shared"] for d in intra.values()),
            "si_lift": math.fsum(d["lift"] for d in intra.values()),
        }
        intra_active[t] = float(raw[t]["si_shared"] if active == "shared" else raw[t]["si_lift"])
    for t in graph.nodes:
        c = cluster_of[t]
        within: float | None = None
        if c.size >= 2:
            values = [intra_active[m] for m in c.members]
            sd = statistics.pstdev(values)
            if sd > 0:
                within = (intra_active[t] - statistics.fmean(values)) / sd
        k = raw[t]["s_shared"] if active == "shared" else raw[t]["s_lift"]
        participation: float | None = None
        if k > 0:
            to_cluster: dict[str, float] = {}
            for u, d in graph[t].items():
                to_cluster[cluster_of[u].label] = to_cluster.get(cluster_of[u].label, 0.0) + d[active]
            participation = 1.0 - math.fsum((s / k) ** 2 for s in to_cluster.values())
        r = raw[t]
        out[t] = NodeMetrics(int(r["degree"]), int(r["degree_intra"]), float(r["s_shared"]), float(r["s_lift"]),
                             float(r["si_shared"]), float(r["si_lift"]), within, participation)
    return out


def within_z_cap(size: int) -> float:
    """The largest possible within_z in an n-tag cluster: sqrt(n - 1)."""
    return math.sqrt(size - 1)


@dataclass(frozen=True)
class Center:
    medoid_scores: dict[int, float]  # members of clusters with 2+ tags
    center: int | None
    center_status: str | None
    top_strength: int | None


def medoid_scores(members: list[int], index: dict[int, int], distances: np.ndarray) -> dict[int, float]:
    out = {}
    for t in members:
        others = [m for m in members if m != t]
        out[t] = math.fsum(float(distances[index[t], index[m]]) for m in others) / len(others)
    return out


def center_of(cluster: Cluster, index: dict[int, int], distances: np.ndarray, tag_games: dict[int, frozenset[int]],
              intra_strength: dict[int, float]) -> Center:
    if cluster.size == 1:
        return Center({}, None, "one_tag_cluster", None)
    members = sorted(cluster.members)
    scores = medoid_scores(members, index, distances)
    if cluster.size == 2:
        return Center(scores, None, "two_tag_cluster", None)
    center = min(members, key=lambda t: (round(scores[t], TIE_DECIMALS), -len(tag_games[t]), t))
    top = min(members, key=lambda t: (-round(intra_strength[t], TIE_DECIMALS), -len(tag_games[t]), t))
    return Center(scores, center, None, top)


def member_order(members: frozenset[int], scores: dict[int, float], tag_games: dict[int, frozenset[int]]) -> list[int]:
    """Members by medoid_score, then the center tie-break (more games, lower tag_id)."""
    return sorted(members, key=lambda t: (round(scores[t], TIE_DECIMALS) if t in scores else math.inf,
                                          -len(tag_games[t]), t))
