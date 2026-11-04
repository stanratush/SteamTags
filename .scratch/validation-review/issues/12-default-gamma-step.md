# Should the default γ step be finer than 0.05?
Type: grilling
Status: resolved
Blocked by: 10

## Question

[Domain-width sensitivity to the scan step](10-scan-step-width-sensitivity.md) found a material move under its pre-set rule. At puzzle 11/5, "observed wider than k of K" goes from 50/100 at step 0.05 to 54/100 at 0.025 and 61/100 at 0.01. rpg 7/5 moves +0.09, and every other pair moves by at most 0.05.
- Across all 8 pairs, no observed Selected Partition changes, and the Q count never moves.
- Null median widths fall by 3–30%, while observed widths barely move.
- So 0.05 understates how distinctive the observed width is, rather than overstating it.

Decide whether the default `gamma_step` (`config.py`, `[parameter_selection]`, 0.05) changes, and to what. Weigh:
- **Reach:** `gamma_step` is in `grid_key()`, so changing it recomputes every Parameter Grid and validation, and every shipped App Bundle. It may move the Automatic Parameter Selection's chosen pair, which was not measured. This reopens the step choice of the Automatic Parameter Selection map ([Graph-specific γ scan](../../auto-parameter-selection/issues/16-graph-specific-gamma-scan.md)).
- **Cost:** 2.0× (0.025) or 5.9× (0.01) the scan time, for the grid and for every validation replicate.
- **0.025 is uneven.** `champ.scan_gammas` rounds γ to 2 decimals, so 0.025 scans 0, 0.03, 0.05, 0.08, … A 0.025 step needs that rounding changed. The Workbench's two-decimal γ is unaffected.
- **Options:**
  - keep 0.05 and rely on the guide's "widths are upper bounds, conditional on the scan" sentence plus the study's quote (ticket 05 decided that sentence anyway);
  - change the default step;
  - use a finer step for the Null Comparison's scans only. The observed must then be rescanned too, so the Selected Partition and γ_obs might no longer match the grid's.
- **Interaction with versioning:** any change is a records change for [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md).

## Answer

Decided by grilling with the researcher, 2026-11-04, on the evidence of [Domain-width sensitivity to the scan step](10-scan-step-width-sensitivity.md). Facts checked: `champ.scan_gammas` rounds to 2 decimals (`champ.py:43`), `config.py:471` only checks `gamma_step > 0`, and the grid takes 329 s on 12 workers at 0.05 ([16-remeasure](../../auto-parameter-selection/prototypes/16-remeasure/results.md)).

**The default `gamma_step` stays 0.05.**
- At 0.05 the bias is a property of a finite scan, and it leans conservative.
  - No observed Selected Partition moved at any step, and the Q count never moved.
  - The one material move (puzzle 11/5, 50 → 61 of 100 at 0.01) understates how distinctive the observed width is. It never overstates it.
- No finite step reaches a settled width. Between 0.025 and 0.01 the null medians were still falling (puzzle 12/2: 0.047 → 0.040), so a finer step only moves a figure that stays conditional on the scan.
- 0.02 (the next even two-decimal step) and 0.01 were weighed and rejected. Either would recompute every Parameter Grid, validation and App Bundle, at about 2.5× or 5.9× the cost. Either could also move the Automatic Parameter Selection's chosen pair, which was never measured.
- So the step choice of [Graph-specific γ scan](../../auto-parameter-selection/issues/16-graph-specific-gamma-scan.md) is **not reopened**.

**Out of scope:** a finer step for the Null Comparison's scans only. A fair comparison would rescan the observed network at that step too, and the rescan can yield a γ_obs, or in principle a Selected Partition, that differs from the one the grid and the Workbench show. That strains [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md)'s rule that validation never changes the Selected Partition, and it would add a second step setting to config and to the validation key.

**Straight fix for the spec**
- `config.py` rejects a `gamma_step` that is not a whole multiple of 0.01 with a `ConfigError`. Without the guard, 0.025 runs silently as the uneven grid 0, 0.03, 0.05, 0.08, … The Workbench is two-decimal too.
- A test case covers it: `gamma_step = 0.025 → ConfigError`.

**Guide wording**
- Ticket 10's guide quote stands as written, and its "may change if the follow-up changes the step" caveat drops.
- In the guide only, a clause follows ticket 05's sentence "widths are upper bounds, conditional on the partitions the γ scan finds": "so the count of shuffled networks the observed outwidths tends to understate, not overstate, how distinctive its width is."
- The card keeps ticket 05's sentence unchanged and makes no direction claim. That direction is an empirical finding on one Build, not a guarantee.

**Rerun on the new Build** (next to ticket 05's rerun item in the spec). The scan-step study carries a pre-set rule:
- **The default step reopens** if any observed Selected Partition changes, an observed width crosses to the other side of the null median, or k/K **falls** by 0.10 or more at 0.01. It reopens as a fresh question on the Automatic Parameter Selection side, not on this map.
- **Otherwise only the guide quote's figures are updated.** That includes a large rise in k/K, like puzzle 11/5's.

**For [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md)**
- This ticket causes no records or summary version bump.
- The config guard changes nothing stored, because every stored setting uses 0.05.

No new glossary term and no ADR: keeping a default is not surprising.
