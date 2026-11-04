# Domain-width sensitivity to the scan step
Type: task
Status: open
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
