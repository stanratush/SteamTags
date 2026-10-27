"""`steamstudy.network.champ`: γ_max(K), CHAMP, γ̂ and the Selected Partition (issue 19)."""

from __future__ import annotations

import dataclasses
import json
import math
import warnings

import numpy as np
import pytest

from steamstudy.network import champ as C
from steamstudy.network.cluster import ScanRun


def _runs(memberships: list[list[int]], gammas: list[float] | None = None) -> list[ScanRun]:
    gammas = gammas or [0.1 * i for i in range(len(memberships))]
    return [ScanRun(g, 7, np.asarray(m), False) for g, m in zip(gammas, memberships)]


# Two triangles 0-1-2 and 3-4-5 joined by the bridge 2-3, and the isolated tag 6; every weight 1, 2m = 14.
#   components   {0..5}{6}          Â 14, P̂ 14
#   triangles    {0,1,2}{3,4,5}{6}  Â 12, P̂ (7² + 7²)/14 = 7
#   one tag each                       Â 0,  P̂ (4·2² + 2·3²)/14 = 34/14
# Crossings: components/triangles at 2/7; triangles/one tag each at 12/(7 − 34/14) = 2.625.
BRIDGE = C.edge_arrays(7, [(0, 1, 1.0), (0, 2, 1.0), (1, 2, 1.0), (3, 4, 1.0), (3, 5, 1.0), (4, 5, 1.0), (2, 3, 1.0)])
COMPONENTS = [0, 0, 0, 0, 0, 0, 1]
TRIANGLES = [0, 0, 0, 1, 1, 1, 2]
ONE_TAG_EACH = [0, 1, 2, 3, 4, 5, 6]


def _bridge(min_multi: int = 2, gamma_end: float = 3.0, extra: list[list[int]] = ()) -> C.ChampResult:
    scan = C.dedup(_runs([COMPONENTS, TRIANGLES, ONE_TAG_EACH, *extra]))
    return C.champ(scan, BRIDGE, gamma_end, min_multi)


# ----------------------------------------------------------------------------- γ_max(K) and the scan


def test_gamma_max_matches_gibson_and_mucha_table_s5_and_rises_with_k():
    for k, expected in ((2, 1.0000), (3, 1.0926), (5, 1.4027), (10, 2.1931)):
        assert C.gamma_max_K(k) == pytest.approx(expected, abs=5e-5)
    values = [C.gamma_max_K(k) for k in range(2, 11)]
    assert values == sorted(values) and len(set(values)) == len(values)
    with pytest.raises(ValueError):
        C.gamma_max_K(1)


def test_scan_runs_from_zero_past_gamma_max_on_the_step_grid():
    gammas = C.scan_gammas(3, 0.05)  # γ_max(3) = 1.0926 → last value 1.10
    assert gammas[0] == 0.0 and gammas[-1] == 1.1 and gammas[1] == 0.05 and len(gammas) == 23
    assert all(round(g, 2) == g for g in gammas)


def test_dedup_keeps_the_first_gamma_and_seed_and_counts_hits():
    scan = C.dedup([ScanRun(0.0, 5, np.array([3, 3, 9]), False), ScanRun(0.0, 6, np.array([1, 1, 2]), True),
                    ScanRun(0.5, 5, np.array([4, 2, 2]), False)])
    assert [m.tolist() for m in scan.memberships] == [[0, 0, 1], [0, 1, 1]]
    assert scan.first == [(0.0, 5), (0.5, 5)] and scan.hits == [2, 1]
    assert (scan.n_runs, scan.capped_runs) == (3, 1)


# ----------------------------------------------------------------------------- CHAMP


def test_coefficients_of_the_bridge_graph():
    a, p = C.partition_coefficients([np.array(m) for m in (COMPONENTS, TRIANGLES, ONE_TAG_EACH)], BRIDGE)
    assert a.tolist() == [14.0, 12.0, 0.0]
    assert p.tolist() == pytest.approx([14.0, 7.0, 34 / 14])


def test_domains_estimates_and_map_targets_of_the_bridge_graph():
    result = _bridge()
    assert [p.membership for p in result.admissible] == [tuple(COMPONENTS), tuple(TRIANGLES), tuple(ONE_TAG_EACH)]
    assert [(p.a, p.b) for p in result.admissible] == pytest.approx([(0, 2 / 7), (2 / 7, 2.625), (2.625, 3.0)])
    assert [p.clipped_high for p in result.admissible] == [False, False, True]
    assert [p.reason for p in result.admissible] == ["one_group", None, "not_assortative"]
    tri = result.admissible[1]
    assert (tri.omega_in, tri.omega_out) == pytest.approx((12 / 7, 2 / 7))
    assert tri.gamma_hat == pytest.approx((10 / 7) / math.log(6))
    assert [p.stable for p in result.admissible] == [False, True, False]
    assert [p.target for p in result.admissible] == [None, 1, None]
    assert [(p.n_multi, p.n_one, p.n_one_isolated) for p in result.admissible] == [(1, 1, 1), (2, 1, 1), (0, 7, 1)]


def test_no_cross_weight_when_the_clusters_are_unions_of_components():
    split = C.edge_arrays(6, [(0, 1, 1.0), (0, 2, 1.0), (1, 2, 1.0), (3, 4, 1.0), (3, 5, 1.0), (4, 5, 1.0)])
    result = C.champ(C.dedup(_runs([[0, 0, 0, 1, 1, 1], [0, 1, 2, 3, 4, 5]])), split, 3.0, 1)
    assert result.admissible[0].reason == "no_cross_weight" and not result.admissible[0].stable


