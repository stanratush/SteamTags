# 21: Editing datasets, shared-setting changes and state across switches

**What to build:** the user can change one dataset's g, s or γ in its row, and change the shared settings in the header; each change re-resolves what it must and keeps what it can. The comparison's view survives every mode switch, and a Build switch starts it fresh.

**Blocked by:** 18

**Status:** done

Spec: [Cluster Comparison spec](../spec.md): "Datasets and their values" (editing, Pair Constraints changed, a cell that vanishes), "Shared settings" (changing one), "Compute and caching" (memo reuse, when cells are read), "Moving between modes" (state survives, Build switch). Decisions: tickets [03](03-per-dataset-defaults.md), [12](12-compute-and-caching.md), [13](13-moving-between-modes.md).

- [x] **Editing in the row:** g and s that name a cell with a Selected Partition select that cell (source `cell`, γ follows); any other pair, or editing γ, makes the dataset "set by hand" (γ as typed). Limits are the Workbench's, not the Parameter Grid's.
- [x] **Pair Constraints changed** in Parameter Selection reach the comparison on its next resolve: a dataset on the pick follows the new pick; a selected cell or hand-set values are kept.
- [x] **A shared-setting change** re-resolves every dataset against the run for the new settings (its pick, or no run); hand edits are lost and a notice says so.
- [x] One dataset's change reuses the others' memo entries; cells are read only when the mode resolves (nothing polls).
- [x] **State survives every mode switch:** included datasets, sources and values, chosen pair and orientation, chosen match, minimum, "show weaker".
- [x] **On a Build switch** the mode stays open and starts fresh, every dataset on its pick.
- [x] New strings (the notice) have bg entries.
- [x] Tests: typing a cell's g/s selects it; typing another pair or γ makes it hand-set; out-of-limit values are refused as in the Workbench; a Pair Constraints change moves a pick dataset only; a shared-setting change resets hand edits and shows the notice; switching to the Workbench and back keeps the whole view; a Build switch resets to picks.
