# 19: Connections matrix in the Cluster quality tab

**What to build:** a **Connections matrix**, Clusters × Clusters, across the full width of the Cluster quality tab. Its cells show the Connection Ratio or the Connection Share on one colour ramp. A **Matrix | Table** toggle keeps today's grid. Cells select pairs and row headers select Clusters.

**Blocked by:** 18

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Connections matrix", "Numbers on screen", "Architecture". Prototype: [cluster connections, variant B](../prototypes/07-cluster-connections/PROTOTYPE-cluster-connections.html).

- [x] **One escaped HTML block** (`data-html`), rendered by the existing Cluster quality callback from the `cluster_connections.csv` rows it already has. No new callback.
- [x] **Cell modes**: **Ratio** (the default, symmetric) or **Share (row → column)**, where each row adds to 100 %. The choice resets to Ratio when the dataset changes. Under Lift the shared-game ratio is only in the tooltip.
- [x] **Colour**: a continuous ramp `#c9ced8` → `#3b2f6b`, fixed to 0…γ (Share: 0…100 %), with a key strip marking 1 and γ. No bands. A value above γ takes the darkest colour and keeps its number. Empty cells are blank and say why in the tooltip.
- [x] **Order and special cells**:
  - C1, C2, … in label order, with the pool last as "pool";
  - the diagonal is hatched with the Cluster's tag count;
  - the pool–pool cell holds the between-one-tag-clusters row;
  - the pool's row header is inert, and its cells select.
- [x] **Selection**: a cell selects the pair and a row header selects the Cluster. The selected cell, and the selected Cluster's row and column, are marked. The tooltip gives every number of the pair.
- [x] **Matrix | Table**: Table shows the existing grid with the five new columns. Its rows select the pair. Matrix is the default.
- [x] **Many Clusters**: it scrolls inside the tab with sticky headers, and cells are at least 40 px.
- [x] Numbers via `tx.num` and words via `tx`, in English.
- [x] **Guide** (`02-app-controls.md`): the Cluster quality entry gains a **Connections matrix** paragraph.
- [x] Tests:
  - Unit: each cell equals its CSV row, in both modes. Share rows add to 100 %.
  - Browser: a pair picked from a cell is highlighted within 50 ms and shown in the Inspector within 300 ms, with no `graph-data` request.
  - A table row selects the same pair.
  - The mode resets on a dataset change.
  - At γ = 2.5 on Overall (14 Multi-Tag Clusters), the matrix scrolls with sticky headers.

## Comments

**2026-10-28, implementation.** Done. Notes:

- `view.connections_matrix` renders both modes' tables and the key strips in one escaped HTML block, inside the existing `quality-detail` output (`state_views`), so a language switch re-renders it like the rest of the tab. `workbench.js` keeps the view choices in the browser, with no callback: Ratio or Share (back to Ratio when the block's dataset changes), and Matrix or Table (a class on `#blk-quality` shows the existing `connections-grid`). The Table's rows select the pair through the existing `select` callback (a new Input there, not a new callback).
- A cell's `data-pair` and a row header's `data-cluster` go through `graph.js`'s instant-selection path. `markMatrix` marks the selected cells (in both tables), and the selected groups' rows and columns.
- **Guide**: the Cluster quality tab is documented in `01-getting-started.md` (chapter 2 has no Cluster quality entry), so the Connections matrix paragraph is there.
- **Browser checks, by hand**:
  - a cell pick was highlighted in 37 ms; the Inspector followed in 312 ms on the first, cold selection and 152 ms warm; the only `graph-data` request is the selection Patch, no payload;
  - Share mode and the Table view switch with no request, and the mode returned to Ratio on a dataset change;
  - a Table row (C1, C4) selected `C1|C4`;
  - at γ = 2.5 on Overall (14 Multi-Tag Clusters and the pool), the matrix scrolls with sticky column and row headers, and cells are ≥ 40 px;
  - no console errors.
