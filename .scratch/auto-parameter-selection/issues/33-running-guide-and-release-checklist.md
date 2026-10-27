# 33: Running Guide and release checklist

**What to build:** the Running Guide paragraph on Parameter Selection, and the release checklist's steps 4 and 5 for bundles that ship Parameter Selection results.

**Blocked by:** 32, **and** the researcher committing their own edits to `docs/running-guide.md` and `docs/releasing-an-app-bundle.md`. Both files carry uncommitted work in the researcher's tree. Do not start, and never edit over them, until `git status` shows them clean.

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Running Guide and release checklist".

- [x] `docs/running-guide.md`: a short paragraph with the full Run's time on 12 workers and serially, taken from issue 32's measurement (never the old "~3 min / ~23 min"). It also gives the cache location `<build>/app_cache/parameter_selection/` and says that "Clear app cache" (button or `steamstudy app --clear-cache`) removes it.
- [x] `docs/releasing-an-app-bundle.md`:
  - step 4: making a bundle runs Parameter Selection for every carried Build (the measured time per Build); what the stale-cache warning means; `--skip-parameter-selection` is never acceptable for a release;
  - step 5: check that the mode opens on finished results with no Run, and that the provenance line names the maker's machine.
- [x] `test_three_rules_and_running_guide_link` and any other guide test still pass.

## Comments

- 2026-10-27, implementation: Not started: `docs/running-guide.md` still carries the researcher's uncommitted edit and `docs/releasing-an-app-bundle.md` is untracked. Issue 32's comment has the measured times to quote.

- 2026-10-27, implementation: after the researcher committed both files. `docs/running-guide.md` gains the Parameter Selection paragraph in "The app" (about 8½ min on 12 workers, grids about 49 min serially, the whole Run at most about 1½ hours, from issue 32's measurement), the cache location and Clear app cache; its folder layout and bundle section now say what ships, plus `--skip-parameter-selection`. `docs/releasing-an-app-bundle.md` step 4 covers the per-Build run, the stale-cache warning and the ban on `--skip-parameter-selection` for releases; step 5 checks finished results and the provenance line. `tests/test_guide.py` passes.
