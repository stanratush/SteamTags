# Steam assumptions downstream of the Build

Where do `network/`, `analysis/`, `app/`, `export/`, `i18n/` and `bundle/` read something only Steam has? As of commit `65847aa` (2026-11-06). Paths are relative to `src/steamstudy/`. Found by reading the loader, the model and the analysis stage, then grepping every module for the Steam field names, file names, config facts, wording and URLs that the ticket lists.

Each finding is marked **data** (needs a generic field), **config** (needs a generic setting) or **wording** (kept under the Steam-tool decision).

## Short answer

- **The seam already exists in practice.** Everything in `network/` and the app reads one dataset through `BuildContext.rows()` → `games_from_rows()` (`app/loader.py:41-46`, `network/model.py:33-41`). That reader takes six columns of `top100_<dataset>.csv`: `appid`, `name`, `rank`, `months_observed`, `tag_ids`, `tags`. Nothing else in the network or the app reads a Steam column.
- **`network/` and `app/` hold no Steam wording, no links out, no `is_free`, no store genres, no `TOP_N`.** Their Steam ties are the item id (`appid`), the months filter, and two config facts: the defining tag and the Genre Tags.
- **`analysis/` is not downstream of the Build files: it runs inside the Build stage.** It reads the in-memory `BuildResult` (Snapshot store data) for the **Eligible Pool** (`analysis/run.py:60-62`). Only the pool *size* is written down (`build.json` `dataset_sizes.<key>.eligible_pool`, `analysis/run.py:33`). So the pool baselines (tag and genre frequency against the pool) can't be recomputed from a Build folder, and an import must bring its own pool or go without.
- **`export/schema.py` holds most of the Steam text** (46 "Steam" mentions). It also defines the strict loading contract: `read_typed_csv` refuses any file whose header is not exactly `TOP100`'s 17 columns (`export/writer.py:136-140`).
- **No links out.** The only URLs downstream are the local server address (`app/server.py:45`, `bundle/start_tag_network.py:167`, `bundle/files/READ ME FIRST.txt:25`). Store and Steam Charts URLs live only in `collect/`.
- **`TOP_N = 100` and the 20-tag maximum are not downstream.** `TOP_N` lives in `build/datasets.py:13` (used in `build/core.py:131`). The 1–20 bound is on `global_rank_limit` in `config.py:340-341`. Downstream code takes N from the row count (`len(games)`).

## Counts per module

Counted as distinct findings (rows in the tables below), not as lines.

| Module | data | config | wording | links out | "Steam" literals |
|---|---|---|---|---|---|
| `network/` | 6 | 3 | 2 | 0 | 0 |
| `analysis/` | 7 | 6 | 1 | 0 | 8 |
| `app/` | 5 | 3 | 2 | 0 | 0 |
| `export/` | 5 | 1 | 2 | 0 | 46 |
| `i18n/` | 0 | 0 | 1 | 0 | 1 |
| `bundle/` | 1 | 0 | 1 | 0 | 1 |
| **Total** | **24** | **13** | **9** | **0** | **56** |

## `network/`

