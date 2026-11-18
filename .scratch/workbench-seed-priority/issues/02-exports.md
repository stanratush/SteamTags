# 02: Exports record the priority

**What to build:** both places a Parameter Selection result leaves the app record the Build's Workbench Seed Priority.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Workbench Seed Priority spec](../spec.md): "Exports", "Tests".

- [ ] `parameter_selection.json` has a top-level `workbench_seed_priority`, always, including when it is the default. It is also inside `selection_settings` through `asdict`.
- [ ] The Workbench export's `applied_from` block has `workbench_seed_priority` next to `workbench_gamma` and `workbench_seed`.
- [ ] `SCHEMA_VERSION` goes from 6 to 7, with the reason added to the version comment in `steamstudy.export.schema`. The field is declared wherever that module declares the JSON metadata fields.
- [ ] `selection_report.md`'s methods paragraph names the priority only for `main_seed`, so a default report is byte-identical (the en and bg templates both).
- [ ] Saved exports with `schema_version` 6 still open (Open Network State… and anything else that reads `applied_from`).
- [ ] Tests: `parameter_selection.json` has the field for both values. `applied_from` has it after Apply. A default `selection_report.md` is unchanged and a `main_seed` one names it. The schema-version assertions are updated to 7.

## Comments
