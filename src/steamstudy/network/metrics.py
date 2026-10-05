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


def connections(graph: nx.Graph, clusters: list[Cluster]) -> list[tuple[str, str, int, float]]:
    """(cluster_a, cluster_b, edge_count, weight) for every unordered Multi-Tag pair, plus one_tag_pool pairs."""
    multi = [c.label for c in clusters if c.size >= 2]
    singles = [c for c in clusters if c.size == 1]
    group = {t: (c.label if c.size >= 2 else "one_tag_pool") for c in clusters for t in c.members}
    counts: dict[tuple[str, str], list[float]] = {}
    order = {label: i for i, label in enumerate([*multi, "one_tag_pool"])}
    for u, v, d in graph.edges(data=True):
        a, b = group[u], group[v]
        if a == b and a != "one_tag_pool":
            continue
        a, b = sorted((a, b), key=order.__getitem__)
        entry = counts.setdefault((a, b), [0, 0.0])
        entry[0] += 1
        entry[1] += d["w"]
    pairs = [(a, b) for i, a in enumerate(multi) for b in multi[i + 1:]]
    if singles:
        pairs += [(a, "one_tag_pool") for a in multi]
        if len(singles) >= 2:
            pairs.append(("one_tag_pool", "one_tag_pool"))
    return [(a, b, int(counts.get((a, b), [0, 0.0])[0]), float(counts.get((a, b), [0, 0.0])[1])) for a, b in pairs]


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
