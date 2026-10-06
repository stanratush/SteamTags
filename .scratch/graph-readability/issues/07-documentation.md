# 07: Documentation

**What to build:** the user guide describes the new layout and states plainly that positions never touch any result.

**Blocked by:** 02, 03, 04, 05, 06

**Status:** ready-for-agent

Spec: [Graph readability spec](../spec.md): "Documentation", "Overrides".

- [ ] The "Layout positions" entry in `docs/user-guide/03-metric-reference.md`, and its row "Layout and Re-layout" in the overview table, describe:
  - ForceAtlas2 on the visible network, with gravity and the clamp;
  - label-aware spacing;
  - the canvas-sized layout and the reference canvas for exports;
  - the label-area regions;
  - Tidy.

  They also include the sentence: "Positions are computed after, and never used by, any metric; gravity, canvas size and Tidy change only coordinates."
- [ ] The text no longer says that moving a slider never moves the graph.
- [ ] Every user-facing mention of "Re-layout" (user guide, help, running guide) says "Tidy".
- [ ] The [App readability spec](../../app-readability/spec.md) and the [Steam Success Study spec](../../steam-success-study/spec.md) §580 point to this spec where it overrides them.
- [ ] The guide index tests (`tests/test_guide.py`) still pass.
