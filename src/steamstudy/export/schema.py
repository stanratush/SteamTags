"""The single declaration of every exported file and column.

Every CSV the package writes is declared here with its columns, types and one-line descriptions, and
every writer validates against these declarations (`steamstudy.export.writer`). `export.json` and
`analysis.json` embed a `columns` block generated from here.

Adding, removing or renaming a column bumps `SCHEMA_VERSION` (separate from the Network State
`key_version`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# 1 + the one shared bump for the ticket 25, 27 and 28 overrides (spec); 3 adds the Parameter Selection
# export zip (`parameter_selection` group) and `applied_from` in export.json.
SCHEMA_VERSION = 4

# Column types and how the writer renders them:
#   str        as is
#   int        decimal integer
#   float      shortest round-trip repr, so app and Build values compare exactly
#   float6     exactly 6 decimals (mean_monthly_players, so the rank can be reproduced)
#   bool       true / false
#   str_list   ;-separated strings
#   int_list   ;-separated integers
# None is n/a and is written as an empty cell, whatever the type.
COLUMN_TYPES = ("str", "int", "float", "float6", "bool", "str_list", "int_list")


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    description: str
    guide_entry: str | None = None
    app_panel: str | None = None
    report_section: str | None = None

    def __post_init__(self) -> None:
        if self.type not in COLUMN_TYPES:
            raise ValueError(f"column {self.name}: unknown type {self.type!r}")
        if not self.description.strip():
            raise ValueError(f"column {self.name}: a one-line description is required")


@dataclass(frozen=True)
class FileSchema:
    name: str
    description: str
    columns: tuple[Column, ...]
    group: str = ""  # "build_datasets", "build_reports", "analysis", "app_export", ...

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name}: duplicate column names")

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns)

    def column(self, name: str) -> Column:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(f"{self.name} has no column {name!r}")

    def with_prefix(self, name: str, prefix: tuple[Column, ...], group: str = "") -> FileSchema:
        """The same file with leading columns, e.g. an app table stacked by dataset in the Build."""
        return replace(self, name=name, columns=(*prefix, *self.columns), group=group or self.group)


@dataclass
class Registry:
    files: dict[str, FileSchema] = field(default_factory=dict)

    def declare(self, schema: FileSchema) -> FileSchema:
        key = f"{schema.group}/{schema.name}"
        if key in self.files:
            raise ValueError(f"file {key} declared twice")
        self.files[key] = schema
        return schema

    def __getitem__(self, key: str) -> FileSchema:
        """A file by `<group>/<name>`."""
        return self.files[key]

    def __iter__(self):
        return iter(self.files.values())


REGISTRY = Registry()


def declare(name: str, description: str, columns: list[Column] | tuple[Column, ...], group: str = "") -> FileSchema:
    """Declare a file; each column gets its guide entry, app panel and report section (see guide_index)."""
    return REGISTRY.declare(FileSchema(name, description, tuple(_annotate(name, group, c) for c in columns), group))


def _annotate(file_name: str, group: str, column: Column) -> Column:
    from steamstudy.export import guide_index as G

    return replace(
        column,
        guide_entry=column.guide_entry or G.guide_entry(file_name, column.name),
        app_panel=column.app_panel or G.app_panel(file_name, group),
        report_section=column.report_section or G.report_section(file_name, column.name),
    )


def file(key: str) -> FileSchema:
    """A declared file by `<group>/<name>`, e.g. `app_export/nodes.csv`."""
    return REGISTRY[key]


def columns_block(schemas: list[FileSchema] | tuple[FileSchema, ...]) -> dict[str, dict[str, dict[str, str]]]:
    """The `columns` block embedded in `export.json` / `analysis.json`: file -> column -> type/description."""
    return {
        s.name: {c.name: {"type": c.type, "description": c.description} for c in s.columns} for s in schemas
    }


# ============================================================================= declarations

C = Column
IDENTIFIERS_ENTRY = "identifiers-names-and-lists"

# ----------------------------------------------------------------------------- Build: reports/

PARSE_ERRORS = declare(
    "parse_errors.csv",
    "Every parse error in the Snapshot. Any row fails the Build unless --allow-parse-errors was passed.",
    [
        C("appid", "int", "Steam AppID; empty for a listing page."),
        C("source", "str", "Which response: top_page, steamcharts_app, store_page or appdetails."),
        C("request_key", "str", "The response's path in the Snapshot's raw archive."),
        C("error", "str", "What the parser could not read."),
    ],
    group="build_reports",
)

PLACEHOLDER_ROWS = declare(
    "placeholder_rows.csv",
    "Every Placeholder Row (Avg. Players 0.00 and Peak 0) in the Candidate Pool, treated as an absent row.",
    [
        C("appid", "int", "Steam AppID."),
        C("month", "str", "The row's month, YYYY-MM."),
        C("position", "str", "leading (before the Release Month), interior or trailing (after the last data row)."),
    ],
    group="build_reports",
)

COMPLETENESS = declare(
    "completeness.csv",
    "Counts that show how complete the Candidate Pool and the datasets are, one count per row.",
    [
        C("section", "str", "Group of the count: listing, scoring, exclusions_overlapping, exclusions_primary, depth_check."),
        C("item", "str", "What is counted."),
        C("dataset", "str", "Dataset key for per-dataset counts; empty otherwise."),
        C("value", "int", "The count (or rank, for depth-check ranks)."),
        C("note", "str", "How to read the count."),
    ],
    group="build_reports",
)

DATASET_KEYS = ("overall", "puzzle", "rpg", "strategy", "simulation")


def _would_be_rank_columns() -> list[Column]:
    return [
        C(f"would_be_rank_{key}", "int",
          f"Rank the game takes in the {key} ranking, or would take had it not been excluded; empty when the game "
          f"is outside that dataset's scope (no defining tag, or tags unknown).")
        for key in DATASET_KEYS
    ]


# ----------------------------------------------------------------------------- Build: datasets/

TOP100 = declare(
    "top100_<dataset>.csv",
    "One Top-100 Dataset: the 100 non-excluded games with the highest Mean Monthly Players. The app's loading contract.",
    [
        C("dataset", "str", "Dataset key: overall, puzzle, rpg, strategy or simulation."),
        C("rank", "int", "1-100; by mean_monthly_players desc, then months_observed desc, then appid asc."),
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name from the Steam store (or the Manual Metadata Entry)."),
        C("mean_monthly_players", "float6",
          "Mean Monthly Players: mean of Steam Charts Monthly Avg. Players over post-release months with data in the "
          "Observation Window; 6 decimals, so the rank can be reproduced."),
        C("months_observed", "int", "Post-release months in the Observation Window that have a Monthly Avg. Players value."),
        C("release_month", "str", "First Steam Charts month that is not a Placeholder Row, YYYY-MM."),
        C("store_release_date", "str", "Release date as given by the Steam store; metadata only."),
        C("is_free", "bool", "Steam store is_free flag (Free-to-Play Game)."),
        C("app_type", "str", "Steam app type from appdetails."),
        C("tag_ids", "int_list", "Displayed store tag ids in display order."),
        C("tags", "str_list", "Displayed store tag names, matching tag_ids."),
        C("genre_ids", "int_list", "Store genre ids, in store order."),
        C("genres", "str_list", "Store genre names, matching genre_ids."),
        C("content_flags", "str_list", "Content Flag codes the game carries; never used to filter."),
        C("metadata_source", "str", "store, manual (full Manual Metadata Entry) or manual_tags (tags-only entry)."),
        C("top_listing_rank", "int", "Best rank in the Steam Charts /top listing across passes; empty if not listed."),
    ],
    group="build_datasets",
)

MONTHLY_PLAYERS = declare(
    "monthly_players.csv",
    "The months behind every Top-100 game's score: one row per AppID and month (never a Placeholder Row). "
    "Not published until the Steam Charts operator agrees.",
    [
        C("appid", "int", "Steam AppID."),
        C("month", "str", "Calendar month, YYYY-MM, from the Release Month on, inside the Observation Window."),
        C("avg_players", "float", "Steam Charts Monthly Avg. Players."),
        C("peak_players", "int", "Steam Charts monthly Peak Players."),
    ],
    group="build_datasets",
)

# ----------------------------------------------------------------------------- Build: reports/ (datasets)

TIES = declare(
    "ties.csv",
    "Games outside a Top 100 whose Mean Monthly Players equals that of rank 100.",
    [
        C("dataset", "str", "Dataset key."),
        C("position", "int", "Position after the tie-break (101, 102, ...)."),
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("mean_monthly_players", "float6", "Mean Monthly Players (equal to rank 100's)."),
        C("months_observed", "int", "Months Observed (the first tie-break)."),
    ],
    group="build_reports",
)

TAG_VOCABULARY = declare(
    "tag_vocabulary.csv",
    "Every distinct tag and store genre seen on a scored app, with app counts.",
    [
        C("kind", "str", "tag or genre."),
        C("id", "int", "Tag id or store genre id."),
        C("name", "str", "Tag name or genre description as seen."),
        C("app_count", "int", "Scored apps with store data that show it."),
        C("in_vocabulary", "bool", "Tags: whether the id is in the GetTagList snapshot; empty for genres."),
    ],
    group="build_reports",
)

RELEASE_MONTH_CHECK = declare(
    "release_month_check.csv",
    "Diagnostic only, never a rule: Top-100 games whose Release Month and store release date are more than the "
    "configured number of months apart, or whose store date cannot be read.",
    [
        C("appid", "int", "Steam AppID."),
        C("release_month", "str", "Release Month (Steam Charts), YYYY-MM."),
        C("store_release_date", "str", "Release date as given by the store."),
        C("months_apart", "int",
          "(year*12+month) of the store date minus the same for the Release Month; positive = store date later; "
          "empty when the store date cannot be read."),
    ],
    group="build_reports",
)

EXCLUSIONS = declare(
    "exclusions.csv",
    "One row per excluded game and matched exclusion rule, with the rank the game would have taken in each dataset.",
    [
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name (store, or Steam Charts listing when there is no store data)."),
        C("reason", "str", "Matched rule: store_data_unavailable, app_type, no_tags, adult_content, software_tag, "
                            "dating_sim_tag or manual."),
        C("detail", "str", "What matched (the app type, the tags and positions, the adult-content signals, the manual reason)."),
        C("primary_reason", "str", "The game's first matching rule in evaluation order."),
        C("mean_monthly_players", "float6", "The game's Mean Monthly Players."),
        *_would_be_rank_columns(),
    ],
    group="build_reports",
)

IMPACT_REMOVALS = declare(
    "impact_removals.csv",
    "Removals per rule and per tag or signal: one row per (rule, signal, excluded game).",
    [
        C("rule", "str", "Exclusion rule."),
        C("signal", "str", "The tag, adult-content signal, app type or reason that fired."),
        C("tag_id", "int", "Tag id when the signal is a tag; empty otherwise."),
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("is_primary_reason", "bool", "Whether this rule is the game's primary_reason."),
        *_would_be_rank_columns(),
    ],
    group="build_reports",
)

IMPACT_NEAR_MISSES = declare(
    "impact_near_misses.csv",
    "Exclusion tags present on a scored game but beyond their rank limit, so they did not exclude it.",
    [
        C("rule", "str", "Exclusion rule the tag belongs to."),
        C("tag_id", "int", "Tag id."),
        C("tag", "str", "Tag name."),
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("position", "int", "The tag's position in the displayed list (1 = first)."),
        C("rank_limit", "int", "The rank limit that applies to the tag."),
        C("excluded", "bool", "Whether another rule excluded the game anyway."),
        *_would_be_rank_columns(),
    ],
    group="build_reports",
)

IMPACT_ADULT_SIGNALS = declare(
    "impact_adult_signals.csv",
    "Scored games where the store's Adult Only notice and content descriptor 3 disagree.",
    [
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("adult_only_notice", "bool", "The store page shows the Adult Only notice."),
        C("content_descriptor_3", "bool", "appdetails content_descriptors contains id 3."),
        C("hentai_tag", "bool", "The Hentai tag is within its rank limit."),
        C("excluded", "bool", "Whether the game is excluded (by any rule)."),
        *_would_be_rank_columns(),
    ],
    group="build_reports",
)

IMPACT_UNEXCLUDED = declare(
    "impact_unexcluded.csv",
    "Top-100 games no rule excluded that carry content descriptor 1 or 4, a software store genre or a Content Flag.",
    [
        C("dataset", "str", "Dataset key."),
        C("rank", "int", "Rank in that dataset."),
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("signal", "str", "content_descriptor_1, content_descriptor_4, software_genre:<genre> or content_flag:<code>."),
    ],
    group="build_reports",
)

MANUAL_METADATA = declare(
    "manual_metadata.csv",
    "Every citation of every Manual Metadata Entry: one row per (AppID, field).",
    [
        C("appid", "int", "Steam AppID."),
        C("entry_kind", "str", "full or tags_only."),
        C("field", "str", "The supplied field (name, tags, app_type, genres, is_free, release_date, adult_only)."),
        C("value", "str", "The supplied value as text."),
        C("source_url", "str", "Where the value comes from."),
        C("retrieved", "str", "Retrieval date of the source."),
    ],
    group="build_reports",
)

STEAMDB_CROSSCHECK = declare(
    "steamdb_crosscheck.csv",
    "Store vs SteamDB tags for each Top-100 game with a SteamDB page in the Snapshot. A cross-check only: "
    "SteamDB values never enter a dataset.",
    [
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("steamdb_batch", "str", "The SteamDB batch the page comes from."),
        C("store_tag_ids", "int_list", "Displayed store tag ids, in display order."),
        C("steamdb_tag_ids", "int_list", "Tag ids on the SteamDB page, in page order."),
        C("steamdb_tags", "str_list", "Tag names on the SteamDB page, matching steamdb_tag_ids."),
        C("only_store_tag_ids", "int_list", "Tags on the store list but not on SteamDB."),
        C("only_steamdb_tag_ids", "int_list", "Tags on SteamDB but not on the store list."),
        C("same_tag_set", "bool", "Whether both list the same tags."),
    ],
    group="build_reports",
)

_SKIPPED_COLUMNS = [
    C("appid", "int", "Steam AppID."),
    C("name", "str", "Name in the Steam Charts listing; empty for edge cases added outside the listing."),
    C("url", "str", "The Steam Charts page that could not be collected."),
    C("reason", "str", "Why it was skipped: failed to load after every retry (with the last error), or not parseable."),
    C("last_status", "int", "HTTP status of the last attempt; empty for a timeout or connection failure."),
    C("timestamp", "str", "When the app was skipped (UTC)."),
]

SKIPPED_APPS_SNAPSHOT = declare(
    "skipped_apps.csv",
    "Steam Charts app pages that kept failing to load or parse during collection, so the app was skipped "
    "instead of stopping collection. Written next to snapshot.json.",
    _SKIPPED_COLUMNS, group="snapshot",
)

SKIPPED_APPS = declare(
    "skipped_apps.csv",
    "Apps skipped during collection because their Steam Charts page kept failing to load or parse; they have "
    "no score and cannot rank.",
    _SKIPPED_COLUMNS, group="build_reports",
)

# ----------------------------------------------------------------------------- app export (one Network State)

SIL_STATUS = "Why silhouette is empty: fewer_than_2_multi_tag_clusters or one_tag_cluster."

NODES = declare(
    "nodes.csv",
    "One row per Tag Network node (tag), sorted by cluster, medoid_score, tag_id.",
    [
        C("tag_id", "int", "Steam tag id."),
        C("tag", "str", "Tag name."),
        C("cluster", "str", "Cluster label C1…, numbered by size; never a semantic name."),
        C("n_games", "int", "Games having the tag among the N games the network is built from."),
        C("is_isolated", "bool", "True when no edge reaches the minimum shared games (degree 0)."),
        C("degree", "int", "Number of edges (unweighted)."),
        C("degree_intra", "int", "Number of edges to tags in the same cluster."),
        C("strength_shared", "float", "Sum of shared-game counts over the tag's edges."),
        C("strength_lift", "float", "Sum of lift values over the tag's edges."),
        C("strength_shared_intra", "float", "strength_shared over edges inside the tag's cluster."),
        C("strength_lift_intra", "float", "strength_lift over edges inside the tag's cluster."),
        C("silhouette", "float", "Jaccard game-set silhouette of the tag (-1..1); descriptive diagnostic."),
        C("silhouette_status", "str", SIL_STATUS),
        C("medoid_score", "float",
          "Mean Jaccard distance to the other members of the cluster (0..1); empty in One-Tag Clusters."),
        C("is_center", "bool", "Whether the tag is its cluster's Cluster Center (Jaccard medoid, clusters of 3+ tags)."),
        C("within_z", "float",
          "Within-cluster strength z-score on the active weight (population SD); its cap in an n-tag cluster is "
          "sqrt(n-1); empty in One-Tag Clusters or when every member has the same strength."),
        C("participation", "float",
          "1 - sum over clusters of (strength to the cluster / total strength)^2 on the active weight; empty at zero strength."),
        C("membership_stability", "float",
          "Mean Jaccard overlap (0..1) of the tag's cluster across the noise seeds; empty for isolated tags."),
        C("x_global", "float", "Global layout x position (renderer units)."),
        C("y_global", "float", "Global layout y position (renderer units)."),
        C("x_cluster_separated", "float", "Cluster-separated layout x position."),
        C("y_cluster_separated", "float", "Cluster-separated layout y position."),
    ],
    group="app_export",
)

EDGES = declare(
    "edges.csv",
    "One row per edge (pair of tags with at least the minimum shared games), sorted by source, target.",
    [
        C("source_tag_id", "int", "The lower tag id of the pair."),
        C("source_tag", "str", "Name of source_tag_id."),
        C("target_tag_id", "int", "The higher tag id of the pair."),
        C("target_tag", "str", "Name of target_tag_id."),
        C("shared_games", "int", "Edge weight: games having both tags; drives thresholds."),
        C("lift", "float", "shared_games x N / (n_source x n_target); 1 = as often as independent tags would."),
        C("source_cluster", "str", "Cluster of the source tag."),
        C("target_cluster", "str", "Cluster of the target tag."),
        C("is_intra_cluster", "bool", "Whether both tags are in the same cluster."),
        C("appids", "int_list", "AppIDs of the games having both tags, in dataset rank order."),
    ],
    group="app_export",
)

CLUSTERS = declare(
    "clusters.csv",
    "One row per cluster, sorted by label.",
    [
        C("cluster", "str", "Cluster label C1…."),
        C("kind", "str", "multi_tag (2+ tags) or one_tag."),
        C("size", "int", "Number of tags."),
        C("member_tag_ids", "int_list", "Member tag ids by medoid_score, then the center tie-break."),
        C("members", "str_list", "Member tag names, matching member_tag_ids."),
        C("connected", "bool", "Whether the cluster's tags form one connected group (false: try Leiden)."),
        C("internal_edges", "int", "Edges inside the cluster."),
        C("internal_weight", "float", "Summed active weight of the edges inside the cluster."),
        C("edge_density", "float", "internal_edges / (n(n-1)/2); empty for size 1."),
        C("weighted_density", "float", "internal_weight / (n(n-1)/2); empty for size 1."),
        C("cut_weight", "float", "Summed active weight of edges leaving the cluster."),
        C("conductance", "float", "cut_weight / min(volume of cluster, volume of the rest); 0..1."),
        C("conductance_status", "str", "Why conductance is empty: isolated_tag or no_edges_outside_cluster."),
        C("mean_silhouette", "float", "Mean silhouette of the members (Multi-Tag Clusters)."),
        C("silhouette_status", "str", SIL_STATUS),
        C("center_tag_id", "int", "The Cluster Center's tag id (clusters of 3+ tags)."),
        C("center", "str", "The Cluster Center: the member whose games overlap most with the others' (Jaccard medoid)."),
        C("center_medoid_score", "float", "The center's medoid_score."),
        C("center_status", "str", "Why there is no center: one_tag_cluster or two_tag_cluster."),
        C("top_strength_tag_id", "int", "Tag id of the member with the highest intra-cluster strength (active weight)."),
        C("top_strength_tag", "str", "Name of top_strength_tag_id: the frequency-driven alternative to the center."),
        C("center_is_top_strength", "bool", "Whether the center and the top-strength tag are the same tag."),
        C("mean_membership_stability", "float", "Mean Membership Stability of the members; empty for isolated tags."),
    ],
    group="app_export",
)

CLUSTER_QUALITY = declare(
    "cluster_quality.csv",
    "One row: the partition's quality, against its null model and the Seed-Noise Floor.",
    [
        C("n_dataset_games", "int", "N: games after the Minimum Months Filter."),
        C("n_nodes", "int", "Tags in the network."),
        C("n_edges", "int", "Edges in the network."),
        C("total_weight", "float", "Summed active weight of all edges."),
        C("modularity", "float", "Weighted modularity Q at the optimised resolution; 0 = no better than random."),
        C("modularity_status", "str", "Why modularity is empty: no_edges."),
        C("q_null_mean", "float", "Mean Q of the game-tag shuffle null networks."),
        C("q_null_sd", "float", "Sample SD of the null networks' Q."),
        C("modularity_z", "float", "(Q - q_null_mean) / q_null_sd; never read alone; empty when the SD is 0."),
        C("q_excess", "float", "Q - q_null_mean."),
        C("null_n_edges_mean", "float", "Mean edge count of the null networks (compare n_edges)."),
        C("coverage", "float", "Share of the total weight inside clusters (0..1)."),
        C("inter_cluster_weight_share", "float", "1 - coverage."),
        C("n_multi_tag_clusters", "int", "Clusters with 2+ tags (k)."),
        C("n_one_tag_clusters", "int", "One-Tag Clusters (s)."),
        C("n_disconnected_clusters", "int", "Clusters whose tags do not form one connected group."),
        C("mean_silhouette", "float", "Mean silhouette over Multi-Tag Cluster members; a descriptive diagnostic."),
        C("silhouette_status", "str", SIL_STATUS),
        C("seed_ari_min", "float", "Lowest ARI of a noise seed's partition against the shown one."),
        C("seed_ari_mean", "float", "Mean ARI of the noise seeds' partitions against the shown one."),
        C("seed_modularity_sd", "float", "Sample SD of Q across the noise seeds."),
        C("seed_silhouette_sd", "float", "Sample SD of mean silhouette across the noise seeds that have one."),
        C("seed_silhouette_status", "str", "Why seed_silhouette_sd is empty: fewer_than_2_seeds_with_silhouette."),
        C("seed_k_min", "int", "Fewest Multi-Tag Clusters among the noise seeds."),
        C("seed_k_max", "int", "Most Multi-Tag Clusters among the noise seeds."),
    ],
    group="app_export",
)

CLUSTER_CONNECTIONS = declare(
    "cluster_connections.csv",
    "Edges between clusters: every unordered pair of Multi-Tag Clusters, plus pairs with the pooled One-Tag Clusters.",
    [
        C("cluster_a", "str", "First cluster (or one_tag_pool)."),
        C("cluster_b", "str", "Second cluster (or one_tag_pool)."),
        C("edge_count", "int", "Edges between the two."),
        C("weight", "float", "Summed active weight of those edges."),
        C("shared_weight", "float", "Summed shared-game counts of those edges (equals weight under shared games)."),
        C("ratio", "float", "Connection Ratio: weight over the weight the two groups' total link weights alone predict, "
                            "in the Clustering Weight; at most γ. Empty where undefined."),
        C("shared_ratio", "float", "Connection Ratio from shared-game sums and strengths (equals ratio under shared "
                                   "games; under Lift not tied to the clustering). Empty where undefined."),
        C("share_of_a", "float", "Connection Share of cluster_a: weight over all of cluster_a's link weight to other "
                                 "groups. Empty when that is 0."),
        C("share_of_b", "float", "Connection Share of cluster_b: weight over all of cluster_b's link weight to other "
                                 "groups. Empty when that is 0."),
    ],
    group="app_export",
)

CLUSTER_GAMES = declare(
    "cluster_games.csv",
    "Games within each Cluster: one row per Cluster (Multi-Tag and One-Tag, never the pool) and game of the network "
    "that has at least one of its tags, by Cluster label, then most matched tags, then rank.",
    [
        C("cluster", "str", "The Cluster (C1…)."),
        C("appid", "int", "Steam AppID of the game."),
        C("name", "str", "The game's name."),
        C("rank", "int", "The game's rank in the dataset (by Mean Monthly Players)."),
        C("matched", "int", "How many of the Cluster's tags the game has."),
        C("cluster_size", "int", "How many tags the Cluster has."),
        C("network_tags", "int", "How many of the game's tags are in the Tag Network (hidden, removed and "
                                 "below-minimum tags not counted)."),
        C("share_of_game", "float", "matched / network_tags: the part of the game's network tags in this Cluster."),
        C("matched_tag_ids", "int_list", "The matched tags' ids, in the Cluster's Members order."),
        C("matched_tags", "str_list", "The matched tags' names, matching matched_tag_ids."),
    ],
    group="app_export",
)

NULL_MODEL = declare(
    "null_model.csv",
    "One row per null-model replicate (game-tag shuffle, rebuilt and reclustered).",
    [
        C("replicate", "int", "Replicate number, 1..R."),
        C("seed", "int", "The replicate's seed (shuffle and clustering)."),
        C("modularity", "float", "Q of the null network; empty when it has no edges."),
        C("n_edges", "int", "Edges of the null network."),
    ],
    group="app_export",
)

SEED_NOISE = declare(
    "seed_noise.csv",
    "One row per noise seed: the same clustering on the unchanged network, compared with the shown partition.",
    [
        C("noise_seed_index", "int", "1..K."),
        C("seed", "int", "The noise seed."),
        C("modularity", "float", "Q of the seed's partition."),
        C("silhouette", "float", "Mean silhouette of the seed's partition."),
        C("silhouette_status", "str", SIL_STATUS),
        C("ari_vs_main", "float", "ARI against the shown partition (1 = identical, about 0 = chance)."),
        C("n_multi_tag_clusters", "int", "Multi-Tag Clusters in the seed's partition."),
        C("n_one_tag_clusters", "int", "One-Tag Clusters in the seed's partition."),
    ],
    group="app_export",
)

NOT_IN_NETWORK = declare(
    "not_in_network.csv",
    "One row per tag on at least one game of the dataset that is not a node, with every reason.",
    [
        C("tag_id", "int", "Steam tag id."),
        C("tag", "str", "Tag name."),
        C("n_games", "int", "Games having the tag after the Minimum Months Filter (0 if emptied)."),
        C("reasons", "str_list", "removed;defining_tag_hidden;genre_tag_hidden;below_min_games, in that order."),
    ],
    group="app_export",
)

REMOVAL_SENSITIVITY = declare(
    "removal_sensitivity.csv",
    "One row per tested tag, in run order: how the clustering changes when the tag is hypothetically removed.",
    [
        C("run_order", "int", "Position in the run (active strength desc, then tag_id)."),
        C("tag_id", "int", "The removed tag."),
        C("tag", "str", "Tag name."),
        C("cluster", "str", "The tag's cluster in the shown partition."),
        C("is_center", "bool", "Whether the tag is a Cluster Center."),
        C("active_strength", "float", "The tag's strength on the active weight."),
        C("rc_delta_modularity", "float", "Reclustered: Q after - Q before (also reflects the lost edge weight)."),
        C("rc_silhouette_after", "float", "Reclustered: mean silhouette after the removal."),
        C("rc_silhouette_after_status", "str", SIL_STATUS),
        C("rc_delta_silhouette", "float", "Reclustered: silhouette after - before; empty when either is n/a."),
        C("rc_delta_k", "int", "Reclustered: change in the number of Multi-Tag Clusters."),
        C("rc_delta_s", "int", "Reclustered: change in the number of One-Tag Clusters."),
        C("rc_ari", "float", "Reclustered: ARI against the shown partition over the remaining tags."),
        C("rc_centers_lost_tag_ids", "int_list", "Current Cluster Centers (other than the tag) that are no longer centers."),
        C("rc_centers_lost", "str_list", "Names of rc_centers_lost_tag_ids."),
        C("rc_ari_beyond_noise", "bool", "rc_ari < seed_ari_min: a screening flag, not a significance test."),
        C("fp_delta_modularity", "float", "Partition fixed: Q after - Q before."),
        C("fp_silhouette_after", "float", "Partition fixed: mean silhouette after the removal."),
        C("fp_silhouette_after_status", "str", SIL_STATUS),
        C("fp_delta_silhouette", "float", "Partition fixed: silhouette after - before; empty when either is n/a."),
    ],
    group="app_export",
)

APP_TABLES = (NODES, EDGES, CLUSTERS, CLUSTER_QUALITY, CLUSTER_CONNECTIONS, CLUSTER_GAMES, NULL_MODEL, SEED_NOISE,
              NOT_IN_NETWORK, REMOVAL_SENSITIVITY)
# In the Workbench export zip only, never stacked into a Build's analysis/ tables.
EXPORT_ONLY = ("cluster_games.csv",)

# ----------------------------------------------------------------------------- Build: analysis/ network tables

_STACK_PREFIX = (C("dataset", "str", "Dataset key."),
                 C("state_id", "str", "Network State id (12 hex characters) of the report's state for this dataset."))


def _build_name(app_name: str) -> str:
    return app_name if app_name == "removal_sensitivity.csv" else f"network_{app_name}"


STACKED = {s.name: declare(_build_name(s.name), s.description + " Five datasets stacked.",
                           (*_STACK_PREFIX, *s.columns), group="analysis")
           for s in APP_TABLES if s.name not in EXPORT_ONLY}


def stacked(app_file: str) -> FileSchema:
    """The Build's stacked version of an app export table (`dataset`, `state_id` first)."""
    return STACKED[app_file]


