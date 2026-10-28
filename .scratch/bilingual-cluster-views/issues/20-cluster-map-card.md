# 20: Cluster map card

**What to build:** a "Cluster map" toggle in the canvas's top-right overlay. It opens a floating card that draws one bubble per Cluster and a link per connected pair, weighted by Connection Ratio / γ. `graph.js` draws it from a small store. Bubbles and links select.

**Blocked by:** 16, 18

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Cluster map card", "Architecture". Prototype: [cluster connections, variant C's card](../prototypes/07-cluster-connections/PROTOTYPE-cluster-connections.html).

- [ ] **`cluster-connections` store**: the recompute writes the `cluster_connections.csv` rows (and γ) to it. Nothing else changes in the payload.
- [ ] **The card** is a transient overlay, like the Edge appearance card. Opening or closing it never changes the canvas, the layout or the fit. Whether it is open is kept for the session only.
- [ ] **What it draws**:
  - one bubble per Cluster, area by tag count, at its tags' centroid (Global) or its region's centre (Cluster-separated), nudged apart;
  - the pool as a grey bubble labelled with its tag count, not clickable;
  - only pairs with a link, 0.6–7.6 px by ratio / γ, in `#3b2f6b`, with the selected pair in the selection blue.
- [ ] **Selection**: a bubble selects the Cluster and a link selects the pair. Any selection, from anywhere, lights up in the card, with the ratio written on the selected pair and on the selected Cluster's links.
- [ ] It is redrawn in the browser on a layout or Network State change, from positions `graph.js` already holds.
- [ ] Words from `ui-words` (English).
- [ ] **Guide** (`02-app-controls.md`): the Cluster quality entry gains a **Cluster map** paragraph. The toggle's help key points to it.
- [ ] Tests:
  - Browser: opening or closing the card leaves the reported canvas unchanged.
  - A card link selects the pair within 50 ms, with no `graph-data` request and no layout.
  - A matrix selection lights up in the card.
  - The bubbles move with a layout switch.
