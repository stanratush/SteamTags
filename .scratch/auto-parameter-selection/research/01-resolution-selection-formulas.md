# Research 01: Resolution-selection formulas (CHAMP, Newman, Gibson & Mucha)

Answers [ticket 01](../issues/01-resolution-selection-formulas.md). Builds on [Research 31](../../steam-success-study/research/31-data-driven-clustering-parameters.md) §B.1–B.3 and does not repeat it. Checked 2026-10-25.

Labels: **Established** = stated in the cited source (paraphrased, with locator). **Inference** = my own derivation or reading, with the argument given. **Measured** = run here on Build `20261008T221504Z-7a23ae9f` (scripts in the session scratchpad, not committed).

## Summary

- **One pair of numbers per partition is enough.** For a weighted undirected graph with weights `w ≥ 0`, each partition σ has
  Â_σ = Σ_ij A_ij δ = 2·(internal weight) and P̂_σ = Σ_ij k_i k_j/(2m) δ = Σ_c κ_c²/(2m), with Q_σ(γ) = Â_σ − γ P̂_σ [W17 eq. (2); GM22 SI §C.2]. There is no 1/(2m) factor (it is dropped "by convention" and does not move the envelope). `leidenalg`'s `RBConfigurationVertexPartition.quality(γ)` equals Â − γP̂, and `networkx` modularity equals (Â − γP̂)/(2m) (Measured, to 1e-10 and 1e-15).
- **Newman's estimate uses the same two numbers.** ω_in = Â/P̂ and ω_out = (2m − Â)/(2m − P̂). These are [N16] eqs. (17)–(18) with 2m_in = Â (Inference, an identity). Then γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) [N16 eq. (15)].
- **CHAMP** is the upper envelope of these lines on a bounded γ range. Each partition on the envelope gets a contiguous domain. Partitions that are never on top, or on top at only one point, are dropped [W17 §2; `CHAMP_2D`].
- **Stable partition** [GM22 Fig. 1(d), SI §C.3]: the map γ̂ is applied **once** per Admissible Partition. A partition is stable when its own γ̂ lies inside its own Optimality Domain (a fixed point of the map). Stability is conditional on the input set of partitions.
- **One-Tag Clusters that are isolated tags** have k_i = 0. They change neither Â, P̂, ω_in, ω_out nor γ̂, so they never affect CHAMP or stability. They do change the community count K that `restrict_num_communities` uses (Inference + Measured).
- **Undefined γ̂**: no edges; fewer than two groups with κ_c > 0; no cross-group weight (ω_out = 0); or Â ≤ P̂, which is the same as ω_in ≤ ω_out and as Q(γ=1) ≤ 0 (Inference). The sources handle these differently (§3.3).
- **`modularitypruning` 2.0.1** installs and runs on Python 3.14.8 / Windows 11. On six Lift graphs it agrees with the numpy formulas below to ≤ 1e-12 (CHAMP domains, γ̂ and stable sets). It works as a dev-only test oracle with `single_threaded=True`.
- **`resolution_profile` (bisection)** is not a replacement for the grid. On the largest graph it found 13–21 partitions against the grid's 520. They overlapped only 7–9 of the grid's 28 admissible partitions and gave a different stable set. Pooling its partitions with the grid's reproduced the grid result. It is valid as an extra input to CHAMP, not as the only input (Measured, §6).
- **14 open choices** for [ticket 03](../issues/03-resolution-selection-rules.md) are listed in §8.

---

## 1. The CHAMP coefficients for a weighted single-layer graph

**Established**
- [W17 eq. (1)] defines Q(γ) = (1/2m) Σ_ij (A_ij − γ k_i k_j/2m) δ(c_i, c_j) for "possibly weighted" undirected networks, with k_i = Σ_j A_ij the strength and m = ½ Σ_i k_i the total edge weight.
- [W17 §2, eq. (2)] drops the constant prefactor and writes Q_σ(γ) = Σ_ij (A_ij − γP_ij) δ = Â_σ − γP̂_σ, with Â_σ and P̂_σ the within-community sums of A_ij and P_ij. [GM22 SI §C.2] repeats this with P_ij = k_i k_j/2m.
- Self-loops: [N16 §II.B] uses the convention A_ii = 2 for a self-edge. `modularitypruning` counts a self-loop's weight once in m_in and twice in κ (docstring: "Self-loops count as internal edges") [MP-SRC `estimate_singlelayer_SBM_parameters`]. Our Tag Network has no self-loops (`shared_edges` only forms pairs u < v), so this convention never applies.
- `modularitypruning` computes, for undirected graphs, `A_hat = 2·Σ_{internal edges} w` and `P_hat = Σ_c (Σ_{v∈c} strength_v)² / (2·Σ_e w)` [MP-SRC `champ_utilities.partition_coefficients_2D_serial`].
- leidenalg documents RBConfiguration as Q = Σ_ij (A_ij − γ k_i k_j/2m) δ, equivalently Σ_c (m_c − γK_c²/4m) up to the factor 2 [LA-SRC `VertexPartition.py`, `RBConfigurationVertexPartition` docstring].

