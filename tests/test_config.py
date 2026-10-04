from __future__ import annotations

import copy
import shutil
import tomllib

import pytest

from steamstudy.config import ALL_FILES, ConfigError, config_from_data, load_config


def _files(config_dir):
    return {n: tomllib.loads((config_dir / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}


def test_shipped_config_loads_with_spec_defaults(config_dir):
    cfg = load_config(config_dir)
    n = cfg.network
    assert (n.min_games_per_tag, n.min_shared_games, n.min_months) == (8, 8, 0)
    assert (n.clustering_weight, n.algorithm, n.resolution) == ("shared_games", "louvain", 1.0)
    assert (n.null_replicates, n.noise_seeds) == (20, 10)
    assert n.resolution_sweep == (0.5, 0.75, 1.0, 1.25, 1.5)
    assert [d.key for d in cfg.datasets] == ["overall", "puzzle", "rpg", "strategy", "simulation"]
    assert cfg.dataset("overall").defining_tag is None
    assert cfg.dataset("puzzle").defining_tag.id == 1664
    assert cfg.analysis.max_itemset_size == 3 and cfg.analysis.min_support == 10
    assert cfg.analysis.release_month_check == 3
    assert cfg.exclusions.allowed_app_types == ("game",)
    assert cfg.exclusions.global_rank_limit == 20
    assert [t.id for t in cfg.exclusions.dating_sim_tags.tags] == [9551]
    assert len(cfg.genre_tags) == 11
    c = cfg.collection
    assert c.listing_passes == 2 and c.steamcharts_per_second == 3.0 and c.store_seconds_per_request == 2.0
    assert c.retry_schedule == (10.0, 30.0, 90.0)
    assert cfg.manual_metadata == () and cfg.manual_exclusions == () and cfg.exclusion_overrides == ()


@pytest.mark.parametrize("key", ["noise_seeds", "null_replicates"])
def test_validation_rejects_fewer_than_two_seeds_or_replicates(config_dir, key):
    files = _files(config_dir)
    files["network"][key] = 1
    with pytest.raises(ConfigError, match=key):
        config_from_data(files)


def test_validation_rejects_unknown_algorithm(config_dir):
    files = _files(config_dir)
    files["network"]["algorithm"] = "cpm"
    with pytest.raises(ConfigError, match="algorithm"):
        config_from_data(files)


def test_missing_file_is_an_error(tmp_path, config_dir):
    shutil.copytree(config_dir, tmp_path / "c")
    (tmp_path / "c" / "network.toml").unlink()
    with pytest.raises(ConfigError, match="network"):
        load_config(tmp_path / "c")


def test_hashes_ignore_whitespace_comments_and_key_order(tmp_path, config_dir):
    base = load_config(config_dir)
    shutil.copytree(config_dir, tmp_path / "c")
    path = tmp_path / "c" / "network.toml"
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    path.write_text("# reordered\n\n" + "\n\n".join(reversed(lines)) + "\n", encoding="utf-8")
    again = load_config(tmp_path / "c")
    assert again.build_config_hash == base.build_config_hash
    assert again.collection_config_hash == base.collection_config_hash


def test_build_hash_changes_with_build_config_but_not_collection_config(config_dir):
    files = _files(config_dir)
    base = config_from_data(files)
    changed = copy.deepcopy(files)
    changed["network"]["seed"] += 1
    assert config_from_data(changed).build_config_hash != base.build_config_hash
    assert config_from_data(changed).collection_config_hash == base.collection_config_hash
    rate = copy.deepcopy(files)
    rate["collection"]["rates"]["steamcharts_per_second"] = 1.0
    assert config_from_data(rate).build_config_hash == base.build_config_hash
    assert config_from_data(rate).collection_config_hash != base.collection_config_hash


def test_changelog_entries(config_dir):
    entries = load_config(config_dir).changelog_entries()
    assert entries and entries[0]["date"] == "2026-10-04"
