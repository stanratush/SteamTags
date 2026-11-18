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
    assert _text(one["main"]) == CT.FEWER_THAN_TWO and CT.FEWER_THAN_TWO in _text(one["pairs"])
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
