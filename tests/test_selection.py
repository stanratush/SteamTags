"""`steamstudy.network.selection`: Selection Settings, keys, seeds, the grid and choosing the pair (issues 20–22)."""

from __future__ import annotations

import dataclasses

import pytest

from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL
from steamstudy.network.stability import noise_seeds, replicate_seeds


@pytest.fixture(scope="module")
def ctx(tagged_build):
    return load_build(tagged_build)


@pytest.fixture(scope="module")
def defaults(ctx):
    return SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)


# ----------------------------------------------------------------------------- settings and keys (issue 20)


def test_defaults_come_from_the_network_table(defaults, ctx):
    assert (defaults.clustering_weight, defaults.algorithm, defaults.min_months) == ("lift", "leiden", 0)
    assert defaults.genre_hidden == tuple(sorted(t.id for t in ctx.genre_tags)) and defaults.hide_defining_tag
    assert (defaults.seed, defaults.null_replicates, defaults.noise_seeds) == (20261003, 20, 10)
    assert (defaults.replicates, defaults.subsamples, defaults.min_multi_tag_clusters) == (100, 100, 3)
    assert len(defaults.pairs()) == 153 and defaults.pairs()[0] == (3, 2) and defaults.pairs()[-1] == (20, 12)


def test_for_pair_resolves_the_defining_tag(defaults, ctx):
    puzzle = defaults.for_pair("puzzle", ctx.context("puzzle"), 14, 2)
    assert 1664 in puzzle.hidden_tag_ids and (puzzle.min_games_per_tag, puzzle.min_shared_games) == (14, 2)
    assert puzzle.algorithm == "leiden" and puzzle.clustering_weight == "lift"
    no_genres = dataclasses.replace(defaults, genre_hidden=())
    assert no_genres.for_pair("puzzle", ctx.context("puzzle"), 14, 2).hidden_tag_ids == (1664,)
    shown = dataclasses.replace(no_genres, hide_defining_tag=False)
    assert shown.for_pair("puzzle", ctx.context("puzzle"), 14, 2).hidden_tag_ids == ()


def test_keys(defaults, ctx):
    puzzle = ctx.context("puzzle")
    hashed = SEL.key_hash
    assert hashed(defaults.grid_key("puzzle", puzzle)) == hashed(SEL.load_selection_settings(
        ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id).grid_key("puzzle", puzzle))
    for change in ({"min_months": 3}, {"removed_tag_ids": (5001,)}, {"clustering_weight": "shared_games"},
                   {"min_multi_tag_clusters": 2}, {"gamma_step": 0.1}, {"scan_seeds": 5}, {"seed": 1},
                   {"hide_defining_tag": False}, {"g_range": (3, 19)}):
        changed = dataclasses.replace(defaults, **change)
        assert hashed(changed.grid_key("puzzle", puzzle)) != hashed(defaults.grid_key("puzzle", puzzle)), change
        assert hashed(changed.settings_key()) != hashed(defaults.settings_key()), change
    for change in ({"replicates": 50}, {"subsamples": 10}):
        changed = dataclasses.replace(defaults, **change)
        assert hashed(changed.grid_key("puzzle", puzzle)) == hashed(defaults.grid_key("puzzle", puzzle))
        assert hashed(changed.validation_key("puzzle", puzzle, 14, 2)) != hashed(
            defaults.validation_key("puzzle", puzzle, 14, 2))
    assert hashed(defaults.grid_key("puzzle", puzzle)) != hashed(defaults.grid_key("overall", ctx.context("overall")))
    assert defaults.settings_key()["method_version"] == "parameter-selection-1"
    assert "gamma_step" in defaults.settings_key() and "dataset" not in defaults.settings_key()
    v = defaults.validation_key("puzzle", puzzle, 14, 2)
    assert (v["g"], v["s"], v["validation_method_version"], v["trades_per_game"], v["subsample_fraction"]) == (
        14, 2, "ps-validation-1", 10, 0.8)
    assert v["grid_key"] == defaults.grid_key("puzzle", puzzle)


