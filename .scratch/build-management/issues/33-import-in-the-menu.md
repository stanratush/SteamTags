# 33: Import in the Build menu

**What to build:** "Import data…" in the Build menu: a file picker for the CSV and an optional `attributes.csv`, a dropdown to choose the filter column, the same validation as `steamstudy import`, and on failure the errors table with a bg message per code. A new Import appears in the tree with its "Import defaults" root.

**Blocked by:** 26, 28

**Status:** done

Spec: [Build management spec](../spec.md): "Imports", "The Build menu" (Import data…). Decision ticket: [dataset import](09-dataset-import.md).

- [x] The upload goes through `dcc.Upload` into a temporary file, then the Dash-free validation from issue 25. Making an Import is separate from making its first Build.
- [x] The filter dropdown lists the uploaded file's non-reserved columns, plus "none".
- [x] On failure, the errors table shows file, row, column, code, value and message, with every code's message in the bg catalogue and a link to the `errors.csv` path. Warnings show on success.
- [x] A byte-identical re-import is refused with a link to the existing Import.
- [x] On success the tree gains the Import, with its "Import defaults" root ready to start a draft.
- [x] Hidden in App Bundles.
- [x] Tests:
  - A valid upload creates the Import.
  - An invalid upload shows the table and writes `imports/failed/`.
  - Every error and warning code has an en and a bg message (parity).

## Comments

## Implementation note

Import data… (`build_menu.import_dialog`/`import_columns`/`import_go`) decodes the `dcc.Upload` into a temporary file and runs issue 25's `make_import`. The filter dropdown lists the non-reserved columns plus "none". On failure it shows the errors table, with each code's message from the bg catalogue (`NON_LITERAL["build_menu"]`) and the `imports/failed/…/errors.csv` path. A byte-identical re-import is refused, naming the existing Import. On success the tree gains the Import with its "Import defaults" root. The dialog is hidden in App Bundles. Test: a valid upload, a re-import refused, an invalid upload in bg with `imports/failed`, and the filter options.
