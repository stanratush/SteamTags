# Tag network app interaction prototype
Type: prototype
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 06

## Question

How should the Tag Network app look and behave? Layout of controls (dataset loader, minimum games per tag, minimum shared games, Minimum Months Filter, hide/show Genre Tags, seed, manual node removal/restore/reset), graph view with marked cluster centers, inspection panels (node, edge with its games, cluster), metric panels and tables (cluster quality, cluster summary, node sensitivity), and export buttons.

Surfaced by [Feature-analysis definitions](13-feature-analysis-definitions.md):
- This ticket sets the **shared network defaults** (minimum games per tag, minimum shared games, Genre Tags hidden or shown by default). They live in one config that the app and the feature-analysis report both read; the report's "clusters of characteristics" use them with the defining tag removed.

## Prototype

Assets: v1 with the three variants, [PROTOTYPE-tag-network-app-v1-three-variants.html](../prototypes/14-tag-network-app/PROTOTYPE-tag-network-app-v1-three-variants.html) (built 2026-10-03), and v2 reflecting the answer below, [PROTOTYPE-tag-network-app.html](../prototypes/14-tag-network-app/PROTOTYPE-tag-network-app.html) (2026-10-04). Both open with a double-click and need internet for Cytoscape.js. Throwaway: mock data only (`Mock Game …`, generated tag profiles), but the network build, Louvain clustering, modularity, Jaccard silhouette, on-demand remove-and-recluster sensitivity with a seed-noise floor, inspection and exports all run live, so the thresholds can be tuned against node/edge/cluster counts.

v1 layouts, switchable with the bottom bar or ←/→ (`?variant=`):
- **A · Workbench**: controls on the left, graph in the middle, inspector on the right, tabbed tables below. Everything is visible at once.
- **B · Graph-first canvas**: a full-screen graph with a compact floating toolbar and stats HUD. The inspector is a drawer that opens on click, and tables open in a bottom sheet.
- **C · Analysis report**: one scrolling page of numbered sections (Dataset → Filters with every left-out tag and its reason → Network + inspector → Quality → Sensitivity → All nodes/edges → Export).

Placeholders for open tickets: raw edge weight ([Edge weight used for clustering](19-edge-weight-for-clustering.md)), center = max intra-cluster weighted degree ([Cluster center and centrality measures](11-cluster-center-centrality.md)), metric set ([Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md)), sensitivity method ([Node-removal sensitivity method](12-node-removal-sensitivity.md)).

Questions put to the researcher:
1. Which layout (or which parts of each)?
2. Shared network defaults: min games per tag (prototype starts at 5), min shared games (3), Genre Tags hidden by default (yes)?
3. Isolated tags (above min games but no edge ≥ min shared): keep as singletons or drop?
4. Tag-Specific Datasets: hide the defining tag by default in the app, matching the report?
5. Node sensitivity: run on demand (button + progress + cancel), not on every filter change?

## Answer

Resolved 2026-10-03 with the researcher, reacting to the [prototype](../prototypes/14-tag-network-app/PROTOTYPE-tag-network-app.html).

**Layout: two modes over one app**
- **Workbench** (primary, variant A): controls on the left; graph in the centre with a cluster legend; inspector on the right (node / edge with its games / cluster); tabbed tables below (Cluster quality, Clusters, Node sensitivity, Nodes, Edges, Not in network); removed-node list and export buttons in the left column. The inspector and table panels can be **collapsed**, so the graph can fill the window the way variant B does.
- **Analysis report** (second mode, variant C): one scrolling page of numbered sections: Dataset → Filters (with every left-out tag and its reason) → Network + inspector → Cluster quality → Node sensitivity → All nodes/edges → Export.
- The user switches modes from a control in the app. Both modes show the same loaded dataset, filters, removed nodes, seed and results.
- Variant B as a separate mode: rejected. Its full-window graph comes from collapsing the Workbench panels.

**Shared network defaults** (one config, read by both the app and the feature-analysis report):

| Setting | Default | Slider range |
|---|---|---|
| Minimum games per tag | 8 | 1–40 |
| Minimum shared games (edge) | 8 | 1–30 |
| Minimum Months Filter | 0 (off) | 0–60 |
| Genre Tags | hidden (the 11 Top-Level Genres) | per-tag toggles |
| Defining tag (Puzzle, RPG, Strategy, Simulation datasets) | hidden | toggle |
| Isolated tags | kept | — |

- **Isolated tags** (a tag that reaches the minimum games per tag but has no edge reaching the minimum shared games) stay in the network as **one-tag clusters**. They are counted and shown, not dropped.
- On mock data the 8/8 defaults gave 40–54 tags, ~260–320 edges and 3–6 multi-tag clusters per dataset. These numbers only show that the defaults are workable; they are not evidence about real data.

**Node sensitivity** runs **only when the user presses the button** (shows progress, can be cancelled, results marked stale when the settings change), never on a filter change.

**Other behaviour the prototype showed and the researcher kept**: click a node, edge or cluster to inspect it (an edge lists the games having both tags); remove a node from the inspector, restore one or reset all; every tag left out of the network is listed with its reason; cluster centers drawn as ◆ with a heavier outline; clusters labelled `C1…` by size, never named; exports carry dataset, thresholds, hidden/removed tags, seed and timestamp.

**Observation for other tickets**: with the raw shared-game count as edge weight, generic tags (Singleplayer, Indie, PvP) became cluster centers on mock data (see [Edge weight used for clustering](19-edge-weight-for-clustering.md)).

## Addendum: graph layout modes (2026-10-04)

Added by the researcher after the answer above; [v2 prototype](../prototypes/14-tag-network-app/PROTOTYPE-tag-network-app.html) shows it, with the answer's defaults and modes.

**Graph layout modes**, a switch on the graph in both app modes:
- **Global**: one force-directed layout of all nodes (as in v1).
- **Cluster-separated**: clusters occupy separate, non-overlapping regions. Each multi-tag cluster is laid out on its own from its intra-cluster edges only, seeded from the global positions so it keeps its internal shape. The cluster boxes are then packed side by side, each drawn as a labelled, tinted region (`C1 · 14 tags`). One-tag clusters share one grid region at the end. Inter-cluster edges stay drawn, faint.
- Switching layout only moves nodes. It never rebuilds the network or reclusters, and positions are cached per (network state, layout mode) so switching back is instant.

**Collapsed inspector**: in the Workbench, Controls, Inspector and Tables each collapse independently, and "Graph only" collapses all three. With the inspector collapsed, clicking a node, edge or cluster opens it as a floating panel over the graph, closed with ×.

Glossary updated: new **Analysis Report mode** ([CONTEXT.md](../../../CONTEXT.md)), to keep it apart from the generated feature-analysis report.
