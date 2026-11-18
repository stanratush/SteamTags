"""The Cluster Comparison mode in the app (issue 18): the mode, the shared settings, the dataset table and the pair
list, driven through the callback functions on the Parameter Selection test Build (grid g 15–17 × s 2–4, filled by
Run: Overall's run picks (15, 3); the other datasets' runs have no Selected Partition)."""

from __future__ import annotations

import re

import pytest
from dash.exceptions import PreventUpdate

from steamstudy.app import callbacks as CB
from steamstudy.app import cc_view as CC
from steamstudy.app import help as H
from steamstudy.app.layout import build_layout, root_class
from steamstudy.app.loader import load_build
from steamstudy.network import comparison_text as CT
from test_app import _help_targets, _walk, triggered
from test_ps_app import _store, _text, empty_build, ps_build, ps_template  # noqa: F401  (fixtures)


def render(build, include=None, requests=None, pair=None, lang=None, **shared):
    ctx = load_build(build)
    defaults = CC.shared_defaults(ctx)
    keys = [d.key for d in ctx.datasets]
    include = keys if include is None else include
    _, cstore = _store(ctx)
    out = CB.cc_render("comparison", shared.get("weight", defaults.clustering_weight),
                       shared.get("algorithm", defaults.algorithm), shared.get("min_months", defaults.min_months),
                       list(shared.get("genre", defaults.genre_hidden)), list(defaults.removed_tag_ids),
                       [[k] if k in include else [] for k in keys], requests or {}, pair, cstore, str(build), lang)
    return dict(zip(CC.RENDER_OUTPUTS, out))


def main(build, out, include=None, pair=None, lang=None, minimum=None, weak=False, orient=None, focus=None,
         match=None):
    """The main column (`cc_main`) for the view choices, after `render` gave `out`."""
    ctx = load_build(build)
    defaults = CC.shared_defaults(ctx)
    keys = [d.key for d in ctx.datasets]
    include = keys if include is None else include
    _, cstore = _store(ctx)
    got = CB.cc_main(out["shown"], minimum, weak, orient, focus, match, defaults.clustering_weight,
                     defaults.algorithm, defaults.min_months, list(defaults.genre_hidden),
                     list(defaults.removed_tag_ids), [[k] if k in include else [] for k in keys], {}, pair, cstore,
                     str(build), lang)
    return dict(zip(CC.MAIN_OUTPUTS, got))


def _boxes(view) -> list:
    return [c for c in _walk(view["diagram"]) if isinstance(getattr(c, "id", None), dict)
            and c.id.get("type") == "cc-box"]


def _chosen_pair(build, out):
    """The chosen pair's PairResult (Build order) and both partitions, from the warm memos."""
    ctx = load_build(build)
    _, cstore = _store(ctx)
    result = CC.resolve_all(ctx, CC.shared_defaults(ctx), [d.key for d in ctx.datasets], {}, cstore)
    a, b = out["shown"]["pair"]
    return result.pairs[(a, b)], result.resolved[a].partition, result.resolved[b].partition


def _pair_names(out) -> list[str]:
    return [_text(row.children[0]) for row in out["pairs"]]


def test_the_mode_is_the_fourth_option_and_opens_from_the_url(ps_build):
    ctx = load_build(ps_build)
    layout = build_layout(ctx, mode="comparison")
    mode = next(c for c in _walk(layout) if getattr(c, "id", None) == "mode")
    assert mode.value == "comparison" and mode.options[-1]["value"] == "comparison"
    assert {"workbench", "comparison"} <= set(root_class("comparison", ["controls"], False).split())
    ids = {getattr(c, "id", None) for c in _walk(layout) if isinstance(getattr(c, "id", None), str)}
    assert {"cc-body", "cc-sidebar", "cc-main", "cc-s-weight", "cc-s-algorithm", "cc-s-genre", "cc-s-removed",
            "cc-comparison-id", "cc-pairs"} <= ids
    rows = [c for c in _walk(layout) if getattr(c, "id", None) == {"type": "cc-include", "dataset": "overall"}]
    assert rows and rows[0].value == ["overall"]  # every dataset is included when the mode first opens


