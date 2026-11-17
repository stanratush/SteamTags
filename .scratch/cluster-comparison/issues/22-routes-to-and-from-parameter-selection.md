# 22: Routes to and from Parameter Selection

**What to build:** each dataset row links to Parameter Selection on that dataset, and Parameter Selection gains "Use in Cluster Comparison" beside Apply to Workbench, which puts the highlighted cell into the comparison and switches there. There is still no route between the comparison and the Workbench.

**Blocked by:** 18

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "Moving between modes", the `no_run` source line's "Open Parameter Selection". Decision: ticket [13](13-moving-between-modes.md).

- [ ] **The row link** opens Parameter Selection on that dataset (`ps-dataset`) with its current cell highlighted (`ps-pair`); for a hand-set or no-run dataset, on its pick or with no cell highlighted.
- [ ] **"Use in Cluster Comparison"** · *Използвай в сравнението на клъстери*, always shown beside Apply to Workbench in `app/ps_view.py`. It sets the highlighted cell as that dataset's values (source `cell`; the dataset is included if it was not), resolves and switches mode.
- [ ] Enabled under Apply to Workbench's rule (a cell with a Selected Partition); **disabled when Parameter Selection's current settings differ from the comparison's shared settings** (including a shown defining Tag), with the spec's tooltip in en and bg.
- [ ] Its `?` uses `selection.use_in_comparison`.
- [ ] No "Open in Workbench", and the Workbench's values are never sent in.
- [ ] Tests: the row link lands on the right dataset and cell for each source; the button is disabled with no Selected Partition, disabled with different settings (and a shown defining Tag), enabled otherwise; using it sets source `cell`, includes an excluded dataset and switches mode.
