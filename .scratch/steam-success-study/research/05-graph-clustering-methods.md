# Research 05: Graph clustering and quality methods for the Tag Network

Ticket: [../issues/05-graph-clustering-methods.md](../issues/05-graph-clustering-methods.md)
Date: 2026-10-03

**Question:** What are the methodologically sound options for clustering and evaluating a small weighted **Tag Network** (about 50 to 400 nodes) that is re-clustered every time a filter changes?

How to read this file. Sections marked **Established** report what a cited source says. Sections marked **Recommendation** are my proposals, and the researcher makes the final call in later grilling tickets. Section 7 is a measurement I ran on synthetic data, and it is labelled that way.

---

## 1. Louvain vs. Leiden

### Established

- **Louvain** (Blondel et al. 2008) is a greedy heuristic that maximises modularity. It alternates between local node moves and aggregating communities into super-nodes. The order in which nodes are visited changes the result [B08]. NetworkX shuffles that order at random and recommends passing a `seed` for reproducible output [NX-LV].
- **Louvain can produce badly connected or even internally disconnected communities.** When a node that bridges two parts of its community moves to another community, the rest of the community stays put, because every remaining node is still individually optimal. Traag et al. report that up to 25% of Louvain communities are badly connected and up to 16% are disconnected in their experiments [T19].
- **What Leiden guarantees** [T19, Table 1]:
  - After every iteration, communities are γ-separated and γ-connected. Louvain only guarantees γ-separation.
  - After a stable iteration, Leiden adds node optimality and subpartition γ-density. Louvain only reaches node optimality.
  - If Leiden is iterated until nothing changes, it also reaches uniform γ-density and subset optimality.
  - Leiden is also reported to run faster than Louvain [T19].
- Leiden adds a refinement phase that has its own randomness parameter, θ (called `theta` in NetworkX, `beta` in igraph). The paper uses θ = 0.01 and reports that values from about 0.0005 to 0.1 give reasonable results [T19].
- **Connectivity and resolution are separate problems.** Modularity has a resolution limit: it may fail to separate modules whose internal link count is about √(2L) or smaller, where L is the total number of links in the network [FB07]. The Constant Potts Model (CPM) avoids that limit. Louvain's connectivity defect occurs under both modularity and CPM [T19].
- **Weighted modularity.** Newman (2004) shows that a weighted network can be mapped onto a multigraph, so modularity applies directly with edge weights [N04]. NetworkX computes Q = Σ_c [ L_c/m − γ (k_c/2m)² ] with `weight=` and `resolution=` arguments. Here L_c is the total edge weight inside community c, k_c is the summed weighted degree of c, and m is the total edge weight. Setting γ < 1 favours larger communities and γ > 1 favours smaller ones [NX-Q]. γ is the Reichardt and Bornholdt resolution parameter [RB06].
- **Degeneracy.** Modularity typically has an exponential number of distinct partitions that score nearly as well as the best one, and these partitions can disagree about which nodes belong to the main communities. Good et al. advise interpreting the output of modularity maximisation cautiously and combining information from many solutions [GMC10]. Consensus clustering (aggregating many runs of a stochastic method) improves stability and accuracy [LF12].
- **Random graphs score high too.** Graphs with no community structure can still reach high modularity through random fluctuations [GSA04]. A modularity value is therefore only meaningful when compared against a null model.

### Python implementations

| Library | Function | Objective / default | Seed and determinism | Warm start |
|---|---|---|---|---|
| NetworkX (3.4.2 is installed here) | `louvain_communities(G, weight='weight', resolution=1, threshold=1e-07, max_level=None, seed=None)`; `louvain_partitions` returns every level | modularity | `seed` controls a random shuffle of node order [NX-LV] | none (no initial-partition argument) |
| NetworkX (3.7 stable docs) | `leiden_communities(G, *, weight, resolution=1.0, max_level=None, seed=None, metric='cpm', theta=0.01)` | **default is CPM**, not modularity | `seed` controls node order and refinement merges [NX-LD] | none |
| python-louvain (`community`) | `best_partition(graph, partition=None, weight='weight', resolution=1.0, randomize=None, random_state=None)` | modularity | `random_state` [PL] | `partition=` |
| leidenalg (on python-igraph) | `find_partition(graph, partition_type, initial_membership=None, weights=None, n_iterations=2, max_comm_size=0, seed=None)` | the class you pass: `ModularityVertexPartition`, `RBConfigurationVertexPartition(resolution_parameter)`, or `CPMVertexPartition` | `seed=`; a negative `n_iterations` runs until an iteration brings no improvement [LA] | `initial_membership=`; `Optimiser.optimise_partition(..., is_membership_fixed=...)` |
| python-igraph | `Graph.community_leiden(objective_function='CPM', weights=None, resolution=1.0, beta=0.01, initial_membership=None, n_iterations=2, ...)` | **default is CPM** | uses Python's global `random` module, so call `random.seed()` first [IG-SRC, IG-DISC] | `initial_membership=` |

