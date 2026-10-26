# Resolution-selection rules
Type: grilling
Status: resolved
Blocked by: 01

## Question

Exactly how does one **Threshold Pair** get its **Selected Partition** and **Selected Resolution**, including every edge case?

- The γ scan: 80 values evenly spaced from 0.25 to 3.0 (linear or log?), 10 seeds per γ; or bisection, if [Resolution-selection formulas](01-resolution-selection-formulas.md) recommends it.
- Deduplicating partitions: equality as set partitions over all nodes, isolated tags included.
- The CHAMP range: is the envelope taken over [0.25, 3.0] only or over [0, 3.0]? How is a domain cut off at a range end treated (its width, its midpoint, its eligibility)?
- Self-consistent γ: evaluated once or iterated; what happens when it is undefined (ω_in ≤ ω_out, ω_out = 0, fewer than two groups), or when it falls outside the scan range.
- "At least three Multi-Tag Clusters": how One-Tag Clusters and isolated tags count.
- Ties on domain width; and the outcome when no Stable Partition qualifies (does the pair become ineligible with a recorded reason?).
- Rounding: `Settings` stores γ to 2 decimals (`resolution_text`). What if the domain is narrower than 0.01, or the rounded midpoint falls outside it?
- Recorded per pair: every Admissible Partition with its domain, γ estimate and stability flag, so the UI can draw the CHAMP plot.

## Answer

Decided by grilling with the researcher, 2026-10-26. Formulas and section numbers refer to [research/01-resolution-selection-formulas.md](../research/01-resolution-selection-formulas.md).

**The scan (input set)**
- γ runs **linearly from 0.25 to 3.00 in steps of 0.05**: 56 values, computed as `round(0.25 + 0.05·i, 2)` so there is no float drift. Every scan γ is therefore a two-decimal value the Workbench's γ input steps through.
- The same 10 scan seeds are used at every γ, giving 560 Leiden runs per Threshold Pair.
- Nothing else feeds CHAMP. `resolution_profile` (bisection) is not used.
- Consequence to check in [Exploratory grid run on the current Build](05-exploratory-grid-run.md): stability depends on the input set, and Research 01's measurements used 80 values. The coarser grid may widen domains and change some stable sets.

**Deduplication**
- Partitions are equal when they are the same set partition of **all** tags, isolated tags included. They are canonicalised by renumbering labels in order of first occurrence.
- For each unique partition we record the **first (γ, seed)** in scan order that found it, and its **hit count** out of the 560 runs.

**CHAMP**
- The envelope is taken over **[0.25, 3.00]**, exactly the scanned range. There is no extrapolation below it.
- A domain cut off at a range end keeps its clipped width and midpoint, carries a `clipped_low` / `clipped_high` flag, and stays eligible.
- One relative tolerance, `rtol = 1e-12` scaled to the size of Q (§2.1), is used for breakpoint ties and for dropping zero-width domains. At a breakpoint tie the smallest P̂ wins.
- Distinct partitions with identical (Â, P̂) keep the one whose canonical membership sorts first. The number of dropped twins is counted.
- The upper end stays fixed at 3.00. It is not γ_max(K_max).

**Self-consistent γ and stability**
- γ̂ is evaluated **once** per Admissible Partition, as a fixed-point test (Gibson & Mucha). Newman's own iteration is never run.
- A partition is stable when **a ≤ γ̂ ≤ b**, a closed interval.
- If γ̂ lies outside [0.25, 3.00], the partition is not stable, with reason `estimate_above_range` or `estimate_below_range`. This holds even for a domain clipped at 3.00.
- These cases get "no estimate", so the partition is never stable. The guards use counts, not floats (§3.3):

  | Case | Reason code |
  |---|---|
  | No edges | `no_edges` |
  | Fewer than two groups with strength | `one_group` |
  | ω_out = 0 | `no_cross_weight` |
  | Â ≤ P̂ | `not_assortative` |

  The last case differs from `modularitypruning`, which computes a γ̂ there. Oracle tests compare stable sets only on graphs where these cases don't occur.
- Each Admissible Partition records its **map target**, for the CHAMP plot: the Admissible Partition whose domain contains its γ̂, or `below_range`, `above_range` or `none`.

**The Selected Partition**
- The **minimum Multi-Tag Clusters** is a setting, default 3, and part of the cache key.
  - It counts only Clusters with ≥ 2 tags. One-Tag Clusters never count, whether isolated or connected.
  - It is applied **after** stability, as a filter on the Stable Partitions, never as a filter on CHAMP's input.
  - [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md) keeps its own pair-level constraints on cluster counts.
- Among the qualifying Stable Partitions, the widest domain wins.
  - Width is in plain γ units (b − a). Log-width and Gibson & Mucha's γ-scaled area were considered and rejected; the methods text says so.
  - Widths equal within tolerance go to the lower midpoint, then to canonical membership order.
- If none qualifies, the pair has **no Selected Partition** and records the first matching reason, in this order: `no_edges`, `no_stable_partition`, `too_few_multi_tag_clusters`. Eligibility and Neighbour Agreement handling belong to tickets 06 and 04.

**Rounding**
- The **Selected Resolution** is the exact midpoint of the domain, stored unrounded.
- A separate **Workbench resolution** is stored: the two-decimal value closest to the midpoint that lies inside the domain.
  - *Amended by [Apply-to-Workbench semantics](09-apply-to-workbench.md):* the Workbench resolution is the first two-decimal γ in the domain, nearest the midpoint first, at which the main seed or a scan seed reproduces the Selected Partition. That seed is stored as the **Workbench seed**. A representable pair where nothing reproduces is flagged `not_reproduced`.
- If no two-decimal value lies inside the domain, the Selected Partition stands but is flagged `not_representable`.
- There is no minimum domain width.
- Facts for [Apply-to-Workbench semantics](09-apply-to-workbench.md):
  - the Workbench γ input has `step=0.05` and `min=0.1` (`app/layout.py`);
  - every first (γ, seed) lies on the 0.05 grid, so it can be entered there directly.

**Recorded per pair**
- **Per Admissible Partition:**
  - canonical membership, Â and P̂;
  - the domain [a, b] with its clip flags;
  - ω_in, ω_out, and γ̂ or a reason code;
  - the map target and the stable flag;
  - the number of Multi-Tag Clusters and of One-Tag Clusters;
  - the first (γ, seed) and the hit count.
- **Per pair:**
  - 2m, the number of tags and of isolated tags;
  - the number of unique partitions and of twins dropped;
  - the index of the Selected Partition, or the no-selection reason;
  - the Selected Resolution and the Workbench resolution, with the `not_representable` flag.
- The memberships of partitions that are never admissible are not stored, only their count.
