# 18: Connections in the Inspector, the pair view and the pair highlight

**What to build:** the Inspector becomes the home of every connection detail. A Cluster gets a **Connections** ranking. A new selection kind, `pair`, gets its own Inspector view and a canvas highlight drawn by `graph.js`. A link between Clusters offers "show this pair". The matrix (issue 19) and the map card (issue 20) only select into this.

**Blocked by:** 13, 15, 17

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Cluster connections view" (Inspector, Canvas, Numbers on screen, Architecture, Guide). Prototype: [cluster connections, variant B](../prototypes/07-cluster-connections/PROTOTYPE-cluster-connections.html).

- [ ] **The Cluster's Connections section** (after Members, and after Games if issue 21 has landed): one row per partner from issue 17's rows.
  - Order: ratio high to low, ties by weight, zero-edge partners at 0, then rows with an empty ratio.
  - The pool is labelled as the pool.
  - Columns: Ratio (with a 0…γ bar marking 1), Share, total in the Clustering Weight, links. Under Lift, also the shared-game total and ratio, labelled "not tied to the clustering; can exceed γ".
  - The reference line reads "1 = as their total link weight predicts; γ is the most it can reach".
  - A row selects the pair.
- [ ] **Pair view** (server-built, like the other Inspector views):
  - both swatches and names; the ratio with γ; both shares; the total and the link count (plus the shared-game total and ratio under Lift); the reference line;
  - "Links between them": the tag in each Cluster, shared games and Lift, sorted by shared games. Links hidden by Hide links below are marked "hidden from the drawing". A row selects that link.
  - An empty ratio names its case.
- [ ] **Link Inspector**: a link whose ends are in two different groups offers "show this pair". A link opened from a pair's list shows "← C1 ↔ C2", which returns to the pair.
- [ ] **Selection kind `pair`** travels the same event path as region taps. It survives a layout switch.
- [ ] **Canvas**: `graph.js` dims every other tag and link and fits to both Clusters. The pair's links keep their colour mode and become opaque, in both layouts. Hidden links stay hidden. A Cluster selection is unchanged (dim and zoom).
- [ ] **Numbers**: Ratio to 2 decimals; Share as a whole percent (one decimal below 1 %); totals in the weight's format (shared games whole, Lift to 1 decimal). All through `tx.num`.
- [ ] All text goes through `tx`, in English. The Ratio and Share headers and tooltips point to the Connection Ratio and Connection Share anchors.
- [ ] **Guide** (`02-app-controls.md`): the Inspector entry gains the Cluster's **Connections** section and the **pair view**.
- [ ] Tests:
  - Unit: the ranking follows the spec's order on a fixture with a zero pair and an empty ratio. The pair view's numbers equal the CSV row.
  - Browser: a pair picked from a ranking row is highlighted within 50 ms and shown in the Inspector within 300 ms, with no `graph-data` request and no layout.
  - "show this pair" and "← C1 ↔ C2" round-trip.
  - The selection survives a layout switch.
