# Research 31: Data-driven choice of the network thresholds and the resolution

Ticket: none (requested by the main session for the research paper)
Date: 2026-10-22

**Question:** Can `min_games_per_tag`, `min_shared_games` and the resolution γ of the **Tag Network** be chosen in a defensible, data-driven way for a paper, instead of the current defaults (8, 8 and 1.0 in `config/network.toml`)? Or should the study adopt or add a method that infers the number or scale of **Clusters** from the data?

How to read this file. Sections marked **Established** report what a cited primary source says, with its section, equation or figure. **Inference** marks my own derivations or readings that no source states. **Recommendation** marks proposals; the researcher decides. Package facts (versions, wheels) come from the PyPI JSON API and the official docs or source code, checked on 2026-10-22. Terms follow [CONTEXT.md](../../../CONTEXT.md). Like the rest of the project, this note does not call a result "significant". Where a method's own name or literature uses the word, it is quoted as the method's term.

Research 05 already covers Louvain vs Leiden, the resolution limit, degeneracy, consensus clustering in general and the random-graph modularity problem [GSA04]. This note builds on that and does not repeat it.

---

## Summary

1. **The thresholds can be replaced by a per-pair test, and both thresholds then follow from the data.** Test each tag pair's shared-game count with a one-sided hypergeometric test, where the tag frequencies and n are fixed (the "statistically validated network" of [T11], eq. (1)). Keep the pairs that pass an FDR or Bonferroni level α. This is the same test as a one-sided Fisher exact test. Neal et al. call this null the Fixed Row Model (FRM) and show that its edge-weight distribution is hypergeometric [NDS21, model definitions]. The project already runs two-sided Fisher tests with BH q for every pair (`associations.csv`), so the change is small.
2. **How the tag-frequency floor falls out (my computation, n = 100).** A pair of tags with c games each can reach at best p = 1/C(100, c). That is 2.0·10⁻⁴ for c = 2, 6.2·10⁻⁶ for c = 3 and 2.6·10⁻⁷ for c = 4. Under a Bonferroni level of 0.05 over all pairs of 200–300 tags, a tag needs **at least 4 games** before any edge of it can pass at all. Tarone's (1990) rule makes this exact: hypotheses that cannot reach the corrected level are left out of the correction [LL15 §5]. The shared-game floor becomes pair-specific. For two 8-game tags it is 6 shared games (lift ≈ 9.4) under Bonferroni, and 3 without correction. **Edges to very frequent tags (in about 60 or more of 100 games) almost never pass**, which makes them One-Tag Clusters (Section A.7).
3. **The FRM test should be close to the exact bipartite null for Steam data (inference, needs a check).** Neal et al. find that FRM and FDSM backbones are very similar when the "artifact" degrees (here, visible tags per game) are constant or normally distributed (Jaccard 1.0 and 0.863) [NDS21 Study 3]. Steam displays at most 20 tags per game, so tags per game should vary little. The project's curveball sampler (`network/stability.py`) can compute exact FDSM p-values in the Build as a check.
4. **Disparity filter and noise-corrected backbone are poor fits.** Both test a weighted network with no knowledge that it is a bipartite projection. Neal shows a disparity backbone of a projection that comes out empty [N22]. The noise-corrected "lift" is built from node strengths, not from game counts [CN17 §IV].
5. **γ from data: Newman's estimate exists, but it is a heuristic.** The estimate is γ = (ω_in − ω_out)/(ln ω_in − ln ω_out) [N16 eq. (15)], iterated with eqs. (17)–(18). Newman himself gives "no formal guarantees of correctness or convergence" for real networks [N16 §III.A]. Zhang & Peixoto show that the iteration does not restore consistency with maximum likelihood [ZP20 §II.A]. The paper does not cover weights. Gibson & Mucha's **stable partitions** (fixed points of the γ map inside their CHAMP domain) [GM22] are the most defensible form. They are implemented in `modularitypruning` 2.0.1, a pure-Python wheel built on leidenalg that supports weights as "an extension beyond the original publication" [MP-SRC].
6. **leidenalg can scan γ exactly.** `Optimiser.resolution_profile` bisects γ and keeps only the γ values where the partition changes [LA-REF, LA-SRC]. Its default stopping rule (`min_diff_bisect_value=1`) assumes integer weights and must be rescaled for lift. Leiden's **Significance** objective is parameter-free but "not suitable for weighted graphs" [LA-REF]. **Surprise** accepts positive weights and tends to over-split [TAD15 §VI].
7. **PyGenStability (Markov stability) cannot be installed from wheels on Windows or on Python 3.12–3.14.** Version 0.2.7 ships only cp38 wheels for Linux and macOS and no sdist. Its scale-selection idea can be reproduced with leidenalg, because linearised Markov stability is equivalent to the RB modularity [LDB14 eq. (9)]: low seed-to-seed variation at a γ, and persistence across neighbouring γ [A24 §2.3].
8. **Methods with no resolution parameter: the nonparametric (nested, degree-corrected) SBM.** It infers the number of groups by minimum description length and does not find groups in maximally random networks [P14, P17, P23 Fig. 2]. A bipartite SBM can be fitted to the game–tag matrix directly, which avoids both thresholds and γ [LCJ14, YL20]. graph-tool has **no pip wheels and no native Windows support**: it is installed with conda-forge (Linux, macOS), Docker or WSL [GT-INST, PYPI]. It can therefore only be used in the Build pipeline, and only under WSL or Docker on this machine.
9. **Peixoto (2023) bears directly on this study.** Modularity is descriptive: it finds groups in networks drawn from its own null model, and a null-model test of Q only shows that the *network* is not random, not that the *partition* is meaningful [P23 §III, §IV.C, Fig. 12]. That is exactly what the project's `q_excess` measures, so the paper must word it that way. Peixoto accepts descriptive methods when the conclusions would not change if the network were maximally random (his "litmus test", §II.B).
10. **Infomap** (pip wheels for Windows and Linux; macOS only arm64, 15+) returns a single module on random graphs except sparse ones [LF09 §VII]. It is still descriptive [P23 §II.D] and has its own scale knob (`markov_time`) [IM-OPT].
11. **Reporting practice.** VOSviewer's documentation justifies its thresholds by default and by purpose ("terms with fewer than 10 occurrences are excluded"; try resolutions and use "the most appropriate level of detail for one's purposes") [VOS pp. 23–24, 37], not by a statistical criterion. A **multiverse analysis** (run every reasonable choice and report all results) is the citable framework for a sensitivity grid [SVGV16].
12. **Ranked recommendation** (Section H): (1) a validated tag network (one-sided hypergeometric + BH) with γ from the stable-partition pruning; (2) a nonparametric bipartite SBM cross-check in the Build, under WSL or Docker; (3) a multiverse grid over thresholds and γ with a plateau criterion, reported in any case as a supplement.

---

## A. Replacing the hard thresholds with a statistical edge filter

### A.1 Why fixed thresholds are hard to defend

**Established**
- Coscia & Neffke call a fixed weight cut-off the "Naive" approach. In broad weight distributions there is no characteristic scale, which renders "the choice of δ meaningless". Local weight correlations mean that whole parts of the network can be cut off [CN17 §III.B].
- Neal et al.: a global threshold applied to a projection "still yields highly clustered networks in which low-degree nodes are excluded while high-degree nodes are preserved". Every method built for ordinary weighted networks "ignore[s] information about the artifacts, which is lost when generating the projection" [NDS21, Introduction].
- Larremore et al.: projections "are necessarily composed only of overlapping cliques, which are extremely low probability under most community detection null models, including Girvan-Newman modularity Q, and tend to inflate measures such as assortativity and the clustering coefficient" [LCJ14 §I].

**Inference.** In our Tag Network a game with k visible tags adds a k-clique, and a shared-count threshold keeps every edge between frequent tags whether or not they co-occur above chance. Under the lift Clustering Weight, the edges that survive the shared-count threshold include pairs with lift < 1 (frequent tags that co-occur *less* than expected). Modularity still treats them as positive attraction. A test-based filter removes them.

### A.2 Statistically validated networks (Tumminello et al. 2011)

**Established** [T11]
- **Test.** For two elements A and B with N_A and N_B occurrences among N_T observations, the null of random co-occurrence gives the hypergeometric H(X | N_T, N_A, N_B) (eq. (1)). The p-value is p(N_AB) = 1 − Σ_{X=0}^{N_AB−1} H(X | N_T, N_A, N_B), a one-sided test for over-representation.
- **Heterogeneity of the other set.** The null accounts for how frequent A and B are. To also control for the heterogeneity of the other set, the authors test within subsets of equal degree (their "COG_k" subsets). For the movie–actor data they skip this and accept that "a number of false positive links can be expected".
- **Multiple testing.** Bonferroni at p_t / N_t with p_t = 1% (Bonferroni network), or FDR [BH95] (FDR network). By construction the Bonferroni network is a subgraph of the FDR network, which is a subgraph of the full co-occurrence network.
- **Random-network check.** "By randomly rewiring the bipartite network the associated Bonferroni network was empty" for all three systems (concluding paragraph).
- Community detection (Infomap) on validated networks gave clear communities where the full network, a complete graph in the COG example, did not.