def test_constraints_enter_no_key(defaults, ctx):
    constraints = SEL.default_constraints(ctx.network)
    assert constraints == SEL.Constraints(0.05, 0.5, 0.1, 0.9, 2, None)
    assert "tolerance" not in str(defaults.grid_key("puzzle", ctx.context("puzzle")))


def test_labels(defaults, ctx):
    names = {5001: "Puzzle-ish", 5002: "Casual-ish"}
    assert SEL.settings_label(defaults, defaults, names).text == "Default settings"
    custom = dataclasses.replace(defaults, min_months=12, removed_tag_ids=(5001, 5002))
    label = SEL.settings_label(custom, defaults, names)
    assert label.text == "Custom settings: Minimum Months 12 (default 0), 2 removed tags (Puzzle-ish, Casual-ish)"
    assert label.changes == [{"setting": "min_months", "value": 12, "default": 0},
                             {"setting": "removed_tag_ids", "value": [5001, 5002], "default": []}]
    base = SEL.default_constraints(ctx.network)
    assert SEL.constraints_label(base, base).text == "Default constraints"
    tighter = dataclasses.replace(base, tolerance=0.1, max_multi_tag_clusters=8)
    assert SEL.constraints_label(tighter, base).text == (
        "Custom constraints: tolerance 0.10 (default 0.05), Multi-Tag Clusters ≤ 8 (default off)")


def test_selection_seed_streams_are_disjoint_and_stable(defaults):
    scan, null, sub = SEL.selection_seeds(defaults)
    assert (len(scan), len(null), len(sub)) == (10, 100, 100)
    lower = set(replicate_seeds(defaults.seed, 20)) | set(noise_seeds(defaults.seed, 10, 20))
    groups = [set(scan), set(null), set(sub), lower]
    assert sum(len(g) for g in groups) == len(set().union(*groups))
    assert SEL.selection_seeds(defaults) == (scan, null, sub)
    assert scan[:3] == GOLDEN_SCAN


GOLDEN_SCAN = [1558840077, 1805315920, 847274496]  # main seed 20261003, stream 3: frozen so a change to the streams shows


def test_pair_networks_on_the_test_build(defaults, ctx):
    pairs = SEL.pair_networks(ctx.games("overall"), defaults, "overall", ctx.context("overall"))
    assert len(pairs) == 153
    by_pair = {(p.g, p.s): p for p in pairs}
    for (g, s), p in by_pair.items():
        if (g + 1, s) in by_pair:
            assert set(by_pair[(g + 1, s)].network.nodes) <= set(p.network.nodes)
        if (g, s + 1) in by_pair:
            assert by_pair[(g, s + 1)].network.nodes == p.network.nodes
            assert {(e.u, e.v) for e in by_pair[(g, s + 1)].network.edges} <= {(e.u, e.v) for e in p.network.edges}
    same = [(a, b) for a in pairs for b in pairs if a is not b and a.network.nodes == b.network.nodes
            and a.network.edges == b.network.edges]
    assert same and all(a.graph_hash == b.graph_hash for a, b in same)
    assert len({p.graph_hash for p in pairs}) < 153
    removed = dataclasses.replace(defaults, removed_tag_ids=(5001,))
    assert all(5001 not in p.network.nodes for p in SEL.pair_networks(ctx.games("overall"), removed, "overall",
                                                                       ctx.context("overall")))


# ----------------------------------------------------------------------------- run_graph and run_grid (issue 21)


@pytest.fixture(scope="module")
def small(defaults):
    return defaults.with_(g_range=(15, 17), s_range=(2, 4))


@pytest.fixture(scope="module")
def small_grid(ctx, small):
    return SEL.run_grid(ctx.games("overall"), small, "overall", ctx.context("overall"))


def _dump(run):
    return {h: SEL.canonical_json(r.to_json(), drop=["seconds"]) for h, r in run.results.items()}


def test_serial_and_a_pool_of_two_give_byte_identical_results(ctx, small, small_grid):
    import multiprocess as mp

    with mp.Pool(2) as pool:
        parallel = SEL.run_grid(ctx.games("overall"), small, "overall", ctx.context("overall"),
                                map_fn=pool.imap_unordered)
    assert parallel.complete and small_grid.complete
    assert parallel.pair_hash == small_grid.pair_hash and len(small_grid.pair_hash) == 9
    assert _dump(parallel) == _dump(small_grid)
    assert list(small_grid.results) == sorted(small_grid.results)


