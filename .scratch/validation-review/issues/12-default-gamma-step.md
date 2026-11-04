# Should the default γ step be finer than 0.05?
Type: grilling
Status: open
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
