# Spec: Build management

Settled through the [Build management map](map.md) (wayfinder, 2026-11-05 to 2026-11-07). Each decision below is the current state of its ticket, with every later decision already applied. When this spec and a ticket's Answer disagree, the spec wins; [Resolved while writing this spec](#resolved-while-writing-this-spec) lists every place it adds to or sharpens a ticket. Glossary: [CONTEXT.md](../../CONTEXT.md), already updated by the map, so implementation writes no glossary entries. ADRs: [0005, the dataset seam is in memory](../../docs/adr/0005-dataset-seam-is-in-memory.md) and [0006, Build per tab in the URL](../../docs/adr/0006-build-per-tab-in-the-url.md). Constraints: ADR 0001 (App Bundles, no new runtime dependency), ADR 0002 (layout stays downstream of analysis), ADR 0003 (every new string has a bg catalogue entry, enforced by the parity test). Implementation happens on branch `build-management`.

## Goal

Three features, one effort:

1. **Build Settings.** Every setting that changes the Top-N is a Build setting the researcher can change: the datasets and their **List Size**, **Tag Depth** ("tags per game"), ordered **Exclusion Rules**, rank limits, Manual Exclusions, Exclusion Overrides, Manual Metadata Entries, Content Flags, Genre Tags and the genre-kind map, plus the report, analysis and network-default settings.
2. **Build Management.** In the app, run from the repository, the researcher creates, duplicates, deletes and switches Builds. Unsaved settings are **Build Drafts**, edited in a step dialog with a live Eligible Pool preview. Each Build keeps its own config, results and caches. A **Lightweight Snapshot** makes Builds fast (about 24 s instead of 99 s) and makes a Snapshot easy to move between machines.
3. **Data Independence.** Steam becomes one source behind an in-memory seam. An **Import** (one CSV of items with ordered attributes) gives **Import Builds** that the network, Parameter Selection, validation and the app analyse exactly like Steam Builds.

**What never changes.** A Build is immutable and deterministic (same source, settings and `build_id` give the same bytes). Every existing Build still opens, no saved export stops opening, and a Build from today's `config/` gives byte-identical datasets, reports and analysis (only `build.json` changes, with the new config shape and keys). App Bundles stay open-only. The app stays a Steam tool that can also open imported data: Steam wording is kept, with a note that Game means item and Tag means attribute.

## Facts this spec rests on

- **The seam already exists.** The network and the app read a dataset only through `BuildContext.rows()` → `games_from_rows()` (`app/loader.py:41-46`, `network/model.py:33-41`): six columns (`appid`, `name`, `rank`, `months_observed`, `tag_ids`, `tags`) plus two config facts (defining tag, Genre Tags). Steam-only fields (`is_free`, store genres, Content Flags, the Eligible Pool) are read only by `analysis/`, inside the Build stage. [Research 01](research/01-steam-assumptions.md).
- **Eight places would change Steam bytes if generalised** (research 01, "What would change a Steam result"): the `min_months` name in every `state_id`, integer tag-id order feeding seeded clustering, rank order feeding the null model, the months filter's `>=` and default 0, the `genre_tag_hidden` reason, the strict `TOP100` header, `build.json` hash identity, and the pool baselines. Every one is avoided by adapting at read time and keeping Steam values verbatim.
- **A Build reads little of its Snapshot.** Only pool, parse and games read it: the `/top` pages, every Candidate Pool app's Steam Charts page, every scored app's store page and `appdetails`, GetTagList, eight `snapshot.json` keys, and request-log outcomes. As tables: 6.3 MB gzipped, against 447 MB of files. A Build takes **99 s**, 79% of it reading raw pages; the network stage 11.6 s. [Research 02](research/02-build-inputs.md).
- **One process can switch Builds.** Callbacks already read the Build per request from the per-tab `build-path` store; only `app/server.py:29-38`, the layout's Build-dependent values (`app/layout.py:235-327`, `:463`) and the Parameter Selection stores (`app/ps_view.py:987-1031`) bind it at startup. The layout function sees no query string, so the Build goes in the path (Dash Pages). A background manager is fixed at registration, so there is one job store, which must leave `<build>/app_cache/` (an open diskcache `cache.db` blocks deleting the Build on Windows, WinError 32). Three relabel entries close over the startup Build: `brand-build`, `ps-run-one`, `ps-s-defining`. Today, Open Network State with another Build's export half-switches (latent bug). Dash 4.4.1, diskcache 5.6.3. [Research 03](research/03-switch-builds.md).
- **The Eligible Pool preview is cheap.** Loading lightweight tables takes 2.8 s (largest Import, 50,000 items: 2.4 s). A warm preview (manual-list validation, Manual Metadata, every rule, Content Flags, five datasets ranked, games entering Overall) takes **0.34 s on Steam and 1.3 s on the largest Import**, matching the raw records exactly. Any one edit costs the same; incremental reuse saves under 0.2 s on Steam. [Research 17](research/17-eligible-pool-timing.md).
- **Code facts:** `TOP_N = 100` (`build/datasets.py:13`); `DATASET_KEYS` fixes five datasets (`export/schema.py:168`, enforced at `build/core.py:127`, also read by `build/assemble.py:27` and `collect/run.py:533`); `read_typed_csv` refuses any header but `TOP100`'s 17 columns (`export/writer.py:136-140`); `build_id` is `<UTC timestamp>-<build_config_hash[:8]>`; `write_build` points both `latest` pointers at the Build just written; Open Network State matches a Build by `build_id` plus the `build.json` hash (`app/export.py:185-200`); `SCHEMA_VERSION = 5`.
- **Settings inventory:** [Build settings by layer](research/00-build-settings-inventory.md).
- **Prototypes, reference only:** [the Build menu](prototypes/12-build-menu/PROTOTYPE-build-menu.html) (variant D), [the User Guide outline](prototypes/15-user-guide-outline/OUTLINE.md), [the timing script](prototypes/17-eligible-pool-timing/measure.py) (a working loader and preview over stand-in tables).

