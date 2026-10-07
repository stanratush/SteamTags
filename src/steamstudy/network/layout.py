"""Graph positions: the Global layout and the Cluster-separated layout. Never part of the Network State.

Layout is downstream of analysis (ADR 0002): `layout_state(state, canvas)` takes a finished Network State
and only reads it. No analysis module imports this one, so no coordinate can reach a metric.

Positions and node sizes share model units, so no node hides another at any zoom: a node's size is a
fixed function of its `n_games` relative to the dataset's most frequent tag (never of what is visible),
and a deterministic overlap-removal pass keeps every pair of nodes at least `GAP` apart.
"""

from __future__ import annotations

import functools
import math
import unicodedata
from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

import networkx as nx
import numpy as np

from steamstudy.network.cluster import Cluster
from steamstudy.network.graph import build_network, filter_games, to_graph
from steamstudy.network.model import Game, Settings, TagContext

if TYPE_CHECKING:
    from steamstudy.network.state import NetworkState

SCALE = 1000.0  # positions are returned in renderer units
Positions = dict[int, tuple[float, float]]
K = TypeVar("K", bound=Hashable)


@dataclass(frozen=True)
class Canvas:
    """The free graph area a layout is made for, in screen pixels."""

    width: float
    height: float

    @property
    def aspect(self) -> float:
        return self.width / self.height


# The free graph area of a 1440 x 900 Workbench with the Tables and the Inspector closed: exports use it, so the
# same Network State exports the same coordinates on every machine.
REFERENCE_CANVAS = Canvas(1116, 678)


@dataclass(frozen=True)
class Layout:
    """Where every visible tag is drawn: the Global positions, the node sizes, and the Cluster-separated
    positions with their regions (top-left corner, width, height, label and cluster)."""

    positions: Positions
    sizes: dict[int, float]
    separated: Positions
    regions: list[dict[str, Any]]
    zoom: float = 1.0  # the zoom the Global labels are spaced for: the first fit on the canvas is at least this
    separated_zoom: float = 1.0  # the same for the Cluster-separated layout


@dataclass(frozen=True)
class LayoutInput:
    """What the layout reads of a Network State: the visible network (weighted by the active Clustering Weight),
    the start positions (the dataset's loose layout), node sizes, label widths, the clusters with their Centers,
    and the seed. The app keeps it as plain data between callbacks."""

    graph: nx.Graph
    start: Positions
    sizes: dict[int, float]
    widths: dict[int, float]
    clusters: list[Cluster]
    centers: dict[str, int | None]
    seed: int


def layout_input(state: NetworkState) -> LayoutInput:
    """Read a finished Network State; nothing in it changes."""
    nodes = state.nodes
    games = state.network.games  # already after the Minimum Months Filter
    settings = state.settings
    sizes = node_sizes(games, settings.min_months)
    loose = loose_layout(games, settings.min_months, settings.clustering_weight, settings.seed)
    return LayoutInput(state.graph, {t: loose[t] for t in nodes}, {t: sizes[t] for t in nodes},
                       {t: label_width(state.network.tag_names[t]) for t in nodes}, list(state.clusters),
                       {label: c.center for label, c in state.centers.items()}, settings.seed)


def layout_state(state: NetworkState, canvas: Canvas = REFERENCE_CANVAS, params: LayoutParams | None = None, *,
                 positions: Mapping[int, tuple[float, float]] | None = None, zoom: float = 1.0) -> Layout:
    """The layout of a finished Network State, which it only reads."""
    return lay_out(layout_input(state), canvas, params, positions=positions, zoom=zoom)


def lay_out(inp: LayoutInput, canvas: Canvas = REFERENCE_CANVAS, params: LayoutParams | None = None, *,
            positions: Mapping[int, tuple[float, float]] | None = None, zoom: float = 1.0,
            separated: bool = True) -> Layout:
    """Both layouts for a canvas (only the Global one without `separated`). `positions` (with the `zoom` their
    labels are spaced for) replace the computed Global positions: Tidy's, or an older export's restored ones.
    The Cluster-separated layout always starts from the Global one."""
    nodes = sorted(inp.graph.nodes)
    if positions is None:
        positions, zoom = global_layout(inp.graph, inp.start, inp.sizes, inp.widths, canvas, params or LayoutParams())
    global_ = {t: positions[t] for t in nodes}
    if not separated:
        return Layout(global_, dict(inp.sizes), {}, [], zoom)
    apart, regions, apart_zoom = cluster_separated_positions(
        inp.graph, inp.clusters, global_, centers=inp.centers, sizes=inp.sizes, widths=inp.widths, canvas=canvas,
        zoom=zoom)
    return Layout(global_, dict(inp.sizes), apart, regions, zoom, apart_zoom)


