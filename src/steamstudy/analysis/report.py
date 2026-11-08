"""`analysis/report.html`: the feature-analysis report, one section per dataset.

Built only from fixed templates; every number is read from the Build's analysis rows (the same rows
written to the CSVs) or from `analysis.json`.
"""

from __future__ import annotations

import statistics
from typing import Any

from steamstudy.analysis.templates import fmt, paragraph, render_report, sentence, wording
from steamstudy.build.summary import build_banners
from steamstudy.config import Config
from steamstudy.export.schema import build_kind

TOP_TAGS, TOP_GENRES, TOP_PAIRS = 5, 3, 3


def _pct(share: float | None) -> str:
    return "n/a" if share is None else f"{share * 100:.0f}%"


def _of(rows: list[dict[str, Any]], dataset: str) -> list[dict[str, Any]]:
    return [r for r in rows if r["dataset"] == dataset]


def report_html(result: Any, config: Config) -> str:
    a = result.analysis_json
    w = wording(config)
    blocks = [paragraph("caveat", **w)]
    for d in config.datasets:
        blocks += _dataset_section(result, config, d.key, d.label, a["datasets"][d.key])
    disconnected = sum(info["n_disconnected_clusters"] for info in a["datasets"].values())
    steam = build_kind(result.build_json) == "steam"
    blocks += ["## Methods", paragraph("methods"), sentence("methods_disconnected", count=disconnected, number=w["number"]),
               "## Limitations",
               paragraph("limitations", **w) if steam else paragraph("limitations_import", **w),
               paragraph("attribution") if steam else paragraph("attribution_import",
                                                                import_id=result.build_json["import_id"])]
    return render_report(f"Feature analysis of the {w['top_h']} Datasets", blocks, config.analysis.causal_words,
                         banners=build_banners(result.build_json))


def _dataset_section(result: Any, config: Config, key: str, label: str, info: dict[str, Any]) -> list[str]:
    top = result.dataset_rows[key]
    steam = build_kind(result.build_json) == "steam"
    n = len(top)
    blocks = [f"## {label}", sentence("ds_state", state_id=info["state_id"])]
    if n == 0:
        return blocks
    pool = info["eligible_pool"]
    blocks.append(sentence("ds_intro", label=label, n=n, pool=pool, ceiling=pool / n))
    if steam:  # Months Observed and is_free are Steam facts
        months = [r["months_observed"] for r in top]
        blocks += [sentence("ds_months", min=min(months), max=max(months), median=statistics.median(months),
                            short=sum(m < 12 for m in months)),
                   sentence("ds_free", count=sum(bool(r["is_free"]) for r in top), n=n)]
    blocks.append("### Frequencies")
    tags = [r for r in _of(result.rows("analysis/tag_frequency.csv"), key) if not r["defining_tag"]][:TOP_TAGS]
    blocks += ["- " + sentence("ds_tag", tag=r["tag"], count=r["count"], n=n, baseline=_pct(r["baseline_share"]))
               for r in tags]
    genres = [r for r in _of(result.rows("analysis/genre_frequency.csv"), key)
              if r["kind"] == "genre"][:TOP_GENRES] if steam else []
    blocks += ["- " + sentence("ds_genre", genre=r["genre"], count=r["count"], n=n,
                               baseline=_pct(r["baseline_share"])) for r in genres]
    if info.get("genre_note"):
        blocks.append(info["genre_note"])
    pairs = [r for r in _of(result.rows("analysis/combinations.csv"), key) if r["size"] == 2][:TOP_PAIRS]
    blocks += ["- " + sentence("ds_pair", tag_a=r["tags"][0], tag_b=r["tags"][1], count=r["support_count"],
                               lift=r["lift"]) for r in pairs]
    blocks += ["- " + sentence("ds_flag", flag=flag, count=count) for flag, count in info["content_flag_counts"].items()]
    blocks += _network_blocks(result, key, info)
    return blocks


def _network_blocks(result: Any, key: str, info: dict[str, Any]) -> list[str]:
    blocks = ["### Clusters"]
    clusters = _of(result.rows("analysis/network_clusters.csv"), key)
    quality = _of(result.rows("analysis/network_cluster_quality.csv"), key)[0]
    if quality["n_edges"] == 0:
        return [*blocks, sentence("ds_no_network")]
    singles = []
    for c in clusters:
        if c["kind"] == "one_tag":
            singles.append(c["members"][0])
        elif c["center"] is not None:
            blocks.append("- " + sentence(
                "ds_cluster", label=c["cluster"], size=c["size"], members=", ".join(c["members"]), center=c["center"],
                center_score=f" (medoid score {fmt(c['center_medoid_score'])})",
                top=c["top_strength_tag"] + (" (the same tag)" if c["center_is_top_strength"] else "")))
        else:
            blocks.append("- " + sentence("ds_cluster_small", label=c["cluster"], size=c["size"],
                                          members=", ".join(c["members"]), status=c["center_status"]))
    if singles:
        blocks.append(sentence("ds_one_tag", count=len(singles), members=", ".join(singles)))
    state_key = info["state_key"]
    blocks.append(sentence(
        "ds_quality", gamma=state_key["resolution"], q=quality["modularity"], null_mean=quality["q_null_mean"],
        null_sd=quality["q_null_sd"], excess=quality["q_excess"], z=quality["modularity_z"],
        null_edges=None if quality["null_n_edges_mean"] is None else round(quality["null_n_edges_mean"]),
        edges=quality["n_edges"], k=quality["n_multi_tag_clusters"], s=quality["n_one_tag_clusters"],
        silhouette=quality["mean_silhouette"]))
    if quality["n_disconnected_clusters"]:
        blocks.append(sentence("ds_disconnected", count=quality["n_disconnected_clusters"]))

    blocks.append("### Stability")
    blocks.append(sentence("ds_stability", k_seeds=state_key["noise_seeds"], ari_min=quality["seed_ari_min"],
                           ari_mean=quality["seed_ari_mean"], k_min=quality["seed_k_min"], k_max=quality["seed_k_max"]))
    nodes = [r for r in _of(result.rows("analysis/network_nodes.csv"), key) if r["membership_stability"] is not None]
    below = sorted((r for r in nodes if r["membership_stability"] < 1.0),
                   key=lambda r: (r["membership_stability"], r["tag_id"]))
    if below:
        shown = below[:5]
        blocks.append(sentence("ds_least_stable", tags=", ".join(f"{r['tag']} {fmt(r['membership_stability'])}"
                                                                 for r in shown)))
    else:
        blocks.append(sentence("ds_all_stable"))
    ranges = info["resolution_sweep"]
    blocks.append(sentence("ds_sweep", g_min=ranges["gamma_min"], g_max=ranges["gamma_max"], k_min=ranges["k_min"],
                           k_max=ranges["k_max"], gamma=state_key["resolution"], ari_min=ranges["ari_min"],
                           ari_max=ranges["ari_max"]))
    rs = _of(result.rows("analysis/removal_sensitivity.csv"), key)
    flagged = [r["tag"] for r in rs if r["rc_ari_beyond_noise"]]
    blocks.append(sentence("ds_removal", flagged=len(flagged), tested=len(rs), names=", ".join(flagged) or "none",
                           expected=f'{info["removal_sensitivity"]["expected_by_chance_at_most"]:.1f}'))
    return blocks
