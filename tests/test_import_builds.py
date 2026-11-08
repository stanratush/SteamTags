"""Issue 26: Import Builds, built from an Import and analysed by the app exactly like Steam Builds."""

from __future__ import annotations

import datetime as dt
import json
import random
import shutil
from pathlib import Path

import pytest

from conftest import CONFIG_DIR
from steamstudy import imports as I
from steamstudy.build.core import BuildFailed, BuildIdentity
from steamstudy.build.import_build import build_import, import_defaults, open_import
from steamstudy.build.writer import write_build
from steamstudy.export import schema as S
from steamstudy.export.writer import read_csv

BUILD_ID = "20261108T120000Z-abcdef12"
GROUPS = [["Action", "Shooter", "Arena", "Fast", "Loud"], ["Puzzle", "Logic", "Calm", "Grid", "Tiles"],
          ["Farming", "Cozy", "Crafting", "Seasons", "Village"], ["Space", "Ships", "Trade", "Stars", "Fleet"]]
ALL = [a for g in GROUPS for a in g]


def _csv(n: int = 60, *, score: bool = True, filter_field: bool = True, extra: bool = True) -> str:
    rng = random.Random(7)
    head = ["id", "name", "attributes"] + (["score"] if score else []) + (["months"] if filter_field else []) \
        + (["price"] if extra else [])
    lines = [",".join(head)]
    for i in range(n):
        group = GROUPS[i % 4]
        attrs = rng.sample(group, 4) + rng.sample([a for a in ALL if a not in group], 2)
        if i % 3 == 0 and "Puzzle" not in attrs:
            attrs.append("Puzzle")
        cells = [str(1000 + i), f"Item {i}", ";".join(attrs)]
        if score:
            cells.append(str(500 - i * 3 if i != 40 else 500 - 39 * 3))  # item 40 ties rank 40 (item 39)
        if filter_field:
            cells.append(str(3 + (i % 24) * 0.5))
        if extra:
            cells.append("" if i % 5 == 0 else f"{i % 7}.99")
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


def _import(root: Path, text: str, name: str = "items.csv", **kw) -> str:
    src = root / "incoming" / name
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(text, encoding="utf-8")
    return I.make_import(root, src, now=dt.datetime(2026, 11, 8, 11, 0, tzinfo=dt.UTC), **kw).name


