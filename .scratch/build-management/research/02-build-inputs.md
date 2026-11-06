# What a Build reads from a Snapshot, and how long it takes

Facts for [What is a lightweight Snapshot?](../issues/08-lightweight-snapshot.md) and the [Build menu](../issues/12-build-menu.md). As of commit `cc82322` (2026-11-06), Snapshot `20261005T062558Z-full`, the current `config/`. Paths are relative to `src/steamstudy/`.

How this was found: by reading `build/core.py` and every function it calls, then running [measure.py](../prototypes/02-build-inputs/measure.py). The script has two modes. `timing` runs one Build through the same functions as `steamstudy build`, with timers around each stage. `extract` writes exactly the fields the Build reads as plain CSV tables and measures them. [load_tables.py](../prototypes/02-build-inputs/load_tables.py) times reading those tables back. Raw outputs: [sizes](../prototypes/02-build-inputs/sizes_20261005T062558Z-full.json), [timing](../prototypes/02-build-inputs/timing_20261005T062558Z-full.json) (the uncontended run), [timing with the extract running beside it](../prototypes/02-build-inputs/timing_run1_contended.json). The extracted tables were deleted after measuring: they are Steam data, and `/snapshots/` is never committed.

## Short answer

- **Only the first three stages read the Snapshot**, plus one re-read of the listing in assemble. Exclusion, datasets, analysis, the network stage and the reports work on parsed records in memory.
- **The Build reads every app it could ever need, whatever the settings.** It reads the Steam Charts page of every Candidate Pool app (13,412), and the store page and `appdetails` of every **scored** app (10,973), excluded or not. So one extract covers every current setting.
- **Those fields come to 23.3 MB as plain CSV and 6.3 MB gzipped**, against 447 MB of Snapshot files (509 MB on disk). That is about 1.4% (70× smaller). Keeping only the month rows that scoring and the reports use brings it to 17.3 MB CSV and **4.6 MB gzipped** (about 1%). The store page HTML alone is 342 MB, and the Build reads only the tag list and the Adult Only notice from it.
- **A Build takes 99 s, and 78 s of it (79%) is reading and parsing the raw archive.** The network stage takes 11.6 s (12%), so it **does not dominate**. Reading the extracted tables back takes 2.9 s, so a Build from them would take about 24 s.
- **Outputs that depend on something besides those fields:** the `build_id` (a timestamp, written into every `state_id`), the installed software versions, the config, request-log *outcomes* and, for skipped apps, the log's URL, detail, status and timestamp. A Build never reads file timestamps or HTML beyond what its parsers extract.

## What each stage reads

"All" means the whole Candidate Pool or every scored app, whatever the settings select.

| Stage | Snapshot records read | Fields used | Apps |
|---|---|---|---|
| 1 pool (`build/pool.py:39` `read_listing`) | `steamcharts/top/pass-N/p-M.html.gz`, every page; log outcome | per row: rank, appid, name. Gives best rank across passes, first-seen name, rows and AppIDs per pass | all listing pages (26,826 rows, 2 passes) |
| 2 parse (`build/core.py:272` `_read_histories`) | `steamcharts/app/<appid>.html.gz`; log outcome | month rows up to the window's last month: month, Avg. Players, Peak Players. Peak is used for the Placeholder Row test and `monthly_players.csv` | all Candidate Pool apps: listing ∪ `extra_appids` (13,412) |
| 3 games (`build/games.py:77` `read_game`) | `store/page/<appid>.html.gz`, `store/appdetails/<appid>.json.gz`; log outcomes. `steam_api/GetTagList.json` once | page: tags (id, name, display position), Adult Only notice. appdetails: type, name, `is_free`, genres (id, description), release-date string, content descriptor ids. GetTagList: ids and names | **every scored app** (10,973), excluded or not |
| 4 exclusion (`build/exclusion.py:117`) | none | Game fields above, plus config lists | all scored apps |
| 5 datasets (`build/datasets.py:43`) | none | scores, tags | all scored apps |
| 6 assemble (`build/core.py:141-164`, `build/assemble.py`) | listing pages **again** (`skipped_app_rows` calls `read_listing`); log entries of `steamcharts/app/*` with outcome `skipped`: url, detail, status, timestamp; `steamdb/*` pages and log `batch`, only if present (none in this Snapshot) | histories for Top-N members only (`monthly_players.csv`); Game fields of all scored apps (`tag_vocabulary.csv`, exclusion reports) | members / all scored |
| 7 analysis: feature tables (`analysis/run.py:51`) | none | Top-N rows; tags and genres of **every Eligible Pool app** (pool baselines, up to 8,776 in `overall`) | Eligible Pools |
| 8 network stage (`analysis/network_stage.py:37`) | none | Top-N rows only | ≤ 500 apps |
| 9 reports (`analysis/report.py`, `build/summary.py`) | none | in-memory results | — |

