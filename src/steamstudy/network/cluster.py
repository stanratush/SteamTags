"""Community detection (Louvain default, Leiden optional) and the `C1…` cluster labels."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np

LOUVAIN_THRESHOLD = 1e-7
# Leiden stops at the first pass that gains <= 0 (leidenalg's n_iterations=-1) or after this many passes:
# float-noise gains can keep the strict > 0 test going for ever at high γ.
PASS_CAP = 1000


def detect(graph: nx.Graph, algorithm: str, resolution: float, seed: int) -> list[frozenset[int]]:
    """Clusters of the graph on edge attribute `w`; every node (isolated ones too) is in exactly one."""
    if graph.number_of_nodes() == 0:
        return []
    if algorithm == "louvain":
        communities = nx.community.louvain_communities(
            graph, weight="w", resolution=resolution, seed=seed, threshold=LOUVAIN_THRESHOLD
        )
        return [frozenset(c) for c in communities]
    if algorithm == "leiden":
        nodes = sorted(graph.nodes)
        g, weights = _leiden_graph(graph)
        labels, _ = _leiden_passes(g, weights, resolution, seed)
        groups: dict[int, set[int]] = {}
        for i, label in enumerate(labels):
            groups.setdefault(label, set()).add(nodes[i])
        return [frozenset(s) for s in groups.values()]
    raise ValueError(f"unknown algorithm {algorithm!r}")


def _leiden_graph(graph: nx.Graph) -> tuple[Any, list[float] | None]:
    """The igraph and weights Leiden runs on: nodes sorted, edges sorted by (min, max)."""
    import igraph as ig

    nodes = sorted(graph.nodes)
    index = {t: i for i, t in enumerate(nodes)}
    edges = sorted((min(u, v), max(u, v), d["w"]) for u, v, d in graph.edges(data=True))
    g = ig.Graph(n=len(nodes), edges=[(index[u], index[v]) for u, v, _ in edges])
    return g, ([w for _, _, w in edges] if edges else None)


def _leiden_passes(g: Any, weights: list[float] | None, resolution: float, seed: int) -> tuple[list[int], bool]:
    """One seeded partition and optimiser, one pass at a time; (membership in node order, capped)."""
    import leidenalg as la

    partition = la.RBConfigurationVertexPartition(g, weights=weights, resolution_parameter=resolution)
    optimiser = la.Optimiser()
    optimiser.set_rng_seed(seed)
    for _ in range(PASS_CAP):
        if optimiser.optimise_partition(partition, n_iterations=1) <= 0:
            return list(partition.membership), False
    return list(partition.membership), True


@dataclass(frozen=True)
class ScanRun:
    gamma: float
    seed: int
    membership: np.ndarray  # Leiden's labels in node order (sorted tag ids)
    capped: bool


def leiden_scan(graph: nx.Graph, gammas: Sequence[float], seeds: Sequence[int]) -> list[ScanRun]:
    """Leiden at every (γ, seed) in scan order (γ ascending as given, then seeds), on one igraph construction."""
    g, weights = _leiden_graph(graph)
    runs = []
    for gamma in gammas:
        for seed in seeds:
            labels, capped = _leiden_passes(g, weights, gamma, seed)
            runs.append(ScanRun(float(gamma), int(seed), np.asarray(labels, dtype=np.int64), capped))
    return runs


@dataclass(frozen=True)
class Cluster:
    label: str
    members: frozenset[int]

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def kind(self) -> str:
        return "multi_tag" if self.size >= 2 else "one_tag"


def label_clusters(communities: list[frozenset[int]]) -> list[Cluster]:
    """C1… by size desc, ties by smallest member tag_id; Multi-Tag Clusters first, then One-Tag by tag_id."""
    multi = sorted((c for c in communities if len(c) >= 2), key=lambda c: (-len(c), min(c)))
    single = sorted((c for c in communities if len(c) == 1), key=min)
    return [Cluster(f"C{i}", c) for i, c in enumerate([*multi, *single], start=1)]


def membership(clusters: list[Cluster]) -> dict[int, str]:
    return {t: c.label for c in clusters for t in c.members}


def label_order(label: str) -> int:
    return int(label[1:]) if label.startswith("C") and label[1:].isdigit() else 10**9
