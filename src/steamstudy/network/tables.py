"""The network tables of one Network State: one writer for the app export and the Build.

`state_tables(state, layout)` gives the app zip's rows; `stack(rows, dataset, state_id)` prefixes them for the
Build's stacked `analysis/network_*.csv` files. Both are validated against `steamstudy.export.schema`.
Coordinates are an input, computed after the state by the layout (ADR 0002), never here.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Protocol

from steamstudy.network.cluster import label_order
from steamstudy.network.metrics import member_order
from steamstudy.network.state import NetworkState

Rows = list[dict[str, Any]]
Positions = Mapping[int, tuple[float, float]]


class Coordinates(Protocol):
    """What the tables read of a layout: the Global and the Cluster-separated positions."""

    @property
    def positions(self) -> Positions: ...

    @property
    def separated(self) -> Positions: ...


def state_tables(state: NetworkState, layout: Coordinates | None = None) -> dict[str, Rows]:
    """Every app-export table except removal_sensitivity.csv, keyed by file name. Without a layout the four
    coordinate columns are empty."""
    positions = layout.positions if layout is not None else {}
    cluster_positions = layout.separated if layout is not None else {}
    return {
        "nodes.csv": node_rows(state, positions, cluster_positions),
        "edges.csv": edge_rows(state),
        "clusters.csv": cluster_rows(state),
        "cluster_quality.csv": [cluster_quality_row(state)],
        "cluster_connections.csv": [
            {"cluster_a": a, "cluster_b": b, "edge_count": n, "weight": w} for a, b, n, w in state.connections],
        "null_model.csv": [{"replicate": r.replicate, "seed": r.seed, "modularity": r.modularity, "n_edges": r.n_edges}
                           for r in state.null_replicates],
        "seed_noise.csv": [
            {"noise_seed_index": r.index, "seed": r.seed, "modularity": r.modularity, "silhouette": r.silhouette,
             "silhouette_status": r.silhouette_status, "ari_vs_main": r.ari_vs_main,
             "n_multi_tag_clusters": r.n_multi, "n_one_tag_clusters": r.n_single} for r in state.seed_runs],
        "not_in_network.csv": [{"tag_id": n.tag_id, "tag": n.tag, "n_games": n.n_games, "reasons": list(n.reasons)}
                               for n in state.network.not_in_network],
    }


def stack(rows: Rows, dataset: str, state_id: str) -> Rows:
    return [{"dataset": dataset, "state_id": state_id, **r} for r in rows]


def node_rows(state: NetworkState, positions: Positions, cluster_positions: Positions) -> Rows:
    names = state.network.tag_names
    rows = []
    for t in state.nodes:
        m = state.node_metrics[t]
        x, y = positions.get(t, (None, None))
        cx, cy = cluster_positions.get(t, (None, None))
        rows.append({
            "tag_id": t, "tag": names[t], "cluster": state.cluster_of[t], "n_games": state.network.n(t),
            "is_isolated": m.degree == 0, "degree": m.degree, "degree_intra": m.degree_intra,
            "strength_shared": m.strength_shared, "strength_lift": m.strength_lift,
            "strength_shared_intra": m.strength_shared_intra, "strength_lift_intra": m.strength_lift_intra,
            "silhouette": state.silhouette.per_node[t], "silhouette_status": state.silhouette.node_status[t],
            "medoid_score": state.medoid_score(t), "is_center": state.is_center(t),
            "within_z": m.within_z, "participation": m.participation,
            "membership_stability": state.membership_stability[t],
            "x_global": x, "y_global": y, "x_cluster_separated": cx, "y_cluster_separated": cy,
        })
    rows.sort(key=_node_sort_key)
    return rows


def _node_sort_key(row: dict[str, Any]) -> tuple[int, float, int]:
    score = row["medoid_score"]
    return label_order(str(row["cluster"])), math.inf if score is None else round(float(score), 12), int(row["tag_id"])


def edge_rows(state: NetworkState) -> Rows:
    names = state.network.tag_names
    return [{
        "source_tag_id": e.u, "source_tag": names[e.u], "target_tag_id": e.v, "target_tag": names[e.v],
        "shared_games": e.shared, "lift": e.lift, "source_cluster": state.cluster_of[e.u],
        "target_cluster": state.cluster_of[e.v], "is_intra_cluster": state.cluster_of[e.u] == state.cluster_of[e.v],
        "appids": state.network.edge_appids(e.u, e.v),
    } for e in state.network.edges]


def cluster_rows(state: NetworkState) -> Rows:
    names = state.network.tag_names
    rows = []
    for c in state.clusters:
        center = state.centers[c.label]
        metrics = state.cluster_metrics[c.label]
        order = member_order(c.members, center.medoid_scores, state.network.tag_games)
        stability = [state.membership_stability[t] for t in c.members]
        known = [s for s in stability if s is not None]
        rows.append({
            "cluster": c.label, "kind": c.kind, "size": c.size, "member_tag_ids": order,
            "members": [names[t] for t in order], "connected": metrics.connected,
            "internal_edges": metrics.internal_edges, "internal_weight": metrics.internal_weight,
            "edge_density": metrics.edge_density, "weighted_density": metrics.weighted_density,
            "cut_weight": metrics.cut_weight, "conductance": metrics.conductance,
            "conductance_status": metrics.conductance_status,
            "mean_silhouette": state.silhouette.per_cluster[c.label],
            "silhouette_status": state.silhouette.cluster_status[c.label],
            "center_tag_id": center.center, "center": names[center.center] if center.center is not None else None,
            "center_medoid_score": center.medoid_scores[center.center] if center.center is not None else None,
            "center_status": center.center_status,
            "top_strength_tag_id": center.top_strength,
            "top_strength_tag": names[center.top_strength] if center.top_strength is not None else None,
            "center_is_top_strength": (center.center == center.top_strength) if center.center is not None else None,
            "mean_membership_stability": (sum(known) / len(known)) if known else None,
        })
    return rows


def cluster_quality_row(state: NetworkState) -> dict[str, Any]:
    null = state.null_summary()
    seed = state.seed_summary()
    return {
        "n_dataset_games": state.network.n_games, "n_nodes": len(state.nodes), "n_edges": len(state.network.edges),
        "total_weight": state.total_weight, "modularity": state.modularity,
        "modularity_status": "no_edges" if state.modularity is None else None,
        **null,
        "coverage": state.coverage,
        "inter_cluster_weight_share": None if state.coverage is None else 1.0 - state.coverage,
        "n_multi_tag_clusters": len(state.multi_tag_clusters),
        "n_one_tag_clusters": len(state.clusters) - len(state.multi_tag_clusters),
        "n_disconnected_clusters": state.n_disconnected,
        "mean_silhouette": state.silhouette.mean, "silhouette_status": state.silhouette.status,
        **seed,
    }
