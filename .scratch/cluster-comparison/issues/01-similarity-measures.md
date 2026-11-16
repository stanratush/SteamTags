# Which measures can score the similarity of two Clusters from different datasets?
Type: research
Status: resolved
Blocked by:

## Question

A Cluster is a set of Tags. Two Top-N Datasets of one Build give two partitions of two overlapping but different Tag sets. Jaccard on the two Tag sets is the baseline. Find the alternatives worth trying, from primary sources, and say what each one answers that Jaccard does not.

Cover at least:
- **Set-overlap measures for one pair of Clusters:** Jaccard, the overlap coefficient (Szymkiewicz–Simpson), containment in each direction (the share of each Cluster's Tags that are shared, which the view shows anyway), Dice/Sørensen, cosine/Ochiai. How each behaves when the two Clusters differ a lot in size, and when one is nested in the other.
- **Chance correction:** what overlap two Clusters of these sizes would share by chance (hypergeometric expectation, a p-value or a standardised score), and whether a chance-corrected value is sound when the Clusters come from a clustering, not from independent draws.
- **Weighted variants:** weighting a Tag by how many games have it, or by its strength in the network (weighted Jaccard / Ruzicka), and what that changes.
- **Whole-partition measures** for the pair overview: ARI, NMI/AMI, variation of information, and how each is defined when the two partitions cover different element sets (restrict to the common Tags, or treat missing Tags as a class). The repository already uses ARI and NMI inside one dataset (`src/steamstudy/network/metrics.py`, `selection.py`).
- **One-to-many matching:** how the literature on tracking communities across networks or time steps (e.g. Greene et al. 2010; Palla et al. 2007; Hennig 2007 for cluster-wise Jaccard) defines a match, a split and a merge, and what thresholds it uses.

For each candidate give: the formula, its range, its source, how it treats size imbalance and nesting, and whether it needs a common Tag universe. End with a short list of the two to four candidates most worth running beside Jaccard in [Which measures survive on the real Builds?](04-measures-on-real-builds.md)

Findings go in `research/01-similarity-measures.md`.

## Answer

Findings: [research/01-similarity-measures.md](../research/01-similarity-measures.md).

- Every symmetric set-overlap measure (Jaccard, Dice, cosine/Ochiai, overlap coefficient, Hopcroft's match value) is a mean of the two containments the view already shows, so none adds information to them. Dice ranks pairs exactly as Jaccard does. Jaccard cannot tell a nested Cluster from a partial overlap; the containments can.
- A hypergeometric expectation (overlap the two sizes alone would give, on the common Tags) is usable as a descriptive ratio, the same construction as Lift. A p-value or z-score is not sound: the overlaps within one partition are dependent, Cluster sizes are outcomes, the random-shuffle null is not plausible, and the Clusters are small.
- Weighted Jaccard (Σmin/Σmax) is left out: per-dataset Tag weights are not on one scale, and identical Tag sets would score below 1.
- Different Tag sets: the sources restrict to the common elements and report coverage separately (Hennig 2007; Strehl & Ghosh 2002), as the repository already does. No source was found for treating missing Tags as a class. Unadjusted NMI and VI are biased at this few Tags per Cluster; ARI (already implemented) or AMI are the defensible overview measures. NMI is not in the code today, contrary to the ticket text.
- Tracking literature: one-to-many matching is a threshold on a pairwise measure (Jaccard θ 0.1–0.5, lower for splits and merges, Greene et al.; min-containment 0.5–0.7, Hopcroft et al.; directional inclusion 50–100%, GED). A Jaccard minimum of 0.5 forces one-to-one matching and hides every split and merge.
- **Shortlist to run beside Jaccard in ticket 04:** (1) the two containments with their minimum as a strict summary: is one Cluster inside the other; (2) Jaccard on the common Tags beside the plain Jaccard: is a low score regrouping or just absent Tags; (3) overlap Lift on the common Tags, with the expected overlap: is the overlap more than the sizes alone give; (4) ARI on the common Tags with the share of common Tags, for the pair overview.
- Not verified against the source: Dice 1945, Sørensen 1948, Szymkiewicz 1934, Simpson 1943, Ružička 1958, Hubert & Arabie 1985, Real & Vargas 1996, Baselga 2010, Asur et al., Palla et al.'s Supplementary Information. Each is marked in the findings with what the claim rests on instead.
