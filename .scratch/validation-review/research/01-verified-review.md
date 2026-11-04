# Verified review of the Validation feature (2026-11-04)

Scope: the 23 reported issues (the list skips 5), checked against `bilingual-cluster-views` at `964e889` and against the **9 stored validations** (all `ps-validation-1`, R = S = 100) in `builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f/app_cache/parameter_selection/validation/`. Nothing in the code was changed. The mining script is in the session scratchpad (`mine.py`). Its output is summarised below.

Verdicts: **Confirmed** (the defect is in the code and shows in current results), **Latent** (it is in the code, but no stored result triggers it), **Partly** (the claim is partly right or overstated), **Design conflict** (the issue reopens a decision that is already recorded).

## Evidence from the stored runs

| Pair | γ_obs | min null / sub scan end | null Q undefined | absent Clusters | Clusters "Dissolved" (re-sel.) | mean > 0.5 but dissolved in ≥ 50% of B* |
|---|---|---|---|---|---|---|
| rpg 7/5 | 2.006 | 9.75 / 10.10 | 0 | 0 | 6 of 15 (sizes 4,4,3,3,2,2) | C7 (0.543, 52/100) |
| puzzle 12/2 | 1.244 | 6.60 / 6.05 | 0 | 0 | 0 of 6 | C3 (0.562, 52/92), C6 (0.506, 66/92) |
| puzzle 14/2 (min-multi 2) | 1.092 | 5.15 / 5.05 | 0 | 0 | C3 (0.490), C4 | — |
| puzzle 14/2 (min-multi 3) | 1.092 | 5.15 / 5.05 | 0 | 0 | C4 only: **C3 = 0.515** | C3 (0.515, 67/100) |
| puzzle 11/5 | 1.520 | 6.70 / 6.60 | 0 | 0 | C7 (size 3), C8 (size 2) | C4 (0.576, 51/100) |
| overall 12/2 | 1.122 | 6.70 / 6.70 | 0 | 0 | C4 (size 3) | — |
| overall 17/2 | 1.151 | 4.90 / 4.75 | 0 | 0 | C4 | — |
| strategy 14/2, simulation 14/5 | ≤ 1.01 | ≥ 5.55 | 0 | 0 | 0 | — |

- Monte Carlo s.e. of a mean Jaccard is 0.007–0.029 (sd/√B*). The two puzzle 14/2 runs differ only in `min_multi_tag_clusters`, which changes selection inside the replicates. Their at-resolution arms are identical, as they should be. In the re-selected arm, C3 is Dissolved in one run (0.490) and not in the other (0.515), a difference of about 1.3 s.e.
- Every Cluster the mean rule calls Dissolved has 2–4 tags, except puzzle C3 (8).
- Null Q at γ_obs never comes close: the null maximum is 0.01–0.17 against an observed 0.07–0.30, and reach = 0 in all 9 runs.
- Retention averages 0.92–1.00. Single-tag survival occurs (rpg C14, size 2: 9 of 100). J = 1 despite lost tags occurs up to 44 of 100 times (simulation C1, at resolution).
- The chosen pairs have s = 2 in 5 of 9 runs, so s′ = max(2, ⌊1.6⌋) = 2.

## Bugs and misleading results

### 1. The heatmap can collapse. **Confirmed (by CSS analysis; reproduce in the browser while fixing)**
- `.main{display:flex;flex-direction:column;min-height:0}` with `.ps-main{overflow:auto}` (`assets/app.css:87,401`). The heatmap has only `style={"height": "460px"}` (`ps_view.py` `mode_layout`).
- Flex items default to `flex-shrink:1`. A responsive Plotly graph's min-content height is about 0, because its SVG is absolutely positioned and sized in percentages. The text panels' min-content is their text. So when the column overflows, all the shrinkage lands on the heatmap. Plotly then either redraws it smaller or paints past its box onto `ps-why`.
- **Fix:** `#ps-heatmap{flex:0 0 460px}` (or `flex-shrink:0; min-height:460px`). For safety, give every direct child of `.ps-main` `flex-shrink:0`, since the column scrolls anyway. Add a layout test for `flex-shrink` on the heatmap if the CSS tests allow it.