**Measured.** On six Lift graphs, for 20 partitions each at γ ∈ {0.5, 1, 2}:
- `la.RBConfigurationVertexPartition(...).quality(γ)` equals Â − γP̂ to ≤ 1.3e-10.
- `nx.community.modularity(G, ..., weight="w", resolution=γ)` (used by `metrics.modularity`) equals (Â − γP̂)/(2m) to ≤ 1.6e-15.
- So the Q values the app already shows are each partition's CHAMP line divided by 2m.

**Implementation (numpy)**, edges as arrays `u, v, w` (u < v, weights = Lift), `n` tags, `memb` an int array of cluster labels 0..K−1 over all n tags, isolated tags included:

```python
k      = np.bincount(u, w, n) + np.bincount(v, w, n)   # strength; 0 for an isolated tag
two_m  = k.sum()                                      # 2m = Σ_i k_i = 2·Σ_e w_e
same   = memb[u] == memb[v]
a_hat  = 2.0 * w[same].sum()                          # Â = Σ_ij A_ij δ   (= 2 m_in)
kappa  = np.bincount(memb, k)                         # κ_c = Σ_{i∈c} k_i
p_hat  = (kappa ** 2).sum() / two_m                   # P̂ = Σ_c κ_c² / 2m
```

For a batch of partitions (rows of an int matrix `M`): `same = M[:, u] == M[:, v]`, `A = 2*(same*w).sum(1)`, and κ by `np.add.at` on `(row, M)`. Each partition is O(E + n), negligible next to Leiden [W17 §2.1 last paragraph; GM22 SI §K.1].

**Inference.**
- Isolated tags have k_i = 0 and no edges, so they add nothing to Â or κ_c. Two partitions that differ only in where isolated tags sit have identical (Â, P̂), which gives the exact ties of §2.3.
- Leiden never moves a zero-strength node because the gain is 0, so it always returns isolated tags as One-Tag Clusters. Measured: K minus the number of groups with κ > 0 always equalled the number of isolated tags.

## 2. The CHAMP envelope over a bounded γ range

### 2.1 Algorithm

**Established** [W17 §2, eqs. (3)–(4)]
1. Start at γ_0. The partition with the largest Q there is optimal (at γ_0 = 0, the one with maximum Â).
2. From the current optimal partition σ*_p, compute the crossing point with every other line, γ = (Â_{σ*p} − Â_σ)/(P̂_{σ*p} − P̂_σ). Take the smallest crossing above γ_p as γ_{p+1}.
3. If several partitions cross at γ_{p+1}, the one with the **smallest P̂** wins.
4. Repeat until no crossing remains. σ*_p is optimal on [γ_p, γ_{p+1}), and the envelope is the piecewise-linear Q̃(γ).
5. The domain of each partition is connected, because the lines are straight. "Admissible" means a non-empty domain. Partitions never on top are discarded.

The procedure "can be started at any selected γ of interest" (Weir restricts to γ ≥ 0). Gibson & Mucha use Qhull halfspace intersection instead, O(N log N) [GM22 SI §C.2]. The result is the same.

**Established** [MP-SRC `CHAMP_2D`]
- Builds halfspaces Q ≥ Â − γP̂, plus four box halfspaces: γ_0 ≤ γ ≤ γ_f, and bottom ≤ Q ≤ top with top = max(Â − γ_0P̂) and bottom = min(Â − γ_fP̂).
- Normalises the halfspaces and finds an interior point by linear programming (`linprog`, method `highs-ipm`).
- Runs `scipy.spatial.HalfspaceIntersection` and keeps every partition halfspace that owns a facet. Each partition's range is that facet's two vertices.
- So **domains are clipped to [γ_0, γ_f]**.
- Partitions whose line only touches the envelope at a vertex own no facet and are dropped.
- Returns `(γ_start, γ_end, membership)` sorted by γ_start.

