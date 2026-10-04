# 17: Layout modes and collapsible Workbench

**What to build:** The researcher can switch the graph between the Global layout and a Cluster-separated layout without reclustering. In the Cluster-separated layout each Multi-Tag Cluster sits in its own labelled, tinted region and the One-Tag Clusters share one grid region. A Re-layout button tidies the positions, and that choice is recorded in exports. Controls, Inspector and Tables collapse independently, or all at once with "Graph only", and a collapsed inspector opens as a floating panel.

**Blocked by:** 13

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Cluster-separated positions), "App" (Layout, Two modes).

- [ ] The Global ↔ Cluster-separated switch computes positions from the current elements alone (each node's cluster + its global position), with no rebuild and no recluster. The renderer instance is not re-mounted.
- [ ] Cluster-separated layout: each Multi-Tag Cluster is laid out from its intra-cluster edges, seeded from the global positions. Boxes are packed side by side as labelled, tinted regions ("C1 · 14 tags"). One-Tag Clusters share one grid region at the end. Inter-cluster edges are drawn faint.
- [ ] Re-layout refines from the current positions and is held client-side. It is dropped when the dataset, filter, Clustering Weight or seed changes, or on reload. Exports record `layout_source`.
- [ ] `nodes.csv` gains `x_global, y_global, x_cluster_separated, y_cluster_separated`. Cluster-separated positions are always computed for export. `schema_version` is bumped.
- [ ] Controls, Inspector and Tables collapse independently, and "Graph only" collapses all three. With the inspector collapsed, a click opens a floating panel closed with ×.
- [ ] Tests: the switch leaves the `state_id` and the partition unchanged, and the export carries both coordinate sets.