**Applied to this study (inference).** In our case N_T = n = the number of games in the Network State (100, or fewer after the Minimum Months Filter), and N_A, N_B are tag frequencies. The test equals `scipy.stats.fisher_exact(..., alternative="greater")` on the 2 × 2 table, or `hypergeom.sf(s − 1, n, c_a, c_b)`. Note that `features.py` currently uses `alternative="two-sided"` (line 154). A two-sided p also flags avoidance pairs, which must not become edges. The parameter left is α (or q) and the choice between FWER and FDR. BH controls FDR under PRDS dependence [BY01 Thm 1.2]; BY works under any dependence [BY01 Thm 1.3]. Tag-pair tests share margins, and PRDS is not shown for them, which is the same caveat Appendix C already records.

### A.3 Bipartite null models: FDSM, FRM, SDSM, BiCM (Neal; Saracco)

**Established**
- Neal (2014) introduced backbone extraction for bipartite projections [N14]. It is cited here through [NDS21]; I did not read the Social Networks article.
- Neal, Domagalski & Sagan compare five ensembles [NDS21, model definitions]:
  - **FDSM** fixes the agent and artifact degrees exactly. Its edge-weight distribution "is unknown" and is estimated by Monte Carlo; they use 1000 curveball samples [STR14].
  - **FRM** fixes the agent degrees only. Its distribution "is hypergeometric … sometimes referred to as the hypergeometric model", and it is the model used by [T11].
  - **FCM** fixes the artifact degrees only (Poisson-binomial).
  - **FFM** fixes the number of ones only.
  - **SDSM** has Bernoulli cells with probabilities p_ik that match both degree sequences on average (Poisson-binomial). Their decision rule keeps an edge if Pr(P*_ij ≥ P_ij) < α/2 (two-tailed), "however a one-tailed test may also be used".
- **Which model approximates FDSM** [NDS21 Study 3; synthetic 100 × 100 bipartite networks, density 0.1, close to our size]:
  - All models give the FDSM backbone (mean J = 1) when agent degrees are constant and artifact degrees are constant or left-tailed.
  - FRM vs FDSM "depends primarily on the distribution of artifact degrees". It is very similar for normally distributed artifact degrees (J = 0.863) and very different for right-tailed ones (J = 0.186).
  - SDSM at α = 0.05 is more conservative than FDSM. With α ≈ 0.13 it reproduces an FDSM backbone at α = 0.05 (mean J = 0.865).
  - Recommendations: SDSM with BiCM probabilities, and SDSM at α = 0.13 when an FDSM-like backbone at 0.05 is wanted (Discussion).
- Saracco et al. validate projections against the BiCM (maximum-entropy, degrees matched on average) with a Poisson-binomial test of the shared-neighbour count (V-motifs) and FDR [S17 §II.B–C]. Their rule of thumb: Bonferroni suits cases where few tests are expected to pass. Otherwise it "may … produce a too large number of false negatives" and "very sparse (if not empty) projections" [S17 §II.C].
- Neal's R package `backbone` implements `sdsm()`, `fdsm()`, `fixedrow()`, `fixedcol()`, `fixedfill()` and `disparity()`. It recommends models built for projections and offers Holm correction (`mtc = "holm"`) [N22].

**Applied to this study (inference, needs an empirical check).**
- In the tag projection the **agents are tags** (degree = tag frequency) and the **artifacts are games** (degree = visible tags per game). Steam displays at most 20 tags per game (CONTEXT.md, "Tag"). After hiding the Genre Tags and the defining tag, the per-game degree is probably narrow and roughly normal. If so, [NDS21 Study 3] predicts that the simple FRM / hypergeometric / one-sided Fisher test gives nearly the FDSM backbone.
- The project already has a curveball sampler (`src/steamstudy/network/stability.py`, `curveball`, `TRADES_PER_GAME = 10`), so FDSM p-values can be computed in the Build as a check. **Cost caveat:** a Monte Carlo p-value cannot go below 1/(R + 1) [PS10]. A BH threshold near 0.05/M with M ≈ 5,000 pairs needs R of about 10⁵ samples, which is Build-only. The 10 trades per game were chosen for the modularity null, and their mixing for pair-level p-values has not been checked.
- `bicm` 3.4.0 (pure-Python wheel, `py3-none-any`; depends on numba, which has cp312–cp314 wheels for Windows, Linux and macOS arm64) provides BiCM probabilities and validated projections (`compute_projection(rows=True, alpha=0.05, method='poisson', …)`) [BICM]. The README warns that an earlier projection threshold "was validating less links than it should have".

### A.4 Disparity filter (Serrano, Boguñá & Vespignani 2009)

**Established** [SBV09]
- Null: a node of degree k divides its strength among its k edges as if k − 1 points were placed uniformly on [0, 1], giving ρ(x) = (k − 1)(1 − x)^{k−2} (eq. [1]).
- For edge (i, j), p_ij = w_ij / s_i and α_ij = 1 − (k − 1) ∫₀^{p_ij} (1 − x)^{k−2} dx (eq. [2]). That equals (1 − p_ij)^{k−1}, which is my closed form, not stated in the paper. An edge is kept if α_ij < α "for at least one of the two nodes".
- The parameter is α. The paper reports, for example, α ≈ 0.05 keeping 17% of edges in the US airport network.

**Fit for this study (inference).**
- The test knows nothing about games or n.
- In a dense projection a frequent tag has degree near the number of tags, so its share p_ij is small for every edge and its edges survive mainly through the other endpoint.
- Neal shows a projection whose disparity backbone is empty while a projection-aware model is not [N22, "Bipartite projections" toy example].
- No frequency floor falls out of the test.
- Python: `backbone-network` 1.1.3 (pure Python, last release 2022) [PYPI]. A ten-line implementation is just as easy.

### A.5 Noise-corrected backbone (Coscia & Neffke 2017)

**Established** [CN17 §IV]
- Expected weight E[N_ij] = N_i. N_.j / N.. from **node strengths**. Lift L_ij = N_ij / E[N_ij], transformed to L̃ = (L − 1)/(L + 1) (eq. (1)).
- Variance by the delta method, with a Beta posterior for P_ij whose prior comes from a hypergeometric model of strengths.
- An edge is kept if L̃_ij exceeds δ standard deviations. δ is "the only parameter", with common values 1.28, 1.64 and 2.32 (≈ p 0.1, 0.05, 0.012, one-tailed).
- The authors released a `backboning` Python module (not on PyPI: the PyPI name `backboning` returns 404).

**Fit for this study (inference).** Its "lift" uses co-occurrence strengths (sums of shared counts over all partners), not tag frequencies over n games. It is therefore a different quantity from the project's Lift (shared·n/(c_a·c_b), CONTEXT.md). It accounts for the network's weights but not for the bipartite structure, so Neal's critique in A.1 applies. No frequency floor falls out.

### A.6 Comparison of the edge filters

| Filter | What it tests | Parameter left | Does a frequency floor fall out? | Suited to n = 100 games? | Python (Windows, 3.12–3.14) |
|---|---|---|---|---|---|
| Fixed thresholds (current) | nothing | `min_games_per_tag`, `min_shared_games` | no (set by hand) | — | built in |
| Hypergeometric / FRM / one-sided Fisher [T11, NDS21] | shared count vs. random placement, tag frequencies and n fixed | α (or q), FWER vs FDR | **yes**: minimum attainable p (A.7); exact with Tarone [LL15] | yes; exact test, no asymptotics | SciPy (already a dependency) |
| FDSM [NDS21] | same, with tags per game also fixed exactly | α, Monte Carlo R | yes, but the floor depends on R | yes; R ≈ 10⁵ needed for small α | project's curveball (Build only) |
| SDSM / BiCM [NDS21, S17] | both degree sequences matched on average | α (≈ 0.13 mimics FDSM at 0.05) | approximately | yes | `bicm` 3.4.0 pure wheel + numba |
| Disparity filter [SBV09] | a node's weight shares vs uniform split | α | no | weak (ignores n and games) | `backbone-network` 1.1.3 pure wheel, or hand-written |
| Noise-corrected [CN17] | strength-based lift vs binomial | δ | no | weak (ignores n and games) | not on PyPI; easy to reimplement |

