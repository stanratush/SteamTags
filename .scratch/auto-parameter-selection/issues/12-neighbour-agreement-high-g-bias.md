# Does Neighbour Agreement favour high g?
Type: grilling
Status: resolved
Blocked by: none

## Question

Is Neighbour Agreement systematically higher at large g, so that Automatic Parameter Selection drifts towards small networks for a reason unrelated to parameter stability? And if so, what changes in the method or in how its choice is reported?

- **The evidence** ([Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md), "After unblinding"; per-pair values in [neighbour-agreement-by-pair.md](../prototypes/05-grid-run/neighbour-agreement-by-pair.md)):
  - Neighbour Agreement peaks in the high-g half of the grid in every dataset.
  - Every chosen pair lies at g = 14–17, with 29–39 tags and 3–8 Multi-Tag Clusters.
  - Without the Pair Constraints, rpg would pick g=19, s=4 (NA 1.000).
- **Suspected mechanisms** to confirm or rule out:
  - fewer tags and fewer Multi-Tag Clusters leave less to disagree about;
  - at high g, a g-step removes few tags, so the tag Jaccard is high and the graphs are nearly identical (ticket 05: 66 identical-graph g-links, all in puzzle, rpg and simulation);
  - ARI's behaviour with few, large Clusters;
  - the 3-Cluster minimum binding at g ≥ 12 (184 of 196 such pairs).
- **What would show it:**
  - NA against g, tags and Multi-Tag Clusters per dataset;
  - NA split by link direction (g-links against s-links);
  - a baseline NA under a reference, for example the same comparison with neighbours' Selected Partitions replaced by size-matched random partitions, or a per-g normalisation.
  - Any check is a throwaway script under `prototypes/12-.../` over the ticket 05 results, with no new grid run.
- **Possible responses**, each to be decided or rejected:
  - leave the method as it is and add a fixed caveat to the explanation and the documentation;
  - report NA alongside a size-adjusted or baseline-relative value;
  - change the objective, or the tie-break (smallest g already pushes the other way).
- **Fixed by ticket 06, not reopened here:** the Pair Constraint defaults and the tolerance stay as decided, and are not re-tuned against the selected pairs. A method change that alters which pair is chosen is a change to the objective. If adopted, it is recorded here as such.

## Answer

Decided by grilling with the researcher, 2026-10-26. Evidence: [na_bias.py](../prototypes/12-neighbour-agreement-bias/na_bias.py) → [results.md](../prototypes/12-neighbour-agreement-bias/results.md), and [after_q3.py](../prototypes/12-neighbour-agreement-bias/after_q3.py) → [after-q3.md](../prototypes/12-neighbour-agreement-bias/after-q3.md). Both run over the ticket 05 raw records; edge sets were rebuilt with `build_network`, with no clustering and no new grid run.

**Verdict: the bias is confirmed, and its main cause is step size.**
- NA rises with g in every dataset: Spearman ρ(NA, g) is +0.27 to +0.50, and ρ with tags and with Multi-Tag Clusters is about the same with the opposite sign. In overall, mean NA is 0.62 at g 3–6 and 0.80 at g 15–20.
- **Cause: a one-step change in the thresholds, particularly in s, produces a smaller change in the graph when g is large.**
  - Link ARI follows Edge Overlap (ρ +0.45 to +0.54).
  - An s-step at g 3–6 keeps 68–74% of the edges (by Jaccard); at g 15–20 it keeps 87–90%.
  - As a result, s-link ARI climbs steeply with g (overall 0.51 → 0.79), while g-link ARI barely moves (0.73 → 0.82).
- **Ruled out as causes:**
  - *Chance agreement* ("less to disagree about"). With the neighbour's labels permuted, ARI averages ≈ 0 at every g. The spread does widen (p99 0.06 at g 3–6, 0.20–0.30 at g 15–20).
  - *ARI's behaviour with few, large Clusters.* It works the other way: moving one tag costs 0.10 ARI at g 15–20 and 0.02 at g 3–6.
