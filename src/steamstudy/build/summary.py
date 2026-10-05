"""`reports/reports.html`: the Build's report summary, rendered only from fixed templates."""

from __future__ import annotations

from typing import Any

from steamstudy.analysis.templates import paragraph, render_report, sentence
from steamstudy.config import Config


def reports_html(result: Any, config: Config) -> str:
    bj = result.build_json
    counts = {r["item"]: r["value"] for r in result.rows("reports/completeness.csv") if not r["dataset"]}
    primary = {r["item"]: r["value"] for r in result.rows("reports/completeness.csv")
               if r["section"] == "exclusions_primary" and r["item"] != "excluded_games"}
    depth = {(r["dataset"], r["item"]): r["value"] for r in result.rows("reports/completeness.csv")
             if r["section"] == "depth_check"}
    window = bj["observation_window"] or {}
    blocks = [paragraph("summary_intro"), "## Build",
              sentence("summary_build", build_id=bj["build_id"], snapshot_id=bj["snapshot_id"], mode=bj["mode"],
                       config_hash=bj["build_config_hash"][:12]),
              sentence("summary_window", first=window.get("first"), last=window.get("last"),
                       collection_date=bj["collection_date"]),
              sentence("summary_parse_errors", count=bj["parse_error_count"],
                       allowed=" (allowed with --allow-parse-errors)" if bj["parse_errors_allowed"] else ""),
              "## Candidate Pool and scoring",
              sentence("summary_pool", pool=counts.get("candidate_pool"), listing_rows=counts.get("listing_rows"),
                       scored=counts.get("scored_apps"), scored_games=counts.get("scored_game_apps")),
              sentence("summary_unscored", no_rows=counts.get("unscored_no_month_rows"),
                       only_placeholders=counts.get("unscored_only_placeholder_rows"),
                       none_in_window=counts.get("unscored_no_month_in_window"),
                       not_found=counts.get("unscored_not_found")),
              sentence("summary_placeholders", count=counts.get("placeholder_rows")),
              sentence("summary_skipped", count=counts.get("unscored_skipped", 0)),
              "## Exclusions",
              sentence("summary_excluded", excluded=counts.get("excluded_games", sum(primary.values())),
                       by_reason=", ".join(f"{k} {v}" for k, v in primary.items() if v) or "none"),
              sentence("summary_manual", count=len(bj.get("manual_metadata_entries", []))),
              sentence("summary_overrides", count=len(bj.get("exclusion_overrides_applied", []))),
              "## Datasets"]
    for d in config.datasets:
        size = bj["dataset_sizes"][d.key]
        blocks.append("- " + sentence("summary_dataset", label=d.label, rows=size["rows"], pool=size["eligible_pool"],
                                      deepest=depth.get((d.key, "deepest_top_listing_rank"))))
    blocks += [sentence("summary_ties", count=len(result.rows("reports/ties.csv"))),
               sentence("summary_release_check", count=len(result.rows("reports/release_month_check.csv")),
                        threshold=config.analysis.release_month_check)]
    if result.warnings:
        blocks.append("## Warnings")
        blocks += ["- " + sentence("summary_warning", text=w) for w in result.warnings]
    blocks += [paragraph("monthly_players"), paragraph("attribution")]
    return render_report("Build report summary", blocks, config.analysis.causal_words, banners=build_banners(bj))


def build_banners(build_json: dict[str, Any]) -> dict[str, str]:
    banners = {}
    if build_json.get("mode") == "test":
        banners["test"] = paragraph("test_mode")
    if build_json.get("parse_errors_allowed"):
        banners["parse_errors"] = paragraph("parse_errors_allowed")
    return banners
