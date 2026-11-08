"""Issue 24: Build identity, drafts and lifecycle, through `steamstudy.build_admin` (Dash-free)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from conftest import CONFIG_DIR
from steamstudy import build_admin as BA
from steamstudy.builds import list_builds
from steamstudy.config import exclusions_new_shape

T1 = dt.datetime(2026, 11, 8, 10, 0, 0, tzinfo=dt.UTC)
T2 = dt.datetime(2026, 11, 8, 11, 0, 0, tzinfo=dt.UTC)
T3 = dt.datetime(2026, 11, 8, 12, 0, 0, tzinfo=dt.UTC)


@pytest.fixture(scope="module")
def world_root(tmp_path_factory) -> Path:
    """A repository root with two closed test Snapshots of the tagged world (S1, S2)."""
    from test_build_network import tagged_world

    root = tmp_path_factory.mktemp("admin")
    for sid in ("S1", "S2"):
        tagged_world().snapshot(root / "snapshots" / sid)
    return root


@pytest.fixture
def root(world_root, tmp_path) -> Path:
    """A fresh copy of the world per test (the Snapshots only; builds/ starts empty)."""
    import shutil

    shutil.copytree(world_root / "snapshots", tmp_path / "snapshots")
    return tmp_path


def _built(root: Path, name: str, *, source: str = "S1", from_build: str | None = None, now=T1) -> str:
    draft = BA.start_draft(root, source, from_build=from_build, config_dir=CONFIG_DIR, name=name)
    draft.description = f"why {name} exists"
    BA.save_draft(root, draft)
    folder = BA.build_draft(root, draft, now=now)
    return f"{folder.parent.name}/{folder.name}"


# ----------------------------------------------------------------------------- names


def test_a_name_clash_with_a_build_or_a_draft_is_refused_ignoring_case(root):
    _built(root, "Baseline")
    with pytest.raises(BA.NameClash):
        BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="BASELINE")
    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Wide pool")
    other = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Other")
    other.name = "wide POOL"
    with pytest.raises(BA.NameClash):
        BA.save_draft(root, other)
    # The same name on another Snapshot is fine.
    assert BA.start_draft(root, "S2", config_dir=CONFIG_DIR, name="Baseline").name == "Baseline"
    assert draft.name == "Wide pool"


def test_a_cli_build_is_named_after_its_build_id_and_name_sets_one(root):
    from steamstudy.cli import main

    assert main(["--config", str(CONFIG_DIR), "--root", str(root), "build", "--snapshot", "S1"]) == 0
    (info,) = list_builds(root)
    assert info.name == info.build_id and info.description is None and info.parent_build_id is None
    assert main(["--config", str(CONFIG_DIR), "--root", str(root), "build", "--snapshot", "S1",
                 "--name", info.build_id.upper()]) == 2  # a clash, ignoring case
    assert main(["--config", str(CONFIG_DIR), "--root", str(root), "build", "--snapshot", "S1",
                 "--name", "Named"]) == 0
    assert sorted(b.name for b in list_builds(root)) == sorted(["Named", info.build_id])


def test_an_old_build_json_reads_with_its_id_as_name(root):
    ref = _built(root, "Fresh")
    path = root / "builds" / ref / "datasets" / "build.json"
    bj = json.loads(path.read_text(encoding="utf-8"))
    for key in ("name", "description", "parent_build_id"):
        del bj[key]
    path.write_text(json.dumps(bj), encoding="utf-8")
    (info,) = list_builds(root)
    assert (info.name, info.description, info.parent_build_id) == (info.build_id, None, None)


# ----------------------------------------------------------------------------- drafts


def test_a_draft_survives_a_restart_and_a_built_one_records_identity_outside_the_hash(root):
    from steamstudy.config import load_config

    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Survivor")
    draft.description = "kept across restarts"
    BA.save_draft(root, draft)
    (again,) = BA.list_drafts(root, "S1")  # read back from disk, as a new process would
    assert (again.name, again.description, again.parent_build_id) == ("Survivor", "kept across restarts", None)
    assert again.config == {k: v for k, v in load_config(CONFIG_DIR).files.items() if k != "collection"}

    folder = BA.build_draft(root, again, now=T1)
    assert BA.list_drafts(root, "S1") == []
    bj = json.loads((folder / "datasets" / "build.json").read_text(encoding="utf-8"))
    assert (bj["name"], bj["description"], bj["parent_build_id"]) == ("Survivor", "kept across restarts", None)
    assert bj["build_config_hash"] == load_config(CONFIG_DIR).build_config_hash  # identity is not in the hash
    assert bj["build_id"].endswith(bj["build_config_hash"][:8])
    inherited = load_config(CONFIG_DIR).changelog_entries()
    assert bj["changelog"][:-1] == inherited
    assert bj["changelog"][-1] == {"date": "2026-11-08", "title": "Survivor", "text": "kept across restarts"}
    assert (root / "builds" / "latest").read_text(encoding="utf-8").strip() == f"S1/{folder.name}"


def test_a_failed_draft_keeps_its_failure_and_a_later_success_removes_draft_and_failed_file(root):
    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Fragile")
    draft.description = "fails first"
    # A parse error: an app's Steam Charts page that does not parse.
    page = root / "snapshots" / "S1" / "raw" / "steamcharts" / "app" / "10000.html.gz"
    original = page.read_bytes()
    import gzip
    page.write_bytes(gzip.compress(b"<html><body>no table</body></html>"))
    BA.save_draft(root, draft)
    with pytest.raises(BA.BuildFailed):
        BA.build_draft(root, draft, now=T1, from_raw=True)
    (kept,) = BA.list_drafts(root, "S1")
    failure = kept.last_failure
    assert failure["kind"] == "parse_errors" and failure["count"] == 1
    failed_csv = root / failure["path"]
    assert failed_csv.is_file()
    assert list_builds(root) == []  # a failed run is not a Build

    page.write_bytes(original)
    BA.build_draft(root, kept, now=T2, from_raw=True)
    assert BA.list_drafts(root, "S1") == [] and not failed_csv.exists()


def test_a_causal_word_failure_is_recorded_as_its_sentence(root):
    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Causal")
    draft.description = "a causal word in the reports"
    draft.config["analysis"]["causal_words"] = ["games"]
    BA.save_draft(root, draft)
    with pytest.raises(BA.BuildFailed):
        BA.build_draft(root, draft, now=T1)
    (kept,) = BA.list_drafts(root, "S1")
    assert kept.last_failure["kind"] == "message" and "games" in kept.last_failure["message"]


def test_discarding_a_draft_removes_it_and_its_failed_file(root):
    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Throwaway")
    draft.config["exclusion_overrides"] = {"override": [{"appid": 10000, "rule": "no_such_rule",
                                                         "reason": "r", "evidence": "e"}]}
    BA.save_draft(root, draft)
    with pytest.raises(BA.BuildFailed):
        BA.build_draft(root, draft, now=T1)
    BA.discard_draft(root, BA.list_drafts(root, "S1")[0])
    assert BA.list_drafts(root, "S1") == []


def test_renaming_a_draft_moves_its_file(root):
    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="First name")
    draft.name = "Second name"
    BA.save_draft(root, draft)
    assert [d.name for d in BA.list_drafts(root, "S1")] == ["Second name"]
    assert sorted(p.name for p in (root / "builds" / "S1" / "drafts").iterdir()) == ["second-name.json"]


def test_config_dir_is_never_written(root, tmp_path_factory):
    import shutil

    config = tmp_path_factory.mktemp("cfg") / "config"
    shutil.copytree(CONFIG_DIR, config)
    before = {p.name: p.read_bytes() for p in config.iterdir()}
    draft = BA.start_draft(root, "S1", config_dir=config, name="Untouched")
    draft.config["datasets"]["tag_depth"] = 10
    BA.save_draft(root, draft)
    BA.discard_draft(root, draft)
    assert {p.name: p.read_bytes() for p in config.iterdir()} == before


# ----------------------------------------------------------------------------- duplicate, identical, delete


def test_duplicate_onto_another_snapshot_records_the_parent_and_a_deleted_parent_shows(root):
    parent = _built(root, "Parent")
    draft = BA.duplicate(root, parent, "S2")
    assert draft.source_id == "S2" and draft.parent_build_id == parent and draft.name == "Parent (copy)"
    draft.description = "the same settings on S2"
    BA.save_draft(root, draft)
    child = BA.build_draft(root, draft, now=T2)
    info = {b.ref: b for b in list_builds(root)}[f"S2/{child.name}"]
    assert info.parent_build_id == parent and BA.parent_name(root, info.parent_build_id) == "Parent"

    plan = BA.delete_build(root, parent, open_build=None)
    assert plan.orphaned_builds == [f"S2/{child.name}"]
    assert BA.parent_name(root, info.parent_build_id) is None  # "from a deleted Build"


def test_identical_settings_are_allowed_and_reported_with_the_version_flag(root):
    first = _built(root, "One")
    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Two")
    matches = BA.identical_builds(root, "S1", BA.draft_config_hash(draft))
    assert [(m.ref, m.versions_differ) for m in matches] == [(first, False)]
    bj_path = root / "builds" / first / "datasets" / "build.json"
    bj = json.loads(bj_path.read_text(encoding="utf-8"))
    bj["software_versions"] = {"steamstudy": "0.0.1"}
    bj_path.write_text(json.dumps(bj), encoding="utf-8")
    assert [m.versions_differ for m in BA.identical_builds(root, "S1", BA.draft_config_hash(draft))] == [True]
    draft.description = "same settings, allowed"
    BA.save_draft(root, draft)
    BA.build_draft(root, draft, now=T2)
    assert len(list_builds(root)) == 2


def test_delete_moves_both_latest_pointers_removes_empty_ones_and_refuses_the_open_build(root):
    a = _built(root, "A", now=T1)
    b = _built(root, "B", source="S2", now=T2)
    c = _built(root, "C", now=T3)
    builds = root / "builds"
    (root / "bundles").mkdir()
    (root / "bundles" / f"tag-network-{c.split('/')[1]}-windows.zip").write_bytes(b"zip")
    assert (builds / "latest").read_text(encoding="utf-8").strip() == c

    with pytest.raises(BA.DeleteRefused):
        BA.delete_build(root, c, open_build=c)

    plan = BA.deletion_plan(root, c, open_build=a)
    assert plan.bundles == [f"tag-network-{c.split('/')[1]}-windows.zip"]
    assert plan.size_bytes > 0 and plan.latest_moves == {"S1": a, "root": b}
    BA.delete_build(root, c, open_build=a)
    assert not (builds / c).exists()
    assert (builds / "S1" / "latest").read_text(encoding="utf-8").strip() == a.split("/")[1]
    assert (builds / "latest").read_text(encoding="utf-8").strip() == b  # newest of any Snapshot

    BA.delete_build(root, b, open_build=a)
    assert not (builds / "S2" / "latest").exists()
    assert (builds / "latest").read_text(encoding="utf-8").strip() == a
    BA.delete_build(root, a, open_build=None)
    assert not (builds / "S1" / "latest").exists() and not (builds / "latest").exists()


def test_a_draft_from_an_old_shape_build_is_converted_to_named_rules(root):
    from steamstudy.config import load_config

    ref = _built(root, "Old shape")
    path = root / "builds" / ref / "datasets" / "build.json"
    bj = json.loads(path.read_text(encoding="utf-8"))
    bj["config"]["exclusions"] = {
        "allowed_app_types": ["game"], "global_rank_limit": 20,
        "per_tag_rank_limit": {"9551": 10},
        "adult_content": {"content_descriptor_ids": [3], "tags": [{"id": 9130, "name": "Hentai"}]},
        "software_tag": {"tags": [{"id": 8013, "name": "Software"}], "name_only": ["GameMaker"]},
        "dating_sim_tag": {"tags": [{"id": 9551, "name": "Dating Sim"}]},
        "content_flags": {"desktop_companion": {"tags": [{"id": 1320952, "name": "Desktop Companion"}]}},
    }
    path.write_text(json.dumps(bj), encoding="utf-8")
    draft = BA.duplicate(root, ref, "S1")
    ex = draft.config["exclusions"]
    assert "per_tag_rank_limit" not in ex and "adult_content" not in ex
    assert [r["name"] for r in ex["rule"]] == ["adult_content", "software_tag", "dating_sim_tag"]
    assert ex["rule"][2]["tags"] == [{"id": 9551, "name": "Dating Sim", "rank_limit": 10}]
    assert ex["content_flag"] == [{"name": "desktop_companion", "label": "desktop_companion",
                                   "tags": [{"id": 1320952, "name": "Desktop Companion"}]}]
    # The shipped config converts to itself.
    assert exclusions_new_shape(load_config(CONFIG_DIR).files["exclusions"]) == load_config(CONFIG_DIR).files["exclusions"]


def test_a_steam_build_does_not_accept_the_import_rank_limit_sentinel(root):
    from steamstudy.config import NO_RANK_LIMIT

    draft = BA.start_draft(root, "S1", config_dir=CONFIG_DIR, name="Unlimited")
    draft.config["exclusions"]["global_rank_limit"] = NO_RANK_LIMIT
    BA.save_draft(root, draft)
    with pytest.raises(BA.BuildFailed, match="between 1 and 20"):
        BA.build_draft(root, draft, now=T1)


def test_a_missing_snapshot_is_recorded_on_the_draft(root):
    import shutil

    draft = BA.start_draft(root, "S2", config_dir=CONFIG_DIR, name="Gone")
    BA.save_draft(root, draft)
    shutil.rmtree(root / "snapshots" / "S2")
    with pytest.raises(BA.BuildFailed):
        BA.build_draft(root, draft, now=T1)
    (kept,) = BA.list_drafts(root, "S2")
    assert kept.last_failure["kind"] == "message"