GAP = 4.0  # free space kept between two nodes
MIN_SIZE, SIZE_RANGE = 18.0, 30.0  # node diameter: MIN_SIZE + SIZE_RANGE * sqrt(n_games / most frequent tag's)


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


def loose_layout(games: list[Game], min_months: int, clustering_weight: str, seed: int) -> Positions:
    """The dataset's fixed loose layout, where every Global layout starts: a pure function of (dataset, Minimum
    Months Filter, Clustering Weight, seed).

    A weighted, seeded spring layout on the active Clustering Weight, at the loosest thresholds and with
    no tag hidden or removed, then overlap removal. Similar visible sets start alike, so they end up alike.
    """
    return dict(_loose_layout(tuple(filter_games(games, min_months)), clustering_weight, seed))


@functools.lru_cache(maxsize=32)
def _loose_layout(games: tuple[Game, ...], clustering_weight: str,
                  seed: int) -> tuple[tuple[int, tuple[float, float]], ...]:
    loose = Settings(build_id="layout", dataset="layout", min_months=0, min_games_per_tag=1,
                     min_shared_games=1, clustering_weight=clustering_weight, seed=seed)
    network = build_network(list(games), loose, TagContext())
    graph = to_graph(network.nodes, network.edges, clustering_weight)
    if graph.number_of_nodes() == 0:
        return ()
    pos = nx.spring_layout(graph, weight="w", seed=seed)
    spread = {int(t): (float(x) * SCALE, float(y) * SCALE) for t, (x, y) in sorted(pos.items())}
    return tuple(remove_overlaps(spread, node_sizes(list(games), 0)).items())


# ----------------------------------------------------------------------------- labels

LABEL_PX = 11.5  # every label's on-screen size
LABEL_HEIGHT = 15.0  # one label line at LABEL_PX with its halo, in pixels
LABEL_MARGIN = 2.0  # between a node and its label below it, in pixels
BOX_GAP = 2.0  # free space kept between two node-plus-label boxes, in pixels
# The bold system UI font (Segoe UI) at 11.5 px, in pixels per character, measured in a browser.
CHAR_WIDTHS = {
    " ": 3.17, "!": 3.76, '"': 5.67, "#": 6.81, "$": 6.61, "%": 9.97, "&": 9.77, "'": 3.37, "(": 4.25, ")": 4.25,
    "*": 5.23, "+": 8.13, ",": 3.12, "-": 4.65, ".": 3.12, "/": 5.1, ":": 3.12, ";": 3.12, "<": 8.13, "=": 8.13,
    ">": 8.13, "?": 5.04, "@": 10.97, "[": 4.25, "\\": 5.01, "]": 4.25, "^": 8.13, "_": 4.77, "`": 3.61, "{": 4.25,
    "|": 3.75, "}": 4.25, "~": 8.13,
    **dict.fromkeys("0123456789", 6.61),
    "A": 8.09, "B": 7.37, "C": 7.18, "D": 8.48, "E": 6.12, "F": 5.98, "G": 8.18, "H": 8.81, "I": 3.64, "J": 5.12,
    "K": 7.46, "L": 5.88, "M": 11.01, "N": 9.09, "O": 8.72, "P": 7.06, "Q": 8.72, "R": 7.51, "S": 6.45, "T": 6.74,
    "U": 8.32, "V": 7.67, "W": 11.56, "X": 7.54, "Y": 6.98, "Z": 6.98,
    "a": 6.19, "b": 7.13, "c": 5.52, "d": 7.12, "e": 6.22, "f": 4.41, "g": 7.12, "h": 6.92, "i": 3.27, "j": 3.27,
    "k": 6.43, "l": 3.27, "m": 10.53, "n": 6.96, "o": 7.03, "p": 7.13, "q": 7.12, "r": 4.58, "s": 5.06, "t": 4.48,
    "u": 6.96, "v": 6.23, "w": 9.17, "x": 6.35, "y": 6.19, "z": 5.51,
}
WIDE_CHAR = LABEL_PX  # a character outside the table without a base letter in it (one em)
WIDTH_SLACK = 1.1  # room for other fonts and the halo


def label_width(text: str) -> float:
    """A label's width on screen at LABEL_PX, from a fixed table: the same on every machine, so exports never
    depend on the viewer's fonts."""
    total = 0.0
    for ch in text:
        width = CHAR_WIDTHS.get(ch)
        if width is None:
            width = CHAR_WIDTHS.get(unicodedata.normalize("NFKD", ch)[:1], WIDE_CHAR)
        total += width
    return WIDTH_SLACK * total


