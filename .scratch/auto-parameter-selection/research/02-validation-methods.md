# Research 02: Validation methods (curveball, Hennig, Karrer)

Ticket: [02 Validation methods](../issues/02-validation-methods.md), for [07 Validation design](../issues/07-validation-design.md)
Date: 2026-10-25

**Question:** What do the primary sources say about the curveball null, Hennig's cluster-wise Jaccard stability and Karrer, Levina & Newman's perturbation robustness? What does a defensible null comparison of a clustering procedure look like? Is there precedent for scaling count thresholds with the subsample size? The answers feed the decisions in ticket 07.

**How to read this file.** **Established** sections report what a cited primary source says, with its section, equation, figure or table. **Inference** marks my own readings and derivations, which no source states. **Open for 07** marks a choice that ticket 07 has to make. Terms follow [CONTEXT.md](../../../CONTEXT.md). Like the rest of the project, this note never calls a result "significant". Where a source uses the word, it is quoted as the source's term. [Research 31](../../steam-success-study/research/31-data-driven-clustering-parameters.md) §C.2 (Peixoto 2023) and §C.5 (random-network risk by method) are not repeated here, only built on.

---

## Summary

1. **10 trades per game is enough, and the rule is citable, though only empirically.** No source gives a mixing-time bound for curveball that can be used in practice. Carstens 2015 proves that the chain converges to the uniform distribution, not how fast [C15 abstract]. Carstens & Kleer prove that it mixes rapidly whenever the switch chain does, a polynomial bound with no usable constant [CK18 Thm 1, §1.1]. The citable practice is Strona et al.'s plateau criterion. A 100 × 100 matrix stopped changing after fewer than 200 trades, that is 2 per row [STR14 Fig. 3b]. Across 295 real matrices, the number of trades needed to stabilise the mean checkerboard count was 3–366, "with an average of 1.2 times the largest matrix dimension". The authors call 1,000 trades "rather conservative" [STR14 Supplementary Note 2]. The app's 10 trades per game is 1,000 trades for 100 games, which is ≥ 1,000 and about 6 times 1.2 × the largest dimension (≤ 139 visible tags). **On this Build** (Section A.4: 5 dataset–pair cases, 100 chains each, against a 200-trades-per-game reference), every statistic I tracked was within about 0.8 SD of its long-run level by 5 trades per game, and within Monte Carlo noise at 10. The pair-level memory of the observed table falls by about e per trade per game. **Recommendation:** keep `TRADES_PER_GAME = 10`. Cite [STR14 Suppl. Note 2] plus this check. Never claim a proven mixing time.
2. **The sampler meets the one condition Carstens 2015 attaches to uniformity.** "Certain failed trades" must be counted as steps [C15 abstract]. Strona's transition probabilities likewise "refer to any attempted pair extraction" [STR14 Results, "Uniform distribution of null matrices"]. `curveball()` spends a trade on every pair it draws, including pairs with nothing to exchange, and its shuffle can return the unchanged split. **Inference:** it is the chain Carstens analysed. I read only the abstract of [C15], so the precise list of required failed trades is not checked.
3. **Hennig (2007): the per-cluster mean of the best-match Jaccard, computed only on points present in both data sets.**
   - The scheme: for each resample, restrict the original cluster and the new clustering to the points in both, take the maximum Jaccard over new clusters, and average over resamples [H07 §2, steps (1)–(4)].
   - Resampling schemes: bootstrap, subsetting (m = [n/2], §3.1), replacement by noise (§3.2), jittering and bootstrap/jittering (§3.3). "Jittering alone" is not recommended. The suggested strategy is bootstrap, bootstrap/jittering or subsetting, together with a noise scheme (§6).
   - Thresholds: ≤ 0.5 is "dissolution", with a theoretical justification (§2). The paper gives > 0.75 "good recoveries, say" (§2). The 0.6 / 0.75 / 0.85 bands come from the `fpc::clusterboot` documentation, which says they "refer to bootstrap". For other schemes they depend on the tuning constants [FPC Details].
   - Single points are "perfectly stable, though totally meaningless" (§2), so One-Tag Clusters must be left out.
4. **Here the sampled units (games) are not the clustered units (tags).** That is the pvclust / phylogenetic-bootstrap setting (resample observations, cluster objects [PVC]), not Hennig's. Hennig's rule for missing points (compare on the points present in both) carries over, but a tag's absence here is an outcome of the data, not of the design. **Recommendation:** compute the Jaccard on the tags present in both networks, as Hennig does. Report the share of each cluster's tags that survived next to it, and never fold absent tags into the Jaccard as mismatches. `fpc` and the paper differ when *all* of a cluster's points are missing: `fpc` scores 0, while the paper averages only over resamples where the cluster is present [FPC source; H07 §2]. **Open for 07:** which rule, and whether that count is reported separately.
5. **Karrer, Levina & Newman (2008) back the *principle* of the brief, not its *mechanics*.**
   - Their perturbation rewires each edge of the one-mode network with probability α towards the configuration model. Expected degrees stay fixed and the vertex set stays fixed [KLN08 §III.A, eqs. (2)–(5)].
   - They measure the change by the variation of information, normalised by log n (§III.C, eq. (12)), as a curve over 40 values of α (§IV).
   - Their null is the **same perturbation analysis repeated on configuration-model random graphs**, compared as curves (§IV, Figs. 1–2), not a comparison of Q. They show the Q z-score to be unreliable (§I eq. (1), §V Table I).
   - What carries over: robustness to small data changes as the criterion, a null run through the identical procedure, and isolated nodes kept as singleton communities [KLN08 ref. 44].
   - What differs: the brief perturbs the data (games), not edges. It uses one level (80%), not a curve. It measures with ARI and Jaccard, not VI. Its curveball null is used for Q and structure, not for robustness. KLN themselves ask for cluster-level measures as future work (§VI), which Hennig's provides.
