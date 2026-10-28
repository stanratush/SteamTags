# Cluster connections view
Type: prototype
Status: resolved
Blocked by: 06

## Question

How does a researcher explore Cluster-to-Cluster connections visually and inspect the connections between any two Clusters? This is a HITL prototype (`prototype`, in `prototypes/07-cluster-connections/`), working from [Inter-cluster measures](06-inter-cluster-measures.md).

- Candidate overviews: a cluster × cluster matrix or heatmap, a cluster-level graph (one node per Cluster, edge width as Connection Ratio), and highlighting on the existing canvas (pick a Cluster and the others shade by strength).
- Per-cluster ranking in the Cluster Inspector: every other Cluster with the columns and order fixed in Inter-cluster measures (Connection Ratio, Connection Share, totals, edge count).
- The pair inspector: picking two Clusters shows the edges between them (tag pairs, shared games, Lift) and highlights them on the canvas, with rows that select an edge, as connected-tag rows do today.
- Where it sits (the Inspector, the Cluster quality tab, or a new tab), how it behaves in the Global and the Cluster-separated layout, and the cost against the [Graph interaction spec](../../graph-interaction/spec.md) budgets.

## Answer

Settled with the researcher on 2026-10-28. The researcher picked variant B of the [prototype](../prototypes/07-cluster-connections/PROTOTYPE-cluster-connections.html), with a button that opens variant C's card, then accepted every recommendation in two grilling rounds. The prototype ran on four real Network States (Overall, Puzzle, Overall under Lift, Overall at γ = 2.5 with 14 Multi-Tag Clusters); ticket 06's columns were computed in its `dump_state.py` only.

- **One home per selection: the Inspector.** The matrix and the card give an overview and select; they never show detail.
  - The Cluster Inspector gains a **Connections** section: the ranking from [Inter-cluster measures](06-inter-cluster-measures.md) (Ratio with a 0…γ bar marking 1, Share, total in the Clustering Weight, links; under Lift also the shared-game total and the shared-game ratio, labelled "not tied to the clustering; can exceed γ"), with the reference line "1 = as their total link weight predicts; γ is the most it can reach". A row selects the pair.
  - A new **pair** view: both swatches and names, the Connection Ratio with γ, both Connection Shares, the total, the link count (under Lift also the shared-game total and ratio), the reference line, then "Links between them" (tag in each Cluster, shared games, Lift; by shared games). A row selects that link. An empty ratio says why (one of the three cases in 06).
  - The link Inspector: a link between two Clusters offers "show this pair"; a link opened from a pair's list shows "← C1 ↔ C2".
- **Connections matrix**, in the Cluster quality tab, the tab's full width:
  - Cells: **Ratio** (default, symmetric) or **Share (row → column)**, each row adding to 100%. A view choice that resets to Ratio when the dataset changes. Under Lift the shared-game ratio is only in the cell tooltip and the pair view, never a cell mode.
  - Colour: one continuous ramp, `#c9ced8` to `#3b2f6b` (the Edge Appearance value ramp), fixed to 0…γ (Share: 0…100 %), with a key strip marking 1 and γ. No bands or thresholds; a value a hair above γ takes the darkest colour and keeps its number.
  - Order: label order C1, C2, …, `one_tag_pool` last as "pool". The diagonal is hatched with the Cluster's tag count; the pool–pool cell holds the "between one-tag clusters" row. The pool's row header is inert (not a Cluster, as today); its cells select.
  - Click a cell: the pair. Click a row header: the Cluster. The selected cell, and the selected Cluster's row and column, are marked. The tooltip gives every number of the pair.
  - A **Matrix | Table** toggle keeps the existing `cluster_connections.csv` grid with its five new columns; its rows select the pair too. Matrix is the default.
  - Many Clusters: it scrolls inside the tab with sticky headers; cells stay at least 40 px. No grouping or cut-off.
- **Pool share** (open in 06): the pool's Connection Share is the pair's weight over all link weight touching the pool's tags, pool–pool links counted once (cut_p = k_p − w_pp), so the pool's shares also add up to 1. The Connection Share guide entry states it as the one special case.
- **Cluster map card**: a "Cluster map" toggle in the canvas's top-right overlay opens a floating card (a transient overlay like the Edge appearance card: opening or closing never changes the canvas, the layout or the fit). The map only: one bubble per Cluster, area by tag count, at its tags' centroid (Global) or its region's centre (Cluster-separated), nudged apart; the pool a grey bubble labelled with its tag count, not clickable; only pairs with a link are drawn, 0.6–7.6 px by ratio / γ in `#3b2f6b`, the selected pair in the selection blue. A bubble or link selects the Cluster or pair; any selection lights up in the card, with the ratio written on the selected and the selected Cluster's links. Redrawn in the browser on a layout or Network State change. Open or closed is not kept; it stays open for the session.
- **Canvas**: a pair dims every other tag and link and fits to both Clusters, like today's Cluster focus. The pair's links keep their Edge Appearance colour mode and become opaque (one colour darkens them), also in the Cluster-separated layout where links between Clusters are faint. Links hidden by "Hide links below" stay hidden and are marked "hidden from the drawing" in the pair's list. A Cluster selection keeps today's dim-and-zoom, plus its matrix row and card bubble; there is no shading of partners by ratio. A selection survives a layout switch.
- **Numbers**: Ratio to 2 decimals, Share as a whole percent (one decimal below 1 %), totals in the Clustering Weight's own format (shared games whole, Lift to 1 decimal). Bulgarian follows the Interface Language rule; the CSV keeps fractions and full precision.
- **Architecture**: the matrix is one escaped HTML block (`data-html`, like the Inspector's long tables), rendered by the existing Cluster quality callback from the rows it already has; no new callback. The recompute also writes those rows to a small `cluster-connections` store, from which `graph.js` draws the card with the positions it already holds. A pair, from a cell, a card link, a table row or a ranking row, is one new selection kind, `pair`, through the same event path as region taps. Its Inspector view is built on the server like the others; the canvas highlight is a `graph.js` restyle. No new canvas payload, nothing re-sent for a highlight.
- **Tests**:
  - Browser: a pair picked from a cell, a card link and a ranking row is highlighted within 50 ms and in the Inspector within 300 ms, with no `graph-data` request and no layout. Opening or closing the card does not change the reported canvas.
  - Unit: each matrix cell equals its `cluster_connections.csv` row; the ranking follows 06's order (ratio high to low, ties by weight, zero pairs then empty ones last); the pool's shares add up to 1.
  - The prototype measured 2–8 ms per highlight on all four states, with 0 payloads and 0 layouts per selection.
- **Guide**: in `02-app-controls.md` the Cluster quality entry gains **Connections matrix** and **Cluster map** paragraphs, and the Inspector entry the Cluster's **Connections** section and the **pair view**. Every Ratio and Share header and tooltip points to the Connection Ratio and Connection Share anchors.
- **Not added**: no new export (the matrix and card are views of `cluster_connections.csv`), no new CONTEXT.md term ("Connections matrix" and "Cluster map" are UI names in the guide), nothing in Analysis Report mode.