### A.7 Worked numbers for n = 100 (my computation, not a literature value)

Computed with `scipy.stats.hypergeom` (one-sided upper tail). The script is in the session scratchpad, not in the repo. "Bonf K" means Bonferroni level 0.05 / C(K, 2) over all pairs of K tags.

**Minimum attainable p for two tags of equal frequency c** (they share all c games): 1/C(100, c).

| c | 2 | 3 | 4 | 5 | 6 | 8 |
|---|---|---|---|---|---|---|
| p_min | 2.0·10⁻⁴ | 6.2·10⁻⁶ | 2.6·10⁻⁷ | 1.3·10⁻⁸ | 8.4·10⁻¹⁰ | 5.4·10⁻¹² |

Bonferroni levels: K = 100 gives 1.0·10⁻⁵; K = 200 gives 2.5·10⁻⁶; K = 300 gives 1.1·10⁻⁶. The smallest frequency at which a tag can have **any** edge pass is therefore **3** (K = 100) or **4** (K ≥ 200). With a partner of a different frequency it is higher: for c_a ≤ c_b, p_min = C(c_b, c_a)/C(100, c_a), which grows with c_b.

**Minimum shared games s for a pair to pass** (with the implied lift = s·100/(c_a·c_b)):

| (c_a, c_b) | Bonf K = 100 | Bonf K = 300 | unadjusted 0.05 |
|---|---|---|---|
| (5, 5) | s = 4 (lift 16) | s = 5 (lift 20) | s = 2 (lift 8) |
| (8, 8) | s = 6 (lift 9.4) | s = 6 (lift 9.4) | s = 3 (lift 4.7) |
| (10, 10) | s = 7 (lift 7.0) | s = 7 (lift 7.0) | s = 4 (lift 4.0) |
| (20, 20) | s = 12 (lift 3.0) | s = 13 (lift 3.25) | s = 8 (lift 2.0) |
| (30, 30) | s = 19 (lift 2.1) | s = 20 (lift 2.2) | s = 13 (lift 1.4) |
| (50, 50) | s = 37 (lift 1.5) | s = 38 (lift 1.5) | s = 30 (lift 1.2) |
| (8, 30) | impossible | impossible | s = 6 (lift 2.5) |
| (8, 60) | impossible | impossible | s = 8 (lift 1.7) |
| (10, 90) | impossible | impossible | impossible |
| (30, 90) | impossible | impossible | s = 30 (lift 1.1) |

Reading the tables (inference):
- **Tag-frequency floor.** With a family-wise correction, `min_games_per_tag` is implied at about 3–4. With BH the effective level lies between the Bonferroni and the unadjusted column and depends on how many pairs pass, so the floor is data-dependent. Tarone's procedure formalises this: drop the pairs whose minimum attainable p exceeds the tentative level, shrink the correction factor accordingly, and take the largest δ with δ·m(δ) ≤ α [LL15 §5, describing Tarone 1990].
- **Shared-game floor.** `min_shared_games` becomes pair-specific: high for rare pairs, a large share of the smaller tag for frequent pairs.
- **Near-universal tags lose their edges.** A tag in about 90 of 100 games can only rarely be validated against anything. This matches what Li & Zhang did by hand (removing the five highest-degree tags, Q 0.150 → 0.414; research 30, [LZ20]), but it follows from the test rather than from a choice. Such tags become One-Tag Clusters.
- **Power is low** for rare tags at n = 100. Even a perfect co-occurrence of two 3-game tags fails a Bonferroni correction over 300 tags. Any validated network will be sparser than the current one.

---

## B. Choosing γ from the data

### B.1 Newman (2016): modularity and the planted-partition likelihood

**Established** [N16]
- Generalised modularity Q(γ) = (1/2m) Σ_ij (A_ij − γ k_i k_j / 2m) δ(g_i, g_j) (eq. (6)).
- With the degree-corrected planted-partition model, θ_rs = (ω_in − ω_out) δ_rs + ω_out (eq. (12)). The log-likelihood is B·Q(γ) + C (eq. (14)), with
  **γ = (ω_in − ω_out) / (ln ω_in − ln ω_out)**   (eq. (15)).
  For known ω_in and ω_out, maximising the likelihood over the group assignments is the same as maximising Q(γ) (§III).
- Estimates from a partition (§III.A):
  **ω_in = 2 m_in / (Σ_r κ_r² / 2m)**   (eq. (17)) and **ω_out = (2m − 2 m_in) / (2m − Σ_r κ_r² / 2m)**   (eq. (18)).
  Here m_in is the number of within-group edges, κ_r the sum of degrees in group r, and m the number of edges.
- Iteration: start with γ = 1, maximise Q(γ), re-estimate ω_in and ω_out, recompute γ, and repeat until it converges. Newman reports convergence "within a few percent after just one iteration" and never more than ten iterations in his tests (§III.A; Fig. 1, Table I).
- Caveats from the author himself:
  - "For all other networks (meaning, in practice, for all real-world applications of the method) we have no formal guarantees of correctness or convergence" (§III.A).
  - "Whether the algorithm given here is in fact a useful one in practice is a debatable point" (§III.A).
  - Modularity "assumes all communities in a network to be statistically similar" and "implicitly favors groups of uniform size" (§III).
- Weights: the model is a Poisson multigraph with integer A_ij. The paper does not mention weighted networks.

**Critiques (Established)**
- Zhang & Peixoto [ZP20 §II.A]:
  - The equivalence holds with maximum likelihood "only in the very narrow case where all groups have the same sum of degrees" (point 1).
  - "The scheme suggested in Ref. [21] of updating the value of γ according to Eq. 16 is insufficient to restore consistency" (point 2).
  - Their nonparametric planted-partition inference finds assortative groups "unlike alternatives such as modularity maximization, which systematically overfits" (abstract).
- Peixoto: the maximum-likelihood γ "is only applicable for situations when the number of groups is known, directly undermining its use to counteract the resolution limit" [P23 §IV.D, footnote 20]. Equivalences "expose more clearly its sins, but offer no redemption" [P23 §IV.A].
- Gibson & Mucha: the SBM equivalence is "only known for unweighted multigraphs" (Discussion). Resolution estimates "can strongly depend on the number of communities" (karate club section) [GM22].

**Weights and lift (inference, my derivations).**
- (a) Eqs. (15)–(18) use A only through m, m_in and κ_r, so they can be evaluated for any non-negative weights. `modularitypruning` does exactly that (`estimate_singlelayer_SBM_parameters` sums `e['weight']`) [MP-SRC].
- (b) Multiplying all weights by c > 0 leaves ω_in, ω_out and γ unchanged. Only the relative internal weight matters.
- (c) γ in eq. (15) is the logarithmic mean of ω_in and ω_out, so it always lies between them.
- (d) For the **shared-game count** (integer) the multigraph reading is formally available: each shared game is one parallel edge. But projection edges come in cliques, not as independent Poisson draws [LCJ14 §I], so the model is misspecified.
- (e) For **lift** (non-integer) the likelihood interpretation is lost. The formula is then a heuristic rescaling with no generative model behind it.

### B.2 CHAMP (Weir et al. 2017) and stable partitions (Gibson & Mucha 2022)

**Established**
- For a fixed partition, Q(γ) is linear in γ. Given a set of partitions from many runs and γ values, CHAMP computes the upper convex hull of these lines and each partition's "domain of optimality" (the γ interval where it beats every other partition in the set), and discards partitions with empty domains [W17 abstract, §2]. Users can then "select robust community structures by observing the sizes of domains of optimization". CHAMP "itself is not a method for partitioning a network": it can only rank the partitions it is given (Discussion).
- Gibson & Mucha map each admissible partition to its Newman γ estimate. "The 'stable' partitions are those whose parameters fall within their domains of optimality; that is, they are fixed points of the map" [GM22, Fig. 1(d) caption]. In their examples few partitions remain. The one-community partition has no γ estimate (Figs. 2 and 4 captions).
- Implementation:
  - `modularitypruning` 2.0.1 (released 2026-10-20; `py3-none-any`; requires leidenalg, igraph, numpy, scipy, scikit-learn, matplotlib, seaborn, psutil and tqdm, all with Windows wheels for 3.12–3.14) [PYPI].
  - `prune_to_stable_partitions(G, parts, gamma_start, gamma_end, restrict_num_communities=None)`: "Directed, undirected, weighted, and unweighted graphs are supported. Edge weights must be non-negative." It warns that disconnected graphs are not thoroughly tested [MP-SRC].
  - It includes its own CHAMP (`CHAMP_2D`). The original `champ` 2.1.1 package depends on Traag's deprecated `louvain`, which has no wheels for 3.12 or later, so it fails the ADR 0001 constraint [PYPI].
  - The module `iterative_monolayer_resolution_parameter_estimation` implements Newman's iteration, citing Pamfil et al. (2019), doi:10.1137/18M1231304 [MP-SRC]. I did not read Pamfil et al.

