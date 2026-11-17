"""Cluster Comparison core (`steamstudy.network.comparison`): matches, figures, Tag groups, flags, the pair
overview, games in both Clusters and the Comparison State key, on small hand-made partitions."""

from __future__ import annotations

import pytest

from steamstudy.network import comparison as CMP
from steamstudy.network.cluster import Cluster
from steamstudy.network.model import Game


def part(dataset, clusters, *, edged=None, hidden=(), games=(), g=1):
    """A resolved partition: `clusters` maps a label to its Tag ids; every Tag is edged unless `edged` is given."""
    cs = tuple(Cluster(label, frozenset(tags)) for label, tags in clusters.items())
    nodes = {t for c in cs for t in c.members}
    return CMP.Partition(dataset=dataset, clusters=cs, edged=frozenset(nodes if edged is None else edged),
                         hidden=frozenset(hidden), games=tuple(games), min_games_per_tag=g)


def game(appid, rank, *tags):
    return Game(appid, f"game {appid}", rank, 0.0, tuple(tags), tuple(f"t{t}" for t in tags))


def match(pair, a, b):
    return next(m for m in pair.matches if (m.cluster_a, m.cluster_b) == (a, b))


def test_cluster_matches_are_every_pair_of_multi_tag_clusters_sharing_a_tag():
    A = part("overall", {"C1": [1, 2, 3, 4], "C2": [5, 6], "C3": [7]})
    B = part("puzzle", {"C1": [1, 2, 5, 9], "C2": [3, 10], "C3": [6], "C4": [7]})
    pair = CMP.compare_pair(A, B)
    assert {(m.cluster_a, m.cluster_b) for m in pair.matches} == {("C1", "C1"), ("C1", "C2"), ("C2", "C1")}
    m = match(pair, "C1", "C1")
    # n = 2 shared (1, 2) of |a| = 4 and |b| = 4: 2 / 6.
    assert (m.n_shared, m.n_tags_a, m.n_tags_b) == (2, 4, 4)
    assert m.jaccard == pytest.approx(2 / 6)
    assert pair.matches[0].jaccard >= pair.matches[-1].jaccard  # ranked by Match Jaccard


def test_match_figures_on_the_whole_clusters_and_on_their_comparable_tags():
    A = part("overall", {"C1": [1, 2, 3, 4], "C2": [5, 6], "C3": [7]})
    B = part("puzzle", {"C1": [1, 2, 5, 9], "C2": [3, 10], "C3": [6], "C4": [7]})
    pair = CMP.compare_pair(A, B)
    # Comparable Tags {1, 2, 3, 5, 6, 7}: N = 6, One-Tag Clusters counted.
    assert pair.comparable == (1, 2, 3, 5, 6, 7) and pair.n_comparable == 6
    m = match(pair, "C1", "C1")
    assert (m.share_a, m.share_b) == (pytest.approx(0.5), pytest.approx(0.5))
    # a' = {1, 2, 3}, b' = {1, 2, 5}.
    assert (m.n_comparable_a, m.n_comparable_b) == (3, 3)
    assert (m.comparable_share_a, m.comparable_share_b) == (pytest.approx(2 / 3), pytest.approx(2 / 3))
    assert m.comparable_jaccard == pytest.approx(0.5)
    # E = 3 * 3 / 6 = 1.5; 2 shared Tags are 1.33x that.
    assert m.expected_overlap == pytest.approx(1.5)
    assert m.overlap_vs_expected == pytest.approx(2 / 1.5)


def test_comparable_figures_are_blank_below_two_comparable_tags_and_the_match_stays_ranked():
    A = part("overall", {"C1": [1, 20, 21], "C2": [2, 3]})
    B = part("puzzle", {"C1": [1, 2], "C2": [3, 4]})
    pair = CMP.compare_pair(A, B)
    m = match(pair, "C1", "C1")  # a' = {1}
    assert m.comparable_jaccard is None and m.comparable_share_a is None
    assert m.comparable_share_b == pytest.approx(0.5)
    assert m.jaccard == pytest.approx(1 / 4)
    assert len(pair.matches) == 3


