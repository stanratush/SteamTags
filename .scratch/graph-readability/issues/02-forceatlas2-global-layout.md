# 02: ForceAtlas2 Global layout with gravity and clamp

**What to build:** the Global layout is computed on the visible network with ForceAtlas2. Tags with no visible link stay close to the main graph, and no tag can end up far away.

**Blocked by:** 01

**Status:** done

Spec: [Graph readability spec](../spec.md): "Global layout", "Nodes", "Facts found while grilling".

- [x] `layout_state` lays out the **visible** network with `nx.forceatlas2_layout`, weighted by the active Clustering Weight, with gravity and hub dissuasion and a fixed seed. It starts from the dataset's loose 244-tag layout, limited to the visible tags.
- [x] Positions are a pure function of (layout basis, visible set, canvas). The same inputs give identical positions.
- [x] Hard clamp after ForceAtlas2: no tag is farther from the main component's centre than its radius plus about 1.5 label heights.
- [x] Node diameters use the larger range (about 18 + 30·√ratio). Final constants are tuned with issue 03's geometry test.
- [x] The app animates moves when the visible set changes (thresholds, hidden or removed tags), using the existing 350 ms move. Dragged positions keep their current rule.
- [x] Node overlap removal still runs at the end, so nothing overlaps until issue 03 replaces it with the label-aware pass.
- [x] Tests:
  - On every dataset's default state, every tag is within the clamp, and the extent is at most about 1.3× the main component's extent.
  - Same inputs give identical positions.
  - A threshold change moves positions; the same thresholds give the same positions again.
  - Performance: a default state's layout takes ≤ 300 ms; the loosest state takes ≤ 1.5 s.

## Comments

- 2026-10-07: Done. `global_layout(graph, start, sizes, canvas, params)` in `network/layout.py`: `nx.forceatlas2_layout` (200 iterations, lowered to 100 in issue 05 for time, gravity 1, `distributed_action=True` for hub dissuasion, weights scaled to at most 1) from the cached loose layout (`loose_layout`, formerly `global_positions`), the main component scaled to 70 % of the canvas (at most 1.6× stretched per axis), then the clamp, kept during overlap removal. The clamp is per axis: every tag within the main component's half-extent plus 1.5 label heights (`LABEL_HEIGHT = 15` px) of its centre; it is skipped when no two tags are linked. `LayoutParams(gravity, clamp)` exist for the invariance test. Node sizes are 18 + 30·√ratio.
- Timing on the real Build (warm loose layout): default states 76–112 ms, loosest states (229–251 tags, ~7,000 links) 0.7–1.3 s. The test's synthetic large network mimics that shape.
- The app's 350 ms animated move already runs on any position change of the same dataset (`graph.js` `sync`), so a threshold change now moves the graph animated with no JS change.
