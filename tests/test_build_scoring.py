"""Seam 2 (part 1): parsing, scoring and the Build skeleton, through `build(snapshot, config)`."""

from __future__ import annotations

import json
import socket

import pytest

from helpers import make_snapshot, raw, steamcharts_page, top_page
from steamstudy.build.core import BuildFailed, build
from steamstudy.build.parse import parse_steamcharts_app
from steamstudy.build.score import Window, score
from steamstudy.build.writer import BuildExists, resolve_build, write_build
from steamstudy.config import load_config
from steamstudy.export.writer import read_csv
from steamstudy.snapshot import Snapshot

WINDOW = Window("2021-10", "2026-09")

# Derived cases (Steam Charts returned 500 at capture time; see tests/fixtures/README.md).
BOLD_BLADE = steamcharts_page([("2024-01", 10.0, 20), ("2024-02", 0.0, 0), ("2024-03", 30.0, 50)], name="Bold Blade")
BLACK_HOLE = steamcharts_page([], name="Black Hole Simulator")
DADISH = steamcharts_page([], name="Dadish 3D")


@pytest.fixture
def config(config_dir):
    return load_config(config_dir)


def _snapshot(tmp_path, extra: dict[str, tuple[str, bytes | None]] | None = None):
    listing = top_page([(1, 413150, "Stardew Valley"), (2, 698670, "Scorn"), (3, 749110, "Bold Blade"),
                        (4, 1401150, "Black Hole Simulator"), (5, 2888870, "Dadish 3D"), (6, 999999990, "Gone")])
    responses = {
        "steamcharts/top/pass-1/p-0001.html.gz": ("ok", listing),
        "steamcharts/top/pass-1/p-0002.html.gz": ("end_of_listing", b"404"),
        "steamcharts/app/413150.html.gz": ("ok", raw("steamcharts/app/413150.html.gz")),
        "steamcharts/app/698670.html.gz": ("ok", raw("steamcharts/app/698670.html.gz")),
        "steamcharts/app/749110.html.gz": ("ok", BOLD_BLADE),
        "steamcharts/app/1401150.html.gz": ("ok", BLACK_HOLE),
        "steamcharts/app/2888870.html.gz": ("ok", DADISH),
        "steamcharts/app/999999990.html.gz": ("not_found", raw("steamcharts/app/999999990.html.gz")),
        "steamcharts/app/1086940.html.gz": ("ok", raw("steamcharts/app/1086940.html.gz")),
    }
    responses.update(extra or {})
    return Snapshot(make_snapshot(tmp_path / "snap", responses, extra_appids=[1086940]))


# ----------------------------------------------------------------------------- parser


def test_last_30_days_is_skipped_and_months_are_chronological():
    history = parse_steamcharts_app(raw("steamcharts/app/698670.html.gz"))
    assert history.name == "Scorn"
    assert all(r.month[:4].isdigit() for r in history.rows)
    assert [r.month for r in history.rows] == sorted(r.month for r in history.rows)
    assert history.rows[-1].month == "2026-09" and history.errors == ()


def test_unknown_labels_and_duplicate_months_are_parse_errors():
    page = steamcharts_page([("2024-01", 1.0, 2)], extra_labels=["Smarch 2024", "January 2024"])
    history = parse_steamcharts_app(page)
    assert any("unknown row label 'Smarch 2024'" in e for e in history.errors)
    assert any("duplicate month 'January 2024'" in e for e in history.errors)


# ----------------------------------------------------------------------------- score()


def _history(rows):
    return parse_steamcharts_app(steamcharts_page(rows))


def test_placeholder_rows_are_absent_wherever_they_are():
    h = _history([("2022-01", 0.0, 0), ("2022-02", 10.0, 12), ("2022-03", 0.0, 0), ("2022-04", 20.0, 25),
                  ("2022-05", 0.0, 0)])
    s = score(h, WINDOW)
    assert (s.release_month, s.months_observed, s.mean_monthly_players) == ("2022-02", 2, 15.0)


def test_zero_average_with_a_peak_is_data():
    s = score(_history([("2022-01", 0.0, 1), ("2022-02", 10.0, 12)]), WINDOW)
    assert (s.release_month, s.months_observed, s.mean_monthly_players) == ("2022-01", 2, 5.0)


def test_months_outside_the_window_are_ignored_and_missing_months_stay_missing():
    h = _history([("2021-08", 1000.0, 2000), ("2021-12", 4.0, 5), ("2023-06", 8.0, 9), ("2026-10", 9999.0, 9999)])
    s = score(h, WINDOW)
    assert (s.release_month, s.months_observed, s.mean_monthly_players) == ("2021-08", 2, 6.0)


