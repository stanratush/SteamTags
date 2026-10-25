# Per-pair metric definitions
Type: grilling
Status: open
Blocked by: none

## Question

What is the exact formula, and the "unavailable" rule, for every metric reported per **Threshold Pair**?

- **Neighbour Agreement**: ARI between Selected Partitions on the intersection of the two pairs' tags. Do isolated tags count? The neighbours are (g−1, s), (g+1, s), (g, s−1), (g, s+1). What happens at the grid edges and the s ≤ g border (fewer neighbours, so a mean over the available ones)? If a neighbour has no Selected Partition, is it missing or 0? "Identical graphs count as agreement = 1": does that mean identical graphs, or identical Selected Partitions? Report each direction's node overlap (Jaccard or count) and ARI separately.
- **Seed-Noise Floor** at the Selected Resolution: minimum ARI over the noise seeds against the Selected Partition (which came from the scan, not from the main seed).
- **Information Retention**: the numerator and denominator. Are game–tag assignments counted over all tags of the dataset, or only over visible tags after hiding Genre Tags and the defining tag? Over games after the Minimum Months Filter?
- **Fragmentation**: isolated tags (count, share of nodes), largest connected component (tags, share), number of Multi-Tag and One-Tag Clusters.
- **Descriptive metrics**: Q at the Selected Resolution, weighted Coverage on Lift, Jaccard silhouette (with the existing unavailable statuses), edge count, node count, share of edges with Lift < 1. Each reuses `network/metrics.py`; which need new code?
- Wording that keeps Q, Coverage and Silhouette descriptive and never comparable as objectives across graphs.
