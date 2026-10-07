"""Graph positions: layout downstream of analysis, no node hides another, the packed Cluster-separated layout,
and determinism."""

from __future__ import annotations

import ast
import math
import random
import time
from pathlib import Path

import networkx as nx

import pytest

from steamstudy.app.loader import load_build
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.network.layout import (LABEL_HEIGHT, LABEL_MARGIN, MIN_ZOOM, REFERENCE_CANVAS, TITLE_ROOM, Canvas, Layout,
                                      LayoutParams, label_width, layout_input, layout_state, loose_layout,
                                      node_sizes, restore, tidy, cluster_separated_positions)
from steamstudy.network.cluster import Cluster
from steamstudy.network.model import Game, Settings
from steamstudy.network.state import compute_state
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world

DATASETS = ["overall", "puzzle"]  # the other datasets have no games in the test world
CANVASES = [Canvas(1116, 678), Canvas(956, 561)]  # 1440 x 900 and 1280 x 800 with the Tables and Inspector closed
LABEL_PX = 11.5


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    config = load_config(__import__("conftest").CONFIG_DIR)
    root = tmp_path_factory.mktemp("layout")
    return load_build(write_build(build(Snapshot(tagged_world().snapshot(root / "snap")), config,
                                        "20261006T120000Z-abcdef12"), root))


def _settings(ctx, dataset, loosest):
    s = ctx.default_settings(dataset)
    return s.with_(min_games_per_tag=1, min_shared_games=1, hidden_tag_ids=()) if loosest else s


def _state(ctx, dataset, loosest=False):
    return compute_state(ctx.games(dataset), _settings(ctx, dataset, loosest), ctx.context(dataset))


def _overlaps(positions, sizes):
    tags = sorted(positions)
    bad = []
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            (xa, ya), (xb, yb) = positions[a], positions[b]
            if math.hypot(xa - xb, ya - yb) < (sizes[a] + sizes[b]) / 2 - 1e-6:
                bad.append((a, b))
    return bad


def _separated(state):
    layout = layout_state(state)
    return layout.separated, layout.regions


NETWORK = Path(__import__("steamstudy.network", fromlist=["x"]).__path__[0])


def _imports(path):
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
    return found


def test_only_the_layout_module_knows_about_layout():
    """ADR 0002: no analysis module can import the layout, so no coordinate can reach a metric."""
    modules = sorted(NETWORK.glob("*.py"))
    assert {p.stem for p in modules} >= {"state", "metrics", "cluster", "stability", "sensitivity", "sweep", "layout"}
    for path in modules:
        if path.stem != "layout":
            assert "steamstudy.network.layout" not in _imports(path), path.name


def test_compute_state_holds_no_coordinates_and_layout_state_only_reads_it(ctx):
    state = _state(ctx, "overall")
    assert not hasattr(state, "positions") and not hasattr(state, "sizes")
    before = (state.state_id, [sorted(c.members) for c in state.clusters], state.modularity, state.silhouette.mean)
    layout = layout_state(state)
    assert isinstance(layout, Layout)
    assert set(layout.positions) == set(state.nodes) == set(layout.separated) == set(layout.sizes)
    assert layout.regions
    assert (state.state_id, [sorted(c.members) for c in state.clusters], state.modularity,
            state.silhouette.mean) == before


@pytest.mark.parametrize("loosest", [False, True])
@pytest.mark.parametrize("dataset", DATASETS)
def test_no_two_nodes_overlap_in_either_layout_or_after_tidy(ctx, dataset, loosest):
    state = _state(ctx, dataset, loosest)
    layout = layout_state(state)
    assert state.nodes and set(layout.sizes) >= set(state.nodes)
    assert _overlaps(layout.positions, layout.sizes) == []
    assert _overlaps(layout.separated, layout.sizes) == []
    tidied, _ = tidy(layout_input(state), layout.positions, REFERENCE_CANVAS, zoom=layout.zoom)
    assert _overlaps(tidied, layout.sizes) == []


def test_the_global_layout_has_no_overlap_on_the_full_loose_network(ctx):
    games = ctx.games("overall")
    positions = loose_layout(games, 0, "shared_games", 7)
    sizes = node_sizes(games, 0)
    assert len(positions) > len(_state(ctx, "overall").nodes)  # the loose network holds more tags
    assert _overlaps(positions, sizes) == []


