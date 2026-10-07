# Spec: Graph readability

Settled in a grilling session on 2026-10-06. Glossary: [CONTEXT.md](../../CONTEXT.md). Builds on the [App readability spec](../app-readability/spec.md); the Overrides section names what it replaces there. Decision record: [ADR 0002](../../docs/adr/0002-layout-is-downstream-of-analysis.md).

## Goal

The Tag Network graph is readable at the first fit, with readability as the primary goal. In the default state of every dataset, at the first fit in a 1440 × 900 and a 1280 × 800 Workbench, in both layouts:

- every visible tag's label is shown at 11.5 px;
- no two node-plus-label boxes overlap;
- the smallest node is at least 14 px across on screen;
- no tag sits far from the graph, also after Tidy (the former Re-layout).

No analytical result changes. Layout parameters (gravity, canvas size, spacing, Tidy) change only coordinates.

**Amendment (2026-10-07, during implementation):** "the first fit in a 1440 × 900 and a 1280 × 800 Workbench" means the Workbench with the **Tables and the Inspector closed** (Controls open). Measured free graph areas: 1116 × 678 and 956 × 561. With every panel docked the free area is only 764 × 352 and 604 × 252. There, the default states' node-plus-label boxes need 127–153k px² even at the smallest zoom that keeps nodes at 14 px, which is 47–57 % and 83–100 % of the free area. A force layout that keeps the graph's structure cannot pack that densely. The reference canvas for exports is 1116 × 678. With more panels open, the same layout fits zoomed out and labels are culled by rank, as for a large set.

**Amendment (2026-10-07, during issue 05):** the Goal holds strictly for the **Global** layout. The **Cluster-separated** layout is best effort. A region needs at least 2.5× its members' node-plus-label area and packing adds 1.2–1.9×, so it needs about twice the Global layout's room. Its labels are spaced for the highest zoom down to 0.55 at which the first fit holds them. Where the regions don't fit even at 0.55, the first fit is lower and labels are culled by rank, as for a large set. Measured on Build `20261006T062622Z-7a23ae9f`: at 1116 × 678 Overall, Puzzle and RPG fit at 0.78–0.86, Strategy and Simulation need about 0.5. At 956 × 561 all five need 0.40–0.53.

## Facts found while grilling

Measured on Build `20261006T062622Z-7a23ae9f`, default states (thresholds 8 / 8, Genre Tags and the defining tag hidden, seed 20261003):

| Dataset | Visible tags | Components (largest first) | Visible extent | Re-layout extent | Main component after Re-layout | Isolated tags' distance after Re-layout |
| --- | --- | --- | --- | --- | --- | --- |
| Overall | 59 | 55, then 4 single tags | 541 × 540 | 1906 × 1447 | 299 × 261 | about 1,020–1,090 |
| Puzzle | 58 | 51, then 7 single tags | 489 × 740 | 1612 × 1535 | 217 × 229 | about 960–1,080 |
| RPG | 67 | 54, then 13 single tags | 560 × 539 | 1934 × 1858 | 247 × 255 | about 900–1,030 |
| Strategy | 65 | 60, then 5 single tags | 664 × 550 | 1973 × 1784 | 281 × 265 | about 950–1,020 |
| Simulation | 60 | 57, then 3 single tags | 556 × 555 | 1473 × 1938 | 279 × 244 | about 970–1,120 |

- **Re-layout's far-away nodes:** `relayout` runs `nx.spring_layout` on the visible graph, which is disconnected. Repulsion throws every tag without a visible link about 1,000 units out, and the rescale to the unit box squeezes the main component to about half. The extent grows about 3.5× and the main structure ends up about 7× smaller on screen. The median distance to the nearest neighbour drops from about 35 to 25 units.
- **The crowded centre:** the default Global layout is the 244-tag loose layout, and the about 60 visible tags are a subset of it. The most frequent tags sit together in its centre. Visible diameters are 17–33 units against a median nearest-neighbour distance of about 35. Only node circles are de-overlapped, never label boxes.
- **Small labels:** only priority labels (about 12 per view) keep a constant 11.5 px. Every other label is 6.5 units and hidden below 7 px on screen, so it disappears at any zoom under about 1.08.
- networkx 3.7 (installed) has `forceatlas2_layout` (gravity, `strong_gravity`, `dissuade_hubs`, `linlog`, `node_size`, `seed`, `pos`) and `kamada_kawai_layout`. scipy 1.18.1 is installed.
- **Positions are already downstream of analysis.** `compute_state` computes the graph, Jaccard distances, clusters, Q and silhouette (Jaccard game-set silhouette, not coordinates), node metrics, Cluster Centers (Jaccard medoid), the null model, seed noise and Membership Stability, and only then positions ([state.py](../../src/steamstudy/network/state.py)). Nothing reads positions except table writing. Removal Sensitivity reclusters `state.graph` and never reads positions (its `position` variable is the run order). `state_id` is a hash of the settings key only. Exports carry positions only in `x_global`, `y_global`, `x_cluster_separated` and `y_cluster_separated` of `nodes.csv`, in the app export and the Build's analysis report tables.
- `recorded_table_hashes_match` ([export.py](../../src/steamstudy/app/export.py)) compares whole CSVs byte for byte, coordinates included. Nothing calls it.

