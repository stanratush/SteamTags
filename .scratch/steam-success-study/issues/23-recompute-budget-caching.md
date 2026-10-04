# Recompute turnaround and caching
Type: grilling
Status: open
Blocked by: 10, 11

## Question

How fast must the Tag Network app turn around a settings change (threshold, Genre Tag or defining-tag visibility, node removal, Minimum Months Filter, seed): network build + clustering + quality metrics + centers + positions, excluding on-demand node sensitivity? Which server-side caching makes that target achievable in Dash: cache keys (dataset, thresholds, hidden Genre Tags, hidden defining tag, removed nodes, Minimum Months Filter, seed, γ/algorithm), where the cache lives (in-process memo vs. the `<build>/app_cache/` diskcache), eviction, and how the server-side network state that serves edge-click AppID lookups is keyed?

Graduated from the map's fog after [Web stack selection](18-web-stack-selection.md) fixed the stack. Known data points ([Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md)): 46–305 ms server-side build + Louvain at ~400 nodes; ~55 ms worst-case redraw; callbacks queue rather than drop during rapid toggling. The payload no longer carries AppID lists. Blocked on the metric and center definitions, because they set the per-change compute cost (e.g. Jaccard silhouette, closeness/eigenvector centrality).

Settled by [Edge weight used for clustering](19-edge-weight-for-clustering.md):
- `clustering_weight` (`shared_games` / `lift`) joins every network-state cache key. Global layout positions are computed once per dataset + Minimum Months Filter + Clustering Weight and cached; switching mode moves nodes once.

Settled by [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md):
- `algorithm` (`louvain` default / `leiden`) and γ (`resolution`) join every network-state cache key.
- Per-change compute now includes: the active clustering, Jaccard game-set distances + silhouette, the per-cluster metric set and the cluster × cluster connection table, and the null-model baseline (R = 20 bipartite-shuffle replicates, each a rebuild + recluster; configurable). Decide here whether the null baseline runs on every recompute, lazily, or on demand.

Settled by [Cluster center and centrality measures](11-cluster-center-centrality.md):
- No closeness/eigenvector/betweenness. Per change: one n_c² medoid pass per cluster over the Jaccard matrix the silhouette already builds, plus O(E) degrees, strengths, `within_z` and `participation`.

Surfaced by [Dash spike re-run on Python 3.14](22-dash-spike-python-314.md):
- Fixed per-callback overhead is 7–9 ms for an empty response when the page is opened at `http://127.0.0.1:<port>`, but ~270–450 ms at `http://localhost:<port>` (Windows name resolution). The turnaround budget assumes `127.0.0.1`. Python 3.14 changes nothing else here: build + Louvain was 19–113 ms per change on the spike graph, and the worst-case `elements` update is still ~800 KB with AppIDs inline (the payload without them has not been measured).

## Answer
