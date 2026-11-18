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