def test_a_tag_hidden_in_only_one_dataset_is_set_aside_and_each_unshared_tag_gets_its_group():
    # Strategy hides its defining Tag 50; Overall shows it in its C1. Tag 7 is on one Strategy game (g = 2).
    A = part("overall", {"C1": [1, 2, 3, 5, 7, 50], "C2": [8, 9]}, games=[game(100, 1, 4, 8)], g=3)
    B = part("strategy", {"C1": [1, 2, 4], "C2": [5, 6], "C3": [3]}, hidden=[50],
             games=[game(100, 1, 7, 50), game(101, 2, 50)], g=2)
    pair = CMP.compare_pair(A, B)
    assert pair.set_aside_a == (50,) and pair.set_aside_b == ()
    m = match(pair, "C1", "C1")
    # 50 is in no figure: |a| = 5, n = 2.
    assert (m.n_tags_a, m.n_shared) == (5, 2)
    assert m.jaccard == pytest.approx(2 / 6)
    assert m.shared_tags == (1, 2)
    assert [(p.tag_id, p.group) for p in m.only_a] == [
        (5, "other_cluster"), (3, "one_tag"), (7, "not_in_network"), (50, "hidden")]  # by group, then id
    place = {p.tag_id: p for p in m.only_a}
    assert place[5].cluster == "C2"
    assert (place[7].n_games, place[7].minimum) == (1, 2)
    # Tag 4 of Strategy C1 is on one Overall game, below Overall's minimum of 3.
    assert [(p.tag_id, p.group, p.n_games, p.minimum) for p in m.only_b] == [(4, "not_in_network", 1, 3)]
    assert m.group_counts_a == {"other_cluster": 1, "one_tag": 1, "not_in_network": 1, "hidden": 1}


def test_each_multi_tag_cluster_gets_its_no_match_flag_in_both_directions():
    A = part("overall", {"C1": [1, 2, 5], "C2": [3, 4, 22], "C3": [20, 21], "C4": [24, 50], "C5": [3_0]})
    B = part("strategy", {"C1": [1, 9, 10, 11, 12], "C2": [3], "C3": [4]}, hidden=[50])
    pair = CMP.compare_pair(A, B)
    flags = {f.cluster: f for f in pair.flags_a}
    assert set(flags) == {"C1", "C2", "C3", "C4"}  # Multi-Tag Clusters only
    assert flags["C3"].flag == "outside_network"
    assert flags["C4"].flag == "outside_network"  # 50 set aside, 24 not in Strategy's network
    assert flags["C2"].flag == "only_one_tag_clusters"
    assert (flags["C2"].n_in_one_tag_clusters, flags["C2"].n_not_in_network) == (2, 1)
    # C1 ~ Strategy C1 shares one Tag: 1 / (3 + 5 - 1).
    assert (flags["C1"].flag, flags["C1"].n_matches) == ("", 1)
    assert flags["C1"].best_jaccard == pytest.approx(1 / 7)
    assert flags["C1"].flag_at(0.10) == "" and flags["C1"].flag_at(0.20) == "below_minimum"
    assert flags["C2"].flag_at(0.20) == "only_one_tag_clusters" and flags["C2"].best_jaccard is None
    assert [(f.cluster, f.flag) for f in pair.flags_b] == [("C1", "")]


def test_pair_overview_ari_on_comparable_tags_with_an_edge_shares_and_games_in_common():
    # Tag 5 is in both networks but has no edge in either: it is a Comparable Tag but not in the ARI.
    A = part("overall", {"C1": [1, 2], "C2": [3, 4], "C3": [5], "C4": [6]}, edged=[1, 2, 3, 4],
             games=[game(100, 1), game(101, 2), game(102, 3)])
    B = part("puzzle", {"C1": [1, 3], "C2": [2, 4], "C3": [5]}, edged=[1, 2, 3, 4],
             games=[game(101, 1), game(102, 2), game(103, 3)])
    pair = CMP.compare_pair(A, B)
    assert pair.n_comparable == 5
    assert (pair.comparable_share_a, pair.comparable_share_b) == (pytest.approx(5 / 6), pytest.approx(1.0))
    assert pair.ari == pytest.approx(-0.5)  # [a a b b] against [a b a b]
    assert pair.n_games_in_common == 2
    assert pair.n_matches == 4


