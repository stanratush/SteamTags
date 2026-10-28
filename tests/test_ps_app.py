"""The Parameter Selection mode in the app: Run, the strip, heatmap, constraints, Inspector, validation, Selection
settings and Apply to Workbench (issues 26–30), driven through the callback functions with a serial `map_fn`."""

from __future__ import annotations

import io
import json
import shutil
import tomllib
import zipfile

import pytest
from dash.exceptions import PreventUpdate

from conftest import CONFIG_DIR, REPO
from steamstudy.i18n import text
from steamstudy.app.relabel import Labels
from steamstudy.app import callbacks as CB
from steamstudy.app import ps_cache, ps_run
from steamstudy.app import ps_view as PV
from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL
from steamstudy.network import selection_text as T
from test_app import _help_targets, _walk, triggered

EN = text("en")
from test_i18n import pseudo  # noqa: E402,F401  (the bracketing pseudo-language fixture)

SMALL = {"g_range": [15, 17], "s_range": [2, 4], "null_replicates": 2, "subsamples": 2}
OUTPUTS = ["rows", "cache_line", "provenance", "banner", "banner_style", "continue_style", "continue_text",
           "export_disabled", "strip", "loading", "heatmap", "why", "validation", "inspector", "apply_disabled",
           "apply_line", "apply_class", "validate_style", "c_label", "s_label", "run_one", "pill_run",
           "pill_constraints", "pill_settings"]


def _text(component) -> str:
    out = []
    for c in _walk(component):
        children = getattr(c, "children", None)
        for child in children if isinstance(children, list) else [children]:
            if isinstance(child, str):
                out.append(child)
    return " ".join(out)


