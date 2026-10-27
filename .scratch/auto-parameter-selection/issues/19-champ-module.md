# 19: CHAMP, γ̂ and the Selected Partition (`network.champ`)

**What to build:** a pure numpy/scipy module that takes one graph's edge arrays and a scan's unique memberships and returns the Admissible Partitions with their Optimality Domains, γ̂, stability and map targets, plus the Selected Partition or its reason code. It also provides γ_max(K) and the scan values.

**Blocked by:** none

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "The γ scan and Leiden" (scan values, γ_max(K)), "CHAMP", "γ̂ and Stable Partitions", "Selected Partition, Selected Resolution, Workbench γ and seed" (selection rule only). Reference code: [grid_run.py](../prototypes/05-grid-run/grid_run.py), [scan_ends.py](../prototypes/16-citable-upper-bound/scan_ends.py). Formulas: [Research 01](../research/01-resolution-selection-formulas.md), [Research 16](../research/16-citable-gamma-upper-bound.md).

- [x] `gamma_max_K(K)`: the exact bounded maximisation from the spec (scipy `minimize_scalar`, `xatol` 1e-12), cached. Undefined (raises or NaN, documented) for K < 2.
- [x] `scan_gammas(n_e, step)`: `round(step·i, 2)` for i = 0 … ⌈γ_max(n_e)/step − 1e-9⌉.
- [x] `canonical(membership)` renumbers labels by first occurrence. Dedup helpers record the first (γ, seed) and the hit count, given runs in scan order.
- [x] Â = 2·internal weight and P̂ = Σκ²/2m per partition, from the edge arrays. Isolated tags affect only the counts.
- [x] Envelope over [0, γ_end]:
  - one rtol (1e-12, scaled to the size of Q) for ties and zero-width domains;
  - the smallest P̂ wins a breakpoint tie;
  - twins (identical Â, P̂) keep the first canonical membership, and the dropped twins are counted;
  - `clipped_high` when a domain ends at γ_end.
- [x] γ̂ via ω_in and ω_out, evaluated once per Admissible Partition:
  - the count-based reason codes `no_edges`, `one_group`, `no_cross_weight` and `not_assortative`;
  - stable when a ≤ γ̂ ≤ b;
  - the map target is an Admissible Partition or `none`;
  - an assertion that γ̂ ≤ γ_max(n_e) ≤ γ_end for every assortative partition.
- [x] `select(...)`:
  - the minimum Multi-Tag Clusters (≥ 2 tags) is applied after stability;
  - the widest plain-γ domain wins, with ties to the lower midpoint, then canonical order;
  - the reason when nothing is selected is `no_edges`, then `no_stable_partition`, then `too_few_multi_tag_clusters`;
  - the Selected Resolution is the exact midpoint.
- [x] Results are plain dataclasses that serialise to JSON deterministically (sorted, no float formatting surprises).
- [x] `modularitypruning==2.0.1` is added as a **dev-only** dependency (not in the app extras, and not in the bundle's wheels).
- [x] Tests:
  - `gamma_max_K` matches GM22 Table S5 for K = 2…10 to 4 decimals, and rises with K.
  - On a hand-built graph with known partitions: domains, the breakpoint tie rule, twin dropping, `clipped_high`, each reason code and the map targets.
  - **Oracle:** on several test-Build Lift graphs (at least 3 pairs), domains, γ̂ and stable sets match `modularitypruning` (`single_threaded=True`) to ≤ 1e-10, restricted to graphs without `not_assortative` partitions.
  - The selection rule: the minimum filter applied after stability (a case where applying it before CHAMP would change the result), width ties, and each no-selection reason.
  - The γ̂ ≤ γ_max(n_e) assertion holds over every Admissible Partition of a full test-Build scan.

## Comments

- 2026-10-27, implementation: Everything else is implemented in `network/champ.py` and tested in `tests/test_champ.py`, including the `modularitypruning` oracle on four test-Build graphs. Not met: the Table S5 test covers K = 2, 3, 5 and 10 only, the values quoted in Research 16; K = 4 and 6–9 need reading from the GM22 SI and adding to `test_gamma_max_matches_gibson_and_mucha_table_s5_and_rises_with_k`.
- 2026-10-27, human check: the Table S5 test now covers K = 2…10. The values were read from GM22 SI p. 38 (§J.1), checked by the researcher, and all nine match `gamma_max_K` to four decimals.
