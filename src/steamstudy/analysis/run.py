"""The Build's `analysis/` folder: network tables, Removal Sensitivity, Resolution Sweep and `analysis.json`."""

from __future__ import annotations

import json
from typing import Any

from steamstudy.analysis.network_stage import network_outputs
from steamstudy.config import Config
from steamstudy.export import schema as S
from steamstudy.export.schema import SCHEMA_VERSION, columns_block


def run_analysis(result: Any, config: Config) -> None:
    """Add the analysis tables and `analysis.json` to a BuildResult (in place)."""
    dataset_rows = {d.key: result.rows(f"datasets/top100_{d.key}.csv") for d in config.datasets}
    net = network_outputs(config, result.build_id, dataset_rows)
    written = []
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
            key: {**info, "eligible_pool": result.build_json["dataset_sizes"][key]["eligible_pool"]}
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
