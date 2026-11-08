# 25: Imports

**What to build:** `steamstudy import <file> [--filter <column>]` validates one wide UTF-8 CSV (plus an optional `attributes.csv`) all-or-nothing, and stores a fixed Import in `imports/<import_id>/` with normalised tables and `import.json`. A failure writes `imports/failed/<attempt_id>/errors.csv`. The validation is a Dash-free function, reused by the menu in issue 33.

**Blocked by:** none

**Status:** done

Spec: [Build management spec](../spec.md): "Imports". Decision ticket: [dataset import](09-dataset-import.md).

- [x] Reading: UTF-8 only (BOM stripped), comma, RFC 4180, header required, `.` decimals; other encodings and delimiters are refused with "save as CSV UTF-8"; no sniffing. Names are trimmed and NFC-normalised.
- [x] Header: `id`, `name`, `attributes` required; `score` optional; case-sensitive; duplicates refused. The filter column is named by `--filter` and must be filled for every item. Every other column is an extra numeric field (empty allowed).
- [x] Ids and attributes: positive integer item ids, unique; `;`-separated attribute names in order. With `attributes.csv`: unique positive ids and names covering every attribute used (mixing is refused), with unused rows warned and dropped. Without it: numbered 1…k in code-point name order.
- [x] Every error code and warning code from the spec is collected in one pass, each with a stable code string. Errors: `errors.csv` (`file, row, column, code, value, message`, spreadsheet row numbers) and a copy of the input under `imports/failed/<attempt_id>/`. The CLI prints counts per code and the first 20 rows, and exits non-zero.
- [x] Success: `imports/<import_id>/` (`import_id = <UTC timestamp>-<slug of file name>`) holds the original file verbatim, its sha256, the normalised tables (items with rank by score descending then file order, or file order; ordered item attributes; attribute ids and how they were assigned), and `import.json` (counts, filter field, score present, extra fields, warnings). It is never changed afterwards.
- [x] A byte-identical re-import (same sha256, including `attributes.csv`) is refused, pointing at the existing Import.
- [x] A loader for the normalised tables, used by the import adapter (issue 26) and the preview (issue 32).
- [x] `.gitignore` covers `imports/`.
- [x] Tests: one fixture CSV per error and warning code; a valid file with and without `attributes.csv`, with and without score and filter; row reordering doesn't renumber numbered attributes; the re-import refusal; a 50,001-item synthetic file warns.

## Comments

Implemented in `steamstudy/imports.py`: `validate_import` (Dash-free, every code in `ERROR_CODES` / `WARNING_CODES` with its English message, for the menu's bg catalogue in issue 33), `make_import`, `list_imports` and `load_import`. Normalised tables: `items.csv`, `item_attributes.csv`, `attributes.csv`, `item_fields.csv`. Fatal reading problems (`not_csv_utf8`, `not_comma_delimited`, `bad_csv`, `empty_file`) and header problems stop before the rows are checked. The CLI takes `--attributes <file>`, defaulting to an `attributes.csv` beside the file. Tests: `tests/test_imports.py`.
