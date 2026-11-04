# Appendix A. Published rules of thumb and why this guide does not use them

Papers you read will use cut-offs such as "Q above 0.3 indicates community structure". This guide never does. None of the bands below was calibrated on tag co-occurrence networks, several were made for a different procedure, and some would contradict the study's decision to show stability numbers without labels. Read each metric against its bounds, its reference points and the project's own comparisons instead (see [How to read this chapter](03-metric-reference.md#how-to-read-this-chapter)).

## Modularity

- "In practice, values for such networks typically fall in the range from about 0.3 to 0.7. Higher values are rare." (Newman & Girvan 2004, §IV)
- A value above about 0.3 is "a good indicator of significant community structure" (Clauset, Newman & Moore 2004, §II).
- "Usually, a value of Q larger than 0.3 − 0.4 is a clear indication that the subgraphs of the corresponding partition are modules." (Fortunato & Barthélemy 2007, §II)
- "Values around 0.3 or more usually indicate good divisions" (Newman 2004, §II.C), from a word co-occurrence example.

**Why not here.** These describe unweighted networks at γ = 1. Random networks with no groups also reach high Q (Guimerà, Sales-Pardo & Amaral 2004), the maximum reachable Q depends on the network's size and density (Fortunato & Barthélemy 2007, §III), and the values do not carry over to other γ or to the lift weight. The project compares Q with its own null model instead (`q_excess`, `q_null_mean`).

## Silhouette

- Silhouette coefficient 0.71–1.00: a strong structure; 0.51–0.70: a reasonable structure; 0.26–0.50: weak and possibly artificial; ≤ 0.25: no substantial structure (Struyf, Hubert & Rousseeuw 1997, p. 10, Table 2), offered by the authors as a "subjective interpretation".

**Why not here.** The bands are for the silhouette *coefficient* (the best average silhouette over several numbers of clusters) of partitioning methods such as PAM. Our partition maximises modularity on graph weights and is only scored on Jaccard distance afterwards, so low values are expected by construction. The study labels the silhouette a descriptive diagnostic and compares it with the seed spread instead.

## Cluster-wise Jaccard stability

- In one resample, a cluster whose Jaccard with its best match is 0.5 or less counts as "dissolved", and values above 0.75 as "good recoveries, say"; Hennig suggests summarising a cluster by the mean or by the number of dissolutions or good recoveries (Hennig 2007, §2). The `fpc` package's `clusterboot` documentation adds bands for the mean: values below 0.6 should not be trusted, 0.6–0.75 indicate patterns with doubtful membership, and 0.85 and above highly stable clusters.

**Why not here.** Hennig's measure is per cluster under resampling of the data. Membership Stability is per tag across random seeds on fixed data, and the study decided to show it as a plain number. The one exception is Subsample Stability in the Parameter Selection mode, which uses Hennig's measure itself, on 80% subsamples rather than the bootstrap. There the study takes one cut from Hennig: in a subsample, a Cluster is dissolved when its Jaccard is ≤ 0.5 (Hennig 2007, §2), the smallest value at which every cluster of a partition can be dissolved by a new one. Over the subsamples it applies its own majority rule (**Dissolved in most subsamples**: ≤ 0.5 in more than half) instead of a cut on the mean, and marks a Cluster **borderline** when the 95% Wilson interval of that frequency contains ½. Hennig's 0.75 is reported only as a frequency, never as a label. The `fpc` bands on the mean (0.6, 0.75 and 0.85) stay unused: `fpc` says they refer to the bootstrap. The **Whole-Cluster Jaccard**, which counts lost tags, gets no cut at all, because Hennig's 0.5 argument assumes the two clusters are compared on a common tag set. A Cluster with fewer than two surviving tags in every subsample is **Not assessable** rather than scored.

## Node roles

- Guimerà and Amaral (2005) call nodes with within-module z ≥ 2.5 hubs and split nodes into seven roles by participation coefficient (regions R1–R7), which they describe as defined heuristically.

**Why not here.** The regions come from metabolic networks with large modules and use link counts. In a cluster of n tags the within-cluster z cannot exceed √(n − 1), so z ≥ 2.5 is impossible in clusters of fewer than 8 tags, and the study's clusters are often smaller. The word "hub" is also avoided for Cluster Centers.

## Phi

- Effect size w = 0.10 small, 0.30 medium, 0.50 large (Cohen 1992, Table 1, p. 157). For a 2 × 2 table, w² = χ² / N = phi², so w = |phi| (a derivation; Cohen's table gives the same values for the product-moment r, which phi is for two binary variables).

**Why not here.** The bands were made for power analysis in behavioural science. Phi's reachable maximum depends on the two tags' frequencies (Warrens 2008, §3.2), so "small" can be the largest value possible for a rare tag.

## Reference points that are not bands

Lift 1 and phi 0 mean independence (Brin, Motwani & Silverstein 1997, §3.1); ARI 1 means identical partitions and ARI near 0 chance agreement; Q 0 means no better than random (Newman & Girvan 2004, §IV). These are bounds and reference points, not cut-offs, and the guide uses them. Conventional 0.05 cut-offs for p or q values are not used: the study never calls a result significant.

No published bands were found for conductance, densities, coverage, the modularity z-score, the Seed-Noise Floor SDs, the share ratio or the median tag position.