_DATASET = C("dataset", "str", "Dataset key.")
_BASELINE = (
    C("baseline_count", "int", "Games in the Eligible Pool (Top 100 included) that have it."),
    C("baseline_share", "float", "baseline_count / Eligible Pool size."),
    C("share_ratio", "float",
      "share / baseline_share: over 1 = more common in the Top 100 than in its Eligible Pool; its ceiling is "
      "Eligible Pool size / 100."),
)

TAG_FREQUENCY = declare(
    "tag_frequency.csv",
    "Every tag on at least one game of a full Top-100 Dataset, against the Eligible Pool. Sorted by count, then name.",
    [
        _DATASET,
        C("tag_id", "int", "Steam tag id."),
        C("tag", "str", "Tag name."),
        C("count", "int", "Games in the Top 100 that have the tag (anywhere in the displayed list)."),
        C("share", "float", "count / number of games in the dataset."),
        C("median_position", "float", "Median position of the tag in the store tag list among the games that have it."),
        C("defining_tag", "bool", "Whether the tag defines the dataset (then it is on every game)."),
        *_BASELINE,
        C("archived_category", "str", "Category in the archived Steamworks tag table (' / ' between several); "
                                      "information only, empty when the tag has none."),
    ],
    group="analysis",
)

GENRE_FREQUENCY = declare(
    "genre_frequency.csv",
    "Every store-genre value on at least one game of a full Top-100 Dataset, against the Eligible Pool.",
    [
        _DATASET,
        C("genre_id", "int", "Steam store genre id."),
        C("genre", "str", "Genre description."),
        C("kind", "str", "Config kind: genre, business or software (unmapped when genres.toml has no entry)."),
        C("count", "int", "Games in the Top 100 with this store genre."),
        C("share", "float", "count / number of games in the dataset."),
        *_BASELINE,
    ],
    group="analysis",
)

