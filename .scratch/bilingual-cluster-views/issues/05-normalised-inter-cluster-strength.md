# Normalised inter-cluster strength in the literature
Type: research
Status: open
Blocked by: none

## Question

Which established measures express how strongly two Clusters connect while accounting for their sizes, and what does each assume? This is AFK `research` against primary sources, with findings in `research/05-normalised-inter-cluster-strength.md`.

- Candidates to check: between-cluster density (weight / (n_a · n_b)), observed against configuration-model expected weight (the modularity term w_ab − k_a k_b / 2m and the ratio w_ab / (k_a k_b / 2m)), normalised cut and conductance between two groups, the block-model affinity matrix (SBM ω_ab), and Jaccard or cosine on cluster game sets.
- For each: the formula, the citable source (exact locator), the range and its reading, how it behaves with weighted edges (shared-game counts and Lift), with small or two-tag clusters and with zero edges, and whether it is comparable across Network States.
- Fit with what the app already has: `metrics.connections` (edge_count, weight), `conductance` per Cluster and Coverage, and the One-Tag pool (`one_tag_pool`).
