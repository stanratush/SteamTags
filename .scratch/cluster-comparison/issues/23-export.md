# 23: Export CSV: six tables and `comparison.json`

**What to build:** the header's Export CSV button downloads every pair of included datasets, whatever is on screen, as one zip of six CSVs and `comparison.json`, named with the `comparison_id`. The columns are declared in `schema.py`, documented in the User Guide and derived for Import Builds.

**Blocked by:** 18

**Status:** done

Spec: [Cluster Comparison spec](../spec.md): "Export", "Comparison State" (record only), "Documentation and in-app help" (Ch. 4, Appendix B). Decisions: tickets [09](09-comparison-identity-and-export.md), [11](11-names-and-readings.md), [14](14-defining-tag-in-a-match.md).

- [x] **The zip** `steamstudy_cluster-comparison_<comparison_id>_<UTC timestamp>.zip`, written by `app/cc_export.py` (after `ps_export`) from the pair memo, whole; A is always the earlier dataset in the Build's order; tables byte-identical for the same inputs.
- [x] **Six CSVs** with the spec's columns: `datasets.csv`, `clusters.csv` (One-Tag Clusters included), `pairs.csv`, `matches.csv` (every match regardless of the minimum, with the unshared-Tag group counts and game counts), `cluster_flags.csv` (only the minimum-free flags plus `best_jaccard`), `match_games.csv` (unclipped).
- [x] **`schema.py`:** a new group `cluster_comparison`; `SCHEMA_VERSION` 6 → 7; every column with its description, guide entry and panel per the file's conventions; final column names follow its conventions.
- [x] **`comparison.json`:** the full key and `comparison_id`, schema and software versions, Build provenance, the `columns` block generated from `schema.py`, the minimum on screen (information only) and the caution from the sentences module. No `.md` report.
- [x] **Import Builds:** declared as Steam files; `import_variant` derives the Import ones (`appid` → `id`, Steam-only columns per the rule).
- [x] **The button:** right of the header, disabled while computing, its help text in en and bg (`comparison.export`).
- [x] **Docs:** Ch. 4 describes the zip, the six CSVs and `comparison.json`; Appendix B lists the new columns; both mirrored in bg; the committed column index regenerated.
- [x] Tests: the zip holds the six files and `comparison.json` for a fixture comparison; two exports of the same inputs give byte-identical tables; the export includes pairs not on screen and matches below the minimum; an Import Build's files use `id`; the schema, column-index and guide tests pass.