COMBINATIONS = declare(
    "combinations.csv",
    "Tag combinations (2 up to max_itemset_size tags) with at least min_support games; defining tag excluded.",
    [
        _DATASET,
        C("size", "int", "Number of tags in the combination (k)."),
        C("tag_ids", "int_list", "Member tag ids, sorted by tag_id."),
        C("tags", "str_list", "Member tag names, matching tag_ids."),
        C("support_count", "int", "Games that have every member tag."),
        C("support_share", "float", "support_count / number of games in the dataset."),
        C("lift", "float", "support_count x N^(k-1) / product of the member tags' counts; 1 = as often as "
                           "independent tags would; a high triple lift may be inherited from one strong pair."),
        C("confidence_a_to_b", "float", "Pairs only: share of the first tag's games that also have the second."),
        C("confidence_b_to_a", "float", "Pairs only: share of the second tag's games that also have the first."),
    ],
    group="analysis",
)

ASSOCIATIONS = declare(
    "associations.csv",
    "Every pair of tags that each reach min_support, including pairs that never co-occur: a descriptive screen.",
    [
        _DATASET,
        C("tag_id_a", "int", "The lower tag id."),
        C("tag_a", "str", "Name of tag_id_a."),
        C("tag_id_b", "int", "The higher tag id."),
        C("tag_b", "str", "Name of tag_id_b."),
        C("count_a", "int", "Games with tag a."),
        C("count_b", "int", "Games with tag b."),
        C("count_ab", "int", "Games with both."),
        C("phi", "float", "Phi coefficient (-1..1; 0 = independence); empty when either tag is on every game."),
        C("lift", "float", "count_ab x N / (count_a x count_b); 1 = independence."),
        C("jaccard", "float", "count_ab / (count_a + count_b - count_ab)."),
        C("fisher_p", "float", "Two-sided Fisher exact p for the 2x2 table within this dataset."),
        C("bh_q", "float", "Benjamini-Hochberg q within this dataset: co-occurrence unlikely under independence "
                           "within this dataset, not evidence about Steam in general."),
    ],
    group="analysis",
)