def test_unscored_apps():
    assert score(_history([]), WINDOW) is None
    assert score(_history([("2020-01", 0.0, 0)]), WINDOW) is None
    assert score(_history([("2019-01", 5.0, 6)]), WINDOW) is None


# ----------------------------------------------------------------------------- build()


def _rows(result, path):
    return result.rows(path)


def test_real_fixture_histories(tmp_path, config):
    result = build(_snapshot(tmp_path), config, "B1")
    placeholders = _rows(result, "reports/placeholder_rows.csv")
    assert {"appid": 698670, "month": "2017-09", "position": "leading"} in placeholders
    assert {"appid": 749110, "month": "2024-02", "position": "interior"} in placeholders
    completeness = {r["item"]: r["value"] for r in _rows(result, "reports/completeness.csv")}
    # Stardew, Scorn, Bold Blade and Baldur's Gate 3 are scored; Black Hole Simulator and Dadish 3D have
    # no month rows (Dadish has only "Last 30 Days"); 999999990 is a Steam Charts 404.
    assert completeness["scored_apps"] == 4
    assert completeness["unscored_no_month_rows"] == 2
    assert completeness["unscored_not_found"] == 1
    assert completeness["placeholder_rows"] == 2
    assert completeness["candidate_pool"] == 7 and completeness["extra_appids"] == 1
    assert completeness["listing_rows"] == 6


def test_scorn_and_stardew_scores(tmp_path, config):
    snap = _snapshot(tmp_path)
    scorn = score(parse_steamcharts_app(snap.response("steamcharts/app/698670.html.gz").body), WINDOW)
    assert (scorn.release_month, scorn.months_observed) == ("2022-10", 48)  # Sep 2017 placeholder ignored
    stardew = score(parse_steamcharts_app(snap.response("steamcharts/app/413150.html.gz").body), WINDOW)
    assert stardew.release_month == "2015-12"  # tiny pre-launch rows (0.60, 0.53) count as data


def test_parse_errors_fail_the_build(tmp_path, config):
    bad = steamcharts_page([("2024-01", 1.0, 2)], extra_labels=["Smarch 2024"])
    snap = _snapshot(tmp_path, {"steamcharts/app/413150.html.gz": ("ok", bad)})
    with pytest.raises(BuildFailed) as info:
        build(snap, config, "B1")
    assert info.value.parse_errors[0]["appid"] == 413150


def test_allow_parse_errors_treats_apps_as_unscored_and_is_recorded(tmp_path, config):
    bad = steamcharts_page([("2024-01", 1.0, 2)], extra_labels=["Smarch 2024"])
    snap = _snapshot(tmp_path, {"steamcharts/app/413150.html.gz": ("ok", bad)})
    result = build(snap, config, "B1", allow_parse_errors=True)
    assert result.build_json["parse_errors_allowed"] is True and result.build_json["parse_error_count"] == 1
    assert len(_rows(result, "reports/parse_errors.csv")) == 1
    completeness = {r["item"]: r["value"] for r in _rows(result, "reports/completeness.csv")}
    assert completeness["scored_apps"] == 3 and completeness["unscored_parse_error"] == 1


def test_build_makes_no_network_access(tmp_path, config, monkeypatch):
    snap = _snapshot(tmp_path)

    def refuse(*args, **kwargs):
        raise AssertionError("network access during a Build")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    build(snap, config, "B1")


def test_build_json_provenance(tmp_path, config):
    bj = build(_snapshot(tmp_path), config, "B1").build_json
    assert bj["snapshot_id"] == "snap" and bj["build_id"] == "B1" and bj["mode"] == "test"
    assert bj["build_config_hash"] == config.build_config_hash
    assert set(bj["config"]) >= {"network", "exclusions", "datasets", "analysis", "genres"}
    assert bj["parse_errors_allowed"] is False and "python" in bj["software_versions"]
    assert bj["attribution"] == "Player data: Steam Charts; tags/metadata: Steam store"


def test_writer_layout_never_overwrites_and_maintains_latest(tmp_path, config):
    snap = _snapshot(tmp_path)
    folder = write_build(build(snap, config, "20261004T000000Z-abcdef12"), tmp_path)
    assert folder == tmp_path / "builds" / "snap" / "20261004T000000Z-abcdef12"
    assert (folder / "reports" / "parse_errors.csv").is_file()
    assert read_csv(folder / "reports" / "placeholder_rows.csv")[0].keys() == {"appid", "month", "position"}
    assert json.loads((folder / "datasets" / "build.json").read_text(encoding="utf-8"))["build_id"] == folder.name
    with pytest.raises(BuildExists):
        write_build(build(snap, config, "20261004T000000Z-abcdef12"), tmp_path)
    second = write_build(build(snap, config, "20261004T000001Z-abcdef12"), tmp_path)
    assert resolve_build(tmp_path) == second
    assert resolve_build(tmp_path, folder.name) == folder
