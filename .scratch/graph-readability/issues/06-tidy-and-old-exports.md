# 06: Tidy, and opening old exports

**What to build:** Re-layout becomes Tidy, which settles the graph around the nodes you dragged and never throws a tag away. Exports made with the old layout open readable.

**Blocked by:** 03

**Status:** ready-for-agent

Spec: [Graph readability spec](../spec.md): "Tidy (was Re-layout)", "Opening old exports".

- [ ] The Re-layout button becomes **Tidy** (same place, new label and tooltip). It starts from the current positions including dragged nodes, pins the dragged nodes, and re-runs ForceAtlas2, the clamp and the label-aware pass on the visible network.
- [ ] A Tidy result is exported as today (`layout_source=relayout`).
- [ ] Opening an export:
  - `layout_source=default`: positions are computed by the new layout;
  - `layout_source=relayout`: the stored global coordinates are kept, shape preserved, rescaled into the reference box, clamped and passed through the label-aware pass.
- [ ] Tests:
  - The issue 03 geometry test after Tidy, on every dataset's default state.
  - Pinned dragged nodes stay exactly where they were dropped.
  - An old-style Re-layout export with tags about 1,000 units out opens with every tag inside the clamp and no overlapping boxes.
- [ ] Browser check: Tidy on each dataset keeps the first-fit zoom the same or larger. Describe it in the comments.