**Inference.** For this study the stable-partition approach turns "pick γ" into "report the partitions that are self-consistent under the planted-partition reading, and the γ range over which each is optimal". If no stable partition exists in [γ_min, γ_max], that is itself a reportable result. With 30–95 nodes, thousands of Leiden runs cost seconds.

### B.3 leidenalg resolution profile (bisection)

**Established**
- `Optimiser.resolution_profile(graph, partition_type, resolution_range, weights=None, bisect_func=lambda p: p.bisect_value(), min_diff_bisect_value=1, min_diff_resolution=0.001, linear_bisection=False, number_iterations=1, **kwargs)` returns "a list of partitions for different resolutions". The partition type must have a linear resolution parameter (RBConfiguration, RBER or CPM) [LA-REF].
- In the source, `bisect_value()` returns `total_weight_in_all_comms()`. Bisection is geometric unless 0 is in the range. A post-pass (`ensure_monotonicity`) replaces a partition by one found at another γ if that one scores better there [LA-SRC].
- Traag, Krings & Van Dooren prove for CPM that a partition optimal at γ₁ and γ₂ is optimal on [γ₁, γ₂] (Theorem 1), and that the internal edge count and the sum of squared sizes change monotonically with γ (Theorem 2). Only the change points need to be found. Long plateaus mean "more clear-cut" structure [TKV13 §II.A, eq. (4)]. The paper restricts itself "to simple, unweighted graphs" (§II).

**Inference.**
- The same proof applies to `RBConfigurationVertexPartition`, which is also linear in γ (Q = E_in − γ Σ_c K_c²/4m) [LA-REF formula]. leidenalg treats it the same way.
- With lift weights (typically 0.5–10) the default `min_diff_bisect_value=1` is coarse. Set it relative to the total weight, for example 10⁻³ · Σw.
- A resolution profile is CHAMP's input with the γ values chosen adaptively. Profile, then CHAMP, then stable-partition pruning chain naturally.

### B.4 Significance and Surprise (Traag et al. 2013, 2015)

**Established**
- **Significance** S = Σ_c C(n_c, 2) · D(p_c ‖ p), with p_c the community density and p the graph density (D is the binary Kullback–Leibler divergence) [TKV13 eq. (8); LA-REF].
  - leidenalg: `SignificanceVertexPartition(graph, initial_membership=None, node_sizes=None)` has **no weights argument**: "This method is not suitable for weighted graphs" [LA-REF].
  - Use: choose the γ of CPM with the highest significance, or optimise significance directly. "Significance as an objective function is not resolution limit free" [TKV13 §II.B.2].
  - In ER graphs the maximum significance "seems to scale as n log n", which gives a reference value [TKV13 Fig. 3b and the text on ER graphs that follows it].
- **Surprise**, asymptotic form Q = m · D(q ‖ ⟨q⟩), with q the internal edge share and ⟨q⟩ the internal share of node pairs [TAD15; LA-REF].
  - Weighted version: q becomes the internal weight share and ⟨q⟩ stays a pair share, "assuming then a uniform distribution of weights" [TAD15 §II].
  - leidenalg: "well-defined only for positive edge weights" [LA-REF].
  - "Surprise tends to overestimate the number of communities, whereas [they] may be underestimated by modularity"; it "tends to find substructure in larger communities, arising from random fluctuations" [TAD15 §VI].
  - Both measures use an ER-type null (no degree correction) [TAD15 §III].

**Inference.** On a **validated, unweighted** backbone (A.2), Significance becomes applicable and parameter-free, and it pairs naturally with an edge filter that already removes the frequency effect. On the weighted lift network only Surprise applies. Its uniform-weight and ER assumptions do not hold for co-occurrence data, where tag degrees are very heterogeneous.

### B.5 Markov stability and PyGenStability

**Established**
- Delvenne, Yaliraki & Barahona define a partition's stability r(t) as the clustered autocovariance of a random walk. Markov time t acts as a resolution, and r(1) is modularity [DYB10]. The linear interpolation r(0)(1 − t) + t r(1) (eq. (5)) "provides an interpretation in terms of Markov time of the resolution parameter proposed by Reichardt and Bornholdt".
- Lambiotte, Delvenne & Barahona: the linearised stability Q_NL(t) = (1 − t) R_NL(0) + t Q_conf (eq. (9)) "is equivalent up to a linear transformation to the tuneable Hamiltonian proposed by Reichardt and Bornholdt". Relevant scales are found by "plateaux" of persistence over t [LDB14, "Time as a resolution parameter"]. By my algebra, the correspondence is γ = 1/t.
- PyGenStability [A24 §2.3–2.4]:
  - It runs Louvain or Leiden n_tries (= 100) times at each of n_scale (= 20) scales.
  - It measures the average normalised variation of information **NVI(t)** within a scale (robustness to the optimiser) and **NVI(t, t′)** across scales (persistence).
  - It selects scales at minima of a smoothed "Block NVI" (after Schindler, Clarke & Barahona 2023 [SCB23]).
  - It supports weighted undirected graphs (§2.2).
- **Availability** [PYPI]:
  - 0.2.7 (2026-03-09) ships only `cp38-cp38` wheels for macOS arm64, manylinux x86_64 and musllinux, and **no sdist**.
  - 0.2.5 had cp310–cp312 wheels for Linux and macOS.
  - No version has a Windows wheel.
  - It is therefore not installable from wheels on Windows or on 3.13/3.14, which fails ADR 0001 for the app. The Build could only use it on Linux/WSL with a source build (needs cmake and pybind11).

**Inference.** Because linearised Markov stability is RB modularity with γ = 1/t, PyGenStability's *criterion* can be reproduced with leidenalg and the project's existing pieces:
- the **Seed-Noise Floor** at each γ gives the within-scale variation (ARI or VI);
- the **Resolution Sweep**, extended to a denser γ grid with partitions compared across neighbouring γ, gives the persistence.

This needs no new dependency. The full (non-linearised) Markov stability is not reproduced this way.

### B.6 Multiresolution and consensus clustering

**Established**
- Jeub, Sporns & Fortunato:
  - "Event sampling" draws γ values so that all scales of the multiresolution modularity are covered.
  - Hierarchical consensus uses a modularity whose null model is built from the ensemble of partitions, which "allows us to assess statistical significance of co-classification". As a result the procedure "does not identify communities in random networks … without the need of setting an arbitrary threshold" (Introduction).
  - It has a significance level α (0.05 in their Fig. 8).
  - "Consensus clustering is essentially a noise-reduction technique, that delivers robust results, but not necessarily a better solution of the problem" (Introduction).
  - The implementation is **MATLAB only** (github.com/LJeub/HierarchicalConsensus) [JSF18].
- Lancichinetti & Fortunato: consensus matrix D, entries below a threshold τ set to zero, re-clustering until stable. τ and the number of runs n_P are parameters, and "the best value of τ is situation dependent" [LF12 Methods, Appendix A; also JSF18 on LF].
- Peixoto: "a descriptive community detection method can in fact display a cohesive set of solutions on a maximally random network" (his Fig. 11: consensus over 10⁵ maximum-modularity runs on an ER graph shows substantial agreement). "Solution heterogeneity and overfitting are, in general, orthogonal concepts" [P23 §IV.B].

**Inference.** Consensus reduces seed noise, which the project already measures (Seed-Noise Floor, Membership Stability). It does not by itself choose γ or protect against random structure. Jeub's null-model consensus is the exception, but it has no Python package.

---

## C. Methods without a resolution parameter

### C.1 Nonparametric Bayesian / MDL stochastic block models (Peixoto)

