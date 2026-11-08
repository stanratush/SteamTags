"""Issue 22: the export schema keyed by Build kind (steam / import)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from steamstudy.export import schema as S
from steamstudy.export.writer import SchemaError, render_csv

FIXTURES = Path(__file__).parent / "fixtures"

DROPPED = {"archived_category", "months_observed", "release_month", "store_release_date", "is_free", "app_type",
           "genre_ids", "genres", "genre_id", "genre", "metadata_source", "top_listing_rank"}


# ----------------------------------------------------------------------------- registry


def test_a_file_is_looked_up_by_kind_group_and_name():
    assert S.file("steam/app_export/nodes.csv").kind == "steam"
    assert S.file("import/app_export/nodes.csv").kind == "import"
    assert S.file("app_export/nodes.csv") is S.file("steam/app_export/nodes.csv")  # two parts: Steam


def test_a_file_that_does_not_differ_is_declared_once_for_both_kinds():
    null = S.file("steam/app_export/null_model.csv")
    assert null is S.file("import/app_export/null_model.csv") and null.kind == "both"
    assert sum(1 for s in S.REGISTRY if s.name == "null_model.csv") == 1


def test_steam_only_files_have_no_import_variant():
    for key in ("build_reports/parse_errors.csv", "build_datasets/top100_<dataset>.csv", "analysis/genre_frequency.csv",
                "build_reports/impact_adult_signals.csv", "build_datasets/monthly_players.csv"):
        assert S.file(f"steam/{key}")
        with pytest.raises(KeyError):
            S.file(f"import/{key}")


def test_import_only_files_have_no_steam_variant():
    topn = S.file("import/build_datasets/topn_<dataset>.csv")
    assert topn.column_names == ("dataset", "rank", "id", "name", "score", "filter_value", "tag_ids", "tags")
    assert S.file("import/build_datasets/item_fields.csv").column_names == ("id", "field", "value")
    with pytest.raises(KeyError):
        S.file("steam/build_datasets/topn_<dataset>.csv")


# ----------------------------------------------------------------------------- derivation rule


def test_an_import_variant_renames_ids_and_score_and_drops_steam_only_columns():
    steam, imp = S.file("steam/build_reports/ties.csv"), S.file("import/build_reports/ties.csv")
    assert steam.column_names == ("dataset", "position", "appid", "name", "mean_monthly_players", "months_observed")
    assert imp.column_names == ("dataset", "position", "id", "name", "score")
    assert imp.name == steam.name
    freq = S.file("import/analysis/tag_frequency.csv")
    assert "archived_category" not in freq.column_names and {"tag_id", "tag"} <= set(freq.column_names)
    assert freq.column("tag_id").description == "Attribute id."
    assert S.file("import/app_export/edges.csv").column("ids").type == "int_list"


def test_every_import_variant_follows_the_rule_and_keeps_no_dropped_column():
    for steam in S.REGISTRY.of_kind("steam"):
        if steam.kind == "both":
            continue
        try:
            imp = S.REGISTRY[f"import/{steam.group}/{steam.name}"]
        except KeyError:
            continue
        renamed = {"appid": "id", "appids": "ids", "mean_monthly_players": "score"}
        expected = tuple(renamed.get(c, c) for c in steam.column_names if c not in DROPPED)
        assert imp.column_names == expected, steam.name
    for imp in S.REGISTRY.of_kind("import"):
        assert not DROPPED & set(imp.column_names), imp.name
        assert not {"appid", "appids", "mean_monthly_players"} & set(imp.column_names), imp.name
        assert all("Steam tag id" not in c.description and "AppID" not in c.description for c in imp.columns), imp.name
    assert "Steam" not in S.file("import/build_reports/exclusions.csv").column("name").description


def test_completeness_declares_the_import_section():
    section = S.file("import/build_reports/completeness.csv").column("section").description
    assert "import" in section and "listing" not in section


def test_the_import_build_file_list_is_data_in_the_registry():
    written = S.import_build_paths()
    assert {"datasets/build.json", "datasets/topn_<dataset>.csv", "datasets/item_fields.csv", "reports/exclusions.csv",
            "reports/ties.csv", "reports/reports.html", "analysis/network_nodes.csv", "analysis/removal_sensitivity.csv",
            "analysis/analysis.json", "analysis/report.html"} <= set(written)
    for name in ("parse_errors.csv", "genre_frequency.csv", "monthly_players.csv", "top100_<dataset>.csv",
                 "impact_unexcluded.csv", "skipped_apps.csv", "tag_vocabulary.csv"):
        assert not any(p.endswith("/" + name) for p in written), name
        assert name in S.IMPORT_NOT_WRITTEN or name == "top100_<dataset>.csv"


def test_writer_validation_is_strict_for_import_variants():
    ties = S.file("import/build_reports/ties.csv")
    row = {"dataset": "overall", "position": 11, "id": 7, "name": "x", "score": 1.5}
    assert render_csv(ties, [row]).splitlines()[0].lstrip("﻿") == "dataset,position,id,name,score"
    with pytest.raises(SchemaError):
        render_csv(ties, [{**row, "appid": 7}])


def test_a_columns_block_refuses_a_file_of_another_kind():
    assert "id" in S.columns_block([S.file("import/build_reports/ties.csv")], kind="import")["ties.csv"]
    with pytest.raises(ValueError):
        S.columns_block([S.file("import/build_reports/ties.csv")], kind="steam")
    with pytest.raises(ValueError):
        S.columns_block([S.file("steam/build_reports/ties.csv")], kind="import")


def test_build_kind_reads_the_build_json_source():
    assert S.build_kind({}) == "steam" and S.build_kind({"source": "import"}) == "import"


# ----------------------------------------------------------------------------- Steam output


def _changed_descriptions(old: dict, new: dict) -> dict[tuple[str, str], tuple[str, str]]:
    assert old.keys() == new.keys()
    changed = {}
    for file, columns in old.items():
        assert list(columns) == list(new[file]), file  # same columns, same order
        for name, info in columns.items():
            assert info["type"] == new[file][name]["type"]
            if info["description"] != new[file][name]["description"]:
                changed[(file, name)] = (info["description"], new[file][name]["description"])
    return changed


def test_steam_analysis_and_export_json_change_only_in_version_and_stacking_text(tagged_build):
    from steamstudy.app.export import export_zip
    from steamstudy.app.loader import load_build

    old = json.loads((FIXTURES / "schema5_columns.json").read_text(encoding="utf-8"))
    analysis = json.loads((tagged_build / "analysis" / "analysis.json").read_text(encoding="utf-8"))
    assert old["schema_version"] == 5 and analysis["schema_version"] == S.SCHEMA_VERSION == 6
    ctx = load_build(tagged_build)
    _, data = export_zip(ctx, ctx.default_settings("overall"))
    export = json.loads(zipfile.ZipFile(io.BytesIO(data)).read("export.json"))
    assert export["schema_version"] == 6
    assert _changed_descriptions(old["export_json_columns"], export["columns"]) == {}
    # The columns blocks carry column descriptions only; the stacking text is in the file description.
    assert _changed_descriptions(old["analysis_json_columns"], analysis["columns"]) == {}
    assert S.file("analysis/network_nodes.csv").description.endswith(" Every dataset stacked.")
    assert "Five" not in S.file("analysis/network_nodes.csv").description
    assert S.file("build_datasets/top100_<dataset>.csv").column("dataset").description == "Dataset key."


def test_a_schema_5_network_state_export_still_opens(tagged_build):
    from steamstudy.app.export import export_zip, open_export, read_export, recorded_table_hashes_match
    from steamstudy.app.loader import load_build

    ctx = load_build(tagged_build)
    _, data = export_zip(ctx, ctx.default_settings("overall"))
    export, files = read_export(data)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
        v5_columns = json.loads((FIXTURES / "schema5_columns.json").read_text(encoding="utf-8"))["export_json_columns"]
        zf.writestr("export.json", json.dumps({**export, "schema_version": 5, "columns": v5_columns}))
    v5 = buffer.getvalue()
    opened = open_export(v5, builds_root=tagged_build.parent.parent)
    assert opened.schema_version == 5 and recorded_table_hashes_match(opened, v5)
