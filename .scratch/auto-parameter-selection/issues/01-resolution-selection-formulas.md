# Resolution-selection formulas (CHAMP, Newman, Gibson & Mucha)
Type: research
Status: open
Blocked by: none

## Question

What exactly do the primary sources define, so that our own numpy CHAMP and self-consistent γ estimate can be implemented correctly for a **weighted** (Lift) single-layer network?

- **CHAMP (Weir et al. 2017)**: the single-layer form. Each partition gives Q(γ) = A − γ·P; what are A and P exactly under RB/configuration modularity with weights (normalisation by 2m or not, self-loops)? How is the upper envelope (the admissible set and each partition's domain) computed over a bounded γ range, and how are ties, partitions that are never optimal, and the range ends handled?
- **Newman (2016)**: eq. (15) γ = (ω_in − ω_out)/(ln ω_in − ln ω_out), and eqs. (16)–(18) for ω_in and ω_out from a partition. What changes for weighted graphs (Newman's paper is unweighted)? Which cases leave the estimate undefined (ω_in ≤ ω_out, ω_out = 0, a single group, empty graph), and what do the sources say to do then?
- **Gibson & Mucha (2022)**: the definition of a stable partition (estimate inside its own CHAMP domain), whether the map γ → γ̂ is iterated or evaluated once per admissible partition, how One-Tag Clusters (isolated nodes, singletons) enter ω_in/ω_out, and what they recommend when several or no stable partitions exist.
- **`modularitypruning` 2.0.1**: which functions do this (`prune_to_stable_partitions`, `CHAMP_2D`, `gamma_estimate`, …), the exact formulas in its source code, how it treats weights ("an extension beyond the original publication"), and its defaults (`restrict_num_communities`, `single_threaded`). Can it run as a dev-only test oracle on our Lift graphs under Python 3.14 on Windows?
- Leiden's `resolution_profile` and deduplication: is bisection over γ a valid or better replacement for the fixed 80-value grid? (Research 31 B.3 notes that `min_diff_bisect_value` assumes integer weights.)

Write the formulas as they will be implemented, with section/equation references, and flag every point where the sources leave a choice open; [Resolution-selection rules](03-resolution-selection-rules.md) decides those.
