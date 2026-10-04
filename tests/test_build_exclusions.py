"""Seam 2: Exclusion rules, overrides, Content Flags, Manual Metadata Entries and the impact report."""

from __future__ import annotations

import tomllib

import pytest

from helpers import World, steamcharts_page
from steamstudy.build.core import BuildFailed, build
from steamstudy.config import ALL_FILES, config_from_data
from steamstudy.snapshot import Snapshot

EVIDENCE = [{"url": "https://store.steampowered.com/app/2923300/", "retrieved": "2026-10-05"}]
KARRYN_HISTORY = steamcharts_page([("2026-07", 900.0, 1500), ("2026-08", 900.0, 1500), ("2026-09", 900.0, 1500)])
WALLPAPER_HISTORY = steamcharts_page([("2026-08", 800.0, 900), ("2026-09", 800.0, 900)])


def _config(config_dir, **patch):
    files = {n: tomllib.loads((config_dir / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}
    for name, value in patch.items():
        files[name] = {**files[name], **value}
    return config_from_data(files, directory=config_dir)


def _world():
    """Real fixture games plus synthetic ones for the cases the fixtures lack."""
    w = World()
    w.real(413150)  # Stardew Valley: Dating Sim at position 17
    w.real(3419430)  # Bongo Cat: Desktop Companion (1) and Software (18)
    w.real(2923300)  # Banana: Dating Sim at position 18
    w.real(1619750, history=KARRYN_HISTORY)  # Karryn's Prison: Adult Only notice, descriptor 3, Hentai at 2
    w.real(431960, history=WALLPAPER_HISTORY)  # Wallpaper Engine: Utilities, Software, ... and Dating Sim at 20
    w.real(698670)  # Scorn: Sexual Content and Nudity tags (never exclusion grounds; a Content Flag)
    w.add(1, avg=500.0, page="no_store_page", name="Delisted")  # no store data
    w.add(2, avg=400.0, tags=[], name="No Tags")
    w.add(3, avg=300.0, app_type="dlc", tags=[(9551, "Dating Sim")], name="A DLC")
    w.add(4, avg=200.0, descriptors=[3], name="Descriptor Three")
    return w


def _build(tmp_path, config, world=None, **kw):
    return build(Snapshot((world or _world()).snapshot(tmp_path / "snap")), config, "B1", **kw)


def _reasons(result):
    out: dict[int, list[str]] = {}
    for r in result.rows("reports/exclusions.csv"):
        out.setdefault(r["appid"], []).append(r["reason"])
    return out


def test_every_rule_with_all_reasons_and_primary_reason(tmp_path, config_dir):
    result = _build(tmp_path, _config(config_dir))
    reasons = _reasons(result)
    assert reasons[413150] == ["dating_sim_tag"]
    assert reasons[3419430] == ["software_tag"]
    assert reasons[2923300] == ["dating_sim_tag"]
    assert reasons[1619750] == ["adult_content"]
    assert reasons[431960] == ["software_tag", "dating_sim_tag"]
    assert reasons[1] == ["store_data_unavailable"]
    assert reasons[2] == ["no_tags"]
    assert reasons[3] == ["app_type"]  # app_type short-circuits: its Dating Sim tag is not evaluated
    assert reasons[4] == ["adult_content"]
    assert 698670 not in reasons  # Sexual Content / Nudity never exclude
    rows = {(r["appid"], r["reason"]): r for r in result.rows("reports/exclusions.csv")}
    assert rows[(431960, "dating_sim_tag")]["primary_reason"] == "software_tag"
    assert rows[(3, "app_type")]["detail"] == "dlc"
    assert rows[(1619750, "adult_content")]["detail"] == (
        "signals: adult_only_notice; content_descriptor_3; tag Hentai (9130)")
    assert rows[(413150, "dating_sim_tag")]["detail"] == "Dating Sim (9551) at position 17"
    assert "no_store_page" in rows[(1, "store_data_unavailable")]["detail"]
    assert [r["appid"] for r in result.rows("datasets/top100_overall.csv")] == [698670]


def test_would_be_ranks(tmp_path, config_dir):
    rows = {(r["appid"], r["reason"]): r for r in _build(tmp_path, _config(config_dir)).rows("reports/exclusions.csv")}
    stardew = rows[(413150, "dating_sim_tag")]
    # Stardew (~48k players) would rank above Scorn, the only eligible game.
    assert stardew["would_be_rank_overall"] == 1 and stardew["would_be_rank_rpg"] == 1
    assert stardew["would_be_rank_puzzle"] is None  # Stardew has no Puzzle tag
    assert rows[(1, "store_data_unavailable")]["would_be_rank_rpg"] is None  # tags unknown
    assert rows[(1, "store_data_unavailable")]["would_be_rank_overall"] is not None


def test_override_keeps_stardew_and_is_recorded(tmp_path, config_dir):
    override = {"appid": 413150, "name": "Stardew Valley", "rule": "dating_sim_tag", "reason": "farming sim",
                "evidence": EVIDENCE, "added": "2026-10-05"}
    result = _build(tmp_path, _config(config_dir, exclusion_overrides={"override": [override]}))
    assert 413150 not in _reasons(result)
    assert result.rows("datasets/top100_overall.csv")[0]["appid"] == 413150
    assert result.build_json["exclusion_overrides_applied"] == [
        {"appid": 413150, "rule": "dating_sim_tag", "reason": "farming sim"}]


def test_manual_exclusion(tmp_path, config_dir):
    entry = {"appid": 2923300, "name": "Banana", "reason": "clicker with joke tags", "evidence": EVIDENCE,
             "added": "2026-10-05"}
    reasons = _reasons(_build(tmp_path, _config(config_dir, manual_exclusions={"exclusion": [entry]})))
    assert reasons[2923300] == ["dating_sim_tag", "manual"]


@pytest.mark.parametrize("missing", ["reason", "evidence", "added"])
def test_manual_exclusion_entries_need_every_field(tmp_path, config_dir, missing):
    entry = {"appid": 2923300, "name": "Banana", "reason": "r", "evidence": EVIDENCE, "added": "2026-10-05"}
    del entry[missing]
    with pytest.raises(BuildFailed, match=missing):
        _build(tmp_path, _config(config_dir, manual_exclusions={"exclusion": [entry]}))


def test_per_tag_rank_limit_and_near_misses(tmp_path, config_dir):
    cfg = _config(config_dir, exclusions={"per_tag_rank_limit": {"9551": 10}})
    result = _build(tmp_path, cfg)
    reasons = _reasons(result)
    assert 413150 not in reasons and 2923300 not in reasons  # Dating Sim at 17 and 18 is beyond 10
    near = {(r["appid"], r["tag"]): r for r in result.rows("reports/impact_near_misses.csv")}
    assert near[(413150, "Dating Sim")]["position"] == 17 and near[(413150, "Dating Sim")]["rank_limit"] == 10
    assert near[(413150, "Dating Sim")]["excluded"] is False
    assert near[(431960, "Dating Sim")]["excluded"] is True  # excluded anyway, by software_tag
    # "Has tag" is unaffected: Stardew still carries Dating Sim in its dataset row.
    stardew = next(r for r in result.rows("datasets/top100_overall.csv") if r["appid"] == 413150)
    assert 9551 in stardew["tag_ids"]


def test_content_flags_never_filter(tmp_path, config_dir):
    override = {"appid": 3419430, "name": "Bongo Cat", "rule": "software_tag", "reason": "a desktop pet game",
                "evidence": EVIDENCE, "added": "2026-10-05"}
    result = _build(tmp_path, _config(config_dir, exclusion_overrides={"override": [override]}))
    rows = {r["appid"]: r for r in result.rows("datasets/top100_overall.csv")}
    assert rows[3419430]["content_flags"] == ["desktop_companion"]
    assert rows[698670]["content_flags"] == ["sexual_content_tag"]
    unexcluded = {(r["appid"], r["signal"]) for r in result.rows("reports/impact_unexcluded.csv")}
    assert (3419430, "content_flag:desktop_companion") in unexcluded
    assert (698670, "content_descriptor_1") in unexcluded


def test_impact_removals_and_adult_signals(tmp_path, config_dir):
    result = _build(tmp_path, _config(config_dir))
    removals = {(r["rule"], r["signal"], r["appid"]) for r in result.rows("reports/impact_removals.csv")}
    assert ("adult_content", "Hentai", 1619750) in removals
    assert ("software_tag", "Utilities", 431960) in removals
    assert ("dating_sim_tag", "Dating Sim", 413150) in removals
    adult = {r["appid"]: r for r in result.rows("reports/impact_adult_signals.csv")}
    assert 1619750 not in adult  # notice and descriptor 3 agree
    assert adult[4]["adult_only_notice"] is False and adult[4]["content_descriptor_3"] is True


def test_exclusion_counts_in_completeness(tmp_path, config_dir):
    rows = _build(tmp_path, _config(config_dir)).rows("reports/completeness.csv")
    overlapping = {r["item"]: r["value"] for r in rows if r["section"] == "exclusions_overlapping"}
    primary = {r["item"]: r["value"] for r in rows if r["section"] == "exclusions_primary"}
    assert overlapping["dating_sim_tag"] == 3 and primary["dating_sim_tag"] == 2
    assert primary["excluded_games"] == 9
    assert next(r for r in rows if r["item"] == "scored_game_apps")["value"] == 8
    depth = {r["item"]: r["value"] for r in rows if r["section"] == "depth_check" and r["dataset"] == "overall"}
    assert depth["members"] == 1 and depth["deepest_top_listing_rank"] == 6


def test_missing_configured_tag_id_warns(tmp_path, config_dir):
    cfg = _config(config_dir, exclusions={"dating_sim_tag": {"tags": [{"id": 424242, "name": "Not A Tag"}]}})
    result = _build(tmp_path, cfg)
    assert any("424242" in w for w in result.warnings)


# ----------------------------------------------------------------------------- Manual Metadata Entries


def _field(value):
    return {"value": value, "source_url": "https://web.archive.org/web/2024/store.steampowered.com/app/1/",
            "retrieved": "2026-10-05"}


FULL = {
    "appid": 1, "kind": "full", "name": _field("Delisted"),
    "tags": _field([{"id": 19, "name": "Action"}, {"id": 122, "name": "RPG"}]),
    "app_type": _field("game"), "genres": _field([{"id": 1, "name": "Action"}]), "is_free": _field(True),
    "release_date": _field("28 May, 2024"), "adult_only": _field(False),
}


def test_full_entry_adds_a_game_back(tmp_path, config_dir):
    result = _build(tmp_path, _config(config_dir, manual_metadata={"entry": [FULL]}))
    assert 1 not in _reasons(result)
    rpg = {r["appid"]: r for r in result.rows("datasets/top100_rpg.csv")}
    assert rpg[1]["metadata_source"] == "manual" and rpg[1]["tags"] == ["Action", "RPG"] and rpg[1]["is_free"] is True
    citations = result.rows("reports/manual_metadata.csv")
    assert {c["field"] for c in citations if c["appid"] == 1} == {
        "name", "tags", "app_type", "genres", "is_free", "release_date", "adult_only"}
    assert result.build_json["manual_metadata_entries"] == [{"appid": 1, "kind": "full"}]


def test_tags_only_entry_for_a_no_tags_game(tmp_path, config_dir):
    entry = {"appid": 2, "kind": "tags_only", "tags": _field([{"id": 1664, "name": "Puzzle"}])}
    result = _build(tmp_path, _config(config_dir, manual_metadata={"entry": [entry]}))
    puzzle = {r["appid"]: r for r in result.rows("datasets/top100_puzzle.csv")}
    assert puzzle[2]["metadata_source"] == "manual_tags" and puzzle[2]["genres"] == ["Action"]


def test_unsourced_field_is_rejected(tmp_path, config_dir):
    entry = dict(FULL, app_type={"value": "game", "source_url": "", "retrieved": "2026-10-05"})
    with pytest.raises(BuildFailed, match="app_type has no source_url"):
        _build(tmp_path, _config(config_dir, manual_metadata={"entry": [entry]}))


def test_entry_for_a_store_provided_app_fails(tmp_path, config_dir):
    entry = dict(FULL, appid=413150)
    with pytest.raises(BuildFailed, match="provides this app"):
        _build(tmp_path, _config(config_dir, manual_metadata={"entry": [entry]}))


def test_tags_only_entry_for_a_tagged_game_fails(tmp_path, config_dir):
    entry = {"appid": 413150, "kind": "tags_only", "tags": _field([{"id": 19, "name": "Action"}])}
    with pytest.raises(BuildFailed, match="shows no tags"):
        _build(tmp_path, _config(config_dir, manual_metadata={"entry": [entry]}))
