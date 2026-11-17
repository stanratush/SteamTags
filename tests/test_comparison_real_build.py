"""Cluster Comparison on the full Build, each dataset on its pick (skipped without the Build on disk).

The expected numbers are the spec's "Facts this spec rests on" (prototype 04's report): Lift, Leiden, no Minimum
Months Filter, Genre Tags and defining Tags hidden, default Pair Constraints."""

from __future__ import annotations

from pathlib import Path

import pytest

from steamstudy.app import ps_cache, ps_view
from steamstudy.app.loader import load_build
from steamstudy.network import comparison as CMP
from steamstudy.network import selection as SEL
from steamstudy.network.graph import filter_games

REAL_BUILD = Path(__file__).resolve().parents[1] / "builds" / "20261005T062558Z-full" / "20261008T221504Z-7a23ae9f"

# Cluster Matches per pair (A = the earlier dataset in the Build's order), and ARI (comparable Tags) to 2 dp.
PAIRS = {
    ("overall", "puzzle"): (8, 0.23), ("overall", "rpg"): (16, 0.17), ("overall", "strategy"): (7, 0.32),
    ("overall", "simulation"): (7, 0.27), ("puzzle", "rpg"): (15, 0.07), ("puzzle", "strategy"): (7, 0.30),
    ("puzzle", "simulation"): (5, 0.07), ("rpg", "strategy"): (18, 0.10), ("rpg", "simulation"): (14, 0.11),
    ("strategy", "simulation"): (6, 0.53),
}
GAMES_IN_COMMON_WITH_OVERALL = {"puzzle": 1, "rpg": 38, "strategy": 24, "simulation": 28}

pytestmark = pytest.mark.skipif(not REAL_BUILD.is_dir(), reason="the full Build 20261008T221504Z-7a23ae9f is not on disk")


@pytest.fixture(scope="module")
def pairs():
    mp = pytest.MonkeyPatch()
    mp.setattr(ps_cache, "NAME_LENGTH", 64)  # this Build's cache predates the 16-digit folder names
    try:
        ctx = load_build(REAL_BUILD)
        settings, constraints = ps_view.defaults_of(ctx)
        partitions = []
        for ds in ctx.datasets:
            view = ps_view.dataset_view(ctx, settings, ds.key, constraints, constraints)
            assert view.star is not None, ds.key
            r = view.result(view.star)
            partitions.append(CMP.Partition(
                dataset=ds.key, clusters=tuple(SEL.clusters_of(r.nodes, r.selected)), edged=frozenset(r.edged),
                hidden=frozenset(settings.hidden_tag_ids(ctx.context(ds.key))),
                games=tuple(filter_games(ctx.games(ds.key), settings.min_months)), min_games_per_tag=view.star[0]))
    finally:
        mp.undo()
    return CMP.compare_all(partitions)


def test_ten_pairs_and_103_cluster_matches_with_the_reported_ari(pairs):
    assert {k: (p.n_matches, round(p.ari, 2)) for k, p in pairs.items()} == PAIRS
    assert sum(p.n_matches for p in pairs.values()) == 103


def test_match_jaccard_reaches_0_58_and_games_in_common_with_overall(pairs):
    assert round(max(m.jaccard for p in pairs.values() for m in p.matches), 2) == 0.58
    assert {b: pairs[("overall", b)].n_games_in_common for b in GAMES_IN_COMMON_WITH_OVERALL} == \
        GAMES_IN_COMMON_WITH_OVERALL


def test_at_a_minimum_of_0_10_48_matches_remain(pairs):
    assert sum(m.jaccard >= 0.10 for p in pairs.values() for m in p.matches) == 48
