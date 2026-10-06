# 03: Non-overlapping layouts and the packed Cluster-separated layout

**What to build:** when the graph first loads, every node is visible and separated from the others, in both layouts. The Cluster-separated layout is compact: each region is sized to its cluster, and the regions are packed tightly.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Layout". Prototype: `packedPositions` in [01-styling-directions](../prototypes/01-styling-directions/PROTOTYPE-styling-directions.html). It only scales the global positions; the real layout runs a local spring layout.

- [ ] Node size is a fixed function of `n_games` relative to the dataset's most frequent tag. It is computed in Python and sent in the payload; the renderer no longer derives it from the visible set.
- [ ] A deterministic overlap-removal pass (node radii + a 4-unit gap) runs after the seeded spring layout in `global_positions`, on the full loose layout, so thresholds still never move the graph. The same pass runs after `relayout`.
- [ ] `cluster_separated_positions`:
  - Region side grows with √(members).
  - Members are placed by a short seeded spring layout from their global positions, with the Cluster Center pinned in the middle, then de-overlapped.
  - Regions are shelf-packed biggest first with small even gaps, rows aimed at the canvas aspect ratio (passed in; default 1.4).
  - One-Tag Clusters share one compact grid region, packed as the last box.
- [ ] Positions stay a pure function of their inputs and are never part of the Network State. `nodes.csv` coordinates change value only; the columns and `schema_version` stay the same.
- [ ] Tests:
  - No two nodes overlap (centre distance ≥ r1 + r2) for every dataset of the test Build, at the default and the loosest thresholds, in both layouts and after Re-layout.
  - The same inputs give identical positions.
  - The packed area is at most 1.5 × the sum of the region areas.
  - The Center sits at its region's centre.
  - Moving a threshold leaves the global positions unchanged.
- [ ] The "Layout" entry in `docs/user-guide/03-metric-reference.md` describes overlap removal and the packed regions. Positions are still never a metric.

## Comments
