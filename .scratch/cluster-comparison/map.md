# Map: Cluster Comparison

Label: wayfinder:map

## Destination

An **implementation-ready spec** (`.scratch/cluster-comparison/spec.md`) for a fourth mode of the Tag Network app, **Cluster Comparison**: the user includes Top-N Datasets of the open Build, sets g, s and the resolution for each, and sees how the Clusters of one dataset match the Clusters of another. Every design choice is locked, so the spec can be sliced into issues without further design questions. *(Charted with the researcher, 2026-11-16.)*

## Notes

- **Domain:** the Tag Network app and `steamstudy.network`. Glossary: [CONTEXT.md](../../CONTEXT.md). Use its terms: Top-N Dataset, Build, Cluster, Multi-Tag Cluster, One-Tag Cluster, Threshold Pair, Network State, Selected Resolution, Membership Stability, Seed-Noise Floor, Hennig's Jaccard, Whole-Cluster Jaccard.
- **Skills:** grilling tickets use `grilling` + `domain-modeling`. Prototypes use `prototype` and live in `prototypes/NN-<slug>/`. Research findings go in `research/NN-<slug>.md` on the working branch.
- **Decided while charting** (don't re-ask; a ticket that reopens one says so explicitly):
  - The comparison covers the **Top-N Datasets of the open Build** only. Comparing across Builds is out of scope (see Out of scope).
  - Each included dataset carries its own **g, s and resolution**. Clustering Weight, algorithm, seed, hidden and removed Tags and the Minimum Months Filter are **shared** across the comparison. *(The seed is amended: a dataset on a cell involves no seed; see [Why does the seed change between cells, and should it be the same for every dataset?](issues/10-seed-per-dataset.md))*
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
- [Where do each dataset's g, s and resolution come from, and the shared settings?](issues/03-per-dataset-defaults.md): each dataset takes a cell of its Automatic Parameter Selection run as "Apply to Workbench" does, starting on the pick under Parameter Selection's current Pair Constraints; values stay editable ("set by hand"), a dataset with no run starts from the network defaults, and a source line says which; the shared settings are the mode's own controls starting from the Parameter Selection settings, and changing one re-resolves every dataset (no defining-Tag control: see the last decision); the seed is left to its own ticket.
- [Why does the seed change between cells, and should it be the same for every dataset?](issues/10-seed-per-dataset.md): the seed differs per cell because a Selected Partition is chosen from a pool found with 10 scan seeds and the Workbench seed is only an address for it; a dataset on a cell shows the stored Selected Partition with no re-clustering and no seed, a hand-set or no-run dataset uses the main seed, the mode has no seed control, and each dataset shows its Seed-Noise Floor.
- [Which measures survive on the real Builds?](issues/04-measures-on-real-builds.md): on 103 matches of the full Build, whole-Cluster Jaccard ranks and takes the minimum similarity (a user control starting at 0.10); the two shared shares and Common-Tag Jaccard are shown beside it; the minimum containment is dropped; Lift with the expected overlap appears only in a match's detail; the pair overview shows ARI on the Common Tags with their count and shares (no AMI, no mean best Jaccard); a lopsided pair gets no warning.
- [What are "the games in both Clusters" of a match?](issues/05-games-in-both-clusters.md): games in both Top-N Datasets that have at least one Tag of each Cluster (all its Tags, the Inspector's rule), never called "shared games"; columns show the rank and matched count on each side; a count line splits the games in common into in both / only A / only B / neither; the empty list says whether the datasets have no games in common; the pair overview gains a games-in-common count.
- [What does the Cluster Comparison mode look like?](issues/06-look-of-the-mode.md): variant B of the prototype: a sidebar with the datasets (include, g/s/γ edited in the row, source line; cells selected in Parameter Selection) and the pairs ranked by ARI; the chosen pair as a two-column link diagram of Multi-Tag Clusters (curve width = Jaccard, flags as badges on the boxes, the minimum slider above it, weaker matches hidden or dashed); the match's detail under it; Clusters named "Overall C3" in a colour per dataset, not the Workbench's Cluster colours.
- [How is a match read against seed and threshold dependence?](issues/07-seed-and-threshold-dependence.md): a written caution plus figures the datasets already have, with no new per-match figure: each dataset row shows its Seed-Noise Floor and, on a cell, its Neighbour Agreement; low Membership Stability is never marked; the caution says a match is not evidence that the Clusters are real and moves with seed, g, s and resolution.
- [What fixes one comparison, and what does its export hold?](issues/09-comparison-identity-and-export.md): a Comparison State (working name, with a `comparison_id` made like `state_id`) is the Build, the shared settings and each dataset's source and values (a cell by its run's settings key and g, s; otherwise g, s, γ and the main seed); the minimum similarity and pair orientation are view choices; the export is record-only, holds every pair in Build dataset order as six CSVs (datasets, clusters, pairs, matches, cluster flags without the minimum, match games) plus `comparison.json`, and Import variants come from the usual rule.
- [What are the measures called, and how is each one read?](issues/11-names-and-readings.md): Cluster Match / *съвпадение на клъстери*; "Common Tags" renamed Comparable Tags (*сравними тагове*), freeing shared Tags (*общи тагове*); headline Match Jaccard plus Jaccard (comparable); match Lift renamed Overlap vs. expected (export columns renamed); flags as a "No match:" family; One-Tag Cluster never "isolated"; source line by Threshold Pair; no wording bands; caution, readings, Export CSV help worded in both languages; five terms for CONTEXT.md and the guide outline.
- [Where does each dataset's Network State come from, and how long does a comparison take?](issues/12-compute-and-caching.md): a dataset on a cell uses its stored Selected Partition (no Network State); a hand-set or no-run dataset gets a light partition-plus-noise-seeds function tested equal to `compute_state`; all in the request with one loading overlay, under about 5 s cold for five datasets; LRU memos per dataset and per `comparison_id`, so pair, minimum and A/B swap never recompute; cells are read on resolve, a vanished cell falls to the no-run rule.
- [How does the user move between Cluster Comparison and the Workbench?](issues/13-moving-between-modes.md): no route between the comparison and the Workbench either way (Apply to Workbench stays in Parameter Selection); the mode's state survives mode switches and starts fresh on a Build switch; the dataset row links to Parameter Selection on its cell, which gains "Use in Cluster Comparison" (disabled when its settings differ from the comparison's shared ones); a dataset on the pick follows changed Pair Constraints.
- [What happens to a defining Tag in a match when Genre Tags or defining Tags are shown?](issues/14-defining-tag-in-a-match.md): each dataset's own defining Tag is always hidden (the mode has no control for it; shown, it made 9 matches resting on it alone); a Tag hidden in only one dataset of a pair is set aside for that pair and listed as "hidden in Strategy (its defining Tag)"; other Genre Tags, when shown, are matched like any Tag.

## Not yet specified

_Nothing. Every ticket is resolved, and the destination is reached: [spec.md](spec.md) (written 2026-11-17)._

## Out of scope

- **Similarity computed on games.** Two Top-N Datasets of one Build mostly hold different games, so game overlap would mostly measure how the datasets were drawn. Shared games are shown for a match, never scored.
- **Multi-way matching** of one Cluster across three or more datasets at once.
- **The generated feature-analysis report.** Cluster Comparison is an app mode with its own export.
- **Comparing datasets of different Builds** ([Can datasets of different Builds be compared?](issues/08-cross-build-comparison.md)). Every decision here rests on one Build: one Tag universe for the Common Tags, one Parameter Selection cache, and one Tag Depth and exclusion list behind the shared settings. Across Builds, Tag identity, "shared" settings and one Build per tab (ADR 0006) would each need their own design. It may come back as a later effort; meanwhile, two tabs side by side.