def test_node_size_is_fixed_by_n_games_relative_to_the_most_frequent_tag(ctx):
    games = ctx.games("overall")
    sizes = node_sizes(games, 0)
    counts = {t: sum(t in g.tag_ids for g in games) for t in sizes}
    biggest = max(counts.values())
    top = [t for t, n in counts.items() if n == biggest]
    assert all(sizes[t] == max(sizes.values()) for t in top)
    assert all(sizes[a] <= sizes[b] for a in counts for b in counts if counts[a] <= counts[b])
    assert max(sizes.values()) == pytest.approx(48.0) and min(sizes.values()) >= 18.0  # 18 + 30 * sqrt(ratio)
    assert layout_state(_state(ctx, "overall")).sizes == {t: sizes[t] for t in _state(ctx, "overall").nodes}


def test_the_same_inputs_give_identical_positions(ctx):
    a, b = layout_state(_state(ctx, "overall")), layout_state(_state(ctx, "overall"))
    assert a == b
    inp = layout_input(_state(ctx, "overall"))
    assert tidy(inp, a.positions, REFERENCE_CANVAS, zoom=a.zoom) == tidy(inp, b.positions, REFERENCE_CANVAS, zoom=b.zoom)


def _main_component(state):
    return min(nx.connected_components(state.graph), key=lambda c: (-len(c), min(c)))


def _clamp_violations(state, positions, zoom=1.0):
    """Tags farther from the main component's centre than its radius plus 1.5 label heights (per axis), with the
    labels at their on-screen size for `zoom`."""
    main = _main_component(state)
    xs, ys = [positions[t][0] for t in main], [positions[t][1] for t in main]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    room = 1.5 * LABEL_HEIGHT / zoom
    rx, ry = (max(xs) - min(xs)) / 2 + room, (max(ys) - min(ys)) / 2 + room
    return [t for t, (x, y) in positions.items() if abs(x - cx) > rx + 1e-6 or abs(y - cy) > ry + 1e-6]


@pytest.mark.parametrize("dataset", DATASETS)
def test_unlinked_tags_stay_next_to_the_main_graph(ctx, dataset):
    state = _state(ctx, dataset)
    components = sorted(len(c) for c in nx.connected_components(state.graph))
    if dataset == "puzzle":
        assert components[0] == 1 and components[-1] < len(state.nodes)  # tags without a visible link
    layout = layout_state(state)
    positions = layout.positions
    assert _clamp_violations(state, positions, layout.zoom) == []
    main = _main_component(state)
    for axis in (0, 1):
        extent = max(p[axis] for p in positions.values()) - min(p[axis] for p in positions.values())
        main_extent = max(positions[t][axis] for t in main) - min(positions[t][axis] for t in main)
        assert extent <= 1.3 * main_extent


def test_the_layout_depends_on_the_visible_network_not_on_the_clustering(ctx):
    default = _state(ctx, "overall")
    other = compute_state(ctx.games("overall"), default.settings.with_(resolution=1.7, algorithm="leiden"),
                          ctx.context("overall"))
    assert other.state_id != default.state_id
    assert layout_state(other).positions == layout_state(default).positions


def test_a_threshold_change_moves_the_graph_and_moving_back_restores_it(ctx):
    default = _state(ctx, "overall")
    moved = compute_state(ctx.games("overall"), default.settings.with_(min_shared_games=12), ctx.context("overall"))
    again = _state(ctx, "overall")
    same = set(moved.nodes) & set(default.nodes)
    assert {t: layout_state(moved).positions[t] for t in same} != {t: layout_state(default).positions[t] for t in same}
    assert layout_state(again).positions == layout_state(default).positions


def test_gravity_and_the_clamp_are_layout_settings(ctx):
    state = _state(ctx, "puzzle")
    default = layout_state(state).positions
    assert layout_state(state, params=LayoutParams(gravity=10.0)).positions != default
    unclamped = layout_state(state, params=LayoutParams(clamp=False)).positions
    assert unclamped != default


@pytest.mark.parametrize("loosest, budget", [(False, 0.3), (True, 1.5)])
def test_a_layout_is_fast_enough(ctx, loosest, budget):
    state = _state(ctx, "overall", loosest)
    layout_state(state)  # warm-up (imports, the cached loose layout)
    started = time.perf_counter()
    layout_state(state)
    assert time.perf_counter() - started <= budget