def test_the_shared_settings_start_from_parameter_selection_and_have_no_seed_or_defining_tag_control(ps_build):
    ctx = load_build(ps_build)
    layout = build_layout(ctx, mode="comparison")
    by_id = {c.id: c for c in _walk(layout) if isinstance(getattr(c, "id", None), str)}
    shared = CC.shared_defaults(ctx)
    assert (by_id["cc-s-weight"].value, by_id["cc-s-algorithm"].value) == ("lift", "leiden")
    assert by_id["cc-s-genre"].value == list(shared.genre_hidden)
    assert not {"cc-s-seed", "cc-s-defining"} & set(by_id)


def test_an_empty_cache_resolves_every_dataset_with_no_run(empty_build):
    out = render(empty_build)
    assert all("No Automatic Parameter Selection run" in _text(s) for s in out["sources"])
    assert re.fullmatch(r"[0-9a-f]{12}", out["comparison_id"])
    assert len(out["pairs"]) == 10 and out["shown"]["pair"] is not None


def test_a_filled_cache_puts_each_dataset_on_its_pick_with_its_figures(ps_build):
    out = render(ps_build)
    overall = _text(out["sources"][0])
    assert "★ Selected Partition at g 15 · s 3 (chosen pair)" in overall and "Seed-Noise Floor" in overall
    assert (out["g"][0], out["s"][0]) == (15, 3)
    puzzle = _text(out["sources"][1])
    assert "No qualifying pair in the Automatic Parameter Selection run" in puzzle and "NA —" in puzzle


def test_the_pairs_are_ranked_by_ari_and_the_top_pair_is_chosen_on_first_open(ps_build):
    out = render(ps_build)
    aris = []
    for row in out["pairs"]:
        shown = _text(row.children[1]).split()[-1]
        aris.append(-2.0 if shown == "—" else float(shown))
    assert aris == sorted(aris, reverse=True)
    assert "on" in out["pairs"][0].className.split()
    first = out["pairs"][0].id
    assert out["shown"]["pair"] == [first["a"], first["b"]]
    assert "Comparable Tag" in _text(out["pairs"][0]) and "in common" in _text(out["pairs"][0])


def test_including_and_excluding_datasets_changes_the_pairs_and_the_comparison_id(ps_build):
    everything = render(ps_build)
    three = render(ps_build, include=["overall", "puzzle", "rpg"])
    assert len(three["pairs"]) == 3 and three["comparison_id"] != everything["comparison_id"]
    assert all("Strategy" not in name for name in _pair_names(three))
    one = render(ps_build, include=["overall"])
    assert one["comparison_id"] == "—" and one["shown"]["pair"] is None
    assert CT.FEWER_THAN_TWO in _text(one["pairs"])
    empty = main(ps_build, one, include=["overall"])
    assert empty["empty"] == CT.FEWER_THAN_TWO and empty["pair_style"] == {"display": "none"}
    assert len(one["sources"]) == 5  # an excluded dataset's row still shows its source


def test_a_clicked_pair_is_chosen_while_both_its_datasets_are_included(ps_build):
    triggered('{"a":"puzzle","b":"rpg","type":"cc-pair"}.n_clicks')
    assert CB.cc_pick_pair([0, 1]) == ["puzzle", "rpg"]
    with pytest.raises(PreventUpdate):
        CB.cc_pick_pair([0, 0])  # a re-rendered list, nothing clicked
    assert render(ps_build, pair=["puzzle", "rpg"])["shown"]["pair"] == ["puzzle", "rpg"]
    gone = render(ps_build, include=["overall", "puzzle", "strategy"], pair=["puzzle", "rpg"])
    assert gone["shown"]["pair"] != ["puzzle", "rpg"]


def test_the_mode_never_renders_outside_its_mode(ps_build):
    with pytest.raises(PreventUpdate):
        CB.cc_render("workbench", "lift", "leiden", 0, [], [], [], {}, None, None, str(ps_build))


def test_the_memos_answer_a_second_resolve_without_recomputing(ps_build, monkeypatch):
    render(ps_build)
    calls = []
    monkeypatch.setattr(CC, "resolve", lambda *a, **k: calls.append(a) or pytest.fail("resolved again"))
    monkeypatch.setattr(CC.CMP, "compare_all", lambda *a, **k: pytest.fail("matched again"))
    render(ps_build, pair=["overall", "rpg"])  # a pair click: derived from the memo (b)
    assert calls == []


