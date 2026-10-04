"""Seam 4: the app through its export zip (equality with the Build, zip contents, Open Network State)."""

from __future__ import annotations

import csv
import re
import hashlib
import io
import json
import shutil
import zipfile

import pytest

from steamstudy.app import rs_cache
from steamstudy.app.export import BuildNotFound, OpenRefused, export_zip, open_export, read_export
from steamstudy.app.loader import load_build
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.export.writer import read_csv
from steamstudy.network.layout import relayout
from steamstudy.network.sensitivity import removal_sensitivity
from steamstudy.network.state import compute_state
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world


@pytest.fixture(scope="module")
def build_folder(tmp_path_factory):
    config = load_config(__import__("conftest").CONFIG_DIR)
    root = tmp_path_factory.mktemp("app")
    result = build(Snapshot(tagged_world().snapshot(root / "snap")), config, "20261005T120000Z-abcdef12")
    return write_build(result, root)


def _zip_rows(data: bytes, name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return list(csv.DictReader(io.StringIO(zf.read(name).decode("utf-8-sig"))))


@pytest.mark.parametrize("dataset", ["overall", "puzzle"])
def test_app_at_the_report_settings_equals_the_build(build_folder, dataset):
    ctx = load_build(build_folder)
    _, data = export_zip(ctx, ctx.default_settings(dataset))
    for app_name, build_name in (("nodes.csv", "network_nodes.csv"), ("edges.csv", "network_edges.csv"),
                                 ("clusters.csv", "network_clusters.csv"),
                                 ("cluster_quality.csv", "network_cluster_quality.csv"),
                                 ("cluster_connections.csv", "network_cluster_connections.csv"),
                                 ("null_model.csv", "network_null_model.csv"),
                                 ("seed_noise.csv", "network_seed_noise.csv"),
                                 ("not_in_network.csv", "network_not_in_network.csv")):
        build_rows = [{k: v for k, v in r.items() if k not in ("dataset", "state_id")}
                      for r in read_csv(build_folder / "analysis" / build_name) if r["dataset"] == dataset]
        assert _zip_rows(data, app_name) == build_rows, app_name


def test_zip_contents_hashes_and_row_counts(build_folder):
    ctx = load_build(build_folder)
    before = sorted(p.relative_to(build_folder) for p in build_folder.rglob("*"))
    filename, data = export_zip(ctx, ctx.default_settings("overall"))
    assert re.fullmatch(r"steamstudy_overall_[0-9a-f]{12}_\d{8}T\d{6}Z\.zip", filename)
    export, files = read_export(data)
    assert "removal_sensitivity.csv" not in files and export["removal_sensitivity"] == "not_run"
    assert "seed_noise.csv" in files
    for name, info in export["files"].items():
        assert hashlib.sha256(files[name]).hexdigest() == info["sha256"]
        assert len(list(csv.DictReader(io.StringIO(files[name].decode("utf-8-sig"))))) == info["rows"]
    assert export["state_id"] in filename and export["build_json"]["build_id"] == ctx.build_id
    constants = export["method_constants"]
    assert constants["silhouette"] == "jaccard_game_set" and len(constants["replicate_seeds"]) == 20
    assert len(constants["noise_seeds"]) == 10 and "removal_sensitivity_method_version" in constants
    assert "nodes.csv" in export["columns"] and export["layout_source"] == "default"
    assert sorted(p.relative_to(build_folder) for p in build_folder.rglob("*")) == before  # nothing written


def test_removal_sensitivity_only_for_the_exact_key(build_folder, tmp_path):
    ctx = load_build(build_folder)
    settings = ctx.default_settings("overall")
    state = compute_state(ctx.games("overall"), settings, ctx.context("overall"))
    rows = removal_sensitivity(state, should_stop=lambda: False)[:3]
    _, data = export_zip(ctx, settings, removal_rows=rows, state=state)
    export, files = read_export(data)
    assert export["removal_sensitivity"] == {"status": "partial", "done": 3, "total": len(state.nodes)}
    assert len(_zip_rows(data, "removal_sensitivity.csv")) == 3
    # The cache is keyed by the state key: another key finds nothing, so stale rows are never exported.
    cache = tmp_path / "app_cache"
    for row in rows:
        rs_cache.add_row(cache, settings.key(), len(state.nodes), row)
    assert rs_cache.load(cache, settings.key()).done == 3
    assert rs_cache.load(cache, settings.with_(seed=settings.seed + 1).key()) is None
    assert rs_cache.clear(cache) == 1 and rs_cache.load(cache, settings.key()) is None


def test_open_network_state_round_trip(build_folder):
    ctx = load_build(build_folder)
    settings = ctx.default_settings("overall").with_(min_games_per_tag=10, removed_tag_ids=(5000,), resolution=1.2)
    state = compute_state(ctx.games("overall"), settings, ctx.context("overall"))
    moved = relayout(state.graph, state.positions, settings.seed, iterations=5)
    rows = removal_sensitivity(state)[:2]
    _, data = export_zip(ctx, settings, relayout_positions=moved, removal_rows=rows, state=state)
    for payload in (data, json.dumps(read_export(data)[0]).encode("utf-8")):
        opened = open_export(payload)
        assert opened.settings == settings and opened.state_id_matches
    opened = open_export(data)
    assert opened.layout_source == "relayout"
    assert opened.relayout_positions == pytest.approx({t: moved[t] for t in state.nodes})
    assert [r["tag_id"] for r in opened.removal_rows] == [r["tag_id"] for r in rows]
    _, again = export_zip(ctx, opened.settings, relayout_positions=opened.relayout_positions,
                          removal_rows=opened.removal_rows)
    assert read_export(again)[1] == read_export(data)[1]  # identical tables


def test_open_refuses_a_changed_build_or_key_version(build_folder, tmp_path):
    ctx = load_build(build_folder)
    _, data = export_zip(ctx, ctx.default_settings("overall"))
    export, files = read_export(data)
    bad_key = dict(export, state_key={**export["state_key"], "key_version": 999})
    with pytest.raises(OpenRefused, match="key_version"):
        open_export(json.dumps(bad_key).encode("utf-8"))
    moved = tmp_path / "moved"
    shutil.copytree(build_folder, moved)
    bj = json.loads((moved / "datasets" / "build.json").read_text(encoding="utf-8"))
    bj["build_config_hash"] = "0" * 64
    (moved / "datasets" / "build.json").write_text(json.dumps(bj), encoding="utf-8")
    with pytest.raises(OpenRefused, match="differs"):
        open_export(data, build_path=moved)
    gone = dict(export, build_path=str(tmp_path / "nowhere"))
    with pytest.raises(BuildNotFound):
        open_export(json.dumps(gone).encode("utf-8"))
    assert open_export(json.dumps(gone).encode("utf-8"), build_path=build_folder).state_id_matches


def test_open_accepts_an_older_schema_version(build_folder):
    ctx = load_build(build_folder)
    _, data = export_zip(ctx, ctx.default_settings("overall"))
    export = read_export(data)[0]
    export["schema_version"] = 0
    export.pop("columns")
    opened = open_export(json.dumps(export).encode("utf-8"))
    assert opened.schema_version == 0 and opened.state_id_matches


