# 04: Graph labels and focus cluster

**What to build:** the important labels are readable at any zoom without piling up, and the graph takes on B's look. A cluster can be focused from the legend, its region title or the Clusters table.

**Blocked by:** 01, 02

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Labels", "Focus cluster and tag search", "Styling and layout" (the B items for the graph).

- [ ] Priority labels keep a constant on-screen size (about 11.5 px, re-sized on zoom). They are:
  - the selected element and its neighbours;
  - the Cluster Centers;
  - the 15 largest tags by `n_games` (ties broken by tag id);
  - in Cluster-separated mode, the largest tag of each cluster.

  Region titles also keep a constant size.
- [ ] Collision culling after each zoom: a priority label that overlaps a higher-ranked one is hidden. The ranking is: the selection and its neighbours (never hidden), then Centers, then `n_games`.
- [ ] Other labels scale with zoom and hide below 7 px on screen.
- [ ] B's graph look:
  - a white background behind priority labels;
  - thin dark node borders;
  - slightly muted cluster colours;
  - edges at opacity 0.3, and inter-cluster edges at 0.06 in Cluster-separated mode.

  One-Tag Clusters stay grey.
- [ ] Focus cluster: a legend chip, a region title or a Clusters-grid row selects the cluster and zooms to it. That means its region in Cluster-separated mode, or its members' bounding box in Global. Region titles accept clicks; tags inside regions stay clickable.
- [ ] Browser check: the default Overall and Puzzle states show readable, non-overlapping priority labels at the first fit, in both layouts.

## Comments
