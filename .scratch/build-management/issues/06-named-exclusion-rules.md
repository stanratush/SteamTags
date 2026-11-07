# How do named exclusion rules work?
Type: grilling
Status: resolved
Blocked by:

## Question

Charted: tag-based Exclusion rules become **generic named rules** (a name, a tag list, optional name-only matches and, for Steam, content descriptor ids). Adult content and Dating Sim stay separate defaults, and an Exclusion Override targets one named rule.

Decide:
- a rule's fields and their validation (unique names, tag ids checked against the GetTagList snapshot, empty rules);
- which rules stay fixed rather than named and editable (`store_data_unavailable`, `app_type`, `no_tags`, `manual`), and which can be overridden;
- how `exclusions.csv`, the impact reports and `build.json` record named rules;
- moving the current `exclusions.toml` over, so a Build from today's config gives byte-identical datasets;
- how a `build.json` from before the change still loads in the app;
- whether Content Flags become named rules of the same shape, since they are already tag lists;
- the glossary entry for Exclusion.

Already settled by [tags per game](05-tags-per-game-and-list-size.md): rules and Content Flags read the full displayed list, and rank limits count positions in it, independent of tags per game.

## Answer

Grilled with the researcher, 2026-11-07. Code read at `src/steamstudy/build/exclusion.py`, `config.py` (`_exclusions`), `export/schema.py`.

**Facts that shaped it.** `adult_content` is not a plain tag rule: it fires on the store's Adult Only notice (hard-coded today), descriptor 3 or the Hentai tag. `primary_reason` is the first match in the fixed order `store_data_unavailable → app_type → no_tags → adult_content → software_tag → dating_sim_tag → manual`. Rank limits are shared (`global_rank_limit`, `per_tag_rank_limit` by tag id, empty). The app never parses the exclusion config in `build.json` (versions, banners, hash only). An unknown tag id is a warning today.

1. **A named rule** is one ordered `[[rule]]` entry in `exclusions.toml`: `name` (code written to `exclusions.csv`, the impact reports and overrides; `[a-z0-9_]`), `label` (menu wording), `tags` (id + name, each optionally with its own `rank_limit`), `name_only`, and for Steam `content_descriptor_ids` and `adult_only_notice` (bool; today's hard-coded signal becomes a setting). Defaults keep the codes `adult_content`, `software_tag`, `dating_sim_tag`.
2. **Fixed vs named.** `store_data_unavailable`, `app_type`, `no_tags` stay fixed and run first; `manual` stays fixed and runs last. Named rules run between them in file order; the menu can reorder them, because order decides `primary_reason`.
3. **Rank limits.** `global_rank_limit` stays global (1–20). The per-tag limit moves onto the tag entry inside its rule; `per_tag_rank_limit` is removed (empty today). A tag can have different limits in different rules.
4. **Validation (the Build fails):** duplicate rule names; a name equal to a fixed rule code; a rule with no signal (no tags, name-only, descriptor ids or notice); a limit outside 1–20. A tag id missing from GetTagList stays a warning (the menu only offers vocabulary tags). A tag may appear in two rules; both match.
5. **Overrides** target `app_type`, `no_tags` or any named rule; never `store_data_unavailable` (use a Manual Metadata Entry) or `manual` (remove the entry). An override naming a rule that does not exist fails the Build. Renaming a rule in the menu renames its overrides; deleting one asks to drop them.
6. **Content Flags** stay a separate list with the same `name`/`label`/`tags`/`name_only` shape and editor; no descriptor ids, no rank limit (anywhere), never filter.
7. **Imports get Exclusions, reduced:** named rules over attributes (`attributes` + `rank_limit`, no Steam fields), Manual Exclusions and Overrides keyed by item id, no fixed Steam rules, Content Flags as attribute lists. The pool is the import minus its Exclusions. File details go to [How does a dataset get imported?](09-dataset-import.md).
8. **Old Builds.** A new `build.json` records the new shape; old Builds are never rewritten. One config reader accepts the old shape (`adult_content`/`software_tag`/`dating_sim_tag` tables + `per_tag_rank_limit`) and converts it to named rules; only Duplicate and a rebuild need it. Byte-identity covers the datasets and reports; `build.json` itself changes with the config shape.
9. **`impact_adult_signals.csv`** is written for the rule named `adult_content`, reading its descriptor ids and tags; columns keep their names, descriptions say "the rule's descriptor ids / tags (default 3 / Hentai)". No such rule: headers only.
10. **`impact_unexcluded.csv`**: descriptors 1 and 4 and software store genres stay fixed Steam diagnostics, not settings, tied to no rule; Content Flags still feed it as `content_flag:<code>`.
11. **Zero named rules** is a valid Build, not flagged.
12. **Glossary:** Exclusion rewritten, Exclusion Rule added (fixed vs named rules, defaults, non-grounds), Exclusion Override and Content Flag adjusted, in [CONTEXT.md](../../../CONTEXT.md). Still says Top-100 Dataset; the Top-N rename belongs to the wording fog.
