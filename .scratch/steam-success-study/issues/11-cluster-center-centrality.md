# Cluster center and centrality measures
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 05, 19

## Question

Which graph-based measure defines each cluster's central node (with tie-break rule), and which node centralities (global and intra-cluster) are computed, shown and exported?

Surfaced by [Tag network app interaction prototype](14-tag-network-app-prototype.md):
- A one-tag cluster (isolated tag) is its own center by definition. Should it get the center styling (◆) or not? (The prototype gave it none and greyed singletons out.)
- On mock data with raw edge weights, the placeholder center (max intra-cluster weighted degree) picked generic tags (Singleplayer, Indie, PvP); see [Edge weight used for clustering](19-edge-weight-for-clustering.md).

Settled by [Edge weight used for clustering](19-edge-weight-for-clustering.md):
- The shared-game count stays the default Clustering Weight, so the frequency bias seen on mock data persists by default; a centre defined by intra-cluster weighted degree will favour generic tags unless the Lift mode is active. Weighted degree is always computed both ways (`strength_shared`, `strength_lift`, global and intra-cluster), active mode shown first. Any further weight-based centrality must say which weight it uses; a Jaccard medoid is mode-independent.

Settled by [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md):
- Clusters come from Louvain (default) or Leiden (optional `algorithm` mode); under Louvain a cluster can be disconnected (flagged `connected = false`, never split), so any center or centrality needing a connected intra-cluster subgraph must say what it does then.
- One-Tag Clusters are counted apart from Multi-Tag Clusters (glossary). Jaccard distance on game sets (over the games after the Minimum Months Filter) is already computed for silhouette and can be reused for a medoid.

## Answer

Resolved 2026-10-04 with the researcher. The center measures typicality, not frequency. The frequency-driven alternative stays visible next to it, so the bias is shown openly rather than hidden.

**Cluster Center** (new glossary term, [CONTEXT.md](../../../CONTEXT.md))
- **Jaccard medoid**: the member with the smallest `medoid_score` = mean Jaccard distance d(u,v) = 1 − |G_u ∩ G_v| / |G_u ∪ G_v| to the other members of its cluster, with G_t counted over the loaded dataset after the Minimum Months Filter (the silhouette's distance, [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md)).
- Independent of the Clustering Weight and the algorithm for a given partition; changes only when the partition changes.
- Works on disconnected Louvain clusters (game-set distance, not graph paths), computed over the whole cluster; the `connected` flag is shown beside it.
- **Tie-break**: scores compared rounded to 12 decimals; on a tie, more `n_games` wins, then the lower `tagid`. Rule recorded in export metadata and the methods section.
- **Only clusters of 3+ tags have a center.** One-Tag Clusters: "n/a (one-tag cluster)", no ◆, greyed as in the prototype. Two-tag clusters: "n/a (two-tag cluster)", no ◆ (the medoid is always a tie there, so the tie-break alone would pick the more frequent tag); both members still get a `medoid_score`.

**Frequency-driven comparison**: `top_strength_tag` = the member with the highest intra-cluster strength on the active Clustering Weight, same tie-break, same n/a rule (none for one- or two-tag clusters).

**Where it shows**
- Graph: ◆ with a heavier outline on the Cluster Center only.
- Clusters table, cluster inspector, Analysis Report mode, and the feature-analysis report's cluster list: `center`, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength`.
- Cluster inspector: members ranked by `medoid_score`, with intra-cluster strength (active mode first), `within_z` and `participation` as columns.
- Node inspector and Nodes table: every node metric below; Nodes table adds `is_center`.

**Per-node metrics** (in addition to the settled `strength_shared` / `strength_lift`, global and intra-cluster, and per-node silhouette)
- `n_games` (games with the tag after the Minimum Months Filter), `degree` and `degree_intra` (unweighted), `medoid_score`, `is_center`.
- `within_z` (Guimerà–Amaral within-module degree z-score) on the active Clustering Weight: Multi-Tag Clusters only; n/a for One-Tag Clusters and when every member has the same intra-cluster strength.
- `participation` = 1 − Σ_s (k_is / k_i)² on the active Clustering Weight, s over **every** cluster of the partition including One-Tag Clusters; n/a at zero strength.
- The active `clustering_weight` is recorded in metadata (already required).
- **Not computed**: betweenness, closeness (need a 1/w distance transform; betweenness is the costly one), eigenvector, PageRank (track strength closely in dense tag graphs; eigenvector is ambiguous on disconnected subgraphs). `participation` covers the "bridge tag" question.

**Cost**: one n_c² pass per cluster over the Jaccard matrix the silhouette already builds, plus O(E) for degrees, strengths, z and participation; negligible next to clustering.

**For the methods section**: "Each cluster of three or more tags is given a center: its Jaccard medoid, the tag whose set of games is on average most similar to those of the other tags in the cluster (ties: more games, then lower tag id). The tag with the highest within-cluster weighted degree is reported alongside it to show the effect of tag frequency. Centers mark the most typical tag of a cluster, not the most important one."
