# 22: Export schema by Build kind

**What to build:** the schema registry is keyed by Build kind (`steam` / `import`). Import variants are derived from the Steam declarations by one rule, the Import-only files are declared, and `SCHEMA_VERSION` goes to 6. Steam output changes only in the version number and description text.

**Blocked by:** 20

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Export schema". Decision ticket: [export schema](13-export-schema.md).

- [ ] `FileSchema` gains `kind`, and the registry key becomes `kind/group/name`. A file that does not differ is declared once for both kinds.
- [ ] One derivation function builds each Import variant from its Steam declaration:
  - same file name;
  - `appid` → `id`, `mean_monthly_players` → `score`;
  - `tag_id`, `tag`, `tag_ids`, `tags` kept;
  - Steam-only columns dropped (`archived_category`, `months_observed`, `release_month`, `store_release_date`, `is_free`, `app_type`, genre columns, `metadata_source`, `top_listing_rank`);
  - "Steam tag id." reads "Attribute id."
- [ ] Import-only declarations: `datasets/topn_<key>.csv` (`dataset, rank, id, name, score, filter_value, tag_ids, tags`), `datasets/item_fields.csv` (`id, field, value`), and the `import` section of `completeness.csv`.
- [ ] The files an Import Build writes and does not write (spec, "Files an Import Build writes") are data in the registry, so issue 26 and the docs generator read them from there.
- [ ] `export.json` and `analysis.json` embed only their Build kind's columns. Writer validation is strict for both kinds.
- [ ] `SCHEMA_VERSION = 6`. Steam description text says "Every dataset stacked", and the `dataset` column no longer lists five keys. bg schema tips updated.
- [ ] The schema docs and the column-index generator list Import variants in their own section. (The guide text is issue 35.)
- [ ] Tests:
  - The test Build's Steam `export.json` and `analysis.json` differ from before only in `schema_version` and the changed descriptions.
  - Each Import variant matches the derivation rule, and no Import declaration contains a dropped Steam column.
  - A saved Network State export from schema 5 still opens.

## Comments