def test_a_large_network_is_laid_out_within_the_budget():
    """About the loosest real state: 100 games of about 20 tags each, 250 tags, some 7,000 links."""
    rng = random.Random(5)
    weights = [1 / (t ** 0.8) for t in range(1, 251)]
    games = []
    for i in range(100):
        tags: set[int] = set()
        while len(tags) < 20:
            tags.add(rng.choices(range(1, 251), weights)[0])
        games.append(Game(i, f"g{i}", i + 1, 12, tuple(sorted(tags)), tuple(f"tag number {t}" for t in sorted(tags))))
    settings = Settings(build_id="perf", dataset="overall", min_games_per_tag=1, min_shared_games=1, seed=3,
                        null_replicates=2, noise_seeds=2)
    state = compute_state(games, settings)
    assert len(state.nodes) >= 200 and state.graph.number_of_edges() >= 5000
    layout_state(state, Canvas(500, 400))  # warm-up: the dataset's loose layout is computed once per basis
    started = time.perf_counter()
    layout = layout_state(state)
    assert time.perf_counter() - started <= 1.5
    assert _clamp_violations(state, layout.positions, layout.zoom) == []
    assert _box_overlaps(_boxes(state, layout.positions, layout.sizes, layout.zoom)) == []


# ----------------------------------------------------------------------------- geometry at the first fit


def _boxes(state, positions, sizes, zoom):
    """Each node plus its label below it (centred), in model units, with the label at 11.5 px on screen."""
    out = {}
    for t, (x, y) in positions.items():
        size, width = sizes[t], label_width(state.network.tag_names[t]) / zoom
        half = max(size, width) / 2
        out[t] = (x - half, y - size / 2, x + half, y + size / 2 + (LABEL_MARGIN + LABEL_HEIGHT) / zoom)
    return out


def _box_overlaps(boxes):
    tags = sorted(boxes)
    return [(a, b) for i, a in enumerate(tags) for b in tags[i + 1:]
            if boxes[a][0] < boxes[b][2] and boxes[b][0] < boxes[a][2]
            and boxes[a][1] < boxes[b][3] and boxes[b][1] < boxes[a][3]]


def _fit_zoom(state, positions, sizes, canvas, regions=()):
    """The first fit: the largest zoom, at most 1, at which every node and label (and every region with its
    title, 22 px above it) is inside the canvas."""
    def fits(zoom):
        boxes = list(_boxes(state, positions, sizes, zoom).values())
        boxes += [(r["x"], r["y"] - TITLE_ROOM / zoom, r["x"] + r["width"], r["y"] + r["height"]) for r in regions]
        width = max(b[2] for b in boxes) - min(b[0] for b in boxes)
        height = max(b[3] for b in boxes) - min(b[1] for b in boxes)
        return width * zoom <= canvas.width and height * zoom <= canvas.height
    if fits(1.0):
        return 1.0
    low, high = 0.01, 1.0
    for _ in range(50):
        low, high = ((low + high) / 2, high) if fits((low + high) / 2) else (low, (low + high) / 2)
    return low


@pytest.mark.parametrize("canvas", CANVASES, ids=["1440x900", "1280x800"])
@pytest.mark.parametrize("dataset", DATASETS)
def test_every_label_fits_at_the_first_fit(ctx, dataset, canvas):
    state = _state(ctx, dataset)
    layout = layout_state(state, canvas)
    zoom = _fit_zoom(state, layout.positions, layout.sizes, canvas)
    assert zoom >= layout.zoom - 1e-6  # the first fit is at least the zoom the labels were spaced for
    assert _box_overlaps(_boxes(state, layout.positions, layout.sizes, zoom)) == []
    assert min(layout.sizes.values()) * zoom >= 14.0
    assert _clamp_violations(state, layout.positions, layout.zoom) == []


def test_one_model_unit_is_one_pixel_at_the_first_fit_of_a_canvas_that_holds_the_graph(ctx):
    state = _state(ctx, "overall")
    big, small = layout_state(state, Canvas(1600, 1000)), layout_state(state, Canvas(700, 420))
    assert big.zoom == 1.0
    assert _fit_zoom(state, big.positions, big.sizes, Canvas(1600, 1000)) == 1.0
    width = lambda p: max(x for x, _ in p.values()) - min(x for x, _ in p.values())  # noqa: E731
    assert width(small.positions) < width(big.positions)  # laid out for the smaller canvas, not just zoomed


