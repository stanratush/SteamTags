# 20: Feature-analysis tables

**What to build:** Every Build writes the per-dataset feature-analysis tables for each full Top-100 Dataset (one count per game, no Minimum Months Filter):
- tag and genre frequencies against the Eligible Pool, with `share_ratio`;
- tag combinations up to the configured size, with support, k-way lift and pair confidence;
- every pairwise association, with phi, lift, Jaccard, Fisher p and within-dataset BH q;
- Content Flag counts and flagged games.

**Blocked by:** 07

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Feature analysis", "Export schemas" (Build `analysis/` folder).

- [x] `tag_frequency.csv`: every tag on at least one game, with count, share, `median_position`, `defining_tag` (true and 100% for the defining tag), `baseline_count`, `baseline_share` (Eligible Pool, Top 100 included), `share_ratio`, `archived_category`. Sorted by count desc, ties by name.
- [x] `genre_frequency.csv`: every store-genre value with `genre_id` and the config `kind`, with nothing dropped, plus the baseline columns.
- [x] `combinations.csv`: sizes 2…`max_itemset_size` with support ≥ `min_support`. `lift = support_count × N^(k−1) / (product of member counts)` with N = 100. Pair confidences both ways. A triple is dropped when its support equals a sub-pair's. The defining tag is excluded.
- [x] `associations.csv`: every pair of tags each reaching `min_support`, including zero co-occurrence. phi is empty when a tag is on all 100 games, but that row keeps lift 1, a defined Jaccard, and Fisher p = 1 in the BH family. BH runs within each dataset. Sorted by |phi| desc, empty last. No "significant" column. The defining tag is excluded.
- [x] `content_flags.csv` is in long form. `analysis.json` gains the Eligible Pool size and per-flag counts (zeros included) per dataset.
- [x] Every table is declared in the schema, with `dataset` first and the five datasets stacked.
- [x] Hand-built tests: lift at k = 2 equals the pair formula; a hand-computed k = 3 lift; triple pruning; phi n/a at count 100; BH within one dataset only.

## Comments

- 2026-10-04 (agent): Implemented: analysis/features.py (tag/genre frequency vs Eligible Pool, combinations with triple pruning, associations with phi/lift/Jaccard/Fisher/BH, content_flags long form). archived_category comes from a package-data mapping generated from research note 04 (multiple categories joined with ' / '). The combination lift uses N = the dataset's game count (100 for a full Build).
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
