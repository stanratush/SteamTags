# What does the Cluster Comparison mode look like?
Type: prototype
Status: resolved
Blocked by: 03, 04, 05

## Question

Make a rough, clickable Cluster Comparison mode on real data and decide its shape with the researcher:
- how datasets are included and how each one's g, s and resolution are set (per [Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md));
- the overview of all dataset pairs, and how one pair is picked;
- how the matches of one pair are shown so that one-to-many reads clearly: a table of matches, a Cluster-by-Cluster heatmap, a two-column link diagram, or a mix;
- one match in detail: shared Tags, Tags unique to each Cluster, the two shared percentages, the measures from [Which measures survive on the real Builds?](04-measures-on-real-builds.md), and the games from [What are "the games in both Clusters" of a match?](05-games-in-both-clusters.md) (its columns, count line and empty-list texts are decided there; place them, and the games-in-common count in the pair overview);
- how the two flags look (no overlap; no match above the minimum) and where the minimum similarity is set;
- how a Cluster is named so its dataset is never in doubt (`C3` alone means nothing across datasets), and whether the Cluster's colour from the Workbench carries over.

Prototype in `prototypes/06-look-of-the-mode/`.

## Answer

Decided with the researcher on the prototype, 2026-11-17: **variant B (pair list · link diagram) as it stands.** Prototype: [index.html](../prototypes/06-look-of-the-mode/index.html) (open with `?variant=B`), data from [export.py](../prototypes/06-look-of-the-mode/export.py) on Build `20261008T221504Z-7a23ae9f`, every grid cell's stored Selected Partition, matching rules in [logic.js](../prototypes/06-look-of-the-mode/logic.js) (it reproduces the figures of the [measures report](../prototypes/04-measures-on-real-builds/report.md)). Variants A (dataset × dataset matrix, grouped match table, Inspector) and C (all-pairs table, Cluster × Cluster heatmap, a g × s grid per dataset) were weighed and not taken. Names are working names.

**Layout.** The mode's header carries the shared settings as one line of controls, as decided in [Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md). Below it, two columns: a left sidebar with the datasets and then the pairs, and a main column with the link diagram of the chosen pair and, under it, the detail of the chosen match.

**Datasets** (sidebar, top): a compact table, one row per Top-N Dataset of the Build: an include checkbox, the dataset's name, g, s and γ, and under the name the source line (★ pick / cell you selected / set by hand / no run) and the Seed-Noise Floor. g, s and γ are edited in the row itself, with the editing rules of ticket 03. **A cell is selected in Parameter Selection, not in the mode**: the mode has no grid of its own and links there.

**Pairs** (sidebar, below): a list of every pair of included datasets, **ranked by ARI on the Common Tags**, highest first. Each row shows ARI with a small bar, the Common Tags count with the two shares, and the number of games in common. Clicking a row chooses the pair. A ⇄ button by the pair's title swaps which dataset is on the left (A).

**Matches of one pair: a two-column link diagram.** A's Multi-Tag Clusters stand in a column on the left, B's on the right, each as a box with its label, Tag count, its Tags listed (clipped to two lines) and its flag. A curve joins two boxes for each Cluster Match; its width and strength follow whole-Cluster Jaccard and its value is written on it. One-to-many reads as several curves leaving one box. Clicking a box shows only its curves and dims the Clusters it doesn't match; clicking it again shows every curve. Clicking a curve chooses the match.

**Minimum similarity and flags.** The minimum-similarity slider (Jaccard, starting at 0.10) sits above the diagram, on the right. Matches below it are hidden, with a "show" link that draws them dashed. The three flags (not in the other network; no overlap; no match above the minimum) are coloured badges on the Cluster's box, on either side. A line under the diagram says how many One-Tag Clusters each side has and that they are not matched.

**One match in detail** sits under the diagram: the two Clusters' names; the four figures (whole-Cluster Jaccard, the share of each Cluster's Tags that is shared, Jaccard on the Common Tags with their counts); the Lift sentence ("n shared Tags: x× the E the Cluster sizes alone give", with N Common Tags); three Tag columns, namely Shared, Only in A's Cluster and Only in B's Cluster, where each unshared Tag says where it sits in the other dataset (in Cluster Cx / isolated / not in the network); then **Games in both Clusters** with ticket 05's count line, columns, `GAMES_SHOWN` rows with "Show all N", and empty-list texts.

**Naming and colour.** A Cluster is always written with its dataset, **"Overall C3"**, wherever it stands alone (detail, Tag columns, tooltips). In the diagram the column heading names the dataset and the boxes say only "C3". **Each dataset has its own colour**, used on its name everywhere and as the left border of its Cluster boxes. **The Workbench's Cluster colours do not carry over**: they follow the label, so Overall C1 and Strategy C1 would both be blue (seen in variant A).

**Seen on the data**

- The diagram stays readable for the lopsided pairs: RPG × Strategy (15 against 3 Clusters) is tall but shows at a glance which RPG Clusters carry a flag (9 "no match above the minimum", 3 "not in the other network" at 0.10).
- Puzzle pairs have 1–2 games in common, so the games list is nearly always the "no games in common" text.

**Not settled by the prototype**

- A hand-set dataset can't be re-clustered in the browser, so the prototype only changes its source line. How long re-clustering takes is part of the compute question.
- The wording of every label: [What are the measures called, and how is each one read?](11-names-and-readings.md)
- The prototype has no export button and no route into the Workbench.
