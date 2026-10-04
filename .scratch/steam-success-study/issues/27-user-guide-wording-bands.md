# User Guide metric wording and interpretation bands
Type: grilling
Status: open
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