From `snapshot.json` the Build reads `id`, `mode` (a test Build may hold fewer than 100), `observation_window`, `collection_date`, `collection_config_hash`, `taglist_version_hash`, `store_country` and `extra_appids`. The CLI also reads `closed`, for a warning only (`cli.py:112`). The others (`user_agent`, `stages`, `pool`, `rates`, `gate`, `steamdb`, `repairs`, `software_versions`, `created_at`, `closed_at`, `age_check_birth_date`) are never read.

**Parsed but never used:** a tag's vote count, the store page's country, `coming_soon`, and the Steam Charts page title. The request log's `sha256` and `final_url` are not used either.

**Does any setting read more?** No. Every setting in today's config files reads only the fields above, for apps the Build already reads in full. That covers defining tags, exclusion tag ids *and names* (name-only matches), rank limits, descriptor ids, allowed app types, the manual lists, Genre Tags, analysis and network settings. The Observation Window is fixed by the Snapshot, so it is not a setting. Future settings on this map also stay inside: tags per game uses the display positions, and list size uses all scored apps. Fields outside the set would be needed only by a new setting on tag votes, the Steam Charts title or the store country (votes would add about 0.5 MB).

## Sizes

All sizes are in bytes, as in the [sizes file](../prototypes/02-build-inputs/sizes_20261005T062558Z-full.json). Snapshot sizes are file sizes. On disk the folder is 509 MB, because 35,000 small files waste cluster space.

| Snapshot part | Size |
|---|---|
| `raw/store/page` (10,973 pages) | 341.7 MB |
| `raw/store/appdetails` | 46.3 MB |
| `raw/steamcharts/app` (13,412 pages) | 42.7 MB |
| `requests.sqlite` | 10.7 MB |
| `raw/steamcharts/top` | 5.9 MB |
| `raw/steam_api/GetTagList.json`, `snapshot.json` | 0.04 MB |
| **Total** | **447.2 MB** |