def test_an_include_change_reuses_every_dataset_partition(ps_build, monkeypatch):
    render(ps_build)
    monkeypatch.setattr(CC, "resolve", lambda *a, **k: pytest.fail("resolved again"))
    out = render(ps_build, include=["overall", "rpg", "strategy"])  # only the matching runs again
    assert len(out["pairs"]) == 3


def test_every_help_key_the_mode_shows_is_a_comparison_key_and_the_bulgarian_words_are_catalogued(ps_build):
    layout = build_layout(load_build(ps_build), mode="comparison")
    out = render(ps_build)
    targets = set(_help_targets([layout, list(out.values())]))
    shown = {H.target(k) for k in ("comparison.mode", "comparison.datasets", "comparison.pairs", "comparison.ari",
                                   "comparison.comparable_tags", "comparison.games_in_common",
                                   "comparison.seed_noise", "comparison.neighbour_agreement",
                                   "comparison.source.pick", "comparison.comparison_id")}
    assert shown <= targets
    bg = render(ps_build, lang="bg")
    assert "сравними тага" in _text(bg["pairs"]) and "Избрано разбиване при g 15 · s 3" in _text(bg["sources"][0])


# ----------------------------------------------------------------------------- the link diagram (issue 19)


def test_the_diagram_lists_every_multi_tag_cluster_and_one_curve_per_match_at_or_above_the_minimum(ps_build):
    out = render(ps_build)
    pair, A, B = _chosen_pair(ps_build, out)
    assert pair.matches, "the fixture's top pair has Cluster Matches"
    view = main(ps_build, out)
    assert view["pair_style"] == {} and view["empty"] == ""
    boxes = {(b.id["dataset"], b.id["cluster"]) for b in _boxes(view)}
    assert boxes == {(A.dataset, c.label) for c in A.multi} | {(B.dataset, c.label) for c in B.multi}
    assert sorted((x["a"], x["b"]) for x in view["links"]) == sorted(
        (m.cluster_a, m.cluster_b) for m in pair.matches if m.jaccard >= 0.10)
    assert not any(x["dashed"] for x in view["links"])
    assert "One-Tag Clusters are not matched" in view["one_tag"]
    assert view["weak_label"] == "show weaker"


def test_the_minimum_changes_the_curves_and_the_badges_but_not_the_comparison_id_and_recomputes_nothing(
        ps_build, monkeypatch):
    out = render(ps_build)
    pair, *_ = _chosen_pair(ps_build, out)
    top = max(m.jaccard for m in pair.matches)
    monkeypatch.setattr(CC, "resolve", lambda *a, **k: pytest.fail("resolved again"))
    monkeypatch.setattr(CC.CMP, "compare_all", lambda *a, **k: pytest.fail("matched again"))
    everything = main(ps_build, out, minimum=0)
    assert len(everything["links"]) == len(pair.matches)
    assert "No match above" not in _text(everything["diagram"])
    above = main(ps_build, out, minimum=round(top + 0.01, 2))
    assert above["links"] == []
    badges = [c for c in _walk(above["diagram"]) if "below_minimum" in (getattr(c, "className", "") or "")]
    assert badges and f"No match above {top + 0.01:.2f}" in _text(badges[0])
    assert render(ps_build)["comparison_id"] == out["comparison_id"]


def test_show_weaker_adds_the_hidden_matches_dashed(ps_build):
    out = render(ps_build)
    pair, *_ = _chosen_pair(ps_build, out)
    minimum = round(max(m.jaccard for m in pair.matches) + 0.01, 2)
    weak = main(ps_build, out, minimum=minimum, weak=True)
    assert len(weak["links"]) == len(pair.matches) and all(x["dashed"] for x in weak["links"])
    assert weak["weak_label"] == "hide weaker"
    assert CB.cc_toggle_weak(1, False) is True and CB.cc_toggle_weak(2, True) is False


