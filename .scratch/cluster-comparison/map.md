# Map: Cluster Comparison

Label: wayfinder:map

## Destination

An **implementation-ready spec** (`.scratch/cluster-comparison/spec.md`) for a fourth mode of the Tag Network app, **Cluster Comparison**: the user includes Top-N Datasets of the open Build, sets g, s and the resolution for each, and sees how the Clusters of one dataset match the Clusters of another. Every design choice is locked, so the spec can be sliced into issues without further design questions. *(Charted with the researcher, 2026-11-16.)*

## Notes

- **Domain:** the Tag Network app and `steamstudy.network`. Glossary: [CONTEXT.md](../../CONTEXT.md). Use its terms: Top-N Dataset, Build, Cluster, Multi-Tag Cluster, One-Tag Cluster, Threshold Pair, Network State, Selected Resolution, Membership Stability, Seed-Noise Floor, Hennig's Jaccard, Whole-Cluster Jaccard.
- **Skills:** grilling tickets use `grilling` + `domain-modeling`. Prototypes use `prototype` and live in `prototypes/NN-<slug>/`. Research findings go in `research/NN-<slug>.md` on the working branch.
- **Decided while charting** (don't re-ask; a ticket that reopens one says so explicitly):
  - The comparison covers the **Top-N Datasets of the open Build** only. Comparing across Builds is a question of its own: [Can datasets of different Builds be compared?](issues/08-cross-build-comparison.md)
  - Each included dataset carries its own **g, s and resolution**. Clustering Weight, algorithm, seed, hidden and removed Tags and the Minimum Months Filter are **shared** across the comparison.
  - **Any number** of datasets can be included. Matches are always computed and shown **between two datasets at a time**, with an overview of all the pairs. No multi-way matching.
  - It is a **fourth app mode** beside Workbench, Analysis Report mode and Parameter Selection, with a CSV export.
  - **Jaccard is the baseline**. Which other measures ship is decided on this map, on real data; the spec names the final set. The app does not ship a menu of every candidate.
  - **Cluster Match** (new term): a pair of Clusters, one from each of two datasets, that share at least one Tag. One Cluster can have several. Matches are ranked by similarity, and a user-set **minimum similarity** hides weak ones.
  - Two distinct flags: **no overlap** (the Cluster shares no Tag with any Cluster of the other dataset) and the weaker **no match above the minimum**.
  - Only **Multi-Tag Clusters** are matched. A Tag that sits in a One-Tag Cluster in the other dataset is shown as isolated there, not as a match.
  - Similarity is computed on **Tag sets only**. For a match the view may also **show the games that are in both Clusters**, as the app shows each Cluster's games today; that is display, never part of a similarity.
  - For each match the view shows the shared Tags, the Tags unique to each Cluster, and the percentage of each Cluster's Tags that are shared.
  - The spec covers the glossary terms, a User Guide section, metric-reference entries, in-app help and the Bulgarian wording.
- **Constraints:**
  - Every new string needs a bg catalogue entry (ADR 0003; parity test).
  - A new glossary term must also appear in the User Guide (`tests/test_guide.py` reads CONTEXT.md), so **Cluster Match** and the other new terms enter CONTEXT.md with the implementation, not during this map. Tickets record the agreed wording in their answers.
  - One Build per tab (ADR 0006). Layout stays downstream of analysis (ADR 0002).
  - Clusters are labelled `C1…` per Network State, so the same label in two datasets means nothing. The view must always say which dataset a Cluster belongs to.
  - Nothing is implemented on this map except throwaway prototypes.
- **Finish:** when no ticket is open and Not yet specified is empty, write `spec.md` from the Decisions so far.

## Decisions so far

<!-- one line per resolved ticket: gist + link -->
- [Which measures can score the similarity of two Clusters from different datasets?](issues/01-similarity-measures.md): run four beside Jaccard: the two containments (with their minimum), Jaccard on the common Tags, the overlap Lift on the common Tags (descriptive, no p-value), and ARI on the common Tags for the pair overview; Dice, cosine, weighted Jaccard, NMI and VI are left out.
- [How do Tags missing from the other dataset's network enter a match?](issues/02-tags-missing-from-the-other-network.md): Common Tags are the Tags in both networks; a Cluster's unshared Tags are split into in another Cluster, isolated, and not in the network; every similarity is shown on the whole Cluster (headline) and on the Common Tags, the latter "—" below two Common Tags; "no overlap" is split from "not in B's network"; the pair overview shows the Common Tags count and shares.

## Not yet specified

- **Wording and documentation.** The names and plain-language readings of the measures that ship, the wording bands if any, the User Guide section, the help entries and the Bulgarian forms. Waits on which measures survive the prototype.
- **Compute and caching.** A comparison needs one Network State per included dataset. Whether these reuse the Workbench's cached states, how long a comparison of several datasets takes, and whether it needs a background job. Waits on the defaults and on the look of the mode.
- **Moving between modes.** Opening a matched Cluster in the Workbench, or sending the Workbench's current g, s and resolution into the comparison. Waits on the look of the mode.
- **The defining Tag of a Tag-Specific Dataset.** In the Puzzle dataset every game has Puzzle, so that Tag behaves differently there than in Overall. Whether the comparison needs a rule for it, or only a caveat, should show in the prototype on real data.
- **Datasets of very different size or density.** Two datasets at the same g and s can give networks with very different numbers of Tags and Clusters. Whether the view should warn about a lopsided comparison is unclear until the measures are run on real data.

## Out of scope

- **Similarity computed on games.** Two Top-N Datasets of one Build mostly hold different games, so game overlap would mostly measure how the datasets were drawn. Shared games are shown for a match, never scored.
- **Multi-way matching** of one Cluster across three or more datasets at once.
- **The generated feature-analysis report.** Cluster Comparison is an app mode with its own export.