class Boxes:
    """Node-plus-label boxes in model units, with the labels at LABEL_PX on screen at `zoom`: each centred on
    its node horizontally, from the node's top to the bottom of the label below it."""

    def __init__(self, sizes: np.ndarray, widths: np.ndarray, zoom: float):
        label = (LABEL_MARGIN + LABEL_HEIGHT) / zoom
        self.half_width = np.maximum(sizes, widths / zoom) / 2
        self.half_height = (sizes + label) / 2
        self.top = -sizes / 2  # relative to the node's centre
        self.bottom = sizes / 2 + label
        self.gap = BOX_GAP / zoom


def fit_zoom(xy: np.ndarray, sizes: np.ndarray, widths: np.ndarray, canvas: Canvas) -> float:
    """The first fit: the largest zoom, at most 1, at which every node and its label is inside the canvas.
    graph.js fits the same way."""
    if len(xy) == 0:
        return 1.0

    def fits(zoom: float) -> bool:
        boxes = Boxes(sizes, widths, zoom)
        width = (xy[:, 0] + boxes.half_width).max() - (xy[:, 0] - boxes.half_width).min()
        height = (xy[:, 1] + boxes.bottom).max() - (xy[:, 1] + boxes.top).min()
        return bool(width * zoom <= canvas.width and height * zoom <= canvas.height)

    if fits(1.0):
        return 1.0
    low, high = 1e-3, 1.0
    for _ in range(40):
        mid = (low + high) / 2
        low, high = (mid, high) if fits(mid) else (low, mid)
    return low


def separate(xy: np.ndarray, boxes: Boxes, *, free: np.ndarray | None = None, clamp: Clamp | None = None,
             aspect: float = 1.0, max_rounds: int = 400) -> None:
    """Push overlapping node-plus-label boxes apart, in place, until every pair is at least the gap apart.

    Deterministic: every round moves each overlapping pair apart along the axis where they overlap least (a
    vertical overlap counts `aspect` times, so a wide canvas grows the layout sideways), half each (all of it on
    the free one when the other is pinned; two pinned boxes are left as they are). Only pairs near each other
    are checked between full checks; it stops only when a full check finds no overlap. If that takes more than
    `max_rounds`, the free boxes spread out by a tenth and it starts again, so it always ends. A `clamp` is kept
    before every full check; a spread also widens the main component the clamp follows."""
    n = len(xy)
    free = np.ones(n) if free is None else free
    if n < 2:
        return
    i_all, j_all = np.triu_indices(n, 1)
    keep = (free[i_all] > 0) | (free[j_all] > 0)
    i_all, j_all = i_all[keep], j_all[keep]
    need = np.stack([boxes.half_width[i_all] + boxes.half_width[j_all],
                     boxes.half_height[i_all] + boxes.half_height[j_all]], axis=1) + boxes.gap
    anchor = xy[free == 0].mean(axis=0) if (free == 0).any() else xy.mean(axis=0)
    while not _push_apart(xy, free, i_all, j_all, need, max_rounds, clamp, aspect):
        xy[free > 0] = anchor + (xy[free > 0] - anchor) * 1.1
        if clamp is not None:
            clamp(xy)


def _push_apart(xy: np.ndarray, free: np.ndarray, i_all: np.ndarray, j_all: np.ndarray, need: np.ndarray,
                max_rounds: int, clamp: Clamp | None, aspect: float) -> bool:
    """`separate`'s rounds; whether a full check found no overlap."""
    pairs = np.zeros(0, dtype=int)
    for round_ in range(max_rounds):
        if round_ % 5 == 0:  # keep the clamp, then refresh the pairs close enough to touch soon
            if clamp is not None:
                clamp(xy)
            near = np.abs(xy[i_all] - xy[j_all]) < need * 1.5 + 10.0
            pairs = np.flatnonzero(near[:, 0] & near[:, 1])
        i, j = i_all[pairs], j_all[pairs]
        d = xy[i] - xy[j]
        over = need[pairs] - np.abs(d)
        hit = (over > 1e-7).all(axis=1)
        if not hit.any():
            if round_ % 5 == 0:
                return True  # a full check found nothing
            continue
        i, j, d, over = i[hit], j[hit], d[hit], over[hit]
        along = (over[:, 1] * aspect <= over[:, 0]).astype(int)  # 0: x, 1: y
        rows = np.arange(len(i))
        tie = np.where((i + j) % 2 == 0, 1.0, -1.0)  # a fixed side for coincident boxes
        side = d[rows, along]
        sign = np.where(np.abs(side) > 1e-9, np.sign(side), tie)
        step = np.zeros_like(d)
        # Slightly more than the overlap, so pairs settle instead of creeping towards exactly the gap.
        step[rows, along] = sign * over[rows, along] * 1.02
        both = free[i] * free[j]
        share_i, share_j = np.where(both > 0, 0.5, free[i]), np.where(both > 0, 0.5, free[j])
        n = len(xy)
        for axis in (0, 1):
            xy[:, axis] += (np.bincount(i, step[:, axis] * share_i, minlength=n)
                            - np.bincount(j, step[:, axis] * share_j, minlength=n))
    over = need - np.abs(xy[i_all] - xy[j_all])
    return not (over > 1e-7).all(axis=1).any()


