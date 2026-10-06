"""Graph positions: no node hides another, the packed Cluster-separated layout, and determinism."""

from __future__ import annotations

import math

import pytest

from steamstudy.app.loader import load_build
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.network.layout import cluster_separated_positions, global_positions, node_sizes, relayout
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
    centers = {label: c.center for label, c in state.centers.items()}
    return cluster_separated_positions(state.graph, state.clusters, state.positions, state.settings.seed,
                                       centers=centers, sizes=state.sizes)


@pytest.mark.parametrize("loosest", [False, True])
@pytest.mark.parametrize("dataset", DATASETS)
def test_no_two_nodes_overlap_in_either_layout_or_after_relayout(ctx, dataset, loosest):
    state = _state(ctx, dataset, loosest)
    assert state.nodes and set(state.sizes) >= set(state.nodes)
    visible = {t: state.positions[t] for t in state.nodes}
    assert _overlaps(visible, state.sizes) == []
    assert _overlaps(_separated(state)[0], state.sizes) == []
    refined = relayout(state.graph, state.positions, state.settings.seed, sizes=state.sizes)
    assert _overlaps(refined, state.sizes) == []


def test_the_global_layout_has_no_overlap_on_the_full_loose_network(ctx):
    games = ctx.games("overall")
    positions = global_positions(games, 0, "shared_games", 7)
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
    state = _state(ctx, "overall")
    assert {t: state.sizes[t] for t in state.nodes} == {t: sizes[t] for t in state.nodes}  # not the visible set


def test_the_same_inputs_give_identical_positions(ctx):
    a, b = _state(ctx, "overall"), _state(ctx, "overall")
    assert a.positions == b.positions
    assert _separated(a) == _separated(b)
    assert relayout(a.graph, a.positions, 3, sizes=a.sizes) == relayout(b.graph, b.positions, 3, sizes=b.sizes)


def test_moving_a_threshold_leaves_the_global_positions_unchanged(ctx):
    default = _state(ctx, "overall")
    other = compute_state(ctx.games("overall"), default.settings.with_(min_games_per_tag=12, min_shared_games=5),
                          ctx.context("overall"))
    assert other.positions == default.positions


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
            radius = state.sizes[t] / 2
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
