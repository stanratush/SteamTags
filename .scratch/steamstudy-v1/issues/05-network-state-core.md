# 05: Network State core

**What to build:** The pure `network` computation from Top-100-shaped rows plus Network State settings to a Tag Network result: nodes, edges, Not-in-network tags with their reasons, Clusters from Louvain or Leiden on the chosen Clustering Weight, `C1…` labels, global positions, and the canonical Network State key with its `state_id`. The app and the feature-analysis report will both use it. It is built and tested on hand-built fixture datasets, so it can start before the collection chain finishes.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Interface, Network State key, Network build, Clustering Weight, Clustering algorithm, Cluster labels, Global positions).

- [ ] Input: rows following the `top100_<dataset>.csv` contract, plus settings. Output: a Network State result object.
- [ ] The Minimum Months Filter drops games below the threshold, with no re-ranking or backfill. N is the number of games left.
- [ ] Nodes are tags with at least `min_games_per_tag` games, minus hidden and removed tags. Edges are pairs with shared games ≥ `min_shared_games`. The edge weight is always the shared-game count. Isolated tags stay as One-Tag Clusters.
- [ ] Not-in-network lists every tag on at least one game that is not a node, with all its reasons in the fixed order `removed;defining_tag_hidden;genre_tag_hidden;below_min_games`.
- [ ] Clustering Weight: `shared_games`, or `lift = shared·N/(n_i·n_j)`. Lift < 1 edges are kept. Hiding or removing tags changes neither N nor any lift.
- [ ] `louvain` uses NetworkX with the exact arguments in the spec. `leiden` uses `leidenalg` `RBConfigurationVertexPartition` with `n_iterations=-1`, never CPM. Graphs are built in canonical order, and a fixed seed gives identical partitions across runs.
- [ ] Disconnected Louvain clusters are flagged `connected = false` and never split.
- [ ] Cluster labels: `C1…` by size desc, ties by smallest member `tag_id`, Multi-Tag Clusters first, then One-Tag Clusters ordered by `tag_id`.
- [ ] Network State key: canonical JSON of the spec's field list (`hidden_tag_ids`, `removed_tag_ids`, `resolution` as `"1.00"`, `null_replicates`, `noise_seeds`, `key_version`, …). SHA-256 → 12-character `state_id`. Layout mode is not in the key.
- [ ] Global positions come from a seeded, weighted `spring_layout` on the active Clustering Weight at the loosest thresholds. They are a pure function of dataset + filter + weight + seed, and are identical across threshold changes.
- [ ] Edge games are the intersection of the two tags' game sets over dataset + filter, available on demand.
- [ ] Hand-built fixture tests cover every criterion above, including the lift formula, the reason order, label ties, state_id stability, and identical Louvain and Leiden partitions on repeat runs.
