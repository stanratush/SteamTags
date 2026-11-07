# 23: Lightweight Snapshots

**What to build:** `steamstudy snapshot lighten` writes `snapshots/<snapshot_id>.light.zip` (parsed tables plus `meta.json`). Builds read it by default (`--from-raw` forces raw pages) with byte-identical results apart from `snapshot_form`. Staleness is guarded by the extract version and the repair count. `steamstudy snapshot verify-light` runs the comparison on a real Snapshot, and lightening runs automatically after collect closes a Snapshot and after a repair.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Lightweight Snapshots". Decision ticket: [lightweight Snapshot](08-lightweight-snapshot.md). Findings: [research 02](../research/02-build-inputs.md); reference loader: [prototypes/02-build-inputs/load_tables.py](../prototypes/02-build-inputs/load_tables.py).

- [ ] An extraction module writes the tables from the research: listing (every row), Steam Charts outcomes, all month rows up to the window's end, store apps, store tags with display position, store genres, tag vocabulary, the eight `snapshot.json` keys, request-log outcomes for every key a Build looks up (including "missing"), skipped apps' log url/detail/status/timestamp, and SteamDB fields with their log `batch` when present.
- [ ] `<snapshot_id>.light.zip`: CSV members (deflate) and `meta.json` (format version, `EXTRACT_VERSION`, the Snapshot keys, the raw form's repair count, each table's sha256). Written deterministically (fixed member order and timestamps). sha256 checked on open; a mismatch refuses the file.
- [ ] Only closed Snapshots can be lightened. The raw form is never changed by lightening.
- [ ] The Build's pool, parse and games stages take a source interface with a raw and a lightweight implementation. The lightweight one is the default when present, fresh and of the current extract version. `steamstudy build --from-raw` forces raw.
- [ ] Old extract version: with raw present, read raw and warn to lighten again; without raw, refuse the Build, naming the version gap. Repair count behind the raw form's: stale, not used.
- [ ] `build.json` records `snapshot_form` (`raw` | `lightweight`) and the extract version.
- [ ] CLI: `steamstudy snapshot lighten [<snapshot_id>]` (default: the latest closed Snapshot) and `steamstudy snapshot verify-light <snapshot_id>` (builds from both forms with a fixed `build_id` in a temporary folder and compares every file, ignoring `snapshot_form`).
- [ ] Collect lightens automatically when it closes a Snapshot, and repair does so after every repair.
- [ ] `.gitignore` covers `snapshots/*.light.zip`.
- [ ] Tests:
  - Fixture Snapshot: lighten, build from both forms with a fixed `build_id`, and every file is byte-identical apart from `snapshot_form`.
  - Two lightenings give byte-identical zips.
  - A bumped `EXTRACT_VERSION` falls back to raw with a warning, and refuses when raw is absent. A repair makes the lightweight form stale. A tampered member is refused.
  - A lightweight-only Snapshot folder (raw removed) builds.

## Comments
