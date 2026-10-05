"""Seam 1: Collect, through the Fetcher and its fixture-backed fake transport."""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import sqlite3

import pytest

from conftest import neutral_collection
from helpers import appdetails, captured, raw, steamcharts_page, store_page, top_page
from steamstudy.collect.fetcher import (
    FakeClock,
    FakeTransport,
    Fetcher,
    HardStop,
    RawResponse,
    SourcePolicy,
    TransportError,
)
from steamstudy.collect.run import CollectRefused, age_check_cookie, run_collect
from steamstudy.config import load_config
from steamstudy.snapshot import Snapshot, SnapshotStore

SC = "https://steamcharts.com"
STORE = "https://store.steampowered.com"
TODAY = dt.date(2026, 10, 4)


@pytest.fixture
def config(config_dir):
    return neutral_collection(load_config(config_dir))


_OPEN_STORES: list[SnapshotStore] = []


@pytest.fixture(autouse=True)
def _close_stores():
    yield
    while _OPEN_STORES:
        _OPEN_STORES.pop().close()


def _fetcher(tmp_path, routes, clock=None, **kw):
    clock = clock or FakeClock()
    transport = FakeTransport(routes, clock)
    store = SnapshotStore(tmp_path / "snap")
    _OPEN_STORES.append(store)
    policies = {
        "steamcharts": SourcePolicy("steamcharts", 1 / 3),
        "store": SourcePolicy("store", 2.0, "birthtime=1"),
        "steamdb": SourcePolicy("steamdb", 2.0),
    }
    return Fetcher(store, transport, policies, "ua (contact)", clock=clock, **kw), transport, clock


OK_APP = RawResponse(200, f"{SC}/app/1", raw("steamcharts/app/698670.html.gz"))


# ----------------------------------------------------------------------------- Fetcher


def test_rate_spacing_per_source_and_one_connection_per_source(tmp_path):
    routes = {f"{SC}/app/{i}": OK_APP for i in range(4)}
    routes |= {f"{STORE}/api/appdetails?appids={i}&l=english": RawResponse(200, "x", appdetails(i)) for i in range(3)}
    fetcher, transport, _ = _fetcher(tmp_path, routes)
    for i in range(3):
        fetcher.fetch(f"store/appdetails/{i}.json.gz", f"{STORE}/api/appdetails?appids={i}&l=english")
        fetcher.fetch(f"steamcharts/app/{i}.html.gz", f"{SC}/app/{i}")
    times = {s: [c.at for c in transport.calls if c.source == s] for s in ("steamcharts", "store")}
    assert all(b - a >= 1 / 3 - 1e-9 for a, b in zip(times["steamcharts"], times["steamcharts"][1:]))
    assert all(b - a >= 2.0 - 1e-9 for a, b in zip(times["store"], times["store"][1:]))
    assert transport.sessions == {"steamcharts", "store"}
    assert all(c.headers["User-Agent"] == "ua (contact)" for c in transport.calls)
    assert all("Cookie" in c.headers for c in transport.calls if c.source == "store")


@pytest.mark.parametrize("status", [403, 429, 503])
def test_hard_stop_statuses_save_log_and_never_retry(tmp_path, status):
    fetcher, transport, clock = _fetcher(tmp_path, {f"{SC}/app/1": RawResponse(status, f"{SC}/app/1", b"denied")})
    with pytest.raises(HardStop, match=str(status)):
        fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1")
    assert len(transport.calls) == 1 and clock.sleeps == []
    assert fetcher.store.latest("steamcharts/app/1.html.gz").outcome == "hard_stop"
    assert fetcher.store.read_archive("steamcharts/app/1.html.gz") == b"denied"


@pytest.mark.parametrize(
    "body",
    [
        b"<html><head><title>Just a moment...</title></head><body>challenge-platform</body></html>",
        b"<html><body>a page without the expected structure</body></html>",
    ],
    ids=["cloudflare", "structure-marker-missing"],
)
def test_challenge_pages_hard_stop(tmp_path, body):
    fetcher, transport, _ = _fetcher(tmp_path, {f"{SC}/app/1": RawResponse(200, f"{SC}/app/1", body)})
    with pytest.raises(HardStop):
        fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1")
    assert len(transport.calls) == 1