# ----------------------------------------------------------------------------- Global layout

GRAVITY = 1.0  # ForceAtlas2 gravity: pulls tags without a visible link towards the graph
FA2_ITERATIONS = 100
FILL = 0.7  # the main component's share of the canvas, before the label-aware pass
MAX_STRETCH = 1.6  # at most this much wider (or taller) than the layout's own shape, to fill the canvas
CLAMP_ROOM = 1.5 * LABEL_HEIGHT  # how far beyond the main component's radius a tag may sit, in pixels
NEIGHBOUR_ROOM = 3.0  # a small set's neighbours: at most this many times the room their boxes need
CROWDING = 0.4  # the share of the canvas that boxes can fill at best: where the search for the zoom starts
MIN_ZOOM = 0.55  # the lowest zoom the labels are spaced for; a larger set fits only further out
ATTEMPTS = 8


@dataclass(frozen=True)
class LayoutParams:
    """Layout settings. Like the canvas, they change only coordinates, never a result (ADR 0002)."""

    gravity: float = GRAVITY
    clamp: bool = True


def global_layout(graph: nx.Graph, start: Mapping[int, tuple[float, float]], sizes: Mapping[int, float],
                  widths: Mapping[int, float], canvas: Canvas = REFERENCE_CANVAS,
                  params: LayoutParams = LayoutParams()) -> tuple[Positions, float]:
    """The Global layout of the visible network for a canvas, and the zoom its labels are spaced for.

    ForceAtlas2 with gravity and hub dissuasion from the start positions, scaled to the canvas, then the clamp
    and the label-aware pass. One model unit is one pixel at zoom 1: the zoom is the highest (at most 1) at which
    the first fit shows every label at LABEL_PX without an overlap, down to MIN_ZOOM. Deterministic."""
    keys = sorted(graph.nodes)
    if not keys:
        return {}, 1.0
    main = _main_component(graph, keys)
    shape = _shape(_forceatlas2(graph, keys, start, params.gravity), main, canvas)
    s = np.array([sizes[t] for t in keys], dtype=float)
    w = np.array([widths[t] for t in keys], dtype=float)
    xy, zoom = _place(shape, main if params.clamp and main.sum() >= 2 else None, s, w, canvas)
    return {t: (float(x), float(y)) for t, (x, y) in zip(keys, xy)}, zoom


def _forceatlas2(graph: nx.Graph, keys: list[int], start: Mapping[int, tuple[float, float]],
                 gravity: float) -> np.ndarray:
    """`nx.forceatlas2_layout` on the active Clustering Weight (scaled to at most 1), with hub dissuasion."""
    g = nx.Graph()
    g.add_nodes_from(keys)
    top = max((float(w) for *_, w in graph.edges(data="w")), default=1.0) or 1.0
    for u, v, w in sorted(graph.edges(data="w")):
        g.add_edge(u, v, w=float(w) / top)
    init = {t: np.array(start[t], dtype=float) / SCALE for t in keys if t in start}
    pos = nx.forceatlas2_layout(g, pos=init or None, max_iter=FA2_ITERATIONS, gravity=gravity,
                                distributed_action=True, weight="w", seed=0)
    return np.array([pos[t] for t in keys], dtype=float)


def _main_component(graph: nx.Graph, keys: list[int]) -> np.ndarray:
    """A mask over `keys`: the largest connected component (ties: the one with the smallest tag id)."""
    main = min(nx.connected_components(graph), key=lambda c: (-len(c), min(c)))
    return np.array([t in main for t in keys])


def _shape(xy: np.ndarray, main: np.ndarray, canvas: Canvas) -> np.ndarray:
    """Centre the main component and scale it to fill the canvas (stretched at most MAX_STRETCH per axis).
    Without a main component of two or more tags, the whole layout is scaled instead."""
    basis = xy[main] if main.sum() >= 2 else xy
    centre = (basis.min(axis=0) + basis.max(axis=0)) / 2
    extent = basis.max(axis=0) - basis.min(axis=0)
    if extent.max() < 1e-9:
        extent = np.ones(2)
    extent = np.maximum(extent, extent.max() / MAX_STRETCH)
    scale = np.array([canvas.width, canvas.height]) / extent
    scale = np.minimum(scale, scale.min() * MAX_STRETCH)
    return (xy - centre) * scale


