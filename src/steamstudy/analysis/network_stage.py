"""The Build's network outputs: each Top-100 Dataset's Network State at the report's settings.

Uses the same `steamstudy.network` computation and the same table writer as the app export, so the
app opened at these settings gives exactly these rows (minus `dataset` / `state_id`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from steamstudy.config import Config, DatasetDef
from steamstudy.network.defaults import default_settings
from steamstudy.network.model import Settings, TagContext, games_from_rows
from steamstudy.network.sensitivity import METHOD_VERSION, expected_chance_flags, removal_sensitivity
from steamstudy.network.state import NetworkState, compute_state
from steamstudy.network.sweep import resolution_sweep, sweep_grid
from steamstudy.network.tables import stack, state_tables


def report_settings(config: Config, build_id: str, dataset: DatasetDef) -> tuple[Settings, TagContext]:
    """The shared network defaults with the defining tag out: the feature-analysis report's Network State."""
    defining = dataset.defining_tag.id if dataset.defining_tag else None
    return default_settings(build_id, dataset.key, defining, (t.id for t in config.genre_tags), config.network)


@dataclass
class NetworkOutputs:
    tables: dict[str, list[dict[str, Any]]]  # app file name -> stacked rows
    sweep: list[dict[str, Any]]
    states: dict[str, NetworkState]
    summary: dict[str, Any]


def network_outputs(config: Config, build_id: str, dataset_rows: dict[str, list[dict[str, Any]]]) -> NetworkOutputs:
    tables: dict[str, list[dict[str, Any]]] = {}
    sweep_rows: list[dict[str, Any]] = []
    states: dict[str, NetworkState] = {}
    per_dataset: dict[str, Any] = {}
    grid = sweep_grid(config.network.resolution_sweep, config.network.resolution)
    for d in config.datasets:
        settings, context = report_settings(config, build_id, d)
        state = compute_state(games_from_rows(dataset_rows[d.key]), settings, context)
        states[d.key] = state
        for name, rows in state_tables(state).items():
            tables.setdefault(name, []).extend(stack(rows, d.key, state.state_id))
        rs = removal_sensitivity(state)
        tables.setdefault("removal_sensitivity.csv", []).extend(stack(rs, d.key, state.state_id))
        sweep = resolution_sweep(state, grid)
        sweep_rows.extend({"dataset": d.key, **r} for r in sweep)
        flagged = sum(r["rc_ari_beyond_noise"] for r in rs)
        per_dataset[d.key] = {
            "state_key": state.key,
            "state_id": state.state_id,
            "n_games": state.network.n_games,
            "seed_noise_floor": {k: v for k, v in state.seed_summary().items()},
            "n_disconnected_clusters": state.n_disconnected,
            "removal_sensitivity": {
                "method_version": METHOD_VERSION, "tags_tested": len(rs), "tags_flagged": flagged,
                "expected_by_chance_at_most": expected_chance_flags(len(rs), settings.noise_seeds),
            },
            "resolution_sweep": _sweep_ranges(sweep, settings.resolution),
        }
    return NetworkOutputs(tables, sweep_rows, states, {"datasets": per_dataset, "resolution_grid": grid})


def _sweep_ranges(rows: list[dict[str, Any]], gamma: float) -> dict[str, Any]:
    ks = [r["n_multi_tag_clusters"] for r in rows]
    aris = [r["ari_vs_report"] for r in rows]
    return {"gamma_min": rows[0]["resolution"] if rows else None, "gamma_max": rows[-1]["resolution"] if rows else None,
            "report_gamma": gamma, "k_min": min(ks) if ks else None, "k_max": max(ks) if ks else None,
            "ari_min": min(aris) if aris else None, "ari_max": max(aris) if aris else None}