def test_swap_puts_the_other_dataset_on_the_left_with_its_flags_against_the_first(ps_build):
    out = render(ps_build)
    pair, A, B = _chosen_pair(ps_build, out)
    orient = CB.cc_swap(1, out["shown"], None)
    assert orient == [B.dataset, A.dataset]
    assert CB.cc_swap(2, out["shown"], orient) == [A.dataset, B.dataset]
    swapped = main(ps_build, out, orient=orient, minimum=0)
    assert _text(swapped["title"]).index(load_build(ps_build).dataset(B.dataset).label) == 0
    sides = {b.id["dataset"]: getattr(b, "data-side") for b in _boxes(swapped)}
    assert (sides[B.dataset], sides[A.dataset]) == ("a", "b")
    assert sorted((x["b"], x["a"]) for x in swapped["links"]) == sorted(
        (m.cluster_a, m.cluster_b) for m in pair.matches)
    # every flag now reads against the dataset on the right
    left = load_build(ps_build).dataset(A.dataset).label
    flags = [_text(c) for c in _walk(swapped["diagram"]) if "cc-flag" in (getattr(c, "className", "") or "")]
    assert all(left in f for f in flags if f.startswith("No match:"))


def test_a_box_click_shows_only_its_curves_and_a_second_click_shows_all(ps_build):
    out = render(ps_build)
    pair, A, B = _chosen_pair(ps_build, out)
    label = pair.matches[0].cluster_a
    triggered(f'{{"cluster":"{label}","dataset":"{A.dataset}","type":"cc-box"}}.n_clicks')
    focus = CB.cc_focus([1], out["shown"], None)
    assert focus["dataset"] == A.dataset and focus["cluster"] == label
    view = main(ps_build, out, focus=focus, minimum=0)
    assert view["links"] and all(x["a"] == label for x in view["links"])
    reached = {x["b"] for x in view["links"]}
    for box in _boxes(view):
        dim = "dim" in box.className.split()
        if box.id["dataset"] == B.dataset:
            assert dim == (box.id["cluster"] not in reached)
        else:
            assert dim == (box.id["cluster"] != label)
    assert CB.cc_focus([1], out["shown"], focus) is None  # again: show all
    with pytest.raises(PreventUpdate):
        CB.cc_focus([0], out["shown"], None)


def test_a_curve_click_records_the_match_in_build_order_and_swap_keeps_it(ps_build):
    out = render(ps_build)
    pair, A, B = _chosen_pair(ps_build, out)
    view = main(ps_build, out, minimum=0)
    record = view["links"][0]["record"]
    m = pair.matches[0]
    assert record == {"comparison_id": out["comparison_id"], "pair": [A.dataset, B.dataset], "a": m.cluster_a,
                      "b": m.cluster_b}
    chosen = main(ps_build, out, minimum=0, match=record)
    assert [x["chosen"] for x in chosen["links"]].count(True) == 1 and chosen["links"][0]["chosen"]
    swapped = main(ps_build, out, minimum=0, match=record, orient=[B.dataset, A.dataset])
    marked = [x for x in swapped["links"] if x["chosen"]]
    assert len(marked) == 1 and (marked[0]["a"], marked[0]["b"]) == (m.cluster_b, m.cluster_a)
    assert marked[0]["record"] == record
    stale = main(ps_build, out, minimum=0, match={**record, "comparison_id": "000000000000"})
    assert not any(x["chosen"] for x in stale["links"])


def test_a_pair_with_no_cluster_match_shows_the_empty_state(ps_build):
    out = render(ps_build)
    ctx = load_build(ps_build)
    _, cstore = _store(ctx)
    result = CC.resolve_all(ctx, CC.shared_defaults(ctx), [d.key for d in ctx.datasets], {}, cstore)
    pair = result.pairs[tuple(out["shown"]["pair"])]
    import dataclasses
    view = CC.main_view(ctx, result, dataclasses.replace(pair, matches=()), CC.DiagramView(), CB.text("en"))
    assert _text(view.diagram) == CT.NO_MATCH and view.links == []


