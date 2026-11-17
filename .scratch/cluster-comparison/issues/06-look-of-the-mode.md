# What does the Cluster Comparison mode look like?
Type: prototype
Status:
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
