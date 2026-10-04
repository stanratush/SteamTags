# 19: Open Network State

**What to build:** "Open Network State…" lets anyone reopen an exported zip, or its `export.json`. The app finds the Build, refuses when the Build or `key_version` no longer matches, restores every setting and any Re-layout positions, recomputes, and shows ✓ or ✗ for whether the recomputed `state_id` equals the recorded one. The zip's Removal Sensitivity results are shown as "loaded from export". This is how a cited figure gets reproduced.

**Blocked by:** 16, 17

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Open Network State…).

- [ ] Accepts a zip directly (no unzipping) or an `export.json`. Locates the Build by the path in the copied `build.json`, and offers a file picker if it has moved.
- [ ] Refuses, with a clear reason, when the Build's hash differs from the copied `build.json` or when `key_version` differs. Accepts an older `schema_version` as long as the key fields can be read.
- [ ] Restores every key field, recomputes, and shows ✓ / ✗ for `state_id` equality.
- [ ] When `layout_source = relayout`, the exported x/y are restored as the Re-layout positions.
- [ ] The zip's Removal Sensitivity results are shown and marked "loaded from export", not rerun.
- [ ] Round-trip test: export, open, ✓, identical tables. Both refusal paths and the older-schema acceptance are tested.
