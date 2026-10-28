"""`steamstudy.network.validation`: the Null Comparison and Subsample Stability (issue 23)."""

from __future__ import annotations

from collections import Counter

import pytest

from steamstudy.i18n import text
from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL
from steamstudy.network import selection_text as T
from steamstudy.network import validation as V
from steamstudy.network.graph import filter_games

EN = text("en")


@pytest.fixture(scope="module")
def ctx(tagged_build):
    return load_build(tagged_build)


@pytest.fixture(scope="module")
def settings(ctx):
    base = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    return base.with_(g_range=(15, 15), s_range=(3, 3), replicates=4, subsamples=4)


@pytest.fixture(scope="module")
def observed(ctx, settings):
    run = SEL.run_grid(ctx.games("overall"), settings, "overall", ctx.context("overall"))
    (result,) = run.results.values()
    assert result.selected is not None
    return result


@pytest.fixture(scope="module")
def tasks(ctx, settings, observed):
    return V.validation_tasks(ctx.games("overall"), settings, "overall", ctx.context("overall"), 15, 3, observed,
                              SEL.selection_seeds(settings))


def test_tasks_use_streams_four_and_five(settings, tasks):
    _, null, sub = SEL.selection_seeds(settings)
    assert [t.seed for t in tasks if t.kind == "null"] == null
    assert [t.seed for t in tasks if t.kind == "subsample"] == sub
    assert len({t.weight for t in tasks}) == 1


def test_the_curveball_null_keeps_every_tag_and_game_count(ctx, observed):
    games = filter_games(ctx.games("overall"), 0)
    shuffled = V.shuffled_games(games, observed.nodes, 99)
    nodes = set(observed.nodes)
    before = [frozenset(t for t in g.tag_ids if t in nodes) for g in games]
    after = [frozenset(g.tag_ids) for g in shuffled]
    assert [len(r) for r in before] == [len(r) for r in after]
    assert Counter(t for r in before for t in r) == Counter(t for r in after for t in r)
    assert before != after