def test_the_workbench_gamma_and_seed_show_the_selected_partition(ctx, small, small_grid):
    from steamstudy.network.cluster import detect
    from steamstudy.network.graph import to_graph

    scan_seeds, _, _ = SEL.selection_seeds(small)
    by_hash = {p.graph_hash: p for p in SEL.pair_networks(ctx.games("overall"), small, "overall",
                                                          ctx.context("overall"))}
    selected = [r for r in small_grid.results.values() if r.selected is not None]
    assert selected
    for r in selected:
        wb = r.workbench
        if wb["flag"] is not None:
            continue
        p = by_hash[r.graph_hash]
        graph = to_graph(p.network.nodes, p.network.edges, "lift")
        assert wb["seed"] == small.seed if wb["seed_kind"] == "main" else wb["seed"] in scan_seeds
        groups = detect(graph, "leiden", wb["gamma"], wb["seed"])
        expected: dict[int, set[int]] = {}
        for t, label in zip(r.nodes, r.selected):
            expected.setdefault(label, set()).add(t)
        assert set(groups) == {frozenset(c) for c in expected.values()}
        assert round(wb["gamma"], 2) == wb["gamma"] and r.selected_partition["a"] <= wb["gamma"] <= r.selected_partition["b"]


def test_workbench_flags(ctx, small):
    from steamstudy.network.graph import build_network, to_graph

    network = build_network(ctx.games("overall"), small.for_pair("overall", ctx.context("overall"), 15, 2),
                            ctx.context("overall"))
    graph = to_graph(network.nodes, network.edges, "lift")
    nodes = len(network.nodes)
    narrow = SEL.workbench_setting(graph, [0] * nodes, 1.231, 1.239, 1.235, small.seed, [1, 2])
    assert (narrow.flag, narrow.gamma, narrow.seed, narrow.seed_kind) == ("not_representable", 1.24, small.seed, "main")
    never = list(range(nodes))  # every tag its own One-Tag Cluster: Leiden never returns it at γ ≤ 0.5 here
    missed = SEL.workbench_setting(graph, never, 0.2, 0.5, 0.35, small.seed, [1, 2])
    assert (missed.flag, missed.gamma) == ("not_reproduced", 0.35) and missed.ari < 1
    assert SEL.workbench_candidates(0.0, 0.031, 0.0155) == [0.02, 0.01, 0.03]


def test_descriptive_q_equals_the_envelope_value(small_grid):
    for r in small_grid.results.values():
        p = r.selected_partition
        if p is None:
            continue
        gamma = r.selected_resolution
        assert gamma == (p["a"] + p["b"]) / 2
        assert r.modularity == pytest.approx((p["a_hat"] - gamma * p["p_hat"]) / r.champ["two_m"], abs=1e-12)


def test_information_retention_counts_visible_tags_only():
    from test_network import TOY, D, H
    from steamstudy.network.model import TagContext

    def retention(**kw):
        settings = SEL.SelectionSettings(
            build_id="B", genre_hidden=kw.get("hidden", ()), hide_defining_tag=False,
            removed_tag_ids=kw.get("removed", ()), min_months=0, clustering_weight="lift", seed=11,
            null_replicates=4, noise_seeds=4, g_range=(2, 2), s_range=(2, 2), gamma_step=0.05, scan_seeds=2,
            min_multi_tag_clusters=1, replicates=2, subsamples=2)
        run = SEL.run_grid(TOY, settings, "overall", TagContext(genre_tag_ids=frozenset({D})))
        (result,) = run.results.values()
        return result

    # Tag game counts A 4, B 3, C 3, D 4, E 3, F 3, G 2, H 1; at g = s = 2 the edged tags are A-F (20 games);
    # G is an isolated node and H is below g: both still count in the denominator.
    assert retention().retention == pytest.approx(20 / 23)
    assert retention(removed=(H,)).retention == pytest.approx(20 / 22)
    assert retention(hidden=(D,)).retention == pytest.approx(16 / 19)  # D's triangle loses D: E-F stays
    plain = retention()
    assert (plain.n_isolated, plain.isolated_share, plain.lcc_tags, plain.lcc_share) == (1, 1 / 7, 3, 3 / 6)