6. **A consistent null procedure re-runs the whole optimisation, and the comparison only says the network is not random.**
   - KLN optimise Q on each random graph before comparing [KLN08 §I eq. (1)].
   - Peixoto: a deviation from the null that "completely ignores the optimization step" overfits [P23 §III]. A Q test answers only "can we reject the hypothesis that the observed network was sampled from a random null model?" [P23 §IV.C, Fig. 12].
   - Number of groups: under modularity maximisation it is strongly correlated between real networks and their degree-preserving randomisations [P23 §III, Fig. 8]. So it is a weak statistic for telling the observed network from its null.
   - **Inference:** Automatic Parameter Selection includes a selection step (γ scan, CHAMP, Stable Partition rule). Applying the full procedure to each null replicate is the analogue of "optimise on the null". Clustering the null at the observed Selected Resolution leaves the γ choice out.
   - **Open for 07:** full procedure, fixed γ, or both. Recommended statistics: whether a qualifying Stable Partition exists, the width of its Optimality Domain, and the number of Multi-Tag Clusters. Add Q only at a common γ.
7. **Scaling thresholds under subsampling: one precedent, from frequent-itemset mining.** Toivonen (1996) defines the frequency threshold as a *fraction* of rows, so it carries over to a sample proportionally [T96 §2]. He *lowers* it in the sample so that frequent sets are "very unlikely" to be missed (§4, Theorem 3). I found no network or co-occurrence paper that scales absolute count thresholds under subsampling (limited search).
   - **Inference:** with 80 of 100 games, floor(0.8·g) keeps more borderline tags than round or ceil. Every rule's keep-probability for a tag exactly at g oscillates with g mod 5, from 0.40 to 0.96 (Section E.2).
   - **Recommendation:** use integer arithmetic: floor = (4g)//5, round = (4g+2)//5, ceil = −(−4g//5). Set a minimum of s′ ≥ 2, since s′ = 1 makes every co-occurrence an edge. Report a subsample in which the procedure finds no qualifying Stable Partition as a failure, never drop it.

---

## A. Curveball: how many trades

### A.1 Strona et al. (2014)

**Established** [STR14]
- **Algorithm** (Results, Fig. 1). A matrix is a set of row lists. Each step draws two rows. The elements present in only one of them are pooled, then randomly redistributed, keeping each row's count of such elements. Strona calls one step a "pair extraction". No element is created or destroyed, so row and column totals are fixed.
- **Uniformity, numerically** (Results, "Uniform distribution of null matrices"; Tables 1–3; Fig. 2).
  - For all five 3 × 3 matrices with margins [1-2-1], the transition matrix of one step has the uniform distribution as its eigenvector solution. "As few as five pair extractions are sufficient" (Table 3, the 5th power).
  - The transition probabilities "refer to any attempted pair extraction, and not only to those leading to some trade of elements". Convergence holds in both cases (Supplementary Tables 1–2).
  - 10,000 null matrices from each start: the frequencies were not different from 1:1:1:1:1 (average χ² P ≈ 0.73).
- **Plateau as the stopping rule** (Results, "Computational demand", Fig. 3a–b).
  - On a 100 × 100 random matrix with 50% fill, the share of cells differing from the start "became stable (with a value around 50%)".
  - Swaps needed about 50,000 attempts to reach that plateau. Curveball reached it "after less than 200 iterations" (Fig. 3b), i.e. ≤ 2 per row.
  - Fill from 10% to 90% "did not affect the performance of the Curveball algorithm" (Fig. 4b).
- **Supplementary Note 2, "Optimal number of pair extractions"** (Supplementary Fig. 1). This is the only guidance on the number of trades.
  - On the Vanuatu (56 × 28) and Sashegy (118 × 80) matrices, mean checkerboard counts over sets of null matrices converged to the values Miklós & Podani reported. "Less than 1000 for both matrices" was enough.
  - "The optimal number of pair extractions clearly depends on the size of a matrix, or, better, on its smallest dimension."
  - Across the 295 matrices of the Nestedness Temperature Calculator, the stopping rule was a change of no more than 1% over 100 subsequent sets. The minimum number needed "ranging from 3 to 366 (mean: 24.34 …)" was "in most cases smaller than or equal to the largest matrix dimension (with an average of 1.2 times the largest matrix dimension)". "Thus, the value of 1000 pair extractions … is likely to be rather conservative."
- **Discussion.** The curveball step identifies "in a single step all the possible swaps between a pair of matrix rows" and performs any of them "with a random probability".

**Inference.**
- Strona's criteria are first-moment plateaus: perturbation share and mean checkerboards. They show that a statistic has stopped drifting. They do not bound the distance to the uniform distribution.
- They are, however, exactly the kind of diagnostic that matters for a null used through summary statistics (edge count, Q).
- The rule of thumb ("about the largest dimension; 1,000 is conservative") is the only citable number.

### A.2 Carstens (2015) and follow-ups: uniformity is proven, speed is not

**Established**
- [C15] gives "a rigorous proof of convergence to the uniform distribution". It shows "the Curveball algorithm must include certain failed trades to ensure uniform sampling" (abstract; full text paywalled, not read).
- [CBS16] §4 "Mixing time and experimental stopping times".
  - The mixing time is "the number N of reiteration steps".
  - The authors "use the point where this perturbation score stabilizes as an estimate for the mixing time" (§4.1, Figs. 5–6).
  - "There is experimental evidence that the mixing time of the Curveball algorithms is much faster than that of switching models, there is currently no theoretical proof" (§4.2). Multi-commodity-flow proofs break down because curveball transition probabilities "can be exponentially small".
