"""The single declaration of every exported file and column.

Every CSV the package writes is declared here with its columns, types and one-line descriptions, and
every writer validates against these declarations (`steamstudy.export.writer`). `export.json` and
`analysis.json` embed a `columns` block generated from here.

Adding, removing or renaming a column bumps `SCHEMA_VERSION` (separate from the Network State
`key_version`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

SCHEMA_VERSION = 2  # 1 + the one shared bump for the ticket 25, 27 and 28 overrides (spec)

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

# ----------------------------------------------------------------------------- Build: reports/

PARSE_ERRORS = declare(
    "parse_errors.csv",
    "Every parse error in the Snapshot. Any row fails the Build unless --allow-parse-errors was passed.",
    [
        C("appid", "int", "Steam AppID; empty for a listing page."),
        C("source", "str", "Which response: top_page, steamcharts_app, store_page, appdetails or steamdb_page."),
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
    "Store vs SteamDB tags for each Top-100 game with a SteamDB page in the Snapshot. In a Snapshot whose Tag "
    "Source is the store page it is a cross-check only: SteamDB values never enter a dataset.",
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
        C("shared_games", "int", "Edge weight: games having both tags; drives thresholds and edge thickness."),
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

APP_TABLES = (NODES, EDGES, CLUSTERS, CLUSTER_QUALITY, CLUSTER_CONNECTIONS, NULL_MODEL, SEED_NOISE, NOT_IN_NETWORK,
              REMOVAL_SENSITIVITY)

# ----------------------------------------------------------------------------- Build: analysis/ network tables

_STACK_PREFIX = (C("dataset", "str", "Dataset key."),
                 C("state_id", "str", "Network State id (12 hex characters) of the report's state for this dataset."))


def _build_name(app_name: str) -> str:
    return app_name if app_name == "removal_sensitivity.csv" else f"network_{app_name}"


STACKED = {s.name: declare(_build_name(s.name), s.description + " Five datasets stacked.",
                           (*_STACK_PREFIX, *s.columns), group="analysis")
           for s in APP_TABLES}


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
