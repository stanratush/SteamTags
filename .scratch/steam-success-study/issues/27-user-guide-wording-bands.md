# User Guide metric wording and interpretation bands
Type: grilling
Status: resolved
Blocked by: 26

## Question

Given the metric reference from [User Guide metric reference](26-user-guide-metric-reference.md), how should the User Guide present metrics to a non-specialist researcher?

- Does it print rule-of-thumb interpretation bands from the literature (e.g. silhouette or modularity "weak / reasonable / strong") or only bounds and comparisons (against the null model, the Seed-Noise Floor, the Eligible Pool)? Bands would sit uneasily with the decision that stability numbers carry no stable/unstable labels.
- How much notation: formulas for every metric, formulas in an appendix, or prose and worked examples only?
- Order and grouping: by where the researcher meets the metric (app panel, Analysis Report section, Build CSV) or by concept (ranking, association, clustering, stability)?
- Which metrics, if any, does the research show to be misleading enough here to need a change to the spec (dropped, renamed, or always shown beside a comparison), rather than just a warning in the guide?

Settled by [User Guide metric reference](26-user-guide-metric-reference.md) ([findings](../research/26-user-guide-metric-reference.md); see its "Bands offered in the literature" and "Open issues for the researcher"). Open issues this ticket owns (numbers as in the findings):
1. `beyond_noise` on reclustered ΔQ/Δsilhouette compares a partly mechanical change (the tag and its edges are gone) with pure seed noise; with seed SD 0 (likely in Leiden mode) every tag with a non-zero ΔQ is flagged. Options raised: compare against the fixed-partition reading, flag the difference, or restrict the flag to ARI.
2. Expected chance ARI flags: with K = 10, about 1 removal in 11 falls below `seed_ari_min` by chance (4–5 of 50 tags). State it in the report sentence, or change the rule?
8. `modularity_z` invites over-reading (small null SD from R = 20; null networks have different edge counts). Show Q − `q_null_mean` and the null edge count beside it?
9. Membership Stability is structurally 1 for isolated tags and their One-Tag Clusters, so they sort as "most stable". Make it n/a there?
10. `within_z` is capped near √(n−1); in the 3–7-tag clusters the defaults produce it is compressed, and the Guimerà–Amaral hub cut-off (z ≥ 2.5) is unreachable below 8–9 tags. Size threshold, or warning?
11. `share_ratio`'s baseline includes the Top 100 itself, pulling ratios towards 1 and capping them at pool size / 100. Keep (as decided in [Feature-analysis definitions](13-feature-analysis-definitions.md)) or use the Eligible Pool minus the Top 100?
12. Silhouette bands would often read "weak" by construction (the partition maximises modularity, not silhouette); ARI and cluster-wise Jaccard bands clash with the no-label rule for the Seed-Noise Floor and Membership Stability.

## Answer

Resolved 2026-10-04 with the researcher. The guide explains metrics through bounds, reference points and comparisons, never through published cut-offs. Three metrics change in the spec so that the misleading reading is not the default one.

**Guide form**
- **No interpretation bands** in any metric entry, the app or the report. Each entry gives:
  - theoretical bounds;
  - reference points: lift 1 and phi 0 = independence; ARI 1 = identical and about 0 = chance; Q 0 = no better than random;
  - the project's own comparisons: the null model, the Seed-Noise Floor, the Eligible Pool.
- **One appendix, "Published rules of thumb and why this guide does not use them"**, lists each band from the findings' "Bands offered in the literature" table with its source and the reason it does not transfer. Readers will meet "Q > 0.3" in papers; the appendix says why it does not apply here.
- **Notation**: each entry opens with prose and a worked example. It ends with one marked "Exact definition" line holding the formula, so the definition stays beside its caveats.
- **Order**: by concept (ranking and data → feature analysis → network → clusters and partition quality → stability → Removal Sensitivity), as in the research draft. It is followed by an alphabetical **column index**: every column name with its file(s), its app panel and report section, and a link to its entry.

**Spec changes** (each column change is declared in `steamstudy.export.schema` and bumps `schema_version`)
1. **`beyond_noise` on ARI only.** Reclustered ΔQ and Δsilhouette always contain a mechanical part: the tag and its edges are gone. At seed SD 0 every tag would be flagged. They stay as plain numbers, shown beside `seed_modularity_sd` / `seed_silhouette_sd`, with no flag.
   - `rc_beyond_noise` (a `;`-list) becomes the boolean `rc_ari_beyond_noise` = `rc_ari` < `seed_ari_min`.
   - If all seeds agree (`seed_ari_min` = 1), any removal that moves a tag is flagged. That is correct: seed noise is zero, so the change exceeds it.
   - Still labelled "screening flag, not a significance test".
2. **Expected chance flags stated; the rule is unchanged.** The report sentence and the app's Removal Sensitivity table footer read, e.g.: "7 of 50 tags flagged; if removals acted only like another seed, at most about 5 would be (n / (K + 1))". It says "at most" because ties among seed ARIs lower the chance rate.
3. **Excess modularity as the headline.** `cluster_quality.csv` gains:
   - `q_excess` = `modularity` − `q_null_mean`;
   - `null_n_edges_mean`: the mean of `null_model.csv` `n_edges`, beside the real `n_edges`.

   The app and report show, e.g., "Q 0.42 vs null 0.31 ± 0.01 (excess 0.11, z 11; null networks average 640 edges vs 702)". `modularity_z` stays, never shown alone.
4. **Membership Stability n/a for isolated tags.** `membership_stability` is empty for every tag with `degree` = 0, and `mean_membership_stability` is empty for their One-Tag Clusters. This is a fixed-cause n/a, derivable from `degree`, so it has no status column, per [Export schemas for the app and the feature analysis](24-export-schemas.md).
   - A connected tag the algorithm left alone keeps its value, which is genuine.
   - Empty values sort last.
   - The guide states the cluster-size effect: one lost companion costs a 2-tag member 0.5 but a 20-tag member 0.05.
5. **`within_z` kept, with its cap shown.** The node inspector shows, e.g., "within-z 1.2 (max 1.7 in a 4-tag cluster)". The cap is computed from the cluster size and the SD convention chosen in [Metric definition gaps](28-metric-definition-gaps.md). No new column: the cap is derivable from `clusters.csv` size. The guide says values are not comparable across cluster sizes. The Guimerà–Amaral role regions and the word "hub" are not used.
6. **`share_ratio` baseline unchanged**: the Eligible Pool includes the Top 100, as decided in [Feature-analysis definitions](13-feature-analysis-definitions.md). The guide states the pull towards 1 and the ceiling (pool size / 100). The tag and genre frequency tables print the Eligible Pool size, so the ceiling is visible.

Overrides: [Node-removal sensitivity method](12-node-removal-sensitivity.md) (flag rule and its "e.g. ARI, Q" label) and [Export schemas for the app and the feature analysis](24-export-schemas.md) (`rc_beyond_noise`, `cluster_quality.csv` columns, the n/a list). No glossary change. No ADR: the choices are easy to reverse.