def test_ari_is_blank_below_two_comparable_tags_with_an_edge():
    A = part("overall", {"C1": [1, 2]}, edged=[2])
    B = part("puzzle", {"C1": [1, 3]}, edged=[3])
    assert CMP.compare_pair(A, B).ari is None


def test_games_in_both_clusters_follow_the_cluster_inspector_rule_with_counts_and_sort():
    A = part("overall", {"C1": [1, 2, 3], "C2": [8, 9]},
             games=[game(100, 1, 1, 2), game(101, 2, 3), game(102, 3, 9), game(103, 4, 2), game(104, 5, 1),
                    game(106, 6)])
    B = part("rpg", {"C1": [1, 4, 5], "C2": [8, 9]},
             games=[game(101, 1, 4), game(100, 2, 1, 4, 5), game(102, 3, 5), game(103, 4, 9), game(105, 5, 1),
                    game(106, 6)])
    games = match(CMP.compare_pair(A, B), "C1", "C1").games
    # In both datasets: 100, 101, 102, 103, 106.
    assert (games.n_in_common, len(games.rows), games.n_only_a, games.n_only_b, games.n_neither) == (5, 2, 1, 1, 1)
    first, second = games.rows
    assert (first.appid, first.rank_a, first.rank_b) == (100, 1, 2)  # matched 2 + 3 before 1 + 1
    assert (first.matched_a, first.matched_b) == ((1, 2), (1, 4, 5))
    assert (first.tags, first.shared) == ((1, 2, 4, 5), (1,))
    assert second.appid == 101


def test_games_tie_on_matched_sum_then_rank_in_a_then_rank_in_b():
    A = part("overall", {"C1": [1, 2]}, games=[game(100, 2, 1), game(101, 1, 2)])
    B = part("rpg", {"C1": [1, 2]}, games=[game(100, 1, 1), game(101, 2, 2)])
    assert [r.appid for r in match(CMP.compare_pair(A, B), "C1", "C1").games.rows] == [101, 100]


def _rich_pair():
    A = part("overall", {"C1": [1, 2, 3, 5, 7, 50], "C2": [8, 9], "C3": [4, 10], "C4": [11]}, edged=[1, 2, 3, 8, 9],
             games=[game(100, 1, 1, 4, 8), game(101, 2, 2, 9), game(102, 3, 3)], g=3)
    B = part("strategy", {"C1": [1, 2, 4], "C2": [5, 6, 9], "C3": [3], "C4": [8, 10, 11]}, hidden=[50], edged=[1, 4, 6],
             games=[game(101, 1, 2, 6), game(100, 2, 7, 50, 1, 8), game(103, 3, 50)], g=2)
    return A, B


def test_swapping_a_and_b_gives_what_comparing_the_other_way_gives():
    A, B = _rich_pair()
    assert CMP.compare_pair(A, B).swapped() == CMP.compare_pair(B, A)


def test_compare_all_computes_each_unordered_pair_once_with_the_earlier_dataset_as_a():
    A, B = _rich_pair()
    C = part("rpg", {"C1": [1, 9], "C2": [2, 3]})
    pairs = CMP.compare_all([A, B, C])
    assert list(pairs) == [("overall", "strategy"), ("overall", "rpg"), ("strategy", "rpg")]
    assert pairs[("strategy", "rpg")] == CMP.compare_pair(B, C)


SHARED = CMP.SharedSettings(clustering_weight="lift", algorithm="leiden", min_months=0, genre_hidden=(7, 3),
                            removed_tag_ids=())
SEL_KEY = {"build_id": "b1", "grid": "lift-leiden"}


def _datasets(**overrides):
    on_cell = CMP.DatasetValues("overall", "pick", 17, 2, 1.15, selection_key=SEL_KEY)
    by_hand = CMP.DatasetValues("puzzle", "hand", 9, 7, 1.2, seed=0)
    values = {"overall": on_cell, "puzzle": by_hand}
    values.update(overrides)
    return list(values.values())