def test_should_stop_and_skip(ctx, small, small_grid):
    calls = []
    stopped = SEL.run_grid(ctx.games("overall"), small, "overall", ctx.context("overall"),
                           on_result=lambda *a: calls.append(a), should_stop=lambda: len(calls) >= 1)
    assert len(stopped.results) == 1 and not stopped.complete
    done = set(stopped.results)
    rest = SEL.run_grid(ctx.games("overall"), small, "overall", ctx.context("overall"), skip=done)
    assert rest.complete and set(rest.results) == set(small_grid.results) - done
    assert _dump(rest) == {h: v for h, v in _dump(small_grid).items() if h not in done}


def test_a_whole_grid_finishes_quickly_on_two_workers(ctx, defaults):
    import multiprocess as mp
    import time

    started = time.perf_counter()
    with mp.Pool(2) as pool:
        run = SEL.run_grid(ctx.games("puzzle"), defaults, "puzzle", ctx.context("puzzle"), map_fn=pool.imap_unordered)
    assert run.complete and len(run.pair_hash) == 153
    assert time.perf_counter() - started < 300


# ----------------------------------------------------------------------------- Neighbour Agreement and choice (issue 22)


def _result(h: str, nodes, edges, selected=None, *, retention=0.8, isolated_share=0.0, lcc_share=1.0, n_multi=3,
            floor=0.9, workbench=None):
    edged = sorted({t for e in edges for t in e})
    champ = None
    if selected is not None:
        champ = {"selected": 0, "two_m": 1.0,
                 "admissible": [{"membership": list(selected), "a": 1.0, "b": 1.2, "a_hat": 1.0, "p_hat": 0.5}]}
    fields = {f.name: None for f in dataclasses.fields(SEL.GraphResult)}
    fields.update(graph_hash=h, nodes=list(nodes), edged=edged, edges=[list(e) for e in edges], champ=champ,
                  retention=retention, isolated_share=isolated_share, lcc_share=lcc_share, n_multi=n_multi,
                  selected_resolution=1.1 if selected is not None else None, seconds=0.0,
                  seed_noise={"floor": floor, "mean": floor, "exact": 5, "runs": 10},
                  workbench=workbench or {"gamma": 1.1, "seed": 1, "seed_kind": "main", "flag": None, "ari": 1.0})
    return SEL.GraphResult(**fields)


PATH = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
TWO = [0, 0, 0, 1, 1, 1]


def _grid(results):
    return SEL.Grid("toy", {p: r.graph_hash for p, r in results.items()}, {r.graph_hash: r for r in results.values()})


def test_neighbour_agreement_counts_missing_and_identical_links_apart():
    nodes = [1, 2, 3, 4, 5, 6]
    same = _result("h1", nodes, PATH, TWO)
    grid = _grid({
        (3, 2): same, (4, 2): same,  # identical graph: flagged, not counted
        (3, 3): _result("h2", nodes, PATH[:4], [0, 0, 0, 1, 1, 2]),
        (4, 3): _result("h3", nodes, PATH, None),  # no Selected Partition: missing, never 0
        (5, 2): _result("h4", [1, 7], [], [0, 1]),  # only tag 1 is shared: too few compared tags
        (5, 3): _result("h5", [1, 7], [], None),
    })
    links = SEL.neighbour_links(grid)
    by_ends = {(x.p, x.q): x for x in links}
    assert set(by_ends) == {((3, 2), (4, 2)), ((3, 2), (3, 3)), ((3, 3), (4, 3)), ((4, 2), (5, 2)),
                            ((4, 2), (4, 3)), ((4, 3), (5, 3)), ((5, 2), (5, 3))}
    assert by_ends[((3, 2), (4, 2))].identical_graph and by_ends[((3, 2), (4, 2))].ari == 1.0
    assert by_ends[((3, 3), (4, 3))].status == "neighbour_has_no_selected_partition"
    assert by_ends[((4, 2), (5, 2))].status == "too_few_compared_tags"
    na = SEL.neighbour_agreement(grid, links)
    first = na[(3, 2)]
    assert (first.n_in_grid, first.n_comparable, first.n_different, first.n_identical) == (2, 2, 1, 1)
    assert first.value == pytest.approx(by_ends[((3, 2), (3, 3))].ari) and first.value < 1
    assert na[(4, 2)].n_missing == 1 and na[(4, 2)].n_different == 0
    assert na[(4, 2)].status == "no_comparable_neighbours" and na[(4, 2)].value is None
    assert na[(4, 3)].status == "no_selected_partition"
    directions = SEL.pair_links(links, 3, 2, grid.pairs)
    assert directions["g-"] is None and directions["s-"] is None  # outside the grid
    assert directions["g+"] is by_ends[((3, 2), (4, 2))] and directions["s+"] is by_ends[((3, 2), (3, 3))]