Notes on the table:
- In some earlier NetworkX releases (around 3.4), `leiden_communities` had no built-in implementation and needed a backend such as cuGraph. The 3.7 stable source has a pure-Python implementation [NX-LD-SRC]. The pinned version therefore matters.
- **Pitfall:** both the NetworkX and igraph Leiden functions default to CPM. CPM with resolution 1.0 applied to raw co-occurrence counts behaves nothing like modularity with γ = 1. To compare Leiden fairly with the settled Louvain choice, set `metric='modularity'` in NetworkX, `objective_function='modularity'` in igraph, or use `ModularityVertexPartition` in leidenalg.
- **Determinism caveat (my inference from the NetworkX docs and source):** the seed fixes the shuffle, but the shuffle is applied to the graph's insertion order. Two graphs with the same edges inserted in a different order can therefore produce different partitions under the same seed. Results can also change between library versions.

### Recommendation

1. The map currently settles on Louvain with a fixed, configurable seed. **The cheapest sound upgrade is Leiden with the modularity objective**: the objective, γ and seed semantics stay the same, and the connectivity guarantee is added. If Louvain stays, add a post-check that flags any community whose induced subgraph is disconnected. Splitting disconnected communities into their components is a possible fix, but it is my suggestion and not something the cited sources prescribe.
2. **Build the graph in canonical order**: sort the nodes, then add edges sorted by (u, v). Pin library versions and store them in exports, together with the seed, γ and the algorithm name.
3. Expose **γ (resolution)** next to the seed, with a default of 1.0, and store it in exports. Given the resolution limit and degeneracy results, a single γ and a single seed should not be presented as *the* structure (see Section 5 on stability).
4. **Isolated nodes** (degree 0 after filtering) each come back as a one-node community. List them separately as "unclustered" rather than counting them as communities.
5. Show modularity alongside a **null-model reference**, for example the mean Q over a few degree-preserving randomisations [GSA04]. Otherwise readers will over-read Q.

---

## 2. Silhouette on graph communities

### Established

- Silhouette (Rousseeuw 1987): s(i) = (b(i) − a(i)) / max(a(i), b(i)), where a(i) is the mean distance from i to the other members of its cluster and b(i) is the lowest mean distance from i to any other cluster. Any dissimilarity can be used. For a one-member cluster, s(i) = 0 by definition, a neutral choice [R87, WP-SIL].
- scikit-learn `silhouette_score(X, labels, *, metric='euclidean', sample_size=None, random_state=None)`:
  - With `metric='precomputed'`, X is an n × n distance matrix [SK-SIL].
  - It is defined only when 2 ≤ n_labels ≤ n_samples − 1; otherwise `check_number_of_labels` raises `ValueError` [SK-SRC].
  - The diagonal must be zero (within `eps*100` for floats), otherwise it raises "non-zero elements on the diagonal. Use np.fill_diagonal(X, 0)" [SK-SRC].
  - One-member clusters produce NaN internally, which is replaced by 0 ("nan values are for clusters of size 1, and should be 0") [SK-SRC].
  - Input goes through `check_X_y`, whose defaults reject inf and NaN. An unreachable pair with infinite shortest-path distance therefore raises an error. This is my reading of sklearn's default validation, not an explicit statement in the silhouette docs.
  - `sample_size` subsamples using `random_state`. With n ≤ 400 it is unnecessary, so leave it as `None` for determinism.
