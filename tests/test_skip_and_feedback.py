"""Skipping Steam Charts pages that keep failing, collection feedback, and the exactly-100 rule."""

from __future__ import annotations

import csv
import dataclasses
import io
import logging
import random

import pytest

from conftest import neutral_collection
from helpers import World, captured, raw, steamcharts_page
from steamstudy.build.core import BuildFailed, build
from steamstudy.build.parse import parse_steamcharts_app
from steamstudy.collect.fetcher import FakeClock, FakeTransport, HardStop, RawResponse, TransportError
from steamstudy.collect.progress import Progress
from steamstudy.collect.run import run_collect
from steamstudy.config import load_config
from steamstudy.network.cluster import Cluster
from steamstudy.network.graph import Edge, to_graph
from steamstudy.network import metrics as M
from steamstudy.snapshot import Snapshot
from test_collect import SC, TODAY, _fetcher, _close_stores, _test_cfg, _world  # noqa: F401

ERROR_500 = RawResponse(500, f"{SC}/app/1", raw("steamcharts/app/1401150-500.html.gz"))


@pytest.fixture
def config(config_dir):
    return neutral_collection(load_config(config_dir))


# ----------------------------------------------------------------------------- Fetcher


def test_a_page_that_keeps_failing_to_load_is_skipped_after_the_retries(tmp_path):
    fetcher, transport, clock = _fetcher(tmp_path, {f"{SC}/app/1": ERROR_500})
    resp = fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1", skip_on_failure=True)
    assert resp.outcome == "skipped" and resp.status == 500
    assert clock.sleeps == [10.0, 30.0, 90.0] and len(transport.calls) == 4
    entry = fetcher.store.latest("steamcharts/app/1.html.gz")
    assert entry.outcome == "skipped" and entry.is_final and "failed to load after 4 attempts: HTTP 500" in entry.detail


def test_a_connection_failure_is_skipped_too(tmp_path):
    fetcher, _, _ = _fetcher(tmp_path, {f"{SC}/app/1": TransportError("timeout", "read timed out")})
    resp = fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1", skip_on_failure=True)
    assert resp.outcome == "skipped" and resp.status is None and "timeout" in fetcher.store.latest(
        "steamcharts/app/1.html.gz").detail


def test_parse_failures_are_skipped_and_never_stop_collection(tmp_path):
    routes = {f"{SC}/app/{i}": RawResponse(200, "x", raw("steamcharts/app/698670.html.gz")) for i in range(8)}
    fetcher, _, _ = _fetcher(tmp_path, routes)
    outcomes = [fetcher.fetch(f"steamcharts/app/{i}.html.gz", f"{SC}/app/{i}", check=lambda b: False,
                              skip_on_failure=True).outcome for i in range(8)]
    assert outcomes == ["skipped"] * 8  # no hard stop after 5 in a row
    assert "parser could not read" in fetcher.store.latest("steamcharts/app/7.html.gz").detail


@pytest.mark.parametrize("response", [
    RawResponse(503, "x", b"busy"), RawResponse(429, "x", b"slow down"),
    RawResponse(200, "x", b"<title>Just a moment...</title> challenge-platform"),
], ids=["503", "429", "challenge"])
def test_anti_bot_signals_still_stop_even_when_skipping(tmp_path, response):
    fetcher, transport, _ = _fetcher(tmp_path, {f"{SC}/app/1": response})
    with pytest.raises(HardStop):
        fetcher.fetch("steamcharts/app/1.html.gz", f"{SC}/app/1", skip_on_failure=True)
    assert len(transport.calls) == 1


def test_steamdb_page_without_tag_links_is_a_structure_miss(tmp_path):
    fetcher, _, _ = _fetcher(tmp_path, {"https://steamdb.info/app/1/": RawResponse(200, "x", b"<html>no tags</html>")})
    with pytest.raises(HardStop, match="SteamDB page structure marker missing"):
        fetcher.fetch("steamdb/app/1.html.gz", "https://steamdb.info/app/1/")


# ----------------------------------------------------------------------------- collection