def test_retry_schedule_then_hard_stop(tmp_path):
    errors = [TransportError("timeout"), RawResponse(502, "x", b""), TransportError("connection"),
              TransportError("timeout")]
    fetcher, transport, clock = _fetcher(tmp_path, {f"{SC}/app/1": errors})
    with pytest.raises(HardStop, match="gave up"):
        fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1")
    assert clock.sleeps == [10.0, 30.0, 90.0]
    assert len(transport.calls) == 4


def test_retry_recovers(tmp_path):
    fetcher, _, clock = _fetcher(tmp_path, {f"{SC}/app/1": [TransportError("timeout"), RawResponse(500, "x", b""), OK_APP]})
    assert fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1").outcome == "ok"
    assert clock.sleeps[:2] == [10.0, 30.0]


def test_five_parse_structure_failures_in_a_row_hard_stop(tmp_path):
    routes = {f"{SC}/app/{i}": OK_APP for i in range(6)}
    fetcher, _, _ = _fetcher(tmp_path, routes)
    for i in range(4):
        assert fetcher.fetch(f"steamcharts/app/{i}.html.gz", f"{SC}/app/{i}", check=lambda b: False).outcome == "parse_failure"
    with pytest.raises(HardStop, match="5 parse-structure failures"):
        fetcher.fetch("steamcharts/app/4.html.gz", f"{SC}/app/4", check=lambda b: False)


def test_parse_failure_counter_resets_on_success(tmp_path):
    routes = {f"{SC}/app/{i}": OK_APP for i in range(10)}
    fetcher, _, _ = _fetcher(tmp_path, routes)
    for i in range(10):
        fetcher.fetch(f"steamcharts/app/{i}.html.gz", f"{SC}/app/{i}", check=lambda b, i=i: i % 4 == 3)


def test_final_outcomes(tmp_path):
    routes = {
        f"{SC}/app/999999990": captured("steamcharts/app/999999990.html.gz"),
        f"{STORE}/app/5/?l=english": RawResponse(200, f"{STORE}/", raw("store/page/413150.html.gz")),
        f"{STORE}/app/6/?l=english": RawResponse(200, f"{STORE}/agecheck/app/6/?l=english", b"age check", (302,)),
        f"{STORE}/api/appdetails?appids=7&l=english": RawResponse(200, "x", appdetails(7, success=False)),
    }
    fetcher, _, _ = _fetcher(tmp_path, routes)
    assert fetcher.fetch("steamcharts/app/999999990.html.gz", f"{SC}/app/999999990").outcome == "not_found"
    assert fetcher.fetch("store/page/5.html.gz", f"{STORE}/app/5/?l=english").outcome == "no_store_page"
    assert fetcher.fetch("store/page/6.html.gz", f"{STORE}/app/6/?l=english").outcome == "age_gate"
    assert fetcher.fetch("store/appdetails/7.json.gz", f"{STORE}/api/appdetails?appids=7&l=english").outcome == "no_appdetails"


