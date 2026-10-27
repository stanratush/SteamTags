# Research 16: A citable upper end for the γ scan

Answers the open upper-end question of [ticket 16](../issues/16-graph-specific-gamma-scan.md). Its comment of 2026-10-27 says the researcher wants a rule that can be cited directly, in place of this project's own γ_pos. Builds on [Research 15](15-graph-specific-gamma-bounds.md) and does not repeat it. Research 15 covers γ_max, γ_pos, γ_max(K), CHAMP's Q = 0 cut and event sampling. Notation (Â, P̂, ω_in, ω_out, γ̂) is from [Research 01](01-resolution-selection-formulas.md). The lower end is already decided: the scan starts at 0 on `round(0.05·i, 2)`. Checked 2026-10-27.

## How to read this file

- **Established** = stated in the cited source, paraphrased, with a locator.
- **Inference** = my own derivation or reading, with the argument given. Not citable as such.
- **Measured** = run here on Build `20261008T221504Z-7a23ae9f` with the scripts in [prototypes/16-citable-upper-bound/](../prototypes/16-citable-upper-bound/).
- **Open for 16** = a choice the sources leave open. It is listed, not decided.

Notation follows Research 15: w_ij ≥ 0, no self-loops, strengths k_i, 2m = Σk_i, P_ij = k_i k_j/2m, Q_σ(γ) = Â_σ − γP̂_σ.
- **K of a partition** = its number of groups with positive strength, i.e. Clusters that contain at least one tag with an edge. Isolated tags never count.
- **n_e** = the number of tags with an edge in the graph. No partition has more than n_e groups of positive strength.

## Summary

- **No source states the Q > 0 bound.** I found no paper or package that bounds γ by the point where every partition's modularity becomes non-positive, so γ_pos stays this project's own inference (§5). The closest citable pieces each give only part of the argument, never a γ bound:
  - Fortunato & Barthélemy's module condition (a group is a module if its modularity term is positive);
  - Reichardt & Bornholdt's ground-state property that every community has non-negative cohesion;
  - Lu, Cross & Szymanski's ω_out ≤ γ̂ ≤ ω_in;
  - CHAMP's code, which cuts the hull at Q = 0.
- **Three citable candidates, ranked by how well they fit:**
  1. **Gibson & Mucha's γ_max(K_max), with K_max = n_e** (recommended).
     - Citations: [GM22 Results, "Bounds on γ estimates"]; [GM22 SI §J.1–J.3].
     - Established: GM22 propose ending the γ range at γ_max(K_max) when a maximum number of communities is known. The SI says heuristics should not be run above it.
     - Inference: the derivation in SI §J.2 bounds γ̂ for *any* assortative partition with K groups of positive strength, whatever the group sizes. γ_max(K) rises with K, and K ≤ n_e always. So γ_max(n_e) bounds every γ̂ on the graph and needs no user choice.
     - Measured (Lift): 3.79–17.71, median 5.92. Scan length on the 0.05 grid from 0 is 77–356 values (median 120), 1.86× the runs of a γ_pos-ended scan. It is above γ_pos on all 765 graphs.
     - The Selected Partition is identical to the γ_pos-ended scan on all 765 Lift pairs.
     - Shared games gets the same values, because γ_max(K) depends only on K.
  2. **Jeub, Sporns & Fortunato's γ_max, which is Bazzi et al.'s γ⁺.**
     - Definition: max over pairs of A_ij/P_ij = max over edges of 2m·w_ij/(k_i k_j).
     - Citations, four independent ones: [JSF18 Methods]; [Bazzi et al. 2016 §2.3], which states it for non-negative weights and samples γ over [γ⁻, γ⁺]; [GM22 Results], which calls it the "maximum meaningful resolution parameter"; [HC-SRC `gammaRange.m`].
     - Guarantee: exact. It ends the sequence of optimal partitions, because all-singletons is optimal above it. No parameter.
     - Measured (Lift): 2.57–204, median 15.4. Scan length is 53–4,077 values (median 310), 7.3× the runs of γ_pos. On Shared games it reaches 1,317, which is 26,337 values.
     - The Selected Partition is identical on a sample of 122 graphs, at 7.8× the Leiden runs. The sample includes the three pairs that changed in Research 15.
  3. **CHAMP's Q ≥ 0 hull cut, used as a stopping rule.**
     - Citation: [CHAMP-SRC 2.1.0 `get_intersection`]. Code only: it is not in Weir et al.'s text, and the code gives no reason for it.
     - The stopping rule built on it is my inference. Scan until every partition found so far has Q ≤ 0 at the current γ, then run CHAMP up to where the found envelope reaches 0.
     - Guarantee: none from a source. It stops at or below γ_pos rounded up, because the found envelope never exceeds the bound F of Research 15.
     - Measured: stops at 1.30–12.15 (median 2.70), which is 0.79–0.99 of γ_pos. Scan length is 27–244 values (median 55). The Selected Partition is identical on all 765 pairs.
