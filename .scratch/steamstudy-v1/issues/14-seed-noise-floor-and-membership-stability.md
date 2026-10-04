# 14: Seed-Noise Floor and Membership Stability

**What to build:** Every Network State reports how much its clustering varies across K other seeds: a line such as "Seed-noise floor (K = 10): ARI vs. main min 0.84, mean 0.93 · multi-tag clusters 5–7 · SD Q 0.004 · SD silhouette 0.01". It also reports each tag's Membership Stability (how consistently the tag lands with the same tags) and each cluster's mean. These are numbers only, with no stable/unstable labels, shown in the app, the export and the Build.

**Blocked by:** 12

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Seed-Noise Floor, Membership Stability), "Export schemas".

- [ ] K = `noise_seeds` (config only). Noise seeds are derived from the main seed through a stream separate from the null-model replicate seeds, and the two sets never overlap (tested). Each noise seed runs the same algorithm, γ and weight on the unchanged network, synchronously in every recompute.
- [ ] Each seed is compared with the main partition only: `seed_ari_min`, `seed_ari_mean` (sklearn ARI), `seed_modularity_sd` (sample SD), `seed_silhouette_sd` with `seed_silhouette_status = fewer_than_2_seeds_with_silhouette`, `seed_k_min`, `seed_k_max`. These are added to `cluster_quality.csv`. With no edges, every ARI is 1.
- [ ] `seed_noise.csv` (`noise_seed_index, seed, modularity, silhouette, silhouette_status, ari_vs_main, n_multi_tag_clusters, n_one_tag_clusters`) is always written to the zip, and stacked in the Build as `network_seed_noise.csv`.
- [ ] Membership Stability: the mean over seeds of the Jaccard overlap between v's main cluster and its seed cluster (both including v). Empty for `degree = 0`. `mean_membership_stability` per cluster is empty for isolated tags' clusters. Empty values sort last. Added to `nodes.csv` and `clusters.csv`.
- [ ] The app shows the seed-noise line in the Cluster-quality row, and Membership Stability in the node inspector and the Nodes/Clusters tables. No graph overlay.
- [ ] `export.json` method constants gain K and the noise seeds. `analysis.json` gains the per-dataset network-level noise summary. `schema_version` is bumped, and the equality test still passes.
- [ ] Hand-built tests: Membership Stability values worked out on paper, the isolated-tag n/a, and the seed stream separation.
