# 04: Grid column headers

**What to build:** the metric columns of the five grids (Clusters, Removal sensitivity, Nodes, Edges, Not in network) show the guide's In short as their header tooltip, and an ⓘ in the header opens the entry.

**Blocked by:** 03

**Status:** ready-for-agent

Spec: [Metric help spec](../spec.md): "Layer 1" (grid headers), "Layer 2".

- [ ] `columns_for` puts the In short lines plus "Column: `name`" in `headerTooltip` for metric columns. Identifier columns keep the schema description.
- [ ] Metric headers show an ⓘ that opens the entry. Clicking the header still sorts.
- [ ] The remaining entries these columns reach (internal edges and densities, cut weight, cluster connections, disconnected clusters, seed spread, seed ranges, tags not in the network, …) have an In short block and `*Why it matters here.*`.
- [ ] Test: every metric column of the five grids resolves to an entry with an In short.
- [ ] Checked in the browser: tooltip, ⓘ to modal and sorting, in the Workbench and in Analysis Report mode.

## Comments