- [CK18] Theorem 1 bounds the Curveball relaxation time by the switch chain's, up to a polynomial factor in the number of rows and the maximum row sum. Hence curveball "is also rapidly mixing for (almost) half-regular marginals" (§1.1), i.e. when all row sums (or all column sums) are equal or nearly so. Published at APPROX/RANDOM 2018 under the title "Speeding up switch Markov chains for sampling bipartite graphs with given degree sequence" (LIPIcs 116, 36). I read arXiv v3, whose title differs.
- [CHMPTW18] §5.1 measures mixing by edge-wise autocorrelation and thinning, for **undirected simple graphs** with global trades. "20 global trades consistently give at least the quality of 10m edge switches". The authors are "not aware of any practical theoretical bounds on the mixing time".

**Inference.**
- On this Build almost every game shows 20 tags, but hiding Genre Tags and the threshold g make the visible row sums uneven, so the half-regular condition of [CK18] does not apply exactly (Section A.4 gives the row-sum range).
- Even where it applies, "rapidly mixing" is a polynomial bound without a usable constant.
- The defensible claim is empirical: Strona's rule plus a check on the data actually sampled.

### A.3 The project's sampler

**Established (code)** `steamstudy.network.stability.curveball`, `null_model`.
- Each null replicate is an **independent chain started from the observed table** (`random.Random(seed)` per replicate), restricted to the visible tags of the Threshold Pair. Every replicate is thinned by construction, unlike the sequential swap [STR14 Introduction].
- Each trade draws an ordered pair of distinct games (i, j) uniformly. If either has no tag the other lacks, the trade is spent with no change (`continue`). Otherwise the pooled non-shared tags are shuffled and split back by the original counts, so the identity split is possible.
- `TRADES_PER_GAME * len(rows)` trades, i.e. 1,000 for 100 games.

**Inference.** This is the standard ("binomial trade") curveball chain [CK18 §1], not the "Good-Shuffle" variant that forces a non-zero trade [CBS16 §4.1]. Both converge to the uniform distribution [CBS16 §4.1, citing C15]. Counting the no-op draws as trades matches [STR14]'s convention and the failed-trade condition of [C15].

### A.4 Empirical check on this Build

**Set-up.**
- Build `20261008T221504Z-7a23ae9f`. Fixed settings as in map.md: Genre Tags and the defining tag hidden, Minimum Months 0, Lift, Leiden.
- Five (dataset, g, s) cases spanning the Parameter Grid.
- For each case, 100 independent chains from the observed table restricted to the visible tags, exactly as `null_model` does it, using the project's `curveball()`. Statistics are recorded at cumulative checkpoints of 0.25 to 200 trades per game.
- **Reference ("well mixed"):** the 200-trades-per-game checkpoint, 20 times the app's setting.
- **Statistics:**
  - **perturbation**: the share of the observed 1-cells that moved [STR14 Fig. 3];
  - mean Stone–Roberts **C-score** over tag pairs [STR14 Suppl. Note 2];
  - **edge count** at s;
  - **Q** of Leiden on Lift at γ = 1;
  - number of **Multi-Tag Clusters** at γ = 1;
  - **memory**: the least-squares slope of (mean shared count per tag pair at T − reference mean) on (observed − reference mean), over all pairs. It is the fraction of the observed table's excess co-occurrence still present, a pair-level diagnostic finer than the means.
- Script: `mixing_check.py` (scratchpad). Seeds `random.Random(1000 + r)` for the chain, Leiden seed 7 + r.

**Results.** Each cell gives the mean at T minus the reference mean, in units of the reference SD. With 100 chains, the standard error of such a difference is about 0.14, so |value| ≲ 0.3 is within noise.

| Case (tags; visible row sums min/median/max) | Statistic | T = 1 | 2 | 3 | 5 | **10** | 20 | 50 |
|---|---|---|---|---|---|---|---|---|
| overall g=3 s=2 (126; 4/16/19) | perturbation | −31.4 | −11.9 | −4.3 | −0.47 | **−0.08** | −0.18 | −0.12 |
| | edges | −1.6 | −0.54 | −0.26 | −0.13 | **−0.23** | −0.12 | −0.03 |
| | Q | 3.73 | 0.69 | 0.25 | 0.16 | **0.08** | −0.15 | −0.04 |
| | memory slope | 0.366 | 0.136 | 0.048 | 0.008 | **0.002** | 0.002 | 0.004 |
| overall g=20 s=12 (26; 2/9/14) | perturbation | −17.4 | −6.9 | −2.7 | −0.31 | **0.26** | 0.13 | 0.08 |
| | edges | 0.62 | 0.05 | −0.18 | −0.26 | **−0.28** | −0.22 | −0.17 |
| | Q | 1.29 | 0.18 | −0.04 | −0.02 | **0.10** | 0.08 | 0.03 |
| | memory slope | 0.378 | 0.147 | 0.057 | 0.010 | **0.005** | 0.002 | 0.010 |
| rpg g=3 s=2 (128; 10/16/19) | perturbation | −32.1 | −11.9 | −4.4 | −0.80 | **0.02** | −0.04 | −0.08 |
| | Q | 4.23 | 0.73 | 0.33 | 0.28 | **0.19** | 0.20 | 0.20 |
| | memory slope | 0.358 | 0.132 | 0.049 | 0.010 | **0.005** | 0.004 | 0.005 |
| rpg g=8 s=5 (67; 7/14/18) | perturbation | −26.0 | −10.0 | −3.8 | −0.70 | **−0.20** | −0.04 | −0.09 |
| | Q | 3.20 | 0.07 | 0.07 | 0.13 | **0.01** | 0.02 | 0.12 |
| | memory slope | 0.367 | 0.132 | 0.049 | 0.007 | **0.003** | 0.005 | 0.005 |
| puzzle g=12 s=8 (42; 3/10/15) | perturbation | −23.0 | −8.7 | −3.4 | −0.52 | **−0.08** | 0.00 | 0.05 |
| | Q | 1.43 | 0.10 | 0.03 | −0.01 | **0.13** | −0.04 | −0.06 |
| | memory slope | 0.372 | 0.139 | 0.053 | 0.010 | **0.002** | 0.002 | 0.004 |