def test_the_diagram_controls_carry_their_comparison_tooltips_and_bulgarian_words(ps_build):
    layout = build_layout(load_build(ps_build), mode="comparison")
    by_id = {c.id: c for c in _walk(layout) if isinstance(getattr(c, "id", None), str)}
    tx = CB.text("en")
    assert getattr(by_id["cc-swap"], "data-tip") == H.tip("comparison.swap", tx)
    assert getattr(by_id["cc-minimum-label"], "data-tip") == H.tip("comparison.minimum", tx)
    assert by_id["cc-minimum"].value == 0.10
    out = render(ps_build)
    view = main(ps_build, out, minimum=1)
    badge = next(c for c in _walk(view["diagram"]) if "cc-flag" in (getattr(c, "className", "") or ""))
    code = badge.className.split()[-1]
    assert getattr(badge, "data-tip").startswith(H.tip(f"comparison.flag.{code}", tx)[:-1])
    bg = main(ps_build, out, minimum=1, lang="bg", weak=True)
    assert bg["weak_label"] == "скрий по-слабите" and "Няма съвпадение" in _text(bg["diagram"])


def test_the_registered_outputs_follow_the_render_functions(ps_build):
    from steamstudy.app.server import create_app

    outputs = [[repr(o) for o in spec["output"]] for spec in create_app(ps_build).callback_map.values()
               if isinstance(spec["output"], list)]
    render_outputs = next(o for o in outputs if "<Output `cc-shown.data`>" in o)
    main_outputs = next(o for o in outputs if "<Output `cc-diagram.children`>" in o)
    assert len(render_outputs) == len(CC.RENDER_OUTPUTS) and "<Output `cc-main.children`>" not in render_outputs
    assert len(main_outputs) == len(CC.MAIN_OUTPUTS)


# ----------------------------------------------------------------------------- the match detail (issue 20)

from steamstudy.network import comparison as CMP  # noqa: E402
from test_comparison import game, part  # noqa: E402

EN = CB.text("en")


def _read(component) -> str:
    """The text in reading order, spaces collapsed."""
    def walk(c):
        if isinstance(c, (list, tuple)):
            return " ".join(walk(x) for x in c)
        if isinstance(c, (str, int, float)):
            return str(c)
        return walk(getattr(c, "children", None)) if c is not None else ""
    return " ".join(walk(component).split())


def _detail(A, B, a, b, names=None):
    pair = CMP.compare_pair(A, B)
    m = next(x for x in pair.matches if (x.cluster_a, x.cluster_b) == (a, b))
    return m, CC.match_detail(CC.Side("Overall"), CC.Side("Puzzle"), m, pair.n_comparable, names or {}, EN)


def _rows(detail) -> list:
    return [r for r in _walk(detail) if type(r).__name__ == "Tr" and type(r.children[0]).__name__ == "Td"]


def test_with_no_match_chosen_the_detail_asks_for_a_curve(ps_build):
    out = render(ps_build)
    assert _read(main(ps_build, out)["detail"]) == CT.CHOOSE_A_MATCH
    assert _read(CC.match_detail(CC.Side("A"), CC.Side("B"), None, 0, {}, EN)) == CT.CHOOSE_A_MATCH


def test_a_chosen_match_shows_its_figures_tag_groups_and_games():
    # Overall C1 {1,2,3,4} ~ Puzzle C1 {1,2,5,9}: 3 is in Puzzle C2, 4 not in Puzzle's network, 5 in Overall C2, 9 not
    # in Overall's network. N = 6; E = 3·3/6 = 1.5.
    A = part("overall", {"C1": [1, 2, 3, 4], "C2": [5, 6], "C3": [7]},
             games=[game(10, 1, 1, 5), game(11, 2, 3), game(12, 3, 7)], g=2)
    B = part("puzzle", {"C1": [1, 2, 5, 9], "C2": [3, 10], "C3": [6], "C4": [7]},
             games=[game(10, 4, 2, 9), game(11, 5, 3), game(12, 6, 7)], g=2)
    names = {1: "Puzzle", 2: "Logic", 3: "Casual", 4: "Cute", 5: "Relaxing", 9: "Sokoban"}
    m, detail = _detail(A, B, "C1", "C1", names)
    text = _read(detail)
    assert "Overall C1" in text and "Puzzle C1" in text
    assert "Match Jaccard" in text and "0.33" in text  # 2 / 6
    assert "Shared, % of Overall C1" in text and "50%" in text and "comparable: 67%" in text
    assert "Jaccard (comparable)" in text and "0.50" in text and "Comparable Tags: 3 in Overall C1, 3 in Puzzle C1" in text
    assert "2 shared Tags: 1.3× the 1.50 expected from the Cluster sizes (N = 6 Comparable Tags)" in text
    assert "in Puzzle C2" in text and "not in Puzzle's network (0 games, minimum 2)" in text
    assert "in Overall C2" in text and "not in Overall's network (0 games, minimum 2)" in text
    # games: 10 is in both Clusters, 11 only in neither C1 (3 is in C1 of A only), 12 in neither
    assert "Of 3 games in both datasets: 1 in both Clusters, 1 only in Overall C1, 0 only in Puzzle C1, 1 in neither." \
        in text
    (row,) = _rows(detail)
    assert [_read(c) for c in row.children[:5]] == ["1", "4", "game 10", "1 / 4", "2 / 4"]
    # its Tags from either Cluster, the shared ones (Puzzle, Logic) marked
    assert _read(row.children[5]) == "Puzzle , Logic , Sokoban"
    assert [_read(t) for t in row.children[5].children if type(t).__name__ == "B"] == ["Puzzle", "Logic"]


