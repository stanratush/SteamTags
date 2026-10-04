# Recompute turnaround and caching
Type: grilling
Status: resolved
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

Settled by [Node-removal sensitivity method](12-node-removal-sensitivity.md):
- Removal Sensitivity stays outside the turnaround budget (button-only background job). Its cache key is the full network-state key decided here + K (`sensitivity_noise_seeds`) + a method-version string, stored in `<build>/app_cache/`; returning to an earlier state must show its cached results as current, so the network-state key must be stable and canonical (e.g. sorted hidden/removed tag lists). Partial (cancelled) runs and single-tag runs are cached too; eviction decided here must not drop a partial run that the UI offers to Continue without also clearing that offer.

## Answer

Resolved 2026-10-04 with the researcher, over two rounds. Costs were measured first on synthetic data: [benchmark](../prototypes/23-recompute-benchmark/README.md) (Python 3.14.8). The researcher then set the principle for v1: **no performance target, no performance optimisation; correctness and functionality first.** A cache stays only where something would break or behave wrongly without it.

**Turnaround**: no target in v1. Measured for reference (synthetic, ms median, at thresholds 8/8 · 3/3 · 1/1): full recompute without the null model 17 · 61 · 245; null model R = 20 with Louvain 297 · 785 · 2,946 (Leiden 261 · 587 · 1,574); global layout ~217 extra; Cluster-separated layout 8 · 28 · 59; payload without AppIDs 29 KB · 152 KB · 984 KB. Clustering dominates; Jaccard, silhouette and metrics are under 30 ms even at 1/1.

**Network-state key** (identifies a state in every export and in the Removal Sensitivity cache)
- Fields: `build_id`, `dataset`, `min_months`, `min_games_per_tag`, `min_shared_games`, `hidden_tagids` (Genre Tags and the defining tag, sorted), `removed_tagids` (sorted; separate from hidden because "Not in network" gives each its own reason), `clustering_weight`, `algorithm`, `resolution` (fixed 2-decimal string, `"1.00"`), `seed`, `null_replicates` (R), `key_version` (bumped whenever a method or code change would alter results).
- Not in the key: the layout mode, the isolated-tags policy (fixed: kept).
- Form: canonical JSON (sorted keys, no whitespace) → SHA-256; `state_id` = first 12 hex characters. Exports store the full JSON and the `state_id`.
- The Removal Sensitivity key stays as settled in [Node-removal sensitivity method](12-node-removal-sensitivity.md): this key + K + method version.

**Recompute model**: every settings change recomputes everything from the loaded dataset: network, clustering, null-model baseline, silhouette, metrics, centers, global positions. The pipeline is deterministic (canonical order, fixed seeds), so the same key always gives the same result. The server holds no state between requests.
- **No performance caches in v1**: no in-memory LRU, no disk cache for network states, null-model results or layouts. Caching can be added later, keyed by `state_id`.
- **Null-model baseline**: inside every recompute, synchronously, so the Cluster-quality row is always complete and no export is ever missing it.
- **Global positions**: a pure function of (dataset, Minimum Months Filter, Clustering Weight, seed), the seeded `spring_layout` at the loosest thresholds, recomputed on each change rather than cached. Thresholds aren't inputs, so the graph doesn't jump as thresholds change. This replaces "computed once and cached" in [Web stack selection](18-web-stack-selection.md) and [Edge weight used for clustering](19-edge-weight-for-clustering.md); the observable behaviour is the same.
- **Edge-click AppIDs**: computed on click as the intersection of the two tags' game sets over dataset + Minimum Months Filter (~1 µs). A late click always gets the correct games for that pair; no server-side network state.

**Layout switch and Re-layout** (no server state)
- Global ↔ Cluster-separated: the graph elements already carry each node's cluster and global position, so the switch callback computes Cluster-separated positions from those alone: no rebuild, no recluster. Cluster-separated positions are computed only while that mode is shown. This replaces "cached per (network state, layout mode)" in the addendum to [Tag network app interaction prototype](14-tag-network-app-prototype.md).
- Re-layout: positions kept in a client-side store and reused for later changes, dropped when the dataset, Minimum Months Filter, Clustering Weight or seed changes, or on page reload. Exports record `layout_source = "default" | "relayout"`.

**Input debouncing** (functional: stops queued recomputes from showing stale states for a long time): sliders send on release (`updatemode="mouseup"`, value label live while dragging); seed and γ inputs on Enter or blur (`debounce=True`); toggles and checkboxes immediately.

**Persistent cache and eviction**
- The only persistent cache is Removal Sensitivity in `<build>/app_cache/`. Never evicted automatically.
- "Clear app cache" (button + CLI) deletes the results and their "Continue (n of N done)" offers in one step. Deleting a Build deletes its cache.
- The `DiskcacheManager` job store is a separate directory (job plumbing, not results) and may be culled normally.

**For the known limitations**: the app is not optimised in v1; at the loosest thresholds a change can take several seconds (mostly the null-model baseline).