CONTENT_FLAG_GAMES = declare(
    "content_flags.csv",
    "One row per dataset, Content Flag and flagged game (long form).",
    [
        _DATASET,
        C("flag", "str", "Content Flag code."),
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("rank", "int", "Rank in the dataset."),
    ],
    group="analysis",
)

RESOLUTION_SWEEP = declare(
    "resolution_sweep.csv",
    "The report's clustering repeated at each resolution of the grid, everything else unchanged; one row per "
    "dataset and resolution.",
    [
        C("dataset", "str", "Dataset key."),
        C("resolution", "float", "The resolution γ of this row."),
        C("n_multi_tag_clusters", "int", "Multi-Tag Clusters at this γ."),
        C("n_one_tag_clusters", "int", "One-Tag Clusters at this γ."),
        C("modularity", "float", "Q at this γ; not comparable across rows."),
        C("mean_silhouette", "float", "Mean silhouette over Multi-Tag Cluster members at this γ."),
        C("silhouette_status", "str", SIL_STATUS),
        C("ari_vs_report", "float", "ARI of this γ's partition against the report's partition."),
        C("seed_ari_min", "float", "Lowest noise-seed ARI at this γ."),
        C("seed_ari_mean", "float", "Mean noise-seed ARI at this γ."),
    ],
    group="analysis",
)


