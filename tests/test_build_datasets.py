"""Seam 2: store data, ranking and the Top-100 Datasets, through `build(snapshot, config)`."""

from __future__ import annotations

import pytest

from helpers import World, raw, steamcharts_page
from steamstudy.build.core import BuildFailed, build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.export.writer import read_csv
from steamstudy.snapshot import Snapshot

PUZZLE, RPG = (1664, "Puzzle"), (122, "RPG")


@pytest.fixture
def config(config_dir):
    return load_config(config_dir)


def _fillers(world: World, n: int, start: int = 100000, base: float = 5000.0, tags=((19, "Action"),)):
    for i in range(n):
        world.add(start + i, avg=base - i, tags=list(tags))
    return world


def _build(tmp_path, world, config, **kw):
    return build(Snapshot(world.snapshot(tmp_path / "snap")), config, "B1", **kw)


def test_exactly_100_rows_in_rank_order(tmp_path, config):
    result = _build(tmp_path, _fillers(World(), 130), config)
    rows = result.rows("datasets/top100_overall.csv")
    assert len(rows) == 100
    assert [r["rank"] for r in rows] == list(range(1, 101))
    assert [r["appid"] for r in rows] == [100000 + i for i in range(100)]


def test_tie_breaks_and_ties_at_rank_100(tmp_path, config):
    world = _fillers(World(), 98)  # ranks 1-98, scores 5000..4903
    # Four games share the score at rank 99-100: months_observed desc, then appid asc decides.
    world.add(9, avg=10.0, months=12).add(7, avg=10.0, months=24).add(8, avg=10.0, months=12).add(6, avg=10.0, months=6)
    world.add(5, avg=1.0)
    result = _build(tmp_path, world, config)
    rows = result.rows("datasets/top100_overall.csv")
    assert [r["appid"] for r in rows[-2:]] == [7, 8]
    ties = result.rows("reports/ties.csv")
    assert [(t["appid"], t["position"]) for t in ties if t["dataset"] == "overall"] == [(9, 101), (6, 102)]


def test_tag_specific_datasets_need_the_exact_defining_tag(tmp_path, config):
    world = World()
    world.add(1, avg=50.0, tags=[PUZZLE, (19, "Action")])
    world.add(2, avg=60.0, tags=[(1738, "Hidden Object")])  # a puzzle sub-genre, not the Puzzle tag
    world.add(3, avg=40.0, tags=[(19, "Action")] * 0 + [(4182, "Singleplayer")] * 1 + [PUZZLE])
    result = _build(tmp_path, world, config)
    puzzle = result.rows("datasets/top100_puzzle.csv")
    assert [r["appid"] for r in puzzle] == [1, 3]
    assert [r["appid"] for r in result.rows("datasets/top100_overall.csv")] == [2, 1, 3]
    assert result.build_json["dataset_sizes"]["puzzle"] == {"rows": 2, "eligible_pool": 2}


def test_top100_contract(tmp_path, config):
    world = World().add(2, is_free=True, avg=5.0)
    history = steamcharts_page([("2025-10", 1.0, 2), ("2025-11", 2.0, 3), ("2025-12", 2.0, 3)])
    world.add(1, history=history, tags=[(19, "Action"), (492, "Indie")], genres=[(1, "Action"), (23, "Indie")],
              release_date="5 Mar, 2025")
    folder = write_build(_build(tmp_path, world, config), tmp_path)
    rows = read_csv(folder / "datasets" / "top100_overall.csv")
    assert list(rows[0].keys()) == [
        "dataset", "rank", "appid", "name", "mean_monthly_players", "months_observed", "release_month",
        "store_release_date", "is_free", "app_type", "tag_ids", "tags", "genre_ids", "genres", "content_flags",
        "metadata_source", "top_listing_rank"]
    game = next(r for r in rows if r["appid"] == "1")
    assert game["mean_monthly_players"] == "1.666667"
    assert game["release_month"] == "2025-10" and game["store_release_date"] == "5 Mar, 2025"
    assert (game["tag_ids"], game["tags"]) == ("19;492", "Action;Indie")
    assert (game["genre_ids"], game["genres"]) == ("1;23", "Action;Indie")
    assert game["metadata_source"] == "store" and game["is_free"] == "false" and game["app_type"] == "game"
    free = next(r for r in rows if r["appid"] == "2")
    assert free["is_free"] == "true" and free["top_listing_rank"] == "1"
    assert (folder / "datasets" / "top100_simulation.csv").is_file()


