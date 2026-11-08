# 22: Export schema by Build kind

**What to build:** the schema registry is keyed by Build kind (`steam` / `import`). Import variants are derived from the Steam declarations by one rule, the Import-only files are declared, and `SCHEMA_VERSION` goes to 6. Steam output changes only in the version number and description text.

**Blocked by:** 20

**Status:** done

Spec: [Build management spec](../spec.md): "Export schema". Decision ticket: [export schema](13-export-schema.md).

- [x] `FileSchema` gains `kind`, and the registry key becomes `kind/group/name`. A file that does not differ is declared once for both kinds.
- [x] One derivation function builds each Import variant from its Steam declaration:
  - same file name;
  - `appid` → `id`, `mean_monthly_players` → `score`;
  - `tag_id`, `tag`, `tag_ids`, `tags` kept;
  - Steam-only columns dropped (`archived_category`, `months_observed`, `release_month`, `store_release_date`, `is_free`, `app_type`, genre columns, `metadata_source`, `top_listing_rank`);
  - "Steam tag id." reads "Attribute id."
- [x] Import-only declarations: `datasets/topn_<key>.csv` (`dataset, rank, id, name, score, filter_value, tag_ids, tags`), `datasets/item_fields.csv` (`id, field, value`), and the `import` section of `completeness.csv`.
- [x] The files an Import Build writes and does not write (spec, "Files an Import Build writes") are data in the registry, so issue 26 and the docs generator read them from there.
- [x] `export.json` and `analysis.json` embed only their Build kind's columns. Writer validation is strict for both kinds.
- [x] `SCHEMA_VERSION = 6`. Steam description text says "Every dataset stacked", and the `dataset` column no longer lists five keys. bg schema tips updated.
- [x] The schema docs and the column-index generator list Import variants in their own section. (The guide text is issue 35.)
- [x] Tests:
  - The test Build's Steam `export.json` and `analysis.json` differ from before only in `schema_version` and the changed descriptions.
  - Each Import variant matches the derivation rule, and no Import declaration contains a dropped Steam column.
  - A saved Network State export from schema 5 still opens.

## Comments

- 2026-11-08 (implementation): done in `export/schema.py`. The registry is keyed `<kind>/<group>/<name>` (a bare `<group>/<name>` still means Steam); a Steam file whose derived variant is identical is declared once with kind `both`. `import_variant` is the one derivation rule; besides the ticket's renames it maps `appids` → `ids` (the plural of `appid`, in `edges.csv` / `network_edges.csv`) and rewrites "Steam AppID" / "Mean Monthly Players" in descriptions. `IMPORT_NOT_WRITTEN`, `IMPORT_BUILD_TEXT_FILES`, `IMPORT_BUILD_CONDITIONS` and `import_build_paths()` hold the Import Build file list for issue 26 and the docs. `columns_block(schemas, kind=...)` refuses a file of the other kind, and `analysis.json`, `export.json` and the Parameter Selection zip pass their Build's kind (`build_kind(build_json)`); the Build stage and the app still hand it the Steam files, so issue 26 must pick the Import variants (`REGISTRY.variant`) or the call fails loudly. Import `exclusions.csv` `name` reads "Item name from the Import."; other kept columns keep Steam's "game" wording (spec: Steam wording kept). `column_defs`/`GRIDS` take a `kind`, so the parity test covers the Import tooltips (bg: "Attribute id."). Appendix B is regenerated: `would_be_rank_<dataset>` is one row, and a generated *Import Builds* section follows; chapter 4 has short `topn_<dataset>.csv` and `item_fields.csv` paragraphs (en, bg) because the chapter-4 test requires one per declared file (the full guide text stays issue 35). `tests/fixtures/schema5_columns.json` keeps the schema-5 columns blocks; the golden hashes moved only in `analysis/analysis.json`, whose sole change is `schema_version`.
