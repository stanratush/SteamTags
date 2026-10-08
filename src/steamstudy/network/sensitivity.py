"""Removal Sensitivity: a what-if over one Network State that never changes the state.

For each tested tag v, two readings over the shared tag set (every tag except v):
- reclustered (`rc_*`): drop v and its edges, recluster from scratch with the main seed;
- fixed partition (`fp_*`): drop v, keep every other tag in its cluster.
Every Δ is after − before. `rc_ari_beyond_noise` = rc_ari < seed_ari_min (read, never recomputed).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from steamstudy.network import metrics as M
from steamstudy.network.cluster import Cluster, label_clusters, membership
from steamstudy.network.stability import ari
from steamstudy.network.state import NetworkState, cluster_graph

METHOD_VERSION = "removal-sensitivity-1"


def run_order(state: NetworkState) -> list[int]:
    """Active strength descending, then tag_id: a partial run is a prefix of the full one."""
    return sorted(state.nodes, key=lambda t: (-state.active_strength(t), t))


def _delta(after: float | None, before: float | None) -> float | None:
    return None if after is None or before is None else after - before


def _centers(clusters: list[Cluster], state: NetworkState, tags: list[int]) -> set[int]:
    index = {t: state.index[t] for t in tags}
    intra = {}
    cluster_of = {t: c for c in clusters for t in c.members}
    for t in tags:
        members = cluster_of[t].members
        attr = "shared" if state.settings.clustering_weight == "shared_games" else "lift"
        intra[t] = sum(d[attr] for u, d in state.graph[t].items() if u in members and u in index)
    centers = set()
    for c in clusters:
        result = M.center_of(c, index, state.distances, state.network.tag_games, intra)
        if result.center is not None:
            centers.add(result.center)
    return centers


def removal_row(state: NetworkState, tag: int, order: int) -> dict[str, Any]:
    names = state.network.tag_names
    remaining = [t for t in state.nodes if t != tag]
    graph = state.graph.copy()
    graph.remove_node(tag)
    seed_summary = state.seed_summary()
    sil_before = state.silhouette.mean
    q_before = state.modularity

    # reclustered from scratch (cold restart, main seed)
    rc_clusters = cluster_graph(graph, state.settings, state.settings.seed)
    sub = state.distances[[state.index[t] for t in remaining]][:, [state.index[t] for t in remaining]]
    rc_q = M.modularity(graph, rc_clusters, state.settings.resolution)
    rc_sil = M.silhouette(remaining, rc_clusters, state.network.tag_games, sub)
    rc_ari = ari(remaining, state.cluster_of, membership(rc_clusters))
    before_k = len(state.multi_tag_clusters)
    before_s = len(state.clusters) - before_k
    rc_k = sum(c.size >= 2 for c in rc_clusters)
    lost = sorted((state.center_tags() - {tag}) - _centers(rc_clusters, state, remaining))

    # partition fixed
    fp_clusters = label_clusters([frozenset(c.members - {tag}) for c in state.clusters if c.members - {tag}])
    fp_q = M.modularity(graph, fp_clusters, state.settings.resolution)
    fp_sil = M.silhouette(remaining, fp_clusters, state.network.tag_games, sub)

    seed_ari_min = seed_summary["seed_ari_min"]
    return {
        "run_order": order, "tag_id": tag, "tag": names[tag], "cluster": state.cluster_of[tag],
        "is_center": state.is_center(tag), "active_strength": state.active_strength(tag),
        "rc_delta_modularity": _delta(rc_q, q_before),
        "rc_silhouette_after": rc_sil.mean, "rc_silhouette_after_status": rc_sil.status,
        "rc_delta_silhouette": _delta(rc_sil.mean, sil_before),
        "rc_delta_k": rc_k - before_k, "rc_delta_s": (len(rc_clusters) - rc_k) - before_s,
        "rc_ari": rc_ari, "rc_centers_lost_tag_ids": lost, "rc_centers_lost": [names[t] for t in lost],
        "rc_ari_beyond_noise": bool(seed_ari_min is not None and rc_ari < float(seed_ari_min)),
        "fp_delta_modularity": _delta(fp_q, q_before),
        "fp_silhouette_after": fp_sil.mean, "fp_silhouette_after_status": fp_sil.status,
        "fp_delta_silhouette": _delta(fp_sil.mean, sil_before),
    }


def removal_sensitivity(
    state: NetworkState,
    tags: list[int] | None = None,
    *,
    skip: set[int] | frozenset[int] = frozenset(),
    progress: Callable[[int, int], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    on_row: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """Rows for the given tags (default: every node) in run order; stops early when `should_stop()` is true."""
    order = run_order(state)
    position = {t: i for i, t in enumerate(order, start=1)}
    todo = [t for t in order if (tags is None or t in tags) and t not in skip]
    rows = []
    for done, tag in enumerate(todo, start=1):
        if should_stop is not None and should_stop():
            break
        row = removal_row(state, tag, position[tag])
        rows.append(row)
        if on_row is not None:
            on_row(row)
        if progress is not None:
            progress(done, len(todo))
    return rows


def expected_chance_flags(n_tags: int, k: int) -> float:
    """If removals acted only like another seed, about n / (K + 1) tags would be flagged on average."""
    return n_tags / (k + 1)
