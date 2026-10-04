# Seed stability reporting and consensus clustering
Type: grilling
Status: open
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
