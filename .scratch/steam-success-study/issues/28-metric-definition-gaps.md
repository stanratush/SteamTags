# Metric definition gaps
Type: grilling
Status: resolved
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

## Answer

Resolved 2026-10-04 with the researcher (all recommendations accepted).

1. **Combination lift, any size**: `lift` = `support_count` × N^(k−1) / (count of each member tag, multiplied), with N = 100 and k = itemset size. This is the "obvious extension" of interest in Brin, Motwani & Silverstein 1997 §3.1, and equals the existing pair formula at k = 2. No rule lifts, no new columns. Every sub-pair of a listed triple is always listed too (its support is at least the triple's), so the guide says a high triple lift can be inherited from one strong pair and points the reader to the pair rows.
2. **Column names**: only `cluster_quality.csv` `n_games` is renamed, to **`n_dataset_games`** (games in the dataset after the Minimum Months Filter), because it clashed with the per-tag `n_games` in `nodes.csv` / `not_in_network.csv` inside the same zip. `lift`, `mean_silhouette` and `resolution_sweep.csv` `modularity` keep their names; their schema descriptions state the difference (N = 100 vs. N after the filter; cluster vs. Network State grain; one γ per row, not comparable across rows).
3. **One-Tag Clusters**:
   - `edge_density` and `weighted_density` are fixed-cause n/a for `size` = 1 (empty, no status column).
   - Conductance is computed wherever it is defined, so a connected One-Tag Cluster shows 1.0. New **`conductance_status`** in `clusters.csv` with `isolated_tag` (vol(C) = 0) and `no_edges_outside_cluster` (vol(rest) = 0). Conductance is computed in our own code, not with NetworkX `conductance`, which raises at vol(C) = 0.
4. **phi**: empty when either tag is on all 100 games; fixed-cause n/a (visible from `count_a` / `count_b` = 100), no `phi_status` column. The row stays, with lift 1, Jaccard defined, Fisher p = 1 kept in the BH family; empty phi sorts last in the |phi| order.
5. **Signs**: every Δ column (`rc_delta_modularity`, `rc_delta_silhouette`, `rc_delta_k`, `rc_delta_s`, `fp_delta_modularity`, `fp_delta_silhouette`) is after removal − before. `months_apart` is signed: (year × 12 + month) of the store release date minus the same for the Release Month; positive = store date later (typical for Early Access). The listing threshold (default 3) applies to |`months_apart`|.
6. **SD conventions**:
   - `within_z`: population SD (ddof = 0), the Guimerà–Amaral definition over all cluster members. Its cap for an n-tag cluster is √(n−1), as used in [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md).
   - `q_null_sd`, `seed_modularity_sd`, `seed_silhouette_sd`: sample SD (ddof = 1), estimates of run-to-run spread from R or K runs.

   Each column's schema description names its convention.
7. **`seed_silhouette_status`**: one code, `fewer_than_2_seeds_with_silhouette` (also covers the no-edges case, which `modularity_status` shows). Config validation requires `noise_seeds` ≥ 2 and `null_replicates` ≥ 2.
8. **Schema version**: these changes share the `schema_version` bump from [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md); nothing has been published under the earlier schema.

Overrides: [Export schemas for the app and the feature analysis](24-export-schemas.md) (`cluster_quality.csv` `n_games` → `n_dataset_games`; `clusters.csv` gains `conductance_status`; the status-code list gains `conductance_status` and `seed_silhouette_status` codes; the fixed-cause list gains density for size 1 and phi at count 100) and [Feature-analysis definitions](13-feature-analysis-definitions.md) (lift formula for triples). No glossary change. No ADR: the choices are easy to reverse.
