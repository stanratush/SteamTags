# Per-pair metric definitions
Type: grilling
Status: resolved
Blocked by: none

## Question

What is the exact formula, and the "unavailable" rule, for every metric reported per **Threshold Pair**?

- **Neighbour Agreement**: ARI between Selected Partitions on the intersection of the two pairs' tags. Do isolated tags count? The neighbours are (g−1, s), (g+1, s), (g, s−1), (g, s+1). What happens at the grid edges and the s ≤ g border (fewer neighbours, so a mean over the available ones)? If a neighbour has no Selected Partition, is it missing or 0? "Identical graphs count as agreement = 1": does that mean identical graphs, or identical Selected Partitions? Report each direction's node overlap (Jaccard or count) and ARI separately.
- **Seed-Noise Floor** at the Selected Resolution: minimum ARI over the noise seeds against the Selected Partition (which came from the scan, not from the main seed).
- **Information Retention**: the numerator and denominator. Are game–tag assignments counted over all tags of the dataset, or only over visible tags after hiding Genre Tags and the defining tag? Over games after the Minimum Months Filter?
- **Fragmentation**: isolated tags (count, share of nodes), largest connected component (tags, share), number of Multi-Tag and One-Tag Clusters.
- **Descriptive metrics**: Q at the Selected Resolution, weighted Coverage on Lift, Jaccard silhouette (with the existing unavailable statuses), edge count, node count, share of edges with Lift < 1. Each reuses `network/metrics.py`; which need new code?
- Wording that keeps Q, Coverage and Silhouette descriptive and never comparable as objectives across graphs.

## Answer

Decided by grilling with the researcher, 2026-10-26. Every metric below is per **Threshold Pair**. A metric that needs a partition is unavailable, with status `no_selected_partition` plus the pair's reason from [Resolution-selection rules](03-resolution-selection-rules.md), when the pair has no Selected Partition. The graph-level figures are always available.

**Facts these rest on** (from `network/graph.py`, `stability.py`, `metrics.py`)
- Within a dataset, a tag's game count and every edge's Lift depend only on the fixed game set. So the (g+1, s) graph is the (g, s) graph restricted to tags with ≥ g+1 games, and (g, s+1) has the same tags as (g, s) with some edges removed. Tag overlap with an s-neighbour is always 100%, and with a g-neighbour always |nodes(g+1)| / |nodes(g)|.
- Isolated tags are always One-Tag Clusters. `stability.ari` scores all nodes, so tags isolated in both partitions add agreement for free. That pushes ARI towards pair-F1, more so as fragmentation grows.

**Neighbour Agreement**
- **Neighbours**: (g−1, s), (g+1, s), (g, s−1), (g, s+1), limited to the grid (3 ≤ g ≤ 20, 2 ≤ s ≤ 12, s ≤ g).
- **Compared tags**: the shared tags with at least one edge in at least one of the two graphs. A tag isolated in both is dropped; a tag isolated in one graph and clustered in the other counts as a real disagreement.
- **Per direction**, one record, stored once per unordered neighbour pair (ARI is symmetric):
  - `status`: `ok`, `outside_grid`, `neighbour_has_no_selected_partition` or `too_few_compared_tags` (fewer than 2 compared tags; never 1.0, unlike `ari` on an empty set);
  - the number of shared tags and their Jaccard overlap;
  - the number of compared tags;
  - `identical_graph`;
  - the ARI between the two Selected Partitions on the compared tags.
- **Aggregate**: the **mean ARI over the comparable neighbours**, those with status `ok`.
  - A neighbour without a Selected Partition is **missing, never 0**.
  - The pair reports how many neighbours are in the grid, comparable and missing, and how many of the comparable ones have an identical graph.
  - The minimum over comparable neighbours is reported, as a descriptive value only.
  - With no comparable neighbour, the pair's Neighbour Agreement is unavailable: `no_comparable_neighbours`.
- **Identical graphs are not special-cased.** Identical graphs give identical Selected Partitions, so ARI = 1 is computed normally. The `identical_graph` flag and count make visible when agreement only means a threshold step removed nothing.
- **Independent of eligibility.** A neighbour's Selected Partition is used whether or not that neighbour passes the constraints of [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md). Neighbour Agreement never depends on the constraint settings, so those stay out of its part of the cache key.

**Seed-Noise Floor at the Selected Resolution**
- Leiden at the **exact, unrounded Selected Resolution**. This is defined even for `not_representable` pairs. After Apply, the Workbench computes its own floor at its two-decimal γ.
- **Seeds**: the existing `noise_seeds(main_seed, 10, 20)`, unchanged. The scan seed stream excludes those seeds and the null-replicate seeds.
- **ARI over all nodes**, exactly as `stability.ari` does today, so the term means one thing app-wide. It is never compared numerically with Neighbour Agreement.
- **Reported**: the minimum ARI against the Selected Partition (the floor), the mean ARI, and how many noise runs reproduce the Selected Partition exactly.

**Information Retention**
- Numerator: Σ |games of t| over tags with at least one edge.
- Denominator: Σ |games of t| over the **visible** tags: every tag of the dataset except hidden and removed ones, tags below g included.
- Games are those left after the Minimum Months Filter.
- Unavailable (`no_visible_tags`) when the denominator is 0.
- Also reported, descriptive only: the share of games with at least one tag that has an edge.
- The glossary entry now says "visible" and "after the Minimum Months Filter".

**Fragmentation**
- Isolated tags: count, and share of all nodes.
- Number of connected components with ≥ 2 tags.
- Largest connected component: its tags, and its share of the **non-isolated** tags. This keeps ticket 06's isolated-share and LCC-share constraints independent.
- From the Selected Partition: the number of Multi-Tag Clusters, and of One-Tag Clusters split into isolated and connected.

**Descriptive metrics** (Selected Partition, exact Selected Resolution, Lift graph)
- Q: `metrics.modularity`. A test checks it against CHAMP's (Â − γP̂)/2m.
- Weighted Coverage: `metrics.coverage`.
- Jaccard silhouette: `metrics.silhouette`, with its existing statuses. Isolated tags still count as "other clusters" for b(i). The distance matrix is computed once per g, since nodes depend only on g.
- Graph counts, always available: tags, edges, and the share of edges with Lift < 1.
- **New code** is only these: Neighbour Agreement (a thin wrapper that picks the compared tags for `ari`), Information Retention, Fragmentation, and the Lift < 1 share. Everything else reuses `network/metrics.py` and `stability.py`.

**Wording**
- Q, Coverage and Silhouette sit in a group labelled **"Descriptive: not comparable across pairs"**, with the shared help text: *"Describes this pair's Selected Partition on its own network. Pairs differ in tags and edges, so a higher value at one pair does not make it a better choice."*
- The selection explanation never cites them.
- Their heatmaps carry the same caption and no "best" marker.

**Handed on**
- To [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md): whether a pair needs a minimum number of comparable neighbours (without one, a single lucky neighbour scores 1.0), and whether the identical-graph count affects eligibility.
- To [Exploratory grid run on the current Build](05-exploratory-grid-run.md): record those counts per pair.
