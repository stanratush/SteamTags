# 33: Import in the Build menu

**What to build:** "Import data…" in the Build menu: a file picker for the CSV and an optional `attributes.csv`, a dropdown to choose the filter column, the same validation as `steamstudy import`, and on failure the errors table with a bg message per code. A new Import appears in the tree with its "Import defaults" root.

**Blocked by:** 26, 28

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Imports", "The Build menu" (Import data…). Decision ticket: [dataset import](09-dataset-import.md).

- [ ] The upload goes through `dcc.Upload` into a temporary file, then the Dash-free validation from issue 25. Making an Import is separate from making its first Build.
- [ ] The filter dropdown lists the uploaded file's non-reserved columns, plus "none".
- [ ] On failure, the errors table shows file, row, column, code, value and message, with every code's message in the bg catalogue and a link to the `errors.csv` path. Warnings show on success.
- [ ] A byte-identical re-import is refused with a link to the existing Import.
- [ ] On success the tree gains the Import, with its "Import defaults" root ready to start a draft.
- [ ] Hidden in App Bundles.
- [ ] Tests:
  - A valid upload creates the Import.
  - An invalid upload shows the table and writes `imports/failed/`.
  - Every error and warning code has an en and a bg message (parity).

## Comments
