# 07: Exclusion rules, overrides and Content Flags

**What to build:** The Build removes games from every Top-100 Dataset by the configured Exclusion rules. Each excluded game records every rule it matches, with detail and a `primary_reason`. Each removal shows the rank the game would otherwise have taken. The researcher's manual exclusions and Exclusion Overrides take effect, and Content Flags are exported per game without filtering anything.

**Blocked by:** 04

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Build" (Exclusion rules, Content Flags, Genre Tags), "Config".

- [x] Rules are evaluated in order: `store_data_unavailable`, `app_type`, `no_tags`, `adult_content`, `software_tag`, `dating_sim_tag`, `manual`. The first two short-circuit. All matches are recorded with detail, and `primary_reason` is the first match.
- [x] Tag lists are tag id + name pairs, matched on tag id. A configured tag id missing from the `GetTagList` snapshot gives a warning, not a failure.
- [x] `adult_content` fires on the Adult Only notice, content descriptor 3, or `Hentai` within its rank limit, and the detail names which signals fired. The spec's "never exclusion grounds" tags never exclude.
- [x] Rank limits: a global default ("anywhere in the 20") plus optional per-tag limits. "Has tag" for datasets and the network is unaffected.
- [x] `manual_exclusions.toml` entries (AppID, name, reason, at least one evidence URL with retrieval date, date added) exclude with reason `manual`. `exclusion_overrides.toml` entries cancel the named rule for that game. Entries missing a required field fail validation.
- [x] Content Flags `desktop_companion` and `sexual_content_tag` are matched anywhere in the 20 and exported in `top100_<dataset>.csv` `content_flags`. They never filter.
- [x] `reports/exclusions.csv` has one row per (AppID, matched reason) with detail, `primary_reason`, and would-be rank per dataset.
- [x] `completeness.csv` gains exclusion counts per reason, both overlapping and partitioned by primary reason.
- [x] Fixture tests cover Stardew Valley 413150 (Dating Sim farming game: excluded at the default rank limit, kept by an override), Bongo Cat 3419430 (Desktop Companion flag and Software tag), Banana 2923300 (manual exclusion), an Adult Only game, a software app, and a delisted / no-store-data app.

## Comments

- 2026-10-04 (agent): Implemented: ordered rules with short-circuit, rank limits, overrides (recorded in build.json exclusion_overrides_applied), manual exclusions, Content Flags, exclusions.csv with would-be ranks, overlapping/primary counts.
