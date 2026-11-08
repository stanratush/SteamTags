"""Seam 4 (UI side): the served page, and the app's callbacks called as plain functions."""

from __future__ import annotations

import base64
import io
import json
import re
import subprocess
import sys
import zipfile

import pytest

from steamstudy.app import callbacks as CB
from steamstudy.app import rs_cache
from steamstudy.app.export import read_export
from steamstudy.app.layout import block_styles
from steamstudy.app.loader import load_build
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.i18n import text
from steamstudy.network.layout import REFERENCE_CANVAS, Canvas, label_width, layout_state
from steamstudy.network.sensitivity import removal_sensitivity
from steamstudy.network.state import compute_state
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world


@pytest.fixture(scope="module")
def build_folder(tmp_path_factory):
    config = load_config(__import__("conftest").CONFIG_DIR)
    root = tmp_path_factory.mktemp("ui")
    return write_build(build(Snapshot(tagged_world().snapshot(root / "snap")), config, "20261005T130000Z-abcdef12"),
                       root)


EN = text("en")


def _tip(data_tip: str | None) -> str:
    """A tooltip's structured lines (help.py) as the English text the browser shows."""
    from steamstudy.app.help import tip_text

    return tip_text(json.loads(data_tip), EN) if data_tip else ""


def _controls(ctx, dataset="overall"):
    s = ctx.default_settings(dataset)
    c = CB.controls_from_settings(ctx, s)
    return [c[k] for k in CB.CONTROL_IDS] + [c["removed"]]


def _recompute(build_folder, **changes):
    ctx = load_build(build_folder)
    values = dict(zip([*CB.CONTROL_IDS, "removed"], _controls(ctx)))
    values.update(changes)
    return CB.recompute(str(build_folder), *[values[k] for k in CB.CONTROL_IDS], values["removed"], None)


def test_served_page_loads_nothing_from_outside_127_0_0_1(build_folder):
    from steamstudy.app.server import create_app

    app = create_app(build_folder)
    client = app.server.test_client()
    assert client.get("/").status_code == 302  # to the startup Build's URL
    page = client.get(client.get("/").headers["Location"])
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    urls = re.findall(r'(?:src|href)="([^"]+)"', html)
    assert urls and all(not re.match(r"^(https?:)?//", u) or "127.0.0.1" in u for u in urls), urls
    for path in ("/_dash-layout", "/_dash-dependencies"):
        body = client.get(path).get_data(as_text=True)
        assert not re.search(r"https?://(?!127\.0\.0\.1)[a-z0-9.-]+\.[a-z]{2,}/[^\"]*\.(?:js|css)", body)
    assert app.config.serve_locally is True


def test_importing_the_app_does_nothing_but_define_it(tmp_path):
    code = ("import os, steamstudy.app.server, steamstudy.app.callbacks, steamstudy.app.layout; "
            "print(sorted(os.listdir('.')))")
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0 and out.stdout.strip() == "[]"