- **Rejected or not applicable** (§4):
  - Arenas et al.'s r_max: the same all-singletons threshold, but for a self-loop resolution that is not γ.
  - Traag et al.'s CPM range [0, 1]: unweighted CPM, not modularity.
  - Ronhovde & Nussinov's practical γ ≤ 19: unweighted Potts model with a different null model.
  - PyGenStability's default Markov-time range: γ from 0.32 to 100, fixed and unjustified.
  - leidenalg `resolution_profile`: the range is supplied by the user.
  - GM22's SNAP script stops a scan at more than 100 communities. That is practice, not a bound. Here it never triggers before γ_max(n_e), and fires only on the 23 graphs with more than 100 tags with an edge.
  - Lu et al.'s per-partition range: for a partition that contains a One-Tag Cluster, it is empty.
  - Markov stability: singletons at time 0, with no finite end.
- **Measured on this Build (§6):** none of the three candidates changes any Selected Partition against the γ_pos-ended scan. The choice is therefore about citability, cost and Leiden pass caps, not about results.
- **Recommendation:** γ_max(n_e) from GM22 §J. It is the only candidate that (a) is cited as a rule for the end of a γ scan, (b) bounds exactly the quantity stability depends on (γ̂), (c) needs no user parameter once K_max = n_e, (d) contains the γ_pos range on every graph here, and (e) costs less than twice the γ_pos scan.
  - The one weak point: GM22's title for SI §J.2 restricts it to equal-sized blocks. Citing it for unequal Clusters rests on reading their algebra, which does not use equal sizes (§2.2).
  - If that reading is not acceptable, the strictly citable fallback is γ⁺ (Bazzi et al. 2016; JSF18). It costs 7× more and runs far into the region where Leiden needs a pass cap.

---

## 1. γ_max = γ⁺: where all-singletons becomes optimal

### 1.1 What the sources say

**Established**
- [Bazzi et al. 2016, §2.3, p. 8 of arXiv v3]:
  - They define γ⁻ = min and γ⁺ = max of A_ij/P_ij over i ≠ j with P_ij ≠ 0, for observed and null networks with non-negative entries, which they say covers most applications.
  - Below γ⁻ the optimum is a single community. Above γ⁺ it is N singletons, because every off-diagonal B_ij is then negative.
  - They call these the coarsest and finest possible partitions, and vary γ between the two bounds.
  - For signed networks they scan [0, γ⁺] instead (same page, and footnote 4).
- [Bazzi et al. 2016, §2.3, definition of "multiscale community structure"]: the sampled γ values run from γ_1 = γ⁻ to γ_l = γ⁺. [§4.3, p. 19]: the experiments use a step of the order of 10⁻³ on {γ⁻, …, γ⁺}, or {0, …, γ⁺} for the signed null network.
  - Their networks are weighted: Pearson correlation matrices, shifted to [0, 1] for the non-negative null networks [§4.3].
- [JSF18 Methods, "Sampling Strategies for γ", Eq. (3)] give the same γ_max, as the end of the range of all possible resolutions. [HC-SRC `gammaRange.m` v1.1.1] computes it as max(A/P) over non-zero entries (Research 15 §1.1).
- **New here:** [GM22 Results, "Bounds on γ estimates"] say there is a "maximum meaningful resolution parameter", above which every off-diagonal entry of the modularity matrix is negative and every node sits alone. This is the same γ⁺, stated by the authors of the Stable Partition method.
- **Event sampling adds no earlier end.**
  - [HC-SRC `eventSamples.m` v1.1.1] takes β from β(γ_min) up to 1, and β = 1 is γ_max. The code appends β = 1 explicitly if rounding left it out.
  - Neither the code nor [JSF18 "Event Sampling"] truncates the range below γ_max.
- [Bazzi et al. 2016, §2.3] build their multiscale structure from the heuristic's local optima at the sampled values, not from the exact envelope.

### 1.2 What it guarantees for this method

**Inference**
- Exact end of the envelope: no partition except all-singletons is optimal above γ⁺ (Research 15 §1.2). Scanning to γ⁺ therefore finds every Optimality Domain the optimiser can find.
- Every γ̂ is below it:
  - [Lu et al. 2020, Eq. (10)] state and prove ω_out ≤ γ̂ ≤ ω_in for 0 < ω_out < ω_in. This is the logarithmic-mean property of Research 01 §3.3, now with a citation.
  - Separately, ω_in = Â/P̂ < γ⁺ because Σ_{i≠j same} A_ij ≤ γ⁺·Σ_{i≠j same} P_ij (Research 15 §1.2). This one-line step is not printed in any source. It follows directly from the stated definition of γ⁺.
- Weights: Bazzi et al. state it for non-negative weighted matrices, so it is citable for Lift and Shared games without inference.

