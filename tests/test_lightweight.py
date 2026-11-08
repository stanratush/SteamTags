"""Issue 23: Lightweight Snapshots, the parsed tables a Build reads in one zip."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from helpers import FIXTURES, World
from steamstudy import lightweight as L
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.snapshot import Snapshot

BUILD_ID = "20261108T000000Z-abcdef12"
STEAMDB_PAGE = (FIXTURES / "steamdb" / "SYNTHETIC-app.html").read_bytes()


def _rich_world() -> World:
    """Every kind of record a Build reads: real pages, every request outcome, parse errors, SteamDB pages."""
    from test_build_exclusions import _world

    w = _world()
    w.add(5, avg=90.0, name="Skipped")
    w.add(6, avg=80.0, name="Not Found")
    w.add(7, avg=70.0, name="Store Parse Failure")
    w.add(8, avg=60.0, name="No Details")
    w.add(9, avg=50.0, name="Broken Chart")
    w.add(10, avg=40.0, name="Never Fetched")
    w.responses["steamcharts/app/5.html.gz"] = ("skipped", None)
    w.responses["steamcharts/app/6.html.gz"] = ("not_found", None)
    w.responses["store/page/7.html.gz"] = ("parse_failure", None)
    w.responses["store/appdetails/8.json.gz"] = ("ok", b'{"8": {"success": false}}')
    w.responses["steamcharts/app/9.html.gz"] = ("ok", b"<html><body>no table</body></html>")
    del w.responses["steamcharts/app/10.html.gz"]
    w.responses["steamdb/app/413150.html.gz"] = ("ok", STEAMDB_PAGE)
    w.responses["steamdb/app/1.html.gz"] = ("ok", b"<html></html>")  # unreadable: a warning
    return w


def _snapshot(tmp_path: Path, world: World | None = None) -> Path:
    return (world or _rich_world()).snapshot(tmp_path / "snapshots" / "S1")


def _files(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def _build_both(tmp_path: Path, snap: Path, config, **kw) -> tuple[dict[str, bytes], dict[str, bytes]]:
    light = L.LightSource.from_zip(L.lighten(snap))
    raw_folder = write_build(build(Snapshot(snap), config, BUILD_ID, **kw), tmp_path / "raw")
    light_folder = write_build(build(light, config, BUILD_ID, **kw), tmp_path / "light")
    return _files(raw_folder), _files(light_folder)


# ----------------------------------------------------------------------------- the guarantee


@pytest.mark.parametrize("world", ["rich", "tagged"])
def test_a_build_from_the_lightweight_form_is_byte_identical_apart_from_snapshot_form(tmp_path, config_dir, world):
    from test_build_network import tagged_world

    snap = _snapshot(tmp_path, _rich_world() if world == "rich" else tagged_world())
    raw, light = _build_both(tmp_path, snap, load_config(config_dir), allow_parse_errors=world == "rich")
    assert raw.keys() == light.keys()
    assert [f for f in raw if f != "datasets/build.json" and raw[f] != light[f]] == []
    raw_json, light_json = raw["datasets/build.json"], light["datasets/build.json"]
    assert (json.loads(raw_json)["snapshot_form"], json.loads(light_json)["snapshot_form"]) == ("raw", "lightweight")
    assert L.without_snapshot_form(raw_json) == L.without_snapshot_form(light_json) != raw_json
    assert json.loads(raw_json)["extract_version"] == L.EXTRACT_VERSION
    if world == "rich":  # the cases are really there
        errors = raw["reports/parse_errors.csv"]
        assert b"steamcharts_app" in errors and b"store_page" in errors
        assert raw["reports/skipped_apps.csv"].count(b"\n") == 2
        assert "reports/steamdb_crosscheck.csv" in raw


def test_the_lightweight_records_equal_the_raw_records(tmp_path):
    snap = _snapshot(tmp_path)
    raw, light = L.RawSource(Snapshot(snap)), L.LightSource.from_zip(L.lighten(snap))
    assert light.listing_pages() == raw.listing_pages()
    assert light.meta == {k: raw.meta[k] for k in L.SNAPSHOT_KEYS}
    for appid in (413150, 1, 2, 5, 6, 7, 8, 9, 10, 99999):
        assert light.charts(appid) == raw.charts(appid), appid
        assert light.store(appid) == raw.store(appid), appid
        assert light.steamdb(appid) == raw.steamdb(appid), appid
    assert light.vocabulary() == raw.vocabulary() and light.skipped() == raw.skipped()
    assert light.has_steamdb() and raw.has_steamdb()


def test_two_lightenings_give_byte_identical_zips(tmp_path):
    snap = _snapshot(tmp_path)
    first = L.lighten(snap).read_bytes()
    assert L.lighten(snap).read_bytes() == first
    assert L.light_path(snap.parent, "S1").name == "S1.light.zip"


def test_lightening_never_changes_the_raw_form(tmp_path):
    snap = _snapshot(tmp_path)
    before = _files(snap)
    L.lighten(snap)
    assert _files(snap) == before


def test_only_a_closed_snapshot_is_lightened(tmp_path):
    snap = _snapshot(tmp_path)
    meta = json.loads((snap / "snapshot.json").read_text(encoding="utf-8"))
    (snap / "snapshot.json").write_text(json.dumps({**meta, "closed": False}), encoding="utf-8")
    with pytest.raises(L.LightweightError, match="not closed"):
        L.lighten(snap)


# ----------------------------------------------------------------------------- choosing a form


def test_the_lightweight_form_is_the_default_and_from_raw_forces_raw(tmp_path):
    snap = _snapshot(tmp_path)
    assert L.open_build_source(snap.parent, "S1").source.form == "raw"  # not lightened yet
    L.lighten(snap)
    opened = L.open_build_source(snap.parent, "S1")
    assert opened.source.form == "lightweight" and opened.warnings == []
    assert L.open_build_source(snap.parent, "S1", from_raw=True).source.form == "raw"


def test_another_extract_version_reads_raw_with_a_warning_and_is_refused_without_raw(tmp_path, monkeypatch):
    snap = _snapshot(tmp_path)
    L.lighten(snap)
    monkeypatch.setattr(L, "EXTRACT_VERSION", L.EXTRACT_VERSION + 1)
    opened = L.open_build_source(snap.parent, "S1")
    assert opened.source.form == "raw" and "extract version" in opened.warnings[0] and "lighten" in opened.warnings[0]
    shutil.rmtree(snap)
    with pytest.raises(L.LightweightError, match=f"extract version {L.EXTRACT_VERSION - 1}"):
        L.open_build_source(snap.parent, "S1")


@pytest.mark.parametrize("change", ["repairs", "steamdb"])
def test_a_repair_or_steamdb_batch_makes_the_lightweight_form_stale(tmp_path, change):
    snap = _snapshot(tmp_path)
    L.lighten(snap)
    meta = json.loads((snap / "snapshot.json").read_text(encoding="utf-8"))
    if change == "repairs":
        meta["repairs"].append({"appid": 1, "reason": "test"})
    else:
        meta["steamdb"]["batches"].append({"batch": "steamdb-1"})
    (snap / "snapshot.json").write_text(json.dumps(meta), encoding="utf-8")
    opened = L.open_build_source(snap.parent, "S1")
    assert opened.source.form == "raw" and "stale" in opened.warnings[0]


def test_a_tampered_member_is_refused(tmp_path):
    snap = _snapshot(tmp_path)
    path = L.lighten(snap)
    with zipfile.ZipFile(path) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    members["months.csv"] = members["months.csv"].replace(b".", b"9", 1)
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    with pytest.raises(L.LightweightError, match="months.csv does not match its recorded sha256"):
        L.LightSource.from_zip(path)


def test_a_lightweight_only_snapshot_builds(tmp_path, config_dir):
    snap = _snapshot(tmp_path)
    L.lighten(snap)
    shutil.rmtree(snap)
    assert L.latest_source_snapshot_id(snap.parent) == "S1"
    opened = L.open_build_source(snap.parent, "S1")
    result = build(opened.source, load_config(config_dir), BUILD_ID, allow_parse_errors=True)
    assert result.build_json["snapshot_form"] == "lightweight" and result.build_json["snapshot_id"] == "S1"
    with pytest.raises(L.LightweightError, match="no raw form"):
        L.open_build_source(snap.parent, "S1", from_raw=True)


def test_verify_light_finds_no_difference_and_refuses_a_stale_form(tmp_path, config_dir):
    snap = _snapshot(tmp_path)
    L.lighten(snap)
    assert L.verify_light(snap.parent, "S1", load_config(config_dir)) == []
    meta = json.loads((snap / "snapshot.json").read_text(encoding="utf-8"))
    meta["repairs"].append({"appid": 1})
    (snap / "snapshot.json").write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(L.LightweightError, match="stale"):
        L.verify_light(snap.parent, "S1", load_config(config_dir))


def test_an_unreadable_zip_is_refused_and_names_no_snapshot(tmp_path):
    snap = _snapshot(tmp_path)
    L.light_path(snap.parent, "S1").write_bytes(b"not a zip")
    (snap.parent / "S0.light.zip").write_bytes(b"not a zip either")
    with pytest.raises(L.LightweightError, match="not a readable Lightweight Snapshot"):
        L.open_build_source(snap.parent, "S1")
    assert L.latest_source_snapshot_id(snap.parent) == "S1"  # from the raw folder; the broken zips are skipped


# ----------------------------------------------------------------------------- CLI


def _cli(*args: str) -> int:
    from conftest import CONFIG_DIR
    from steamstudy.cli import main

    return main(["--config", str(CONFIG_DIR), *args])


def test_the_cli_lightens_verifies_and_builds_from_either_form(tmp_path):
    from test_build_network import tagged_world

    snap = _snapshot(tmp_path, tagged_world())
    assert _cli("--root", str(tmp_path), "snapshot", "lighten") == 0  # the latest closed Snapshot
    assert (snap.parent / "S1.light.zip").is_file()
    assert _cli("--root", str(tmp_path), "snapshot", "verify-light", "S1") == 0
    assert _cli("--root", str(tmp_path), "build", "--snapshot", "S1") == 0
    assert _cli("--root", str(tmp_path), "build", "--snapshot", "S1", "--from-raw") == 0
    forms = sorted(json.loads(p.read_text(encoding="utf-8"))["snapshot_form"]
                   for p in (tmp_path / "builds" / "S1").glob("*/datasets/build.json"))
    assert forms == ["lightweight", "raw"]


def test_gitignore_covers_the_lightweight_zip():
    from conftest import REPO

    text = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "/snapshots/" in text or "snapshots/*.light.zip" in text
