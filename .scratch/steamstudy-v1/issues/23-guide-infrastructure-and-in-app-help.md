# 23: Guide infrastructure and in-app help

**What to build:** The User Guide is kept in step with the code. Every exported column's schema declaration names its guide entry, app panel and report section. The alphabetical column index is generated from the schema. Tests fail the moment the guide goes stale. In the app, every metric label and column header shows its one-line description as a tooltip, and a `?` on each panel opens the matching guide section offline.

**Blocked by:** 18, 19, 22

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Export schemas" (Single source), "App" (Help), "User Guide and Running Guide".

- [ ] Every column declaration gains `guide_entry` (an anchor in chapter 3), `app_panel` and `report_section`. `schema_version` is bumped.
- [ ] A generator writes Appendix B (alphabetical column index: column, file(s), app panel, report section, link to entry), and the output is committed.
- [ ] The guide skeleton exists: one Markdown file per part (chapters 0–6, Appendices A–C), with headings for every anchor the schema and app reference. Prose follows in tickets 24 and 25.
- [ ] Tests fail when the committed index is stale; when a column has no `guide_entry` or its anchor has no heading; when a schema-declared file is missing from chapter 4; when an in-app `?` anchor has no guide heading.
- [ ] Tooltips on every metric label and table column header use the schema descriptions.
- [ ] `?` on each panel renders the matching guide section with `dcc.Markdown`, offline, from guide files shipped as package data.
