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
    page = client.get("/")
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


def test_relayout_is_recorded_and_dropped_when_the_basis_changes(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    relayout_store = CB.do_relayout(1, base, None)
    positions, used = CB.current_global_positions(base, relayout_store)
    assert used
    sent = CB.do_export(1, None, str(build_folder), meta, relayout_store, base, None)
    export = read_export(base64.b64decode(sent["content"]))[0]
    assert export["layout_source"] == "relayout"
    other = dict(base, basis=[*base["basis"][:3], base["basis"][3] + 1])
    assert CB.current_global_positions(other, relayout_store)[1] is False


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
    assert message.startswith("Cleared 1") and cleared is None
    assert CB.refresh_rs_view(meta, None, None, str(build_folder))["rows"] == []


def test_open_restores_every_control(build_folder):
    ctx = load_build(build_folder)
    settings = ctx.default_settings("puzzle").with_(min_games_per_tag=9, removed_tag_ids=(5001,), algorithm="leiden",
                                                    resolution=0.85, seed=7, hidden_tag_ids=(9, 19))
    from steamstudy.app.export import export_zip

    _, data = export_zip(ctx, settings)
    contents = "data:application/zip;base64," + base64.b64encode(data).decode("ascii")
    out = CB.do_open(contents, "x.zip", None)
    values = dict(zip(["build-path", *CB.CONTROL_IDS, "removed", "relayout", "rs-view", "pending", "verify", "msg"], out))
    assert values["dataset"] == "puzzle" and values["min-games"] == 9 and values["algorithm"] == "leiden"
    assert values["gamma"] == 0.85 and values["seed"] == 7 and values["removed"] == [5001]
    assert values["genre-hidden"] == [9, 19] and values["defining-hidden"] == []
    assert values["verify"] == {"expected": read_export(data)[0]["state_id"]}
    refused = CB.do_open("data:x;base64," + base64.b64encode(b"not an export").decode("ascii"), "y.json", None)
    assert refused[-1].startswith("Refused")


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
    out = CB.arrange("workbench", "quality", ["controls", "tables"], True, sel, False)
    assert out[-2] == "inspector has-sel" and out[-1] == "workbench controls-on tables-on"
    out = CB.arrange("workbench", "quality", ["controls", "inspector", "tables"], True, sel, True)
    assert out[-2] == "inspector docked has-sel" and out[-1].endswith("tables-on graph-only")
    assert CB.arrange("report", "quality", [], False, None, False)[-2:] == ["inspector", "report"]


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
    assert sizes == {str(t): state.sizes[t] for t in state.nodes}  # fixed by the layout, not by the visible set


@pytest.mark.parametrize("layout_mode", ["global", "separated"])
def test_priority_labels_are_centers_the_15_largest_and_in_regions_each_clusters_largest(build_folder, layout_mode):
    meta, tables, base, *_ = _recompute(build_folder, **{"min-games": 1, "min-shared": 1})
    payload = CB.render_graph(base, layout_mode, None, None)
    by_id = {n["id"]: n for n in base["nodes"]}
    ranked = sorted(base["nodes"], key=lambda n: (-n["n_games"], int(n["id"])))
    expected = {n["id"] for n in ranked[:15]} | {n["id"] for n in base["nodes"] if n["center"]}
    if layout_mode == "separated":
        for cluster in {n["cluster"] for n in base["nodes"]}:
            expected.add(next(n["id"] for n in ranked if n["cluster"] == cluster))
    priority = [n for n in payload["nodes"] if "pri" in n["classes"].split()]
    assert {n["id"] for n in priority} == expected and len(base["nodes"]) > len(expected)
    order = [n["id"] for n in sorted(priority, key=lambda n: n["prio"])]  # culling rank: Centers, then n_games
    centers = [i for i in order if by_id[i]["center"]]
    assert order[:len(centers)] == centers
    rest = order[len(centers):]
    assert rest == sorted(rest, key=lambda i: (-by_id[i]["n_games"], int(i)))
    assert all(n["prio"] is None for n in payload["nodes"] if "pri" not in n["classes"].split())


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

    options = V.search_options(tables, meta["key"]["min_games_per_tag"])
    values = _search_values(options)
    nodes = [f"node:{r['tag_id']}" for r in tables["nodes"]]
    missing = [f"nin:{r['tag_id']}" for r in tables["nin"]]
    assert set(values) == set(nodes) | set(missing) and len(values) == len(nodes) + len(missing)
    assert max(values.index(v) for v in nodes) < min(values.index(v) for v in missing)  # visible tags first
    text = {o["value"]: o["search"] + " " + json.dumps(o["label"].to_plotly_json(), default=str) for o in options
            if not o.get("disabled")}
    for r in tables["nin"]:
        for reason in r["reasons"]:
            assert V.reason_text(reason, r["n_games"], meta["key"]["min_games_per_tag"]) in text[f"nin:{r['tag_id']}"]
    assert V.reason_text("below_min_games", 3, 8) == "3 games, below 8"
    assert V.reason_text("genre_tag_hidden", 0, 8) == "Genre Tag hidden"
    assert V.reason_text("defining_tag_hidden", 0, 8) == "defining tag hidden"
    assert V.reason_text("removed", 0, 8) == "removed"


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


def test_the_tag_view_lists_its_games_then_its_connected_tags_then_the_metrics(build_folder):
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
    assert lead in text and text.index(lead) < text.index("Connected tags") < text.index("Metrics")
    assert body[2].children[0].children == str(node["n_games"])  # the bold count of the lead sentence
    assert "used for clustering" in text and "descriptive" in text and "hub" not in text.lower()
    rows = [b for b in body if getattr(b, "id", None) is None]
    assert any(f"Show all {node['n_games']}" in json.dumps(b.to_plotly_json(), default=str) for b in rows) == \
           (node["n_games"] > 10)


def test_a_connected_tag_row_selects_its_edge_and_pans_to_it():
    triggered('{"edge":"5000-5001","type":"conn"}.n_clicks', 1)
    sel, _ = CB.select(None, [], None, None, None, [], None, [1])
    assert sel == {"kind": "edge", "id": "5000-5001", "source": "5000", "target": "5001", "pan": True}