- The C-score mean and the number of Multi-Tag Clusters were within ±0.3 SD from T = 2 in every case, with one exception: Multi-Tag Clusters at T = 50 in overall g=20 s=12 were 0.52 SD above the reference, with no trend over T. The edge count was within ±0.3 SD from T = 3.
- **Reference values against the observed table:**

  | Case | Edges, null (mean ± SD) | Edges, observed | Q at γ = 1, null | Q at γ = 1, observed |
  |---|---|---|---|---|
  | overall g=3 s=2 | 2,275 ± 21 | 2,185 | 0.191 ± 0.008 | 0.346 |
  | rpg g=3 s=2 | 2,318 ± 18 | 2,195 | 0.190 | 0.366 |
  | overall g=20 s=12 | 119 ± 4 | 126 | 0.116 | 0.235 |
  | rpg g=8 s=5 | 615 ± 10 | 639 | 0.142 | 0.253 |
  | puzzle g=12 s=8 | 189 ± 6 | 212 | 0.169 | 0.300 |

  At s = 2 the null has *more* edges than the observed network. These numbers are descriptive and play no part in the mixing question.
- Runtime: 100 chains × 200 trades per game, with the statistics, took 32–89 s per case on one core. The prototype-23 benchmark gives 9.4–16.8 ms per 1,000 curveball trades.

**Inference.**
- On these tables the chain forgets its start fast. The memory slope falls by a factor of about e per trade per game (0.37 → 0.14 → 0.05), which fits each game taking part in about two trades per "trade per game".
- By 5 trades per game every tracked statistic is within about 0.8 SD of the reference, and the memory slope is at its noise floor (≈ 0.005–0.01).
- At 10 everything is within noise. Extrapolating the decay gives a residual memory of about 0.37¹⁰ ≈ 5·10⁻⁵ at T = 10. That is my extrapolation, not a measurement.
- So `TRADES_PER_GAME = 10` has a margin of roughly 2× over the empirical plateau and agrees with [STR14]'s "1,000 is conservative".
- Caveats:
  - These are first- and pair-moment diagnostics, as in [STR14] and [CBS16]. They cannot prove mixing in total variation, and no source can at present (A.2).
  - The visible row sums vary (2–19), so the half-regular case of [CK18] does not apply.
  - Raising the trades is cheap in a fixed-γ replicate, where the shuffle already dominates (prototype 23 README, "at 8/8 the shuffle dominates"). It is negligible next to the 0.2–4.3 s of a full-procedure replicate (map.md).

---

## B. Hennig (2007): cluster-wise Jaccard stability

### B.1 The measure and its schemes

**Established** [H07] (author preprint dated 15 July 2006, read in full; the journal version was not compared)
- **Measure** (§2). The Jaccard coefficient γ(C, D) = |C ∩ D| / |C ∪ D|. For each of B resamples:
  1. Draw the resample x*ᵢ.
  2. Cluster it.
  3. Let x̃ᵢ be the original points also present in the resample. Restrict the original cluster to them (C*ᵢ = C ∩ x̃ᵢ) and the new clustering likewise.
  4. If C*ᵢ ≠ ∅, γ_{C,i} = max over new clusters D of γ(C*ᵢ, D). Otherwise γ_{C,i} = 0.

  The stability is γ̄_C = (1/B*) Σᵢ γ_{C,i}, "B* being the number of bootstrap replications for which C*ᵢ ≠ ∅". **My reading:** the preprint's PDF loses the ≠ glyph, so "C*ᵢ = ∅" there must be read as ≠ for the sentence to make sense. That gives a mean over the resamples in which the cluster is present.
- **Why compare on x̃ᵢ** (§2). Each original point counts once. The alternative, comparing on the bootstrap sample with repeated points, "would have the disadvantage that clusters dominated by multiple points would be upweighted".
- **Summaries** (§2). The mean, or "the number of dissolutions (γ_{C,i} ≤ 0.5) or good recoveries (γ_{C,i} > 0.75, say)". "Experience suggests that the mean is a good choice."
- **Why 0.5** (§2). It is "the smallest value so that every cluster in a partition consisting of more than one cluster can be dissolved by a new partition". Whenever a new clustering has r < s clusters, "at least s − r clusters of the original clustering are dissolved" (citing Hennig 2004c).
- **Singletons** (§2). Under a full hierarchy "every subset containing only one point is always a cluster and these clusters will be perfectly stable, though totally meaningless".
- **Schemes** (§3).
  - **Subsetting** (§3.1): draw m < n points without replacement. "If m is too large, subsetting will not generate enough variation to be informative. If m is too small, the clustering results can be expected to be much worse." "I always worked with m = [n/2]." Subsetting "is as general as bootstrapping": it works on dissimilarity data too.
  - **Replacing points by noise** (§3.2): m points replaced by draws from a noise distribution, compared on the n − m kept points.
  - **Jittering, and bootstrap plus jittering** (§3.3), for Euclidean data.
- **Simulations** (§4).
  - Model 1 with a normal mixture: true clusters 3 and 4 were "often instable under Subsetting". "Bootstrap and Bootstrap/Jittering performed best in terms of correlation. Jittering alone didn't produce useful results" (§4.1).
  - 4-means (§4.3): "Bootstrap, Subsetting and Bootstrap/Jittering performing better than Noise and Jittering alone".
- **Discussion** (§6).
  - "A good strategy in practice can be the use of one of the schemes Bootstrap, Bootstrap/Jittering and Subsetting together with one of the Noise schemes."
  - B "doesn't have to be very large": a mean "can be fairly precisely estimated with 50 replications".
  - "Inflexible methods can yield meaningless but stable clusters" (example in §5, Fig. 3: one cluster of 354 of 366 points with γ̄ = 0.9225). Yet "detected instabilities almost always point to serious problems".

