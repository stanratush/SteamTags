"""Graph positions: the Global layout and the Cluster-separated layout. Never part of the Network State."""

from __future__ import annotations

import math

import networkx as nx
import numpy as np

from steamstudy.network.cluster import Cluster
from steamstudy.network.graph import build_network, to_graph
from steamstudy.network.model import Game, Settings, TagContext

SCALE = 1000.0  # positions are returned in renderer units
Positions = dict[int, tuple[float, float]]


def global_positions(games: list[Game], min_months: int, clustering_weight: str, seed: int) -> Positions:
    """A pure function of (dataset, Minimum Months Filter, Clustering Weight, seed).

    A weighted, seeded spring layout on the active Clustering Weight, at the loosest thresholds and with
    no tag hidden or removed, so moving a slider never moves the graph.
    """
    loose = Settings(build_id="layout", dataset="layout", min_months=min_months, min_games_per_tag=1,
                     min_shared_games=1, clustering_weight=clustering_weight, seed=seed)
    network = build_network(games, loose, TagContext())
    graph = to_graph(network.nodes, network.edges, clustering_weight)
    if graph.number_of_nodes() == 0:
        return {}
    pos = nx.spring_layout(graph, weight="w", seed=seed)
    return {int(t): (float(x) * SCALE, float(y) * SCALE) for t, (x, y) in sorted(pos.items())}


def relayout(graph: nx.Graph, start: Positions, seed: int, iterations: int = 50) -> Positions:
    """Re-layout: refine positions on the current graph, starting from the current ones."""
    if graph.number_of_nodes() == 0:
        return {}
    init = {t: (start[t][0] / SCALE, start[t][1] / SCALE) for t in graph.nodes if t in start}
    pos = nx.spring_layout(graph, weight="w", seed=seed, pos=init or None, iterations=iterations)
    return {int(t): (float(x) * SCALE, float(y) * SCALE) for t, (x, y) in sorted(pos.items())}


def cluster_separated_positions(graph: nx.Graph, clusters: list[Cluster], start: Positions, seed: int,
                                gap: float = 0.6) -> tuple[Positions, list[dict]]:
    """Each Multi-Tag Cluster laid out from its intra-cluster edges (seeded from `start`), packed side by side;
    One-Tag Clusters share one grid region at the end. Returns positions and the labelled regions."""
    boxes: list[tuple[str, list[int], np.ndarray, float]] = []
    singles: list[int] = []
    for c in clusters:  # already in label order: multi-tag by size, then one-tag
        members = sorted(c.members)
        if c.size < 2:
            singles.extend(members)
            continue
        sub = graph.subgraph(members)
        init = {t: (start[t][0] / SCALE, start[t][1] / SCALE) for t in members if t in start}
        p = nx.spring_layout(sub, pos=init or None, weight="w", seed=seed)
        arr = np.array([p[t] for t in members], dtype=float)
        arr -= arr.mean(axis=0)
        span = float(np.abs(arr).max()) or 1.0
        side = math.sqrt(len(members))
        boxes.append((f"{c.label} · {len(members)} tags", members, arr / span * side / 2, side))
    if singles:
        cols = max(1, math.ceil(math.sqrt(len(singles))))
        arr = np.array([[(i % cols) * 0.5, (i // cols) * 0.5] for i in range(len(singles))], dtype=float)
        arr -= arr.mean(axis=0)
        boxes.append((f"one-tag clusters · {len(singles)} tags", singles, arr, max(cols * 0.5, 0.5)))
    total = sum((side + gap) ** 2 for *_, side in boxes)
    row_width = math.sqrt(total) * 1.3 if total else 1.0
    positions: Positions = {}
    regions = []
    x = y = row_h = 0.0
    for label, members, arr, side in boxes:
        if x > 0 and x + side > row_width:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        cx, cy = x + side / 2, y + side / 2
        for t, (px, py) in zip(members, arr):
            positions[t] = ((cx + float(px)) * SCALE / 2, (cy + float(py)) * SCALE / 2)
        regions.append({"label": label, "x": (x - gap / 4) * SCALE / 2, "y": (y - gap / 4) * SCALE / 2,
                        "width": (side + gap / 2) * SCALE / 2, "height": (side + gap / 2) * SCALE / 2})
        x += side + gap
        row_h = max(row_h, side)
    return positions, regions
