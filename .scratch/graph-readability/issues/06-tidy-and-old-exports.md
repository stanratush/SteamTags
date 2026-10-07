# 06: Tidy, and opening old exports

**What to build:** Re-layout becomes Tidy, which settles the graph around the nodes you dragged and never throws a tag away. Exports made with the old layout open readable.

**Blocked by:** 03

**Status:** done

Spec: [Graph readability spec](../spec.md): "Tidy (was Re-layout)", "Opening old exports".

- [x] The Re-layout button becomes **Tidy** (same place, new label and tooltip). It starts from the current positions including dragged nodes, pins the dragged nodes, and re-runs ForceAtlas2, the clamp and the label-aware pass on the visible network.
- [x] A Tidy result is exported as today (`layout_source=relayout`).
- [x] Opening an export:
  - `layout_source=default`: positions are computed by the new layout;
  - `layout_source=relayout`: the stored global coordinates are kept, shape preserved, rescaled into the reference box, clamped and passed through the label-aware pass.
- [x] Tests:
  - The issue 03 geometry test after Tidy, on every dataset's default state.
  - Pinned dragged nodes stay exactly where they were dropped.
  - An old-style Re-layout export with tags about 1,000 units out opens with every tag inside the clamp and no overlapping boxes.
- [x] Browser check: Tidy on each dataset keeps the first-fit zoom the same or larger. Describe it in the comments.

## Comments

- 2026-10-07: Done. `tidy(inp, current, canvas, pinned=..., zoom=...)`:
  1. Run ForceAtlas2 from the current positions (dragged ones included).
  2. Turn, scale and move the result back onto the current positions (Procrustes, no mirroring), so the view keeps its frame.
  3. Put the dragged nodes back exactly; run the clamp (which never moves them) and the label-aware pass, with the dragged nodes pinned and labels spaced for the current zoom.

  `graph.js` reports the nodes dragged in the Global layout on a new `graph-dragged` store `{basis, positions}`; `do_tidy` pins them only under the same basis. The button reads **Tidy** (same id `relayout-btn`, title "Settle the graph around the nodes you dragged; positions only"). Its store also keeps the zoom, so the canvas culls correctly, and it holds only while the basis and the visible tags are unchanged. Exports still say `layout_source=relayout`.
- Opening an export with `layout_source=relayout` stores its positions with `restore: true`. `relayout_positions` then runs `restore`: the shape is kept with one scale for both axes, so the main component fits the reference canvas, then `_place` (clamp, label-aware pass, zoom search) runs. Tests: an old-style layout with the unlinked tags 1,100 units out comes back inside the clamp with no overlap and its left-to-right order kept, and the same through `do_open` and the app.
- Browser check, real Build, Global, 1440 × 900, Tables and Inspector closed. Before Tidy and after it, all five datasets show every label, no visible overlap, first fit 1.00 → 1.00 (the same, never smaller). On Overall, Puzzle and Strategy I dragged the best-linked tag by (+90, −45) first; it came back from the server at exactly the dropped coordinates.
- 2026-10-07, after code review:
  - Tidy's alignment is now weighted: the dragged nodes together count three times all the others. The rest settles around where they were dropped rather than where ForceAtlas2 moved them. Test: `test_tidy_settles_the_others_around_where_nodes_were_dropped`.
  - The label-aware pass spreads from the free boxes' own centre, so a spread no longer drags them away from pinned ones.