**Established** [FPC] (`fpc::clusterboot` reference, version 2.2-12 on search.r-project.org; source from the CRAN GitHub mirror, version 2.2-15)
- Defaults: `B=100` ("While B=100 is recommended, smaller run numbers could give quite informative results as well"), `subtuning=floor(nrow(data)/2)`, `dissolution=0.5`, `recover=0.75`.
- Bands (Details):
  - ≤ 0.5 is a "dissolved cluster", with "some theoretical justification" (Hennig 2008).
  - "A valid, stable cluster should yield a mean Jaccard similarity value of 0.75 or more."
  - "Between 0.6 and 0.75, clusters may be considered as indicating patterns in the data, but which points exactly should belong to these clusters is highly doubtful."
  - "Below average Jaccard values of 0.6, clusters should not be trusted."
  - "Highly stable" clusters reach "0.85 and above".
  - "All of this refers to bootstrap; for the other resampling schemes it depends on the tuning constants, though their default values should grant similar interpretations in most cases."
- Source, `subset` branch: `clujaccard(c1$clusterlist[[j]][bsamp], bc1$clusterlist[[k]], zerobyzero=0)`, i.e. the original cluster restricted to the sampled points.
  - A cluster with **no** sampled points scores 0 against every new cluster, and so 0 in `subsetresult`.
  - `bootmean` etc. are `apply(…, 1, mean, na.rm=TRUE)` over all B.
  - **So the package averages over all B, absent clusters as 0, while the preprint averages over B*.** For clusters of several points and m = n/2 the two rarely differ.

### B.2 Applying it when games are resampled and tags are clustered

**Established** [PVC] pvclust clusters the *objects* (columns) and resamples the *observations* (rows), at relative sample sizes `r = n′/n`, default `seq(.5, 1.4, by=.1)`. This is the multiscale bootstrap of Shimodaira (2004) and Suzuki & Shimodaira (2006).

**Inference.**
- Our Subsample Stability resamples games (observations) and clusters tags (objects), as pvclust and the phylogenetic bootstrap do. Hennig resamples the clustered points themselves.
- So the analogy to [H07] holds for the *summary* (per-cluster mean best-match Jaccard), not for the *design*.
- In Hennig, a point is missing because the design left it out. Here a tag is missing because, in the 80% subsample, it fell below the scaled g′, or (if its edges vanish) it became a One-Tag Cluster. Both are outcomes of the data, and they say something about that tag.
- Options for points not present:
  - **(a) Hennig's rule (recommended).** Compute γ on the tags present in both the full and the subsample network. Alongside it, report each Multi-Tag Cluster's **retention**: the mean share of its tags present. A cluster that "survives" only because most of its tags dropped out then shows as low retention, not as high Jaccard.
  - **(b) Penalise absence.** Treat absent tags as One-Tag Clusters of their own in the subsample. This mixes loss of data with change of grouping, which is the confusion the three-stabilities rule in map.md is meant to avoid.
  - **(c) Present or absent as a whole.** For a cluster that is entirely absent, use 0 and average over all subsamples (fpc), or skip it (preprint B*). (c) is a sub-choice under (a).
- **One-Tag Clusters.** Leave them out of the Jaccard report: they are "perfectly stable, though totally meaningless" [H07 §2]. That matches the CONTEXT.md rule that a One-Tag Cluster "never enters a cluster-quality average".
- **Best match.** Take the maximum over all subsample clusters, One-Tag Clusters included. That is Hennig's definition, and it lets a two-tag cluster that splits into two singletons score 0.5 (dissolved).
- **Bands.** The 0.6 / 0.75 / 0.85 bands are calibrated to the bootstrap, which keeps about 63% distinct points, and fpc's subsetting default is n/2. An 80% game subsample is a milder perturbation of a different kind. So the bands are indicative at best. The theoretically grounded line is ≤ 0.5 = dissolved [H07 §2].
- **Recommendation:** report the mean Jaccard, the count of dissolutions (≤ 0.5) and the count of good recoveries (> 0.75) per Multi-Tag Cluster. Quote 0.5 as the only principled cut, and the other bands as "from fpc's documentation, for the bootstrap". This also fits the project's no-label stance.

**Open for 07.**
- Retention reported next to the Jaccard: yes or no.
- fpc's all-B mean or the preprint's B* mean for clusters that are entirely absent.
- Whether to add a noise-type scheme as Hennig recommends (§6). The bipartite analogue would replace some games by curveball-shuffled rows. That is my construction, not a source's.

---

## C. Karrer, Levina & Newman (2008)

**Established** [KLN08] (arXiv:0709.2108v1, read in full; the journal version was not compared)
- **Motivation** (§I).
  - The z-score of eq. (1), z = (Q − μ)/σ over modularity optimised on random graphs, "has a number of problems" (false positives and negatives).
  - What the authors call "significant" community structure is defined by robustness: "If a small change in the network … can completely change the outcome … the communities found should not be considered trustworthy."
  - §II (after Massen & Doye) links this to competing maxima. Real networks tend to have one clear maximum, random graphs many.
- **Perturbation** (§III.A).
  - The vertex count and edge count stay fixed. Each edge is, with probability α, removed and replaced by an edge drawn with probability e_ij/m, where e_ij = k_i k_j / 2m (eq. (2)).
  - So E[A′_ij] = (1 − α)A_ij + α k_i k_j/2m (eq. (3)), and expected degrees are preserved (eq. (5)).
  - α = 0 keeps the network. α = 1 gives a configuration-model random graph.
  - Ref. [44]: isolated nodes created by rewiring are not discarded "since that would make the perturbed network a different size"; "we assign each isolated node to its own community".
