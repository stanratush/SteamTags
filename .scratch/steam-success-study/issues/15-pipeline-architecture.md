# Pipeline architecture and export schema
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 07

## Question

What is the modular pipeline structure: stages (enumerate pool, collect player history, collect tags/metadata, score, exclude, rank), module boundaries, cache/checkpoint layout, rate limiting and retry policy, the resumable-collection command, five dataset entry points sharing code, config files, and the exact Top-100 export CSV + metadata JSON schema that the app loader reads? Includes the subset test-run plan.

Surfaced by [Data source selection and substitution sign-off](07-data-source-signoff.md):
- Collectors: Steam Charts (configurable rate, default 3 req/s, single connection), Steam store page + `appdetails` (1 req/2 s shared, `l=english`, age-check cookie with birth date = collection date − 30 years), SteamDB cross-check collector (disabled unless a config flag carries the permission reference; tested only on hand-saved fixture pages).
- Shared hard-stop rule (403/429/503/challenge → stop, resume from checkpoint) and retry/backoff for timeouts and connection errors.
- Raw response archive layout (every HTML/JSON response kept locally, never redistributed).
- Manual Metadata Entry overrides file: schema, per-field source URL + retrieval date, validation (reject unsourced entries), and where it enters the pipeline (before exclusion).
- `store_data_unavailable` exclusions, plus a report of those that would have scored inside a Top 100.
- Test-run vs. full-run modes: the small test may run before the Steam Charts operator replies; the full run may not.

