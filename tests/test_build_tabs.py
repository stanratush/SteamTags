"""Issue 27: each tab names its Build in the URL, `/build/<source_id>/<build_id>` (ADR 0006)."""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

import pytest
from dash import no_update
from dash.exceptions import PreventUpdate

from dash_http import client_page, layout_props, start_path
from steamstudy.app import callbacks as CB
from steamstudy.app import pending
from steamstudy.app.loader import load_build

B_ID = "20261006T000000Z-abcdef12"


@pytest.fixture(scope="module")
def tabs(tagged_build, tmp_path_factory):
    """Two Builds on two sources (B a copy of A under another id) and the app started on A."""
    from steamstudy.app.server import create_app

    root = tmp_path_factory.mktemp("tabs") / "builds"
    a = root / "S1" / tagged_build.name
    b = root / "S2" / B_ID
    skip = shutil.ignore_patterns("app_cache")
    shutil.copytree(tagged_build, a, ignore=skip)
    shutil.copytree(tagged_build, b, ignore=skip)
    bj = b / "datasets" / "build.json"
    data = json.loads(bj.read_text(encoding="utf-8"))
    data["build_id"] = B_ID
    bj.write_text(json.dumps(data, indent=2), encoding="utf-8")
    app = create_app(a)
    return app, a, b


def _page(app, path: str, search: str = "") -> dict:
    return layout_props(client_page(app.server.test_client(), path, search))


def test_slash_opens_the_startup_build(tabs):
    app, a, _ = tabs
    assert start_path(app.server.test_client()) == f"/build/S1/{a.name}"


def test_two_tabs_on_two_builds_keep_their_own_dataset_header_and_selection_keys(tabs, monkeypatch):
    app, a, b = tabs
    pa = _page(app, f"/build/S1/{a.name}", "?dataset=puzzle&mode=report")
    pb = _page(app, f"/build/S2/{B_ID}")
    assert pa["build-path"]["data"] == f"S1/{a.name}" and pb["build-path"]["data"] == f"S2/{B_ID}"
    assert pa["dataset"]["value"] == "puzzle" and pb["dataset"]["value"] == "overall"
    assert pa["mode"]["value"] == "report" and pb["mode"]["value"] == "workbench"
    assert pa["brand-build"]["children"] == f"Build {a.name}" and pb["brand-build"]["children"] == f"Build {B_ID}"
    assert B_ID in json.dumps(pb["ps-active"]["data"]) and B_ID not in json.dumps(pa["ps-active"]["data"])
    # A language switch in B's tab relabels the header from B, though A's page filled the registry first.
    set_ = {}
    monkeypatch.setattr(CB, "set_props", lambda id_, props: set_.setdefault(str(id_), {}).update(props))
    CB.relabel("bg", f"S2/{B_ID}")
    assert B_ID in set_["brand-build"]["children"]
    # A key unknown to the Build falls back to its first dataset.
    assert _page(app, f"/build/S2/{B_ID}", "?dataset=nonesuch")["dataset"]["value"] == "overall"


def test_the_server_resolves_ids_and_never_takes_a_path_from_the_browser(tabs):
    app, a, _ = tabs
    with app.server.test_request_context("/_dash-update-component"):
        assert load_build(f"S1/{a.name}").path == a
        for value in (str(a), "S1/../S1", "..\\builds"):
            with pytest.raises(FileNotFoundError):
                load_build(value)
    assert "missing-build" in _page(app, "/build/S1/..%2F..%2Fetc")


def test_open_with_another_builds_export_navigates_there_and_reopens_it(tabs):
    from steamstudy.app.export import export_zip

    app, a, b = tabs
    ctx_b = load_build(b)
    settings = ctx_b.default_settings("puzzle").with_(min_games_per_tag=9, seed=7)
    _, data = export_zip(ctx_b, settings)
    contents = "data:application/zip;base64," + base64.b64encode(data).decode("ascii")
    out = CB.do_open(contents, "b.zip", f"S1/{a.name}", "en", "report")
    url = out[0]
    assert url.startswith(f"/build/S2/{B_ID}?") and "mode=report" in url and "dataset=puzzle" in url
    assert all(v is no_update for v in out[1:-1])  # A's page is left as it is
    path, _, search = url.partition("?")
    page = _page(app, path, "?" + search)
    token = page["open-token"]["data"]
    assert page["build-path"]["data"] == f"S2/{B_ID}" and page["dataset"]["value"] == "puzzle"
    reopened, filename = CB.reopen(token)
    assert filename == "b.zip"
    with pytest.raises(PreventUpdate):
        CB.reopen(token)  # taken once
    values = dict(zip(["switch-to", *CB.CONTROL_IDS], CB.do_open(reopened, filename, f"S2/{B_ID}")))
    assert values["switch-to"] is no_update  # already on its Build: applied in place
    assert values["dataset"] == "puzzle" and values["min-games"] == 9 and values["seed"] == 7


def test_running_jobs_are_counted_by_their_cancel_buttons(tabs):
    """The switch's confirmation counts this tab's running jobs by their enabled Cancel buttons (workbench.js
    `runningJobs`), so both start disabled and only a running job enables its own."""
    app, a, _ = tabs
    page = _page(app, f"/build/S1/{a.name}")
    assert page["rs-cancel"]["disabled"] is True and page["ps-cancel"]["disabled"] is True
    js = (Path(CB.__file__).parent / "assets" / "workbench.js").read_text(encoding="utf-8")
    assert '["rs-cancel", "ps-cancel"]' in js and "switchBuild" in js
    deps = app.server.test_client().get("/_dash-dependencies").get_json()
    cancels = {c["id"] for d in deps for c in d.get("inputs", []) if c["id"] in ("rs-cancel", "ps-cancel")}
    assert cancels == {"rs-cancel", "ps-cancel"}


def test_a_deleted_builds_url_shows_the_notice_and_the_job_store_is_outside_every_build(tabs, tmp_path):
    app, a, b = tabs
    store = pending._STORE
    assert store is not None and a.parents[1] not in store.parents
    gone = a.parents[1] / "S3" / "20261007T000000Z-abcdef12"
    shutil.copytree(b, gone)
    assert "missing-build" not in _page(app, "/build/S3/20261007T000000Z-abcdef12")
    shutil.rmtree(gone)  # while the app runs: nothing of the app holds it open
    page = client_page(app.server.test_client(), "/build/S3/20261007T000000Z-abcdef12")
    assert "This Build no longer exists" in json.dumps(page)
    assert f"/build/S1/{a.name}" in json.dumps(page)  # the link to the latest (here the startup) Build
