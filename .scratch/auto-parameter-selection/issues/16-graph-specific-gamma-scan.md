# Graph-specific γ scan
Type: grilling
Status: resolved
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
- 2026-10-27, grilling in progress. Gibson & Mucha 2022 (main text, read in the browser) and the leidenalg 0.12.0 reference and source were checked. Accepted so far:
  - Lower end: the scan starts at 0, as every Gibson & Mucha and Weir example does; the γ = 0 runs return the trivial partition, so nothing is added to CHAMP's input and no γ_min bound is computed.
  - Spacing: linear, `round(0.05·i, 2)`, with the 10 scan seeds.
  - Null replicates and subsamples derive their own range by the same rule.
  - Leiden: `detect` and `leiden_scan` loop `optimise_partition(n_iterations=1)` on one optimiser, stopping at gain ≤ 0 or after 1,000 passes; identical to leidenalg's own `n_iterations=-1` loop below the cap; `pass_capped_runs` recorded per pair; a test asserts equality with `-1`.
  - Upper end: open. The researcher asked for a rule that can be cited directly instead of γ_pos; research in [research/16-citable-gamma-upper-bound.md](../research/16-citable-gamma-upper-bound.md).
- 2026-10-27, further accepted: upper end = Gibson & Mucha's γ_max(K) at K = n_e (tags with an edge), rounded up to the 0.05 grid, same rule for both weights; computed by exact 1-D maximisation and tested against GM22 Table S5; the methods text cites GM22 §J and notes that §J.2 needs no equal sizes ([research/16](../research/16-citable-gamma-upper-bound.md)). No low-γ guard. `clipped_low`, `estimate_below_range` and the `below_range` map target removed. Workbench γ minimum 0.01. `grid_key()` carries only the step; the end rule changes with `selection.METHOD_VERSION`.

## Answer

Decided by grilling with the researcher, 2026-10-27. Gibson & Mucha 2022 (main text in the browser, SI §J) and the leidenalg 0.12.0 reference and source were checked during the session. The citable upper end is researched in [research/16-citable-gamma-upper-bound.md](../research/16-citable-gamma-upper-bound.md), and the decided rule is re-measured in [prototypes/16-remeasure/results.md](../prototypes/16-remeasure/results.md). This replaces the scan and CHAMP-range parts of [Resolution-selection rules](03-resolution-selection-rules.md). The rest of ticket 03 stands.

**The scan**
- γ runs linearly on the two-decimal grid, `round(0.05·i, 2)` for i = 0 … ⌈γ_max(n_e)/0.05⌉, with the same 10 scan seeds.
  - It starts at 0, as every Gibson & Mucha and Weir example does. The γ = 0 runs return the trivial partition, so nothing is added to CHAMP's input and no lower bound is computed.
  - **The upper end is Gibson & Mucha's γ_max(K) at K = n_e**, the number of tags with an edge (GM22, "Bounds on γ estimates" and Discussion; SI §J.1–J.3). They propose γ_max(K_max) as the end of the γ range. n_e is the largest K any partition can have, and γ_max(K) rises with K, so it needs no user choice.
  - It is computed by exact one-dimensional maximisation and unit-tested against GM22's Table S5 (K = 2…10).
  - The methods text cites §J and adds one sentence: the §J.2 derivation uses only Cauchy–Schwarz and assortativity, so the bound holds for unequal Clusters and for weights. Research 16 §2.2 has the argument. It was also checked on about 135,000 found partitions and 1,523 deliberately unequal random ones, with no violation.
- The same rule serves Lift and Shared games. γ_max(n_e) depends only on n_e.
- Our own γ_pos (Research 15) is not used and not recorded, because no source states it. Jeub et al.'s and Bazzi et al.'s γ⁺ was the strictly citable fallback, at 7× the cost (26× on Shared games), and was rejected.
- No cap on the scan length. γ_max(K) grows slowly (3.79 at 21 tags, 17.7 at 139), so a scan is 77–356 values on this Build.
- Null replicates and subsamples each derive n_e, and so their own range, from their own graph. The fixed-γ Q arm still uses the observed Selected Resolution.

