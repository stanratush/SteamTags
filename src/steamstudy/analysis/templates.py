"""Fixed sentence templates and the causal-word check: the only way report text is produced.

Every sentence of a generated report comes from `SENTENCES` (filled with numbers and names read from
the Build's files) or from `PARAGRAPHS` (fixed text). `render_report` turns the Markdown into HTML and
fails if the text contains any word from `analysis.toml`'s causal-word list.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterable, Mapping
from typing import Any

import markdown

SENTENCES: dict[str, str] = {
    # reports.html (Build summary)
    "summary_build": "Build {build_id} of Snapshot {snapshot_id} (mode: {mode}), config hash {config_hash}.",
    "summary_window": "Observation Window: {first} to {last} (collection date {collection_date}).",
    "summary_pool": "The Candidate Pool holds {pool} apps from {listing_rows} listing rows; {scored} apps have a "
                    "Mean Monthly Players value, {scored_games} of them of app type game.",
    "summary_unscored": "Unscored apps: {no_rows} with no month rows, {only_placeholders} with only Placeholder Rows, "
                        "{none_in_window} with month rows but none in the Observation Window, {not_found} with no "
                        "Steam Charts page.",
    "summary_skipped": "{count} apps were skipped during collection: their Steam Charts page kept "
                       "failing to load or parse (skipped_apps.csv); they have no score.",
    "summary_placeholders": "{count} Placeholder Rows were treated as absent rows (placeholder_rows.csv).",
    "summary_excluded": "{excluded} scored games were excluded; by primary reason: {by_reason}.",
    "summary_dataset": "{label}: {rows} games from an Eligible Pool of {pool}; deepest /top rank of a member: {deepest}.",
    "summary_ties": "{count} games outside a Top 100 share the score of rank 100 (ties.csv).",
    "summary_release_check": "{count} Top-100 games have a Release Month more than {threshold} months from the "
                             "store release date, or an unreadable store date (release_month_check.csv).",
    "summary_parse_errors": "Parse errors: {count}{allowed}.",
    "summary_warning": "Warning: {text}",
    "summary_manual": "{count} Manual Metadata Entries were used (manual_metadata.csv).",
    "summary_overrides": "{count} Exclusion Overrides were applied.",
    # report.html (feature analysis), per dataset
    "ds_intro": "The {label} dataset holds {n} games; its Eligible Pool holds {pool} games, so a share_ratio "
                "cannot exceed {ceiling}.",
    "ds_months": "Months Observed ranges from {min} to {max} (median {median}); {short} games have fewer than "
                 "12 months.",
    "ds_free": "{count} of the {n} games are free to play (is_free).",
    "ds_tag": "{tag} appears in {count} of the {n} games (Eligible Pool: {baseline}).",
    "ds_genre": "The store genre {genre} appears in {count} of the {n} games (Eligible Pool: {baseline}).",
    "ds_pair": "{tag_a} co-occurs with {tag_b} in {count} games (lift {lift}).",
    "ds_flag": "Content Flag {flag}: {count} games.",
    "ds_cluster": "{label} ({size} tags): {members}. Center: {center}{center_score}; top-strength tag: {top}.",
    "ds_cluster_small": "{label} ({size} tags): {members}. No center ({status}).",
    "ds_one_tag": "{count} One-Tag Clusters: {members}.",
    "ds_quality": "Q (γ = {gamma}) {q} vs null {null_mean} ± {null_sd} (excess {excess}, z {z}; null networks "
                  "average {null_edges} edges vs {edges}); {k} multi-tag + {s} one-tag clusters; silhouette "
                  "(Jaccard game-set distance, a descriptive diagnostic) {silhouette}.",
    "ds_disconnected": "{count} clusters are not connected groups of tags; the Leiden mode avoids such clusters.",
    "ds_stability": "Across {k_seeds} other random seeds, agreement with the reported partition (ARI) ranged from "
                    "{ari_min} to 1.00 (mean {ari_mean}), and the number of multi-tag clusters from {k_min} to {k_max}.",
    "ds_least_stable": "Lowest Membership Stability: {tags}.",
    "ds_all_stable": "Every connected tag has Membership Stability 1.00.",
    "ds_sweep": "Between γ = {g_min} and {g_max} the number of multi-tag clusters ranged from {k_min} to {k_max}; "
                "agreement with the γ = {gamma} partition ranged from {ari_min} to {ari_max} (ARI).",
    "ds_removal": "Removal Sensitivity flags {flagged} of {tested} tags ({names}); if removals acted only like "
                  "another seed, at most about {expected} would be flagged (n / (K + 1)); the flag is a screening "
                  "aid.",
    "ds_no_network": "The network at the report's settings has no edges, so no clusters are reported.",
    "ds_state": "Network State {state_id} (quote it with every network number).",
    "methods_disconnected": "The report's runs produced {count} disconnected clusters across the five datasets.",
}

PARAGRAPHS: dict[str, str] = {
    "caveat": (
        "This report describes the five published Top-100 Datasets. Each Top 100 is a ranked selection of the "
        "most-played games, not a random sample, so nothing here generalises to Steam as a whole. Frequencies, "
        "co-occurrences and clusters describe which characteristics recur together; none of them shows what "
        "makes a game popular. The q-values in associations.csv are a descriptive screen: a small q means "
        "co-occurrence unlikely under independence within this dataset, not evidence about Steam in general. "
        "Clusters are labelled C1, C2, … by size and carry no meaning of their own."
    ),
    "methods": (
        "Clusters come from Louvain community detection (NetworkX) by default, with Leiden "
        "(RBConfigurationVertexPartition, the modularity objective) as the alternative, at one seed and one "
        "resolution γ. Edges join tags that share at least the minimum number of games; the edge weight is the "
        "shared-game count, and lift is an optional Clustering Weight. Modularity Q is compared with a null model "
        "that shuffles the game–tag table (curveball trades preserving every game's and every tag's count), "
        "rebuilds the network with the same thresholds and reclusters it the same way. The silhouette uses the "
        "Jaccard distance between tags' game sets and is a descriptive diagnostic over Multi-Tag Clusters, not a "
        "selection criterion. A Cluster Center is the Jaccard medoid of a cluster of three or more tags (ties: "
        "medoid score rounded to 12 decimals, then more games, then the lower tag id), shown beside the member "
        "with the highest intra-cluster strength. Removal Sensitivity removes one tag at a time and reads the "
        "clustering twice, reclustered from scratch and with the partition fixed; its flag (ARI below the lowest "
        "seed ARI) is a screening aid. The clustering is repeated at other random seeds to give the Seed-Noise "
        "Floor and each tag's Membership Stability, and at a fixed grid of γ values (the Resolution Sweep). No "
        "consensus partition was computed: every partition shown comes from a single run."
    ),
    "limitations": (
        "Limitations: tags are a current snapshot, not historical; the Top 100 is a ranked selection, not a "
        "sample; the partition comes from a single clustering run; Steam Charts has coverage gaps, and a gap "
        "means the app was not tracked, not that nobody played. The full list is in "
        "[User Guide chapter 6](../../../../docs/user-guide/06-known-limitations.md)."
    ),
    "summary_intro": (
        "Summary of this Build's reports. Every number below is read from the files in reports/ and datasets/."
    ),
    "attribution": "Player data: Steam Charts; tags/metadata: Steam store.",
    "test_mode": "This is a test Build (test Snapshot): never publish it.",
    "parse_errors_allowed": "This Build was made with --allow-parse-errors: never publish it.",
    "monthly_players": "monthly_players.csv is not published until the Steam Charts operator agrees.",
}


class CausalLanguageError(ValueError):
    """The rendered text contains a configured causal word."""


def sentence(name: str, **values: Any) -> str:
    return SENTENCES[name].format(**{k: fmt(v) for k, v in values.items()})


def paragraph(name: str) -> str:
    return PARAGRAPHS[name]


def fmt(value: Any) -> str:
    """Numbers as report text: floats to 2 decimals (3 when small), n/a for missing values."""
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.3f}" if 0 < abs(value) < 0.01 else f"{value:.2f}"
    return str(value)


def causal_patterns(words: Iterable[str]) -> list[tuple[str, re.Pattern[str]]]:
    out = []
    for word in words:
        parts = [p.strip() for p in word.split("...")]
        if len(parts) == 2 and all(parts):  # "makes ... successful": both words within one sentence
            pattern = rf"\b{re.escape(parts[0])}\b[^.!?]*\b{re.escape(parts[1])}\b"
        else:
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in word.split()) + r"\b"
        out.append((word, re.compile(pattern, re.IGNORECASE)))
    return out


def causal_hits(text: str, words: Iterable[str]) -> list[str]:
    return [word for word, pattern in causal_patterns(words) if pattern.search(text)]


def check_causal(text: str, words: Iterable[str]) -> None:
    hits = causal_hits(text, words)
    if hits:
        raise CausalLanguageError(f"report contains causal language: {', '.join(hits)}")


def render_report(title: str, blocks: Iterable[str], causal_words: Iterable[str],
                  banners: Mapping[str, str] | None = None) -> str:
    """Markdown blocks -> a standalone HTML page; raises CausalLanguageError on a causal word."""
    words = list(causal_words)
    body_md = "\n\n".join(blocks)
    body = markdown.markdown(body_md, extensions=["tables"])
    text_only = html.unescape(re.sub(r"<[^>]+>", " ", body))
    check_causal(text_only + " " + title, words)
    banner_html = "".join(f'<p class="banner">{html.escape(text)}</p>' for text in (banners or {}).values())
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head><body>"
        f"<h1>{html.escape(title)}</h1>{banner_html}{body}</body></html>\n"
    )


_CSS = (
    "body{font-family:system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;line-height:1.5;"
    "color:#1d1d1f;background:#fff}h1,h2,h3{line-height:1.2}table{border-collapse:collapse}"
    "td,th{border:1px solid #ccc;padding:.2rem .5rem}.banner{background:#fff3cd;border:1px solid #e0c36b;"
    "padding:.5rem 1rem}"
)
