"""`steamstudy.network.validation`: the Null Comparison and Subsample Stability (issue 23)."""

from __future__ import annotations

import statistics
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
    assert (c3["mean_jaccard"], c3["absent"], c3["assessable_subsamples"]) == (None, 1, 0)
    assert (c3["assessable"], c3["dissolved_in_most"], c3["borderline"]) == (False, False, False)  # Not assessable
    assert [c["label"] for c in summary["clusters"]] == ["C1", "C2", "C3"]


def test_the_whole_cluster_jaccard_counts_lost_tags():
    # C1 = {1, 2, 3} keeps only tag 1 (one tag left), C2 = {4, 5} loses both, C3 = {6, 7} survives whole.
    obs = _observed([[1, 2, 3], [4, 5], [6, 7]], [1, 2, 3, 4, 5, 6, 7], [0, 0, 0, 1, 1, 2, 2])
    got = V.compare(obs, [1, 6, 7, 8], [1, 6, 7, 8], [0, 1, 1, 0])
    assert got["survivors"] == [1, 0, 2]
    assert got["jaccard"] == [None, None, 1.0]  # Hennig's Jaccard needs two surviving tags
    # On the comparison set (tag 8 is not in the observed network): C1 against {1} is |{1}| / |{1, 2, 3}|; C2 matches
    # nothing; C3 is {6, 7} exactly.
    assert got["whole_jaccard"] == [pytest.approx(1 / 3), 0.0, 1.0]
    none = V.compare(obs, [1], [1], None)
    assert none["whole_jaccard"] == [None] * 3 and none["survivors"] == [None] * 3


def test_degenerate_subsamples_are_counted_never_scored_zero():
    obs = _observed([[1, 2]], [1, 2, 3], [0, 0, 1])
    good = {"degenerate": None, "ari": 0.4, "jaccard": [0.4], "whole_jaccard": [0.4], "survivors": [2],
            "retention": [1.0], "edged_share": 1.0, "resolution": 1.0, "n_multi": 1}
    bad = {"degenerate": "no_stable_partition", "ari": None, "jaccard": [None], "whole_jaccard": [None],
           "survivors": [None], "retention": [None], "edged_share": None, "resolution": None, "n_multi": None}
    records = [{"kind": "subsample", "index": i, "seed": i, "m": 8, "g": 2, "s": 2, "n_edges": 1, "scan_length": 1,
                "capped_runs": 0, "arms": {"reselected": arm, "at_resolution": good}}
               for i, arm in enumerate([good, bad, bad], start=1)]
    summary = V.summarise(obs, records)
    re_ = summary["subsample"]["reselected"]
    assert (re_["degenerate"], re_["reasons"], re_["ari"]["median"]) == (2, {"no_stable_partition": 2}, 0.4)
    assert re_["clusters"][0]["mean_jaccard"] == 0.4 and re_["clusters"][0]["dissolved_in_most"]
    assert summary["verdicts"]["dissolved_in_most"] == {"reselected": ["C1"], "at_resolution": ["C1"]}


# ----------------------------------------------------------------------------- summarise on synthetic records


def _null(i, q=None, q_reason=None, width=None, n_multi=None):
    return {"kind": "null", "index": i, "seed": i, "n_edges": 0 if q_reason == "no_edges" else 5, "scan_length": 1,
            "capped_runs": 0, "reason": "no_edges" if q_reason == "no_edges" else (
                None if width is not None else "no_stable_partition"), "selected": width is not None,
            "width": width, "resolution": None if width is None else 1.0, "n_multi": n_multi, "q_envelope": q,
            "q_fixed": q, "q_reason": q_reason, "perturbation_share": 0.6}


def _arm(jaccard, survivors, whole, degenerate=None):
    return {"degenerate": degenerate, "ari": None if degenerate else 0.5, "jaccard": jaccard, "whole_jaccard": whole,
            "survivors": survivors, "retention": [None if s is None else s / 4 for s in survivors],
            "edged_share": None if degenerate else 1.0, "resolution": None if degenerate else 1.0,
            "n_multi": None if degenerate else 2}


def _sub(i, jaccard, survivors=None, whole=None, degenerate=None):
    survivors = survivors or [None if j is None else 4 for j in jaccard]
    whole = whole or [j if j is not None else 0.0 for j in jaccard]
    arm = _arm(jaccard, survivors, whole, degenerate)
    return {"kind": "subsample", "index": i, "seed": i, "m": 8, "g": 2, "s": 2, "n_edges": 5, "scan_length": 1,
            "capped_runs": 0, "arms": {"reselected": arm, "at_resolution": arm}}


