"""The Tag Source: a Snapshot takes its tags from the Steam store page (default) or from SteamDB."""

from __future__ import annotations

import dataclasses

import pytest

from conftest import neutral_collection
from helpers import World
from steamstudy import cli
from steamstudy.build.core import build
from steamstudy.collect.fetcher import FakeClock, FakeTransport, RawResponse
from steamstudy.collect.run import CollectRefused, run_collect, run_repair, run_steamdb
from steamstudy.config import GateRecord, load_config
from steamstudy.snapshot import Snapshot
from test_collect import TODAY, _test_cfg, _world

STEAMDB_TAGS = [(87918, "Farming Sim"), (3964, "Pixel Graphics"), (1664, "Puzzle"), (424242, "Not On The Store")]


def steamdb_page(tags):
    """A page in the shape of the synthetic SteamDB fixture (the parser's assumed structure) with these tags."""
    links = "".join(f'<a href="/tag/{t}/">{n}</a>' for t, n in tags)
    return f'<html><body><div class="store-tags">{links}</div><a href="/app/1/">x</a></body></html>'.encode()


STEAMDB_PAGE = steamdb_page(STEAMDB_TAGS)


@pytest.fixture
def config(config_dir):
    return neutral_collection(load_config(config_dir))


def _permitted(config):
    c = dataclasses.replace(config.collection, steamdb_permission=GateRecord("SteamDB email 2026-11-01", "2026-11-01"))
    return _test_cfg(dataclasses.replace(config, collection=c))


def _steamdb_world():
    routes = _world()
    routes["https://steamdb.info/app/10/"] = RawResponse(200, "https://steamdb.info/app/10/", STEAMDB_PAGE)
    return routes


# ----------------------------------------------------------------------------- Collect


def test_default_tag_source_is_steam_and_never_contacts_steamdb(tmp_path, config):
    transport = FakeTransport(_steamdb_world())
    sid = run_collect(tmp_path, _test_cfg(config), mode="test", transport=transport, clock=FakeClock(), today=TODAY)
    assert Snapshot(tmp_path / "snapshots" / sid).meta["tag_source"] == "steam"
    assert not any("steamdb" in c.url for c in transport.calls)


def test_steamdb_tag_source_fetches_a_steamdb_page_for_every_scored_app(tmp_path, config):
    transport = FakeTransport(_steamdb_world())
    sid = run_collect(tmp_path, _permitted(config), mode="test", tag_source="steamdb", transport=transport,
                      clock=FakeClock(), today=TODAY)
    steamdb_calls = [c for c in transport.calls if "steamdb" in c.url]
    assert [c.url for c in steamdb_calls] == ["https://steamdb.info/app/10/"]  # app 10 is the only scored app
    assert {c.source for c in steamdb_calls} == {"steamdb"}
    snap = Snapshot(tmp_path / "snapshots" / sid)
    assert snap.meta["tag_source"] == "steamdb"
    assert snap.entry("steamdb/app/10.html.gz").outcome == "ok"
    # The store page and appdetails are still collected: they carry the metadata the exclusion rules need.
    assert snap.entry("store/page/10.html.gz").outcome == "ok"
    assert snap.entry("store/appdetails/10.json.gz").outcome == "ok"


def test_steamdb_tag_source_refuses_without_a_permission_reference_and_sends_nothing(tmp_path, config):
    transport = FakeTransport(_steamdb_world())
    with pytest.raises(CollectRefused, match="SteamDB permission"):
        run_collect(tmp_path, _test_cfg(config), mode="test", tag_source="steamdb", transport=transport,
                    clock=FakeClock(), today=TODAY)
    assert transport.calls == []
    assert not (tmp_path / "snapshots").exists()


def test_unknown_tag_source_is_refused(tmp_path, config):
    with pytest.raises(CollectRefused, match="tag source"):
        run_collect(tmp_path, _test_cfg(config), mode="test", tag_source="steamspy", transport=FakeTransport({}),
                    clock=FakeClock(), today=TODAY)


def test_resume_keeps_the_recorded_tag_source_and_refuses_a_different_one(tmp_path, config):
    cfg = _permitted(config)
    sid = run_collect(tmp_path, cfg, mode="test", tag_source="steamdb", stage="pool",
                      transport=FakeTransport(_steamdb_world()), clock=FakeClock(), today=TODAY)
    with pytest.raises(CollectRefused, match="steamdb"):
        run_collect(tmp_path, cfg, snapshot_id=sid, tag_source="steam", transport=FakeTransport({}), clock=FakeClock())
    transport = FakeTransport(_steamdb_world())
    run_collect(tmp_path, cfg, snapshot_id=sid, transport=transport, clock=FakeClock())  # no flag: keeps steamdb
    assert "https://steamdb.info/app/10/" in [c.url for c in transport.calls]


def test_repair_refetches_the_steamdb_page_of_a_steamdb_snapshot(tmp_path, config):
    cfg = _permitted(config)
    sid = run_collect(tmp_path, cfg, mode="test", tag_source="steamdb", transport=FakeTransport(_steamdb_world()),
                      clock=FakeClock(), today=TODAY)
    transport = FakeTransport(_steamdb_world())
    repair = run_repair(tmp_path, cfg, 10, "SteamDB page was stale", snapshot_id=sid, transport=transport,
                        clock=FakeClock())
    assert "https://steamdb.info/app/10/" in {c.url for c in transport.calls}
    assert repair["outcomes"]["steamdb/app/10.html.gz"] == "ok"


