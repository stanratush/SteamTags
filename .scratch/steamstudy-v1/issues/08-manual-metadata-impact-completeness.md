# 08: Manual Metadata Entries, impact report and completeness

**What to build:** The researcher can add back a game the Steam store cannot provide through a sourced Manual Metadata Entry: a full entry, or tags-only for a `no_tags` game. The Build then reviews every exclusion rule's effect in an impact report and publishes the full completeness report, including the depth check that shows whether declined games were caught.

**Blocked by:** 07

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Build" (Manual Metadata Entry, Build folder reports).

- [ ] In `manual_metadata.toml` every field is `{value, source_url, retrieved}`. An unsourced field is rejected.
- [ ] A full entry needs tags (in display order), `app_type`, store genres, `is_free`, release date and `adult_only`. A tags-only entry is allowed only for a `no_tags` game.
- [ ] An entry for an app the store does provide fails the Build.
- [ ] Entries are applied after store parsing and before exclusion. Added games then go through every rule and can rank, flagged `metadata_source = manual` / `manual_tags`.
- [ ] `reports/manual_metadata.csv` copies every citation, and `build.json` lists the entries used.
- [ ] `impact_*.csv` reports:
  - removals per rule and per tag or signal, with would-be ranks;
  - near-misses (exclusion tags present beyond their rank limit);
  - Adult Only vs descriptor 3 disagreements;
  - Top-100 games no rule excluded that carry descriptor 1 or 4, a software store genre, or a Content Flag.
- [ ] `completeness.csv` is complete: listing rows, scored apps, scored `game` apps, per-pass stats, exclusion counts, the unscored three-way split, the Placeholder Row count, and the depth check (each dataset's members' `top_listing_rank`, including the deepest).
- [ ] Fixture tests cover a full entry, a tags-only entry, a rejected unsourced entry, an entry for a store-provided app (Build fails), and the impact rows for the Dating Sim near-miss.