def test_semicolon_in_a_name_fails_the_build(tmp_path, config):
    world = World().add(1, tags=[(19, "Action;Adventure")])
    with pytest.raises(BuildFailed, match="';'"):
        _build(tmp_path, world, config)


def test_apps_without_store_data_or_tags_do_not_rank(tmp_path, config):
    world = World()
    world.add(1, avg=100.0)
    world.add(2, avg=900.0, page="no_store_page")
    world.add(3, avg=800.0, page="age_gate")
    world.add(4, avg=700.0, details="no_appdetails")
    world.add(5, avg=600.0, tags=[])
    result = _build(tmp_path, world, config)
    assert [r["appid"] for r in result.rows("datasets/top100_overall.csv")] == [1]


def test_monthly_players_holds_the_scored_months_without_placeholders(tmp_path, config):
    history = steamcharts_page([("2017-01", 0.0, 0), ("2024-01", 10.0, 20), ("2024-02", 0.0, 0), ("2024-03", 30.0, 50),
                                ("2026-10", 99.0, 99)])
    result = _build(tmp_path, World().add(749110, history=history), config)
    rows = result.rows("datasets/monthly_players.csv")
    assert [(r["month"], r["avg_players"], r["peak_players"]) for r in rows] == [("2024-01", 10.0, 20), ("2024-03", 30.0, 50)]
    assert result.rows("datasets/top100_overall.csv")[0]["mean_monthly_players"] == 20.0


def test_release_month_check_for_early_access(tmp_path, config):
    world = World().real(1086940)  # Baldur's Gate 3: Steam Charts from Oct 2020, store date 3 Aug, 2023
    world.add(1, months=3, release_date="1 Jul, 2026")  # Release Month 2026-07: 0 months apart, not listed
    world.add(2, months=3, release_date="Coming soon")  # unreadable store date: listed with an empty months_apart
    rows = {r["appid"]: r for r in _build(tmp_path, world, config).rows("reports/release_month_check.csv")}
    assert rows[1086940] == {"appid": 1086940, "release_month": "2020-10", "store_release_date": "3 Aug, 2023",
                             "months_apart": 34}
    assert 1 not in rows and rows[2]["months_apart"] is None


def test_tag_vocabulary(tmp_path, config):
    world = World().add(1, tags=[(19, "Action"), (999999999, "Unknown Tag")]).add(2, tags=[(19, "Action")])
    rows = _build(tmp_path, world, config).rows("reports/tag_vocabulary.csv")
    action = next(r for r in rows if r["kind"] == "tag" and r["id"] == 19)
    assert action["app_count"] == 2 and action["in_vocabulary"] is True
    assert next(r for r in rows if r["id"] == 999999999)["in_vocabulary"] is False
    assert next(r for r in rows if r["kind"] == "genre")["in_vocabulary"] is None


def test_real_store_page_and_appdetails_parsing(tmp_path, config):
    result = _build(tmp_path, World().real(413150), config)
    game = result.games[413150]
    assert game.name == "Stardew Valley" and game.app_type == "game" and game.is_free is False
    assert [t.name for t in game.tags][:3] == ["Farming Sim", "Pixel Graphics", "Multiplayer"]
    assert [(g.genre_id, g.name) for g in game.genres] == [(23, "Indie"), (3, "RPG"), (28, "Simulation")]
    assert game.release_date == "26 Feb, 2016"


def test_fewer_than_100_eligible_games_warns(tmp_path, config):
    result = _build(tmp_path, World().add(1), config)
    assert any("overall has only 1 eligible games" in w for w in result.warnings)


def test_determinism(tmp_path, config):
    world = _fillers(World().real(413150).real(1086940), 20)
    path = world.snapshot(tmp_path / "snap")
    a = write_build(build(Snapshot(path), config, "B-a"), tmp_path)
    b = write_build(build(Snapshot(path), config, "B-b"), tmp_path)
    for folder in ("datasets", "reports"):
        for f in (a / folder).glob("*.csv"):
            assert f.read_bytes() == (b / folder / f.name).read_bytes(), f.name