def test_a_small_set_sits_centred_at_its_designed_size():
    names = {1: "Puzzle", 2: "Relaxing", 3: "Casual", 4: "2D", 5: "Cute"}
    rows = [(1, 2, 3)] * 4 + [(3, 4)] * 3 + [(4, 5)] * 3
    games = [Game(i, f"g{i}", i + 1, 12, tags, tuple(names[t] for t in tags)) for i, tags in enumerate(rows)]
    state = compute_state(games, Settings(build_id="small", dataset="overall", min_games_per_tag=1,
                                          min_shared_games=1, seed=2, null_replicates=2, noise_seeds=2))
    assert len(state.nodes) == 5
    canvas = Canvas(1116, 678)
    layout = layout_state(state, canvas)
    assert layout.zoom == 1.0 and _fit_zoom(state, layout.positions, layout.sizes, canvas) == 1.0
    boxes = _boxes(state, layout.positions, layout.sizes, 1.0)
    for t, (x1, y1, x2, y2) in boxes.items():  # every tag's nearest neighbour within 3x the room their boxes need
        def need(u):
            ox1, oy1, ox2, oy2 = boxes[u]
            dx = abs((x1 + x2) / 2 - (ox1 + ox2) / 2) / (((x2 - x1) + (ox2 - ox1)) / 2)
            dy = abs((y1 + y2) / 2 - (oy1 + oy2) / 2) / (((y2 - y1) + (oy2 - oy1)) / 2)
            return max(dx, dy)
        assert min(need(u) for u in boxes if u != t) <= 3.0 + 1e-9
    assert _box_overlaps(boxes) == []


def test_label_widths_come_from_a_fixed_table():
    assert label_width("Puzzle") == label_width("Puzzle")
    assert label_width("Massively Multiplayer") > label_width("Puzzle") > label_width("2D") > 0
    assert label_width("WWW") > label_width("iii")
    assert 1.05 * 6 * 6.0 < label_width("Puzzle") < 1.2 * 6 * 7.5  # about 10 % above the 11.5 px bold widths
    assert label_width("Café") > label_width("Caf")  # a character outside the table still takes room


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("loosest", [False, True])
def test_regions_are_packed_tightly_with_each_center_in_the_middle(ctx, dataset, loosest):
    state = _state(ctx, dataset, loosest)
    layout = layout_state(state)
    positions, regions, zoom = layout.separated, layout.regions, layout.separated_zoom
    multi = [c for c in state.clusters if c.size >= 2]
    assert [r["cluster"] for r in regions[:len(multi)]] == [c.label for c in multi]
    x1 = min(r["x"] for r in regions)
    y1 = min(r["y"] for r in regions)
    x2 = max(r["x"] + r["width"] for r in regions)
    y2 = max(r["y"] + r["height"] for r in regions)
    assert (x2 - x1) * (y2 - y1) <= 1.5 * sum(r["width"] * r["height"] for r in regions)
    boxes = _boxes(state, positions, layout.sizes, zoom)
    for c, r in zip(multi, regions):
        center = state.centers[c.label].center
        cx, cy = positions[center]
        assert cx == pytest.approx(r["x"] + r["width"] / 2) and cy == pytest.approx(r["y"] + r["height"] / 2)
    members = {t: r for c, r in zip(multi, regions) for t in c.members}
    if len(state.clusters) > len(multi):
        assert regions[-1]["cluster"] == "one_tag_pool"
        members.update({min(c.members): regions[-1] for c in state.clusters if c.size == 1})
    for t, r in members.items():  # every member's node and label inside its region
        bx1, by1, bx2, by2 = boxes[t]
        assert r["x"] <= bx1 and bx2 <= r["x"] + r["width"] and r["y"] <= by1 and by2 <= r["y"] + r["height"]


def test_a_region_is_sized_by_its_members_label_boxes(ctx):
    state = _state(ctx, "overall", loosest=True)
    layout = layout_state(state)
    boxes = _boxes(state, layout.separated, layout.sizes, layout.separated_zoom)
    area = {c.label: sum((boxes[t][2] - boxes[t][0]) * (boxes[t][3] - boxes[t][1]) for t in c.members)
            for c in state.clusters if c.size >= 2}
    regions = [r for r in layout.regions if r["cluster"] in area]
    assert len(regions) >= 2
    for r in regions:
        assert 2.5 * area[r["cluster"]] <= r["width"] * r["height"] <= 6 * area[r["cluster"]]
    big = max(regions, key=lambda r: area[r["cluster"]])
    small = min(regions, key=lambda r: area[r["cluster"]])
    assert big["width"] * big["height"] > small["width"] * small["height"]


