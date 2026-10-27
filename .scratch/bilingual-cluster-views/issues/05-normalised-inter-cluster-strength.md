# Normalised inter-cluster strength in the literature
Type: research
Status: resolved
Blocked by: none

## Question

Which established measures express how strongly two Clusters connect while accounting for their sizes, and what does each assume? This is AFK `research` against primary sources, with findings in `research/05-normalised-inter-cluster-strength.md`.

- Candidates to check: between-cluster density (weight / (n_a · n_b)), observed against configuration-model expected weight (the modularity term w_ab − k_a k_b / 2m and the ratio w_ab / (k_a k_b / 2m)), normalised cut and conductance between two groups, the block-model affinity matrix (SBM ω_ab), and Jaccard or cosine on cluster game sets.
- For each: the formula, the citable source (exact locator), the range and its reading, how it behaves with weighted edges (shared-game counts and Lift), with small or two-tag clusters and with zero edges, and whether it is comparable across Network States.
- Fit with what the app already has: `metrics.connections` (edge_count, weight), `conductance` per Cluster and Coverage, and the One-Tag pool (`one_tag_pool`).

## Answer

- The configuration-model ratio r_ab = w_ab / (k_a k_b / 2m) is the degree-corrected SBM block affinity relative to the null (Karrer & Newman 2011 eqs. (18), (23)–(24)). Its pooled form is Newman's ω_out.
- It is the only candidate tied to the clustering: merging two Clusters raises modularity exactly when r_ab > γ, and Louvain and Leiden guarantee γ-separation (Traag et al. 2019 Thm. 4). So 0 ≤ r_ab ≤ γ for every pair shown, pool rows included. Measured on 25 Network States, it was never above γ.
- Between-cluster density (the plain-SBM ω̂; CPM's test) is inflated for two-tag Clusters and still tracks strength. Normalised-cut shares are bounded but not size-neutral and have no null.
- Game-set Jaccard and cluster-level Lift are saturated on these data: one Cluster covers 39–96% of games. PAGA is binarised and capped.
- Recommendation, non-binding (ticket 06 decides): r_ab as the headline, in the Clustering Weight, with γ shown. Add a shared-game r_ab under Lift, labelled as not γ-bounded, and w_ab / cut_a for the per-cluster view.
- Full findings: [research/05-normalised-inter-cluster-strength.md](../research/05-normalised-inter-cluster-strength.md).