@pytest.fixture(scope="module")
def ps_template(tmp_path_factory):
    """A test Build whose `[parameter_selection]` grid is 3 × 3 with R = S = 2, its cache filled by Run."""
    from steamstudy.build.core import build
    from steamstudy.build.writer import write_build
    from steamstudy.config import ALL_FILES, config_from_data
    from steamstudy.snapshot import Snapshot
    from test_build_network import tagged_world

    files = {n: tomllib.loads((CONFIG_DIR / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}
    files["network"]["parameter_selection"].update(SMALL)
    root = tmp_path_factory.mktemp("ps")
    folder = write_build(build(Snapshot(tagged_world().snapshot(root / "snap")), config_from_data(files),
                               "20261005T150000Z-abcdef12"), root)
    ctx = load_build(folder)
    defaults, _ = PV.defaults_of(ctx)
    ps_run.run(ctx, defaults, [d.key for d in ctx.datasets])
    return folder


@pytest.fixture
def ps_build(ps_template, tmp_path):
    folder = tmp_path / "root" / "builds" / ps_template.parent.name / ps_template.name
    shutil.copytree(ps_template, folder)
    return folder


@pytest.fixture
def empty_build(ps_template, tmp_path):
    folder = tmp_path / "root" / "builds" / ps_template.parent.name / ps_template.name
    shutil.copytree(ps_template, folder, ignore=shutil.ignore_patterns("app_cache"))
    return folder


def _store(ctx):
    defaults, constraints = PV.defaults_of(ctx)
    return PV.settings_data(defaults), {"shared": PV.constraints_data(constraints), "datasets": {}}


def render(build, dataset="overall", metric="neighbour_agreement", pair=None, progress=None, active=None,
           cstore=None):
    ctx = load_build(build)
    a, c = _store(ctx)
    out = CB.ps_render("selection", active or a, cstore or c, dataset, metric, pair, progress is not None, progress,
                       str(build))
    return dict(zip(OUTPUTS, out))


def _views(build, cstore=None, active=None):
    ctx = load_build(build)
    defaults, constraints = PV.defaults_of(ctx)
    settings = PV.settings_of(active) if active else defaults
    return {d.key: PV.dataset_view(ctx, settings, d.key, PV.active_constraints(cstore, d.key, constraints), constraints)
            for d in ctx.datasets}


# ----------------------------------------------------------------------------- issue 26: mode, Run, strip


def test_the_mode_is_the_third_option_and_carries_every_selection_help_key(ps_build):
    from steamstudy.app import help as H
    from steamstudy.app.layout import build_layout, root_class

    layout = build_layout(load_build(ps_build))
    mode = next(c for c in _walk(layout) if getattr(c, "id", None) == "mode")
    assert [o["label"] for o in mode.options] == ["Workbench", "Analysis Report mode", "Parameter Selection"]
    assert "selection" in root_class("selection", ["controls"], False).split()
    shown = render(ps_build)
    targets = set(_help_targets([layout, list(shown.values())]))
    assert {H.target(k) for k in H.SELECTION_HELP} <= targets


def test_an_empty_cache_shows_not_run_everywhere(empty_build):
    out = render(empty_build)
    assert _text(out["strip"]).count("not run") == 5
    assert _text(out["why"]) == T.NOTHING_RUN and out["export_disabled"]
    assert all("not run" in _text(row) for row in out["rows"])
    assert out["continue_style"] == {"display": "none"} and out["loading"] == []


def test_a_filled_cache_shows_each_dataset_status(ps_build):
    out = render(ps_build)
    views = _views(ps_build)
    strip = _text(out["strip"])
    for v in views.values():
        assert v.status == "complete"
        if v.star:
            g, s = v.star
            assert f"★ {g}·{s} NA" in strip
    assert "no qualifying pair" in strip  # the three empty datasets
    assert not out["export_disabled"] and "Results from the app cache: Build" in out["cache_line"]
    assert out["provenance"] == "" and out["banner_style"] == {"display": "none"}


def test_the_run_job_fills_the_cache_and_the_rows(empty_build):
    ctx = load_build(empty_build)
    active, _ = _store(ctx)
    request = {"datasets": ["overall"], "settings": active, "nonce": 1.0}
    progress = []
    assert CB.ps_job(progress.append, request, str(empty_build), map_fn=map) == 1.0
    assert progress[-1]["weight_done"] == pytest.approx(progress[-1]["weight_total"])
    rows = [_text(r) for r in render(empty_build)["rows"]]
    assert "grid done, validated" in rows[0] or "grid done, not validated" in rows[0]
    assert "not run" in rows[1]
    loading = render(empty_build, progress=progress[0])["loading"]
    assert "Searching 9 Threshold Pairs" in _text(loading) and "Dataset 1 of 1" in _text(loading)


def test_cancel_then_continue(empty_build):
    ctx = load_build(empty_build)
    defaults, _ = PV.defaults_of(ctx)
    ticks = []
    ps_run.run(ctx, defaults, ["overall"], on_progress=ticks.append, should_stop=lambda: len(ticks) >= 2)
    out = render(empty_build)
    assert out["continue_style"] == {"display": "inline-block"}
    assert out["continue_text"].startswith("Continue (") and "of 9 pairs)" in out["continue_text"]
    assert T.NO_SELECTION_YET.split(".")[0] in _text(out["why"])
    active, _ = _store(ctx)
    triggered("ps-continue.n_clicks")
    request = CB.ps_run_request(None, None, 1, active, "overall", str(empty_build))
    assert request["datasets"] == ["overall"]
    CB.ps_job(lambda _: None, request, str(empty_build), map_fn=map)
    assert render(empty_build)["continue_style"] == {"display": "none"}


def test_a_strip_click_switches_the_dataset_and_resets_the_pair():
    triggered('{"dataset":"puzzle","type":"ps-strip"}.n_clicks')
    assert CB.ps_pick_dataset([None, 1]) == ("puzzle", None)


def test_each_controls_section_is_a_pill_with_its_section_in_the_popover(ps_build):
    ctx = load_build(ps_build)
    items = [c for c in _walk(PV.controls(Labels(EN), ctx, *PV.defaults_of(ctx)))
             if getattr(c, "className", None) == "ctl-item"]
    assert [i.children[0].children[0].children for i in items] == ["Run", "Pair Constraints", "Selection settings"]
    pops = [i.children[1] for i in items]
    assert all(p.className == "pill-pop" and p.children.className == "ctl-section" for p in pops)
    assert "ps-run-all" in {getattr(c, "id", None) for c in _walk(pops[0])}
    out = render(ps_build)
    assert (out["pill_run"], out["pill_constraints"], out["pill_settings"]) == ("5 of 5 done", "default", "default")
    progress = {"dataset": "overall", "dataset_index": 1, "n_datasets": 5, "phase": "grid", "done": 1, "total": 9,
                "weight_done": 1.0, "weight_total": 45.0, "elapsed": 2.0}
    assert render(ps_build, progress=progress)["pill_run"] == "running"
    _, cstore = _store(ctx)
    cstore["shared"]["min_retention"] = 0.9
    assert render(ps_build, cstore=cstore)["pill_constraints"] == "custom"


def test_the_run_pill_says_not_run_on_an_empty_cache(empty_build):
    assert render(empty_build)["pill_run"] == "not run"


def test_the_floating_inspector_starts_closed_opens_on_a_heatmap_pick_and_closes_with_its_x(ps_build):
    layout = PV.mode_layout(load_build(ps_build), Labels(EN))
    inspector = next(c for c in _walk(layout) if getattr(c, "id", None) == "ps-inspector")
    assert "has-sel" not in inspector.className.split()  # docked at wide; hidden at medium and narrow
    triggered("ps-heatmap.clickData")
    assert CB.ps_inspector_form({"points": [{"x": 3, "y": 16}]}, None).split() == ["inspector", "docked", "ps-inspector", "has-sel"]
    triggered("ps-inspector-close.n_clicks")
    assert "has-sel" not in CB.ps_inspector_form({"points": [{"x": 3, "y": 16}]}, 1).split()


def test_the_provenance_line_and_the_library_banner(ps_build):
    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    path = ps_cache.grid_dir(ctx.app_cache, defaults.grid_key("overall", ctx.context("overall"))) / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["computed_with"]["versions"]["python"] = "3.12.0"
    manifest["computed_with"]["utc"] = "2026-10-26T10:00:00Z"
    ps_cache.write_json(path, manifest)
    out = render(ps_build)
    assert out["provenance"].startswith("Computed when this bundle was made: Python 3.12.0") and "2026-10-26" in out[
        "provenance"]
    manifest["computed_with"]["versions"]["numpy"] = "0.0.1"
    ps_cache.write_json(path, manifest)
    out = render(ps_build)
    assert out["banner"].endswith("Clear app cache and Run to recompute here.") and out["banner_style"] == {}


# ----------------------------------------------------------------------------- issue 27: heatmap and constraints


def test_the_heatmap_has_one_cell_per_pair_with_letters_star_and_outlines(ps_build):
    view = _views(ps_build)["overall"]
    fig = PV.heatmap(view, "neighbour_agreement", (16, 3), tx=EN)
    trace = fig.data[0]
    cells = [(g, s) for gi, g in enumerate(trace.y) for si, s in enumerate(trace.x) if trace.z[gi][si] is not None
             or trace.text[gi][si]]
    assert sorted(cells) == sorted(view.pairs)
    for gi, g in enumerate(trace.y):
        for si, s in enumerate(trace.x):
            letters = "".join(PV.LETTERS[r] for r in view.choice.reasons[(g, s)])
            assert trace.text[gi][si] == ("★" if view.star == (g, s) else "") + letters
    colors = [shape.line.color for shape in fig.layout.shapes]
    assert colors.count("#f28e2b") == len(view.choice.near_best) and colors.count("#222") == 1
    grey = PV.heatmap(view, "q", None, tx=EN)
    assert grey.data[0].colorscale[0][1] != trace.colorscale[0][1] and grey.layout.title.text == T.DESCRIPTIVE_CAPTION


def test_confirm_with_another_constraint_rechooses_and_labels_custom(ps_build):
    ctx = load_build(ps_build)
    active, cstore = _store(ctx)
    before = _views(ps_build)["overall"]
    assert before.star == (15, 3)  # (15, 2) has one neighbour with a different graph
    triggered("ps-c-confirm.n_clicks")
    store = CB.ps_constraints_store(1, None, 0.5, 0.1, 0.9, 1, None, 0.05, "all", cstore, "overall", active,
                                    str(ps_build))
    assert _views(ps_build, store)["overall"].star == (15, 2)
    out = render(ps_build, cstore=store)
    assert out["c_label"] == "Custom constraints: comparable neighbours ≥ 1 (default 2)"
    assert "Custom constraints: comparable neighbours ≥ 1 (default 2)" in _text(out["why"])
    assert not list(ps_cache.root(ctx.app_cache).glob("**/*.tmp"))  # nothing written: no job


def test_a_per_dataset_override_touches_only_that_dataset(ps_build):
    ctx = load_build(ps_build)
    active, cstore = _store(ctx)
    triggered("ps-c-confirm.n_clicks")
    store = CB.ps_constraints_store(1, None, 0.5, 0.1, 0.9, 2, None, 0.2, "dataset", cstore, "puzzle", active,
                                    str(ps_build))
    assert set(store["datasets"]) == {"puzzle"}
    out = render(ps_build, cstore=store)
    custom = [b for b in out["strip"][0].children if any(getattr(c, "className", "") == "ps-custom"
                                                         for c in b.children)]
    assert [b.id["dataset"] for b in custom] == ["puzzle"]
    assert render(ps_build, "overall", cstore=store)["c_label"] == "Default constraints"
    triggered("ps-c-reset.n_clicks")
    reset = CB.ps_constraints_store(None, 1, 0.5, 0.1, 0.9, 2, None, 0.2, "dataset", store, "puzzle", active,
                                    str(ps_build))
    assert reset == cstore


def test_constraints_that_exclude_everything_show_the_no_qualifying_message(ps_build):
    ctx = load_build(ps_build)
    active, cstore = _store(ctx)
    triggered("ps-c-confirm.n_clicks")
    store = CB.ps_constraints_store(1, None, 1.0, 0.0, 1.0, 4, None, 0.05, "all", cstore, "overall", active,
                                    str(ps_build))
    view = _views(ps_build, store)["overall"]
    assert view.choice.status == "no_qualifying_pair"
    why = _text(render(ps_build, cstore=store)["why"])
    assert "No pair qualifies" in why and f"{view.choice.n_selected} of 9 pairs have a Selected Partition" in why
    for e in view.choice.exclusion:
        assert str(e.alone) in why and str(e.cumulative) in why


def test_constraint_marks_and_confirm_state(ps_build):
    ctx = load_build(ps_build)
    active, cstore = _store(ctx)
    *marks, disabled, note = CB.ps_constraint_marks(0.5, 0.1, 0.9, 2, None, 0.05, cstore, "overall", active,
                                                    str(ps_build), "en")
    assert marks == [""] * 6 and disabled and note == ""
    *marks, disabled, note = CB.ps_constraint_marks(0.6, 0.1, 0.9, 2, None, 0.05, cstore, "overall", active,
                                                    str(ps_build), "en")
    assert marks[0] == "changed" and not disabled and note == "Unconfirmed changes"


# ----------------------------------------------------------------------------- issue 28: Inspector and validation


def test_the_inspector_for_chosen_non_qualifying_and_unselected_pairs(ps_build):
    views = _views(ps_build)
    overall = views["overall"]
    chosen = render(ps_build, pair=None)
    assert f"g = {overall.star[0]}, s = {overall.star[1]}" in _text(chosen["inspector"])
    assert "✓ qualifies" in _text(chosen["inspector"]) and not chosen["apply_disabled"]
    assert "Workbench γ" in chosen["apply_line"]
    other = next(p for p in overall.pairs if overall.choice.reasons[p])
    out = render(ps_build, pair=list(other))
    assert PV.REASON_WORDS[overall.choice.reasons[other][0]] in _text(out["inspector"])
    empty = render(ps_build, dataset="rpg", pair=[15, 2])
    assert empty["apply_disabled"] and empty["apply_line"].startswith("No Selected Partition: no_edges")


def test_the_champ_figure_and_the_links_table(ps_build):
    view = _views(ps_build)["overall"]
    result = view.result(view.star)
    fig = PV.champ_figure(result, tx=EN)
    lines = [t for t in fig.data if t.name and t.name.startswith("P")]
    assert len(lines) == len(result.champ["admissible"])
    assert tuple(fig.layout.xaxis.range) == (0, result.gamma_end)
    table = PV.links_table(view, (15, 2), tx=EN)  # a corner: g− and s− lie outside the grid
    assert [r.children[0].children for r in table.children[1:]] == ["g+", "s+"]


def test_the_validation_card_renders_the_block_and_dissolved_only_at_half_or_less(ps_build):
    ctx = load_build(ps_build)
    view = _views(ps_build)["overall"]
    validation = PV.validation_of(ctx, PV.defaults_of(ctx)[0], "overall", view.default_choice.chosen)
    assert validation is not None
    card = PV.validation_card(view, validation, {}, tx=EN)
    text = _text(card)
    assert "Null Comparison" in text and "Subsample Stability" in text
    summary = validation["summary"]
    for arm in ("reselected", "at_resolution"):
        for c in summary["subsample"][arm]["clusters"]:
            assert c["dissolved"] == (c["mean_jaccard"] is not None and c["mean_jaccard"] <= 0.5)
    table = PV.cluster_table(summary, {}, tx=EN)
    dissolved = sum(c["dissolved"] for arm in ("reselected", "at_resolution")
                    for c in summary["subsample"][arm]["clusters"])
    assert _text(table).count("Dissolved") == dissolved


def test_validate_this_pair_writes_the_file_and_updates_the_card(ps_build):
    ctx = load_build(ps_build)
    view = _views(ps_build)["overall"]
    other = next(p for p in view.pairs if p != view.star and view.result(p).selected is not None)
    out = render(ps_build, pair=list(other))
    assert out["validate_style"] == {"display": "inline-block"}
    active, _ = _store(ctx)
    request = CB.ps_validate_request(1, active, "overall", list(other), str(ps_build))
    assert CB.ps_validate_job(lambda _: None, request, str(ps_build), map_fn=map) == request["nonce"]
    assert PV.validation_of(ctx, PV.defaults_of(ctx)[0], "overall", other) is not None
    after = render(ps_build, pair=list(other))
    assert after["validate_style"] == {"display": "none"} and "Not validated" not in _text(after["inspector"])


# ----------------------------------------------------------------------------- issue 29: Selection settings


def test_use_switches_the_key_and_switching_back_shows_the_cache(ps_build):
    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    active, cstore = _store(ctx)
    new, store, pair = CB.ps_use_settings(1, list(defaults.genre_hidden), [1], [], 12, "lift", 3, cstore,
                                          str(ps_build))
    assert new["min_months"] == 12 and pair is None
    out = render(ps_build, active=new)
    assert _text(out["strip"]).count("not run") == 5
    assert out["s_label"] == "Custom settings: Minimum Months 12 (default 0)"
    back, *_ = CB.ps_use_settings(1, list(defaults.genre_hidden), [1], [], 0, "lift", 3, cstore, str(ps_build))
    assert back == active and "★" in _text(render(ps_build, active=back)["strip"])


def test_a_new_minimum_raises_an_active_maximum(ps_build):
    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    _, cstore = _store(ctx)
    cstore["shared"]["max_multi_tag_clusters"] = 4
    _, store, _ = CB.ps_use_settings(1, list(defaults.genre_hidden), [1], [], 0, "lift", 6, cstore, str(ps_build))
    assert store["shared"]["max_multi_tag_clusters"] == 6


def test_copy_from_workbench_reset_and_remove_stage_settings(ps_build):
    triggered("ps-s-copy.n_clicks")
    copied = CB.ps_stage_settings(None, 1, [], [], [9, 19], [1], 12, "shared_games", [5001], str(ps_build))
    assert copied[:5] == ([9, 19], [1], [5001], 12, "shared_games")  # never g, s, γ or seed
    triggered('{"tag":5003,"type":"ps-remove"}.n_clicks')
    staged = CB.ps_stage_settings(None, None, [1], [5001], None, None, None, None, None, str(ps_build))
    assert staged[2] == [5001, 5003]
    triggered("ps-s-reset.n_clicks")
    reset = CB.ps_stage_settings(1, None, [], [5001], None, None, None, None, None, str(ps_build))
    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    assert reset == (list(defaults.genre_hidden), [1], [], 0, "lift", 3)


def test_a_run_under_custom_settings_removes_the_tag_from_every_network(ps_build):
    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    custom = defaults.with_(removed_tag_ids=(5001,))
    ps_run.run(ctx, custom, ["overall"])
    folder = ps_cache.grid_dir(ctx.app_cache, custom.grid_key("overall", ctx.context("overall"))) / "graphs"
    files = list(folder.glob("*.json"))
    assert files and all(5001 not in json.loads(f.read_text(encoding="utf-8"))["nodes"] for f in files)
    names = PV.tag_names(ctx)
    assert SEL.settings_label(custom, defaults, names, tx=EN).text == f"Custom settings: 1 removed tag ({names[5001]})"


# ----------------------------------------------------------------------------- issue 30: Apply to Workbench


def _apply(build, pair=None):
    ctx = load_build(build)
    active, _ = _store(ctx)
    out = CB.ps_apply(1, "overall", pair, active, str(build))
    values = dict(zip([*CB.CONTROL_IDS, "removed", "relayout", "rs-view", "pending", "verify", "mode"], out))
    return ctx, values


def _recompute_with(build, values, verify):
    return CB.recompute(str(build), *[values[k] for k in CB.CONTROL_IDS], values["removed"], verify)


def test_apply_sets_the_workbench_and_shows_the_reproduced_line(ps_build):
    ctx, values = _apply(ps_build)
    view = _views(ps_build)["overall"]
    result = view.result(view.star)
    assert values["mode"] == "workbench" and values["relayout"] is None and values["rs-view"] is None
    assert (values["min-games"], values["min-shared"]) == view.star
    assert (values["algorithm"], values["weight"]) == ("leiden", "lift")
    assert (values["gamma"], values["seed"]) == (result.workbench["gamma"], result.workbench["seed"])
    out = _recompute_with(ps_build, values, values["verify"])
    line, verify = out[16], out[17]
    assert line.endswith("— Selected Partition reproduced ✓") and verify["applied_key"] == out[0]["key"]
    clusters = {frozenset(t for t, c in zip(result.nodes, result.selected) if c == label)
                for label in set(result.selected)}
    tables = out[1]
    shown: dict[str, set[int]] = {}
    for row in tables["nodes"]:
        shown.setdefault(row["cluster"], set()).add(row["tag_id"])
    assert {frozenset(x) for x in shown.values()} == clusters
    # a changed setting removes the line
    changed = _recompute_with(ps_build, {**values, "min-games": values["min-games"] + 1}, verify)
    assert changed[16] == "" and changed[17] is None


def test_a_not_reproduced_pair_applies_the_fallback_and_shows_the_ari(ps_build):
    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    view = _views(ps_build)["overall"]
    result = view.result(view.star)
    path = ps_cache.grid_dir(ctx.app_cache, defaults.grid_key("overall", ctx.context("overall"))) / "graphs" / (
        f"{result.graph_hash}.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    fallback = max(0.01, round(result.selected_resolution, 2))
    wrong = 0.01  # a γ that shows a different partition
    data["workbench"] = {"gamma": wrong, "seed": defaults.seed, "seed_kind": "main", "flag": "not_reproduced",
                         "ari": 0.3}
    ps_cache.write_json(path, data)
    PV._LOADED.clear()
    _, values = _apply(ps_build)
    assert (values["gamma"], values["seed"]) == (wrong, defaults.seed) and fallback != wrong
    out = _recompute_with(ps_build, values, values["verify"])
    assert "shows a different partition from the Selected Partition: ARI" in out[16]
    assert "not_reproduced" in render(ps_build)["apply_line"]


def test_an_export_after_apply_records_applied_from_and_keeps_the_state_id(ps_build):
    from steamstudy.app.export import open_export

    ctx, values = _apply(ps_build)
    out = _recompute_with(ps_build, values, values["verify"])
    meta, verify = out[0], out[17]
    sent = CB.do_export(1, None, str(ps_build), meta, None, None, None, verify)
    plain = CB.do_export(1, None, str(ps_build), meta, None, None, None, None)
    unpack = lambda s: json.loads(zipfile.ZipFile(io.BytesIO(__import__("base64").b64decode(s["content"])))  # noqa
                                  .read("export.json"))
    with_block, without = unpack(sent), unpack(plain)
    assert with_block["applied_from"]["reproduced"] is True and "applied_from" not in without
    assert with_block["state_id"] == without["state_id"] and "applied_from" not in with_block["state_key"]
    data = __import__("base64").b64decode(sent["content"])
    opened = open_export(data, builds_root=str(ps_build.parents[1]))
    assert opened.state_id_matches


def test_apply_needs_a_selected_partition(ps_build):
    ctx = load_build(ps_build)
    active, _ = _store(ctx)
    with pytest.raises(PreventUpdate):
        CB.ps_apply(1, "rpg", [15, 2], active, str(ps_build))


# ----------------------------------------------------------------------------- issue 31: Export tables


def _export(build, cstore=None):
    import datetime as dt

    from steamstudy.app.ps_export import export_tables

    ctx = load_build(build)
    defaults, _ = PV.defaults_of(ctx)
    name, data = export_tables(ctx, defaults, cstore, now=dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.UTC))
    zf = zipfile.ZipFile(io.BytesIO(data))
    return name, {n: zf.read(n) for n in zf.namelist()}


def _rows(files, name):
    import csv

    return list(csv.DictReader(io.StringIO(files[name].decode("utf-8-sig"))))


def test_export_tables_writes_the_record(ps_build):
    import hashlib

    from steamstudy.export import schema as S

    ctx = load_build(ps_build)
    defaults, _ = PV.defaults_of(ctx)
    name, files = _export(ps_build)
    assert name == f"steamstudy_parameter-selection_{SEL.key_hash(defaults.settings_key())[:12]}_20261027T120000Z.zip"
    assert set(files) == {s.name for s in S.PS_TABLES} | {"parameter_selection.json", "selection_report.md"}
    meta = json.loads(files["parameter_selection.json"])
    assert meta["schema_version"] == 4 and all(i["status"] == "complete" for i in meta["datasets"].values())
    for file, info in meta["files"].items():
        assert hashlib.sha256(files[file]).hexdigest() == info["sha256"], file
    assert len(_rows(files, "pairs.csv")) == 9 * 5 and len(_rows(files, "selection.csv")) == 5
    assert any(v["status"] == "complete" for v in meta["datasets"]["overall"]["validation"].values())
    assert {r["arm"] for r in _rows(files, "validation_replicates.csv")} == {
        "null", "subsample_reselected", "subsample_at_resolution"}
    assert len(_rows(files, "neighbour_links.csv")) == 4 * 9 * 5
    report = files["selection_report.md"].decode("utf-8")
    assert "## Overall" in report and "## Methods" in report and "Gibson & Mucha 2022" in report
    assert meta["grid"]["scan_end_rule"] == "gm22_gamma_max_n_e" and meta["grid"]["pass_cap"] == 1000
    # a partial grid is left out of every table and listed with its count
    folder = ps_cache.grid_dir(ctx.app_cache, defaults.grid_key("overall", ctx.context("overall"))) / "graphs"
    next(iter(sorted(folder.glob("*.json")))).unlink()
    _, files = _export(ps_build)
    meta = json.loads(files["parameter_selection.json"])
    assert meta["datasets"]["overall"]["status"].startswith("partial, ") and "of 9" in meta["datasets"]["overall"][
        "status"]
    assert "overall" not in {r["dataset"] for r in _rows(files, "pairs.csv")}
    assert len(_rows(files, "pairs.csv")) == 9 * 4 and _rows(files, "validation_replicates.csv") == []


def test_two_exports_are_byte_identical_and_constraints_change_only_the_selection(ps_build):
    _, first = _export(ps_build)
    _, again = _export(ps_build)
    for name in first:
        if name != "parameter_selection.json":
            assert first[name] == again[name], name
    ctx = load_build(ps_build)
    _, cstore = _store(ctx)
    custom = {"shared": {**cstore["shared"], "min_comparable_neighbours": 1}, "datasets": {}}
    _, changed = _export(ps_build, custom)
    assert changed["admissible_partitions.csv"] == first["admissible_partitions.csv"]
    assert changed["selection.csv"] != first["selection.csv"]
    rows = {r["dataset"]: r for r in _rows(changed, "selection.csv")}
    assert rows["overall"]["constraints_label"] == "Custom constraints: comparable neighbours ≥ 1 (default 2)"
    meta_a, meta_b = json.loads(first["parameter_selection.json"]), json.loads(changed["parameter_selection.json"])
    assert meta_a["settings_key_hash"] == meta_b["settings_key_hash"]
    assert meta_a["datasets"]["overall"]["grid_key_hash"] == meta_b["datasets"]["overall"]["grid_key_hash"]


# ----------------------------------------------------------------------------- review fixes


def test_apply_and_validate_follow_the_pair_the_inspector_shows_under_custom_constraints(ps_build):
    ctx = load_build(ps_build)
    active, cstore = _store(ctx)
    custom = {"shared": {**cstore["shared"], "min_comparable_neighbours": 1}, "datasets": {}}
    assert _views(ps_build, custom)["overall"].star == (15, 2)
    out = CB.ps_apply(1, "overall", None, active, str(ps_build), custom)
    values = dict(zip([*CB.CONTROL_IDS, "removed"], out))
    assert (values["min-games"], values["min-shared"]) == (15, 2)
    request = CB.ps_validate_request(1, active, "overall", None, str(ps_build), custom)
    assert request["pair"] == [15, 2]


def test_a_pair_validated_by_hand_is_exported(ps_build):
    ctx = load_build(ps_build)
    active, _ = _store(ctx)
    view = _views(ps_build)["overall"]
    other = next(p for p in view.pairs if p != view.star and view.result(p).selected is not None)
    request = CB.ps_validate_request(1, active, "overall", list(other), str(ps_build))
    CB.ps_validate_job(lambda _: None, request, str(ps_build), map_fn=map)
    _, files = _export(ps_build)
    exported = {(r["g"], r["s"]) for r in _rows(files, "validation_replicates.csv") if r["dataset"] == "overall"}
    assert (str(other[0]), str(other[1])) in exported
    meta = json.loads(files["parameter_selection.json"])
    assert meta["datasets"]["overall"]["validation"][f"{other[0]},{other[1]}"]["status"] == "complete"


# ----------------------------------------------------------------------------- the English report (bilingual issue 14)


@pytest.mark.parametrize("variant", ["default", "none_qualifies"])
def test_selection_report_stays_byte_identical(ps_build, variant):
    """`selection_report.md` is English in every Interface Language: byte-identical to the report written before the
    Parameter Selection text went through the translator (tests/fixtures/selection_report_<variant>.md)."""
    import os

    ctx = load_build(ps_build)
    _, constraints = PV.defaults_of(ctx)
    cstore = None
    if variant == "none_qualifies":
        cstore = {"shared": {**PV.constraints_data(constraints), "min_retention": 1.0}, "datasets": {}}
    _, files = _export(ps_build, cstore)
    golden = REPO / "tests" / "fixtures" / f"selection_report_{variant}.md"
    if os.environ.get("STEAMSTUDY_WRITE_GOLDEN"):
        golden.write_bytes(files["selection_report.md"])
    assert files["selection_report.md"] == golden.read_bytes()


# ----------------------------------------------------------------------------- the Interface Language (bilingual issue 14)


def test_the_modes_text_goes_through_the_translator(ps_build, pseudo):
    """With Bulgarian as a bracketing pseudo-language, the loading panel, run rows, dataset strip, "Why this pair", the
    validation card, the Pair Inspector, the pills and the heatmap's own words are all bracketed; dataset labels, tag
    names, cluster labels and export codes are not."""
    import re

    from test_i18n import texts, unbracketed

    ctx = load_build(ps_build)
    a, c = _store(ctx)
    progress = {"dataset": "overall", "dataset_index": 1, "n_datasets": 5, "phase": "grid", "done": 3, "total": 9,
                "weight_done": 3.0, "weight_total": 9.0, "elapsed": 75.0}
    out = dict(zip(OUTPUTS, CB.ps_render("selection", a, c, "overall", "neighbour_agreement", [15, 3], True, progress,
                                         str(ps_build), "bg")))
    names = ({d.label for d in ctx.datasets} | {d.key for d in ctx.datasets} | set(PV.tag_names(ctx).values())
             | {ctx.build_id, "Leiden", "CHAMP", "ARI", "LCC"})
    shown = []
    for key, value in out.items():
        if key == "heatmap":
            continue
        shown += texts(value) if not isinstance(value, str) else [value]
    shown = [x for x in shown if x.strip() and not re.fullmatch(r"[a-z]+(_[a-z]+)*", x)]  # export codes stay
    assert not unbracketed(shown, names)
    fig = out["heatmap"]
    hover = [h for row in fig.data[0].hovertext for h in row if h]
    assert hover and not unbracketed(hover, names)
    assert not unbracketed([fig.layout.xaxis.title.text, fig.layout.yaxis.title.text], names)
    assert fig.layout.separators == "," and PV.plotly_separators(EN) == ".,"  # English keeps Plotly's default
    # the elapsed time, worded from the job's raw numbers
    assert any("⟦1 min 15 s elapsed⟧" in x for x in texts(out["loading"]))


def test_a_language_switch_re_renders_the_mode_and_never_touches_a_running_job(ps_build):
    from steamstudy.app.server import create_app

    deps = create_app(ps_build).server.test_client().get("/_dash-dependencies").get_json()
    render_ = next(d for d in deps if "ps-rows.children" in d["output"])
    assert "lang" in [i["id"] for i in render_["inputs"]]
    for job in ("ps-run-done.data", "ps-validate-done.data", "ps-run-request.data"):
        d = next(d for d in deps if job in d["output"])
        assert "lang" not in [i["id"] for i in d["inputs"] + d["state"]], job
