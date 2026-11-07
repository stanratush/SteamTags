"""Named Exclusion Rules: the config shapes, validation, evaluation order and byte-identical output."""

from __future__ import annotations

import copy
import json
import tomllib
from pathlib import Path

import pytest

from golden_builds import all_worlds
from steamstudy.build.core import BuildFailed, build
from steamstudy.config import ALL_FILES, ConfigError, config_from_data, load_config
from steamstudy.snapshot import Snapshot
from test_build_exclusions import EVIDENCE, _build, _reasons, _world

FIXTURES = Path(__file__).parent / "fixtures"


def _files(config_dir):
    return {n: tomllib.loads((config_dir / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}


def _cfg(config_dir, *, rules=None, flags=None, **extra):
    files = _files(config_dir)
    if rules is not None:
        files["exclusions"]["rule"] = rules
    if flags is not None:
        files["exclusions"]["content_flag"] = flags
    for name, value in extra.items():
        files[name] = {**files[name], **value}
    return config_from_data(files, directory=config_dir)


def _rules(config_dir):
    return copy.deepcopy(_files(config_dir)["exclusions"]["rule"])


def _old_shape_config(config_dir):
    files = _files(config_dir)
    files["exclusions"] = tomllib.loads((FIXTURES / "exclusions_old_shape.toml").read_text(encoding="utf-8"))
    return config_from_data(files, directory=config_dir)


# ----------------------------------------------------------------------------- byte identity


def test_old_shape_gives_the_bytes_of_a_build_made_before_this_change(config_dir):
    golden = json.loads((FIXTURES / "golden_build_hashes.json").read_text(encoding="utf-8"))
    assert all_worlds(_old_shape_config(config_dir)) == golden


def test_new_shape_differs_only_in_the_config_hash_the_report_prints(config_dir):
    golden = json.loads((FIXTURES / "golden_build_hashes.json").read_text(encoding="utf-8"))
    got = all_worlds(load_config(config_dir))
    for world, files in got.items():
        assert {f for f in files if files[f] != golden[world][f]} == {"reports/reports.html"}


def test_old_and_new_shape_read_to_the_same_rules(config_dir):
    old, new = _old_shape_config(config_dir).exclusions, load_config(config_dir).exclusions
    assert [r.name for r in old.rules] == [r.name for r in new.rules] == ["adult_content", "software_tag", "dating_sim_tag"]
    assert (old.rules[0].content_descriptor_ids, old.rules[0].adult_only_notice) == ((3,), True)
    assert [(r.tags, r.name_only) for r in old.rules] == [(r.tags, r.name_only) for r in new.rules]
    assert [f.name for f in old.content_flags] == [f.name for f in new.content_flags]
    assert [f.tags for f in old.content_flags] == [f.tags for f in new.content_flags]


def test_old_per_tag_rank_limit_moves_onto_the_tag_entry(config_dir):
    files = _files(config_dir)
    files["exclusions"] = {**tomllib.loads((FIXTURES / "exclusions_old_shape.toml").read_text(encoding="utf-8")),
                           "per_tag_rank_limit": {"9551": 10}}
    cfg = config_from_data(files, directory=config_dir)
    dating = next(r for r in cfg.exclusions.rules if r.name == "dating_sim_tag")
    assert [(t.id, t.rank_limit) for t in dating.tags] == [(9551, 10)]


def test_mixing_the_old_and_new_shape_is_refused(config_dir):
    files = _files(config_dir)
    files["exclusions"]["dating_sim_tag"] = {"tags": [{"id": 9551, "name": "Dating Sim"}]}
    with pytest.raises(ConfigError, match="mixes the old shape"):
        config_from_data(files, directory=config_dir)


# ----------------------------------------------------------------------------- validation


def test_duplicate_rule_names_fail(config_dir):
    rules = _rules(config_dir)
    rules.append(copy.deepcopy(rules[2]))
    with pytest.raises(ConfigError, match="duplicate rule name 'dating_sim_tag'"):
        _cfg(config_dir, rules=rules)


@pytest.mark.parametrize("name", ["store_data_unavailable", "app_type", "no_tags", "manual"])
def test_a_name_equal_to_a_fixed_rule_fails(config_dir, name):
    rules = _rules(config_dir)
    rules[2]["name"] = name
    with pytest.raises(ConfigError, match="fixed rule"):
        _cfg(config_dir, rules=rules)


@pytest.mark.parametrize("name", ["Dating-Sim", "dating sim", "", "Æ"])
def test_a_name_outside_the_code_alphabet_fails(config_dir, name):
    rules = _rules(config_dir)
    rules[2]["name"] = name
    with pytest.raises(ConfigError, match="a-z, 0-9 and _"):
        _cfg(config_dir, rules=rules)


def test_a_rule_with_no_signal_fails(config_dir):
    rules = _rules(config_dir)
    rules.append({"name": "empty", "label": "Empty"})
    with pytest.raises(ConfigError, match="at least one signal"):
        _cfg(config_dir, rules=rules)


@pytest.mark.parametrize("limit", [0, 21, -3, "5", True])
def test_a_rank_limit_outside_1_to_20_fails(config_dir, limit):
    rules = _rules(config_dir)
    rules[2]["tags"][0]["rank_limit"] = limit
    with pytest.raises(ConfigError, match="between 1 and 20"):
        _cfg(config_dir, rules=rules)


def test_zero_rules_is_a_valid_build(tmp_path, config_dir):
    result = _build(tmp_path, _cfg(config_dir, rules=[]))
    reasons = _reasons(result)
    assert reasons[1] == ["store_data_unavailable"] and reasons[2] == ["no_tags"] and reasons[3] == ["app_type"]
    assert 413150 not in reasons and 1619750 not in reasons  # nothing named excludes them
    assert result.rows("reports/impact_adult_signals.csv") == []
    items = [r["item"] for r in result.rows("reports/completeness.csv") if r["section"] == "exclusions_primary"]
    assert items == ["store_data_unavailable", "app_type", "no_tags", "manual", "excluded_games"]


def _override(rule, appid=413150):
    return {"appid": appid, "name": "Stardew Valley", "rule": rule, "reason": "r", "evidence": EVIDENCE,
            "added": "2026-10-05"}


@pytest.mark.parametrize("rule, fragment", [
    ("no_such_rule", "is not a rule of exclusions.toml"),
    ("store_data_unavailable", "Manual Metadata Entry"),
    ("manual", "remove the manual exclusion"),
])
def test_an_override_naming_an_unavailable_rule_fails_the_build(tmp_path, config_dir, rule, fragment):
    cfg = _cfg(config_dir, exclusion_overrides={"override": [_override(rule)]})
    with pytest.raises(BuildFailed, match=fragment) as err:
        _build(tmp_path, cfg)
    assert repr(rule) in str(err.value)


def test_an_override_may_name_a_renamed_rule(tmp_path, config_dir):
    rules = _rules(config_dir)
    rules[2]["name"] = "romance_sim"
    cfg = _cfg(config_dir, rules=rules, exclusion_overrides={"override": [_override("romance_sim")]})
    result = _build(tmp_path, cfg)
    assert 413150 not in _reasons(result)
    assert result.build_json["exclusion_overrides_applied"][0]["rule"] == "romance_sim"
    with pytest.raises(BuildFailed, match="dating_sim_tag"):
        _build(tmp_path / "b", _cfg(config_dir, rules=rules, exclusion_overrides={"override": [_override("dating_sim_tag")]}))


def test_an_unknown_tag_id_stays_a_warning(tmp_path, config_dir):
    rules = _rules(config_dir)
    rules.append({"name": "ghost", "label": "Ghost", "tags": [{"id": 999999991, "name": "Ghost"}]})
    result = _build(tmp_path, _cfg(config_dir, rules=rules))
    assert any("ghost: tag id 999999991 (Ghost)" in w for w in result.warnings)


# ----------------------------------------------------------------------------- evaluation


def test_rule_order_decides_the_primary_reason(tmp_path, config_dir):
    default = {(r["appid"], r["reason"]): r for r in _build(tmp_path / "a", load_config(config_dir)).rows("reports/exclusions.csv")}
    assert default[(431960, "software_tag")]["primary_reason"] == "software_tag"
    rules = _rules(config_dir)
    rules[1], rules[2] = rules[2], rules[1]
    swapped = _build(tmp_path / "b", _cfg(config_dir, rules=rules))
    rows = {(r["appid"], r["reason"]): r for r in swapped.rows("reports/exclusions.csv")}
    assert rows[(431960, "software_tag")]["primary_reason"] == "dating_sim_tag"
    primary = {r["item"]: r["value"] for r in swapped.rows("reports/completeness.csv") if r["section"] == "exclusions_primary"}
    assert list(primary)[:6] == ["store_data_unavailable", "app_type", "no_tags", "adult_content", "dating_sim_tag", "software_tag"]


def test_a_tag_in_two_rules_matches_both(tmp_path, config_dir):
    rules = _rules(config_dir)
    rules.append({"name": "also_dating", "label": "Also", "tags": [{"id": 9551, "name": "Dating Sim"}]})
    reasons = _reasons(_build(tmp_path, _cfg(config_dir, rules=rules)))
    assert reasons[413150] == ["dating_sim_tag", "also_dating"]


def test_per_tag_limits_differ_per_rule(tmp_path, config_dir):
    rules = _rules(config_dir)
    rules[2]["tags"][0]["rank_limit"] = 10  # Stardew has Dating Sim at 17
    rules.append({"name": "wide", "label": "Wide", "tags": [{"id": 9551, "name": "Dating Sim", "rank_limit": 18}]})
    result = _build(tmp_path, _cfg(config_dir, rules=rules))
    reasons = _reasons(result)
    assert reasons[413150] == ["wide"]  # tight in dating_sim_tag, wide enough in the second rule
    near = {(r["appid"], r["rule"]): r for r in result.rows("reports/impact_near_misses.csv")}
    assert near[(413150, "dating_sim_tag")]["rank_limit"] == 10
    assert (413150, "wide") not in near
    assert (2923300, "wide") not in near and 2923300 in reasons  # position 18 is within 18


def test_adult_only_notice_fires_only_where_the_rule_says_so(tmp_path, config_dir):
    rules = _rules(config_dir)
    rules[0]["adult_only_notice"] = False
    result = _build(tmp_path, _cfg(config_dir, rules=rules))
    rows = {(r["appid"], r["reason"]): r for r in result.rows("reports/exclusions.csv")}
    assert rows[(1619750, "adult_content")]["detail"] == "signals: content_descriptor_3; tag Hentai (9130)"


def test_a_descriptor_rule_under_another_name_has_no_adult_signal_report(tmp_path, config_dir):
    rules = _rules(config_dir)
    rules[0]["name"] = "mature"
    result = _build(tmp_path, _cfg(config_dir, rules=rules))
    assert _reasons(result)[4] == ["mature"]
    assert result.rows("reports/impact_adult_signals.csv") == []


def test_rules_and_flags_read_the_full_displayed_list(tmp_path, config_dir):
    # Dating Sim at position 17 is matched by position, whatever Tag Depth later cuts for "has".
    reasons = _reasons(_build(tmp_path, load_config(config_dir)))
    assert reasons[413150] == ["dating_sim_tag"]


def test_content_flags_feed_the_unexcluded_report_by_code(tmp_path, config_dir):
    flags = [{"name": "cosy", "label": "Cosy", "tags": [{"id": 1320952, "name": "Desktop Companion"}]}]
    bongo = {**_override("software_tag", 3419430), "name": "Bongo Cat"}
    result = _build(tmp_path, _cfg(config_dir, flags=flags, exclusion_overrides={"override": [bongo]}))
    assert {r["flag"] for r in result.rows("analysis/content_flags.csv")} == {"cosy"}
    unexcluded = {(r["appid"], r["signal"]) for r in result.rows("reports/impact_unexcluded.csv")}
    assert (3419430, "content_flag:cosy") in unexcluded


def test_an_old_build_json_still_loads_in_the_app(tmp_path, config_dir):
    from steamstudy.app.loader import load_build

    from steamstudy.build.writer import write_build

    old_cfg = _old_shape_config(config_dir)

    folder = write_build(build(Snapshot(_world().snapshot(tmp_path / "snap")), old_cfg, "20261005T140000Z-abcdef12"), tmp_path)
    loaded = load_build(folder)
    assert [d.key for d in loaded.datasets] == ["overall", "puzzle", "rpg", "strategy", "simulation"]
    assert [r["appid"] for r in loaded.rows("overall")] == [698670]
    assert "dating_sim_tag" not in json.dumps(loaded.build_json["config"]["exclusions"]["content_flags"])
