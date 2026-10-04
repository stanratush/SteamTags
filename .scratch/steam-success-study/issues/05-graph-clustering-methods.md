# Graph clustering and quality methods
Type: research
Status: resolved
Blocked by: none

## Question

What are the methodologically sound options for clustering and evaluating a small weighted tag co-occurrence graph (roughly 50–400 nodes) that is re-clustered on every filter change?

- Louvain vs. Leiden on weighted graphs (connectivity guarantees, resolution parameter, seeding); Python implementations (networkx, python-louvain, leidenalg/igraph) and their determinism.
- Silhouette on graph communities: candidate distance representations (weighted shortest-path with weight→distance transforms; Jaccard/cosine distance on game-incidence or adjacency vectors), and when silhouette is undefined or misleading (one cluster, singletons, disconnected components).
- Other quality measures: weighted modularity, intra-cluster density, inter-cluster connectivity/conductance, coverage.
- Cluster-center measures: intra-cluster weighted degree, closeness, eigenvector centrality, graph medoid; their trade-offs.
- Cost of node-removal sensitivity (n reclusterings per state) and known efficient strategies.

Cite literature where possible.

## Answer

- **Algorithm:** Louvain can return badly connected or disconnected communities (up to 25% and 16% in Traag et al. 2019). Leiden guarantees connected communities. Recommended: Leiden with the **modularity** objective, fixed seed and γ = 1 exposed. Watch out: NetworkX `leiden_communities` and igraph `community_leiden` default to CPM. If Louvain stays, add a disconnected-community check.
- **Determinism:** the seed alone is not enough. Use canonical node and edge insertion order, pin library versions, and store seed, γ, algorithm and versions in exports. igraph is seeded through Python's `random`.
- **Silhouette:** recommend Jaccard distance on tag game-sets. It is always finite, a metric, and needs no weight transform. 1/w shortest-path distance is the alternative, but it produces inf on disconnected graphs, which sklearn rejects, and hub tags compress it. Silhouette is undefined when k < 2 or k = n. Singletons score 0 (Rousseeuw 1987; sklearn does the same), so report the mean excluding singletons plus the singleton count. Treat it as a diagnostic only.
- **Quality:** weighted Q (with a null-model reference, because of degeneracy and high modularity in random graphs), weighted coverage, and per-community density and conductance. `nx.community.partition_quality` ignores weights.
- **Centers:** Jaccard medoid as the primary center, plus intra-cluster weighted degree (frequency-biased). Eigenvector and closeness need connected subgraphs or a distance transform. Use deterministic tie-breaks.
- **Sensitivity:** a full NetworkX n-removal sweep took about 74 s for ~350 nodes on synthetic data, which is too slow to run eagerly. Use on-demand or background computation, warm starts, a compiled library (leidenalg), and caching. Measure a seed-to-seed ARI noise floor first.
- **Flag:** raw co-occurrence counts are frequency-dominated. Normalising them (e.g. association strength) is an open decision.

Details and citations: [../research/05-graph-clustering-methods.md](../research/05-graph-clustering-methods.md)