- **Comparison measure** (§III.B–C).
  - The authors review pair counting (Rand, adjusted indices, which have the disadvantage of "non-locality"), cluster matching (van Dongen, eq. (7)) and information-theoretic measures.
  - They choose the variation of information V = H(X|Y) + H(Y|X) (eq. (12)), a true metric and local. Maximum log n; they normalise by log n.
- **Procedure** (§IV).
  - Optimise Q on the network. Perturb, re-optimise and measure V against the original, many times, for "40 different values of α from 0 to 1".
  - "For comparison, we also perform the same set of calculations on a random graph drawn from a configuration model with the same degree sequence", averaged over 10 or 100 random graphs.
- **Reading the curves** (§V, Fig. 1).
  - Structure is robust when the observed V(α) curve rises more slowly than the null curve.
  - Reference lines show the V of randomly reassigning 10% and 20% of vertices. Crossing α values could serve as a scalar, "but to do so can mean missing interesting structure present in the full curves".
- **Results** (§V, Table I).
  - The karate club has z = 1.77, yet robust structure. The power grid has z = 100.8, yet weak robustness.
  - Z-scores "are in general unreliable and should not be trusted unless backed up by other calculations".
- **Limits** (§VI). The global V "cannot reveal" whether "some communities in a network are robust under perturbation while others are not"; "more detailed local measures are needed".

**Inference: what supports the brief and what differs.**

| Aspect | KLN08 | Brief (80% games, curveball null) | Consequence |
|---|---|---|---|
| What is perturbed | edges of the one-mode network, towards the configuration model | observations (games) of the bipartite data, thresholds rescaled | The brief perturbs the *data*. KLN perturb the *network*. Both test "small change, same answer?". |
| Size of perturbation | curve over α ∈ [0, 1], 40 values | one level (80%) | A few levels (e.g. 90/80/70%) would be the closer analogue. **Open for 07**, cost × levels. |
| Node set | fixed; isolated nodes become singletons | tags can fall out (below g′) | KLN avoid the missing-node problem by design. We cannot, hence Section B.2. |
| Comparison | VI (normalised) over the whole partition | ARI on shared tags + Hennig Jaccard per cluster | ARI is a pair-counting index that KLN call non-local (§III.B). The cluster-wise Jaccard answers their §VI call for local measures. VI could be added cheaply. |
| Null | the *same robustness analysis* on configuration-model graphs, compared as curves | curveball null of the bipartite table, compared by Q and structure | KLN's null asks "is the observed partition more robust than a random graph's?". The brief's asks "is the observed network's structure different from a random one's?". Different questions. |
| Degrees | expected degrees preserved (eq. (5)) | exact row and column sums (curveball) | Curveball is the stricter, bipartite-level null. |

**Recommendation.** Cite KLN for the *principle*: robustness to small data changes, compared with a null analysed identically, and singleton handling. Do not cite them for the 80% figure or for ARI. **Open for 07:** whether to run Subsample Stability on a few curveball null replicates too. That would be the KLN-style comparison: the observed ARI and Jaccard next to the null network's. The cost is (null replicates) × (subsamples) × the procedure.

---

## D. Comparing the observed structure with a null

**Established**
- [KLN08 §I] The null comparison of Q optimises Q on each random graph ("optimize the modularity for a large number of networks drawn from the random graph ensemble"), then uses μ, σ in eq. (1). In the robustness analysis the null is put through "the same set of calculations" (§IV).
- [P23 §III] The modularity deviation "completely ignores the optimization step of Eq. 16, although it is a crucial part of the algorithm". This is "data dredging". The method finds structure in samples of its own null (Fig. 6).
- [P23 §III, Fig. 8] The number of groups found by modularity maximisation in 263 empirical networks and in their degree-preserving randomisations "is strongly correlated", "a strong indication of the substantial amount of noise that is incorporated into the partitions".
- [P23 §IV.C, Fig. 12] Comparing the quality value with randomised networks answers only "Can we reject the hypothesis that the observed network was sampled from a random null model?". In Fig. 12 the null is rejected (P = 0.002) because of one planted six-node clique, while seven other groups are "entirely meaningless". Research 31 §C.2 has the rest.
- [P23 §IV.E] Swapping the null model does not fix this: "the approach will find spurious communities in networks sampled from its null model, regardless of how it is chosen".

**Inference.**
- **Consistency means repeating every data-dependent choice.** The Selected Resolution is chosen from the observed network (CHAMP envelope, then the Stable Partition rule).
  - Clustering a null replicate at the observed Selected Resolution leaves out the selection step, the very gap [P23 §III] describes for the optimisation step.
  - The consistent version runs the **full procedure** on each null replicate at the same (g, s): γ scan, CHAMP, Stable Partitions, the ≥ 3 Multi-Tag Cluster rule.
- **Which statistics are comparable.**
  - Q at γ is only comparable between graphs at the **same γ**. The full procedure gives each null its own γ, so its Q is not comparable with the observed Q (map.md already rules Q out as a cross-graph objective).
  - Statistics that survive the full procedure:
    - whether a qualifying Stable Partition exists;
    - the width of its Optimality Domain (the CHAMP stability notion);
    - the Selected Resolution itself;
    - the number of Multi-Tag Clusters. Per [P23 Fig. 8] this is a weak discriminator for modularity methods; report it, don't lean on it.
  - The fixed-γ comparison (re-optimise Leiden at the observed Selected Resolution, compare Q) is cheaper and continues the app's existing `q_excess`. But it answers only Peixoto's narrower question.
  - The edge-count ratio (null/observed at the same s) is a diagnostic of how much co-occurrence the margins alone produce (already so in ticket 07). Inference from A.4: at s = 2 the null has *more* edges than the observed network.
- **What can be claimed.** Neither comparison says the Clusters are meaningful [P23 §IV.C]. Defensible wording: "the observed table's structure is not reproduced by tables with the same tag and game counts"; "a qualifying Stable Partition was found in k of R null replicates".

