"""Datasets, List Size and Tag Depth as Build settings."""

from __future__ import annotations

import copy
import tomllib

import pytest

from helpers import World
from steamstudy.analysis.templates import wording
from steamstudy.build.core import BuildFailed, build
from steamstudy.build.games import counted_tags
from steamstudy.config import ALL_FILES, ConfigError, config_from_data, load_config
from steamstudy.export.writer import read_csv
from steamstudy.snapshot import Snapshot


def _files(config_dir):
    return {n: tomllib.loads((config_dir / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}


def _cfg(config_dir, *, datasets=None, **datasets_keys):
    files = _files(config_dir)
    if datasets is not None:
        files["datasets"]["dataset"] = datasets
    files["datasets"].update(datasets_keys)
    return config_from_data(files, directory=config_dir)


def _datasets(config_dir):
    return copy.deepcopy(_files(config_dir)["datasets"]["dataset"])


def _tags(*ids):
    return [(i, f"tag {i}") for i in ids]


# ----------------------------------------------------------------------------- config


def test_the_default_config_sets_neither_list_size_nor_tag_depth(config_dir):
    files = _files(config_dir)
    assert "tag_depth" not in files["datasets"]
    assert all("list_size" not in d for d in files["datasets"]["dataset"])  # so no build_config_hash moves
    cfg = load_config(config_dir)
    assert cfg.tag_depth == "all" and cfg.depth_cut is None
    assert {d.list_size for d in cfg.datasets} == {100}


def test_tag_depth_and_list_size_are_read(config_dir):
    ds = _datasets(config_dir)
    ds[0]["list_size"] = 150
    cfg = _cfg(config_dir, datasets=ds, tag_depth=10)
    assert cfg.tag_depth == 10 and cfg.depth_cut == 10 and cfg.datasets[0].list_size == 150
    assert _cfg(config_dir, tag_depth="all").tag_depth == "all"


@pytest.mark.parametrize("depth", [1, 0, -2, 21, 2.5, "ten", True])
def test_a_bad_tag_depth_is_refused(config_dir, depth):
    with pytest.raises(ConfigError, match="tag_depth"):
        _cfg(config_dir, tag_depth=depth)


@pytest.mark.parametrize("size", [9, 0, -1, "100", 100.5, True])
def test_a_bad_list_size_is_refused(config_dir, size):
    ds = _datasets(config_dir)
    ds[1]["list_size"] = size
    with pytest.raises(ConfigError, match="list_size"):
        _cfg(config_dir, datasets=ds)


def test_dataset_validation(config_dir):
    ds = _datasets(config_dir)

    def check(mutate, match):
        d = copy.deepcopy(ds)
        mutate(d)
        with pytest.raises(ConfigError, match=match):
            _cfg(config_dir, datasets=d)

    check(lambda d: d[1].update(key="Puzzle!"), "a-z, 0-9 and _")
    check(lambda d: d[2].update(key="puzzle"), "duplicate dataset keys")
    check(lambda d: d[1].update(label="  "), "label")
    check(lambda d: d.__setitem__(slice(0, 2), [d[1], d[0]]), "listed first")
    check(lambda d: d[2].pop("defining_tag"), "exactly one dataset must have no defining tag")
    check(lambda d: d[0].update(key="all", defining_tag=None), "key must be 'overall'")
    check(lambda d: d[2].update(defining_tag=d[1]["defining_tag"]), "defining tag may be used by one dataset")
    check(lambda d: d.pop(0), "exactly one dataset must have no defining tag")


def test_a_parameter_grid_with_no_pairs_is_refused(config_dir):
    files = _files(config_dir)
    files["network"]["parameter_selection"]["g_range"] = [2, 6]
    files["network"]["parameter_selection"]["s_range"] = [7, 12]
    with pytest.raises(ConfigError, match="no \\(g, s\\) pairs"):
        config_from_data(files, directory=config_dir)


def test_counted_tags_keeps_the_first_depth_tags():
    tags = tuple(range(1, 8))
    assert counted_tags(tags, None) == tags and counted_tags(tags, 3) == (1, 2, 3) and counted_tags(tags, 99) == tags


# ----------------------------------------------------------------------------- Tag Depth


def _depth_world():
    w = World()
    w.add(1, avg=900.0, name="Puzzle 11th", tags=_tags(*range(100, 110), 1664))  # defining tag at position 11
    w.add(2, avg=800.0, name="Puzzle 3rd", tags=_tags(100, 101, 1664, 102))
    w.add(3, avg=700.0, name="Dating 14th", tags=_tags(*range(100, 113)) + [(9551, "Dating Sim"), (1664, "Puzzle")])  # excluding tag at 14
    return w


def test_tag_depth_cuts_membership_but_not_exclusions(tmp_path, config_dir):
    result = build(Snapshot(_depth_world().snapshot(tmp_path / "snap")), _cfg(config_dir, tag_depth=10), "B1")
    puzzle = [r["appid"] for r in result.rows("datasets/top100_puzzle.csv")]
    assert puzzle == [2]  # the game whose Puzzle is 11th is not in the dataset
    overall = [r["appid"] for r in result.rows("datasets/top100_overall.csv")]
    assert overall == [1, 2]  # game 3 is still excluded by Dating Sim at position 14 (full list)
    reasons = {r["appid"]: r["reason"] for r in result.rows("reports/exclusions.csv")}
    assert reasons == {3: "dating_sim_tag"}
    # Files keep the full tag lists; the analysis counts the first ten.
    full = next(r for r in result.rows("datasets/top100_overall.csv") if r["appid"] == 1)
    assert len(full["tag_ids"]) == 11
    freq = {r["tag_id"]: r["count"] for r in result.rows("analysis/tag_frequency.csv") if r["dataset"] == "overall"}
    assert freq[1664] == 1 and freq[100] == 2  # game 1's Puzzle is 11th, so only game 2 counts it


def test_the_default_depth_keeps_the_game_in_the_dataset(tmp_path, config_dir):
    result = build(Snapshot(_depth_world().snapshot(tmp_path / "snap")), load_config(config_dir), "B1")
    assert sorted(r["appid"] for r in result.rows("datasets/top100_puzzle.csv")) == [1, 2]


def test_impact_removals_notes_a_tag_beyond_depth(tmp_path, config_dir):
    result = build(Snapshot(_depth_world().snapshot(tmp_path / "snap")), _cfg(config_dir, tag_depth=10), "B1")
    signals = [r["signal"] for r in result.rows("reports/impact_removals.csv")]
    assert signals == ["Dating Sim (beyond tags per game)"]
    plain = build(Snapshot(_depth_world().snapshot(tmp_path / "snap2")), load_config(config_dir), "B1")
    assert [r["signal"] for r in plain.rows("reports/impact_removals.csv")] == ["Dating Sim"]


# ----------------------------------------------------------------------------- List Size


def _crowd(n):
    w = World()
    for i in range(n):
        w.add(1000 + i, avg=5000.0 - i, tags=_tags(19, 1664, 100 + i % 7))
    return w


def test_a_pool_smaller_than_list_size_fails_a_full_build_naming_the_dataset(tmp_path, config_dir):
    snap = _crowd(40).snapshot(tmp_path / "snap", mode="full")
    ds = _datasets(config_dir)[:2]
    ds[0]["list_size"] = 50
    ds[1]["list_size"] = 10
    with pytest.raises(BuildFailed, match=r"dataset overall has only 40 eligible games; every dataset must hold exactly 50"):
        build(Snapshot(snap), _cfg(config_dir, datasets=ds), "B1")


def test_a_test_build_only_warns(tmp_path, config_dir):
    snap = _crowd(40).snapshot(tmp_path / "snap", mode="test")
    ds = _datasets(config_dir)[:2]
    ds[0]["list_size"] = 50
    result = build(Snapshot(snap), _cfg(config_dir, datasets=ds), "B1")
    assert any("overall has only 40 eligible games" in w and "test Build" in w and "exactly 50" in w for w in result.warnings)
    assert len(result.rows("datasets/top100_overall.csv")) == 40


def test_list_size_150_and_ties_at_the_cutoff(tmp_path, config_dir):
    w = _crowd(160)
    snap = w.snapshot(tmp_path / "snap", mode="full")
    ds = _datasets(config_dir)[:2]
    ds[0]["list_size"] = 150
    ds[1]["list_size"] = 20
    result = build(Snapshot(snap), _cfg(config_dir, datasets=ds), "B1")
    assert len(result.rows("datasets/top100_overall.csv")) == 150
    assert len(result.rows("datasets/top100_puzzle.csv")) == 20
    assert result.build_json["dataset_sizes"]["overall"] == {"rows": 150, "eligible_pool": 160}
    assert wording(_cfg(config_dir, datasets=ds))["top"] == "Top-N"


def test_wording_writes_100_only_when_every_size_is_100(config_dir):
    assert wording(load_config(config_dir)) == {"top": "Top 100", "top_h": "Top-100", "cutoff": "rank 100",
                                                "number": "five"}
    ds = _datasets(config_dir)
    ds[2]["list_size"] = 20
    w = wording(_cfg(config_dir, datasets=ds))
    assert (w["top"], w["top_h"], w["cutoff"], w["number"]) == ("Top-N", "Top-N", "the last rank", "five")


def test_other_list_sizes_reach_the_report_text(tmp_path, config_dir):
    ds = _datasets(config_dir)[:2]
    ds[0]["list_size"] = 20
    ds[1]["list_size"] = 10
    result = build(Snapshot(_crowd(40).snapshot(tmp_path / "snap", mode="test")), _cfg(config_dir, datasets=ds), "B1")
    html = result.texts["analysis/report.html"]
    assert "Top-N" in html and "Top-100" not in html and "Top 100" not in html and "two published" in html
    assert "Top-100" not in result.texts["reports/reports.html"]


# ----------------------------------------------------------------------------- more datasets


def test_a_sixth_dataset_adds_a_would_be_rank_column_in_config_order(tmp_path, config_dir):
    ds = _datasets(config_dir)
    ds.insert(2, {"key": "action", "label": "Action", "defining_tag": {"id": 19, "name": "Action"}})
    w = _crowd(30)
    w.add(1, avg=10.0, app_type="dlc", tags=_tags(19, 1664))  # excluded, so it has would-be ranks
    result = build(Snapshot(w.snapshot(tmp_path / "snap")), _cfg(config_dir, datasets=ds), "B1")
    columns = [c for c in result.tables["reports/exclusions.csv"][0].column_names if c.startswith("would_be_rank_")]
    assert columns == ["would_be_rank_overall", "would_be_rank_puzzle", "would_be_rank_action", "would_be_rank_rpg",
                       "would_be_rank_strategy", "would_be_rank_simulation"]
    for path in ("impact_removals", "impact_near_misses", "impact_adult_signals"):
        names = result.tables[f"reports/{path}.csv"][0].column_names
        assert [c for c in names if c.startswith("would_be_rank_")] == columns
    row = result.rows("reports/exclusions.csv")[0]
    assert row["would_be_rank_action"] is not None and row["would_be_rank_action"] > 1
    assert "datasets/top100_action.csv" in result.tables


def test_a_dataset_can_be_dropped(tmp_path, config_dir):
    ds = _datasets(config_dir)[:2]
    result = build(Snapshot(_crowd(30).snapshot(tmp_path / "snap")), _cfg(config_dir, datasets=ds), "B1")
    assert [p for p in result.tables if p.startswith("datasets/top100_")] == [
        "datasets/top100_overall.csv", "datasets/top100_puzzle.csv"]
    names = result.tables["reports/exclusions.csv"][0].column_names
    assert [c for c in names if c.startswith("would_be_rank_")] == ["would_be_rank_overall", "would_be_rank_puzzle"]


def test_written_files_validate_against_the_expanded_schema(tmp_path, config_dir):
    from steamstudy.build.writer import write_build

    ds = _datasets(config_dir)[:2]
    folder = write_build(build(Snapshot(_crowd(30).snapshot(tmp_path / "snap")), _cfg(config_dir, datasets=ds), "B1"),
                         tmp_path)
    header = read_csv(folder / "reports" / "impact_near_misses.csv")
    assert header == []  # no near misses here; the header row was still validated on write
