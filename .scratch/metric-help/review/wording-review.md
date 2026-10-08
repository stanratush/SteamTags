# Metric help: wording review

Generated on 2026-10-08 from Build `20261006T062622Z-7a23ae9f` (first dataset, default settings) by `make_review.py`, from the app's own components and the User Guide. **Do not edit this page**: correct the guide entry it links to, then run the script again.

How to review (spec: *Review*; issue 07):

- Each surface lists every element of the app that has help: its tooltip (layer 1) and the guide entry a click opens (layer 2). Labels are bold; a line the app adds below the guide text (a **Now:** line of live values, the column or Network State field) is in italics.
- A tooltip is written out in full the first time its entry appears; later elements with the same entry say so and show only the lines the app adds.
- Words: the In short block's length, against the cap of 60.
- The appendix gives every linked entry's *Why it matters here.* paragraph once.
- Write a correction as a comment under issue 07, or edit the guide entry directly. Tick a surface when its wording is approved.

## Decisions

- [x] **"the most-played games"**, not "successful games" (decided 2026-10-08). Entries the app links to that still say "success…" in their In short or Why it matters: none.
- [x] **Self-explanatory controls carry no help** (decided 2026-10-08): the minimum games per tag, the minimum shared games, Hidden Genre Tags, Hide defining tag, Remove / Restore, Global / Cluster-separated and Tidy. Their entries stay in the guide, linked from the Control reference; Tidy keeps a native title.
- [ ] **A pill's click** (pill bar, medium and narrow forms) opens its popover, whose dotted label then opens the entry; hover and Tab show the In short. The spec asked for the click to open the entry (issue 05).

