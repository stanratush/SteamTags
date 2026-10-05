"""Ticket 10: the SteamDB cross-check (permission-gated; tested only on a local fixture page)."""

from __future__ import annotations

import dataclasses

import pytest

from conftest import neutral_collection
from helpers import FIXTURES, World
from steamstudy.build.core import build
from steamstudy.build.parse import parse_steamdb_app
from steamstudy.build.writer import write_build
from steamstudy.collect.fetcher import FakeClock, FakeTransport, RawResponse
from steamstudy.collect.run import CollectRefused, run_steamdb
from steamstudy.config import GateRecord, load_config
from steamstudy.snapshot import Snapshot

PAGE = (FIXTURES / "steamdb" / "SYNTHETIC-app.html").read_bytes()


@pytest.fixture
def config(config_dir):
    return neutral_collection(load_config(config_dir))


def _with_permission(config):
    c = dataclasses.replace(config.collection, steamdb_permission=GateRecord("SteamDB email 2026-11-01", "2026-11-01"))
    return dataclasses.replace(config, collection=c)


def _built(tmp_path, config):
    world = World().real(413150)
    world.add(1, avg=50.0, tags=[(87918, "Farming Sim")])
    world.add(2, avg=40.0, tags=[(19, "Action")], app_type="dlc")  # excluded: never fetched from SteamDB
    snapshot = world.snapshot(tmp_path / "snapshots" / "snap")
    override = {"appid": 413150, "name": "Stardew", "rule": "dating_sim_tag", "reason": "r", "added": "2026-10-05",
                "evidence": [{"url": "https://x", "retrieved": "2026-10-05"}]}
    cfg = dataclasses.replace(config, exclusion_overrides=(override,))
    folder = write_build(build(Snapshot(snapshot), cfg, "B-steamdb"), tmp_path)
    return snapshot, folder, cfg


def test_parser_reads_tag_links_in_order():
    assert parse_steamdb_app(PAGE) == [(87918, "Farming Sim"), (3964, "Pixel Graphics"), (9551, "Dating Sim"),
                                       (424242, "Not On The Store")]


def test_refuses_without_a_permission_reference_and_sends_nothing(tmp_path, config):
    _, folder, _ = _built(tmp_path, config)
    transport = FakeTransport({})
    with pytest.raises(CollectRefused, match="no SteamDB permission"):
        run_steamdb(tmp_path, config, folder.name, transport=transport, clock=FakeClock())
    assert transport.calls == []


def test_batch_fetches_only_the_builds_top100_members(tmp_path, config):
    snapshot, folder, cfg = _built(tmp_path, config)
    routes = {f"https://steamdb.info/app/{a}/": RawResponse(200, f"https://steamdb.info/app/{a}/", PAGE)
              for a in (413150, 1, 2)}
    transport = FakeTransport(routes)
    record = run_steamdb(tmp_path, _with_permission(cfg), folder.name, transport=transport, clock=FakeClock())
    assert sorted(c.url for c in transport.calls) == ["https://steamdb.info/app/1/", "https://steamdb.info/app/413150/"]
    assert {c.source for c in transport.calls} == {"steamdb"}
    meta = Snapshot(snapshot).meta
    assert meta["steamdb"]["batches"] == [record] and record["batch"] == "steamdb-1"
    assert record["permission_reference"] == "SteamDB email 2026-11-01" and record["apps"] == 2


def test_next_build_writes_the_crosscheck_without_changing_datasets(tmp_path, config):
    snapshot, folder, cfg = _built(tmp_path, config)
    routes = {f"https://steamdb.info/app/{a}/": RawResponse(200, "x", PAGE) for a in (413150, 1)}
    run_steamdb(tmp_path, _with_permission(cfg), folder.name, transport=FakeTransport(routes), clock=FakeClock())
    before = build(Snapshot(snapshot), cfg, "B-before-check")
    after = build(Snapshot(snapshot), cfg, "B-steamdb-2")
    rows = {r["appid"]: r for r in after.rows("reports/steamdb_crosscheck.csv")}
    assert rows[1]["only_steamdb_tag_ids"] == [3964, 9551, 424242] and rows[1]["same_tag_set"] is False
    assert rows[1]["steamdb_batch"] == "steamdb-1"
    for key in ("overall", "puzzle", "rpg", "strategy", "simulation"):
        assert after.rows(f"datasets/top100_{key}.csv") == before.rows(f"datasets/top100_{key}.csv")
