"""Ticket 09 and 22: repair, gate records, the template/causal-word component, reports.html and report.html."""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
import tomllib

import pytest

from conftest import neutral_collection
from helpers import World, captured, raw
from steamstudy.analysis.templates import CausalLanguageError, causal_hits, fmt, render_report
from steamstudy.build.core import BuildFailed, build
from steamstudy.collect.fetcher import FakeClock, FakeTransport, HardStop, RawResponse
from steamstudy.collect.run import CollectRefused, run_collect, run_repair
from steamstudy.config import ALL_FILES, GateRecord, config_from_data, load_config
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world
from test_collect import TODAY, _test_cfg, _world

WORDS = ["drives", "leads to", "makes ... successful", "key to success", "predicts", "because", "effect"]


@pytest.fixture
def config(config_dir):
    return neutral_collection(load_config(config_dir))


# ----------------------------------------------------------------------------- repair and gate


def _closed_snapshot(tmp_path, config):
    return run_collect(tmp_path, _test_cfg(config), mode="test", transport=FakeTransport(_world()), clock=FakeClock(),
                       today=TODAY)


def test_repair_refetches_one_app_and_is_logged(tmp_path, config):
    sid = _closed_snapshot(tmp_path, config)
    routes = _world()
    transport = FakeTransport(routes)
    repair = run_repair(tmp_path, _test_cfg(config), 10, "page changed after collection", snapshot_id=sid,
                        transport=transport, clock=FakeClock())
    assert {c.url for c in transport.calls} == {
        "https://steamcharts.com/app/10", "https://store.steampowered.com/app/10/?l=english",
        "https://store.steampowered.com/api/appdetails?appids=10&l=english"}
    meta = Snapshot(tmp_path / "snapshots" / sid).meta
    assert meta["repairs"] == [repair] and repair["reason"] == "page changed after collection"
    assert repair["batch"] == "repair-1" and meta["closed"] is True


def test_repair_needs_a_reason_a_closed_snapshot_and_a_pool_app(tmp_path, config):
    sid = _closed_snapshot(tmp_path, config)
    with pytest.raises(CollectRefused, match="reason"):
        run_repair(tmp_path, _test_cfg(config), 10, " ", snapshot_id=sid, transport=FakeTransport({}))
    with pytest.raises(CollectRefused, match="not in"):
        run_repair(tmp_path, _test_cfg(config), 424242, "x", snapshot_id=sid, transport=FakeTransport({}))
    routes = _world()
    routes["https://steamcharts.com/app/11"] = RawResponse(429, "x", b"")
    with pytest.raises(HardStop):
        run_collect(tmp_path / "open", _test_cfg(config), mode="test", transport=FakeTransport(routes),
                    clock=FakeClock(), today=TODAY)
    with pytest.raises(CollectRefused, match="still open"):
        run_repair(tmp_path / "open", _test_cfg(config), 10, "x", transport=FakeTransport({}))


def test_full_run_records_the_gate_references(tmp_path, config):
    c = dataclasses.replace(_test_cfg(config).collection, operator_reply=GateRecord("email 2026-10-07", "2026-10-07"),
                            ethics_check=GateRecord("REC-42", "2026-10-08"), listing_passes=1)
    sid = run_collect(tmp_path, dataclasses.replace(config, collection=c), mode="full",
                      transport=FakeTransport(_world()), clock=FakeClock(), today=TODAY)
    gate = Snapshot(tmp_path / "snapshots" / sid).meta["gate"]
    assert gate == {"operator_reply": {"reference": "email 2026-10-07", "date": "2026-10-07"},
                    "ethics_check": {"reference": "REC-42", "date": "2026-10-08"}}


# ----------------------------------------------------------------------------- templates


@pytest.mark.parametrize("text, hit", [
    ("Strategy drives play time.", "drives"), ("This tag leads to more players.", "leads to"),
    ("Co-op makes a game successful.", "makes ... successful"), ("A key to success.", "key to success"),
    ("The tag predicts rank.", "predicts"), ("Because of the tag.", "because"), ("A strong effect.", "effect"),
])
def test_causal_words_are_found(text, hit):
    assert causal_hits(text, WORDS) == [hit]


def test_harmless_words_pass():
    assert causal_hits("Effective cooperation. It makes sense. A successful run.", WORDS) == []


def test_a_causal_template_fails_the_render():
    with pytest.raises(CausalLanguageError, match="drives"):
        render_report("t", ["Open world drives retention."], WORDS)


def test_fmt():
    assert (fmt(0.123456), fmt(0.004), fmt(None), fmt(True), fmt(12)) == ("0.12", "0.004", "n/a", "yes", "12")


# ----------------------------------------------------------------------------- Build reports


@pytest.fixture(scope="module")
def report_build(tmp_path_factory):
    config = load_config(__import__("conftest").CONFIG_DIR)
    root = tmp_path_factory.mktemp("r")
    result = build(Snapshot(tagged_world().snapshot(root / "snap")), config, "B-report")
    return result, config


def test_reports_html_summarises_the_build(report_build):
    result, _ = report_build
    page = result.texts["reports/reports.html"]
    assert "This is a test Build" in page and "Player data: Steam Charts; tags/metadata: Steam store" in page
    pool = next(r["value"] for r in result.rows("reports/completeness.csv") if r["item"] == "candidate_pool")
    assert f"The Candidate Pool holds {pool} apps" in page


def test_report_html_numbers_come_from_the_csvs(report_build):
    result, _ = report_build
    page = result.texts["analysis/report.html"]
    top_tag = next(r for r in result.rows("analysis/tag_frequency.csv") if r["dataset"] == "overall")
    assert f"{top_tag['tag']} appears in {top_tag['count']} of the 100 games " \
           f"(Eligible Pool: {top_tag['baseline_share'] * 100:.0f}%)" in page
    q = next(r for r in result.rows("analysis/network_cluster_quality.csv") if r["dataset"] == "overall")
    assert f"Q (γ = 1.00) {fmt(q['modularity'])} vs null {fmt(q['q_null_mean'])}" in page
    assert result.analysis_json["datasets"]["overall"]["state_id"] in page
    assert "Puzzle is not a Steam store genre" in page
    assert "No consensus partition was computed" in page and "User Guide chapter 6" in page
    assert not re.search(r"signific", page, re.IGNORECASE)


def test_a_causal_word_in_the_report_fails_the_build(tmp_path, config_dir):
    files = {n: tomllib.loads((config_dir / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}
    files["analysis"]["causal_words"] = ["co-occurs"]
    with pytest.raises(BuildFailed, match="causal language: co-occurs"):
        build(Snapshot(tagged_world().snapshot(tmp_path / "snap")), config_from_data(files), "B1")


def test_build_json_full_provenance(report_build):
    result, config = report_build
    bj = result.build_json
    assert bj["changelog"][0]["date"] == "2026-10-04"
    assert bj["source_substitutions"][0]["confirmed"] == "2026-10-03"
    assert bj["taglist_version_hash"] == "711684454" and bj["mode"] == "test"