def test_the_comparison_key_names_the_build_shared_settings_and_each_dataset_by_its_source():
    key = CMP.comparison_key("b1", SHARED, _datasets())
    assert key == {
        "build_id": "b1",
        "shared": {"clustering_weight": "lift", "algorithm": "leiden", "min_months": 0, "genre_hidden": [3, 7],
                   "removed_tag_ids": []},
        "datasets": [
            {"dataset": "overall", "selection_key": SEL_KEY, "g": 17, "s": 2, "resolution": "1.15"},
            {"dataset": "puzzle", "g": 9, "s": 7, "resolution": "1.20", "seed": 0},
        ],
        "key_version": CMP.COMPARISON_KEY_VERSION,
    }
    cid = CMP.comparison_id(key)
    assert len(cid) == 12 and int(cid, 16) >= 0


def test_comparison_id_ignores_pick_versus_cell_and_hand_versus_no_run_but_not_values():
    base = CMP.comparison_id(CMP.comparison_key("b1", SHARED, _datasets()))
    same = [
        _datasets(overall=CMP.DatasetValues("overall", "cell", 17, 2, 1.15, selection_key=SEL_KEY)),
        _datasets(puzzle=CMP.DatasetValues("puzzle", "no_run", 9, 7, 1.2, seed=0)),
    ]
    for datasets in same:
        assert CMP.comparison_id(CMP.comparison_key("b1", SHARED, datasets)) == base
    different = [
        CMP.comparison_key("b2", SHARED, _datasets()),
        CMP.comparison_key("b1", CMP.SharedSettings("shared_games", "leiden", 0, (3, 7), ()), _datasets()),
        CMP.comparison_key("b1", CMP.SharedSettings("lift", "louvain", 0, (3, 7), ()), _datasets()),
        CMP.comparison_key("b1", CMP.SharedSettings("lift", "leiden", 6, (3, 7), ()), _datasets()),
        CMP.comparison_key("b1", CMP.SharedSettings("lift", "leiden", 0, (3,), ()), _datasets()),
        CMP.comparison_key("b1", CMP.SharedSettings("lift", "leiden", 0, (3, 7), (12,)), _datasets()),
        CMP.comparison_key("b1", SHARED, _datasets(puzzle=CMP.DatasetValues("puzzle", "hand", 10, 7, 1.2, seed=0))),
        CMP.comparison_key("b1", SHARED, _datasets(puzzle=CMP.DatasetValues("puzzle", "hand", 9, 6, 1.2, seed=0))),
        CMP.comparison_key("b1", SHARED, _datasets(puzzle=CMP.DatasetValues("puzzle", "hand", 9, 7, 1.3, seed=0))),
        CMP.comparison_key("b1", SHARED, _datasets(puzzle=CMP.DatasetValues("puzzle", "hand", 9, 7, 1.2, seed=1))),
        CMP.comparison_key("b1", SHARED, _datasets(overall=CMP.DatasetValues(
            "overall", "cell", 17, 2, 1.15, selection_key={**SEL_KEY, "grid": "other"}))),
        CMP.comparison_key("b1", SHARED, _datasets()[:1]),
    ]
    ids = [CMP.comparison_id(k) for k in different]
    assert base not in ids and len(set(ids)) == len(ids)


def test_an_empty_network_compares_without_matches_or_shares():
    A = part("overall", {})
    B = part("puzzle", {"C1": [1, 2]})
    pair = CMP.compare_pair(A, B)
    assert (pair.n_matches, pair.comparable_share_a, pair.comparable_share_b, pair.ari) == (0, None, 0.0, None)
    assert [(f.cluster, f.flag) for f in pair.flags_b] == [("C1", "outside_network")]


def test_a_pair_whose_multi_tag_clusters_share_no_tag_has_no_cluster_match():
    # Both networks have Multi-Tag Clusters, but A's Comparable Tags 1 and 3 are One-Tag Clusters in B.
    A = part("overall", {"C1": [1, 2], "C2": [3, 4]})
    B = part("rpg", {"C1": [5, 6], "C2": [1], "C3": [3]})
    none = CMP.compare_pair(A, B)
    assert none.matches == () and none.n_matches == 0
    assert [(f.cluster, f.flag, f.best_jaccard) for f in none.flags_a] == [
        ("C1", "only_one_tag_clusters", None), ("C2", "only_one_tag_clusters", None)]
