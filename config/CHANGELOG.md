# Config changelog

Every config change, with its rationale. The Build copies these entries into `build.json`.
Each entry is a `## YYYY-MM-DD: title` heading followed by its rationale.

## 2026-10-04: initial defaults

Defaults as decided in the Steam Success Study spec: exclusion rules, Genre Tags, datasets, network and analysis defaults. Every configured tag id was checked against a `GetTagList` response captured on 2026-10-04 (`version_hash` 711684454) as a test fixture. Experimental is tag 13782.

## 2026-11-07: exclusions.toml uses named rules

`exclusions.toml` now lists ordered `[[rule]]` entries (name, label, tags with an optional per-tag `rank_limit`, `name_only`, and for the Steam adult rule `content_descriptor_ids` and `adult_only_notice`) and `[[content_flag]]` entries. The three default rules keep today's codes (`adult_content`, `software_tag`, `dating_sim_tag`), tags, order and behaviour, so datasets, reports and analysis are unchanged; only the config shape and the `build.json` copy of it differ. `per_tag_rank_limit` is gone: a tag's tighter limit now sits on its entry in the rule. The reader still accepts the old shape.
