# 19: Named Exclusion Rules

**What to build:** `exclusions.toml` becomes ordered `[[rule]]` entries between the fixed rules, with per-tag rank limits, the Adult Only notice as a setting, Content Flags in the same shape, and a reader that converts today's shape. A Build from today's `config/` gives byte-identical datasets and reports.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Named Exclusion Rules". Decision ticket: [named exclusion rules](06-named-exclusion-rules.md).

- [ ] `config.py`: `ExclusionConfig` holds `allowed_app_types`, `global_rank_limit` and an ordered tuple of named rules (`name`, `label`, `tags` of `{id, name, rank_limit?}`, `name_only`, `content_descriptor_ids`, `adult_only_notice`), plus Content Flags as `name`/`label`/`tags`/`name_only`.
- [ ] The reader accepts the new shape and today's (`adult_content`/`software_tag`/`dating_sim_tag` tables, `per_tag_rank_limit`, `content_flags.<code>`), converting the old one to the three default rules in today's order. `per_tag_rank_limit` entries move onto the matching tag entries.
- [ ] `config/exclusions.toml` is rewritten in the new shape, with the same effect; `config/CHANGELOG.md` gains an entry.
- [ ] Validation fails the Build on: duplicate rule names; a name equal to `store_data_unavailable`, `app_type`, `no_tags` or `manual`; a name outside `[a-z0-9_]`; a rule with no signal; a rank limit outside 1–20. Unknown tag ids stay a warning. Zero rules is valid.
- [ ] `build/exclusion.py`: evaluation runs the fixed rules, then named rules in order, then `manual`; `primary_reason` is the first match; the Adult Only notice fires only where `adult_only_notice = true`.
- [ ] Overrides target `app_type`, `no_tags` or a named rule; one naming an unknown rule, `store_data_unavailable` or `manual` fails the Build with a message naming it.
- [ ] `impact_adult_signals.csv` is written for the rule named `adult_content` (headers only when absent), with updated descriptions. `impact_unexcluded.csv` keeps descriptors 1 and 4 and software genres as fixed diagnostics; Content Flags feed it as `content_flag:<code>`.
- [ ] Rules and Content Flags read the full displayed list; rank limits count positions in it. (Issue 20 adds Tag Depth and must not change this.)
- [ ] Tests:
  - A Build of the test fixture from the old-shape config and from the new `config/exclusions.toml` gives byte-identical `datasets/`, `reports/` and `analysis/` files to a Build made before this change (fixed `build_id`).
  - Each validation failure, the unknown-override failure, and a zero-rule Build.
  - Rule order changes `primary_reason`; a tag in two rules matches both; per-tag limits differ per rule.
  - An old `build.json` still loads in the app unchanged.

## Comments
