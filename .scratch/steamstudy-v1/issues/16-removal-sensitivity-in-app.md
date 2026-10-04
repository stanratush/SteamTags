# 16: Removal Sensitivity in the app

**What to build:** In the Workbench, the researcher presses Run to start a background Removal Sensitivity sweep over every visible tag, or presses "Run for this tag" in the node inspector. They see a time estimate, progress and Cancel, and can resume with "Continue (n of N done)". Results are cached per Network State, shown as current whenever they return to that state and greyed as stale otherwise, and included in the export zip. "Clear app cache" removes them.

**Blocked by:** 15

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Removal sensitivity tab, Stack and process), "Export schemas" (`export.json` `removal_sensitivity`).

- [ ] Runs use Dash background callbacks with `DiskcacheManager`. Inputs are plain picklable values only. The job store is separate from results. No multiprocessing.
- [ ] Before a run, an estimate is shown (n × the measured time of the current clustering). Progress and Cancel work. Starting or cancelling clears the progress bar.
- [ ] Results are cached in `<build>/app_cache/` keyed by the Network State key plus the method version. A cancelled run is cached as partial and offers Continue, which runs only the remaining tags in the same order. Single-tag runs share the table, and a later full run skips them.
- [ ] Results for another key stay visible but greyed and not clickable until a re-run.
- [ ] Table: default sort `rc_ari` asc, then |`rc_delta_modularity`| desc. All columns sortable. Membership Stability joined in as a column. Filters: "beyond noise only" and a cluster selector. The noise line sits above the table. The footer reads "x of n tags flagged; if removals acted only like another seed, at most about n/(K+1) would be". The flag is labelled "screening flag, not a significance test".
- [ ] A row click selects the tag in the graph and the inspector. The node inspector shows the tag's row and "Run for this tag".
- [ ] Export: `removal_sensitivity.csv` is included only for results under the exact current key. `export.json` `removal_sensitivity` is `"not_run"` or `partial` with `done`/`total`. The method version is added to the method constants. Stale results are never exported (tested).
- [ ] "Clear app cache" (button and CLI) deletes the results and their Continue offers. Nothing is evicted automatically.
