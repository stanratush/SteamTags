"""Where each exported column is explained, shown and reported: the schema's `guide_entry`, `app_panel` and
`report_section`, filled in by `steamstudy.export.schema.declare`.

`guide_entry` is a heading anchor in User Guide chapter 3 (docs/user-guide/03-metric-reference.md).
"""

from __future__ import annotations

GUIDE_CHAPTER = "03-metric-reference.md"

IDENTIFIERS = "identifiers-names-and-lists"

# Column -> chapter-3 anchor, whatever the file.
ENTRY_BY_COLUMN: dict[str, str] = {
    **{c: IDENTIFIERS for c in (
        "appid", "name", "tag_id", "tag", "tag_ids", "tags", "genre_ids", "genres", "dataset", "state_id",
        "member_tag_ids", "members", "source_tag_id", "source_tag", "target_tag_id", "target_tag", "tag_id_a",
        "tag_a", "tag_id_b", "tag_b", "genre_id", "genre", "top_strength_tag_id")},
    "avg_players": "monthly-avg-players", "peak_players": "monthly-avg-players",
    "mean_monthly_players": "mean-monthly-players", "months_observed": "months-observed",
    "rank": "rank-and-ties", "release_month": "release-month-and-store-release-date",
    "store_release_date": "release-month-and-store-release-date", "months_apart": "release-month-gap",
    "is_free": "store-metadata", "app_type": "store-metadata", "metadata_source": "store-metadata",
    "content_flags": "store-metadata", "top_listing_rank": "listing-rank-and-the-depth-check",
    "section": "completeness-counts", "item": "completeness-counts", "note": "completeness-counts",
    "reason": "exclusions-and-would-be-ranks", "detail": "exclusions-and-would-be-ranks",
    "primary_reason": "exclusions-and-would-be-ranks",
    **{f"would_be_rank_{k}": "exclusions-and-would-be-ranks"
       for k in ("overall", "puzzle", "rpg", "strategy", "simulation")},
    "rule": "impact-report", "signal": "impact-report", "is_primary_reason": "impact-report",
    "rank_limit": "impact-report", "excluded": "impact-report", "adult_only_notice": "impact-report",
    "content_descriptor_3": "impact-report", "hentai_tag": "impact-report",
    **{c: "build-diagnostics" for c in (
        "source", "request_key", "error", "id", "app_count", "in_vocabulary", "entry_kind", "field", "source_url",
        "retrieved", "steamdb_batch", "store_tag_ids", "steamdb_tag_ids", "steamdb_tags", "only_store_tag_ids",
        "only_steamdb_tag_ids", "same_tag_set", "url", "last_status", "timestamp")},
    # feature analysis
    "count": "tag-count-and-share", "share": "tag-count-and-share", "median_position": "median-tag-position",
    "defining_tag": "defining-tag", "baseline_count": "eligible-pool-baseline",
    "baseline_share": "eligible-pool-baseline", "share_ratio": "share-ratio",
    "archived_category": "archived-tag-category", "support_count": "combination-support",
    "support_share": "combination-support", "confidence_a_to_b": "confidence", "confidence_b_to_a": "confidence",
    "count_a": "pair-counts", "count_b": "pair-counts", "count_ab": "pair-counts", "phi": "phi-coefficient",
    "jaccard": "jaccard-index", "fisher_p": "fisher-exact-p", "bh_q": "benjamini-hochberg-q",
    "flag": "content-flag-counts",
    # network
    "shared_games": "edge-weight-shared-games", "appids": "edge-weight-shared-games",
    "is_intra_cluster": "edge-weight-shared-games", "source_cluster": "edge-weight-shared-games",
    "target_cluster": "edge-weight-shared-games", "n_games": "tag-game-count",
    "degree": "degree-and-isolated-tags", "degree_intra": "degree-and-isolated-tags",
    "is_isolated": "degree-and-isolated-tags",
    **{c: "strength-weighted-degree" for c in (
        "strength_shared", "strength_lift", "strength_shared_intra", "strength_lift_intra")},
    "medoid_score": "medoid-score", "is_center": "cluster-center", "center_tag_id": "cluster-center",
    "center": "cluster-center", "center_medoid_score": "cluster-center", "center_status": "cluster-center",
    "top_strength_tag": "top-strength-tag", "center_is_top_strength": "top-strength-tag",
    "within_z": "within-cluster-strength-z-score", "participation": "participation-coefficient",
    **{c: "layout-positions" for c in ("x_global", "y_global", "x_cluster_separated", "y_cluster_separated")},
    "reasons": "tags-not-in-the-network",
    # clusters and partition quality
    "cluster": "cluster-labels-and-counts", "n_multi_tag_clusters": "cluster-labels-and-counts",
    "n_one_tag_clusters": "cluster-labels-and-counts",
    "n_dataset_games": "network-size", "n_nodes": "network-size", "n_edges": "network-size",
    "total_weight": "network-size", "modularity": "modularity-q", "modularity_status": "modularity-q",
    "q_null_mean": "null-model-baseline", "q_null_sd": "null-model-baseline",
    "null_n_edges_mean": "null-model-baseline", "replicate": "null-model-baseline",
    "q_excess": "excess-modularity-and-z-score", "modularity_z": "excess-modularity-and-z-score",
    "coverage": "coverage-and-inter-cluster-weight-share",
    "inter_cluster_weight_share": "coverage-and-inter-cluster-weight-share",
    "connected": "disconnected-clusters", "n_disconnected_clusters": "disconnected-clusters",
    "mean_silhouette": "mean-silhouette", "internal_edges": "internal-edges-weight-and-densities",
    "internal_weight": "internal-edges-weight-and-densities", "edge_density": "internal-edges-weight-and-densities",
    "weighted_density": "internal-edges-weight-and-densities", "cut_weight": "cut-weight-and-conductance",
    "conductance": "cut-weight-and-conductance", "conductance_status": "cut-weight-and-conductance",
    "cluster_a": "cluster-connections", "cluster_b": "cluster-connections", "edge_count": "cluster-connections",
    "weight": "cluster-connections", "shared_weight": "cluster-connections",
    "ratio": "connection-ratio", "shared_ratio": "connection-ratio",
    "share_of_a": "connection-share", "share_of_b": "connection-share",
    "matched": "games-within-a-cluster", "cluster_size": "games-within-a-cluster",
    "network_tags": "games-within-a-cluster", "share_of_game": "games-within-a-cluster",
    "matched_tag_ids": "games-within-a-cluster", "matched_tags": "games-within-a-cluster",
    # stability
    "seed_ari_min": "adjusted-rand-index", "seed_ari_mean": "adjusted-rand-index", "ari_vs_main": "adjusted-rand-index",
    "noise_seed_index": "adjusted-rand-index",
    "seed_modularity_sd": "seed-spread-of-modularity-and-silhouette",
    "seed_silhouette_sd": "seed-spread-of-modularity-and-silhouette",
    "seed_silhouette_status": "seed-spread-of-modularity-and-silhouette",
    "seed_k_min": "seed-range-of-cluster-counts", "seed_k_max": "seed-range-of-cluster-counts",
    "membership_stability": "membership-stability", "mean_membership_stability": "membership-stability",
    "resolution": "resolution-sweep", "ari_vs_report": "resolution-sweep",
    # Removal Sensitivity
    "run_order": "run-order-and-identity", "active_strength": "run-order-and-identity",
    "rc_delta_modularity": "reclustered-change-in-modularity",
    "rc_silhouette_after": "reclustered-silhouette", "rc_silhouette_after_status": "reclustered-silhouette",
    "rc_delta_silhouette": "reclustered-silhouette", "rc_delta_k": "reclustered-change-in-cluster-counts",
    "rc_delta_s": "reclustered-change-in-cluster-counts", "rc_ari": "reclustered-ari",
    "rc_centers_lost_tag_ids": "centers-lost", "rc_centers_lost": "centers-lost",
    "rc_ari_beyond_noise": "beyond-noise-flag", "fp_delta_modularity": "fixed-partition-change-in-modularity",
    "fp_silhouette_after": "fixed-partition-silhouette", "fp_silhouette_after_status": "fixed-partition-silhouette",
    "fp_delta_silhouette": "fixed-partition-silhouette",
}

