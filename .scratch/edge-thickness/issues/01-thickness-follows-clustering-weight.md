# 01: Edge thickness follows the Clustering Weight

**What to build:** edge thickness shows the selected Clustering Weight, in the Global and the Cluster-separated layout alike, and the legend says which measure is drawn.

| Clustering weight | Default edge thickness |
|---|---|
| Shared games | Shared-game count |
| Lift | Lift |

**Blocked by:** none

**Status:** done

Overrides [Edge weight used for clustering](../../steam-success-study/issues/19-edge-weight-for-clustering.md) ("What does not follow the mode": edge thickness) and spec story 76 of the [Steam success study spec](../../steam-success-study/spec.md). The edge weight, the thresholds and the edge inspector still use shared games in every mode.

- [x] Width = 0.4 + 2.6 × value / the network's largest value, for shared games or lift (`renderer.payload`, `thickness`).
- [x] Under Lift, a switch beside the legend ("show shared games") draws shared-game thickness while the clustering still runs on lift. It is a view choice: never part of the Network State, the export or any number. Changing the Clustering Weight unticks it, so Lift always starts on lift thickness.
- [x] The legend reads "Edge thickness: shared games" or "Edge thickness: lift", with both help layers (`legend.thickness` → Edge thickness in `02-app-controls.md`). It names the state drawn (`elements-base`), so it never runs ahead of a recompute.
- [x] User Guide (Reading the graph, Edge thickness, Clustering weight, Minimum shared games), metric reference (Edge weight, Edge lift), the `shared_games` export description CONTEXT.md (Clustering Weight) updated; story 76 and the Clustering Weight lists of the study spec marked superseded.

## Comments

- 2026-10-09: Done. Checked in the browser on the full Build: under Lift the legend reads "Edge thickness: lift" and the switch appears; ticking it relabels to "Edge thickness: shared games" and changes the width of all 332 edges without moving a node.