def test_request_log_and_archive(tmp_path):
    fetcher, _, _ = _fetcher(tmp_path, {f"{SC}/app/1": OK_APP})
    fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1")
    db = sqlite3.connect(tmp_path / "snap" / "requests.sqlite")
    url, status, final_url, ts, sha, outcome = db.execute(
        "SELECT url, status, final_url, timestamp, sha256, outcome FROM requests").fetchone()
    db.close()
    assert (url, status, final_url, outcome) == (f"{SC}/app/1", 200, f"{SC}/app/1", "ok")
    assert len(sha) == 64 and ts.endswith("Z")
    assert (tmp_path / "snap" / "raw" / "steamcharts" / "app" / "1.html.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_final_outcomes_are_not_refetched(tmp_path):
    fetcher, transport, _ = _fetcher(tmp_path, {f"{SC}/app/1": OK_APP})
    first = fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1")
    again = fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1")
    assert len(transport.calls) == 1 and again.from_archive and again.body == first.body


# ----------------------------------------------------------------------------- stages


def _top_routes(pages: list[bytes], end: RawResponse | None = None):
    routes = {f"{SC}/top/p.{i + 1}": RawResponse(200, f"{SC}/top/p.{i + 1}", body) for i, body in enumerate(pages)}
    routes[f"{SC}/top/p.{len(pages) + 1}"] = end or captured("steamcharts/app/999999990.html.gz")
    return routes


def test_listing_passes_end_at_404_and_union_by_appid(tmp_path, config):
    cfg = dataclasses.replace(config, collection=dataclasses.replace(config.collection, listing_passes=2))
    # Pass 1 sees apps 1, 2, 3; pass 2 (same URLs, re-fetched) sees 1, 3, 4: rows shifted between passes.
    p1 = [top_page([(1, 1, "A"), (2, 2, "B")]), top_page([(3, 3, "C")])]
    p2 = [top_page([(1, 1, "A"), (2, 3, "C")]), top_page([(3, 4, "D")])]
    routes = {f"{SC}/top/p.1": [RawResponse(200, "x", p1[0]), RawResponse(200, "x", p2[0])],
              f"{SC}/top/p.2": [RawResponse(200, "x", p1[1]), RawResponse(200, "x", p2[1])],
              f"{SC}/top/p.3": captured("steamcharts/app/999999990.html.gz")}
    meta = _run_pool(tmp_path, cfg, routes, mode="full")
    passes = meta["pool"]["passes"]
    assert [p["rows"] for p in passes] == [3, 3]
    assert [p["ended_by"] for p in passes] == ["404", "404"]
    assert meta["pool"]["one_pass_only_appids"] == 2  # apps 2 and 4
    assert meta["stages"]["pool"]["pool_size"] == 4


def test_listing_pass_ends_at_empty_page(tmp_path, config):
    routes = _top_routes([top_page([(1, 1, "A")]), top_page([])])
    meta = _run_pool(tmp_path, config, routes, mode="full", passes=1)
    assert meta["pool"]["passes"][0]["ended_by"] == "empty_page"
    assert meta["pool"]["passes"][0]["rows"] == 1


def _run_pool(tmp_path, config, routes, *, mode, passes=None):
    c = config.collection
    if passes is not None:
        c = dataclasses.replace(c, listing_passes=passes)
    if mode == "full":
        from steamstudy.config import GateRecord

        c = dataclasses.replace(c, operator_reply=GateRecord("ref", "2026-10-01"), ethics_check=GateRecord("ref", "2026-10-01"))
    cfg = dataclasses.replace(config, collection=c)
    sid = run_collect(tmp_path, cfg, mode=mode, stage="pool", transport=FakeTransport(routes), clock=FakeClock(),
                      today=TODAY)
    return json.loads((tmp_path / "snapshots" / sid / "snapshot.json").read_text(encoding="utf-8"))


def _world():
    """Routes for a tiny pool: app 10 scored, app 11 unscored (placeholder only), app 12 not on Steam Charts."""
    routes = _top_routes([top_page([(1, 10, "Scored"), (2, 11, "Placeholder"), (3, 12, "Missing")])])
    routes[f"{SC}/app/10"] = RawResponse(200, "x", steamcharts_page([("2025-01", 100.0, 150), ("2025-02", 50.0, 70)]))
    routes[f"{SC}/app/11"] = RawResponse(200, "x", steamcharts_page([("2017-09", 0.0, 0)]))
    routes[f"{SC}/app/12"] = captured("steamcharts/app/999999990.html.gz")
    routes[f"{STORE}/app/10/?l=english"] = RawResponse(200, f"{STORE}/app/10/Scored/", store_page(10, [(19, "Action")]))
    routes[f"{STORE}/api/appdetails?appids=10&l=english"] = RawResponse(200, "x", appdetails(10))
    routes["https://api.steampowered.com/IStoreService/GetTagList/v1/?language=english"] = captured("steam_api/GetTagList.json")
    return routes


def _test_cfg(config, **kw):
    return dataclasses.replace(config, collection=dataclasses.replace(config.collection, edge_case_appids=(), **kw))


def test_full_collection_runs_stages_in_order_and_store_only_fetches_scored_apps(tmp_path, config):
    transport = FakeTransport(_world())
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=transport, clock=FakeClock(), today=TODAY)
    urls = [c.url for c in transport.calls]
    kinds = ["top" if "/top/" in u else "app" if "steamcharts.com/app" in u else "store" for u in urls]
    assert kinds == sorted(kinds, key=["top", "app", "store"].index)
    store_urls = [u for u in urls if "steampowered" in u]
    assert store_urls[0].startswith("https://api.steampowered.com/IStoreService/GetTagList")
    assert {u for u in store_urls if "appids=" in u or "/app/" in u} == {
        f"{STORE}/app/10/?l=english", f"{STORE}/api/appdetails?appids=10&l=english"}
    assert all("cc=" not in u for u in urls)
    snap = Snapshot(tmp_path / "snapshots" / sid)
    assert snap.meta["closed"] is True
    assert snap.meta["taglist_version_hash"] == "711684454"
    assert snap.meta["store_country"] == "BG"
    assert snap.entry("steamcharts/app/12.html.gz").outcome == "not_found"