**Leiden**
- `detect` and `leiden_scan` both run `optimise_partition(n_iterations=1)` in a loop on one optimiser. They stop at the first pass that gains ≤ 0, or after **1,000 passes**.
  - leidenalg's own `n_iterations=-1` is this loop (Python, `diff_inc > 0`) without the cap, so results below the cap are identical by construction. A unit test asserts equality with `-1` on a graph where it stops.
  - The cap is needed because the strict `> 0` test never ends on float-noise gains (~1e-14). On this Build that happens on simulation g=5–8 s=5 at γ 6.2–7.25: 77 runs.
- `pass_capped_runs` is counted per graph and appears only in the exports.

**CHAMP and stability**
- The envelope runs over **[0, last scan γ]**: the range searched, as CHAMP's own `max_pt` intends.
  - A domain cut at the top keeps its clipped width, carries `clipped_high` and stays eligible.
  - `clipped_low` is removed: the trivial partition owns [0, first split].
- **`estimate_above_range`, `estimate_below_range` and the `above_range` / `below_range` map targets are removed.**
  - γ̂ > 0 always holds, and a γ̂ below every non-trivial domain maps to the trivial partition.
  - γ̂ ≤ γ_max(n_e) ≤ the last scan γ for every assortative partition. An assertion, covered by a unit test, guards this.
  - A map target is now an Admissible Partition or `none`.
- **No low-γ guard.** The widest plain-γ domain still wins, and the minimum Multi-Tag Clusters is the user's lever. On puzzle g=4 s=4 a 3-Cluster partition with domain [0.064, 0.367] now wins. Its Neighbour Agreement falls to 0.003, so NA marks it without a guard.

**The Workbench**
- The γ input becomes **min 0.01, no maximum, step 0.01**.
- rpg g=3 s=3's Selected Resolution is 3.090 and reproduces only at γ = 3.23, so a maximum of 3.0 would have broken Apply.

**Keys, records and exports**
- `grid_key()` drops the fixed (0.25, 3.00, 0.05) triple and carries only the **step** (0.05, config-only). The end rule changes with `selection.METHOD_VERSION`.
- Each graph file and the exports' pairs table record **n_e, γ_max(n_e), the last scan γ, the scan length and `pass_capped_runs`**. Nothing else about the range is recorded.
- Validation records each replicate's scan length and capped runs, aggregated per pair.
- `parameter_selection.json` names the rule (`gm22_gamma_max_n_e`) and the step.
- The CHAMP plot's x-axis runs from 0 to the last scan γ.
- The loading panel's ETA uses the scan length as an extra weight.

**Re-measured on this Build** ([results](../prototypes/16-remeasure/results.md); the reference was recomputed and matches [Does Neighbour Agreement favour high g?](12-neighbour-agreement-high-g-bias.md) exactly)
- 764 of 765 pairs have a Selected Partition (rpg g=18 s=4 still has none). Three change, all at g ≤ 4: puzzle 3/3, puzzle 4/4 and rpg 3/3.
- No `clipped_high`, `not_representable` or γ̂ above the range occurs across 27,549 Admissible Partitions.
- **No chosen pair moves:** overall 17,2 · puzzle 14,2 · rpg 7,5 · simulation 14,5 · strategy 14,2. Their NA and near-best sets are unchanged, and no pair's Qualifying status changed.
- The Workbench reproduction is still 758 of 764, with the same six `not_reproduced` pairs.
- Cost: 1,032,800 Leiden runs (2.4×) and 329 s on 12 workers, against 95 s. simulation g=5 s=5 alone takes 136 s, because of its 56 capped runs. Heaviest-first dispatch starts it first.
- So ticket 05's and ticket 09's measurements need no separate re-run. The spec quotes these numbers.

**Handed on**
- To the spec: the scan rule, `gamma_max_K` with its Table S5 test, the Leiden pass loop and its equality test, the removed reason codes and map targets, the Workbench input range, and the recorded fields.
- To [Exports and documentation](11-exports-and-documentation.md): the methods paragraph on the γ range (GM22 §J plus the unequal-size sentence) and the pairs-table and `parameter_selection.json` fields above.
