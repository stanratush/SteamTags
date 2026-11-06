# How do named exclusion rules work?
Type: grilling
Status: open
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
