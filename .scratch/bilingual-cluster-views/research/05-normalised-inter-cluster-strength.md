# Research 05: Normalised inter-cluster strength in the literature

Answers [ticket 05](../issues/05-normalised-inter-cluster-strength.md). The question: which established measures say how strongly two Clusters connect while allowing for their sizes, and what does each one assume? The decision belongs to [ticket 06](../issues/06-inter-cluster-measures.md). Checked 2026-10-27.

## How to read this file

- **Established** = stated in the cited source, paraphrased, with a locator. Where only the arXiv text was read, the locators are from that text.
- **Inference** = my own derivation or reading, with the argument given. Not citable as such.
- **Measured** = run on Build `20261008T221504Z-7a23ae9f` with a throwaway script kept outside the repo. Section 8 has the exact settings.
- **Recommendation** = non-binding. Ticket 06 decides.

Notation, for one Network State:

| Symbol | Meaning |
|---|---|
| a, b | two groups: Multi-Tag Clusters, or the `one_tag_pool` |
| n_a | number of Tags in a |
| w_ij | weight of edge i–j in the weight being measured (shared games, or Lift) |
| w_ab | sum of w_ij over the edges with one end in a and one in b. This is `metrics.connections`' `weight` when measured in the Clustering Weight |
| e_ab | number of such edges (`edge_count`) |
| k_i | strength of tag i, Σ_j w_ij |
| k_a = vol(a) | Σ_{i∈a} k_i = 2·`internal_weight` + `cut_weight` of `cluster_metrics` |
| 2m | Σ_i k_i |
| G_a | set of games that have at least one tag of a |
| N | number of games the network is built from |
| γ | the resolution |

## Summary

- **Six families of measure exist.** Each gets a section below.
  1. Between-cluster density.
  2. Observed against configuration-model expected weight, as a difference (the modularity term) or as a ratio.
  3. Normalised cut, conductance and random-walk shares.
  4. Block-model affinity ω_ab, in the plain SBM and in the degree-corrected SBM.
  5. Game-set similarity: Jaccard, cosine, and association strength, i.e. a cluster-level Lift.
  6. PAGA connectivity.
- **Two of the textbook ideas are the same number.** Take the configuration-model ratio r_ab = w_ab / (k_a k_b / 2m).
  - Established: it is the observed-to-expected term inside the degree-corrected SBM log-likelihood [KN11 eq. (24)].
  - Inference: up to the constant 2m, it is the degree-corrected maximum-likelihood block affinity ω̂_ab/(κ_a κ_b) [KN11 eq. (18)].
  - Inference: it is the pair-specific version of Newman's ω_out [N16 eq. (18)], which Parameter Selection already uses. Pooled over all pairs, the r_ab give ω_out exactly (§3.3).
  - Established: association strength is the same form, c_ij/(s_i s_j), when the occurrence totals are strengths [VEW09 eqs. (2), (5), §4].
  - The plain-SBM ω̂_ab = w_ab/(n_a n_b) [KN11 eq. (5)] is exactly the between-cluster density.
- **Only r_ab is tied to the clustering objective.**
  - Established: merging a and b changes modularity by ΔQ = 2(e_ab − a_a a_b) [N04f §II]. This is the γ = 1 case.
  - Inference: for resolution γ, ΔQ_ab = (w_ab − γ k_a k_b/2m)/m. The merge raises Q exactly when **r_ab > γ**.
  - Established: Louvain and Leiden both guarantee γ-separation, meaning no two communities can be merged [TWvE19 §III, Table I, Definition 5, Theorem 4].
  - So for every pair of Clusters the app shows, in the Clustering Weight, **0 ≤ r_ab ≤ γ**.
  - Inference: the bound carries over to the `one_tag_pool` rows (§3.4).
  - Measured: it held on all 25 Network States tried, pool rows included.
  - CPM's analogue is between-cluster density read against γ [TVN11 §II.B]. The app does not use CPM, so density is not tied to its objective.
- **The weights behave differently.**
  - Established: shared-game counts fit the multigraph reading of modularity and the SBM [N04w §II; KN11 §II].
  - Established: real-valued weights such as Lift carry over to modularity by a change of unit [N04w §II, §II.C].
  - Established: in the SBM, real-valued weights are edge covariates, not edge counts [P18 §II].
  - Inference: the ratio and density formulas are defined for Lift, but no likelihood stands behind them. Research 01 §3.2 found the same for γ̂.
  - Measured: under Lift, the shared-game ratio on the Lift partition is not bounded by γ (up to 1.45 at γ = 1).
- **Two-tag clusters, zero pairs and the pool.**
  - Every measure gives 0 for a pair with no edges. No denominator is zero unless a group has zero strength.
  - Density is inflated for two-tag Clusters. Measured: up to 10.0 shared games per tag pair, against at most 5.9 for larger pairs in the same state. The reason is that n_a n_b is tiny.
  - Strength-based measures (r_ab, Ncut) are not inflated this way, because k_a grows with the cluster's actual edges.
  - Isolated tags in the pool add to n but not to k. So density dilutes pool rows, and strength measures ignore isolated tags.
