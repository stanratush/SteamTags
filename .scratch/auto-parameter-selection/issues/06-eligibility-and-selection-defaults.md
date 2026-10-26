# Eligibility constraints and selection defaults
Type: grilling
Status: resolved
Blocked by: 05

## Question

Which constraints make a Threshold Pair eligible, what are their documented defaults, and how exactly is the pair chosen?

- The constraints: minimum Information Retention, maximum share of isolated tags, minimum largest-connected-component share, a minimum and/or maximum number of Clusters, and "has a Selected Partition". Default values are justified by [Exploratory grid run on the current Build](05-exploratory-grid-run.md) and fixed before looking at which pair they select.
- From [Per-pair metric definitions](04-pair-metric-definitions.md): whether a pair needs a minimum number of comparable neighbours (with none, one lucky neighbour scores 1.0), and whether the share of identical-graph neighbours affects eligibility.
- The tolerance: within 0.05 of the maximum Neighbour Agreement among eligible pairs (configurable); then the smallest g, then the smallest s.
- What to report when no pair is eligible, and how the reasons for selection are worded for each dataset.
- Where the defaults live (`config/network.toml`? a new `[parameter_selection]` table?) and how they enter the cache key.

## Answer

Decided by grilling with the researcher, 2026-10-26. Evidence: [Exploratory grid run on the current Build](05-exploratory-grid-run.md), [results](../prototypes/05-grid-run/results.md). The defaults were fixed while per-pair Neighbour Agreement was still blinded. It was unblinded only after both rounds were accepted (see "After unblinding").

**Terms** (now in [CONTEXT.md](../../../CONTEXT.md))
- A **Qualifying Pair** has a Selected Partition and a Neighbour Agreement, and meets every **Pair Constraint**. "Eligible" is avoided because it belongs to the Eligible Pool.
- Automatic Parameter Selection picks only among Qualifying Pairs.

**Pair Constraints and their defaults** (the same for all five datasets, all bounds inclusive)

| Pair Constraint | Default | Why this value |
|---|---|---|
| Minimum Information Retention | 0.50 | The network still represents at least half of the visible game–tag assignments. It cuts only the high-g corner: from g ≥ 12 in puzzle, g ≥ 18–19 in rpg, simulation and strategy, never in overall. 0.60 would cut about half the grid, which would amount to choosing g rather than guarding against a bad pair. |
| Maximum share of isolated tags | 0.10 | Retention already penalises isolation. This one guards the network's structure, and cuts the tail above about p90–p95. |
| Minimum LCC share (of non-isolated tags) | 0.90 | Never binds on this Build (always 1.000). Kept as a guard for other Builds. |
| Minimum comparable neighbours **with a different graph** | 2 | Corner and diagonal pairs have at most 2 neighbours in the grid, so 3 would rule out the diagonal regardless of quality. Identical-graph neighbours still enter the mean (ticket 04), but don't count towards this minimum. |
| Maximum Multi-Tag Clusters | off | No principled value; the observed range is 3–23. |

- **No pair-level minimum on Clusters.** The Selected Partition's minimum Multi-Tag Clusters (default 3, from [Resolution-selection rules](03-resolution-selection-rules.md)) is the only one.
- **Not constraints:** the Seed-Noise Floor and the Selected Partition's hit count. They are reported next to the chosen pair, so algorithmic stability never enters a choice made by parameter stability.
- A pair whose Neighbour Agreement is unavailable never qualifies.

**Choosing the pair**
1. Among Qualifying Pairs, the **near-best set** is every pair with Neighbour Agreement ≥ max − tolerance. The comparison is in absolute ARI, inclusive, with a 1e-12 float tolerance. The tolerance defaults to **0.05** and is configurable from 0 to 1.
2. From the near-best set, the pair with the smallest g is chosen, then the one with the smallest s.
3. The near-best set is reported and highlighted on the heatmap, not only the chosen pair.

**Reasons a pair doesn't qualify.** Every failing constraint is recorded, not only the first, as a list of codes: `no_selected_partition`, `no_neighbour_agreement`, `too_few_comparable_neighbours`, `retention_below_min`, `isolated_share_above_max`, `lcc_share_below_min`, `too_many_clusters`.

**When no pair qualifies**
- There is no automatic relaxation. The status is `no_qualifying_pair`, and there is no chosen pair and no validation run.
- A table shows how many pairs each constraint excludes, alone and cumulatively.
- The heatmaps stay usable, and any pair can still be inspected and applied by hand.
- Wording: "**No pair qualifies** under the default constraints. 152 of 153 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): … Loosen a constraint, or inspect any pair in the grid and apply it by hand."