def test_edge_overlap_counts_edges_of_dropped_tags_as_differences():
    a = _result("a", [1, 2, 3, 4], [(1, 2), (2, 3), (3, 4)], [0, 0, 1, 1])
    b = _result("b", [1, 2, 3], [(1, 2), (2, 3)], [0, 0, 1])  # tag 4 dropped by the g-step
    x = SEL.link(_grid({(3, 2): a, (4, 2): b}), (3, 2), (4, 2))
    assert x.edge_overlap == pytest.approx(2 / 3) and x.shared_jaccard == pytest.approx(3 / 4)
    assert x.n_compared == 3


def _choice_grid(values):
    """A grid whose NA is set directly: {(g, s): (NA, result keyword arguments)}."""
    grid = _grid({p: _result(f"h{p}", [1, 2, 3], [(1, 2)], [0, 0, 1], **kw) for p, (_, kw) in values.items()})
    na = {p: SEL.NeighbourAgreement(v, "ok" if v is not None else "no_comparable_neighbours", 2, 2,
                                    2 if v is not None else 0, 0, 0, v) for p, (v, _) in values.items()}
    return grid, na


C0 = SEL.Constraints(0.05, 0.5, 0.1, 0.9, 2, None)


def test_choose_near_best_tolerance_edge_and_tie_breaks():
    grid, na = _choice_grid({(3, 2): (0.80, {}), (4, 2): (0.85, {}), (5, 2): (0.90, {}), (5, 3): (0.85, {})})
    choice = SEL.choose(grid, na, C0)
    assert choice.status == "ok" and choice.max_na == 0.90 and choice.best == (5, 2)
    assert choice.near_best == [(4, 2), (5, 2), (5, 3)] and choice.chosen == (4, 2)  # exactly max − 0.05 is in
    assert SEL.choose(grid, na, dataclasses.replace(C0, tolerance=0.0)).chosen == (5, 2)


def test_choose_records_every_failing_reason_with_inclusive_bounds():
    grid, na = _choice_grid({
        (3, 2): (0.9, {"retention": 0.5, "isolated_share": 0.1, "lcc_share": 0.9}),  # every bound met exactly
        (4, 2): (0.9, {"retention": 0.49, "isolated_share": 0.2, "lcc_share": 0.5, "n_multi": 9}),
        (5, 2): (None, {}),
    })
    choice = SEL.choose(grid, na, dataclasses.replace(C0, max_multi_tag_clusters=8))
    assert choice.reasons[(3, 2)] == [] and choice.chosen == (3, 2)
    assert choice.reasons[(4, 2)] == ["retention_below_min", "isolated_share_above_max", "lcc_share_below_min",
                                      "too_many_clusters"]
    assert choice.reasons[(5, 2)] == ["no_neighbour_agreement", "too_few_comparable_neighbours"]
    none = _grid({(3, 2): _result("x", [1, 2], [(1, 2)], None)})
    lone = SEL.NeighbourAgreement(None, "no_selected_partition", 0, 0, 0, 0, 0, None)
    assert SEL.choose(none, {(3, 2): lone}, C0).reasons[(3, 2)] == ["no_selected_partition",
                                                                     "too_few_comparable_neighbours"]