def test_crosscheck_batch_is_refused_for_a_steamdb_snapshot(tmp_path, config):
    from steamstudy.build.writer import write_build

    snapshot = _steamdb_snapshot(tmp_path / "snapshots" / "snap")
    folder = write_build(build(Snapshot(snapshot), config, "B-x"), tmp_path)
    transport = FakeTransport({})
    with pytest.raises(CollectRefused, match="already takes its tags from SteamDB"):
        run_steamdb(tmp_path, _permitted(config), folder.name, transport=transport, clock=FakeClock())
    assert transport.calls == []


# ----------------------------------------------------------------------------- Build


def _steamdb_snapshot(path, *, steamdb_outcomes=None):
    """App 1 (store tags: Action) and app 2 (store tags: Puzzle); both have SteamDB pages unless overridden."""
    world = World()
    world.add(1, avg=50.0, tags=[(19, "Action")])
    world.add(2, avg=40.0, tags=[(1664, "Puzzle")])
    outcomes = steamdb_outcomes or {}
    for appid in (1, 2):
        outcome = outcomes.get(appid, "ok")
        world.responses[f"steamdb/app/{appid}.html.gz"] = (outcome, STEAMDB_PAGE if outcome == "ok" else b"")
    return world.snapshot(path, meta={"tag_source": "steamdb"})


def test_build_reads_tags_from_steamdb_for_a_steamdb_snapshot(tmp_path, config):
    result = build(Snapshot(_steamdb_snapshot(tmp_path / "snap")), config, "B-steamdb")
    game = result.games[1]
    assert [(t.tag_id, t.name) for t in game.tags] == STEAMDB_TAGS
    assert [t.position for t in game.tags] == [1, 2, 3, 4]
    assert game.tag_source == "steamdb"
    row = next(r for r in result.rows("datasets/top100_overall.csv") if r["appid"] == 1)
    assert row["tag_ids"] == [t for t, _ in STEAMDB_TAGS]
    assert result.build_json["tag_source"] == "steamdb"
    assert "SteamDB" in result.build_json["attribution"]


def test_build_crosscheck_of_a_steamdb_snapshot_compares_the_store_page_tags(tmp_path, config):
    result = build(Snapshot(_steamdb_snapshot(tmp_path / "snap")), config, "B-steamdb")
    rows = {r["appid"]: r for r in result.rows("reports/steamdb_crosscheck.csv")}
    assert rows[1]["store_tag_ids"] == [19]
    assert rows[1]["steamdb_tag_ids"] == [t for t, _ in STEAMDB_TAGS]
    assert rows[1]["same_tag_set"] is False


def test_an_app_without_a_steamdb_page_has_no_tags(tmp_path, config):
    snap = _steamdb_snapshot(tmp_path / "snap", steamdb_outcomes={2: "not_found"})
    result = build(Snapshot(snap), config, "B-steamdb")
    assert result.games[2].tags == ()
    assert "no SteamDB page for appid 2 (not_found): it has no tags" in result.warnings
    rows = {r["reason"]: r for r in result.rows("reports/exclusions.csv") if r["appid"] == 2}
    assert "SteamDB" in rows["no_tags"]["detail"]


def test_an_unreadable_steamdb_page_is_a_parse_error(tmp_path, config):
    world = World().add(1, avg=50.0)
    world.responses["steamdb/app/1.html.gz"] = ("ok", b"<html><body>no tags here</body></html>")
    snap = world.snapshot(tmp_path / "snap", meta={"tag_source": "steamdb"})
    result = build(Snapshot(snap), config, "B-x", allow_parse_errors=True)
    errors = result.rows("reports/parse_errors.csv")
    assert [(e["appid"], e["source"], e["request_key"]) for e in errors] == [(1, "steamdb_page", "steamdb/app/1.html.gz")]


def test_a_snapshot_without_a_recorded_tag_source_uses_the_store_page(tmp_path, config):
    world = World().add(1, avg=50.0, tags=[(19, "Action")])
    world.responses["steamdb/app/1.html.gz"] = ("ok", STEAMDB_PAGE)  # a cross-check page: never a tag source
    result = build(Snapshot(world.snapshot(tmp_path / "snap")), config, "B-x")
    assert [t.tag_id for t in result.games[1].tags] == [19]
    assert result.build_json["tag_source"] == "steam"


# ----------------------------------------------------------------------------- CLI


def test_cli_passes_the_tag_source_flag_to_collect(monkeypatch, tmp_path):
    seen = {}

    def fake_run_collect(root, config, **kw):
        seen.update(kw)
        return "snap"

    monkeypatch.setattr("steamstudy.collect.run.run_collect", fake_run_collect)
    assert cli.main(["--root", str(tmp_path), "collect", "--mode", "test", "--tag-source", "steamdb"]) == 0
    assert seen["tag_source"] == "steamdb"
    seen.clear()
    assert cli.main(["--root", str(tmp_path), "collect", "--mode", "test"]) == 0
    assert seen["tag_source"] is None


def test_cli_rejects_an_unknown_tag_source(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["--root", str(tmp_path), "collect", "--mode", "test", "--tag-source", "steamspy"])
