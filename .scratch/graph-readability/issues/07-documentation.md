# 07: Documentation

**What to build:** the user guide describes the new layout and states plainly that positions never touch any result.

**Blocked by:** 02, 03, 04, 05, 06

**Status:** done

Spec: [Graph readability spec](../spec.md): "Documentation", "Overrides".

- [x] The "Layout positions" entry in `docs/user-guide/03-metric-reference.md`, and its row "Layout and Re-layout" in the overview table, describe:
  - ForceAtlas2 on the visible network, with gravity and the clamp;
  - label-aware spacing;
  - the canvas-sized layout and the reference canvas for exports;
  - the label-area regions;
  - Tidy.

  They also include the sentence: "Positions are computed after, and never used by, any metric; gravity, canvas size and Tidy change only coordinates."
- [x] The text no longer says that moving a slider never moves the graph.
- [x] Every user-facing mention of "Re-layout" (user guide, help, running guide) says "Tidy".
- [x] The [App readability spec](../../app-readability/spec.md) and the [Steam Success Study spec](../../steam-success-study/spec.md) §580 point to this spec where it overrides them.
- [x] The guide index tests (`tests/test_guide.py`) still pass.

## Comments

- 2026-10-07: Done. "Layout positions" in `03-metric-reference.md` is rewritten: ForceAtlas2 on the visible network with gravity and the clamp, label-aware spacing, the canvas-sized layout and the 1,116 × 678 reference canvas, label-area regions (best effort, per the spec's amendment), Tidy, and reopening old exports. It carries the required sentence verbatim. The overview row is now "Layout and Tidy". Getting Started now describes every label at a constant size, thresholds and panels moving the graph, and Tidy with dragged nodes. App Controls and Citing say Tidy. Appendix C adds `forceatlas2_layout`. The running guide and the in-app help (which renders these chapters) had no Re-layout text of their own. Override pointers were added to the App readability spec (Renderer, Layout, Labels, Motion) and to the Steam Success Study spec's "Global positions". `tests/test_guide.py`: 22 passed.