def test_the_one_tag_pool_is_a_grid_as_wide_as_its_longest_label():
    names = {i: f"tag {i}" for i in range(1, 7)} | {7: "A Very Long Single Tag Name", 8: "x"}
    rows = [(1, 2, 3)] * 3 + [(4, 5, 6)] * 3 + [(7,)] * 2 + [(8,)] * 2
    games = [Game(i, f"g{i}", i + 1, 12, tags, tuple(names[t] for t in tags)) for i, tags in enumerate(rows)]
    state = compute_state(games, Settings(build_id="pool", dataset="overall", min_games_per_tag=1,
                                          min_shared_games=2, seed=2, null_replicates=2, noise_seeds=2))
    singles = [min(c.members) for c in state.clusters if c.size == 1]
    assert sorted(singles) == [7, 8]
    layout = layout_state(state)
    pool = layout.regions[-1]
    assert pool["cluster"] == "one_tag_pool"
    assert pool["width"] >= label_width(names[7]) / layout.separated_zoom
    boxes = _boxes(state, layout.separated, layout.sizes, layout.separated_zoom)
    assert _box_overlaps({t: boxes[t] for t in singles}) == []


@pytest.mark.parametrize("canvas", CANVASES, ids=["1440x900", "1280x800"])
@pytest.mark.parametrize("dataset", DATASETS)
def test_the_cluster_separated_labels_fit_at_the_first_fit_when_the_regions_allow(ctx, dataset, canvas):
    """Best effort (the spec's amendment): the labels never overlap at the zoom they were spaced for, and the first
    fit is at least that zoom unless even MIN_ZOOM could not hold the regions."""
    state = _state(ctx, dataset)
    layout = layout_state(state, canvas)
    assert layout.separated_zoom >= MIN_ZOOM
    assert _box_overlaps(_boxes(state, layout.separated, layout.sizes, layout.separated_zoom)) == []
    zoom = _fit_zoom(state, layout.separated, layout.sizes, canvas, layout.regions)
    if layout.separated_zoom > MIN_ZOOM:
        assert zoom >= layout.separated_zoom - 1e-6
    assert _box_overlaps(_boxes(state, layout.separated, layout.sizes, zoom)) == [] or zoom < layout.separated_zoom
    assert min(layout.sizes.values()) * layout.separated_zoom >= 14.0


# ----------------------------------------------------------------------------- Tidy and old exports


@pytest.mark.parametrize("canvas", CANVASES, ids=["1440x900", "1280x800"])
@pytest.mark.parametrize("dataset", DATASETS)
def test_every_label_fits_at_the_first_fit_after_tidy(ctx, dataset, canvas):
    state = _state(ctx, dataset)
    layout = layout_state(state, canvas)
    positions, zoom = tidy(layout_input(state), layout.positions, canvas, zoom=layout.zoom)
    fit = _fit_zoom(state, positions, layout.sizes, canvas)
    assert fit >= zoom - 1e-6 and zoom >= layout.zoom - 1e-6  # Tidy never needs a lower zoom
    assert _box_overlaps(_boxes(state, positions, layout.sizes, fit)) == []
    assert min(layout.sizes.values()) * fit >= 14.0
    assert _clamp_violations(state, positions, zoom) == []


def test_tidy_keeps_dragged_nodes_exactly_where_they_were_dropped(ctx):
    state = _state(ctx, "overall")
    layout = layout_state(state)
    hub, other = sorted(state.nodes, key=lambda t: -state.network.n(t))[:2]
    (hx, hy), (ox, oy) = layout.positions[hub], layout.positions[other]
    dropped = {hub: (hx + 120.5, hy - 60.25), other: ((hx + ox) / 2, (hy + oy) / 2)}
    current = {**layout.positions, **dropped}
    positions, zoom = tidy(layout_input(state), current, REFERENCE_CANVAS, pinned=dropped, zoom=layout.zoom)
    assert {t: positions[t] for t in dropped} == dropped  # exactly, not approximately
    boxes = _boxes(state, positions, layout.sizes, zoom)
    assert _box_overlaps(boxes) == []
    assert set(_clamp_violations(state, positions, zoom)) <= set(dropped)


