# What does the Null Comparison state, and by which rule?
Type: grilling
Status: resolved
Blocked by:

## Question

Five problems, from [Verified review](../research/01-verified-review.md) items 2, 3, 8, 9, 10, 12 and 19:
- The verdict "Q not above the null" fires when ≥ 1 replicate reaches the observed Q. That is the strictest rule and depends on R (reach 0 ⇔ Monte Carlo p ≤ 1/(R+1)), but it is unstated.
- Undefined null Q, from edgeless shuffles, crashes the card when every replicate has it (a TypeError in `_signed`), and otherwise stays in the denominator.
- The guide says reaching Q means the Clusters "are no more than what the counts produce".
- Null Multi-Tag Cluster counts are computed but not shown.
- "Same procedure" reads as the whole pipeline.

Decide:
- The three verdict states (above all defined, reached, undefined) and their exact wording, in the card and the Inspector badge.
- Whether the rule is stated as a count only, or with the Monte Carlo p bound. This reopens [Validation design](../../auto-parameter-selection/issues/07-validation-design.md)'s "no p-value".
- The replacement for the over-strong guide sentence (`docs/user-guide/03-metric-reference.md:2114`).
- Which null figures the card shows: Multi-Tag Clusters (observed vs median and range), resolution, edge ratio.
- The domain-width sentence: "median domain width", fixed precision, handling of equality and ties.
- How the module docstring, guide, methods paragraph and CONTEXT.md name the scope: "the per-pair procedure at the chosen pair", not the grid or the Neighbour Agreement choice.

## Answer

Resolved 2026-11-04 by grilling with the researcher. Every change below is **summary-only**: it is derivable from the stored records and needs no new replicate calculations.

**Verdict: three states, computed over the D replicates with a defined Q.** R = D + U, where U is the replicates whose Q is undefined: `no_edges`, plus `beyond_scan` from [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md). The summary carries `q_defined = D`. A three-valued `verdicts.null_q` (`above_all_defined` / `reached` / `undefined`) replaces the boolean `q_not_above_null`. Reaching means ≥, as today.

| State | Condition | Card, after "Q at resolution 1.151 is 0.067;" | Inspector badge |
|---|---|---|---|
| above all defined | D ≥ 1, reach = 0 | "none of the D shuffled networks with a Q reaches it (range over D shuffled networks: −0.021 to −0.012)." | "Q above all D shuffled networks" |
| reached | reach ≥ 1 | "k of D shuffled networks with a Q reach it: Q not above the null." | "Q not above the null (k of D)", with the help link |
| undefined | D = 0 | "no shuffled network has a Q ({reasons}), so Q cannot be compared." With edgeless nulls only: "no shuffled network has edges, so Q cannot be compared." | "Null Q undefined" |

- When U > 0 in the first two states, the reasons follow the way degenerate subsamples are reported ("; 3 had no edges").
- **There is no minimum D.** D is always printed. When D < R/2 the card adds "Most shuffled networks have no Q (U of R), so this comparison is weak", and the badge gets a "⚠" suffix. This matches the B* flag in [How does tag loss count in Cluster recovery?](01-tag-loss-in-cluster-recovery.md).
- **"Shuffled networks" is the one user-facing term.** The badge's "null replicates" goes.
- This settles the wording of the review's straight bugs #2 (the TypeError) and #3 (the denominator).

**The rule is stated as a count only.** The rule is "at least one of the D shuffled networks with a Q reaches the observed Q". [Validation design](../../auto-parameter-selection/issues/07-validation-design.md)'s "no p-value" is **kept**, and the guide now gives two reasons:
- **The bound would only be nominal.** γ_obs and the pair are chosen on the observed data, so the observed Q_X(γ(X)) is not exchangeable with the nulls' Q_Xr(γ(X)), and a Monte Carlo bound p ≤ 1/(D+1) would only be nominal. One rpg null reached 0.129 against 0.131 at its own resolution.
- **Its dependence on R is stated instead.** With 100 networks, "none reaches it" is the strongest result the comparison can give.

**The guide's over-strong sentence** (`03-metric-reference.md`, Null Comparison, "Why it matters here") becomes: "If shuffled networks reach the same Q at the same γ, Q gives no evidence of structure beyond what the tag and game counts produce. Q is one number for the whole partition: a shuffled network can reach it with entirely different groups, and not exceeding the null is absence of evidence, not evidence of absence." The rule paragraph in the same section changes to the D denominator and the three states. The bg catalogue mirrors both.

**Null figures on the card:**
- **Multi-Tag Clusters are added.** The card shows "Multi-Tag Clusters: observed 7, median 5 (range over k shuffled networks with a Selected Partition: 3 to 9)".
- **Selected Resolution and the edge ratio go to the export and the guide only.** A null's own resolution is not comparable to γ_obs, and the edge ratio is a diagnostic.
- **Layout** is left to [How should the validation card and the Inspector's Validation section look?](06-validation-card-and-inspector-layout.md).

**The domain-width sentence** becomes "median domain width 0.049 vs observed 0.158; observed wider than 79 of 79".
- Precision is fixed at `.3f`.
- The narrower/wider side word goes, since it describes the median.
- Ties are exact float equality, counted apart only when present: "wider than 76, equal to 3, of 79".

**Scope phrase:** "**the per-pair procedure at the same Threshold Pair** (its own γ scan, CHAMP, γ̂ and the Selected Partition rule), not the Parameter Grid or the choice of pair".
- **"Chosen pair" is not used.** Validate runs on any inspected pair with a Selected Partition (`02-app-controls.md`).
- **The phrase is used everywhere.** It goes into the module docstring, the methods paragraph ("each analysed by the identical procedure"), the guide, and CONTEXT.md's Null Comparison and Subsample Stability entries.
- **The card header** becomes "(100 shuffled networks, per-pair procedure at g = 12, s = 2)".
- **A limitation sentence is added:** "The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no part in the choice, so the Null Comparison is barely affected."
- **The full-pipeline null is out of scope.** Measuring the selection effect that way (≈ 9 h per dataset) is ruled out on the map.

**Glossary:** CONTEXT.md gains **Q not above the null**. The Null Comparison entry now says "the per-pair procedure at that Threshold Pair", and the Subsample Stability entry says "the same per-pair procedure".
