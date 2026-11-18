"""The single declaration of every exported file and column, per Build kind.

Every CSV the package writes is declared here with its columns, types and one-line descriptions, and
every writer validates against these declarations (`steamstudy.export.writer`). `export.json` and
`analysis.json` embed a `columns` block generated from here, with only their Build kind's files.

Files are keyed `<kind>/<group>/<name>`, the kind being `steam` or `import` (`build.json` `source`). The
declarations below are the Steam files. Each Steam file an Import Build also writes gets an Import variant
derived by one rule (`import_variant`); a file the rule leaves unchanged is declared once, with kind `both`.
Import-only files are declared with kind `import`.

Adding, removing or renaming a column bumps `SCHEMA_VERSION` (separate from the Network State
`key_version`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# 1 + the one shared bump for the ticket 25, 27 and 28 overrides (spec); 3 adds the Parameter Selection
# export zip (`parameter_selection` group) and `applied_from` in export.json; 5 (the validation review) adds
# validation_pairs.csv and the new validation_replicates.csv and validation_clusters.csv columns; 6 (Build
# management, once for the whole effort) keys the files by Build kind and adds the Import Build files; 7 adds the
# Cluster Comparison export zip (`cluster_comparison` group); 8 adds `workbench_seed_priority` to
# parameter_selection.json and to `applied_from` in export.json (Workbench Seed Priority).
SCHEMA_VERSION = 8

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

KINDS = ("steam", "import")
BOTH = "both"  # a file that does not differ between the kinds


def build_kind(build_json: dict) -> str:
    """The Build kind of a `build.json`: `import` for an Import Build, else `steam` (no `source` means Steam)."""
    return "import" if build_json.get("source") == "import" else "steam"


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
    kind: str = "steam"  # "steam", "import" or "both"

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name}: duplicate column names")
        if self.kind not in (*KINDS, BOTH):
            raise ValueError(f"{self.name}: unknown kind {self.kind!r}")

    @property
    def kinds(self) -> tuple[str, ...]:
        return KINDS if self.kind == BOTH else (self.kind,)

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns)

    def column(self, name: str) -> Column:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(f"{self.name} has no column {name!r}")

    def for_datasets(self, keys: tuple[str, ...] | list[str]) -> FileSchema:
        """The file for a Build whose datasets are `keys`: the `would_be_rank_<dataset>` column, declared once
        per default dataset, becomes one column per dataset in the given (config) order."""
        template = [c for c in self.columns if c.name.startswith(WOULD_BE_RANK)]
        if not template:
            return self
        first = next(i for i, c in enumerate(self.columns) if c.name.startswith(WOULD_BE_RANK))
        expanded = tuple(
            replace(template[0], name=f"{WOULD_BE_RANK}{k}", description=_would_be_rank_description(k)) for k in keys)
        rest = [c for c in self.columns if not c.name.startswith(WOULD_BE_RANK)]
        return replace(self, columns=(*rest[:first], *expanded, *rest[first:]))

    def with_prefix(self, name: str, prefix: tuple[Column, ...], group: str = "") -> FileSchema:
        """The same file with leading columns, e.g. an app table stacked by dataset in the Build."""
        return replace(self, name=name, columns=(*prefix, *self.columns), group=group or self.group)


@dataclass
class Registry:
    files: dict[str, FileSchema] = field(default_factory=dict)  # <kind>/<group>/<name>; `both` under each kind
    declared: list[FileSchema] = field(default_factory=list)  # each file once, in declaration order

    def declare(self, schema: FileSchema) -> FileSchema:
        keys = [f"{kind}/{schema.group}/{schema.name}" for kind in schema.kinds]
        for key in keys:
            if key in self.files:
                raise ValueError(f"file {key} declared twice")
        for key in keys:
            self.files[key] = schema
        self.declared.append(schema)
        return schema

    def __getitem__(self, key: str) -> FileSchema:
        """A file by `<kind>/<group>/<name>`; a bare `<group>/<name>` is the Steam file."""
        return self.files[key if key.split("/", 1)[0] in KINDS else f"steam/{key}"]

    def __iter__(self):
        return iter(self.declared)

    def of_kind(self, kind: str) -> list[FileSchema]:
        """Every file a Build of `kind` can write, in declaration order."""
        return [s for s in self.declared if kind in s.kinds]

    def variant(self, schema: FileSchema, kind: str) -> FileSchema | None:
        """The `kind` file of the same group and name as `schema`, or None when that kind has none."""
        return self.files.get(f"{kind}/{schema.group}/{schema.name}")


REGISTRY = Registry()

# ----------------------------------------------------------------------------- Import variants

# The Steam files an Import Build does not write (spec, "Files an Import Build writes"); `top100_<dataset>.csv` is
# replaced by `topn_<dataset>.csv`, and the Snapshot folder's files have no Import counterpart. Every other Steam file
# gets an Import variant by `import_variant`.
IMPORT_NOT_WRITTEN = ("parse_errors.csv", "placeholder_rows.csv", "tag_vocabulary.csv", "release_month_check.csv",
                      "impact_adult_signals.csv", "impact_unexcluded.csv", "manual_metadata.csv",
                      "steamdb_crosscheck.csv", "skipped_apps.csv", "genre_frequency.csv", "monthly_players.csv")
_STEAM_ONLY_FILES = (*IMPORT_NOT_WRITTEN, "top100_<dataset>.csv")
STEAM_ONLY_GROUPS = ("snapshot",)
# The non-CSV files of an Import Build, beside the declared CSVs (`import_build_paths`).
IMPORT_BUILD_TEXT_FILES = ("datasets/build.json", "reports/reports.html", "analysis/analysis.json",
                           "analysis/report.html")
# Written only under a condition.
IMPORT_BUILD_CONDITIONS = {"reports/ties.csv": "only when the Import has a score"}
_BUILD_FOLDERS = {"build_datasets": "datasets", "build_reports": "reports", "analysis": "analysis"}

# The derivation rule: renamed columns, Steam-only columns dropped, Steam wording of identifiers made generic.
IMPORT_RENAMED = {"appid": "id", "appids": "ids", "mean_monthly_players": "score"}
IMPORT_DROPPED = frozenset({
    "archived_category", "months_observed", "release_month", "store_release_date", "is_free", "app_type",
    "genre_ids", "genres", "genre_id", "genre", "metadata_source", "top_listing_rank"})
_RENAMED_DESCRIPTION = {"id": "Item id.", "score": "The item's score from the Import: ranks the items, highest first."}
_RENAMED_ENTRY = {"score": "rank-and-ties"}
_STEAM_TO_GENERIC_WORDING = (("Steam tag id.", "Attribute id."), ("AppIDs", "Item ids"), ("Steam AppID", "Item id"),
         ("Mean Monthly Players", "score"))
# Import-only wording of a column the rule keeps: (file, column) -> description.
_IMPORT_DESCRIPTION = {
    ("exclusions.csv", "name"): "Item name from the Import.",
    ("completeness.csv", "section"):
        "Group of the count: exclusions_overlapping, exclusions_primary, depth_check, import (items, attributes, "
        "warnings).",
}


def _generic_wording(text: str) -> str:
    for steam, generic in _STEAM_TO_GENERIC_WORDING:
        text = text.replace(steam, generic)
    return text


def import_variant(steam: FileSchema) -> FileSchema:
    """The Import Build's file derived from a Steam declaration: same file name; `appid` -> `id`, `appids` -> `ids`,
    `mean_monthly_players` -> `score`; `tag_id`, `tag`, `tag_ids`, `tags` kept; Steam-only columns dropped; "Steam tag
    id." reads "Attribute id."."""
    columns = []
    for c in steam.columns:
        if c.name in IMPORT_DROPPED:
            continue
        name = IMPORT_RENAMED.get(c.name, c.name)
        description = (_IMPORT_DESCRIPTION.get((steam.name, name)) or _RENAMED_DESCRIPTION.get(name)
                       or _generic_wording(c.description))
        columns.append(replace(c, name=name, description=description,
                               guide_entry=_RENAMED_ENTRY.get(name, c.guide_entry)))
    return replace(steam, description=_generic_wording(steam.description), columns=tuple(columns), kind="import")