- Weight-to-distance for shortest paths: tie weights are strengths, so they must be inverted before computing shortest paths. Opsahl et al. (2010) generalise this as d = min over paths of Σ (1/w)^α, where α tunes the balance between the number of ties and their weights [O10, O10-BLOG]. NetworkX `closeness_centrality(distance=...)` treats the attribute as a *distance*, so passing raw co-occurrence counts would be wrong [NX-CC].
- Silhouette rewards compact, roughly convex clusters [WP-SIL]. Modularity communities are not optimised for silhouette, so a valid modularity partition can still score low or negative.

### Options for the distance representation

| Option | Definition | Strengths | Pitfalls |
|---|---|---|---|
| **A. Weighted shortest path, d = 1/w** | Dijkstra on edge length 1/w_uv | Uses the same graph the clustering used; the standard inversion [O10] | In a dense tag graph, near-universal hub tags (e.g. Singleplayer) create shortcuts, so distances compress and silhouettes drift towards 0. Disconnected components give inf, which sklearn rejects, so cap the value or compute per component. Results depend on the transform. |
| **B. Shortest path, d = −log(w / w_max)** or d = 1 − w/w_max | log or linear transform | Additive along paths (log); bounded (linear) | The transform is an arbitrary modelling choice that must be justified; the linear form gives d = 0 for the heaviest edge, which breaks the zero-diagonal-only assumption; same inf issue as A |
| **C. Jaccard distance on game sets** | 1 − \|G_u ∩ G_v\| / \|G_u ∪ G_v\|, where G_t is the set of games that have tag t | Computed directly from the dataset, so it shares the edge-weight data (the intersection is the edge weight); defined for every pair (1.0 when two tags never co-occur), so no inf; bounded in [0, 1]; a true metric; normalises away raw tag frequency | Measures overlap of game sets, not graph topology, which is a different notion than the clustering objective (arguably a good thing for an independent check). Two rare tags that share one game look very close. |
| **D. Cosine distance on game-incidence vectors** | 1 − cos(x_u, x_v), where x_t is the binary game vector of tag t | Common, frequency-normalised | Not a true metric (fails the triangle inequality); silhouette does not require one, but say so. For binary vectors it behaves much like C. |
| **E. Cosine or Jaccard on adjacency rows** | Compares weighted neighbourhoods (structural equivalence) | Captures "tags with similar co-tags" | In dense co-occurrence graphs nearly every row looks alike, giving low contrast; double-counts hubs |

### When silhouette is undefined or misleading

- **One community, or every node its own community:** undefined, and sklearn raises an error. Show "n/a (k = 1)" rather than 0.
- **Singletons, including isolated nodes:** each contributes exactly 0 and pulls the mean towards 0. Report the mean over non-singleton nodes and the singleton count next to each other.
- **Disconnected components (options A and B):** infinite distances. Either compute only within the largest component or replace inf with a documented cap. Options C and D avoid the problem.
- **Mismatched objective:** the communities maximise modularity, not silhouette, so a low silhouette does not prove the communities are wrong. Treat silhouette as a diagnostic and never as the selection criterion.
- **Comparing across filter states:** silhouette depends on n and on the distance choice, so comparisons between filter states are only indicative.

### Recommendation

Use **option C (Jaccard on game sets)** as the primary silhouette distance. It is always finite, it is a metric, it is derived from the same data, and it needs no arbitrary weight transform. Optionally offer A as a secondary "graph-distance silhouette". Report per-node s(i), per-community mean, overall mean excluding singletons, and the singleton count. Fix `sample_size=None`.

---

## 3. Other quality measures

### Established

- **Weighted modularity Q:** see Section 1. It depends on γ, and absolute values are not comparable across graphs of different size or density because of degeneracy and fluctuations in random graphs [GMC10, GSA04].
- **Coverage and performance:** coverage is the fraction of edges that fall inside communities; performance is (intra-community edges + inter-community non-edges) / all possible pairs [F10]. **NetworkX `partition_quality(G, partition)` counts edges and ignores weights** [NX-PQ-SRC]. A weighted coverage has to be computed by hand as Σ intra-community weight / Σ total weight.
- **Conductance:** φ(S) = cut(S, S̄) / min(vol(S), vol(S̄)). NetworkX provides `conductance(G, S, T=None, weight=None)` with weights supported [NX-COND]. Kannan, Vempala and Vetta (2004) use conductance as a cluster-quality criterion [KVV04].
- **Intra-cluster density (weighted):** Σ internal weight / (n_c (n_c − 1) / 2). Fortunato (2010) gives intra- and inter-cluster density as the basic definitions of community quality [F10].

