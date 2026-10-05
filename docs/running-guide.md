# Running Guide

How to install and operate the `steamstudy` pipeline (Collect, Build) and the Tag Network app without reading the code. It assumes you are comfortable with a terminal. Researchers who only read results should use the [User Guide](user-guide/README.md).

Before a **full** collection, the project has one-time obligations (contacting the Steam Charts operator, the ethics-office check, the SteamDB permission request). They are listed in the spec's [pre-run checklist](../.scratch/steam-success-study/spec.md#pre-run-checklist-one-time-project-obligations-not-product-features); this guide only explains how the software enforces them. Here "operator" always means the Steam Charts site operator.

## Install

You need [uv](https://docs.astral.sh/uv/) and Python 3.14 (uv can install it: `uv python install 3.14`).

```bash
uv sync --compile-bytecode
```

`pyproject.toml` also sets `compile-bytecode = true`, so a plain `uv sync` compiles too. Never set `PYTHONDONTWRITEBYTECODE`: without bytecode each Removal Sensitivity background job starts several seconds slower. Exact dependency versions are frozen in `uv.lock`. Before upgrading `dash`, `dash-cytoscape` or `dash-ag-grid`, rerun the Windows spike checklist from the planning effort.

Check the install:

```bash
uv run steamstudy --help
```

## Configuration

All settings live in `config/`, as TOML. Record every change, with its rationale, in `config/CHANGELOG.md` as a `## YYYY-MM-DD: title` entry; each Build copies the entries into its `build.json`.

| File | What it holds |
|---|---|
| `collection.toml` | Collection only: the User-Agent with your contact details, listing passes (default 2), request rates (Steam Charts 3 requests/s; store 1 request per 2 s; SteamDB defaults to the store rate), timeouts (10 s connect / 30 s read), the retry schedule (10, 30, 90 s), the parse-failure stop (5 in a row), test-mode edge-case AppIDs, the full-run gate records and the SteamDB permission reference. Hashed into `collection_config_hash`; it never changes dataset output |
| `exclusions.toml` | Exclusion rules: allowed app types, the global tag-rank limit (20 = anywhere) and per-tag limits, adult-content signals, software and Dating Sim tags, Content Flags. Tags by id, names as labels |
| `genres.toml` | The Genre Tags (hidden in the network by default) and the store-genre `kind` map |
| `datasets.toml` | The five datasets and their defining tag ids |
| `network.toml` | Network defaults shared by the app and the report: thresholds 8 / 8 / 0, hidden tags, Clustering Weight, algorithm, γ, seed, R = 20 null replicates, K = 10 noise seeds (both must be ≥ 2), the Resolution Sweep grid |
| `analysis.toml` | `max_itemset_size`, `min_support`, the causal-word list checked in every report, the release-month check threshold |
| `manual_metadata.toml` | Manual Metadata Entries (researcher-maintained; ships empty). Every field needs a `source_url` and a `retrieved` date |
| `manual_exclusions.toml` | Games excluded individually, each with a reason, evidence URLs with retrieval dates, and the date added (ships empty) |
| `exclusion_overrides.toml` | Overrides cancelling one rule for one game, with the same documentation (ships empty) |

Every file except `collection.toml` is hashed into `build_config_hash`, whose first 8 characters end every `build_id`.

Fill in `contact.user_agent` in `collection.toml` before collecting: Collect refuses to run while it still contains the placeholder.

## Collect

Collect fetches every raw response into a Snapshot under `snapshots/<snapshot_id>/`. It runs four stages strictly in order: `pool` (the Steam Charts `/top` listing, N passes), `history` (one Steam Charts page per pool app), `store` (store page and `appdetails`, only for apps that have a score, plus the SteamDB page when the tag source is SteamDB) and `taglist` (`GetTagList`, fetched when the store stage starts).

```bash
uv run steamstudy collect --mode test
```

runs every stage on a new test Snapshot, or resumes the latest open one. `--snapshot <id>` picks a Snapshot.

**Tag source.** `--tag-source steam` (the default) takes every game's tags from its Steam store page. `--tag-source steamdb` takes them from each scored app's SteamDB page instead, fetched in the store stage at the SteamDB rate; the store page and `appdetails` are still fetched, because app type, genres, the Adult Only notice and the "store data unavailable" rule come from the store. SteamDB shows every tag a game has, not only the store's top 20, so the two sources give different tag sets. The choice is recorded in `snapshot.json` and `build.json` and cannot change once a Snapshot exists: resuming with the other value is refused. `steamdb` is refused before any request unless `collection.toml` records the SteamDB permission reference.

```bash
uv run steamstudy collect --mode test --tag-source steamdb
```
 `uv run steamstudy collect pool` (or `history`, `store`, `taglist`) runs one stage on the open Snapshot; a stage refuses to start before the previous stages have finished.

**Resuming.** Rerun the same command. Requests that already have a final outcome (a page, a 404, a missing store page, an age gate, `success: false`, a parse failure) are skipped; requests that failed or were stopped are fetched again. A run that finishes closes the Snapshot; after that it only changes through `--repair` and SteamDB batches.

**Rates.** Each source has its own rate and one kept-alive connection; requests are sequential. If the operator asks for a lower rate, change it in `collection.toml` and log the change; `snapshot.json` records every rate actually used.

**Feedback.** Collect prints what it is doing: the Snapshot it starts or resumes, each listing pass, and for the history and store stages a progress line every 10 seconds (items done, how many were already collected in an earlier run, how many were skipped, and an estimate of the time left), followed by a summary of outcomes when each stage finishes. Retries and skipped pages are printed as warnings.

**Skipped apps.** When an app's Steam Charts page keeps failing to load (a timeout, connection reset or 5xx other than 503 that persists through the 10 / 30 / 90 s retries) or cannot be parsed, Collect skips that app and carries on. It records the app, the URL and the reason in `snapshots/<snapshot_id>/skipped_apps.csv`, and every Build copies the list into `reports/skipped_apps.csv`. A skipped app has no score. A rerun does not retry it; to try one again after collection, use `--repair <appid>`.

**Hard stop.** Collection stops at once, saves the response, logs the reason and exits with code 3 on HTTP 403, 429 or 503, or on any challenge page (Cloudflare markers, or a page without the structure the parser expects), whatever the page. Outside the Steam Charts app pages it also stops after 5 parse-structure failures in a row, or when a timeout, connection reset or other 5xx persists through the retries. **Never retry around a challenge** (no browser emulation, proxies or challenge solving). Wait, check whether the site has changed or objects, lower the rate if appropriate, and rerun to resume. Refusals before any request (missing contact, gate not met, closed Snapshot) exit with code 2.

**Repair.** To refetch one app in a closed Snapshot, give a written reason:

```bash
uv run steamstudy collect --repair 413150 --reason "store page was mid-update during collection"
```

It refetches the app's Steam Charts page and, if the app is scored, its store page and `appdetails` (and its SteamDB page when the tag source is SteamDB), records the repair in `snapshot.json` and updates `skipped_apps.csv`.

**SteamDB cross-check.** Disabled until `collection.toml` records a SteamDB permission reference. With permission, it fetches pages only for one Build's Top-100 members, as a logged batch; the next Build writes `reports/steamdb_crosscheck.csv`. It is refused for a Snapshot whose tag source is SteamDB: every scored app already has a SteamDB page there, and each Build writes the cross-check on its own:

```bash
uv run steamstudy collect steamdb --build 20261005T120000Z-abcdef12
```

## The test Snapshot

`--mode test` collects the first 4 listing pages of one pass (100 apps) plus the edge-case AppIDs listed in `collection.toml`: placeholder rows, missing histories, Early Access, Desktop Companion, Dating Sim, Adult Only and software cases. It may run before the operator replies. Its Builds carry `mode: test` in `snapshot.json` and `build.json`, and the app shows a banner. Never publish them.

## The full-run gate

`--mode full` refuses to start unless `collection.toml` records both pre-run obligations, each with a reference and a date:

```toml
[gate.operator_reply]
reference = "email from the Steam Charts operator, 2026-10-07"
date = "2026-10-07"
publish_monthly_players = "yes"

[gate.ethics_check]
reference = "research-integrity office, case 2026-114"
date = "2026-10-09"
```

Both records are copied into `snapshot.json`. If the operator objects, do not start (or stop) the full run.

## Build

```bash
uv run steamstudy build
```

derives a new Build from the latest Snapshot (`--snapshot <id>` picks one) without contacting any source. It writes `builds/<snapshot_id>/<build_id>/` with `datasets/`, `reports/` and `analysis/` (the files are described in [chapter 4 of the User Guide](user-guide/04-files.md)), never overwrites an earlier Build, and updates the `latest` pointers. All five datasets are always built; `--dataset` only limits what is printed.

Every dataset of a full Build holds exactly the 100 highest-ranked games of its Eligible Pool; if a pool has fewer than 100 games, the Build fails. A test Build may be shorter, with a warning. The Build fails (exit code 1) on any parse error, writing the errors to `builds/<snapshot_id>/failed/<build_id>-parse_errors.csv`. It also fails on an invalid Manual Metadata Entry or exclusion-list entry, a `;` in a tag or genre name, or a causal word in a generated report.

```bash
uv run steamstudy build --allow-parse-errors
```

treats the affected apps as unscored (or without store data), sets `parse_errors_allowed: true` with the count in `build.json`, and makes the app show a banner. Such Builds are for diagnosis only and are **never published**.

## Folder layouts

```
snapshots/<snapshot_id>/          one Snapshot (never published)
  raw/                            every response, gzipped: steamcharts/top/pass-<n>/p-<NNNN>.html.gz,
                                  steamcharts/app/<appid>.html.gz, store/page/<appid>.html.gz,
                                  store/appdetails/<appid>.json.gz, steam_api/GetTagList.json, steamdb/…
  requests.sqlite                 the request log and checkpoint (URL, status, final URL, time, sha256, outcome)
  snapshot.json                   collection metadata
  skipped_apps.csv                apps skipped because their Steam Charts page kept failing (if any)
builds/latest                     <snapshot_id>/<build_id> of the newest Build
builds/<snapshot_id>/latest       the newest Build of that Snapshot
builds/<snapshot_id>/<build_id>/  one Build
  datasets/                       top100_<dataset>.csv ×5, monthly_players.csv, build.json
  reports/                        exclusions, completeness, impact, ties, diagnostics, reports.html
  analysis/                       feature analysis, network tables, removal_sensitivity.csv,
                                  resolution_sweep.csv, analysis.json, report.html
  app_cache/                      the app's Removal Sensitivity results and job store (regenerable)
```

`snapshots/` and `builds/` are git-ignored. Only the derived Top-100 exports, reports and analysis are published; `monthly_players.csv` waits for the operator's agreement.

## The app

```bash
uv run steamstudy app
```

opens the latest Build (`--build <id>` picks another, `--port` changes the port, `--no-browser` skips opening the browser). The app listens only on `127.0.0.1` and loads nothing from the internet. Removal Sensitivity results are cached in the Build's `app_cache/`, never evicted automatically. Clear them with the app's **Clear app cache** button or:

```bash
uv run steamstudy app --clear-cache
```

## Windows notes

- Open the app at `http://127.0.0.1:8050`, never `localhost`: name resolution adds about 300 ms to every callback.
- Every file is read and written with an explicit UTF-8 encoding (tag and game names are not ASCII-safe, and the system locale may be cp1251); a test enforces this.
- Run the tests with `-W default -X faulthandler`, never `-X dev`, which crashes some interpreters at exit:

```bash
uv run python -W default -X faulthandler -m pytest
```

- After changing the export schema, regenerate the User Guide's column index; a test fails while it is stale:

```bash
uv run python -m steamstudy.export.column_index
```
