# 31: Export tables

**What to build:** "Export tables" in the Run section writes one record-only zip per settings key: seven stacked tables, `parameter_selection.json` and a templated `selection_report.md`. The new files are declared in the export schema (`SCHEMA_VERSION` 3) and documented in ch. 4 and Appendix B.

**Blocked by:** 29, 30

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Exports", the labels, "Methods paragraph".

- [x] `export/schema.py` gains a `parameter_selection` group with the seven files and every column the spec lists, each with `column_attrs` (help key, guide entry, app panel). `SCHEMA_VERSION = 3`, with a comment naming this feature.
- [x] A Dash-free writer (for example `export/parameter_selection.py`) builds, from the cache and the current constraints:
  - `pairs.csv`, `admissible_partitions.csv`, `neighbour_links.csv`, `selected_partitions.csv`, `selection.csv` (with the constraints label and `settings_label`), `validation_replicates.csv` and `validation_clusters.csv`, stacked by `dataset`, covering complete grids only;
  - `parameter_selection.json`: keys and hashes; Selection Settings and both labels; the grid (ranges, step, `gm22_gamma_max_n_e`, scan seeds, pass cap); every seed stream with seeds; R, S and per-pair g′ / s′; constraints, tolerance and overrides; method and software versions; `build.json`; per-dataset status and `computed_with`; each file's rows, SHA-256 and `columns`;
  - `selection_report.md`: per dataset, the explanation and validation block from `selection_text`, then `METHODS_TEMPLATE` rendered with the run's numbers.
- [x] The zip is named `steamstudy_parameter-selection_<settings_key_hash[:12]>_<UTC>.zip`. The button is disabled only when no dataset is complete. Incomplete datasets are listed in the JSON as "partial, k of 153" / "not run", and unvalidated complete grids as validation `not_run`.
- [x] **Ch. 4** gets a paragraph per new file. The committed column index (Appendix B, `export/column_index.py`) is regenerated.
- [x] Tests:
  - On a cache fixture (two complete datasets, one partial, one validated pair): the zip holds the expected files, row counts (153 per complete dataset) and hashes matching the JSON.
  - Partial datasets are absent from the tables.
  - Two exports of the same cache give byte-identical tables.
  - Custom constraints change `selection.csv` and the labels but no key.
  - The existing guide tests pass (every column has an entry, every file has a ch. 4 paragraph, the column index isn't stale).

## Comments

- 2026-10-27, implementation: Implemented in `export/schema.py` (`parameter_selection` group, `SCHEMA_VERSION = 3`) and the Dash-free writer `app/ps_export.py` (in `app/`, not `export/`, because it reads the app cache). Appendix B regenerated.
