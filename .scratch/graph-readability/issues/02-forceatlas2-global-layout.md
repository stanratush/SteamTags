# 02: ForceAtlas2 Global layout with gravity and clamp

**What to build:** the Global layout is computed on the visible network with ForceAtlas2. Tags with no visible link stay close to the main graph, and no tag can end up far away.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Graph readability spec](../spec.md): "Global layout", "Nodes", "Facts found while grilling".

- [ ] `layout_state` lays out the **visible** network with `nx.forceatlas2_layout`, weighted by the active Clustering Weight, with gravity and hub dissuasion and a fixed seed. It starts from the dataset's loose 244-tag layout, limited to the visible tags.
- [ ] Positions are a pure function of (layout basis, visible set, canvas). The same inputs give identical positions.
- [ ] Hard clamp after ForceAtlas2: no tag is farther from the main component's centre than its radius plus about 1.5 label heights.
- [ ] Node diameters use the larger range (about 18 + 30·√ratio). Final constants are tuned with issue 03's geometry test.
- [ ] The app animates moves when the visible set changes (thresholds, hidden or removed tags), using the existing 350 ms move. Dragged positions keep their current rule.
- [ ] Node overlap removal still runs at the end, so nothing overlaps until issue 03 replaces it with the label-aware pass.
- [ ] Tests:
  - On every dataset's default state, every tag is within the clamp, and the extent is at most about 1.3× the main component's extent.
  - Same inputs give identical positions.
  - A threshold change moves positions; the same thresholds give the same positions again.
  - Performance: a default state's layout takes ≤ 300 ms; the loosest state takes ≤ 1.5 s.
