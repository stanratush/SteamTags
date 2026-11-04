# 20: Export schema 5: `validation_pairs.csv` and the new columns

**What to build:** the Parameter Selection export carries the new figures. A new `validation_pairs.csv` holds one row per validated pair (the Null Comparison's state, D, U, the width count and the flags). `validation_clusters.csv` and `validation_replicates.csv` gain their new columns. `SCHEMA_VERSION` goes from 4 to 5, and the column index and Appendix B follow.

**Blocked by:** 16

**Status:** done

Spec: [Validation review spec](../spec.md): "Export: schema 5", "Resolved while writing this spec". Sources: [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md), [What do the User Guide's validation passages … say?](13-guide-and-context-wording.md) (§5, the `04-files` descriptions).

- [x] **`validation_pairs.csv`** (new, before `validation_replicates.csv` in the zip): `dataset`, `g`, `s`, `resolution`, `observed_q`, `observed_q_selected`, `null_state`, `replicates`, `q_defined`, `q_undefined`, `q_undefined_no_edges`, `q_undefined_beyond_scan`, `reach`, `width_observed`, `width_null_median`, `width_wider`, `width_equal`, `width_compared`, `weak_null`, `rarely_assessable`.
- [x] **`validation_clusters.csv`**: adds `size`, `dissolved_in_most` (replacing `dissolved`), `dissolution_frequency`, `wilson_low`, `wilson_high`, `borderline`, `assessable`, `recovered`, `recovery_frequency`, `recovery_wilson_low`, `recovery_wilson_high`, `mean_jaccard_se`, `mean_whole_cluster_jaccard`. `mean_jaccard`, `at_most_half` and `present` are re-described for Hennig's Jaccard and B*.
- [x] **`validation_replicates.csv`**: adds `perturbation_share`, `beyond_scan`, `null_q_envelope`, `q_defined`, `edged_share`, `at_resolution_changed`; `null_q` is the final Q.
- [x] Every column declared in `export/schema.py` with its "Explained in" anchor (`null-comparison` / `subsample-stability`); `SCHEMA_VERSION = 5`; `guide_index` updated; Appendix B regenerated with `python -m steamstudy.export.column_index`, in English and Bulgarian (schema tips in `i18n/bg/schema_tips.py`).
- [x] `ps_export` builds every row from the derived summary and the records; the report and `method_versions` read `ps-validation-2`.
- [x] Tests: the zip lists eight tables; each new column is filled on a validated test pair; the schema, `guide_index`, Appendix B staleness and catalogue parity tests pass; an older export still opens (`recorded_table_hashes_match` compares on its own columns, as for schema 4).
- [x] The full test suite passes.

## Comments

- 2026-11-05 (agent): Done in aa85254, plus one review fix: `at_resolution_changed` is empty, not false, on a degenerate at-resolution row, since no partition exists there.
- The zip lists eight tables, `validation_pairs.csv` before `validation_replicates.csv`. Every new column is checked as filled on the test Build's validated pair (`test_the_export_has_eight_tables_and_the_validation_figures_of_schema_5`). A schema-4 app export still opens and its table hashes match (`test_a_version_4_export_still_opens_and_matches_its_recomputation`). Appendix B is regenerated in both languages. The 04-files descriptions (guide-text §5) went in here, because the chapter 4 test requires a paragraph for every declared file.
- No Bulgarian schema tips were needed: the Parameter Selection columns are not shown in a grid, and the parity test passes.
- Full suite: 635 passed.