## 1 Summary row (above the graph)

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| Games | **In short.** How big the network is: the games it is built from, the tags shown as nodes, and the links between tags that share enough games.<br>**Higher →** more tags and links: a larger network, usually from looser thresholds.<br>**Here:** shows how much of the dataset and its tags the clusters describe.<br>**Caution:** most other numbers shift with size; compare Network States of similar size.<br>*Now: 100 of the dataset's 100 games pass the Minimum Months Filter.* | [Network size](../../../docs/user-guide/03-metric-reference.md#network-size) | 60 |
| Tags | *Same In short as Games (Summary row).* | [Network size](../../../docs/user-guide/03-metric-reference.md#network-size) | 60 |
| Links | *Same In short as Games (Summary row).*<br>*Now: shuffled networks average 290 links.* | [Network size](../../../docs/user-guide/03-metric-reference.md#network-size) | 60 |
| Clusters | **In short.** Groups of tags linked more among themselves than chance predicts; C1 is the largest.<br>**Higher →** more multi-tag clusters: the tags split into more, smaller groups.<br>**Here:** each cluster is a candidate group of characteristics that co-occur in pairs among the most-played games.<br>**Caution:** the count depends on γ, the thresholds and the seed; one-tag clusters are usually isolated tags, not findings.<br>*Now: all other seeds give 3 multi-tag clusters.* | [Cluster labels and counts](../../../docs/user-guide/03-metric-reference.md#cluster-labels-and-counts) | 58 |
| Q | **In short.** How much more link weight falls inside clusters than if links were placed at random, keeping each tag's total weight.<br>**Higher →** more weight inside clusters than that expectation; 0 = no more than expected.<br>**Here:** the clustering's target score; read it through its excess over the null model.<br>**Caution:** random networks also reach high Q; not comparable across γ, weights, thresholds or datasets.<br>*Now: γ = 1.00; null mean 0.07 ± 0.01 from R = 20 shuffled networks; excess = Q − null mean.* | [Modularity Q](../../../docs/user-guide/03-metric-reference.md#modularity-q) | 60 |
| Silhouette | **In short.** On average, whether tags' games overlap more with their own cluster than with the nearest other; descriptive diagnostic, not a selection criterion.<br>**Higher →** clearer separation; 0 = between clusters; below 0 = closer to another.<br>**Here:** a second view, from game overlap; the links come from the same games.<br>**Caution:** tag distances are mostly near 1, so values near 0 are common.<br>*Now: SD across seeds 0.00.* | [Mean silhouette](../../../docs/user-guide/03-metric-reference.md#mean-silhouette) | 59 |

## 2 Cluster quality tab

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| Q | *Same In short as Q (Summary row).*<br>*Now: γ = 1.00; null mean 0.07 ± 0.01 from R = 20 shuffled networks.* | [Modularity Q](../../../docs/user-guide/03-metric-reference.md#modularity-q) | 60 |
| Null-model excess | **In short.** Q minus the shuffled networks' mean Q: how far Q exceeds what the preserved tag and game counts give.<br>**Higher →** more modularity than the shuffled data; 0 = no more.<br>**Here:** the main check that clusters reflect how characteristics combine, not just popularity.<br>**Caution:** not a share of causes; z is not a p value and can be large for a modest excess.<br>*Now: Q 0.17 − null mean 0.07 ± 0.01 from R = 20 shuffled networks; z 15.* | [Excess modularity and z-score](../../../docs/user-guide/03-metric-reference.md#excess-modularity-and-z-score) | 60 |
| Coverage | **In short.** The share of all link weight that falls inside clusters.<br>**Higher →** more of the weight inside clusters; 1 = all of it, which a single cluster also gives.<br>**Here:** shows how much of the tags' co-occurrence the clusters account for.<br>**Caution:** rises as clusters get fewer and bigger; never read it alone. | [Coverage and inter-cluster weight share](../../../docs/user-guide/03-metric-reference.md#coverage-and-inter-cluster-weight-share) | 49 |
| Silhouette | *Same In short as Silhouette (Summary row).*<br>*Now: SD across the K = 10 seeds 0.00.* | [Mean silhouette](../../../docs/user-guide/03-metric-reference.md#mean-silhouette) | 59 |
| Seed noise | **In short.** ARI (adjusted Rand index): how similar two clusterings of the same tags are, corrected for chance.<br>**Higher →** 1 = identical clusters; about 0 = no more agreement than chance.<br>**Here:** the Seed-Noise Floor: how much the clusters change when only the random seed changes.<br>**Caution:** drops faster in small networks, and does not say which tags moved.<br>*Now: each of the K = 10 extra seeds against the clusters shown; min is the seed that differed most.* | [Adjusted Rand index](../../../docs/user-guide/03-metric-reference.md#adjusted-rand-index) | 54 |
| Q (γ = 1.00) 0.17 vs null 0.07 ± 0.01 (excess… | **In short.** How the tags split into clusters and how clearly: Q with its excess over the null model, coverage, the cluster counts and the silhouette.<br>**Here:** together they show whether the most-played games' tags fall into groups beyond the shuffled baseline.<br>**Caution:** each number answers a different question; read them together, never one alone. | [Clusters and partition quality](../../../docs/user-guide/03-metric-reference.md#clusters-and-partition-quality) | 51 |
| Seed-noise floor (K = 10): ARI vs. main min 0… | **In short.** The Seed-Noise Floor: how much the clusters and their scores vary when only the random seed changes.<br>**Here:** separates findings about the games from accidents of one run of the clustering.<br>**Caution:** the K extra seeds are a sample, not every possible run. | [Stability](../../../docs/user-guide/03-metric-reference.md#stability) | 41 |

## 3 Inspector (labels and table headers)

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| Cluster | *Same In short as Clusters (Summary row).*<br>*Column: cluster (nodes.csv)* | [Cluster labels and counts](../../../docs/user-guide/03-metric-reference.md#cluster-labels-and-counts) | 58 |
| Games | **In short.** How many of the network's games carry the tag.<br>**Higher →** a more common characteristic among these games.<br>**Here:** the most direct answer to how often a characteristic recurs among the most-played games.<br>**Caution:** generic tags are common in any group of games; the share ratio in the feature analysis compares with the Eligible Pool.<br>*Column: n_games (nodes.csv)* | [Tag game count](../../../docs/user-guide/03-metric-reference.md#tag-game-count) | 51 |
| Total shared games | **In short.** The sum of a tag's links, in shared games or in lift, over all its links or those inside its cluster.<br>**Higher →** more, or heavier, links to other tags.<br>**Here:** how much of the network's weight a characteristic carries on the Clustering Weight in use.<br>**Caution:** on shared games it largely restates how common the tag is; on lift, rare tags inflate it.<br>*Column: strength_shared (nodes.csv)* | [Strength (weighted degree)](../../../docs/user-guide/03-metric-reference.md#strength-weighted-degree) | 60 |
| Total lift | *Same In short as Total shared games (Inspector).*<br>*Column: strength_lift (nodes.csv)* | [Strength (weighted degree)](../../../docs/user-guide/03-metric-reference.md#strength-weighted-degree) | 60 |
| Shared games in own cluster | *Same In short as Total shared games (Inspector).*<br>*Column: strength_shared_intra (nodes.csv)* | [Strength (weighted degree)](../../../docs/user-guide/03-metric-reference.md#strength-weighted-degree) | 60 |
| Lift in own cluster | *Same In short as Total shared games (Inspector).*<br>*Column: strength_lift_intra (nodes.csv)* | [Strength (weighted degree)](../../../docs/user-guide/03-metric-reference.md#strength-weighted-degree) | 60 |
| Links · in own cluster | **In short.** How many other tags this tag is linked to, in the whole network and inside its own cluster.<br>**Higher →** linked to more tags; 0 = isolated, shown as a One-Tag Cluster.<br>**Here:** shows how widely a characteristic combines with others among the most-played games.<br>**Caution:** mostly follows how common the tag is, and depends directly on the minimum shared games.<br>*Columns: degree, degree_intra (nodes.csv)* | [Degree and isolated tags](../../../docs/user-guide/03-metric-reference.md#degree-and-isolated-tags) | 57 |
| Membership Stability | **In short.** How much of the tag's cluster, on average, stays the same when the clustering is repeated with other seeds.<br>**Higher →** 1: always with the same tags; lower: its companions change between seeds.<br>**Here:** shows which tags keep their cluster before it is described as a recurring combination.<br>**Caution:** small clusters lose more per moved tag; descriptive only.<br>*Column: membership_stability (nodes.csv)* | [Membership Stability](../../../docs/user-guide/03-metric-reference.md#membership-stability) | 54 |
| Prominence in own cluster (z) | **In short.** How far the tag's link weight inside its cluster lies from the members' average, in standard deviations.<br>**Higher →** above 0: more than the average member; below 0: less.<br>**Here:** shows which members carry most of a cluster's links.<br>**Caution:** cannot exceed √(n − 1) in a cluster of n tags; not comparable across cluster sizes.<br>*Column: within_z (nodes.csv)* | [Within-cluster strength z-score](../../../docs/user-guide/03-metric-reference.md#within-cluster-strength-z-score) | 52 |
| Spread across clusters | **In short.** How evenly a tag's links are spread over the clusters.<br>**Higher →** links spread over several clusters; 0 = all its links in a single cluster, normally its own.<br>**Here:** finds characteristics that the most-played games combine with several different groups of tags.<br>**Caution:** generic tags score high on shared games; the maximum depends on the number of clusters.<br>*Column: participation (nodes.csv)* | [Participation coefficient](../../../docs/user-guide/03-metric-reference.md#participation-coefficient) | 55 |
| Fit to own cluster (silhouette) | **In short.** Whether the tag's games overlap more with its own cluster than with the nearest other cluster.<br>**Higher →** near 1: clearly closer to its own cluster; 0: in between; below 0: closer to another cluster.<br>**Here:** checks each member against the games themselves, not the link weights.<br>**Caution:** the clustering does not optimise it; rare tags never sit close to common ones.<br>*Column: silhouette (nodes.csv)* | [Per-tag silhouette](../../../docs/user-guide/03-metric-reference.md#per-tag-silhouette) | 58 |
| Mean game-set distance to members | **In short.** How different the tag's games are, on average, from the games of the other members of its cluster.<br>**Lower →** more typical of its cluster; the lowest is the Cluster Center.<br>**Here:** orders a cluster's members from most to least typical of the games behind it.<br>**Caution:** changes whenever the membership changes; in a two-tag cluster both members score the same.<br>*Column: medoid_score (nodes.csv)* | [Medoid score](../../../docs/user-guide/03-metric-reference.md#medoid-score) | 57 |
| Cluster Center | **In short.** The most typical tag of a Multi-Tag Cluster of three or more tags: the member with the lowest mean game-set distance to the other members (the medoid).<br>**Here:** gives one tag to orient by when reading a cluster of the most-played games.<br>**Caution:** not a cluster name and not the most common tag; near-tied scores can swap it.<br>*Columns: is_center (nodes.csv); center (clusters.csv)* | [Cluster Center](../../../docs/user-guide/03-metric-reference.md#cluster-center) | 56 |
| Shared games | **In short.** How many games carry both tags.<br>**Higher →** the two tags appear together on more of the games; a link exists only from the minimum shared games up.<br>**Here:** the plain count behind every link: which characteristics the most-played games carry together.<br>**Caution:** common tags share many games just by being common; read it with Lift.<br>*Column: shared_games (edges.csv)* | [Edge weight (shared games)](../../../docs/user-guide/03-metric-reference.md#edge-weight-shared-games) | 52 |
| Lift | **In short.** Shared games divided by the number expected if the two tags were independent.<br>**Higher →** above 1: together more often than chance; 1: as chance predicts; below 1: less often.<br>**Here:** shows pairings these games carry more often than the two tags' frequencies predict.<br>**Caution:** pairs of rare tags reach high values from a few games; association within these games, not a test.<br>*Column: lift (edges.csv)* | [Edge lift](../../../docs/user-guide/03-metric-reference.md#edge-lift) | 59 |
| Center's game-set distance | *Same In short as Cluster Center (Inspector).*<br>*Column: center_medoid_score (clusters.csv)* | [Cluster Center](../../../docs/user-guide/03-metric-reference.md#cluster-center) | 56 |
| Most-linked member | **In short.** The member with the most link weight inside its cluster, shown beside the Cluster Center.<br>**Here:** shows whether a cluster's most typical tag is also its most linked one.<br>**Caution:** on shared games it is usually a common, generic tag.<br>*Column: top_strength_tag (clusters.csv)* | [Top-strength tag](../../../docs/user-guide/03-metric-reference.md#top-strength-tag) | 38 |
| Center is the most-linked member | *Same In short as Most-linked member (Inspector).*<br>*Column: center_is_top_strength (clusters.csv)* | [Top-strength tag](../../../docs/user-guide/03-metric-reference.md#top-strength-tag) | 38 |
| Mean Membership Stability | *Same In short as Membership Stability (Inspector).*<br>*Column: mean_membership_stability (clusters.csv)* | [Membership Stability](../../../docs/user-guide/03-metric-reference.md#membership-stability) | 54 |
| Boundary crossing (conductance) | **In short.** How much of a cluster's link weight crosses to tags outside it, as a share of its members' total strength (or the rest's, if smaller).<br>**Higher →** more of its weight crosses to other clusters; 0 = none.<br>**Here:** shows which clusters are separate groups and which overlap with the rest.<br>**Caution:** on shared games, clusters of common tags cross a lot.<br>*Column: conductance (clusters.csv)* | [Cut weight and conductance](../../../docs/user-guide/03-metric-reference.md#cut-weight-and-conductance) | 58 |
| Agreement after removal (ARI, reclustered) | **In short.** How similar the clusters are, over the remaining tags, after the tag is removed and the clustering rerun.<br>**Higher →** 1 = no tag moved; lower: the clusters reorganised without it.<br>**Here:** the main reading of Removal Sensitivity: does a cluster finding depend on this tag?<br>**Caution:** part of a low value can be seed-like noise; compare with the lowest seed ARI.<br>*Column: rc_ari (removal_sensitivity.csv)* | [Reclustered ARI](../../../docs/user-guide/03-metric-reference.md#reclustered-ari) | 58 |
| Beyond seed noise | **In short.** Whether removing the tag changed the clusters more than any of the K extra seeds did.<br>**Here:** narrows the Removal Sensitivity table to the tags to look at first.<br>**Caution:** a screening flag, not a test; if removals acted only like another seed, about n / (K + 1) would be flagged on average, and the actual count varies widely.<br>*Column: rc_ari_beyond_noise (removal_sensitivity.csv)* | [Beyond-noise flag](../../../docs/user-guide/03-metric-reference.md#beyond-noise-flag) | 58 |
| Change in Q (reclustered) | **In short.** How much Q changes when the tag is removed and the clustering is run again.<br>**Higher →** above 0: Q higher without the tag; below 0: lower.<br>**Here:** shows how much the clustering's overall score depends on one characteristic.<br>**Caution:** part of the change is mechanical, from losing the tag's links; compare with the seeds' SD of Q.<br>*Column: rc_delta_modularity (removal_sensitivity.csv)* | [Reclustered change in modularity](../../../docs/user-guide/03-metric-reference.md#reclustered-change-in-modularity) | 54 |
| Silhouette after removal (reclustered) | **In short.** The mean silhouette after the tag is removed and the clustering is run again, and its change.<br>**Higher →** a change above 0: the remaining tags separate more clearly on game overlap.<br>**Here:** shows whether a characteristic blurs or sharpens the groups on game overlap.<br>**Caution:** some change happens even when no tag moves; compare with the seeds' SD.<br>*Columns: rc_delta_silhouette, rc_silhouette_after (removal_sensitivity.csv)* | [Reclustered silhouette](../../../docs/user-guide/03-metric-reference.md#reclustered-silhouette) | 55 |
| Change in multi-tag · one-tag clusters | **In short.** How many multi-tag and one-tag clusters appear or disappear when the tag is removed and the clustering is run again.<br>**Higher →** above 0: more clusters without the tag; below 0: fewer.<br>**Here:** finds tags that join two groups into one or hold a group together.<br>**Caution:** often mechanical: removing one tag of a two-tag cluster leaves its partner alone.<br>*Columns: rc_delta_k, rc_delta_s (removal_sensitivity.csv)* | [Reclustered change in cluster counts](../../../docs/user-guide/03-metric-reference.md#reclustered-change-in-cluster-counts) | 56 |
| Cluster Centers lost | **In short.** Current Cluster Centers that are no longer centers after the tag is removed and the clustering is run again.<br>**Here:** shows whether the tags used to describe clusters depend on this tag.<br>**Caution:** a center is also lost when its cluster shrinks below three tags, and near-tied centers swap easily.<br>*Column: rc_centers_lost (removal_sensitivity.csv)* | [Centers lost](../../../docs/user-guide/03-metric-reference.md#centers-lost) | 48 |
| Change in Q (clusters kept) | **In short.** How Q changes when the tag is dropped but every other tag stays in its cluster.<br>**Higher →** above 0: Q higher without it; below 0: the tag added to Q.<br>**Here:** shows how much one characteristic contributes to the separation of the clusters as they are.<br>**Caution:** includes the mechanical loss of the tag's links; no noise flag.<br>*Column: fp_delta_modularity (removal_sensitivity.csv)* | [Fixed-partition change in modularity](../../../docs/user-guide/03-metric-reference.md#fixed-partition-change-in-modularity) | 55 |
| Silhouette after removal (clusters kept) | **In short.** The mean silhouette when the tag is dropped but every other tag stays in its cluster, and its change.<br>**Higher →** a change above 0: the remaining tags fit their unchanged clusters better on average.<br>**Here:** finds members whose games point away from their cluster.<br>**Caution:** includes changes to the other tags' distances; n/a when fewer than two multi-tag clusters remain.<br>*Columns: fp_delta_silhouette, fp_silhouette_after (removal_sensitivity.csv)* | [Fixed-partition silhouette](../../../docs/user-guide/03-metric-reference.md#fixed-partition-silhouette) | 57 |

## 4 Grid column headers (one row per entry and grid)

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| nin-grid: n_games | *Same In short as Games (Inspector).*<br>*Column: n_games (not_in_network.csv)* | [Tag game count](../../../docs/user-guide/03-metric-reference.md#tag-game-count) | 51 |
| nin-grid: reasons | **In short.** Every tag of the dataset that is not in the network, with each reason why.<br>**Here:** shows which characteristics of the most-played games the network leaves out, and why.<br>**Caution:** a tag below the minimum games here can be common in another dataset.<br>*Column: reasons (not_in_network.csv)* | [Tags not in the network](../../../docs/user-guide/03-metric-reference.md#tags-not-in-the-network) | 41 |
| connections-grid: edge_count, weight | **In short.** How many links, and how much link weight, join each pair of clusters.<br>**Higher →** more links, or more weight on the Clustering Weight in use, between the two clusters; 0 = none.<br>**Here:** shows which groups of characteristics the most-played games tend to combine with each other.<br>**Caution:** on shared games, big clusters of common tags connect to everything; compare with cluster sizes.<br>*Column: edge_count (cluster_connections.csv)* | [Cluster connections](../../../docs/user-guide/03-metric-reference.md#cluster-connections) | 60 |
| null-grid: modularity, n_edges | **In short.** The Q the same procedure reaches after shuffling which games carry which tags, keeping every tag's game count and every game's tag count.<br>**Higher →** the shuffled data already produce much of the clustering.<br>**Here:** separates how characteristics combine among the most-played games from some tags being everywhere.<br>**Caution:** the SD from 20 shuffles is rough; shuffled networks differ in link count.<br>*Column: modularity (null_model.csv)* | [Null-model baseline](../../../docs/user-guide/03-metric-reference.md#null-model-baseline) | 58 |
| seed-grid: modularity, silhouette, silhouette_status | **In short.** How much Q and the mean silhouette vary when only the random seed changes.<br>**Higher →** the seeds find splits that score more differently; 0 = all score the same.<br>**Here:** the scale of seed noise for reading changes in Q across this study's Network States.<br>**Caution:** an SD from K seeds is rough; Leiden often gives 0.<br>*Column: modularity (seed_noise.csv)* | [Seed spread of modularity and silhouette](../../../docs/user-guide/03-metric-reference.md#seed-spread-of-modularity-and-silhouette) | 54 |
| seed-grid: ari_vs_main | *Same In short as Seed noise (Cluster quality tab).*<br>*Column: ari_vs_main (seed_noise.csv)* | [Adjusted Rand index](../../../docs/user-guide/03-metric-reference.md#adjusted-rand-index) | 54 |
| seed-grid: n_multi_tag_clusters, n_one_tag_clusters | **In short.** The fewest and the most Multi-Tag Clusters found when only the random seed changes.<br>**Higher →** a wider range: the count depends more on the seed.<br>**Here:** check it before reporting how many groups the most-played games' characteristics form.<br>**Caution:** the count can stay the same while members move; read it with the ARI.<br>*Column: n_multi_tag_clusters (seed_noise.csv)* | [Seed range of cluster counts](../../../docs/user-guide/03-metric-reference.md#seed-range-of-cluster-counts) | 50 |
| clusters-grid: cluster, kind, size | *Same In short as Clusters (Summary row).*<br>*Column: cluster (clusters.csv)* | [Cluster labels and counts](../../../docs/user-guide/03-metric-reference.md#cluster-labels-and-counts) | 58 |
| clusters-grid: connected | **In short.** Whether all of a cluster's tags are joined by links inside the cluster.<br>**Here:** keeps two separate groups of characteristics from being read as one cluster.<br>**Caution:** a known defect of Louvain, not a finding; Leiden never produces it.<br>*Column: connected (clusters.csv)* | [Disconnected clusters](../../../docs/user-guide/03-metric-reference.md#disconnected-clusters) | 37 |
| clusters-grid: internal_edges, internal_weight, edge_density, weighted_density | **In short.** How tightly a cluster's tags are linked among themselves: links and link weight, also per possible pair.<br>**Higher →** more of the members' pairs linked, or more heavily; edge density 1 = every pair linked.<br>**Here:** whether a cluster's characteristics occur together pairwise or through a few common tags.<br>**Caution:** small clusters reach high density easily; weighted density is in Clustering Weight units.<br>*Column: internal_edges (clusters.csv)* | [Internal edges, weight and densities](../../../docs/user-guide/03-metric-reference.md#internal-edges-weight-and-densities) | 59 |
| clusters-grid: cut_weight, conductance, conductance_status | *Same In short as Boundary crossing (conductance) (Inspector).*<br>*Column: cut_weight (clusters.csv)* | [Cut weight and conductance](../../../docs/user-guide/03-metric-reference.md#cut-weight-and-conductance) | 58 |
| clusters-grid: mean_silhouette, silhouette_status | *Same In short as Silhouette (Summary row).*<br>*Column: mean_silhouette (clusters.csv)* | [Mean silhouette](../../../docs/user-guide/03-metric-reference.md#mean-silhouette) | 59 |
| clusters-grid: center, center_medoid_score, center_status | *Same In short as Cluster Center (Inspector).*<br>*Column: center (clusters.csv)* | [Cluster Center](../../../docs/user-guide/03-metric-reference.md#cluster-center) | 56 |
| clusters-grid: top_strength_tag, center_is_top_strength | *Same In short as Most-linked member (Inspector).*<br>*Column: top_strength_tag (clusters.csv)* | [Top-strength tag](../../../docs/user-guide/03-metric-reference.md#top-strength-tag) | 38 |
| clusters-grid: mean_membership_stability | *Same In short as Membership Stability (Inspector).*<br>*Column: mean_membership_stability (clusters.csv)* | [Membership Stability](../../../docs/user-guide/03-metric-reference.md#membership-stability) | 54 |
| rs-grid: run_order, active_strength | **In short.** The order in which Removal Sensitivity tests the tags: by active strength (link weight on the Clustering Weight), highest first.<br>**Here:** a partial run has covered the most linked of the most-played games' tags.<br>**Caution:** an order for running the tests, not a ranking of importance.<br>*Column: run_order (removal_sensitivity.csv)* | [Run order and identity](../../../docs/user-guide/03-metric-reference.md#run-order-and-identity) | 44 |
| rs-grid: cluster | *Same In short as Clusters (Summary row).*<br>*Column: cluster (removal_sensitivity.csv)* | [Cluster labels and counts](../../../docs/user-guide/03-metric-reference.md#cluster-labels-and-counts) | 58 |
| rs-grid: is_center | *Same In short as Cluster Center (Inspector).*<br>*Column: is_center (removal_sensitivity.csv)* | [Cluster Center](../../../docs/user-guide/03-metric-reference.md#cluster-center) | 56 |
| rs-grid: rc_delta_modularity | *Same In short as Change in Q (reclustered) (Inspector).*<br>*Column: rc_delta_modularity (removal_sensitivity.csv)* | [Reclustered change in modularity](../../../docs/user-guide/03-metric-reference.md#reclustered-change-in-modularity) | 54 |
| rs-grid: rc_silhouette_after, rc_silhouette_after_status, rc_delta_silhouette | *Same In short as Silhouette after removal (reclustered) (Inspector).*<br>*Column: rc_silhouette_after (removal_sensitivity.csv)* | [Reclustered silhouette](../../../docs/user-guide/03-metric-reference.md#reclustered-silhouette) | 55 |
| rs-grid: rc_delta_k, rc_delta_s | *Same In short as Change in multi-tag · one-tag clusters (Inspector).*<br>*Column: rc_delta_k (removal_sensitivity.csv)* | [Reclustered change in cluster counts](../../../docs/user-guide/03-metric-reference.md#reclustered-change-in-cluster-counts) | 56 |
| rs-grid: rc_ari | *Same In short as Agreement after removal (ARI, reclustered) (Inspector).*<br>*Column: rc_ari (removal_sensitivity.csv)* | [Reclustered ARI](../../../docs/user-guide/03-metric-reference.md#reclustered-ari) | 58 |
| rs-grid: rc_centers_lost | *Same In short as Cluster Centers lost (Inspector).*<br>*Column: rc_centers_lost (removal_sensitivity.csv)* | [Centers lost](../../../docs/user-guide/03-metric-reference.md#centers-lost) | 48 |
| rs-grid: rc_ari_beyond_noise | *Same In short as Beyond seed noise (Inspector).*<br>*Column: rc_ari_beyond_noise (removal_sensitivity.csv)* | [Beyond-noise flag](../../../docs/user-guide/03-metric-reference.md#beyond-noise-flag) | 58 |
| rs-grid: fp_delta_modularity | *Same In short as Change in Q (clusters kept) (Inspector).*<br>*Column: fp_delta_modularity (removal_sensitivity.csv)* | [Fixed-partition change in modularity](../../../docs/user-guide/03-metric-reference.md#fixed-partition-change-in-modularity) | 55 |
| rs-grid: fp_silhouette_after, fp_silhouette_after_status, fp_delta_silhouette | *Same In short as Silhouette after removal (clusters kept) (Inspector).*<br>*Column: fp_silhouette_after (removal_sensitivity.csv)* | [Fixed-partition silhouette](../../../docs/user-guide/03-metric-reference.md#fixed-partition-silhouette) | 57 |
| rs-grid: membership_stability (joined) | *Same In short as Membership Stability (Inspector).*<br>*Column: membership_stability (nodes.csv)* | [Membership Stability](../../../docs/user-guide/03-metric-reference.md#membership-stability) | 54 |
| nodes-grid: cluster | *Same In short as Clusters (Summary row).*<br>*Column: cluster (nodes.csv)* | [Cluster labels and counts](../../../docs/user-guide/03-metric-reference.md#cluster-labels-and-counts) | 58 |
| nodes-grid: n_games | *Same In short as Games (Inspector).*<br>*Column: n_games (nodes.csv)* | [Tag game count](../../../docs/user-guide/03-metric-reference.md#tag-game-count) | 51 |
| nodes-grid: is_isolated, degree, degree_intra | *Same In short as Links · in own cluster (Inspector).*<br>*Column: is_isolated (nodes.csv)* | [Degree and isolated tags](../../../docs/user-guide/03-metric-reference.md#degree-and-isolated-tags) | 57 |
| nodes-grid: strength_shared, strength_lift, strength_shared_intra, strength_lift_intra | *Same In short as Total shared games (Inspector).*<br>*Column: strength_shared (nodes.csv)* | [Strength (weighted degree)](../../../docs/user-guide/03-metric-reference.md#strength-weighted-degree) | 60 |
| nodes-grid: silhouette, silhouette_status | *Same In short as Fit to own cluster (silhouette) (Inspector).*<br>*Column: silhouette (nodes.csv)* | [Per-tag silhouette](../../../docs/user-guide/03-metric-reference.md#per-tag-silhouette) | 58 |
| nodes-grid: medoid_score | *Same In short as Mean game-set distance to members (Inspector).*<br>*Column: medoid_score (nodes.csv)* | [Medoid score](../../../docs/user-guide/03-metric-reference.md#medoid-score) | 57 |
| nodes-grid: is_center | *Same In short as Cluster Center (Inspector).*<br>*Column: is_center (nodes.csv)* | [Cluster Center](../../../docs/user-guide/03-metric-reference.md#cluster-center) | 56 |
| nodes-grid: within_z | *Same In short as Prominence in own cluster (z) (Inspector).*<br>*Column: within_z (nodes.csv)* | [Within-cluster strength z-score](../../../docs/user-guide/03-metric-reference.md#within-cluster-strength-z-score) | 52 |
| nodes-grid: participation | *Same In short as Spread across clusters (Inspector).*<br>*Column: participation (nodes.csv)* | [Participation coefficient](../../../docs/user-guide/03-metric-reference.md#participation-coefficient) | 55 |
| nodes-grid: membership_stability | *Same In short as Membership Stability (Inspector).*<br>*Column: membership_stability (nodes.csv)* | [Membership Stability](../../../docs/user-guide/03-metric-reference.md#membership-stability) | 54 |
| nodes-grid: x_global, y_global, x_cluster_separated, y_cluster_separated | **In short.** Where each tag is drawn; computed after, and never used by, any metric.<br>**Here:** a map for finding the most-played games' characteristics and their clusters.<br>**Caution:** distance on screen is not a metric; never measure or report positions.<br>*Column: x_global (nodes.csv)* | [Layout positions](../../../docs/user-guide/03-metric-reference.md#layout-positions) | 36 |
| edges-grid: shared_games | *Same In short as Shared games (Inspector).*<br>*Column: shared_games (edges.csv)* | [Edge weight (shared games)](../../../docs/user-guide/03-metric-reference.md#edge-weight-shared-games) | 52 |
| edges-grid: lift | *Same In short as Lift (Inspector).*<br>*Column: lift (edges.csv)* | [Edge lift](../../../docs/user-guide/03-metric-reference.md#edge-lift) | 59 |

## 5 Analytical controls (Controls panel, pill bar, graph overlay)

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| Minimum Months Filter | **In short.** Leaves out games with fewer Months Observed than this before the network is built.<br>**Raising it →** fewer games (a smaller N), each with a longer player record; 0 = every game.<br>**Here:** checks whether the clusters hold among the games tracked longest, not only among recent releases.<br>**Caution:** it never re-ranks or adds games: N shrinks, so lift and some counts change. | [Minimum Months Filter](../../../docs/user-guide/02-app-controls.md#minimum-months-filter) | 58 |
| Clustering weight | **In short.** What the clustering runs on: each link's shared-games count, or its lift.<br>**Here:** shared games groups what the most-played games most often carry together; lift, what they combine more often than tag frequencies predict.<br>**Caution:** the two answer different questions; Q and every weighted number differ between them. | [Clustering weight](../../../docs/user-guide/02-app-controls.md#clustering-weight) | 46 |
| Clustering algorithm | **In short.** The method that searches for the clusters: Louvain or Leiden, both seeking high modularity (neither guarantees the best).<br>**Here:** running the second method on the same network shows whether the clusters depend on the method.<br>**Caution:** Louvain can return a cluster in disconnected pieces; Leiden never does. | [Clustering algorithm](../../../docs/user-guide/02-app-controls.md#clustering-algorithm) | 45 |
| Resolution γ | **In short.** Sets the scale of the clusters: the resolution in the modularity that the clustering seeks to maximise.<br>**Raising it →** tends to give more, smaller clusters; lowering it, fewer and larger ones.<br>**Here:** shows whether the groups of characteristics hold at a finer or a coarser scale.<br>**Caution:** Q at different γ is not comparable; compare the clusters instead. | [Resolution γ](../../../docs/user-guide/02-app-controls.md#resolution-γ) | 54 |
| Seed | **In short.** The random seed of the clustering; the null-model and noise seeds are derived from it.<br>**Here:** lets a reported cluster of the most-played games' tags be reproduced exactly.<br>**Caution:** never choose a seed for the clusters it gives; the Seed-Noise Floor already compares other seeds. | [Seed](../../../docs/user-guide/02-app-controls.md#seed) | 43 |
| Months ≥ 0 (pill) | *Same In short as Minimum Months Filter (Analytical controls).* | [Minimum Months Filter](../../../docs/user-guide/02-app-controls.md#minimum-months-filter); a click opens the pill's popover | 58 |
| Weight Shared games (pill) | *Same In short as Clustering weight (Analytical controls).* | [Clustering weight](../../../docs/user-guide/02-app-controls.md#clustering-weight); a click opens the pill's popover | 46 |
| Louvain (pill) | *Same In short as Clustering algorithm (Analytical controls).* | [Clustering algorithm](../../../docs/user-guide/02-app-controls.md#clustering-algorithm); a click opens the pill's popover | 45 |
| γ 1.00 (pill) | *Same In short as Resolution γ (Analytical controls).* | [Resolution γ](../../../docs/user-guide/02-app-controls.md#resolution-γ); a click opens the pill's popover | 54 |
| Seed 20261003 (pill) | *Same In short as Seed (Analytical controls).* | [Seed](../../../docs/user-guide/02-app-controls.md#seed); a click opens the pill's popover | 43 |

## 6 Legend

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| Key | **In short.** What the drawing shows: node size = games, link thickness = shared games, colour = Multi-Tag Cluster, grey = One-Tag Cluster.<br>**Here:** lets the tag network of the most-played games be read at a glance, before the numbers.<br>**Caution:** positions and distances on screen are not metrics. | [Reading the graph](../../../docs/user-guide/02-app-controls.md#reading-the-graph) | 45 |
| 4 one-tag | **In short.** Grey nodes are One-Tag Clusters: tags left on their own, usually because no link reaches them.<br>**Here:** shows characteristics that recur among the most-played games without sharing enough games to join a Multi-Tag Cluster.<br>**Caution:** a One-Tag Cluster is usually an isolated tag, not a finding. | [Grey One-Tag Clusters](../../../docs/user-guide/02-app-controls.md#grey-one-tag-clusters) | 44 |

## 7 Dataset summary (Analysis Report §1) and Export

- [ ] Approved

| Element | Tooltip (layer 1) | Entry (layer 2) | Words |
|---|---|---|---|
| Games after the Minimum Months Filter | *Same In short as Games (Summary row).* | [Network size](../../../docs/user-guide/03-metric-reference.md#network-size) | 60 |
| Minimum Months Filter | *Same In short as Minimum Months Filter (Analytical controls).*<br>*Field: min_months* | [Minimum Months Filter](../../../docs/user-guide/02-app-controls.md#minimum-months-filter) | 58 |
| Clustering Weight | *Same In short as Clustering weight (Analytical controls).*<br>*Field: clustering_weight* | [Clustering weight](../../../docs/user-guide/02-app-controls.md#clustering-weight) | 46 |
| Algorithm | *Same In short as Clustering algorithm (Analytical controls).*<br>*Field: algorithm* | [Clustering algorithm](../../../docs/user-guide/02-app-controls.md#clustering-algorithm) | 45 |
| Resolution γ | *Same In short as Resolution γ (Analytical controls).*<br>*Field: resolution* | [Resolution γ](../../../docs/user-guide/02-app-controls.md#resolution-γ) | 54 |
| Seed | *Same In short as Seed (Analytical controls).*<br>*Field: seed* | [Seed](../../../docs/user-guide/02-app-controls.md#seed) | 43 |
| Null-model replicates R | *Same In short as null-grid: modularity, n_edges (Grid column headers).*<br>*Field: null_replicates* | [Null-model baseline](../../../docs/user-guide/03-metric-reference.md#null-model-baseline) | 58 |
| Noise seeds K | *Same In short as Seed-noise floor (K = 10): ARI vs. main min 0… (Cluster quality tab).*<br>*Field: noise_seeds* | [Stability](../../../docs/user-guide/03-metric-reference.md#stability) | 41 |
| Export | **In short.** Export this state downloads one zip with every table, the full Network State key and its provenance.<br>**Here:** lets readers of a study of the most-played games reopen and check the exact clusters it reports.<br>**Caution:** Removal Sensitivity results are included only if they were computed for exactly this Network State. | [Deposit the export zip](../../../docs/user-guide/05-citing-and-reproducing.md#deposit-the-export-zip) | 49 |

## Appendix: *Why it matters here.* of every linked entry

### Clustering algorithm

[Clustering algorithm](../../../docs/user-guide/02-app-controls.md#clustering-algorithm) · In short 45 words

A group of characteristics that both methods find is less likely to be an artefact of one search procedure. Since both seek high values of the same Q, their Q can be compared directly at the same γ and Clustering Weight.

### Clustering weight

[Clustering weight](../../../docs/user-guide/02-app-controls.md#clustering-weight) · In short 46 words

Shared games describes the most-played games as they are: which characteristics they carry together most often. Lift asks what they combine beyond popularity. Comparing the two weights shows which clusters reflect frequent tags and which reflect characteristics that go together.

### Grey One-Tag Clusters

[Grey One-Tag Clusters](../../../docs/user-guide/02-app-controls.md#grey-one-tag-clusters) · In short 44 words

A grey tag is in the network but in no group. Lowering the minimum shared games often lets it join a cluster, which shows which group of characteristics it is closest to.

### Minimum Months Filter

[Minimum Months Filter](../../../docs/user-guide/02-app-controls.md#minimum-months-filter) · In short 58 words

The study asks which characteristics recur among the most-played commercial games. A cluster that appears only while recent releases are included may reflect a few new games rather than a combination that holds over a longer player record; one that stays when the filter is raised rests on games with a long player record.

### Reading the graph

[Reading the graph](../../../docs/user-guide/02-app-controls.md#reading-the-graph) · In short 45 words

The drawing is the quickest way to see which characteristics the most-played games carry together and how the clusters touch. Knowing what each visual property encodes keeps it from being read as more than it is: a big node is a common tag, not a central one, and two tags drawn side by side may share few games.

### Resolution γ

[Resolution γ](../../../docs/user-guide/02-app-controls.md#resolution-γ) · In short 54 words

There is no single right size for a group of characteristics. A cluster that stays together from γ 0.75 to 1.25 is a combination the most-played games show at several scales; one that appears only at one γ depends on that choice. The Build's Resolution Sweep does this systematically for the report's settings.

### Seed

[Seed](../../../docs/user-guide/02-app-controls.md#seed) · In short 43 words

Results are only citable if they can be reproduced, and the seed is part of the `state_id`. Trying another seed is also the most direct way to see how much a cluster depends on chance, which the Seed-Noise Floor measures for K seeds at once.

### Adjusted Rand index

[Adjusted Rand index](../../../docs/user-guide/03-metric-reference.md#adjusted-rand-index) · In short 54 words

Before a cluster is described as a recurring combination of characteristics, it should be clear that it is not an accident of the random seed. If the lowest ARI is close to 1, every tested seed finds nearly the same clusters; if it is much lower, some clusters depend on the seed, and Membership Stability shows which tags move. The minimum is also the yardstick for Removal Sensitivity: a removal is flagged as beyond seed noise only when its ARI falls below it.

### Beyond-noise flag

[Beyond-noise flag](../../../docs/user-guide/03-metric-reference.md#beyond-noise-flag) · In short 58 words

With dozens of tags tested, some flags are expected by chance, and the footer under the table gives that expected count. A flagged tag is one whose absence reorganises the clusters more than any of the K seeds did, so descriptions of its clusters should be checked without it. Unflagged tags can still change Q or the silhouette, which carry no flag.

### Centers lost

[Centers lost](../../../docs/user-guide/03-metric-reference.md#centers-lost) · In short 48 words

Clusters are described through their Cluster Centers, so a removal that changes them changes how the clusters would be described. If many centers are lost, describe the clusters through several members rather than one center. "none" means every other center stayed.

### Cluster Center

[Cluster Center](../../../docs/user-guide/03-metric-reference.md#cluster-center) · In short 56 words

A cluster of twelve tags is hard to hold in mind; the Cluster Center, drawn as ◆, gives a concrete starting point. It is chosen by game overlap rather than by links, so it tends to be a characteristic typical of the cluster's games rather than a generic tag linked to everything; the most-linked member shows that alternative. Write "the cluster around X" at most, never use the center as the cluster's name, and check its Membership Stability before building on it.

### Cluster connections

[Cluster connections](../../../docs/user-guide/03-metric-reference.md#cluster-connections) · In short 60 words

Clusters are not sealed off from each other: a game often carries tags from several of them. A heavy connection between two clusters means many games combine the two groups of characteristics, so describe them as overlapping rather than as separate kinds of game. The `one_tag_pool` rows show how much the pooled One-Tag Clusters link to each cluster.

### Cluster labels and counts

[Cluster labels and counts](../../../docs/user-guide/03-metric-reference.md#cluster-labels-and-counts) · In short 58 words

A Multi-Tag Cluster is the study's unit of "a recurring combination of characteristics": tags that the most-played games of the dataset tend to carry together in pairs: A, B and C can form a cluster even if no game carries all three. Read a cluster through its members and its Cluster Center, not through its label: `C1` only means "largest in this Network State", and the same group of tags can be `C2` after a small change. Before treating a cluster as a finding, check that it survives other seeds (Membership Stability, the Seed-Noise Floor) and other γ values (the Resolution Sweep).

### Clusters and partition quality

[Clusters and partition quality](../../../docs/user-guide/03-metric-reference.md#clusters-and-partition-quality) · In short 51 words

These numbers describe the clustering as a whole, before any single cluster is read. Q says how separated the clusters are, the null-model excess how far it exceeds the shuffled baseline, coverage how much link weight the clusters hold, and the silhouette whether the games themselves agree. If the excess is near 0, the clusters say more about which tags are common among the most-played games than about how those games combine characteristics.

### Coverage and inter-cluster weight share

[Coverage and inter-cluster weight share](../../../docs/user-guide/03-metric-reference.md#coverage-and-inter-cluster-weight-share) · In short 49 words

Coverage says how much of the co-occurrence among the most-played games' tags the clusters capture; the rest is weight between clusters. Unlike Q, it does not correct for what any split would capture, so compare it only between Network States with similar cluster counts, and read Q and its excess over the null model first.

### Cut weight and conductance

[Cut weight and conductance](../../../docs/user-guide/03-metric-reference.md#cut-weight-and-conductance) · In short 58 words

A cluster with low conductance is a set of characteristics that the most-played games mostly carry among themselves; a cluster with high conductance shares many games with other clusters, so its boundary is a matter of degree. Compare clusters of the same Network State. A tag left on its own but linked elsewhere has conductance 1.

### Degree and isolated tags

[Degree and isolated tags](../../../docs/user-guide/03-metric-reference.md#degree-and-isolated-tags) · In short 57 words

A tag linked to most others is usually a generic characteristic, such as Singleplayer, that appears with almost anything; a tag with few links combines with a narrow set of other characteristics. The second number shows how many of those links stay inside the tag's cluster. Degree counts links, not games: for how many games stand behind the links, read the strength.

### Disconnected clusters

[Disconnected clusters](../../../docs/user-guide/03-metric-reference.md#disconnected-clusters) · In short 37 words

A disconnected cluster would be described as one combination of characteristics when it is really two groups that happen to share a label. The Inspector warns about it and suggests the Leiden mode; switch to Leiden before describing such a cluster.

### Edge lift

[Edge lift](../../../docs/user-guide/03-metric-reference.md#edge-lift) · In short 59 words

Two tags can share many games simply because both are on most of the Top 100. Lift divides that out: a lift of 2.0 means the pair occurs twice as often as the two tags' frequencies predict if they were unrelated. That makes it the closer reading of "which characteristics do the most-played games combine?" beyond popularity. Read it beside the shared-games count: a lift of 3 from 4 games rests on far fewer games than a lift of 1.5 from 30.

### Edge weight (shared games)

[Edge weight (shared games)](../../../docs/user-guide/03-metric-reference.md#edge-weight-shared-games) · In short 52 words

Shared games is the closest the network comes to the raw data: 12 shared games means that 12 of the network's games carry both tags, and the edge inspector lists them. It answers which characteristics the most-played games actually combine, counted in games. Because a tag on most of the Top 100 shares many games with almost every other tag, a large count alone does not show that two tags belong together; the edge's lift corrects for that.

### Excess modularity and z-score

[Excess modularity and z-score](../../../docs/user-guide/03-metric-reference.md#excess-modularity-and-z-score) · In short 60 words

The excess is the most direct answer to "do the most-played games combine characteristics in recognisable groups, beyond popular tags being everywhere?". An excess near 0 means shuffled data with the same tag and game counts give as much modularity, so the clusters could come from those counts alone; a clearly positive excess means the grouping goes beyond them. It still says nothing about which cluster is meaningful: for that, read the clusters themselves and their stability.

### Fixed-partition change in modularity

[Fixed-partition change in modularity](../../../docs/user-guide/03-metric-reference.md#fixed-partition-change-in-modularity) · In short 55 words

This reading keeps the clusters exactly as shown, so it has no reclustering noise; it still includes the loss of the tag's links. A clearly negative value suggests a tag whose links hold its cluster together; a positive value, one that sits loosely in its cluster. Compare with the reclustered change to see whether the clustering would also reorganise.

### Fixed-partition silhouette

[Fixed-partition silhouette](../../../docs/user-guide/03-metric-reference.md#fixed-partition-silhouette) · In short 57 words

A clearly positive change suggests the tag fitted its cluster poorly on game overlap, but the change also includes the other tags' distances shifting without its games. Its per-tag silhouette shows its own fit directly; a negative one means its games overlap more with another cluster.

### Internal edges, weight and densities

[Internal edges, weight and densities](../../../docs/user-guide/03-metric-reference.md#internal-edges-weight-and-densities) · In short 59 words

An edge density near 1 means almost every pair of the cluster's tags shares at least the minimum shared games: the most-played games carry these characteristics together pair by pair. A low density means the cluster hangs together through a few members that link to the rest. Compare clusters of similar size, and read it with the conductance, which says how much the cluster links outward.

### Layout positions

[Layout positions](../../../docs/user-guide/03-metric-reference.md#layout-positions) · In short 36 words

The drawing helps to find tags and to see the clusters, but two tags drawn close together may share few games, and the picture changes with gravity, open panels and Tidy. Read how tags relate from the links, the Inspector and the tables, never from where they sit in the drawing.

### Mean silhouette

[Mean silhouette](../../../docs/user-guide/03-metric-reference.md#mean-silhouette) · In short 59 words

Clusters are found from link weights; the silhouette asks a different question of the same result: do the games that carry a cluster's tags really overlap more with each other than with the games of the next cluster? A value near 0 is common here, because Jaccard distances between tags are mostly near 1 and many of the most-played games carry tags from several clusters at once (an open-world RPG with crafting and survival tags, for example). Use it to compare clusters with each other or one Network State with a close variant, not as a pass mark.

### Medoid score

[Medoid score](../../../docs/user-guide/03-metric-reference.md#medoid-score) · In short 57 words

A cluster's Members list is sorted by this score, so its first tags are the ones whose games overlap most with the rest. When describing a cluster in words, start from those tags; tags at the end of the list are on games that the other members rarely share. The score uses game overlap only: the Clustering Weight changes it only by changing the clusters.

### Membership Stability

[Membership Stability](../../../docs/user-guide/03-metric-reference.md#membership-stability) · In short 54 words

The clustering is a randomised search, so another seed can place some tags differently. A tag near 1 sits with the same companions across the tested seeds, and a cluster's mean shows how much of the whole group holds together. Tags with low values are the ones to leave out, or mention with care, when describing a cluster in a write-up. The Seed-Noise Floor gives the same picture for the whole partition at once.

### Modularity Q

[Modularity Q](../../../docs/user-guide/03-metric-reference.md#modularity-q) · In short 60 words

Q says how clearly the tags of the most-played games fall into separate groups, but on its own it cannot tell combinations of characteristics from the grouping that tag popularity alone would produce. That is why the app always shows it with its excess over the null model: "Q 0.42 · excess +0.11" means the shuffled networks reach about 0.31 on average and the observed network 0.11 more. Use Q to compare Network States that differ only in the seed or the algorithm, never across datasets.

### Network size

[Network size](../../../docs/user-guide/03-metric-reference.md#network-size) · In short 60 words

Every pattern the network shows is a pattern among these N games and these tags only. "100 of 100" games means the whole Top-100 Dataset is in the network; a lower N (from the Minimum Months Filter) means the clusters describe only the games tracked long enough. Tags below the minimum games per tag are left out entirely, so a characteristic shared by only a handful of the most-played games cannot appear in any cluster; the Not in network table lists them.

### Null-model baseline

[Null-model baseline](../../../docs/user-guide/03-metric-reference.md#null-model-baseline) · In short 58 words

Tags such as Singleplayer or Indie appear on a large share of the games, so they share many games with almost every other tag, and that alone creates groups. The null model keeps every tag exactly as common as it is and every game with as many tags as it has, but pairs them at random. The Q the shuffled networks reach is what those counts alone can produce; only Q clearly above it suggests the most-played games combine characteristics in ways the counts do not.

### Participation coefficient

[Participation coefficient](../../../docs/user-guide/03-metric-reference.md#participation-coefficient) · In short 55 words

A tag with a high value sits between clusters: games carry it together with tags from several groups. That can mark a cross-cutting characteristic (a multiplayer tag, for example, can go with many kinds of game) or simply a very common tag. A tag near 0 belongs to one group. Compare values within one Network State only.

### Per-tag silhouette

[Per-tag silhouette](../../../docs/user-guide/03-metric-reference.md#per-tag-silhouette) · In short 58 words

A member with a negative value shares more games with another cluster's tags than with its own: its links placed it, but its games point elsewhere. Such tags are where a cluster's boundary is least clear, and they are the first to check before describing a cluster as a recurring combination of characteristics. Compare the members of one cluster with each other rather than across clusters.

### Reclustered ARI

[Reclustered ARI](../../../docs/user-guide/03-metric-reference.md#reclustered-ari) · In short 58 words

If removing a single tag reorganises the clusters, a description of those clusters rests on that one characteristic, and should say so. The Removal sensitivity table sorts by this value, lowest first, and the Beyond seed noise flag marks values below the Seed-Noise Floor. A value above the floor is within the range the K seeds gave; that does not show the removal had no effect.

### Reclustered change in cluster counts

[Reclustered change in cluster counts](../../../docs/user-guide/03-metric-reference.md#reclustered-change-in-cluster-counts) · In short 56 words

A tag whose removal adds a Multi-Tag Cluster may have been linking two groups, and one whose removal removes one may have been separating them. The change can also come from the whole network shifting, because removing a tag changes every expected weight; look at the new clusters (Remove) before describing it. Compare with the seed range of cluster counts, because other seeds alone can change the count.

### Reclustered change in modularity

[Reclustered change in modularity](../../../docs/user-guide/03-metric-reference.md#reclustered-change-in-modularity) · In short 54 words

Removal Sensitivity asks whether a cluster finding hangs on a single tag. A change in Q within the spread across seeds (`seed_modularity_sd`) is no more than another run of the clustering gives. A larger change can come from the clusters reorganising without the tag or simply from losing its links; the fixed-partition change, which keeps the clusters, helps tell the two apart. It never says that the characteristic matters for how many people play a game.

### Reclustered silhouette

[Reclustered silhouette](../../../docs/user-guide/03-metric-reference.md#reclustered-silhouette) · In short 55 words

A positive change means the remaining tags, reclustered, separate more clearly on the games they share; a negative change, less clearly. Part of any change comes from the removed tag leaving: its own value leaves the mean and the other tags' distances to its cluster change, even if no tag moves. Read it against `seed_silhouette_sd`: small changes are within what another seed gives.

### Run order and identity

[Run order and identity](../../../docs/user-guide/03-metric-reference.md#run-order-and-identity) · In short 44 words

Testing every tag takes time, so the run starts with the tags that carry the most link weight. If you stop early, the rows you have are for those tags; the others are untested, not unaffected.

### Seed range of cluster counts

[Seed range of cluster counts](../../../docs/user-guide/03-metric-reference.md#seed-range-of-cluster-counts) · In short 50 words

Writing "the tags fall into five groups" holds only when other seeds also give five. If the range is 4–7, report the range, or that the count depends on the seed. The shown partition's own count lies within or at the edge of this range.

### Seed spread of modularity and silhouette

[Seed spread of modularity and silhouette](../../../docs/user-guide/03-metric-reference.md#seed-spread-of-modularity-and-silhouette) · In short 54 words

Read a change in Q or the silhouette, between Network States or after removing a tag, beside this SD: a change of similar size is what another run of the clustering can give. It is a scale, not a test: a removal's change in Q always includes the mechanical loss of the tag's links, and an SD of 0, common under Leiden, does not make every change meaningful. A small SD does not mean that the seeds find the same clusters; the adjusted Rand index answers that.

### Stability

[Stability](../../../docs/user-guide/03-metric-reference.md#stability) · In short 41 words

The clustering is a randomised search, and other seeds can give different splits with nearly the same Q. Every number in this section compares the shown clusters with K extra runs on the unchanged network. Read other differences, between settings or after removing a tag, against this floor: a difference of similar size to the seeds' own spread is what another run of the clustering can give.

### Strength (weighted degree)

[Strength (weighted degree)](../../../docs/user-guide/03-metric-reference.md#strength-weighted-degree) · In short 60 words

The clustering works on these weights, so strength shows how much a tag pulls on the clusters; the Inspector marks the version used for clustering. A tag with a high total but a low own-cluster strength is linked mainly to other clusters (compare Spread across clusters). Neither total says that a characteristic matters more for how many people play a game: it describes the network of tags, not the games' player numbers.

### Tag game count

[Tag game count](../../../docs/user-guide/03-metric-reference.md#tag-game-count) · In short 51 words

Node size in the graph shows this count. It is the starting point for every other number of a tag: a tag on 60 of the 100 games shares games with almost every other tag, so it has many links and a high strength whatever it means for the games. Check how common a tag is before reading anything else about it; whether that frequency is unusual among the most-played games is answered by the share ratio in the feature analysis, not here.

### Tags not in the network

[Tags not in the network](../../../docs/user-guide/03-metric-reference.md#tags-not-in-the-network) · In short 41 words

The network describes only the tags it contains. A characteristic that only a handful of the Top 100 share falls below the minimum games per tag and cannot appear in any cluster; hidden and removed tags are left out by choice. Before writing that a characteristic is missing from the clusters, check here whether it was in the network at all.

### Top-strength tag

[Top-strength tag](../../../docs/user-guide/03-metric-reference.md#top-strength-tag) · In short 38 words

When the Cluster Center and the most-linked member are the same tag, the cluster has one reference point. When they differ, the most-linked member is often a tag that is common across the most-played games, and so linked to everything, while the center is the member whose games are closest to the other members'. Showing both keeps a frequent tag from being mistaken for the characteristic that sets a group apart.

### Within-cluster strength z-score

[Within-cluster strength z-score](../../../docs/user-guide/03-metric-reference.md#within-cluster-strength-z-score) · In short 52 words

Inside a cluster, a few members usually hold most of the link weight. A high value marks such a member, and on shared games it is often a common tag. The Inspector shows the cap for the cluster's size beside the value, because a member of a 4-tag cluster cannot exceed 1.7: compare the members of one cluster with each other, not values from clusters of different sizes.

### Deposit the export zip

[Deposit the export zip](../../../docs/user-guide/05-citing-and-reproducing.md#deposit-the-export-zip) · In short 49 words

Clusters and their numbers belong to one Network State, so the figures and tables of a paper should travel with the Network State that produced them. The zip opens in the app on another computer that has the same Build, and the recomputed `state_id` confirms that the numbers are the same.
