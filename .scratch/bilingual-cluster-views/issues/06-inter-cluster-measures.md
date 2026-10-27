# Inter-cluster measures
Type: grilling
Status: open
Blocked by: 05

## Question

Exactly what does feature 3 compute for each pair of Clusters? Uses `grilling` + `domain-modeling` and works from [Normalised inter-cluster strength in the literature](05-normalised-inter-cluster-strength.md).

- The normalisation, or normalisations, and which one is the headline "connection strength". Its name in CONTEXT.md and the words to avoid.
- Weights: the shared-game total always, plus the Lift total and its normalised strength under Lift (settled while charting). Is strength computed on both?
- One-Tag Clusters: keep the existing `one_tag_pool`, show each One-Tag Cluster on its own, or leave them out.
- The per-cluster view ("how strongly C3 connects to every other cluster"): its ordering, shares of the cluster's external weight, and whether zero-edge pairs are listed.
- New `cluster_connections.csv` columns (additive, `schema.py`, guide index, column appendix), and whether any number is read against a baseline or band.
- The guide entries: metric reference text and a caution about what strength does not mean.
