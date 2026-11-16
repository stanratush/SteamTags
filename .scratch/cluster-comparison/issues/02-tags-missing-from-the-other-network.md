# How do Tags missing from the other dataset's network enter a match?
Type: grilling
Status: resolved
Blocked by:

## Question

A Tag of a Cluster in dataset A can be, in dataset B:
1. in a Multi-Tag Cluster (shared with that Cluster, or with another one);
2. in a One-Tag Cluster (charted: shown as isolated there);
3. in B's games but below B's minimum games per tag, so not in B's network at all;
4. absent from B's games entirely;
5. hidden or removed by the shared settings (in neither network).

Charted: the view shows the Tags unique to each Cluster and the percentage of each Cluster's Tags that are shared.

Decide:
- whether "unique to this Cluster" is one list or is split by the cases above (in another Cluster of B, isolated in B, not in B's network);
- which Tags the shared percentage is taken over: all the Cluster's Tags, or only those that are in B's network;
- whether the similarity is reported both ways, as the glossary already does for subsamples with **Hennig's Jaccard** (judged on surviving Tags) and **Whole-Cluster Jaccard** (lost Tags count against);
- whether "no overlap" needs a further split: a Cluster none of whose Tags are in B's network is a different finding from one whose Tags are all there but scattered.

## Answer

Grilled with the researcher, 2026-11-16. Names are working names; final wording, readings and Bulgarian forms belong to the map's "Wording and documentation" item. Nothing enters CONTEXT.md until implementation.

Running example: Cluster A of dataset 1 = {Puzzle, Logic, Casual, Hidden Object, Match 3}. In dataset 2: Puzzle and Logic are in C2, Casual in C5, Hidden Object is a One-Tag Cluster, Match 3 is in 2 games (below g).

1. **Common Tags** (new term): the Tags that are in both networks of a compared pair of datasets, i.e. visible and reaching the minimum games per tag in each. One-Tag Clusters count. It is the counterpart of the "surviving Tags" of **Hennig's Jaccard**. (Example: four of A's Tags are common.)
2. **The unshared Tags of a Cluster in a match are split into three groups**, each labelled with the other dataset's name:
   - **in another Cluster**: the Tag is in a different Multi-Tag Cluster of B; that Cluster is named (Casual → C5);
   - **isolated**: the Tag is a One-Tag Cluster in B (Hidden Object);
   - **not in the network**: the Tag is not in B's network (Match 3).
3. **"Not in the network" is one group** for "below B's minimum games per tag" and "in none of B's games". The Tag's game count in B is shown beside it ("2 games, minimum 5"; "0 games"). Tags hidden or removed by the shared settings are in neither network and appear in no list.
4. **Every similarity is reported both ways:**
   - **whole Cluster** (headline; used for ranking and for the minimum similarity): Tags not in B's network count against. **Jaccard** = n / (a + b − n); **shared share** = n / a (example: 2 of 5 = 40%);
   - **common Tags only**: Tags not in the other network are set aside. **Common-Tag Jaccard** = n / (a′ + b′ − n); **shared share of common Tags** = n / a′ (example: 2 of 4 = 50%).
   The gap between the two shows how much of a low score comes from Tags missing from the other network. The glossary names **Hennig's Jaccard** and **Whole-Cluster Jaccard** stay reserved for subsamples and are not reused here.
5. **Fewer than two common Tags: cannot be judged.** A Cluster's shared share of common Tags shows "—" when that Cluster has fewer than two common Tags. A match's Common-Tag Jaccard shows "—" when either Cluster has fewer than two. The whole-Cluster forms are always shown, and the match stays listed and ranked by its whole-Cluster value.
6. **"No overlap" is split into two flags** for a Cluster of A that shares no Tag with any Multi-Tag Cluster of B:
   - **not in B's network**: none of its Tags is a common Tag; the comparison cannot judge it (a finding about the datasets);
   - **no overlap**: it has common Tags, but every one is isolated in B (a finding about the grouping). The flag shows the counts, e.g. "3 Tags isolated in B, 2 not in B's network".
   A Cluster whose Tags are all in B's network but spread one each over several Clusters is neither: it has several one-Tag matches and falls under the charted "no match above the minimum" flag.
7. **Two Tag sets, both stated by name in the spec:**
   - Lift and Common-Tag Jaccard use the full set of Common Tags (for Lift, N counts every Common Tag, isolated ones included);
   - the pair-overview ARI keeps the existing `selection.link` set: Common Tags with an edge in at least one of the two networks, because Tags isolated in both agree trivially and would inflate ARI.
8. **The pair overview shows the Common Tags of each pair of datasets**: their number, and that number as a share of each network's Tags, in both directions ("38 common Tags: 76% of Overall's, 54% of Puzzle's"). This is the coverage figure kept beside ARI. Whether a lopsided pair also needs a warning stays open on the map.