@pytest.mark.parametrize("g", [3, 7, 14, 20])
def test_subsample_thresholds_scale_with_floor(g):
    m, g2, s2 = V.subsample_thresholds(g, 2, 100)
    assert (m, g2, s2) == (80, 4 * g // 5, 2)
    assert V.subsample_thresholds(g, 12, 101)[2] == (12 * 80) // 101
    assert V.subsample_thresholds(3, 3, 7)[1:] == (2, 2)  # m = 5: 3·5//7 = 2, and s′ never below 2


def _observed(clusters, nodes, selected, edged=None):
    return V.Observed(nodes, edged or nodes, selected, 1.0, 0.3, 0.5, len(clusters), 10, 20, clusters,
                      [f"C{i}" for i in range(1, len(clusters) + 1)])


def test_hennig_jaccard_on_the_comparison_set():
    # Observed: C1 = {1, 2, 3}, C2 = {4, 5}, C3 = {6, 7}, and the One-Tag Cluster {8} (never scored).
    obs = _observed([[1, 2, 3], [4, 5], [6, 7]], [1, 2, 3, 4, 5, 6, 7, 8], [0, 0, 0, 1, 1, 2, 2, 3])
    # The subsample lacks 6 and 7 (C3 absent) and splits 3 off as a One-Tag Cluster, which still counts as a match.
    got = V.compare(obs, [1, 2, 3, 4, 5, 8], [1, 2, 3, 4, 5, 8], [0, 0, 1, 2, 2, 3])
    assert got["jaccard"] == [pytest.approx(2 / 3), 1.0, None]
    assert got["retention"] == [1.0, 1.0, 0.0]
    summary = V._arm_summary(obs, [{"arms": {"x": {"degenerate": None, **got}}}], "x")
    c3 = summary["clusters"][2]
    assert (c3["mean_jaccard"], c3["absent"], c3["present"], c3["dissolved"]) == (None, 1, 0, False)
    assert [c["label"] for c in summary["clusters"]] == ["C1", "C2", "C3"]


def test_degenerate_subsamples_are_counted_never_scored_zero():
    obs = _observed([[1, 2]], [1, 2, 3], [0, 0, 1])
    good = {"degenerate": None, "ari": 0.4, "jaccard": [0.4], "retention": [1.0], "edged_share": 1.0,
            "resolution": 1.0, "n_multi": 1}
    bad = {"degenerate": "no_stable_partition", "ari": None, "jaccard": [None], "retention": [None],
           "edged_share": None, "resolution": None, "n_multi": None}
    records = [{"kind": "subsample", "index": i, "seed": i, "m": 8, "g": 2, "s": 2, "n_edges": 1, "scan_length": 1,
                "capped_runs": 0, "arms": {"reselected": arm, "at_resolution": good}}
               for i, arm in enumerate([good, bad, bad], start=1)]
    summary = V.summarise(obs, records)
    re_ = summary["subsample"]["reselected"]
    assert (re_["degenerate"], re_["reasons"], re_["ari"]["median"]) == (2, {"no_stable_partition": 2}, 0.4)
    assert re_["clusters"][0]["mean_jaccard"] == 0.4 and re_["clusters"][0]["dissolved"]
    assert summary["verdicts"]["dissolved"] == {"reselected": ["C1"], "at_resolution": ["C1"]}


def test_the_fixed_gamma_q_is_read_from_the_envelope(observed):
    from steamstudy.network import champ as C

    result = C.from_json(observed.champ)
    for gamma in (0.3, observed.selected_resolution, result.gamma_end, result.gamma_end + 1):
        top = V.envelope_partition(result, gamma)
        assert top.a_hat - gamma * top.p_hat == max(p.a_hat - gamma * p.p_hat for p in result.admissible)
        if gamma <= result.gamma_end:
            assert result.q_at(gamma) == pytest.approx((top.a_hat - gamma * top.p_hat) / result.two_m)
    obs = V.Observed.of(observed)
    assert obs.q == pytest.approx(observed.modularity, abs=1e-12)


def test_serial_and_a_pool_of_two_give_identical_summaries(tasks, observed):
    import multiprocess as mp

    serial = V.run_validation(tasks)
    with mp.Pool(2) as pool:
        parallel = V.run_validation(tasks, map_fn=pool.imap_unordered)
    assert serial == parallel and len(serial) == 8
    assert [(r["kind"], r["index"]) for r in serial] == [("null", i) for i in range(1, 5)] + [
        ("subsample", i) for i in range(1, 5)]
    assert V.summary_from_records(observed, serial) == V.summary_from_records(observed, parallel)


def test_a_stopped_validation_returns_nothing(tasks):
    seen = []
    assert V.run_validation(tasks, on_result=lambda r, w: seen.append(r), should_stop=lambda: len(seen) >= 2) is None


# ----------------------------------------------------------------------------- the validation block


def _summary(reach=0, dissolved=False, degenerate=1):
    cluster = {"label": "C2", "members": [1, 2, 3, 4], "mean_jaccard": 0.4 if dissolved else 0.8, "at_most_half": 3,
               "present": 99, "mean_retention": 1.0, "absent": 0, "dissolved": dissolved}
    others = [dict(cluster, label=f"C{i}", dissolved=False, mean_jaccard=0.9) for i in (1, 3, 4)]
    arm = lambda ari, clusters, deg: {  # noqa: E731
        "n": 100, "degenerate": deg, "reasons": {"no_stable_partition": deg} if deg else {},
        "ari": {"median": ari, "p10": ari - 0.12, "p90": min(1.0, ari + 0.17), "min": 0.2}, "clusters": clusters,
        "edged_share_mean": 1.0}
    return {
        "resolution": 1.151,
        "null": {"replicates": 100, "selected": 79, "reasons": {},
                 "width": {"observed": 0.158, "median": 0.03, "min": 0.01, "max": 0.1, "narrower": 79},
                 "q": {"observed": 0.067, "median": -0.015, "min": -0.021, "max": -0.012, "reach": reach}},
        "subsample": {"subsamples": 100, "m": 80, "g": 13, "s": 2,
                      "reselected": arm(0.69, [others[0], cluster, *others[1:]], degenerate),
                      "at_resolution": arm(0.86, [others[0], dict(cluster, dissolved=False), *others[1:]], 0)},
    }


def test_validation_block_golden_text():
    names = {1: "Strategy", 2: "Tactical", 3: "Turn-Based", 4: "Wargame"}
    text = T.to_markdown(T.validation_block(_summary(dissolved=True), (17, 2), (17, 2), True, names, tx=EN))
    assert text == (
        "**Validation of g = 17, s = 2**\n\n"
        "**Null Comparison** (100 shuffled networks, same g and s). Q at resolution 1.151 is 0.067; no shuffled "
        "network reaches it (−0.021 to −0.012). 79 of 100 also have a Selected Partition, with narrower domains "
        "(median 0.03 against 0.158; wider than all 79).\n\n"
        "*This shows only that the network is not random, not that its Clusters are real.*\n\n"
        "**Subsample Stability** (100 random 80% subsets of the games, g′ = 13, s′ = 2). Re-selected: median ARI "
        "0.69 (0.57–0.86) over 99 of 100 subsamples; 1 had no Selected Partition. At resolution 1.151: median ARI "
        "0.86 (0.74–1.00). 1 of 4 Multi-Tag Clusters is dissolved when re-selected (mean Jaccard ≤ 0.5): "
        "*C2 (Strategy, Tactical, Turn-Based, …)*.\n\n"
        "*This measures how much the clustering depends on which games are in the dataset. It does not show that "
        "the Clusters are real either.*")


def test_validation_block_variants():
    reached = T.to_markdown(T.validation_block(_summary(reach=3), (17, 2), (17, 2), True, tx=EN))
    assert "Q at resolution 1.151 is 0.067; 3 of 100 shuffled networks reach it: Q not above the null." in reached
    assert "No Multi-Tag Cluster is dissolved (mean Jaccard ≤ 0.5) in either arm." in reached
    assert T.to_markdown(T.validation_block(None, (14, 2), (14, 2), True, tx=EN)) == (
        "**Validation of g = 14, s = 2**\n\nNot validated.")
    custom = T.to_markdown(T.validation_block(_summary(), (17, 2), (15, 3), False, tx=EN))
    assert custom.split("\n\n")[1] == "Validation ran for g = 17, s = 2, the pair chosen under the default constraints."