| # | Finding | Where | Kind |
|---|---|---|---|
| N1 | `Game.appid: int` is the game identity: tag → game sets, edge game lists, the null model, `cluster_games` rows | `network/model.py:25`; `network/graph.py:52`, `:69`; `network/stability.py:94-98`; `network/tables.py:112` | data → item id (an int today) |
| N2 | `Game.months_observed` and the **Minimum Months Filter** (`>=`, never re-ranks): also behind node sizes, the loose layout and validation | `network/model.py:28`; `network/graph.py:55-57`; `network/layout.py:87-88`, `:126-130`, `:199-206`; `network/validation.py:209`, `:275` | data → a numeric item field |
| N3 | `min_months` is a **state key field** and a Parameter Selection settings field | `network/model.py:15`, `:57`, `:89`, `:108`; `network/selection.py:50`, `:85`, `:101`, `:129`, `:206-208` | data (its name is in every `state_id`) |
| N4 | `games_from_rows` reads the `top100_<dataset>.csv` column names | `network/model.py:33-41` | data: this is the seam |
| N5 | Tag ids are `int`; nodes are added in sorted id order | `network/model.py:29`; `network/graph.py:64-79`, `:113-116` | data → attribute id |
| N6 | `Game.rank` orders games: edge game lists, `cluster_games` order, the order the curveball null model shuffles | `network/model.py:27`, `:41`; `network/validation.py:185-192` | data → rank from the score |
| N7 | `TagContext`: the defining tag and Genre Tags give the hidden-tag reasons; **any hidden tag that is neither is labelled `genre_tag_hidden`** | `network/model.py:45-50`; `network/graph.py:78-83` | config |
| N8 | Default Network State hides Genre Tags and the defining tag per `hide_genre_tags` / `hide_defining_tag` | `network/defaults.py:11-24` | config |
| N9 | `SelectionSettings.genre_hidden` / `hide_defining_tag`, part of the Parameter Selection key | `network/selection.py:47-48`, `:78-80`, `:99-100`, `:124-129`, `:197-205` | config |
| N10 | "Top-100 Dataset", "Minimum Months Filter", "hidden Genre Tags", "defining tag" in the methods paragraph and change notes | `network/selection_text.py:427-429`; `network/selection.py:199-208` | wording |
| N11 | "games" across the Parameter Selection and metrics text | `network/selection_text.py`, `network/metrics.py` (docstrings and messages) | wording |

## `analysis/` (runs inside the Build stage)

| # | Finding | Where | Kind |
|---|---|---|---|
| A1 | Reads `datasets/top100_<key>.csv` from the BuildResult | `analysis/run.py:17`; `analysis/report.py:40` | data |
| A2 | **Eligible Pool** taken from in-memory store data (`result.games[appid].tags/.genres`, `result.ranked[key].eligible`); only its size is written to `build.json` | `analysis/run.py:33`, `:60-62` | data → optional pool |
| A3 | Store genres (`genre_ids`, `genres`) → `genre_frequency.csv` with pool baseline | `analysis/features.py:59-80`; `analysis/run.py:65` | data → optional |
| A4 | `content_flags` column → `content_flags.csv` and the report's flag counts | `analysis/features.py:165-168`; `analysis/run.py:54`, `:68-69` | data → optional |
| A5 | `is_free` → the report's free-to-play sentence | `analysis/report.py:51`; `analysis/templates.py:43` | data → optional |
| A6 | `months_observed` → the report's months sentence | `analysis/report.py:46-50` | data → optional numeric field |
| A7 | `appid` in `content_flags.csv` rows | `analysis/features.py:166` | data → item id |
| A8 | The defining tag: listed at 100 % in tag frequency, left out of combinations and associations | `analysis/run.py:63-66`; `analysis/features.py:1-4` | config |
| A9 | Content Flags list taken from `exclusions.toml` | `analysis/run.py:54` | config |
| A10 | `genre_kind` map classifies store genres | `analysis/run.py:65`; `analysis/features.py:76` | config |
| A11 | `PUZZLE_NOTE` keyed on a defining tag named "Puzzle" | `analysis/run.py:48`, `:71-72` | config (hard-coded Steam fact) |
| A12 | `archived_tag_categories.json` (archived Steamworks tag categories) matched by tag **name** | `analysis/features.py:22-26`, `:51` | config (Steam reference data) |
| A13 | "fewer than 12 months" hard-coded in the months sentence | `analysis/report.py:50`; `analysis/templates.py:41-42` | config |
| A14 | Report text: Steam Charts, Steam store, "Top-100 Datasets", limitations and attribution | `analysis/templates.py:25-26`, `:32`, `:72-75`, `:96`, `:103`, `:106`; `analysis/report.py:37` | wording |

## `app/`