- **Contributing:**
  - Identical-graph g-links occur only at g ≥ 11, in puzzle, rpg and simulation (66 links).
  - The 3-Cluster minimum binds for about half the pairs at g 15–20.
- **Possibly genuine in part:** at matched Edge Overlap, link ARI still rises with g in overall, puzzle and strategy. In rpg and simulation it does not.

**Responses**
- **The objective stays Neighbour Agreement.** A graph-change residual, a per-g normalisation and an NA over s-links or g-links only were each tried and rejected. They are new methods with no backing in the literature or the brief, and their picks scatter: rpg goes to 4·4, 13·12, 11·2 or 4·4. The smallest-g tie-break, the tolerance and the Pair Constraints stay as [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md) fixed them.
- **Objective change: identical-graph links leave the Neighbour Agreement mean.** This supersedes "Identical graphs are not special-cased" in [Per-pair metric definitions](04-pair-metric-definitions.md).
  - A step that removes nothing perturbs nothing, so its ARI of 1 is no evidence of stability.
  - NA is the mean ARI over comparable links **with a different graph**. That is the same set ticket 06 already counts towards the neighbour minimum.
  - The `identical_graph` flag stays on the link record, and the pair still reports how many comparable neighbours have an identical graph.
  - A pair whose only comparable neighbours have identical graphs has no NA (`no_comparable_neighbours`). On this Build no pair loses its NA.
  - Effect on this Build: NA changes for 40–42 pairs each in puzzle, rpg and simulation, and for none in overall and strategy. **Only rpg's chosen pair changes**, from g=14, s=12 to **g=7, s=5**: NA 0.774 over 4 neighbours, max 0.822 at 13·12, a near-best set of 9, 15 Multi-Tag Clusters, 71 tags, retention 0.785, γ 2.006 / 2.01, Seed-Noise Floor 0.80, 9 hits. Puzzle's NA becomes 0.980 (was 0.986). Simulation's near-best set becomes 9 (was 10).
  - Mean NA still rises with g everywhere except rpg, so the caveat is still needed.
- **No second NA number.** No size-adjusted or baseline-relative NA is reported: it would depend on a per-dataset fit and would invite choosing by it.

**New term: Edge Overlap** (added to [CONTEXT.md](../../../CONTEXT.md))
- The Jaccard overlap of two neighbouring Threshold Pairs' edge sets: unweighted, each tag pair counted once, over all edges. Edges of tags dropped by a g-step count as differences.
- For reporting only; it never enters selection.

**Reporting**
- **Pair Inspector**: one row per neighbour link, with direction (g or s), status, ARI, tag overlap, Edge Overlap (two decimals) and an "identical graph" marker.
- **Selection explanation** (the template in ticket 06):
  - The neighbour sentence becomes "Its Neighbour Agreement is 0.77 over 4 neighbours with a different graph." When the count is above 0, it adds "1 more neighbour has an identical graph and is not counted."
  - When the chosen Selected Partition has exactly the run's configured minimum number of Multi-Tag Clusters *k*, it adds "Its Selected Partition has the minimum *k* Multi-Tag Clusters; a coarser split was not allowed." Today that applies to simulation and strategy.
  - The italic closing caveat gains a fixed second paragraph, always shown, and the User Guide carries the same text:
    > *Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, particularly s, generally produces a smaller change in the graph. This can increase agreement independently of the robustness of the Clusters. Choosing the smallest g among near-best pairs partially counterbalances this tendency.*

    (The researcher's wording; "community robustness" became "the robustness of the Clusters" to match the glossary.)

**Handed on**
- To [Exports and documentation](11-exports-and-documentation.md): Edge Overlap is a column of the per-direction Neighbour Agreement table. The User Guide carries the high-g caveat, explains why identical-graph links are left out, and describes Edge Overlap.
- [Validation design](07-validation-design.md)'s pilot validated rpg 14·12, the pair chosen under the old rule. It was a feasibility pilot, none of ticket 07's decisions depend on the pair, and it is not re-run.