def test_collection_finishes_with_a_skipped_app_and_reports_it(tmp_path, config, caplog):
    routes = _world()
    routes[f"{SC}/app/11"] = ERROR_500
    caplog.set_level(logging.INFO, logger="steamstudy")
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=FakeTransport(routes), clock=FakeClock(),
                      today=TODAY)
    snap_dir = tmp_path / "snapshots" / sid
    assert Snapshot(snap_dir).meta["closed"] is True
    rows = list(csv.DictReader(io.StringIO((snap_dir / "skipped_apps.csv").read_text(encoding="utf-8-sig"))))
    assert [(r["appid"], r["name"], r["url"], r["last_status"]) for r in rows] == [
        ("11", "Placeholder", f"{SC}/app/11", "500")]
    assert "failed to load after 4 attempts: HTTP 500" in rows[0]["reason"]
    messages = "\n".join(r.getMessage() for r in caplog.records)
    for expected in ("Starting test Snapshot", "pool pass 1 of 1 finished", "history: one Steam Charts page for each of 3 apps",
                     "history finished: 3 apps", "1 skipped", "history: 1 apps skipped; see", "store: store page and appdetails",
                     "taglist: GetTagList vocabulary of 446 tags", "closed after"):
        assert expected in messages, expected
    # A rerun does not retry it (skipped is final), so collection never blocks on it.
    again = FakeTransport(_world())
    with pytest.raises(Exception, match="closed"):
        run_collect(tmp_path, _test_cfg(config), snapshot_id=sid, transport=again, clock=FakeClock())


def test_the_build_reports_skipped_apps_as_unscored(tmp_path, config):
    routes = _world()
    routes[f"{SC}/app/11"] = ERROR_500
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=FakeTransport(routes), clock=FakeClock(),
                      today=TODAY)
    result = build(Snapshot(tmp_path / "snapshots" / sid), config, "B1")
    assert [(r["appid"], r["url"]) for r in result.rows("reports/skipped_apps.csv")] == [(11, f"{SC}/app/11")]
    completeness = {r["item"]: r["value"] for r in result.rows("reports/completeness.csv")}
    assert completeness["unscored_skipped"] == 1
    assert "1 apps were skipped during collection:" in result.texts["reports/reports.html"]


def test_progress_lines_and_estimate():
    now = [0.0]
    lines: list[str] = []
    progress = Progress("history", 100, every=10, clock=lambda: now[0], emit=lines.append)
    for i in range(20):
        now[0] += 1.0
        progress.step(fetched=i >= 10, skipped=i == 15)
    progress.finish("18 ok, 1 skipped")
    assert lines[0] == "history: 10 / 100 apps (10.0%) · 10 already collected"
    assert lines[1] == "history: 20 / 100 apps (20.0%) · 10 already collected · 1 skipped · about 2m 40s left"
    assert lines[-1] == "history finished: 20 apps in 20s (10 from an earlier run); 18 ok, 1 skipped"


# ----------------------------------------------------------------------------- Build rules


def _fillers(world: World, n: int):
    for i in range(n):
        world.add(100000 + i, avg=5000.0 - i, tags=[(1664, "Puzzle"), (122, "RPG"), (9, "Strategy"), (599, "Simulation")])
    return world


def test_a_full_build_needs_exactly_100_games_in_every_dataset(tmp_path, config):
    short = _fillers(World(), 99).snapshot(tmp_path / "short", mode="full")
    with pytest.raises(BuildFailed, match="exactly 100"):
        build(Snapshot(short), config, "B1")
    full = _fillers(World(), 101).snapshot(tmp_path / "full", mode="full")
    result = build(Snapshot(full), config, "B2")
    assert all(len(result.rows(f"datasets/top100_{k}.csv")) == 100
               for k in ("overall", "puzzle", "rpg", "strategy", "simulation"))
    assert [r["rank"] for r in result.rows("datasets/top100_puzzle.csv")] == list(range(1, 101))
    assert result.rows("datasets/top100_puzzle.csv")[-1]["appid"] == 100099  # the 100 highest scores


def test_a_test_build_may_be_short_with_a_warning(tmp_path, config):
    result = build(Snapshot(_fillers(World(), 5).snapshot(tmp_path / "t", mode="test")), config, "B1")
    assert any("allowed only in a test Build" in w for w in result.warnings)


def test_rows_after_the_observation_window_are_ignored():
    page = steamcharts_page([("2026-09", 10.0, 20), ("2026-10", 0.0, 0)], extra_labels=["October 2026"])
    history = parse_steamcharts_app(page, last_month="2026-09")
    assert history.errors == () and [r.month for r in history.rows] == ["2026-09"]
    assert parse_steamcharts_app(page).errors  # without the window the duplicate is still an error


def test_conductance_status_with_float_lift_weights():
    rng = random.Random(3)
    for _ in range(200):
        weights = [rng.uniform(0.3, 3.7) for _ in range(3)]
        edges = [Edge(1, 2, 8, weights[0]), Edge(1, 3, 8, weights[1]), Edge(2, 3, 8, weights[2])]
        graph = to_graph([1, 2, 3, 4], edges, "lift")
        m = M.cluster_metrics(graph, Cluster("C1", frozenset({1, 2, 3})))
        assert m.conductance is None and m.conductance_status == "no_edges_outside_cluster"
