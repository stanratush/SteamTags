# Layout is downstream of analysis

Node positions exist only to draw the Tag Network. We tune them for readability: ForceAtlas2 on the visible network, gravity with a hard clamp, label-aware spacing, a layout sized to the viewer's canvas, and Tidy, which depends on what the viewer dragged. So we make it structurally impossible for them to reach any result. Layout is a separate step, `layout_state(state, canvas)`, which takes a finished `NetworkState` and only reads it. `compute_state` computes no coordinates. Clustering, Q, the Jaccard silhouette, node metrics, Cluster Centers, Membership Stability, the null model, seed noise and Removal Sensitivity never receive positions. Data flows one way: the Cluster-separated layout reads the Cluster Centers to pin them, and nothing flows back. We chose a structural split over relying on code order (positions were already computed last), because the layout now depends on things that have no place in a Network State (the canvas size, dragged positions), and a future change could otherwise quietly read them.

## Consequences

- `state_id` stays a hash of the settings key. Exports change only `x_global`, `y_global`, `x_cluster_separated` and `y_cluster_separated` in `nodes.csv`. An invariance test checks that every other byte is identical under very different layout settings.
- Exports are laid out for a fixed reference canvas (the graph area of a 1440 × 900 Workbench), so the same Network State exports the same coordinates on every machine. The app draws the same layout for its actual canvas, so what is on screen can differ from the exported coordinates.
- Comparing an export with a recomputed state is coordinate-blind. Coordinates in old exports are not expected to match a newer layout.
- Distance on screen is never a metric. Positions are never measured or reported as a result.
