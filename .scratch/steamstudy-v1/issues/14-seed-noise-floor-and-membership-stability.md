# 14: Seed-Noise Floor and Membership Stability

**What to build:** Every Network State reports how much its clustering varies across K other seeds: a line such as "Seed-noise floor (K = 10): ARI vs. main min 0.84, mean 0.93 · multi-tag clusters 5–7 · SD Q 0.004 · SD silhouette 0.01". It also reports each tag's Membership Stability (how consistently the tag lands with the same tags) and each cluster's mean. These are numbers only, with no stable/unstable labels, shown in the app, the export and the Build.

**Blocked by:** 12

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Seed-Noise Floor, Membership Stability), "Export schemas".

- [x] K = `noise_seeds` (config only). Noise seeds are derived from the main seed through a stream separate from the null-model replicate seeds, and the two sets never overlap (tested). Each noise seed runs the same algorithm, γ and weight on the unchanged network, synchronously in every recompute.
- [x] Each seed is compared with the main partition only: `seed_ari_min`, `seed_ari_mean` (sklearn ARI), `seed_modularity_sd` (sample SD), `seed_silhouette_sd` with `seed_silhouette_status = fewer_than_2_seeds_with_silhouette`, `seed_k_min`, `seed_k_max`. These are added to `cluster_quality.csv`. With no edges, every ARI is 1.
- [x] `seed_noise.csv` (`noise_seed_index, seed, modularity, silhouette, silhouette_status, ari_vs_main, n_multi_tag_clusters, n_one_tag_clusters`) is always written to the zip, and stacked in the Build as `network_seed_noise.csv`.
- [x] Membership Stability: the mean over seeds of the Jaccard overlap between v's main cluster and its seed cluster (both including v). Empty for `degree = 0`. `mean_membership_stability` per cluster is empty for isolated tags' clusters. Empty values sort last. Added to `nodes.csv` and `clusters.csv`.
- [x] The app shows the seed-noise line in the Cluster-quality row, and Membership Stability in the node inspector and the Nodes/Clusters tables. No graph overlay.
- [x] `export.json` method constants gain K and the noise seeds. `analysis.json` gains the per-dataset network-level noise summary. `schema_version` is bumped, and the equality test still passes.
- [x] Hand-built tests: Membership Stability values worked out on paper, the isolated-tag n/a, and the seed stream separation.

## Comments

- 2026-10-05 (agent): the network computation and the Build tables for this ticket are done (steamstudy.network, analysis/network_*.csv); the app parts come with the app work.

- 2026-10-04 (agent): App implemented in steamstudy.app (loader, renderer boundary, layout, callbacks, export/open, rs_cache, server). Tested via the export zip (app equals Build, round trip, refusals), the served page (no external URLs) and the callbacks as functions; also exercised live in the browser on a demo Build (node/edge/cluster inspectors, remove, layout switch, Re-layout, background Removal Sensitivity run with stale/current display, Analysis Report mode on the same renderer instance, floating inspector). Open Network State also re-exports and can compare table hashes (recorded_table_hashes_match).
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