def _has_import_variant(schema: FileSchema) -> bool:
    return schema.group not in STEAM_ONLY_GROUPS and schema.name not in _STEAM_ONLY_FILES


def import_build_paths() -> tuple[str, ...]:
    """Every file an Import Build writes, as `<folder>/<name>`: its declared CSVs and its text files."""
    csvs = [f"{_BUILD_FOLDERS[s.group]}/{s.name}" for s in REGISTRY.of_kind("import") if s.group in _BUILD_FOLDERS]
    return tuple(sorted({*csvs, *IMPORT_BUILD_TEXT_FILES}))


def declare(name: str, description: str, columns: list[Column] | tuple[Column, ...], group: str = "",
            kind: str = "steam") -> FileSchema:
    """Declare a file; each column gets its guide entry, app panel and report section (see guide_index). A Steam
    file an Import Build also writes gets its Import variant here, or is declared for both kinds when the variant
    does not differ."""
    schema = FileSchema(name, description, tuple(_annotate(name, group, c) for c in columns), group, kind)
    if kind == "steam" and _has_import_variant(schema):
        variant = import_variant(schema)
        if variant == replace(schema, kind="import"):
            return REGISTRY.declare(replace(schema, kind=BOTH))
        REGISTRY.declare(variant)
    return REGISTRY.declare(schema)


