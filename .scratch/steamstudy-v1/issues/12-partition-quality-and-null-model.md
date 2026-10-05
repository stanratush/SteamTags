# 12: Partition quality and null model

**What to build:** Every Network State comes with its partition-quality context. In the app's Cluster-quality row and Clusters tab, in the export zip and in the Build, the researcher sees:
- Q at the active γ against a game–tag shuffle null model ("Q 0.42 vs null 0.31 ± 0.01 (excess 0.11, z 11; null networks average 640 edges vs 702)");
- coverage and cluster counts as "k multi-tag + s one-tag";
- the Jaccard silhouette, labelled a descriptive diagnostic;
- per-cluster density, conductance and cut weight;
- the cluster × cluster connection table;
- the disconnected-cluster count.

**Blocked by:** 11

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Silhouette, Global metrics, Per-cluster metrics, Inter-cluster connectivity), "Export schemas".

- [x] Silhouette uses Jaccard game-set distance on the full partition. One-Tag Clusters count as "other clusters" for b(i), but their own s = 0 is left out of every mean. It is n/a (`fewer_than_2_multi_tag_clusters` / `one_tag_cluster`) per the spec.
- [x] Q is weighted on the active Clustering Weight at the optimised γ, with `modularity_status = no_edges` when total weight is 0.
- [x] Null model: bipartite game–tag swap randomisation that preserves every game's and every tag's degree. It rebuilds the network with the same thresholds and reclusters with the same algorithm / γ / weight. R = `null_replicates`, with replicate seeds from their own stream off the main seed. Computed synchronously in every recompute.
- [x] `cluster_quality.csv`: `n_dataset_games, n_nodes, n_edges, total_weight, modularity, modularity_status, q_null_mean, q_null_sd` (sample SD), `modularity_z, q_excess, null_n_edges_mean, coverage, inter_cluster_weight_share, n_multi_tag_clusters, n_one_tag_clusters, n_disconnected_clusters, mean_silhouette, silhouette_status`.
- [x] `clusters.csv` gains the per-cluster metric columns. Densities are empty at size 1. Conductance is computed in our own code, with `conductance_status` `isolated_tag` / `no_edges_outside_cluster`. `nodes.csv` gains `silhouette`, `silhouette_status`.
- [x] `cluster_connections.csv` covers every unordered Multi-Tag Cluster pair (zero-edge pairs included) plus `one_tag_pool`. `null_model.csv` has one row per replicate.
- [x] The app shows the Cluster-quality row (never `modularity_z` alone) and a Clusters tab. A disconnected cluster triggers a warning suggesting Leiden.
- [x] The Build writes the stacked `network_cluster_quality.csv`, `network_cluster_connections.csv` and `network_null_model.csv`. `export.json` method constants gain R, the replicate seeds and `"silhouette": "jaccard_game_set"`. `schema_version` is bumped, and the equality test still passes.
- [x] Hand-built network tests: the silhouette n/a rules, the null model preserving degrees, conductance for connected and isolated One-Tag Clusters, and coverage + inter share = 1.

## Comments

- 2026-10-05 (agent): the network computation and the Build tables for this ticket are done (steamstudy.network, analysis/network_*.csv); the app parts come with the app work.

- 2026-10-04 (agent): App implemented in steamstudy.app (loader, renderer boundary, layout, callbacks, export/open, rs_cache, server). Tested via the export zip (app equals Build, round trip, refusals), the served page (no external URLs) and the callbacks as functions; also exercised live in the browser on a demo Build (node/edge/cluster inspectors, remove, layout switch, Re-layout, background Removal Sensitivity run with stale/current display, Analysis Report mode on the same renderer instance, floating inspector). Open Network State also re-exports and can compare table hashes (recorded_table_hashes_match).
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
