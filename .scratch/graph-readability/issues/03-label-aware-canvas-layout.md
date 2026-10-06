# 03: Label-aware spacing and the canvas-sized layout

**What to build:** the layout leaves room for every label, sized for the canvas the viewer actually has, so at the first fit every label fits at 11.5 px without overlapping.

**Blocked by:** 02

**Status:** done

Spec: [Graph readability spec](../spec.md): "Label-aware spacing and canvas size", "Checks".

- [x] Label widths in Python, from a fixed per-character width table for the system UI font at 11.5 px, rounded up about 10 %.
- [x] A label-aware overlap-removal pass replaces node-only overlap removal. Each node plus its label below it (centred) is one box; every pair of boxes stays at least the gap apart. It runs after ForceAtlas2 and the clamp, is deterministic and always ends without an overlap.
- [x] `graph.js` reports the free area's pixel width and height, rounded to about 10 % steps, instead of the aspect only. Python lays out so that one model unit is one screen pixel at the first fit.
- [x] Exports use the reference canvas (the graph area of a 1440 × 900 Workbench).
- [x] The render-time 1.6× x-stretch is removed from `graph.js`.
- [x] Small sets: neighbours are never more than about 3× the spacing their boxes need, and the first fit never zooms past 100 %.
- [x] Large sets: the extent grows beyond the canvas. The first fit still shows everything; labels are culled by rank (issue 04).
- [x] Tests:
  - **Geometry:** for each dataset's default state, Global layout, 1440 × 900 and 1280 × 800 canvases, at the computed fit zoom: every node-plus-label box at 11.5 px is disjoint from every other; the smallest node is ≥ 14 px; no tag is outside the clamp.
  - A 5-tag state fits at zoom ≤ 1.
  - The loosest state is laid out within 1.5 s and has no overlapping boxes.

## Comments

- 2026-10-07: Done, at the Goal canvases of the spec's amendment (1116 × 678 and 956 × 561: the Tables and Inspector closed). `label_width` uses the bold Segoe UI widths at 11.5 px measured in the browser, × 1.1; characters outside the table use their base letter (NFKD) or one em. `separate` replaces node-only overlap removal in the Global layout: node-plus-label boxes, pushed apart along the axis of least overlap (vertical overlap weighted by the canvas aspect, so a wide canvas grows the layout sideways), the clamp kept every round. `global_layout` searches the zoom: it starts where the boxes would cover 40 % of the canvas, scales the ForceAtlas2 shape to 70 % of the canvas at that zoom (capped so every main-component tag has a neighbour within 3× the room their boxes need), and lowers the zoom until the result fits, down to 0.55. A larger set keeps its labels spaced for 0.55 and fits further out (`Layout.zoom` says which; issue 04 culls below it).
- Real Build `20261006T062622Z-7a23ae9f`, default states, Global, checked with the test's geometry functions (`real.py` in the session scratchpad):

  | Dataset | 1116 × 678: fit zoom, smallest node, time | 956 × 561: fit zoom, smallest node, time |
  | --- | --- | --- |
  | Overall | 1.00, 27.4 px, 122 ms | 1.00, 27.4 px, 119 ms |
  | Puzzle | 1.00, 26.5 px, 133 ms | 1.00, 26.5 px, 152 ms |
  | RPG | 1.00, 26.5 px, 113 ms | 1.00, 26.5 px, 138 ms |
  | Strategy | 1.00, 26.5 px, 138 ms | 1.00, 26.5 px, 168 ms |
  | Simulation | 1.00, 26.5 px, 120 ms | 0.91, 24.1 px, 249 ms |

  No overlapping box and no tag outside the clamp in any of them. Loosest states (229–251 tags): 650–850 ms, labels spaced for 0.55, first fit 0.32–0.41.
- `graph.js` reports `{w, h}` on `graph-canvas`, each side rounded down to 1116·1.08^k / 678·1.08^k (within about 1 %), so the 1440 × 900 window lays out exactly like an export. The server floors a transitional canvas at 320 × 240. The fit includes labels (constant on screen) and never passes 100 %; the x-stretch is gone. Browser: Overall at 1440 × 900 reports 1116 × 678, design zoom 1, first fit 1.
