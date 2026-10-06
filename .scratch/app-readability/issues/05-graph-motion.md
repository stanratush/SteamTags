# 05: Graph motion

**What to build:** short, purposeful animations. Nodes glide to new positions, tags fade in and out, selecting a tag fades the rest with a short pulse on the tag, and zoom and pan animate. All motion is off under reduced motion.

**Blocked by:** 01, 02, 03

**Status:** done

Spec: [App readability spec](../spec.md): "Motion", "Layout" (dragging).

- [x] When the dataset is the same and positions change, nodes move over about 350 ms, ease-in-out, while the fit animates to the final box at the same time. This covers changes to the Minimum Months Filter, Clustering Weight, seed, Re-layout, the layout switch, and algorithm or γ in Cluster-separated mode.
- [x] Tags that enter fade in; tags that leave fade out and are then removed; colour changes cross-fade. A dataset change only fits (animated), with no moves.
- [x] Selection:
  - a tag dims everything but its closed neighbourhood and pulses briefly;
  - an edge dims everything but itself and its two tags;
  - a cluster dims everything but its members;
  - a background click clears the selection.
- [x] Fit, focus cluster and search-to-tag animate zoom and pan.
- [x] Under `prefers-reduced-motion: reduce`, every one of these is instant, as is the bottom sheet from 02. There is no in-app toggle.
- [x] Dragging: nodes can be dragged. Dragged positions are kept while the layout basis is unchanged, dropped when the dataset, Minimum Months Filter, Clustering Weight or seed changes, and never exported.
- [x] Browser checks with and without emulated reduced motion: no animation runs continuously, and the CPU is idle when nothing changes.

## Comments

**2026-10-06 (implemented):** All motion lives in `graph.js`: moves animate positions (350 ms, ease-in-out) while the fit animates to the final box; tags and edges leaving get class `leaving`, fade out and are removed (and are taken back if they return mid-fade); entering ones fade in to their stylesheet opacity; colour changes and dimming cross-fade through Cytoscape style transitions, whose duration follows `prefers-reduced-motion` (also when it changes while open). A new dataset only fits, animated. Selection dims through classes (`dim`, `nb`) and the tag pulses once per new selection. Fit, focus and a new `center` view command (for issues 06 and 07) animate. Dragged positions are kept per layout in unstretched units and used only while the payload's new `basis` is unchanged and the layout still sends the same target for that node, so they survive threshold changes and drop on dataset, Minimum Months Filter, weight, seed, Re-layout or a Cluster-separated re-pack. Browser checks: in the app, layout switch, threshold changes, selection dims, background clear, drag kept across a threshold change and dropped on a seed change, and no frames drawn while idle. The in-app pane was hidden for part of the session, which pauses `requestAnimationFrame`, so the timing checks were also run in headless Chrome over the DevTools protocol with a harness that loads the vendored Cytoscape.js and `graph.js` (with and without `--force-prefers-reduced-motion`): with motion everything settles within 760 ms and draws 0 frames while idle; with reduced motion nothing animates.