def _one_cluster():
    return _observed([[1, 2, 3, 4]], [1, 2, 3, 4, 5], [0, 0, 0, 0, 1])  # q 0.3, width 0.5, 1 Multi-Tag Cluster


def _cluster(records, arm="reselected"):
    return V.summarise(_one_cluster(), records)["subsample"][arm]["clusters"][0]


def test_zero_defined_null_q_is_undefined_not_an_error():
    summary = V.summarise(_one_cluster(), [_null(i, q_reason="no_edges") for i in range(1, 5)])
    null = summary["null"]
    assert summary["verdicts"]["null_q"] == "undefined"
    assert (null["q_defined"], null["q_undefined"], null["q_undefined_reasons"]) == (0, 4, {"no_edges": 4})
    assert null["q"]["reach"] == 0 and null["q"]["median"] is None and null["weak"]


def test_partly_defined_null_q_counts_over_the_defined_ones():
    nulls = ([_null(i, q=0.1) for i in range(1, 4)] + [_null(4, q=0.35)]
             + [_null(i, q_reason="no_edges") for i in range(5, 9)] + [_null(9, q_reason="beyond_scan")])
    null = V.summarise(_one_cluster(), nulls)["null"]
    assert (null["replicates"], null["q_defined"], null["q_undefined"]) == (9, 4, 5)
    assert null["q_undefined_reasons"] == {"beyond_scan": 1, "no_edges": 4}
    assert null["q"]["reach"] == 1 and null["weak"]  # D = 4 < R/2 = 4.5
    summary = V.summarise(_one_cluster(), nulls)
    assert summary["verdicts"]["null_q"] == "reached"
    above = V.summarise(_one_cluster(), [_null(i, q=0.1) for i in range(1, 4)] + [_null(4, q_reason="no_edges")])
    assert above["verdicts"]["null_q"] == "above_all_defined" and not above["null"]["weak"]  # D = 3 ≥ R/2 = 2


def test_the_observed_runs_beating_the_selected_q_are_what_the_nulls_are_compared_with():
    nulls = [_null(1, q=0.305), _null(2, q=0.1)]
    plain = V.summarise(_one_cluster(), nulls)
    assert (plain["null"]["q"]["observed"], plain["null"]["q"]["observed_from_runs"], plain["null"]["q"]["reach"]) == (
        0.3, False, 1)
    runs = V.summarise(_one_cluster(), nulls, {"q_selected": 0.3, "q_runs": 0.31})
    q = runs["null"]["q"]
    assert (q["observed_selected"], q["observed"], q["observed_from_runs"], q["reach"]) == (0.3, 0.31, True, 0)
    same = V.summarise(_one_cluster(), nulls, {"q_selected": 0.3, "q_runs": 0.3})["null"]["q"]
    assert (same["observed"], same["observed_from_runs"]) == (0.3, False)


def test_width_ties_are_counted_apart_and_multi_tag_clusters_spread_over_the_same_nulls():
    nulls = [_null(1, q=0.1, width=0.2, n_multi=3), _null(2, q=0.1, width=0.5, n_multi=5),
             _null(3, q=0.1, width=0.7, n_multi=4), _null(4, q=0.1)]
    null = V.summarise(_one_cluster(), nulls)["null"]
    assert (null["selected"], null["width"]["wider"], null["width"]["equal"]) == (3, 1, 1)
    assert null["width"]["median"] == 0.5 and "narrower" not in null["width"]
    assert null["n_multi"] == {"observed": 1, "median": 4, "min": 3, "max": 5}


def test_a_wholly_absent_cluster_is_not_assessable():
    c = _cluster([_sub(i, [None], survivors=[0], whole=[0.0]) for i in range(1, 5)])
    assert (c["assessable_subsamples"], c["absent"], c["assessable"]) == (0, 4, False)
    assert (c["dissolved_in_most"], c["borderline"], c["mean_jaccard"], c["dissolution_frequency"]) == (
        False, False, None, None)
    assert c["mean_whole_cluster_jaccard"] == 0.0
    summary = V.summarise(_one_cluster(), [_sub(i, [None], survivors=[0], whole=[0.0]) for i in range(1, 5)])
    assert summary["verdicts"]["not_assessable"]["reselected"] == ["C1"]