def _annotate(file_name: str, group: str, column: Column) -> Column:
    from steamstudy.export import guide_index as G

    return replace(
        column,
        guide_entry=column.guide_entry or G.guide_entry(file_name, column.name),
        app_panel=column.app_panel or G.app_panel(file_name, group),
        report_section=column.report_section or G.report_section(file_name, column.name),
    )


def file(key: str) -> FileSchema:
    """A declared file by `<kind>/<group>/<name>`, e.g. `import/app_export/nodes.csv`; `<group>/<name>` is Steam's."""
    return REGISTRY[key]


def columns_block(schemas: list[FileSchema] | tuple[FileSchema, ...],
                  kind: str = "steam") -> dict[str, dict[str, dict[str, str]]]:
    """The `columns` block embedded in `export.json` / `analysis.json`: file -> column -> type/description. Every
    file must be one a Build of `kind` writes."""
    for s in schemas:
        if kind not in s.kinds:
            raise ValueError(f"{s.name} is a {s.kind} file, not one of a {kind} Build")
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

WOULD_BE_RANK = "would_be_rank_"
# The datasets of the shipped config. A Build's own datasets come from its config; `FileSchema.for_datasets`
# expands the `would_be_rank_<dataset>` column once per dataset.
DEFAULT_DATASET_KEYS = ("overall", "puzzle", "rpg", "strategy", "simulation")


def _would_be_rank_description(key: str) -> str:
    return (f"Rank the game takes in the {key} ranking, or would take had it not been excluded; empty when the "
            f"game is outside that dataset's scope (no defining tag, or tags unknown).")


def _would_be_rank_columns() -> list[Column]:
    """One column per dataset key; a Build with other datasets gets its own via `FileSchema.for_datasets`."""
    return [C(f"{WOULD_BE_RANK}{key}", "int", _would_be_rank_description(key)) for key in DEFAULT_DATASET_KEYS]


# ----------------------------------------------------------------------------- Build: datasets/