- **Game-set measures are close to saturated here.**
  - Measured: Top-100 games carry up to 20 tags, so one Multi-Tag Cluster's games cover a median 39–96% of all games, across the 20 non-default states.
  - Measured: at the default states, the median pair Jaccard is 0.41–0.88 and the median cluster-level Lift is 0.98–1.00.
  - They describe game overlap, not the graph that was clustered, and are not consistent with modularity.
- **PAGA connectivity** [WOL19 Methods; scanpy source] is a size-normalised ratio of observed to expected inter-edges, capped at 1.
  - It is built for unweighted kNN graphs and its null is a size-based one.
  - Inference: it does not fit weighted co-occurrence graphs.
- **Recommendation (non-binding; ticket 06 decides)**:
  - Headline: the configuration-model ratio r_ab. It is the degree-corrected block affinity relative to the null, computed in the Clustering Weight.
    - Read as "times the weight expected from the two Clusters' strengths".
    - Its natural ceiling is γ.
    - Under Lift, a shared-game version is labelled separately and is not γ-bounded.
  - Per-cluster view: the share w_ab / cut_a, which already sums to 1 across a cluster's row.
  - Density: only as a secondary column, if at all.
  - Not recommended: game-set Jaccard or cluster Lift, and PAGA.

---

## 1. Between-cluster density

### 1.1 What the sources say

**Established**
- Intra- and inter-cluster density of a cluster C:
  - δ_int(C) = (internal edges)/(n_c(n_c − 1)/2), and δ_ext(C) = (edges from C to the rest)/(n_c(n − n_c)) [F10 §III.B.1, eqs. (1)–(2)].
  - A community should have δ_int well above the graph's average density and δ_ext well below it [F10 §III.B.1].
  - Footnote 2 of [F10 §III.B] says that in weighted graphs communities may instead be "subgraphs with a high internal density of weight".
- Cut ratio, the per-community version against the rest of the graph: c_S/(n_S(n − n_S)) [YL12 §2, scoring-function list].
- The plain stochastic block model:
  - Source of the model: [HLL83]. Its modern statement: [FH16 §II.C].
  - Maximum-likelihood estimate given a partition: **ω̂_rs = m_rs/(n_r n_s)** [KN11 §II, eq. (5)].
  - m_rs = Σ_ij A_ij δ(g_i,r) δ(g_j,s) counts the edges between r and s, or twice that number when r = s [KN11 eq. (3)].
  - Eq. (7) rewrites the profile likelihood with the ratio (m_rs/2m)/(n_r n_s/n²). That ratio is the pair's density divided by the graph's mean density.
  - KN11 note that this uniform null model gives Poisson degrees [KN11 §II]. They reject it for real networks for that reason: structure caused merely by the degree sequence gets attributed to the groups.
- CPM:
  - Splitting a community into r and s is better whenever e_rs/(2 n_r n_s) < γ. That ratio "is exactly the density of links between community r and s" [TVN11 §II.B].
  - For CPM, between-cluster density is read directly against γ [TWvE19 §II, the CPM paragraph after the CPM quality function].

### 1.2 Pairwise measure here

D_ab = w_ab / (n_a n_b), the mean edge weight over all n_a·n_b tag pairs, with missing edges counted as 0. This is the existing `weighted_density` idea from `cluster_metrics`, applied between two clusters, and it is ω̂_ab of the plain SBM.

| Aspect | Reading |
|---|---|
| Range | 0 up to the largest edge weight. On shared games the unit is shared games per tag pair; on Lift it is mean Lift per tag pair, zeros included. |
| Zero-edge pair | 0. Always defined, since n_a, n_b ≥ 1. |
| Two-tag clusters | **Unstable**. The denominator is tiny, so one heavy edge dominates. Measured: on overall, shared games, Leiden at γ = 2.5, the densest pair involving a two-tag Cluster reaches 10.0, against at most 5.89 for all other pairs. |
| `one_tag_pool` | n counts isolated tags, which have no edges, so pool rows are diluted by tags that cannot connect. A pool-pool density would use the pairs of distinct One-Tag Clusters, (n_p choose 2). |
| Size awareness | By tag count only. It ignores that common tags have many more shared games: the degree problem that KN11 §II describes. Measured on shared games: D_ab still correlates with k_a k_b (Spearman +0.50 to +0.85 in four of five datasets at the default state). |
| Network States | Not comparable on shared games. Its scale moves with N, with g and s and with the Minimum Months Filter. More comparable on Lift. |
| Consistency with clustering | Only with CPM [TVN11], which the app does not offer. Not with modularity. |
| Threshold caveat (Inference) | A tag pair below the minimum shared games has no edge and counts as 0, so "density" here means density of above-threshold co-occurrence. This applies to every graph-based measure in §1–§3. |