# ----------------------------------------------------------------------------- Parameter Selection export zip

# Every column names its chapter-3 entry and where the mode shows it; selection_report.md is the report that uses them.
_PS_REPORT = "selection_report.md"
_GRID, _ADM = "threshold-pair-and-parameter-grid", "admissible-partition-and-optimality-domain"
_GHAT, _SELP = "resolution-estimate-and-stable-partition", "selected-partition-and-selected-resolution"
_NA, _EO, _RET = "neighbour-agreement", "edge-overlap", "information-retention"
_FRAG, _RULE = "isolated-share-and-lcc-share", "pair-constraints-qualifying-pair-and-the-selection-rule"
_NULL, _SUB = "null-comparison", "subsample-stability"


def _ps(name: str, type_: str, description: str, entry: str, panel: str = "Parameter Selection: Pair Inspector",
        report: str = _PS_REPORT) -> Column:
    return Column(name, type_, description, guide_entry=entry, app_panel=panel, report_section=report)


_HEAT = "Parameter Selection: heatmap and Pair Inspector"
_PS_PAIR = (
    _ps("dataset", "str", "Dataset key.", IDENTIFIERS_ENTRY, "Parameter Selection: dataset strip"),
    _ps("g", "int", "Minimum games per tag of the Threshold Pair.", _GRID, _HEAT),
    _ps("s", "int", "Minimum shared games of the Threshold Pair.", _GRID, _HEAT),
)

