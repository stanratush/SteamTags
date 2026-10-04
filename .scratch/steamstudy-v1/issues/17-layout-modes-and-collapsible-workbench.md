# 17: Layout modes and collapsible Workbench

**What to build:** The researcher can switch the graph between the Global layout and a Cluster-separated layout without reclustering. In the Cluster-separated layout each Multi-Tag Cluster sits in its own labelled, tinted region and the One-Tag Clusters share one grid region. A Re-layout button tidies the positions, and that choice is recorded in exports. Controls, Inspector and Tables collapse independently, or all at once with "Graph only", and a collapsed inspector opens as a floating panel.

**Blocked by:** 13

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Cluster-separated positions), "App" (Layout, Two modes).

- [x] The Global ↔ Cluster-separated switch computes positions from the current elements alone (each node's cluster + its global position), with no rebuild and no recluster. The renderer instance is not re-mounted.
- [x] Cluster-separated layout: each Multi-Tag Cluster is laid out from its intra-cluster edges, seeded from the global positions. Boxes are packed side by side as labelled, tinted regions ("C1 · 14 tags"). One-Tag Clusters share one grid region at the end. Inter-cluster edges are drawn faint.
- [x] Re-layout refines from the current positions and is held client-side. It is dropped when the dataset, filter, Clustering Weight or seed changes, or on reload. Exports record `layout_source`.
- [x] `nodes.csv` gains `x_global, y_global, x_cluster_separated, y_cluster_separated`. Cluster-separated positions are always computed for export. `schema_version` is bumped.
- [x] Controls, Inspector and Tables collapse independently, and "Graph only" collapses all three. With the inspector collapsed, a click opens a floating panel closed with ×.
- [x] Tests: the switch leaves the `state_id` and the partition unchanged, and the export carries both coordinate sets.

## Comments

- 2026-10-04 (agent): App implemented in steamstudy.app (loader, renderer boundary, layout, callbacks, export/open, rs_cache, server). Tested via the export zip (app equals Build, round trip, refusals), the served page (no external URLs) and the callbacks as functions; also exercised live in the browser on a demo Build (node/edge/cluster inspectors, remove, layout switch, Re-layout, background Removal Sensitivity run with stale/current display, Analysis Report mode on the same renderer instance, floating inspector). Open Network State also re-exports and can compare table hashes (recorded_table_hashes_match).
