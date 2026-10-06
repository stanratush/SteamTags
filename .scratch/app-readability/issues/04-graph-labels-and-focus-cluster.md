# 04: Graph labels and focus cluster

**What to build:** the important labels are readable at any zoom without piling up, and the graph takes on B's look. A cluster can be focused from the legend, its region title or the Clusters table.

**Blocked by:** 01, 02

**Status:** done

Spec: [App readability spec](../spec.md): "Labels", "Focus cluster and tag search", "Styling and layout" (the B items for the graph).

- [x] Priority labels keep a constant on-screen size (about 11.5 px, re-sized on zoom). They are:
  - the selected element and its neighbours;
  - the Cluster Centers;
  - the 15 largest tags by `n_games` (ties broken by tag id);
  - in Cluster-separated mode, the largest tag of each cluster.

  Region titles also keep a constant size.
- [x] Collision culling after each zoom: a priority label that overlaps a higher-ranked one is hidden. The ranking is: the selection and its neighbours (never hidden), then Centers, then `n_games`.
- [x] Other labels scale with zoom and hide below 7 px on screen.
- [x] B's graph look:
  - a white background behind priority labels;
  - thin dark node borders;
  - slightly muted cluster colours;
  - edges at opacity 0.3, and inter-cluster edges at 0.06 in Cluster-separated mode.

  One-Tag Clusters stay grey.
- [x] Focus cluster: a legend chip, a region title or a Clusters-grid row selects the cluster and zooms to it. That means its region in Cluster-separated mode, or its members' bounding box in Global. Region titles accept clicks; tags inside regions stay clickable.
- [x] Browser check: the default Overall and Puzzle states show readable, non-overlapping priority labels at the first fit, in both layouts.

## Comments

**2026-10-06 (implemented):** Python decides the priority set and its culling rank (`renderer.priority`, sent as class `pri` and `prio`); `graph.js` adds the selection and its neighbours (class `hot`, never hidden; a selected cluster's members count as its neighbours), re-sizes priority labels and region titles to 11.5 / 12.5 px on screen once per frame while zooming, and culls by label bounding box. B's look: white label backgrounds, 1.2 px translucent dark borders, the muted palette (also used by the legend), edges at 0.3 and inter-cluster edges at 0.06 in Cluster-separated mode. Selecting a cluster (legend chip, region title, Clusters-grid row) adds a `focus` view command to the `graph-data` patch. Browser check on the real Build at 1440 × 900: Overall and Puzzle, both layouts, priority labels at 11.5 px with no overlaps at the first fit (Overall 12 / 9 shown, Puzzle 7 / 11 shown, the rest culled); focusing C2 (Global) and C3 (Cluster-separated) fills the canvas with the cluster.
