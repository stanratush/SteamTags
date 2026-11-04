# Domain-width sensitivity to the scan step
Type: task
Status: resolved
Blocked by:

## Question

Are the Null Comparison's domain widths, and its "observed wider than k of K" count, stable when the γ scan is finer than 0.05? Null median widths of 0.03–0.19 are near the step. Decided in [Which sensitivity checks run, and as one-off studies or in-app?](05-sensitivity-checks-and-scope.md).

Do (AFK):
- **Script:** goes in `prototypes/10-scan-step/` and takes the Build path and the pairs as arguments.
- **What to rescan:** on Build `20261008T221504Z-7a23ae9f`, at the 8 distinct validated pairs, rescan the observed network and **all 100 nulls** (rebuilt from the stored replicate seeds).
- **Steps:** 0.025 and 0.01. If the exact-γ_obs runs of [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md) are implemented by then, add them. Otherwise note that they are absent.
- **Budget:** about 1 h of compute.

Record:
- **Per pair and step:**
  - the observed domain width;
  - the null median width;
  - "observed wider than k (equal to t) of K";
  - whether the Selected Partition changes.
- **The guide's quote:** a sentence dated "on the Build of 2026-10-08".
- **A follow-up if needed:** if any pair's verdict moves materially, open a follow-up ticket on the default `gamma_step`. That would be a records change.

## Answer

Done 2026-11-04 (AFK) on Build `20261008T221504Z-7a23ae9f`. Script, rule, results and full tables: [prototypes/10-scan-step/](../prototypes/10-scan-step/README.md).

**What ran**
- All 9 stored validations at the 8 distinct pairs ran: rpg 7/5, puzzle 12/2, puzzle 14/2 (at min multi 2 and 3, sharing their networks and null seeds), puzzle 11/5, overall 12/2, overall 17/2, strategy 14/2 and simulation 14/5.
- At each pair, the observed network and all 100 nulls (from the stored stream-4 seeds) were rescanned at γ steps 0.05, 0.025 and 0.01. The scans used the app's own `scan_gammas`, `leiden_scan` with the 10 scan seeds, CHAMP and the Selected Partition rule.
- It made 2424 network scans in 1733 s on 12 workers.
- **Determinism:** the 0.05 rerun reproduces all 900 stored null widths and all 9 observed Selected Partitions and widths exactly.
- **The exact-γ_obs runs are absent.** The runs of [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md) are not implemented. The envelope-only Q count was recorded as a by-product.
- **0.025 is not an even grid in the app.** `scan_gammas` rounds to 2 decimals, so it scans 0, 0.03, 0.05, 0.08, … The study ran it as the app would.
- **The rule was set before the run** (README): a move is material if the Selected Partition changes, the observed width falls on the other side of the null median, or k/K moves by 0.10 or more.

**Result**

| Pair | observed width (0.05 / 0.025 / 0.01) | null median width | observed wider than k of K |
|---|---|---|---|
| rpg 7/5 | 0.269 / 0.269 / 0.269 | 0.185 / 0.172 / 0.172 | 79/100 → 86/100 → 88/100 |
| puzzle 12/2 | 0.109 / 0.105 / 0.104 | 0.057 / 0.047 / 0.040 | 64/66 → 65/68 → 68/69 |
| puzzle 14/2 (min multi 2) | 0.092 / 0.092 / 0.092 | 0.065 / 0.063 / 0.061 | 90/100 → 94/100 → 95/100 |
| puzzle 14/2 (min multi 3) | 0.092 / 0.092 / 0.092 | 0.051 / 0.046 / 0.044 | 92/95 → 94/95 → 94/95 |
| puzzle 11/5 | 0.145 / 0.145 / 0.145 | 0.144 / 0.140 / 0.131 | **50/100 → 54/100 → 61/100** |
| overall 12/2 | 0.088 / 0.088 / 0.075 | 0.060 / 0.053 / 0.046 | 91/100 → 94/100 → 92/100 |
| overall 17/2 | 0.158 / 0.158 / 0.158 | 0.049 / 0.040 / 0.040 | 70/70 → 73/73 → 73/73 |
| strategy 14/2 | 0.260 / 0.260 / 0.260 | 0.062 / 0.055 / 0.052 | 100/100 throughout |
| simulation 14/5 | 0.469 / 0.469 / 0.469 | 0.105 / 0.098 / 0.087 | 100/100 throughout |

- **The observed Selected Partition never changes.**
  - The observed width is identical at 7 of 9 runs.
  - It narrows at puzzle 12/2 (0.109 → 0.104) and overall 12/2 (0.088 → 0.075 at 0.01), where a finer scan finds a partition that cuts the domain. γ_obs shifts by at most 0.007 there.
  - No observed domain is clipped at γ_end.
- **The null widths shrink.**
  - At 0.01, 46–77 nulls per pair narrow and 5–21 widen; a widening happens when the old winner's domain is cut and another partition wins.
  - The null median falls by 3–30%; puzzle 12/2 falls most, from 0.057 to 0.040.
  - Up to 5 more nulls gain a Selected Partition: K rises at puzzle 12/2 (66 → 69) and overall 17/2 (70 → 73).
- **The count leans conservative at 0.05.** The share k/K changes by −0.01 to +0.11, and the observed never falls below the null median.
- **The Q count never moves:** 0 of 100 nulls reach the observed Q at every pair and step.
- **Cost:** 0.025 takes 2.0× and 0.01 takes 5.9× the scan time of 0.05.

**Material by the pre-set rule: yes, at one pair.**
- **puzzle 11/5's k/K moves by +0.11 at 0.01** (50 → 61 of 100). Its observed width sits at the null median, so a small narrowing of the nulls moves many of them below it.
- **rpg 7/5 moves +0.09**, just under the threshold.
- Every other pair moves by at most 0.05.

So a follow-up opens: [Should the default γ step be finer than 0.05?](12-default-gamma-step.md).

**Guide quote** (for the sentence "widths are upper bounds, conditional on the partitions the γ scan finds", decided in [Which sensitivity checks run, and as one-off studies or in-app?](05-sensitivity-checks-and-scope.md)): "On the Build of 2026-10-08, rescanning at a γ step of 0.01 instead of 0.05 left every observed Selected Partition unchanged and narrowed the median null domain width by 3–30%. The observed width was then wider than up to 11 more of the 100 shuffled networks." The wording may change if the follow-up changes the step.