### 1.3 Values

**Measured** (765 graphs; from Research 15's `bounds.json`)

| Weight | min | 5% | median | 95% | max | 0.05-grid values from 0: min / median / max / total |
|---|---:|---:|---:|---:|---:|---|
| Lift | 2.57 | 3.79 | 15.44 | 94.23 | 203.80 | 53 / 310 / 4,077 / 406,959 |
| Shared games | 2.53 | 3.47 | 13.04 | 162.86 | 1,316.77 | 52 / 262 / 26,337 / 599,241 |

On Lift this is 7.3× the scan to γ_pos (55,671 values in total).

## 2. Gibson & Mucha's γ_max(K_max)

### 2.1 What the sources say

**Established**
- [GM22 Results, "Bounds on γ estimates"]:
  - The authors note that they always started from pre-selected γ ranges.
  - To pick useful ranges, they derive the largest possible γ estimate γ_max(K) for assortative SBMs with K equal-sized blocks (SI §J).
  - Fig. 6 shows that the bound held for every γ estimate on 16 SNAP social networks.
  - So if a maximum number of communities K_max is known or can be imposed, γ_max(K_max) appears to bound the γ range effectively.
- [GM22 Discussion]: the γ_max(K) bound can help choose the γ range in practice.
- [GM22 SI §J.1]:
  - For equal-sized, non-degree-corrected planted partitions, the expected γ estimate is bounded above for each K. Table S5 gives γ_max for K = 2…10, from 1.0000 up to 2.1931 (γ_max(3) = 1.0926, γ_max(5) = 1.4027).
  - Searching for K-community partitions above γ_max(K) is never right, if modularity is to match the SBM fit.
  - Modularity heuristics should not be run above the γ_max of the largest K of interest.
- [GM22 SI §J.2, "Degree-Corrected, Planted Partition SBMs"]:
  - Start from the partition estimates ω_in = 4m·m_in/Σκ_r² and ω_out = (4m² − 4m·m_in)/(4m² − Σκ_r²) (SI Eq. S4).
  - Since all κ_r > 0 and Σκ_r = 2m, Cauchy–Schwarz gives Σκ_r² ≥ 4m²/K.
  - Assortativity (ω_in > ω_out) gives 4m·m_in > Σκ_r².
  - On that range, ω_in + (K − 1)ω_out decreases in Σκ_r², so it is at most its value at Σκ_r² = 4m²/K, which is K.
  - So the estimates lie in the triangle with vertices (1, 0), (1, 1) and (K, 0) (SI §J.3), and the same γ_max(K) holds.
- [GM22 SI §J.3]:
  - Louvain was run 1,000 times on a uniform γ grid on [0, 10] on each of 16 SNAP networks (unweighted; 4k–82k nodes).
  - Every observed estimate was below γ_max(K).
  - This gives a priori bounds on the useful γ range when a maximum number of communities is known.
- [GM22 SI §J.4]: γ_max(K) has no closed form for K > 2. It grows slowly and is not linear (Fig. S32–S33).
- [MP-REPO `experiments/social_networks/SNAP_boxplot.py`, `find_maximum_gammas`]:
  - The reference code takes the maximum of γ̂ over a 1,000 × 1,000 grid of (ω_in, ω_out) below the line ω_in + (K − 1)ω_out = K.
  - The same script runs `np.linspace(0, 10, 1000)` and breaks out of the scan once a partition has more than 100 communities.

### 2.2 The bound does not need equal-sized groups

**Inference**
- The §J.2 derivation uses only three facts: K groups with κ_r > 0, Σκ_r = 2m, and ω_in > ω_out. Cauchy–Schwarz holds for any κ_r, so unequal groups only move Σκ_r² up, where the left-hand side is smaller.
- So for **every** assortative partition with K groups of positive strength, of any sizes, (ω_in, ω_out) lies in GM22's triangle. Its γ̂ is then at most γ_max(K), because γ̂ increases in both ω_in and ω_out and is therefore largest on the line.
- The equal-sized blocks of the section title are where the bound is attained, not an assumption the derivation uses.
- With weights, m_in, m and κ_r are weighted sums, the same quantities as Â/2, 2m/2 and the Cluster strengths. The algebra is unchanged. GM22 tested only unweighted networks.
- **γ_max(K) increases with K.** A point on the K-line with ω_out < 1 satisfies ω_in + K·ω_out = K + ω_out < K + 1, so it lies inside the K + 1 triangle. So γ_max(K) ≤ γ_max(K + 1), consistent with Table S5.
- **Parameter-free choice: K_max = n_e.** Every partition has K ≤ n_e, so γ_max(n_e) bounds every γ̂ of every assortative partition of the graph.
  - A Stable Partition is assortative and has its γ̂ inside its Optimality Domain.
  - So every Stable Partition's domain starts below γ_max(n_e), and `estimate_above_range` cannot occur with this end.
  - It does not bound domains: a Stable Partition's domain could in principle run past γ_max(n_e). That is the same top-end clipping question as with any end below γ⁺.
- **Measured check:**
  - 0 violations among the 108,993 distinct assortative partitions found in the full scan, and among 25,449 more in the γ⁺ sample.
  - The largest γ̂/γ_max(K) was 0.9996.
  - 0 violations among 1,523 random partitions with very unequal Dirichlet-distributed sizes on random weighted graphs; largest ratio 0.9995 ([gm_random.py](../prototypes/16-citable-upper-bound/gm_random.py)).

### 2.3 Values

**Measured**
- γ_max(n_e) with n_e = 21–139: 3.79–17.71 (5%: 4.20, median 5.92, 95%: 12.34).
- Medians by dataset: overall 6.04, puzzle 5.14, rpg 5.40, simulation 6.04, strategy 6.17.
- Shared games: identical, because n_e does not depend on the weight.
- 0.05-grid values from 0: 77 / 120 / 356 (min / median / max), 103,280 in total, 1.86× the γ_pos scan.
- γ_max(n_e)/γ_pos = 1.28–3.40 (median 1.86). So it is above γ_pos on all 765 graphs, and the γ_pos-ended scan is a prefix of it.

## 3. CHAMP's Q ≥ 0 cut

### 3.1 Paper and code

**Established**
- [W17 §2] says nothing about cutting at Q = 0:
  - The single-layer algorithm starts at γ_0 = 0, takes the next intersection repeatedly, and continues until no intersection lies beyond the current one.
  - It returns the envelope for all positive γ, with an unbounded last domain.
  - The multilayer part describes the hull of half-spaces above the partition planes, with no Q bound.
- [GM22 SI §C] summarises CHAMP and likewise gives no Q ≥ 0 rule.
- [CHAMP-SRC 2.1.0 `champ/champ_functions.py`, `get_intersection`]:
  - For a single layer it always adds two boundary half-spaces, γ ≥ 0 and Q ≥ 0 (commented as the y-axis and x-axis).
  - The comment says only that these are boundary half-spaces always included in the hull, to be removed before returning. No reason is given for Q ≥ 0.
  - `max_pt` adds γ ≤ max_pt, documented as the range originally searched with Louvain.
- [MP-SRC `CHAMP_2D`] (modularitypruning 2.0.1) instead clips to a user-given [γ_0, γ_f] (Research 15 §4.1).

### 3.2 As a stopping rule

**Inference**
- Rule: scan the grid upwards. Stop at the first γ > 0 where every partition found so far has A − γP ≤ 0. Run CHAMP on [0, the found envelope's zero], which is the largest ω_in found, exactly where CHAMP's own code would end the hull.
- The stop always comes at or below γ_pos rounded up to the grid, because every partition's Q is at most F(γ) (Research 15 §1.4).
- What the rule cannot guarantee: a partition first found above the stop could have positive Q at the stop, if Leiden missed it there.
  - Measured: on 22 of 765 graphs, a partition found later in the longer scan had a larger ω_in than the cut, by at most 0.021.
- Citability: only the cut itself is citable, and only to code, with no stated reason. The stopping rule and its argument are ours.

## 4. Other sources checked

| Source | What it says about the top of the range | Fit |
|---|---|---|
| Arenas, Fernández & Gómez 2008 [AFG08 §2; App. A.1.1, Eqs. (A.7)–(A.8)] | For weighted networks with a self-loop resistance r added to each node: r_max is the smallest r with w_ij < (w_i + r)(w_j + r)/(2w + Nr) for all pairs. Above it, all nodes are separate. r_asymp = −2w/N is the lower asymptote. Their scans use 100–500 r values in (r_asymp, r_max]. | Same idea as γ⁺, but for the r parametrisation. r does not map to RB's γ one-to-one. Not usable for the RBConfiguration scan. |
| Reichardt & Bornholdt 2006 [RB06, "Properties of the Hamiltonian and its ground state", property 2, Eq. (19)] | In a ground state, every community has non-negative cohesion and any two communities have non-positive adhesion. No bound on γ. | Gives no γ bound. |
| Traag, Krings & Van Dooren 2013 [TKV13 §II.A] | For unweighted CPM, γ = 0 gives one community and γ = 1 gives singletons. Plateaus are found by bisection on γ. | CPM, not RB modularity; unweighted. |
| Traag & Van Dooren 2011 (Narrow scope…) | No range rule found. | — |
| leidenalg 0.12.0 `Optimiser.resolution_profile` | `resolution_range` is a required argument with no default. Bisection stops on `min_diff_resolution` and `min_diff_bisect_value`. | No rule. |
| Lambiotte, Delvenne & Barahona [LDB, arXiv:0812.1770 §III]; Delvenne et al. 2010 | Linearised stability: at Markov time t = 0 the finest partition is optimal. γ ↔ 1/t. | No finite end. |
| PyGenStability 0.2.7 `run` | Defaults are the `linearized` constructor (modularity, γ = 1/t), `min_scale = −2`, `max_scale = 0.5`, log scale. That is t ∈ [0.01, 3.16], so γ ∈ [0.32, 100]. Optional `with_spectral_gap` rescales t. | A fixed default with no stated justification. |
| Fortunato & Barthélemy 2007 [FB07 §II, Eq. (2)] | A subgraph is a module if its modularity term is positive. A partition into modules has positive Q. At γ = 1 only. | An ingredient of the Q > 0 idea (§5), not a γ bound. |
| Lancichinetti & Fortunato 2011 | γ ranges discussed per benchmark. No general end. | — |
| Newman 2016 [N16 §III.A] | Reports γ̂ on several networks. No bound. | — |
| Prokhorenkova & Tikhonov 2019 (arXiv:1802.04472v3) | Mentions the resolution parameter only in passing. No bound. | — |
| Zhang & Moore 2014 (arXiv:1403.5787) | Uses γ = 1 modularity with a temperature β. No γ bound. | — |
| Lu, Cross & Szymanski 2020 [LCS20 §2.1, Eqs. (9)–(11)] | γ should lie between the largest inter-community density ω_rs and the smallest intra-community density ω_tt. For a planted partition this is ω_out ≤ γ̂ ≤ ω_in (Eq. (10), proved). Eq. (11) applies it to a given partition's estimates. | Per partition, not per graph. A One-Tag Cluster has ω̂_tt = 0, which empties the range for most of our partitions. Useful only as the citation for γ̂ ≤ ω_in (§1.2). |
| Krings & Blondel 2011 (arXiv:1103.5569) | For γ > 1, a community of n nodes can hold at most a fraction n/((n − 1)γ) of the total degree. | A size bound, not an end. |
| Ronhovde & Nussinov 2009/2010 [RN09 p. 19; RN10 ref. 22 note] | For unweighted graphs, 0 < γ ≤ 19 covers the practical range, on a log scale. | Absolute Potts model with a different null model; unweighted; a fixed cap. |
| Mucha et al. 2010; Kehagias & Pitsoulis 2013; Good, de Montjoye & Clauset 2010; Brandes et al. 2008 | No γ range rule. Brandes et al. and Good et al. treat γ = 1 only. | — |
| GenLouvain docs; Granell et al. 2012; Sánchez-García | Not read. | — |

## 5. Is the Q > 0 bound (γ_pos) anywhere in the literature?

**Established (negative):**
- No source I found states that a γ scan can end where no partition has Q > 0. None defines F(γ), its root, or an equivalent.
- Searched: Weir et al. 2017 text and CHAMP 2.1.0 code; Gibson & Mucha 2022 main text, SI §A–J and `modularitypruning` 2.0.1; Jeub et al. 2018 and HierarchicalConsensus; Bazzi et al. 2016; Arenas et al. 2008; Reichardt & Bornholdt 2006; Fortunato & Barthélemy 2007; Brandes et al. 2008; Good et al. 2010; Kehagias & Pitsoulis 2013; Traag et al. 2011 and 2013; Lu et al. 2020; Krings & Blondel 2011; Newman 2016; Prokhorenkova & Tikhonov 2019; Zhang & Moore 2014; web searches for maximum modularity zero, Q > 0 resolution, and positive part of the modularity matrix.
- The nearest results bound something else:
  - Fasino & Tudisco's generalised modularity matrices (2016, seen only in search results): the number of positive eigenvalues of the modularity matrix bounds the number of disjoint modules. This does not give a γ end. For a matrix A − γkkᵀ/2m with two or more positive eigenvalues of A, interlacing keeps a positive eigenvalue for every γ (Inference).
  - The ingredients listed in the Summary.

**Inference:**
- γ_pos can be presented as "derived from" FB07's module condition and RB06's cohesion property, but not cited to them.
- Two parts of its argument are now citable separately: γ̂ ≤ ω_in [LCS20 Eq. (10)] and CHAMP's code ending the hull at Q = 0. The step "every Q ≤ F(γ)" is not.

## 6. Measured on this Build

Setup:
- Build `20261008T221504Z-7a23ae9f`, all five Top-100 Datasets, 153 pairs each, Lift. Graphs are built as in [grid_run.py](../prototypes/05-grid-run/grid_run.py).
- Leiden: RBConfiguration, the 10 scan seeds, the capped pass loop (gain ≤ 0 or 1,000 passes, as decided in ticket 16).
- Grid `round(0.05·i, 2)` from 0. Ticket 03's selection with CHAMP on [0, end] and MIN_MULTI = 3.
- [scan_ends.py](../prototypes/16-citable-upper-bound/scan_ends.py) runs one scan per graph and applies every rule to prefixes of the same runs. Leiden is deterministic per (γ, seed), so the arms differ only in where they stop.
- [report.py](../prototypes/16-citable-upper-bound/report.py) prints the tables.

Arms:
- **pos**: to γ_pos (the rejected reference).
- **q0stop**: §3.2.
- **gmK**: to γ_max(n_e).
- **jsf**: to γ⁺, CHAMP on [0, γ⁺].
- **jsf_q0**: the jsf runs with CHAMP's Q ≥ 0 cut.

Runs and data files:
- All 765 graphs up to max(γ_pos, γ_max(n_e)): 1,032,800 Leiden runs, 312 s on 12 workers, [scan_ends_gmK.json](../prototypes/16-citable-upper-bound/scan_ends_gmK.json).
- The γ⁺ arms on a random sample of 120 pairs (seed 16) plus puzzle 3/3, puzzle 4/4 and rpg 3/3: 122 graphs, 804,040 runs, 437 s, [scan_ends_jsf.json](../prototypes/16-citable-upper-bound/scan_ends_jsf.json).
- A full γ⁺ scan would be about 4.07 M runs. It was not run, to stay within the compute budget.

### 6.1 Scan ends and lengths (Lift, 765 graphs)

| Rule | end: min | 5% | median | 95% | max | grid values min / median / max | total values | capped runs |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| pos (γ_pos) | 1.38 | 1.60 | 3.12 | 7.33 | 13.48 | 29 / 64 / 271 | 55,671 | 56 |
| q0stop | 1.30 | 1.50 | 2.70 | 6.25 | 12.15 | 27 / 55 / 244 | 48,251 | 0 |
| gmK (γ_max(n_e)) | 3.79 | 4.20 | 5.92 | 12.34 | 17.71 | 77 / 120 / 356 | 103,280 | 77 |
| jsf (γ⁺), from `bounds.json` | 2.57 | 3.79 | 15.44 | 94.23 | 203.80 | 53 / 310 / 4,077 | 406,959 | ≥ 151 (sample) |

- q0stop is 0.79–0.99 of γ_pos (median 0.88), and above 3.00 on 311 graphs.
- **Capped runs** (the 1,000-pass cap) all fall on simulation pairs with s = 5:
  - g = 5: 56 runs, already inside γ_pos, as in Research 15;
  - g = 6, 7 and 8: 5, 9 and 7 runs between γ_pos and γ_max(n_e).
  - In the γ⁺ sample, simulation 5/5 rises to 146 capped runs.
  - q0stop never reaches a capped γ.
- **GM22's SNAP practice** (stop once a partition has more than 100 groups with an edge) never fires below γ_max(n_e). In the γ⁺ sample it fires only on the 6 sampled graphs with more than 100 tags with an edge, at γ = 32.6–112.4, which is 18–70% of γ⁺. On graphs of 20–140 tags it is not a usable end.

### 6.2 Does the Selected Partition change?

| Comparison | Graphs | Same Selected Partition | Different | None in both |
|---|---:|---:|---:|---:|
| pos vs q0stop | 765 | 764 | 0 | 1 (rpg 18/4) |
| pos vs gmK | 765 | 764 | 0 | 1 |
| pos vs jsf | 122 | 122 | 0 | 0 |
| pos vs jsf_q0 | 122 | 122 | 0 | 0 |

- The pos arm, started at 0, reproduces Research 15's extended arm on all 765 pairs. It differs from the fixed 0.25–3.00 scan on the same three pairs as there (puzzle 4/4, puzzle 3/3, rpg 3/3). All three are in the γ⁺ sample, and every rule keeps the pos arm's pick on them.
- No arm has a Selected Partition with `clipped_high`, and no arm has `estimate_above_range`.
- The largest stable γ̂ is 2.87, and the largest end of any stable domain is 3.32 (both rpg 3/3). Both are far below the smallest γ_max(n_e) (3.79), so the top-end clipping question of §2.2 never arises here.

**Inference.** On this Build the upper end is decided by citability, cost and pass-cap exposure, not by results:
- γ_max(n_e) costs 1.86× γ_pos and adds 21 capped runs on three graphs.
- γ⁺ costs 7.3× γ_pos (up to 4,077 grid values on rpg 3/3), and goes deep into the region where Leiden's float-noise loop needs the cap.
- On Shared games γ⁺ reaches 26,337 values.

## 7. Open for 16

1. **The rule:**
   - γ_max(n_e) from GM22 §J (recommended);
   - γ⁺ from Bazzi et al. 2016 / JSF18 (strictly citable as stated, 7× the cost);
   - CHAMP's Q ≥ 0 cut as a stopping rule (cut citable only to code, rule ours, shortest);
   - γ_pos, rejected as uncitable.
2. **If γ_max(K): which K_max.**
   - n_e (parameter-free, this note's choice).
   - The number of tags including isolated ones (larger, still valid, no reason to prefer it).
   - A user-set K_max. The maximum-Multi-Tag-Clusters Pair Constraint is not a valid K_max, because K also counts connected One-Tag Clusters, and Pair Constraints apply after selection.
3. **How γ_max(K) is cited and computed.**
   - Whether the docs cite GM22 as stated (equal-sized blocks; an empirically effective bound) or add this note's reading that §J.2 needs no equal sizes (§2.2).
   - Computation: an exact 1-D bounded maximisation (as in `bounds.py` and `scan_ends.py`), or SNAP_boxplot's 1,000-point grid. The grid gives a value slightly below the true maximum.
   - Check the result against Table S5 (K = 2…10).
4. **Rounding and the CHAMP range end:**
   - scan to γ_max(n_e) rounded up to the 0.05 grid;
   - CHAMP on [0, γ_max(n_e)], on [0, the scan's last value], or on [0, ∞) with all-singletons added (Research 15 §4.3);
   - and what `clipped_high` means against it.
5. **`estimate_above_range`:** cannot occur with γ_max(n_e) or γ⁺ as the end (§2.2, §1.2). Keep it as an assertion, or drop it.
6. **Leiden pass cap:** a γ_max(n_e) end adds capped runs on simulation g = 6–8, s = 5 (§6.1). The decided cap of 1,000 passes and `pass_capped_runs` cover it.
7. **Null replicates and subsamples:** each derives n_e, and so γ_max(n_e), from its own graph (consistent with the decision already taken for the range).
8. **Recorded per pair:** n_e and γ_max(n_e), plus γ⁺ and γ_pos as diagnostics if wanted. All are deterministic in the graph. Only the rule enters `grid_key()`.
9. **Shared games:** γ_max(n_e) is the same as for Lift, since it depends only on n_e. Shared games' γ_pos is lower (median 2.05), so the relative cost is higher there (103,280 against 32,966 grid values, 3.1× instead of 1.9×). Not measured on Shared games selection.

---

## Sources

**Read for this note** (full text or source code)
- [Bazzi et al. 2016] Bazzi, M., Porter, M. A., Williams, S., McDonald, M., Fenn, D. J., Howison, S. D. (2016). Community detection in temporal multilayer networks, with an application to correlation networks. *Multiscale Model. Simul.* 14(1), 1–41. doi:10.1137/15M1009615. Read as arXiv:1501.00040v3: §2.3 "Multiscale community structure" (p. 8, γ⁻ and γ⁺, footnote 4, the definition of multiscale community structure with γ_1 = γ⁻ … γ_l = γ⁺); §4.3 (p. 19, discretisation step of order 10⁻³).
- [GM22] Gibson, R. A., Mucha, P. J. (2022). Finite-state parameter space maps for pruning partitions in modularity-based community detection. *Sci. Rep.* 12, 15928. doi:10.1038/s41598-022-20142-6. Main text read in the built-in browser at nature.com: Results "Bounds on γ estimates" and Fig. 6 caption; Discussion.
- [GM22-SI] Supplementary Information, `41598_2022_20142_MOESM1_ESM.pdf` (springernature static content, 47 pp.): §A.3 Eqs. (S3)–(S4); §A.7; §C; §J.1 (Eqs. S25–S27, Table S5, Fig. S28); §J.2 (Cauchy–Schwarz derivation, Figs. S29–S30); §J.3 (Fig. S31); §J.4.
- [MP-REPO] https://github.com/ragibson/ModularityPruning, `master` (package version 2.0.1 in `pyproject.toml`): `experiments/social_networks/SNAP_boxplot.py` (`run_louvain`, lines 87–97; `find_maximum_gammas`, lines 115–142); `utilities/parameter_estimation_utilities.py`; `utilities/champ_utilities.py`.
- [W17] Weir, W. H., Emmons, S., Gibson, R., Taylor, D., Mucha, P. J. (2017). Post-processing partitions to identify domains of modularity optimization. *Algorithms* 10(3), 93. arXiv:1706.03675v4: §1 (pruning description), §2 (single-layer algorithm, Eqs. (2)–(4)), §2.1 (Qhull).
- [CHAMP-SRC] https://github.com/wweir827/CHAMP, `master`, `champ/champ_functions.py`: `get_intersection` (lines 268–380, boundary half-spaces lines 288–309), `create_halfspaces_from_array`. Version 2.1.0 as in Research 15.
- [JSF18] Jeub, Sporns & Fortunato (2018), *Sci. Rep.* 8, 3259; arXiv:1710.02249v2 (as Research 15).
- [HC-SRC] https://github.com/LJeub/HierarchicalConsensus, `master`, v1.1.1: `eventSamples.m` (β up to 1, appended explicitly), `gammaRange.m`, README.
- [AFG08] Arenas, A., Fernández, A., Gómez, S. (2008). Analysis of the structure of complex networks at different resolution levels. *New J. Phys.* 10, 053039. arXiv:physics/0703218v2: §2 (r_max, r_asymp), §3 (sampling in (r_asymp, r_max]), Appendix A.1.1 Eqs. (A.7)–(A.8).
- [RB06] Reichardt, J., Bornholdt, S. (2006). Statistical mechanics of community detection. *Phys. Rev. E* 74, 016110. arXiv:cond-mat/0603718v1: cohesion and adhesion, Eqs. (3)–(5); "Properties of the Hamiltonian and its ground state", properties 1–3, Eq. (19).
- [TKV13] Traag, V. A., Krings, G., Van Dooren, P. (2013). Significant scales in community structure. *Sci. Rep.* 3, 2930. arXiv:1306.3398v2, §II.A "Scanning resolutions", Theorems 1–2.
- Traag, V. A., Van Dooren, P., Nesterov, Y. (2011). Narrow scope for resolution-limit-free community detection. *Phys. Rev. E* 84, 016114. arXiv:1104.3083v2 (searched; no range rule).
- [LA-SRC] leidenalg 0.12.0 as installed: `Optimiser.resolution_profile` (signature and docstring), `VertexPartition.bisect_value`.
- [LDB] Lambiotte, R., Delvenne, J.-C., Barahona, M. (arXiv:0812.1770v3; published as *IEEE Trans. Netw. Sci. Eng.* 1(2), 76–90, 2014): the t = 0 discussion of R_NL. Delvenne, J.-C., Yaliraki, S. N., Barahona, M. (2010), *PNAS* 107, 12755, arXiv:0812.1811v4 (searched). Schaub et al. (2012), *PLoS ONE* 7, e32210, arXiv:1109.5593v2 (searched).
- [PGS-SRC] PyGenStability 0.2.7, https://github.com/barahona-research-group/PyGenStability, `master`: `src/pygenstability/pygenstability.py` (`run` defaults, `_get_scales`), `src/pygenstability/constructors.py` (`constructor_linearized`).
- [FB07] Fortunato, S., Barthélemy, M. (2007). Resolution limit in community detection. *PNAS* 104, 36–41. arXiv:physics/0607100v2, §II, Eq. (2).
- Lancichinetti, A., Fortunato, S. (2011). Limits of modularity maximization in community detection. *Phys. Rev. E* 84, 066122. arXiv:1107.1155v2 (searched).
- [N16] Newman, M. E. J. (2016). *Phys. Rev. E* 94, 052315. arXiv:1606.02319 (searched for bounds).
- Prokhorenkova, L., Tikhonov, A. (2019). Community detection through likelihood optimization: in search of a sound model. *WWW 2019*, 1498–1508. arXiv:1802.04472v3 (searched).
- Zhang, P., Moore, C. (2014). *PNAS* 111, 18144. arXiv:1403.5787v3 (searched).
- [LCS20] Lu, X., Cross, B., Szymanski, B. K. (2020). Asymptotic resolution bounds of generalized modularity and multi-scale community detection. *Information Sciences* (2020). arXiv:1902.04243v2: §2.1, Eqs. (9)–(11) and footnote 3.
- Krings, G., Blondel, V. D. (2011). An upper bound on community size in scalable community detection. arXiv:1103.5569v1.
- [RN09] Ronhovde, P., Nussinov, Z. (2009). *Phys. Rev. E* 80, 016109. arXiv:0812.1072v4, p. 19. [RN10] Ronhovde & Nussinov (2010), *Phys. Rev. E* 81, 046114, arXiv:0803.2548v4 (note to ref. 22).
- Searched without a range rule: Mucha et al. (2010), *Science* 328, 876, arXiv:0911.1824v3; Kehagias & Pitsoulis (2013), arXiv:1209.2678v3; Good, de Montjoye & Clauset (2010), *Phys. Rev. E* 81, 046106, arXiv:0910.0165v2; Brandes et al. (2008), arXiv:physics/0608255v2.
- Seen only in search results, not read: Fasino, D., Tudisco, F. (2016), Generalized modularity matrices, *Linear Algebra Appl.* (arXiv:1502.01139).

**Not read:** GenLouvain documentation; Granell, Gómez & Arenas (2012); Sánchez-García.

**Project code and data**
- [prototypes/16-citable-upper-bound/scan_ends.py](../prototypes/16-citable-upper-bound/scan_ends.py), [report.py](../prototypes/16-citable-upper-bound/report.py), [gm_random.py](../prototypes/16-citable-upper-bound/gm_random.py), `scan_ends_gmK.json`, `scan_ends_jsf.json`.
- Research 15's [bounds.json](../prototypes/15-gamma-bounds/bounds.json) (γ_pos, γ⁺, n_e per graph) and [scan_extended.json](../prototypes/15-gamma-bounds/scan_extended.json) (for the pos-arm reproduction check).
- [grid_run.py](../prototypes/05-grid-run/grid_run.py) (`select`, `champ_1d`).