### 2. A card with no defined null Q crashes. **Latent, confirmed in the code**
- `null_replicate` leaves `q_fixed` as None only when the shuffled network has no edges (`validation.py:138-142`). With every replicate edgeless, `qs = []`, `_spread` returns None values, `reach = 0`, and `null_sentences` takes the "no shuffled network reaches it" branch. It then calls `_range` → `_signed(None)` → `format(None, ".3f")`, which raises a **TypeError** (`selection_text.py:204-205,234`).
- The Inspector badge reads `q_not_above_null` False and prints "Q above all null replicates" (`ps_view.py:790-792`) even though no replicate had a Q.
- This needs a null with no edges at all. Curveball keeps tag degrees, so that only happens at high s on sparse tags. No stored run has it.
- **Fix:** give the verdict three states: `above_all_defined` / `reached` / `undefined` (no defined Q), and carry `q_defined = len(qs)` in the summary. The text says "no shuffled network has edges, so Q cannot be compared", and the badge says "Null Q undefined".

### 3. Undefined null Q stays in the denominator. **Latent, confirmed in the code**
- `reach` counts over `qs`, but the text prints "{reach} of {r}" with `r = replicates` (`selection_text.py:232`). "No shuffled network reaches it" also holds silently when some replicates had no Q.
- **Fix:** use `q_defined` as the denominator ("k of D defined, U without edges"). Report undefined replicates the way degenerate subsamples are reported.

### 4. A Cluster absent from every subsample gets no warning. **Latent, confirmed in the code; the test pins it**
- `dissolved = mean is not None and mean <= 0.5` (`validation.py:268`). A Cluster with `present = 0` therefore has mean None and dissolved False, and the card can say "No Multi-Tag Cluster is dissolved". `test_hennig_jaccard_on_the_comparison_set` asserts `(None, 1, 0, False)`.
- A Leiden Cluster is connected, so all of its tags have edges and are in the comparison set whenever they are present. Absence therefore means that every tag fell below g′. No stored run has it (absent = 0 everywhere).
- The same gap applies, more mildly, to a Cluster present in very few subsamples: a mean over B* = 3 is reported like a mean over 100.
- **Fix:** add a status, "Not assessable" (absent in every subsample, or B* under a stated minimum), shown instead of a blank. The "No Multi-Tag Cluster…" sentence must not appear while any Cluster is unassessable. Report absence as its own frequency (absent k of S). The verdict wording itself is decided in ticket 01.

## Method and interpretation

### 6. Conditional Jaccard can hide cluster loss. **Confirmed; the effect is small on current data**
- `compare` restricts C to the surviving tags C′ (`validation.py:179-184`). This follows Hennig: in his subsetting scheme the *clustered objects* are resampled, so C ∩ X* is a design choice and is uninformative about the cluster. Here the resampled units are **games**, while the clustered objects are **tags**. A tag drops out because it falls below g′, which is an *outcome* of the perturbation, not of the design. Conditioning on survivors therefore discards evidence of instability.
- A survivor set of 1 tag scores 1/|D′|, which is 1.0 when that tag stands alone. That gives no information about co-membership, yet it is averaged in as perfect.
- Data: mean retention is 0.92–1.00, and single-tag survival is rare (9 of 100 at most, in a 2-tag Cluster), so current verdicts barely move. Simulation C1 has J = 1 with lost tags in 44 of 100 subsamples.
- **Fix (decide in ticket 02):** keep Hennig's conditional J as the headline and report retention next to it (already stored). Add an *unconditional recovery* J_full = |C ∩ D′| / |C ∪ D′|, where missing tags count as unrecovered, and treat |C′| < 2 as "not assessable" for that replicate. J_full cannot be rebuilt from stored records (it needs |D′|), so it requires new replicate calculations.

