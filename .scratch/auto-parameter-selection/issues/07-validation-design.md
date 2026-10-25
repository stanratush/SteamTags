# Validation design
Type: grilling
Status: open
Blocked by: 02, 03

## Question

For each dataset's selected Threshold Pair, exactly how are the null-model comparison and Subsample Stability run and reported?

- The null: at least 100 curveball replicates (trades per replicate as [Validation methods](02-validation-methods.md) recommends). Is the "consistent clustering procedure" the full γ scan + CHAMP + stable-partition selection at the same (g, s), or clustering at the Selected Resolution? Which statistics are compared (Q at γ, number of Multi-Tag Clusters, whether a qualifying Stable Partition exists, edge count)? The null-to-observed edge-count ratio is a diagnostic only.
- Subsampling: the number of 80% subsamples (e.g. 100), the threshold scaling rule (round, floor or ceil of 0.8·g and 0.8·s, with a minimum), and whether γ is re-selected per subsample or held at the Selected Resolution.
- Reported: ARI against the Selected Partition on shared tags, Hennig cluster-wise Jaccard per Multi-Tag Cluster, retained-tag coverage.
- What counts as a "failure" that is reported transparently (thresholds or wording), without ever changing the selected parameters.
- Seeds for replicates and subsamples (new seed streams), and the run cost.