def test_no_qualifying_pair_with_alone_and_cumulative_counts():
    from steamstudy.network import selection_text as T

    grid, na = _choice_grid({
        (3, 2): (0.9, {"retention": 0.4}),
        (4, 2): (0.9, {"retention": 0.4, "isolated_share": 0.5}),
        (5, 2): (0.9, {"isolated_share": 0.5, "lcc_share": 0.1}),
    })
    choice = SEL.choose(grid, na, C0)
    assert choice.status == "no_qualifying_pair" and choice.chosen is None
    assert [(e.constraint, e.alone, e.cumulative) for e in choice.exclusion] == [
        ("min_retention", 2, 2), ("max_isolated_share", 2, 3), ("min_lcc_share", 1, 3),
        ("min_comparable_neighbours", 0, 3)]
    assert T.to_markdown(T.no_qualifying_message(choice, "Default constraints")) == (
        "**No pair qualifies** under the default constraints. 3 of 3 pairs have a Selected Partition. Excluded by "
        "each constraint, alone (cumulative): Information Retention ≥ 0.50: 2 (2), isolated tags ≤ 10%: 2 (3), "
        "largest component ≥ 90% of the tags with an edge: 1 (3), ≥ 2 neighbours with a different graph: 0 (3). "
        "Loosen a constraint, or inspect any pair in the grid and apply it by hand.")


def _explained(pair=None, different=3, identical=0, minimum_k=3):
    from steamstudy.network import selection_text as T

    grid, na = _choice_grid({(3, 2): (0.70, {}), (4, 2): (0.98, pair or {}), (5, 2): (0.96, {})})
    choice = SEL.choose(grid, na, C0)
    own = dataclasses.replace(na[(4, 2)], n_different=different, n_identical=identical)
    return T.to_markdown(T.explanation(choice, grid.at(4, 2), own, "Default settings", "Default constraints",
                                       minimum_k))


CAVEATS = ("*Neighbour Agreement measures how little the clustering changes when g or s moves by one. It does not "
           "show that the Clusters are real.*\n\n*Neighbour Agreement tends to be higher at large g because a "
           "one-step change in the thresholds, particularly s, generally produces a smaller change in the graph. "
           "This can increase agreement independently of the robustness of the Clusters. Choosing the smallest g "
           "among near-best pairs partially counterbalances this tendency.*")


def test_explanation_with_every_conditional_sentence():
    assert _explained(pair={"floor": 0.42}, identical=1, minimum_k=3) == (
        "**Selected: g = 4, s = 2**, resolution 1.100 (Workbench 1.10).\n\n"
        "Default constraints · Default settings.\n\n"
        "3 of 3 pairs have a Selected Partition. 3 qualify under the default constraints: Information Retention ≥ "
        "0.50, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a "
        "different graph. The retention, isolated-share, LCC and neighbour constraints excluded no pair.\n\n"
        "The highest Neighbour Agreement among them is 0.98 (g = 4, s = 2). 2 pairs are within 0.05 of it, and of "
        "these the one with the smallest g, then the smallest s, is selected.\n\n"
        "Its Neighbour Agreement is 0.98 over 3 neighbours with a different graph. 1 more neighbour has an identical "
        "graph and is not counted.\n\n"
        "Its Selected Partition has the minimum 3 Multi-Tag Clusters; a coarser split was not allowed.\n\n"
        "The Seed-Noise Floor at this resolution is 0.42: the clustering also depends noticeably on the seed.\n\n"
        + CAVEATS)


def test_explanation_with_every_conditional_sentence_off_and_the_workbench_variants():
    text = _explained(minimum_k=2)
    assert "identical graph" not in text and "minimum" not in text and "Seed-Noise" not in text
    assert text.endswith(CAVEATS)
    flagged = _explained(pair={"workbench": {"gamma": 1.23, "seed": 1, "seed_kind": "main", "flag": "not_reproduced",
                                             "ari": 0.8}})
    assert flagged.startswith("**Selected: g = 4, s = 2**, resolution 1.100 (Workbench 1.23). Workbench 1.23 with "
                              "the main seed shows a different partition.\n\n")
    odd = _explained(pair={"workbench": {"gamma": 1.1, "seed": 1, "seed_kind": "main", "flag": "not_representable",
                                         "ari": 0.8}})
    assert odd.split("\n\n")[0].endswith("(cannot be entered as a two-decimal value).")
