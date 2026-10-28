# Inter-cluster measures
Type: grilling
Status: resolved
Blocked by: 05

## Question

Exactly what does feature 3 compute for each pair of Clusters? Uses `grilling` + `domain-modeling` and works from [Normalised inter-cluster strength in the literature](05-normalised-inter-cluster-strength.md).

- The normalisation, or normalisations, and which one is the headline "connection strength". Its name in CONTEXT.md and the words to avoid.
- Weights: the shared-game total always, plus the Lift total and its normalised strength under Lift (settled while charting). Is strength computed on both?
- One-Tag Clusters: keep the existing `one_tag_pool`, show each One-Tag Cluster on its own, or leave them out.
- The per-cluster view ("how strongly C3 connects to every other cluster"): its ordering, shares of the cluster's external weight, and whether zero-edge pairs are listed.
- New `cluster_connections.csv` columns (additive, `schema.py`, guide index, column appendix), and whether any number is read against a baseline or band.
- The guide entries: metric reference text and a caution about what strength does not mean.

## Answer

Settled with the researcher on 2026-10-28, who accepted every recommendation in three grilling rounds. **Connection Ratio** and **Connection Share** are now in [CONTEXT.md](../../../CONTEXT.md); the choice of measure is [ADR 0004](../../../docs/adr/0004-connection-ratio-is-the-configuration-model-ratio.md). Evidence: [research 05](../research/05-normalised-inter-cluster-strength.md).

- **Headline: the Connection Ratio**, r_ab = w_ab / (k_a·k_b / 2m), in the Clustering Weight. k_a is the Cluster's strength (2·`internal_weight` + `cut_weight`), 2m = 2·`total_weight`. 1 = the weight the two strengths alone predict; the ceiling is γ (the merge test Louvain and Leiden already pass), so a value near γ marks a pair that almost merged. No new graph pass: sums over existing per-tag values.
- **Not used**: density (inflated for two-tag Clusters), pairwise Ncut and the modularity difference ΔQ_ab (add nothing over the ratio and shares), game-set Jaccard and cluster Lift (saturated on these data), PAGA (binarised and capped).
- **One-Tag Clusters**: the existing `one_tag_pool` grouping stays. k_p is the sum of member strengths. The pool–pool expectation is over distinct pairs, E_pp = (k_p² − Σ_i k_i²)/4m, so the γ ceiling holds on pool rows too.
- **Both totals, always**: a new shared-game total is always filled (equal to `weight` under shared games; the second total under Lift), with a **shared-game ratio** from shared-game sums and `strength_shared`. Under Lift it is labelled as not tied to the clustering: it can exceed γ.
- **Connection Share**: w_ab / cut_a, directional, so two values per pair; a Cluster's shares sum to 1. In the Clustering Weight only, with no shared-game twin.
- **Reading**: on screen the ratio is a plain number with γ beside it and the two reference points (1 and γ) in the text. No colour bands, labels or thresholds. The guide gives r/γ as the way to compare across resolutions; it is not a column.
- **Per-cluster view** (content and order only; the look is [Cluster connections view](07-cluster-connections-view.md)): one row per partner, sorted by Connection Ratio high to low, ties by raw weight. Zero-edge partners listed at 0, at the bottom. The `one_tag_pool` row is ranked like any other, labelled as the pool. Columns: Connection Ratio, Connection Share, total in the Clustering Weight, edge count; under Lift also the shared-game total and shared-game ratio.
- **`cluster_connections.csv`**: the four existing columns are unchanged. Five new columns, in this order: `shared_weight`, `ratio`, `shared_ratio` (equals `ratio` under shared games), `share_of_a`, `share_of_b`. Each is declared in `schema.py` and indexed in `guide_index` and the guide's column appendix.
- **Edge values**: shown as computed, never clamped. A ratio a hair above γ (Louvain's 1e-7 gain tolerance) is shown as it is, and the guide says why. The cell is empty where a denominator is zero: a pool of isolated tags only (k_p = 0), a pool–pool row with fewer than two linked pool tags (E_pp = 0), or a Multi-Tag Cluster with no outside links (cut_a = 0, so its shares are empty). No status column; the guide lists the three cases.
- **Wording fix**: w_ab sums shared-game counts over tag pairs, so one game can count several times (3 tags in C1 and 2 in C2 add 6). The guide's example becomes "seven links whose shared-game counts sum to 58", with that caution. Wording only; no number changes.
- **Guide** (`03-metric-reference.md`): the **Cluster connections** entry keeps its anchor and gains the new columns and the reworded example. Two sub-entries, **Connection Ratio** and **Connection Share**, each with its own anchor for tooltips, in the standard In short / Higher → / Here / Caution layout, then Why it matters, Example, Bounds, Compare with, Exact definition. Both go in the column appendix. Agreed In short blocks:
  - Connection Ratio. *In short:* how much link weight joins two clusters, compared with what their total link weight alone would predict. *Higher →* more connected than their sizes explain; 1 = exactly as predicted; the most it can reach is the resolution γ, and a value near γ means the two almost became one cluster. *Here:* shows which groups of characteristics the most-played games combine more often than the clusters' sizes would suggest. *Caution:* values are low partly *because* the clustering separated these tags; they describe this split, not independent evidence that the groups are unrelated.
  - Its full entry also cautions: only links at or above the minimum shared games count; under Lift the shared-game ratio is not tied to the clustering and can exceed γ; across different γ, divide by γ; it is neither a similarity of the games nor a cause.
  - Connection Share. *In short:* of all the link weight leaving a cluster, the part that goes to one other cluster. *Higher →* more of this cluster's outside links go to that partner; a cluster's shares add up to 1. *Here:* shows where each group of characteristics' overlaps with the rest go. *Caution:* big clusters take large shares just by being big; use the Connection Ratio to judge strength.
- **Translation**: Connection Ratio and Connection Share need rows in [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md); they are added when the bulk translation's terms are checked, not decided here.
