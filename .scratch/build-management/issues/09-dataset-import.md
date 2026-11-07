# How does a dataset get imported?
Type: grilling
Status: resolved
Blocked by: 04, 05, 06

## Question

Charted: an imported dataset is items with ordered attributes, an optional score and optional numeric fields. The import plays the Snapshot's role (raw and fixed). The app stays a Steam tool, with a note for imported data.

On the [generic dataset contract](04-generic-dataset-contract.md), decide:
- the file format(s) the user supplies (one CSV with a delimited attribute column, or items plus item–attribute rows), the encoding and the id rules;
- validation and its error report (duplicate ids, empty attribute lists, non-numeric scores);
- where the import is stored, how it is identified, and that it never changes afterwards;
- which Build settings apply to an import (list size, [tags per game](05-tags-per-game-and-list-size.md), [named rules](06-named-exclusion-rules.md) as attribute rules, datasets defined by an attribute), and which are hidden (app types, content descriptors, Manual Metadata, the Observation Window);
- how the file supplies optional attribute ids, the filter field and extra numeric fields, and how its config names attributes.

Already settled by the contract: item ids are positive integers; every item needs at least one attribute and, where there is a filter field, a value in it; with no score, file order ranks the items and list size still applies; the app shows the filter field's name and range in place of Months Observed, and "ID" in place of "AppID".

Settled by [tags per game and list size](05-tags-per-game-and-list-size.md): an import's tags per game is 2 up to its longest list, or `all` (the default); list size is ≥ 10, and an import smaller than it fails the Build.

## Answer

Grilled with the researcher, 2026-11-07. Built on the [generic dataset contract](04-generic-dataset-contract.md) (ADR 0005), [named exclusion rules](06-named-exclusion-rules.md) point 7, and the import blockers in [Steam assumptions](../research/01-steam-assumptions.md).

1. **Name: Import.** The raw, fixed source that plays the Snapshot's role. One Import can define several Top-N Datasets, so "imported dataset" is avoided. Glossary entry added in [CONTEXT.md](../../../CONTEXT.md).
2. **File: one wide CSV.** `id,name,attributes[,score][,numeric fields…]`. `attributes` holds names separated by `;` in order, and a name containing `;` cannot be expressed. An optional `attributes.csv` (`id,name`) supplies attribute ids. Only one format is accepted.
3. **Text rules.** UTF-8 only (BOM stripped), comma delimiter, RFC 4180 quoting, header required, `.` as decimal point. Names are trimmed and NFC-normalised. Attribute names are case-sensitive, and names differing only by case trigger a warning. Other encodings and delimiters are refused ("save as CSV UTF-8"); nothing is sniffed.
4. **Header.** `id`, `name` and `attributes` are required; `score` is optional and reserved. Headers are case-sensitive and a duplicate is refused. The filter field is named at import (`--filter <column>` or a menu dropdown) and must be filled for every item. Every other column is an extra numeric field: empty cells are allowed and any non-numeric value refuses the import. With a `score` column, every item needs a score.
5. **`attributes.csv`.** Unique positive integer ids and unique names, covering **every** attribute used, because mixing supplied and numbered ids is refused. Unused rows trigger a warning and are dropped. Without the file, attributes are numbered 1…k in code-point name order.
6. **Validation is all-or-nothing, and every problem is collected in one pass.**
   - **Errors:** a missing required column; a bad or duplicate id; an empty name; an empty attribute list; an empty attribute between `;`s; an attribute repeated in one item; a bad or empty score, filter value or extra field (NaN and ±inf count as bad); `attributes.csv` problems; fewer than 10 items.
   - **Warnings:** case-only name clashes; duplicate item names; unused `attributes.csv` rows; more than 50,000 items or 5,000 distinct attributes (slow Builds). There is no hard size limit.
   - **Report:** a failure writes `imports/failed/<attempt_id>/errors.csv` (`file, row, column, code, value, message`, spreadsheet row numbers) plus a copy of the input. The CLI prints counts per code and the first 20 rows. The menu shows the table, with a bg message per code. Warnings are kept in the Import's `import.json`.
7. **Storage and identity.** `imports/<import_id>/` with `import_id = <UTC timestamp>-<slug of file name>`. It holds the original file verbatim, its sha256, the normalised tables (items, ordered item attributes, attribute ids and how they were assigned) and `import.json`. It is never changed: a corrected file is a new Import, and a byte-identical re-import is refused with a pointer to the existing one. Imports are not committed. Builds go under `builds/<import_id>/<build_id>/`, which reuses the Snapshot-parent layout, so blockers P4 and B1 need no change.
8. **How an Import is made.** `steamstudy import <file> [--filter <column>]`, or a Build-menu button with a file picker; both run the same validation. Making an Import is a step separate from making its first Build.
9. **Settings that apply:** list size per dataset; tags per game (2…longest list, or `all`); datasets by defining attribute; named attribute rules; Manual Exclusions and Overrides keyed by item id; Content Flags as attribute lists; Genre Tags; all report, analysis and network-default settings. **Hidden or absent:** app types, content descriptor ids, the Adult Only notice, Manual Metadata (a correction means a new Import), the Observation Window and `collection.toml`, and the fixed Steam rules.
10. **Naming attributes in config.** Numbered Imports name attributes by `name`; Imports with `attributes.csv` use `{ id, name }`, and both must match. An attribute missing from the Import's vocabulary **fails the Build**, unlike Steam's warning.
11. **Config files.** An import Build has `datasets`, `exclusions`, `exclusion_overrides`, `manual_exclusions`, `genres` (no genre-kind map), `analysis` and `network`, with no `collection` and no `manual_metadata`. The source marker picks the required set. Where config lives is decided by [Build identity](07-build-identity-and-lifecycle.md).