def _place(shape: np.ndarray, main: np.ndarray | None, sizes: np.ndarray, widths: np.ndarray,
           canvas: Canvas) -> tuple[np.ndarray, float]:
    """Scale the shape for a zoom, clamp it and separate the boxes; lower the zoom until the result fits the
    canvas at that zoom (or MIN_ZOOM is reached)."""
    zoom = _crowding_zoom(sizes, widths, canvas)
    for attempt in range(ATTEMPTS):
        boxes = Boxes(sizes, widths, zoom)
        xy = shape * min(FILL / zoom, _neighbour_cap(shape, boxes, main))
        clamp = Clamp(main, CLAMP_ROOM / zoom) if main is not None else None
        if clamp is not None:
            clamp(xy)
        separate(xy, boxes, clamp=clamp, aspect=canvas.aspect)
        fit = fit_zoom(xy, sizes, widths, canvas)
        if fit >= zoom or zoom <= MIN_ZOOM or attempt == ATTEMPTS - 1:
            return xy, zoom
        zoom = _next_zoom(zoom, fit)
    raise AssertionError("unreachable")


def _next_zoom(zoom: float, fit: float) -> float:
    """After an attempt at `zoom` fitted only at `fit`: lower labels grow in model units, so the next attempt
    goes as far again below the fit (by the square root of the shortfall), but not below MIN_ZOOM."""
    return max(MIN_ZOOM, min(fit, zoom * 0.95) * math.sqrt(min(fit / zoom, 1.0)))


def _crowding_zoom(sizes: np.ndarray, widths: np.ndarray, canvas: Canvas, crowding: float = CROWDING) -> float:
    """The highest zoom, at most 1, at which the boxes cover at most `crowding` of the canvas on screen."""
    def area(zoom: float) -> float:
        width = np.maximum(sizes * zoom, widths) + BOX_GAP
        height = sizes * zoom + LABEL_MARGIN + LABEL_HEIGHT + BOX_GAP
        return float((width * height).sum())

    budget = crowding * canvas.width * canvas.height
    if area(1.0) <= budget:
        return 1.0
    low, high = MIN_ZOOM, 1.0
    for _ in range(20):
        mid = (low + high) / 2
        low, high = (mid, high) if area(mid) <= budget else (low, mid)
    return low


def _neighbour_cap(shape: np.ndarray, boxes: Boxes, main: np.ndarray | None) -> float:
    """The largest scale of the shape at which every tag of the main component has a neighbour within
    NEIGHBOUR_ROOM times the room their two boxes need."""
    if len(shape) < 2:
        return math.inf
    d = np.abs(shape[:, None, :] - shape[None, :, :])
    room = np.stack([boxes.half_width[:, None] + boxes.half_width[None, :],
                     boxes.half_height[:, None] + boxes.half_height[None, :]], axis=-1)
    ratio = (d / room).max(axis=-1)
    np.fill_diagonal(ratio, np.inf)
    nearest = ratio.min(axis=1)
    if main is not None:
        nearest = nearest[main]
    widest = float(nearest.max())
    return NEIGHBOUR_ROOM / widest if widest > 1e-12 else math.inf


class Clamp:
    """Keeps every tag within the main component's radius plus `room` of its centre, per axis: a tag outside is
    moved towards the centre onto that bound. The main component's own tags and the `fixed` ones (dragged, for
    Tidy) are never moved, so the bound grows with the main component."""

    def __init__(self, main: np.ndarray, room: float, fixed: np.ndarray | None = None):
        self.main, self.room = main, room
        self.fixed = np.zeros(len(main), dtype=bool) if fixed is None else fixed

    def __call__(self, xy: np.ndarray) -> None:
        inner = xy[self.main]
        centre = (inner.min(axis=0) + inner.max(axis=0)) / 2
        bound = (inner.max(axis=0) - inner.min(axis=0)) / 2 + self.room
        d = xy - centre
        with np.errstate(divide="ignore"):
            shrink = np.min(np.where(np.abs(d) > 1e-12, bound / np.abs(d), np.inf), axis=1)
        moved = centre + d * np.minimum(1.0, shrink)[:, None]
        xy[~self.fixed] = moved[~self.fixed]


# ----------------------------------------------------------------------------- Tidy and old exports


