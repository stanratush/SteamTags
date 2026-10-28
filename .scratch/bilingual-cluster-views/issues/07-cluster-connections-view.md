# Cluster connections view
Type: prototype
Status: open
Blocked by: 06

## Question

How does a researcher explore Cluster-to-Cluster connections visually and inspect the connections between any two Clusters? This is a HITL prototype (`prototype`, in `prototypes/07-cluster-connections/`), working from [Inter-cluster measures](06-inter-cluster-measures.md).

- Candidate overviews: a cluster × cluster matrix or heatmap, a cluster-level graph (one node per Cluster, edge width as Connection Ratio), and highlighting on the existing canvas (pick a Cluster and the others shade by strength).
- Per-cluster ranking in the Cluster Inspector: every other Cluster with the columns and order fixed in Inter-cluster measures (Connection Ratio, Connection Share, totals, edge count).
- The pair inspector: picking two Clusters shows the edges between them (tag pairs, shared games, Lift) and highlights them on the canvas, with rows that select an edge, as connected-tag rows do today.
- Where it sits (the Inspector, the Cluster quality tab, or a new tab), how it behaves in the Global and the Cluster-separated layout, and the cost against the [Graph interaction spec](../../graph-interaction/spec.md) budgets.