TOP100 = declare(
    "top100_<dataset>.csv",
    "One Top-N Dataset: the N non-excluded games with the highest Mean Monthly Players (N is the dataset's List "
    "Size; the file name dates from when N was always 100). The app's loading contract for Steam Builds.",
    [
        C("dataset", "str", "Dataset key."),
        C("rank", "int", "1-N; by mean_monthly_players desc, then months_observed desc, then appid asc."),
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

TOPN = declare(
    "topn_<dataset>.csv",
    "One Top-N Dataset of an Import Build: its N highest-ranked non-excluded items (N is the dataset's List Size). "
    "The app's loading contract for Import Builds.",
    [
        C("dataset", "str", "Dataset key."),
        C("rank", "int", "1-N; by score desc, then file order (without a score: file order)."),
        C("id", "int", "Item id."),
        C("name", "str", "Item name from the Import."),
        C("score", "float", "The item's score from the Import; empty when the Import has none."),
        C("filter_value", "float", "The item's value of the Build's filter field (named in build.json); empty "
                                   "without one."),
        C("tag_ids", "int_list", "The item's attribute ids in the Import's order (the full list)."),
        C("tags", "str_list", "The item's attribute names, matching tag_ids."),
    ],
    group="build_datasets", kind="import",
)

ITEM_FIELDS = declare(
    "item_fields.csv",
    "The extra numeric fields of every item in a Top-N Dataset of an Import Build, long form; no row for an empty "
    "cell.",
    [
        C("id", "int", "Item id."),
        C("field", "str", "The Import column the value comes from."),
        C("value", "float", "The item's value in that column."),
    ],
    group="build_datasets", kind="import",
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
        C("reason", "str", "Matched rule: store_data_unavailable, app_type, no_tags, a named rule of exclusions.toml "
                            "(by default adult_content, software_tag or dating_sim_tag) or manual."),
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
    "Scored games where the store's Adult Only notice and the rule's content descriptor ids (default 3) disagree; "
    "written for the rule named adult_content, headers only when there is none.",
    [
        C("appid", "int", "Steam AppID."),
        C("name", "str", "Game name."),
        C("adult_only_notice", "bool", "The store page shows the Adult Only notice."),
        C("content_descriptor_3", "bool", "appdetails content_descriptors contains one of the rule's descriptor ids (default 3)."),
        C("hentai_tag", "bool", "One of the rule's tags (default Hentai) is within its rank limit."),
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


STACKED = {s.name: declare(_build_name(s.name), s.description + " Every dataset stacked.",
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
PS_VALIDATION_PAIRS = declare(
    "validation_pairs.csv",
    "One row per validated pair: the Null Comparison's state and counts, and the two flags.",
    [
        *_PS_PAIR,
        _ps("resolution", "float", "The observed Selected Resolution γ_obs, where every shuffled network's Q is read.",
            _NULL, _VAL),
        _ps("observed_q", "float", "The observed Q the comparison uses: the Selected Partition's, or the runs' at "
                                   "γ_obs when higher.", _NULL, _VAL),
        _ps("observed_q_selected", "float", "The Selected Partition's own Q at γ_obs.", _NULL, _VAL),
        _ps("null_state", "str", "above_all_defined, reached or undefined (D = 0).", _NULL, _VAL),
        _ps("replicates", "int", "R: shuffled networks.", _NULL, _VAL),
        _ps("q_defined", "int", "D: shuffled networks with a Q at γ_obs.", _NULL, _VAL),
        _ps("q_undefined", "int", "U = R − D: shuffled networks without one.", _NULL, _VAL),
        _ps("q_undefined_no_edges", "int", "Of U: networks without edges.", _NULL, _VAL),
        _ps("q_undefined_beyond_scan", "int", "Of U: γ_obs lay beyond the network's γ scan.", _NULL, _VAL),
        _ps("reach", "int", "Of D: shuffled networks whose Q reaches observed_q (≥).", _NULL, _VAL),
        _ps("width_observed", "float", "Width of the Selected Partition's domain.", _NULL, _VAL),
        _ps("width_null_median", "float", "Median domain width over the K shuffled networks with a Selected "
                                          "Partition.", _NULL, _VAL),
        _ps("width_wider", "int", "Of K: shuffled networks the observed domain is wider than.", _NULL, _VAL),
        _ps("width_equal", "int", "Of K: equal widths, counted apart.", _NULL, _VAL),
        _ps("width_compared", "int", "K: shuffled networks with a Selected Partition.", _NULL, _VAL),
        _ps("weak_null", "bool", "Most shuffled networks have no Q at γ_obs (D < R/2).", _NULL, _VAL),
        _ps("rarely_assessable", "bool", "A Multi-Tag Cluster is rarely assessable (B* < S/2) in either Subsample "
                                         "Stability arm.", _SUB, _VAL),
    ],
    group="parameter_selection",
)

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
        _ps("degenerate_reason", "str", "Why it is degenerate (beyond_scan: γ_obs lay beyond its γ scan).", _SUB,
            _VAL),
        _ps("beyond_scan", "bool", "Nulls and the at-resolution arm: γ_obs lay beyond the replicate's γ scan.",
            _NULL, _VAL),
        _ps("ari", "float", "Subsamples: ARI against the Selected Partition on the comparison set.", _SUB, _VAL),
        _ps("edged_share", "float", "Subsamples: share of the observed network's edged tags in the comparison set "
                                    "(the tags the ARI covers).", _SUB, _VAL),
        _ps("at_resolution_changed", "bool", "At resolution: the runs at γ_obs beat the envelope's partition; empty "
                                             "when degenerate.", _SUB, _VAL),
        _ps("q_defined", "bool", "Nulls: the replicate has a Q at γ_obs.", _NULL, _VAL),
        _ps("null_q_envelope", "float", "Nulls: Q at γ_obs from the replicate's CHAMP envelope alone.", _NULL, _VAL),
        _ps("null_q", "float", "Nulls: the final Q at γ_obs, the higher of the envelope's and the runs' at γ_obs.",
            _NULL, _VAL),
        _ps("perturbation_share", "float", "Nulls: Perturbation Share, the share of the game × tag table's 1-cells "
                                           "the shuffle moved.", _NULL, _VAL),
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
        _ps("size", "int", "Tags in the Cluster.", _SUB, _VAL),
        _ps("present", "int", "B*: subsamples where Hennig's Jaccard is defined (two or more of the Cluster's tags "
                              "in the comparison set).", _SUB, _VAL),
        _ps("mean_jaccard", "float", "Mean of Hennig's Jaccard (best match, on the comparison set) over the B* "
                                     "subsamples.", _SUB, _VAL),
        _ps("mean_jaccard_se", "float", "Monte Carlo standard error of mean_jaccard (sd/√B*); empty under two "
                                        "values.", _SUB, _VAL),
        _ps("at_most_half", "int", "Of B*: subsamples with Hennig's Jaccard ≤ 0.5.", _SUB, _VAL),
        _ps("dissolution_frequency", "float", "at_most_half / B*.", _SUB, _VAL),
        _ps("wilson_low", "float", "Lower end of the 95% Wilson interval of dissolution_frequency.", _SUB, _VAL),
        _ps("wilson_high", "float", "Upper end of the 95% Wilson interval of dissolution_frequency.", _SUB, _VAL),
        _ps("recovered", "int", "Of B*: subsamples with Hennig's Jaccard > 0.75.", _SUB, _VAL),
        _ps("recovery_frequency", "float", "recovered / B*.", _SUB, _VAL),
        _ps("recovery_wilson_low", "float", "Lower end of the 95% Wilson interval of recovery_frequency.", _SUB,
            _VAL),
        _ps("recovery_wilson_high", "float", "Upper end of the 95% Wilson interval of recovery_frequency.", _SUB,
            _VAL),
        _ps("mean_whole_cluster_jaccard", "float", "Mean Whole-Cluster Jaccard over the arm's non-degenerate "
                                                   "subsamples (0 when no tag survives).", _SUB, _VAL),
        _ps("mean_retention", "float", "Mean share of the Cluster's tags present.", _SUB, _VAL),
        _ps("absent", "int", "Subsamples where none of its tags is present.", _SUB, _VAL),
        _ps("assessable", "bool", "B* ≥ 1; otherwise the Cluster is Not assessable.", _SUB, _VAL),
        _ps("dissolved_in_most", "bool", "Dissolved in most subsamples: at_most_half > B*/2 (exactly half is not "
                                         "labelled).", _SUB, _VAL),
        _ps("borderline", "bool", "The 95% Wilson interval of dissolution_frequency contains ½.", _SUB, _VAL),
    ],
    group="parameter_selection",
)

PS_TABLES = (PS_PAIRS, PS_ADMISSIBLE, PS_LINKS, PS_SELECTED, PS_SELECTION, PS_VALIDATION_PAIRS, PS_REPLICATES,
             PS_CLUSTERS)


# ----------------------------------------------------------------------------- Cluster Comparison export zip

# Every pair of the included datasets, whatever the mode shows; A is always the earlier dataset in the Build's order.
# Each column names its chapter-3 entry and the part of the mode that shows it; the zip has no report.
_CC_STATE, _CC_MATCH = "comparison-state-and-comparisonid", "cluster-match-and-comparable-tags"
_CC_JACC, _CC_SHARE = "match-jaccard-and-jaccard-on-comparable-tags", "shared-share"
_CC_OVERLAP, _CC_ARI, _CC_COVER = "overlap-vs-expected", "ari-on-comparable-tags", "comparable-tags-coverage"
_CC_GAMES, _CC_FLAGS = "games-in-common-and-games-in-both-clusters", "no-match-flags"
_CC_ROWS, _CC_PAIRS = "Cluster Comparison: dataset table", "Cluster Comparison: dataset pairs"
_CC_DIAGRAM, _CC_DETAIL = "Cluster Comparison: link diagram", "Cluster Comparison: match detail"
_CC_GROUPS = (("other_cluster", "in another Multi-Tag Cluster of the other dataset"),
              ("one_tag", "in a One-Tag Cluster of the other dataset"),
              ("not_in_network", "not in the other dataset's network"),
              ("hidden", "hidden in the other dataset (its defining Tag): set aside, in no figure"))


def _cc(name: str, type_: str, description: str, entry: str, panel: str = _CC_DETAIL) -> Column:
    return Column(name, type_, description, guide_entry=entry, app_panel=panel, report_section="none")


_CC_PAIR = (
    _cc("dataset_a", "str", "Dataset A's key: the earlier dataset of the pair in the Build's order.",
        IDENTIFIERS_ENTRY, _CC_PAIRS),
    _cc("dataset_b", "str", "Dataset B's key: the later dataset of the pair in the Build's order.", IDENTIFIERS_ENTRY,
        _CC_PAIRS),
)
_CC_MATCH_KEY = (
    _CC_PAIR[0],
    _cc("cluster_a", "str", "The Multi-Tag Cluster of A (C1…, labels of A's partition).", "cluster-labels-and-counts",
        _CC_DIAGRAM),
    _CC_PAIR[1],
    _cc("cluster_b", "str", "The Multi-Tag Cluster of B (C1…, labels of B's partition).", "cluster-labels-and-counts",
        _CC_DIAGRAM),
)

CC_DATASETS = declare(
    "datasets.csv",
    "One row per included dataset: its source and values, enough to rebuild its partition.",
    [
        _cc("dataset", "str", "Dataset key.", IDENTIFIERS_ENTRY, _CC_ROWS),
        _cc("source", "str", "Where its partition comes from: pick, cell, hand or no_run.", _CC_STATE, _CC_ROWS),
        _cc("g", "int", "Minimum games per tag.", _CC_STATE, _CC_ROWS),
        _cc("s", "int", "Minimum shared games.", _CC_STATE, _CC_ROWS),
        _cc("resolution", "float", "γ: the Selected Resolution on a cell; as set otherwise.", _CC_STATE, _CC_ROWS),
        _cc("seed", "int", "The Build's main seed (hand and no_run); empty on a cell, which has no seed.", _CC_STATE,
            _CC_ROWS),
        _cc("selection_key", "str", "SHA-256 of the Parameter Selection settings key of its run (cell only).",
            _CC_STATE, _CC_ROWS),
        _cc("state_id", "str", "The Network State id of its settings (hand and no_run only).", _CC_STATE, _CC_ROWS),
        _cc("n_games", "int", "Games of the dataset after the shared Minimum Months Filter.", "network-size",
            _CC_ROWS),
        _cc("n_tags", "int", "Tags in its network (nodes).", "network-size", _CC_ROWS),
        _cc("n_multi_tag_clusters", "int", "Multi-Tag Clusters of its partition.", "cluster-labels-and-counts",
            _CC_DIAGRAM),
        _cc("n_one_tag_clusters", "int", "One-Tag Clusters of its partition.", "cluster-labels-and-counts",
            _CC_DIAGRAM),
        _cc("hidden_tag_ids", "int_list", "Tags hidden in this dataset: the hidden Genre Tags and its defining Tag.",
            IDENTIFIERS_ENTRY, _CC_ROWS),
        _cc("seed_noise_floor", "float", "Its Seed-Noise Floor: the run's stored floor on a cell, its own noise "
                                         "seeds otherwise.", "adjusted-rand-index", _CC_ROWS),
        _cc("neighbour_agreement", "float", "The cell's Neighbour Agreement; empty off a cell.", "neighbour-agreement",
            _CC_ROWS),
    ],
    group="cluster_comparison",
)

CC_CLUSTERS = declare(
    "clusters.csv",
    "One row per included dataset and Cluster of its partition, One-Tag Clusters included.",
    [
        _cc("dataset", "str", "Dataset key.", IDENTIFIERS_ENTRY, _CC_DIAGRAM),
        _cc("cluster", "str", "Cluster label (C1…, per partition).", "cluster-labels-and-counts", _CC_DIAGRAM),
        _cc("n_tags", "int", "Tags in the Cluster.", "cluster-labels-and-counts", _CC_DIAGRAM),
        _cc("tag_ids", "int_list", "Its Tags' ids.", IDENTIFIERS_ENTRY, _CC_DIAGRAM),
        _cc("tags", "str_list", "Its Tags' names.", IDENTIFIERS_ENTRY, _CC_DIAGRAM),
    ],
    group="cluster_comparison",
)

CC_PAIRS = declare(
    "pairs.csv",
    "One row per dataset pair: the pair overview.",
    [
        *_CC_PAIR,
        _cc("n_comparable_tags", "int", "Comparable Tags: Tags in both networks, One-Tag Clusters included.", _CC_COVER,
            _CC_PAIRS),
        _cc("comparable_share_a", "float", "The Comparable Tags as a share of A's network Tags.", _CC_COVER, _CC_PAIRS),
        _cc("comparable_share_b", "float", "The Comparable Tags as a share of B's network Tags.", _CC_COVER, _CC_PAIRS),
        _cc("ari_comparable", "float", "ARI on the Comparable Tags with an edge in either network; empty below two.",
            _CC_ARI, _CC_PAIRS),
        _cc("n_games_in_common", "int", "Games in both Top-N Datasets after the shared Minimum Months Filter.",
            _CC_GAMES, _CC_PAIRS),
        _cc("n_matches", "int", "Cluster Matches of the pair.", _CC_MATCH, _CC_PAIRS),
    ],
    group="cluster_comparison",
)


def _cc_group_counts(side: str) -> list[Column]:
    return [_cc(f"only_{side}_{group}", "int", f"Unshared Tags of Cluster {side.upper()} {text}.", _CC_FLAGS)
            for group, text in _CC_GROUPS]


CC_MATCHES = declare(
    "matches.csv",
    "One row per Cluster Match, every one whatever the minimum, ranked by Match Jaccard within each pair.",
    [
        *_CC_MATCH_KEY,
        _cc("n_tags_a", "int", "|a|: Tags of Cluster A, set-aside Tags excluded.", _CC_MATCH),
        _cc("n_tags_b", "int", "|b|: Tags of Cluster B, set-aside Tags excluded.", _CC_MATCH),
        _cc("n_shared", "int", "n: shared Tags (in both Clusters).", _CC_MATCH),
        _cc("jaccard", "float", "Match Jaccard: n / (|a| + |b| − n).", _CC_JACC, _CC_DIAGRAM),
        _cc("share_a", "float", "Shared, % of A: n / |a|.", _CC_SHARE),
        _cc("share_b", "float", "Shared, % of B: n / |b|.", _CC_SHARE),
        _cc("comparable_jaccard", "float", "Jaccard (comparable): n / (|a′| + |b′| − n); empty when either Cluster "
                                           "has fewer than two Comparable Tags.", _CC_JACC),
        _cc("n_comparable_a", "int", "|a′|: Comparable Tags of Cluster A.", _CC_JACC),
        _cc("n_comparable_b", "int", "|b′|: Comparable Tags of Cluster B.", _CC_JACC),
        _cc("overlap_vs_expected", "float", "Overlap vs. expected: n / E (descriptive; no p-value).", _CC_OVERLAP),
        _cc("expected_overlap", "float", "E = |a′| · |b′| / N, N the pair's Comparable Tags.", _CC_OVERLAP),
        _cc("shared_tag_ids", "int_list", "The shared Tags' ids.", IDENTIFIERS_ENTRY),
        _cc("shared_tags", "str_list", "The shared Tags' names.", IDENTIFIERS_ENTRY),
        _cc("only_a_tag_ids", "int_list", "Cluster A's unshared Tags' ids (set-aside ones included).",
            IDENTIFIERS_ENTRY),
        _cc("only_a_tags", "str_list", "Cluster A's unshared Tags' names.", IDENTIFIERS_ENTRY),
        _cc("only_b_tag_ids", "int_list", "Cluster B's unshared Tags' ids (set-aside ones included).",
            IDENTIFIERS_ENTRY),
        _cc("only_b_tags", "str_list", "Cluster B's unshared Tags' names.", IDENTIFIERS_ENTRY),
        *_cc_group_counts("a"),
        *_cc_group_counts("b"),
        _cc("n_games_both_clusters", "int", "Games in both datasets that are in both Clusters.", _CC_GAMES),
        _cc("n_games_only_a", "int", "Games in both datasets that are in Cluster A only.", _CC_GAMES),
        _cc("n_games_only_b", "int", "Games in both datasets that are in Cluster B only.", _CC_GAMES),
        _cc("n_games_neither", "int", "Games in both datasets that are in neither Cluster.", _CC_GAMES),
    ],
    group="cluster_comparison",
)

CC_FLAGS = declare(
    "cluster_flags.csv",
    "One row per dataset pair, direction and Multi-Tag Cluster: each Cluster of one dataset against the other.",
    [
        *_CC_PAIR,
        _cc("dataset", "str", "The dataset whose Cluster this is (dataset_a or dataset_b).", IDENTIFIERS_ENTRY,
            _CC_DIAGRAM),
        _cc("cluster", "str", "The Multi-Tag Cluster's label in that dataset.", "cluster-labels-and-counts",
            _CC_DIAGRAM),
        _cc("n_tags", "int", "Its Tags, set-aside Tags excluded.", _CC_MATCH, _CC_DIAGRAM),
        _cc("n_matches", "int", "Its Cluster Matches in the other dataset.", _CC_MATCH, _CC_DIAGRAM),
        _cc("best_jaccard", "float", "Its best Match Jaccard; empty without a match. Apply any minimum with it.",
            _CC_JACC, _CC_DIAGRAM),
        _cc("flag", "str", "outside_network or only_one_tag_clusters, or empty: only the flags that do not depend on "
                           "the minimum.", _CC_FLAGS, _CC_DIAGRAM),
        _cc("n_in_one_tag_clusters", "int", "Its Comparable Tags that are One-Tag Clusters in the other dataset.",
            _CC_FLAGS, _CC_DIAGRAM),
        _cc("n_not_in_network", "int", "Its Tags not in the other dataset's network.", _CC_FLAGS, _CC_DIAGRAM),
    ],
    group="cluster_comparison",
)

CC_MATCH_GAMES = declare(
    "match_games.csv",
    "One row per Cluster Match and game in both Clusters, every game (the app lists the first 10).",
    [
        *_CC_MATCH_KEY,
        _cc("appid", "int", "Steam AppID.", IDENTIFIERS_ENTRY),
        _cc("name", "str", "Game name.", IDENTIFIERS_ENTRY),
        _cc("rank_a", "int", "The game's rank in dataset A.", "rank-and-ties"),
        _cc("rank_b", "int", "The game's rank in dataset B.", "rank-and-ties"),
        _cc("matched_a", "int", "Its Tags of Cluster A, as counted in A's network (out of n_tags_a).", _CC_GAMES),
        _cc("matched_b", "int", "Its Tags of Cluster B, as counted in B's network (out of n_tags_b).", _CC_GAMES),
        _cc("tag_ids", "int_list", "Its Tags from either Cluster.", IDENTIFIERS_ENTRY),
        _cc("tags", "str_list", "Their names.", IDENTIFIERS_ENTRY),
        _cc("shared_tag_ids", "int_list", "Of those, the match's shared Tags.", IDENTIFIERS_ENTRY),
    ],
    group="cluster_comparison",
)

CC_TABLES = (CC_DATASETS, CC_CLUSTERS, CC_PAIRS, CC_MATCHES, CC_FLAGS, CC_MATCH_GAMES)
