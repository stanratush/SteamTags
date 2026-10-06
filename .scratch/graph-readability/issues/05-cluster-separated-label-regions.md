# 05: Cluster-separated regions sized by label area

**What to build:** the Cluster-separated layout has the same readability as Global: every label fits inside its cluster's region at the first fit.

**Blocked by:** 03

**Status:** ready-for-agent

Spec: [Graph readability spec](../spec.md): "Cluster-separated layout".

- [ ] Each Multi-Tag Cluster's region runs ForceAtlas2 + clamp + the label-aware pass on its members, with the Cluster Center pinned in the middle, starting from the members' global positions.
- [ ] A region's size is the total area of its members' node-plus-label boxes times a fill factor of about 2.5, instead of 90·√members.
- [ ] The one-tag pool is a grid whose cells are as wide as its longest label.
- [ ] Shelf packing is aimed at the real canvas's aspect; exports pack for the reference canvas.
- [ ] Tests:
  - The issue 03 geometry test, for the Cluster-separated layout, at both canvas sizes.
  - The Center sits at its region's centre.
  - The packed area is at most 1.5 × the sum of the region areas.
- [ ] Browser check on the real Build, Cluster-separated, both sizes, every dataset's default state. Describe it in the comments.
