# 20: Cluster map card

**What to build:** a "Cluster map" toggle in the canvas's top-right overlay. It opens a floating card that draws one bubble per Cluster and a link per connected pair, weighted by Connection Ratio / γ. `graph.js` draws it from a small store. Bubbles and links select.

**Blocked by:** 16, 18

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Cluster map card", "Architecture". Prototype: [cluster connections, variant C's card](../prototypes/07-cluster-connections/PROTOTYPE-cluster-connections.html).

- [x] **`cluster-connections` store**: the recompute writes the `cluster_connections.csv` rows (and γ) to it. Nothing else changes in the payload.
- [x] **The card** is a transient overlay, like the Edge appearance card. Opening or closing it never changes the canvas, the layout or the fit. Whether it is open is kept for the session only.
- [x] **What it draws**:
  - one bubble per Cluster, area by tag count, at its tags' centroid (Global) or its region's centre (Cluster-separated), nudged apart;
  - the pool as a grey bubble labelled with its tag count, not clickable;
  - only pairs with a link, 0.6–7.6 px by ratio / γ, in `#3b2f6b`, with the selected pair in the selection blue.
- [x] **Selection**: a bubble selects the Cluster and a link selects the pair. Any selection, from anywhere, lights up in the card, with the ratio written on the selected pair and on the selected Cluster's links.
- [x] It is redrawn in the browser on a layout or Network State change, from positions `graph.js` already holds.
- [x] Words from `ui-words` (English).
- [x] **Guide** (`02-app-controls.md`): the Cluster quality entry gains a **Cluster map** paragraph. The toggle's help key points to it.
- [x] Tests:
  - Browser: opening or closing the card leaves the reported canvas unchanged.
  - A card link selects the pair within 50 ms, with no `graph-data` request and no layout.
  - A matrix selection lights up in the card.
  - The bubbles move with a layout switch.

## Comments

**2026-10-28, implementation.** Done. Notes:

- The `cluster-connections` store is the recompute's last output: the rows, γ, and the Clusters' label, size and kind. `graph.js` `mapData` (clientside) takes it with the `ui-words` store's `map` words. `drawMap` draws the card as SVG:
  - bubbles at the members' centroid (Global) or the region's centre (Cluster-separated), mapped into the card and nudged apart;
  - the pool as a grey bubble with its count, not clickable;
  - a line for each pair with a link, 0.6–7.6 px by ratio / γ.

  It redraws on a new payload (after the move), on every selection (`applySelection` passes the selection being drawn) and when the store changes. Open or closed is kept in `sessionStorage`, so it lasts the browser session only.
- **Guide**: `### Cluster map` under "Reading the graph" in `02-app-controls.md`, where the card's title term points (`graph.cluster_map`). The `GRAPH_ENTRIES` test lists it. Chapter 2 has no Cluster quality entry to host it.
- **Browser checks, by hand**:
  - opening the card left the reported canvas and the viewport unchanged;
  - a card line selected its pair in 37–46 ms warm (73 ms on the first, cold click), with no payload and no layout (the selection Patch only);
  - a matrix pick (`C2|C3`) lit up on the map, and a bubble selected C1, with the ratio on C1's lines;
  - the bubbles moved with the layout switch;
  - no console errors.
