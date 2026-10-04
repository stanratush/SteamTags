# User Guide scope and home
Type: grilling
Status: open
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
