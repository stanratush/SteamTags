# 23: Lightweight Snapshots

**What to build:** `steamstudy snapshot lighten` writes `snapshots/<snapshot_id>.light.zip` (parsed tables plus `meta.json`). Builds read it by default (`--from-raw` forces raw pages) with byte-identical results apart from `snapshot_form`. Staleness is guarded by the extract version and the repair count. `steamstudy snapshot verify-light` runs the comparison on a real Snapshot, and lightening runs automatically after collect closes a Snapshot and after a repair.

**Blocked by:** none

**Status:** done

Spec: [Build management spec](../spec.md): "Lightweight Snapshots". Decision ticket: [lightweight Snapshot](08-lightweight-snapshot.md). Findings: [research 02](../research/02-build-inputs.md); reference loader: [prototypes/02-build-inputs/load_tables.py](../prototypes/02-build-inputs/load_tables.py).

- [x] An extraction module writes the tables from the research: listing (every row), Steam Charts outcomes, all month rows up to the window's end, store apps, store tags with display position, store genres, tag vocabulary, the eight `snapshot.json` keys, request-log outcomes for every key a Build looks up (including "missing"), skipped apps' log url/detail/status/timestamp, and SteamDB fields with their log `batch` when present.
- [x] `<snapshot_id>.light.zip`: CSV members (deflate) and `meta.json` (format version, `EXTRACT_VERSION`, the Snapshot keys, the raw form's repair count, each table's sha256). Written deterministically (fixed member order and timestamps). sha256 checked on open; a mismatch refuses the file.
- [x] Only closed Snapshots can be lightened. The raw form is never changed by lightening.
- [x] The Build's pool, parse and games stages take a source interface with a raw and a lightweight implementation. The lightweight one is the default when present, fresh and of the current extract version. `steamstudy build --from-raw` forces raw.
- [x] Old extract version: with raw present, read raw and warn to lighten again; without raw, refuse the Build, naming the version gap. Repair count behind the raw form's: stale, not used.
- [x] `build.json` records `snapshot_form` (`raw` | `lightweight`) and the extract version.
- [x] CLI: `steamstudy snapshot lighten [<snapshot_id>]` (default: the latest closed Snapshot) and `steamstudy snapshot verify-light <snapshot_id>` (builds from both forms with a fixed `build_id` in a temporary folder and compares every file, ignoring `snapshot_form`).
- [x] Collect lightens automatically when it closes a Snapshot, and repair does so after every repair.
- [x] `.gitignore` covers `snapshots/*.light.zip`.
- [x] Tests:
  - Fixture Snapshot: lighten, build from both forms with a fixed `build_id`, and every file is byte-identical apart from `snapshot_form`.
  - Two lightenings give byte-identical zips.
  - A bumped `EXTRACT_VERSION` falls back to raw with a warning, and refuses when raw is absent. A repair makes the lightweight form stale. A tampered member is refused.
  - A lightweight-only Snapshot folder (raw removed) builds.

## Comments

- 2026-11-08 (implementation): the seam is `build/source.py`. A Build reads parsed records (listing pages, each app's Steam Charts read and store read, the vocabulary, skipped apps' log entries, SteamDB pages, the Snapshot keys) through a `BuildSource`; `RawSource` is today's parsing moved behind it, and `build()` still accepts a plain Snapshot (read raw). `steamstudy/lightweight.py` extracts by reading a `RawSource`, so `LightSource` hands back equal records; a test compares the records of both forms as well as every Build file. Extraction covers every app the raw log has a key for (not only scored apps), so an app absent from the zip reads `missing` exactly as the raw form does. Beyond the ticket: the zip also records the raw form's SteamDB batch count, and a later `collect steamdb` makes it stale like a repair does, because the cross-check report reads those pages. `build.json` records `extract_version` for both forms (the version this software reads), so the two Builds differ only in `snapshot_form`. `LightSource.from_zip` (not `open`: the encoding rule reads any `.open()` as text I/O). A table whose sha256 differs refuses the zip outright; `--from-raw` still builds. A failed automatic lighten logs a warning and leaves the older zip, which is then stale by its counts. `.gitignore` already covers the zip through `/snapshots/`.
- 2026-11-08 (after review): `EXTRACT_VERSION` lives in `build/source.py` (re-exported by `lightweight`), so Build core does not import the lightweight module. An unreadable zip is refused as a `LightweightError` (and skipped when picking the latest Snapshot). `verify-light` refuses a stale or other-version zip with the reason instead of reporting file differences, builds with parse errors allowed so a Snapshot with some still compares, and compares `build.json` as bytes with only its `snapshot_form` line removed. On the real Snapshot `20261005T062558Z-full` (42 repairs): `snapshot lighten` took 2 min 16 s and wrote 7.1 MB; `verify-light` found the two Builds byte-identical (3 min 5 s for both Builds).
