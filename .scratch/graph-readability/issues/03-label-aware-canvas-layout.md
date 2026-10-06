# 03: Label-aware spacing and the canvas-sized layout

**What to build:** the layout leaves room for every label, sized for the canvas the viewer actually has, so at the first fit every label fits at 11.5 px without overlapping.

**Blocked by:** 02

**Status:** ready-for-agent

Spec: [Graph readability spec](../spec.md): "Label-aware spacing and canvas size", "Checks".

- [ ] Label widths in Python, from a fixed per-character width table for the system UI font at 11.5 px, rounded up about 10 %.
- [ ] A label-aware overlap-removal pass replaces node-only overlap removal. Each node plus its label below it (centred) is one box; every pair of boxes stays at least the gap apart. It runs after ForceAtlas2 and the clamp, is deterministic and always ends without an overlap.
- [ ] `graph.js` reports the free area's pixel width and height, rounded to about 10 % steps, instead of the aspect only. Python lays out so that one model unit is one screen pixel at the first fit.
- [ ] Exports use the reference canvas (the graph area of a 1440 × 900 Workbench).
- [ ] The render-time 1.6× x-stretch is removed from `graph.js`.
- [ ] Small sets: neighbours are never more than about 3× the spacing their boxes need, and the first fit never zooms past 100 %.
- [ ] Large sets: the extent grows beyond the canvas. The first fit still shows everything; labels are culled by rank (issue 04).
- [ ] Tests:
  - **Geometry:** for each dataset's default state, Global layout, 1440 × 900 and 1280 × 800 canvases, at the computed fit zoom: every node-plus-label box at 11.5 px is disjoint from every other; the smallest node is ≥ 14 px; no tag is outside the clamp.
  - A 5-tag state fits at zoom ≤ 1.
  - The loosest state is laid out within 1.5 s and has no overlapping boxes.