**Established**
- [P14] (abstract): a nested SBM with model selection by minimum description length "is capable of separating signal from noise, and thus will not lead to the identification of spurious modules even on sparse networks". It removes the resolution limit that also affects non-nested SBM inference.
- [P17] (abstract): a microcanonical nonparametric SBM infers "the number of modules and their hierarchical organization". By the MDL reading, more groups lower the data term but raise the model term, which acts as a "penalty" against overfitting (§II).
- [P18] (abstract, §II, §IV): a weighted SBM in which **edge weights are covariates on the edges that exist**, with the edges themselves modelled by the SBM. Weight models cover continuous, discrete, signed and bounded data (exponential, normal or log-normal via y = ln x, geometric, binomial, Poisson). The best weight model is selected by posterior odds or description length.
- [ZP20]: a Bayesian **assortative planted-partition** model is "not subject to a resolution limit" and avoids the overfitting of modularity.
- [P23 Fig. 2]: an inferential method "would find only a single community" in a degree-constrained random network where descriptive methods find 13 groups.
- **Bipartite input.** Larremore, Clauset & Jacobs formulate a bipartite SBM that is "projection-free and statistically principled" [LCJ14 abstract]. Yen & Larremore give a nonparametric biSBM that "parsimoniously chooses the number of communities". They report "a counterintuitive regime … populated by smaller and sparser networks, where non-hierarchical models outperform" the nested one [YL20 abstract]. Their discussion refers to the nested SBM "implemented in graph-tool".
- **graph-tool availability.**
  - Installation is via conda-forge ("GNU/Linux and MacOS"), Docker, OS packages, or compilation. Its C++ dependencies (Boost, CGAL) are "not installable via Python-only package management systems such as pip". "To use graph-tool on windows, you need to first install Windows Subsystem for Linux (WSL)" [GT-INST].
  - PyPI lists `graph-tool` release names (2.2.6 … 2.11) with **zero files** [PYPI].
  - The homepage gives 3.9 as the newest version.

**Inference (fit for this study).**
- **Input choice matters.**
  - Fitting the SBM to the **bipartite game–tag matrix** (with tag and game groups kept apart) uses the raw data, needs no `min_shared_games` and no γ, and models games and tags together. The `min_games_per_tag` floor could still be applied for readability, but the model does not need it.
  - Fitting to the projection multigraph (A_ij = shared games) misrepresents the clique structure [LCJ14].
  - Fitting to a thresholded simple graph brings the threshold back.
- **Small, dense data.** With about 100 games and 30–300 tags the description-length penalty may favour very few tag groups, possibly one. Peixoto's framework treats such a result as information ("no evidence for more groups"), not as a failure. That would be a substantive finding for the paper.
- **Weights.** For the projection, [P18] puts weights on the edges that exist, so the edge set (and with it a threshold or a filter) still matters. That is one more reason to use the bipartite input.
- **Constraint.** Build-only, under WSL or Docker on this Windows machine. It can never be part of the App Bundle (ADR 0001).

### C.2 Peixoto (2023), "Descriptive vs. inferential community detection": the argument, summarised fairly

**Established** [P23]
- **Two goals** (§II.A–B). Descriptive methods summarise patterns by a chosen criterion. Inferential methods fit a generative model and separate structure from randomness. Litmus test: "Would the usefulness of our conclusions change if we learn, after obtaining the communities, that the network being analyzed is maximally random?" If yes, an inferential approach is needed; if no, a descriptive one may be appropriate. Peixoto stresses that the question is hypothetical, not a claim that real networks are random.
- **Modularity is descriptive and overfits** (§III, Fig. 6). It finds high-scoring partitions in networks sampled from its own null model, because the null comparison "completely ignores the optimization step". It also underfits through the resolution limit (Fig. 7) and has a degenerate landscape.
- **Myths, each argued with an example** (§IV):
  - A. Modularity and SBM inference are not interchangeable: Newman's equivalence holds only for particular parameter values.
  - B. Consensus does not remove overfitting (Fig. 11).
  - C. Testing Q against a randomised network answers "can we reject the hypothesis that the observed network was sampled from a random null model?" and nothing about the partition. Fig. 12: one planted clique makes Q "significant" while the other seven groups are spurious.
  - D. Tuning γ needs prior knowledge of the scale, and "in many cases no single value of γ is appropriate" (Fig. 13).
  - H. Inference does not require believing the model. An SBM fitted to a latent-space network yields a "caricature … much like a histogram", and description length shows whether a pattern compresses the data.
- **Concessions** (§II.A, §II.D, §II.F). Descriptive methods are right when the litmus answer is "no" (e.g. chip design, task scheduling). Infomap is "inferential with respect to an artificial dynamics" but "still only descriptive" of structure. Inferential methods face NP-hard optimisation and misspecification, and are "not a 'silver bullet'".

**How it applies here (inference).**
- The study's **q_excess / modularity z** against the curveball null is exactly the test that §IV.C says answers only "is this network different from the null?". The User Guide and the paper should say so, which is consistent with the project's existing refusal to call anything significant.
- Whether the paper needs an inferential method depends on its claims. "Tags X, Y and Z form a recurring combination among the most-played games" would lose its meaning if the network were maximally random given tag frequencies and tags per game. The litmus answer is then "yes", for that claim.
- A defensible paper either (a) adds an inferential cross-check (Pipeline 2), or (b) keeps modularity as a *descriptive summary* and moves the inferential burden to the pair level: each retained edge has passed a test against a bipartite null (Pipeline 1).

### C.3 Infomap / map equation

**Established**
- The map equation finds modules by "optimally compressing a description of information flows" of a random walk, and works on weighted and directed networks [RB08 abstract].
- On ER and scale-free random graphs (1000 nodes), "Infomap always finds a single module comprising all nodes, except when ⟨k⟩ is low". Modularity methods "always find a few clusters, even in the limit of large ⟨k⟩" [LF09 §VII].
- The map equation's resolution limit is set by the number of links *between* modules rather than in the whole network, so it is "much less restrictive" than that of modularity [KR15 abstract].
- In sparse or incompletely observed networks Infomap can "detect spurious partitions with more and smaller communities". A Bayesian prior network ("regularized" mode) counters this, for weighted and directed networks too [SBER21 abstract, §"Regularized network flows"].
- Peixoto classes Infomap as descriptive of network structure, liable to find communities in maximally random networks [P23 §II.D].
- `infomap` 2.15.1 Python options include `two_level`, `num_trials`, `seed`, `markov_time` ("Higher values result in fewer modules"), `variable_markov_time`, `regularized`, `regularization_strength`, `prefer_modular_solution` ("Prefer a modular solution even when one module gives a lower codelength") and `entropy_corrected` [IM-OPT].
- Wheels: cp311–cp314 for win32, win_amd64, manylinux x86_64/aarch64, and **macOS only `macosx_15_0_arm64`** [PYPI].

**Inference.** Infomap is not parameter-free (it has `markov_time`), but its default 1.0 has a stated meaning, and a one-module answer is a legitimate output. On our dense tag networks, where hub tags let flow escape every group, I expect one module or very few. That has to be checked in the Build (the Empirical check section). Intel Macs and macOS < 15 would need a source build, so it is Build-only in practice unless the bundle drops those targets.

### C.4 Bayesian or regularised SBM alternatives with pip wheels

**Established (package check).** I found no maintained, documented Python package with pip wheels for 3.12–3.14 that performs nonparametric SBM inference:
- `graspologic` 3.4.4 (SBM and DC-SBM estimators) requires Python < 3.13.
- `bayanpy` 0.7.7 does exact modularity maximisation, not inference, and requires the commercial `gurobipy`.
- `cdlib` 0.4.1 wraps many descriptive algorithms.
- `scikit-network` 0.33.5 has no cp314 wheels.

These are PyPI metadata only [PYPI]; I did not test any of them. The search was limited to obvious package names. The closest pip-installable regularised option is Infomap's `regularized` mode.

### C.5 Risk of finding Clusters in random networks, by method

| Method | What the primary source says about random input |
|---|---|
| Modularity (any γ) | High Q in random graphs [GSA04]. A few clusters "even in the limit of large ⟨k⟩" [LF09 §VII]. Overfits its own null [P23 §III, Fig. 6]. |
| Validated network (hypergeometric, Bonferroni) | Rewired bipartite data gave an **empty** Bonferroni network [T11, closing paragraph]. FDR admits a fraction q of false edges by design. |
| Significance | ER maximum ≈ n log n, usable as a reference [TKV13 Fig. 3b]. |
| Surprise | Over-estimates the number of communities; finds substructure from fluctuations [TAD15 §VI]. |
| Consensus (LF) | Can be cohesive on a random network [P23 §IV.B, Fig. 11]. |
| Hierarchical consensus (Jeub) | "Does not identify communities in random networks" [JSF18 Introduction]. |
| Nonparametric / nested SBM | No spurious modules even on sparse networks [P14]. A single group for a degree-constrained random graph [P23 Fig. 2]. |
| Infomap | One module on random graphs except at low ⟨k⟩ [LF09 §VII]. Overfits sparse, incomplete data unless regularised [SBER21]. |

---

## D. Threshold sensitivity: reporting practice

**Established**
- **VOSviewer** (van Eck & Waltman), manual for 1.6.20:
  - Term maps exclude terms "with a small number of occurrences (e.g., by default, terms with fewer than 10 occurrences are excluded)" and by default 40% of terms by relevance score [VOS p. 37].
  - Command line: `min_n_occurrences` [VOS §5].
  - On the clustering resolution: "We recommend to try out different values for the Resolution parameter and to use the value that yields the most appropriate level of detail for one's purposes". A "Min. cluster size" can merge or discard small clusters [VOS pp. 23–24].
  - Association-strength normalisation is the default, "identical to Eq. (6) in Van Eck and Waltman (2009)" up to a constant [VOS p. 22].
  
  The manual gives no statistical rationale for the occurrence threshold.