def tidy(inp: LayoutInput, current: Mapping[int, tuple[float, float]], canvas: Canvas, *,
         pinned: Mapping[int, tuple[float, float]] | None = None, zoom: float = 1.0) -> tuple[Positions, float]:
    """Tidy: settle the Global layout from the current positions, the dragged (`pinned`) nodes staying exactly
    where they were dropped. ForceAtlas2 from the current positions, its result turned and scaled back onto
    them, then the clamp and the label-aware pass with labels spaced for `zoom` (the current layout's)."""
    keys = sorted(inp.graph.nodes)
    if not keys:
        return {}, zoom
    pinned = pinned or {}
    now = np.array([pinned.get(t, current[t]) for t in keys], dtype=float)
    xy = _onto(_forceatlas2(inp.graph, keys, {t: tuple(p) for t, p in zip(keys, now)}, GRAVITY), now)
    fixed = np.array([t in pinned for t in keys])
    xy[fixed] = now[fixed]
    s = np.array([inp.sizes[t] for t in keys], dtype=float)
    boxes = Boxes(s, np.array([inp.widths[t] for t in keys], dtype=float), zoom)
    main = _main_component(inp.graph, keys)
    clamp = Clamp(main, CLAMP_ROOM / zoom, fixed) if main.sum() >= 2 else None
    if clamp is not None:
        clamp(xy)
    separate(xy, boxes, free=(~fixed).astype(float), clamp=clamp, aspect=canvas.aspect)
    out = {t: (float(x), float(y)) for t, (x, y) in zip(keys, xy)}
    out.update({t: (float(pinned[t][0]), float(pinned[t][1])) for t in keys if t in pinned})
    return out, zoom


def _onto(xy: np.ndarray, target: np.ndarray) -> np.ndarray:
    """`xy` turned, scaled and moved to match `target` as closely as possible (Procrustes, no mirroring)."""
    a, b = xy - xy.mean(axis=0), target - target.mean(axis=0)
    norm = float(np.sqrt((a * a).sum()))
    if norm < 1e-12:
        return np.repeat(target.mean(axis=0)[None, :], len(xy), axis=0)
    u, sv, vt = np.linalg.svd(a.T @ b)
    turn = u @ vt
    if np.linalg.det(turn) < 0:
        u[:, -1] *= -1
        sv[-1] *= -1
        turn = u @ vt
    return (a @ turn) * (sv.sum() / norm ** 2) + target.mean(axis=0)


def restore(inp: LayoutInput, stored: Mapping[int, tuple[float, float]],
            canvas: Canvas = REFERENCE_CANVAS) -> tuple[Positions, float]:
    """Global positions from an older export's Re-layout: their shape kept (one scale for both axes), scaled into
    the canvas, then the clamp and the label-aware pass, so tags thrown far out by the old Re-layout come back
    next to the graph."""
    keys = sorted(inp.graph.nodes)
    if not keys:
        return {}, 1.0
    xy = np.array([stored[t] for t in keys], dtype=float)
    main = _main_component(inp.graph, keys)
    basis = xy[main] if main.sum() >= 2 else xy
    centre = (basis.min(axis=0) + basis.max(axis=0)) / 2
    extent = np.maximum(basis.max(axis=0) - basis.min(axis=0), 1e-9)
    shape = (xy - centre) * float(min(canvas.width / extent[0], canvas.height / extent[1]))
    s = np.array([inp.sizes[t] for t in keys], dtype=float)
    out, zoom = _place(shape, main if main.sum() >= 2 else None, s,
                       np.array([inp.widths[t] for t in keys], dtype=float), canvas)
    return {t: (float(x), float(y)) for t, (x, y) in zip(keys, out)}, zoom


# ----------------------------------------------------------------------------- Cluster-separated

REGION_FILL = 2.5  # a region's area: its members' node-plus-label boxes times this
REGION_GAP = 16.0  # between packed regions, in model units
REGION_PAD = 8.0  # between a region's edge and its members' boxes, in model units
REGION_START = FILL  # the members' share of the region's half side before the label-aware pass
REGION_CROWDING = 0.3  # where the zoom search starts: packed regions take about three times their members' boxes
TITLE_ROOM = 22.0  # above each row of regions, for the region titles (constant on screen), in pixels


