"""Seam 2/3: the Build's network tables, Removal Sensitivity, Resolution Sweep and analysis.json."""

from __future__ import annotations

import json
import random

import pytest

from helpers import World
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.export.writer import read_csv
from steamstudy.snapshot import Snapshot

GROUPS = [[5000 + g * 10 + i for i in range(6)] for g in range(4)]


def tagged_world(n: int = 120, seed: int = 4) -> World:
    """Games with tags from one of four groups plus two random ones; every 3rd game also has Puzzle (1664)."""
    rng = random.Random(seed)
    world = World()
    for i in range(n):
        group = GROUPS[i % 4]
        tags = rng.sample(group, 5) + rng.sample([t for g in GROUPS for t in g if t not in group], 2)
        if i % 3 == 0:
            tags.append(1664)
        world.add(10_000 + i, avg=10_000.0 - i * 7, months=12 + i % 30, tags=[(t, f"tag {t}") for t in tags])
    return world


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    config = load_config(__import__("conftest").CONFIG_DIR)
    root = tmp_path_factory.mktemp("b")
    path = tagged_world().snapshot(root / "snap")
    result = build(Snapshot(path), config, "20261005T000000Z-abcdef12")
    return result, write_build(result, root), path, config


def test_network_tables_are_stacked_with_dataset_and_state_id(built):
    result, folder, _, _ = built
    nodes = read_csv(folder / "analysis" / "network_nodes.csv")
    assert list(nodes[0].keys())[:3] == ["dataset", "state_id", "tag_id"]
    analysis = json.loads((folder / "analysis" / "analysis.json").read_text(encoding="utf-8"))
    ids = {key: info["state_id"] for key, info in analysis["datasets"].items()}
    assert {"overall", "puzzle"} <= {r["dataset"] for r in nodes}  # the other datasets have no games here
    assert all(r["state_id"] == ids[r["dataset"]] for r in nodes)
    quality = read_csv(folder / "analysis" / "network_cluster_quality.csv")
    assert [r["dataset"] for r in quality] == ["overall", "puzzle", "rpg", "strategy", "simulation"]
    for name in ("network_edges.csv", "network_clusters.csv", "network_not_in_network.csv",
                 "network_cluster_connections.csv", "network_null_model.csv", "network_seed_noise.csv",
                 "removal_sensitivity.csv", "resolution_sweep.csv"):
        assert (folder / "analysis" / name).is_file(), name


def test_report_settings_hide_genre_tags_and_the_defining_tag(built):
    result, *_ = built
    key = result.analysis_json["datasets"]["puzzle"]["state_key"]
    assert 1664 in key["hidden_tag_ids"] and 19 in key["hidden_tag_ids"]
    assert (key["min_games_per_tag"], key["min_shared_games"], key["min_months"]) == (8, 8, 0)
    assert (key["algorithm"], key["clustering_weight"], key["resolution"]) == ("louvain", "shared_games", "1.00")
    reasons = {r["tag_id"]: r["reasons"] for r in result.rows("analysis/network_not_in_network.csv")
               if r["dataset"] == "puzzle"}
    assert reasons[1664] == ["defining_tag_hidden", "genre_tag_hidden"]


def test_removal_sensitivity_is_complete_and_the_sweep_includes_the_config_gamma(built):
    result, *_ = built
    nodes = [r for r in result.rows("analysis/network_nodes.csv") if r["dataset"] == "overall"]
    rs = [r for r in result.rows("analysis/removal_sensitivity.csv") if r["dataset"] == "overall"]
    assert len(rs) == len(nodes) > 10 and [r["run_order"] for r in rs] == list(range(1, len(rs) + 1))
    sweep = [r for r in result.rows("analysis/resolution_sweep.csv") if r["dataset"] == "overall"]
    assert [r["resolution"] for r in sweep] == [0.5, 0.75, 1.0, 1.25, 1.5]
    assert next(r for r in sweep if r["resolution"] == 1.0)["ari_vs_report"] == 1.0


def test_analysis_json(built):
    result, *_ = built
    a = result.analysis_json
    assert a["schema_version"] >= 1 and a["build_id"] == "20261005T000000Z-abcdef12"
    overall = a["datasets"]["overall"]
    assert overall["n_games"] == 100 and overall["eligible_pool"] == 120
    assert set(overall["seed_noise_floor"]) >= {"seed_ari_min", "seed_ari_mean", "seed_k_min", "seed_k_max"}
    assert "network_nodes.csv" in a["columns"]


def test_build_json_records_clustering_library_versions(built):
    result, *_ = built
    versions = result.build_json["software_versions"]
    assert versions["networkx"] == "3.7" and versions["leidenalg"] == "0.12.0"
    assert result.build_json["network_defaults"]["seed"] == 20261003


def test_network_tables_are_byte_identical_across_builds(built, tmp_path):
    _, folder, path, config = built
    again = write_build(build(Snapshot(path), config, "20261005T000000Z-abcdef12"), tmp_path)
    for f in sorted((folder / "analysis").glob("*.csv")):
        assert f.read_bytes() == (again / "analysis" / f.name).read_bytes(), f.name