def test_single_tag_survival_is_unscored_by_hennig_and_scored_by_the_whole_cluster_jaccard():
    records = [_sub(1, [0.8], survivors=[4], whole=[0.8]), _sub(2, [None], survivors=[1], whole=[0.25]),
               _sub(3, [None], survivors=[1], whole=[0.25])]
    c = _cluster(records)
    assert (c["assessable_subsamples"], c["one_tag_left"], c["absent"]) == (1, 2, 0)
    assert c["mean_jaccard"] == 0.8 and c["mean_jaccard_se"] is None  # B* < 2
    assert c["mean_whole_cluster_jaccard"] == pytest.approx(1.3 / 3)
    assert c["whole_cluster_jaccard_se"] == pytest.approx(statistics.stdev([0.8, 0.25, 0.25]) / 3 ** 0.5)
    assert c["rarely_assessable"]  # B* = 1 < S/2 = 1.5


def test_a_low_b_star_cluster_is_rarely_assessable():
    records = [_sub(1, [0.9]), _sub(2, [0.9])] + [_sub(i, [None], survivors=[0], whole=[0.0]) for i in range(3, 7)]
    c = _cluster(records)
    assert (c["assessable_subsamples"], c["rarely_assessable"], c["assessable"]) == (2, True, True)
    enough = _cluster([_sub(1, [0.9]), _sub(2, [0.9]), _sub(3, [None], survivors=[0], whole=[0.0])])
    assert not enough["rarely_assessable"]


def test_exactly_half_dissolved_is_not_labelled():
    c = _cluster([_sub(1, [0.4]), _sub(2, [0.5]), _sub(3, [0.8]), _sub(4, [0.9])])
    assert (c["at_most_half"], c["assessable_subsamples"], c["dissolution_frequency"]) == (2, 4, 0.5)
    assert not c["dissolved_in_most"] and c["borderline"]
    more = _cluster([_sub(1, [0.4]), _sub(2, [0.5]), _sub(3, [0.3]), _sub(4, [0.9])])
    assert more["dissolved_in_most"]


def test_borderline_is_a_wilson_interval_containing_a_half():
    # 6 of 10: the Wilson interval is 31–83%, so the label holds but the Cluster is borderline.
    six = _cluster([_sub(i, [0.3 if i <= 6 else 0.9]) for i in range(1, 11)])
    assert six["dissolved_in_most"] and six["borderline"]
    assert (six["wilson_low"], six["wilson_high"]) == (pytest.approx(0.3127, abs=1e-4), pytest.approx(0.8318, abs=1e-4))
    # 19 of 20: 76–99%, labelled and not borderline.
    many = _cluster([_sub(i, [0.3 if i <= 19 else 0.9]) for i in range(1, 21)])
    assert many["dissolved_in_most"] and not many["borderline"]
    assert many["wilson_low"] > 0.5


def test_hennig_figures_recovery_and_spreads():
    values = [0.2, 0.4, 0.6, 0.8, 0.9, 1.0]
    c = _cluster([_sub(i, [v]) for i, v in enumerate(values, start=1)])
    assert c["size"] == 4
    assert c["mean_jaccard"] == pytest.approx(statistics.fmean(values))
    assert c["mean_jaccard_se"] == pytest.approx(statistics.stdev(values) / 6 ** 0.5)
    assert (c["jaccard_p10"], c["jaccard_p90"]) == (pytest.approx(0.3), pytest.approx(0.95))
    assert (c["at_most_half"], c["recovered"], c["recovery_frequency"]) == (2, 3, 0.5)
    assert c["recovery_wilson_low"] < 0.5 < c["recovery_wilson_high"]
    assert (c["whole_cluster_p10"], c["whole_cluster_p90"]) == (pytest.approx(0.3), pytest.approx(0.95))


def test_the_envelope_is_read_inside_the_scan_and_never_extrapolated(observed):
    from steamstudy.network import champ as C

    result = C.from_json(observed.champ)
    for gamma in (0.3, observed.selected_resolution, result.gamma_end):
        top = V.envelope_partition(result, gamma)
        assert top.a_hat - gamma * top.p_hat == max(p.a_hat - gamma * p.p_hat for p in result.admissible)
        assert result.q_at(gamma) == pytest.approx((top.a_hat - gamma * top.p_hat) / result.two_m)
    assert V.envelope_partition(result, result.gamma_end + 1) is None
    beyond = V.at_gamma(result, result.gamma_end + 1, None)
    assert (beyond.membership, beyond.q_envelope, beyond.q, beyond.reason) == (None, None, None, "beyond_scan")
    obs = V.Observed.of(observed)
    assert obs.q == pytest.approx(observed.modularity, abs=1e-12)


