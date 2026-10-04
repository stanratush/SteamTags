# User Guide scope and home
Type: grilling
Status: resolved
Blocked by: none

## Question

The metric reference's content ([User Guide metric reference](26-user-guide-metric-reference.md)) and form ([User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md)) are settled. What does the rest of the User Guide cover, and where does it live?

- **Coverage beyond metrics**: which of these does it include, and in how much depth?
  - how to run the pipeline (Collect, Build, the full-run gate) and the app;
  - what each app control does;
  - how to cite a Network State by its `state_id`;
  - how to read the exports (`top100_<dataset>.csv`, the Build's CSVs, the app's zip, `export.json` / `build.json` provenance);
  - the known limitations, which are currently fog on the map.
- **Home**: an appendix of the spec, Markdown in the repo's `docs/`, in-app help, or a mix. If a mix, which part is the single source, and how do the others stay in step with it? For example, can the in-app help text and the column index be generated from `steamstudy.export.schema`'s column descriptions?
- **Audience boundary**: the guide addresses a researcher without network-analysis training. Does operator material (rate limits, the pre-run checklist, the Snapshot layout) belong in it or in a separate operator README?

Graduated from the map's "User Guide beyond metrics" fog.

## Answer

Resolved 2026-10-04 with the researcher, over two rounds. The User Guide is Markdown in the repo, the single source for its prose. Code keeps its generated parts and in-app help in step with `steamstudy.export.schema`. Running instructions go in a separate Running Guide. One spec change: the app can reopen a Network State from its export.

**Documents and audience**
- **User Guide**: `docs/user-guide/`, Markdown, one file per part, English only in v1. It addresses a researcher without network-analysis training who reads and uses results. It is the single source for all hand-written guide prose.
  - The spec gets a "User Guide" section that fixes the outline below and the required content of each part, not the prose.
  - The prose is written during implementation, against the real column names.
- **Running Guide**: `docs/running-guide.md`, for whoever runs the pipeline, assuming technical skill. The User Guide links to it in one line. Contents:
  - install: `uv`, Python 3.14, `--compile-bytecode`;
  - the TOML configs;
  - Collect: resuming, rate limits, the hard stop on challenges;
  - Build, and the test Snapshot;
  - the full-run gate mechanics: what it checks, how a met condition is recorded;
  - the Snapshot and Build layouts;
  - `--allow-parse-errors` (such Builds are never published);
  - Windows notes from [Dash spike re-run on Python 3.14](22-dash-spike-python-314.md): `127.0.0.1`, `-W default`, explicit UTF-8.
- **Pre-run checklist** (Steam Charts operator reply, ethics check, SteamDB email): stays in the spec as a one-time project obligation. The Running Guide links to it. Anyone reusing the software has different obligations.
- "Operator" keeps its existing meaning on the map, the Steam Charts site operator. It is not used for the person running the pipeline.

**User Guide outline**
0. **Three rules**, before everything:
   - no number shows a cause;
   - clusters carry no meaning;
   - quote the `state_id` with every network number.
1. **Getting started**: open the app, load a dataset, the two modes.
2. **App controls**:
   - a control-by-control reference table: what the control does, its range and default, the Network State field it sets, and which numbers change (extends the research draft's settings table);
   - 4–5 short task recipes (e.g. check whether a cluster survives removing its center, compare Louvain vs Leiden, export a state for a paper);
   - no screenshots.
3. **Metric reference**: concept order, in the form fixed by [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md), with content from [User Guide metric reference](26-user-guide-metric-reference.md).
4. **What's in each file**: hand-written, one paragraph per file (`top100_<dataset>.csv`, each Build CSV, each file in the app zip, `snapshot.json` / `build.json` / `export.json` / `analysis.json`). Each paragraph says what one row is, what the file joins to, and what it is for.
5. **Citing and reproducing a Network State**: quote the `state_id`, deposit the export zip, cite the software version, and reopen the state with Open Network State.
6. **Known limitations**: the single home of the full list. Its content moves from the map's fog into Spec assembly.
- **Appendix A**: published rules of thumb, and why this guide does not use them.
- **Appendix B**: alphabetical column index, generated.
- **Appendix C**: references. The guide cites only sources verified at page level (see [Citation verification for the User Guide](30-citation-verification.md)).

**Kept in step by code** (schema changes bump `schema_version`)
- Each column declaration in `steamstudy.export.schema` gains three fields: `guide_entry` (an anchor in chapter 3), `app_panel` and `report_section`.
- Appendix B is generated from the schema and committed.
- Tests fail when any of these happens:
  - the committed column index is stale;
  - a column has no `guide_entry`, or its anchor has no heading;
  - a file the schema declares is missing from chapter 4;
  - an in-app `?` anchor has no matching guide heading.

**In-app help**
- Every metric label and table column header shows its one-line schema description as a tooltip.
- A `?` on each panel opens the matching guide section inside the app:
  - rendered with `dcc.Markdown`, offline;
  - from `docs/user-guide/`, shipped as package data.

**Spec change: Open Network State…** (app)
- Loads an export zip directly (no unzipping) or its `export.json`.
- Finds the Build by the path in the copied `build.json`, with a file picker if it has moved.
- **Refuses** if the Build's hash differs from the copied `build.json`, or if `key_version` differs: the same settings could give different numbers.
- **Accepts** an older `schema_version` as long as the key fields can be read.
- **Restores**:
  - every key field, then recomputes and shows ✓ / ✗ for equality between the recomputed and the recorded `state_id`;
  - when `layout_source = relayout`, the exported x/y as the Re-layout positions, so the figure looks the same, not only computes the same;
  - the zip's Removal Sensitivity results, shown and marked "loaded from export", not rerun.

**Feature-analysis report**: ends with a fixed template paragraph, not generated from the guide, naming the limitations that bear on every reading:
- tags are a current snapshot, not historical;
- the Top 100 is a ranked selection, not a sample;
- the partition comes from a single clustering run;
- Steam Charts has coverage gaps.

It links to chapter 6.

Extends [Export schemas for the app and the feature analysis](24-export-schemas.md) (schema fields) and [Tag network app interaction prototype](14-tag-network-app-prototype.md) (tooltips, `?`, Open Network State). No glossary change: the guides are documents, not domain terms. No ADR: easy to reverse.
