# Does the fixed-γ arm optimise at the observed resolution?
Type: grilling
Status: resolved
Blocked by:

## Question

The null's Q(γ_obs) and the subsample's at-resolution partition are read from each replicate's own CHAMP envelope. Beyond the replicate's `gamma_end`, `envelope_partition` extrapolates the envelope, and a test pins that. Extrapolation underestimates the null's Q, which makes the comparison anti-conservative.

On the 9 stored runs no replicate is beyond its scan (scan end ≥ 4.75, γ_obs ≤ 2.01). Inside the scan, both sides are envelope values from the same grid and seeds. See [Verified review](../research/01-verified-review.md) item 7.

Decide between:
- (a) marking `beyond_scan` as undefined, with no new runs;
- (b) also running Leiden at the exact γ_obs with the scan seeds in the observed network and every replicate, adding those partitions before the envelope (≈ 10 extra runs per replicate; new replicate calculations);
- (c) both.

Also decide whether the observed side must change in step, to keep the comparison symmetric.

## Answer

Decided by grilling with the researcher, 2026-11-04. Evidence:
- [Verified review](../research/01-verified-review.md) item 7.
- The stored grid: 931 graphs with a Selected Partition. The highest Selected Resolution ÷ scan end is 0.378 (γ 1.43 on 21 edged tags, scan end 3.80).
- γ_max(K) = 1.00, 1.24, 1.40, 2.19, 3.65 at K = 2, 4, 5, 10, 20.
- A measurement on the 5 default pairs, the observed network plus 10 nulls each: Leiden at exactly γ_obs with 10 and 50 extra seeds, against the scan envelope (`fixed_gamma.py`, session scratchpad).

**Measured**

| Pair | γ_obs | Observed Q | Observed gain (+10 / +50 seeds) | Largest null gain (+10 / +50) | Highest null Q | Gap from observed to highest null |
|---|---|---|---|---|---|---|
| overall 17/2 | 1.151 | 0.0667 | 0 / 0 | 0 / 0.00056 | −0.0091 | 0.076 |
| puzzle 14/2 | 1.092 | 0.0910 | 0 / 0 | 0.00039 / 0.00103 | 0.0101 | 0.081 |
| rpg 7/5 | 2.006 | 0.1508 | 0 / 0 | 0 / 0.00013 | 0.0607 | 0.090 |
| strategy 14/2 | 1.009 | 0.1583 | 0 / 0 | 0.00018 / 0.00125 | 0.0486 | 0.110 |
| simulation 14/5 | 0.865 | 0.3032 | 0 / 0 | 0.00010 / 0.00067 | 0.1600 | 0.143 |

The envelope understates a null's Q at γ_obs by at most 0.0013, about 1% of the smallest gap. That favours the observed network, as review item 7 warned, but negligibly. The subsamples' at-resolution partitions were not measured.

**Decisions**
- **No extrapolation.** When γ_obs lies beyond a replicate's own scan end:
  - the null's Q at γ_obs is undefined, with reason `beyond_scan`;
  - the subsample's at-resolution arm is degenerate, also `beyond_scan`;
  - both are counted under the undefined or degenerate rules, never scored.

  `envelope_partition` no longer reads past the scan end. A subsample would need to drop to about 5 edged tags out of 21 for this to happen, so it is a guard, not a live case.
- **Explicit runs at γ_obs.** Leiden runs at exactly γ_obs with the **10 scan seeds**: once on the observed network, and once in every null and every subsample, in both arms. The fixed-γ figures come from the scan envelope plus these runs. There is no new seed stream, and the cost is about 10 runs per replicate against roughly 1,000 or more in the scan.
- **They feed the fixed-γ arm only.** The runs are used only for the null's Q at γ_obs and the subsample's at-resolution partition. They never enter any network's own scan, CHAMP, γ̂ or Selected Partition rule, so every network keeps the identical procedure (ticket 07, Karrer et al. 2008).
- **Equal effort on both sides, and the Selected Partition is never changed by validation.** The observed network and every replicate get the same γ and seeds. Validation never changes the Selected Partition or the Selected Resolution. If the observed side's runs found a higher Q at γ_obs, that Q would serve only as the observed side of the Null Comparison, with a note. It never did on the default pairs.
- **Records keep both values.** Each replicate stores its envelope-only Q and its final Q at γ_obs (and, for subsamples, whether the at-resolution partition changed), so the residual can be reported from any run.
- **The text states the residual**, for example: "Q at γ_obs is the best of the scan and 10 runs at γ_obs; on the default pairs, 50 seeds raised a null's Q by at most 0.0013."

**Hand-offs**
- To [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md):
  - the extra runs and the stored values are a records change, which joins ticket 01's rerun;
  - regression cases: `beyond_scan` (replacing the `gamma_end + 1` extrapolation test); the extra runs never change a replicate's Selected Partition; observed and replicate sides use identical γ and seeds.
- To [What does the Null Comparison state, and by which rule?](04-null-comparison-rule-and-wording.md):
  - `beyond_scan` is one cause of an undefined null Q;
  - the residual sentence;
  - the note when the observed side's runs beat the Selected Partition's Q.

## Comments

- 2026-11-05, spec: a subsample gets **one** run set at γ_obs, which serves both arms ("in both arms" above). Both arms share the subsample's network, so a second set would repeat the first; only the at-resolution arm reads it. The observed network's run is stored in the validation file, not in the grid's graph result, so the grid key is untouched. See the spec's "Resolved while writing this spec".