def test_show_all_reveals_every_game_row_after_the_first_ten():
    tags = [1, 2]
    A = part("overall", {"C1": tags}, games=[game(i, i, 1) for i in range(1, 14)])
    B = part("puzzle", {"C1": tags}, games=[game(i, 20 - i, 2) for i in range(1, 14)])
    _, detail = _detail(A, B, "C1", "C1")
    more = next(c for c in _walk(detail) if type(c).__name__ == "Details")
    assert _read(more.children[0]) == "Show all 13"
    assert len(_rows(detail)) == 13 and len(_rows(more)) == 3


def test_the_two_empty_games_sentences():
    A = part("overall", {"C1": [1, 2]}, games=[game(1, 1, 1)])
    B = part("puzzle", {"C1": [1, 3]}, games=[game(2, 1, 1)])
    _, none_in_common = _detail(A, B, "C1", "C1")
    assert CT.NO_GAMES_IN_COMMON in _read(none_in_common)
    B2 = part("puzzle", {"C1": [1, 3]}, games=[game(1, 1, 9), game(5, 2, 9)])
    A2 = part("overall", {"C1": [1, 2]}, games=[game(1, 1, 7), game(5, 3, 7)])
    _, neither = _detail(A2, B2, "C1", "C1")
    assert "None of the 2 games in both datasets is in both Clusters." in _read(neither)


def test_a_cluster_with_fewer_than_two_comparable_tags_has_no_comparable_jaccard():
    A = part("overall", {"C1": [1, 20, 21], "C2": [2, 3]})
    B = part("puzzle", {"C1": [1, 2], "C2": [3, 4]})
    m, detail = _detail(A, B, "C1", "C1")
    assert m.comparable_jaccard is None
    fig = next(c for c in _walk(detail) if "cc-fig" == getattr(c, "className", None)
               and "Jaccard (comparable)" in _read(c))
    assert "—" in _read(fig)


def test_a_set_aside_defining_tag_is_in_the_hidden_group_and_in_no_figure():
    # Tag 9 (Puzzle's defining Tag) is hidden in Puzzle only: set aside from Overall C1.
    A = part("overall", {"C1": [1, 2, 9]})
    B = part("puzzle", {"C1": [1, 2, 3]}, hidden=[9])
    m, detail = _detail(A, B, "C1", "C1", {9: "Puzzle"})
    assert m.n_tags_a == 2 and m.jaccard == pytest.approx(2 / 3)
    assert "Puzzle hidden in Puzzle (its defining Tag)" in _read(detail)


def test_swap_swaps_the_detail_columns_without_recomputing(ps_build, monkeypatch):
    out = render(ps_build)
    pair, A, B = _chosen_pair(ps_build, out)
    record = main(ps_build, out, minimum=0)["links"][0]["record"]
    monkeypatch.setattr(CC.CMP, "compare_all", lambda *a, **k: pytest.fail("matched again"))
    ctx = load_build(ps_build)
    la, lb = ctx.dataset(A.dataset).label, ctx.dataset(B.dataset).label
    m = pair.matches[0]
    straight = _read(main(ps_build, out, match=record)["detail"])
    swapped = _read(main(ps_build, out, match=record, orient=[B.dataset, A.dataset])["detail"])
    assert straight.index(f"{la} {m.cluster_a}") < straight.index(f"{lb} {m.cluster_b}")
    assert swapped.index(f"{lb} {m.cluster_b}") < swapped.index(f"{la} {m.cluster_a}")
    assert f"Rank in {lb}" in swapped and swapped.index(f"Rank in {lb}") < swapped.index(f"Rank in {la}") \
        or not m.games.rows