def test_recompute_matches_the_default_state(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    ctx = load_build(build_folder)
    state = compute_state(ctx.games("overall"), ctx.default_settings("overall"), ctx.context("overall"))
    assert meta["state_id"] == state.state_id
    assert len(base["nodes"]) == len(state.nodes) and "appids" not in tables["edges"][0]
    assert all("appids" not in e for e in base["edges"])  # AppID lists stay on the server


@pytest.mark.parametrize("layout_mode", ["global", "separated"])
def test_graph_payload_has_every_visible_element_and_no_appids(build_folder, layout_mode):
    meta, tables, base, *_ = _recompute(build_folder)
    payload = CB.render_graph(base, layout_mode, None, {"kind": "node", "id": base["nodes"][0]["id"]})
    assert {n["id"] for n in payload["nodes"]} == {str(r["tag_id"]) for r in tables["nodes"]}
    assert {(e["source"], e["target"]) for e in payload["edges"]} == \
           {(str(r["source_tag_id"]), str(r["target_tag_id"])) for r in tables["edges"]}
    assert set(payload["positions"]) == {n["id"] for n in payload["nodes"]}
    assert all(len(p) == 2 and all(isinstance(v, float) for v in p) for p in payload["positions"].values())
    assert "appid" not in json.dumps(payload).lower()  # AppID lists stay on the server
    assert payload["selected"] == {"kind": "node", "id": base["nodes"][0]["id"]} and payload["view"] is None
    assert bool(payload["regions"]) == (layout_mode == "separated")
    assert payload["dataset"] == "overall" and payload["layout"] == layout_mode
    assert payload["basis"] == base["basis"]  # dragged positions are dropped when it changes


def test_selection_reaches_the_canvas_as_a_patch():
    patch = CB.show_selection({"kind": "edge", "id": "1-2", "source": "1", "target": "2"})
    assert patch.to_plotly_json()["operations"][0]["params"]["value"] == {"kind": "edge", "id": "1-2"}
    assert CB.show_selection(None).to_plotly_json()["operations"][0]["params"]["value"] is None


def test_every_region_sends_its_tag_count_for_a_title_in_the_interface_language(build_folder):
    """graph.js titles each region from its cluster and count (ui-words `map`), never from the English label."""
    _, tables, base, *_ = _recompute(build_folder)
    regions = CB.render_graph(base, "separated", None, None)["regions"]
    sizes = {r["cluster"]: r["size"] for r in tables["clusters"] if r["kind"] == "multi_tag"}
    n_pool = sum(r["kind"] == "one_tag" for r in tables["clusters"])
    sizes.update({"one_tag_pool": n_pool} if n_pool else {})
    assert regions and {r["cluster"]: r["count"] for r in regions} == sizes


def test_layout_switch_keeps_the_partition_and_export_has_both_coordinate_sets(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    global_els = CB.render_graph(base, "global", None, None)
    separated = CB.render_graph(base, "separated", None, None)
    clusters = lambda payload: {n["id"]: n["cluster"] for n in payload["nodes"]}
    assert clusters(global_els) == clusters(separated)
    assert separated["regions"] and not global_els["regions"]
    assert global_els["positions"] != separated["positions"]
    sent = CB.do_export(1, None, str(build_folder), meta, None, base, None)
    data = base64.b64decode(sent["content"]) if sent.get("base64") else sent["content"]
    export, files = read_export(data)
    assert export["state_id"] == meta["state_id"] and export["layout_source"] == "default"
    header = files["nodes.csv"].decode("utf-8-sig").splitlines()[0]
    assert header.endswith("x_global,y_global,x_cluster_separated,y_cluster_separated")
    import csv
    rows = list(csv.DictReader(io.StringIO(files["nodes.csv"].decode("utf-8-sig"))))
    assert all(r["x_global"] and r["y_global"] and r["x_cluster_separated"] and r["y_cluster_separated"] for r in rows)


def test_tidy_pins_dragged_nodes_is_exported_and_dropped_when_the_basis_changes(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    node = base["nodes"][0]["id"]
    dragged = {"basis": base["basis"], "positions": {node: [400.0, -250.0]}}
    relayout_store = CB.do_tidy(1, base, None, None, dragged)
    positions, zoom = CB.relayout_positions(base, relayout_store)
    assert positions[int(node)] == (400.0, -250.0) and 0 < zoom <= 1
    stale = {"basis": [*base["basis"][:3], base["basis"][3] + 1], "positions": {node: [9.0, 9.0]}}
    assert CB.relayout_positions(base, CB.do_tidy(1, base, None, None, stale))[0][int(node)] != (9.0, 9.0)
    sent = CB.do_export(1, None, str(build_folder), meta, relayout_store, base, None)
    export = read_export(base64.b64decode(sent["content"]))[0]
    assert export["layout_source"] == "relayout"
    other = dict(base, basis=[*base["basis"][:3], base["basis"][3] + 1])
    assert CB.relayout_positions(other, relayout_store) is None


def test_stale_results_are_shown_greyed_and_never_exported(build_folder, tmp_path):
    meta, tables, base, *_ = _recompute(build_folder)
    ctx = load_build(build_folder)
    settings = ctx.default_settings("overall")
    state = compute_state(ctx.games("overall"), settings, ctx.context("overall"))
    rows = removal_sensitivity(state)[:2]
    stale_view = {"state_id": "000000000000", "rows": rows, "done": 2, "total": 24, "from_export": False, "stale": True}
    grid_rows, wrap_class, banner, *_ = CB.show_rs(stale_view, [], None, tables, meta)
    assert wrap_class == "stale" and banner.startswith("Stale")
    sent = CB.do_export(1, None, str(build_folder), meta, None, base, stale_view)
    _, files = read_export(base64.b64decode(sent["content"]))
    assert "removal_sensitivity.csv" not in files
    current = {"state_id": meta["state_id"], "rows": rows, "done": 2, "total": len(state.nodes), "from_export": False}
    out = CB.show_rs(current, [], None, tables, meta)
    assert out[1] == "" and out[2].startswith("Partial") and out[6] == {"display": "inline-block"}
    assert out[7] == f"Continue (2 of {len(state.nodes)} done)"
    sent = CB.do_export(1, None, str(build_folder), meta, None, base, current)
    export, files = read_export(base64.b64decode(sent["content"]))
    assert export["removal_sensitivity"]["status"] == "partial" and "removal_sensitivity.csv" in files


def test_rs_view_reads_the_cache_and_clear_cache_removes_it(build_folder):
    meta, *_ = _recompute(build_folder)
    ctx = load_build(build_folder)
    settings = ctx.default_settings("overall")
    state = compute_state(ctx.games("overall"), settings, ctx.context("overall"))
    for row in removal_sensitivity(state)[:3]:
        rs_cache.add_row(ctx.app_cache, settings.key(), len(state.nodes), row)
    view = CB.refresh_rs_view(meta, None, None, str(build_folder))
    assert view["done"] == 3 and view["state_id"] == meta["state_id"] and not view["from_export"]
    message, cleared = CB.clear_cache(1, str(build_folder))
    assert message.startswith("Cleared 1 cached Removal Sensitivity result and 0") and cleared is None
    assert CB.refresh_rs_view(meta, None, None, str(build_folder))["rows"] == []


def test_open_restores_every_control(build_folder):
    ctx = load_build(build_folder)
    settings = ctx.default_settings("puzzle").with_(min_games_per_tag=9, removed_tag_ids=(5001,), algorithm="leiden",
                                                    resolution=0.85, seed=7, hidden_tag_ids=(9, 19))
    from steamstudy.app.export import export_zip

    _, data = export_zip(ctx, settings)
    contents = "data:application/zip;base64," + base64.b64encode(data).decode("ascii")
    out = CB.do_open(contents, "x.zip", str(build_folder))
    values = dict(zip(["build-path", *CB.CONTROL_IDS, "removed", "relayout", "rs-view", "pending", "verify", "msg"], out))
    assert values["dataset"] == "puzzle" and values["min-games"] == 9 and values["algorithm"] == "leiden"
    assert values["gamma"] == 0.85 and values["seed"] == 7 and values["removed"] == [5001]
    assert values["genre-hidden"] == [9, 19] and values["defining-hidden"] == []
    assert values["verify"] == {"expected": read_export(data)[0]["state_id"]}
    refused = CB.do_open("data:x;base64," + base64.b64encode(b"not an export").decode("ascii"), "y.json",
                         str(build_folder))
    assert refused[-1].startswith("Refused")


def test_an_old_relayout_export_opens_with_every_tag_next_to_the_graph(build_folder):
    from steamstudy.app.export import export_zip

    ctx = load_build(build_folder)
    settings = ctx.default_settings("overall")
    state = compute_state(ctx.games("overall"), settings, ctx.context("overall"))
    layout = layout_state(state)
    far = sorted(state.nodes)[0]
    old = {t: (x * 2.0, y * 2.0) for t, (x, y) in layout.positions.items()} | {far: (2600.0, -2400.0)}
    _, data = export_zip(ctx, settings, relayout_positions=old, state=state)
    out = CB.do_open("data:application/zip;base64," + base64.b64encode(data).decode("ascii"), "old.zip",
                     str(build_folder))
    store = out[len(CB.CONTROL_IDS) + 2]
    assert store["restore"] is True and store["positions"][str(far)] == [2600.0, -2400.0]
    meta, tables, base, *_ = _recompute(build_folder)
    positions, zoom = CB.relayout_positions(base, store)
    others = [positions[t][0] for t in state.nodes if t != far]
    assert min(others) - 200 < positions[far][0] < max(others) + 200  # pulled in next to the graph
    sent = CB.do_export(1, None, str(build_folder), meta, store, base, None)
    assert read_export(base64.b64decode(sent["content"]))[0]["layout_source"] == "relayout"


def test_mode_layout_orders():
    report = block_styles("report", "quality", ["tables"])
    assert report["blk-filters"]["order"] < report["blk-graph"]["order"] < report["blk-quality"]["order"]
    assert report["blk-tabs"]["display"] == "none" and report["blk-export"]["display"] == "block"
    wb = block_styles("workbench", "rs", ["tables"])
    assert wb["blk-rs"]["display"] == "block" and wb["blk-nodes"]["display"] == "none"
    assert block_styles("workbench", "rs", [])["blk-rs"]["display"] == "none"  # Tables collapsed


def triggered(prop_id: str, value=1):
    """Run a callback function as if `prop_id` had triggered it."""
    from dash._callback_context import context_value
    from dash._utils import AttributeDict

    context_value.set(AttributeDict(triggered_inputs=[{"prop_id": prop_id, "value": value}]))


@pytest.mark.parametrize("event, expected", [
    ({"kind": "node", "id": "5001"}, {"kind": "node", "id": "5001"}),
    ({"kind": "edge", "id": "5000-5001", "source": "5000", "target": "5001"},
     {"kind": "edge", "id": "5000-5001", "source": "5000", "target": "5001"}),
    ({"kind": "region", "cluster": "C2"}, {"kind": "cluster", "id": "C2"}),
    ({"kind": "background"}, None),
])
def test_every_tap_kind_selects_the_right_inspector_view(event, expected):
    triggered("graph-event.data", event)
    sel, floating = CB.select(dict(event, nonce=1.0), [], None, None, None, ["inspector"])
    assert sel == expected
    if expected is not None:
        assert floating is True  # the floating Inspector opens wherever it is not docked


def test_panels_collapse_independently_and_graph_only_is_a_form():
    sel = {"kind": "node", "id": "5001"}
    assert CB.arrange("workbench", "quality", ["controls", "tables"], False)[-1] == "workbench controls-on tables-on"
    assert CB.arrange("workbench", "quality", ["controls", "inspector", "tables"], True)[-1].endswith(
        "tables-on graph-only")
    assert CB.arrange("report", "quality", [], False)[-1] == "report"
    assert CB.inspector_form(["controls", "tables"], True, sel) == "inspector has-sel"
    assert CB.inspector_form(["controls", "inspector", "tables"], True, sel) == "inspector docked has-sel"
    assert CB.inspector_form([], False, None) == "inspector"


def test_a_selection_does_not_re_arrange_the_page(build_folder):
    """Only the Inspector's form follows the selection: re-sending every block's style made React re-render
    the tables under them on every click."""
    from steamstudy.app.server import create_app

    app = create_app(build_folder)
    inputs = {key: [i["id"] for i in spec["inputs"]] for key, spec in app.callback_map.items()}
    arrange = next(ids for key, ids in inputs.items() if "blk-dataset.style" in key)
    form = next(ids for key, ids in inputs.items() if "inspector-panel.className" in key)
    assert "selection" not in arrange and "floating-open" not in arrange
    assert {"selection", "floating-open", "panels"} <= set(form)


def test_the_app_draws_the_exported_coordinates_in_both_layouts(build_folder):
    import csv

    meta, tables, base, *_ = _recompute(build_folder)
    sent = CB.do_export(1, None, str(build_folder), meta, None, base, None)
    rows = list(csv.DictReader(io.StringIO(read_export(base64.b64decode(sent["content"]))[1]["nodes.csv"]
                                           .decode("utf-8-sig"))))
    for layout_mode, x, y in (("global", "x_global", "y_global"),
                              ("separated", "x_cluster_separated", "y_cluster_separated")):
        drawn = CB.render_graph(base, layout_mode, None, None)["positions"]
        assert {r["tag_id"]: pytest.approx([float(r[x]), float(r[y])], abs=1e-6) for r in rows} == drawn
    sizes = {n["id"]: n["size"] for n in CB.render_graph(base, "global", None, None)["nodes"]}
    ctx = load_build(build_folder)
    state = compute_state(ctx.games("overall"), ctx.default_settings("overall"), ctx.context("overall"))
    assert sizes == {str(t): layout_state(state).sizes[t] for t in state.nodes}  # fixed by the layout, not by the visible set


@pytest.mark.parametrize("layout_mode", ["global", "separated"])
def test_every_label_is_ranked_for_culling_centers_first_then_by_games(build_folder, layout_mode):
    meta, tables, base, *_ = _recompute(build_folder, **{"min-games": 1, "min-shared": 1})
    payload = CB.render_graph(base, layout_mode, None, None)
    by_id = {n["id"]: n for n in base["nodes"]}
    order = [n["id"] for n in sorted(payload["nodes"], key=lambda n: n["prio"])]
    assert sorted(n["prio"] for n in payload["nodes"]) == list(range(len(base["nodes"])))  # every tag, once
    centers = [i for i in order if by_id[i]["center"]]
    assert centers and order[:len(centers)] == centers
    rest = order[len(centers):]
    assert rest == sorted(rest, key=lambda i: (-by_id[i]["n_games"], int(i)))


def _default_widths(payload, measure):
    """The widths graph.js draws at the default Edge Appearance (linear scaling over the default range), from the
    payload's raw values: the look of before the Edge Appearance, 0.4 + 2.6 × value / largest."""
    lo, hi = payload["appearance"]["defaults"]["width"]
    top = max(e[measure] for e in payload["edges"])
    return {e["id"]: lo + (hi - lo) * e[measure] / top for e in payload["edges"]}


def test_edges_are_thin_and_scale_with_shared_games(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    payload = CB.render_graph(base, "global", None, None)
    widths = _default_widths(payload, "shared")
    shared = {e["id"]: e["shared"] for e in payload["edges"]}
    top = max(shared.values())
    assert all(0.4 <= w <= 3.0 for w in widths.values())
    assert max(widths.values()) == pytest.approx(3.0)
    assert all(widths[a] <= widths[b] for a in widths for b in widths if shared[a] <= shared[b])
    assert widths == {i: pytest.approx(0.4 + 2.6 * v / top) for i, v in shared.items()}  # exactly as before


def test_selecting_a_cluster_focuses_it_and_other_selections_do_not():
    ops = CB.show_selection({"kind": "cluster", "id": "C2"}).to_plotly_json()["operations"]
    view = next(o["params"]["value"] for o in ops if o["location"] == ["view"])
    assert view["cmd"] == "focus" and view["cluster"] == "C2" and view["nonce"]
    ops = CB.show_selection({"kind": "node", "id": "5001"}).to_plotly_json()["operations"]
    assert [o["location"] for o in ops] == [["selected"]]


@pytest.mark.parametrize("source", ["legend", "region", "grid"])
def test_a_cluster_is_selected_from_the_legend_its_region_title_or_the_clusters_grid(source):
    if source == "legend":
        triggered('{"cluster":"C2","type":"legend"}.n_clicks', 1)
        sel, _ = CB.select(None, [1], None, None, None, [])
    elif source == "region":
        triggered("graph-event.data", {"kind": "region", "cluster": "C2"})
        sel, _ = CB.select({"kind": "region", "cluster": "C2", "nonce": 1}, [], None, None, None, [])
    else:
        triggered("clusters-grid.selectedRows", [{"cluster": "C2"}])
        sel, _ = CB.select(None, [], [{"cluster": "C2"}], None, None, [])
    assert sel == {"kind": "cluster", "id": "C2"}


def _search_values(options):
    return [o["value"] for o in options if not o.get("disabled")]


def test_tag_search_lists_every_node_then_every_tag_not_in_the_network_with_its_reasons(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    from steamstudy.app import view as V

    options = V.search_options(tables, meta["key"]["min_games_per_tag"], tx=EN)
    values = _search_values(options)
    nodes = [f"node:{r['tag_id']}" for r in tables["nodes"]]
    missing = [f"nin:{r['tag_id']}" for r in tables["nin"]]
    assert set(values) == set(nodes) | set(missing) and len(values) == len(nodes) + len(missing)
    assert max(values.index(v) for v in nodes) < min(values.index(v) for v in missing)  # visible tags first
    text = {o["value"]: o["search"] + " " + json.dumps(o["label"].to_plotly_json(), default=str) for o in options
            if not o.get("disabled")}
    for r in tables["nin"]:
        for reason in r["reasons"]:
            assert V.reason_text(reason, r["n_games"], meta["key"]["min_games_per_tag"], tx=EN) in text[f"nin:{r['tag_id']}"]
    assert V.reason_text("below_min_games", 3, 8, tx=EN) == "3 games, below 8"
    assert V.reason_text("genre_tag_hidden", 0, 8, tx=EN) == "Genre Tag hidden"
    assert V.reason_text("defining_tag_hidden", 0, 8, tx=EN) == "defining tag hidden"
    assert V.reason_text("removed", 0, 8, tx=EN) == "removed"


def test_choosing_a_tag_in_the_search_selects_and_centres_it_or_opens_its_card():
    triggered("tag-search.value", "node:5001")
    sel, floating = CB.select(None, [], None, None, None, [], "node:5001")
    assert sel == {"kind": "node", "id": "5001", "pan": True} and floating is True
    ops = CB.show_selection(sel).to_plotly_json()["operations"]
    assert {"cmd": "center", "id": "5001"}.items() <= next(o["params"]["value"] for o in ops
                                                          if o["location"] == ["view"]).items()
    triggered("tag-search.value", "nin:9")
    assert CB.select(None, [], None, None, None, [], "nin:9")[0] == {"kind": "nin", "id": "9"}


@pytest.mark.parametrize("reasons, action", [
    (["removed"], "restore"), (["genre_tag_hidden"], "unhide"), (["defining_tag_hidden"], "unhide"),
    (["defining_tag_hidden", "genre_tag_hidden"], "unhide"), (["removed", "genre_tag_hidden"], None),
    (["below_min_games"], None), (["genre_tag_hidden", "below_min_games"], None)])
def test_only_one_action_that_brings_the_tag_back_is_offered(reasons, action):
    from steamstudy.app import view as V

    assert V.nin_action(reasons) == action


def test_restore_and_unhide_change_the_controls_exactly_as_the_existing_ones(build_folder):
    ctx = load_build(build_folder)
    settings = ctx.default_settings("puzzle")
    c = CB.controls_from_settings(ctx, settings.with_(removed_tag_ids=(5001, 5002)))
    restored = CB.nin_act(1, {"kind": "nin", "id": "5001"}, "restore", c["removed"], c["genre-hidden"],
                          c["defining-hidden"], str(build_folder), "puzzle")
    triggered("restore-btn.n_clicks", 1)
    assert restored[0] == CB.edit_removed(None, 1, None, None, 5001, c["removed"])
    genre = [t for t in c["genre-hidden"] if t != 1664][0]
    unhidden = CB.nin_act(1, {"kind": "nin", "id": str(genre)}, "unhide", c["removed"], c["genre-hidden"],
                          c["defining-hidden"], str(build_folder), "puzzle")
    assert unhidden[1] == [t for t in c["genre-hidden"] if t != genre] and unhidden[2] == c["defining-hidden"]
    puzzle = CB.nin_act(1, {"kind": "nin", "id": "1664"}, "unhide", c["removed"], c["genre-hidden"],
                        c["defining-hidden"], str(build_folder), "puzzle")
    after = CB.settings_from_controls(ctx, "puzzle", settings.min_games_per_tag, settings.min_shared_games,
                                      settings.min_months, puzzle[1], puzzle[2], settings.clustering_weight,
                                      settings.algorithm, settings.resolution, settings.seed, puzzle[0])
    assert 1664 not in after.hidden_tag_ids  # the defining tag (also a Genre Tag) comes back with one press
    assert puzzle[3] == {"kind": "node", "id": "1664"}


def test_the_tag_view_lists_its_metrics_then_its_games_then_its_connected_tags(build_folder):
    from steamstudy.app import view as V
    from steamstudy.network.graph import filter_games

    meta, tables, base, *_ = _recompute(build_folder, **{"min-months": 20})
    ctx = load_build(build_folder)
    node = max(tables["nodes"], key=lambda r: r["degree"])
    tag = node["tag_id"]
    games = V.tag_games(ctx.games("overall"), 20, tag)
    expected = [g for g in filter_games(ctx.games("overall"), 20) if tag in g.tag_ids]
    assert [g["appid"] for g in games] == [g.appid for g in expected] and len(games) == node["n_games"]
    connected = V.connected_tags(tables, tag)
    assert len(connected) == node["degree"]
    assert [c["shared"] for c in connected] == sorted((c["shared"] for c in connected), reverse=True)
    triggered("selection.data", {"kind": "node", "id": str(tag)})
    body, *_ = CB.inspector({"kind": "node", "id": str(tag)}, tables, None, str(build_folder), "overall", 20, meta)
    text = json.dumps([b.to_plotly_json() for b in body], default=str)
    lead = " games in the network have this tag"
    assert lead in text and text.index("Metrics") < text.index(lead) < text.index("Connected tags")
    lead_p = next(b for b in body if getattr(b, "className", None) == "lead")
    assert lead_p.children[0].children == str(node["n_games"])  # the bold count of the lead sentence
    assert "used for clustering" in text and "descriptive" in text and "hub" not in text.lower()
    rows = [b for b in body if getattr(b, "id", None) is None]
    assert any(f"Show all {node['n_games']}" in json.dumps(b.to_plotly_json(), default=str) for b in rows) == \
           (node["n_games"] > 10)


def test_a_connected_tag_row_selects_its_edge_and_pans_to_it():
    """A row of the Inspector's connected tags sends the same event as tapping the link (workbench.js)."""
    triggered("graph-event.data", {"kind": "edge", "id": "5000-5001", "source": "5000", "target": "5001", "pan": True})
    sel, _ = CB.select({"kind": "edge", "id": "5000-5001", "source": "5000", "target": "5001", "pan": True},
                       [], None, None, None, [])
    assert sel == {"kind": "edge", "id": "5000-5001", "source": "5000", "target": "5001", "pan": True}


def _components(tree) -> int:
    """How many Dash components a children tree mounts in the browser."""
    if isinstance(tree, (list, tuple)):
        return sum(_components(c) for c in tree)
    if tree is None or isinstance(tree, (str, int, float)):
        return 0
    return 1 + _components(getattr(tree, "children", None))


def test_the_inspector_stays_a_few_components_however_many_games_and_links_a_tag_has(build_folder):
    """Dash's renderer costs grow faster than the component count, so long lists are one HTML component each:
    switching between two well-linked tags must not take seconds."""
    meta, tables, base, *_ = _recompute(build_folder, **{"min-games": 1, "min-shared": 1})
    by_degree = sorted(tables["nodes"], key=lambda r: r["degree"])
    counts = []
    for node in (by_degree[0], by_degree[-1]):
        body, *_ = CB.inspector({"kind": "node", "id": str(node["tag_id"])}, tables, None, str(build_folder),
                                "overall", 0, meta)
        counts.append(_components(body))
    assert by_degree[-1]["degree"] >= 20 and counts[1] <= 80 and counts[1] - counts[0] <= 5
    edge = max(tables["edges"], key=lambda e: e["shared_games"])
    body, *_ = CB.inspector({"kind": "edge", "id": "x", "source": str(edge["source_tag_id"]),
                             "target": str(edge["target_tag_id"])}, tables, None, str(build_folder), "overall", 0, meta)
    assert _components(body) <= 40
    cluster = max(tables["clusters"], key=lambda c: c["size"])
    body, *_ = CB.inspector({"kind": "cluster", "id": cluster["cluster"]}, tables, None, str(build_folder),
                            "overall", 0, meta)
    assert _components(body) <= 40


def test_inspector_tables_escape_names_and_carry_the_link_to_select():
    from steamstudy.app import view as V

    node = {"tag": "Tag <b>", "tag_id": 1, "cluster": "C1", "n_games": 1, "is_center": False, "within_z": None,
            "silhouette": None, "silhouette_status": "n/a", "strength_shared": 1, "strength_lift": 1,
            "strength_shared_intra": 1, "strength_lift_intra": 1, "degree": 1, "degree_intra": 1,
            "membership_stability": None, "participation": 0, "medoid_score": None}
    games = [{"appid": 7, "name": "<script>alert(1)</script> & Co", "rank": 1}]
    connected = [{"edge": "1-2", "tag": "Rock & <Roll>", "cluster": "C1", "color": "#123456", "shared": 3, "lift": 2.0}]
    html_text = json.dumps([c.to_plotly_json() for c in V.node_inspector(node, "shared_games", None, 2, False, games,
                                                                         connected, tx=EN)], default=str)
    assert "<script>" not in html_text and "&lt;script&gt;alert(1)&lt;/script&gt; &amp; Co" in html_text
    assert "Rock &amp; &lt;Roll&gt;" in html_text and 'data-edge=\\"1-2\\"' in html_text


def _texts(component) -> list[str]:
    """Every text node and tooltip of a component tree."""
    out: list[str] = []
    def walk(c):
        if c is None:
            return
        if isinstance(c, (str, int, float)):
            out.append(str(c))
        elif isinstance(c, (list, tuple)):
            for x in c:
                walk(x)
        else:
            for attr in ("title", "data-tip"):
                if getattr(c, attr, None):
                    out.append(getattr(c, attr))
            walk(getattr(c, "children", None))
    walk(component)
    return out


def test_summary_row_and_quality_boxes_show_the_state_values(build_folder):
    from steamstudy.app import view as V

    values = dict(zip([*CB.CONTROL_IDS, "removed"], _controls(load_build(build_folder))))
    out = CB.recompute(str(build_folder), *[values[k] for k in CB.CONTROL_IDS], values["removed"], None)
    meta, tables = out[0], out[1]
    q = tables["quality"]
    summary, sentence, quality = out[4], out[5], out[6]
    text = " ".join(_texts(summary))
    assert f"{q['n_dataset_games']} of 100" in text or f"{q['n_dataset_games']} of " in text
    for expected in (str(q["n_nodes"]), str(q["n_edges"]), f"{q['n_multi_tag_clusters']} + {q['n_one_tag_clusters']}",
                     EN.num(q["modularity"]), f"excess +{EN.num(q['q_excess'])}", EN.num(q["mean_silhouette"]),
                     "descriptive", "not a selection criterion"):
        assert expected in text, expected
    boxes = " ".join(_texts(quality))
    for expected in (EN.num(q["modularity"]), f"+{EN.num(q['q_excess'])}", V.z_text(q["modularity_z"], EN),
                     f"{EN.num(q['q_null_mean'])} ± {EN.num(q['q_null_sd'])}", EN.num(q["coverage"]),
                     EN.num(q["seed_ari_min"]), EN.num(q["seed_ari_mean"]), "adjusted Rand index"):
        assert expected in boxes, expected
    assert meta["state_id"] in " ".join(_texts(sentence))
    for word in ("stable", "unstable", "excellent", "strong", "weak"):
        assert word not in (text + boxes).lower().replace("membership stability", "")


def test_z_is_never_shown_without_the_excess_and_the_null_mean(build_folder):
    out = _recompute(build_folder)
    for component in (out[4], out[6]):
        for t in _texts(component):
            if re.search(r"\bz [-\d]", t):
                assert "excess" in t.lower() and "null" in t.lower(), t


def test_the_quality_sentence_appears_once_in_the_workbench(build_folder):
    out = _recompute(build_folder)
    ctx = load_build(build_folder)
    texts = " ".join(_texts(list(out[3:8])))  # legend, summary, sentence, quality tab, grids...
    rs = CB.show_rs(None, [], None, out[1], out[0])
    texts += " " + " ".join(_texts(list(rs)))
    assert texts.count("vs null") == 1 and texts.count("Seed-noise floor (K =") == 1


def test_the_network_state_sentence_names_every_setting(build_folder):
    out = _recompute(build_folder, **{"min-games": 9, "removed": [5001]})
    sentence = " ".join(_texts(out[5]))
    for expected in ("Overall", "≥ 0 months", "tags on ≥ 9 games", "links of ≥ 8 shared games", "Genre Tags hidden",
                     "tag 5001", "Louvain", "shared games", "γ 1.00", "seed"):
        assert expected in sentence, expected


def test_report_section_1_is_a_table_of_every_network_state_field_with_names(build_folder):
    from steamstudy.network.model import KEY_FIELDS

    out = _recompute(build_folder, dataset="puzzle", removed=[5001])
    meta, section = out[0], out[18]
    flat = json.dumps(section.to_plotly_json() if hasattr(section, "to_plotly_json") else
                      [s.to_plotly_json() for s in section], default=str)
    rows = [tr for tr in _walk(section) if getattr(tr, "id", None) and str(tr.id).startswith("state-row-")]
    assert {str(tr.id)[len("state-row-"):] for tr in rows} >= set(KEY_FIELDS) - {"build_id", "dataset"}
    assert "state-row-dataset" in flat and meta["state_id"] in flat and "copy-id" in flat
    hidden = next(tr for tr in rows if tr.id == "state-row-hidden_tag_ids")
    text = " ".join(_texts(hidden))
    assert "Puzzle" in text and "Strategy" in text  # names, from the Build's genre-tag list
    assert not re.search(r"\b(9|19|21|1664)\b", text.replace("hidden_tag_ids", ""))  # never bare ids
    removed = " ".join(_texts(next(tr for tr in rows if tr.id == "state-row-removed_tag_ids")))
    assert "tag 5001" in removed
    details = [d for d in _walk(section) if type(d).__name__ == "Details"]
    assert details and "Show JSON" in " ".join(_texts(details[0]))
    pre = " ".join(_texts(details[0]))
    assert '"hidden_tag_ids": [' in pre and "\n    9" not in pre  # one field per line, never one id per line


def _walk(component):
    if isinstance(component, (list, tuple)):
        for c in component:
            yield from _walk(c)
    elif component is not None and not isinstance(component, (str, int, float)):
        yield component
        yield from _walk(getattr(component, "children", None))


def test_cluster_separated_rows_are_packed_for_the_canvas_shape(build_folder):
    meta, tables, base, *_ = _recompute(build_folder, **{"min-games": 1, "min-shared": 1})

    def shape(payload):
        r = payload["regions"]
        w = max(x["x"] + x["w"] / 2 for x in r) - min(x["x"] - x["w"] / 2 for x in r)
        h = max(x["y"] + x["h"] / 2 for x in r) - min(x["y"] - x["h"] / 2 for x in r)
        return w / h

    tall = CB.render_graph(base, "separated", None, None, {"w": 500, "h": 900})
    wide = CB.render_graph(base, "separated", None, None, {"w": 1600, "h": 600})
    assert shape(tall) < shape(wide)
    reference = {"w": REFERENCE_CANVAS.width, "h": REFERENCE_CANVAS.height}
    assert CB.render_graph(base, "separated", None, None, None) == CB.render_graph(base, "separated", None, None, reference)


@pytest.mark.parametrize("canvas", [Canvas(956, 561), Canvas(1600, 1000)])
def test_the_graph_is_laid_out_for_the_canvas_the_browser_reports(build_folder, canvas):
    meta, tables, base, *_ = _recompute(build_folder)
    payload = CB.render_graph(base, "global", None, None, {"w": canvas.width, "h": canvas.height})
    ctx = load_build(build_folder)
    state = compute_state(ctx.games("overall"), ctx.default_settings("overall"), ctx.context("overall"))
    layout = layout_state(state, canvas)
    assert payload["positions"] == {str(t): pytest.approx(list(p), abs=1e-9) for t, p in layout.positions.items()}
    assert payload["zoom"] == layout.zoom
    names = state.network.tag_names
    assert {n["id"]: n["lw"] for n in payload["nodes"]} == {str(t): label_width(names[t]) for t in state.nodes}


def test_a_layout_already_made_for_these_inputs_is_not_computed_again(build_folder, monkeypatch):
    meta, tables, base, *_ = _recompute(build_folder)
    calls = []
    real = CB.lay_out
    monkeypatch.setattr(CB, "lay_out", lambda *a, **k: calls.append(1) or real(*a, **k))
    CB.LAYOUTS.clear()
    wide, narrow = {"w": 1116, "h": 678}, {"w": 957, "h": 538}
    first = CB.render_graph(base, "global", None, None, wide)
    CB.render_graph(base, "global", None, None, narrow)
    again = CB.render_graph(base, "global", None, None, wide)  # a panel opened and closed again
    assert len(calls) == 2 and again == first
    selected = CB.render_graph(base, "global", None, {"kind": "node", "id": base["nodes"][0]["id"]}, wide)
    assert len(calls) == 2 and selected["positions"] == first["positions"]  # the selection is not a layout input
    CB.render_graph(dict(base, seed=base["seed"] + 1), "global", None, None, wide)
    assert len(calls) == 3


def test_the_floating_inspector_is_a_transient_overlay_of_the_graph(build_folder):
    """It covers the graph only while a selection is shown, so it never changes the canvas the layout is made for."""
    from steamstudy.app.layout import build_layout

    inspector = next(c for c in _walk(build_layout(load_build(build_folder)))
                     if getattr(c, "id", None) == "inspector-panel")
    assert inspector.to_plotly_json()["props"].get("data-graph-transient") == "yes"


def test_the_inspector_never_needs_the_tables_sent_back_from_the_browser(build_folder):
    """Selecting is light: the request names the state, and the server finds its tables (or recomputes them)."""
    meta, tables, base, *_ = _recompute(build_folder)
    node = max(tables["nodes"], key=lambda r: r["degree"])
    selection = {"kind": "node", "id": str(node["tag_id"])}
    expected = CB.inspector(selection, tables, None, str(build_folder), "overall", 0, meta)
    as_json = lambda out: json.dumps([[b.to_plotly_json() for b in out[0]], out[1], out[2]], default=str)  # noqa: E731
    assert as_json(CB.inspect(selection, meta, None, str(build_folder), "overall", 0)) == as_json(expected)
    CB.STATE_TABLES.clear()  # the server restarted, or the state is old
    assert as_json(CB.inspect(selection, meta, None, str(build_folder), "overall", 0)) == as_json(expected)


def test_help_modal_follows_guide_links_with_a_back_stack():
    from steamstudy.app.guide import help_markdown_at

    q = "03-metric-reference.md#modularity-q"
    null = "03-metric-reference.md#null-model-baseline"

    triggered("help-target.data", {"target": q, "n": 1})  # a metric label opened from the app
    style, body, history, back = CB.show_help(None, None, {"target": q, "n": 1}, None, ["02-app-controls.md"])
    assert style["display"] == "flex" and body == help_markdown_at("en", "03-metric-reference.md", "modularity-q")
    assert history == [q] and back["display"] == "none"

    triggered("help-target.data", {"target": null, "n": 2, "follow": True})  # a link inside the modal
    style, body, history, back = CB.show_help(None, None, {"target": null, "n": 2, "follow": True}, None, history)
    assert body.startswith("### Null-model baseline") and history == [q, null] and back["display"] != "none"
    _, _, history, _ = CB.show_help(None, None, {"target": null, "n": 3, "follow": True}, None, history)
    assert history == [q, null]  # a link to the entry already shown adds no Back step

    triggered("help-back.n_clicks")
    style, body, history, back = CB.show_help(None, None, None, 1, history)
    assert body.startswith("### Modularity Q") and history == [q] and back["display"] == "none"

    triggered('{"panel":"controls","type":"help"}.n_clicks')  # a panel `?` starts afresh too
    style, body, history, back = CB.show_help([1], None, None, None, [q, null])
    assert body.startswith("## Control reference") and history == ["02-app-controls.md#control-reference"]

    triggered("help-close.n_clicks")
    style, body, history, back = CB.show_help([1], 1, None, None, history)
    assert style["display"] == "none" and history == []


def test_a_chapter_link_in_the_help_modal_opens_its_first_section():
    triggered("help-target.data", {"target": "05-citing-and-reproducing.md", "n": 3, "follow": True})
    _, body, history, _ = CB.show_help(None, None, {"target": "05-citing-and-reproducing.md", "n": 3, "follow": True},
                                       None, ["03-metric-reference.md#modularity-q"])
    assert body.startswith("# Citing and reproducing") and history[-1] == "05-citing-and-reproducing.md"


def _help_attrs(html_text: str) -> list[tuple[str, dict[str, str]]]:
    """(label, attributes) of every element with help in an escaped-HTML block."""
    import html as markup

    return [(markup.unescape(label), {k: markup.unescape(v) for k, v in re.findall(r'([\w-]+)="([^"]*)"', attrs)})
            for attrs, label in re.findall(r"<(?:dt|th) ([^>]*data-help[^>]*)>([^<]*)</(?:dt|th)>", html_text)]


def test_inspector_labels_show_their_in_short_and_open_their_guide_entry():
    from steamstudy.app import view as V

    block = V._kv([("Membership Stability", "0.95"), ("Links · in own cluster", "9 · 5")], EN)
    text = block.to_plotly_json()["props"]["data-html"]
    (first, a), (second, b) = _help_attrs(text)
    assert first == "Membership Stability" and a["data-help"] == "03-metric-reference.md#membership-stability"
    assert a["tabindex"] == "0" and "term" in a["class"] and "title" not in a
    lines = _tip(a["data-tip"]).split("\n")
    assert lines[0].startswith("In short. ") and lines[-1] == "Column: membership_stability (nodes.csv)"
    assert _tip(b["data-tip"]).split("\n")[-1] == "Columns: degree, degree_intra (nodes.csv)"
    assert b["data-help"] == "03-metric-reference.md#degree-and-isolated-tags"


def test_inspector_table_headers_carry_the_help_of_their_label():
    from steamstudy.app import view as V

    cluster = {"cluster": "C1", "size": 3, "kind": "multi_tag", "connected": True, "center": "A", "center_status": None,
               "center_medoid_score": 0.2, "top_strength_tag": "A", "center_is_top_strength": True,
               "mean_membership_stability": 1.0, "conductance": 0.1, "conductance_status": None}
    members = [{"tag": "A", "is_center": True, "n_games": 9, "medoid_score": 0.2, "membership_stability": 1.0}]
    text = "".join(c.to_plotly_json()["props"].get("data-html", "")
                   for c in V.cluster_inspector(cluster, members, "shared_games", tx=EN))
    labels = [label for label, _ in _help_attrs(text)]
    assert {"Games", "Mean game-set distance to members", "Membership Stability", "Cluster Center"} <= set(labels)
    assert "title=" not in text


def test_quality_boxes_and_sentences_show_the_guide_text_with_now_lines(build_folder):
    out = _recompute(build_folder)
    ctx = load_build(build_folder)
    s = ctx.default_settings("overall")
    boxes, sentences = out[6][0].children, out[6][1].children
    props = [b.to_plotly_json()["props"] for b in [*boxes, *sentences]]
    assert [p["data-help"].split("#")[1] for p in props] == [
        "modularity-q", "excess-modularity-and-z-score", "coverage-and-inter-cluster-weight-share", "mean-silhouette",
        "adjusted-rand-index", "clusters-and-partition-quality", "stability"]
    assert all(_tip(p["data-tip"]).startswith("In short. ") and "title" not in p for p in props)
    now = {p["data-help"].split("#")[1]: _tip(p["data-tip"]).split("Now: ")[-1] for p in props
           if "Now: " in _tip(p["data-tip"])}
    assert "γ = 1.00" in now["modularity-q"] and f"R = {s.null_replicates}" in now["excess-modularity-and-z-score"]
    assert f"K = {s.noise_seeds}" in now["adjusted-rand-index"]


def _grids(build_folder) -> list:
    from dash_ag_grid import AgGrid

    from steamstudy.app.layout import build_layout

    return [c for c in _walk(build_layout(load_build(build_folder))) if isinstance(c, AgGrid)]


def test_every_grid_metric_header_shows_its_in_short_and_has_an_info_mark(build_folder):
    from steamstudy.app.guide import chapter, section

    grids = _grids(build_folder)
    assert {g.id for g in grids} >= {"clusters-grid", "rs-grid", "nodes-grid", "edges-grid", "nin-grid"}
    metric, info = 0, set()
    for grid in grids:
        for d in grid.columnDefs:
            tip = d["headerTooltip"]
            if "headerComponentParams" not in d:  # an identifier or row label: the schema description
                assert not tip.startswith("In short."), (grid.id, d["field"])
                continue
            metric += 1
            info.add((grid.id, d["field"]))
            lines = tip.split("\n")
            assert lines[0].startswith("In short. ") and lines[-1].startswith("Column: "), (grid.id, d["field"])
            assert d["field"] in lines[-1], (grid.id, d["field"])
            params = d["headerComponentParams"]
            assert params["innerHeaderComponent"] == "MetricHeader"
            assert _tip(params["innerHeaderComponentParams"]["tip"]) == tip
            file, anchor = params["innerHeaderComponentParams"]["help"].split("#")
            assert "*Why it matters here.*" in section(chapter("en", file), anchor), (grid.id, d["field"])
    assert metric > 60
    assert {("nodes-grid", "n_games"), ("edges-grid", "lift"), ("clusters-grid", "conductance"), ("rs-grid", "rc_ari"),
            ("rs-grid", "run_order"), ("nin-grid", "reasons"), ("seed-grid", "ari_vs_main")} <= info
    assert not info & {("nodes-grid", "tag_id"), ("edges-grid", "source_cluster"), ("edges-grid", "is_intra_cluster"),
                       ("null-grid", "seed"), ("null-grid", "replicate"), ("seed-grid", "noise_seed_index"),
                       ("connections-grid", "cluster_a"), ("clusters-grid", "center_tag_id"),
                       ("rs-grid", "rc_centers_lost_tag_ids")}


def test_the_joined_membership_stability_column_has_the_same_help(build_folder):
    rs = next(g for g in _grids(build_folder) if g.id == "rs-grid")
    joined = next(d for d in rs.columnDefs if d["headerName"] == "membership_stability (joined)")
    assert joined["headerComponentParams"]["innerHeaderComponentParams"]["help"].endswith("#membership-stability")
    assert joined["headerTooltip"].startswith("In short. ")


def test_only_controls_that_need_interpretation_carry_help(build_folder):
    """Controls whose effect needs interpretation carry both help layers on their label and pill; self-explanatory
    ones (the two thresholds, hiding and removing tags, the layout switch, Tidy) carry none."""
    from steamstudy.app.help import HELP
    from steamstudy.app.layout import build_layout

    components = list(_walk(build_layout(load_build(build_folder))))
    helps = {getattr(c, "data-help", None) for c in components}
    controls = {f"{file}#{anchor}" for key, (file, anchor) in HELP.items() if key.startswith("control.")}
    assert controls <= helps and {anchor.split("#")[1] for anchor in controls} == {
        "minimum-months-filter", "clustering-weight", "clustering-algorithm", "resolution-γ", "seed"}
    pills = {getattr(c, "data-pill"): getattr(c, "data-tip", None) for c in components
             if getattr(c, "className", None) == "pill-btn"}
    for pill in ("min-months", "weight", "algorithm", "gamma", "seed"):
        assert _tip(pills[pill]).startswith("In short. "), pill
    for pill in ("min-games", "min-shared", "hidden", "dataset", "state"):
        assert pills[pill] is None, pill
    for anchor in ("minimum-games-per-tag", "minimum-shared-games", "hidden-genre-tags", "hide-defining-tag",
                   "remove--restore", "global--cluster-separated", "tidy"):
        assert f"02-app-controls.md#{anchor}" not in helps, anchor
    assert not any("hinfo" in str(getattr(c, "className", "")) for c in components)  # ⓘ only in grid headers
    tidy = next(c for c in components if getattr(c, "id", None) == "relayout-btn")
    assert tidy.title and not getattr(tidy, "data-tip", None)
    assert not any(getattr(c, "title", None) == "0.1–3.0" for c in components)  # the range is in the entry now


def _help_targets(tree) -> list[str]:
    """Every guide entry a component tree opens: data-help attributes, escaped-HTML blocks and grid headers."""
    import html as markup

    out = []
    for c in _walk(tree):
        if getattr(c, "data-help", None):
            out.append(getattr(c, "data-help"))
        out += [markup.unescape(t) for t in re.findall(r'data-help="([^"]+)"', getattr(c, "data-html", None) or "")]
        for d in getattr(c, "columnDefs", None) or []:
            params = d.get("headerComponentParams", {}).get("innerHeaderComponentParams", {})
            if params.get("help"):
                out.append(params["help"])
        if getattr(c, "id", None) == "ui-words":  # the Edge appearance card's controls (graph.js renderCard)
            out += [h["help"] for h in c.data["edges"]["help"].values()]
    return out


def test_the_legend_has_a_key_and_the_one_tag_chip_explains_itself(build_folder):
    out = _recompute(build_folder, **{"min-shared": 20})
    legend = out[3]
    key, *chips = legend
    assert getattr(key, "data-help") == "02-app-controls.md#reading-the-graph"
    assert _tip(getattr(key, "data-tip")).startswith("In short. ")
    clusters = [c for c in chips if isinstance(getattr(c, "id", None), dict)]
    assert clusters and all(c.title == "Select this cluster" and not getattr(c, "data-help", None) for c in clusters)
    one_tag = next(c for c in chips if "one-tag" in " ".join(_texts(c)))
    assert getattr(one_tag, "data-help") == "02-app-controls.md#grey-one-tag-clusters"


@pytest.mark.parametrize("layout_mode", ["global", "separated"])
@pytest.mark.parametrize("weight", ["shared_games", "lift"])
def test_every_edge_carries_its_raw_values_for_the_browser_to_draw(build_folder, layout_mode, weight):
    """Edge Appearance (issue 15): no width leaves Python. graph.js draws the Clustering Weight's measure (or shared
    games, when the legend's switch asks under lift) from these values, with renderer.py's defaults."""
    from steamstudy.app.renderer import APPEARANCE

    base = _recompute(build_folder, weight=weight)[2]
    payload = CB.render_graph(base, layout_mode, None, None)
    assert payload["weight"] == weight and payload["appearance"] == APPEARANCE
    raw = {f"{e['source']}-{e['target']}": (e["shared"], e["lift"], e["intra"]) for e in base["edges"]}
    assert {e["id"]: (e["shared"], e["lift"], e["intra"]) for e in payload["edges"]} == raw
    assert not any("width" in e for e in payload["edges"])
    assert APPEARANCE["defaults"] == {"width": [0.4, 3.0], "scale": "linear", "color": "one", "strength": 0.18,
                                      "between": 0.06}


@pytest.mark.parametrize("weight, switch, label, switch_shown", [
    ("shared_games", [], "Edge thickness: shared games", False),
    ("shared_games", [1], "Edge thickness: shared games", False),
    ("lift", [], "Edge thickness: lift", True),
    ("lift", [1], "Edge thickness: shared games", True)])
def test_the_legend_names_what_edge_thickness_shows(weight, switch, label, switch_shown):
    """The switch to shared-game thickness is offered only while the clustering runs on lift; the key's first words
    (renderer.thickness_key) are the ones graph.js `edgeKey` writes when the switch is toggled."""
    from steamstudy.app.renderer import thickness_key

    assert thickness_key(weight, bool(switch), EN)[0] == label
    assert (CB.thickness_legend({"weight": weight}).get("display") != "none") == switch_shown


def test_the_edge_thickness_key_sits_in_the_legend_overlay_and_explains_itself(build_folder):
    from steamstudy.app.layout import build_layout
    from steamstudy.app.server import create_app

    page = list(_walk(build_layout(load_build(build_folder))))
    overlay = next(c for c in page if getattr(c, "data-graph-overlay", None) == "bottom")
    ids = {getattr(c, "id", None) for c in _walk(overlay)}
    assert {"legend", "thickness-label", "edge-card-toggle"} <= ids
    card = next(c for c in page if getattr(c, "id", None) == "edge-card")  # the switch is in the card's header
    assert getattr(card, "data-graph-transient") == "yes" and getattr(card, "data-graph-overlay") == "bottom"
    assert "thickness-shared" in {getattr(c, "id", None) for c in _walk(card)}
    label = next(c for c in _walk(overlay) if getattr(c, "id", None) == "thickness-label")
    assert getattr(label, "data-help") == "02-app-controls.md#edge-appearance"
    deps = create_app(build_folder).server.test_client().get("/_dash-dependencies").get_json()
    drawing = next(d for d in deps if d["output"] == "graph-data.data" and "elements-base" in [i["id"] for i in d["inputs"]])
    assert "thickness-shared" not in [i["id"] for i in drawing["inputs"]]  # the switch never re-sends the graph
    key = next(d for d in deps if "thickness-label.children" in d["output"])
    assert key.get("clientside_function", {}).get("function_name") == "edgeKey"  # no request on a toggle
    assert {"elements-base", "thickness-shared"} <= {i["id"] for i in key["inputs"]}  # named for the state drawn
    assert "weight" not in [i["id"] for i in key["inputs"]]


def test_a_new_clustering_weight_starts_on_its_own_thickness(build_folder):
    """A tick on the switch never carries over: switching weight unticks it, so Lift always starts on lift."""
    from steamstudy.app.server import create_app

    deps = create_app(build_folder).server.test_client().get("/_dash-dependencies").get_json()
    reset = next(d for d in deps if d["output"] == "thickness-shared.value")
    assert [i["id"] for i in reset["inputs"]] == ["weight"] and CB.untick_thickness("lift") == []


def test_the_dataset_summary_explains_each_analytical_field(build_folder):
    from steamstudy.app import view as V

    ctx = load_build(build_folder)
    s = ctx.default_settings("overall")
    rows = {tr.id: tr for tr in _walk(V.state_table(s.key(), "abc", "Overall", 100, 100, {}, tx=EN))
            if str(getattr(tr, "id", "")).startswith("state-row-")}
    th = {field[len("state-row-"):]: tr.children[0] for field, tr in rows.items()}
    assert getattr(th["min_months"], "data-help") == "02-app-controls.md#minimum-months-filter"
    assert getattr(th["resolution"], "data-help") == "02-app-controls.md#resolution-γ"
    assert getattr(th["null_replicates"], "data-help") == "03-metric-reference.md#null-model-baseline"
    assert _tip(getattr(th["min_months"], "data-tip")).split("\n")[-1] == "Field: min_months"
    assert not _tip(getattr(th["n_games"], "data-tip")).split("\n")[-1].startswith("Field:")  # derived, not a key field
    assert not getattr(th["dataset"], "data-help", None) and not getattr(th["key_version"], "data-help", None)
    for field in ("min_games_per_tag", "min_shared_games", "hidden_tag_ids", "removed_tag_ids"):
        assert not getattr(th[field], "data-help", None) and th[field].title, field


def test_every_help_target_in_the_app_opens_an_entry_with_in_short_and_why_it_matters(build_folder):
    """The coverage test: every element of the app that has help, on every surface, and every help key."""
    from steamstudy.app import help as H
    from steamstudy.app import view as V
    from steamstudy.app.guide import chapter, in_short_at, section
    from steamstudy.app.layout import build_layout

    out = _recompute(build_folder, **{"min-shared": 20})
    targets = _help_targets([build_layout(load_build(build_folder)), list(out),
                             V._kv([(label, "x") for label in V.INSPECTOR_LABELS], EN)])
    # every help key is on a surface of the app (Parameter Selection's: test_ps_app)
    assert {H.target(key) for key in H.HELP if key not in H.SELECTION_HELP} <= set(targets)
    assert {H.column_help(columns, EN)[1] for columns in V.INSPECTOR_LABELS.values()} <= set(targets)
    for target in set(targets):
        file, anchor = target.split("#")
        assert in_short_at("en", file, anchor), target
        assert "*Why it matters here.*" in section(chapter("en", file), anchor), target


def test_the_help_modal_keeps_back_and_close_outside_the_scrolling_content(build_folder):
    """Long entries scroll inside the modal; ← Back and × stay in a header that does not scroll."""
    from steamstudy.app.layout import build_layout

    modal = next(c for c in _walk(build_layout(load_build(build_folder))) if getattr(c, "id", None) == "help-modal")
    head, scroll = modal.children
    assert head.className == "help-head" and scroll.className == "help-scroll"
    assert {getattr(c, "id", None) for c in _walk(head)} >= {"help-back", "help-close"}
    assert [c.id for c in _walk(scroll) if getattr(c, "id", None)] == ["help-body"]
    triggered('{"panel":"controls","type":"help"}.n_clicks')
    style, *_ = CB.show_help([1], None, None, None, [])
    assert style["display"] == "flex"


def test_the_graph_says_what_it_is_computing_while_a_setting_takes_effect(build_folder):
    """A clustering change recomputes the Network State, then lays it out; a layout switch (Global or
    Cluster-separated), Tidy or a canvas resize only lays out. While each runs, its status chip over the graph is
    shown (Dash's `running`), and hidden again when it ends, whatever the outcome."""
    from steamstudy.app.server import create_app

    deps = create_app(build_folder).server.test_client().get("/_dash-dependencies").get_json()  # what the browser reads
    clustering = next(d for d in deps if "state-meta.data" in d["output"])
    laying_out = next(d for d in deps if d["output"] == "graph-data.data"
                      and "elements-base" in [i["id"] for i in d["inputs"]])
    assert clustering["running"] == {"running": {"busy-clustering.hidden": False},
                                     "runningOff": {"busy-clustering.hidden": True}}
    tidying = next(d for d in deps if "relayout.data" in d["output"]
                   and "relayout-btn" in [i["id"] for i in d["inputs"]])
    for spec in (laying_out, tidying):
        assert spec["running"] == {"running": {"busy-layout.hidden": False}, "runningOff": {"busy-layout.hidden": True}}


def test_the_busy_chips_sit_over_the_graph_without_changing_its_canvas(build_folder):
    """They are announced to screen readers (a status role is a polite live region), hidden at first, and never a
    graph overlay (graph.js would shrink the canvas the layout is made for, and so lay it out again)."""
    from steamstudy.app.layout import build_layout

    page = list(_walk(build_layout(load_build(build_folder))))
    stage = next(c for c in page if getattr(c, "className", None) == "graph-stage")
    busy = next(c for c in _walk(stage) if "graph-busy" in str(getattr(c, "className", "")).split())
    props = busy.to_plotly_json()["props"]
    assert props.get("role") == "status"
    assert "data-graph-overlay" not in props
    chips = {c.id: c for c in busy.children}
    assert set(chips) == {"busy-clustering", "busy-layout"}
    assert all(c.hidden is True for c in chips.values())


def test_the_inspector_says_it_is_loading_while_a_selection_or_its_content_is_on_its_way(build_folder):
    """Switching cluster (legend, Clusters table, a region title) asks the server for the selection, then for the
    Inspector's content; while each runs, its label in the Inspector's status chip is shown (app.css fades the old
    content only while the content is on its way)."""
    from steamstudy.app.server import create_app

    deps = create_app(build_folder).server.test_client().get("/_dash-dependencies").get_json()
    selecting = next(d for d in deps if "selection.data" in d["output"] and "floating-open.data" in d["output"])
    inspecting = next(d for d in deps if "inspector-body.children" in d["output"])
    for spec, chip in ((selecting, "busy-selecting"), (inspecting, "busy-inspector")):
        assert spec["running"] == {"running": {f"{chip}.hidden": False}, "runningOff": {f"{chip}.hidden": True}}


def test_the_inspector_busy_chip_sits_in_its_title_bar(build_folder):
    from steamstudy.app.layout import build_layout

    page = list(_walk(build_layout(load_build(build_folder))))
    title = next(c for c in page if getattr(c, "className", None) == "insp-title")
    busy = next(c for c in _walk(title) if "busy" in str(getattr(c, "className", "")).split())
    assert busy.to_plotly_json()["props"].get("role") == "status"
    assert [(c.id, c.hidden) for c in busy.children] == [("busy-selecting", True), ("busy-inspector", True)]


@pytest.mark.parametrize("gamma", [1.09, 3.23, 0.01, 7.5])
def test_the_gamma_input_takes_any_two_decimal_value_from_0_01(build_folder, gamma):
    from dash.exceptions import PreventUpdate

    from steamstudy.app.layout import build_layout

    gamma_input = next(c for c in _walk(build_layout(load_build(build_folder))) if getattr(c, "id", None) == "gamma")
    assert (gamma_input.min, gamma_input.step, getattr(gamma_input, "max", None)) == (0.01, 0.01, None)
    meta, *_ = _recompute(build_folder, gamma=gamma)
    assert meta["gamma"] == f"{gamma:.2f}" and meta["key"]["resolution"] == f"{gamma:.2f}"
    with pytest.raises(PreventUpdate):
        _recompute(build_folder, gamma=0.0)
