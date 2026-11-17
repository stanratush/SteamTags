# What fixes one comparison, and what does its export hold?
Type: grilling
Status: resolved
Blocked by: 03, 04, 10

## Question

A **Network State** fixes one Tag Network result and can be exported and reopened. A comparison is made of several.

Decide:
- what fixes one comparison result: the included datasets, each one's g, s and resolution, the shared settings, and whether the minimum similarity is part of it or a view choice;
- whether it gets a name in the glossary and an id, as a Network State has a `state_id`;
- the export: which files and columns (one row per Cluster Match with both Clusters' Tags, the shared and unique Tags, the percentages and the measures; one row per unmatched Cluster with its flag; the settings), following the export schema conventions in `src/steamstudy/export/schema.py`;
- whether an exported comparison can be reopened, like Open Network State, or is a record only;
- whether the export holds every pair of included datasets or only the pair on screen.
- whether the export carries the **games in both Clusters** of each match (as defined in [What are "the games in both Clusters" of a match?](05-games-in-both-clusters.md): a file like `cluster_games.csv`, one row per match × game) or only the counts (games in common for the pair; in both / only A / only B / neither for a match).

## Comments

- From [How is a match read against seed and threshold dependence?](07-seed-and-threshold-dependence.md): each dataset row now shows its Seed-Noise Floor and, on a cell, its Neighbour Agreement ("—" otherwise). Decide whether the export carries both.
- From [What are the measures called, and how is each one read?](11-names-and-readings.md): export columns renamed for Comparable Tags and Overlap vs. expected (`lift` → `overlap_vs_expected`, `common_*` → `comparable_*`, `ari_common` → `ari_comparable`); see that ticket's answer, point 5.

## Answer

Resolved with the researcher, 2026-11-17. Names are working names; the final wording is [What are the measures called, and how is each one read?](11-names-and-readings.md)'s.

**Facts from the code that shaped the answer**

- A Network State's key (`Settings.key` in `src/steamstudy/network/model.py`) holds the Build, dataset, filter, g, s, hidden and removed Tags, weight, algorithm, resolution, seed, replicates and noise seeds; `state_id` is the first 12 hex of the SHA-256 of its canonical JSON. A Network State export can be reopened and is verified by recomputing `state_id`.
- The Parameter Selection export (`src/steamstudy/app/ps_export.py`) is record-only: one zip per settings key, `steamstudy_parameter-selection_<hash12>_<UTC>.zip`, tables stacked by `dataset`, a JSON manifest with a `columns` block from `schema.py`, byte-identical tables for the same inputs.
- Since [Why does the seed change between cells, and should it be the same for every dataset?](10-seed-per-dataset.md), a dataset on a cell has no seed: its partition is the stored Selected Partition, identified by the run's settings key and the cell.

**Identity**

1. **What fixes a comparison:** the Build; the shared settings (Clustering Weight, algorithm, Minimum Months Filter, the hidden-Tag rules, the removed Tags); and for each included dataset its source and values: **on a cell**, the Parameter Selection settings key, g, s and the Selected Resolution; **set by hand or with no run**, g, s, γ and the main seed. Whether a cell is the pick is not part of it (the key records the cell, not why).
2. **View choices, never part of it:** the minimum similarity, which dataset of a pair is A (⇄), the chosen pair and match.
3. **A glossary term, working name Comparison State** ("everything that fixes one Cluster Comparison result", by analogy with Network State), entering CONTEXT.md with the implementation. It has a **`comparison_id`**, 12 hex of the SHA-256 of the canonical key, made as `state_id` is; the view shows it and the export's file name carries it.
4. **Record only.** No "Open comparison": a cell's partition lives in the Parameter Selection cache, which may be gone or stale when an export is reopened. The export names, per dataset, its `state_id` (hand-set or no run) or its run's settings key and cell, so any one dataset can be rebuilt.

**Export**

5. **Every pair of included datasets**, whatever is on screen, each in one fixed order: A is the earlier dataset in the Build's dataset order.
6. **Six CSVs**, a new group `cluster_comparison` in `src/steamstudy/export/schema.py` (bumps `SCHEMA_VERSION`; every column gets its description, guide entry and panel per the file's conventions):
   - `datasets.csv`: one row per included dataset: `dataset`, `source` (pick / cell / hand / no_run), `g`, `s`, `resolution`, `seed` (empty on a cell), `selection_key` (cell only), `state_id` (hand / no run only), `n_games`, `n_tags`, `n_multi_tag_clusters`, `n_one_tag_clusters`, `hidden_tags`, `seed_noise_floor` (the run's for a cell, the Network State's otherwise), `neighbour_agreement` (empty when not on a cell).
   - `clusters.csv`: one row per dataset × Cluster, **One-Tag Clusters included**: `cluster`, `n_tags`, `tag_ids`, `tags`. It is each network's whole partition, so where any unshared Tag sits can be derived.
   - `pairs.csv`: one row per pair: `dataset_a`, `dataset_b`, `n_common_tags`, `common_share_a`, `common_share_b`, `ari_common`, `n_games_in_common`, `n_matches`.
   - `matches.csv`: one row per Cluster Match, **every** pair of Multi-Tag Clusters sharing a Tag, regardless of the minimum: both Clusters, `jaccard`, `share_a`, `share_b`, `common_jaccard` (empty below two Common Tags), `n_common_a`, `n_common_b`, `n_shared`, `lift`, `expected_overlap`, `shared_tags`, `only_a_tags`, `only_b_tags` (lists), the unshared counts split by in another Cluster / isolated / not in the network on each side, and the game counts in both / only A / only B / neither.
   - `cluster_flags.csv`: one row per pair × direction × Multi-Tag Cluster: `n_matches`, `best_jaccard`, `flag`, with **only the flags that don't depend on the minimum** (not in the other network; no overlap). A reader applies any minimum with `best_jaccard`.
   - `match_games.csv`: one row per match × game in both Clusters, unclipped (not `GAMES_SHOWN`), with the columns of [What are "the games in both Clusters" of a match?](05-games-in-both-clusters.md) (rank and matched count on each side).
7. **`comparison.json`**: the full key and `comparison_id`, schema and software versions, Build provenance, the `columns` block generated from `schema.py`, the minimum similarity on screen at export (information only), and the caution text of [How is a match read against seed and threshold dependence?](07-seed-and-threshold-dependence.md). **No `.md` report**; the User Guide and metric-reference entries do that work.
8. **`steamstudy_cluster-comparison_<comparison_id>_<UTC timestamp>.zip`**, from one "Export CSV" button in the mode's header line beside the shared settings, disabled while any dataset is still being computed; its help lists the files.
9. **Import Builds:** the files are declared as Steam files and `import_variant` derives the Import ones (in `match_games.csv`, `appid` → `id`, Steam-only columns dropped or renamed by the rule). No Import-only file.