def test_a_three_line_breakpoint_goes_to_the_smallest_p_and_drops_the_middle_line():
    a, p = np.array([10.0, 8.0, 6.0]), np.array([10.0, 6.0, 2.0])
    domains, n_twins = C.admissible(a, p, [np.array([0]), np.array([1]), np.array([2])], 2.0)
    assert [(d.index, d.a, d.b) for d in domains] == [(0, 0.0, 0.5), (2, 0.5, 2.0)] and n_twins == 0


def test_twins_keep_the_canonical_membership_that_sorts_first():
    twin = [0, 0, 0, 1, 1, 1, 0]  # the isolated tag moved into the first triangle: same Â and P̂
    result = _bridge(extra=[twin])
    assert result.n_twins == 1
    assert result.admissible[1].membership == tuple(twin)


def test_no_edges_has_no_admissible_partition():
    result = C.champ(C.dedup(_runs([[0, 1, 2]])), C.edge_arrays(3, []), 1.0, 1)
    assert result.admissible == () and result.selected is None and result.reason == "no_edges"


# ----------------------------------------------------------------------------- the Selected Partition


def test_the_minimum_multi_tag_clusters_applies_after_stability():
    result = _bridge(min_multi=2)
    assert result.selected == 1 and result.reason is None
    # Filtering before CHAMP would drop the components partition and give the triangles [0, 2.625].
    assert result.selected_resolution == pytest.approx((2 / 7 + 2.625) / 2)
    assert _bridge(min_multi=3).reason == "too_few_multi_tag_clusters"


def test_no_stable_partition():
    result = C.champ(C.dedup(_runs([COMPONENTS, ONE_TAG_EACH])), BRIDGE, 3.0, 1)
    assert result.selected is None and result.reason == "no_stable_partition"


def test_equal_widths_go_to_the_lower_midpoint_then_canonical_order():
    base = _bridge().admissible[1]
    low = dataclasses.replace(base, a=0.2, b=0.7, membership=(0, 1, 1))
    high = dataclasses.replace(base, a=1.0, b=1.5, membership=(0, 0, 1))
    narrow = dataclasses.replace(base, a=2.0, b=2.4, membership=(0, 0, 0))
    assert C.select([high, narrow, low], 1, 1e-12) == (2, None)
    same = dataclasses.replace(low, membership=(0, 0, 1))
    assert C.select([low, same], 1, 1e-12) == (1, None)


def test_results_serialise_to_canonical_json():
    result = _bridge()
    text = json.dumps(C.to_json(result), sort_keys=True)
    assert json.loads(text)["admissible"][1]["membership"] == TRIANGLES
    assert C.from_json(json.loads(text)) == result


# ----------------------------------------------------------------------------- test-Build graphs


def _scan(tagged_build, dataset: str, g: int, s: int):
    from steamstudy.app.loader import load_build
    from steamstudy.network.cluster import leiden_scan
    from steamstudy.network.graph import build_network, to_graph

    ctx = load_build(tagged_build)
    settings = ctx.default_settings(dataset).with_(clustering_weight="lift", algorithm="leiden",
                                                   min_games_per_tag=g, min_shared_games=s)
    network = build_network(ctx.games(dataset), settings, ctx.context(dataset))
    graph = to_graph(network.nodes, network.edges, "lift")
    index = {t: i for i, t in enumerate(network.nodes)}
    arrays = C.edge_arrays(len(network.nodes), [(index[e.u], index[e.v], e.lift) for e in network.edges])
    gammas = C.scan_gammas(arrays.n_e, 0.05)
    return graph, arrays, C.dedup(leiden_scan(graph, gammas, [11, 22, 33])), gammas[-1]


@pytest.mark.parametrize(("dataset", "g", "s"), [("overall", 20, 6), ("overall", 25, 10), ("puzzle", 6, 3),
                                                 ("overall", 8, 2)])
def test_champ_agrees_with_modularitypruning(tagged_build, dataset, g, s):
    from modularitypruning.champ_utilities import CHAMP_2D
    from modularitypruning.parameter_estimation_utilities import ranges_to_gamma_estimates

    graph, arrays, scan, gamma_end = _scan(tagged_build, dataset, g, s)
    ours = C.champ(scan, arrays, gamma_end, 1)
    import igraph as ig

    oracle_graph = ig.Graph(n=arrays.n, edges=list(zip(arrays.u.tolist(), arrays.v.tolist())))
    oracle_graph.es["weight"] = arrays.w.tolist()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ranges = CHAMP_2D(oracle_graph, [tuple(m.tolist()) for m in scan.memberships], 0.0, gamma_end,
                          single_threaded=True)
        estimates = ranges_to_gamma_estimates(oracle_graph, ranges)
    assert [p.membership for p in ours.admissible] == [tuple(m) for _, _, m in ranges]
    for mine, (start, end, _, gamma_hat) in zip(ours.admissible, estimates):
        assert (mine.a, mine.b) == pytest.approx((start, end), abs=1e-10)
        if mine.reason is None:
            assert mine.gamma_hat == pytest.approx(gamma_hat, abs=1e-10)
            assert mine.stable == (start <= gamma_hat <= end)


def test_every_estimate_stays_below_gamma_max_of_n_e(tagged_build):
    for g, s in ((10, 3), (20, 8), (30, 12)):
        _, arrays, scan, gamma_end = _scan(tagged_build, "overall", g, s)
        result = C.champ(scan, arrays, gamma_end, 1)  # asserts γ̂ ≤ γ_max(n_e) ≤ γ_end itself
        top = C.gamma_max_K(arrays.n_e)
        assert top <= gamma_end
        assert all(p.gamma_hat <= top for p in result.admissible if p.gamma_hat is not None)
