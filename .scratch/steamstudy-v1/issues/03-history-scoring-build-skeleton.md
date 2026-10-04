# 03: Steam Charts history, scoring and Build skeleton

**What to build:** `steamstudy collect history` fetches every pool app's Steam Charts page. After that, `steamstudy build` derives each app's Mean Monthly Players, Release Month and Months Observed offline from the Snapshot. It writes a new Build folder with the scoring diagnostics, and it fails loudly on any parse error unless the researcher explicitly allows parse errors.

**Blocked by:** 02

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Collect" (stages), "Build" (Interface, Row parsing, Scoring, Build folder, Parse failures).

- [ ] `collect history` fetches one `/app/{appid}` page per pool AppID through the Fetcher. A 404 gives the final outcome `not_found`.
- [ ] `parse_steamcharts_app -> MonthlyHistory`: only `<English month name> <YYYY>` rows are months, `Last 30 Days` is skipped, and unknown labels and duplicate months become parse errors.
- [ ] `score(history, window) -> Score` is the single scoring function. A Placeholder Row (Avg 0.00 and Peak 0, at any position) is treated as absent. Avg 0.00 with Peak ≥ 1 is data. Release Month is the first non-placeholder month. Mean Monthly Players and `months_observed` cover months from the Release Month on inside the Observation Window. Rows after the window are ignored without error.
- [ ] `build(snapshot, config) -> BuildResult` is pure, and its only inputs are a read-only `Snapshot` (`response(key)`, `meta`) and config. A test proves a Build makes no network access.
- [ ] A writer lays out `builds/<snapshot_id>/<build_id>/` (`build_id` = UTC timestamp + 8 characters of `build_config_hash`), never overwrites a Build, and maintains `latest`.
- [ ] `build.json` holds at least the Snapshot id, `build_id`, `build_config_hash` with a copy of the parsed config, software versions, `mode` and `parse_errors_allowed`.
- [ ] `reports/parse_errors.csv` is written. Any entry fails the Build. `--allow-parse-errors` treats those apps as unscored and records the flag and the count.
- [ ] `reports/placeholder_rows.csv` (`appid, month, position`, where position is `leading`/`interior`/`trailing`) and an initial `completeness.csv` are written. `completeness.csv` holds listing rows, scored apps, the Placeholder Row count, and unscored apps split three ways (no month rows / only Placeholder Rows / none in the window).
- [ ] Fixture tests use real pages for Scorn 698670 (leading placeholder), Bold Blade 749110 (interior placeholder), Stardew Valley 413150 (tiny pre-launch rows count), Black Hole Simulator 1401150 (no month rows) and Dadish 3D 2888870 (only `Last 30 Days`).
