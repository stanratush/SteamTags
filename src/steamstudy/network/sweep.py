"""The Resolution Sweep (Build only): the report's clustering repeated at fixed γ values, all else unchanged."""

from __future__ import annotations

import statistics
from typing import Any

from steamstudy.network import metrics as M
from steamstudy.network.cluster import membership
from steamstudy.network.model import resolution_text
from steamstudy.network.stability import ari, noise_seeds
from steamstudy.network.state import NetworkState, cluster_graph


def sweep_grid(grid: tuple[float, ...] | list[float], config_gamma: float) -> list[float]:
    """The configured grid, plus the config γ if the grid lacks it, so the report's partition is always a row."""
    values = {resolution_text(g): float(resolution_text(g)) for g in grid}
    values.setdefault(resolution_text(config_gamma), float(resolution_text(config_gamma)))
    return sorted(values.values())


def resolution_sweep(state: NetworkState, grid: list[float]) -> list[dict[str, Any]]:
    """One row per γ: cluster counts, Q at that γ, silhouette, ARI vs the report partition, seed ARIs at that γ."""
    nodes = state.nodes
    rows = []
    for gamma in grid:
        settings = state.settings.with_(resolution=gamma)
        clusters = cluster_graph(state.graph, settings, settings.seed)
        sil = M.silhouette(nodes, clusters, state.network.tag_games, state.distances)
        cluster_of = membership(clusters)
        aris = []
        for seed in noise_seeds(settings.seed, settings.noise_seeds, settings.null_replicates):
            aris.append(ari(nodes, cluster_of, membership(cluster_graph(state.graph, settings, seed))))
        k = sum(c.size >= 2 for c in clusters)
        rows.append({
            "resolution": float(resolution_text(gamma)), "n_multi_tag_clusters": k,
            "n_one_tag_clusters": len(clusters) - k, "modularity": M.modularity(state.graph, clusters, gamma),
            "mean_silhouette": sil.mean, "silhouette_status": sil.status,
            "ari_vs_report": ari(nodes, state.cluster_of, cluster_of),
            "seed_ari_min": min(aris) if aris else None,
            "seed_ari_mean": statistics.fmean(aris) if aris else None,
        })
    return rows
