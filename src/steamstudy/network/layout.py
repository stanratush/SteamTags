"""Graph positions: the Global layout and the Cluster-separated layout. Never part of the Network State.

Positions and node sizes share model units, so no node hides another at any zoom: a node's size is a
fixed function of its `n_games` relative to the dataset's most frequent tag (never of what is visible),
and a deterministic overlap-removal pass keeps every pair of nodes at least `GAP` apart.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Mapping
from typing import Any, TypeVar

import networkx as nx
import numpy as np

from steamstudy.network.cluster import Cluster
from steamstudy.network.graph import build_network, filter_games, to_graph
from steamstudy.network.model import Game, Settings, TagContext

SCALE = 1000.0  # positions are returned in renderer units
Positions = dict[int, tuple[float, float]]
K = TypeVar("K", bound=Hashable)

GAP = 4.0  # free space kept between two nodes
MIN_SIZE, SIZE_RANGE = 10.0, 24.0  # node diameter: MIN_SIZE + SIZE_RANGE * sqrt(n_games / most frequent tag's)
REGION_UNIT = 90.0  # a Cluster-separated region's side per square root of its members
REGION_GAP = 24.0  # between packed regions
TITLE_ROOM = 26.0  # above each row of regions, for the region titles
REGION_PAD = 8.0  # between a region's edge and its members
ASPECT = 1.4  # default canvas aspect ratio the packed rows aim at


def node_size(n_games: int, most_frequent: int) -> float:
    return MIN_SIZE + SIZE_RANGE * math.sqrt(n_games / max(most_frequent, 1))


def node_sizes(games: list[Game], min_months: int) -> dict[int, float]:
    """The diameter of every tag of the dataset after the Minimum Months Filter (games of the tag relative to
    the most frequent tag). Thresholds and hidden tags never change it."""
    counts: dict[int, int] = {}
    for g in filter_games(games, min_months):
        for t in set(g.tag_ids):
            counts[t] = counts.get(t, 0) + 1
    biggest = max(counts.values(), default=1)
    return {t: node_size(n, biggest) for t, n in sorted(counts.items())}


def remove_overlaps(positions: Mapping[K, tuple[float, float]], sizes: Mapping[K, float], *, gap: float = GAP,
                    fixed: Iterable[K] = (), max_rounds: int = 2000) -> dict[K, tuple[float, float]]:
    """Push overlapping nodes apart until every pair is at least `gap` apart (radius = size / 2).

    Deterministic: nodes are taken in sorted order and every round moves each overlapping pair apart along
    the line between them, half each (all of it on the free node when the other is fixed). Only pairs near
    each other are checked between full checks; it stops only when a full check finds no overlap. If that
    takes more than `max_rounds`, the free nodes spread out by half and it starts again (with at most one
    fixed node, or fixed nodes far enough apart, this always ends)."""
    keys = sorted(positions, key=_sort_key)
    n = len(keys)
    if n < 2:
        return {k: positions[k] for k in keys}
    xy = np.array([positions[k] for k in keys], dtype=float)
    radius = np.array([sizes[k] / 2 for k in keys], dtype=float)
    pinned = set(fixed)
    free = np.array([k not in pinned for k in keys], dtype=float)
    upper_i, upper_j = np.triu_indices(n, 1)
    need_all = radius[upper_i] + radius[upper_j] + gap
    # The fixed nodes stay put; if a settle runs out of rounds, the free nodes spread out from them (or from
    # the centroid when none is fixed) and settle again, so it always ends without an overlap.
    anchor = xy[free == 0].mean(axis=0) if (free == 0).any() else xy.mean(axis=0)
    while not _settle(xy, free, upper_i, upper_j, need_all, n, max_rounds):
        xy[free > 0] = anchor + (xy[free > 0] - anchor) * 1.5
    return {k: (float(x), float(y)) for k, (x, y) in zip(keys, xy)}


def _settle(xy: np.ndarray, free: np.ndarray, upper_i: np.ndarray, upper_j: np.ndarray, need_all: np.ndarray,
            n: int, max_rounds: int) -> bool:
    """Push overlapping pairs apart in place for at most `max_rounds`; whether a full check found no overlap."""
    pairs = np.zeros(0, dtype=int)
    for round_ in range(max_rounds):
        if round_ % 5 == 0:  # refresh the pairs close enough to touch soon
            d = xy[upper_i] - xy[upper_j]
            pairs = np.flatnonzero(np.hypot(d[:, 0], d[:, 1]) < need_all + 40.0)
        i, j, need = upper_i[pairs], upper_j[pairs], need_all[pairs]
        d = xy[i] - xy[j]
        dist = np.hypot(d[:, 0], d[:, 1])
        over = need - dist
        hit = over > 1e-7
        if not hit.any():
            if round_ % 5 == 0:
                return True  # a full check found nothing
            continue
        i, j, d, dist, over = i[hit], j[hit], d[hit], dist[hit], over[hit]
        coincident = dist < 1e-9
        angle = (i * n + j) * 2.399963  # a fixed direction for coincident points
        unit = np.where(coincident[:, None], np.stack([np.cos(angle), np.sin(angle)], axis=1),
                        d / np.where(coincident, 1.0, dist)[:, None])
        both = free[i] * free[j]
        share_i = np.where(both > 0, 0.5, free[i])
        share_j = np.where(both > 0, 0.5, free[j])
        # Slightly more than the overlap, so pairs settle instead of creeping towards exactly `gap`.
        step = (over * 1.02)[:, None] * unit
        delta = np.zeros_like(xy)
        np.add.at(delta, i, step * share_i[:, None])
        np.add.at(delta, j, -step * share_j[:, None])
        xy += delta
    d = xy[upper_i] - xy[upper_j]
    return not (need_all - np.hypot(d[:, 0], d[:, 1]) > 1e-7).any()


def global_positions(games: list[Game], min_months: int, clustering_weight: str, seed: int) -> Positions:
    """A pure function of (dataset, Minimum Months Filter, Clustering Weight, seed).

    A weighted, seeded spring layout on the active Clustering Weight, at the loosest thresholds and with
    no tag hidden or removed, then overlap removal, so moving a slider never moves the graph.
    """
    loose = Settings(build_id="layout", dataset="layout", min_months=min_months, min_games_per_tag=1,
                     min_shared_games=1, clustering_weight=clustering_weight, seed=seed)
    network = build_network(games, loose, TagContext())
    graph = to_graph(network.nodes, network.edges, clustering_weight)
    if graph.number_of_nodes() == 0:
        return {}
    pos = nx.spring_layout(graph, weight="w", seed=seed)
    spread = {int(t): (float(x) * SCALE, float(y) * SCALE) for t, (x, y) in sorted(pos.items())}
    return remove_overlaps(spread, node_sizes(games, min_months))


def relayout(graph: nx.Graph, start: Mapping[Any, tuple[float, float]], seed: int, iterations: int = 50, *,
             sizes: Mapping[Any, float]) -> dict[Any, tuple[float, float]]:
    """Re-layout: refine positions on the current graph, starting from the current ones, then remove overlaps."""
    if graph.number_of_nodes() == 0:
        return {}
    init = {t: (start[t][0] / SCALE, start[t][1] / SCALE) for t in graph.nodes if t in start}
    pos = nx.spring_layout(graph, weight="w", seed=seed, pos=init or None, iterations=iterations)
    return remove_overlaps({t: (float(x) * SCALE, float(y) * SCALE) for t, (x, y) in pos.items()}, sizes)


# ----------------------------------------------------------------------------- Cluster-separated


def cluster_separated_positions(graph: nx.Graph, clusters: list[Cluster], start: Mapping[Any, tuple[float, float]],
                                seed: int, *, centers: Mapping[str, Any] | None = None,
                                sizes: Mapping[Any, float] | None = None,
                                aspect: float = ASPECT) -> tuple[dict[Any, tuple[float, float]], list[dict[str, Any]]]:
    """One region per Multi-Tag Cluster, its side growing with the square root of its members; One-Tag Clusters
    share one compact grid region, packed last. Regions are shelf-packed biggest first (label order), with
    rows aimed at the canvas aspect ratio. Returns positions and the regions (top-left corner, width, height,
    label and cluster)."""
    sizes = sizes or {}
    size = lambda t: float(sizes.get(t, MIN_SIZE))  # noqa: E731
    boxes: list[tuple[str, str, dict[Any, tuple[float, float]], float, float]] = []
    singles: list[Any] = []
    for c in clusters:  # already in label order: multi-tag by size, then one-tag
        members = sorted(c.members, key=_sort_key)
        if c.size < 2:
            singles.extend(members)
            continue
        center = (centers or {}).get(c.label)
        if center not in c.members:
            center = max(members, key=lambda t: (size(t), _neg(t)))
        local, side = _region(graph, members, center, start, seed, size)
        boxes.append((f"{c.label} · {len(members)} tags", c.label, local, side, side))
    if singles:
        cell = max(size(t) for t in singles) + GAP + 2 * REGION_PAD
        cols = max(1, math.ceil(math.sqrt(len(singles))))
        rows = math.ceil(len(singles) / cols)
        local = {t: (((i % cols) - (cols - 1) / 2) * cell, ((i // cols) - (rows - 1) / 2) * cell)
                 for i, t in enumerate(singles)}
        boxes.append((f"one-tag clusters · {len(singles)} tags", "one_tag_pool", local, cols * cell, rows * cell))
    corners = _shelf_pack([(w, h) for *_, w, h in boxes], aspect)
    positions: dict[Any, tuple[float, float]] = {}
    regions = []
    for (label, cluster, local, w, h), (x, y) in zip(boxes, corners):
        cx, cy = x + w / 2, y + h / 2
        for t, (px, py) in local.items():
            positions[t] = (cx + px, cy + py)
        regions.append({"label": label, "cluster": cluster, "x": x, "y": y, "width": w, "height": h})
    return positions, regions


def _region(graph: nx.Graph, members: list[Any], center: Any, start: Mapping[Any, tuple[float, float]], seed: int,
            size: Any) -> tuple[dict[Any, tuple[float, float]], float]:
    """Members laid out around the pinned Cluster Center (at 0, 0) by a short seeded spring layout from their
    global positions, then de-overlapped; returns their positions and the region's side."""
    side = REGION_UNIT * math.sqrt(len(members))
    origin = start.get(center, (0.0, 0.0))
    init = {}
    for i, t in enumerate(members):
        if t in start:
            init[t] = ((start[t][0] - origin[0]) / SCALE, (start[t][1] - origin[1]) / SCALE)
        else:
            init[t] = (0.01 * math.cos(i * 2.399963), 0.01 * math.sin(i * 2.399963))
    init[center] = (0.0, 0.0)
    pos = nx.spring_layout(graph.subgraph(members), pos=init, fixed=[center], iterations=30, weight="w", seed=seed)
    others = [t for t in members if t != center]
    # The others' centroid moves onto the Center and each axis fills the region, so members surround it.
    mx = sum(float(pos[t][0]) for t in others) / len(others)
    my = sum(float(pos[t][1]) for t in others) / len(others)
    shifted = {t: (float(pos[t][0]) - mx, float(pos[t][1]) - my) for t in others}
    ex = max(abs(x) for x, _ in shifted.values()) or 1.0
    ey = max(abs(y) for _, y in shifted.values()) or 1.0
    inner = side / 2 - REGION_PAD - max(size(t) for t in members) / 2
    local = {t: (x / ex * inner, y / ey * inner) for t, (x, y) in shifted.items()}
    local[center] = (0.0, 0.0)
    local = remove_overlaps(local, {t: size(t) for t in members}, fixed=[center])
    needed = max(max(abs(x), abs(y)) + size(t) / 2 for t, (x, y) in local.items()) + REGION_PAD
    return local, max(side, 2 * needed)