| Extracted table | Rows | CSV | gzipped CSV |
|---|---|---|---|
| `listing` (pass, page, rank, appid, name, outcome) | 26,826 | 1.15 MB | 0.49 MB |
| `steamcharts_outcomes` (appid, outcome; url, detail, status, timestamp when skipped) | 13,412 | 0.20 MB | 0.04 MB |
| `steamcharts_months_all` (every month row up to the window's end) | 643,989 | 15.95 MB | 4.53 MB |
| `steamcharts_months_min` (window months, Release Month, first and last data month, Placeholder Rows) | 396,755 | 9.94 MB | 2.83 MB |
| `store_apps` (outcomes, name, type, `is_free`, release date, Adult Only, descriptor ids) | 10,973 | 0.74 MB | 0.21 MB |
| `store_tags` (appid, position, tag id, name) | 185,327 | 4.71 MB | 0.96 MB |
| `store_genres` (appid, genre id, name) | 30,583 | 0.57 MB | 0.10 MB |
| `tag_vocabulary` | 446 | 0.01 MB | 0.004 MB |
| `snapshot_meta.json` (the eight keys above) | — | 0.0004 MB | 0.0003 MB |
| **Total, all month rows** | | **23.3 MB** | **6.3 MB** |
| **Total, minimal month rows** | | **17.3 MB** | **4.6 MB** |

The month rows are most of what is left. Rows before the window matter only for the Release Month and for the Placeholder Row positions (leading/interior/trailing). Both can be kept as a few values per app instead of as rows, which is what `months_min` does.

## Timings

One `steamstudy build` on the full Snapshot. Windows 11, Python 3.14.8, warm file cache, nothing else running: **98.96 s, plus 0.76 s to write the Build folder** (3.4 MB). The same Build with the extract script running beside it took 118 s.

| Stage | Seconds | Share |
|---|---|---|
| 1 pool: read and parse the `/top` pages | 3.98 | 4% |
| 2 parse: Steam Charts histories and scores | 45.89 | 46% |
| 3 games: store page and appdetails (10,973 calls) | 23.99 | 24% |
| 4 exclusion: evaluate and Content Flags | 0.47 | <1% |
| 5 datasets: rank five datasets | 0.16 | <1% |
| 6 assemble: `skipped_app_rows` (re-parses the `/top` pages) | 4.07 | 4% |
| 6 assemble: every other row builder and check | 0.72 | 1% |
| 7 analysis: feature tables (frequencies, combinations, associations) | 8.01 | 8% |
| 8 network stage, five datasets | 11.62 | 12% |
| — compute_state (null model 2.42, seed noise and the rest 0.62) | 3.04 | |
| — layout | 2.94 | |
| — Removal Sensitivity | 3.81 | |
| — Resolution Sweep (5 values) | 1.80 | |
| — state tables | 0.02 | |
| 9 reports | 0.05 | <1% |

- **The Snapshot stages (1, 2, 3 and the listing re-read in 6) take 77.9 s, 79% of the Build.** Of that, 19.4 s is reading and decompressing 37,511 archive files, and the rest is parsing. That means `lxml` on the Steam Charts pages, and a regex plus JSON decode on 342 MB of store HTML.
- **The network stage does not dominate**: 11.6 s at the defaults (20 null replicates, 10 noise seeds, a 5-value sweep). Its cost grows with those settings and with the network's size (list size, tags per game). Stages 4–9 together take about 21 s.
- **`skipped_app_rows` parses the whole listing a second time** (4.1 s) just for the names of skipped apps. That is waste an implementer could remove; it does not change any output.
- **A Build from extracted tables:** reading all eight gzipped tables takes 2.91 s. So a Build from a lightweight Snapshot would take about 99 − 78 + 3 ≈ **24 s**. That is an estimate: no Build was run from the tables.

## What else a Build's bytes depend on

- **`build_id`** (UTC timestamp + the first 8 characters of `build_config_hash`, `build/core.py:409`). It is written into `build.json` and `analysis.json`, and into the **state key of every Network State**, so every `state_id` column in `analysis/` changes with it (`network/model.py:85-99`). Two Builds with the same Snapshot and settings already differ in these bytes today. The seeds do not depend on it: they derive from `network.seed` (`network/stability.py:42-48`). A byte comparison between a lightweight and a full Build has to fix the `build_id`.
- **The installed software**: `software_versions()` goes into `build.json` (`versions.py:28`).
- **The config**: every Build file's parsed content, `build_config_hash`, and the `CHANGELOG.md` entries (`build/core.py:388-390`).
- **Request-log outcomes, not just bodies.** `not_found`, `skipped`, `parse_failure`, `no_store_page`, `age_gate` and `no_appdetails` decide the unscored counts in `completeness.csv` and the `store_data_unavailable` detail text (`Game.store_detail`). They have no body to extract, so a lightweight Snapshot must carry the outcome of every key the Build looks up. A missing key ("missing") is an outcome too.
- **Request-log metadata, for skipped apps only.** `skipped_apps.csv` reads each skipped app's `url`, `detail`, `status` and `timestamp` (`build/pool.py:74-85`); this Snapshot has none. `steamdb_crosscheck.csv` reads the log's `batch` (`build/core.py:209`); this Snapshot has no SteamDB pages.
- **Parse outcomes.** If a page does not parse, the Build fails, or with `--allow-parse-errors` reports the error (this Snapshot: 0). A Snapshot of parsed fields fixes the parser version used to make it: a later parser change would not reach Builds made from it. A Snapshot of raw pages does not have that limit.
- **Key order.** An app's listing name is the first one seen with keys in sorted order. `pass-N/p-M` sorts as text, so `p-10` comes before `p-2`. The best rank is the minimum across passes. Keeping every listing row keeps both; a reduced listing must store the chosen name.
- **Not read:** file timestamps, file order on disk, HTML outside what the parsers extract, `sha256`, `final_url`.