def cluster_separated_positions(graph: nx.Graph, clusters: list[Cluster], start: Mapping[int, tuple[float, float]],
                                *, centers: Mapping[str, int | None], sizes: Mapping[int, float],
                                widths: Mapping[int, float], canvas: Canvas = REFERENCE_CANVAS,
                                zoom: float = 1.0) -> tuple[Positions, list[dict[str, Any]], float]:
    """One region per Multi-Tag Cluster, with its Center pinned in the middle; One-Tag Clusters share one grid
    region, listed last. Regions are shelf-packed in label order or tallest first, whichever packs tighter, rows
    aimed at the canvas aspect.
    Like the Global layout, the labels are spaced for the highest zoom (down to MIN_ZOOM) at which the first fit
    holds them all, starting from `zoom` (the Global layout's: regions never need less room). Returns positions,
    the regions (top-left corner, width, height, label and cluster) and that zoom."""
    multi = [c for c in clusters if c.size >= 2]
    singles = sorted(t for c in clusters if c.size < 2 for t in c.members)
    shapes = {c.label: _region_shape(graph, c, centers.get(c.label), start, sizes) for c in multi}
    tags = sorted(t for c in clusters for t in c.members)
    zoom = min(zoom, _crowding_zoom(np.array([sizes[t] for t in tags], dtype=float),
                                    np.array([widths[t] for t in tags], dtype=float), canvas, REGION_CROWDING))
    for attempt in range(ATTEMPTS):
        boxes: list[tuple[str, str, Positions, float, float]] = []
        for c in multi:
            local, w, h = _region_members(shapes[c.label], sizes, widths, zoom)
            boxes.append((f"{c.label} · {c.size} tags", c.label, local, w, h))
        if singles:
            local, w, h = _pool(singles, sizes, widths, zoom)
            boxes.append((f"one-tag clusters · {len(singles)} tags", "one_tag_pool", local, w, h))
        corners = _pack([(w, h) for *_, w, h in boxes], canvas.aspect, TITLE_ROOM / zoom)
        positions: Positions = {}
        regions = []
        for (label, cluster, local, w, h), (x, y) in zip(boxes, corners):
            for t, (px, py) in local.items():
                positions[t] = (x + w / 2 + px, y + h / 2 + py)
            regions.append({"label": label, "cluster": cluster, "x": x, "y": y, "width": w, "height": h})
        fit = _regions_fit(regions, canvas)
        if fit >= zoom or zoom <= MIN_ZOOM or attempt == ATTEMPTS - 1:
            return positions, regions, zoom
        zoom = _next_zoom(zoom, fit)
    raise AssertionError("unreachable")


def _region_shape(graph: nx.Graph, cluster: Cluster, center: int | None, start: Mapping[int, tuple[float, float]],
                  sizes: Mapping[int, float]) -> tuple[list[int], int, np.ndarray, np.ndarray]:
    """ForceAtlas2 on a cluster's members from their Global positions, centred on the Center (or, without one,
    on the largest member). Members, the Center's index among them, their positions and the mask of the
    members' own main component."""
    keys = sorted(cluster.members)
    if center not in cluster.members:
        center = max(keys, key=lambda t: (sizes.get(t, MIN_SIZE), -t))
    sub = graph.subgraph(keys)
    xy = _forceatlas2(sub, keys, start, GRAVITY)
    i = keys.index(center)
    return keys, i, xy - xy[i], _main_component(sub, keys)


def _region_members(shape: tuple[list[int], int, np.ndarray, np.ndarray], sizes: Mapping[int, float],
                    widths: Mapping[int, float], zoom: float) -> tuple[Positions, float, float]:
    """A region's members around its pinned Center (at 0, 0), the Global layout's way: the shape scaled to FILL
    of a square of REGION_FILL times the members' box area, the clamp, and the label-aware pass. The region is
    that square, or larger when its members need it, with the Center in the middle. Returns the members'
    positions and the region's size."""
    keys, center, raw, main = shape
    s = np.array([sizes[t] for t in keys], dtype=float)
    boxes = Boxes(s, np.array([widths[t] for t in keys], dtype=float), zoom)
    side = math.sqrt(REGION_FILL * float((4 * boxes.half_width * boxes.half_height).sum()))
    # The other members' centroid moves onto the Center and each axis fills the square, so members surround it.
    others = np.arange(len(keys)) != center
    xy = raw - (raw[others].mean(axis=0) if others.any() else 0.0)
    reach = np.abs(xy[others]).max(axis=0) if others.any() else np.zeros(2)
    xy = xy * np.where(reach > 1e-9, REGION_START * side / 2 / np.maximum(reach, 1e-9), 0.0)
    xy[center] = 0.0
    free = np.ones(len(keys))
    free[center] = 0.0
    clamp = Clamp(main, CLAMP_ROOM / zoom) if main.sum() >= 2 else None
    if clamp is not None:
        clamp(xy)
    separate(xy, boxes, free=free, clamp=clamp)
    half_w = float((np.abs(xy[:, 0]) + boxes.half_width).max())
    half_h = float(max((-(xy[:, 1] + boxes.top)).max(), (xy[:, 1] + boxes.bottom).max()))
    width = max(side, 2 * (half_w + REGION_PAD))
    height = max(side, 2 * (half_h + REGION_PAD))
    return {t: (float(x), float(y)) for t, (x, y) in zip(keys, xy)}, width, height