## 2. Observed against configuration-model expected weight

### 2.1 What the sources say

**Established**
- Newman & Girvan's mixing matrix:
  - e_ij is the fraction of all edges that link community i to community j, and a_i = Σ_j e_ij.
  - "In a network in which edges fall between vertices without regard for the communities they belong to, we would have e_ij = a_i a_j". Then Q = Σ_i (e_ii − a_i²) [NG04 §IV, eq. (5)].
  - Note [49] warns about the factors of 2: an edge between i and j is split half-and-half between e_ij and e_ji.
- The change in Q from joining two communities is **ΔQ = e_ij + e_ji − 2 a_i a_j = 2(e_ij − a_i a_j)**. "Joining … a pair of communities between which there are no edges at all can never result in an increase in Q" [N04f §II].
- Weighted networks:
  - A weighted network maps to a multigraph, one parallel edge per unit of weight. Non-integer weights are handled by shrinking the unit [N04w §II, last paragraphs before §II.A].
  - The weighted modularity is "precisely the same formula", eq. (9), with A_ij the weight and k_i the strength [N04w §II.C].
- The configuration null model: P_ij = k_i k_j/2m, giving p_degree(r,s) = (κ_r/2m)(κ_s/2m), with κ_r the sum of degrees in group r [KN11 §II, eqs. (11)–(12)].
- Resolution form:
  - Q(γ) = (1/2m) Σ_ij (A_ij − γ k_i k_j/2m) δ(c_i,c_j) [N16 eq. (6)]. This is what the app optimises (`nx.community.louvain_communities(..., resolution=γ)`; `la.RBConfigurationVertexPartition`).
  - TVN11 rewrite modularity as H = −Σ_c (e_c − γ[e_c]) and read e_c/[e_c] as a "degree density". Within communities it should exceed the threshold, and between them it should be lower [TVN11 App. B, eq. (B4) and the paragraph after it].
- Leiden guarantees:
  - Definition 5: a pair of communities C, D is γ-separated if ΔH(C → D) ≤ 0.
  - Theorem 4: every iteration of Leiden returns a γ-separated partition.
  - "The property of γ-separation also holds after each iteration of the Louvain algorithm" [TWvE19 App. B Def. 5; App. D.1 Thm. 4 and the paragraph after it; §III and Table I]. Both modularity and CPM are covered.

### 2.2 The two pairwise forms

For groups a ≠ b, the expected weight between them under the configuration model is E_ab = Σ_{i∈a, j∈b} k_i k_j/2m = k_a k_b/2m. **Inference** (algebra).

- **Difference, or the modularity term.** Inference, from N04f with weights [N04w] and γ [N16 eq. (6)]: ΔQ_ab(γ) = (w_ab − γ k_a k_b/2m)/m. At γ = 1 this is 2(e_ab − a_a a_b) with e_ab = w_ab/2m and a_a = k_a/2m.
- **Ratio.** r_ab = w_ab / (k_a k_b/2m) = 2m·w_ab/(k_a k_b). It is 1 when the two Clusters share exactly the weight their strengths predict.

**Inference: the γ bound.**
- ΔQ_ab(γ) > 0 exactly when r_ab > γ.
- Louvain's and Leiden's output is γ-separated [TWvE19 Thm. 4 and §III], so for every pair of Clusters in the Clustering Weight, r_ab ≤ γ, and so ΔQ_ab ≤ 0.
- The app's Louvain stops at a gain threshold of 1e-7 (`cluster.LOUVAIN_THRESHOLD`), so the guarantee is "up to that tolerance".
- Leiden here runs until a pass gains nothing, or until `PASS_CAP`.
- **Measured:** no pair exceeded γ in any of the 25 Network States in §8, including pool rows. The largest r_ab was close to γ: 0.98 at γ = 1, 2.50 at γ = 2.5, 1.95 at γ = 2.

| Aspect | Ratio r_ab | Difference ΔQ_ab |
|---|---|---|
| Range | 0 up to 2m/max(k_a,k_b) in general. For Clusters of a γ-separated partition, in the Clustering Weight, [0, γ]. | ≤ 0 for every pair of Clusters shown, in the Clustering Weight. The lower end is −γ k_a k_b/(2m²) for a zero pair. |
| Reading | 1 = as much weight as the two strengths predict; < 1 = less. Because the clustering has already separated them, values well below 1 are normal at γ = 1. A value near γ means the pair is close to being merged at this resolution. | How much Q would fall, as a fraction of total weight, if the two were merged. It depends on K and m, so it is not a "strength". |
| Zero-edge pair | 0 | −γ k_a k_b/(2m²), which is still informative |
| Two-tag clusters | Stable. k_a counts the cluster's real edges, internal and external, so a small cluster with few edges has a small expectation. A two-tag Cluster with one strong external edge can still reach γ, but no further. | Small in magnitude |
| `one_tag_pool` | Well defined; isolated tags contribute k = 0. For pool–pool, use E_pp = Σ_{i<j in pool} k_i k_j/2m = (k_p² − Σ_i k_i²)/4m, not k_p²/4m (Inference). | Same |
| Weights | Shared games: the multigraph reading is exact [N04w]. Lift: defined, by the unit change of [N04w §II], but there is no null-model or likelihood interpretation beyond "Lift-strength-proportional". Lift is already a tag-level observed/expected ratio, so this is a second normalisation. | Same |
| Size awareness | By strength, the degree correction of KN11 §II. Measured: on the default states, Spearman of r_ab with k_a k_b ranges from −1.0 to +0.55. It has no consistent sign, unlike raw w_ab (+0.77 to +1.0 in eight of ten states). | By strength |
| Network States | Dimensionless with a fixed null value of 1, so comparable as a ratio. But the ceiling γ moves with the resolution, so across different γ compare r_ab/γ or state the γ. | Poor: it scales with 1/m and with the whole partition |
| Consistency with clustering | **Exact**: it is the merge test of the objective the app optimises | Exact (same test) |