### Recommendation

For each state, report:
- global weighted Q, with a null-model reference value
- weighted coverage
- for each community: size, weighted internal density, weighted conductance, and a connectivity flag

Do not use `nx.community.partition_quality`, because it is unweighted. Keep all of these labelled as descriptive. They do not validate that the communities are meaningful, which is consistent with the standing constraint against auto-generated semantic cluster names.

---

## 4. Cluster-center measures

### Established

- **Within-community strength** is a node's weighted degree inside its own community. Guimerà and Amaral (2005) standardise it as a within-module degree z-score and pair it with a participation coefficient that measures how evenly a node's links spread across communities [GA05].
- **Closeness:** Freeman (1979). Disconnected graphs use the Wasserman–Faust correction (on by default as `wf_improved=True`), and the edge attribute passed to `distance=` must be a distance [NX-CC].
- **Eigenvector centrality:** the Perron–Frobenius eigenvector of A. A unique positive solution needs a (strongly) connected graph; on disconnected graphs the result is ambiguous. NetworkX iterates on A + I and raises `PowerIterationFailedConvergence` if it does not converge [NX-EC].
- **Medoid:** the member with the smallest total dissimilarity to the other members, as in PAM (Kaufman and Rousseeuw 1990) [KR90].

### Options

| Measure (computed within each community's induced subgraph) | Strengths | Pitfalls |
|---|---|---|
| **Intra-cluster weighted degree** (strength; optionally the z-score [GA05]) | O(E), deterministic, easy to explain ("co-occurs most with the other tags in this cluster") | Strongly biased towards frequent tags, so the generic tags present in most games will "lead" every cluster; ties are possible |
| **Closeness** (on 1/w distances) | Captures global centrality within the cluster | Needs a weight-to-distance transform; a Louvain community may be disconnected (Section 1); on small dense subgraphs nearly every node scores about the same |
| **Eigenvector centrality** (weighted) | Accounts for well-connected neighbours | Undefined or ambiguous on a disconnected subgraph; may fail to converge; on dense subgraphs it correlates closely with strength, so it adds little |
| **Graph medoid** (argmin Σ d, using the silhouette distance) | Consistent with the silhouette metric; with Jaccard it rewards "typical" tags rather than merely frequent ones | O(n_c²) cost, which is trivial at this size; ties; for 2-node communities the choice is arbitrary |

### Recommendation

Make the **medoid under the chosen silhouette distance** (Jaccard) the primary "center". Also report **intra-cluster weighted degree** as a second, more intuitive column, because it shows the frequency effect openly. Always break ties deterministically, for example by higher global frequency and then alphabetically, and record the tie-break rule. For communities with fewer than 3 nodes, show "n/a" for centers.

---

## 5. Node-removal sensitivity: cost and strategies

### Established

- Comparing partitions: the Adjusted Rand Index (Hubert and Arabie 1985) [HA85] and Variation of Information (Meilă 2007, a true metric) [M07]. scikit-learn provides `adjusted_rand_score`.
- Perturbation robustness: Karrer, Levina and Newman (2008) measure how much a partition changes when the network is randomly perturbed, and compare that with the change seen in random graphs [KLN08]. Consensus over repeated runs improves stability [LF12].

### Measured cost (synthetic data, this machine; NetworkX 3.4.2, Python 3.13)

The test graph was 100 synthetic "games" with 20 tags each, drawn from a Zipf-like distribution. **This is not real data.** It only shows the order of magnitude. Script: scratchpad `bench.py`, not kept in the repo.

| Nodes | Edges | One Louvain run | Full n-removal sweep (n reruns) | Silhouette (precomputed, n × n) |
|---|---|---|---|---|
| 50 | 1,222 | 15 ms | 0.9 s | 3 ms |
| 150 | 6,094 | 67 ms | 14 s | 2 ms |
| 352 | 11,009 | 184 ms | 74 s | 5 ms |

Takeaways:
- A full sweep in pure-Python NetworkX is **too slow to run interactively on every filter change** at the top of the range.
- Silhouette and the center measures cost almost nothing.
- Cost grows with the number of edges, and tag graphs are dense.

**Confound:** the synthetic graph has no planted structure (Q ≈ 0.0–0.1). Louvain still returned 3–6 communities, which illustrates the random-graph modularity point in [GSA04].

### Strategies (my recommendations; none of these is a literature prescription unless cited)

1. **Compiled implementation:** leidenalg/igraph runs in C++ and is reported to be faster than Louvain [T19]. I could not measure it here because the package is not installed.
2. **Warm start:** initialise G − v from the base partition with v removed, using leidenalg `initial_membership` or python-louvain `partition=`. This is faster and also reduces seed-order noise. Caveat: it biases the result towards the base partition, so document it.
3. **On demand rather than eager:** compute sensitivity only for a node the user selects, or as a background job with progress and a cache keyed by (dataset, thresholds, hidden genre tags, removed nodes, minimum months, seed, γ, library version).
4. **Restrict to top-k nodes** (for example by strength), or **parallelise** across processes, since each rerun is independent.
5. **Separate seed noise from real sensitivity:** before reading anything into ΔARI after removing v, measure the seed-to-seed ARI on the unperturbed graph across a few seeds. That is the noise floor. Removing a node also changes the shuffle order, so a naive comparison mixes the two effects. Compare partitions only on the shared node set V \ {v}.
6. Report Δ#communities, ΔQ (with the caveat from Section 3), and ARI or VI against the base partition.

---

## 6. Related issue to flag (out of the ticket's scope)

Raw co-occurrence counts are dominated by frequent tags. Bibliometrics recommends normalising co-occurrence (for example with *association strength*) before mapping and clustering [VEW09]. Whether edge weights should stay as raw counts, as CONTEXT.md currently defines them, or be normalised for clustering only, is a methodological decision for the researcher. It affects every result above.

---

## Summary of recommendations

| Topic | Recommended default | Alternatives |
|---|---|---|
| Algorithm | Leiden with the modularity objective (leidenalg `ModularityVertexPartition` or NX `metric='modularity'`), fixed seed, γ = 1 exposed | Louvain (as settled) plus a disconnected-community check; Leiden with CPM |
| Determinism | Canonical node and edge order, pinned versions, seed, γ, algorithm and versions in exports | — |
| Silhouette distance | Jaccard on game sets | 1/w shortest path; cosine |
| Silhouette reporting | Mean excluding singletons, plus singleton count; "n/a" when k < 2 or k = n | Mean including singletons (sklearn default) |
| Quality | Weighted Q with a null reference, weighted coverage, per-community density and conductance | `partition_quality` (unweighted, not recommended) |
| Center | Jaccard medoid, plus intra-cluster strength | Within-module z-score; eigenvector; closeness |
| Sensitivity | On demand or background, warm-started, compiled library, noise floor from multiple seeds | Eager full sweep (too slow in NX at about 350 nodes) |

---

## Sources

- [B08] Blondel, V. D., Guillaume, J.-L., Lambiotte, R., Lefebvre, E. (2008). Fast unfolding of communities in large networks. *J. Stat. Mech.* P10008. https://doi.org/10.1088/1742-5468/2008/10/P10008 (arXiv:0803.0476)
- [T19] Traag, V. A., Waltman, L., van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. *Scientific Reports* 9, 5233. https://doi.org/10.1038/s41598-019-41695-z (full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/)
- [N04] Newman, M. E. J. (2004). Analysis of weighted networks. *Phys. Rev. E* 70, 056131. arXiv:cond-mat/0407503
- [RB06] Reichardt, J., Bornholdt, S. (2006). Statistical mechanics of community detection. *Phys. Rev. E* 74, 016110. (cited by NetworkX `modularity` docs)
- [FB07] Fortunato, S., Barthélemy, M. (2007). Resolution limit in community detection. *PNAS* 104(1), 36–41. arXiv:physics/0607100
- [GSA04] Guimerà, R., Sales-Pardo, M., Amaral, L. A. N. (2004). Modularity from fluctuations in random graphs and complex networks. *Phys. Rev. E* 70, 025101(R).
- [GMC10] Good, B. H., de Montjoye, Y.-A., Clauset, A. (2010). The performance of modularity maximization in practical contexts. *Phys. Rev. E* 81, 046106. arXiv:0910.0165
- [LF12] Lancichinetti, A., Fortunato, S. (2012). Consensus clustering in complex networks. *Scientific Reports* 2, 336. arXiv:1203.6093
- [F10] Fortunato, S. (2010). Community detection in graphs. *Physics Reports* 486(3–5), 75–174. arXiv:0906.0612
- [R87] Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *J. Comput. Appl. Math.* 20, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7
- [KR90] Kaufman, L., Rousseeuw, P. J. (1990). *Finding Groups in Data: An Introduction to Cluster Analysis*. Wiley. (PAM / medoids)
- [O10] Opsahl, T., Agneessens, F., Skvoretz, J. (2010). Node centrality in weighted networks: generalizing degree and shortest paths. *Social Networks* 32(3), 245–251. [O10-BLOG] https://toreopsahl.com/2010/04/21/article-node-centrality-in-weighted-networks-generalizing-degree-and-shortest-paths/
- [GA05] Guimerà, R., Amaral, L. A. N. (2005). Functional cartography of complex metabolic networks. *Nature* 433, 895–900.
- [KVV04] Kannan, R., Vempala, S., Vetta, A. (2004). On clusterings: good, bad and spectral. *J. ACM* 51(3), 497–515.
- [HA85] Hubert, L., Arabie, P. (1985). Comparing partitions. *J. Classification* 2, 193–218.
- [M07] Meilă, M. (2007). Comparing clusterings: an information based distance. *J. Multivariate Analysis* 98, 873–895.
- [KLN08] Karrer, B., Levina, E., Newman, M. E. J. (2008). Robustness of community structure in networks. *Phys. Rev. E* 77, 046119.
- [VEW09] van Eck, N. J., Waltman, L. (2009). How to normalize cooccurrence data? An analysis of some well-known similarity measures. *JASIST* 60(8), 1635–1651.
- [WP-SIL] Wikipedia, "Silhouette (clustering)" (secondary source, used only for the singleton convention attributed to [R87]). https://en.wikipedia.org/wiki/Silhouette_(clustering)
- [NX-LV] NetworkX docs, `louvain_communities`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html
- [NX-LD] NetworkX docs, `leiden_communities`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.leiden.leiden_communities.html ; [NX-LD-SRC] https://networkx.org/documentation/stable/_modules/networkx/algorithms/community/leiden.html (v3.7)
- [NX-Q] NetworkX docs, `modularity`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.quality.modularity.html
- [NX-PQ-SRC] NetworkX source, `community/quality.py` (`partition_quality` counts edges, ignores weights). https://github.com/networkx/networkx/blob/main/networkx/algorithms/community/quality.py
- [NX-COND] NetworkX docs, `conductance`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cuts.conductance.html
- [NX-CC] NetworkX docs, `closeness_centrality`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.closeness_centrality.html
- [NX-EC] NetworkX docs, `eigenvector_centrality`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.eigenvector_centrality.html
- [PL] python-louvain API. https://python-louvain.readthedocs.io/en/latest/api.html
- [LA] leidenalg reference. https://leidenalg.readthedocs.io/en/stable/reference.html
- [IG-SRC] python-igraph source, `community.py` (`_community_leiden`). https://github.com/igraph/python-igraph/blob/main/src/igraph/community.py
- [IG-DISC] igraph forum, "Set up seed for community_leiden". https://igraph.discourse.group/t/set-up-seed-for-community-leiden/2193
- [SK-SIL] scikit-learn docs, `silhouette_score`. https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html
- [SK-SRC] scikit-learn source, `metrics/cluster/_unsupervised.py`. https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/metrics/cluster/_unsupervised.py

Citation caveat: [B08], [T19], [N04], [FB07], [GMC10], [LF12] and all library docs and sources were checked during this research. [RB06], [GSA04], [GA05], [KVV04], [HA85], [M07], [KLN08], [VEW09] and [KR90] are standard references cited from bibliographic knowledge, and their exact page numbers should be verified before they go into a publication.