def test_snapshot_json_records_provenance(tmp_path, config):
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=FakeTransport(_world()), clock=FakeClock(),
                      today=TODAY)
    meta = Snapshot(tmp_path / "snapshots" / sid).meta
    assert meta["mode"] == "test" and meta["collection_date"] == "2026-10-04"
    assert meta["observation_window"] == {"first": "2021-10", "last": "2026-09"}
    assert meta["collection_config_hash"] == config.collection_config_hash or len(meta["collection_config_hash"]) == 64
    assert meta["user_agent"].startswith("steamstudy-test")
    assert meta["rates"][0]["values"]["steamcharts_per_second"] == 3.0
    assert meta["age_check_birth_date"] == "1996-10-04"
    assert {"started", "ended"} <= set(meta["pool"]["passes"][0])
    assert "python" in meta["software_versions"]


def test_age_check_cookie_is_thirty_years_before_collection():
    cookie = age_check_cookie(dt.date(1996, 10, 4))
    assert "birthtime=844387200" in cookie and "lastagecheckage=4-9-1996" in cookie


def test_resume_skips_final_outcomes_and_refetches_stopped_requests(tmp_path, config):
    routes = _world()
    routes[f"{SC}/app/11"] = RawResponse(429, "x", b"slow down")
    first = FakeTransport(routes)
    with pytest.raises(HardStop):
        run_collect(tmp_path, _test_cfg(config), mode="test", transport=first, clock=FakeClock(), today=TODAY)
    second = FakeTransport(_world())
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=second, clock=FakeClock(), today=TODAY)
    refetched = [c.url for c in second.calls]
    assert f"{SC}/app/10" not in refetched and f"{SC}/top/p.1" not in refetched
    assert f"{SC}/app/11" in refetched
    assert Snapshot(tmp_path / "snapshots" / sid).meta["closed"] is True


def test_full_run_gate_refuses_without_operator_reply_and_ethics_check(tmp_path, config):
    with pytest.raises(CollectRefused, match="operator_reply.*ethics_check"):
        run_collect(tmp_path, config, mode="full", transport=FakeTransport({}), clock=FakeClock(), today=TODAY)
    assert not (tmp_path / "snapshots").exists()


def test_collection_refuses_without_contact_details(tmp_path, config_dir):
    with pytest.raises(CollectRefused, match="contact"):
        cfg = neutral_collection(load_config(config_dir), user_agent="steamstudy (contact: <fill in before collecting>)")
        run_collect(tmp_path, cfg, mode="test", transport=FakeTransport({}), today=TODAY)


def test_closed_snapshot_refuses_more_collection(tmp_path, config):
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=FakeTransport(_world()), clock=FakeClock(),
                      today=TODAY)
    with pytest.raises(CollectRefused, match="closed"):
        run_collect(tmp_path, _test_cfg(config), snapshot_id=sid, transport=FakeTransport({}), clock=FakeClock())