PS_PAIRS = declare(
    "pairs.csv",
    "One row per dataset and Threshold Pair of the Parameter Grid (153 per dataset).",
    [
        *_PS_PAIR,
        _ps("n_tags", "int", "Tags in the pair's network (nodes).", _GRID),
        _ps("n_edges", "int", "Edges of the pair's network.", _GRID),
        _ps("n_e", "int", "Tags with at least one edge.", _GRID),
        _ps("graph_hash", "str", "SHA-256 of the sorted nodes and (u, v, shared count, weight) edges.", _GRID),
        _ps("lift_below_1_share", "float", "Share of edges with lift < 1; empty without edges.", _GRID),
        _ps("gamma_max_n_e", "float", "Gibson & Mucha's γ_max(K) at K = n_e: the scan's end rule.", _ADM),
        _ps("gamma_end", "float", "The last scan γ, the end of CHAMP's range.", _ADM),
        _ps("scan_length", "int", "γ values scanned (each with every scan seed).", _ADM),
        _ps("pass_capped_runs", "int", "Scan runs that reached the 1,000-pass cap.", _ADM),
        _ps("n_unique", "int", "Distinct partitions the scan found.", _ADM),
        _ps("n_twins", "int", "Partitions dropped as twins (identical Â and P̂).", _ADM),
        _ps("selection_reason", "str", "Why there is no Selected Partition: no_edges, no_stable_partition or "
                                       "too_few_multi_tag_clusters; empty with one.", _SELP),
        _ps("selected_low", "float", "Start a of the Selected Partition's Optimality Domain.", _SELP),
        _ps("selected_high", "float", "End b of the Selected Partition's Optimality Domain.", _SELP),
        _ps("selected_resolution", "float", "The Selected Resolution: (a + b)/2, unrounded.", _SELP),
        _ps("clipped_high", "bool", "Whether the Selected Partition's domain ends at the scan's end.", _SELP),
        _ps("workbench_gamma", "float", "The two-decimal γ Apply to Workbench enters.", _SELP),
        _ps("workbench_seed", "int", "The seed Apply to Workbench enters.", _SELP),
        _ps("reproduced", "bool", "Whether the Workbench γ and seed give exactly the Selected Partition.", _SELP),
        _ps("workbench_ari", "float", "ARI of the Workbench γ and seed's partition against the Selected Partition.",
            _SELP),
        _ps("not_representable", "bool", "No two-decimal γ ≥ 0.01 lies in the domain.", _SELP),
        _ps("not_reproduced", "bool", "A two-decimal γ lies in the domain, but no candidate reproduces it.", _SELP),
        _ps("neighbour_agreement", "float", "Mean ARI over comparable neighbours with a different graph.", _NA, _HEAT),
        _ps("na_status", "str", "ok, no_selected_partition or no_comparable_neighbours.", _NA),
        _ps("n_comparable", "int", "Neighbour links that could be compared.", _NA),
        _ps("n_different_graph", "int", "Comparable links with a different graph (the ones counted).", _NA),
        _ps("n_identical_graph", "int", "Comparable links with an identical graph (flagged, not counted).", _NA),
        _ps("n_missing", "int", "Neighbours without a Selected Partition (missing, never 0).", _NA),
        _ps("na_min_ari", "float", "The lowest ARI among the counted links (descriptive).", _NA),
        _ps("retention", "float", "Information Retention.", _RET, _HEAT),
        _ps("retention_status", "str", "no_visible_tags when no tag is visible; else empty.", _RET),
        _ps("games_with_edged_tag_share", "float", "Share of games with a tag that has an edge (descriptive).", _RET),
        _ps("n_isolated", "int", "Tags with no edge.", _FRAG),
        _ps("isolated_share", "float", "Isolated tags / tags.", _FRAG, _HEAT),
        _ps("n_components", "int", "Connected components with 2 or more tags.", _FRAG),
        _ps("lcc_tags", "int", "Tags in the largest connected component.", _FRAG),
        _ps("lcc_share", "float", "Largest component's tags / tags with an edge.", _FRAG),
        _ps("n_multi_tag_clusters", "int", "Multi-Tag Clusters of the Selected Partition.", _SELP, _HEAT),
        _ps("n_one_isolated", "int", "One-Tag Clusters that are isolated tags.", _FRAG),
        _ps("n_one_connected", "int", "One-Tag Clusters of tags with an edge.", _FRAG),
        _ps("seed_noise_floor", "float", "Seed-Noise Floor at the Selected Resolution: lowest ARI over the noise "
                                         "seeds.", "adjusted-rand-index", _HEAT),
        _ps("seed_noise_mean", "float", "Mean ARI over the noise seeds.", "adjusted-rand-index"),
        _ps("seed_noise_exact", "int", "Noise seeds that give exactly the Selected Partition.", "adjusted-rand-index"),
        _ps("hits", "int", "Scan runs that found the Selected Partition.", _ADM),
        _ps("modularity", "float", "Descriptive: Q of the Selected Partition; not comparable across pairs.",
            "modularity-q", _HEAT),
        _ps("coverage", "float", "Descriptive: weighted coverage; not comparable across pairs.",
            "coverage-and-inter-cluster-weight-share"),
        _ps("silhouette", "float", "Descriptive: mean Jaccard silhouette; not comparable across pairs.",
            "mean-silhouette"),
        _ps("silhouette_status", "str", SIL_STATUS, "mean-silhouette"),
        _ps("qualifies", "bool", "Whether the pair is a Qualifying Pair under the export's constraints.", _RULE,
            _HEAT),
        _ps("reasons", "str_list", "Every failing reason code, in the selection rule's order.", _RULE, _HEAT),
        _ps("near_best", "bool", "In the near-best set.", _RULE, _HEAT),
        _ps("chosen", "bool", "The chosen pair.", _RULE, _HEAT),
    ],
    group="parameter_selection",
)

