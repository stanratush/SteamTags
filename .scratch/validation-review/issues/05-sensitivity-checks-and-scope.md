# Which sensitivity checks run, and as one-off studies or in-app?
Type: grilling
Status: resolved
Blocked by:

## Question

Four method checks are open. See [Verified review](../research/01-verified-review.md) items 8, 11, 16 and 17.

- **Mixing:** [Validation methods](../../auto-parameter-selection/research/02-validation-methods.md) checked 10 trades per game on 5 grid cases of one Build, not at the chosen pairs (g = 12–17, mostly s = 2). Add a per-replicate perturbation share to the records? Rerun `mixing_check.py` at the chosen pairs?
- **Subsample fraction:** test alternatives to 80%? A fraction curve is listed under **Out of scope** in the [Automatic Parameter Selection map](../../auto-parameter-selection/map.md), so this needs an explicit scope decision. Separately, the s′ = 2 clamp makes the relative edge threshold stricter at s = 2 (2/80 vs 2/100), and 5 of 9 validated pairs have s = 2. Document only, or measure?
- **Scan step:** CHAMP widths are upper bounds conditional on the partitions discovered. Null median widths of 0.03–0.19 are near the 0.05 step. Rescan the observed network and ~10 nulls per chosen pair at step 0.025 and 0.01?
- **Selection effect:** the pair is chosen on the same data. Measure how much that inflates Subsample Stability, or only state the limitation? A full-pipeline null costs ≈ 9 h per dataset.

For each one decide:
- in scope or not;
- one-off study (a `task` ticket, results quoted in the guide) or in-app feature;
- its budget.

## Answer

Resolved 2026-11-04 by grilling with the researcher.

Facts used:
- A replicate takes about 0.7 s (validation pilot), and a whole validation about 3 min on 12 workers.
- A mixing case takes 32–89 s for 100 chains × 200 trades (Research 02).
- `mixing_check.py` is lost. It was in an old session's scratchpad.
- The 9 stored validations cover 8 distinct pairs, and 5 of them have s = 2.

| Check | In scope? | Form | Budget |
|---|---|---|---|
| Selection effect | No measurement | Limitation sentence only (ticket 04) | none |
| Mixing: perturbation share | Yes | **In-app** record, in the export and the guide | ≈ 0 (the records are recomputed anyway) |
| Mixing: chain check at the validated pairs | Yes | One-off: [Mixing check at the validated pairs](08-mixing-check-at-validated-pairs.md) | < 1 h compute |
| Subsample fraction | No | Stays at 80%; the curve stays out of scope | none |
| s′ clamp at s = 2 | Yes | The guide documents the direction, plus a one-off: [Threshold clamp bracket at s = 2](09-threshold-clamp-bracket.md) | ≈ 10 min compute |
| Scan step | Yes | A card and guide sentence, plus a one-off: [Domain-width sensitivity to the scan step](10-scan-step-width-sensitivity.md) | ≈ 1 h compute |

**The selection effect is not measured.** [What does the Null Comparison state, and by which rule?](04-null-comparison-rule-and-wording.md) already ruled out the full-pipeline null and added the limitation sentence. A cheaper probe is ruled out too: about 10 subsamples, each re-running the grid and the pair choice, at about 55 min per dataset. Ten replicates would give too noisy an estimate of what is probably a small optimism.

**Perturbation share (in-app).**
- **What is recorded:** every null record carries the share of observed 1-cells that the Curveball moved, which is Strona's diagnostic. It is a new replicate field, so the records version covers it. The replicates are recomputed anyway for Whole-Cluster Jaccard and the exact-γ runs.
- **Where it appears:** in `validation_replicates.csv`, plus one sentence in the guide's Null Comparison section.
- **Not on the card:** it is a diagnostic, like the edge ratio.
- **No threshold or warning:** nothing tells us where too little mixing starts.

**The subsample fraction stays at a single 80%.** The Automatic Parameter Selection map's "curve of subsample fractions" stays out of scope. This effort does not reopen it.

**The s′ = 2 clamp.**
- **What the guide documents:** at s = 2, the subsample's edge threshold is 2/80 = 2.5% of the games, not the proportional 2%. That is stricter, while g′ is looser. Those subsample networks are therefore sparser in edges than a proportional design would make them.
- **The bracket study:** a one-off study brackets the proportional 1.6. At a fixed m = 80 it runs s′ = 1 (1.25%) next to the stored s′ = 2 (2.5%). The guide quotes how many labels the clamp moves.
- **The app doesn't change**, whatever the bracket shows.
- **m = 90 is rejected.** It changes the fraction and the threshold together.

**Scan step.**
- **A new sentence, whatever the study shows:** the card's width sentence and the guide gain "widths are upper bounds, conditional on the partitions the γ scan finds".
- **The Q comparison no longer depends on the step:** [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md) runs Leiden at exactly γ_obs. So the study measures widths only.
- **A follow-up only if a verdict moves:** if a pair's "observed wider than k of K" verdict moves materially, a follow-up ticket decides the default `gamma_step`. That would be a records change.

**Common to the three one-off studies (`task` tickets, AFK).**
- **Build and pairs:** they run on Build `20261008T221504Z-7a23ae9f` at the 8 distinct pairs of the 9 stored validations. The clamp study uses the 5 s = 2 pairs.
- **Scripts:** they go in `prototypes/NN-<slug>/` and take the Build path and the pairs as arguments, so they can be rerun.
- **Guide quotes** say "on the Build of 2026-10-08".
- **The new Build:** a new Build is coming. **The spec lists rerunning the three scripts on it as a follow-up**, done by hand (about 75 min of compute).
- **Not run at bundle time.** Running the studies inside `steamstudy bundle`, so that they ship with each Build, was rejected:
  - three scripts would become production code (keys, versions, tests, bg strings);
  - bundling would take about 75 min longer per Build;
  - the app would need a display for checks that are expected to pass.

  [Bundle-shipped results](../../auto-parameter-selection/issues/13-bundle-shipped-results.md) already recomputes the validation itself, perturbation share included, for every Build a bundle carries.

**No prior decision is reopened.** [Validation design](../../auto-parameter-selection/issues/07-validation-design.md)'s single 80% fraction stands, and so does the out-of-scope fraction curve on the Automatic Parameter Selection map.

**Glossary:** CONTEXT.md gains **Perturbation Share**.