## Decisions

### Analysis and layout are separate (ADR 0002)
- Layout leaves `compute_state`. A new `layout_state(state, canvas) -> positions, sizes, regions` takes a finished `NetworkState` and only reads it. The app, the app export and the Build's analysis report call it after the state is computed. Analysis code never receives coordinates.
- Positions never feed into clustering, Q, silhouette, node metrics, Cluster Centers, Membership Stability, the null model, seed noise or Removal Sensitivity. Data flows one way only: the Cluster-separated layout reads the Cluster Centers in order to pin them.
- `state_id` stays a hash of the settings key. Exports change only the four coordinate columns; every other column, file and the `schema_version` stay the same.
- **Invariance test:** for every dataset of the test Build, compute the state and export it under very different layout settings (default gravity vs. 10× gravity, a different reference canvas, clamp off). Assert that `state_id` and every export file except the four coordinate columns are byte-identical, including `removal_sensitivity.csv` for a few tags.
- `recorded_table_hashes_match` becomes coordinate-blind: it compares every column except the four coordinate columns.

### Global layout
- **ForceAtlas2** (`nx.forceatlas2_layout`) on the **visible** network (the current Network State's nodes and edges, weighted by the active Clustering Weight), with gravity and hub dissuasion. Its parameters are fixed in code and tuned against the geometry test on all five datasets.
- **Start positions:** the dataset's fixed loose layout (the existing 244-tag layout), limited to the visible tags. Positions are a pure function of (layout basis, visible set, canvas size): the same inputs give identical positions, and similar visible sets start alike, so they end up alike.
- **Gravity and clamp:** tags with no visible link are pulled in by gravity. A hard clamp then keeps every tag within the main component's radius plus about 1.5 label heights of its centre, so unlinked tags sit on a ring just outside the main graph. The extent is bounded by design.
- The graph moves when the visible set changes (thresholds, hidden or removed tags), using issue 05's 350 ms animated move. Dragged positions keep their rule from the App readability spec.

### Label-aware spacing and canvas size
- **Label-aware overlap removal** replaces node-only overlap removal. Each node and its label below it (centred) form one box, and every pair of boxes is kept at least the gap apart. It runs after ForceAtlas2 and after the clamp. It is deterministic and always ends without an overlap, like `remove_overlaps` today.
- **Label widths** come from a fixed per-character width table for the system UI font at 11.5 px, rounded up about 10 %, computed in Python. The same width on every machine, so exports don't depend on the viewer's fonts.
- **Canvas size:** `graph.js` reports the free area's pixel size (width and height, rounded to about 10 % steps, so small resizes don't trigger a new layout), replacing the aspect-only `graph-aspect` report. Python lays out for that size, so one model unit is one screen pixel at the first fit, and a label of 11.5 px needs 11.5 units. Opening or closing a panel can trigger a new layout, animated.
- **Exports** use a fixed reference canvas: the graph area of a 1440 × 900 Workbench.
- The render-time 1.6× x-stretch is removed, because the layout already matches the canvas shape.
- **Small sets:** neighbours are never placed more than about 3× the spacing their boxes need, and the first fit never zooms past 100 %. A small graph sits centred at its designed size.
- **Large sets** (loose thresholds, up to about 250 tags): the label room is kept, so the extent grows beyond the canvas. The first fit still shows the whole graph, zoomed out; labels are culled by rank, and more appear as you zoom in. The Goal applies to the default states only.

### Nodes
- Node diameters stay in model units, as a fixed function of `n_games` relative to the dataset's most frequent tag, with a larger range: about 18 + 30·√ratio instead of 10 + 24·√ratio. The final constants are chosen so that the smallest node meets the 14 px goal at the first fit.

