# Seed stability reporting and consensus clustering
Type: grilling
Status: open
Blocked by: 23

## Question

Beyond the single fixed seed, should the clustering's seed stability be reported as a standing metric (e.g. mean and minimum ARI across K seeds on the unchanged network, the same Seed-Noise Floor that Removal Sensitivity computes) in the Cluster-quality row, the Analysis Report mode and the feature-analysis report; when is it computed (every recompute, lazily, on demand, Build only); and should consensus clustering (or reporting per-tag co-assignment frequency across seeds) be added, or left out of v1 with a stated limitation?

Graduated from the map's fog ("Clustering stability") after [Node-removal sensitivity method](12-node-removal-sensitivity.md) fixed the Seed-Noise Floor: K = 10 extra seeds (config `sensitivity_noise_seeds`, seeds derived from the main seed), SD of Q and silhouette, ARI of each seed's partition vs. the main seed's; currently computed only inside a sensitivity run. Research background: [Graph clustering and quality methods](05-graph-clustering-methods.md) section 5 (Karrer–Levina–Newman perturbation robustness, consensus [LF12]); a single γ and seed should not be presented as *the* structure.

Blocked by [Recompute turnaround and caching](23-recompute-budget-caching.md): K extra clusterings per state change is a per-recompute cost that the turnaround budget has to absorb or defer.
