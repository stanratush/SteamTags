# Seed stability reporting and consensus clustering
Type: grilling
Status: resolved
Blocked by: 23

## Question

Beyond the single fixed seed, should the clustering's seed stability be reported as a standing metric (e.g. mean and minimum ARI across K seeds on the unchanged network, the same Seed-Noise Floor that Removal Sensitivity computes) in the Cluster-quality row, the Analysis Report mode and the feature-analysis report; when is it computed (every recompute, lazily, on demand, Build only); and should consensus clustering (or reporting per-tag co-assignment frequency across seeds) be added, or left out of v1 with a stated limitation?

Graduated from the map's fog ("Clustering stability") after [Node-removal sensitivity method](12-node-removal-sensitivity.md) fixed the Seed-Noise Floor: K = 10 extra seeds (config `sensitivity_noise_seeds`, seeds derived from the main seed), SD of Q and silhouette, ARI of each seed's partition vs. the main seed's; currently computed only inside a sensitivity run. Research background: [Graph clustering and quality methods](05-graph-clustering-methods.md) section 5 (Karrer–Levina–Newman perturbation robustness, consensus [LF12]); a single γ and seed should not be presented as *the* structure.

Blocked by [Recompute turnaround and caching](23-recompute-budget-caching.md): K extra clusterings per state change is a per-recompute cost that the turnaround budget has to absorb or defer.

Settled by [Recompute turnaround and caching](23-recompute-budget-caching.md):
- v1 has no performance target and no performance caches; every change recomputes everything from a stateless server. So the turnaround budget no longer forces a deferral; the question is only what is useful and correct to show.
- Measured cost of the K = 10 Seed-Noise Floor on synthetic data ([benchmark](../prototypes/23-recompute-benchmark/README.md)): 40 ms at thresholds 8/8, 155 ms at 3/3, ~1 s at 1/1 (Louvain), on top of a full recompute of 17 · 61 · 245 ms plus the null model's 0.3 · 0.8 · 2.9 s.

