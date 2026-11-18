"""Export CSV: one record-only zip per Comparison State, from the pair memo (`cc_view.PAIRS`), whole.

Every pair of the included datasets, whatever the mode shows (the chosen pair, ⇄, the minimum, the chosen match are
view choices), as six tables and `comparison.json`. A is always the earlier dataset in the Build's order. Dash-free;
the same inputs give byte-identical tables. There is no "Open comparison": each dataset is rebuilt from its
`state_id` or from its run's settings key and Threshold Pair.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from typing import Any

from steamstudy.app.cc_view import ComparisonResult, Resolved
from steamstudy.app.loader import BuildContext
from steamstudy.app.ps_export import tag_names
from steamstudy.export import schema as S
from steamstudy.export.writer import csv_bytes
from steamstudy.i18n import text
from steamstudy.network import comparison as CMP
from steamstudy.network import comparison_text as CT
from steamstudy.network import selection as SEL
from steamstudy.network.cluster import label_order
from steamstudy.versions import software_versions


def zip_name(comparison_id: str, now: dt.datetime) -> str:
    return f"steamstudy_cluster-comparison_{comparison_id}_{now.strftime('%Y%m%dT%H%M%SZ')}.zip"


def _names(ids: Any, names: Mapping[int, str]) -> list[str]:
    return [names.get(t, str(t)) for t in ids]


def _dataset_row(r: Resolved) -> dict[str, Any]:
    v, p = r.values, r.partition
    return {"dataset": v.dataset, "source": v.source, "g": v.g, "s": v.s, "resolution": v.resolution,
            "seed": v.seed, "selection_key": SEL.key_hash(v.selection_key) if v.selection_key else None,
            "state_id": r.state_id, "n_games": len(p.games), "n_tags": len(p.nodes),
            "n_multi_tag_clusters": len(p.multi), "n_one_tag_clusters": len(p.clusters) - len(p.multi),
            "hidden_tag_ids": sorted(p.hidden), "seed_noise_floor": r.seed_noise_floor,
            "neighbour_agreement": r.neighbour_agreement}


def _cluster_rows(p: CMP.Partition, names: Mapping[int, str]) -> list[dict[str, Any]]:
    rows = []
    for c in sorted(p.clusters, key=lambda c: label_order(c.label)):
        ids = sorted(c.members)
        rows.append({"dataset": p.dataset, "cluster": c.label, "n_tags": c.size, "tag_ids": ids,
                     "tags": _names(ids, names)})
    return rows


def _pair_row(pair: CMP.PairResult) -> dict[str, Any]:
    return {"dataset_a": pair.dataset_a, "dataset_b": pair.dataset_b, "n_comparable_tags": pair.n_comparable,
            "comparable_share_a": pair.comparable_share_a, "comparable_share_b": pair.comparable_share_b,
            "ari_comparable": pair.ari, "n_games_in_common": pair.n_games_in_common, "n_matches": pair.n_matches}


def _match_row(pair: CMP.PairResult, m: CMP.Match, names: Mapping[int, str]) -> dict[str, Any]:
    only_a, only_b = [p.tag_id for p in m.only_a], [p.tag_id for p in m.only_b]
    g = m.games
    return {
        "dataset_a": pair.dataset_a, "cluster_a": m.cluster_a, "dataset_b": pair.dataset_b, "cluster_b": m.cluster_b,
        "n_tags_a": m.n_tags_a, "n_tags_b": m.n_tags_b, "n_shared": m.n_shared, "jaccard": m.jaccard,
        "share_a": m.share_a, "share_b": m.share_b, "comparable_jaccard": m.comparable_jaccard,
        "n_comparable_a": m.n_comparable_a, "n_comparable_b": m.n_comparable_b,
        "overlap_vs_expected": m.overlap_vs_expected, "expected_overlap": m.expected_overlap,
        "shared_tag_ids": list(m.shared_tags), "shared_tags": _names(m.shared_tags, names),
        "only_a_tag_ids": only_a, "only_a_tags": _names(only_a, names),
        "only_b_tag_ids": only_b, "only_b_tags": _names(only_b, names),
        **{f"only_a_{k}": n for k, n in m.group_counts_a.items()},
        **{f"only_b_{k}": n for k, n in m.group_counts_b.items()},
        "n_games_both_clusters": len(g.rows), "n_games_only_a": g.n_only_a, "n_games_only_b": g.n_only_b,
        "n_games_neither": g.n_neither,
    }


def _flag_rows(pair: CMP.PairResult) -> list[dict[str, Any]]:
    rows = []
    for dataset, flags in ((pair.dataset_a, pair.flags_a), (pair.dataset_b, pair.flags_b)):
        for f in flags:
            rows.append({"dataset_a": pair.dataset_a, "dataset_b": pair.dataset_b, "dataset": dataset,
                         "cluster": f.cluster, "n_tags": f.n_tags, "n_matches": f.n_matches,
                         "best_jaccard": f.best_jaccard, "flag": f.flag or None,
                         "n_in_one_tag_clusters": f.n_in_one_tag_clusters, "n_not_in_network": f.n_not_in_network})
    return rows


def _game_rows(pair: CMP.PairResult, m: CMP.Match, names: Mapping[int, str]) -> list[dict[str, Any]]:
    return [{"dataset_a": pair.dataset_a, "cluster_a": m.cluster_a, "dataset_b": pair.dataset_b,
             "cluster_b": m.cluster_b, "appid": r.appid, "name": r.name, "rank_a": r.rank_a, "rank_b": r.rank_b,
             "matched_a": len(r.matched_a), "matched_b": len(r.matched_b), "tag_ids": list(r.tags),
             "tags": _names(r.tags, names), "shared_tag_ids": list(r.shared)} for r in m.games.rows]


def tables(ctx: BuildContext, result: ComparisonResult) -> dict[str, list[dict[str, Any]]]:
    """The six tables, keyed by file name, from one resolve of the mode (every pair, whatever is on screen)."""
    names = tag_names(ctx)
    out: dict[str, list[dict[str, Any]]] = {s.name: [] for s in S.CC_TABLES}
    for d in result.included:
        out["datasets.csv"].append(_dataset_row(result.resolved[d]))
        out["clusters.csv"] += _cluster_rows(result.resolved[d].partition, names)
    for pair in result.pairs.values():  # the Build's order, the earlier dataset as A (`compare_all`)
        out["pairs.csv"].append(_pair_row(pair))
        out["cluster_flags.csv"] += _flag_rows(pair)
        for m in pair.matches:
            out["matches.csv"].append(_match_row(pair, m, names))
            out["match_games.csv"] += _game_rows(pair, m, names)
    return out


def _provenance(r: Resolved) -> dict[str, Any]:
    """How to rebuild one dataset: its run's settings key and Threshold Pair on a cell, its `state_id` otherwise."""
    v = r.values
    out: dict[str, Any] = {"source": v.source, "g": v.g, "s": v.s, "resolution": v.resolution}
    if v.on_cell:
        out.update({"selection_key": v.selection_key, "selection_key_hash": SEL.key_hash(v.selection_key or {}),
                    "threshold_pair": [v.g, v.s]})
    else:
        out.update({"state_id": r.state_id, "seed": v.seed})
    if r.fallback:
        out["fallback"] = r.fallback
    return out


