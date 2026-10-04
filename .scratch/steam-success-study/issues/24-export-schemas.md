# Export schemas for the app and the feature analysis
Type: grilling
Status: open
Blocked by: 23

## Question

What are the exact file names, formats (CSV vs. JSON), column names, types and metadata blocks of every export: the Tag Network app's exports (network with nodes/edges incl. x/y for both layout modes and AppID lists, cluster quality, clusters, cluster × cluster connections, nodes, tags not in the network, Removal Sensitivity) and the Build's feature-analysis CSVs (including the per-dataset Removal Sensitivity table)? How do they reuse the `build_id`, list conventions and provenance of `build.json` and the `top100_<dataset>.csv` contract, and how is the network-state key recorded so an export can be matched to a cached app state?

Graduated from the map's fog after [Node-removal sensitivity method](12-node-removal-sensitivity.md). Contents already fixed (only the layout is open):
- Starting export set: [Tag network app interaction prototype](14-tag-network-app-prototype.md). Top-100 CSV, Build folder, `build.json`: [Pipeline architecture and export schema](15-pipeline-architecture.md). Feature-analysis table contents: [Feature-analysis definitions](13-feature-analysis-definitions.md).
- x/y for both layout modes, AppID lists: [Web stack selection](18-web-stack-selection.md). `shared_games` + `lift` on edges, `strength_shared` + `strength_lift` on nodes, `clustering_weight`: [Edge weight used for clustering](19-edge-weight-for-clustering.md).
- `algorithm`, `resolution`, null-model R, library versions; Cluster-quality global row; per-cluster metrics; per-node silhouette; connection table: [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md).
- `center`, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength`; node metrics `n_games`, `degree`, `degree_intra`, `medoid_score`, `is_center`, `within_z`, `participation`; tie-break rule: [Cluster center and centrality measures](11-cluster-center-centrality.md).
- Removal Sensitivity rows (identity, reclustered ΔQ/Δsilhouette/Δk/Δs/ARI/centers lost, fixed-partition ΔQ/Δsilhouette, `beyond_noise`, silhouette n/a transitions) and metadata (noise-floor values, K, derived seeds, partial flag n of N, method version, state key): [Node-removal sensitivity method](12-node-removal-sensitivity.md).

Blocked by [Recompute turnaround and caching](23-recompute-budget-caching.md), which defines the network-state key exports must record.