### 7. The fixed-γ arm can miss better partitions. **Partly; the extrapolation path is never used**
- `envelope_partition` extends the envelope past `gamma_end` (`validation.py:99-104`), and a test exercises `gamma_end + 1`. Beyond the replicate's scan, finer partitions were never searched, so the null's Q(γ_obs) would be a *lower* bound. That makes the Null Comparison anti-conservative, and for subsamples it picks a stale partition.
- In practice the scan end is γ_max(n_e) ≥ 4.75 against γ_obs ≤ 2.01, so no replicate in the 9 runs is beyond its scan. Inside the scan, the comparison is like for like: the observed Q(γ_obs) is also an envelope value from the same grid and seeds (ticket 07: "both sides are the best of the scan").
- **Fix:** (a) minimum: when γ_obs > the replicate's `gamma_end`, record `q_fixed` as undefined with reason `beyond_scan` instead of extrapolating. (b) Optional and cheap: run Leiden at the exact γ_obs with the 10 scan seeds in every replicate *and* in the observed network, and add those partitions before taking the envelope. That is ~10 extra runs out of hundreds, and it keeps the two sides symmetric. (b) needs new replicate calculations. Decide in ticket 03.

### 8. Validation scope is ambiguous. **Confirmed (wording)**
- Replicates repeat the per-pair procedure (scan, CHAMP, γ̂, rule) at a fixed (g, s), or the scaled (g′, s′). They do not repeat the grid or the Neighbour Agreement choice (`validation_tasks`). The metric reference says so precisely ("the whole per-pair procedure"). The methods paragraph ("each analysed by the identical procedure") and the CONTEXT.md entry ("the same procedure") read as the whole pipeline.
- Scientific note: the pair was picked on the same data, so Subsample Stability is conditional on that choice. Neighbour Agreement rewards parameter stability, which plausibly correlates with data stability, so a small optimism is possible. Q played no role in the choice, so the Null Comparison is little affected. A full-pipeline null costs about 100 × the grid (≈ 9 h per dataset at 329 s per grid).
- **Fix:** name it "per-pair procedure at the chosen pair" in the methods paragraph, CONTEXT.md, the card and the module docstring, and add one limitation sentence. Whether to measure the selection effect is decided in ticket 04.

### 9. The null verdict uses an unstated decision rule. **Confirmed**
- `q_not_above_null = reach >= 1` (`validation.py:312`). With R = 100, reach 0 corresponds to a Monte Carlo p ≤ 1/(R+1) ≈ 0.0099 (Phipson & Smyth), and reach 1 to p = 0.0198. The rule is the strictest possible and depends on R, but nothing says so. Ticket 07 ruled out z-scores and p-values on purpose.
- On current data it is robust: the gap to the null maximum is enormous in every run.
- **Fix (ticket 05):** state the rule wherever the verdict appears: "at least one of the D shuffled networks with a Q reaches the observed Q". Optionally add the bound "(Monte Carlo p ≤ 1/(D+1))", which sits within ticket 07's no-p-value stance only if the stance is reopened.

### 10. The documentation asserts too much. **Confirmed**
- `docs/user-guide/03-metric-reference.md:2114` says that if shuffled networks reach the same Q, "the observed Clusters are no more than what the counts produce". Q is a single global scalar: a null can reach it with entirely different groups, and failing to exceed is absence of evidence.
- **Fix:** "If shuffled networks reach the same Q at the same γ, Q gives no evidence of structure beyond what the tag and game counts produce." Mirror it in the bg catalogue.

### 11. Shuffle mixing is unchecked. **Partly (overstated)**
- It was checked once: Research 02 ran 100 chains for 5 (dataset, g, s) cases spanning the grid, at 0.25–200 trades per game. By 10 trades per game every statistic (perturbation, C-score, edges, Q, Multi-Tag Clusters, memory slope) was within noise, and the memory slope was at its floor of about 0.005. TRADES_PER_GAME is also in the validation key.
- The gaps:
  - the check covered one Build, and none of the chosen pairs (g = 12–17, s = 2);
  - first- and pair-moment plateaus do not prove mixing (Research 02 says so);
  - nothing at run time records how far each replicate moved from the observed table.
- **Fix:** record a per-replicate **perturbation share** (the fraction of observed 1-cells moved) in the null record. It is cheap and is Strona's diagnostic. Show its range in the card or the export. Optionally rerun `mixing_check.py` at the five chosen pairs. Both need new replicate calculations, or a one-off study. Decide in ticket 04.

