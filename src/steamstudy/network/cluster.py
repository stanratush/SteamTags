"""Community detection (Louvain default, Leiden optional) and the `C1…` cluster labels."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

LOUVAIN_THRESHOLD = 1e-7


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
        import igraph as ig
        import leidenalg as la

        nodes = sorted(graph.nodes)
        index = {t: i for i, t in enumerate(nodes)}
        edges = sorted((min(u, v), max(u, v), d["w"]) for u, v, d in graph.edges(data=True))
        g = ig.Graph(n=len(nodes), edges=[(index[u], index[v]) for u, v, _ in edges])
        weights = [w for _, _, w in edges]
        partition = la.find_partition(
            g, la.RBConfigurationVertexPartition, weights=weights if edges else None,
            resolution_parameter=resolution, n_iterations=-1, seed=seed,
        )
        groups: dict[int, set[int]] = {}
        for i, membership in enumerate(partition.membership):
            groups.setdefault(membership, set()).add(nodes[i])
        return [frozenset(s) for s in groups.values()]
    raise ValueError(f"unknown algorithm {algorithm!r}")


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
