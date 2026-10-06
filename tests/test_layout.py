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
from steamstudy.network.layout import (LABEL_HEIGHT, Canvas, Layout, LayoutParams, layout_state, loose_layout, node_sizes,
                                      relayout)
from steamstudy.network.model import Game, Settings
from steamstudy.network.state import compute_state
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world

DATASETS = ["overall", "puzzle"]  # the other datasets have no games in the test world


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
def test_no_two_nodes_overlap_in_either_layout_or_after_relayout(ctx, dataset, loosest):
    state = _state(ctx, dataset, loosest)
    layout = layout_state(state)
    assert state.nodes and set(layout.sizes) >= set(state.nodes)
    assert _overlaps(layout.positions, layout.sizes) == []
    assert _overlaps(layout.separated, layout.sizes) == []
    refined = relayout(state.graph, layout.positions, state.settings.seed, sizes=layout.sizes)
    assert _overlaps(refined, layout.sizes) == []


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
    graph = _state(ctx, "overall").graph
    assert relayout(graph, a.positions, 3, sizes=a.sizes) == relayout(graph, b.positions, 3, sizes=b.sizes)


def _main_component(state):
    return min(nx.connected_components(state.graph), key=lambda c: (-len(c), min(c)))


def _clamp_violations(state, positions):
    """Tags farther from the main component's centre than its radius plus 1.5 label heights (per axis)."""
    main = _main_component(state)
    xs, ys = [positions[t][0] for t in main], [positions[t][1] for t in main]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rx, ry = (max(xs) - min(xs)) / 2 + 1.5 * LABEL_HEIGHT, (max(ys) - min(ys)) / 2 + 1.5 * LABEL_HEIGHT
    return [t for t, (x, y) in positions.items() if abs(x - cx) > rx + 1e-6 or abs(y - cy) > ry + 1e-6]


@pytest.mark.parametrize("dataset", DATASETS)
def test_unlinked_tags_stay_next_to_the_main_graph(ctx, dataset):
    state = _state(ctx, dataset)
    components = sorted(len(c) for c in nx.connected_components(state.graph))
    if dataset == "puzzle":
        assert components[0] == 1 and components[-1] < len(state.nodes)  # tags without a visible link
    positions = layout_state(state).positions
    assert _clamp_violations(state, positions) == []
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
    assert _clamp_violations(state, layout.positions) == []


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("loosest", [False, True])
def test_regions_are_packed_tightly_with_each_center_in_the_middle(ctx, dataset, loosest):
    state = _state(ctx, dataset, loosest)
    positions, regions = _separated(state)
    multi = [c for c in state.clusters if c.size >= 2]
    assert [r["cluster"] for r in regions[:len(multi)]] == [c.label for c in multi]
    x1 = min(r["x"] for r in regions)
    y1 = min(r["y"] for r in regions)
    x2 = max(r["x"] + r["width"] for r in regions)
    y2 = max(r["y"] + r["height"] for r in regions)
    assert (x2 - x1) * (y2 - y1) <= 1.5 * sum(r["width"] * r["height"] for r in regions)
    for c, r in zip(multi, regions):
        center = state.centers[c.label].center
        cx, cy = positions[center]
        assert cx == pytest.approx(r["x"] + r["width"] / 2) and cy == pytest.approx(r["y"] + r["height"] / 2)
        for t in c.members:  # every member inside its region
            px, py = positions[t]
            radius = layout_state(state).sizes[t] / 2
            assert r["x"] <= px - radius and px + radius <= r["x"] + r["width"]
            assert r["y"] <= py - radius and py + radius <= r["y"] + r["height"]
    if len(state.clusters) > len(multi):
        assert regions[-1]["cluster"] == "one_tag_pool"


def test_region_side_grows_with_the_square_root_of_its_members(ctx):
    state = _state(ctx, "overall", loosest=True)
    _, regions = _separated(state)
    sizes = {c.label: c.size for c in state.clusters}
    multi = [r for r in regions if r["cluster"] in sizes]
    assert len(multi) >= 2
    for r in multi:
        assert r["width"] == pytest.approx(r["height"])
    big, small = multi[0], multi[-1]
    if sizes[big["cluster"]] > sizes[small["cluster"]]:
        assert big["width"] > small["width"]


def test_overlap_removal_always_ends_without_overlaps_even_when_rounds_run_out():
    from steamstudy.network.layout import remove_overlaps

    crowd = {i: (float(i), 0.0) for i in range(10)}  # a chain of size-20 nodes 1 unit apart: one round is not enough
    sizes = {i: 20.0 for i in crowd}
    out = remove_overlaps(crowd, sizes, max_rounds=1, fixed=[0])
    assert _overlaps(out, sizes) == [] and out[0] == crowd[0]
    assert remove_overlaps(crowd, sizes, max_rounds=1, fixed=[0]) == out  # still deterministic