| # | Finding | Where | Kind |
|---|---|---|---|
| P1 | `BuildContext.rows()` reads `datasets/top100_<dataset>.csv` with the strict `TOP100` schema: **the one reader every app consumer uses** | `app/loader.py:41-46` | data: the seam's natural home |
| P2 | The rank / **AppID** / name table in the inspector | `app/view.py:197-201`, `:257-260`, `:368`; `app/callbacks.py:538-548` | data → item id (and "AppID" header, wording) |
| P3 | The months control: slider **0–60** in the Workbench and in Parameter Selection, and every callback that passes `min_months` | `app/layout.py:249-250`; `app/ps_view.py:367-368`; `app/callbacks.py:61-79`, `:256-291`, `:510-568`, `:785`, `:1081-1113` | data → numeric field (range hard-coded in months) |
| P4 | A Build sits at `<root>/builds/<snapshot_id>/<build_id>/`: Open Network State finds it by that layout, and the refusal names the Snapshot | `app/export.py:63-67`, `:185-200`; `builds.py:1-31` | data (Build identity assumes a Snapshot) |
| P5 | `export.json` embeds the whole `build.json` (`snapshot_id`, config) and identifies the Build by its hash | `app/export.py:118`, `:185-200` | data (export schema; see fog) |
| P6 | `load_build` passes a stub `collection.toml` with Steam Charts rates because `config_from_data` demands it | `app/loader.py:78-79`, `:86-92` | config |
| P7 | `config_from_data` demands all eight Build config files (`exclusions`, `genres`, `manual_metadata` …); a Build without them won't load | `app/loader.py:78-81`; `config.py:228-251` | config |
| P8 | Genre Tag chips and the defining-tag toggle in the Workbench and in Parameter Selection | `app/layout.py:239-261`; `app/callbacks.py:64-107`, `:205`, `:270-271`, `:604`; `app/ps_view.py:332`, `:351-361` | config |
| P9 | Export names `steamstudy_<dataset>_…zip`, `steamstudy_parameter-selection_…` | `app/export.py:71`; `app/ps_export.py:35`; `app/callbacks.py:217` | wording |
| P10 | "Top {rows}, games with ≥ {months} months observed" and "≥ {n} months observed" | `app/view.py:885`, `:932` | wording |

## `export/`

| # | Finding | Where | Kind |
|---|---|---|---|
| E1 | `TOP100`: 17 columns. Generic: `dataset`, `rank`, `name`, `tag_ids`, `tags`. Steam-only: `appid`, `mean_monthly_players`, `months_observed`, `release_month`, `store_release_date`, `is_free`, `app_type`, `genre_ids`, `genres`, `content_flags`, `metadata_source`, `top_listing_rank` | `export/schema.py:182-207` | data |
| E2 | `monthly_players.csv`: Steam Charts months (not published until the operator agrees) | `export/schema.py:209-220` | data (Steam-only file) |
| E3 | `build_reports` group: 14 files, every one about collection and Exclusions (parse errors, Placeholder Rows, impact, SteamDB cross-check …); written by the Build, read by nothing downstream | `export/schema.py:72-387` | data (Steam-only reports) |
| E4 | App export tables: `cluster_games.appid` "Steam AppID", `edges.appids`, `not_in_network.tag_id` "Steam tag id." | `export/schema.py:449`, `:545`, `:591` | data |
| E5 | Analysis tables: `tag_frequency.tag_id` "Steam tag id.", `archived_category`, the Eligible Pool baseline columns; `genre_frequency.genre_id` "Steam store genre id."; `content_flags.appid` | `export/schema.py:654-658`, `:666`, `:673`, `:684`, `:740` | data |
| E6 | `dataset` column text lists the five Steam keys: "overall, puzzle, rpg, strategy or simulation" | `export/schema.py:186` | config |
| E7 | "Steam tag id." in the Parameter Selection tables, "not evidence about Steam in general" | `export/schema.py:729`, `:909` | wording |
| E8 | User Guide anchors such as `eligible-pool-baseline` | `export/guide_index.py:39-40` | wording |

"Steam" literals in `export/schema.py` by group: build reports 25, build datasets 12, app export 3, analysis 5, Parameter Selection 1 (total 46). Schema version is 5 (`export/schema.py:18`).

## `i18n/`

| # | Finding | Where | Kind |
|---|---|---|---|
| I1 | The bg catalogue mirrors each English string above: "Steam tag id.", "AppID", "Top {rows} … months observed", "≥ {n} months observed", the methods paragraph's "Top-100 Dataset". Any wording change needs its bg entry (ADR 0003; parity test) | `i18n/bg/schema_tips.py:17`; `i18n/bg/view.py:62`, `:201`, `:212`; `i18n/bg/selection_text.py:158` | wording |