Surfaced by [Candidate pool definition](08-candidate-pool-definition.md) (settled there, to be placed in the architecture):
- Pool enumeration: N listing passes (user parameter, default 2, min 1), unioned by AppID; stop at first 404/empty page; per-pass timestamps, row counts, one-pass-only AppIDs.
- Store data fetched only for scored apps; the store rate is a user parameter (default 1 req/2 s).
- Exclusion reasons include `no_tags` alongside `store_data_unavailable`.
- Completeness report output (counts, pass stats, exclusion counts per reason, depth check of Top-100 members' `/top` ranks): its file format and location.

Surfaced by [Exclusion and genre-tag config contents](09-exclusion-genre-config.md) (settled there, to be placed in the architecture):
- Config files: tag lists as `tagid` + name pairs; global tag rank limit (default 20) with per-tag overrides; `allowed_app_types`; `content_flags`; Genre Tag list; store-genre `kind` map; `manual_exclusion` and `exclusion_override` lists. Config change log with rationale.
- Collectors must capture: `GetTagList` snapshot + `version_hash`; store page "Adult Only" notice; `appdetails.content_descriptors` ids; every distinct `(tagid, name)` and `(genre id, description)` seen.
- Exclusion records: all matching reasons with detail plus `primary_reason`; Content Flags per game in the exports.
- Impact report (before freeze): per-rule/per-tag removals with would-be ranks, near-misses beyond rank limits, Adult Only vs. descriptor 3 disagreements, unexcluded Top-100 games with descriptor 1/4, software genre or a Content Flag. Its file format and location.

## Answer

Resolved 2026-10-04 with the researcher, over three rounds.

**Code layout**
- One Python package, `steamstudy`, in a `src/` layout, managed with `uv` on Python 3.12, with dependencies pinned in `uv.lock`. *(Superseded: Python 3.14, see [Web stack selection](18-web-stack-selection.md).)*
- Subpackages:
  - `collect`: network I/O only;
  - `build`: parsing, scoring, Manual Metadata, exclusion, ranking, reports, export;
  - `network`: graph build, clustering, metrics, centers; never imports UI code;
  - `analysis`: feature-analysis tables and report;
  - `app`: the UI; depends on `network`, never the reverse.

**Collect / Build split** (new glossary terms **Snapshot** and **Build**, [CONTEXT.md](../../../CONTEXT.md))
- **Collect** is slow, online and resumable. It writes one Snapshot:
  - every raw response;
  - a request log;
  - a fixed collection date, which sets the Observation Window. Rows for months ending after it are ignored.
- **Build** is offline and deterministic: Snapshot plus config → the five Top-100 Datasets, their reports and the feature analysis. It never contacts a source. One Snapshot can have many Builds (e.g. before and after the impact-report review).
- Collection order, strictly one stage after the other, no overlap:
  1. `pool`: N listing passes;
  2. `history`: Steam Charts app pages;
  3. `store`: store page + `appdetails`, only for scored apps, decided by the same `score()` function the Build uses;
  4. `taglist`: `GetTagList`, fetched once when the store stage starts.

**Module interfaces**
- `Fetcher.fetch(request_key, url) -> StoredResponse` hides all request handling:
  - per-source rate and the single kept-alive connection;
  - User-Agent and age-check cookie;
  - retries, challenge detection, hard stop;
  - writing the archive file and log entry, and skipping on resume.

  Adapters: live HTTP and a fixture-backed fake for tests.
- Parsers are pure functions from a stored response to a typed record: `parse_top_page`, `parse_steamcharts_app → MonthlyHistory`, `parse_store_page → tags + Adult Only notice`, `parse_appdetails`, `parse_tag_list`.
- `build(snapshot, config) -> BuildResult` is pure. A separate writer lays out the Build folder. `score(history, window) -> Score` is the single scoring function. The placeholder-row rule from [Placeholder rows and the Release Month definition](16-placeholder-rows-release-month.md) goes inside it.
- `network.build_network(top100_rows, settings) -> NetworkState` is pure and shared by the app and the feature-analysis report.
- `Snapshot` is read-only (`response(key)`, `meta`) and is the Build's only input besides config.

**Raw archive and resume**
- `snapshots/<snapshot_id>/raw/…`: one gzipped file per response:
  - `steamcharts/top/pass-<n>/p-<NNNN>.html.gz`
  - `steamcharts/app/<appid>.html.gz`
  - `store/page/<appid>.html.gz`
  - `store/appdetails/<appid>.json.gz`
  - `steam_api/GetTagList.json`
  - `steamdb/…`
- `requests.sqlite` logs url, status, final URL after redirects, timestamp, sha256 and outcome. It is the checkpoint.
- Resume = rerun the same command. Requests with a final outcome are skipped. Errors that may clear on a retry and hard stops are fetched again.
- A Snapshot is closed after collection. The only later changes are `collect --repair <appid> --reason "…"` and the SteamDB cross-check batches, both logged.

**Retry and stop policy** (all numbers in `collection.toml`)

| Situation | Action |
|---|---|
| 403, 429, 503, challenge page (Cloudflare markers, or the expected structural marker missing) | Hard stop: save, log, exit non-zero; no automatic retry |
| 5 parse-structure failures in a row | Hard stop |
| Timeout (connect 10 s / read 30 s), connection reset, other 5xx | Retry after 10 s, 30 s, 90 s; then hard stop |
| `/top` page 404 or empty | End of that listing pass |
| Steam Charts app page 404 | Final `not_found` (unscored) |
| Store page redirects to the home page, or to a page with no app | Final `no_store_page` → `store_data_unavailable` |
| Age check still shown after the cookie | Final `age_gate`, flagged for review; no workaround |
| `appdetails` `success:false` | Final `no_appdetails` |

- No `cc=` parameter: the store is fetched as a logged-out visitor from the researcher's location. The country Steam reports is recorded in `snapshot.json`. Region-locked results are a Known limitation.

**Config** (TOML, `config/`)
- `collection.toml`:
  - rates, listing passes, User-Agent contact, timeouts, retries;
  - test-mode edge-case AppIDs;
  - SteamDB permission reference;
  - Steam Charts operator reply and ethics-office check (reference + date each);
  - operator answer on publishing `monthly_players.csv`.
- `exclusions.toml`: rules, tag lists, rank limits, `allowed_app_types`, `content_flags`.
- `genres.toml`: Genre Tag list, store-genre `kind` map.
- `datasets.toml`: one entry per dataset (`overall` has no defining tag; the others have a defining tagid, checked against the `GetTagList` snapshot).
- `network.toml`: shared network defaults and seed.
- `analysis.toml`: `max_itemset_size`, `min_support`, causal-word list.
- Researcher-maintained lists: `manual_metadata.toml`, `manual_exclusions.toml`, `exclusion_overrides.toml`.
- `CHANGELOG.md`: every config change with its rationale.
- Two hashes over the parsed, normalised contents:
  - `collection_config_hash`, stored in the Snapshot;
  - `build_config_hash`, over every file a Build reads, stored in `build.json`.

  Collection settings never change dataset output.

**Datasets**: config entries. One Build always produces all five from one shared Eligible Pool. `build --dataset` limits only what is printed.

**Manual Metadata Entry** (`manual_metadata.toml`)
- Every field is `{value, source_url, retrieved}`. A full entry requires:
  - tags (tagid + name, display order);
  - `app_type`, store genres, `is_free`, release date;
  - `adult_only`.
- Applied in the Build after store parsing, before exclusion.
- An entry for an app the store does provide → the Build fails.
- A **tags-only** entry is allowed for a `no_tags` game: other fields come from the store, flagged `metadata_source = manual_tags`. Full entries are flagged `manual`.
- Citations are copied into `reports/manual_metadata.csv`.

**Ranking**
- Order: `mean_monthly_players` desc, then `months_observed` desc, then `appid` asc.
- Always exactly 100 rows.
- Games outside the top 100 whose score equals rank 100's go to `reports/ties.csv`.

**Build folder**: `builds/<snapshot_id>/<build_id>/`, with `build_id` = UTC timestamp + first 8 characters of `build_config_hash`. A Build never overwrites an earlier one; `latest` points to the newest.
- `datasets/`:
  - `top100_<dataset>.csv` × 5;
  - `monthly_players.csv`: one row per appid and month (avg, peak) for every game in any Top-100 Dataset. Always written; **not published** until the Steam Charts operator agrees;
  - `build.json`.
- `reports/`:
  - `exclusions.csv`: one row per (appid, matched reason), with detail, `primary_reason`, would-be rank per dataset;
  - `completeness.csv`;
  - `impact_*.csv`;
  - `ties.csv`;
  - `parse_errors.csv`;
  - `tag_vocabulary.csv`: every distinct `(tagid, name)` and `(genre id, description)` seen, with app counts;
  - `manual_metadata.csv`;
  - `steamdb_crosscheck.csv`, when SteamDB batches exist;
  - `reports.html`: summary rendered from Markdown templates, with the same causal-word test as the feature-analysis report.
- `analysis/`: feature-analysis output, as decided in [Feature-analysis definitions](13-feature-analysis-definitions.md).

**Top-100 export CSV** (the app's loading contract): `top100_<dataset>.csv`, UTF-8 with BOM, one row per game, sorted by rank.

| Column | Note |
|---|---|
| `dataset`, `rank` | |
| `appid`, `name` | |
| `mean_monthly_players` | 6 decimals, so the rank can be reproduced |
| `months_observed`, `release_month` | `YYYY-MM` |
| `store_release_date` | as given by the store; metadata only |
| `is_free`, `app_type` | |
| `tag_ids`, `tags` | display order, `;`-separated, matching lists; the Build fails if a name contains `;` |
| `genre_ids`, `genres` | same convention |
| `content_flags` | `;`-separated codes |
| `metadata_source` | `store` / `manual` / `manual_tags` |
| `top_listing_rank` | best `/top` rank across passes |

Tag votes and the monthly series are not in this file.

**Provenance contract** (exact key names are left to implementation)
- `snapshot.json`:
  - id, mode, collection date, Observation Window;
  - per-stage and per-pass start/end times;
  - request rates actually used, with any change;
  - User-Agent, age-check birth date, store-reported country;
  - `GetTagList` `version_hash`;
  - `collection_config_hash`;
  - operator-reply and ethics-check references;
  - SteamDB permission reference and cross-check batches;
  - repairs;
  - software versions.
- `build.json`:
  - Snapshot id, `build_id`;
  - `build_config_hash` plus a copy of the full parsed config;
  - `CHANGELOG.md` entries up to the Build;
  - Source Substitutions used (store page + `appdetails`, confirmed 2026-10-03);
  - attribution line;
  - seed, network defaults;
  - software versions;
  - `mode`, `parse_errors_allowed`;
  - the Manual Metadata Entries used.
- CSVs carry no repeated header or metadata rows.

**Parse failures at Build time**
- Collected into `reports/parse_errors.csv`. The Build fails if there are any.
- `--allow-parse-errors` treats those apps as unscored or `store_data_unavailable`, sets `parse_errors_allowed: true` plus the count, and the app shows a warning banner.
- A published Build never has this flag set.

**Commands**
- `steamstudy collect --mode test|full [--snapshot <id>]`, or a single stage with `collect <stage>`.
- `steamstudy collect steamdb --build <id>`.
- `steamstudy collect --repair <appid> --reason "…"`.
- `steamstudy build [--snapshot <id>] [--allow-parse-errors]`.
- `steamstudy app [--build <id>]`.

**Test run and full-run gate**
- **Test Snapshot** (`--mode test`): the first 4 `/top` pages of one pass (100 apps), plus the edge-case AppIDs listed in `collection.toml`, picked from the research notes when the code is written:
  - leading 0.00 placeholder (Scorn);
  - no month rows (Black Hole Simulator);
  - delisted; region-locked or login-only;
  - Adult Only;
  - Dating Sim farming game;
  - free-to-play;
  - Desktop Companion;
  - software app.

  It is built in full, and `build.json` plus the app banner show `mode: test`. Parser tests run offline on fixtures saved from it.
- **Full Snapshot** (`--mode full`): refuses to start unless `collection.toml` records the Steam Charts operator reply and the ethics-office check. Both are copied into `snapshot.json`.

**SteamDB cross-check**
- `collect steamdb --build <id>` fetches SteamDB pages only for that Build's Top-100 members, into `raw/steamdb/` as its own logged batch.
- It refuses to run without the permission reference.
- The next Build adds `steamdb_crosscheck.csv` (store vs. SteamDB tags per game). SteamDB values never enter a dataset.
- Until permission is granted, it is tested only on pages saved by hand.
