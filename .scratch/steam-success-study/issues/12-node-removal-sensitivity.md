# Node-removal sensitivity method
Type: grilling
Status: open
Blocked by: 05, 10

## Question

How is a node's contribution to clustering measured: remove-and-recluster vs. remove-with-fixed-assignments (or both); which deltas are reported (silhouette, modularity, number of clusters); how its cost is controlled (caching keys, parallelism, lazy/on-demand computation, size limits); and how results are sorted and filtered in the UI?

Surfaced by Graph clustering and quality methods: a full remove-and-recluster sweep took ~74 s on a synthetic ~350-node graph (NetworkX Louvain), so it cannot run on every filter change; options are on-demand, background job, top-k only, warm start, leidenalg, caching. Per-node deltas need a seed-noise floor (partition variation across seeds on the unchanged graph) to be interpretable.

Surfaced by [Tag network app interaction prototype](14-tag-network-app-prototype.md):
- Settled: sensitivity runs **only on a button press**, with progress and cancel; results are marked stale when settings change. "Run on every filter change" is off the table. Still open: the method, the reported deltas, the noise floor, caching, and whether a run can be limited to some nodes.
- The prototype's remove-and-recluster plus a 10-seed noise floor finished in seconds on ~80 nodes in browser JS; at the 8/8 defaults, mock graphs have 40–54 nodes.

Surfaced by [Web stack selection](18-web-stack-selection.md):
- Settled: the run is a Dash background callback (`DiskcacheManager`). Up to ~4 s startup per run is accepted; inputs are plain picklable values; the job cache lives in `<build>/app_cache/`; starting or cancelling clears progress and marks old results stale. The method, deltas, noise floor and node limits are still open here.

Settled by [Edge weight used for clustering](19-edge-weight-for-clustering.md):
- Sensitivity runs and its seed-noise floor re-cluster on the active Clustering Weight (`shared_games` or `lift`); results are stale when the mode changes, and the mode is part of the cache key. Removing a node does not change any remaining edge's lift (N is unchanged).

Settled by [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md):
- Re-clustering uses the active `algorithm` (Louvain default via NetworkX; Leiden via leidenalg, compiled) and γ; both join the cache key, and switching either marks results stale.
- Silhouette available for deltas: Jaccard game-set silhouette, mean over Multi-Tag Cluster members, n/a with fewer than 2 Multi-Tag Clusters (a removal can flip it to or from n/a). Cluster count is "k multi-tag + s one-tag". Q is reported at the active γ, with a null-model z.

Settled by [Cluster center and centrality measures](11-cluster-center-centrality.md):
- Cluster Center = Jaccard medoid (clusters of 3+ tags only); a removal can change a cluster's center, so "center changed" is a candidate per-node delta. Node metrics now include `within_z` and `participation` on the active Clustering Weight.