**Open for 07.**
1. Full procedure on the null, fixed γ, or both. Recommendation: both. The full procedure answers "would Automatic Parameter Selection have found something this structured in a random table?". Fixed-γ Q gives continuity with `q_excess`.
2. Statistics: existence of a qualifying Stable Partition, Optimality Domain width, number of Multi-Tag Clusters, and Q at the observed Selected Resolution (fixed-γ arm only).
3. R. The map fixes ≥ 100. Only fractions with denominator R can be reported, e.g. "k of 100"; Research 31 notes Phipson & Smyth's 1/(R + 1) floor.

---

## E. Scaling the count thresholds under subsampling

### E.1 Precedent

**Established** [T96] (VLDB 1996, read in full)
- The frequency of an itemset is "the fraction of the baskets" containing it. A threshold `min_fr` is a fraction, so it carries over to a sample of any size (§2).
- When mining a sample, "the frequency threshold is lowered" (example: 2% → 1.5% for a 20,000-row sample) so that the sample's collection "is likely to be a superset of the collection of frequent sets" (§4). Theorem 3 (§5.1) gives a lowered threshold low_fr < min_fr − √((1/(2|s|)) ln(1/δ)) that bounds the probability of missing a given frequent set by δ.
- "Setting the lowered threshold … is not trivial" (§6).

**Not found.** No network, co-occurrence or bibliometric source that rescales minimum-count thresholds under subsampling. Research 31 §D found that VOSviewer justifies its thresholds by default and purpose only. pvclust's multiscale bootstrap rescales the *sample size*, but it has no frequency thresholds [PVC]. My search was limited to these.

**Inference.** The brief's rule (scale g and s by 0.8) treats g/n and s/n as relative frequencies, as Toivonen does. Toivonen's lowering exists to avoid *misses*, which here means losing tags that are in the full network. That argues for the rule that errs towards keeping tags: floor.

### E.2 What each rounding rule does with 80 of 100 games (my computation)

A tag with c games in the full dataset has a Hypergeometric(N = 100, K = c, n = 80) count in a subsample (mean 0.8c). The table shows the probability that a tag **exactly at** the full threshold (c = g) stays at or above g′, and that a tag **just below** it (c = g − 1, absent from the full network) enters the subsample network.

| g | floor / round / ceil of 0.8g | P(keep), c = g: floor / round / ceil | P(enter), c = g − 1: floor / round / ceil |
|---|---|---|---|
| 2 | 1 / 2 / 2 | 0.96 / 0.64 / 0.64 | 0.80 / 0 / 0 |
| 3 | 2 / 2 / 3 | 0.90 / 0.90 / 0.51 | 0.64 / 0.64 / 0 |
| 4 | 3 / 3 / 4 | 0.82 / 0.82 / 0.40 | 0.51 / 0.51 / 0 |
| 5 | 4 / 4 / 4 | 0.74 / 0.74 / 0.74 | 0.40 / 0.40 / 0.40 |
| 6 | 4 / 5 / 5 | 0.91 / 0.66 / 0.66 | 0.74 / 0.32 / 0.32 |
| 8 | 6 / 6 / 7 | 0.80 / 0.80 / 0.50 | 0.57 / 0.57 / 0.20 |
| 10 | 8 / 8 / 8 | 0.68 / 0.68 / 0.68 | 0.43 / 0.43 / 0.43 |
| 12 | 9 / 10 / 10 | 0.81 / 0.56 / 0.56 | 0.62 / 0.31 / 0.31 |
| 15 | 12 / 12 / 12 | 0.65 / 0.65 / 0.65 | 0.44 / 0.44 / 0.44 |
| 20 | 16 / 16 / 16 | 0.64 / 0.64 / 0.64 | 0.44 / 0.44 / 0.44 |

The same table applies to s for a tag pair's shared-game count.

**Inference.**
- No rule is neutral. Integer thresholds make the keep-probability of a borderline tag swing with g mod 5. Every rule gives the same threshold when g is a multiple of 5.
- floor keeps the most borderline tags and lets the most below-threshold tags in.
- ceil does not scale at all for g ≤ 4 (ceil(2.4) = 3, ceil(3.2) = 4). For small g it tests something closer to "the same threshold on fewer games", the harshest version.
- New tags entering the subsample network do not enter the Jaccard under Hennig's rule (B.2), but they can change the subsample's clustering.

**Recommendation.**
- Compute thresholds in integer arithmetic: floor = (4g)//5, round = (4g+2)//5, ceil = −(−4g//5). 0.8·g in floating point invites off-by-one errors under ceil and floor.
- Clamp s′ ≥ 2, since s′ = 1 makes every co-occurrence an edge, a different network regime. Also g′ ≥ s′, which every monotone rule preserves.
- Report per subsample g′, s′ and the retained tags, plus the retention per Multi-Tag Cluster (B.2).

**Degenerate outcomes (Inference).** A subsample is degenerate when its network has no qualifying Stable Partition (fewer than three Multi-Tag Clusters at every Stable Partition), or no edges. Ticket 07 already says failures are reported without changing the selected parameters. The defensible report is "k of S subsamples yielded no qualifying Stable Partition", with those subsamples entering the ARI and Jaccard summaries as missing, never dropped silently. Hennig's B* rule (B.1) is the per-cluster precedent for averaging only where the object exists.

**Open for 07.** The rounding rule (floor is recommended; round is the neutral-looking default and gives the same result for 3 g values in 5), the minimum clamps, and whether γ is re-selected per subsample. A *consistent* subsample, by the argument of Section D, would repeat the full procedure. Holding γ at the Selected Resolution measures something narrower.

---

## F. Open choices for ticket 07 (collected)

