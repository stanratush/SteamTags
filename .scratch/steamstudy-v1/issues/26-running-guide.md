# 26: Running Guide

**What to build:** `docs/running-guide.md` lets someone with technical skill install and operate the pipeline and app without reading the code. It covers install, configs, Collect, Build, the test Snapshot, the full-run gate, the folder layouts, `--allow-parse-errors`, and the Windows notes.

**Blocked by:** 09, 11

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "User Guide and Running Guide" (Running Guide), "Commands", "Pre-run checklist".

- [ ] Install: uv, Python 3.14, bytecode compiled, no `PYTHONDONTWRITEBYTECODE`.
- [ ] Each TOML config and the researcher-maintained lists, and `CHANGELOG.md` practice.
- [ ] Collect: stages, resuming, rate parameters, what a hard stop means and what to do after one (never retry around a challenge), and `--repair`.
- [ ] Build and the test Snapshot. `--allow-parse-errors` and why such Builds are never published.
- [ ] Full-run gate mechanics: what it checks and how to record a met condition. It links to the spec's pre-run checklist rather than restating it.
- [ ] Snapshot and Build folder layouts, `latest`, and `app_cache` with Clear app cache.
- [ ] Windows notes: open `127.0.0.1` not `localhost`, run tests with `-W default -X faulthandler` (not `-X dev`), explicit UTF-8.
- [ ] Every command shown in the guide is run once against the test Snapshot to confirm it works as written.
