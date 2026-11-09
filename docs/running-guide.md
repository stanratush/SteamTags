# Running Guide

How to install and operate the `steamstudy` pipeline (Collect, Build) and the Tag Network app without reading the code. It assumes you are comfortable with a terminal. Researchers who only read results should use the [User Guide](user-guide/README.md).

Before a **full** collection, the project has one-time obligations (contacting the Steam Charts operator, the ethics-office check, the SteamDB permission request). They are listed in the spec's [pre-run checklist](../.scratch/steam-success-study/spec.md#pre-run-checklist-one-time-project-obligations-not-product-features); this guide only explains how the software enforces them. Here "operator" always means the Steam Charts site operator.

## Install

You need [uv](https://docs.astral.sh/uv/) and Python 3.14 (uv can install it: `uv python install 3.14`). The repository pins the development environment to 3.14 (`.python-version`); the `steamstudy` package itself declares only the Tag Network app's dependencies and supports Python 3.12–3.14 (not 3.14.1), so the app can be delivered as an App Bundle. The pipeline's own dependencies (pandas, requests, lxml, markdown) are the `pipeline` dependency group, and `packaging` (for `steamstudy bundle`) is the `bundle` group; `uv sync` installs both by default.

```bash
uv sync --compile-bytecode
```

`pyproject.toml` also sets `compile-bytecode = true`, so a plain `uv sync` compiles too. Never set `PYTHONDONTWRITEBYTECODE`: without bytecode each Removal Sensitivity background job starts several seconds slower. Exact dependency versions are frozen in `uv.lock`. Before upgrading `dash` or `dash-ag-grid`, rerun the Windows spike checklist from the planning effort.

The graph is drawn by **Cytoscape.js 3.34.3**, vendored (not installed by uv) as `src/steamstudy/app/assets/cytoscape.min.js` with its MIT licence beside it (`cytoscape.LICENSE.txt`); the app never loads it from the internet. To upgrade it, replace both files with the ones from the new release's npm package (`dist/cytoscape.min.js` and `LICENSE`), update the version named here, then rerun the app's browser checks: the first fit fills the canvas in both layouts at 1280 × 800 and after each panel is collapsed, and a tag, a link, a region title and the background each open the right inspector view.

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

Collect fetches every raw response into a Snapshot under `snapshots/<snapshot_id>/`. It runs four stages strictly in order: `pool` (the Steam Charts `/top` listing, N passes), `history` (one Steam Charts page per pool app), `store` (store page and `appdetails`, only for apps that have a score) and `taglist` (`GetTagList`, fetched when the store stage starts).

```bash
uv run steamstudy collect --mode test
```

runs every stage on a new test Snapshot, or resumes the latest open one. `--snapshot <id>` picks a Snapshot. `uv run steamstudy collect pool` (or `history`, `store`, `taglist`) runs one stage on the open Snapshot; a stage refuses to start before the previous stages have finished.

**Resuming.** Rerun the same command. Requests that already have a final outcome (a page, a 404, a missing store page, an age gate, `success: false`, a parse failure) are skipped; requests that failed or were stopped are fetched again. A run that finishes closes the Snapshot; after that it only changes through `--repair` and SteamDB batches.

**Rates.** Each source has its own rate and one kept-alive connection; requests are sequential. If the operator asks for a lower rate, change it in `collection.toml` and log the change; `snapshot.json` records every rate actually used.

**Feedback.** Collect prints what it is doing: the Snapshot it starts or resumes, each listing pass, and for the history and store stages a progress line every 10 seconds (items done, how many were already collected in an earlier run, how many were skipped, and an estimate of the time left), followed by a summary of outcomes when each stage finishes. Retries and skipped pages are printed as warnings.

**Skipped apps.** When an app's Steam Charts page keeps failing to load (a timeout, connection reset or 5xx other than 503 that persists through the 10 / 30 / 90 s retries) or cannot be parsed, Collect skips that app and carries on. It records the app, the URL and the reason in `snapshots/<snapshot_id>/skipped_apps.csv`, and every Build copies the list into `reports/skipped_apps.csv`. A skipped app has no score. A rerun does not retry it; to try one again after collection, use `--repair <appid>`.

**Hard stop.** Collection stops at once, saves the response, logs the reason and exits with code 3 on HTTP 403, 429 or 503, or on any challenge page (Cloudflare markers, or a page without the structure the parser expects), whatever the page. Outside the Steam Charts app pages it also stops after 5 parse-structure failures in a row, or when a timeout, connection reset or other 5xx persists through the retries. **Never retry around a challenge** (no browser emulation, proxies or challenge solving). Wait, check whether the site has changed or objects, lower the rate if appropriate, and rerun to resume. Refusals before any request (missing contact, gate not met, closed Snapshot) exit with code 2.

**Repair.** To refetch one app in a closed Snapshot, give a written reason:

```bash
uv run steamstudy collect --repair 413150 --reason "store page was mid-update during collection"
```

It refetches the app's Steam Charts page and, if the app is scored, its store page and `appdetails`, records the repair in `snapshot.json` and updates `skipped_apps.csv`.

**SteamDB cross-check.** Disabled until `collection.toml` records a SteamDB permission reference. With permission, it fetches pages only for one Build's Top-100 members, as a logged batch; the next Build writes `reports/steamdb_crosscheck.csv`:

```bash
uv run steamstudy collect steamdb --build 20261005T120000Z-abcdef12
```

## Lightweight Snapshots

A Snapshot has two forms with one `snapshot_id`. The **raw** form is the folder of pages, the request log and `snapshot.json`. The **lightweight** form is `snapshots/<snapshot_id>.light.zip`, about 6 MB: the parsed tables a Build reads, with a `meta.json` that records the extract version, the raw form's repair count and each table's sha256 (checked on open). A Build from the lightweight form is byte-identical to one from the raw form, apart from `build.json`'s `snapshot_form`, and takes about 24 s instead of about 99 s.

Collect makes the lightweight form automatically when it closes a Snapshot, and again after every `--repair` (about 80 s). To make it yourself:

```bash
uv run steamstudy snapshot lighten
```

lightens the latest closed Snapshot (name another as an argument). It is never changed afterwards: collect, repair and SteamDB batches act on the raw form only, and lightening again replaces the zip. To check the guarantee on a real Snapshot:

```bash
uv run steamstudy snapshot verify-light 20261005T120000Z
```

builds from both forms with one `build_id` and compares every file.

**Which form a Build reads.** When both forms are present, the lightweight one; `steamstudy build --from-raw` forces the raw pages. The lightweight form is **stale** when its extract version is older than the code's (a parser or the extracted fields changed) or when its repair count is behind the raw form's. A stale zip is not used: the Build reads the raw form and warns you to lighten again, and refuses, naming the gap, when the raw form is absent.

**Moving a Snapshot.** The zip alone is enough to build from, so to move a Snapshot to another computer, copy its `.light.zip` into that computer's `snapshots/`. Keep the raw folder where it was made: repairs and SteamDB batches need it.

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

derives a new Build from the latest Snapshot (`--snapshot <id>` picks one) without contacting any source. It writes `builds/<snapshot_id>/<build_id>/` with `datasets/`, `reports/` and `analysis/` (the files are described in [chapter 4 of the User Guide](user-guide/04-files.md)), never overwrites an earlier Build, and updates the `latest` pointers. Every dataset in `config/datasets.toml` is always built; `--dataset` only limits what is printed. Options:

- `--name <name>` names the Build (unique per Snapshot, ignoring case; default: its `build_id`). The name is what the app's Build menu, citations and bundles show.
- `--from-raw` reads the raw pages even when a Lightweight Snapshot is present.
- `--import <import_id>` builds an Import instead (see [Import](#import)).

The datasets, their List Sizes (default 100) and the Tags per game (Tag Depth) come from `config/datasets.toml`. Every dataset of a full Build holds exactly its List Size of highest-ranked games from its Eligible Pool; if a pool is smaller than its List Size, the Build fails. A test Build may be shorter, with a warning. Builds can also be made from the app's Build menu, through a draft (see [chapter 7 of the User Guide](user-guide/07-making-builds.md)). The Build fails (exit code 1) on any parse error, writing the errors to `builds/<snapshot_id>/failed/<build_id>-parse_errors.csv`. It also fails on an invalid Manual Metadata Entry or exclusion-list entry, a `;` in a tag or genre name, or a causal word in a generated report.

```bash
uv run steamstudy build --allow-parse-errors
```

treats the affected apps as unscored (or without store data), sets `parse_errors_allowed: true` with the count in `build.json`, and makes the app show a banner. Such Builds are for diagnosis only and are **never published**.

## Import

An **Import** plays the Snapshot's role for data that does not come from Steam: one wide UTF-8 CSV of items, `id,name,attributes[,score][,numeric fields…]`, where `attributes` holds names separated by `;`, most important first. The file format, every refusal code and what changes in an Import Build are in [chapter 8 of the User Guide](user-guide/08-imported-data.md).

```bash
uv run steamstudy import items.csv --filter months
```

validates the whole file in one pass. When it is valid, the command stores it as `imports/<import_id>/` (`import_id` = UTC timestamp plus a slug of the file name). The Import holds the original file verbatim, its sha256, the normalised tables and `import.json`, and it is never changed: a corrected file is a new Import, and a byte-identical re-import is refused, naming the existing one. `--filter <column>` names the numeric column the app's filter slider uses; it must be filled for every item. `--attributes <file>` supplies attribute ids (`id,name`). By default, `attributes.csv` beside the file is used when present. Without one, attributes are numbered in name order.

When the file is refused, nothing is stored. The command prints counts per code and the first 20 problems, and writes the full list to `imports/failed/<attempt_id>/errors.csv` beside a copy of the input.

```bash
uv run steamstudy build --import 20261101T090000Z-items --name "Items, first look"
```

builds an Import with the Import defaults, or with the reduced config set in `--config <dir>` when that folder holds one. It writes `builds/<import_id>/<build_id>/`. The app's **Import data…** in the Build menu does the same import from a file upload.

## Folder layouts

```
snapshots/<snapshot_id>/          one Snapshot (never published)
  raw/                            every response, gzipped: steamcharts/top/pass-<n>/p-<NNNN>.html.gz,
                                  steamcharts/app/<appid>.html.gz, store/page/<appid>.html.gz,
                                  store/appdetails/<appid>.json.gz, steam_api/GetTagList.json, steamdb/…
  requests.sqlite                 the request log and checkpoint (URL, status, final URL, time, sha256, outcome)
  snapshot.json                   collection metadata
  skipped_apps.csv                apps skipped because their Steam Charts page kept failing (if any)
snapshots/<snapshot_id>.light.zip the lightweight form of that Snapshot (never published)
imports/<import_id>/              one Import: the original file, its sha256, normalised tables, import.json
imports/failed/<attempt_id>/      a refused import: errors.csv and a copy of the input
builds/latest                     <source_id>/<build_id> of the newest Build
builds/<snapshot_id>/latest       the newest Build of that Snapshot
builds/<snapshot_id>/drafts/      Build Drafts of that Snapshot, one <name-slug>.json each
builds/<snapshot_id>/failed/      the parse errors of a Build that failed on them
bundles/                          App Bundle zips and their wheel cache (steamstudy bundle)
builds/<snapshot_id>/<build_id>/  one Build
  datasets/                       top100_<dataset>.csv per dataset, monthly_players.csv, build.json
  reports/                        exclusions, completeness, impact, ties, diagnostics, reports.html
  analysis/                       feature analysis, network tables, removal_sensitivity.csv,
                                  resolution_sweep.csv, analysis.json, report.html
  app_cache/                      the app's Removal Sensitivity and Parameter Selection results (regenerable)
builds/<import_id>/…              Import Builds, with the same layout (latest, drafts/, <build_id>/)
```

`top100_<dataset>.csv` keeps its name whatever the List Size. The app's running job store is no longer in `app_cache/`: each app process keeps it in a temporary folder of the operating system and deletes it on exit. `snapshots/`, `imports/`, `builds/` and `bundles/` are git-ignored. Only the derived Top-100 exports, reports and analysis are published; `monthly_players.csv` waits for the operator's agreement.

## The app

```bash
uv run steamstudy app
```

opens the latest Build (`--build <id>` picks another, `--port` changes the port, `--no-browser` skips opening the browser). The app listens only on `127.0.0.1` and loads nothing from the internet. Each tab shows one Build, named in its URL (`/build/<source_id>/<build_id>`), so two tabs can compare two Builds. Run from the repository, the **Build menu** (click the Build's name in the header) switches Builds, starts and edits drafts, runs Builds, deletes them and makes Imports; [chapter 7 of the User Guide](user-guide/07-making-builds.md) walks through it. Removal Sensitivity and Parameter Selection results are cached in the Build's `app_cache/`, never evicted automatically. Clear them with the app's **Clear app cache** button or:

```bash
uv run steamstudy app --clear-cache
```

**Parameter Selection** (the app's third mode) searches the Parameter Grid of each dataset and validates each chosen pair. A full Run of all five datasets at the default Selection Settings takes about 8½ minutes on 12 workers (measured on Build `20261008T221504Z-7a23ae9f`: 298 s for the five grids, 208 s for the five validations). Run serially, the grids alone are about 49 minutes of computing, and the whole Run at most about 1½ hours. The worker count is `[parameter_selection] workers` in `config/network.toml` (0 = one fewer than the computer's cores). Results are cached in `<build>/app_cache/parameter_selection/`, so a Run computes only what is missing, and they are never evicted automatically. **Clear app cache** (the button, or `steamstudy app --clear-cache`) deletes them along with the Removal Sensitivity results.

When a library the app computes with is installed at another version than the one the Build recorded in `build.json` (`software_versions`), the app shows a banner naming each library with both versions. Pipeline-only libraries and the Python version never trigger it. **Open Network State…** finds an export's Build by its identity (`build_id` and the `build.json` hash) among the Builds under the `builds/` folder the app was started from; the path recorded in `export.json` is informational only.

## Making an App Bundle

An App Bundle lets a researcher run the Tag Network app on another computer that has only Python 3.12–3.14 (not 3.14.1): no uv, no repository, no internet. It never collects. By default it opens only the Builds it carries; made `--with-sources`, it can also make new Builds from the Snapshots it carries. See [ADR 0001](adr/0001-app-bundle-wheels-not-frozen.md) for why it ships wheels and a launcher rather than a frozen executable. To release a bundle after a code update, follow [Releasing an updated App Bundle](releasing-an-app-bundle.md).

```bash
uv run steamstudy bundle --build "Overall, first release"
```

writes `bundles/tag-network-<build_id>-<targets>.zip` for this computer's operating system, with the Builds you name. Options:

- `--build` (required, repeatable) names a Build: its `build_id`, `<source_id>/<build_id>`, its name, or `<source_id>/<name>` (names ignore case; an ambiguous name is refused, listing the matches). `--build latest` is the newest Build. The first one named opens by default.
- `--allow-test` allows Builds of test Snapshots (test bundles only).
- `--with-sources` also ships each Build's lightweight Snapshot (or Import), `config/` and the libraries a Build needs, so the bundled app can make new Builds ([ADR 0007](adr/0007-a-bundle-may-carry-its-sources.md)). The zip's name ends in `-sources`.
- `--target windows|macos|linux` (repeatable) makes it for those systems instead (Windows x64, macOS on Apple silicon, Linux x86_64 with glibc 2.28 or newer). Intel Macs and ARM Linux are not supported.
- `--out <folder>` writes the zip elsewhere.
- `--skip-parameter-selection` ships no Parameter Selection results. It is for quick test bundles only, never for a release.

```bash
uv run steamstudy bundle --target windows --target macos --target linux --build latest
```

makes one zip for all three. What goes in: the launcher `start_tag_network.py` (standard library only) with `Start Tag Network.bat` and `Start Tag Network.command`; `READ ME FIRST.txt`; the User Guide; the app-only `steamstudy` wheel; every dependency wheel each target needs for Python 3.12, 3.13 and 3.14, pinned exactly to `uv.lock` and checked against its hashes (pure-Python wheels stored once); per-target requirement files with those hashes; the Build folders with `latest` pointers, without your own `app_cache/` but each with freshly computed Parameter Selection results (every dataset's grid and the validation of its default-constraint pair, under the default Selection Settings, about 8½ minutes per Build on 12 workers); and `bundle.json` (format version, `steamstudy` version, `uv.lock` hash, targets, Python versions, Builds with their names, descriptions and parents, date, and the shipped Parameter Selection keys or `"skipped"`). Import Builds bundle like Steam ones; `imports/` is never shipped. None of the pipeline's libraries are installed, except `requests`: dash itself declares it, so it comes along, but the app never imports it. Each target adds about 220 MB. The command refuses, writing nothing, when a selected Build does not exist or when `uv.lock` has no wheel for some package on some target and Python.

**Making a bundle needs internet** (it downloads the wheels from PyPI into `bundles/.cache/`, and later runs reuse them); **using one never does**. On the target computer the launcher installs the wheels into a private `environment/` folder inside the bundle with no package index, and rebuilds it when the folder moved, the Python changed or the bundle changed. It opens the app on port 8050 or the next free one.

macOS and Linux bundles are checked for completeness (every required wheel present for every supported Python) but have not been tested on real hardware; only Windows bundles are installed and started by the test suite (`tests/test_bundle_acceptance.py`, marked `slow`, about six minutes; skip it with `-m "not slow"`).

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