## 3. Block-model affinity ω_ab

### 3.1 Plain SBM

ω̂_ab = m_ab/(n_a n_b) [KN11 eq. (5)]. This is §1.

### 3.2 Degree-corrected SBM

**Established**
- Expected A_ij = θ_i θ_j ω_{g_i g_j}, with Σ_{i∈r} θ_i = 1 [KN11 §III, eqs. (14)–(15)].
- Maximum-likelihood estimates: θ̂_i = k_i/κ_{g_i} and **ω̂_rs = m_rs** [KN11 eq. (18)]. The expected edges between i and j are then k_i k_j m_rs/(κ_r κ_s).
- The profile log-likelihood is **L = Σ_rs m_rs log(m_rs/(κ_r κ_s))** [KN11 eq. (23)]. In normalised form it is Σ_rs (m_rs/2m) log[(m_rs/2m)/((κ_r/2m)(κ_s/2m))] [KN11 eq. (24)].
- KN11 read eq. (24) as the KL divergence between the observed edge-end distribution p_K and p_degree, which is the mutual information of the group labels at the two ends of an edge [KN11 §III, after eq. (24)].
- The only difference from the plain-SBM likelihood is "the replacement of the number n_r of vertices in each group by the number κ_r of stubs" [KN11 §III, after eq. (23)].

**Inference**
- The argument of KN11 eq. (24)'s logarithm, for r ≠ s, is (w_rs/2m)/((k_r/2m)(k_s/2m)) = r_rs.
- The configuration ratio is therefore the degree-corrected block affinity per unit of null expectation. Put another way, the fitted DC-SBM edge rate between i ∈ a and j ∈ b, divided by the configuration null's rate k_i k_j/2m, is r_ab.
- So "SBM ω_ab" and "observed/expected" are one candidate, in two flavours:
  - plain = density;
  - degree-corrected = r_ab.
- The Clusters were found by modularity, not by fitting an SBM. So ω̂ is a plug-in estimate given the partition, never a claim that a block model fits.

### 3.3 Link to Newman's ω_out (already in the app)

**Established**: [N16 eq. (18)], as used in Research 01 §3.1: ω_out = (2m − 2m_in)/(2m − Σ_r κ_r²/2m).

**Inference**
- The numerator is 2·Σ_{a<b} w_ab. The denominator is 2·Σ_{a<b} k_a k_b/2m.
- So ω_out = Σ_{a<b} w_ab / Σ_{a<b} E_ab, the expectation-weighted mean of the pairwise r_ab.
- Parameter Selection's γ̂ already depends on this pooled value. r_ab splits it by pair.
- The planted-partition model assumes one ω_out for all pairs. The spread of r_ab shows how far that assumption is from this graph.
- Caveat: N16's groups are every community, and `one_tag_pool` is not one. The identity holds over all groups of positive strength, with each One-Tag Cluster separate.

### 3.4 The `one_tag_pool` under the γ bound

**Inference**
- Each One-Tag Cluster {i} is a community of the γ-separated partition, so w_ia ≤ γ k_i k_a/2m for every Cluster a.
- Summing over the pool gives w_pa ≤ γ k_p k_a/2m, so r_pa ≤ γ.
- For pool–pool, summing over distinct pairs gives w_pp ≤ γ·E_pp with E_pp as in §2.2.
- So the pooled rows obey the same ceiling, provided E_pp is computed over distinct pairs.

### 3.5 Weighted SBMs

**Established**
- [P18 §II]: weighted SBMs treat weights as "edge covariates", sampled per block pair, separately from edge placement. The original SBMs are "defined strictly for simple or multigraphs" [P18 §I].
- [KN11 §II] allow multi-edges as Poisson counts.

**Inference**
- Shared-game counts are integer multiplicities and fit KN11 directly.
- Lift does not fit KN11. A weighted SBM would model the Lift values between a and b as a distribution, for example their mean, alongside the edge-count affinity.

## 4. Normalised cut, conductance and random-walk shares

