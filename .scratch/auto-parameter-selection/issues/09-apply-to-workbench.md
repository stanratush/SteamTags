# Apply-to-Workbench semantics
Type: grilling
Status: resolved
Blocked by: 03

## Question

What exactly happens when the user applies a selected (or any inspected) Threshold Pair to the Workbench?

- Which controls change: g, s, Minimum Months, the hidden tags, Clustering Weight = Lift, algorithm = Leiden, γ = the rounded Selected Resolution, the seed.
- The Workbench clusters with one seed at one γ. Leiden at the domain midpoint with the main seed may not reproduce the Selected Partition, which was found at some scan γ and seed. Do we pick the first scan seed that reproduces it at the rounded midpoint? If none does, do we show the ARI between what the Workbench shows and the Selected Partition, or refuse?
- Fixed by [Modules, caching and parallelism](08-modules-caching-parallelism.md): `detect` and the scan's `leiden_scan` share one igraph construction, so Leiden at the Selected Partition's first (γ, seed), which the cache stores with its hit count, reproduces it exactly. The open question is the Workbench's two-decimal γ, not the code path.
- How the Workbench shows that its state came from Automatic Parameter Selection, and whether that changes the Network State key (it shouldn't, if every applied value is an ordinary setting).

## Answer

Decided by grilling with the researcher, 2026-10-26. Facts: [prototypes/09-apply-reproduction/results.md](../prototypes/09-apply-reproduction/results.md).

**What Apply sets**
- Apply **replaces** every Network State setting the Workbench controls with the run's values, as "Open Network State…" (`do_open`) does. Nothing is merged. The settings are:
  - dataset, g, s, Minimum Months;
  - the hidden Genre Tags and the defining tag, and the removed tags;
  - Clustering Weight, algorithm, γ and seed.
- `null_replicates` and `noise_seeds` are not controls. They are already in `SelectionSettings`, so they match.
- The Tidy layout and the Removal Sensitivity view are cleared, and the app switches to the Workbench mode.
- There is no confirmation dialog, matching Open.

**γ and seed: a search, precomputed**
- The **Workbench resolution** and a new **Workbench seed** are found by a search over:
  - the two-decimal γ values inside the Selected Partition's Optimality Domain, nearest the Selected Resolution first (ties go to the lower value);
  - at each γ, the main seed and then the 10 scan seeds in stream order.
- The first (γ, seed) at which Leiden reproduces the Selected Partition exactly is kept.
- The search runs inside the per-graph grid task, is deterministic, and is cached with the graph's result, so Apply computes nothing.
- On this Build it reproduces 758 of 764 Selected Partitions. 673 of them reproduce at the nearest-to-midpoint value. γ never leaves the domain. The other options were rejected:
  - the Workbench resolution with the main seed only: 55% exact, and the puzzle pick fails;
  - the scan's first (γ, seed): exact, but outside the domain in 31% of pairs, so the Workbench would show Q where CHAMP says another partition wins;
  - the search at the nearest-to-midpoint value only: 88%.
- `not_representable` keeps its meaning: no two-decimal value lies inside the domain. A new flag, `not_reproduced`, marks a representable pair where the search finds nothing.
- Consequence: when the Workbench seed is a scan seed, the Workbench derives its null and noise seeds from it. Its Seed-Noise Floor then differs from the one Parameter Selection reports, which uses the main seed's noise seeds at the exact Selected Resolution. The User Guide says so (ticket 11).

**When nothing reproduces**
- For `not_reproduced` and `not_representable` pairs, Apply still works. It never refuses.
- It applies γ = the Selected Resolution rounded to two decimals and kept inside [0.25, 3.00], with the main seed.
- The Workbench then says it "shows a different partition from the Selected Partition: ARI 0.xx". There are 6 such pairs on this Build, each hit once in 560 runs.

**Where the Workbench says its state came from**
- A provenance line sits where `verify-result` is today, for example "Applied from Parameter Selection: puzzle, g=14, s=2 — Selected Partition reproduced ✓", or the ARI line above.
- It is checked once, on the first recompute after Apply, by comparing the Workbench's Clusters with the stored membership through the `verify` store mechanism.
- The line stays while the Network State key equals the applied key and disappears as soon as any setting changes.
- It is display only and not part of the Network State. Every applied value is an ordinary setting, so the key and `state_id` are unchanged.
- Whether an export records the provenance belongs to [Exports and documentation](11-exports-and-documentation.md).

**γ input**
- The Workbench γ input goes from `step=0.05` to `step=0.01`. `min=0.1` and `max=3.0` stay.
- Before, a two-decimal value off the 0.05 grid (1.09) was invalid in the browser, and Dash turns a user edit of an invalid number into `None`. "Open Network State…" had the same latent problem.

**What can be applied**
- The Selected Partition of **any** pair that has one: the chosen pair, a near-best pair, any heatmap cell.
- A pair without a Selected Partition shows Apply disabled with its reason code.
- Other Admissible or Stable Partitions in the CHAMP view are for inspection only and cannot be applied.

**Amends**
- [Resolution-selection rules](03-resolution-selection-rules.md): the Workbench resolution is now the γ found by the search, not just the nearest-to-midpoint value. A Workbench seed and the `not_reproduced` flag are added.
- [Modules, caching and parallelism](08-modules-caching-parallelism.md): the graph file also holds the Workbench resolution, the Workbench seed and the flags. The search is part of the grid task, so it falls under the method version.

## Comments

- 2026-10-27, amended by [Graph-specific γ scan](16-graph-specific-gamma-scan.md): the Workbench γ input becomes min 0.01, no maximum, step 0.01. rpg g=3 s=3 reproduces only at γ = 3.23. The reproduction is still 758 of 764 under the new scan.
