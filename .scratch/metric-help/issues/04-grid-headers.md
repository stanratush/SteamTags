# 04: Grid column headers

**What to build:** the metric columns of the five grids (Clusters, Removal sensitivity, Nodes, Edges, Not in network) show the guide's In short as their header tooltip, and an ⓘ in the header opens the entry.

**Blocked by:** 03

**Status:** done

Spec: [Metric help spec](../spec.md): "Layer 1" (grid headers), "Layer 2".

- [x] `columns_for` puts the In short lines plus "Column: `name`" in `headerTooltip` for metric columns. Identifier columns keep the schema description.
- [x] Metric headers show an ⓘ that opens the entry. Clicking the header still sorts.
- [x] The remaining entries these columns reach (internal edges and densities, cut weight, cluster connections, disconnected clusters, seed spread, seed ranges, tags not in the network, …) have an In short block and `*Why it matters here.*`.
- [x] Test: every metric column of the five grids resolves to an entry with an In short.
- [x] Checked in the browser: tooltip, ⓘ to modal and sorting, in the Workbench and in Analysis Report mode.

## Comments

- 2026-10-08: Done. `view.column_defs` gives every metric column of every grid it builds (the five named grids, plus the three Cluster quality grids whose entries the issue lists: connections, null model, seed noise) `headerTooltip` = the entry's In short lines and "Column: name (file)", and an ⓘ through `headerComponentParams.innerHeaderComponent` = `MetricHeader`, a small React component in `workbench.js` (`dashAgGridComponentFunctions`). A header `template` was tried first, but dash-ag-grid blocks template strings unless `dangerously_allow_code` is on. The ⓘ sits inside the label that sorts, so `workbench.js` takes its pointerdown, click and Enter in the capture phase; the rest of the header still sorts. On hover the header shows ag-grid's tooltip (`white-space: pre-line`); on keyboard focus the ⓘ shows the same lines in the app's tooltip. `help.column_has_help` decides which columns get help: not the ids-and-names entry's columns, not tag id lists, and not row labels that the schema files under a metric's entry (`source_cluster`, `target_cluster`, `is_intra_cluster`, `appids`, `cluster_a`, `cluster_b`, `seed`, `replicate`, `noise_seed_index`); those keep the schema description. `help.column_help` returns the tip and target for both the Inspector and the grids. The Removal sensitivity grid's joined `membership_stability` column has the same help. Guide: 8 entries got In short and *Why it matters here.* (Layout positions, Tags not in the network, Disconnected clusters, Internal edges, Cluster connections, Seed spread, Seed range, Run order). After the two-axis review: Cluster connections' weight is the active weight, not shared games; only edge density is a share; the seed spread is a scale, not a cut-off; glossary terms and study-use Here lines fixed. Tests: every grid header with an ⓘ has an In short tooltip ending in its Column line and an entry with Why it matters; named metric columns have the ⓘ and named ids and row labels do not. Checked in the browser: the ⓘ opens the entry by click and Enter without sorting, clicking the name sorts, the hover tooltip shows the lines, focus shows them too, and Analysis Report mode's grids have the ⓘ.