def test_the_fixed_gamma_q_is_the_best_of_the_envelope_and_the_runs(observed):
    from steamstudy.network import champ as C

    result = C.from_json(observed.champ)
    gamma = observed.selected_resolution
    top = V.envelope_partition(result, gamma)
    q_env = (top.a_hat - gamma * top.p_hat) / result.two_m
    lower = V.at_gamma(result, gamma, (tuple(range(len(top.membership))), q_env - 0.01))
    assert (lower.q_envelope, lower.q, lower.changed, lower.membership) == (q_env, q_env, False, top.membership)
    higher = V.at_gamma(result, gamma, ((0,) * len(top.membership), q_env + 0.01))
    assert (higher.q_envelope, higher.q, higher.changed) == (q_env, q_env + 0.01, True)
    assert higher.membership == (0,) * len(top.membership)


def test_the_runs_at_the_observed_resolution_use_one_gamma_and_the_scan_seeds_and_never_select(tasks, monkeypatch):
    calls = []
    real = V.runs_at

    def spy(graph, arrays, gamma, seeds):
        calls.append((gamma, tuple(seeds)))
        return real(graph, arrays, gamma, seeds)

    null, sub = next(t for t in tasks if t.kind == "null"), next(t for t in tasks if t.kind == "subsample")
    plain = [V.run_replicate(null), V.run_replicate(sub)]
    monkeypatch.setattr(V, "runs_at", spy)
    observed = V.observed_runs(null)
    assert [V.run_replicate(null), V.run_replicate(sub)] == plain
    assert observed["q_selected"] == null.observed.q and observed["q_runs"] is not None
    assert len(calls) == 3 and set(calls) == {(null.observed.resolution, null.scan_seeds)}

    # A run that beats every scan partition moves only the fixed-γ figures, never a Selected Partition.
    monkeypatch.setattr(V, "runs_at", lambda graph, arrays, gamma, seeds: ((0,) * graph.number_of_nodes(), 99.0))
    boosted_null, boosted_sub = V.run_replicate(null), V.run_replicate(sub)
    keep = ("selected", "width", "resolution", "n_multi", "q_envelope", "n_edges", "scan_length")
    assert {k: boosted_null[k] for k in keep} == {k: plain[0][k] for k in keep} and boosted_null["q_fixed"] == 99.0
    assert boosted_sub["arms"]["reselected"] == plain[1]["arms"]["reselected"]
    assert boosted_sub["arms"]["at_resolution"]["at_resolution_changed"] is True


def test_the_perturbation_share_counts_the_lost_ones(ctx, observed):
    games = filter_games(ctx.games("overall"), 0)
    assert V.perturbation_share(games, games, observed.nodes) == 0
    share = V.perturbation_share(games, V.shuffled_games(games, observed.nodes, 99), observed.nodes)
    assert 0 < share <= 1


def test_serial_and_a_pool_of_two_give_identical_summaries(tasks, observed):
    import multiprocess as mp

    serial = V.run_validation(tasks)
    with mp.Pool(2) as pool:
        parallel = V.run_validation(tasks, map_fn=pool.imap_unordered)
    assert serial == parallel and len(serial) == 8
    assert [(r["kind"], r["index"]) for r in serial] == [("null", i) for i in range(1, 5)] + [
        ("subsample", i) for i in range(1, 5)]
    assert V.summary_from_records(observed, {"records": serial}) == V.summary_from_records(
        observed, {"records": parallel})


def test_a_stopped_validation_returns_nothing(tasks):
    seen = []
    assert V.run_validation(tasks, on_result=lambda r, w: seen.append(r), should_stop=lambda: len(seen) >= 2) is None


# ----------------------------------------------------------------------------- the validation block


def _clusters(dissolved=(), borderline=(), unassessable=()):
    return [{"label": f"C{i}", "members": [4 * i - 3 + j for j in range(4)],
             "dissolved_in_most": f"C{i}" in dissolved, "borderline": f"C{i}" in borderline,
             "assessable": f"C{i}" not in unassessable} for i in range(1, 5)]


