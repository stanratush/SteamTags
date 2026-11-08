"""The Build's `analysis/` folder: network tables, Removal Sensitivity, Resolution Sweep and `analysis.json`."""

from __future__ import annotations

import json
from typing import Any

from steamstudy.analysis import features as F
from steamstudy.build.games import counted_tags
from steamstudy.analysis.network_stage import network_outputs
from steamstudy.dataset import import_games, steam_games
from steamstudy.config import Config
from steamstudy.export import schema as S
from steamstudy.export.schema import SCHEMA_VERSION, columns_block


def run_analysis(result: Any, config: Config) -> None:
    """Add the analysis tables and `analysis.json` to a BuildResult (in place). The datasets are read from
    `result.dataset_rows` (rows in the `top100_<dataset>.csv` shape; an Import Build's carry its score as
    `mean_monthly_players` and its filter value as `months_observed`). An Import Build gets the generic sections
    only, and its `analysis.json` lists the Import variants of the files."""
    depth = config.depth_cut
    kind = S.build_kind(result.build_json)
    dataset_rows = result.dataset_rows
    written: list[Any] = []
    counted_rows = {key: cut_rows(rows, depth) for key, rows in dataset_rows.items()}
    feature_summary = _feature_tables(result, config, counted_rows, written, kind)
    to_games = import_games if kind == "import" else steam_games
    net = network_outputs(config, result.build_id, {k: to_games(rows, depth) for k, rows in dataset_rows.items()})
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
        "columns": columns_block(sorted((S.REGISTRY.variant(s, kind) or s for s in written), key=lambda s: s.name),
                                 kind=kind),
    }
    result.analysis_json = analysis_json
    result.texts["analysis/analysis.json"] = json.dumps(analysis_json, indent=2, ensure_ascii=False) + "\n"


PUZZLE_NOTE = "Puzzle is not a Steam store genre: the store's genre field never shows it."


def cut_rows(rows: list[dict[str, Any]], depth: int | None) -> list[dict[str, Any]]:
    """Dataset rows with the tag lists cut to Tag Depth: the files keep the full lists, the analysis counts the
    first `depth` tags only."""
    if depth is None:
        return rows
    return [{**r, "tag_ids": r["tag_ids"][:depth], "tags": r["tags"][:depth]} for r in rows]


def _feature_tables(result: Any, config: Config, dataset_rows: dict[str, list[dict[str, Any]]],
                    written: list[Any], kind: str = "steam") -> dict[str, dict[str, Any]]:
    a = config.analysis
    flags = [f.name for f in config.exclusions.content_flags]
    tables: dict[str, list[dict[str, Any]]] = {name: [] for name in (
        "tag_frequency.csv", "genre_frequency.csv", "combinations.csv", "associations.csv", "content_flags.csv")}
    summary: dict[str, dict[str, Any]] = {}
    for d in config.datasets:
        top = dataset_rows[d.key]
        pool = [{"tag_ids": [t.tag_id for t in counted_tags(result.games[appid].tags, config.depth_cut)],
                 "genre_ids": [g.genre_id for g in result.games[appid].genres] if kind == "steam" else []}
                for appid in result.ranked[d.key].eligible]
        defining = d.defining_tag.id if d.defining_tag else None
        tables["tag_frequency.csv"] += F.tag_frequency(d.key, top, pool, defining)
        if kind == "steam":
            tables["genre_frequency.csv"] += F.genre_frequency(d.key, top, pool, config.genre_kind)
        tables["combinations.csv"] += F.combinations_table(d.key, top, defining, a.max_itemset_size, a.min_support)
        tables["associations.csv"] += F.associations_table(d.key, top, defining, a.min_support)
        flag_rows, flag_counts = F.content_flag_rows(d.key, top, flags)
        tables["content_flags.csv"] += flag_rows
        summary[d.key] = {"content_flag_counts": flag_counts,
                          "genre_note": PUZZLE_NOTE if kind == "steam" and d.defining_tag
                          and d.defining_tag.name == "Puzzle" else None}
    schemas = (S.TAG_FREQUENCY, S.GENRE_FREQUENCY, S.COMBINATIONS, S.ASSOCIATIONS, S.CONTENT_FLAG_GAMES)
    for schema in schemas if kind == "steam" else [s for s in schemas if s is not S.GENRE_FREQUENCY]:
        result.add(f"analysis/{schema.name}", schema, tables[schema.name])
        written.append(schema)
    return summary