### 4.1 What the sources say

**Established**
- Normalised cut:
  - Ncut(A,B) = cut(A,B)/assoc(A,V) + cut(A,B)/assoc(B,V), where assoc(A,V) is the total weight from A to all nodes [SM00 §2, eq. (2)].
  - It was introduced against min-cut's bias "for partitioning out small sets of points". Nassoc is eq. (3), and Ncut = 2 − Nassoc is eq. (4) [SM00 §2].
- k-way forms:
  - Ncut(A_1..A_k) = ½ Σ W(A_i, Ā_i)/vol(A_i), and RatioCut uses |A_i| in place of vol(A_i) [VL07 §5].
  - vol(A) = Σ_{i∈A} d_i [VL07 §2.1].
- Random-walk reading: for a walk started from the stationary distribution, Ncut(A, Ā) = P(Ā|A) + P(A|Ā) [VL07 §6, Proposition 5, after Meilă & Shi 2001].
- Conductance of a community: cut/min(vol(S), vol(V∖S)) [YL12 §2 list; LLDM08]. This is the app's per-Cluster `conductance`.

### 4.2 Pairwise forms here

**Inference**. These are restrictions of the cited definitions to one pair. No source defines a pairwise normalised cut inside a larger partition, so the forms below are adaptations.

- Share of a's strength going to b: P(b|a) = w_ab / k_a. By the [VL07 Prop. 5] argument, this is the probability that one step of a stationary random walk in a lands in b.
- Symmetric pairwise Ncut: N_ab = w_ab/k_a + w_ab/k_b = P(b|a) + P(a|b), in [0, 2].
- Pairwise conductance: w_ab / min(k_a, k_b), in [0, 1].
- Share of a's external weight: w_ab / cut_a. It sums to 1 over a's row, because every external edge of a goes to another Multi-Tag Cluster or to the pool. This is exactly what ticket 06's per-cluster view asks for.

| Aspect | Reading |
|---|---|
| Size awareness | By volume (strength), like r_ab, but linear in 1/k rather than in 1/(k_a k_b). N_ab = w_ab(k_a + k_b)/(k_a k_b), while r_ab = 2m·w_ab/(k_a k_b). Inference: N_ab = r_ab·(k_a + k_b)/2m, so N_ab rises with the pair's share of total strength. Measured: N_ab correlates with k_a k_b at +0.53 to +1.0 on most states, close to raw w_ab. It is less size-neutral than r_ab. |
| Zero pair | 0 |
| Two-tag | Stable, through volume |
| Pool | Defined; isolated tags add nothing |
| Network States | Bounded and unit-free, so comparable in range, but it has no null value and no γ link |
| Consistency with clustering | None with modularity. Spectral or Ncut clustering optimises it, and the app does not use that. |

## 5. Game-set similarity: Jaccard, cosine, association strength

### 5.1 What the sources say

**Established**
- Definitions [VEW09 §2]:
  - Association strength S_A = c_ij/(s_i s_j), eq. (5).
  - Cosine c_ij/√(s_i s_j), eq. (6).
  - Inclusion c_ij/min(s_i, s_j), eq. (7).
  - Jaccard c_ij/(s_i + s_j − c_ij), eq. (8).
  - s_i is either the occurrence count, eq. (1), or the total co-occurrence count, eq. (2).
- Jaccard and cosine are "set-theoretic". Association strength is the only "probabilistic" measure, up to proportionality [VEW09 §4, Proposition 4.1].
- c_ij/e_ij with e_ij = s_i s_j/m equals m·S_A. It is above 1 when the two co-occur more than chance would predict [VEW09 §4, final paragraphs].
- Their conclusion: co-occurrence data "can best be normalized using a probabilistic measure" [VEW09 abstract, §6].

**Inference**
- The project's tag-level Lift (`graph.shared_edges`: shared·N/(|G_u||G_v|)) is N·S_A with occurrence totals, eq. (1).
- Applied to Clusters, it gives two different numbers:
  - **Cluster Lift** (occurrence form): |G_a ∩ G_b|·N/(|G_a||G_b|), counted over games.
  - **Strength form**, eq. (2): w_ab/(k_a k_b) ∝ r_ab, which is §2 again.

### 5.2 Fit here

- These measures count games, not tag pairs.
  - Inference, from `graph.shared_edges`: w_ab is a sum over tag pairs, so a game with x tags in a and y in b adds x·y to w_ab (above-threshold edges only).
  - |G_a ∩ G_b| counts that game once.
  - That makes them the only candidates that answer "how many games combine the two Clusters". The current guide's "a total weight of 58 shared games" is really 58 shared-game tag-pair incidences. Ticket 06 should word this.
- **Measured, the saturation problem.**
  - Top-100 games carry up to 20 tags. Across the 20 non-default states, each Multi-Tag Cluster's game set covers a median 39–96% of all games, and the smallest single Cluster covers 9%.
  - At the default states, the median pair Jaccard is 0.41–0.88 and the median cluster Lift is 0.98–1.00.
  - The values separate more at high γ (Leiden at γ = 2–2.5), where there are many small Clusters: Jaccard medians of 0.24–0.43, and cluster Lift from 0.0 to 1.95.