def _shelf_pack(boxes: list[tuple[float, float]], aspect: float) -> list[tuple[float, float]]:
    """Top-left corners for boxes placed in rows (each row topped by room for the titles), each box in the first
    row with room for it. Every contiguous run of boxes is tried as the row width; the packing whose bounding
    box is smallest, weighted by how far its shape is from `aspect`, wins."""
    if not boxes:
        return []
    widths = [w for w, _ in boxes]
    candidates = sorted({sum(widths[i:j]) + REGION_GAP * (j - i - 1)
                         for i in range(len(boxes)) for j in range(i + 1, len(boxes) + 1)})
    best: tuple[float, list[tuple[float, float]]] | None = None
    for row_width in candidates:
        if row_width < max(widths) - 1e-9:
            continue
        corners, width, height = _shelves(boxes, row_width)
        ratio = width / height if height else aspect
        score = width * height * max(ratio / aspect, aspect / ratio) ** 0.5
        if best is None or score < best[0] - 1e-9:
            best = (score, corners)
    assert best is not None
    return best[1]


def _shelves(boxes: list[tuple[float, float]], row_width: float) -> tuple[list[tuple[float, float]], float, float]:
    """First fit: rows are [used width, height]; a box opens a new row only when no row has room for it."""
    rows: list[list[float]] = []
    placed: list[tuple[int, float]] = []
    for w, h in boxes:
        for i, row in enumerate(rows):
            if row[0] + REGION_GAP + w <= row_width + 1e-9:
                placed.append((i, row[0] + REGION_GAP))
                row[0] += REGION_GAP + w
                row[1] = max(row[1], h)
                break
        else:
            placed.append((len(rows), 0.0))
            rows.append([w, h])
    tops, y = [], TITLE_ROOM
    for _, h in rows:
        tops.append(y)
        y += h + REGION_GAP + TITLE_ROOM
    width = max(used for used, _ in rows)
    return [(x, tops[i]) for i, x in placed], width, tops[-1] + rows[-1][1]


def _sort_key(key: Any) -> tuple[int, Any]:
    """Numeric ids sort as numbers, even when they arrive as strings (the app's element ids)."""
    try:
        return 0, int(key)
    except (TypeError, ValueError):
        return 1, str(key)


def _neg(key: Any) -> Any:
    k = _sort_key(key)
    return (-k[1],) if k[0] == 0 else (0,)
