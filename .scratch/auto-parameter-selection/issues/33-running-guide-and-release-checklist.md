# 33: Running Guide and release checklist

**What to build:** the Running Guide paragraph on Parameter Selection, and the release checklist's steps 4 and 5 for bundles that ship Parameter Selection results.

**Blocked by:** 32, **and** the researcher committing their own edits to `docs/running-guide.md` and `docs/releasing-an-app-bundle.md`. Both files carry uncommitted work in the researcher's tree. Do not start, and never edit over them, until `git status` shows them clean.

**Status:** ready-for-agent (once unblocked)

Spec: [Automatic Parameter Selection spec](../spec.md): "Running Guide and release checklist".

- [ ] `docs/running-guide.md`: a short paragraph with the full Run's time on 12 workers and serially, taken from issue 32's measurement (never the old "~3 min / ~23 min"). It also gives the cache location `<build>/app_cache/parameter_selection/` and says that "Clear app cache" (button or `steamstudy app --clear-cache`) removes it.
- [ ] `docs/releasing-an-app-bundle.md`:
  - step 4: making a bundle runs Parameter Selection for every carried Build (the measured time per Build); what the stale-cache warning means; `--skip-parameter-selection` is never acceptable for a release;
  - step 5: check that the mode opens on finished results with no Run, and that the provenance line names the maker's machine.
- [ ] `test_three_rules_and_running_guide_link` and any other guide test still pass.
