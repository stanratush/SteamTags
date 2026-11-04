"""Export tables: one record-only zip per settings key, from the Parameter Selection cache and the current constraints.

Seven tables stacked by `dataset` (complete grids only), `parameter_selection.json` and `selection_report.md`.
Dash-free. The same Build, settings and cache give byte-identical tables.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from steamstudy.app import ps_cache
from steamstudy.app.loader import BuildContext
from steamstudy.export import schema as S
from steamstudy.export.writer import csv_bytes
from steamstudy.i18n import text
from steamstudy.network import selection as SEL
from steamstudy.network import selection_text as T
from steamstudy.network import validation as V
from steamstudy.network.cluster import PASS_CAP, label_clusters
from steamstudy.network.stability import TRADES_PER_GAME, noise_seeds, replicate_seeds
from steamstudy.versions import software_versions

DIRECTION_NAMES = {"g-": "g−", "g+": "g+", "s-": "s−", "s+": "s+"}


def zip_name(settings: SEL.SelectionSettings, now: dt.datetime) -> str:
    return (f"steamstudy_parameter-selection_{SEL.key_hash(settings.settings_key())[:12]}_"
            f"{now.strftime('%Y%m%dT%H%M%SZ')}.zip")


def constraints_for(store: Mapping[str, Any] | None, dataset: str, defaults: SEL.Constraints) -> SEL.Constraints:
    """The mode's constraints store: the dataset's override, else the shared set, else the defaults."""
    store = store or {}
    data = (store.get("datasets") or {}).get(dataset) or store.get("shared")
    return SEL.Constraints(**{k: data[k] for k in asdict(defaults)}) if data else defaults


def tag_names(ctx: BuildContext) -> dict[int, str]:
    names: dict[int, str] = {}
    for d in ctx.datasets:
        for g in ctx.games(d.key):
            for t, n in zip(g.tag_ids, g.tags):
                names.setdefault(t, n)
    return names


def _pair_rows(dataset: str, grid: SEL.Grid, na: Mapping[tuple[int, int], SEL.NeighbourAgreement],
               choice: SEL.Choice) -> list[dict[str, Any]]:
    rows = []
    for g, s in grid.pairs:
        r = grid.at(g, s)
        a = na[(g, s)]
        p = r.selected_partition
        wb = r.workbench or {}
        noise = r.seed_noise or {}
        rows.append({
            "dataset": dataset, "g": g, "s": s, "n_tags": r.n_tags, "n_edges": r.n_edges, "n_e": r.n_e,
            "graph_hash": r.graph_hash, "lift_below_1_share": r.lift_below_1_share,
            "gamma_max_n_e": r.gamma_max_n_e, "gamma_end": r.gamma_end, "scan_length": r.scan_length,
            "pass_capped_runs": r.pass_capped_runs, "n_unique": r.n_unique, "n_twins": r.n_twins,
            "selection_reason": r.reason if p is None else None,
            "selected_low": None if p is None else p["a"], "selected_high": None if p is None else p["b"],
            "selected_resolution": r.selected_resolution, "clipped_high": None if p is None else p["clipped_high"],
            "workbench_gamma": wb.get("gamma"), "workbench_seed": wb.get("seed"),
            "reproduced": None if p is None else wb.get("flag") is None,
            "workbench_ari": wb.get("ari"), "not_representable": None if p is None else wb.get("flag") ==
            "not_representable", "not_reproduced": None if p is None else wb.get("flag") == "not_reproduced",
            "neighbour_agreement": a.value, "na_status": a.status, "n_comparable": a.n_comparable,
            "n_different_graph": a.n_different, "n_identical_graph": a.n_identical, "n_missing": a.n_missing,
            "na_min_ari": a.min_ari, "retention": r.retention, "retention_status": r.retention_status,
            "games_with_edged_tag_share": r.games_with_edged_tag_share, "n_isolated": r.n_isolated,
            "isolated_share": r.isolated_share, "n_components": r.n_components, "lcc_tags": r.lcc_tags,
            "lcc_share": r.lcc_share, "n_multi_tag_clusters": r.n_multi, "n_one_isolated": r.n_one_isolated,
            "n_one_connected": r.n_one_connected, "seed_noise_floor": noise.get("floor"),
            "seed_noise_mean": noise.get("mean"), "seed_noise_exact": noise.get("exact"),
            "hits": None if p is None else p["hits"], "modularity": r.modularity, "coverage": r.coverage,
            "silhouette": r.silhouette, "silhouette_status": r.silhouette_status,
            "qualifies": not choice.reasons[(g, s)], "reasons": choice.reasons[(g, s)],
            "near_best": (g, s) in choice.near_best, "chosen": choice.chosen == (g, s),
        })
    return rows


def _admissible_rows(dataset: str, grid: SEL.Grid) -> list[dict[str, Any]]:
    rows = []
    for g, s in grid.pairs:
        r = grid.at(g, s)
        if r.champ is None:
            continue
        for i, p in enumerate(r.champ["admissible"]):
            rows.append({
                "dataset": dataset, "g": g, "s": s, "partition": i + 1, "a_hat": p["a_hat"], "p_hat": p["p_hat"],
                "domain_low": p["a"], "domain_high": p["b"], "clipped_high": p["clipped_high"],
                "omega_in": p["omega_in"], "omega_out": p["omega_out"], "gamma_hat": p["gamma_hat"],
                "gamma_hat_reason": p["reason"], "map_target": None if p["target"] is None else p["target"] + 1,
                "stable": p["stable"], "n_multi_tag_clusters": p["n_multi"], "n_one_tag_clusters": p["n_one"],
                "first_gamma": p["first_gamma"], "first_seed": p["first_seed"], "hits": p["hits"],
                "selected": r.champ["selected"] == i,
            })
    return rows


def _link_rows(dataset: str, grid: SEL.Grid, links: list[SEL.Link]) -> list[dict[str, Any]]:
    rows = []
    for g, s in grid.pairs:
        for name, (dg, ds) in SEL.DIRECTIONS.items():
            x = SEL.pair_links(links, g, s, grid.pairs)[name]
            base = {"dataset": dataset, "g": g, "s": s, "direction": DIRECTION_NAMES[name], "neighbour_g": g + dg,
                    "neighbour_s": s + ds}
            if x is None:
                rows.append({**base, "status": "outside_grid", "identical_graph": None, "n_shared": None,
                             "shared_jaccard": None, "n_compared": None, "ari": None, "edge_overlap": None})
            else:
                rows.append({**base, "status": x.status, "identical_graph": x.identical_graph, "n_shared": x.n_shared,
                             "shared_jaccard": x.shared_jaccard, "n_compared": x.n_compared, "ari": x.ari,
                             "edge_overlap": x.edge_overlap})
    return rows


def _selected_rows(dataset: str, grid: SEL.Grid, names: Mapping[int, str]) -> list[dict[str, Any]]:
    rows = []
    for g, s in grid.pairs:
        r = grid.at(g, s)
        label: dict[int, str] = {}
        if r.selected is not None:
            groups: dict[int, set[int]] = {}
            for t, c in zip(r.nodes, r.selected):
                groups.setdefault(c, set()).add(t)
            label = {t: c.label for c in label_clusters([frozenset(x) for x in groups.values()]) for t in c.members}
        rows += [{"dataset": dataset, "g": g, "s": s, "tag_id": t, "tag": names.get(t, str(t)),
                  "cluster": label.get(t)} for t in r.nodes]
    return rows


def _selection_row(dataset: str, choice: SEL.Choice, constraints_label: str, settings_label: str) -> dict[str, Any]:
    c = choice.constraints
    return {
        "dataset": dataset, "status": choice.status, "chosen_g": choice.chosen[0] if choice.chosen else None,
        "chosen_s": choice.chosen[1] if choice.chosen else None, "max_neighbour_agreement": choice.max_na,
        "tolerance": c.tolerance, "near_best": [f"{g}·{s}" for g, s in choice.near_best],
        "tie_break": "smallest g, then smallest s", "n_qualifying": len(choice.qualifying),
        "min_retention": c.min_retention, "max_isolated_share": c.max_isolated_share, "min_lcc_share": c.min_lcc_share,
        "min_comparable_neighbours": c.min_comparable_neighbours, "max_multi_tag_clusters": c.max_multi_tag_clusters,
        "constraints_label": constraints_label, "settings_label": settings_label,
    }


def _validation_rows(dataset: str, pair: tuple[int, int], validation: Mapping[str, Any]) -> tuple[list, list]:
    g, s = pair
    reps, clusters = [], []
    for r in validation["records"]:
        base = {"dataset": dataset, "g": g, "s": s, "replicate": r["index"], "seed": r["seed"],
                "n_edges": r["n_edges"], "scan_length": r["scan_length"], "capped_runs": r["capped_runs"]}
        if r["kind"] == "null":
            reps.append({**base, "arm": "null", "has_selected_partition": r["selected"],
                         "reason": None if r["selected"] else r["reason"], "degenerate": None,
                         "degenerate_reason": None, "ari": None, "null_q": r["q_fixed"], "domain_width": r["width"],
                         "selected_resolution": r["resolution"], "n_multi_tag_clusters": r["n_multi"]})
            continue
        for arm, name in (("reselected", "subsample_reselected"), ("at_resolution", "subsample_at_resolution")):
            x = r["arms"][arm]
            reps.append({**base, "arm": name,
                         "has_selected_partition": None if arm != "reselected" else x["degenerate"] is None,
                         "reason": None, "degenerate": x["degenerate"] is not None,
                         "degenerate_reason": x["degenerate"], "ari": x["ari"], "null_q": None, "domain_width": None,
                         "selected_resolution": x.get("resolution"), "n_multi_tag_clusters": x.get("n_multi")})
    summary = validation["summary"]
    for arm, name in (("reselected", "subsample_reselected"), ("at_resolution", "subsample_at_resolution")):
        for c in summary["subsample"][arm]["clusters"]:
            clusters.append({"dataset": dataset, "g": g, "s": s, "arm": name, "cluster": c["label"],
                             "member_tag_ids": c["members"], "mean_jaccard": c["mean_jaccard"],
                             "at_most_half": c["at_most_half"], "present": c["present"],
                             "mean_retention": c["mean_retention"], "absent": c["absent"],
                             "dissolved": c["dissolved"]})
    return reps, clusters


def export_tables(ctx: BuildContext, settings: SEL.SelectionSettings, constraints_store: Mapping[str, Any] | None,
                  *, now: dt.datetime | None = None, cache_root: Path | None = None) -> tuple[str, bytes]:
    now = now or dt.datetime.now(dt.UTC)
    cache_root = Path(cache_root or ctx.app_cache)
    defaults_settings = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    default_constraints = SEL.default_constraints(ctx.network)
    names = tag_names(ctx)
    en = text("en")  # the export is English in every Interface Language (ADR 0003)
    settings_label = SEL.settings_label(settings, defaults_settings, names, tx=en)
    tables: dict[str, list[dict[str, Any]]] = {s.name: [] for s in S.PS_TABLES}
    datasets: dict[str, Any] = {}
    report: list[str] = [f"# Parameter Selection report\n\nBuild {ctx.build_id} · {settings_label.text}."]
    scan, null, sub = SEL.selection_seeds(settings)
    for d in ctx.datasets:
        key = settings.grid_key(d.key, ctx.context(d.key))
        state = ps_cache.grid_state(cache_root, key, len(settings.pairs()))
        info: dict[str, Any] = {"grid_key": key, "grid_key_hash": SEL.key_hash(key)}
        loaded = ps_cache.load_grid(cache_root, key, d.key) if state.status == "complete" else None
        if loaded is None:
            info["status"] = f"partial, {state.done} of {state.total}" if state.done else "not run"
            datasets[d.key] = info
            continue
        grid, links, na = loaded
        constraints = constraints_for(constraints_store, d.key, default_constraints)
        label = SEL.constraints_label(constraints, default_constraints, tx=en)
        choice = SEL.choose(grid, na, constraints)
        default_choice = SEL.choose(grid, na, default_constraints)
        tables["pairs.csv"] += _pair_rows(d.key, grid, na, choice)
        tables["admissible_partitions.csv"] += _admissible_rows(d.key, grid)
        tables["neighbour_links.csv"] += _link_rows(d.key, grid, links)
        tables["selected_partitions.csv"] += _selected_rows(d.key, grid, names)
        tables["selection.csv"].append(_selection_row(d.key, choice, label.text, settings_label.text))
        info.update({"status": "complete", "constraints_label": label.text, "constraints_changes": label.changes,
                     "computed_with": {"grid": state.computed_with}, "validation": {}})
        report.append(f"## {d.label}")
        if choice.chosen is None:
            report.append(T.to_markdown(T.no_qualifying_message(choice, label.text, tx=en)))
        else:
            report.append(T.to_markdown(T.explanation(choice, grid.at(*choice.chosen), na[choice.chosen],
                                                      settings_label.text, label.text,
                                                      settings.min_multi_tag_clusters, tx=en)))
        shown = {p for p in (choice.chosen, default_choice.chosen) if p is not None}
        for pair in grid.pairs:  # the chosen pairs, and every pair validated by hand
            vkey = settings.validation_key(d.key, ctx.context(d.key), *pair)
            stored = ps_cache.read_validation(cache_root, vkey)
            entry = f"{pair[0]},{pair[1]}"
            validation = (None if stored is None
                          else {**stored, "summary": V.summary_from_records(grid.at(*pair), stored)})
            if validation is None:
                if pair in shown:
                    info["validation"][entry] = {"status": "not_run"}
                continue
            reps, clusters = _validation_rows(d.key, pair, validation)
            tables["validation_replicates.csv"] += reps
            tables["validation_clusters.csv"] += clusters
            summary = validation["summary"]
            info["validation"][entry] = {"status": "complete", "validation_key": vkey,
                                         "validation_key_hash": SEL.key_hash(vkey),
                                         "g_prime": summary["subsample"]["g"], "s_prime": summary["subsample"]["s"],
                                         "m": summary["subsample"]["m"], "computed_with": validation["computed_with"]}
            if pair in shown:
                report.append(T.to_markdown(T.validation_block(summary, pair, choice.chosen, pair == choice.chosen
                                                               or label.text == "Default constraints", names,
                                                               tx=en)))
        datasets[d.key] = info
    files = {schema.name: csv_bytes(schema, tables[schema.name]) for schema in S.PS_TABLES}
    shared = constraints_for(constraints_store, "", default_constraints)
    report.append("## Methods\n\n" + T.methods_paragraph(en, T.methods_values(settings, shared, tx=en)))
    report_bytes = ("\n\n".join(report) + "\n").encode("utf-8")
    meta = {
        "schema_version": S.SCHEMA_VERSION, "settings_key": settings.settings_key(),
        "settings_key_hash": SEL.key_hash(settings.settings_key()), "exported_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "selection_settings": asdict(settings), "settings_label": settings_label.text,
        "settings_changes": settings_label.changes,
        "grid": {"g_range": list(settings.g_range), "s_range": list(settings.s_range),
                 "gamma_step": settings.gamma_step, "scan_end_rule": SEL.SCAN_RULE, "scan_seeds": scan,
                 "pass_cap": PASS_CAP},
        "seeds": {"main": settings.seed, "null_replicates_stream_1": replicate_seeds(settings.seed,
                                                                                    settings.null_replicates),
                  "noise_stream_2": noise_seeds(settings.seed, settings.noise_seeds, settings.null_replicates),
                  "scan_stream_3": scan, "null_shuffle_stream_4": null, "subsample_stream_5": sub},
        "validation": {"replicates": settings.replicates, "subsamples": settings.subsamples,
                       "trades_per_game": TRADES_PER_GAME, "subsample_fraction": SEL.SUBSAMPLE_FRACTION,
                       "m_rule": "floor(0.8 n); g' = floor(g m / n); s' = max(2, floor(s m / n))"},
        "constraints": {"shared": asdict(constraints_for(constraints_store, "", default_constraints)),
                        "per_dataset": dict((constraints_store or {}).get("datasets") or {}),
                        "defaults": asdict(default_constraints)},
        "method_versions": {"selection": SEL.METHOD_VERSION, "validation": SEL.VALIDATION_METHOD_VERSION},
        "software_versions": software_versions(), "build_json": ctx.build_json, "datasets": datasets,
        "files": {**{name: {"rows": len(tables[name]), "sha256": hashlib.sha256(data).hexdigest()}
                     for name, data in sorted(files.items())},
                  "selection_report.md": {"rows": None, "sha256": hashlib.sha256(report_bytes).hexdigest()}},
        "columns": S.columns_block(S.PS_TABLES),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in sorted(files.items()):
            zf.writestr(name, data)
        zf.writestr("selection_report.md", report_bytes)
        zf.writestr("parameter_selection.json", json.dumps(meta, indent=2, ensure_ascii=False).encode("utf-8"))
    return zip_name(settings, now), buffer.getvalue()
