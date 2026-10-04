"""`compute_state(games, settings, context) -> NetworkState`: one complete Network State result.

The app and the Build both call this, so they never disagree. It covers the network, clustering,
the null model, the Seed-Noise Floor, silhouette, metrics, centers, Membership Stability and global
positions. Removal Sensitivity and the Resolution Sweep are separate entry points over the same state.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field

import networkx as nx
import numpy as np

from steamstudy.network import metrics as M
from steamstudy.network.cluster import Cluster, detect, label_clusters, membership
from steamstudy.network.graph import TagNetwork, build_network, to_graph
from steamstudy.network.layout import Positions, global_positions
from steamstudy.network.model import Game, Settings, TagContext, state_id_of
from steamstudy.network.stability import (
    NullReplicate,
    ari,
    membership_stability,
    noise_seeds,
    null_model,
    replicate_seeds,
    sample_sd,
)


@dataclass(frozen=True)
class SeedRun:
    index: int
    seed: int
    clusters: list[Cluster]
    modularity: float | None
    silhouette: float | None
    silhouette_status: str | None
    ari_vs_main: float

    @property
    def n_multi(self) -> int:
        return sum(c.size >= 2 for c in self.clusters)

    @property
    def n_single(self) -> int:
        return sum(c.size == 1 for c in self.clusters)


@dataclass
class NetworkState:
    settings: Settings
    context: TagContext
    network: TagNetwork
    graph: nx.Graph
    clusters: list[Cluster]
    cluster_of: dict[int, str]
    modularity: float | None
    coverage: float | None
    silhouette: M.Silhouette
    cluster_metrics: dict[str, M.ClusterMetrics]
    node_metrics: dict[int, M.NodeMetrics]
    centers: dict[str, M.Center]
    connections: list[tuple[str, str, int, float]]
    null_replicates: list[NullReplicate]
    seed_runs: list[SeedRun]
    membership_stability: dict[int, float | None]
    positions: Positions
    distances: np.ndarray
    clustering_seconds: float
    index: dict[int, int] = field(default_factory=dict)

    # -- identity

    @property
    def key(self) -> dict:
        return self.settings.key()

    @property
    def state_id(self) -> str:
        return state_id_of(self.key)

    # -- convenience

    @property
    def nodes(self) -> list[int]:
        return self.network.nodes

    def cluster(self, label: str) -> Cluster:
        return next(c for c in self.clusters if c.label == label)

    @property
    def multi_tag_clusters(self) -> list[Cluster]:
        return [c for c in self.clusters if c.size >= 2]

    @property
    def n_disconnected(self) -> int:
        return sum(not self.cluster_metrics[c.label].connected for c in self.clusters)

    @property
    def total_weight(self) -> float:
        return M.total_weight(self.graph)

    def medoid_score(self, tag: int) -> float | None:
        return self.centers[self.cluster_of[tag]].medoid_scores.get(tag)

    def is_center(self, tag: int) -> bool:
        return self.centers[self.cluster_of[tag]].center == tag

    def center_tags(self) -> set[int]:
        return {c.center for c in self.centers.values() if c.center is not None}

    def active_strength(self, tag: int) -> float:
        m = self.node_metrics[tag]
        return m.strength_shared if self.settings.clustering_weight == "shared_games" else m.strength_lift

    def intra_strength(self, tag: int) -> float:
        m = self.node_metrics[tag]
        return m.strength_shared_intra if self.settings.clustering_weight == "shared_games" else m.strength_lift_intra

    # -- partition quality summary

    def null_summary(self) -> dict[str, float | None]:
        qs = [r.modularity for r in self.null_replicates if r.modularity is not None]
        mean = statistics.fmean(qs) if qs else None
        sd = sample_sd(qs)
        z = None
        if self.modularity is not None and mean is not None and sd:
            z = (self.modularity - mean) / sd
        return {
            "q_null_mean": mean,
            "q_null_sd": sd,
            "modularity_z": z,
            "q_excess": (self.modularity - mean) if self.modularity is not None and mean is not None else None,
            "null_n_edges_mean": statistics.fmean(r.n_edges for r in self.null_replicates) if self.null_replicates else None,
        }

    def seed_summary(self) -> dict[str, float | int | str | None]:
        aris = [r.ari_vs_main for r in self.seed_runs]
        qs = [r.modularity for r in self.seed_runs if r.modularity is not None]
        sils = [r.silhouette for r in self.seed_runs if r.silhouette is not None]
        ks = [r.n_multi for r in self.seed_runs]
        return {
            "seed_ari_min": min(aris) if aris else None,
            "seed_ari_mean": statistics.fmean(aris) if aris else None,
            "seed_modularity_sd": sample_sd(qs),
            "seed_silhouette_sd": sample_sd(sils),
            "seed_silhouette_status": None if len(sils) >= 2 else "fewer_than_2_seeds_with_silhouette",
            "seed_k_min": min(ks) if ks else None,
            "seed_k_max": max(ks) if ks else None,
        }


def cluster_graph(graph: nx.Graph, settings: Settings, seed: int) -> list[Cluster]:
    return label_clusters(detect(graph, settings.algorithm, settings.resolution, seed))


def partition_metrics(graph: nx.Graph, clusters: list[Cluster], tags: list[int],
                      tag_games: dict[int, frozenset[int]], distances: np.ndarray,
                      resolution: float) -> tuple[float | None, M.Silhouette]:
    return M.modularity(graph, clusters, resolution), M.silhouette(tags, clusters, tag_games, distances)


def compute_state(games: list[Game], settings: Settings, context: TagContext | None = None,
                  *, with_positions: bool = True) -> NetworkState:
    context = context or TagContext()
    network = build_network(games, settings, context)
    graph = to_graph(network.nodes, network.edges, settings.clustering_weight)
    nodes = network.nodes
    index = {t: i for i, t in enumerate(nodes)}
    distances = M.jaccard_distances(nodes, network.tag_games)

    started = time.perf_counter()
    clusters = cluster_graph(graph, settings, settings.seed)
    clustering_seconds = time.perf_counter() - started
    cluster_of = membership(clusters)

    q, sil = partition_metrics(graph, clusters, nodes, network.tag_games, distances, settings.resolution)
    node_metrics = M.node_metrics(graph, clusters, settings.clustering_weight)
    intra = {t: (m.strength_shared_intra if settings.clustering_weight == "shared_games" else m.strength_lift_intra)
             for t, m in node_metrics.items()}
    centers = {c.label: M.center_of(c, index, distances, network.tag_games, intra) for c in clusters}

    r_seeds = replicate_seeds(settings.seed, settings.null_replicates)
    nulls = null_model(network.games, nodes, settings.min_shared_games, settings.clustering_weight,
                       settings.algorithm, settings.resolution, r_seeds, M.modularity)

    runs = []
    for i, seed in enumerate(noise_seeds(settings.seed, settings.noise_seeds, settings.null_replicates), start=1):
        seed_clusters = cluster_graph(graph, settings, seed)
        sq, ssil = partition_metrics(graph, seed_clusters, nodes, network.tag_games, distances, settings.resolution)
        runs.append(SeedRun(i, seed, seed_clusters, sq, ssil.mean, ssil.status,
                            ari(nodes, cluster_of, membership(seed_clusters))))
    stability = membership_stability(nodes, {t: m.degree for t, m in node_metrics.items()}, clusters,
                                     [r.clusters for r in runs])

    positions = global_positions(games, settings.min_months, settings.clustering_weight, settings.seed) \
        if with_positions else {}
    return NetworkState(
        settings=settings, context=context, network=network, graph=graph, clusters=clusters, cluster_of=cluster_of,
        modularity=q, coverage=M.coverage(graph, cluster_of), silhouette=sil,
        cluster_metrics={c.label: M.cluster_metrics(graph, c) for c in clusters}, node_metrics=node_metrics,
        centers=centers, connections=M.connections(graph, clusters), null_replicates=nulls, seed_runs=runs,
        membership_stability=stability, positions=positions, distances=distances,
        clustering_seconds=clustering_seconds, index=index,
    )
