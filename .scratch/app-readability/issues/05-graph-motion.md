# 05: Graph motion

**What to build:** short, purposeful animations. Nodes glide to new positions, tags fade in and out, selecting a tag fades the rest with a short pulse on the tag, and zoom and pan animate. All motion is off under reduced motion.

**Blocked by:** 01, 02, 03

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Motion", "Layout" (dragging).

- [ ] When the dataset is the same and positions change, nodes move over about 350 ms, ease-in-out, while the fit animates to the final box at the same time. This covers changes to the Minimum Months Filter, Clustering Weight, seed, Re-layout, the layout switch, and algorithm or γ in Cluster-separated mode.
- [ ] Tags that enter fade in; tags that leave fade out and are then removed; colour changes cross-fade. A dataset change only fits (animated), with no moves.
- [ ] Selection:
  - a tag dims everything but its closed neighbourhood and pulses briefly;
  - an edge dims everything but itself and its two tags;
  - a cluster dims everything but its members;
  - a background click clears the selection.
- [ ] Fit, focus cluster and search-to-tag animate zoom and pan.
- [ ] Under `prefers-reduced-motion: reduce`, every one of these is instant, as is the bottom sheet from 02. There is no in-app toggle.
- [ ] Dragging: nodes can be dragged. Dragged positions are kept while the layout basis is unchanged, dropped when the dataset, Minimum Months Filter, Clustering Weight or seed changes, and never exported.
- [ ] Browser checks with and without emulated reduced motion: no animation runs continuously, and the CPU is idle when nothing changes.

## Comments
