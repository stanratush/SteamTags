# 03: Non-overlapping layouts and the packed Cluster-separated layout

**What to build:** when the graph first loads, every node is visible and separated from the others, in both layouts. The Cluster-separated layout is compact: each region is sized to its cluster, and the regions are packed tightly.

**Blocked by:** 01

**Status:** done

Spec: [App readability spec](../spec.md): "Layout". Prototype: `packedPositions` in [01-styling-directions](../prototypes/01-styling-directions/PROTOTYPE-styling-directions.html). It only scales the global positions; the real layout runs a local spring layout.

- [x] Node size is a fixed function of `n_games` relative to the dataset's most frequent tag. It is computed in Python and sent in the payload; the renderer no longer derives it from the visible set.
- [x] A deterministic overlap-removal pass (node radii + a 4-unit gap) runs after the seeded spring layout in `global_positions`, on the full loose layout, so thresholds still never move the graph. The same pass runs after `relayout`.
- [x] `cluster_separated_positions`:
  - Region side grows with √(members).
  - Members are placed by a short seeded spring layout from their global positions, with the Cluster Center pinned in the middle, then de-overlapped.
  - Regions are shelf-packed biggest first with small even gaps, rows aimed at the canvas aspect ratio (passed in; default 1.4).
  - One-Tag Clusters share one compact grid region, packed as the last box.
- [x] Positions stay a pure function of their inputs and are never part of the Network State. `nodes.csv` coordinates change value only; the columns and `schema_version` stay the same.
- [x] Tests:
  - No two nodes overlap (centre distance ≥ r1 + r2) for every dataset of the test Build, at the default and the loosest thresholds, in both layouts and after Re-layout.
  - The same inputs give identical positions.
  - The packed area is at most 1.5 × the sum of the region areas.
  - The Center sits at its region's centre.
  - Moving a threshold leaves the global positions unchanged.
- [x] The "Layout" entry in `docs/user-guide/03-metric-reference.md` describes overlap removal and the packed regions. Positions are still never a metric.

## Comments

**2026-10-06 (implemented):** `network/layout.py`: `node_sizes` (diameter 10 + 24·√(n / most frequent tag's n), stored on `NetworkState.sizes` and sent in the payload), `remove_overlaps` (deterministic, vectorised over candidate pairs; it stops only after a full check finds no pair closer than the 4-unit gap), the packed `cluster_separated_positions` (Center pinned in the middle, the others' centroid moved onto it so members surround it; first-fit shelf packing that tries every contiguous run of boxes as the row width and keeps the smallest box weighted by its distance from the aspect). `aspect` is a parameter; the app packs at the default 1.4 so the drawn positions equal the exported ones (tested), and the render-time stretch adapts the drawing to the canvas. The app now lays out on the canonical int-id graph of `to_graph`, which also fixed an old mismatch between the drawn and the exported Cluster-separated coordinates. Overall's global layout takes about 220 ms on the real Build (spring 146 ms). On the real Build the first Cluster-separated fit is at zoom 0.49 instead of 0.093.

**2026-10-06 (review fix):** The app now passes the real canvas shape: `graph.js` reports the free area's aspect ratio (steps of 0.2, within 0.6-2.4) on a `graph-aspect` store, and `render_graph` packs the Cluster-separated rows for it. Exports keep the default 1.4, so the drawn and exported Cluster-separated coordinates are equal only at that aspect (tested). `remove_overlaps` now always ends without an overlap: when a settle runs out of rounds, the free nodes spread out by half from the fixed node (or the centroid) and settle again (tested with a chain that one round cannot resolve).