# (file name, column) -> anchor, where one column name means different things in different files.
ENTRY_BY_FILE: dict[tuple[str, str], str] = {
    ("combinations.csv", "lift"): "combination-lift",
    ("associations.csv", "lift"): "pair-lift",
    ("edges.csv", "lift"): "edge-lift",
    ("tag_vocabulary.csv", "kind"): "build-diagnostics",
    ("clusters.csv", "kind"): "cluster-labels-and-counts",
    ("genre_frequency.csv", "kind"): "genre-frequency",
    ("clusters.csv", "size"): "cluster-labels-and-counts",
    ("combinations.csv", "size"): "combination-support",
    ("placeholder_rows.csv", "position"): "placeholder-rows",
    ("placeholder_rows.csv", "month"): "placeholder-rows",
    ("ties.csv", "position"): "rank-and-ties",
    ("impact_near_misses.csv", "position"): "impact-report",
    ("monthly_players.csv", "month"): "monthly-avg-players",
    ("completeness.csv", "value"): "completeness-counts",
    ("manual_metadata.csv", "value"): "build-diagnostics",
    ("impact_unexcluded.csv", "rank"): "impact-report",
    ("content_flags.csv", "rank"): "content-flag-counts",
    ("null_model.csv", "modularity"): "null-model-baseline",
    ("null_model.csv", "n_edges"): "null-model-baseline",
    ("null_model.csv", "seed"): "null-model-baseline",
    ("seed_noise.csv", "modularity"): "seed-spread-of-modularity-and-silhouette",
    ("seed_noise.csv", "silhouette"): "seed-spread-of-modularity-and-silhouette",
    ("seed_noise.csv", "silhouette_status"): "seed-spread-of-modularity-and-silhouette",
    ("seed_noise.csv", "seed"): "adjusted-rand-index",
    ("seed_noise.csv", "n_multi_tag_clusters"): "seed-range-of-cluster-counts",
    ("seed_noise.csv", "n_one_tag_clusters"): "seed-range-of-cluster-counts",
    ("resolution_sweep.csv", "modularity"): "resolution-sweep",
    ("resolution_sweep.csv", "mean_silhouette"): "resolution-sweep",
    ("resolution_sweep.csv", "silhouette_status"): "resolution-sweep",
    ("resolution_sweep.csv", "n_multi_tag_clusters"): "resolution-sweep",
    ("resolution_sweep.csv", "n_one_tag_clusters"): "resolution-sweep",
    ("resolution_sweep.csv", "seed_ari_min"): "resolution-sweep",
    ("resolution_sweep.csv", "seed_ari_mean"): "resolution-sweep",
    ("nodes.csv", "silhouette"): "per-tag-silhouette",
    ("nodes.csv", "silhouette_status"): "per-tag-silhouette",
    ("clusters.csv", "silhouette_status"): "mean-silhouette",
    ("cluster_quality.csv", "silhouette_status"): "mean-silhouette",
    ("removal_sensitivity.csv", "silhouette_status"): "reclustered-silhouette",
    ("release_month_check.csv", "release_month"): "release-month-gap",
    ("release_month_check.csv", "store_release_date"): "release-month-gap",
    ("ties.csv", "mean_monthly_players"): "rank-and-ties",
    ("ties.csv", "months_observed"): "rank-and-ties",
}

