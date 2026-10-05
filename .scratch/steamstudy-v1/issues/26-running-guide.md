# 26: Running Guide

**What to build:** `docs/running-guide.md` lets someone with technical skill install and operate the pipeline and app without reading the code. It covers install, configs, Collect, Build, the test Snapshot, the full-run gate, the folder layouts, `--allow-parse-errors`, and the Windows notes.

**Blocked by:** 09, 11

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "User Guide and Running Guide" (Running Guide), "Commands", "Pre-run checklist".

- [x] Install: uv, Python 3.14, bytecode compiled, no `PYTHONDONTWRITEBYTECODE`.
- [x] Each TOML config and the researcher-maintained lists, and `CHANGELOG.md` practice.
- [x] Collect: stages, resuming, rate parameters, what a hard stop means and what to do after one (never retry around a challenge), and `--repair`.
- [x] Build and the test Snapshot. `--allow-parse-errors` and why such Builds are never published.
- [x] Full-run gate mechanics: what it checks and how to record a met condition. It links to the spec's pre-run checklist rather than restating it.
- [x] Snapshot and Build folder layouts, `latest`, and `app_cache` with Clear app cache.
- [x] Windows notes: open `127.0.0.1` not `localhost`, run tests with `-W default -X faulthandler` (not `-X dev`), explicit UTF-8.
- [ ] Every command shown in the guide is run once against the test Snapshot to confirm it works as written.

## Comments

- 2026-10-04 (agent): Written: docs/running-guide.md. Every command was run once against a synthetic test-mode Snapshot (offline): the collect commands refuse before any request while the contact placeholder is in collection.toml (and steamdb without permission); build, build --allow-parse-errors, build --dataset and app --clear-cache ran as written. No live collection was run.
- 2026-10-05 (agent, audit): Audit: one criterion not met. The commands were run against a synthetic test-mode Snapshot, not the real test Snapshot, which did not exist then. Agent action: once 20261005T062954Z-test closes, run every command in docs/running-guide.md against it and fix any difference. The guide now also documents collection feedback, skipped apps and the exactly-100 rule.