The language cookie `steamstudy_lang` (`i18n/__init__.py:23`) is an internal name, never shown.

## `bundle/`

| # | Finding | Where | Kind |
|---|---|---|---|
| B1 | The bundle copies `builds/<snapshot>/<build>` folders and writes a `latest` pointer per Snapshot | `bundle/make.py:161`, `:188-199`, `:209-214` | data (the same Snapshot-parent layout as P4) |
| B2 | "the Tag Network app of the Steam Success Study" | `bundle/files/READ ME FIRST.txt:4` | wording |

## What would change a Steam result if generalised

These are the places where a generic rewrite could change bytes for an existing Build. Every one is avoided by keeping Steam's values as they are and adapting at read time.

1. **State key field names.** `state_id` is a SHA-256 over the canonical key JSON (`network/model.py:121-128`). Renaming `min_months` (for example to a generic field name), or adding a field such as the filter field's name, changes every `state_id`. Then the memos and caches miss, and saved exports no longer match (`app/export.py:164`, `:211-212`). The same holds for the Parameter Selection key (`network/selection.py:99-101`), which names `ps_cache` entries and zip names. A generic field needs either the same key name or a `KEY_VERSION` bump with a migration path.
2. **Tag id type and order.** Nodes go into the graph in sorted integer id order (`network/graph.py:64-79`, `:113-116`), and the seeded Louvain/Leiden results depend on that order. Steam tag ids must stay as they are. Import attribute ids must map to integers in a deterministic order.
3. **Game order.** Games are kept in `rank` order (`network/model.py:41`). The curveball null model shuffles over that order (`network/validation.py:185-192`) and the edge game lists follow it. Downstream code reads `rank` and never recomputes it, so keep reading it. An import without a score still needs a deterministic rank (file order, say).
4. **The months filter.** `months_observed >= min_months` with a default of 0 (`network/graph.py:55-57`). A generic numeric filter must be off at 0 and keep `>=`. A dataset without the field must keep every item, never drop it.
5. **The hidden-tag reason.** Any hidden tag is reported as `genre_tag_hidden` unless it is the defining tag (`network/graph.py:82-83`). If tags other than Genre Tags could be hidden, a new reason would change `not_in_network.csv` bytes. The partition would not change.
6. **The strict header check.** `read_typed_csv` refuses any header other than `TOP100`'s (`export/writer.py:136-140`). Adding or renaming columns in `top100_<key>.csv` makes every existing Build unreadable unless the reader accepts the old header.
7. **`build.json` identity.** Open Network State matches a Build by the hash of its `build.json` (`app/export.py:185-200`). Rewriting an old `build.json` in place, for example to migrate keys, makes its saved exports unopenable (`build_changed`). Migration has to happen at read time only.
8. **Pool baselines.** They come from Snapshot store data during the Build (A2). As long as Steam Builds keep computing them there, nothing changes. Moving them behind a file-based pool would have to reproduce the same set and the same `set(tag_ids)` counting.

## Notes for the dataset-contract ticket

- **Smallest contract the network and app need:** item id (int today), name, rank, ordered attribute ids (int) with names, and one optional numeric filter field (today `months_observed`). Config: an optional defining attribute per dataset and an optional set of "genre" attributes that can be hidden.
- **Steam-only and optional:** `mean_monthly_players` (the score), `release_month`, `store_release_date`, `is_free`, `app_type`, store genres, `content_flags`, `metadata_source`, `top_listing_rank`, `monthly_players.csv`, the Eligible Pool and the 14 Build reports. Only `analysis/` (Build stage) reads `is_free`, genres, Content Flags and the pool. The network and the app read none of them, so an import that lacks them costs the feature-analysis report, not the app.
- **Hard-coded Steam facts to make optional:** the "Puzzle" note, the archived Steamworks categories, the 0–60 months slider, the "12 months" sentence and the five dataset keys in the schema text.
- **Structural blockers for an import Build:** the `<snapshot_id>/<build_id>` folder layout (P4, B1), the eight required config files plus the collection stub (P6, P7), and the strict `TOP100` header (finding 6). Build identity and the export schema (still fog on the map) depend on how these are resolved.
