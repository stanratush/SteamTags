# Graph-specific γ scan
Type: grilling
Status: open
Blocked by: 15

## Question

Given the bounds from [Graph-specific γ bounds](15-graph-specific-gamma-bounds.md), how exactly is each graph's γ scan built, and what does that change in the decisions built on the fixed 0.25–3.00 scan?

Reopens the scan and CHAMP-range parts of [Resolution-selection rules](03-resolution-selection-rules.md). The rest of ticket 03 (dedup, tie rules, γ̂ as a single fixed-point test, the minimum Multi-Tag Clusters, the widest-domain rule) stands unless this ticket says otherwise.

- **The scan:** which bounds, the number of values or the step, linear or log or event sampling, and whether every scan γ stays a two-decimal value the Workbench can step through. The 10 scan seeds stay.
- **CHAMP and stability:** the envelope range per graph, what `clipped_low` / `clipped_high` mean against a computed bound, and whether `estimate_above_range` / `estimate_below_range` survive.
- **The Workbench:** its γ input runs 0.1–3.0, now with step 0.01 ([Apply-to-Workbench semantics](09-apply-to-workbench.md)). What happens to a Selected Resolution outside it (`not_representable`, or a wider input)?
- **Validation:** does each null replicate and each subsample derive its own bounds, as the "full procedure" of [Validation design](07-validation-design.md) suggests?
- **Keys and exports:** what goes into `grid_key()` in place of the fixed γ list ([Modules, caching and parallelism](08-modules-caching-parallelism.md)), the bounds recorded per pair, and `parameter_selection.json` ([Exports and documentation](11-exports-and-documentation.md)).
- **Re-measuring:** whether the [Exploratory grid run on the current Build](05-exploratory-grid-run.md) and ticket 09's 758 of 764 reproduction must be re-run, and whether the chosen pairs (g = 14–17, [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md)) move.

## Comments

- 2026-10-26, from [Graph-specific γ bounds](15-graph-specific-gamma-bounds.md) ([research](../research/15-graph-specific-gamma-bounds.md) §6). The bounds are settled; these choices are left open for this ticket:
  1. The upper end: γ_pos (no stable partition or γ̂ can lie above it; median 3.12 on Lift), Jeub et al.'s γ_max (exact end of the envelope; median 15, up to 204), or CHAMP's Q = 0 cut.
  2. The lower end: 0 (as in the sources), the λ₂ lower bound on γ_min, or Jeub et al.'s iterated upper bound. Also whether each end is rounded outwards to the two-decimal grid.
  3. The CHAMP range: [0, ∞) with the trivial and all-singletons partitions added to the input (no clipping), or the scan range with clip flags. This decides how the top and bottom domains' widths count for the widest-domain rule.
  4. Whether `estimate_above_range` / `estimate_below_range` survive. Above cannot happen once the scan reaches γ_pos; below becomes a "maps to trivial" map target.
  5. The spacing: linear 0.05 as now, 0.01, log, or event sampling. The scan length is no longer fixed.
  6. A cap on the scan length or end, for graphs like rpg g=3 s=3 (γ_pos = 11.8).
  7. What is recorded per pair and what enters `grid_key()`: the rule, or also the bound values.
  8. Whether null replicates and subsamples derive their own bounds.
  9. The Workbench γ input (0.1–3.0) against Selected Resolutions above 3.0.
  10. One rule for both Clustering Weights. On Shared games, γ_pos is lower (median 2.05, max 3.99).
  11. A Leiden pass cap. With `n_iterations=-1`, Leiden never returned on simulation g=5 s=5 at several γ between 6.2 and 6.7: each pass gained only float noise.
  12. Whether the widest-domain rule needs a guard once the bottom is not clipped at 0.25. On puzzle g=4 s=4, a low-γ partition with 3 Multi-Tag Clusters (domain [0.064, 0.367]) becomes the widest.
