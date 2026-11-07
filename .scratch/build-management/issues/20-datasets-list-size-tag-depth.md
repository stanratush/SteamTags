# 20: Datasets, List Size and Tag Depth in the Build

**What to build:** the dataset set, each dataset's List Size and the Build's Tag Depth become settings in `datasets.toml`. One helper defines "has" (within Tag Depth) for membership, the Eligible Pool, its baselines and the feature analysis. `would_be_rank_<dataset>` becomes a templated column, and Build-output text writes the actual N. The default config gives byte-identical output.

**Blocked by:** 19

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Datasets, List Size and Tag Depth", "Export schema" (`would_be_rank_<dataset>`), "Resolved while writing this spec". Decision tickets: [tags per game and list size](05-tags-per-game-and-list-size.md), [grid scaling](11-grid-and-defaults-scaling.md), [Top-N glossary](14-top-n-glossary.md).

- [ ] `datasets.toml`: per dataset `list_size` (integer ≥ 10, absent = 100); per Build `tag_depth` (integer ≥ 2 or `all`; Steam 2–20, absent = 20, above 20 refused). `all` stays the string `all` in config and `build.json`.
- [ ] Dataset validation: keys `[a-z0-9_]` and unique; label required; exactly one dataset without a defining tag, keyed `overall`, listed first; defining tags unique. `DATASET_KEYS` is removed. `build/core.py`, `build/assemble.py` and `collect/run.py` (SteamDB cross-check, reading the datasets from the Build's `build.json`) use the Build's datasets in config order.
- [ ] `TOP_N` is removed. `rank_dataset` slices to the dataset's List Size. A pool smaller than N fails the Build, naming the dataset and its pool size (a warning in test Builds). Ranking and slicing are separate functions, so a List Size change only re-slices.
- [ ] One helper (e.g. `counted_tags(tags, depth)`) used by Tag-Specific Dataset membership, the Eligible Pool, `tag_frequency`, `genre_frequency`, combinations, associations and `median_position`. Exclusions, Content Flags and rank limits keep reading the full list. "No tags" is unchanged. Manual Metadata tags-only entries go through the same helper.
- [ ] `impact_removals.csv` notes when the matching tag sits beyond Tag Depth (informational).
- [ ] The network config reader refuses a Parameter Grid with no pairs (s_low > g_high), with a bg error string.
- [ ] `would_be_rank_<dataset>`: the four reports that hard-code five columns expand one column per dataset in config order. The schema documents it as one column per dataset key.
- [ ] Build-output text writes "Top 100" when every dataset in scope has N = 100, and "Top-N" otherwise. Dataset counts ("the five published datasets") follow the same rule. Every changed string has a bg entry.
- [ ] Tests:
  - Default config: byte-identical `datasets/`, `reports/` and `analysis/` to before (fixed `build_id`), and the `build_id` hash is unchanged.
  - Tag Depth 10 on the fixture: a game whose defining tag is 11th is not in that dataset, but a game with an excluding tag 14th is still excluded.
  - A List Size larger than the pool fails a full-mode Build and warns in a test Build. List Size 150, and a six-dataset config (an extra defining tag), both build; the latter has six `would_be_rank_` columns.
  - Each dataset validation failure, and the no-pairs grid refusal.

## Comments