- They ignore the edge threshold s, because they are computed from the game–tag table. They are therefore not a property of the network that was clustered, and they have no link to modularity.
- Two-tag clusters and the pool: defined, with |G_a| ≥ the minimum games per tag. The pool's game set is the union over unrelated tags, so it is hard to read.
- Network States: Jaccard and cosine are in [0, 1]. Cluster Lift has a null value of 1. Both still depend on how many tags a Cluster has, because bigger Clusters cover more games and push both toward saturation.
- An existing glossary term, **Cluster Center**, already uses Jaccard on game sets. Reusing Jaccard here for a different purpose risks confusion.

## 6. PAGA connectivity

**Established**
- PAGA weights the edges of a cluster graph by a "connectivity" measure: "the ratio of the number of inter-edges between the clusters normalized with the number of inter-edges expected under random assignment of edges". It has "a close relation with modularity" [WOL19 Methods, "PAGA connectivity"; full definition in Additional file 1, eq. (11), not read].
- Source check, scanpy `_compute_connectivities_v1_2` (`scanpy/tools/_paga.py`, v1.10.4):
  - It **binarises** the kNN graph.
  - It counts e_i, the edges with an endpoint in group i, and the inter-edges (ε_ij + ε_ji).
  - Expected = (e_i n_j + e_j n_i)/(n − 1).
  - Connectivity = observed/expected, **capped at 1**.

**Inference**
- It is a size-normalised observed/expected ratio, like r_ab. Its null spreads group i's edge ends uniformly over the other *nodes* (n_j/(n − 1)), whereas modularity spreads them over other *edge ends* (k_j/2m).
- On a kNN graph every node has the same out-degree, so the difference matters little there. On a co-occurrence graph with very unequal strengths it would bring back the size bias that KN11 §II warns about.
- Binarisation throws away the shared-game weights.
- The cap at 1 turns it into a confidence that two clusters are connected, not a strength.
- Not recommended. It is the same idea as r_ab, with a null that does not fit weighted co-occurrence graphs.

## 7. Fit with what the app has

**Inference**, from `metrics.py`, `graph.py` and `tables.py`.

- **`metrics.connections`** gives (a, b, edge_count, weight) with weight in the **Clustering Weight** (`d["w"]`).
  - Under Lift, the existing `weight` column is therefore the Lift sum, not the shared-game sum.
  - The map's settled wording ("total inter-cluster edge weight means the shared-game sum; under Lift a second total") needs a new, additive shared-game column under Lift. `weight` must keep its meaning (hard rule: no redefinition).
- **Strengths**: k_a in the Clustering Weight is 2·`internal_weight` + `cut_weight` from `cluster_metrics`.
  - For the pool, k_p is the sum of member strengths.
  - Shared-game strengths under Lift come from `node_metrics.strength_shared`, summed over members.
  - 2m = 2·`total_weight`.
  - So r_ab, N_ab and the shares need no new graph pass, only sums over existing per-tag values.
- **Conductance and Coverage**:
  - Coverage = internal/total.
  - Inference: Coverage = 1 − Σ_{rows} w_ab/m in the Clustering Weight, summing every `connections` row (pool–pool included). The rows partition the inter-cluster weight.
  - Per-Cluster conductance is cut/min(vol, rest).
  - The pairwise measures in §4 split `cut_weight` by partner, so they line up with the existing columns.
- **`one_tag_pool`**:
  - Every strength-based measure is well defined on it and ignores isolated tags.
  - The γ bound carries over (§3.4) if the pool–pool expectation uses distinct pairs.
  - Density is diluted by isolated tags.

## 8. Measurements

**Measured**

- Build `20261008T221504Z-7a23ae9f`, all five Top-100 Datasets.
- 25 Network States in total:
  - each dataset's default Network State (g = s = 8, γ = 1, Louvain, seed 0), on Shared games and on Lift;
  - plus Shared games with Louvain at γ = 1.5;
  - Shared games with Leiden at γ = 2.5;
  - Lift with Leiden at γ = 2.0;
  - Lift with Louvain at γ = 0.6.
- Clusters came from `state.cluster_graph`. Measures were computed per pair of groups as in the notation table, with the pool treated as one group. Pool–pool pairs were not computed.

