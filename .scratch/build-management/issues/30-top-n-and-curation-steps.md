# 30: Top-N and Curation steps

**What to build:** the editors for the settings that change the Top-N:
- datasets (key, label, defining tag, List Size);
- Tag Depth, `global_rank_limit` and app types;
- ordered named rules between the fixed rules, with rename and delete keeping overrides consistent;
- Manual Exclusions, Exclusion Overrides and Manual Metadata Entries, each with a reason and evidence and today's validation.

The Eligible Pool column shows a placeholder until issue 32.

**Blocked by:** 19, 20, 29

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "The Build menu" (steps 2 and 3), "Datasets, List Size and Tag Depth", "Named Exclusion Rules". Decision tickets: [Build menu](12-build-menu.md), [named exclusion rules](06-named-exclusion-rules.md), [tags per game and list size](05-tags-per-game-and-list-size.md).

- [ ] Datasets table: add, remove and relabel, with key and defining tag validation as issue 20 defines it. `overall` cannot be removed or given a defining tag. The tag picker offers vocabulary tags only (Steam: GetTagList; Import: its attributes).
- [ ] Tag Depth: an integer input plus an "all" choice. Steam is bounded 2–20 (20 = all); an Import is bounded 2 to its longest list.
- [ ] `global_rank_limit` (1–20). App types are shown for Steam only.
- [ ] The rule list shows the fixed rules before and after the named rules, not editable, with drag or up/down reordering of named rules. Each rule edits name, label, tags with optional rank limits and name-only matches, and (Steam) descriptor ids and the Adult Only notice. Validation errors mark the step red. Renaming a rule renames its overrides; deleting one asks to drop them.
- [ ] Curation: Manual Exclusions, Overrides (targets `app_type`, `no_tags` or a named rule) and Manual Metadata Entries (Steam only). Each needs a reason and evidence and is validated as the Build validates it. The would-be Overall ranks of excluded games are a shortcut for adding an Override (the data is wired by issue 32).
- [ ] Steam-only fields are hidden in an Import's draft.
- [ ] bg entries for every string.
- [ ] Tests:
  - Each editor writes the draft in the config shape that issues 19–20 read.
  - A duplicate rule name marks the step red and Review lists it.
  - Renaming a rule renames its override.
  - An Import draft shows no Steam-only field.

## Comments