**Implementation (numpy)**, partitions as coefficient arrays `A, P`, range `[lo, hi]` (Inference; this is W17's sweep with a tolerance):

```python
def champ_1d(A, P, lo, hi, rtol=1e-12):
    tol = rtol * max(1.0, np.abs(A).max(), np.abs(P).max() * hi)
    q = A - lo * P
    cand = np.flatnonzero(q >= q.max() - tol)
    cur = cand[np.argmin(P[cand])]               # W17 tie rule at lo: smallest P̂
    start, out = lo, []
    while True:
        dP = P[cur] - P
        ok = dP > tol                             # only flatter lines can overtake as γ grows
        x = np.full(len(A), np.inf)
        x[ok] = (A[cur] - A[ok]) / dP[ok]
        x = np.maximum(x, start)
        nxt = x.min()
        if nxt >= hi:
            out.append((cur, start, hi)); return out
        cand = np.flatnonzero(x <= nxt + tol)
        new = cand[np.argmin(P[cand])]            # W17 tie rule at a breakpoint
        if nxt > start + tol:                     # drop zero-width (single-point) domains
            out.append((cur, start, nxt))
        cur, start = new, nxt
```

This is O(N·H) for N partitions and H admissible ones, which is milliseconds for the 20–520 unique partitions per Threshold Pair seen here. An upper-hull pass after sorting by P̂ would be O(N log N) if ever needed.

**Measured.**
- This function and `CHAMP_2D` returned the same admissible set on all six graphs (14–31 admissible partitions from 27–520 unique ones), on both [0.25, 3] and [0, 3].
- Domain endpoints agreed to ≤ 1.1e-12.

### 2.2 Range ends

**Established**
- [W17 §2] works on γ ≥ 0 from γ_0 = 0. Examples scan Louvain on [0, 6] or [0, 4] and run CHAMP over "the original parameter search space".
- [GM22] scans start at 0 in every example: karate [0, 2], hierarchical SBM [0, 2.5], SNAP [0, 10].
- `prune_to_stable_partitions(G, parts, gamma_start, gamma_end)` clips domains to the given range. Stability is then tested against the clipped domain [MP-SRC].

**Inference**
- CHAMP uses every input partition at every γ, regardless of the γ it was found at [W17 §2; GM22 SI §C.2]. Extending the CHAMP range below the scan's lowest γ (e.g. [0, 3] with a scan starting at 0.25) therefore extrapolates: below 0.25, the envelope is made of partitions found at ≥ 0.25.
- On these graphs the lowest admissible partition was always "every connected tag in one Cluster", found at γ = 0.25. So [0, 3] and [0.25, 3] gave the same admissible and stable sets (Measured). Only the first domain's start changed.
- A domain cut by a range end has an unknown true width, and the cut changes its midpoint.
- A partition whose γ̂ lies just beyond `gamma_end` is called unstable even if its unclipped domain would contain γ̂.

### 2.3 Ties and degenerate lines

**Established**
- [W17 §2]: two different partitions can have identical (Â, P̂) and so equal Q at every γ. The authors had not seen this, ignore it, and note it would only mean "two partitions of equal merit".
- Crossings at one point among several partitions are resolved by the smallest P̂.

**Measured** (`CHAMP_2D`, strategy g=12 s=10, 5 isolated tags)
- A stable partition and a twin that differs only by moving one isolated tag into a Multi-Tag Cluster had dA = dP = 0.
- `CHAMP_2D` kept the original and dropped the twin, whether the twin came first or last in the input. Which one Qhull keeps is not specified.
- Three lines through one point: the middle line's single-point domain is dropped by both implementations.

## 3. Newman's self-consistent γ estimate

### 3.1 Formulas

**Established** [N16]
- Eq. (6): Q(γ) = (1/2m) Σ_ij (A_ij − γ k_i k_j/2m) δ.
- Degree-corrected planted partition: ω_rs = ω_in if r = s, else ω_out (eq. (11)), written as eqs. (12)–(13).
- The log-likelihood is B·Q(γ) + C (eq. (14)), with **γ = (ω_in − ω_out)/(ln ω_in − ln ω_out)** (eq. (15)).
- §III.A: m_in = (ω_in/4m) Σ_r κ_r² (eq. (16)), so **ω_in = 2m_in / (Σ_r κ_r²/2m)** (eq. (17)) and **ω_out = (2m − 2m_in)/(2m − Σ_r κ_r²/2m)** (eq. (18)).
- [GM22 Methods eqs. (3)–(5)] and [GM22 SI eq. (S4)] repeat these as θ_in and θ_out.

**Inference.**
- Σ_r κ_r²/2m = P̂ and 2m_in = Â, so ω_in = Â/P̂ and ω_out = (2m − Â)/(2m − P̂).
- γ̂ is therefore a function of the CHAMP coefficients and 2m alone, and costs nothing extra once CHAMP has run.

### 3.2 Weighted graphs

**Established**
- [N16] is a Poisson multigraph model with integer A_ij and does not discuss weights. Research 31 §B.1 already covers the consequences.
- [GM22 Discussion]: the SBM equivalence is "only known for unweighted multigraphs"; whether a weighted reading is appropriate is left open.
- [MP-SRC README]: weighted support is "an extension beyond the original publication". The code simply sums `e['weight']` in m, m_in and κ.

**Inference**
- With Lift weights, eqs. (17)–(18) are well defined for any w ≥ 0, but there is no likelihood behind them (Research 31 §B.1(e)).
- Use γ̂ as a selection device only. Never claim a planted-partition fit.

### 3.3 Cases where γ̂ is undefined

**Inference** (each from the formulas in §3.1)

| Case | Test (combinatorial, not float) | ω_in, ω_out | γ̂ |
|---|---|---|---|
| No edges (m = 0) | `len(w) == 0` | 0/0 | undefined; CHAMP lines are all Q ≡ 0 |
| Fewer than two groups with κ_c > 0 (e.g. one Cluster plus isolated One-Tag Clusters) | `np.count_nonzero(kappa) < 2` | P̂ = Â = 2m, so ω_in = 1 and ω_out = 0/0 | undefined |
| No cross-group weight (Clusters are unions of connected components) | `not (~same).any()` | ω_out = 0 | ln 0; the limit as ω_out → 0⁺ is 0 |
| ω_in = ω_out | Â = P̂ | γ̂ = 0/0 | the limit is ω_in (γ̂ is the logarithmic mean of ω_in and ω_out) |
| ω_in < ω_out (disassortative) | Â < P̂ | | finite, positive, but the equivalence is to **minimising** Q |

Proof of the last two rows: ω_in > ω_out ⇔ Â(2m − P̂) > P̂(2m − Â) ⇔ Â > P̂ ⇔ Q_σ(1) > 0.

Further consequences (Inference):
- Any partition that strictly beats the one-Cluster partition at some γ < 1 has Â − P̂ > (1 − γ)(2m − P̂) ≥ 0, so it is assortative.
- A non-assortative Admissible Partition can therefore only occur on a stretch of the envelope above γ = 1 where Q̃ < 0.

Floating point: a one-group partition computed in floats gave 2m − P̂ ≈ 1e-13 instead of 0, and ω_out came out as −0.25 (Measured). The guards must use the counts above, not float comparisons.

**Established: what the sources say**
- [N16 §III]: γ in eq. (15) is positive whatever ω_in and ω_out are. When ω_out > ω_in, maximising the likelihood is equivalent to *minimising* modularity.
- [GM22 SI §A.4]: the equivalence to modularity *maximisation* holds only when ω_in > ω_out.
- [GM22 SI §A.6]: γ̂ is undefined at ω_in = ω_out.
- [GM22 Fig. 2 and Fig. 4 captions]: the one-community partition has no estimate.
- [GM22 SI §K.3]: the only parameter-estimation loops the authors found involved a partition with ω_in < ω_out. They attribute these to a breakdown of the equivalence.
- `gamma_estimate_from_parameters` [MP-SRC]:
  - returns `None` if ω_in == 0 or ω_out == 0 (comment: "this could reasonably be taken to be 0");
  - returns `nan` for ω_in == ω_out, with a RuntimeWarning;
  - returns `nan` for a tiny negative float ω_out;
  - returns a positive γ̂ for ω_in < ω_out and **can call such a partition stable**.
- `estimate_singlelayer_SBM_parameters` sets ω_in = 0 when Σκ²/2m ≤ 0, and ω_out = 0 when Σκ²/2m ≥ 2m.
- `gamma_estimates_to_stable_partitions` skips `None`. `nan` fails `start <= nan <= end` and so is silently "not stable".

**Inference:** treating ω_out = 0 as γ̂ = 0 or as "no estimate" gives the same verdict whenever the CHAMP range starts above 0. The two differ only for a domain that starts at exactly 0.

### 3.4 Iteration

**Established**
- [N16 §III.A]: start from a guess (γ = 1 "usually works fine"), maximise Q(γ), re-estimate ω_in and ω_out, recompute γ, and repeat until it converges.
- No guarantee for real networks; usually within a few percent after one iteration, never more than ten. Table I uses the "generally accepted" number of groups q for each network.
- [GM22 SI §A.3]: the full equivalence holds only with K fixed during the maximisation.
- `iterative_monolayer_resolution_parameter_estimation(G, gamma=1.0, tol=1e-2, max_iter=25)` [MP-SRC `parameter_estimation.py`] calls an unseeded `leidenalg.find_partition`. It raises `ValueError` when a step yields a degenerate partition.

**Measured** (illustration only, 3 repeats from each start γ ∈ {0.5, 1, 2, 3})
- overall g=20 s=12 and strategy g=12 s=10: the iteration ended on partitions that the grid + CHAMP also calls stable.
- Starts at 0.5 on overall g=20 s=12 raised "degenerate partition", because the one-Cluster partition was found.
- overall g=3 s=2 (126 tags): it ended at γ ≈ 2.15–2.48 on partitions that are **not** in the grid's stable set.

## 4. Gibson & Mucha (2022): Stable Partitions

**Established**
- **Definition.** Run CHAMP on the input set, compute each admissible partition's estimate, and map the partition to the partition whose domain contains that estimate. This is a deterministic finite-state map on the admissible set, conditional on the input partitions. Stable partitions are its fixed points: estimate inside the partition's own domain [GM22 Results ¶ before Fig. 1; Fig. 1 caption (d)].
- [GM22 SI §C.3] calls such a partition "stable under the resolution parameter estimation map" with respect to the pruned subset. Testing stability is "as easy as finding self loops in a graph" (§C.3.1).
- **Once or iterated.** The map is evaluated **once per admissible partition**. Stability is a fixed-point test, not an iteration run to convergence.
  - Iterating the map only traces orbits; e.g. in Fig. 4 the iterations "converge to other stable partitions".
  - Periodic orbits are possible in principle but were never found for assortative partitions in > 10⁶ random trials [GM22 SI §K.2–K.4; Discussion].
  - `prune_to_stable_partitions` likewise evaluates γ̂ once per CHAMP range and keeps `start ≤ γ̂ ≤ end` [MP-SRC].
- **K fixed or varying.** Both are supported. Restricting the input to K-community partitions before CHAMP only widens domains. Stability with K varying therefore implies stability within its own K, and stability for a set implies stability for any subset containing the partition [GM22 SI §C.3.2, §C.3.4; Results: karate gives one fixed point for each K ∈ {2, …, 8} but one overall].
  - `restrict_num_communities` counts `len(set(membership))` [MP-SRC `partition_utilities.num_communities`]. That count **includes One-Tag Clusters**, isolated tags among them.
- **Several stable partitions.** Expected when there is structure at several scales (hierarchical SBM: 3, 6 and 9 communities stable at once, Fig. 3; Lazega: three stable) [GM22 Results; SI §C.3.3]. All are reported. No rule picks one.
  - Where many domains map near a region, the authors suggest adding runs there and comparing the few partitions near it [GM22 Results, Lazega].
- **No stable partition.** Not addressed in the main text. For LFR benchmarks the authors report the fraction of realisations with stable partitions inside the chosen range [GM22 SI §I.2, Fig. S27], which treats "none in range" as a possible outcome.
- **Range guidance.** For K equal-sized assortative blocks, γ̂ ≤ γ_max(K) [GM22 SI §J; e.g. γ_max(2) = 1, γ_max(3) ≈ 1.0926]. If a maximum K is known, γ_max(K_max) can set the scan's upper end [GM22 Results "Bounds on γ estimates"].
  - The derivation assumes all K groups have κ_r > 0 (SI §J.2). For us, K would be the number of groups with κ > 0, not including isolated tags (Inference).
- **Domain size.** [W17 abstract] suggests choosing "robust" structures by the sizes of the domains.
  - [GM22 SI §A.7] notes that a domain γ_c ± r corresponds to an area ∝ r·γ_c in the (ω_in, ω_out) plane. Equal γ-widths at higher γ therefore cover more parameter space. The authors say it is unclear whether rescaling by this is useful.
- **One-Tag Clusters.** Neither paper discusses isolated nodes or singletons. `modularitypruning` warns that disconnected graphs are "not thoroughly tested" [MP-SRC].
  - By §1 (Inference), isolated tags contribute nothing to Â, P̂, ω_in, ω_out or γ̂.
  - A connected tag that Leiden leaves alone is an ordinary group with κ_c > 0 and enters Σκ² like any other Cluster.

**Measured** (80 γ linear on [0.25, 3] × 10 seeds, Leiden on Lift, `n_iterations=-1`)

| Dataset, g/s | tags (isolated) | unique | admissible | stable (γ̂; Multi-Tag Clusters) |
|---|---|---|---|---|
| overall 3/2 | 126 (0) | 520 | 28 | 3 (2.07; 12), (2.11; 13), (2.43; 17) |
| overall 20/12 | 26 (0) | 27 | 14 | 3 (1.01; 3), (1.30; 6), (1.42; 7) |
| puzzle 6/4 | 82 (1) | 391 | 31 | 2 (1.96; 11), (2.02; 12) |
| rpg 10/6 | 55 (1) | 118 | 23 | 2 (1.48; 9), (1.62; 8) |
| strategy 12/10 | 50 (5) | 56 | 16 | 1 (1.49; 7) |
| simulation 8/8 | 60 (3) | 80 | 21 | 2 (1.41; 6), (1.47; 7) |

- Every admissible partition had ω_in > ω_out except the lowest one (one connected Cluster), which has no estimate.
- γ̂ lay above the domain for partitions optimal at low γ, and below it for those optimal at high γ. The stable partitions sit where the two cross.

## 5. `modularitypruning` 2.0.1

**Established** [MP-SRC: PyPI wheel `modularitypruning-2.0.1-py3-none-any`, read as installed]

| Function | What it computes |
|---|---|
| `champ_utilities.partition_coefficients_2D(G, parts, single_threaded=False)` | Â, P̂ as in §1. Directed graphs use Leicht–Newman: Â = Σ internal w, P̂ = Σ_c k_c^in k_c^out / m. Default splits work over `multiprocessing.Pool(cpu_count())` |
| `champ_utilities.CHAMP_2D(G, all_parts, gamma_0, gamma_f, single_threaded=False)` | §2.1 via `HalfspaceIntersection`; returns `[(start, end, membership)]`, clipped to the range, sorted |
| `parameter_estimation_utilities.estimate_singlelayer_SBM_parameters(G, partition, m=None)` | ω_in = 2m_in/(Σκ²/2m), ω_out = (2m − 2m_in)/(2m − Σκ²/2m), with κ accumulated from edges (isolated nodes get 0) and the guards of §3.3. Asserts the partition is a `leidenalg.RBConfigurationVertexPartition` |
| `gamma_estimate(G, partition)` | wraps the above; converts a membership tuple with `leiden_part_with_membership`; **sets `G.es['weight'] = 1.0` if G is unweighted** (mutates the graph) |
| `gamma_estimate_from_parameters(ω_in, ω_out)` | eq. (15); `None` if either is 0 |
| `ranges_to_gamma_estimates`, `gamma_estimates_to_stable_partitions` | γ̂ per range; keep `start ≤ γ̂ ≤ end` (closed interval), skip `None` |
| `prune_to_stable_partitions(G, parts, gamma_start, gamma_end, restrict_num_communities=None, single_threaded=False)` | full pipeline, see below |
| `leiden_utilities.sorted_tuple` | canonical membership: labels renumbered by first occurrence |
| `parameter_estimation.iterative_monolayer_resolution_parameter_estimation(G, gamma=1.0, tol=1e-2, max_iter=25)` | Newman's iteration (§3.4) |

`prune_to_stable_partitions` steps, in order:
1. Warns if G is not weakly connected.
2. Raises if any weight is < 0 or the total weight is ≤ 0.
3. Canonicalises and deduplicates the input.
4. Optionally filters by K.
5. Runs `CHAMP_2D`, then γ̂ per range, then the stability test.
6. Returns membership tuples only, without domains.

**Defaults**
- `restrict_num_communities=None` (K varies).
- `single_threaded=False`, i.e. a process pool in the CHAMP coefficient step. The γ̂ step is always serial.

**Measured: test oracle on this machine**
- **Install.** `uv run --with modularitypruning==2.0.1` on CPython 3.14.8 (MSC, AMD64), Windows 11 Pro 26200 installed 27 packages from wheels without a build step.
  - Metadata: Requires-Python ≥ 3.10, classifiers up to 3.15.
  - Dependencies: leidenalg, igraph, numpy, scipy ≥ 1.7, scikit-learn, matplotlib, seaborn, psutil, tqdm.
  - Nothing was added to `pyproject.toml` or `uv.lock`.
- **Agreement.** On the six graphs of §4, against the numpy code of §1–§3:
  - γ̂ to ≤ 3.5e-14;
  - identical admissible sets with endpoints to ≤ 1.1e-12;
  - identical stable sets.
- **Speed.** `single_threaded=True`: 5–212 ms per pair. The default multiprocess path works under an `if __name__ == "__main__"` guard but took 7.6 s for one graph because of Windows process spawn. Tests must pass `single_threaded=True`.
- **Warnings.** It emits a `UserWarning` on every graph with an isolated tag, and RuntimeWarnings for `nan` estimates. Tests should filter these.
- **Oracle caveats.**
  - Its stability verdict will differ from ours wherever ticket 03 chooses a rule that differs from it: ω_in ≤ ω_out, tie handling, closed interval, range clipping.
  - Oracle tests should compare Â, P̂, domains and γ̂ directly, and compare stable sets only on graphs where those cases do not occur.

## 6. leidenalg `resolution_profile` and bisection

**Established** [LA-SRC leidenalg 0.12.0 `Optimiser.resolution_profile`, as installed in `.venv`]
- Signature: `resolution_profile(graph, partition_type, resolution_range, weights=None, bisect_func=lambda p: p.bisect_value(), min_diff_bisect_value=1, min_diff_resolution=1e-3, linear_bisection=False, number_iterations=1, **kwargs)`.
- Requires a `LinearResolutionParameterVertexPartition` (RBConfiguration qualifies).
- `bisect_value()` is `total_weight_in_all_comms()`, the internal weight (= Â/2).
- An interval is bisected while the bisect values at its ends differ by more than `min_diff_bisect_value` **and** the ends differ by more than `min_diff_resolution`. The difference is in log space when both ends are > 0, and the new point is then the geometric mean.
- One partition is optimised per point, from the Optimiser's own RNG.
- `ensure_monotonicity` is meant to replace a point's partition by a better one found elsewhere. Its second loop assigns `best_res = new_res` in both branches, so that half is a no-op as written.
- `clean_stepwise` at the end keeps, at each point, the best partition among all found, then drops consecutive points with equal bisect value.
- The docstring describes `min_diff_bisect_value=1` as "a single edge". That is an unweighted reading, which Research 31 §B.3 flagged.

**Inference**
- For exact optima of a linear Q = Â − γP̂: if σ₁ is optimal at γ₁ < γ₂ and σ₂ at γ₂, adding the two optimality inequalities gives (γ₂ − γ₁)(P̂₁ − P̂₂) ≥ 0, and then Â₁ − Â₂ ≥ γ₁(P̂₁ − P̂₂) ≥ 0.
- So the internal weight is non-increasing in γ along the true envelope, and bisection on it is valid for exact optimisation (cf. [TKV13] Thm 2 for CPM).
- Heuristic optima break this, which is why the code patches monotonicity.
- The number of Clusters is *not* guaranteed monotone for the configuration null model [W17 §3.2]. The measured envelopes confirm it:
  - puzzle 6/4: K = 6 on [0.788, 0.800], then K = 5 on [0.800, 0.876];
  - rpg 10/6: Multi-Tag Clusters 9 on [1.424, 1.488], then 8 on [1.488, 1.865].

**Measured** (resolution range (0.25, 3.0), `number_iterations=-1`, seed 0)

| Graph | grid 80×10 | profile, min_diff=1 | min_diff=10⁻³·Σw | min_diff=10⁻⁶ |
|---|---|---|---|---|
| overall 3/2 (Σw = 4,581) | 5.3 s; 520 unique, 28 admissible, 3 stable | 1.5 s; 21 parts; 9 shared admissible; 5 stable (≠ grid) | 0.9 s; 13; 7; 3 (≠ grid) | 1.7 s; 18; 8; 4 (≠ grid) |
| strategy 12/10 (Σw = 273) | 0.9 s; 56, 16, 1 stable | 0.2 s; 13; 12; 1 (= grid) | 0.2 s; 15; 12; 1 (= grid) | 0.3 s; 15; 13; 1 (= grid) |

- Pooling profile and grid partitions gave exactly the grid's stable set on both graphs.

Reading of the results (Inference):
- With Lift totals of 270–4,600, `min_diff_bisect_value=1` is 0.02–0.4% of Σw, not a coarse threshold here, and changing it barely mattered. Research 31 §B.3's worry does not bite on these graphs.
- The real limit is one optimiser run per bisection point. With fewer competitors in the input, domains widen, and a partition can look stable only because a better partition was never found (cf. [GM22 Fig. 1 caption]: the map is conditional on the input set).
- Bisection is valid but not better than the multi-seed grid as the **only** input. It is cheap enough to add as extra input to CHAMP, which is method-agnostic [W17 §3; GM22 Discussion].

## 7. Reference implementation sketch (numpy, as it would be implemented)

```python
def gamma_hat(a_hat, p_hat, two_m, n_groups_with_strength, has_cross_edge):
    """Newman (2016) eqs. (15),(17),(18) from CHAMP coefficients; None where undefined (§3.3)."""
    if two_m <= 0 or n_groups_with_strength < 2 or not has_cross_edge:
        return None                      # no edges / one effective group / ω_out = 0
    if a_hat <= p_hat:
        return None                      # ω_in ≤ ω_out ⇔ Q(1) ≤ 0: not modularity *maximisation*  [open choice]
    w_in = a_hat / p_hat
    w_out = (two_m - a_hat) / (two_m - p_hat)
    return (w_in - w_out) / (np.log(w_in) - np.log(w_out))

# per Threshold Pair:
#   parts   = unique canonical memberships over all γ × seeds        (set partitions, isolated tags included)
#   A, P    = coefficients(parts)                                    (§1)
#   domains = champ_1d(A, P, lo, hi)                                 (§2)
#   for (i, a, b) in domains: g = gamma_hat(...); stable = g is not None and a <= g <= b
#   map target (for the UI / orbits): the domain containing g, if any
```

## 8. Open choices left by the sources (for ticket 03)

1. **CHAMP range**: the scan range [0.25, 3.0] or [0, 3.0]. The sources scan from 0 and run CHAMP over the scanned range (§2.2). Starting at 0 extrapolates below the lowest scanned γ.
2. **End-truncated domains**: whether a domain cut by a range end counts at its clipped width and midpoint, is flagged, or is ineligible. `modularitypruning` silently clips (§2.2).
3. **Interval closure**: closed [a, b] (`modularitypruning`) or half-open [γ_p, γ_{p+1}) (W17). This matters only for estimates that land exactly on a breakpoint.
4. **Exact ties between distinct partitions with identical (Â, P̂)**: W17 ignores the case and Qhull keeps an arbitrary one (§2.3). A deterministic rule is needed, e.g. canonical-membership order. With full-set-partition deduplication this occurs only when isolated tags are placed differently, which Leiden does not do.
5. **Ties at a breakpoint and zero-width domains**: W17 picks the smallest P̂. Both implementations drop single-point domains. The float tolerance needs fixing.
6. **ω_in ≤ ω_out (Â ≤ P̂)**: `modularitypruning` computes a positive γ̂ and may call the partition stable. [N16 §III] and [GM22 SI §A.4] say the equivalence is then to minimisation. Choose between "no estimate" and following the library.
7. **ω_out = 0 and one-effective-group partitions**: "no estimate" (`None`) or γ̂ = 0 (the limit, as the library's own comment suggests). The verdict is the same unless a domain starts at 0.
8. **Once or iterated**: GM22 evaluates the map once per admissible partition (fixed-point test). Whether to also record each partition's map target or orbit (e.g. for the CHAMP plot) is a presentation choice. Newman's own iteration (§3.4) is a different procedure and should not be mixed in.
9. **K fixed or varying, and what K counts**:
   - `restrict_num_communities` counts One-Tag Clusters, isolated tags included.
   - γ_max(K) assumes κ > 0 for every group.
   - Restricting the input set changes domains and so stability [GM22 SI §C.3.4]. Applying "≥ 3 Multi-Tag Clusters" **before** CHAMP is therefore a different procedure from applying it **after** stability. The sources describe only pre-CHAMP restriction, by exact K.
10. **Several Stable Partitions**: the sources report all and give no selection rule. "Widest Optimality Domain" is our rule, supported only by W17's remark on domain size. GM22 SI §A.7's γ-scaling of domain area is a possible alternative.
11. **No Stable Partition**: the sources are silent beyond "add more runs near the region". Decide whether the Threshold Pair becomes ineligible, and with what recorded reason.
12. **Input set**: stability depends on the partitions supplied (§6).
    - Decide the seed count and grid spacing (linear vs log, which the sources do not specify; GM22 and W17 use uniform grids).
    - Decide whether to add `resolution_profile` partitions.
    - Set equality for deduplication is per set partition over all tags.
13. **Scan upper end**: the fixed 3.0, or γ_max(K_max) from [GM22 SI §J] if a maximum number of Clusters is set.
14. **Weighted reading**: the Lift estimate has no likelihood behind it [GM22 Discussion; Research 31 §B.1]. The methods text should present it as a selection device, not an SBM fit.

---

## Sources

**Read in full text for this note**
- [N16] Newman, M. E. J. (2016). Equivalence between modularity optimization and maximum likelihood methods for community detection. *Phys. Rev. E* 94, 052315. doi:10.1103/PhysRevE.94.052315. arXiv:1606.02319v1 (§II.A eqs. (1)–(6); §II.B eq. (7) self-edge convention; §III eqs. (11)–(15) and the ω_out > ω_in paragraph; §III.A eqs. (16)–(18), Fig. 1, Table I).
- [W17] Weir, W. H., Emmons, S., Gibson, R., Taylor, D., Mucha, P. J. (2017). Post-processing partitions to identify domains of modularity optimization. *Algorithms* 10(3), 93. doi:10.3390/a10030093. arXiv:1706.03675v4 (abstract; §1 eq. (1); §2 eqs. (2)–(4) and tie remarks; §2.1 eqs. (5)–(7), Qhull; §3 intro; §3.1; §3.2 on non-monotone community counts).
- [GM22] Gibson, R. A., Mucha, P. J. (2022). Finite-state parameter space maps for pruning partitions in modularity-based community detection. *Sci. Rep.* 12, 15928. doi:10.1038/s41598-022-20142-6 (Introduction; Results: karate, hierarchical SBM, temporal, Lazega, "Bounds on γ estimates"; Figs. 1, 3–6 captions; Discussion; Methods eqs. (1)–(6)). Volume and article number from the article PDF header (this corrects Research 31's "not verified").
- [GM22-SI] Supplementary Information to [GM22], `41598_2022_20142_MOESM1_ESM.pdf` (§A.3 eq. (S4); §A.4; §A.6; §A.7 eq. (S8); §A.8; §B.5; §C.1–C.3.4; §I.2 Fig. S27; §J.1–J.3; §K.1–K.4).

**Software source (read as installed)**
- [MP-SRC] modularitypruning 2.0.1, PyPI wheel `py3-none-any` (METADATA/README; `champ_utilities.py`: `CHAMP_2D`, `partition_coefficients_2D(_serial)`, `halfspaces_from_coefficients_2D`, `get_interior_point`; `parameter_estimation_utilities.py`: `estimate_singlelayer_SBM_parameters`, `gamma_estimate`, `gamma_estimate_from_parameters`, `ranges_to_gamma_estimates`, `gamma_estimates_to_stable_partitions`, `prune_to_stable_partitions`; `parameter_estimation.py`: `iterative_monolayer_resolution_parameter_estimation`; `leiden_utilities.py`: `sorted_tuple`, `singlelayer_leiden`, `leiden_part_with_membership`; `partition_utilities.py`: `num_communities`, `all_strengths`). https://github.com/ragibson/ModularityPruning
- [LA-SRC] leidenalg 0.12.0 as installed in the project `.venv` (`Optimiser.py`: `resolution_profile`, `ensure_monotonicity`, `clean_stepwise`; `VertexPartition.py`: `bisect_value`, `RBConfigurationVertexPartition` docstring). https://github.com/vtraag/leidenalg

**Cited through Research 31 (not re-read)**
- [TKV13] Traag, Krings & Van Dooren (2013), *Sci. Rep.* 3, 2930, Theorems 1–2.
- [ZP20], [P23] critiques of the Newman estimate, as summarised in Research 31 §B.1.

**Project code read**
- `src/steamstudy/network/cluster.py` (`detect`: Leiden RBConfiguration on `w`, `n_iterations=-1`), `graph.py` (`shared_edges`, `to_graph`: `w` = Lift, u < v, no self-loops), `metrics.py` (`modularity` via networkx).