# ----------------------------------------------------------------------------- editing and state (issue 21)
# The fixture's Overall run has a Selected Partition in every cell of g 15–17 × s 2–4 and picks (15, 3); the other
# runs have none.


def edit(build, out, dataset, g=None, s=None, gamma=None, requests=None, cstore=None, shared_id=None, **shared):
    """`cc_requests` after an edit of one row (g, s or γ; the rest as shown) or a shared setting."""
    ctx = load_build(build)
    defaults = CC.shared_defaults(ctx)
    keys = [d.key for d in ctx.datasets]
    values = out["shown"]["values"]
    gs, ss, rs = ([values[k][i] for k in keys] for i in range(3))
    if dataset:
        i = keys.index(dataset)
        gs[i], ss[i], rs[i] = (gs[i] if g is None else g), (ss[i] if s is None else s), (rs[i] if gamma is None
                                                                                          else gamma)
        triggered(f'{{"dataset":"{dataset}","type":"cc-g"}}.value')
    else:
        triggered(f"{shared_id}.value")
    return CB.cc_requests(gs, ss, rs, shared.get("weight", defaults.clustering_weight), defaults.algorithm,
                          defaults.min_months, list(shared.get("genre", defaults.genre_hidden)),
                          list(defaults.removed_tag_ids), out["shown"], requests or {}, cstore or _store(ctx)[1],
                          str(build), None)


def test_typing_a_cells_g_and_s_selects_that_cell_and_its_gamma_follows(ps_build):
    out = render(ps_build)
    requests, notice = edit(ps_build, out, "overall", g=16, s=4)
    assert requests == {"overall": {"source": "cell", "g": 16, "s": 4}} and notice == ""
    now = render(ps_build, requests=requests)
    assert "Selected Partition at g 16 · s 4" in _text(now["sources"][0]) and "★" not in _text(now["sources"][0])
    assert (now["g"][0], now["s"][0], now["resolution"][0]) == (16, 4, 1.39)  # its Selected Resolution, 1.385
    back, _ = edit(ps_build, now, "overall", g=15, s=3, requests=requests)
    assert back == {"overall": {"source": "pick"}}


def test_typing_a_pair_with_no_selected_partition_or_a_gamma_sets_the_dataset_by_hand(ps_build):
    out = render(ps_build)
    requests, _ = edit(ps_build, out, "overall", g=10, s=5)
    assert requests == {"overall": {"source": "hand", "g": 10, "s": 5, "resolution": out["resolution"][0]}}
    gamma, _ = edit(ps_build, out, "overall", gamma=0.8)
    assert gamma == {"overall": {"source": "hand", "g": 15, "s": 3, "resolution": 0.8}}
    puzzle, _ = edit(ps_build, out, "puzzle", g=9)  # no run: any pair is by hand
    assert puzzle["puzzle"]["source"] == "hand"
    now = render(ps_build, requests=gamma)
    assert "Set by hand: one Leiden run, main seed" in _text(now["sources"][0]) and now["resolution"][0] == 0.8
    assert now["comparison_id"] != out["comparison_id"]


@pytest.mark.parametrize("values", [{"g": 0}, {"g": 1000}, {"s": 0}, {"g": 2.5}, {"gamma": 0}, {"gamma": None}])
def test_values_out_of_the_workbench_limits_are_refused(ps_build, values):
    out = render(ps_build)
    with pytest.raises(PreventUpdate):
        edit(ps_build, out, "overall", **values)


def test_a_value_the_render_wrote_is_no_edit(ps_build):
    out = render(ps_build)
    with pytest.raises(PreventUpdate):
        edit(ps_build, out, "overall")


