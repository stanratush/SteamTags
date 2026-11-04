# Parameter Selection report

Build 20261005T150000Z-abcdef12 · Default settings.

## Overall

**Selected: g = 15, s = 3**, resolution 1.385 (Workbench 1.38).

Default constraints · Default settings.

9 of 9 pairs have a Selected Partition. 3 qualify under the default constraints: Information Retention ≥ 0.50, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a different graph. The retention, isolated-share and LCC constraints excluded no pair.

The highest Neighbour Agreement among them is 1.00 (g = 15, s = 3). 3 pairs are within 0.05 of it, and of these the one with the smallest g, then the smallest s, is selected.

Its Neighbour Agreement is 1.00 over 2 neighbours with a different graph. 1 more neighbour has an identical graph and is not counted.

*Neighbour Agreement measures how little the clustering changes when g or s moves by one. It does not show that the Clusters are real.*

*Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, particularly s, generally produces a smaller change in the graph. This can increase agreement independently of the robustness of the Clusters. Choosing the smallest g among near-best pairs partially counterbalances this tendency.*

**Validation of g = 15, s = 3**

**Null Comparison** (2 shuffled networks, per-pair procedure at g = 15, s = 3)

Q at resolution 1.385 is 0.163; none of the 2 shuffled networks with a Q reaches it (range over 2 shuffled networks: −0.050 to −0.047).

Multi-Tag Clusters: observed 4, median 3 (range over 1 shuffled networks with a Selected Partition: 3 to 3). Median domain width 0.081 vs observed 1.426; observed wider than 1 of 1. Widths are upper bounds, conditional on the partitions the γ scan finds.

*This shows only that the network is not random, not that its Clusters are real.*

**Subsample Stability** (2 random 80% subsets of the games, g′ = 12, s′ = 2).

Re-selected: median ARI 1.00 (10th–90th percentile: 1.00 to 1.00) over 2 of 2 subsamples, on 100% of the tags. At resolution 1.385: median ARI 1.00 (10th–90th percentile: 1.00 to 1.00).

**Borderline** (the 95% Wilson interval contains ½): in both arms: *C1 (tag 5000, tag 5001, tag 5002, …)*, *C2 (tag 5010, tag 5011, tag 5012, …)*, *C3 (tag 5020, tag 5021, tag 5022, …)*, *C4 (tag 5030, tag 5031, tag 5032, …)*.

No Multi-Tag Cluster is dissolved in most subsamples in either arm.

*This measures how much the clustering depends on which games are in the dataset. It does not show that the Clusters are real either.*

*The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no part in the choice, so the Null Comparison is barely affected.*

## Puzzle

**No pair qualifies** under the default constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 0.50: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## RPG

**No pair qualifies** under the default constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 0.50: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## Strategy

**No pair qualifies** under the default constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 0.50: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## Simulation

**No pair qualifies** under the default constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 0.50: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## Methods

For each Top-100 Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, 15–17 games per tag and 2–4 shared games with s ≤ g (9 pairs), with Lift as the Clustering Weight, a Minimum Months Filter of 0 and 11 Genre Tags and each dataset's defining tag hidden. On each distinct graph we ran Leiden (RBConfiguration, at most 1,000 passes) with 10 seeds at every γ from 0 to Gibson and Mucha's γ_max(K), K being the number of tags with an edge, in steps of 0.05 (Gibson & Mucha 2022, SI §J); the derivation in SI §J.2 uses only the Cauchy–Schwarz inequality and assortativity, so the bound also holds for Clusters of unequal size and for weighted graphs. The unique partitions found were reduced to the upper envelope of their lines Q(γ) = Â − γP̂, giving the Admissible Partitions and their Optimality Domains (CHAMP; Weir et al. 2017, §2, eqs. 1–4). For each we evaluated once the self-consistent resolution γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) (Newman 2016, §III.A, eqs. 15–18) and called the partition stable when γ̂ lies in its own domain (Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3). Among the Stable Partitions with at least 3 Multi-Tag Clusters, the Selected Partition has the widest domain in plain γ units, and the Selected Resolution is the domain's midpoint; the sources give no rule for choosing among Stable Partitions, and we did not rescale the width to log γ or to Gibson and Mucha's γ-scaled area (SI §A.7), whose usefulness the authors leave open. Neighbour Agreement is the mean adjusted Rand index between a pair's Selected Partition and those of its grid neighbours (g ± 1, s ± 1) with a different graph, on the shared tags with an edge in either graph. The chosen pair is the one with the smallest g, then the smallest s, among the pairs whose Neighbour Agreement is within 0.05 of the highest, among pairs with Information Retention ≥ 0.50, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a different graph. We compared each validated Threshold Pair with 2 networks whose game–tag table was shuffled by curveball trades (every tag and game keeps its count; Strona et al. 2014), each analysed by the identical procedure: the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the Selected Partition rule), not the Parameter Grid or the choice of pair (Karrer, Levina & Newman 2008, abstract, §III and §VI). Q at the observed Selected Resolution was taken as the best of each network's scan envelope and 10 Leiden runs at exactly that γ, on the observed network and every replicate alike; we report how many of the D shuffled networks with a defined Q reach the observed Q, and give no p-value, because the resolution and the pair were chosen on the observed data. We also compared the pair with 2 random subsets of m = ⌊0.8·n⌋ of the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)), once re-selecting by the same per-pair procedure and once reading the partition at the observed resolution. For each Multi-Tag Cluster we report Hennig's (2007, §2) mean best-match Jaccard on its tags present in both networks, over the B* subsamples in which at least two of them survive, with its Monte Carlo standard error and the frequencies of values ≤ 0.5 and > 0.75 with 95% Wilson intervals (Wilson 1927), and a Whole-Cluster Jaccard that counts lost tags as not recovered. We call a Cluster dissolved in most subsamples when its Jaccard is 0.5 or less in more than half of the B* subsamples (the per-subsample cut is Hennig's, the majority our rule); the 0.6, 0.75 and 0.85 bands of the fpc package refer to the bootstrap and are not applied. The pair was chosen on the same data, so Subsample Stability may be slightly optimistic.