Settled by [Export schemas for the app and the feature analysis](24-export-schemas.md):
- Any standing stability metric goes into `cluster_quality.csv` (one row per Network State, stacked by dataset in the Build's `network_cluster_quality.csv`) and is declared in `steamstudy.export.schema`, bumping `schema_version`. Per-seed rows already have a shape: `removal_sensitivity_noise.csv` (`noise_seed_index`, `seed`, `modularity`, `silhouette`, `silhouette_status`, `ari_vs_main`), which a standing floor could reuse rather than duplicate.
- Per-tag co-assignment frequency, if adopted, would be a new `nodes.csv` column or its own file, under the same conventions (empty-cell n/a, `tag_id`, shortest round-trip floats).

## Answer

Resolved 2026-10-04 with the researcher. The seed-to-seed variation becomes a standing part of every Network State's result, with a per-tag reading beside it, and the Build gains an offline check across γ. The displayed partition is unchanged: one run with the active algorithm, γ and main seed.

**Terms** (glossary, [CONTEXT.md](../../../CONTEXT.md))
- **Seed-Noise Floor** stays the one term for how much the clustering varies across seeds, and is now computed for every Network State. Don't use "seed stability" as a second name for the same numbers.
- **Membership Stability** (new): how consistently one tag lands with the same tags across seeds. Avoid: confidence, certainty, robustness, core-ness.
- **Resolution Sweep** (new): a Build-only diagnostic that reclusters at a fixed grid of γ values. Avoid: γ stability test, robustness check.

**Seed-Noise Floor as a standing metric**
- Computed inside every recompute, synchronously, like the null-model baseline. Measured cost (synthetic data, [benchmark](../prototypes/23-recompute-benchmark/README.md)): about 40 ms at 8/8, 155 ms at 3/3 and 1 s at 1/1 with Louvain. The null model costs 0.3, 0.8 and 2.9 s at the same settings.
- K = `noise_seeds`, default 10, set in config only (like R) with no app control. The config key `sensitivity_noise_seeds` is renamed to `noise_seeds`.
- The noise seeds are derived from the main seed, from a stream separate from the null-model replicate seeds, so the two sets never share a seed.
- Each noise seed runs the same clustering on the unchanged network: the active algorithm, γ and Clustering Weight.
- The **network-state key** gains `noise_seeds`, next to `null_replicates`, and `key_version` is bumped. The **Network State** glossary entry now lists the number of noise seeds.
- **Removal Sensitivity** reads the standing floor and no longer computes its own. Its cache key becomes the state key plus the method version, since K is now inside the state key. Its method and "beyond noise" rules are unchanged from [Node-removal sensitivity method](12-node-removal-sensitivity.md).

**Values** (each noise seed is compared with the main partition, never pairwise between seeds, because the main partition is the one shown)
- `seed_ari_min` and `seed_ari_mean`: the ARI of each noise seed's partition against the main partition (`sklearn.metrics.adjusted_rand_score`).
- `seed_modularity_sd`: the SD of Q at the active γ across the K seeds.
- `seed_silhouette_sd`, with `seed_silhouette_status`: the SD covers only the seeds that have a silhouette. It is n/a, with a reason, when fewer than 2 seeds have one.
- `seed_k_min` and `seed_k_max`: the range of Multi-Tag Cluster counts across the K seeds.
- A network with no edges gives every seed the same partition, all One-Tag Clusters, so every ARI is 1.

**Membership Stability**
- For tag v: the mean over the K seeds of |A ∩ B| / |A ∪ B|, where A is v's cluster in the main partition and B is v's cluster in seed s. Both sets include v itself.
- 1.0 means v always lands with exactly the same tags. It is defined for One-Tag Clusters too: a tag that is alone in both partitions scores 1.
- Per cluster, `mean_membership_stability` is the mean over the cluster's members.
- Descriptive only. It doesn't say whether a tag or a cluster is "real".

**Exports** (under the [Export schemas for the app and the feature analysis](24-export-schemas.md) conventions; `schema_version` is bumped)
- `cluster_quality.csv` gains `seed_ari_min`, `seed_ari_mean`, `seed_modularity_sd`, `seed_silhouette_sd`, `seed_silhouette_status`, `seed_k_min` and `seed_k_max`.
- `nodes.csv` gains `membership_stability`.
- `clusters.csv` gains `mean_membership_stability`.
- `removal_sensitivity_noise.csv` is renamed **`seed_noise.csv`** and is always written, whether or not Removal Sensitivity has run.
  - Columns: `noise_seed_index`, `seed`, `modularity`, `silhouette`, `silhouette_status`, `ari_vs_main`, `n_multi_tag_clusters`, `n_one_tag_clusters`.
  - The Build stacks it by dataset as `network_seed_noise.csv`.
- `export.json`:
  - The noise-floor summary moves out of the `removal_sensitivity` block, because it is now part of the network result.
  - K and the noise seeds stay under the method constants.
  - `removal_sensitivity` keeps `"not_run"`, or `partial` with `done` / `total`.
- `analysis.json`: the per-dataset noise summary becomes network-level. A Resolution Sweep summary is added: the grid, plus the per-dataset ranges the report sentence uses.

**Presentation** (numbers only: no "stable"/"unstable" labels, colours or thresholds, because no calibrated cut-off exists)
- **Cluster-quality row**: "Seed-noise floor (K = 10): ARI vs. main min 0.84, mean 0.93 · multi-tag clusters 5–7 · SD Q 0.004 · SD silhouette 0.01".
- **Analysis Report mode**: the same line in its cluster-quality section. The noise line in the Removal Sensitivity section refers back to it.
- **Membership Stability in the app**: shown in the node inspector and as a column in the node and cluster tables. It is also an extra column in the Removal Sensitivity table, because a tag that moves between clusters also explains a low ARI there. No graph overlay: graph colour always means cluster.
- **Feature-analysis report**: one templated sentence per dataset, for example: "Across 10 other random seeds, agreement with the reported partition (ARI) ranged from 0.84 to 1.00 (mean 0.93), and the number of multi-tag clusters from 5 to 7."
  - It is followed by the tags with the lowest Membership Stability: the bottom 5, or every tag below 1.0 if fewer than 5 are.
  - This is a descriptive list with no cut-off.

**Resolution Sweep** (Build only, no app UI)
- Config `resolution_sweep = [0.50, 0.75, 1.00, 1.25, 1.50]`. The Build adds the config γ (`resolution`) if the grid lacks it, so the report's own partition is always one of the rows.
- It runs at the feature-analysis report's settings: shared defaults, defining tag out, and the config algorithm, Clustering Weight and main seed. Only γ varies, so the node set is identical across γ and ARI is well defined.
- **Output**: `analysis/resolution_sweep.csv`, one row per dataset × γ, sorted by dataset, then resolution. Columns:
  - `dataset`, `resolution`;
  - `n_multi_tag_clusters`, `n_one_tag_clusters`;
  - `modularity` (at that γ), `mean_silhouette`, `silhouette_status`;
  - `ari_vs_report`: against the partition at the config γ;
  - `seed_ari_min`, `seed_ari_mean`: the Seed-Noise Floor at that γ (K noise seeds), so a reader can see whether a change across γ is larger than seed noise.
- Not included: a null model per γ, Cluster Centers, per-tag rows.
- **Report**: one descriptive sentence per dataset, for example: "Between γ = 0.50 and 1.50 the number of multi-tag clusters ranged from 3 to 9; agreement with the γ = 1.00 partition ranged from 0.61 to 1.00 (ARI)." Q at different γ is never compared in prose, because it isn't comparable.

**Ruled out of v1**: consensus clustering (Lancichinetti–Fortunato co-assignment reclustering), either as the displayed partition or as an optional mode. It would redefine what a Cluster is and reopen the cluster-center, quality-metric and Removal Sensitivity decisions. Membership Stability answers the useful part of the question ("which tags' assignment depends on the seed?") without doing that.

**For the known limitations**:
- The shown partition comes from a single run (one seed, one γ); no consensus partition is computed.
- The Seed-Noise Floor samples K = 10 seeds, not every possible seed.
- The Resolution Sweep covers a fixed γ grid, at the report's settings only.

**For the methods section**: "Because modularity optimisation depends on the random seed, every clustering was repeated with ten further seeds on the same network. We report each repeat's agreement with the reported partition (adjusted Rand index), the spread of modularity and silhouette, the range of cluster counts, and, per tag, the mean Jaccard overlap of its cluster across seeds. To show dependence on the resolution parameter, the report's clustering was repeated at γ = 0.50–1.50 and compared with the γ = 1.00 partition. These are descriptive diagnostics; no consensus partition was computed."