def test_a_pair_constraints_change_moves_a_pick_dataset_only(ps_build):
    ctx = load_build(ps_build)
    _, cstore = _store(ctx)
    strict = {**cstore, "datasets": {d: {**cstore["shared"], "max_multi_tag_clusters": 1} for d in ("overall", "rpg")}}
    out = CB.cc_render("comparison", "lift", "leiden", CC.shared_defaults(ctx).min_months,
                       list(CC.shared_defaults(ctx).genre_hidden), [], [[d.key] for d in ctx.datasets], {}, None,
                       strict, str(ps_build), None)
    sources = dict(zip(CC.RENDER_OUTPUTS, out))["sources"]
    assert "No qualifying pair in the Automatic Parameter Selection run" in _text(sources[0])  # the pick moved
    kept = CB.cc_render("comparison", "lift", "leiden", CC.shared_defaults(ctx).min_months,
                        list(CC.shared_defaults(ctx).genre_hidden), [], [[d.key] for d in ctx.datasets],
                        {"overall": {"source": "cell", "g": 16, "s": 4}}, None, strict, str(ps_build), None)
    assert "Selected Partition at g 16 · s 4" in _text(dict(zip(CC.RENDER_OUTPUTS, kept))["sources"][0])


def test_a_shared_setting_change_puts_every_dataset_back_on_its_pick_with_a_notice(ps_build):
    out = render(ps_build)
    hand = {"overall": {"source": "hand", "g": 10, "s": 5, "resolution": 1.0}, "puzzle": {"source": "pick"}}
    requests, notice = edit(ps_build, out, None, requests=hand, shared_id="cc-s-weight", weight="shared_games")
    assert requests == {} and notice == CT.SHARED_SETTINGS_CHANGED
    quiet = edit(ps_build, out, None, requests={"puzzle": {"source": "pick"}}, shared_id="cc-s-genre", genre=[])
    assert quiet == ({}, "")
    louvain = render(ps_build, algorithm="louvain")  # no run under Louvain: every dataset with no run
    assert all("No Automatic Parameter Selection run" in _text(s) for s in louvain["sources"])


def test_one_datasets_edit_reuses_the_others_partitions(ps_build, monkeypatch):
    render(ps_build)
    resolved = []
    real = CC.resolve
    monkeypatch.setattr(CC, "resolve", lambda ctx, shared, request, *a, **k: resolved.append(request.dataset)
                        or real(ctx, shared, request, *a, **k))
    render(ps_build, requests={"overall": {"source": "hand", "g": 12, "s": 5, "resolution": 1.0}})
    assert resolved == ["overall"]


def test_switching_to_another_mode_and_back_keeps_the_whole_view(ps_build):
    requests = {"overall": {"source": "cell", "g": 16, "s": 4}}
    out = render(ps_build, include=["overall", "rpg", "strategy"], requests=requests, pair=["overall", "strategy"])
    with pytest.raises(PreventUpdate):  # away: nothing in the mode's stores changes
        CB.cc_render("workbench", "lift", "leiden", 0, [], [], [], requests, ["overall", "strategy"], None,
                     str(ps_build))
    back = render(ps_build, include=["overall", "rpg", "strategy"], requests=requests, pair=["overall", "strategy"])
    assert back["shown"] == out["shown"] and back["comparison_id"] == out["comparison_id"]
    # the view choices live in stores and a static slider outside the re-rendered column
    layout = build_layout(load_build(ps_build), mode="workbench")
    ids = {getattr(c, "id", None) for c in _walk(layout) if isinstance(getattr(c, "id", None), str)}
    assert {"cc-requests", "cc-pair", "cc-orient", "cc-weak", "cc-focus", "cc-match", "cc-minimum"} <= ids


def test_a_build_switch_starts_the_comparison_fresh_on_every_pick(ps_build):
    from steamstudy.app.build_menu import build_url

    layout = build_layout(load_build(ps_build), mode="comparison")
    stores = {c.id: c for c in _walk(layout) if type(c).__name__ == "Store" and str(c.id).startswith("cc-")}
    assert stores["cc-requests"].data == {}  # every dataset on its pick
    assert all(getattr(stores[k], "data", None) is None for k in ("cc-pair", "cc-orient", "cc-focus", "cc-match"))
    assert "mode=comparison" in build_url(CB.ref_of(CB.build_folder(str(ps_build))), "comparison", "overall")
