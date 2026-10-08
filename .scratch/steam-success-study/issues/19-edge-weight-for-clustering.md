# Edge weight used for clustering
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

The brief fixes the Tag Network edge weight as the raw number of games having both tags. Raw co-occurrence counts are dominated by frequent tags (e.g. Singleplayer, Action), which drives modularity-based clustering and weighted centrality toward them. Should community detection, weighted degree and quality metrics run on the raw count, or on a normalised weight (e.g. association strength / lift, Jaccard, cosine) while the displayed and exported edge weight stays the raw count? If normalised, which measure, and are both weights exported?

Context: [Graph clustering and quality methods](05-graph-clustering-methods.md).

Surfaced by [Tag network app interaction prototype](14-tag-network-app-prototype.md):
- Evidence: on mock data at the 8/8 defaults with raw counts, generic tags (Singleplayer, Indie, PvP) became cluster centers and one large cluster formed around Singleplayer. The shared defaults (min games per tag 8, min shared games 8) apply to raw counts in any case: the edge threshold filters on the raw count whatever weight clustering uses.

## Answer

Resolved 2026-10-04 with the researcher. The brief's raw count stays the default; the frequency-corrected alternative is an optional mode, so the frequency effect can be shown openly rather than silently removed.

**Edge weight**: always the shared-game count (glossary: Tag Network), in every mode. It drives the thresholds (min games per tag, min shared games), edge thickness and the edge inspector.

**Clustering Weight** (new glossary term): the per-edge value community detection runs on, in one of two modes:
- `shared_games` (**default**): the edge weight itself, as in the brief.
- `lift` (optional): `lift = shared · N / (n_i · n_j)`, observed ÷ expected co-occurrence. Equal to association strength [van Eck & Waltman 2009] up to a constant factor; since modularity is invariant to rescaling all weights, both give identical clusters.
- **N** = games in the loaded Top-100 Dataset after the Minimum Months Filter; `n_i` = those games that have tag i. At Minimum Months Filter 0 an edge's lift equals the pair's `lift` in the feature-analysis association table ([Feature-analysis definitions](13-feature-analysis-definitions.md)). Hiding Genre Tags or the defining tag, or removing nodes, does not change N or any remaining edge's lift.
- Edges with lift < 1 that pass the shared-games threshold are **kept** in Lift mode with weight = lift (always > 0). Both modes cluster the same edge set.

**Where the mode is chosen**
- Shared network-defaults config: `clustering_weight = "shared_games"`.
- App: a "Clustering weight: Shared games / Lift" selector beside seed and γ, initialised from the config. Shown in both app modes (Workbench and Analysis Report mode).
- Feature-analysis report: uses the config value only. A Lift report is a second Build with the config changed.

**What follows the mode**
- Community detection.
- All graph quality metrics: modularity and its null-model baseline, coverage, conductance, intra-cluster density (measured on the weight that was optimised).
- Global layout: the weighted seeded `spring_layout` uses the active Clustering Weight; positions are computed once per dataset + Minimum Months Filter + mode and cached (refines [Web stack selection](18-web-stack-selection.md)). Cluster-separated positions follow, since they derive from the network state.
- Node-removal sensitivity and its seed-noise floor (they re-cluster).

**What does not follow the mode**: thresholds, edge thickness, the edge inspector, and any Jaccard-on-game-sets measure (the silhouette distance and medoid recommended in [Graph clustering and quality methods](05-graph-clustering-methods.md), if adopted).

**Weighted degree**: always computed both ways, `strength_shared` and `strength_lift` (global and intra-cluster), with the active mode's value shown first.

**Exports and caching**
- Every edge row carries both `shared_games` and `lift`, whatever the mode.
- App exports and the report's metadata record `clustering_weight` next to seed, γ and algorithm.
- `clustering_weight` is part of every network-state cache key.

**For the methods section**: "Edges are shown and thresholded by the number of shared games; communities are detected on the shared-game count by default, with lift (association strength) as an optional frequency-corrected alternative."

## Comments

- 2026-10-09: Edge thickness now follows the Clustering Weight (lift thickness under Lift, with a switch back to shared games); the thresholds and the edge inspector still use shared games. See [Edge thickness follows the Clustering Weight](../../edge-thickness/issues/01-thickness-follows-clustering-weight.md).