- **Multiverse analysis** (Steegen, Tuerlinckx, Gelman & Vanpaemel 2016):
  - When processing choices are "arbitrary", perform the analysis "across the whole set of alternatively processed data sets corresponding to a large set of reasonable scenarios" (abstract, p. 702).
  - Show the results as a histogram over the multiverse and a **grid of results per choice combination** (Figs. 1–2).
  - The selection of options is "highly context-specific and inherently subjective" (Discussion).
  - It is a transparency tool, "not a formal test" (Discussion).
- Saracco et al.: "an a priori selection of the number of validated links is not necessarily compatible with the existence of a level t of statistical significance" [S17 §II.C]. In other words, picking a density is not the same as picking α.
- Neal's `backbone` package can emit a "suggested manuscript text and citations" (`narrative = TRUE`) stating the model, α and correction [N22]. That is a usable template for wording.

**Recommendation (reporting).** Whatever pipeline is chosen, report a small multiverse.
- Axes: α ∈ {0.01, 0.05} × {BH, Bonferroni} (or, if the hard thresholds stay, `min_games_per_tag` × `min_shared_games` on a grid such as {3, 5, 8, 12} × {2, 3, 5, 8}), by Clustering Weight, by γ (or by the stable-partition procedure).
- Per cell: number of tags, edges and density, number of Multi-Tag Clusters and One-Tag Clusters, ARI to the primary partition, and the Seed-Noise Floor.
- Name one cell "primary" before looking at the results and say why. Present the grid as a sensitivity display, never as a search for the best cell.

---

## E. Package availability (checked 2026-10-22 on PyPI and in official docs)

| Package | Version (date) | Wheels for Windows? | Python 3.12–3.14? | Weighted edges? | Use under ADR 0001 |
|---|---|---|---|---|---|
| scipy | 1.18.1 | yes | yes (cp312–cp315) | n/a (tests) | app and Build (already a dependency) |
| leidenalg | 0.12.0 (2026-05-24) | yes (`cp38-abi3`, win32, win_amd64) | yes (abi3) | RBConfiguration, CPM, Surprise yes; **Significance no** | app and Build (already used) |
| igraph | 1.0.0 | yes (abi3, incl. win_arm64) | yes | yes | app and Build |
| modularitypruning | 2.0.1 (2026-10-20) | pure Python | yes (≥3.10) | yes ("extension beyond the original publication") | Build; app possible but pulls matplotlib and seaborn |
| champ | 2.1.1 (2020) | pure Python, but depends on `louvain` 0.8.2 (wheels only up to cp311) | **no** | yes | not usable; use modularitypruning's CHAMP |
| infomap | 2.15.1 (2026-08-04) | yes (win32, win_amd64) | yes (cp311–cp314) | yes | Build; app only if Intel and older macOS are dropped (only macosx_15_0_arm64) |
| PyGenStability | 0.2.7 (2026-03-09) | **no** (cp38 Linux/macOS only, no sdist) | **no** | yes | neither (source build on Linux only) |
| graph-tool | 3.9 per homepage; PyPI entries have 0 files | **no** (WSL or Docker) | conda-forge Linux/macOS | yes (edge covariates) | Build only, via WSL or Docker |
| bicm | 3.4.0 (2025-05-23) | pure Python + numba (win_amd64 cp312–cp314) | yes | n/a (binary bipartite) | Build (or app) |
| backbone-network | 1.1.3 (2022) | pure Python | yes | yes (disparity) | possible, not recommended |
| netbone | 0.2.3 (2024) | **sdist only**, no declared dependencies | unknown | yes | not recommended |
| Coscia `backboning` | not on PyPI | — | — | yes | reimplement if needed |
| graspologic | 3.4.4 | pure Python | **no** (< 3.13) | yes | not usable |
| bayanpy | 0.7.7 | pure Python, needs `gurobipy` (commercial) | — | yes | not usable |
| Jeub HierarchicalConsensus | MATLAB only | — | — | — | not usable |

---

## F. Other observations

- **The working-tree config differs from the description in the request.** `config/network.toml` says `clustering_weight = "shared_games"` and `algorithm = "louvain"`, whereas the request describes lift and Leiden. The paper's Network State must state which was used. Everything above applies to both, but Newman's γ has a generative reading only for the integer shared-game count (B.1 (d)).
- **The two-sided Fisher test in `features.py`** cannot be reused as an edge filter as it stands. It needs `alternative="greater"` (A.2).
- **Appendix C cites [VEW09] eq. (5) for association strength.** The VOSviewer manual refers to "Eq. (6) in Van Eck and Waltman (2009)" [VOS p. 22]. The difference is probably preprint vs journal numbering. Worth one check before publication.
- **Wording for q_excess:** "the Tag Network differs from networks with the same tag frequencies and tags per game", not "the Clusters are real" [P23 §IV.C].

---

## G. Decision table

Costs are my estimates for 30–95 nodes and n ≈ 100 games on this machine. None was measured.

| Method | What it chooses from data | Parameters left | Weighted support | pip / Windows (3.12–3.14) | Fit for n = 100 dense tag networks | Cost |
|---|---|---|---|---|---|---|
| Fixed thresholds + γ = 1 (current) | nothing | 3 (both thresholds, γ) | yes | yes | descriptive only; hard to defend | negligible |
| **Hypergeometric / FRM validated edges** [T11, NDS21] | edge set, implied tag and shared floors | α, FWER vs FDR | test on counts; cluster on lift or binary | yes (SciPy) | good; exact test; prunes hubs; low power for rare tags | negligible |
| FDSM via curveball [NDS21] | edge set (exact bipartite null) | α, R samples | as above | yes (project code) | best null; Build only | minutes to hours (R ≈ 10⁵) |
| SDSM / BiCM [NDS21, S17] | edge set | α (0.13 ≈ FDSM 0.05) | as above | yes (`bicm`) | good approximation | seconds |
| Disparity filter [SBV09] | edge set per node | α | yes | yes | weak (projection-blind) | negligible |
| Noise-corrected [CN17] | edge set | δ | yes | reimplement | weak (strength-based lift) | negligible |
| Newman iterative γ [N16] | γ (given the partition family) | start γ, tolerance | formula yes; likelihood only for integer multigraph | yes (modularitypruning) | heuristic; may not converge | seconds |
| **CHAMP + stable partitions** [W17, GM22] | admissible partitions, their γ domains, self-consistent γ | γ range, number of runs | yes (extension) | yes (modularitypruning) | good; can return none | seconds to a minute |
| leidenalg `resolution_profile` [LA-REF, TKV13] | all change points of the optimal partition in γ | γ range, stopping tolerances | yes (rescale the tolerance for lift) | yes | good as CHAMP input | seconds |
| Significance [TKV13] | partition and number of groups, no γ | none | **unweighted only** | yes (leidenalg) | only on an unweighted validated backbone; ER null | seconds |
| Surprise [TAD15] | partition and number of groups, no γ | none | positive weights (uniform-weight assumption) | yes (leidenalg) | over-splits; ER null | seconds |
| Markov stability (PyGenStability) [A24] | robust scales (NVI) | scale range, n_tries, kernel and window sizes | yes | **no** | criterion reproducible with leidenalg | minutes |
| Hierarchical consensus [JSF18] | consensus hierarchy | α, ensemble size | yes | **no** (MATLAB) | — | — |
| LF consensus [LF12] | consensus partition | τ, n_P | yes | hand-written | reduces seed noise only | seconds |
| **Nonparametric / nested / bipartite SBM** [P14, P17, P18, LCJ14, YL20] | number of groups and partition (MDL / posterior) | model variant, MCMC effort | yes (covariates) | **no** (graph-tool: WSL or Docker) | principled; may find 1 group at this n | minutes |
| Infomap [RB08] | number of modules (codelength) | `markov_time` (1 by default), `regularized` | yes | yes (except Intel macOS) | likely 1 module on dense hubs (to check) | seconds |

---

## H. Ranked recommendation

### 1. Validated Tag Network, then Leiden with γ from stable-partition pruning (primary)

Steps:
1. For each Top-100 Dataset (after the Minimum Months Filter, with n its number of games) and every pair of visible tags, compute the one-sided hypergeometric p = P(X ≥ s | n, c_a, c_b).
2. Apply Tarone's testability rule (A.7).
3. Keep the pairs with BH q ≤ α as edges.
4. Tags without a retained edge are One-Tag Clusters.
5. As a Build check, compare the backbone with FDSM p-values from the curveball sampler (Jaccard of edge sets) and report the distribution of tags per game, which is the condition from [NDS21 Study 3].
6. Run Leiden (RBConfiguration) with lift as the Clustering Weight on the retained edges, many seeds × a γ grid (or a `resolution_profile`).
7. Apply `prune_to_stable_partitions` over γ ∈ [0, γ_max].
8. Report every stable partition with its γ domain, or report that none exists.