def _pool(singles: list[int], sizes: Mapping[int, float], widths: Mapping[int, float],
          zoom: float) -> tuple[Positions, float, float]:
    """The One-Tag Clusters' grid: every cell as wide as the longest label (or node) and as tall as the biggest
    node with its label; about as many columns as rows by area."""
    s = np.array([sizes[t] for t in singles], dtype=float)
    boxes = Boxes(s, np.array([widths[t] for t in singles], dtype=float), zoom)
    cell_w = 2 * float(boxes.half_width.max()) + boxes.gap
    cell_h = float(s.max()) + (LABEL_MARGIN + LABEL_HEIGHT) / zoom + boxes.gap
    cols = max(1, math.ceil(math.sqrt(len(singles) * cell_h / cell_w)))
    rows = math.ceil(len(singles) / cols)
    drop = (LABEL_MARGIN + LABEL_HEIGHT) / zoom / 2  # the node sits above its label, the pair centred in the cell
    local = {t: (((i % cols) - (cols - 1) / 2) * cell_w, ((i // cols) - (rows - 1) / 2) * cell_h - drop)
             for i, t in enumerate(singles)}
    return local, cols * cell_w + 2 * REGION_PAD, rows * cell_h + 2 * REGION_PAD


def _regions_fit(regions: list[dict[str, Any]], canvas: Canvas) -> float:
    """The first fit of packed regions with their titles (constant on screen): the largest zoom, at most 1."""
    if not regions:
        return 1.0
    x1 = min(r["x"] for r in regions)
    x2 = max(r["x"] + r["width"] for r in regions)
    y2 = max(r["y"] + r["height"] for r in regions)

    def fits(zoom: float) -> bool:
        y1 = min(r["y"] - TITLE_ROOM / zoom for r in regions)
        return (x2 - x1) * zoom <= canvas.width and (y2 - y1) * zoom <= canvas.height

    if fits(1.0):
        return 1.0
    low, high = 1e-3, 1.0
    for _ in range(40):
        mid = (low + high) / 2
        low, high = (mid, high) if fits(mid) else (low, mid)
    return low


def _pack(boxes: list[tuple[float, float]], aspect: float, title_room: float) -> list[tuple[float, float]]:
    """`_shelf_pack` of the boxes in their order and tallest first (ties in their order); the better one wins."""
    tallest = sorted(range(len(boxes)), key=lambda i: (-boxes[i][1], i))
    score, corners = _shelf_pack(boxes, aspect, title_room)
    other_score, other = _shelf_pack([boxes[i] for i in tallest], aspect, title_room)
    if other_score < score - 1e-9:
        corners = [(0.0, 0.0)] * len(boxes)
        for k, i in enumerate(tallest):
            corners[i] = other[k]
    return corners


def _shelf_pack(boxes: list[tuple[float, float]], aspect: float,
                title_room: float) -> tuple[float, list[tuple[float, float]]]:
    """Top-left corners for boxes placed in rows (each row topped by room for the titles), each box in the first
    row with room for it. Every contiguous run of boxes is tried as the row width; the packing whose bounding
    box is smallest, weighted by how far its shape is from `aspect`, wins. Returns its score and corners."""
    if not boxes:
        return 0.0, []
    widths = [w for w, _ in boxes]
    candidates = sorted({sum(widths[i:j]) + REGION_GAP * (j - i - 1)
                         for i in range(len(boxes)) for j in range(i + 1, len(boxes) + 1)})
    best: tuple[float, list[tuple[float, float]]] | None = None
    for row_width in candidates:
        if row_width < max(widths) - 1e-9:
            continue
        corners, width, height = _shelves(boxes, row_width, title_room)
        ratio = width / height if height else aspect
        score = width * height * max(ratio / aspect, aspect / ratio) ** 0.5
        if best is None or score < best[0] - 1e-9:
            best = (score, corners)
    assert best is not None
    return best


def _shelves(boxes: list[tuple[float, float]], row_width: float,
             title_room: float) -> tuple[list[tuple[float, float]], float, float]:
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
    tops, y = [], title_room
    for _, h in rows:
        tops.append(y)
        y += h + REGION_GAP + title_room
    width = max(used for used, _ in rows)
    return [(x, tops[i]) for i, x in placed], width, tops[-1] + rows[-1][1]


def _sort_key(key: Any) -> tuple[int, Any]:
    """Numeric ids sort as numbers, even when they arrive as strings (the app's element ids)."""
    try:
        return 0, int(key)
    except (TypeError, ValueError):
        return 1, str(key)
