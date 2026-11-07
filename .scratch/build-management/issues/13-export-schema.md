# What do the Top-N rename and Import Builds change in the export schema?
Type: grilling
Status: resolved
Blocked by: 04, 07, 09

## Question

Steam Builds keep writing `top100_<key>.csv` with its strict 17-column header ([generic dataset contract](04-generic-dataset-contract.md), ADR 0005). An Import Build has its own inputs, the Import's normalised tables ([How does a dataset get imported?](09-dataset-import.md)), and `build.json` gains `name`, `description` and `parent_build_id` ([Build identity](07-build-identity-and-lifecycle.md)).

Decide:
- the Import Build's dataset file: its name and columns (id, name, rank, score, filter field, extra numeric fields, attributes), and whether `top100_` gives way to a Top-N name for imports only or for new Steam Builds too;
- what the published export schema (`export/schema.py`) documents for each Build kind, and whether the schema version is bumped;
- the `dataset` column and `build_id` references in Network State exports: what changes when the Build is an Import Build, and that saved Steam exports still open (matched by the hash of `build.json`);
- which reports an Import Build writes (generic sections only), and their file names.

## Answer

Grilled with the researcher, 2026-11-07. Built on the [generic dataset contract](04-generic-dataset-contract.md) (ADR 0005), [Build identity](07-build-identity-and-lifecycle.md) and [How does a dataset get imported?](09-dataset-import.md). Glossary: the **Build** entry now names Steam Builds and Import Builds.

Facts found in the code: `export/schema.py` keys files `group/name` with fixed columns. Four reports hard-code `would_be_rank_<key>` for the five Steam keys, and `build/core.py:127` refuses any other dataset set. A saved export finds its Build by `build_id` plus the `build.json` hash (`app/export.py:185`), whatever the parent folder.

1. **Steam keeps `top100_<key>.csv`** in every Steam Build, whatever its list size. The schema description says the name dates from when N was always 100. The Steam adapter, collect, the loader and bundles are unchanged, and no Steam path or byte moves.
2. **Import dataset file: `datasets/topn_<key>.csv`**, one per dataset. No file name is shared by both kinds, so the source marker alone picks the adapter.
3. **Import dataset columns, a fixed strict header:** `dataset, rank, id, name, score, filter_value, tag_ids, tags`. `score` is empty when the Import has none, and `filter_value` is empty when it has no filter field. The filter field's name is in `build.json`, not in a header. The tag lists are the full ordered lists, and the reader cuts them to Tag Depth.
4. **Extra numeric fields: one long `datasets/item_fields.csv`** (`id, field, value`) per Build, for items in any Top-N Dataset, with no row for an empty cell. The schema stays fixed and the Build stays self-contained, ready for a Bundle without its Import.
5. **Templated column `would_be_rank_<dataset>`**, expanded once per dataset of the Build in config order, for both kinds. It is documented as one column per dataset key. With today's five Steam datasets, the columns and bytes are unchanged.
6. **Naming rule for Import variants.** Each has the same file name as its Steam counterpart. `appid` becomes `id`, matching the inspector's "ID". `tag_id`, `tag`, `tag_ids` and `tags` stay, since Tag means attribute. `mean_monthly_players` becomes `score`. Steam-only columns are dropped (`archived_category`, `months_observed`, `release_month`, `is_free`, genres and similar). The rule covers datasets, reports, analysis tables, network tables and app exports.
7. **The registry is keyed by Build kind.** `FileSchema` gains a `kind` (`steam` or `import`), and the registry key becomes `kind/group/name`. A file that does not differ is declared once for both kinds, and Import variants are derived from the Steam declarations by rule 6. `export.json` and `analysis.json` embed only the columns of their Build's kind. The schema docs and the guide's column index list Import variants in their own section, and writer validation stays strict for both kinds.
8. **`SCHEMA_VERSION` goes up once, 5 → 6**, for the whole effort. Steam `export.json` and `analysis.json` change only in that number and in description text ("Five datasets stacked" becomes "Every dataset stacked"). Opening a saved export checks `key_version`, so saved exports are unaffected.
9. **Import Build `build.json`** carries:
   - `source: "import"`.
   - `import_id` and `import_sha256` instead of `snapshot_id`.
   - `filter_field` (name or null), `score_present`, and the extra field names.
   - `name`, `description` and `parent_build_id`.

   It carries none of the Steam-only keys (`collection_date`, `observation_window`, `store_country`, `taglist_version_hash`, `manual_metadata_entries`, `source_substitutions`). `find_build` is unchanged. Saved Steam exports still open because old `build.json` files are never rewritten, so their hash still matches.
10. **Network State exports of Import Builds are unchanged.** That covers the `dataset` column, the zip name `steamstudy_<dataset>_<state_id>_<ts>.zip`, `state_key` (including `min_months`), and the embedded `build_json`. Only the not-found message changes: it names the Import (`import_id`), with a bg entry.
11. **Files an Import Build writes:**
    - **`datasets/`**: `build.json`, `topn_<key>.csv`, `item_fields.csv`. No `monthly_players.csv`.
    - **`reports/`**:
      - `exclusions.csv`, `impact_removals.csv` and `impact_near_misses.csv`.
      - `completeness.csv`, with only the `exclusions_overlapping`, `exclusions_primary` and `depth_check` sections, plus a new `import` section (items, attributes, warnings).
      - `ties.csv`, only when the Import has a score.
      - `reports.html`, showing the Import's warnings from `import.json`.
    - **`analysis/`**: `tag_frequency`, `combinations`, `associations`, `content_flags`, `resolution_sweep`, every `network_*` table, `removal_sensitivity`, `analysis.json`, `report.html`.
    - **Not written**: `parse_errors`, `placeholder_rows`, `tag_vocabulary`, `release_month_check`, `impact_adult_signals`, `impact_unexcluded` (its signals are Steam descriptors and store genres), `manual_metadata`, `steamdb_crosscheck`, `skipped_apps`, `genre_frequency`.
