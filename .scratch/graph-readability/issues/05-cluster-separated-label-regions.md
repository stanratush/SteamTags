# 05: Cluster-separated regions sized by label area

**What to build:** the Cluster-separated layout has the same readability as Global: every label fits inside its cluster's region at the first fit.

**Blocked by:** 03

**Status:** done

Spec: [Graph readability spec](../spec.md): "Cluster-separated layout".

- [x] Each Multi-Tag Cluster's region runs ForceAtlas2 + clamp + the label-aware pass on its members, with the Cluster Center pinned in the middle, starting from the members' global positions.
- [x] A region's size is the total area of its members' node-plus-label boxes times a fill factor of about 2.5, instead of 90·√members.
- [x] The one-tag pool is a grid whose cells are as wide as its longest label.
- [x] Shelf packing is aimed at the real canvas's aspect; exports pack for the reference canvas.
- [x] Tests:
  - The issue 03 geometry test, for the Cluster-separated layout, at both canvas sizes.
  - The Center sits at its region's centre.
  - The packed area is at most 1.5 × the sum of the region areas.
- [x] Browser check on the real Build, Cluster-separated, both sizes, every dataset's default state. Describe it in the comments.

## Comments

- 2026-10-07: Done, with the Goal relaxed to best effort for this layout (decided with the user; see the spec's second amendment). A region needs at least 2.5× its members' boxes and packing adds 1.2–1.9×, so it needs about twice the Global layout's room.
- Each Multi-Tag Cluster runs ForceAtlas2 on its members from their Global positions. The other members' centroid is moved onto the Center, each axis is scaled to 70 % of a square of 2.5 × the members' node-plus-label area, then come the Global clamp (on the cluster's own main component) and `separate` with the Center pinned. The region is that square, or larger when the members need it, with the Center in the middle. The one-tag pool is a grid of cells as wide as its longest label. Shelf packing tries label order and tallest-first and keeps the tighter one, aimed at the canvas aspect; `REGION_GAP` is now 16. Titles keep 22 px on screen. The zoom search starts where the members' boxes would cover 30 % of the canvas and lowers the zoom (by the square root of each shortfall) down to 0.55 (`Layout.separated_zoom`).
- The canvas culls a label that covers a higher-ranked label or another tag's node. It measures labels with Cytoscape's label metrics plus the halo, so fewer labels are hidden than with `boundingBox()`. The app computes the Cluster-separated layout only when it is shown.
- Browser check, real Build, Cluster-separated, Tables and Inspector closed. Measured at the target positions; "visible overlaps" counts a shown label covering another label or another tag's node:

  | Dataset | 1440 × 900 | 1280 × 800 (canvas 957 × 538) |
  | --- | --- | --- |
  | Overall | zoom 0.85, all 59 labels, smallest node 23.3 px | 0.54, all 59, 14.7 px |
  | Puzzle | 0.79, all 58, 20.8 px | 0.54, all 58, 14.2 px |
  | RPG | 0.48, 6 of 67 culled, 12.6 px | 0.42, 12 culled, 11.1 px |
  | Strategy | 0.54, all 65, 14.2 px | 0.49, 2 culled, 13.1 px |
  | Simulation | 0.45, 9 culled, 11.8 px | 0.45, 7 culled, 11.9 px |

  No visible overlap anywhere. Screenshot (Overall, 1440 × 900): three tinted regions C1 · 26, C2 · 18, C3 · 11 in a row, each with its diamond Center in the middle and every member's label readable below its node; the four one-tag clusters sit in a small grid underneath.
- Timing on the real Build: the Global layout alone takes 100–170 ms per default state; with the Cluster-separated layout (which starts from it), 245–500 ms. That is over the 300 ms budget in some cases. The perf test on the test Build passes.
- 2026-10-07, after code review:
  - A region's clamp never moves its pinned Center.
  - A region is clamped only when its own main component holds at least half its members. Before, a Center outside the linked core of a mostly unlinked cluster flew off to about 1e15, or the pass never settled.
  - ForceAtlas2 is skipped for fewer than two tags; a one-tag network gave NaN, and Tidy then failed.

  Tests: `test_a_center_outside_its_clusters_linked_core_stays_in_the_middle_of_its_region`, `test_a_one_tag_network_is_laid_out_and_tidied`.
