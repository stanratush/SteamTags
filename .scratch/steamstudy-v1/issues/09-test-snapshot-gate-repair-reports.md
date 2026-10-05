# 09: Test Snapshot, full-run gate, repair and report summary

**What to build:** `steamstudy collect --mode test` builds the small real Snapshot (4 listing pages plus the edge-case AppIDs) that may run before the Steam Charts operator replies. `--mode full` refuses to start until the operator's reply and the ethics check are recorded. A closed Snapshot changes only through a logged `--repair`. Every Build ends with a templated `reports.html` summary that is checked for causal language.

**Blocked by:** 08

**Status:** ready-for-human

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Collect" (Test Snapshot, Full-run gate, Snapshot layout), "Pre-run checklist", "Build" (`build.json`, Build folder).

- [ ] `collect --mode test` runs every stage on the first 4 `/top` pages of one pass plus the edge-case AppIDs from `collection.toml`. The known cases ship in config. Pick the remaining cases from the research notes (delisted, e.g. MultiVersus 1818750 if confirmed; region-locked or login-only; Adult Only; free-to-play; software app) and record them.
- [x] Test Builds carry `mode: test` in `snapshot.json` and `build.json`.
- [x] `collect --mode full` exits with a clear message unless `collection.toml` records the operator reply and the ethics-office check (reference and date for each). Both are copied into `snapshot.json`.
- [x] `collect --repair <appid> --reason "…"` refetches one app into a closed Snapshot and logs the repair in `snapshot.json`. No other change to a closed Snapshot is possible.
- [x] `snapshot.json` and `build.json` carry the full provenance lists from the spec, including the Source Substitutions, the attribution line, `CHANGELOG.md` entries up to the Build, the age-check birth date and the `GetTagList` `version_hash`.
- [x] A reusable templating and causal-word component: report text comes only from fixed sentence templates, and rendering fails if the output contains any word from the `analysis.toml` causal-word list.
- [x] `reports/reports.html` summarises the Build's reports through that component.
- [ ] The saved test-Snapshot raw files become the offline parser and Build fixtures used by the test suite.
- [x] Tests: the gate refuses without records, repair logging, and a deliberately causal template failing the render.

## Comments

- 2026-10-04 (agent): Implemented: --repair (forced refetch of one pool app into a closed Snapshot, logged in snapshot.json repairs), gate records copied into snapshot.json, analysis/templates.py (fixed sentences/paragraphs, causal-word check incl. 'makes ... successful'), reports/reports.html. Added Karryn's Prison (Adult Only) and Wallpaper Engine (software) to the test-mode edge cases. No delisted or region-locked app is confirmed yet (MultiVersus still has a store page); config notes this. The fixtures are the real pages captured on 2026-10-04 (tests/fixtures), not yet a full test Snapshot.
- 2026-10-05 (agent, audit): Audit: two criteria not met. (1) Of the remaining edge cases, Adult Only (1619750), software (431960) and free-to-play (2923300) are recorded; no delisted or region-locked app has been confirmed (MultiVersus still has a store page). (2) Only Bold Blade's page has been taken from a real test Snapshot so far. Human action: pick and verify a delisted and a region-locked app, let the test Snapshot (20261005T062954Z-test) finish, and save its edge-case pages as fixtures.
