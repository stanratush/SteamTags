# Which measures survive on the real Builds?
Type: prototype
Status: resolved
Blocked by: 01, 02

## Question

Run Jaccard and the shortlisted candidates from [Which measures can score the similarity of two Clusters from different datasets?](01-similarity-measures.md) on dataset pairs of the full Build (e.g. Overall vs a Tag-Specific Dataset, and two Tag-Specific Datasets), with the Tag universe rule from [How do Tags missing from the other dataset's network enter a match?](02-tags-missing-from-the-other-network.md). A script and a plain table are enough; no app.

With the researcher looking at the output, decide:
- which measures ship beside Jaccard, and which one ranks the matches;
- the default **minimum similarity** and the measure it applies to;
- whether a whole-pair figure (one number for dataset A vs dataset B) is worth showing in the overview, and which;
- whether a chance-corrected figure tells the reader anything the raw ones do not.

Also note what the run shows about two patches of fog on the [map](../map.md): the defining Tag of a Tag-Specific Dataset, and pairs of datasets with very different numbers of Tags and Clusters.

Prototype in `prototypes/04-measures-on-real-builds/`.

## Answer

Decided with the researcher on the prototype's output, 2026-11-17. Prototype: [run.py](../prototypes/04-measures-on-real-builds/run.py), output [report.md](../prototypes/04-measures-on-real-builds/report.md) and `matches.csv`. Names are working names; nothing enters CONTEXT.md until implementation.

**What was run**

- Build `20261008T221504Z-7a23ae9f`, the only Build with a stored Automatic Parameter Selection run for all five datasets (Lift, Leiden, no Minimum Months Filter, at least 3 Multi-Tag Clusters). Each dataset on its pick under the default Pair Constraints, with the stored Selected Partition: Overall (29 Tags, 4 Multi-Tag Clusters), Puzzle (31, 4), RPG (71, 15, plus 3 One-Tag Clusters), Strategy (39, 3), Simulation (38, 3).
- All 10 pairs of datasets: 103 Cluster Matches. Whole-Cluster Jaccard: median 0.09, quartiles 0.06–0.16, maximum 0.58.
- The Build's cache uses 64-digit folder names; the current code looks up 16-digit ones, so the app would show these runs as "not run". The script overrides the name length in memory. This is a fact about that Build's cache, not a decision.

**Decisions**

1. **Jaccard on the whole Cluster ranks the matches.** Shown beside it for every match: the two shared shares (containments) and the Common-Tag Jaccard.
2. **The minimum of the two containments is not shown as a figure of its own.** Its rank correlation with Jaccard is 0.96 and it never changed a Cluster's top match (58 Clusters with two or more matches). Only 1 match was nested with two or more shared Tags, so the nesting case it was meant to catch is rare here and the two shares already show it.
3. **Common-Tag Jaccard ships.** 27 of the 80 judged matches gain 0.10 or more over the whole-Cluster Jaccard (maximum gain 0.45; median 0.06), so it does separate "Tags missing from the other network" from "Tags grouped differently". 23 matches show "—" (a Cluster with fewer than two Common Tags).
4. **Lift and the expected overlap appear only in a match's detail, never as a ranking and never as a column to sort by.** Lift's rank correlation with Jaccard is 0.38 and it would change the top match of 13 of 58 Clusters, mostly towards one-Tag matches (Lift up to 11.5 for a single shared Tag). It stays as the descriptive reading "x times what the sizes alone give", shown with n.
5. **The minimum similarity applies to the whole-Cluster Jaccard and starts at 0.10.** It remains a control the user sets, down to 0. At 0.10: 48 of 103 matches remain, 51 of the 58 one-Tag matches are hidden, 23 of 116 Clusters (counted per direction) still show two or more matches, 30 are flagged "no match above the minimum". At 0.20 only 1 Cluster still shows a split and 61 are flagged, so the tracking literature's lower thresholds for splits and merges are the ones that fit this data.
6. **The pair overview shows ARI on the Common Tags, with the Common Tags count and shares beside it.** ARI ran from 0.07 (Puzzle × RPG, Puzzle × Simulation) to 0.53 (Strategy × Simulation). AMI and the Tag-weighted mean best Jaccard ordered the 10 pairs almost identically (Spearman 0.90 and 0.84 with ARI), so neither ships.
7. **Chance correction:** at the pair level, ARI is the chance-corrected figure and is kept. At the match level, Lift tells the reader something the raw figures do not only for matches between large Clusters (e.g. Overall C2 × Puzzle C1: Jaccard 0.25, Lift 1.5), which is why it stays in the detail and not in the ranking.
8. **A lopsided pair gets no warning.** RPG's 71 Tags and 15 Clusters against 29–39 Tags and 3–4 Clusters elsewhere show up as low Common Tags shares on RPG's side (32–44%) and as per-Cluster flags (from RPG's side 9–10 of 15 Clusters have no match above 0.20 and 3–4 are "not in B's network"). The overview's shares and each dataset's Tag and Cluster counts are enough.

**Noted for the fog**

- **Defining Tag.** Puzzle, RPG, Strategy and Simulation are all Genre Tags as well as defining Tags, so with Genre Tags hidden they are hidden in every dataset and never enter a match. A rule is only needed if the mode lets the user un-hide Genre Tags or the defining Tag; that was not run.
- **"No overlap" did not occur** in any of the 20 directions: every Cluster with a Common Tag shared one with some Multi-Tag Cluster. "Not in B's network" occurred for 1 Cluster of Puzzle and 3–4 of RPG.
- Three of the five datasets have a Seed-Noise Floor of 1.00; Puzzle's is 0.52 and RPG's 0.80. That bears on [How is a match read against seed and threshold dependence?](07-seed-and-threshold-dependence.md)

**Not checked**

- Only picks were compared; no hand-set dataset and no other cell of a grid.
- One Build, one set of shared settings (Lift, Leiden). The shared-game count as Clustering Weight was not run.
- The hypergeometric mean was not confirmed by simulation, as research 01 suggested.
