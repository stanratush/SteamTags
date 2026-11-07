"""The Build's `analysis/` folder: network tables, Removal Sensitivity, Resolution Sweep and `analysis.json`."""

from __future__ import annotations

import json
from typing import Any

from steamstudy.analysis import features as F
from steamstudy.analysis.network_stage import network_outputs
from steamstudy.config import Config
from steamstudy.export import schema as S
from steamstudy.export.schema import SCHEMA_VERSION, columns_block


def run_analysis(result: Any, config: Config) -> None:
    """Add the analysis tables and `analysis.json` to a BuildResult (in place)."""
    dataset_rows = {d.key: result.rows(f"datasets/top100_{d.key}.csv") for d in config.datasets}
    written: list[Any] = []
    feature_summary = _feature_tables(result, config, dataset_rows, written)
    net = network_outputs(config, result.build_id, dataset_rows)
    for app_name, rows in net.tables.items():
        schema = S.stacked(app_name)
        result.add(f"analysis/{schema.name}", schema, rows)
        written.append(schema)
    result.add("analysis/resolution_sweep.csv", S.RESOLUTION_SWEEP, net.sweep)
    written.append(S.RESOLUTION_SWEEP)
    result.network_states = net.states

    analysis_json = {
        "schema_version": SCHEMA_VERSION,
        "build_id": result.build_id,
        "datasets": {
            key: {**info, "eligible_pool": result.build_json["dataset_sizes"][key]["eligible_pool"],
                  **feature_summary[key]}
            for key, info in net.summary["datasets"].items()
        },
        "resolution_sweep": {
            "grid": net.summary["resolution_grid"],
            "ranges": {k: v["resolution_sweep"] for k, v in net.summary["datasets"].items()},
        },
        "removal_sensitivity": "complete table per dataset at the report's settings (removal_sensitivity.csv)",
        "columns": columns_block(sorted(written, key=lambda s: s.name)),
    }
    result.analysis_json = analysis_json
    result.texts["analysis/analysis.json"] = json.dumps(analysis_json, indent=2, ensure_ascii=False) + "\n"


PUZZLE_NOTE = "Puzzle is not a Steam store genre: the store's genre field never shows it."


def _feature_tables(result: Any, config: Config, dataset_rows: dict[str, list[dict[str, Any]]],
                    written: list[Any]) -> dict[str, dict[str, Any]]:
    a = config.analysis
    flags = [f.name for f in config.exclusions.content_flags]
    tables: dict[str, list[dict[str, Any]]] = {name: [] for name in (
        "tag_frequency.csv", "genre_frequency.csv", "combinations.csv", "associations.csv", "content_flags.csv")}
    summary: dict[str, dict[str, Any]] = {}
    for d in config.datasets:
        top = dataset_rows[d.key]
        pool = [{"tag_ids": [t.tag_id for t in result.games[appid].tags],
                 "genre_ids": [g.genre_id for g in result.games[appid].genres]}
                for appid in result.ranked[d.key].eligible]
        defining = d.defining_tag.id if d.defining_tag else None
        tables["tag_frequency.csv"] += F.tag_frequency(d.key, top, pool, defining)
        tables["genre_frequency.csv"] += F.genre_frequency(d.key, top, pool, config.genre_kind)
        tables["combinations.csv"] += F.combinations_table(d.key, top, defining, a.max_itemset_size, a.min_support)
        tables["associations.csv"] += F.associations_table(d.key, top, defining, a.min_support)
        flag_rows, flag_counts = F.content_flag_rows(d.key, top, flags)
        tables["content_flags.csv"] += flag_rows
        summary[d.key] = {"content_flag_counts": flag_counts,
                          "genre_note": PUZZLE_NOTE if d.defining_tag and d.defining_tag.name == "Puzzle" else None}
    for schema in (S.TAG_FREQUENCY, S.GENRE_FREQUENCY, S.COMBINATIONS, S.ASSOCIATIONS, S.CONTENT_FLAG_GAMES):
        result.add(f"analysis/{schema.name}", schema, tables[schema.name])
        written.append(schema)
    return summary
