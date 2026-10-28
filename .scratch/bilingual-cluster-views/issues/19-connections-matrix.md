# 19: Connections matrix in the Cluster quality tab

**What to build:** a **Connections matrix**, Clusters × Clusters, across the full width of the Cluster quality tab. Its cells show the Connection Ratio or the Connection Share on one colour ramp. A **Matrix | Table** toggle keeps today's grid. Cells select pairs and row headers select Clusters.

**Blocked by:** 18

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Connections matrix", "Numbers on screen", "Architecture". Prototype: [cluster connections, variant B](../prototypes/07-cluster-connections/PROTOTYPE-cluster-connections.html).

- [ ] **One escaped HTML block** (`data-html`), rendered by the existing Cluster quality callback from the `cluster_connections.csv` rows it already has. No new callback.
- [ ] **Cell modes**: **Ratio** (the default, symmetric) or **Share (row → column)**, where each row adds to 100 %. The choice resets to Ratio when the dataset changes. Under Lift the shared-game ratio is only in the tooltip.
- [ ] **Colour**: a continuous ramp `#c9ced8` → `#3b2f6b`, fixed to 0…γ (Share: 0…100 %), with a key strip marking 1 and γ. No bands. A value above γ takes the darkest colour and keeps its number. Empty cells are blank and say why in the tooltip.
- [ ] **Order and special cells**:
  - C1, C2, … in label order, with the pool last as "pool";
  - the diagonal is hatched with the Cluster's tag count;
  - the pool–pool cell holds the between-one-tag-clusters row;
  - the pool's row header is inert, and its cells select.
- [ ] **Selection**: a cell selects the pair and a row header selects the Cluster. The selected cell, and the selected Cluster's row and column, are marked. The tooltip gives every number of the pair.
- [ ] **Matrix | Table**: Table shows the existing grid with the five new columns. Its rows select the pair. Matrix is the default.
- [ ] **Many Clusters**: it scrolls inside the tab with sticky headers, and cells are at least 40 px.
- [ ] Numbers via `tx.num` and words via `tx`, in English.
- [ ] **Guide** (`02-app-controls.md`): the Cluster quality entry gains a **Connections matrix** paragraph.
- [ ] Tests:
  - Unit: each cell equals its CSV row, in both modes. Share rows add to 100 %.
  - Browser: a pair picked from a cell is highlighted within 50 ms and shown in the Inspector within 300 ms, with no `graph-data` request.
  - A table row selects the same pair.
  - The mode resets on a dataset change.
  - At γ = 2.5 on Overall (14 Multi-Tag Clusters), the matrix scrolls with sticky headers.