Methods-section wording (suggested):
> "Two tags were linked when they shared more games than expected if each tag were assigned to games independently of the others. For each pair we computed a one-sided hypergeometric p-value given the number of games n and the two tags' frequencies (the statistically validated network of Tumminello et al., 2011; equivalently the fixed-row model of Neal et al., 2021). Pairs whose minimum attainable p-value could not reach the corrected level were excluded from the correction (Tarone, 1990), and we retained pairs with a Benjamini–Hochberg false discovery rate of at most α. Minimum tag and co-occurrence frequencies therefore follow from n, α and the tag frequencies rather than being fixed in advance. Clusters were obtained by Leiden optimisation of the Reichardt–Bornholdt modularity on lift-weighted retained edges. The resolution was chosen as in Gibson and Mucha (2022): among all partitions found over a range of resolutions, we kept those whose resolution estimate under the degree-corrected planted-partition model (Newman, 2016, eq. 15) falls within the range of resolutions over which the partition is optimal (CHAMP; Weir et al., 2017)."

Still for a human to decide:
- α (0.05 or 0.01), and FDR (BH, or BY under arbitrary dependence) vs Bonferroni.
- Whether near-universal tags dropping out is acceptable, and how to present them.
- Lift vs binary edges for clustering.
- The γ range.
- What to report if no stable partition exists, or if several do.
- Whether the Newman estimate's planted-partition reading is claimed or only used as a selection device. Say the latter, given [ZP20] and [P23 §IV.A].

### 2. Inferential cross-check: nonparametric SBM on the bipartite game–tag matrix (Build only, WSL or Docker)

Steps:
1. Fit a degree-corrected nonparametric SBM to each dataset's game–tag incidence matrix, with games and tags restricted to separate groups.
2. Compare it, by description length, with the trivial model (one tag group).
3. Report the inferred number of tag groups and the ARI against the Pipeline 1 Clusters.

Methods-section wording (suggested):
> "As a check that does not depend on thresholds or a resolution parameter, we fitted a nonparametric degree-corrected stochastic block model to the bipartite game–tag matrix (Peixoto, 2017; Larremore et al., 2014), which selects the number of groups by minimum description length and does not find groups in networks without latent structure (Peixoto, 2014, 2023). We report the number of tag groups it infers and their agreement with the modularity Clusters."

Still for a human to decide:
- Primary or check only.
- Nested vs flat, given that Yen & Larremore find flat models better for small, sparse networks.
- MCMC effort and number of restarts.
- How to report a one-group result. Recommendation: as a finding that the data do not support more than one group at this n, not as a failure.

### 3. Multiverse grid with a plateau criterion for γ (supplement in any case; primary only if the thresholds are kept)

Steps:
1. Run the analysis over a pre-declared grid of thresholds (or of α levels for Pipeline 1) × Clustering Weight.
2. At each cell, scan γ densely with `resolution_profile`.
3. Pick γ at plateaus where the Seed-Noise Floor is low and partitions persist across neighbouring γ (the PyGenStability criterion [A24 §2.3], reproduced with leidenalg via the γ = 1/t link [LDB14 eq. (9)]).
4. Present the grid (Steegen et al., Fig. 2 style).

Methods-section wording (suggested):
> "Because minimum frequencies and the resolution involve choices with no unique justification, we report a multiverse analysis (Steegen et al., 2016) over [grid]. Within each setting the resolution was taken from plateaus over which partitions were both reproducible across random seeds and persistent across neighbouring resolutions, the criterion used for Markov stability scale selection (Arnaudon et al., 2024; Lambiotte et al., 2014)."

Still for a human to decide:
- The grid's ranges.
- The primary cell (declared before the results are seen).
- The plateau rule's thresholds.

---

## Empirical check on this Build

_To be filled in by the main session with results on Build 20261008T221504Z-7a23ae9f._

---

## Sources

Locators: section, equation, figure or table as read in the arXiv or author version. Bibliographic metadata (journal, DOI) for arXiv papers comes from the arXiv API's journal-ref and DOI fields (author-supplied), checked 2026-10-22, unless marked otherwise.

