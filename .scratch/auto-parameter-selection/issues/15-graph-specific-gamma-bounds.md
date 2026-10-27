# Graph-specific γ bounds
Type: research
Status: resolved
Blocked by: none

## Question

What graph-specific lower and upper bounds on the resolution γ does the literature justify for RB/configuration modularity on a **weighted** (Lift, or Shared games) single-layer network, so the scan range can be derived from each graph instead of the fixed 0.25–3.00?

- The researcher's decision ([Editable fixed settings](14-editable-fixed-settings.md)): the γ scan range is not a user setting. It is computed per graph from bounds that can be justified. 0.25–3.00 was a convention, matching the Workbench's γ input ([Resolution-selection rules](03-resolution-selection-rules.md)).
- **Upper end.** Is γ_max = max over edges of 2m·w_ij / (k_i·k_j), the γ at or above which the all-One-Tag-Cluster partition is optimal, stated and proved in a primary source (for example Jeub, Sporns & Fortunato 2018, "Multiresolution consensus clustering in networks")? Does it hold with weights and with isolated tags? How does it compare with Gibson & Mucha's γ_max(K) (Research 01 §J), which ticket 03 rejected?
- **Lower end.** The γ below which "one Cluster per connected component" is optimal has no closed form in general. What do the sources use: an exact bound, a heuristic estimate (Jeub et al.'s γ_min?), a spectral bound, or simply γ = 0 as in Weir et al. 2017 and `modularitypruning`? Which can be computed in numpy on 20–140 tags?
- **Spacing.** Do the sources sample γ linearly, logarithmically, or by an "event sampling" that is uniform in partition change (Jeub et al.)? What does `modularitypruning` or CHAMP's reference code do?
- **Range ends in CHAMP and Gibson & Mucha.** Do CHAMP's domains and the stable-partition test need a bounded range at all once the bounds are exact? How do the sources treat a γ̂ estimate outside the scanned range?
- **Measured on this Build** (`20261008T221504Z-7a23ae9f`, Lift, hidden Genre Tags and defining tag, Minimum Months 0): each bound's value over the 765 pairs' graphs (distribution, extremes, how often each falls outside 0.25–3.00), and for Shared games on a sample.

## Answer

Researched 2026-10-26. Findings, proofs and measurements are in [research/15-graph-specific-gamma-bounds.md](../research/15-graph-specific-gamma-bounds.md); scripts are in [prototypes/15-gamma-bounds/](../prototypes/15-gamma-bounds/).

- **Upper end.** Jeub, Sporns & Fortunato (2018, Eq. 3) define γ_max as the smallest γ at which all One-Tag Clusters is optimal. They state, without proof, that it is the smallest γ with A_ij ≤ γP_ij everywhere, and their `gammaRange.m` computes max over edges of 2m·w_ij/(k_i k_j). The two-line proof holds for any weights ≥ 0 and any isolated tags.
  - On this Build γ_max is set by one rare tag pair: 2.6–204 on Lift (median 15), above 3.00 on 758 of 765 graphs.
- **A tighter provable end for stability (Inference, no source): γ_pos**, the root of Σ_edges 2·max(B_ij, 0) − γΣk²/2m. No partition has Q > 0 above it, every ω_in and γ̂ lies below it, so no Stable Partition can lie above it.
  - On Lift it is 1.38–13.5 (median 3.12), above 3.00 on 412 graphs.
  - Gibson & Mucha's γ_max(K) needs equal-sized groups and a K_max, and is 3.8–17.7 here.
- **Lower end.** The γ below which one Cluster per component is optimal equals a minimum normalised cut (Shi & Malik 2000), scaled by 2m/vol. It is NP-hard in general, so the sources compute it numerically (Jeub et al.'s iteration) or start at 0 (Weir et al., Gibson & Mucha, `modularitypruning`).
  - In numpy it is bracketed by (2m/vol)·λ₂ below and the Fiedler sweep cut or Jeub's iteration above.
  - On Lift: 0.017–0.835, median ≈ 0.5. It is below 0.25 on 29 graphs. Jeub's iteration hit the exact value on all 44 graphs small enough to enumerate.
- **Spacing.** Every CHAMP and Gibson & Mucha example is linear. Jeub et al. offer linear, log and event sampling, and recommend event sampling.
- **Range ends.** `CHAMP_2D` needs a box. CHAMP's own code stops at Q = 0, which loses no Stable Partition. With the trivial and all-One-Tag-Cluster partitions added to the input, CHAMP on [0, ∞) needs no clipping.
- **Effect on this Build.** Scanning from below γ_min to γ_pos keeps 761 of 765 Selected Partitions and changes 3 (puzzle 4/4 to a low-γ partition, two g = 3 pairs). Leiden with `n_iterations=-1` never stopped on one graph at several γ between 6.2 and 6.7.
- **12 choices are left open** for [Graph-specific γ scan](16-graph-specific-gamma-scan.md) (research §6).
