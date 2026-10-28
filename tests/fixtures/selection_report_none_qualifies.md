# Parameter Selection report

Build 20261005T150000Z-abcdef12 · Default settings.

## Overall

**Selected: g = 15, s = 3**, resolution 1.385 (Workbench 1.38).

Custom constraints: Information Retention ≥ 1.00 (default 0.50) · Default settings.

9 of 9 pairs have a Selected Partition. 3 qualify under the custom constraints: Information Retention ≥ 1.00, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a different graph. The retention, isolated-share and LCC constraints excluded no pair.

The highest Neighbour Agreement among them is 1.00 (g = 15, s = 3). 3 pairs are within 0.05 of it, and of these the one with the smallest g, then the smallest s, is selected.

Its Neighbour Agreement is 1.00 over 2 neighbours with a different graph. 1 more neighbour has an identical graph and is not counted.

*Neighbour Agreement measures how little the clustering changes when g or s moves by one. It does not show that the Clusters are real.*

*Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, particularly s, generally produces a smaller change in the graph. This can increase agreement independently of the robustness of the Clusters. Choosing the smallest g among near-best pairs partially counterbalances this tendency.*

**Validation of g = 15, s = 3**

**Null Comparison** (2 shuffled networks, same g and s). Q at resolution 1.385 is 0.163; no shuffled network reaches it (−0.050 to −0.047). 1 of 2 also have a Selected Partition, with narrower domains (median 0.0807 against 1.43; wider than all 1).

*This shows only that the network is not random, not that its Clusters are real.*

**Subsample Stability** (2 random 80% subsets of the games, g′ = 12, s′ = 2). Re-selected: median ARI 1.00 (1.00–1.00) over 2 of 2 subsamples. At resolution 1.385: median ARI 1.00 (1.00–1.00). No Multi-Tag Cluster is dissolved (mean Jaccard ≤ 0.5) in either arm.

*This measures how much the clustering depends on which games are in the dataset. It does not show that the Clusters are real either.*

## Puzzle

**No pair qualifies** under the custom constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 1.00: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## RPG

**No pair qualifies** under the custom constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 1.00: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## Strategy

**No pair qualifies** under the custom constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 1.00: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## Simulation

**No pair qualifies** under the custom constraints. 0 of 9 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): Information Retention ≥ 1.00: 0 (0), isolated tags ≤ 10%: 0 (0), largest component ≥ 90% of the tags with an edge: 0 (0), ≥ 2 neighbours with a different graph: 0 (0). Loosen a constraint, or inspect any pair in the grid and apply it by hand.

## Methods

For each Top-100 Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, 15–17 games per tag and 2–4 shared games with s ≤ g (9 pairs), with Lift as the Clustering Weight, a Minimum Months Filter of 0 and 11 Genre Tags and each dataset's defining tag hidden. On each distinct graph we ran Leiden (RBConfiguration, at most 1,000 passes) with 10 seeds at every γ from 0 to Gibson and Mucha's γ_max(K), K being the number of tags with an edge, in steps of 0.05 (Gibson & Mucha 2022, SI §J); the derivation in SI §J.2 uses only the Cauchy–Schwarz inequality and assortativity, so the bound also holds for Clusters of unequal size and for weighted graphs. The unique partitions found were reduced to the upper envelope of their lines Q(γ) = Â − γP̂, giving the Admissible Partitions and their Optimality Domains (CHAMP; Weir et al. 2017, §2, eqs. 1–4). For each we evaluated once the self-consistent resolution γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) (Newman 2016, §III.A, eqs. 15–18) and called the partition stable when γ̂ lies in its own domain (Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3). Among the Stable Partitions with at least 3 Multi-Tag Clusters, the Selected Partition has the widest domain in plain γ units, and the Selected Resolution is the domain's midpoint; the sources give no rule for choosing among Stable Partitions, and we did not rescale the width to log γ or to Gibson and Mucha's γ-scaled area (SI §A.7), whose usefulness the authors leave open. Neighbour Agreement is the mean adjusted Rand index between a pair's Selected Partition and those of its grid neighbours (g ± 1, s ± 1) with a different graph, on the shared tags with an edge in either graph. The chosen pair is the one with the smallest g, then the smallest s, among the pairs whose Neighbour Agreement is within 0.05 of the highest, among pairs with Information Retention ≥ 1.00, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a different graph. We compared the chosen pair with 2 networks whose game–tag table was shuffled by curveball trades (every tag and game keeps its count), each analysed by the identical procedure (Karrer, Levina & Newman 2008, abstract, §III and §VI), and with 2 random subsets of m = ⌊0.8·n⌋ of the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)). For each Multi-Tag Cluster we report Hennig's (2007, §2) mean best-match Jaccard on the tags present in both networks, over the B* subsamples in which the Cluster has a tag, and call it dissolved at a mean of 0.5 or less; the 0.6, 0.75 and 0.85 bands of the fpc package refer to the bootstrap and are not applied.