def test_an_old_relayout_export_with_far_away_tags_opens_readable(ctx):
    state = _state(ctx, "puzzle")
    loose = loose_layout(ctx.games("puzzle"), state.settings.min_months, state.settings.clustering_weight,
                         state.settings.seed)
    stored = {t: loose[t] for t in state.nodes}  # the old layout: spring layout units, about 1,000 across
    lonely = [t for t in state.nodes if state.graph.degree(t) == 0]
    assert lonely
    for i, t in enumerate(lonely):  # thrown about 1,000 units out, as the old Re-layout did
        angle = i * 2.4
        stored[t] = (1100 * math.cos(angle), 1100 * math.sin(angle))
    positions, zoom = restore(layout_input(state), stored, REFERENCE_CANVAS)
    sizes = layout_state(state).sizes
    assert _clamp_violations(state, positions, zoom) == []
    fit = _fit_zoom(state, positions, sizes, REFERENCE_CANVAS)
    assert fit >= zoom - 1e-6
    assert _box_overlaps(_boxes(state, positions, sizes, fit)) == []
    main = sorted(_main_component(state))  # the shape is kept: tags far apart left to right stay in that order
    xs_before = sorted(main, key=lambda t: stored[t][0])
    left, right = xs_before[0], xs_before[-1]
    assert positions[left][0] < positions[right][0]


def test_a_center_outside_its_clusters_linked_core_stays_in_the_middle_of_its_region():
    """Louvain can return a cluster whose members are not all linked; its Center stays pinned in the middle."""
    graph = nx.Graph()
    graph.add_nodes_from(range(1, 12))
    graph.add_edges_from([(1, 2), (1, 3), (2, 3)], w=5.0)
    members = frozenset(range(1, 12))
    start = {t: (100.0 * math.cos(t), 100.0 * math.sin(t)) for t in members}
    sizes = {t: 20.0 for t in members}
    widths = {t: label_width(f"tag {t}") for t in members}
    for center in (4, 11):
        positions, regions, _ = cluster_separated_positions(
            graph, [Cluster("C1", members)], start, centers={"C1": center}, sizes=sizes, widths=widths)
        (region,) = regions
        assert all(math.isfinite(v) for p in positions.values() for v in p)
        assert positions[center] == pytest.approx((region["x"] + region["width"] / 2, region["y"] + region["height"] / 2))
        assert region["width"] < 2000 and region["height"] < 2000


def test_a_one_tag_network_is_laid_out_and_tidied():
    games = [Game(i, f"g{i}", i + 1, 12, (7,), ("Lonely",)) for i in range(3)]
    state = compute_state(games, Settings(build_id="one", dataset="overall", min_games_per_tag=1,
                                          min_shared_games=1, seed=2, null_replicates=2, noise_seeds=2))
    assert state.nodes == [7]
    layout = layout_state(state)
    assert all(math.isfinite(v) for v in layout.positions[7] + layout.separated[7])
    positions, _ = tidy(layout_input(state), layout.positions, REFERENCE_CANVAS, zoom=layout.zoom)
    assert all(math.isfinite(v) for v in positions[7])


def test_tidy_settles_the_others_around_where_nodes_were_dropped(ctx):
    """The dragged nodes anchor Tidy's frame: dragging the whole picture somewhere else moves the rest with it."""
    state = _state(ctx, "overall")
    layout = layout_state(state)
    shift = (700.0, 400.0)
    moved = {t: (x + shift[0], y + shift[1]) for t, (x, y) in layout.positions.items()}
    pinned = dict(list(moved.items())[:3])
    positions, _ = tidy(layout_input(state), {**layout.positions, **pinned}, REFERENCE_CANVAS, pinned=pinned,
                        zoom=layout.zoom)
    others = [t for t in state.nodes if t not in pinned]
    centre = lambda ps, ts: (sum(ps[t][0] for t in ts) / len(ts), sum(ps[t][1] for t in ts) / len(ts))  # noqa: E731
    dropped = centre(pinned, list(pinned))
    gap = lambda c: math.dist(c, dropped)  # noqa: E731
    assert gap(centre(positions, others)) < 0.8 * gap(centre(layout.positions, others))  # the rest followed them


def test_overlap_removal_always_ends_without_overlaps_even_when_rounds_run_out():
    from steamstudy.network.layout import remove_overlaps

    crowd = {i: (float(i), 0.0) for i in range(10)}  # a chain of size-20 nodes 1 unit apart: one round is not enough
    sizes = {i: 20.0 for i in crowd}
    out = remove_overlaps(crowd, sizes, max_rounds=1, fixed=[0])
    assert _overlaps(out, sizes) == [] and out[0] == crowd[0]
    assert remove_overlaps(crowd, sizes, max_rounds=1, fixed=[0]) == out  # still deterministic
