# Research 15: Graph-specific γ bounds

Answers [ticket 15](../issues/15-graph-specific-gamma-bounds.md). Builds on [Research 01](01-resolution-selection-formulas.md) (its notation: Â, P̂, ω_in, ω_out, γ̂, CHAMP) and does not repeat it. Feeds [ticket 16](../issues/16-graph-specific-gamma-scan.md), which makes the decisions. Checked 2026-10-26.

## How to read this file

- **Established** = stated in the cited source (paraphrased, with locator).
- **Inference** = my own derivation or reading, with the argument given. Every Inference that is a theorem was also checked by brute force over all set partitions of 60 random small weighted graphs ([verify.py](../prototypes/15-gamma-bounds/verify.py)).
- **Measured** = run here on Build `20261008T221504Z-7a23ae9f` with the scripts in [prototypes/15-gamma-bounds/](../prototypes/15-gamma-bounds/); the full tables are in [results.md](../prototypes/15-gamma-bounds/results.md).
- **Open for 16** = a choice the sources leave open. It is listed, not decided.

Notation, as in Research 01: a weighted undirected graph with w_ij ≥ 0, no self-loops, strengths k_i, 2m = Σ_i k_i, null model P_ij = k_i k_j/2m, B_ij(γ) = A_ij − γP_ij, Q_σ(γ) = Σ_ij B_ij δ = Â_σ − γP̂_σ. "Trivial partition" = one Cluster per connected component, isolated tags as One-Tag Clusters. "All-singletons" = every tag a One-Tag Cluster.

## Summary

- **Upper bound, exact: γ_max = max over edges of 2m·w_ij/(k_i k_j).** Jeub, Sporns & Fortunato (2018) define γ_max as the smallest γ at which all-singletons is optimal and say it is the smallest γ with A_ij − γP_ij ≤ 0 for all i, j. Their reference code computes exactly max(A/P) over non-zero entries. Neither the paper nor the code gives a proof or discusses weights or isolated nodes. The proof is two lines and holds for any w ≥ 0 and any isolated tags (§1.2, Inference).
- **But γ_max is far too loose for this method.** It is set by one rare tag pair with a huge Lift (e.g. RTS – Real Time Tactics, 3 shared games, Lift 20: γ_max = 204). On Lift it ranges 2.6–204 (median 15.4) and exceeds 3.00 on 758 of 765 graphs (Measured, §5).
- **A tighter, still provable, upper end for Stable Partitions: γ_pos**, the root of F(γ) = Σ_{edges} 2·max(B_ij(γ), 0) − γΣ_i k_i²/2m. For γ ≥ γ_pos no partition has Q > 0. Every partition's ω_in, and so every γ̂, is below γ_pos, and a Stable Partition must have Q > 0 at its own γ̂. So no partition can be stable, and no γ̂ can land, above γ_pos (§1.4, Inference; not in any source). On Lift γ_pos runs 1.38–13.5 (median 3.12) and is above 3.00 on 412 graphs and below it on 353.
- **Gibson & Mucha's γ_max(K)** bounds γ̂ only for K equal-sized groups and needs a K_max. With K = the number of non-isolated tags it is 3.8–17.7 here, always above 3.00 and not graph-specific beyond K (§1.5).
- **Lower bound: exact value known, not closed-form.** Jeub et al. define γ_min as the largest γ at which one Cluster is optimal and say it "has to be determined numerically". Their code finds an upper bound by an iteration with the optimiser (§2.1). I show that γ_min equals the minimum **normalised cut** (Shi & Malik 2000) over bipartitions of a component, scaled by 2m/vol (§2.2). That is NP-hard in general, but it is bracketed in numpy: (2m/vol)·λ₂ of the normalised Laplacian below it, the best Fiedler sweep cut above it (§2.3).
- **Measured γ_min (Lift):** the bracket is [0.017, 0.771] at its lowest and [0.018, 0.835] at its highest, median 0.41–0.54. Jeub's iteration equals the brute-force exact value on all 44 graphs small enough to enumerate. **29 graphs have γ_min below 0.25** (down to 0.018). A weakly attached pair or triple splits off there (e.g. Card Game, Card Battler, Deckbuilding in strategy).
- **Spacing in the sources:** uniform (linear) in W17, GM22 and every `modularitypruning` example; linear, logarithmic or **event sampling** (uniform in a β that measures the share of negative B_ij) in Jeub et al., who recommend event sampling; geometric-mean bisection in `resolution_profile` (§3).
- **Range ends:** `CHAMP_2D` needs a finite box. CHAMP's original code without `max_pt` stops the hull at Q = 0, which this note shows loses no Stable Partition. GM22 count only stable partitions inside the scanned range and do not discuss γ̂ outside it. With exact bounds, adding the trivial and all-singletons partitions to CHAMP's input bounds every other domain without clipping (§4).
- **Effect on this Build (Measured, §5.4).** Scanning from below γ_min up to γ_pos instead of 0.25–3.00 keeps the Selected Partition on 761 of 765 pairs, with one pair having none either way. It changes 3:
  - puzzle 4/4 now picks a low-γ partition (domain [0.064, 0.367], 3 Multi-Tag Clusters) that the 0.25 clip had made narrow;
  - two g = 3 pairs change through new partitions found above 3.00.
  - No Stable Partition starts above 3.00, and no stable γ̂ exceeds it.
