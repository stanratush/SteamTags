# The Connection Ratio is the configuration-model ratio

How strongly two Clusters connect, allowing for their size, is measured as the **Connection Ratio** r_ab = w_ab / (k_a·k_b / 2m), in the Clustering Weight: the link weight between the two Clusters over what their strengths alone predict. It is the degree-corrected block affinity relative to the configuration null (Karrer & Newman 2011), and it is the merge test of the modularity the app optimises, so for every pair the app shows it lies between 0 and γ (Traag et al. 2019, Theorem 4). The `one_tag_pool` rows use the distinct-pair expectation for pool–pool, so the same ceiling holds.

We chose it over three alternatives that a reader might expect:

- **Between-cluster density**, w_ab / (n_a·n_b): sizes by tag count, so it is inflated for two-tag Clusters and still tracks common tags' strength. It is the test of CPM, which the app does not use.
- **Game-set overlap** (Jaccard, cluster-level Lift): saturated on these data, where one Cluster's games cover 39–96% of all games, and blind to the network that was clustered.
- **Normalised cut or PAGA connectivity**: Ncut has no null and tracks size; PAGA binarises the weights and caps at 1.

## Consequences

- Values are low partly because the clustering separated the tags. The guide says so: the ratio describes the split, not independent evidence that two groups are unrelated.
- Under Lift, a second, shared-game ratio is also computed. It is not tied to the clustering and can exceed γ, and it is labelled as such.
- Its ceiling moves with γ, so the resolution is always shown beside it, and comparisons across γ divide by γ.
- Evidence and measurements: `.scratch/bilingual-cluster-views/research/05-normalised-inter-cluster-strength.md`.