### 12. Null cluster counts are stored but not shown. **Confirmed**
- `summary["null"]["n_multi"]` (and `resolution` and `edges.ratio`) are computed but not shown. Only the export has `n_multi_tag_clusters`.
- This matters scientifically: existence of a Selected Partition barely separates observed from null (Peixoto; 66–100 of 100 nulls have one), so the number of Multi-Tag Clusters (observed 3–15, null median 3–13) is more informative. Show it with its range label (#18).

### 13. "Dissolved" misattributes the aggregation rule. **Confirmed, and it matters on current data**
- Hennig (2007 §2) justifies ≤ 0.5 *per resample* and suggests summaries by "the mean, or the number of dissolutions … or good recoveries (> 0.75)". Research 02 recommended reporting all three. Ticket 07 then made the cut-on-the-mean the verdict, and the code comment and the guide attribute that to Hennig.
- In the data the two disagree in 5 Cluster-runs: rpg C7 has mean 0.543 but is dissolved in 52 of 100 subsamples, and puzzle 12/2 C6 has mean 0.506 but is dissolved in 66 of 92, yet neither is "Dissolved".
- The table already shows the dissolution count ("≤ 0.5 in k of B*"). The recovery count (> 0.75) is not computed.
- **Fix (ticket 01):** report mean J, the dissolution frequency and the recovery frequency (> 0.75, quoted as Hennig's "say"). Then either drop the overall label or redefine it as an explicit, attributed study choice (for example "dissolved in most subsamples"). All of this can be rebuilt from stored records, since per-replicate Jaccard is stored.

### 14. Monte Carlo uncertainty is not shown. **Confirmed, and it matters on current data**
- The s.e. of the mean is 0.007–0.029. The same pair and data give 0.490 (Dissolved) in one run and 0.515 in the other (above).
- **Fix (ticket 01):**
  - Monte Carlo error: s.e. = sd/√B* for the mean, and a Wilson or Clopper–Pearson interval for k/B*.
  - Variability across subsamples: sd or p10–p90 of J_r. This spread *is* the stability.
  - Label them differently, and call neither a confidence interval about the population. The Top 100 is not a sample.
  - Everything can be rebuilt from records.

### 15. Cluster size is ignored when interpreting instability. **Confirmed**
- Of the 13 Cluster-runs called Dissolved, 12 have 2–4 tags (recounted in ticket 02). This is partly mechanical. A k-tag Cluster has few possible J values. When a small Cluster merges into a large D, its best match is |C′|/|D′|, which is small, while the large partner barely changes. A 2-tag Cluster split into singletons scores exactly 0.5 and is dissolved.
- Size is not displayed (`cluster_name` truncates to 3 members).
- **Fix:** add a size column, and optionally the number of retained tags. A one-off check of J against size and retention on the stored runs needs no rerun. Interpret labels for 2–3-tag Clusters with a caveat; whether to set a minimum size is decided in ticket 01.

### 16. The subsampling design needs justification. **Partly; a design conflict for alternative fractions**
- Resampling games is the right unit, because tag associations are estimated from games.
- A curve of subsample fractions is listed under **Out of scope** in the Automatic Parameter Selection map. Reopening it needs an explicit scope decision (ticket 04).
- The floor clamp is confirmed. With n = 100, m = 80 and s = 2, s′ = max(2, 1) = 2. Relative to the games, the edge threshold becomes 2/80 = 2.5% instead of 2%, which is *stricter*, while g′ is looser. 5 of 9 validated pairs have s = 2. So the subsample networks are sparser in edges than a proportional design gives, which biases those pairs' Subsample Stability downwards, or at least changes it. Research 02 chose the clamp because s′ = 1 makes every co-occurrence an edge, but the direction of its effect is not documented.
- **Fix:** document both directions. One-off sensitivity runs at s = 2 with s′ = 2 vs a fraction like m = 90 (where ⌊1.8⌋ still clamps) could be part of ticket 04.

### 17. Narrow domains need scan-step sensitivity. **Confirmed (as a gap)**
- CHAMP domains are exact among the *discovered* partitions. Adding a partition can only shrink the domains around it, so every width is an upper bound conditional on discovery. Null median widths of 0.03–0.19 are near or below the 0.05 step, so they are the most discovery-dependent.
- Ticket 05 measured selection sensitivity to the step on observed graphs only (80 vs 56 values: 720 of 765 unchanged), not width sensitivity on nulls.
- **Fix:** a one-off study rescanning the observed network and ~10 nulls per chosen pair at step 0.025 and 0.01, and comparing widths and the "wider than k of K" count (ticket 04). The in-app text should say widths are conditional on the scan.

## Text and layout

- **18. Unlabelled ranges. Confirmed.** `_ari_spread` prints p10–p90 with no label, and `_range` prints min to max with no label (`selection_text.py:200-202,252-254`). Fix: "(10th–90th percentile …)" and "(range over D shuffled networks …)", plus a guide note that neither is a confidence interval.
- **19. Domain-width comparison. Confirmed.**
  - Equality falls into "wider" (`side = narrower if median < observed else wider`).
  - The `.3g` formatting gives mixed precision: "0,0486 against 0,158" in the bg screenshot.
  - "narrower domains" describes the median.
  - Fix: "median domain width X vs observed Y", fixed `.3f`, an explicit "equal", and "wider than k of K" with ties counted separately.
- **20. Repeated dissolved lists. Confirmed** (`subsample_sentences` loops over both arms). Fix: give the shared list once ("in both arms"), then "only re-selected" and "only at resolution".
- **21. Long cluster table. Confirmed.** It has 2 × N rows, and the last column's header is `""` (`ps_view.cluster_table`). Fix: one row per Cluster with grouped column headers per arm, plus size, and a "Status" header. Use a layout that does not overflow the narrow form.
- **22. Smaller items. All confirmed.**
  - The card's title is a bold `P` with no help link.
  - "Dissolved: {n}" counts the re-selected arm only and does not say so.
  - The Validate button sits under Apply at the top of the Inspector, while the Validation section is at the bottom.
  - When custom constraints give `no_qualifying_pair`, `chosen_pair` is None, so the "Validation ran for … default constraints" note is skipped and the card shows the default pair without explanation.
  - Fix: an `H4` with `_help("selection.validate")`, "Dissolved (re-selected): n", the button moved into the Validation section, and a note branch for `chosen_pair is None`.

## Tests and cache

### 23. Tests pin some problematic behaviour. **Confirmed**
- `test_hennig_jaccard_on_the_comparison_set` asserts dissolved False for an absent Cluster.
- `test_the_fixed_gamma_q_is_read_from_the_envelope` asserts extrapolation at `gamma_end + 1`.
- The golden texts pin unlabelled ranges and the "wider" wording.
- Missing regression cases:
  - zero defined null Q (today a TypeError);
  - partly defined null Q (the denominator);
  - wholly absent and low-B* Clusters;
  - single-tag survival;
  - `beyond_scan` or explicit fixed-γ optimisation;
  - width equality;
  - the `no_qualifying_pair` card note.
- The bg catalogue has a parity test, so every new string needs a bg entry (ADR 0003).

### 24. Versions and reruns. **Confirmed (design gap)**
- The cached file stores `summary` next to `records`, and the app *reads the stored summary* (`ps_view.validation_of` → `validation["summary"]`). The validation key contains `VALIDATION_METHOD_VERSION`.
- So today a summary-only change either goes unseen, because old summaries are shown, or forces a full replicate rerun if the version is bumped.
- **Fix:** split the version in two:
  - `VALIDATION_RECORDS_VERSION`, in the key, bumped only when replicate calculations change. That covers #6 J_full, #7(b) fixed-γ runs, #11 perturbation share, and any change in fraction, budget or scan.
  - `VALIDATION_SUMMARY_VERSION`, stored with the summary, which the app re-derives from the records on read when it is stale. That covers #2–4, #9, #12–15 and #18–21.
- Bundles ship validations (ticket 13), so `steamstudy bundle` must recompute or re-summarise, and the export `SCHEMA_VERSION` changes if columns change (`validation_clusters.csv`: size, dissolution and recovery frequency, s.e.).
