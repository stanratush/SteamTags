# 26: Import Builds

**What to build:** a Build from an Import. It covers the reduced config set, Import defaults, attribute rules, Manual Exclusions and Overrides keyed by item id, `topn_<key>.csv` and `item_fields.csv`, the generic reports and analysis, the import adapter behind `read_dataset`, and `steamstudy build --import`. Import Builds open in the app and run the network, Parameter Selection and validation like Steam Builds.

**Blocked by:** 21, 22, 24, 25

**Status:** done

Spec: [Build management spec](../spec.md): "Import Builds", "Export schema", "The dataset seam", "Named Exclusion Rules" (imports). Decision tickets: [dataset import](09-dataset-import.md), [export schema](13-export-schema.md), [generic dataset contract](04-generic-dataset-contract.md).

- [x] Config for an Import Build: `datasets`, `exclusions` (named attribute rules: `attributes` + `rank_limit`; Content Flags as attribute lists; no app types, descriptor ids or Adult Only notice), `exclusion_overrides` and `manual_exclusions` keyed by item id, `genres` (no `genre_kind`), `analysis`, `network`. The source marker picks the required set.
- [x] Attributes named by `name` (numbered Imports) or `{ id, name }` (`attributes.csv` Imports), both checked. An unknown attribute fails the Build.
- [x] Import defaults: one dataset `overall`, List Size min(100, item count), Tag Depth `all`, no rules, Content Flags or Genre Tags, empty manual lists, and `analysis`/`network` copied from `config/`. `start_draft` (issue 24) uses them for an Import source.
- [x] Tag Depth for Imports: 2 up to the longest list, or `all`.
- [x] Build stage: the Eligible Pool is the Import minus its Exclusions (and, for a Tag-Specific Dataset, those that have its defining attribute within Tag Depth). Ranking uses the Import's rank. It writes `builds/<import_id>/<build_id>/` with exactly the files the registry (issue 22) lists for Import Builds. `completeness.csv` gets its `import` section, `ties.csv` is written only with a score, and `reports.html` shows the Import's warnings.
- [x] The feature analysis runs its generic sections only (tag frequency, combinations, associations, pool baseline, Content Flags). The genre, free-to-play and months sections, the "Puzzle" note and the archived categories are skipped.
- [x] `build.json`: `source: "import"`, `import_id`, `import_sha256`, `filter_field`, `score_present`, extra field names, and name/description/parent, with no Steam-only keys.
- [x] The import adapter in `read_dataset` reads `topn_<key>.csv` and `item_fields.csv`. The filter slider is labelled with the field name and takes its range from the data. Extra fields show in the inspector's item table.
- [x] `steamstudy build --import <import_id> [--config <dir>]`: Import defaults, or the reduced set in `--config`.
- [x] Opening a Network State export from an Import Build works. Its not-found message names the `import_id` (bg entry).
- [x] Tests:
  - A synthetic Import (with score, filter and an extra field; and one with none) builds deterministically: two Builds with a fixed `build_id` are byte-identical.
  - The app opens it. The Workbench, Removal Sensitivity, Parameter Selection (small grid) and export round-trip all work.
  - An attribute rule, a Manual Exclusion and an Override change the pool as expected. An unknown attribute fails.
  - No Steam-only file or column is written.

## Comments

Implemented in `steamstudy/build/import_build.py`. The written settings are resolved against the Import's vocabulary into the Steam shape (`resolve_settings`: rules and Content Flags list `attributes`, entries are keyed by `id`), so the Build's own `evaluate`, `rank_pool` / `slice_top` (now taking a rank key and a tie value) and analysis run unchanged; tables are assembled under their Steam names and converted to their Import variants at the end. `build.json` also carries `resolved_config` (every attribute with its id), which the app reads, since the Import is not shipped. Without a global rank limit, an Import's rules read every position. The Workbench keeps the filter sliders hidden when there is no filter field, so its callbacks still find them; the edge inspector's item table shows "ID" and the extra fields. Tests: `tests/test_import_builds.py`.
