# Validation methods (curveball, Hennig, Karrer)
Type: research
Status: open
Blocked by: none

## Question

What do the primary sources say about the three validation pieces, so that [Validation design](07-validation-design.md) can decide them?

- **Curveball** (Strona et al. 2014; Carstens 2015 for uniformity): how many trades give a well-mixed sample of 0/1 matrices with fixed row and column sums, at our size (≤100 games × ~200–450 tags, ≤20 tags per game)? The app uses 10 trades per game today (`TRADES_PER_GAME` in `network/stability.py`); is that enough, and what is the citable rule?
- **Hennig (2007)**: the cluster-wise Jaccard stability (per original cluster, the mean over resamples of the best-matching cluster's Jaccard). Its resampling schemes (bootstrap, subsetting, jittering, replacing points by noise), how subsetting is defined, and the interpretation thresholds (≤0.5 dissolved, 0.6–0.75 patterns, ≥0.75/0.85 stable). How should points not present in a subsample be handled? Here the "points" are tags, and the subsample removes games, so some tags drop below threshold.
- **Karrer, Levina & Newman (2008)**: their perturbation scheme for the robustness of community structure (the variation of information against a perturbation parameter, compared with a null), and what part of it supports, or differs from, the brief's 80% game subsampling and the curveball null.
- **Comparing observed structure with a null**: what a defensible "consistent clustering procedure" on a null network looks like (the same full selection procedure vs a fixed γ), and which summary statistics the literature compares (Q, number of groups, existence of a stable partition). Bear in mind Peixoto (2023, cited in Research 31): a null test of Q only shows that the network is not random.
- **Proportional threshold scaling under subsampling**: any precedent for scaling minimum-frequency thresholds with sample size (round, floor or ceil of 0.8·g), and how to report pairs that become degenerate.

Cite section, equation or figure for each fact; mark inferences as inferences.
