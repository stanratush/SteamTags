# 25: Imports

**What to build:** `steamstudy import <file> [--filter <column>]` validates one wide UTF-8 CSV (plus an optional `attributes.csv`) all-or-nothing, and stores a fixed Import in `imports/<import_id>/` with normalised tables and `import.json`. A failure writes `imports/failed/<attempt_id>/errors.csv`. The validation is a Dash-free function, reused by the menu in issue 33.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Imports". Decision ticket: [dataset import](09-dataset-import.md).

- [ ] Reading: UTF-8 only (BOM stripped), comma, RFC 4180, header required, `.` decimals; other encodings and delimiters are refused with "save as CSV UTF-8"; no sniffing. Names are trimmed and NFC-normalised.
- [ ] Header: `id`, `name`, `attributes` required; `score` optional; case-sensitive; duplicates refused. The filter column is named by `--filter` and must be filled for every item. Every other column is an extra numeric field (empty allowed).
- [ ] Ids and attributes: positive integer item ids, unique; `;`-separated attribute names in order. With `attributes.csv`: unique positive ids and names covering every attribute used (mixing is refused), with unused rows warned and dropped. Without it: numbered 1…k in code-point name order.
- [ ] Every error code and warning code from the spec is collected in one pass, each with a stable code string. Errors: `errors.csv` (`file, row, column, code, value, message`, spreadsheet row numbers) and a copy of the input under `imports/failed/<attempt_id>/`. The CLI prints counts per code and the first 20 rows, and exits non-zero.
- [ ] Success: `imports/<import_id>/` (`import_id = <UTC timestamp>-<slug of file name>`) holds the original file verbatim, its sha256, the normalised tables (items with rank by score descending then file order, or file order; ordered item attributes; attribute ids and how they were assigned), and `import.json` (counts, filter field, score present, extra fields, warnings). It is never changed afterwards.
- [ ] A byte-identical re-import (same sha256, including `attributes.csv`) is refused, pointing at the existing Import.
- [ ] A loader for the normalised tables, used by the import adapter (issue 26) and the preview (issue 32).
- [ ] `.gitignore` covers `imports/`.
- [ ] Tests: one fixture CSV per error and warning code; a valid file with and without `attributes.csv`, with and without score and filter; row reordering doesn't renumber numbered attributes; the re-import refusal; a 50,001-item synthetic file warns.

## Comments
