# Config changelog

Every config change, with its rationale. The Build copies these entries into `build.json`.
Each entry is a `## YYYY-MM-DD: title` heading followed by its rationale.

## 2026-10-04: initial defaults

Defaults as decided in the Steam Success Study spec: exclusion rules, Genre Tags, datasets, network and analysis defaults. Every configured tag id was checked against a `GetTagList` response captured on 2026-10-04 (`version_hash` 711684454) as a test fixture. Experimental is tag 13782.