**Read in full text for this note**
- [N16] Newman, M. E. J. (2016). Equivalence between modularity optimization and maximum likelihood methods for community detection (arXiv title: "Community detection in networks: Modularity optimization and maximum likelihood are equivalent"). *Phys. Rev. E* 94, 052315. doi:10.1103/PhysRevE.94.052315. arXiv:1606.02319 (§II.A eq. (6); §III eqs. (12)–(15); §III.A eqs. (16)–(18), Fig. 1, Table I; §IV)
- [ZP20] Zhang, L., Peixoto, T. P. (2020). Statistical inference of assortative community structures. *Phys. Rev. Research* 2, 043271. doi:10.1103/PhysRevResearch.2.043271. arXiv:2006.14493 (abstract; §II.A points 1–2)
- [P23] Peixoto, T. P. (2023). Descriptive vs. inferential community detection in networks: pitfalls, myths and half-truths. *Elements in the Structure and Dynamics of Complex Networks*, Cambridge University Press. doi:10.1017/9781009118897. arXiv:2112.00183v7 (§II.A–B, II.D, II.F; §III, Figs. 6–8; §IV.A–D, IV.H; Figs. 11–13; footnote 20)
- [P14] Peixoto, T. P. (2014). Hierarchical block structures and high-resolution model selection in large networks. *Phys. Rev. X* 4, 011047. doi:10.1103/PhysRevX.4.011047. arXiv:1310.4377 (abstract)
- [P17] Peixoto, T. P. (2017). Nonparametric Bayesian inference of the microcanonical stochastic block model. *Phys. Rev. E* 95, 012317. doi:10.1103/PhysRevE.95.012317. arXiv:1610.02703 (abstract; §II MDL penalty)
- [P18] Peixoto, T. P. (2018). Nonparametric weighted stochastic block models. *Phys. Rev. E* 97, 012306. doi:10.1103/PhysRevE.97.012306. arXiv:1708.01432 (abstract; §II; §IV.A–E)
- [LCJ14] Larremore, D. B., Clauset, A., Jacobs, A. Z. (2014). Efficiently inferring community structure in bipartite networks. *Phys. Rev. E* 90, 012805. doi:10.1103/PhysRevE.90.012805. arXiv:1403.2933 (abstract; §I)
- [YL20] Yen, T.-C., Larremore, D. B. (2020). Community detection in bipartite networks with stochastic block models. *Phys. Rev. E* 102, 032309. doi:10.1103/PhysRevE.102.032309. arXiv:2001.11818 (abstract)
- [T11] Tumminello, M., Miccichè, S., Lillo, F., Piilo, J., Mantegna, R. N. (2011). Statistically validated networks in bipartite complex systems. *PLoS ONE* 6(3), e17994. doi:10.1371/journal.pone.0017994. arXiv:1008.1414 (eq. (1) and p-value; Bonferroni and FDR networks; Table I; closing paragraph on rewired data)
- [SBV09] Serrano, M. Á., Boguñá, M., Vespignani, A. (2009). Extracting the multiscale backbone of complex weighted networks. *PNAS* 106, 6483–6488. doi:10.1073/pnas.0808904106. arXiv:0904.2389 (eqs. [1]–[2]; Fig. 1 text)
- [CN17] Coscia, M., Neffke, F. M. H. (2017). Network backboning with noisy data. *Proc. IEEE ICDE 2017*. arXiv:1701.07336 (§III.B; §IV eq. (1), δ values). Proceedings pages and DOI not verified.
- [NDS21] Neal, Z. P., Domagalski, R., Sagan, B. (2021). Comparing alternatives to the fixed degree sequence model for extracting the backbone of bipartite projections. *Sci. Rep.* 11, 23929. doi:10.1038/s41598-021-03238-3. arXiv:2105.13396 (Introduction; model definitions; Study 3 results and Figs. 3–4; Discussion recommendations)
- [N22] Neal, Z. P. (2022). backbone: An R package to extract network backbones. *PLoS ONE* 17(5), e0269137. doi:10.1371/journal.pone.0269137. arXiv:2203.11055 (bipartite projections section, toy example; multiple-test correction section)
- [S17] Saracco, F., Straka, M. J., Di Clemente, R., Gabrielli, A., Caldarelli, G., Squartini, T. (2017). Inferring monopartite projections of bipartite networks: an entropy-based approach. *New J. Phys.* 19, 053022. doi:10.1088/1367-2630/aa6b38. arXiv:1607.02481 (§II.B–C)
- [LL15] Llinares-López, F., Sugiyama, M., Papaxanthos, L., Borgwardt, K. (2015). Fast and memory-efficient significant pattern mining via permutation testing. *Proc. KDD 2015*. arXiv:1502.04315 (§3 minimum attainable p-value and testable set; §5 description of Tarone 1990). Proceedings DOI not verified.
- [W17] Weir, W. H., Emmons, S., Gibson, R., Taylor, D., Mucha, P. J. (2017). Post-processing partitions to identify domains of modularity optimization. *Algorithms* 10(3), 93. doi:10.3390/a10030093. arXiv:1706.03675 (abstract; §2; Discussion)
- [GM22] Gibson, R. A., Mucha, P. J. (2022). Finite-state parameter space maps for pruning partitions in modularity-based community detection. *Sci. Rep.* doi:10.1038/s41598-022-20142-6 (PMC9508178; Methods eqs. 4–5; Fig. 1(d) caption; karate club section; Discussion). Volume and article number not verified.
- [TKV13] Traag, V. A., Krings, G., Van Dooren, P. (2013). Significant scales in community structure. *Sci. Rep.* 3, 2930. doi:10.1038/srep02930. arXiv:1306.3398 (§II.A Theorems 1–2, eq. (4); §II.B eq. (8), §II.B.2; Fig. 3)
- [TAD15] Traag, V. A., Aldecoa, R., Delvenne, J.-C. (2015). Detecting communities using asymptotical surprise. *Phys. Rev. E* 92, 022816. doi:10.1103/PhysRevE.92.022816. arXiv:1503.00445 (abstract; §II weighted extension; §III; §VI)
- [DYB10] Delvenne, J.-C., Yaliraki, S. N., Barahona, M. (2010). Stability of graph communities across time scales. *PNAS* 107(29), 12755–12760. arXiv:0812.1811 (eq. (5) and the text after it). Journal pages and DOI not verified (the arXiv record has no journal-ref).
- [LDB14] Lambiotte, R., Delvenne, J.-C., Barahona, M. (2014). Random walks, Markov processes and the multiscale modular organization of complex networks. *IEEE Trans. Netw. Sci. Eng.* 1(2), 76–90. doi:10.1109/TNSE.2015.2391998. arXiv:0812.1770 (eq. (9) and text; "Time as a resolution parameter")
- [A24] Arnaudon, A., Schindler, D. J., Peach, R. L., Gosztolai, A., Hodges, M., Schaub, M. T., Barahona, M. (2024). PyGenStability: multiscale community detection with generalized Markov stability. *ACM Trans. Math. Softw.* doi:10.1145/3651225 (DOI from the arXiv record; journal volume not verified). arXiv:2303.05385v3 (§2.2–2.4)
- [JSF18] Jeub, L. G. S., Sporns, O., Fortunato, S. (2018). Multiresolution consensus clustering in networks. *Sci. Rep.* 8, 3259. arXiv:1710.02249 (Introduction; Fig. 8; Methods). DOI not verified.
- [LF12] Lancichinetti, A., Fortunato, S. (2012). Consensus clustering in complex networks. *Sci. Rep.* 2, 336. arXiv:1203.6093 (Methods procedure; Appendix A)
- [LF09] Lancichinetti, A., Fortunato, S. (2009). Community detection algorithms: a comparative analysis. *Phys. Rev. E* 80, 056117. doi:10.1103/PhysRevE.80.056117. arXiv:0908.1062 (§VII, Fig. 8)
- [RB08] Rosvall, M., Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. *PNAS* 105, 1118–1123. doi:10.1073/pnas.0706851105. arXiv:0707.0609 (abstract)
- [KR15] Kawamoto, T., Rosvall, M. (2015). Estimating the resolution limit of the map equation in community detection. *Phys. Rev. E* 91, 012809. doi:10.1103/PhysRevE.91.012809. arXiv:1402.4385 (abstract)
- [SBER21] Smiljanić, J., Blöcker, C., Edler, D., Rosvall, M. (2021). Mapping flows on weighted and directed networks with incomplete observations. *J. Complex Netw.* 9, cnab044. doi:10.1093/comnet/cnab044. arXiv:2106.14798 (abstract; "Regularized network flows")
- [SVGV16] Steegen, S., Tuerlinckx, F., Gelman, A., Vanpaemel, W. (2016). Increasing transparency through a multiverse analysis. *Perspect. Psychol. Sci.* 11(5), 702–712. doi:10.1177/1745691616658637 (abstract p. 702; definition p. 703; Figs. 1–2; Discussion)
- [VOS] van Eck, N. J., Waltman, L. (2023). *VOSviewer Manual*, for VOSviewer 1.6.20 (31 October 2023). https://www.vosviewer.com/documentation/Manual_VOSviewer_1.6.20.pdf (pp. 22–24 normalisation and clustering; p. 37 term selection; §5 command-line `min_n_occurrences`)

**Cited through another source (not read)**
- [N14] Neal, Z. P. (2014). The backbone of bipartite projections. *Soc. Networks* 39, 84–97. doi:10.1016/j.socnet.2014.06.001 (as cited in [NDS21] ref. 18)
- [TAR90] Tarone, R. E. (1990). A modified Bonferroni method for discrete data. *Biometrics* 46(2), 515–522 (as described and cited in [LL15] §5, ref. 24)
- [PHLP19] Pamfil, A. R., Howison, S. D., Lambiotte, R., Porter, M. A. (2019). Relating modularity maximization and stochastic block models in multilayer networks. *SIAM J. Math. Data Sci.* doi:10.1137/18M1231304 (DOI as given in the [MP-SRC] docstring)
- [SCB23] Schindler, J., Clarke, J., Barahona, M. (2023). Multiscale mobility patterns and the restriction of human movement. *R. Soc. Open Sci.* 10, 230405 (scale-selection algorithm, as cited in [A24] ref. 18)

**Already in the project's references (Appendix C or research 05 and 30)**
- [GSA04] Guimerà, Sales-Pardo & Amaral 2004; [FB07] Fortunato & Barthélemy 2007; [GMC10] Good, de Montjoye & Clauset 2010; [BH95] Benjamini & Hochberg 1995; [BY01] Benjamini & Yekutieli 2001 (Thms 1.2, 1.3); [STR14] Strona et al. 2014; [PS10] Phipson & Smyth 2010; [LZ20] Li & Zhang 2020; [VEW09] van Eck & Waltman 2009.

**Software documentation and source code**
- [LA-REF] leidenalg reference (stable docs): `Optimiser.resolution_profile`, `RBConfigurationVertexPartition`, `CPMVertexPartition`, `SignificanceVertexPartition`, `SurpriseVertexPartition`. https://leidenalg.readthedocs.io/en/stable/reference.html
- [LA-SRC] leidenalg source, `src/leidenalg/Optimiser.py` (`resolution_profile`) and `VertexPartition.py` (`bisect_value`). https://github.com/vtraag/leidenalg
- [MP-SRC] modularitypruning 2.0.1, README and source (`parameter_estimation_utilities.py`: `estimate_singlelayer_SBM_parameters`, `gamma_estimate_from_parameters`, `prune_to_stable_partitions`; `parameter_estimation.py`). https://github.com/ragibson/ModularityPruning
- [IM-OPT] Infomap Python docs 2.15.1, options. https://mapequation.org/infomap-python-docs/api/options.html
- [BICM] bicm README (`compute_projection`, citation list). https://github.com/mat701/BiCM
- [GT-INST] graph-tool installation instructions. https://graph-tool.skewed.de/installation.html ; homepage https://graph-tool.skewed.de/ (newest version 3.9)
- [PYPI] PyPI JSON API (`https://pypi.org/pypi/<name>/json`) for leidenalg, igraph, infomap, PyGenStability, champ, louvain, modularitypruning, bicm, numba, backbone-network, netbone, graph-tool, graspologic, bayanpy, cdlib, scikit-network, scipy, networkx, h5py, psutil, seaborn, matplotlib and scikit-learn, queried 2026-10-22.

Citation caveat:
- Every source in the first group was read in its arXiv or author version, or as official docs or source, at the cited locator. Page numbers are not given for arXiv texts, so cite section, equation or figure numbers, which carry over to the published versions.
- Not verified:
  - the journal DOIs or pages of [CN17], [DYB10], [JSF18] and [LL15];
  - the volume and article number of [GM22] and [A24];
  - [N14], [TAR90], [PHLP19] and [SCB23] (not read).
- The Section A.7 tables and the B.1, B.3 and B.5 algebra are my own and are labelled as such.