**The user can change the constraints**
- The mode has a **Pair Constraints panel**: the four constraints above, the maximum Multi-Tag Clusters (off, or an integer at least as large as the Selected Partition's minimum) and the tolerance.
  - Allowed values: shares and the tolerance from 0 to 1, minimum neighbours an integer from 0 to 4.
- Editing a value changes nothing on its own. The user confirms with a button, and only then are the Qualifying Pairs, the near-best set, the chosen pair and the explanation recomputed.
  - Recomputing is a cheap post-step over the cached per-pair results: no background job and no re-run of the grid.
  - The panel also has a "Reset to defaults" button.
- One shared set of values applies to all five datasets by default, with an "apply to this dataset only" override. Each dataset's result shows the values it used.
- The minimum Multi-Tag Clusters is **not** in this panel, because changing it changes the Selected Partitions and needs a re-run. It belongs with the fixed settings (map fog: "Changing the fixed settings").
- **Labelling:** when any value differs from the configured default, the explanation, the cross-dataset view and every export carry **"Custom constraints"**, listing each changed value next to its default. Otherwise they say "Default constraints".

**Where the defaults live, and the cache**
- A new **`[parameter_selection]` table in `config/network.toml`**, read by both the app and the report. It holds the tolerance and the Pair Constraint defaults.
- Pair Constraints and the tolerance are **not part of the cache key**, because the selection is recomputed from the cache. The minimum Multi-Tag Clusters stays in the key.
- Each selection result records the constraint values and the tolerance it was computed with.

**The selection explanation** is one template for every dataset. It is built only from Neighbour Agreement, the constraints and the counts, and never cites Q, Coverage or Silhouette.

> **Selected: g = 8, s = 5**, resolution 1.234 (Workbench 1.25).
> 152 of 153 pairs have a Selected Partition. 120 qualify under the default constraints: Information Retention ≥ 0.50, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a different graph. The LCC constraint excluded no pair.
> The highest Neighbour Agreement among them is 0.91 (g = 10, s = 6). 7 pairs are within 0.05 of it, and of these the one with the smallest g, then the smallest s, is selected.
> Its Neighbour Agreement is 0.88 over 4 neighbours (1 with an identical graph).
> *Neighbour Agreement measures how little the clustering changes when g or s moves by one. It does not show that the Clusters are real.*

- A constraint that excluded no pair is named as such.
- When the Seed-Noise Floor is below 0.5, this sentence is added: "The Seed-Noise Floor at this resolution is 0.42: the clustering also depends noticeably on the seed."
- For a `not_representable` pair, the Workbench sentence says its resolution can't be entered as a two-decimal value.
- The closing caveat is always shown.

**After unblinding** (facts only; the defaults are not re-tuned in this effort). Default constraints, tolerance 0.05, Build `20261008T221504Z-7a23ae9f`:

| Dataset | Qualifying | Excluded, alone | Max NA (at g,s) | Near-best set | **Chosen** | NA (min) | Multi-Tag Clusters | Tags | Retention | Selected / Workbench γ | Seed-Noise Floor | Hits |
|---|---:|---|---|---:|---|---|---:|---:|---:|---|---:|---:|
| overall | 149 | isolated 4 | 1.000 (20,3; 20,9) | 7 | **g=17, s=2** | 0.974 (0.921) | 4 | 29 | 0.533 | 1.151 / 1.15 | 1.00 | 30 |
| puzzle | 85 | retention 59, isolated 11 | 0.986 (14,2) | 1 | **g=14, s=2** | 0.986 (0.959) | 4 | 31 | 0.517 | 1.092 / 1.09 | 0.52 | 13 |
| rpg | 120 | retention 22, isolated 10, neighbours 3, no Selected Partition 1, no NA 1 | 0.880 (14,12) | 2 | **g=14, s=12** | 0.880 (0.641) | 8 | 33 | 0.569 | 1.753 / 1.75 | 1.00 | 126 |
| simulation | 129 | retention 22, isolated 1, neighbours 1 | 1.000 (17,2; 17,3; 17,4) | 10 | **g=14, s=5** | 0.981 (0.925) | 3 | 38 | 0.610 | 0.865 / 0.86 | 1.00 | 90 |
| strategy | 113 | retention 33, isolated 7 | 1.000 (14,2) | 3 | **g=14, s=2** | 1.000 (1.000) | 3 | 39 | 0.579 | 1.009 / 1.01 | 1.00 | 63 |

- The LCC constraint and the cluster maximum (off) bound nowhere.
- The constraints changed the chosen pair only in rpg. Unconstrained, rpg would choose g=19, s=4 (NA 1.000), which is excluded for retention.
- Every chosen pair lies at **g = 14–17, with 29–39 tags and 3–8 Multi-Tag Clusters**. In puzzle, the chosen pair's retention (0.517) is close to the 0.50 bound.
- Neighbour Agreement peaks in the high-g half of the grid in every dataset. This question is now [Does Neighbour Agreement favour high g?](12-neighbour-agreement-high-g-bias.md); the defaults stay as decided.

**Handed on**
- To [Validation design](07-validation-design.md): which pair validation runs for when the user changes the constraints. The options are the pair chosen under the default constraints, or the currently chosen one with a "re-run validation" action. There is also no validation when the status is `no_qualifying_pair`.
- To [Modules, caching and parallelism](08-modules-caching-parallelism.md): Pair Constraints and the tolerance are outside the cache key, and the selection is a post-step over cached per-pair results. The defaults live in `[parameter_selection]` in `config/network.toml`.
- To [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md): the Pair Constraints panel with a confirm button and Reset to defaults; the per-dataset override; non-qualifying pairs marked with their reason codes; the near-best set highlighted; the explanation template and the no-qualifying message.
- To [Exports and documentation](11-exports-and-documentation.md): the "Custom constraints" / "Default constraints" label, the constraint values and tolerance in the settings JSON, and the per-pair reason codes in the grid table.