def _files(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.fixture(scope="module")
def full(tmp_path_factory):
    """An Import with a score, a filter field and an extra field, and its Build with two datasets."""
    root = tmp_path_factory.mktemp("imp")
    import_id = _import(root, _csv(), filter_field="months")
    source = open_import(root, import_id)
    files = import_defaults(source, CONFIG_DIR)
    files["datasets"]["dataset"] = [{"key": "overall", "label": "Overall", "list_size": 40},
                                    {"key": "puzzle", "label": "Puzzle", "defining_tag": {"name": "Puzzle"},
                                     "list_size": 10}]
    return root, source, files, write_build(build_import(source, files, BUILD_ID), root)


# ----------------------------------------------------------------------------- the Build


def test_an_import_build_is_deterministic_and_writes_exactly_the_import_files(full, tmp_path):
    root, source, files, folder = full
    again = write_build(build_import(source, files, BUILD_ID), tmp_path)
    assert _files(folder) == _files(again)
    written = set(_files(folder))
    expected = {p.replace("<dataset>", k) for p in S.import_build_paths() for k in ("overall", "puzzle")}
    assert written == expected
    assert folder.parent.name == source.import_id


def test_no_steam_only_file_or_column_is_written(full):
    folder = full[3]
    steam_columns = S.IMPORT_DROPPED | set(S.IMPORT_RENAMED)
    for path in folder.rglob("*.csv"):
        header = set(read_csv(path)[0]) if read_csv(path) else set(path.read_text(encoding="utf-8-sig")
                                                                     .splitlines()[0].split(","))
        assert not header & steam_columns, (path.name, header & steam_columns)
    bj = json.loads((folder / "datasets" / "build.json").read_text(encoding="utf-8"))
    assert bj["source"] == "import" and bj["import_id"] == full[1].import_id
    assert bj["import_sha256"] == full[1].meta["sha256"] and bj["filter_field"] == "months"
    assert bj["score_present"] is True and bj["extra_fields"] == ["price"]
    for key in ("snapshot_id", "collection_date", "observation_window", "store_country", "taglist_version_hash",
                "manual_metadata_entries", "source_substitutions"):
        assert key not in bj
    analysis = json.loads((folder / "analysis" / "analysis.json").read_text(encoding="utf-8"))
    assert "genre_frequency.csv" not in analysis["columns"]
    assert "appid" not in json.dumps(analysis["columns"])


def test_the_datasets_rank_by_score_and_keep_full_lists_and_fields(full):
    root, source, _, folder = full
    rows = read_csv(folder / "datasets" / "topn_overall.csv")
    assert len(rows) == 40 and [r["id"] for r in rows[:3]] == ["1000", "1001", "1002"]
    puzzle = read_csv(folder / "datasets" / "topn_puzzle.csv")
    assert len(puzzle) == 10 and all("Puzzle" in r["tags"] for r in puzzle)
    fields = read_csv(folder / "datasets" / "item_fields.csv")
    assert {r["field"] for r in fields} == {"price"} and not any(r["id"] == "1000" for r in fields)  # empty cell
    ties = read_csv(folder / "reports" / "ties.csv")
    assert list(ties[0]) == ["dataset", "position", "id", "name", "score"] and ties[0]["id"] == "1040"
    completeness = read_csv(folder / "reports" / "completeness.csv")
    assert {r["section"] for r in completeness} == {"exclusions_overlapping", "exclusions_primary", "depth_check",
                                                     "import"}
    html = (folder / "analysis" / "report.html").read_text(encoding="utf-8")
    assert "Months Observed" not in html and "free to play" not in html


def test_an_import_without_score_filter_or_fields_builds_in_file_order(tmp_path):
    import_id = _import(tmp_path, _csv(score=False, filter_field=False, extra=False))
    source = open_import(tmp_path, import_id)
    folder = write_build(build_import(source, import_defaults(source, CONFIG_DIR), BUILD_ID), tmp_path)
    again = write_build(build_import(source, import_defaults(source, CONFIG_DIR), BUILD_ID), tmp_path / "again")
    assert _files(folder) == _files(again)
    rows = read_csv(folder / "datasets" / "topn_overall.csv")
    assert len(rows) == 60 and [r["id"] for r in rows] == [str(1000 + i) for i in range(60)]
    assert rows[0]["score"] == "" and rows[0]["filter_value"] == ""
    assert not (folder / "reports" / "ties.csv").exists()
    assert read_csv(folder / "datasets" / "item_fields.csv") == []


# ----------------------------------------------------------------------------- settings


def _pool(source, files) -> list[int]:
    result = build_import(source, files, BUILD_ID)
    return result.ranked["overall"].eligible


def test_a_rule_a_manual_exclusion_and_an_override_change_the_pool(full):
    _, source, base, _ = full
    files = json.loads(json.dumps(base))
    files["datasets"]["dataset"] = files["datasets"]["dataset"][:1]
    everyone = _pool(source, files)
    assert len(everyone) == 60
    files["exclusions"]["rule"] = [{"name": "no_space", "label": "Space",
                                    "attributes": [{"name": "Space", "rank_limit": 2}]}]
    ruled = _pool(source, files)
    removed = set(everyone) - set(ruled)
    assert removed and all(source.tables.attributes[next(a for a in i.attribute_ids if
                                                         source.tables.attributes[a] == "Space")] == "Space"
                           for i in source.tables.items if i.id in removed)
    evidence = [{"url": "https://example.invalid/e", "retrieved": "2026-11-08"}]
    keep = sorted(removed)[0]
    files["exclusion_overrides"] = {"override": [{"id": keep, "rule": "no_space", "name": "kept", "reason": "test",
                                                  "added": "2026-11-08", "evidence": evidence}]}
    files["manual_exclusions"] = {"exclusion": [{"id": 1001, "name": "Item 1", "reason": "test",
                                                 "added": "2026-11-08", "evidence": evidence}]}
    final = _pool(source, files)
    assert keep in final and 1001 not in final and set(final) == (set(ruled) | {keep}) - {1001}


@pytest.mark.parametrize("change, message", [
    (lambda f: f["genres"].update(genre_tags=[{"name": "Nope"}]), "not in the Import"),
    (lambda f: f["datasets"]["dataset"][1].update(defining_tag={"name": "Puzzle", "id": 99}), "has id"),
    (lambda f: f["exclusions"].update(allowed_app_types=["game"]), "not a setting of an Import Build"),
    (lambda f: f["exclusion_overrides"].update(override=[{"id": 1000, "rule": "app_type"}]), "not a named rule"),
    (lambda f: f["datasets"].update(tag_depth=99), "longest attribute list"),
    (lambda f: f["datasets"]["dataset"][0].update(list_size=61), "only 60 eligible"),
])
def test_invalid_settings_fail_the_build(full, change, message):
    files = json.loads(json.dumps(full[2]))
    change(files)
    with pytest.raises(BuildFailed, match=message):
        build_import(full[1], files, BUILD_ID)


def test_build_admin_drafts_an_import_from_its_defaults(full, tmp_path):
    from steamstudy import build_admin as BA

    root = tmp_path
    shutil.copytree(full[0] / "imports", root / "imports")
    draft = BA.start_draft(root, full[1].import_id, config_dir=CONFIG_DIR, name="Defaults")
    assert draft.config["datasets"]["dataset"] == [{"key": "overall", "label": "Overall", "list_size": 60}]
    assert set(draft.config) == {"datasets", "exclusions", "exclusion_overrides", "manual_exclusions", "genres",
                                 "analysis", "network"}
    draft.description = "the Import defaults"
    BA.save_draft(root, draft)
    folder = BA.build_draft(root, draft, now=dt.datetime(2026, 11, 8, 12, 0, tzinfo=dt.UTC))
    bj = json.loads((folder / "datasets" / "build.json").read_text(encoding="utf-8"))
    assert bj["name"] == "Defaults" and bj["changelog"][-1]["text"] == "the Import defaults"
    assert bj["build_id"].endswith(BA.draft_config_hash(draft)[:8])


def test_the_cli_builds_an_import_from_its_defaults(full, tmp_path):
    from steamstudy.cli import main

    shutil.copytree(full[0] / "imports", tmp_path / "imports")
    assert main(["--config", str(CONFIG_DIR), "--root", str(tmp_path), "build", "--import", full[1].import_id,
                 "--name", "From the CLI"]) == 0
    (folder,) = [p for p in (tmp_path / "builds" / full[1].import_id).iterdir() if p.is_dir()]
    assert json.loads((folder / "datasets" / "build.json").read_text(encoding="utf-8"))["name"] == "From the CLI"


# ----------------------------------------------------------------------------- the app


def test_the_app_reads_an_import_build_through_the_seam(full):
    from steamstudy.app.loader import load_build

    ctx = load_build(full[3])
    ds = ctx.read("overall")
    assert ds.id_label == "ID" and ds.filter_field.label == "months"
    assert (ds.filter_field.minimum, ds.filter_field.maximum) == (3, 15)
    assert ds.items[0].filter_value == 3.0 and ds.items[1].fields == {"price": 1.99}
    puzzle = ctx.read("puzzle")
    assert puzzle.defining_attribute == source_id(full, "Puzzle")
    assert [g.appid for g in ctx.games("overall")][:2] == [1000, 1001]


def source_id(full, name: str) -> int:
    return next(i for i, n in full[1].tables.attributes.items() if n == name)


def test_the_workbench_export_and_open_round_trip_on_an_import_build(full, tmp_path):
    from steamstudy.app import callbacks as CB
    from steamstudy.app.export import BuildNotFound, export_zip, open_export, read_export
    from steamstudy.app.loader import load_build
    from steamstudy.network.sensitivity import removal_sensitivity
    from steamstudy.network.state import compute_state

    folder = full[3]
    ctx = load_build(folder)
    settings = ctx.default_settings("overall")
    values = CB.controls_from_settings(ctx, settings)
    out = CB.recompute(str(folder), *[values[k] for k in CB.CONTROL_IDS], values["removed"], None)
    assert out  # the Workbench computes the state
    state = compute_state(ctx.games("overall"), settings, ctx.context("overall"))
    rows = removal_sensitivity(state)[:2]
    _, data = export_zip(ctx, settings, removal_rows=rows, state=state)
    export, files = read_export(data)
    assert b"appid" not in files["edges.csv"] and b"appid" not in files["cluster_games.csv"]
    opened = open_export(data, builds_root=folder.parents[1])
    assert opened.settings == settings and opened.state_id_matches
    empty = tmp_path / "builds"
    empty.mkdir()
    with pytest.raises(BuildNotFound) as refused:
        open_export(data, builds_root=empty)
    assert full[1].import_id in str(refused.value) and refused.value.reason == "build_not_found_import"


def test_parameter_selection_runs_on_an_import_build(full, tmp_path):
    from steamstudy.app import ps_run
    from steamstudy.app.loader import load_build
    from steamstudy.network import selection as SEL

    folder = tmp_path / "builds" / full[3].parent.name / full[3].name
    shutil.copytree(full[3], folder, ignore=shutil.ignore_patterns("app_cache"))
    ctx = load_build(folder)
    base = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    settings = base.with_(g_range=(3, 5), s_range=(2, 3), replicates=2, subsamples=2)
    outcomes = ps_run.run(ctx, settings, ["overall"])
    assert [o.grid for o in outcomes] == ["complete"]


@pytest.mark.parametrize("with_filter", [True, False])
def test_the_app_serves_an_import_build_with_and_without_a_filter_field(full, tmp_path, with_filter):
    from dash_http import layout_props
    from steamstudy.app.server import create_app

    if with_filter:
        folder = full[3]
    else:
        import_id = _import(tmp_path, _csv(filter_field=False))
        source = open_import(tmp_path, import_id)
        folder = write_build(build_import(source, import_defaults(source, CONFIG_DIR), BUILD_ID), tmp_path)
    client = create_app(folder).server.test_client()
    assert client.get("/").status_code == 200
    props = layout_props(json.loads(client.get("/_dash-layout").get_data(as_text=True)))
    assert "min-months" in props and "ps-s-min-months" in props  # the callbacks always find the sliders
    # The range comes from the data (3 to 14.5 months); without a filter field the slider is a hidden 0-1 stub.
    assert (props["min-months"]["min"], props["min-months"]["max"]) == ((3, 15) if with_filter else (0, 1))


def test_an_import_build_duplicates_only_within_its_import_and_a_missing_import_is_recorded(full, tmp_path):
    from steamstudy import build_admin as BA

    root = tmp_path
    shutil.copytree(full[0] / "imports", root / "imports")
    import_id = full[1].import_id
    draft = BA.start_draft(root, import_id, config_dir=CONFIG_DIR, name="First")
    BA.save_draft(root, draft)
    folder = BA.build_draft(root, draft, now=dt.datetime(2026, 11, 8, 12, 0, tzinfo=dt.UTC))
    ref = f"{import_id}/{folder.name}"
    assert BA.duplicate(root, ref, import_id, name="Second").parent_build_id == ref
    with pytest.raises(BA.WrongSource):
        BA.duplicate(root, ref, "S1", name="Elsewhere")

    draft = BA.start_draft(root, import_id, config_dir=CONFIG_DIR, name="Orphan")
    BA.save_draft(root, draft)
    shutil.rmtree(root / "imports" / import_id / "original")  # the Import is damaged after the draft was saved
    (root / "imports" / import_id / "items.csv").unlink()
    with pytest.raises(BA.BuildFailed):
        BA.build_draft(root, draft, now=dt.datetime(2026, 11, 8, 13, 0, tzinfo=dt.UTC))
    (kept,) = [d for d in BA.list_drafts(root, import_id) if d.name == "Orphan"]
    assert kept.last_failure["kind"] == "message"
