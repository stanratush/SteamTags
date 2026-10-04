# Metric definition gaps
Type: grilling
Status: open
Blocked by: none

## Question

The User Guide research found metrics whose definition in the resolved tickets is incomplete, so the guide cannot explain them until the spec fixes them. For each, what is the rule?

Graduated from [User Guide metric reference](26-user-guide-metric-reference.md) ([findings](../research/26-user-guide-metric-reference.md), "Open issues for the researcher"; numbers as there):

3. **Combination lift for triples**: [Feature-analysis definitions](13-feature-analysis-definitions.md) reports lift for itemsets up to size 3 but only the pair formula exists. Adopt the itemset extension support × N² / (count_a × count_b × count_c) (Brin et al. 1997, §3.1), a rule-based alternative, or no lift for triples?
4. **One column name, several meanings**: `lift` (combinations: itemset over the full Top 100; associations: pair over the full Top 100; edges: pair after the Minimum Months Filter); `n_games` (a tag's game count in `nodes.csv` / `not_in_network.csv`, but N in `cluster_quality.csv`); `mean_silhouette` (per cluster in `clusters.csv`, across all Multi-Tag Cluster members in `cluster_quality.csv`); `modularity` in `resolution_sweep.csv` (a different γ per row). Rename, or rely on the schema's column descriptions and the guide?
5. **n/a for One-Tag Clusters**: conductance divides by vol(C) = 0 for an isolated tag (NetworkX 3.4.2 `conductance` raises there), and edge/weighted density divide by n(n−1)/2 = 0. The spec's n/a rule names only vol(rest) = 0. Which `_status` reason codes apply?
6. **phi n/a**: phi is undefined when a tag is on all 100 games (possible for common tags in a Tag-Specific Dataset). Add a `phi_status` column and reason code?
7. **Unstated conventions**: the sign of every Δ column (after − before?); population or sample SD for `within_z`, `q_null_sd` and the `seed_*_sd` values; whether `months_apart` in `release_month_check.csv` is signed; the reason code(s) for `seed_silhouette_status`, missing from the status list in [Export schemas for the app and the feature analysis](24-export-schemas.md).

Any answer that changes a column or status is declared in `steamstudy.export.schema` and bumps `schema_version`, per [Export schemas for the app and the feature analysis](24-export-schemas.md).

## Comments

- 2026-10-04, from [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md): the inspector shows `within_z` with its maximum for the cluster size, so the population/sample SD choice here also fixes that cap (√(n−1) or (n−1)/√n). That ticket also bumps `schema_version` (`rc_ari_beyond_noise`, `q_excess`, `null_n_edges_mean`); a status-code change here can share the bump.