def _summary(reach=0, d=100, reasons=None, from_runs=False, equal=0, k=79, re_clusters=None, at_clusters=None,
             degenerate=1):
    """A hand-built summary in `validation.summarise`'s shape, with only what the sentences read: the stored Overall
    17/2 run's figures by default."""
    reasons = reasons or ({} if d == 100 else {"no_edges": 100 - d})
    arm = lambda median, p10, p90, deg, clusters: {  # noqa: E731
        "n": 100, "degenerate": deg, "reasons": {"no_stable_partition": deg} if deg else {},
        "ari": {"median": median, "p10": p10, "p90": p90, "min": 0.2}, "edged_share_mean": 0.993,
        "clusters": clusters}
    return {
        "resolution": 1.151,
        "null": {"replicates": 100, "selected": k, "q_defined": d, "q_undefined": 100 - d,
                 "q_undefined_reasons": reasons, "weak": 2 * d < 100,
                 "width": {"observed": 0.158, "median": 0.049, "min": 0.01, "max": 0.1, "wider": k - equal,
                           "equal": equal},
                 "n_multi": {"observed": 4, "median": 5, "min": 3, "max": 9},
                 "q": {"observed": 0.0687 if from_runs else 0.0667, "observed_selected": 0.0667,
                       "observed_from_runs": from_runs, "median": -0.015, "min": -0.021, "max": -0.012,
                       "reach": reach}},
        "subsample": {"subsamples": 100, "m": 80, "g": 13, "s": 2,
                      "reselected": arm(0.69, 0.57, 0.86, degenerate,
                                        re_clusters if re_clusters is not None else _clusters(("C2",))),
                      "at_resolution": arm(0.86, -0.05, 1.0, 0,
                                           at_clusters if at_clusters is not None else _clusters())},
    }


NAMES = {1: "Strategy", 2: "Tactical", 3: "Turn-Based", 4: "Wargame"}


def _block(summary, tx=EN, pair=(17, 2), chosen=(17, 2), ran=True):
    return T.to_markdown(T.validation_block(summary, pair, chosen, ran, NAMES, tx=tx))


def test_validation_block_golden_text():
    assert _block(_summary()) == (
        "**Validation of g = 17, s = 2**\n\n"
        "**Null Comparison** (100 shuffled networks, per-pair procedure at g = 17, s = 2)\n\n"
        "Q at resolution 1.151 is 0.067; none of the 100 shuffled networks with a Q reaches it (range over 100 "
        "shuffled networks: −0.021 to −0.012).\n\n"
        "Multi-Tag Clusters: observed 4, median 5 (range over 79 shuffled networks with a Selected Partition: 3 to "
        "9). Median domain width 0.049 vs observed 0.158; observed wider than 79 of 79. Widths are upper bounds, "
        "conditional on the partitions the γ scan finds.\n\n"
        "*This shows only that the network is not random, not that its Clusters are real.*\n\n"
        "**Subsample Stability** (100 random 80% subsets of the games, g′ = 13, s′ = 2).\n\n"
        "Re-selected: median ARI 0.69 (10th–90th percentile: 0.57 to 0.86) over 99 of 100 subsamples, on 99% of the "
        "tags; 1 had no Selected Partition. At resolution 1.151: median ARI 0.86 (10th–90th percentile: −0.05 to "
        "1.00).\n\n"
        "**Dissolved in most subsamples** (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this study's "
        "rule): re-selected only: *C2 (5, 6, 7, …)*.\n\n"
        "*This measures how much the clustering depends on which games are in the dataset. It does not show that "
        "the Clusters are real either.*\n\n"
        "*The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no part "
        "in the choice, so the Null Comparison is barely affected.*")


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({"reach": 3}, "Q at resolution 1.151 is 0.067; 3 of 100 shuffled networks with a Q reach it: Q not above the "
                   "null."),
    ({"d": 0, "reasons": {"no_edges": 100}, "k": 0},
     "Q at resolution 1.151 is 0.067; no shuffled network has edges, so Q cannot be compared."),
    ({"d": 0, "reasons": {"beyond_scan": 8, "no_edges": 92}, "k": 0},
     "Q at resolution 1.151 is 0.067; no shuffled network has a Q (8 lay beyond their γ scan; 92 had no edges), so Q "
     "cannot be compared."),
    ({"d": 40, "reasons": {"beyond_scan": 8, "no_edges": 52}, "k": 30},
     "none of the 40 shuffled networks with a Q reaches it (range over 40 shuffled networks: −0.021 to −0.012); 8 "
     "lay beyond their γ scan; 52 had no edges."),
])
def test_each_null_state_and_the_reasons_for_undefined_q(kwargs, expected):
    assert expected in _block(_summary(**kwargs))