## Decisions

### Scope

- **In:** the config shape and Build stage for every Top-N setting; the dataset seam and Import Builds; Imports; Lightweight Snapshots; Build identity, drafts and lifecycle; per-tab Builds in the URL; the Build menu; the export schema by Build kind; Bundles of named Builds; the User Guide (en and bg), the Running Guide and the releasing guide.
- **Out:** see [Out of scope](#out-of-scope).
- **No new runtime dependency** (ADR 0001). Dash Pages is part of Dash.

### Datasets, List Size and Tag Depth

Tickets: [tags per game and list size](issues/05-tags-per-game-and-list-size.md), [grid scaling](issues/11-grid-and-defaults-scaling.md), [Top-N glossary](issues/14-top-n-glossary.md).

- **The dataset set is a Build setting.** Datasets can be added, removed and relabelled. Each has a `key` (`[a-z0-9_]`, unique), a `label` (required), an optional defining tag (unique within the Build) and a `list_size`. Exactly one dataset has no defining tag; it is keyed `overall` and listed first. `DATASET_KEYS` goes: every reader takes the Build's datasets in config order (from `build.json`). The default `config/datasets.toml` is unchanged.
- **List Size** is an integer ≥ 10, no maximum, per dataset, default 100 (`list_size` absent reads as 100). `TOP_N` goes. A Top-N always holds exactly N: an Eligible Pool smaller than N fails the Build, naming the dataset and its pool size; in a test Build it stays a warning, as today. Ties at the cutoff are reported as today.
- **Tag Depth** (UI: "tags per game") is one value per Build, `tag_depth` in `datasets.toml`: an integer ≥ 2 or the literal `all`, stored as `all`, never as a number.
  - **Steam:** 2–20, 20 means the same as all; default 20; above 20 is refused; a config or `build.json` without it reads as 20, so no Steam byte and no `build_id` moves.
  - **Import:** 2 up to the longest list, or `all` (the default); no cap.
- **One meaning of "has".** A game has a tag only when the tag is among the first K tags of its displayed list. It applies everywhere "has" is asked: Tag-Specific Dataset membership, the Eligible Pool and its baselines (`tag_frequency`, `genre_frequency`), the network (nodes, edges, Genre Tag hiding) and the feature analysis (frequency, combinations, associations, `median_position`). One helper does the cut; the Build-stage analysis and the dataset reader both use it.
- **Exclusions and Content Flags read the full displayed list.** `global_rank_limit` and per-tag rank limits count positions in that list, ignoring Tag Depth. The "no tags" rule is unchanged (no tags on the store page). Manual Metadata tags-only entries are treated like a store list. `impact_removals.csv` may note an exclusion caused by a tag beyond Tag Depth (informational).
- **Files keep full lists.** Build files store each game's full displayed list; the Build records K; the reader cuts. The inspector shows tags beyond K marked "not counted (beyond tags per game)" (bg entry).
- **Parameter Grid and network defaults do not scale.** `g_range`, `s_range`, the network default g and s, `min_support`, the Pair Constraints, R, S and `resolution_sweep` stay absolute game counts, one value per Build, edited in the menu's network step. The menu warns per dataset (naming it and its N, bg entries) when the grid's largest g exceeds N, the default g or s exceeds N, or `min_support` exceeds N; saving stays allowed. **A grid with no pairs** (s_low > g_high) is refused by the menu and the config reader (bg error). Network State sliders keep 1–40 (g) and 1–30 (s), raised only to the Build's own largest configured value.
- **Build-output wording.** Report and schema text writes the actual number: "Top 100" when every dataset in scope has N = 100, "Top-N" when List Sizes differ; counts such as "the five published datasets" follow the same rule. Default Steam Builds keep identical bytes. Docstrings and comments say Top-N. "Top-N Dataset" as a modifier, "the Top N" as a noun.

### Named Exclusion Rules

Ticket: [named exclusion rules](issues/06-named-exclusion-rules.md).

- **A named rule** is one ordered `[[rule]]` entry in `exclusions.toml`:
  - `name`: code written to `exclusions.csv`, the impact reports and overrides; `[a-z0-9_]`.
  - `label`: menu wording.
  - `tags`: `{ id, name }` entries, each with an optional `rank_limit` (1–20).
  - `name_only`: name-only matches.
  - Steam only: `content_descriptor_ids` and `adult_only_notice` (bool; today's hard-coded Adult Only signal becomes this setting).
- **Defaults** keep today's codes and behaviour: `adult_content` (descriptor 3, Hentai, `adult_only_notice = true`), `software_tag` (9 tags; name-only GameMaker, RPGMaker, Web Publishing), `dating_sim_tag` (Dating Sim).
- **Order.** Fixed rules run first: `store_data_unavailable → app_type → no_tags`; named rules next, in file order; `manual` last. Order decides `primary_reason`; the menu can reorder named rules.
- **Rank limits.** `global_rank_limit` stays (1–20). `per_tag_rank_limit` is removed; the per-tag limit lives on the tag entry inside its rule, so a tag can have different limits in different rules.
- **Validation (the Build fails):** duplicate rule names; a name equal to a fixed rule code; a rule with no signal; a limit outside 1–20; an override naming a rule that does not exist. A tag id missing from GetTagList stays a warning for Steam. A tag may appear in two rules; both match. Zero named rules is a valid Build.
- **Overrides** target `app_type`, `no_tags` or any named rule; never `store_data_unavailable` (use a Manual Metadata Entry) or `manual` (remove the entry). Renaming a rule in the menu renames its overrides; deleting one asks to drop them.
- **Content Flags** stay a separate list with the same `name`/`label`/`tags`/`name_only` shape and editor; no descriptor ids, no rank limit (anywhere in the list), never filter.
- **Old shape.** One config reader accepts today's shape (`adult_content`/`software_tag`/`dating_sim_tag` tables, `per_tag_rank_limit`, `content_flags.<code>`) and converts it to named rules. Old `build.json` files are never rewritten; only Duplicate and a rebuild read them through the converter. A Build from the converted default config gives byte-identical datasets and reports.
- **Reports.** `impact_adult_signals.csv` is written for the rule named `adult_content`, reading its descriptor ids and tags; column names unchanged, descriptions say "the rule's descriptor ids / tags (default 3 / Hentai)"; no such rule writes headers only. In `impact_unexcluded.csv`, descriptors 1 and 4 and software store genres stay fixed Steam diagnostics; Content Flags feed it as `content_flag:<code>`.
- **Imports** get named rules over attributes (`attributes` + `rank_limit`, no Steam fields), Manual Exclusions and Overrides keyed by item id, no fixed Steam rules, and Content Flags as attribute lists.

### The dataset seam

Ticket: [generic dataset contract](issues/04-generic-dataset-contract.md); ADR 0005.

- **`read_dataset(build, key) -> Dataset`** is the one reader. A `Dataset` holds the items in rank order (each: integer id, name, rank, ordered attribute ids and names cut to Tag Depth, the full list for the inspector, the filter value, extra numeric fields), the defining attribute, the Genre Tags, the Tag Depth, and the filter field (name and range, or none). Every consumer uses it: the app (`BuildContext.rows/games/context`, the slider range), the network, Parameter Selection and validation.
- **Two adapters, chosen by `build.json` `source`.** No `source` means Steam, so old Builds need nothing. The Steam adapter is today's code: `top100_<key>.csv`, the strict 17-column header, `months_observed` as the filter value. The import adapter reads `topn_<key>.csv` and `item_fields.csv`.
- **Items.** Unique positive integer id (`appid` for Steam), a name, a rank and at least one attribute. The reader reads `rank` and never recomputes it.
- **Attributes.** Integer ids in a fixed order, each item's list in its order. Steam keeps its tag ids.
- **Filter field.** At most one per dataset, fixed by the Build. Values may be decimals; the test is `>=`, off at the field's minimum. The slider is labelled with the field's name and takes its range from the data (Steam: 0–60 months, as today). With no filter field the slider is hidden and every item is kept. The Network State key keeps the field name `min_months`, so no Steam `state_id`, cache or saved export moves.
- **Defining attribute and Genre Tags** are optional. Same behaviour as today, including the `genre_tag_hidden` reason. With neither set, nothing is hidden by default and their toggles don't appear.
- **Steam-only facts stay out of the contract:** store genres, `is_free`, Content Flags, release dates, `mean_monthly_players` as a named column, `metadata_source`, `top_listing_rank`, `monthly_players.csv`, the Steam Build reports. The inspector's "AppID" header reads "ID" for Import Builds (bg entry).

### Lightweight Snapshots

Ticket: [lightweight Snapshot](issues/08-lightweight-snapshot.md).

- **Content:** parsed tables, not pages: listing (every row), Steam Charts outcomes, **all** month rows up to the window's end, store apps, store tags (with display position), store genres, tag vocabulary, the eight `snapshot.json` keys a Build reads, the request-log outcome of every key the Build looks up (including "missing"), the log url/detail/status/timestamp of skipped apps, and SteamDB pages' fields and log `batch` when present. About 6.3 MB.
- **Two forms, one Snapshot**, named **raw** and **lightweight** (never "full"). Same `snapshot_id`; their Builds share `builds/<snapshot_id>/`. `build.json` records `snapshot_form: raw | lightweight` and the extract version.
- **Default source.** When both forms are present a Build reads the lightweight one; `steamstudy build --from-raw` forces the raw pages.
- **Guarantee:** a Build from the lightweight form is byte-identical to one from the raw form, given the same settings and `build_id`, except `snapshot_form`. Tested by (1) an automated test on the fixture Snapshot (lighten, build both with a fixed `build_id`, compare every file) and (2) `steamstudy snapshot verify-light <id>` on a real Snapshot.
- **Staleness.** An **extract version** is bumped whenever a parser or the extracted field set changes. Old version: with the raw form present, the Build reads raw and warns to lighten again; without it, the Build is refused, naming the gap. The lightweight form records the raw form's repair count; if it is behind and the raw form is present, the lightweight form is stale and not used.
- **Made from a closed Snapshot; never changed.** Repair, collect resume and SteamDB fetches act on the raw form only. Made by `steamstudy snapshot lighten [<snapshot_id>]` (default: the latest closed Snapshot), and automatically when collect closes a Snapshot and after every repair (about 80 s).
- **File:** `snapshots/<snapshot_id>.light.zip`: the CSV tables (deflate) and `meta.json` (format and extract version, the eight Snapshot keys, the repair count, each table's sha256, checked on open). Written deterministically (fixed member order and timestamps). Never committed.

### Imports

Ticket: [dataset import](issues/09-dataset-import.md).

- **An Import** is the raw, fixed source that plays the Snapshot's role for imported data. One Import can define several Top-N Datasets.
- **File: one wide CSV,** `id,name,attributes[,score][,numeric fields…]`; `attributes` holds names separated by `;`, in order. An optional `attributes.csv` (`id,name`) supplies attribute ids.
- **Text rules.** UTF-8 only (BOM stripped), comma delimiter, RFC 4180 quoting, header required, `.` decimal point. Names trimmed and NFC-normalised. Attribute names case-sensitive; names differing only by case warn. Other encodings and delimiters are refused ("save as CSV UTF-8"); nothing is sniffed.
- **Header.** `id`, `name`, `attributes` required; `score` optional and reserved; case-sensitive; duplicates refused. The filter field is named at import (`--filter <column>` or a menu dropdown) and must be filled for every item. Every other column is an extra numeric field (empty cells allowed). With a `score` column, every item needs a score.
- **Ids.** Integer item ids; text ids refused. With `attributes.csv`: unique positive integer ids and unique names covering every attribute used (mixing supplied and numbered ids is refused); unused rows warn and are dropped. Without it: attributes numbered 1…k in code-point name order.
- **Rank.** Score descending, ties by file order; without a score, file order.
- **Validation is all-or-nothing**, every problem collected in one pass.
  - **Errors:** missing required column; bad or duplicate id; empty name; empty attribute list; empty attribute between `;`s; attribute repeated in one item; bad or empty score, filter value or extra field (NaN and ±inf are bad); `attributes.csv` problems; fewer than 10 items.
  - **Warnings:** case-only name clashes; duplicate item names; unused `attributes.csv` rows; more than 50,000 items or 5,000 distinct attributes. No hard size limit.
  - **Report:** `imports/failed/<attempt_id>/errors.csv` (`file, row, column, code, value, message`, spreadsheet row numbers) plus a copy of the input. The CLI prints counts per code and the first 20 rows. The menu shows the table, with a bg message per code. Warnings are kept in `import.json`.
- **Storage.** `imports/<import_id>/`, `import_id = <UTC timestamp>-<slug of file name>`: the original file verbatim, its sha256, the normalised tables (items, ordered item attributes, attribute ids and how they were assigned) and `import.json`. Never changed: a corrected file is a new Import; a byte-identical re-import is refused with a pointer to the existing one. Never committed.
- **Made by** `steamstudy import <file> [--filter <column>]` or the Build-menu Import button (file picker); same validation. Making an Import is separate from making its first Build.

### Import Builds

Tickets: [dataset import](issues/09-dataset-import.md), [export schema](issues/13-export-schema.md).

- **Location:** `builds/<import_id>/<build_id>/`, the same parent layout as Snapshots.
- **Settings that apply:** datasets by defining attribute, List Size, Tag Depth, named attribute rules, Manual Exclusions and Overrides keyed by item id, Content Flags as attribute lists, Genre Tags, all report, analysis and network-default settings. **Hidden or absent:** app types, content descriptor ids, the Adult Only notice, Manual Metadata (a correction is a new Import), the Observation Window, `collection.toml`, the fixed Steam rules, the genre-kind map.
- **Config files:** `datasets`, `exclusions`, `exclusion_overrides`, `manual_exclusions`, `genres` (no `genre_kind`), `analysis`, `network`. The source marker picks the required set, so the app's Steam Charts stub and the eight-file demand go for Import Builds.
- **Naming attributes in config.** Numbered Imports name attributes by `name`; Imports with `attributes.csv` use `{ id, name }`, and both must match. An attribute missing from the Import's vocabulary **fails the Build**.
- **The Eligible Pool** is the whole Import minus its Exclusions (for a Tag-Specific Dataset: those that have its defining attribute). The Top-N Dataset is its N highest-ranked items.
- **Import defaults** (the tree root and `steamstudy build --import`): one dataset `overall`, List Size min(100, item count), Tag Depth `all`, no named rules, Content Flags or Genre Tags, empty manual lists, and `analysis` and `network` copied from `config/`.
- **CLI:** `steamstudy build --import <import_id>` builds the Import defaults, or the reduced config set in `--config <dir>` when that holds one.
- **Feature analysis:** generic sections only (tag frequency, combinations, associations, the pool baseline, Content Flags). Dropped: the genre, free-to-play and months sections, the "Puzzle" note and the archived Steamworks categories.

### Export schema

Ticket: [export schema](issues/13-export-schema.md).

- **Steam keeps `top100_<key>.csv`** in every Steam Build, whatever its List Size; the description says the name dates from when N was always 100.
- **Import dataset file: `datasets/topn_<key>.csv`,** strict header `dataset, rank, id, name, score, filter_value, tag_ids, tags`. `score` empty without a score, `filter_value` empty without a filter field. Full ordered tag lists.
- **Extra fields: `datasets/item_fields.csv`** (`id, field, value`), for items in any Top-N Dataset, no row for an empty cell.
- **`would_be_rank_<dataset>`** is a templated column, expanded once per dataset in config order, for both kinds. Today's five Steam datasets give unchanged columns and bytes.
- **Import variant rule.** Same file name as the Steam counterpart; `appid` → `id`; `tag_id`, `tag`, `tag_ids`, `tags` stay; `mean_monthly_players` → `score`; Steam-only columns dropped (`archived_category`, `months_observed`, `release_month`, `is_free`, genres and similar). It covers datasets, reports, analysis tables, network tables and app exports.
- **Registry keyed by Build kind.** `FileSchema` gains `kind` (`steam` or `import`); the key becomes `kind/group/name`. A file that does not differ is declared once for both; Import variants are derived from the Steam declarations by the rule above. `export.json` and `analysis.json` embed only their kind's columns. Writer validation stays strict for both.
- **`SCHEMA_VERSION` 5 → 6,** once for the whole effort. Steam `export.json` and `analysis.json` change only in that number and description text ("Every dataset stacked").
- **Import `build.json`:** `source: "import"`, `import_id`, `import_sha256` (no `snapshot_id`), `filter_field` (name or null), `score_present`, the extra field names, `name`, `description`, `parent_build_id`; none of `collection_date`, `observation_window`, `store_country`, `taglist_version_hash`, `manual_metadata_entries`, `source_substitutions`.
- **Network State exports** of Import Builds are unchanged in shape (`dataset` column, zip name `steamstudy_<dataset>_<state_id>_<ts>.zip`, `state_key` with `min_months`, embedded `build_json`). The not-found message names the Import (bg entry). Saved Steam exports still open, because old `build.json` files are never rewritten.
- **Files an Import Build writes:**
  - `datasets/`: `build.json`, `topn_<key>.csv`, `item_fields.csv`.
  - `reports/`: `exclusions.csv`, `impact_removals.csv`, `impact_near_misses.csv`; `completeness.csv` with only `exclusions_overlapping`, `exclusions_primary`, `depth_check` and a new `import` section (items, attributes, warnings); `ties.csv` only with a score; `reports.html` showing the Import's warnings.
  - `analysis/`: `tag_frequency`, `combinations`, `associations`, `content_flags`, `resolution_sweep`, every `network_*` table, `removal_sensitivity`, `analysis.json`, `report.html`.
  - Not written: `parse_errors`, `placeholder_rows`, `tag_vocabulary`, `release_month_check`, `impact_adult_signals`, `impact_unexcluded`, `manual_metadata`, `steamdb_crosscheck`, `skipped_apps`, `genre_frequency`, `monthly_players`.

### Build identity and lifecycle

Ticket: [Build identity](issues/07-build-identity-and-lifecycle.md).

- **Name.** Required, stored in `build.json`, fixed at save, in neither `build_id` nor the config hash. Unique within its Snapshot or Import, ignoring case, across Builds and drafts; a clash is refused when the draft is saved. Shown beside the id wherever the id is shown. CLI Builds default to their `build_id`; `steamstudy build --name <name>` sets one, with the same clash check.
- **Description.** Required for a menu Build: why it exists. Stored in `build.json` as that Build's own changelog entry, after the entries inherited from its starting point.
- **Parent.** A duplicated Build records `parent_build_id` as `<source_id>/<build_id>`, shown "from <parent name>", or "from a deleted Build". Information only.
- **Duplicate onto another Snapshot.** Duplicate picks the Snapshot (default: the parent's). Settings that don't fit fail that Build through today's validation. Import Builds duplicate within their Import.
- **Build Drafts.** Complete settings (never a diff), copied when started from defaults or from a Build, with name, description and parent. Saved automatically, survive closing the app, any number per source, at `builds/<source_id>/drafts/<name-slug>.json` in the shape of `build.json`'s `config` block plus name, description and parent. A successful Build uses its draft up; a failed one keeps it; drafts are discarded explicitly.
- **`config/`** stays the repository's hand-edited defaults and the CLI's input. The menu never writes it.
- **Identical settings** (same source and config hash as an existing Build) are allowed with a warning that names the existing Build and says whether the software versions differ.
- **Delete** removes the Build folder, cache included, cancelling any job running on that Build first. It moves `latest`: the per-source pointer to the newest remaining Build of that source (by `build_id` timestamp), the root pointer to the newest of any source; a pointer with no Build left is removed. The confirmation is informational: sizes, zips in `bundles/` whose name contains the `build_id` (they keep working), that Network States exported from it will no longer open here, where `latest` moves, and the Builds and drafts that lose their parent. There is no protected flag.
- **Deleting the open Build** (the tab's own Build) is refused: "switch to another Build first". Deleting a Build another tab has open is allowed.
- **Failed runs are not Builds:** no folder, no list entry. The failure shows on its draft: the parse-error count with a link to the `failed/` CSV, or the causal word and its sentence. That `failed/` file is deleted when the draft is built or discarded. The CLI's failure handling is unchanged.
- **A successful menu Build** becomes `latest`, as `write_build` does today.

### Switching Builds and caches

Tickets: [switch in one process](issues/03-switch-builds-in-one-process.md), [switching and cache separation](issues/10-switching-and-cache-separation.md); ADR 0006.

- **The Build is in the tab's URL:** `/build/<source_id>/<build_id>` through Dash Pages. The server resolves the id under the builds root and never accepts a path from the browser. `/` redirects to the startup Build (`--build`, else root `latest`). A switch navigates and rebuilds the page from the layout; every startup binding (`server.py`, layout values, Parameter Selection stores, the three relabel entries) is resolved from the tab's Build instead.
- **Open Network State** with another Build's export navigates to that Build's URL and reopens the export there (fixes today's half-switch).
- **Kept across a switch:** the Interface Language, the open mode, and the dataset when the new Build has one with the same key (else its first). Network State settings reset to the new Build's network defaults.
- **Caches stay per Build** in `<build>/app_cache/`; nothing is reused across Builds. Clear app cache (button and `--clear-cache`) clears the open Build only.
- **Running jobs on a switch:** a confirmation ("N running jobs will be cancelled; finished parts stay cached"), then that tab's Removal Sensitivity and Parameter Selection jobs are cancelled.
- **A Build run from a draft** is a server-wide job, one at a time per app process, in a background process, shown on its draft. Switching or closing the tab never cancels it.
- **Parameter Selection** for a new Build runs on demand; nothing runs at creation.
- **Job store:** one temporary folder per app process under the OS temp directory, removed at exit; never inside a Build or a bundle; never shared by two processes.
- **Missing Build:** a URL whose Build doesn't exist shows "This Build no longer exists" with a link to the latest Build.

### The Build menu

Tickets: [Build menu](issues/12-build-menu.md) (prototype variant D), [Eligible Pool preview](issues/18-eligible-pool-preview.md).

- **Repository only.** The menu exists only where the app runs from the repository (a Snapshot or Import is needed to create a Build). App Bundles get the switching tree only.
- **The header's Build name is a dropdown lineage tree,** one per Snapshot or Import. The root is `config/` for a Snapshot and "Import defaults" for an Import. Builds sit under their parent, drafts under the Build they started from; a Build whose parent was deleted moves to the root, "from a deleted Build".
  - Build rows: name, chips (✓ open in this tab, latest, test), date, Top-N summary (List Sizes, Tag Depth). Click switches.
  - Draft rows: status (draft / running % / failed), how many settings changed, last saved. Click opens its dialog.
  - Root row: click starts a draft from the defaults.
  - Hover actions: Duplicate and Delete on Build rows, Discard on draft rows. Below the tree: Duplicate the open Build, Import data…, Manage Builds….
  - Each Snapshot shows which forms it has (raw, lightweight).
- **Manage Builds…** is a dialog with the same tree plus folder and app-cache sizes.
- **Duplicate** asks which Snapshot to use (default: the parent's), then opens the new draft's dialog.
- **A draft opens in a full-screen dialog of steps.** A step's marker is green when it has changes, red when it needs a fix. The draft saves automatically; Close keeps it.
  1. **Start:** name, description, started from, Snapshot or Import, last failure. For a raw-only Snapshot, **Make lightweight Snapshot** (a server job).
  2. **Changes the Top-N:** datasets (key, label, defining tag, List Size, Eligible Pool), Tag Depth, `global_rank_limit`, app types (Steam), ordered named rules between the fixed rules (shown, not editable).
  3. **Curation:** Manual Exclusions, Exclusion Overrides and (Steam) Manual Metadata Entries, each needing a reason and evidence and validated as the Build validates them today. Would-be Overall ranks of excluded games act as a shortcut for adding an Override.
  4. **Reports and analysis:** Content Flags, Genre Tags, the genre-kind map (Steam), `analysis.toml`, `resolution_sweep`.
  5. **Network defaults:** `network.toml`, including the Parameter Selection settings and Pair Constraints, with the grid-scaling warnings.
  6. **Review:** every changed setting (source value struck through, draft value beside it, Top-N changes badged), each dataset's List Size against its Eligible Pool, the games that would enter and leave Overall, the identical-settings warning, and the problems still to fix. **Build only from Review.**
- **The Eligible Pool preview:**
  - **When:** recomputed about 0.5 s after the last edit on the Top-N and Curation steps, and on entering Review.
  - **Where:** in the app process, as a plain callback, never a server job. The source's tables are loaded once, the first time a draft dialog opens for that source ("Loading Snapshot…", about 2.8 s): a Snapshot's lightweight form, or an Import's normalised tables. At most one loaded source per process, swapped when a dialog for another source opens, dropped when the source changes (repair, new lighten). The preview calls the Build's own exclusion and ranking code on those records; there is no second implementation. Ranking is kept apart from slicing, so a List Size edit is a re-slice. No incremental reuse.
  - **While computing:** the last numbers stay, dimmed, with a small spinner; a newer edit supersedes a recompute in flight.
  - **Cannot compute** (invalid rule, override on an unknown rule, unknown attribute, missing Snapshot or Import): each number reads "—" with the reason, linking to the step marked red. A pool smaller than its List Size is a red problem on the Top-N step and in Review ("Overall: 87 eligible, List Size 100").
  - **Raw-only Snapshot:** no preview; the numbers read "Not previewed: this Snapshot has no lightweight form". The draft can still be built from raw (about 99 s); Review says the pools are not previewed and Build stays on.
  - **Never stale at Build:** Review's preview is keyed by a hash of the settings plus the source's id and extract version (Imports: `import_sha256`). **Build** stays off until Review shows a preview for the current key. The Build run recomputes everything and is the authority; a test (preview against Build on the fixture, plus `verify-light`) keeps them identical.
  - **Entering and leaving Overall** compare with the draft's source Build; a draft from defaults compares with the source's `latest` Build; with no Build to compare, the line is left out.
- **A running Build** is a strip under the header in every mode: stage, seconds against the estimate (~24 s lightweight, ~99 s raw), a bar. When it finishes, the strip offers "Open it in this tab"; when it fails, "Open the draft", and the dialog shows the failure.
- **Import data…** opens a file picker, a filter-column dropdown, and on failure the errors table with a bg message per code. Steam-only settings are hidden in an Import's draft.
- **Delete, switch and missing Builds** follow [Build identity and lifecycle](#build-identity-and-lifecycle) and [Switching Builds and caches](#switching-builds-and-caches), as drawn in the prototype.
- **bg:** every menu string goes through the catalogue. Terms: Build = компилация, Snapshot = моментна снимка, Build Draft = чернова на компилация (see [Documentation](#documentation) for the rest).

### Bundles

Ticket: [bundles and in-app Builds](issues/16-bundles-and-in-app-builds.md).

- **Explicit Builds.** `steamstudy bundle` needs at least one `--build`; `latest` is no longer implicit. The first named opens by default (the Bundle's `latest` pointers name it). `--build latest` stays a shorthand.
- **Naming a Build.** `--build` accepts a `build_id`, `<source_id>/<build_id>`, a name, or `<source_id>/<name>` (case-insensitive). A name matching Builds on more than one source is refused, listing the matches.
- **Import Builds** bundle like Steam ones (Parameter Selection runs, path-length check applies); `imports/` is not shipped.
- **Names.** The zip name is unchanged (`tag-network-<build_id>-<targets>.zip`, after the default Build). Each `bundle.json` Build entry gains name, description and `parent_build_id`, plus the parent's name looked up at make time. `READ ME FIRST.txt` lists each name beside its id.
- **Lineage in the bundled tree.** A top level per source (no `config/` root, no drafts). A Build whose parent is in the Bundle nests under it; otherwise a top-level row "from <parent name> (not in this Bundle)", or "from a deleted Build". The tree is hidden when a Bundle ships one Build.
- **Checks.** A test-Snapshot Build is refused without `--allow-test`. Two Builds with the same source and config hash warn, naming both. Lightweight sources and failed drafts need no check.

### Documentation

Tickets: [Top-N glossary](issues/14-top-n-glossary.md) (already written into `CONTEXT.md`), [User Guide outline](issues/15-user-guide-outline.md) (per-chapter detail in [the outline](prototypes/15-user-guide-outline/OUTLINE.md), every point accepted).

- **Two new chapters, appended:** `07-making-builds.md` (procedural, no **In short** blocks: the Build tree, Start a draft, one section per draft step, A running Build, Manage and delete Builds, Raw and lightweight Snapshots) and `08-imported-data.md` (reading note; What an Import is; The Import file with a five-row example; Making an Import; When an Import is refused: a code → meaning → what to do table for every error and warning code; What changes in an Import Build). Nothing renumbered. `README.md` groups "Reading results" (0–6) and "Making Builds" (7–8).
- **Help:** each draft step's `?` opens its chapter-7 section; each section is a help anchor with a `test_guide` case. Hover help on a setting opens its chapter-3 entry. The Review section says Build stays off until the preview matches the current settings, and what "Not previewed" means.
- **Top-N wording:** generic text says Top-N; defaults are "the default List Size of 100"; worked examples keep 100; `top100_<dataset>.csv` keeps its name with a history sentence; the chapter-5 methods paragraph mirrors the report template with a `‹top_n›` placeholder.
- **Chapter 3:** List Size and Tags per game (Tag Depth) rows and entries with **In short** (Tag Depth defines "has"); Import sentences only in Rank and ties, Eligible Pool baseline and Tags per game; a `*Steam Builds only.*` line under Monthly Avg. Players, Mean Monthly Players, Months Observed, Release Month, Release-month gap, Placeholder Rows, Store metadata, Listing rank and the depth check, Archived tag category, Genre frequency; the grid-scaling caveat joins Automatic Parameter Selection ("the default Parameter Grid and network defaults were chosen for a Top-100 at 20 tags per game; for other List Sizes or tags per game, review them in the Build menu").
- **Chapters 1, 2, 4, 5, 6:** 1 gains *Switch Builds*; 2 a Build row in the control reference and the Import filter-slider sentence; 4 *Import Builds*, *Import folder* and the new `build.json` keys; 5 citations quote the Build's name beside the `state_id`, plus *Cite an Import Build* (`import_id` + `import_sha256`); 6 an *Imported data* section and a caveat to compare states only at the same Tag Depth and List Size.
- **Appendix B:** the Steam table stays, followed by a generated *Import Builds* section (new or renamed columns, one line of absent Steam columns, "every other column is as above"; `would_be_rank_<dataset>` one row). The bg appendix is generated the same way.
- **bg** is translated in the same change. Terms for `docs/i18n/bg-terms.md`: Top-N Dataset = набор Топ-N, List Size = размер на списъка, Tag Depth / tags per game = дълбочина на таговете / тагове на игра, Import = импорт (pl. импорти; _avoid_ внос), Import Build = компилация от импорт, raw / lightweight Snapshot = сурова / олекотена моментна снимка (_avoid_ пълна), item / attribute = елемент / атрибут. Catalogue strings containing "Top-100" change key and bg value together.
- **Running Guide (English only):** *Build* says datasets and List Sizes come from config; new *Lightweight Snapshots* (after *Collect*) and *Import* (after *Build*) sections; *Folder layouts* gains `imports/`, Import Builds, drafts, the lightweight zip and the job store's move; *The app* links chapter 7.
- **Releasing guide:** the bundle command gains `--build`, names, `--allow-test`, and the lineage shown in a Bundle.

### Resolved while writing this spec

Choices the tickets left implicit, settled with the researcher on 2026-11-07 or made here:

- **The dataset set is editable** (with the researcher): keys `[a-z0-9_]`, unique; exactly one dataset without a defining tag, keyed `overall` and first; defining tags unique; `DATASET_KEYS` goes, and the assembler and the SteamDB cross-check read the Build's own datasets.
- **Import defaults** (with the researcher): the tree root for an Import and what `steamstudy build --import` builds; see [Import Builds](#import-builds).
- **Drafts are menu-only** (with the researcher): no CLI command builds a draft; the CLI gains only `--name`.
- **Entering and leaving Overall** (with the researcher) compare with the draft's source Build, else the source's `latest`, else nothing.
- **Test Builds** keep today's warning for a pool smaller than its List Size.
- **The Import preview** loads the Import's normalised tables (an Import is always "lightweight").
- **`list_size` and `tag_depth`** live in `datasets.toml` (per dataset and per Build), absent meaning 100 and 20 (Steam) or `all` (Import).
- **`source_id`** names a Snapshot id or an Import id wherever the layout `builds/<source_id>/<build_id>/` applies.
- **The Start step's Make lightweight Snapshot** button comes from [Eligible Pool preview](issues/18-eligible-pool-preview.md) and supersedes "no button to make one" in [lightweight Snapshot](issues/08-lightweight-snapshot.md).
- **The User Guide's Review wording**, left open by [the outline](issues/15-user-guide-outline.md), follows [Eligible Pool preview](issues/18-eligible-pool-preview.md).

## Out of scope

- App Bundles creating Builds: the Build menu is repository-only.
- Weighted attributes, several attribute kinds on one item, and links between items.
- Rewriting the glossary, the User Guide and the reports in generic (non-Steam) terms.
- Collecting any non-Steam data: Imports arrive as files.
- Cross-Build cache reuse, incremental preview reuse, and scaling the Parameter Grid with List Size (each can be added later without breaking anything).

## Issues

Status `ready-for-agent`. Numbering continues after the map's decision tickets (01–18). Each issue's `Blocked by` line names its prerequisites. **19, 23 and 25** can start at once. Two issues that edit the same files never run unblocked side by side: 19 → 20 → 21/22/24 share the config and Build-stage code, and the app issues run 27 → 28 → 29 → 30/31.

- [19: Named Exclusion Rules](issues/19-named-exclusion-rules.md)
- [20: Datasets, List Size and Tag Depth in the Build](issues/20-datasets-list-size-tag-depth.md)
- [21: The dataset seam: `read_dataset` and the Steam adapter](issues/21-dataset-seam.md)
- [22: Export schema by Build kind](issues/22-export-schema-by-kind.md)
- [23: Lightweight Snapshots](issues/23-lightweight-snapshots.md)
- [24: Build identity, drafts and lifecycle (Dash-free)](issues/24-build-identity-and-drafts.md)
- [25: Imports](issues/25-imports.md)
- [26: Import Builds](issues/26-import-builds.md)
- [27: Build per tab in the URL](issues/27-build-per-tab-url.md)
- [28: Build tree, Manage Builds and Delete](issues/28-build-tree-and-manage.md)
- [29: Draft dialog shell, Start, Review and the Build run](issues/29-draft-dialog-and-build-run.md)
- [30: Top-N and Curation steps](issues/30-top-n-and-curation-steps.md)
- [31: Reports, Network steps and grid warnings](issues/31-reports-and-network-steps.md)
- [32: Eligible Pool preview](issues/32-eligible-pool-preview.md)
- [33: Import in the Build menu](issues/33-import-in-the-menu.md)
- [34: Bundles of named Builds](issues/34-bundles-of-named-builds.md)
- [35: User Guide chapters 1–6, appendix B and bg terms](issues/35-user-guide-edits.md)
- [36: User Guide chapters 7 and 8 and help anchors](issues/36-user-guide-chapters-7-8.md)
- [37: Running Guide and releasing guide](issues/37-running-and-releasing-guides.md)