1. **Curveball trades:** keep `TRADES_PER_GAME = 10` (recommended) or raise it (e.g. to 20 for a wider margin). The cost is linear: about 10–17 ms per 1,000 trades. That dominates a fixed-γ replicate but is negligible against a full-procedure replicate.
2. **Null procedure:** full Automatic Parameter Selection per null replicate, fixed γ, or both (recommended: both). The full-procedure statistics are existence of a qualifying Stable Partition, Optimality Domain width, Selected Resolution and number of Multi-Tag Clusters. Fixed γ adds Q at the observed Selected Resolution. Edge-count ratio as a diagnostic.
3. **Missing tags in Subsample Stability:** Hennig's present-in-both rule plus a per-cluster retention share (recommended), or penalising absence.
4. **Entirely absent clusters:** fpc's all-B mean (absent = 0) or the preprint's B* mean, with the absent count reported.
5. **Bands:** only ≤ 0.5 = dissolved as principled. 0.6 / 0.75 / 0.85 quoted as fpc's bootstrap guidance, or not at all.
6. **Threshold scaling:** floor (recommended), round or ceil, in integer arithmetic. s′ ≥ 2 clamp. γ re-selected per subsample or held.
7. **KLN-style extensions (optional):** a short curve of subsample fractions instead of a single 80%; Subsample Stability on a few null replicates; VI next to ARI.
8. **Degenerate subsamples:** counted and reported as "k of S"; their handling in the summaries (missing, not dropped).

---

## Sources

Locators are section, equation, figure, table or theorem numbers in the version read. Every source below was read in full text except where noted.

**Curveball**
- [STR14] Strona, G., Nappo, D., Boccacci, F., Fattorini, S., San-Miguel-Ayanz, J. (2014). A fast and unbiased procedure to randomize ecological binary matrices with fixed row and column totals. *Nat. Commun.* 5, 4114. doi:10.1038/ncomms5114. Publisher PDF (Results, "Uniform distribution of null matrices", "Computational demand"; Figs. 1–4; Tables 1–3; Discussion) and Supplementary Information PDF (Supplementary Note 2, Supplementary Fig. 1).
- [C15] Carstens, C. J. (2015). Proof of uniform sampling of binary matrices with fixed row sums and column sums for the fast Curveball algorithm. *Phys. Rev. E* 91, 042812. doi:10.1103/PhysRevE.91.042812. **Abstract only** (APS page); the full text is paywalled.
- [CBS16] Carstens, C. J., Berger, A., Strona, G. (2016–2018). A unifying framework for fast randomization of ecological networks with fixed (node) degrees. arXiv:1609.05137v3 (§4.1–4.2, Figs. 5–6, §5). Journal publication not verified.
- [CK18] Carstens, C. J., Kleer, P. (2017). Comparing the switch and Curveball Markov chains for sampling binary matrices with fixed marginals. arXiv:1709.07290v3 (abstract; §1 Theorem 1; §1.1). Published as "Speeding up switch Markov chains for sampling bipartite graphs with given degree sequence", APPROX/RANDOM 2018, LIPIcs 116, 36:1–36:18, doi:10.4230/LIPIcs.APPROX-RANDOM.2018.36 (title and venue from the Dagstuhl page; content not compared).
- [CHMPTW18] Carstens, C. J., Hamann, M., Meyer, U., Penschuck, M., Tran, H., Wagner, D. (2018). Parallel and I/O-efficient randomisation of massive networks using global Curveball trades. arXiv:1804.08487v2 (§3.3, §5.1, Fig. 5). Journal or proceedings not verified.

**Cluster stability**
- [H07] Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Comput. Stat. Data Anal.* 52(1), 258–271. doi:10.1016/j.csda.2006.11.025. Author preprint of 15 July 2006 from the author's UCL page (`papers/clusta.pdf`; §2 steps (1)–(4) and the mean; §3.1–3.3; §4.1, §4.3; §5 Table 1, Fig. 3; §6).
- [FPC] Hennig, C. `fpc` R package: `clusterboot` reference page, version 2.2-12 (https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html; Usage, Details, Value), and `R/clusterboot.R` from the CRAN GitHub mirror, version 2.2-15 (`clujaccard`; the `subset` branch; `bootmean` etc.).
- [PVC] `pvclust` R package reference page, version 2.2-0 (https://search.r-project.org/CRAN/refmans/pvclust/html/pvclust.html; Arguments `data`, `r`), citing Suzuki & Shimodaira (2006), *Bioinformatics* 22(12), 1540–1542, and Shimodaira (2004), *Ann. Stat.* 32, 2616–2641 (both not read).

**Robustness and null comparison**
- [KLN08] Karrer, B., Levina, E., Newman, M. E. J. (2008). Robustness of community structure in networks. *Phys. Rev. E* 77, 046119. doi:10.1103/PhysRevE.77.046119. arXiv:0709.2108v1 (§I eq. (1); §II; §III.A eqs. (2)–(5) and ref. 44; §III.B eq. (7); §III.C eq. (12); §IV; §V Fig. 1, Table I; §VI).
- [P23] Peixoto, T. P. (2023). Descriptive vs. inferential community detection in networks: pitfalls, myths and half-truths. Cambridge Elements. doi:10.1017/9781009118897. arXiv:2112.00183v7 (§III, Figs. 6 and 8; §IV.C, Fig. 12; §IV.E).

**Thresholds under sampling**
- [T96] Toivonen, H. (1996). Sampling large databases for association rules. *Proc. 22nd VLDB*, Mumbai, 134–145. https://www.vldb.org/conf/1996/P134.PDF (§2 frequency as a fraction; §4 lowered threshold and example; §5.1 Theorems 1 and 3; §6).

**Code**
- `src/steamstudy/network/stability.py` (`curveball`, `null_model`, `TRADES_PER_GAME`), `src/steamstudy/network/graph.py` (`build_network`, `shared_edges`), on branch `auto-parameter-selection` at 0752168.
- Scratch scripts (not in the repo): `mixing_check.py` in the session scratchpad.
