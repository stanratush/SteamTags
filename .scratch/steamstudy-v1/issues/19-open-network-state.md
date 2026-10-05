# 19: Open Network State

**What to build:** "Open Network State…" lets anyone reopen an exported zip, or its `export.json`. The app finds the Build, refuses when the Build or `key_version` no longer matches, restores every setting and any Re-layout positions, recomputes, and shows ✓ or ✗ for whether the recomputed `state_id` equals the recorded one. The zip's Removal Sensitivity results are shown as "loaded from export". This is how a cited figure gets reproduced.

**Blocked by:** 16, 17

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Open Network State…).

- [x] Accepts a zip directly (no unzipping) or an `export.json`. Locates the Build by the path in the copied `build.json`, and offers a file picker if it has moved.
- [x] Refuses, with a clear reason, when the Build's hash differs from the copied `build.json` or when `key_version` differs. Accepts an older `schema_version` as long as the key fields can be read.
- [x] Restores every key field, recomputes, and shows ✓ / ✗ for `state_id` equality.
- [x] When `layout_source = relayout`, the exported x/y are restored as the Re-layout positions.
- [x] The zip's Removal Sensitivity results are shown and marked "loaded from export", not rerun.
- [x] Round-trip test: export, open, ✓, identical tables. Both refusal paths and the older-schema acceptance are tested.

## Comments

- 2026-10-04 (agent): App implemented in steamstudy.app (loader, renderer boundary, layout, callbacks, export/open, rs_cache, server). Tested via the export zip (app equals Build, round trip, refusals), the served page (no external URLs) and the callbacks as functions; also exercised live in the browser on a demo Build (node/edge/cluster inspectors, remove, layout switch, Re-layout, background Removal Sensitivity run with stale/current display, Analysis Report mode on the same renderer instance, floating inspector). Open Network State also re-exports and can compare table hashes (recorded_table_hashes_match).
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