| Finding | Values |
|---|---|
| Pairs of Multi-Tag Clusters per state | 1–105. Zero-edge pairs: 0–31 per state. |
| Max r_ab vs γ, in the Clustering Weight, pool rows included | 0.78–0.98 at γ = 1; 1.06–1.48 at γ = 1.5; 2.23–2.50 at γ = 2.5; 1.62–1.95 at γ = 2; 0.44–0.57 at γ = 0.6. **Never above γ** (25/25 states). |
| Shared-game r_ab on a Lift partition (γ = 1) | max 1.02–1.45. Not γ-bounded, as expected. |
| Spearman(raw w_ab, k_a k_b), default states | +0.77 to +1.00 in eight of ten; −0.50 and −0.04 in the other two. Raw totals mostly track size. |
| Spearman(r_ab, k_a k_b), default states | −1.00 to +0.55, with no consistent sign |
| Two-tag density inflation | Max density on pairs with a two-tag Cluster: 10.0 / 9.17 / 8.00 / 6.25 (overall / puzzle / RPG / strategy, Shared games, Leiden γ = 2.5), against 5.89 / 7.00 / 6.17 / 5.47 for the other pairs |
| Game-set coverage of one Multi-Tag Cluster (20 non-default states) | median 0.39–0.96 of all games, depending on γ; smallest single Cluster 0.09 |
| Default-state pair Jaccard / cluster Lift | Jaccard median 0.41–0.88; cluster Lift median 0.98–1.00 |

## 9. Comparison

