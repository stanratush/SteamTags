"""Feature-analysis tables on hand-built datasets (values worked out by hand)."""

from __future__ import annotations

import pytest

from steamstudy.analysis import features as F

P, A, B, C, D = 1664, 10, 20, 30, 40  # P = the defining tag (Puzzle)


def _rows(spec: list[tuple[tuple[int, ...], int]], genres=((1, "Action"),), flags=()) -> list[dict]:
    rows = []
    for tags, n in spec:
        for _ in range(n):
            i = len(rows)
            rows.append({"appid": 100 + i, "name": f"g{i}", "rank": i + 1, "tag_ids": list(tags),
                         "tags": [f"t{t}" for t in tags], "genre_ids": [g for g, _ in genres],
                         "genres": [n for _, n in genres], "content_flags": list(flags)})
    return rows


# 100 games, all with P. A on 60, B on 50, A&B on 40, C on 30 (C&A&B on 20), D on 100.
TOP = _rows([((P, A, B, C, D), 20), ((P, A, B, D), 20), ((P, A, D), 20), ((P, B, D), 10), ((P, C, D), 10),
             ((P, D), 20)])


def test_tag_frequency_against_the_eligible_pool():
    pool = TOP + _rows([((P, D), 100)])  # Eligible Pool: 200 games, A only in the Top 100
    rows = {r["tag_id"]: r for r in F.tag_frequency("puzzle", TOP, pool, P)}
    assert rows[P]["count"] == 100 and rows[P]["share"] == 1.0 and rows[P]["defining_tag"] is True
    assert rows[A]["count"] == 60 and rows[A]["baseline_count"] == 60 and rows[A]["baseline_share"] == 0.3
    assert rows[A]["share_ratio"] == pytest.approx(2.0)  # ceiling = 200 / 100
    assert rows[A]["median_position"] == 2.0
    order = [r["tag_id"] for r in F.tag_frequency("puzzle", TOP, pool, P)]
    assert order[:2] == [P, D]  # both on 100 games: ties by name ("t1664" < "t40")


def test_lift_at_k2_equals_the_pair_formula_and_a_hand_computed_k3_lift():
    rows = {tuple(r["tag_ids"]): r for r in F.combinations_table("puzzle", TOP, P, 3, 10)}
    ab = rows[(A, B)]
    assert ab["support_count"] == 40 and ab["lift"] == pytest.approx(40 * 100 / (60 * 50))
    assert ab["confidence_a_to_b"] == pytest.approx(40 / 60) and ab["confidence_b_to_a"] == pytest.approx(40 / 50)
    assert P not in {t for key in rows for t in key}
    # k = 3: A 60, B 50, C 40; pairs AB 40, AC 30, BC 30; ABC 20 (below every pair, so it is kept); N = 100.
    top3 = _rows([((A, B, C), 20), ((A, B), 20), ((A, C), 10), ((B, C), 10), ((A,), 10), ((D,), 30)])
    abc = {tuple(r["tag_ids"]): r for r in F.combinations_table("x", top3, None, 3, 10)}[(A, B, C)]
    assert abc["support_count"] == 20 and abc["lift"] == pytest.approx(20 * 100 ** 2 / (60 * 50 * 40))
    assert abc["confidence_a_to_b"] is None


def test_triple_dropped_when_support_equals_a_sub_pair():
    # A&C occur only together with B, so {A,B,C} has the same support as {A,C}: dropped. Its pairs stay.
    rows = {tuple(r["tag_ids"]): r for r in F.combinations_table("x", TOP, P, 3, 10)}
    assert (A, C) in rows and rows[(A, C)]["support_count"] == 20
    assert (A, B, C) not in rows
    top = _rows([((A, B, C), 15), ((A, B), 10), ((B, C), 5)])
    pruned = {tuple(r["tag_ids"]) for r in F.combinations_table("x", top, None, 3, 10)}
    assert (A, B, C) not in pruned and {(A, B), (A, C), (B, C)} <= pruned


def test_associations_phi_is_empty_at_count_100_and_bh_stays_within_the_dataset():
    rows = {(r["tag_id_a"], r["tag_id_b"]): r for r in F.associations_table("puzzle", TOP, P, 10)}
    ad = rows[(A, D)]  # D is on all 100 games
    assert ad["phi"] is None and ad["lift"] == 1.0 and ad["fisher_p"] == 1.0
    assert ad["jaccard"] == pytest.approx(60 / 100)
    assert all(P not in key for key in rows)
    ab = rows[(A, B)]
    # 2x2: n11 40, n10 20, n01 10, n00 30 -> phi = (40*30 - 20*10) / sqrt(60*40*50*50)
    assert ab["phi"] == pytest.approx((40 * 30 - 20 * 10) / (60 * 40 * 50 * 50) ** 0.5)
    ps = [r["fisher_p"] for r in rows.values()]
    assert [r["bh_q"] for r in rows.values()] == pytest.approx(F.benjamini_hochberg(ps))
    phis = [r["phi"] for r in F.associations_table("puzzle", TOP, P, 10)]
    known = [abs(p) for p in phis if p is not None]
    assert known == sorted(known, reverse=True) and phis[-1] is None


def test_benjamini_hochberg_by_hand():
    # sorted p 0.01, 0.03, 0.04, 0.5 -> p*m/rank 0.04, 0.06, 0.0533, 0.5 -> running minimum from the top
    assert F.benjamini_hochberg([0.01, 0.04, 0.03, 0.5]) == pytest.approx([0.04, 0.16 / 3, 0.16 / 3, 0.5])


def test_zero_co_occurrence_pairs_are_kept():
    top = _rows([((A,), 15), ((B,), 15), ((C,), 70)])
    rows = {(r["tag_id_a"], r["tag_id_b"]): r for r in F.associations_table("x", top, None, 10)}
    assert rows[(A, B)]["count_ab"] == 0 and rows[(A, B)]["jaccard"] == 0.0


def test_genre_frequency_keeps_every_value_with_its_kind():
    top = _rows([((A,), 3)], genres=((23, "Indie"), (999, "New Genre")))
    rows = {r["genre_id"]: r for r in F.genre_frequency("x", top, top, {23: "business"})}
    assert rows[23]["kind"] == "business" and rows[999]["kind"] == "unmapped" and rows[999]["count"] == 3


def test_content_flags_long_form_with_zero_counts():
    top = _rows([((A,), 2)], flags=("desktop_companion",))
    rows, counts = F.content_flag_rows("x", top, ["desktop_companion", "sexual_content_tag"])
    assert len(rows) == 2 and counts == {"desktop_companion": 2, "sexual_content_tag": 0}


def test_archived_category():
    assert F.archived_categories()["Farming Sim"] == ["Genres"]
    assert "Features" in F.archived_categories()["Base Building"]
