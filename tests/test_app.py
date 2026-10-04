"""Seam 4 (UI side): the served page, and the app's callbacks called as plain functions."""

from __future__ import annotations

import base64
import io
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


def test_layout_switch_keeps_the_partition_and_export_has_both_coordinate_sets(build_folder):
    meta, tables, base, *_ = _recompute(build_folder)
    global_els = CB.render_graph(base, "global", None, None)
    separated = CB.render_graph(base, "separated", None, None)
    clusters = lambda els: {e["data"]["id"]: e["data"]["cluster"] for e in els if "source" not in e["data"]
                            and not e["data"]["id"].startswith("region-")}
    assert clusters(global_els) == clusters(separated)
    assert any(e["data"]["id"].startswith("region-") for e in separated)
    assert {e["data"]["id"]: e["position"] for e in global_els if "position" in e} != \
           {e["data"]["id"]: e["position"] for e in separated if "position" in e}
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