PS_ADMISSIBLE = declare(
    "admissible_partitions.csv",
    "One row per dataset, Threshold Pair and Admissible Partition, in domain order.",
    [
        *_PS_PAIR,
        _ps("partition", "int", "The Admissible Partition's position, 1 = lowest γ.", _ADM),
        _ps("a_hat", "float", "Â: twice the weight inside Clusters.", _ADM),
        _ps("p_hat", "float", "P̂: Σ κ_c² / 2m.", _ADM),
        _ps("domain_low", "float", "Start a of the Optimality Domain.", _ADM),
        _ps("domain_high", "float", "End b of the Optimality Domain.", _ADM),
        _ps("clipped_high", "bool", "The domain ends at the scan's end.", _ADM),
        _ps("omega_in", "float", "ω_in = Â / P̂.", _GHAT),
        _ps("omega_out", "float", "ω_out = (2m − Â) / (2m − P̂).", _GHAT),
        _ps("gamma_hat", "float", "γ̂; empty with gamma_hat_reason.", _GHAT),
        _ps("gamma_hat_reason", "str", "no_edges, one_group, no_cross_weight or not_assortative.", _GHAT),
        _ps("map_target", "int", "The partition whose domain holds γ̂; empty if none.", _GHAT),
        _ps("stable", "bool", "domain_low ≤ γ̂ ≤ domain_high.", _GHAT),
        _ps("n_multi_tag_clusters", "int", "Multi-Tag Clusters of this partition.", _SELP),
        _ps("n_one_tag_clusters", "int", "One-Tag Clusters of this partition.", _SELP),
        _ps("first_gamma", "float", "The first scan γ that found it.", _ADM),
        _ps("first_seed", "int", "The scan seed of that first run.", _ADM),
        _ps("hits", "int", "Scan runs that found it.", _ADM),
        _ps("selected", "bool", "Whether it is the pair's Selected Partition.", _SELP),
    ],
    group="parameter_selection",
)

PS_LINKS = declare(
    "neighbour_links.csv",
    "One row per dataset, Threshold Pair and direction (g−, g+, s−, s+).",
    [
        *_PS_PAIR,
        _ps("direction", "str", "g−, g+, s− or s+.", _NA),
        _ps("neighbour_g", "int", "The neighbour's g.", _NA),
        _ps("neighbour_s", "int", "The neighbour's s.", _NA),
        _ps("status", "str", "ok, neighbour_has_no_selected_partition, too_few_compared_tags or outside_grid.", _NA),
        _ps("identical_graph", "bool", "The two pairs have the same graph hash.", _NA),
        _ps("n_shared", "int", "Tags in both networks.", _NA),
        _ps("shared_jaccard", "float", "Jaccard overlap of the two node sets.", _NA),
        _ps("n_compared", "int", "Shared tags with an edge in at least one network.", _NA),
        _ps("ari", "float", "ARI of the two Selected Partitions on the compared tags.", _NA),
        _ps("edge_overlap", "float", "Edge Overlap: Jaccard overlap of the two edge sets.", _EO),
    ],
    group="parameter_selection",
)

