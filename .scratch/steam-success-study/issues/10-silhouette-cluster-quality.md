# Silhouette space and cluster-quality metrics
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 05, 19

## Question

Which distance/feature space is used for silhouette, under which graph states silhouette is reported as unavailable, and what are the exact definitions of modularity, intra-cluster density, inter-cluster connectivity and any further quality metric shown after every clustering? Also: Louvain vs. Leiden, and the resolution parameter.

Surfaced by Graph clustering and quality methods: Louvain (brief's preference, with a disconnected-community check) vs. Leiden-modularity (connected guarantee; beware CPM defaults in networkx/igraph); expose γ in the UI and its default; Jaccard-on-game-sets vs. 1/w shortest-path vs. cosine for silhouette; singleton handling in the mean; null-model modularity baseline; whether to add leidenalg/python-igraph as dependencies; determinism requirements (canonical node/edge order, pinned versions, seed/γ/algorithm/versions in exports).

Surfaced by [Tag network app interaction prototype](14-tag-network-app-prototype.md):
- Isolated tags stay in the network as one-tag clusters, so singletons are expected at the 8/8 defaults (0–5 per dataset on mock data). How do they enter the silhouette mean, the cluster count and modularity, and how are they reported?

Surfaced by [Web stack selection](18-web-stack-selection.md):
- Python is pinned to 3.14. leidenalg 0.12.0 and igraph 1.0.0 ship abi3 Windows wheels that install on 3.14, and networkx 3.7 has a pure-Python Leiden; adding leidenalg/igraph would only need a clean import check (part of [Dash spike re-run on Python 3.14](22-dash-spike-python-314.md)).

Settled by [Edge weight used for clustering](19-edge-weight-for-clustering.md):
- Clustering runs on the Clustering Weight: `shared_games` (default) or `lift` (optional, app selector). Every graph quality metric (modularity and its null-model baseline, coverage, conductance, intra-cluster density) is measured on the active Clustering Weight. Jaccard-on-game-sets silhouette, if chosen, is independent of the mode. Because the raw count stays the default, the metrics must stay meaningful under frequency-dominated weights.

## Answer

Resolved 2026-10-04 with the researcher. The brief's Louvain stays the default; Leiden is an optional mode, so the connectivity guarantee is available without replacing the brief's method.

**Clustering algorithm** (new setting, mirrors the Clustering Weight)
- `louvain` (**default**): NetworkX `louvain_communities(weight=<active Clustering Weight>, resolution=γ, seed=seed, threshold=1e-7)`, final (highest-modularity) level.
- `leiden` (optional): `leidenalg.find_partition(g, RBConfigurationVertexPartition, weights=<active Clustering Weight>, resolution_parameter=γ, n_iterations=-1, seed=seed)`: modularity with γ, run until stable; other leidenalg defaults. CPM is never used.
- Shared network-defaults config: `algorithm = "louvain"`. App: "Clustering algorithm: Louvain / Leiden" selector beside seed, γ and Clustering Weight, initialised from the config, in both app modes. The feature-analysis report uses the config value only; a Leiden report is a second Build.
- `algorithm` joins every network-state cache key and every export's metadata. Null-model replicates and node-removal sensitivity use the active algorithm; switching it marks sensitivity results stale.
- `leidenalg` and `python-igraph` are regular pinned dependencies of `steamstudy` (every install offers both modes). A failed import on 3.14 counts as a failure of [Dash spike re-run on Python 3.14](22-dash-spike-python-314.md), whose rule is to fall back to 3.13.
- **Disconnected clusters under Louvain are flagged, never split**: `connected = false` on the cluster, "disconnected clusters: n" in the Cluster-quality row, a warning in the inspector and Analysis Report mode suggesting the Leiden mode. The methods section reports how many disconnected clusters the report's runs produced.

**Determinism**: NetworkX and igraph graphs are built in canonical order (nodes sorted, edges sorted by (u, v)); library versions pinned; algorithm, γ, seed, `clustering_weight` and library versions (pinned versions of both libraries, whichever mode ran) stored in every export and in `build.json`.

**Resolution γ**: shared network-defaults config `resolution = 1.0`; app numeric input 0.1–3.0, step 0.05, beside seed, in both app modes; the feature-analysis report uses the config value only. Q is always reported at the γ that was optimised, labelled "Q (γ = 1.00)"; no second Q at γ = 1.

**Silhouette**: Jaccard distance on game sets only, d(u,v) = 1 − |G_u ∩ G_v| / |G_u ∪ G_v|, with G_t counted over the loaded dataset after the Minimum Months Filter (the same games as N for Lift). Independent of the Clustering Weight and the algorithm. No graph-distance silhouette. Labelled "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion". `sample_size=None`.

**One-Tag Clusters** (glossary: Cluster, One-Tag Cluster, [CONTEXT.md](../../../CONTEXT.md))
- Cluster count is reported as "k multi-tag clusters + s one-tag clusters", never as one total.
- Silhouette is computed on the full partition (One-Tag Clusters count as "other clusters" for b(i)); their own s = 0 is left out of every mean. Reported: per-node s(i) (blank for One-Tag Clusters), per-cluster mean, overall mean over Multi-Tag Cluster members, with s beside it.
- Silhouette is **n/a** (with the reason) when there are fewer than 2 Multi-Tag Clusters, including exactly one.
- Modularity and coverage are computed over the whole network (isolated tags contribute 0). Q is "n/a (no edges)" when total weight is 0.

**Null-model baseline**: bipartite game–tag shuffle (curveball / swap randomisation) over the same games and the same visible tags, preserving each game's tag count and each tag's game count; the network is rebuilt with the same thresholds and reclustered with the same algorithm, γ and Clustering Weight. R = 20 replicates by default (config, stored in exports); replicate seeds derived from the main seed. Reported: Q_null mean ± sd and z = (Q − mean) / sd (n/a when sd = 0). It answers "more structure than tag popularity alone produces?", which matters because shared games is the default Clustering Weight. Whether it runs on every recompute or on demand is for [Recompute turnaround and caching](23-recompute-budget-caching.md).

**Metric set** (all weighted values on the active Clustering Weight)
- Global, one Cluster-quality row per state: Q (γ) · Q_null mean ± sd, z · weighted coverage = intra-cluster weight / total weight · inter-cluster weight share = 1 − coverage · k + s cluster counts · mean silhouette (Multi-Tag Cluster members) · number of disconnected clusters.
- Per cluster: size · internal edge count · edge density = internal edges / (n(n−1)/2) (unweighted) · weighted density = internal weight / (n(n−1)/2) · weighted conductance = cut(C) / min(vol(C), vol(rest)) (n/a when vol(rest) = 0) · cut weight · mean silhouette · connected flag.
- Inter-cluster connectivity: cluster × cluster connection table of edge count and summed weight between each pair of Multi-Tag Clusters; One-Tag Clusters pooled into one row.
- Not used: `nx.community.partition_quality` (unweighted), "performance".
- All are labelled descriptive; none validates that a cluster is meaningful.

**For the methods section**: "Communities are detected with Louvain (NetworkX, fixed seed, γ = 1 by default), with Leiden (modularity objective) as an optional alternative. Modularity is compared with a null model that shuffles game–tag assignments while keeping every tag's and every game's tag count. Silhouette uses Jaccard distance between tags' game sets and is reported as a descriptive diagnostic over multi-tag clusters only."