| Measure | Formula (a ≠ b) | Source | Range, reading | Weights | Two-tag / zero / pool | Across Network States | Consistent with modularity |
|---|---|---|---|---|---|---|---|
| Raw total | w_ab, e_ab | (existing) | ≥ 0; not size-aware | both | fine / 0 / fine | no | — |
| Density (plain-SBM ω̂) | w_ab/(n_a n_b) | F10 eqs. (1)–(2); KN11 eq. (5); TVN11 §II.B | ≥ 0; weight per tag pair | Lift: mean Lift with 0s | **inflated** / 0 / diluted by isolated tags | shared: no; Lift: partly | no (CPM's test) |
| **Config ratio (DC-SBM affinity / null)** | 2m·w_ab/(k_a k_b) | NG04 eq. (5); N04f §II; KN11 eqs. (18), (23)–(24); N16 eq. (18); TWvE19 Thm. 4 | ≥ 0; 1 = as expected; **≤ γ** for shown Clusters | shared: multigraph-exact; Lift: defined, no likelihood | stable / 0 / fine (distinct-pair E_pp) | yes as a ratio; state γ | **yes: merge test r_ab > γ** |
| Modularity term | (w_ab − γ k_a k_b/2m)/m | N04f §II; N16 eq. (6) | ≤ 0 for shown Clusters | as above | stable / negative / fine | poor (∝ 1/m) | yes (same test) |
| Pairwise Ncut | w_ab/k_a + w_ab/k_b | SM00 eq. (2); VL07 §5, §6 Prop. 5 | [0, 2]; walk-step probabilities | both | stable / 0 / fine | bounded, no null | no |
| Share of a's cut | w_ab/cut_a | (Inference from the above) | [0, 1], row sums to 1 | both | stable / 0 / fine | bounded | no |
| Jaccard on game sets | \|G_a∩G_b\|/\|G_a∪G_b\| | VEW09 eq. (8) | [0, 1]; **saturated here** | ignores edges | fine / >0 even with no edge / hard to read | yes, but size-dependent | no |
| Cluster Lift (association strength) | \|G_a∩G_b\|·N/(\|G_a\|\|G_b\|) | VEW09 eq. (5), §4 | ≥ 0; 1 = chance; **≈ 1 here** | ignores edges | fine / fine / hard to read | yes | no |
| PAGA connectivity | inter/((e_a n_b + e_b n_a)/(n − 1)), cap 1 | WOL19 Methods; scanpy source | [0, 1] confidence | **binarised** | fine / 0 / — | yes | loosely ("close relation") |

## 10. Recommendation (non-binding; the decision belongs to ticket 06)

1. **Headline normalised strength: the configuration-model ratio r_ab = w_ab / (k_a k_b / 2m)**, in the Clustering Weight.
   - It is the only candidate that matches what the clustering itself optimises (the merge test r_ab > γ).
   - It is the degree-corrected block affinity [KN11], so it allows for size the way the literature recommends: by strength, not by tag count.
   - It is stable for two-tag Clusters, 0 for zero pairs, and well defined for the pool.
   - Its reading has a built-in reference: 1 = what the strengths alone predict, and γ = the most the clustering allows. Values near γ mark pairs that are nearly one Cluster at this resolution.
   - Show γ beside it, because its ceiling moves with γ.
2. **Under Lift** (settled while charting: a normalised strength for both totals):
   - Compute r_ab on the Lift sums (γ-bounded, consistent with the clustering).
   - Compute r_ab on the shared-game sums with shared-game strengths. Label it as not tied to the Lift clustering: it can exceed γ.
3. **Per-cluster view**: order a Cluster's partners by r_ab, and show w_ab/cut_a as "share of this Cluster's outside weight". Zero pairs can be listed at 0 without special cases.
4. **Not as the headline**:
   - Density: it is unstable for two-tag Clusters and not size-aware in the degree sense. At most, a secondary column.
   - Game-set Jaccard or Cluster Lift: saturated on these data and blind to the network that was clustered. They would also need new game-set terms.
   - PAGA: binarised, capped, and built on a node-uniform null.
5. **Caution text for the guide** (Inference):
   - Every inter-cluster r_ab is low partly *because* the clustering put the tags apart. It describes the partition, not independent evidence that two groups of characteristics are unrelated.
   - All graph-based values count only edges at or above the minimum shared games.
   - "Shared games" totals count tag-pair incidences, so one game can add several.
6. **Naming hazard**: the glossary's Lift avoids "affinity" and "association strength". Ticket 06 should name r_ab so that it is not confused with Lift. It is a cluster-level observed/expected over strengths, not over games.

## Sources

- [F10] Fortunato, S. (2010). Community detection in graphs. *Phys. Rep.* 486, 75–174. arXiv:0906.0612. §III.B.1 eqs. (1)–(2), and footnote 2.
- [FH16] Fortunato, S., & Hric, D. (2016). Community detection in networks: A user guide. *Phys. Rep.* 659, 1–44. arXiv:1608.00163. §II.C (SBM, stochastic block matrix).
- [HLL83] Holland, P. W., Laskey, K. B., & Leinhardt, S. (1983). Stochastic blockmodels: First steps. *Social Networks* 5, 109–137. Cited via FH16 §II.C and KN11 §I. Not read directly.
- [KN11] Karrer, B., & Newman, M. E. J. (2011). Stochastic blockmodels and community structure in networks. *Phys. Rev. E* 83, 016107. arXiv:1008.3926v1. Locators from the arXiv text: §II eqs. (3), (5)–(7), (9)–(13); §III eqs. (14)–(15), (18), (23)–(24).
- [LLDM08] Leskovec, J., Lang, K. J., Dasgupta, A., & Mahoney, M. W. (2008). Community structure in large networks. arXiv:0810.1355. Conductance.
- [N04f] Newman, M. E. J. (2004). Fast algorithm for detecting community structure in networks. *Phys. Rev. E* 69, 066133. arXiv:cond-mat/0309508. §II, ΔQ = 2(e_ij − a_i a_j).
- [N04w] Newman, M. E. J. (2004). Analysis of weighted networks. *Phys. Rev. E* 70, 056131. arXiv:cond-mat/0407503. §II (multigraph mapping, non-integer weights) and §II.C eq. (9).
- [N16] Newman, M. E. J. (2016). Equivalence between modularity optimization and maximum likelihood methods for community detection. *Phys. Rev. E* 94, 052315. Eqs. (6), (17)–(18), as in Research 01 §3.1.
- [NG04] Newman, M. E. J., & Girvan, M. (2004). Finding and evaluating community structure in networks. *Phys. Rev. E* 69, 026113. arXiv:cond-mat/0308217. §IV eq. (5) and note [49].
- [P18] Peixoto, T. P. (2018). Nonparametric weighted stochastic block models. *Phys. Rev. E* 97, 012306. arXiv:1708.01432. §I and §II.
- [SM00] Shi, J., & Malik, J. (2000). Normalized cuts and image segmentation. *IEEE TPAMI* 22(8), 888–905. §2 eqs. (2)–(4).
- [TVN11] Traag, V. A., Van Dooren, P., & Nesterov, Y. (2011). Narrow scope for resolution-limit-free community detection. *Phys. Rev. E* 84, 016114. arXiv:1104.3083v2. §II.B (CPM density threshold) and App. B eq. (B4).
- [TWvE19] Traag, V. A., Waltman, L., & van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. *Sci. Rep.* 9, 5233. arXiv:1810.08473. §II (CPM paragraph), §III and Table I, App. B Definition 5, App. D.1 Theorem 4.
- [VEW09] van Eck, N. J., & Waltman, L. (2009). How to normalize cooccurrence data? An analysis of some well-known similarity measures. *JASIST* 60(8), 1635–1651. Working-paper version ERS-2009-001-LIS (repub.eur.nl/pub/14528). §2 eqs. (1)–(2), (5)–(8); §4 Proposition 4.1 and the probabilistic interpretation.
- [VL07] von Luxburg, U. (2007). A tutorial on spectral clustering. *Stat. Comput.* 17, 395–416. arXiv:0711.0189. §2.1, §5 and §6 Proposition 5.
- [WOL19] Wolf, F. A., et al. (2019). PAGA: graph abstraction reconciles clustering with trajectory inference through a topology preserving map of single cells. *Genome Biol.* 20, 59. Methods, "PAGA connectivity". Code: scanpy 1.10.4, `src/scanpy/tools/_paga.py`, `_compute_connectivities_v1_2`.
- [YL12] Yang, J., & Leskovec, J. (2012). Defining and evaluating network communities based on ground-truth. ICDM 2012. arXiv:1205.6233. §2, scoring functions (conductance, normalised cut, cut ratio).
- Not consulted: Newman's *Networks* textbook (2010/2018). No locators are claimed from it.