APP_PANEL_BY_FILE: dict[str, str] = {
    "nodes.csv": "Nodes table; node inspector",
    "edges.csv": "Edges table; edge inspector",
    "clusters.csv": "Clusters table; cluster inspector",
    "cluster_quality.csv": "Cluster-quality row; Cluster quality tab",
    "cluster_connections.csv": "Cluster quality tab",
    "cluster_games.csv": "cluster inspector (Games)",
    "null_model.csv": "Cluster quality tab (replicates)",
    "seed_noise.csv": "Cluster quality tab (replicates)",
    "not_in_network.csv": "Not in network tab (Analysis Report section 2)",
    "removal_sensitivity.csv": "Removal sensitivity tab",
    "top100_<dataset>.csv": "loaded dataset (edge inspector lists its games)",
}
APP_PANEL_BUILD_ONLY = "none (Build only)"

REPORT_BY_FILE: dict[str, str] = {
    "tag_frequency.csv": "report.html: Frequencies",
    "genre_frequency.csv": "report.html: Frequencies",
    "combinations.csv": "report.html: Frequencies",
    "content_flags.csv": "report.html: Frequencies",
    "clusters.csv": "report.html: Clusters",
    "cluster_quality.csv": "report.html: Clusters and Stability",
    "removal_sensitivity.csv": "report.html: Stability",
    "resolution_sweep.csv": "report.html: Stability",
    "completeness.csv": "reports.html",
    "exclusions.csv": "reports.html",
    "ties.csv": "reports.html",
    "release_month_check.csv": "reports.html",
    "skipped_apps.csv": "reports.html",
}
REPORT_BY_COLUMN: dict[tuple[str, str], str] = {
    ("top100_<dataset>.csv", "months_observed"): "report.html: dataset introduction",
    ("top100_<dataset>.csv", "is_free"): "report.html: dataset introduction",
    ("nodes.csv", "membership_stability"): "report.html: Stability",
}
REPORT_NONE = "none"


def _base(file_name: str) -> str:
    """App file name behind a stacked Build file (network_nodes.csv -> nodes.csv)."""
    return file_name[len("network_"):] if file_name.startswith("network_") else file_name


def guide_entry(file_name: str, column: str) -> str:
    base = _base(file_name)
    return ENTRY_BY_FILE.get((base, column)) or ENTRY_BY_COLUMN[column]


def app_panel(file_name: str, group: str) -> str:
    if group in ("app_export", "analysis") and _base(file_name) in APP_PANEL_BY_FILE:
        return APP_PANEL_BY_FILE[_base(file_name)]
    return APP_PANEL_BY_FILE.get(file_name, APP_PANEL_BUILD_ONLY)


def report_section(file_name: str, column: str) -> str:
    base = _base(file_name)
    return REPORT_BY_COLUMN.get((base, column)) or REPORT_BY_FILE.get(base, REPORT_NONE)
