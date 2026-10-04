# Config changelog

Every config change, with its rationale. The Build copies these entries into `build.json`.
Each entry is a `## YYYY-MM-DD: title` heading followed by its rationale.

## 2026-10-04: initial defaults

Defaults as decided in the Steam Success Study spec: exclusion rules, Genre Tags, datasets, network and analysis defaults. The Genre Tag ids for Experimental (844), Sports (701) and Tabletop (17389) are not yet confirmed against a `GetTagList` snapshot. The Build warns if any configured id is missing from it.
