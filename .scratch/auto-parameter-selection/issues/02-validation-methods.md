# Validation methods (curveball, Hennig, Karrer)
Type: research
Status: resolved
Blocked by: none

## Question

What do the primary sources say about the three validation pieces, so that [Validation design](07-validation-design.md) can decide them?

- **Curveball** (Strona et al. 2014; Carstens 2015 for uniformity): how many trades give a well-mixed sample of 0/1 matrices with fixed row and column sums, at our size (≤100 games × ~200–450 tags, ≤20 tags per game)? The app uses 10 trades per game today (`TRADES_PER_GAME` in `network/stability.py`); is that enough, and what is the citable rule?
- **Hennig (2007)**: the cluster-wise Jaccard stability (per original cluster, the mean over resamples of the best-matching cluster's Jaccard). Its resampling schemes (bootstrap, subsetting, jittering, replacing points by noise), how subsetting is defined, and the interpretation thresholds (≤0.5 dissolved, 0.6–0.75 patterns, ≥0.75/0.85 stable). How should points not present in a subsample be handled? Here the "points" are tags, and the subsample removes games, so some tags drop below threshold.
- **Karrer, Levina & Newman (2008)**: their perturbation scheme for the robustness of community structure (the variation of information against a perturbation parameter, compared with a null), and what part of it supports, or differs from, the brief's 80% game subsampling and the curveball null.
- **Comparing observed structure with a null**: what a defensible "consistent clustering procedure" on a null network looks like (the same full selection procedure vs a fixed γ), and which summary statistics the literature compares (Q, number of groups, existence of a stable partition). Bear in mind Peixoto (2023, cited in Research 31): a null test of Q only shows that the network is not random.
- **Proportional threshold scaling under subsampling**: any precedent for scaling minimum-frequency thresholds with sample size (round, floor or ceil of 0.8·g), and how to report pairs that become degenerate.

Cite section, equation or figure for each fact; mark inferences as inferences.

## Answer

Findings: [research/02-validation-methods.md](../research/02-validation-methods.md). Section F collects the open choices for ticket 07.

- **Curveball.** Keep `TRADES_PER_GAME = 10`. No usable mixing-time bound exists. Carstens 2015 proves uniform convergence. Carstens & Kleer prove only that curveball mixes rapidly whenever the switch chain does. The citable rule is Strona et al.'s plateau criterion: about the largest matrix dimension on average, and "1000 pair extractions … rather conservative" (Suppl. Note 2; Fig. 3b: < 2 per row). 10 per game is 1,000 trades, about 6 times that average. On this Build (5 cases, 100 chains, 200-per-game reference), every tracked statistic was within noise by 10 trades per game and within about 0.8 SD by 5. The sampler counts no-op draws as trades, as the uniformity proof requires (abstract-level check).
- **Hennig.** The mean over resamples of the best-match Jaccard, computed on points present in both data sets (§2).
  - Schemes: bootstrap, subsetting with m = [n/2], noise replacement, and jittering (not recommended alone).
  - Thresholds: ≤ 0.5 = dissolved has a theoretical basis. The 0.6 / 0.75 / 0.85 bands are fpc's and "refer to bootstrap".
  - Missing tags: compare on the tags present in both, and report each Multi-Tag Cluster's retained share alongside. Leave One-Tag Clusters out ("perfectly stable, though totally meaningless").
  - fpc scores a wholly absent cluster 0 over all B. The preprint averages over the resamples where the cluster is present.
- **Karrer, Levina & Newman.** They back the principle: robustness to small changes, compared with a null put through the identical analysis, with isolated nodes kept as singletons. They do not back the mechanics. Their method is edge rewiring at fixed nodes, a VI curve over α, and robustness of configuration-model graphs as the null. They call the Q z-score unreliable and ask for cluster-level measures, which Hennig's provides.
- **Null comparison.** A consistent null re-runs the whole optimisation (KLN §I; Peixoto §III: a deviation ignoring "the optimization step" overfits). Here that means the full γ scan + CHAMP + Stable Partition rule per null replicate. Compare existence of a qualifying Stable Partition, Optimality Domain width and number of Multi-Tag Clusters (weak per Peixoto Fig. 8). Q is comparable only at a common γ, so add fixed-γ Q as a second arm. Either way the comparison only says the network is not random (Peixoto §IV.C).
- **Threshold scaling.** One precedent: Toivonen 1996 treats the threshold as a fraction and lowers it in samples to avoid misses (§4, Thm 3). I found none in network analysis. With 80 of 100 games every rounding rule makes borderline tags' survival swing with g mod 5; floor keeps the most. Recommended: floor in integer arithmetic, s′ ≥ 2, and degenerate subsamples reported as "k of S", never dropped.