def export_comparison(ctx: BuildContext, shared: CMP.SharedSettings, result: ComparisonResult, minimum: float, *,
                      now: dt.datetime | None = None) -> tuple[str, bytes]:
    """The zip's name and bytes. `minimum` is the Minimum Match Jaccard on screen, recorded for information only."""
    if result.comparison_id is None:
        raise ValueError("a comparison needs at least two included datasets")
    now = now or dt.datetime.now(dt.UTC)
    en = text("en")  # the export is English in every Interface Language (ADR 0003)
    kind = S.build_kind(ctx.build_json)
    rows = tables(ctx, result)
    if kind == "import":  # the Import Build's files (`import_variant`): appid -> id
        rows = {name: [_import_row(r) for r in table] for name, table in rows.items()}
    schemas = [S.REGISTRY.variant(s, kind) or s for s in S.CC_TABLES]
    files = {schema.name: csv_bytes(schema, rows[schema.name]) for schema in schemas}
    key = CMP.comparison_key(ctx.build_id, shared, [result.resolved[d].values for d in result.included])
    meta = {
        "schema_version": S.SCHEMA_VERSION, "comparison_id": result.comparison_id, "comparison_key": key,
        "exported_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "minimum_match_jaccard_on_screen": minimum,
        "caution": CT.caution(en), "software_versions": software_versions(), "build_json": ctx.build_json,
        "datasets": {d: _provenance(result.resolved[d]) for d in result.included},
        "files": {name: {"rows": len(rows[name]), "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(files.items())},
        "columns": S.columns_block(schemas, kind=kind),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in sorted(files.items()):
            zf.writestr(name, data)
        zf.writestr("comparison.json", json.dumps(meta, indent=2, ensure_ascii=False).encode("utf-8"))
    return zip_name(result.comparison_id, now), buffer.getvalue()


def _import_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {S.IMPORT_RENAMED.get(k, k): v for k, v in row.items() if k not in S.IMPORT_DROPPED}