PS_SELECTED = declare(
    "selected_partitions.csv",
    "One row per dataset, Threshold Pair and tag of its network: the tag's Cluster in the Selected Partition.",
    [
        *_PS_PAIR,
        _ps("tag_id", "int", "Steam tag id.", IDENTIFIERS_ENTRY),
        _ps("tag", "str", "Tag name.", IDENTIFIERS_ENTRY),
        _ps("cluster", "str", "C1… as in the app; empty when the pair has no Selected Partition.", _SELP),
    ],
    group="parameter_selection",
)

PS_SELECTION = declare(
    "selection.csv",
    "One row per dataset: the chosen pair under the export's constraints.",
    [
        _ps("dataset", "str", "Dataset key.", IDENTIFIERS_ENTRY, "Parameter Selection: dataset strip"),
        _ps("status", "str", "ok or no_qualifying_pair.", _RULE, "Parameter Selection: Why this pair"),
        _ps("chosen_g", "int", "g of the chosen pair.", _RULE, "Parameter Selection: Why this pair"),
        _ps("chosen_s", "int", "s of the chosen pair.", _RULE, "Parameter Selection: Why this pair"),
        _ps("max_neighbour_agreement", "float", "The highest Neighbour Agreement among Qualifying Pairs.", _RULE,
            "Parameter Selection: Why this pair"),
        _ps("tolerance", "float", "The near-best tolerance.", _RULE, "Parameter Selection: Pair Constraints"),
        _ps("near_best", "str_list", "The near-best set as g·s.", _RULE, "Parameter Selection: Why this pair"),
        _ps("tie_break", "str", "The tie-break used among near-best pairs.", _RULE, "Parameter Selection: Why this pair"),
        _ps("n_qualifying", "int", "Qualifying Pairs.", _RULE, "Parameter Selection: Why this pair"),
        _ps("min_retention", "float", "Pair Constraint: minimum Information Retention.", _RULE,
            "Parameter Selection: Pair Constraints"),
        _ps("max_isolated_share", "float", "Pair Constraint: maximum isolated share.", _RULE,
            "Parameter Selection: Pair Constraints"),
        _ps("min_lcc_share", "float", "Pair Constraint: minimum LCC share.", _RULE,
            "Parameter Selection: Pair Constraints"),
        _ps("min_comparable_neighbours", "int", "Pair Constraint: minimum comparable neighbours with a different "
                                                "graph.", _RULE, "Parameter Selection: Pair Constraints"),
        _ps("max_multi_tag_clusters", "int", "Pair Constraint: maximum Multi-Tag Clusters; empty = off.", _RULE,
            "Parameter Selection: Pair Constraints"),
        _ps("constraints_label", "str", "\"Default constraints\" or \"Custom constraints: …\".", _RULE,
            "Parameter Selection: Pair Constraints"),
        _ps("settings_label", "str", "\"Default settings\" or \"Custom settings: …\".", _RULE,
            "Parameter Selection: Selection settings"),
    ],
    group="parameter_selection",
)

_VAL = "Parameter Selection: validation card"
PS_REPLICATES = declare(
    "validation_replicates.csv",
    "One row per validated pair, replicate and arm (null, subsample_reselected, subsample_at_resolution).",
    [
        *_PS_PAIR,
        _ps("arm", "str", "null, subsample_reselected or subsample_at_resolution.", _SUB, _VAL),
        _ps("replicate", "int", "1..R or 1..S.", _NULL, _VAL),
        _ps("seed", "int", "The replicate's seed (stream 4 for nulls, 5 for subsamples).", _NULL, _VAL),
        _ps("has_selected_partition", "bool", "The replicate's own procedure found a Selected Partition (null and "
                                              "re-selected arms).", _NULL, _VAL),
        _ps("reason", "str", "Why not, as for the observed pair.", _NULL, _VAL),
        _ps("degenerate", "bool", "Subsample left out of the summaries (no edges; re-selected: no Selected "
                                  "Partition).", _SUB, _VAL),
        _ps("degenerate_reason", "str", "Why it is degenerate.", _SUB, _VAL),
        _ps("ari", "float", "Subsamples: ARI against the Selected Partition on the comparison set.", _SUB, _VAL),
        _ps("null_q", "float", "Nulls: Q at the observed Selected Resolution from the replicate's envelope.", _NULL,
            _VAL),
        _ps("domain_width", "float", "Width of the replicate's Selected Partition's domain.", _NULL, _VAL),
        _ps("selected_resolution", "float", "The replicate's Selected Resolution.", _NULL, _VAL),
        _ps("n_multi_tag_clusters", "int", "Multi-Tag Clusters of the replicate's Selected Partition.", _NULL, _VAL),
        _ps("n_edges", "int", "Edges of the replicate's network.", _NULL, _VAL),
        _ps("scan_length", "int", "γ values the replicate scanned.", _NULL, _VAL),
        _ps("capped_runs", "int", "Scan runs that reached the pass cap.", _NULL, _VAL),
    ],
    group="parameter_selection",
)

PS_CLUSTERS = declare(
    "validation_clusters.csv",
    "One row per validated pair, Subsample Stability arm and Multi-Tag Cluster of its Selected Partition.",
    [
        *_PS_PAIR,
        _ps("arm", "str", "subsample_reselected or subsample_at_resolution.", _SUB, _VAL),
        _ps("cluster", "str", "C1… of the Selected Partition.", _SUB, _VAL),
        _ps("member_tag_ids", "int_list", "The Cluster's tags.", IDENTIFIERS_ENTRY, _VAL),
        _ps("mean_jaccard", "float", "Hennig's mean best-match Jaccard over the B* subsamples where it is present.",
            _SUB, _VAL),
        _ps("at_most_half", "int", "Subsamples with a Jaccard ≤ 0.5.", _SUB, _VAL),
        _ps("present", "int", "B*: subsamples where the Cluster has a tag in the comparison set.", _SUB, _VAL),
        _ps("mean_retention", "float", "Mean share of the Cluster's tags present.", _SUB, _VAL),
        _ps("absent", "int", "Subsamples where none of its tags is present (left out of the mean).", _SUB, _VAL),
        _ps("dissolved", "bool", "mean_jaccard ≤ 0.5 (Hennig 2007, §2).", _SUB, _VAL),
    ],
    group="parameter_selection",
)

PS_TABLES = (PS_PAIRS, PS_ADMISSIBLE, PS_LINKS, PS_SELECTED, PS_SELECTION, PS_REPLICATES, PS_CLUSTERS)