- **`leidenalg` with `n_iterations=-1` can fail to stop at high γ.** On simulation g=5 s=5 it loops for ever at several γ between 6.2 and 6.7 on float-noise gains of ~1e-14 (§5.4). Any scan above about 3 needs a pass cap.
- **Open for 16:** listed in §6.

---

## 1. Upper bound

### 1.1 What the sources say

**Established**
- [JSF18 Methods, "Sampling Strategies for γ", Eq. (3)] defines the range of "all possible resolutions" as γ_min = max{γ : #[g_max(γ)] = 1} and γ_max = min{γ : #[g_max(γ)] = n}, with g_max(γ) the optimal partition and # its number of communities.
- Same paragraph: "The upper bound γmax can be computed exactly by noting that γmax is the smallest value of γ such that" A_ij − γP_ij ≤ 0 for all i and j. No proof is given. P_ij = k_i k_j/2m [JSF18 Methods, "Multiresolution Modularity", Eq. (2)].
- [JSF18 Methods, "Event Sampling"]: β(γ) = 1 for γ ≥ γ_max.
- The paper applies the method to weighted brain networks [JSF18 Results, "Real Networks"] but does not say how weights enter the bounds, and does not discuss zero-degree nodes.
- [HC-SRC `gammaRange.m`, v1.1.1]:
  - `gamma_max = max(max(div_0(AT,PT)))`, with AT = (A + Aᵀ)/2, PT = AT − B(γ=1), and `div_0` dividing only at non-zero entries of A.
  - So γ_max = max over edges of A_ij/P_ij. Its docstring: γ_max is the "Smallest value of 'gamma' for which the network is split into singleton communities"; it is "simply the largest value of gamma for which there exist ferromagnetic interactions in the modularity matrix".
  - It also computes `g_min = min(div_0(AT,PT))` "to handle the case where A has negative entries" and uses the partition found at g_min as the baseline for γ_min, "to handle the case where the network is not connected".

### 1.2 Proof, with weights and isolated tags

**Inference.** Let γ* = max over edges (i, j) of A_ij/P_ij = max 2m·w_ij/(k_i k_j). Assume w ≥ 0 and m > 0.

1. **At γ ≥ γ*, all-singletons is optimal.** Q_σ(γ) = Σ_i B_ii + Σ_{i≠j, same Cluster} B_ij. The first sum is the same for every partition, and it is all of all-singletons' Q. Every off-diagonal B_ij ≤ 0 when γ ≥ γ*: on an edge because γ ≥ A_ij/P_ij, on a non-edge because A_ij = 0 and P_ij ≥ 0. So Q_σ(γ) ≤ Q_singletons(γ) for every σ.
2. **At γ < γ*, it is not.** Take the edge (i, j) that attains γ*. Merging i and j, leaving the rest as singletons, adds 2B_ij(γ) = 2P_ij(γ* − γ) > 0.
3. So γ* is exactly the smallest γ at which all-singletons is optimal, which is JSF18's γ_max. Above γ*, all-singletons is the unique optimum up to where isolated tags sit.

Weights: the argument uses only A_ij ≥ 0 and P_ij = k_i k_j/2m, so it holds for Lift and Shared games alike. With signed weights it fails, which is why `gammaRange.m` has `g_min`; Lift is always > 0 here.

Isolated tags: k_i = 0 gives P_ij = 0 and A_ij = 0, so B_ij = 0 for every pair that involves them. They are excluded from the max (`div_0` skips them; 0/0 never arises). They can be put in any Cluster at no cost, so "all-singletons optimal" means "optimal up to where isolated tags sit", the same tie as Research 01 §2.3. Leiden keeps them as One-Tag Clusters.

Consequences:
- **Every non-trivial Optimality Domain ends at or before γ_max.** Every partition's line Q_σ(γ) − Q_singletons(γ) = Σ_{i≠j same} B_ij(γ) is ≤ 0 for γ ≥ γ_max. So in CHAMP every input partition crosses the all-singletons line at or below γ_max, with equality only if the input contains a partition that is optimal right up to γ_max.
- **No γ̂ reaches γ_max.** For any σ, Â = Σ_{i≠j same} A_ij ≤ γ_max·Σ_{i≠j same} P_ij = γ_max·(P̂ − Σ_i k_i²/2m) < γ_max·P̂. So ω_in = Â/P̂ < γ_max. γ̂ is the logarithmic mean of ω_in and ω_out and so lies strictly between them (Research 01 §3.3). For an assortative partition (ω_in > ω_out) this gives γ̂ < ω_in < γ_max.

### 1.3 γ_max on this Build is set by one rare pair

**Measured** (Lift, 765 graphs; [results.md](../prototypes/15-gamma-bounds/results.md), [inspect_extremes.py](../prototypes/15-gamma-bounds/inspect_extremes.py))
- γ_max is 2.57–203.8, median 15.4, 95th percentile 94.2. It exceeds 3.00 on 758 of 765 graphs.
- The highest, rpg g=3 s=3: RTS – Real Time Tactics, 3 shared games out of 5 and 3, Lift 20, strengths 24 and 20, 2m = 4,883.
- The lowest, rpg g=18 s=2 (27 tags): Great Soundtrack – First-Person, 9 shared games, Lift 1.96.
- Shared games weights: 2.53–1,317, median 13.0, above 3.00 on 749 graphs. The maximum is the same RTS pair: Shared games 3, but strengths 13 and 3.

**Inference.** The pair that sets γ_max is the one that two-tag Cluster is "worth" splitting off last. It is decided by a few games among rare tags, the cases where the Lift is least reliable (Research 31 §B.1). As a scan end, γ_max would mean a linear 0.05 scan of 50 to 4,000 values to reach a region where, by §1.4, nothing can be stable.

### 1.4 A tighter provable end for Stable Partitions: γ_pos

**Inference** (no source found; checked in [verify.py](../prototypes/15-gamma-bounds/verify.py)).
- Define F(γ) = Σ_{i≠j} max(B_ij(γ), 0) + Σ_i B_ii(γ) = Σ_{edges} 2·max(w_ij − γk_i k_j/2m, 0) − γ·Σ_i k_i²/2m.
- For any σ, Q_σ(γ) = Σ_i B_ii + Σ_{i≠j same} B_ij ≤ F(γ).
- F is continuous, strictly decreasing, F(0) = 2m > 0 and F(γ_max) = −γ_max·Σk²/2m < 0. So it has one root, γ_pos < γ_max, found by bisection in O(E) per step.
- **Every ω_in ≤ γ_pos.** ω_in(σ) is the root of Q_σ, and Q_σ ≤ F with F decreasing.
- **No Stable Partition, and no γ̂, at or above γ_pos.** A Stable Partition is assortative (ticket 03's rule), so γ̂ < ω_in ≤ γ_pos. Also Q_σ(γ̂) > 0, so it lies where the envelope is positive.
- This is the same reasoning as GM22's γ_max(K), but for any group sizes and any number of groups, with the graph's own weights.
- What γ_pos does not bound: partitions that are optimal between γ_pos and γ_max exist and can be found by the scan. They are never stable, and their domains can only matter to Stable Partitions through the domain of the partition optimal just below γ_pos (§4.3).

**Measured.**
- Lift: γ_pos is 1.38–13.48, median 3.12. It is above 3.00 on 412 graphs and below on 353. It is 4–57% of γ_max (median 21%).
- By dataset (medians): overall 2.95, puzzle 3.06, rpg 2.80, simulation 3.34, strategy 3.51. It falls as g rises: puzzle g=20 s=2 has 1.38, puzzle g=3 s=3 has 13.48.
- Shared games: 1.24–3.99, median 2.05, above 3.00 on only 42 graphs.

### 1.5 Comparison with Gibson & Mucha's γ_max(K)

**Established** (via Research 01 §4, verified there)
- [GM22 SI §J; Results "Bounds on γ estimates"]: for K equal-sized assortative blocks, γ̂ ≤ γ_max(K), e.g. γ_max(2) = 1 and γ_max(3) ≈ 1.0926. If a maximum K is known, γ_max(K_max) can end the scan. The derivation assumes every group has κ_r > 0 (SI §J.2).
- [MP-REPO `experiments/social_networks/SNAP_boxplot.py`, `find_maximum_gammas`]: γ_max(K) is computed as the maximum of γ̂ over a grid of (ω_in, ω_out) on the line ω_in + (K − 1)ω_out = K. The same script scans γ on `np.linspace(0, 10, 1000)` and stops the scan once a partition has more than 100 communities.

**Inference.**

| | JSF18 γ_max | γ_pos (this note) | GM22 γ_max(K) |
|---|---|---|---|
| What it bounds | where all-singletons becomes optimal | every ω_in and γ̂; where any Q > 0 | γ̂ of a K-group partition with equal-sized groups |
| Depends on | one edge's 2m·w/(k_i k_j) | all weights and strengths | K only |
| Exact or bound | exact | upper bound (not tight) | bound, under an assumption that does not hold here (unequal Clusters) |
| Needs a choice | no | no | K_max |

- Ticket 03 rejected γ_max(K) because it needs a K_max. It is also not a bound on the optimal partitions, only on γ̂, and only for equal-sized groups.
- **Measured:** with K = the number of non-isolated tags (the loosest possible K_max), γ_max(K) runs 3.79–17.71 (median 5.92). It is above 3.00 on all 765 graphs, and above γ_pos on most. It has no information about the weights.

## 2. Lower bound

### 2.1 What the sources say

**Established**
- [JSF18 Methods, "Sampling Strategies for γ"]: γ_min (Eq. (3)) "has to be determined numerically". Modularity is linear in γ for a fixed partition, so each partition has a minimum γ at which it beats the one-community partition, which they call "effectively a special case of the CHAMP algorithm". They estimate γ_min from a small sample at γ = 1, then sample at γ_min − ε so the earlier partitions are strictly non-optimal, and repeat until the new sample holds only the trivial partition.
- [HC-SRC `gammaRange.m`]:
  - Its output is documented as an "Upper bound for smallest value of 'gamma' for which the network splits into communities".
  - Defaults: `InitialGuess` 1, `Samples` 10, `NUM_TOL` = 1e-9. The guess is doubled (capped at γ_max) until some sample splits. Each sampled σ gives (a0 − a)/(p0 − p), where (a0, p0) are the coefficients of the partition found at `g_min`, which for a disconnected graph is the per-component baseline.
- [W17 §2]: CHAMP starts at γ_0 = 0, where the optimal partition is one community for a connected network (each component its own community otherwise, Research 01 §2.1). No γ_min is computed. Weir et al. and GM22's main-text scans and every `modularitypruning` example start at γ = 0 (Research 01 §2.2; [MP-REPO] `docs/source/basic_example.rst`: `np.linspace(0, 2, 1000)`).
- [SM00 §2, Eq. (2)]: the normalised cut of a bipartition (A, B) is Ncut = cut(A,B)/assoc(A,V) + cut(A,B)/assoc(B,V), with assoc(A,V) the total connection from A to all nodes (= vol A).
- [SM00 §2, last paragraph; Appendix A]: "minimizing normalized cut exactly is NP-complete, even for the special case of graphs on grids" (proof due to Papadimitriou).
- [SM00 §2.1, Eqs. (5)–(9)]: Ncut equals the Rayleigh quotient yᵀ(D − W)y / yᵀDy for a two-valued y with yᵀD1 = 0. Relaxing y to real values gives the generalised eigensystem (D − W)y = λDy, Eq. (6). Its second-smallest eigenvector is the real-valued minimiser, Eqs. (8)–(9). [SM00 §3] turns it into a bipartition by trying splitting points along the eigenvector and keeping the best Ncut.

### 2.2 γ_min is a minimum normalised cut

**Inference** (checked against all set partitions in [verify.py](../prototypes/15-gamma-bounds/verify.py)).

1. **Reduce to refinements of the components.** For γ ≥ 0, splitting any Cluster along component boundaries removes no internal weight and cannot increase Σκ². So the best partition at any γ ≥ 0 can be taken to refine the trivial partition, and Q_σ − Q_trivial is a sum of one term per component.
2. **One component c with volume vol_c, split into parts S_1…S_r (r ≥ 2):** Q_σ − Q_trivial = −Σ_a cut(S_a) + γ·Σ_a vol(S_a)(vol_c − vol(S_a))/2m, where cut(S_a) is the weight from S_a to the rest of c. This is positive iff γ > 2m·Σ_a cut(S_a) / Σ_a vol(S_a)(vol_c − vol(S_a)).
3. **Bipartitions suffice.** By the mediant inequality, that ratio is ≥ min_a 2m·cut(S_a)/(vol(S_a)(vol_c − vol(S_a))), which is the threshold of the bipartition (S_a, c ∖ S_a).
4. So **γ_min = min over components c and non-empty proper S ⊂ c of 2m·cut(S)/(vol S·vol(c ∖ S))**. For a connected graph (vol_c = 2m) this is exactly min Ncut(S, S̄) of [SM00 Eq. (2)]. For a component it is (2m/vol_c)·Ncut within c.
5. Isolated tags have vol 0 and form their own component. They never enter.

Consequences:
- γ_min is exact and well-defined for any w ≥ 0, but computing it is NP-hard in general [SM00 §2]. JSF18's "determined numerically" is the honest statement for large graphs.
- Below γ_min the only optimal partition is the trivial one. It is never stable: Research 01 §3.3 gives it no estimate (`one_group` or `no_cross_weight`).

### 2.3 Computing it in numpy on 20–140 tags

**Inference**
- **Lower bound:** (2m/vol_c)·λ₂(D_c^{-1/2}(D_c − W_c)D_c^{-1/2}), minimised over components. It follows from [SM00 Eqs. (5)–(9)]: the relaxed minimum is ≤ the discrete one. One dense `eigh` on ≤ 140 × 140 costs milliseconds.
- **Upper bounds:**
  - the best Fiedler sweep cut, which is [SM00 §3]'s discretisation over every splitting point;
  - JSF18's iteration with Leiden, at 20–50 Leiden runs per graph here.
  - Both are attained bipartitions or partitions, so both are ≥ γ_min.
- **Exact by enumeration** of 2^(n−1) bipartitions, feasible to about 24 tags (≈ 4 s at 22 tags in vectorised numpy).
- Cheeger-type inequalities would give an upper bound from λ₂ alone, but the sweep cut is already an explicit upper bound and is tighter.

**Measured** (Lift, 765 graphs)

| | min | 5% | median | 95% | max | below 0.25 |
|---|---:|---:|---:|---:|---:|---:|
| lower: (2m/vol)·λ₂ | 0.017 | 0.215 | 0.407 | 0.687 | 0.771 | 88 |
| upper: min(sweep, Jeub) | 0.018 | 0.257 | 0.537 | 0.776 | 0.835 | 29 |
| exact (44 graphs with ≤ 24 tags) | 0.260 | 0.412 | 0.664 | 0.827 | 0.835 | 0 |

- The upper/lower ratio has median 1.29 and maximum 1.64.
- On the 44 enumerable graphs, Jeub's iteration hit the exact value on all 44 and the sweep cut on 35. Over all graphs Jeub's was lower on 238 and the sweep on 25. So the Leiden iteration is the better upper bound, and the sweep a cheap check.
- Every graph is connected apart from isolated tags (matching ticket 05's LCC share of 1.0), so the per-component case never arises on this Build.
- The lowest γ_min: strategy g=8 s=8 at 0.018, where {Deckbuilding, Card Battler, Card Game} hangs off the rest by little weight. Also puzzle g=4 s=4 at 0.053 ({Comic Book, Superhero}) and rpg g=3 s=3 at 0.091 ({RTS, Real Time Tactics}).
- Shared games: the upper bound runs 0.144–0.882 (median 0.723); only one graph is below 0.25.

## 3. Spacing of γ samples in the sources

**Established**
- **Linear.**
  - [W17 §3]: each Louvain run uses a γ chosen "uniformly" from the search range ([0, 6], [0, 4], and a 600 × 400 grid for the multilayer Senate example).
  - [MP-REPO experiments]: `np.linspace` everywhere: karate [0, 2]; hierarchical SBM [0, 2.5] with 10,000 values; SNAP [0, 10] with 1,000 values, stopped at > 100 communities; LFR [0.5, 2.0]; Lazega 2,000 γ × 500 ω.
  - [MP-REPO `docs/source/basic_example.rst`]: `np.linspace(0, 2, 1000)`.
- **Linear and logarithmic.** [JSF18 "Sampling Strategies for γ"; HC-SRC `linearSamples.m`, `exponentialSamples.m`]: `linspace(gamma_min, gamma_max, n)` and `logspace(log10(gamma_min), log10(gamma_max), n)`. JSF18 say both "do not work well in practice when considering the entire range of gamma values", because many samples land where almost every node is a singleton.
- **Event sampling.** [JSF18 "Event Sampling", Eqs. (4)–(5); HC-SRC `eventSamples.m`]:
  - β(γ) = Σ_{B_ij<0} |B_ij| / Σ_{i≠j} |B_ij| over all pairs. It is 0 at γ ≤ 0, 1 at γ ≥ γ_max, and increasing in between.
  - γ(β) is piecewise rational between the "events" A_ij/P_ij at which a pair changes sign. n values of β are taken equally spaced from β(γ_min) to 1 and mapped back to γ.
  - The README says `eventSamples` "is usually recommended". JSF18 first tried the unweighted share of negative pairs and "found this not to give a good coverage".
- **Bisection.** [LA-SRC `resolution_profile`] bisects in log space (geometric mean) when both ends are > 0 (Research 01 §6).

**Measured** (event sampling, 56 values from β(γ_min upper bound) to 1, Lift)
- A median of 52 of the 56 values falls inside [0.25, 3.00] (range 40–56).
- A median of 4 falls above 3.00 (range 0–11). These are spread up to γ_max, i.e. into the region where nothing can be stable (§1.4).
- The median event γ is 1.24.
- So on these graphs event sampling is close to a linear scan on [γ_min, ~3] plus a few points at very high γ.

**Inference.**
- No source samples in a way tied to stability. All of them treat the scan as producing CHAMP's input set, and the sources are silent on step size beyond "dense enough".
- Ticket 03's two-decimal grid has one property no other scheme has: every scan γ can be typed into the Workbench. Log and event sampling lose it unless rounded.

## 4. Range ends in CHAMP and Gibson & Mucha

### 4.1 What the code does

**Established**
- [MP-SRC `CHAMP_2D`] needs a finite [γ_0, γ_f]. It builds a box (γ_0 ≤ γ ≤ γ_f, bottom ≤ Q ≤ top) for Qhull, and domains are clipped to it (Research 01 §2.1).
- [CHAMP-SRC 2.1.0 `get_intersection(coef_array, max_pt=None)`]:
  - For a single layer it always adds the halfspaces γ ≥ 0 and **Q ≥ 0**. `max_pt`, described as an "Upper bound for the domains … such as the range of parameters originally searched using Louvain", adds γ ≤ max_pt.
  - Without `max_pt`, the hull is the region above every partition line and above Q = 0. Domains therefore end where the envelope reaches Q = 0. A partition can own a facet only where its line is ≥ 0.
  - For the interior-point LP only, the code imposes γ ≤ 10.
- [W17 §3.1]: domains are not clipped to the search range in the text (one domain runs "just below 44" against a [0, 6] scan). Counts are reported "in the original parameter search space". [W17 §3.4] counts 267 partitions whose domains lay "completely outside the selected parameter range".
- [MP-SRC `prune_to_stable_partitions(G, parts, gamma_start, gamma_end)`] clips to the given range and keeps start ≤ γ̂ ≤ end. A γ̂ outside every clipped domain makes the partition "not stable", with no separate flag. `plotting.py` likewise draws an estimate only if it lies in some domain.
- [GM22 SI §I.2]: on LFR graphs, the fraction of realisations "with stable partitions inside the chosen range" is reported. The main text does not otherwise discuss γ̂ outside the range (Research 01 §4).
- [MP-REPO `lfr_benchmark_test.py`]: prints a warning when the ground-truth γ̂ exceeds the sweep's upper end, and still runs.

### 4.2 Is CHAMP's Q ≥ 0 cut safe for stability?

**Inference.** Yes. A Stable Partition σ has γ̂ < ω_in(σ) (§1.2), so Q_σ(γ̂) > 0 and the envelope is positive at γ̂. Cutting the hull at Q = 0 removes only the part of each domain where no estimate can land.

That end is input-dependent: it is max ω_in over the input set, a lower bound on γ_pos. Like any clip, it changes the width of the last positive domain, and so the widest-domain rule.

### 4.3 Is a bounded range needed once the bounds are exact?

**Inference**
- **For the true envelope, no.**
  - On [0, γ_min] the trivial partition is optimal (§2.2), and on [γ_max, ∞) all-singletons is (§1.2).
  - Every other partition's domain lies inside [γ_min, γ_max].
  - Neither trivial partition can be stable: the trivial one has no estimate (`one_group` / `no_cross_weight`), and all-singletons has Â = 0, so it is `not_assortative`.
- **For the found envelope, almost.** CHAMP extrapolates every input line (Research 01 §2.2).
  - If the input contains the trivial and all-singletons partitions (both are known exactly and cost nothing), then CHAMP on [0, ∞) is well-defined. The trivial line wins at 0 by W17's smallest-P̂ tie rule. The all-singletons line wins beyond the last crossing, which is ≤ γ_max (§1.2).
  - Every non-trivial domain is then a finite interval set only by the input partitions. No domain is clipped, and `clipped_low` / `clipped_high` cannot occur. Our `champ_1d` already handles `hi = inf` (the loop ends when the next crossing is ∞).
- **What still depends on where the scan stops:**
  - The partition found nearest the scan's top end gets a domain that runs to its crossing with the next found partition, or with all-singletons. If the scan stops below γ_max, that domain is longer than the true one.
  - If the scan reaches γ_pos, this inflation lies above γ_pos, where no γ̂ can land (§1.4). It cannot create a false Stable Partition, but it can widen a domain and so change the widest-domain rule.
  - The same holds at the bottom if the scan starts above γ_min: the lowest found partition's domain extends down to its crossing with the trivial line, which is the found γ_min (JSF18's "special case of CHAMP").
- **γ̂ outside the scanned range:**
  - With [0, ∞) and the two trivial partitions in the input, every γ̂ > 0 lies in some domain.
  - A γ̂ below every non-trivial domain maps to the trivial partition. One above maps to the top partition or to all-singletons.
  - By §1.4, γ̂ is always < γ_pos. So with a scan that reaches γ_pos, ticket 03's `estimate_above_range` cannot occur.
  - `estimate_below_range` becomes "maps to the trivial partition". It is still never stable, because γ̂ is outside the partition's own domain.

## 5. Measured on this Build

Setup: Build `20261008T221504Z-7a23ae9f`, all five Top-100 Datasets, 153 pairs each, Genre Tags and the defining tag hidden, Minimum Months 0. Graphs are built exactly as [grid_run.py](../prototypes/05-grid-run/grid_run.py) builds them. Leiden runs use RBConfiguration with `n_iterations=-1` and the 10 scan seeds of ticket 05. Scripts:
- [bounds.py](../prototypes/15-gamma-bounds/bounds.py): every bound for Lift and Shared games, 765 graphs each, 220 s on 12 workers.
- [scan_extended.py](../prototypes/15-gamma-bounds/scan_extended.py): §5.4.
- [verify.py](../prototypes/15-gamma-bounds/verify.py): brute-force proofs check.
- [inspect_extremes.py](../prototypes/15-gamma-bounds/inspect_extremes.py): tag names behind the extremes.
- [report.py](../prototypes/15-gamma-bounds/report.py) → [results.md](../prototypes/15-gamma-bounds/results.md).

Shared games was measured on all 765 graphs, not a sample, because the bounds take milliseconds.

### 5.1 Distribution against the fixed 0.25–3.00

| Bound (Lift) | min | median | max | graphs < 0.25 | graphs > 3.00 |
|---|---:|---:|---:|---:|---:|
| γ_min, lower (λ₂) | 0.017 | 0.407 | 0.771 | 88 | 0 |
| γ_min, upper (Jeub / sweep) | 0.018 | 0.537 | 0.835 | 29 | 0 |
| γ_pos | 1.384 | 3.119 | 13.479 | 0 | 412 |
| γ_max (JSF18) | 2.574 | 15.443 | 203.798 | 0 | 758 |
| γ_max(K), K = non-isolated tags | 3.790 | 5.915 | 17.713 | 0 | 765 |

| Bound (Shared games) | min | median | max | graphs < 0.25 | graphs > 3.00 |
|---|---:|---:|---:|---:|---:|
| γ_min, lower (λ₂) | 0.121 | 0.586 | 0.818 | 1 | 0 |
| γ_min, upper (Jeub / sweep) | 0.144 | 0.723 | 0.882 | 1 | 0 |
| γ_pos | 1.243 | 2.047 | 3.987 | 0 | 42 |
| γ_max (JSF18) | 2.526 | 13.042 | 1316.769 | 0 | 749 |

### 5.2 By dataset (Lift, medians)

| Dataset | γ_min lower | γ_min upper | γ_pos | γ_max | γ_max(K) |
|---|---:|---:|---:|---:|---:|
| overall | 0.457 | 0.604 | 2.950 | 11.870 | 6.043 |
| puzzle | 0.384 | 0.517 | 3.063 | 17.417 | 5.137 |
| rpg | 0.472 | 0.592 | 2.802 | 15.246 | 5.399 |
| simulation | 0.362 | 0.486 | 3.337 | 13.413 | 6.043 |
| strategy | 0.341 | 0.479 | 3.505 | 21.927 | 6.171 |

### 5.3 Reading

**Inference**
- **At the bottom**, 0.25 is certainly below γ_min on 677 Lift graphs (λ₂ bound ≥ 0.25) and certainly above it on 29 (upper bound < 0.25). On the other 59 the bracket straddles 0.25. Jeub's value, which equalled the exact γ_min wherever that could be checked, is above 0.25 on all 59, so γ_min probably is too. Where 0.25 < γ_min, the scan's lowest values return only the trivial partition, which is what Research 01 saw ("the lowest admissible partition was always … found at γ = 0.25").
- On the 29 graphs with γ_min < 0.25, a small weakly attached group splits off below the scan. CHAMP over [0.25, …] then clips that partition's domain at 0.25. It was never selected (ticket 05: no clipped Selected Partition).
- **At the top**, 3.00 is above γ_pos on 353 Lift graphs. On those, the scan between γ_pos and 3.00 can only add partitions that cannot be stable.
- On the other 412 graphs, γ_pos > 3.00, so in principle a Stable Partition could exist above the fixed range. §5.4 measures whether one does.

### 5.4 Does the graph-specific range change the selection?

**Measured** ([scan_extended.py](../prototypes/15-gamma-bounds/scan_extended.py), Lift, 765 graphs, 143 s on 12 workers)

Setup:
- One Leiden scan per graph on the 0.05 grid with the 10 scan seeds. It runs from min(0.25, the λ₂ lower bound rounded down) up to γ_pos rounded up: 24–269 values per graph (median 59), 519,850 runs against the fixed scan's 428,400.
- Ticket 03's selection is applied twice to the same runs:
  - **fixed**: only the runs at the 56 values 0.25…3.00, CHAMP on [0.25, 3.00];
  - **extended**: every run, CHAMP on [scan start, γ_pos].
- The fixed arm reproduces ticket 05's Selected Resolution on all 765 pairs.

Results:
- **761 pairs keep the same Selected Partition.** rpg g=18 s=4 has none in either arm. **3 change:**

  | Pair | Fixed: Selected domain, Multi-Tag Clusters | Extended | Why |
  |---|---|---|---|
  | puzzle g=4 s=4 | [2.148, 2.362], 16 | **[0.064, 0.367], 3** | A Stable Partition that was clipped to [0.25, 0.367] keeps its full width below 0.25 and becomes the widest. γ_min ≈ 0.053 here ({Comic Book, Superhero} splits off). |
  | puzzle g=3 s=3 | [2.694, 2.951], 23 | [2.448, 2.660], 20 | Partitions found only at γ > 3 are optimal from 2.855, so the old winner's domain shrinks to [2.694, 2.855] and is no longer the widest. |
  | rpg g=3 s=3 | [2.532, 2.787], 22 | [2.864, 3.317], 26 | A new Stable Partition (γ̂ = 2.87) whose domain crosses 3.00, found by the extended scan. |

- **Above 3.00.**
  - Only one Stable Partition anywhere reaches above 3.00 (rpg g=3 s=3), and none starts above it.
  - No stable γ̂ is above 3.00. The largest γ̂ of any Admissible Partition is 4.17 (median 1.61). Some γ̂ exceeds 3.00 on 23 graphs, all with g ≤ 5, and every one is outside its own domain.
  - `estimate_above_range` and `estimate_below_range` occur 0 times in either arm.
- **Below 0.25.**
  - 12 graphs have a Stable Partition whose domain starts below 0.25: puzzle 4/4; rpg 5/5, 6/5, 6/6, 7/7, 8/7, 9/6, 9/7; strategy 7/7, 8/7, 8/8, 9/8.
  - In the fixed arm these were clipped at 0.25. Only puzzle 4/4 changes its pick.
- **γ_pos is fairly tight.** The found envelope's zero crossing (max ω_in over Admissible Partitions) is 0.79–0.95 of γ_pos (median 0.87).
- **Leiden does not always stop at high γ.** On simulation g=5 s=5, `find_partition(..., n_iterations=-1)` never returns at γ = 6.2–6.7 for any of the 10 seeds: each pass "improves" quality by 3.6e-15 to 1.1e-14 (float noise). The prototype therefore loops `optimise_partition(n_iterations=1)` itself, stopping at the first pass with gain ≤ 0 or after 1,000 passes. That is identical to `n_iterations=-1` wherever the latter stops. 56 runs hit the cap, all on that graph and all above γ = 6.2; none at γ ≤ 3.00.

**Inference.**
- Moving to a graph-specific range changes few picks on this Build (3 of 765), but it can change them through both ends.
  - At the bottom, a "split off one weakly attached pair" partition with exactly 3 Multi-Tag Clusters can win the widest-domain rule once its domain is no longer clipped.
  - At the top, the larger input set reshapes domains near 3.
- The non-termination is a production risk for any scan that goes above about 3. `cluster.detect` and ticket 08's `leiden_scan` use `n_iterations=-1`. Ticket 16 should know about it before choosing the upper end.

## 6. Open for 16

1. **Upper end of the scan:** γ_pos (provable for stability, median 3.1), JSF18's γ_max (exact for the envelope, median 15, up to 204), or something in between such as max ω_in found so far (CHAMP's Q = 0 cut). The sources support γ_max as "the full range" and give no stability-specific end. γ_pos is this note's inference.
2. **Lower end of the scan:** 0 (W17, GM22, `modularitypruning`), the λ₂ lower bound (provably ≤ γ_min), or JSF18's iterated upper bound (exact on all 44 checkable graphs, but an upper bound in general, so a scan starting there can miss the first split). Rounding each end outwards to the 0.05 or 0.01 grid keeps scan γ values Workbench-enterable.
3. **CHAMP range:** [0, ∞) with the trivial and all-singletons partitions added to the input (no clipping), or the scan range with clip flags as now, or CHAMP's Q ≥ 0 cut. This decides whether `clipped_low` / `clipped_high` survive, and how the width of the top and bottom found domains is measured for the widest-domain rule (§4.3).
4. **`estimate_above_range` / `estimate_below_range`:** impossible above if the scan reaches γ_pos. Below, they become a "maps to trivial" map target. Whether to keep the reason codes or fold them into the map target.
5. **Spacing:** linear 0.05 (ticket 03; every source example is linear), 0.01, log, or event sampling (JSF18's recommendation). A linear scan's length is no longer fixed. On Lift, a 0.05 scan from below γ_min to γ_pos is 24–269 values (median 59; §5.4).
6. **A cap:** whether to cap the scan length or the upper end (e.g. GM22's "stop at > 100 communities" practice, or a maximum number of γ values) for graphs like rpg g=3 s=3 (γ_pos = 11.8).
7. **Which bound per graph is recorded and keyed:** the bounds are deterministic functions of the graph. A computed range would not need to enter `grid_key()` beyond the rule that produces it, but the bound values (γ_min bracket, γ_pos, γ_max) are cheap to record per pair.
8. **Null replicates and subsamples:** each has its own graph, so its own bounds (ticket 07's "full procedure"). Whether that is wanted, or whether they reuse the observed pair's range.
9. **Workbench input range:** its γ input runs 0.1–3.0. γ_pos > 3 on 412 Lift graphs, so a Selected Resolution above 3.0 becomes possible if §5.4 finds one.
10. **Shared games:** γ_pos is much lower (median 2.05, max 3.99), so a γ_pos-ended scan is shorter. The same rule serves both weights.
11. **A Leiden pass cap:** `n_iterations=-1` can loop for ever above γ ≈ 6 (§5.4). Whether `leiden_scan` caps the passes, and at what number, or stops on a relative gain tolerance; and whether a capped run is recorded.
12. **Low-γ partitions and the widest-domain rule:** once the bottom is not clipped at 0.25, a partition that only splits off a weakly attached pair or triple can have the widest domain (puzzle 4/4, §5.4). Whether ticket 03's widest plain-γ domain rule still stands, or the lower end, width measure or minimum Multi-Tag Clusters should guard against it.

---

## Sources

**Read in full text or as source code for this note**
- [JSF18] Jeub, L. G. S., Sporns, O., Fortunato, S. (2018). Multiresolution consensus clustering in networks. *Sci. Rep.* 8, 3259. doi:10.1038/s41598-018-21352-7. arXiv:1710.02249v2, read as the ar5iv HTML (Methods: "Multiresolution Modularity" Eq. (2); "Sampling Strategies for γ" Eq. (3); "Event Sampling" Eqs. (4)–(5); Results "Real Networks"; Introduction for the code link). The section headings are unnumbered.
- [HC-SRC] HierarchicalConsensus MATLAB code, v1.1.1 (8 Mar 2018), https://github.com/LJeub/HierarchicalConsensus, `master`: `gammaRange.m`, `eventSamples.m`, `linearSamples.m`, `exponentialSamples.m`, README.
- [SM00] Shi, J., Malik, J. (2000). Normalized cuts and image segmentation. *IEEE TPAMI* 22(8), 888–905. doi:10.1109/34.868688 (§2 Eq. (2) and the NP-completeness paragraph; §2.1 Eqs. (4)–(9); §3; Appendix A cited, not read).
- [CHAMP-SRC] CHAMP 2.1.0, https://github.com/wweir827/CHAMP, `champ/champ_functions.py` (`create_halfspaces_from_array`, `get_intersection`).
- [MP-SRC] modularitypruning 2.0.1, PyPI wheel as installed (`champ_utilities.CHAMP_2D`; `parameter_estimation_utilities.prune_to_stable_partitions`, `gamma_estimates_to_stable_partitions`; `plotting.py`).
- [MP-REPO] https://github.com/ragibson/ModularityPruning, `master`: `docs/source/basic_example.rst`; `experiments/karate_club_test/karate_club_test.py`; `experiments/hierarchical_SBM_test/hierarchical_SBM_test.py`; `experiments/social_networks/SNAP_boxplot.py`; `experiments/lfr_benchmark_test/lfr_benchmark_test.py`; `experiments/lazega_law_firm/lazega_figures.py`.
- [W17] Weir et al. (2017), *Algorithms* 10(3), 93, arXiv:1706.03675v4, re-read for §2 (γ ≥ 0) and §3.1–3.4 (sampling, ranges, domains outside the range).

**Cited through Research 01 (verified there, not re-read)**
- [GM22], [GM22-SI] Gibson & Mucha (2022), *Sci. Rep.* 12, 15928: SI §I.2, §J, Results "Bounds on γ estimates". The nature.com and PMC pages were behind a browser check on 2026-10-26.
- [LA-SRC] leidenalg 0.12.0 `resolution_profile`.
- Research 31 §B.1 on Lift weights.

**Project code read**
- `.scratch/auto-parameter-selection/prototypes/05-grid-run/grid_run.py` (graph construction, scan, `select`, `champ_1d`); `src/steamstudy/network/graph.py` (`Edge`: `shared`, `lift`; `tag_names`); `src/steamstudy/network/model.py` (`clustering_weight`).
