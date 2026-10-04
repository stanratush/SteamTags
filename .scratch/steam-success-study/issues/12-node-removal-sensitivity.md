# Node-removal sensitivity method
Type: grilling
Status: resolved
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

## Answer

Resolved 2026-10-04 with the researcher. The measure keeps the prototype's remove-and-recluster as the main reading, adds a noise-free fixed-partition reading beside it, and treats every flag as a screening aid, never a significance test.

**Name** (glossary, [CONTEXT.md](../../../CONTEXT.md)): **Removal Sensitivity**, read against the **Seed-Noise Floor**. A what-if: it never changes the app state (distinct from the app's real remove/restore/reset). UI tab and Analysis Report mode section: "Removal sensitivity". Avoid "node sensitivity", "influence", "importance".

**Method**: for each tag v, two readings, as two labelled column groups:
- **Reclustered**: drop v and its edges, recluster **from scratch** (cold restart, no warm start, in both Louvain and Leiden modes) with the main seed, the active algorithm, γ and Clustering Weight. Answers "does the partition depend on v?".
- **Fixed partition**: drop v, keep every other tag in its current cluster, recompute Q and silhouette. Deterministic and nearly free. Answers "how much does v add to the quality of this partition?".
- Comparisons are against the current state over the shared tag set (all tags except v). Removing v changes no remaining edge's lift (N unchanged).

**Reported per tag**
- Identity: tag, tagid, current cluster, `is_center`, active strength.
- Reclustered: ΔQ (active γ), Δsilhouette, Δk (multi-tag clusters), Δs (one-tag clusters), **ARI** vs. the current partition (`sklearn.metrics.adjusted_rand_score`, the main "did it reorganise?" number), **centers lost** (current Cluster Centers other than v that are no longer centers).
- Fixed partition: ΔQ, Δsilhouette.
- A silhouette switching between a value and n/a is shown as a transition ("0.21 → n/a", with the reason), never as a number.
- Not recomputed per removal: null-model Q_null/z, per-cluster metrics, layout.
- ΔQ label caveat: it also reflects the drop in total edge weight when v's edges go, so it is not a pure structural change.

**Seed-Noise Floor**: K = 10 extra seeds (config `sensitivity_noise_seeds`, stored in exports; seeds derived from the main seed) clustered on the unchanged graph; computed once per run and reused by single-tag runs and by Continue.
- Q and silhouette: SD across the K seeds.
- ARI: ARI between each extra seed's partition and the main seed's.

**"Beyond noise" flag** (reclustered readings only)
- ΔQ, Δsilhouette: |Δ| > 2√2 · SD (a difference of two single runs has about √2 times the single-run SD).
- ARI: below the lowest of the K noise ARIs ("more restructuring than any of 10 seed changes produced"). If all noise ARIs are 1.0 (SD 0), any change is flagged; correct, since the clustering is seed-stable.
- No flag on Δk, Δs, centers lost or the fixed-partition columns (integers or noise-free).
- One `beyond_noise` column listing the measures that crossed (e.g. "ARI, Q"), labelled "screening flag, not a significance test" (with n tags tested, a few cross by chance).

**Scope and cost**
- "Run" covers every visible tag (including One-Tag Clusters); the node inspector also has "Run for this tag" (one recluster plus the noise floor if not yet cached).
- No node cap; before starting, show an estimate (n × the measured time of the current clustering).
- Order: active strength descending, ties by lower tagid, so a cancelled run has covered the most connected tags first.
- No multiprocessing in v1 (Windows spawn ~2.5 s per process); revisit only if the first test Build shows a default-threshold sweep over ~60 s.

**Caching and resume** (the general network-state key, storage and eviction are for [Recompute turnaround and caching](23-recompute-budget-caching.md))
- Sensitivity key = full network-state key + K + a method-version string; results in `<build>/app_cache/`.
- Returning to an earlier state shows its cached results as current, not stale.
- A cancelled run is cached as partial; the button becomes "Continue (n of N done)" and runs only the remaining tags in the same order, reusing the noise floor.
- Single-tag runs go into the same cached table; a later full run skips them.

**UI**
- Table default sort: ARI ascending, then |ΔQ reclustered| descending; every column sortable. Filters: "beyond noise only" toggle, cluster selector.
- Noise-floor line above the table: K, SD(Q), SD(silhouette), minimum seed ARI; partial or stale banner when relevant.
- Row click selects the tag in the graph and inspector; the node inspector shows the tag's row and "Run for this tag".
- Stale results stay visible, greyed and not clickable, until a re-run.
- No colour-by-sensitivity overlay in v1: graph colour always means cluster.
- Analysis Report mode section 5 shows the same table and noise line.
- Export: CSV plus metadata with the noise-floor values, K, derived seeds, partial flag with n of N, method version and the state key.

**Build**: the offline Build also computes a complete Removal Sensitivity table per dataset at the feature-analysis report's settings (shared defaults, defining tag out, config algorithm/γ/seed/Clustering Weight) and writes it as a CSV beside the other analysis outputs; the report adds one descriptive sentence: how many tags are beyond noise and which. Column names belong to the export-schema work.

**For the methods section**: "To show how much the clustering depends on individual tags, each tag was removed in turn and the network reclustered with the same settings; the resulting partition was compared with the original by the adjusted Rand index, modularity and silhouette. Changes are compared with the variation across ten other random seeds on the unchanged network and flagged when larger; this is a screening aid, not a significance test. A second reading keeps all other tags in their clusters and reports the change in modularity and silhouette only."