### Labels and edges
- **Every** visible tag's label is drawn at a constant 11.5 px on screen, at any zoom.
- Collision culling (same rank as today: the selection and its neighbours, never hidden; then Centers; then `n_games`) only applies once the view is zoomed out past the fit, or when a large set cannot hold every label. The 7 px hiding rule and the 6.5-unit label size go away.
- Every label has a white text halo. Selected or highlighted (`hot`) labels get a solid white background box and bold weight. Cluster Centers stay bold.
- Edges are 0.4–3 px wide (instead of 0.6–6.6) at a base opacity of about 0.18, drawn under every label's halo. Inter-cluster edges in Cluster-separated mode stay fainter. A selection still highlights its links at full strength. Every link the threshold kept is still drawn.

### Cluster-separated layout
- Each Multi-Tag Cluster's region runs the same ForceAtlas2 + clamp + label-aware pass on its members, with the Cluster Center pinned in the middle, starting from the members' global positions.
- A region's size comes from the total area of its members' node-plus-label boxes times a fill factor of about 2.5, instead of 90·√members.
- The one-tag pool is a grid whose cells are as wide as its longest label.
- Packing keeps today's shelf packing, aimed at the real canvas aspect. Exports pack for the reference canvas.
- Region titles keep their constant size.

### Tidy (was Re-layout)
- The Re-layout button becomes **Tidy**. It starts from the current positions including dragged nodes, pins the dragged nodes, and re-runs the same ForceAtlas2, clamp and label-aware pass on the visible network.
- Its positions are view-history-dependent, as Re-layout's are today. The export still marks them `layout_source=relayout`.

### Opening old exports
- An export with `layout_source=default`: positions are computed again by the new layout.
- An export with `layout_source=relayout`: its stored global coordinates are kept, shape preserved, rescaled into the reference box, clamped and passed through the label-aware pass. So an old file with far-out tags opens readable.

### Checks
- **Geometry test** (Python): for each dataset's default state, both layouts, at 1440 × 900 and 1280 × 800 canvases, compute the fit zoom and assert:
  - every node-plus-label box at 11.5 px is disjoint from every other;
  - the smallest node is ≥ 14 px;
  - no tag is outside the clamp.

  The same checks run after Tidy.
- **Invariance test** (see "Analysis and layout are separate").
- **Performance:** one layout of a default state takes ≤ 300 ms on the server; the loosest state takes ≤ 1.5 s.
- **Browser check** on the real Build, at both sizes, in both layouts and after Tidy, with screenshots described in the issue comments.

### Documentation
- The "Layout positions" entry in `docs/user-guide/03-metric-reference.md` describes the new layout and says: positions are computed after, and never used by, any metric; gravity, canvas size and Tidy change only coordinates.
- ADR 0002: "Layout is downstream of analysis".

## Overrides
- [App readability spec](../app-readability/spec.md):
  - "Layout": the Global layout is no longer computed on the loose network "so moving a threshold slider never moves the graph". It is computed on the visible network and moves (animated) when the visible set changes. The Cluster-separated region side no longer grows with √members.
  - "Labels": every label is a constant-size label. The rule "every other label scales with zoom and is hidden below 7 px" is gone. White backgrounds are now only for selected and highlighted labels; every other label has a halo.
  - "Renderer": the render-time stretch of x by the canvas aspect ratio is removed.
  - "Layout" and "Motion": Re-layout becomes Tidy.
  - The B look's edges at opacity 0.3 become about 0.18, with the thinner width range.
- [Steam Success Study spec](../steam-success-study/spec.md) "Global positions" (§580): positions are a pure function of (dataset, Minimum Months Filter, Clustering Weight, seed, visible set, canvas size), from ForceAtlas2 on the visible network started from the loose spring layout, so thresholds do move the graph.

## Out of scope
- Any change to clustering, metrics, the Network State, `state_id`, the export schema or `schema_version`.
- Hiding links the thresholds kept (top-k edges or display cutoffs), and edge bundling.
- Measuring label widths in the browser.
- The WebGL renderer and continuous physics.

## Issues

- [01: Layout downstream of analysis](issues/01-layout-downstream-of-analysis.md)
- [02: ForceAtlas2 Global layout with gravity and clamp](issues/02-forceatlas2-global-layout.md)
- [03: Label-aware spacing and the canvas-sized layout](issues/03-label-aware-canvas-layout.md)
- [04: Every label shown, and lighter edges](issues/04-all-labels-and-edges.md)
- [05: Cluster-separated regions sized by label area](issues/05-cluster-separated-label-regions.md)
- [06: Tidy, and opening old exports](issues/06-tidy-and-old-exports.md)
- [07: Documentation](issues/07-documentation.md)