def test_the_weak_warning_appears_only_when_most_shuffled_networks_have_no_q():
    weak = "⚠ Most shuffled networks have no Q (60 of 100), so this comparison is weak."
    assert weak in _block(_summary(d=40, k=30))
    assert "this comparison is weak" not in _block(_summary(d=50, k=30))


def test_the_observed_runs_note_ties_and_no_selected_partition():
    note = ("The runs at γ_obs found a Q of 0.069 on the observed network, above its Selected Partition's 0.067; the "
            "comparison uses 0.069.")
    assert note in _block(_summary(from_runs=True)) and "The runs at γ_obs" not in _block(_summary())
    assert "observed wider than 76, equal to 3, of 79." in _block(_summary(equal=3))
    none = _block(_summary(k=0))
    assert "None of the 100 shuffled networks has a Selected Partition." in none
    assert "Widths are upper bounds" not in none and "Multi-Tag Clusters: observed" not in none


def test_the_combined_dissolved_list_with_all_three_groups_and_with_one():
    three = _block(_summary(re_clusters=_clusters(("C1", "C2")), at_clusters=_clusters(("C1", "C3"))))
    assert ("**Dissolved in most subsamples** (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this "
            "study's rule): 1 of 4 Multi-Tag Clusters in both arms: *C1 (Strategy, Tactical, Turn-Based, …)*; re-selected only: "
            "*C2 (5, 6, 7, …)*; at resolution only: *C3 (9, 10, 11, …)*.") in three
    both = _block(_summary(re_clusters=_clusters(("C1", "C2")), at_clusters=_clusters(("C1", "C2"))))
    assert "rule): 2 of 4 Multi-Tag Clusters in both arms: *C1 (Strategy, Tactical, Turn-Based, …)*, *C2 (5, 6, 7, …)*." in both
    assert "only:" not in both
    border = _block(_summary(re_clusters=_clusters(borderline=("C4",)), at_clusters=_clusters(borderline=("C4",))))
    assert ("**Borderline** (the 95% Wilson interval contains ½): in both arms: *C4 (13, 14, 15, …)*.") in border
    assert "No Multi-Tag Cluster is dissolved in most subsamples in either arm." in border


def test_a_not_assessable_cluster_suppresses_the_no_dissolved_sentence():
    gone = _block(_summary(re_clusters=_clusters(unassessable=("C3",)), at_clusters=_clusters(unassessable=("C3",))))
    assert ("**Not assessable** (fewer than 2 of its tags survive in every subsample): in both arms: "
            "*C3 (9, 10, 11, …)*.") in gone
    assert "No Multi-Tag Cluster is dissolved" not in gone
    assert "No Multi-Tag Cluster is dissolved in most subsamples in either arm." in _block(
        _summary(re_clusters=_clusters()))


def test_validation_block_variants():
    assert _block(None, pair=(14, 2), chosen=(14, 2)) == "**Validation of g = 14, s = 2**\n\nNot validated."
    custom = _block(_summary(), chosen=(15, 3), ran=False)
    assert custom.split("\n\n")[1] == "Validation ran for g = 17, s = 2, the pair chosen under the default constraints."
    none = _block(_summary(), chosen=None, ran=False)
    assert none.split("\n\n")[1] == ("⚠ No pair qualifies under your constraints, so this is the validation of g = 17, "
                                     "s = 2, the pair chosen under the default constraints.")


def test_the_validation_block_in_bulgarian_uses_the_decimal_comma_and_from_to_ranges():
    bg = _block(_summary(equal=3), tx=text("bg"))
    assert "Q при резолюция 1,151 е 0,067;" in bg
    assert "обхват от −0,021 до −0,012" in bg
    assert "(персентили 10–90: от 0,57 до 0,86)" in bg
    assert "наблюдаваната е по-широка от 76 и равна на 3 от 79." in bg
    assert "**Разпаднати в повечето подизвадки** (индекс на Jaccard по Hennig ≤ 0,5" in bg
