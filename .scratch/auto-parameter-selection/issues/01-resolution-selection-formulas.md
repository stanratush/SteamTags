# Resolution-selection formulas (CHAMP, Newman, Gibson & Mucha)
Type: research
Status: resolved
Blocked by: none

## Question

What exactly do the primary sources define, so that our own numpy CHAMP and self-consistent γ estimate can be implemented correctly for a **weighted** (Lift) single-layer network?

- **CHAMP (Weir et al. 2017)**: the single-layer form. Each partition gives Q(γ) = A − γ·P; what are A and P exactly under RB/configuration modularity with weights (normalisation by 2m or not, self-loops)? How is the upper envelope (the admissible set and each partition's domain) computed over a bounded γ range, and how are ties, partitions that are never optimal, and the range ends handled?
- **Newman (2016)**: eq. (15) γ = (ω_in − ω_out)/(ln ω_in − ln ω_out), and eqs. (16)–(18) for ω_in and ω_out from a partition. What changes for weighted graphs (Newman's paper is unweighted)? Which cases leave the estimate undefined (ω_in ≤ ω_out, ω_out = 0, a single group, empty graph), and what do the sources say to do then?
- **Gibson & Mucha (2022)**: the definition of a stable partition (estimate inside its own CHAMP domain), whether the map γ → γ̂ is iterated or evaluated once per admissible partition, how One-Tag Clusters (isolated nodes, singletons) enter ω_in/ω_out, and what they recommend when several or no stable partitions exist.
- **`modularitypruning` 2.0.1**: which functions do this (`prune_to_stable_partitions`, `CHAMP_2D`, `gamma_estimate`, …), the exact formulas in its source code, how it treats weights ("an extension beyond the original publication"), and its defaults (`restrict_num_communities`, `single_threaded`). Can it run as a dev-only test oracle on our Lift graphs under Python 3.14 on Windows?
- Leiden's `resolution_profile` and deduplication: is bisection over γ a valid or better replacement for the fixed 80-value grid? (Research 31 B.3 notes that `min_diff_bisect_value` assumes integer weights.)

Write the formulas as they will be implemented, with section/equation references, and flag every point where the sources leave a choice open; [Resolution-selection rules](03-resolution-selection-rules.md) decides those.

## Answer

Findings: [research/01-resolution-selection-formulas.md](../research/01-resolution-selection-formulas.md).

- **CHAMP (Weir et al. 2017 §2, eqs. 2–4).** Each partition gives a line Q(γ) = Â − γP̂ with:
  - Â = 2·(internal Lift weight);
  - P̂ = Σ_c κ_c²/2m;
  - no 1/2m factor and no self-loops in our graph.

  `leidenalg` quality equals Â − γP̂, and the app's networkx Q equals it divided by 2m. The upper envelope on a bounded range gives each Admissible Partition a contiguous, range-clipped Optimality Domain. Partitions that are never on top, or on top at only one point, are dropped. Ties at a breakpoint go to the smallest P̂.
- **Newman (2016) eqs. 15, 17, 18.** These reduce to ω_in = Â/P̂ and ω_out = (2m − Â)/(2m − P̂), so γ̂ comes free from the CHAMP coefficients. For Lift weights they are well defined but have no likelihood behind them. γ̂ is undefined when:
  - there are no edges;
  - fewer than two groups have strength;
  - there is no cross-group weight;
  - Â ≤ P̂, which is the same as ω_in ≤ ω_out and as Q(1) ≤ 0.
- **Gibson & Mucha (2022).** γ̂ is evaluated once per Admissible Partition. A partition is a Stable Partition when γ̂ lies in its own domain. Stability depends on the input set. Restricting the set by K before CHAMP widens domains, so a filter applied before CHAMP and the same filter applied after stability give different procedures. All Stable Partitions are reported, and the paper has no rule for picking one or for the case of none. Isolated tags (k = 0) affect nothing except K counts.
- **`modularitypruning` 2.0.1.** Installs and runs on Python 3.14 / Windows. It agrees with the numpy formulas to ≤ 1e-12 on six Lift graphs (domains, γ̂, stable sets), so it works as a dev-only oracle with `single_threaded=True`. It differs from the papers on ω_in ≤ ω_out: it still computes a γ̂ and may call such a partition stable.
- **`resolution_profile`.** A valid but sparser input. On the largest graph it gave a different stable set from the 80 × 10 grid, so it does not replace the grid. It can be added to the grid's partitions as extra input.
- **14 open choices** are listed in §8 of the research file, for ticket 03.
