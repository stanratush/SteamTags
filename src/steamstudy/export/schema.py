"""The single declaration of every exported file and column.

Every CSV the package writes is declared here with its columns, types and one-line descriptions, and
every writer validates against these declarations (`steamstudy.export.writer`). `export.json` and
`analysis.json` embed a `columns` block generated from here.

Adding, removing or renaming a column bumps `SCHEMA_VERSION` (separate from the Network State
`key_version`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

SCHEMA_VERSION = 1

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
        if schema.name in self.files:
            raise ValueError(f"file {schema.name} declared twice")
        self.files[schema.name] = schema
        return schema

    def __getitem__(self, name: str) -> FileSchema:
        return self.files[name]

    def __iter__(self):
        return iter(self.files.values())


REGISTRY = Registry()


def declare(name: str, description: str, columns: list[Column] | tuple[Column, ...], group: str = "") -> FileSchema:
    return REGISTRY.declare(FileSchema(name, description, tuple(columns), group))


def file(name: str) -> FileSchema:
    return REGISTRY[name]


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
