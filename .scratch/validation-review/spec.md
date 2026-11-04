# Spec: Validation review

Settled through the [Validation review map](map.md) (wayfinder, 2026-11-04 to 2026-11-05). Each decision below is the current state of its ticket, with every later amendment applied: ticket 11 widened 06's Size column, and ticket 13 reworded 12's guide clause and closed 03's note gap. When this spec and a ticket's original Answer disagree, the spec wins. Glossary: [CONTEXT.md](../../CONTEXT.md) (**Null Comparison**, **Subsample Stability**, **Hennig's Jaccard**, **Whole-Cluster Jaccard**, **Dissolved in most subsamples**, **Q not above the null**, **Perturbation Share**). Records: [ADR 0003](../../docs/adr/0003-bulgarian-is-a-view-only-translation.md) (every new string needs its Bulgarian). Evidence: [Verified review](research/01-verified-review.md) ("review item N" below).

Verbatim text lives in two assets, which the issues quote from and this spec does not repeat:
- [bg-strings.md](prototypes/11-bg-wording/bg-strings.md): every card and Inspector string, English key and Bulgarian, with the number and plural conventions.
- [guide-text.md](prototypes/13-guide-wording/guide-text.md): the User Guide passages, the methods paragraph, Appendix A, the knock-on edits and the bg-terms rows, in English and Bulgarian.

Implementation happens on a new branch `validation-review`, cut from `bilingual-cluster-views`, because export schema 4 and the Bulgarian catalogue exist only there.

## Goal

Fix the Parameter Selection **Validation** so that what it reports is correct, uncertain where it is uncertain, and attributed honestly:

1. **Straight bugs**: the heatmap collapses (item 1); the card crashes when no shuffled network has a Q (item 2); undefined null Q stays in the denominator (item 3); a Cluster absent from every subsample reads as stable (item 4).
2. **Recovery that counts lost tags**: a **Whole-Cluster Jaccard** beside **Hennig's Jaccard**, and an assessability rule.
3. **A verdict that matches its source**: **Dissolved in most subsamples** (a majority of per-subsample cuts) replaces "Dissolved" (a cut on the mean), with Monte Carlo uncertainty and a borderline mark.
4. **A fixed-γ arm that optimises at γ_obs**, with no extrapolation past a scan.
5. **A Null Comparison with three stated states**, a count-only rule, a scope phrase and a limitation sentence.
6. **A redesigned card and Inspector section** (interval plot), in English and Bulgarian.
7. **Records-only caching**, one records version bump, export schema 5, and the guide.

**What does not change:** the Parameter Grid, the Selected Partition and Selected Resolution of any pair, Neighbour Agreement, the Automatic Parameter Selection's choice, the selection `METHOD_VERSION`, the subsample fraction (80%), `TRADES_PER_GAME` (10) and the default `gamma_step` (0.05). Validation never changes a Selected Partition.

## Facts this spec rests on

Measured on `bilingual-cluster-views` and Build `20261008T221504Z-7a23ae9f` (9 stored `ps-validation-1` runs at 8 distinct pairs, R = S = 100), 2026-11-04 to 2026-11-05.

- **Code today:**
  - `network/validation.py`: `envelope_partition` extrapolates past `gamma_end`. `compare` scores Hennig's Jaccard on the comparison set and leaves an absent Cluster `None`. `_arm_summary` sets `dissolved = mean ≤ 0.5`. `summarise` sets `verdicts.q_not_above_null = reach ≥ 1`, with `reach` over defined Qs and the text's denominator R.
  - `network/selection_text.py`: `null_sentences`, `subsample_sentences`, `validation_block`, `methods_paragraph`. `_signed(None)` raises a TypeError when every null is edgeless.
  - `app/ps_view.py`: `validation_of` reads `validation["summary"]`; `cluster_table` has 2 × N rows; `validation_card`; `inspector` (badges "Q above all null replicates", "Dissolved: {n}"); `mode_layout` puts the `ps-validate` button under Apply and gives `ps-heatmap` only `height: 460px`.
  - `app/ps_cache.write_validation` stores `summary` beside `records`. `app/ps_run.py:195` writes it. `app/ps_export.py` reads `validation["summary"]` (lines 174, 238).
  - `VALIDATION_METHOD_VERSION = "ps-validation-1"` (`network/selection.py:32`), in the validation key. `SCHEMA_VERSION = 4` (`export/schema.py:17`).
  - `config.py:471` checks only `gamma_step > 0`. `champ.scan_gammas` rounds γ to 2 decimals.
  - `bundle/make.ship_parameter_selection` recomputes every shipped grid and validation into staging and ships its own wheel; `stale_files` compares files.
  - The catalogue's parity test (`tests/test_i18n.py`) fails on a missing, orphaned or placeholder-mismatched key.
  - `tests/test_guide.py:100` and `tests/test_guide_bg.py:247` require the guide's methods paragraph to equal `methods_paragraph(tx)`.
- **Stored runs** (review, tickets 02–03, 08–10):
  - Null Q at γ_obs never comes close (reach 0 in all 9 runs). The envelope understates a null's Q at γ_obs by at most 0.0013 (50 seeds), about 1% of the smallest gap. No replicate is beyond its scan.
  - Under the new rule, 19 Cluster-runs are Dissolved in most subsamples, against 13 under mean ≤ 0.5. 8 are borderline.
  - Shuffle mixing has plateaued by 10 trades per game at every validated pair. The Perturbation Share is 0.58–0.70.
  - The s′ = 2 clamp moves 0 of 50 labels. A γ step of 0.01 changes no observed Selected Partition and narrows null median widths by 3–30%.

## Decisions

### Records (replicate calculations): `ps-validation-2`

From tickets [01](issues/01-tag-loss-in-cluster-recovery.md), [03](issues/03-fixed-gamma-arm.md), [05](issues/05-sensitivity-checks-and-scope.md) and [07](issues/07-versioning-reruns-and-tests.md).

- **Whole-Cluster Jaccard**, per subsample, arm and Multi-Tag Cluster: max_D |C ∩ D′| / |C ∪ D′| over the subsample's Clusters D′ on the comparison set, where C is the whole Cluster. It is 0 when no tag of C survives. Each record also stores |C′|, the surviving-tag count. Hennig's Jaccard keeps its definition (on C′, best match over every subsample Cluster, One-Tag ones included) and is stored only when |C′| ≥ 2.
- **Explicit Leiden runs at γ_obs.** Leiden runs at exactly γ_obs with the **10 scan seeds**: once on the observed network, once in every null, and once in every subsample (one run set serves both arms). Q at γ_obs is the best of the network's own scan envelope at γ_obs and these runs. The subsample's at-resolution partition is the best of the same candidates.
  - The runs feed the fixed-γ arm only. They never enter any network's own scan, CHAMP, γ̂ or Selected Partition rule.
  - Each record stores the envelope-only value and the final one: `q_envelope` and `q_fixed` for nulls; for subsamples, whether the at-resolution partition changed (`at_resolution_changed`).
  - The observed network's run result is stored in the validation file (`observed.q_runs`), next to the Selected Partition's Q.
- **No extrapolation.** `envelope_partition` returns nothing when γ exceeds the replicate's `gamma_end`. Then the null's Q is undefined with reason `beyond_scan`, and the subsample's at-resolution arm is degenerate with reason `beyond_scan`. A test replaces the `gamma_end + 1` extrapolation case.
- **Perturbation Share**, per null: the share of the observed table's 1-cells that are 0 after the shuffle (Strona's diagnostic). No threshold and no warning.
- **Version:** `VALIDATION_METHOD_VERSION` becomes `ps-validation-2`, once, in the first issue that changes records. Old `ps-validation-1` files simply miss: the pair shows as not validated and the user reruns it. There is no migration, partial read or automatic cleanup.

### Storage: records only

From [07](issues/07-versioning-reruns-and-tests.md).

- The validation file holds `validation_key`, `records`, `observed` (the observed run at γ_obs) and `computed_with`. It holds **no `summary`**.
- Every reader derives the summary from the records with `validation.summary_from_records(observed_result, file)`: the card, the Inspector, the export and the report. `ps_view.validation_of` takes the observed `GraphResult` and returns the file plus its derived summary.
- There is one version, the records version, in the key. Summary-only changes need no bump.
- `steamstudy bundle` does not change. A bundle recomputes into staging and ships its own code, so with no stored summary `stale_files` flags only records that really differ.

### Per-Cluster figures and statuses (derived)

From [01](issues/01-tag-loss-in-cluster-recovery.md) and [02](issues/02-cluster-figures-and-verdict.md). The same in both arms, over the non-degenerate subsamples S.

- **B\*** = the subsamples with |C′| ≥ 2. |C′| = 1 counts as "one tag left"; |C′| = 0 as absent. Both are left out of Hennig's Jaccard.
- **Hennig's Jaccard**, over B*: the mean with its Monte Carlo s.e. sd/√B*; the 10th–90th percentile spread; the **dissolution frequency** (J ≤ 0.5) as k of B* with a 95% Wilson interval (z = 1.96); the **good-recovery frequency** (J > 0.75, Hennig's "say") as k of B* with a 95% Wilson interval.
- **Whole-Cluster Jaccard**, over S: the mean with its s.e., and the 10th–90th percentile spread. No frequencies, no label.
- **Size** |C|, beside the mean retention share and the absent count, which are kept.
- **Statuses**, in display order:
  1. **Not assessable**: B* = 0.
  2. **Dissolved in most subsamples**: J ≤ 0.5 in more than half of B*, on the point estimate. Exactly half is not labelled.
  3. **Borderline**: the Wilson interval of the dissolution frequency contains ½ (`wilson_low ≤ 0.5 ≤ wilson_high`), labelled or not.
- **Rarely assessable** is a flag, not a status: B* < S/2. It is shown as "(B* of S)".
- No minimum size, no minimum B*, no fpc bands. Hennig's per-subsample 0.5 is his; the majority is this study's rule, and the text says so.
- The `DISSOLVED` constant's comment and the module docstring stop attributing a cut on the mean to Hennig.

### Null Comparison (derived)

From [03](issues/03-fixed-gamma-arm.md) and [04](issues/04-null-comparison-rule-and-wording.md).

- **D** = the nulls with a defined Q at γ_obs; **U** = R − D, with reasons `no_edges` and `beyond_scan`. The summary carries `q_defined = D`.
- **`verdicts.null_q`** replaces the boolean `q_not_above_null`, with three states: `above_all_defined` (D ≥ 1, reach 0), `reached` (reach ≥ 1, where reaching means ≥) and `undefined` (D = 0).
- **Weak flag:** D < R/2. No minimum D.
- **The observed Q** in the comparison is the Selected Partition's Q, unless the observed runs at γ_obs found a higher one. Then the higher one is used and the card adds a note.
- **The rule is a count only.** No p-value, for two reasons the guide states: the bound would only be nominal, because γ_obs and the pair are chosen on the observed data; and with R = 100, "none reaches it" is the strongest result possible.
- **Multi-Tag Clusters:** observed, plus the median and range over the K nulls with a Selected Partition.
- **Domain width:** the median over the K nulls vs observed, both `.3f`. "Observed wider than n of K", with ties (exact float equality) counted apart only when present: "wider than 76, equal to 3, of 79". The side word ("narrower"/"wider" for the median) goes.
- Selected Resolution and the edge ratio of the nulls stay in the export and the guide, not on the card. So does the Perturbation Share.

### The card

From [06](issues/06-validation-card-and-inspector-layout.md), as amended by [11](issues/11-bg-wording-card-and-inspector.md) and [13](issues/13-guide-and-context-wording.md). Every string's English and Bulgarian are in [bg-strings.md](prototypes/11-bg-wording/bg-strings.md). The layout is the **interval plot** of [PROTOTYPE-validation-layout.html](prototypes/06-validation-layout/PROTOTYPE-validation-layout.html). Top to bottom:

1. **Header:** an H4 "Validation of g = …, s = …" with `_help("selection.validate")`, replacing the bold `P`.
2. **Constraints note:** the existing muted sentence when custom constraints choose another pair. When custom constraints give `no_qualifying_pair` (`view.star` is None), a warning note: "No pair qualifies under your constraints, so this is the validation of g = …, s = …, the pair chosen under the default constraints."
3. **Null Comparison:** an H5 with its ? link; the muted header "(100 shuffled networks, per-pair procedure at g = …, s = …)". Then prose:
   - the Q sentence in its three states, with U's reasons appended when U > 0 ("; 52 had no edges; 8 lay beyond their γ scan");
   - the observed-runs note, when it applies;
   - the D < R/2 warning: "⚠ Most shuffled networks have no Q (U of R), so this comparison is weak.";
   - the Multi-Tag Cluster line, or "None of the R shuffled networks has a Selected Partition.";
   - the width sentence, then "Widths are upper bounds, conditional on the partitions the γ scan finds." The card makes no direction claim;
   - `NULL_CAVEAT` in italics.
4. **Subsample Stability:** an H5 with its ? link and the existing muted header. Then:
   - ARI with labelled spreads: "Re-selected: median ARI 0.54 (10th–90th percentile: 0.45 to 0.65) over 100 of 100 subsamples, on 99% of the tags." Degenerate reasons follow as today. Then the at-resolution sentence;
   - **one combined dissolved list**: the one-key lead "Dissolved in most subsamples (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this study's rule):" (bolded up to the first " ("), then "k of N Multi-Tag Clusters in both arms: …; re-selected only: …; at resolution only: …". Empty groups are left out;
   - **Borderline** in the same shape, only when there is one;
   - **Not assessable** as its own sentence;
   - "No Multi-Tag Cluster is dissolved in most subsamples in either arm." only when no Cluster is labelled and none is not assessable.
5. **The Cluster list**, replacing `cluster_table`:
   - a small muted legend;
   - a header row: Cluster | Size (44 px, with the small-Cluster caveat as its ? help) | "≤ 0.5: 0 — ½ — 1" | Status;
   - one row per Multi-Tag Cluster: the label with up to 3 member tags; |C|; a dot-and-whisker plot (about 150 px; lines R and A; dot = dissolution frequency, whisker = Wilson interval, a dashed line at ½; dark when Dissolved in most subsamples in that arm, hollow grey otherwise; "Not assessable" in words instead of a whisker); the status chips (once when the arms agree, "R … A …" when they differ); "⚑ rarely assessable (B* of S)" under the status;
   - under about 650 px, the Status cell wraps onto its own line;
   - expanding a row (`html.Details`/`Summary`, no callback) shows a small table for both arms: Arm | Hennig's J (mean ± s.e.; 10th–90th pct) | ≤ 0.5 in (k of B*; 95% Wilson) | > 0.75 in (k of B*; 95% Wilson) | Whole-Cluster J (mean ± s.e.), then all member tags. Wilson intervals read "42–62%";
   - the whiskers are absolutely positioned CSS spans, not Plotly.
6. **Closing lines:** `SUBSAMPLE_CAVEAT` and the limitation sentence, both in italics, then the existing three help links.

The residual sentence ("50 seeds raised a null's Q by at most 0.0013") is guide-only.

### The Inspector's Validation section

From [06](issues/06-validation-card-and-inspector-layout.md). At the bottom of the Inspector:

- An H5 "Validation" with its ? link.
- **Not validated:** "Not validated", with the **Validate this pair** button under it, moved from under Apply. No run-time hint (bg-strings.md lists "About 3 min on 12 workers." from the prototype; it does not ship).
- **Validated:**
  - the null badge in three states: "Q above all D shuffled networks" / "Q not above the null (k of D)" with the help link / "Null Q undefined", each with a " ⚠" suffix when D < R/2;
  - the badge "Dissolved in most subsamples (re-selected): n";
  - two status strips, R and A: one 12 px square per Multi-Tag Cluster in Cluster order (dark = dissolved in most subsamples, dashed outline = borderline, hatched = not assessable), each with its label as a tooltip;
  - the existing line "median ARI re-selected …, at resolution …";
  - a link "Open the validation card ↓" that scrolls the main column to the card, shown only when the inspected pair is the card's pair.

### Heatmap

Review item 1: `#ps-heatmap{flex:0 0 460px}`, and `flex-shrink:0` on every direct child of `.ps-main` (which scrolls).

### Configuration guard

From [12](issues/12-default-gamma-step.md): `config.py` rejects a `gamma_step` that is not a whole multiple of 0.01 with a `ConfigError`. The default stays 0.05. No version bump.

### Bulgarian

From [11](issues/11-bg-wording-card-and-inspector.md) and [13](issues/13-guide-and-context-wording.md): every new card and Inspector string takes its entry from bg-strings.md, plus the observed-runs note from 13 ("Изпълненията при γ_obs намериха Q {q} за наблюдаваната мрежа, над {q0} на избраното ѝ разбиване; сравнението използва {q}."). The conventions there hold: the decimal comma everywhere (labels included), "от … до" for prose and ARI ranges, en-dash compact ranges for quantities ≥ 0, colon forms for counts that are not `{n}`, and one `tx.n` pair. The retired keys are removed (the parity test fails on orphans):
- `selection_text`: "({r} shuffled networks, same g and s).", "{reach} of {r} shuffled networks reach it: Q not above the null.", "no shuffled network reaches it ({range}).", "narrower", "wider", both "{k} of {r} also have a Selected Partition, with {side} domains …" keys, "None of the {r} has a Selected Partition.", "median ARI {median} ({p10}–{p90})", "Re-selected: {ari} over {n} of {total} subsamples", "At resolution {gamma}: {ari}", both counted "… is dissolved … (mean Jaccard ≤ 0.5):" keys, and "No Multi-Tag Cluster is dissolved (mean Jaccard ≤ 0.5) in either arm.";
- `ps_view`: "mean Jaccard", "≤ 0.5 in k of B*", "retention share", "absent", "Dissolved", "Q above all null replicates" and "Dissolved: {n}".

### Export: schema 5

From [07](issues/07-versioning-reruns-and-tests.md) and [13](issues/13-guide-and-context-wording.md). `SCHEMA_VERSION` 4 → 5. Every column is declared in `schema.py` with an "Explained in" anchor, indexed in `guide_index`, and Appendix B is regenerated in both languages.

- **New `validation_pairs.csv`**, one row per validated pair: `dataset`, `g`, `s`, `resolution`, `observed_q` (the Q the comparison uses), `observed_q_selected` (the Selected Partition's), `null_state` (`above_all_defined` / `reached` / `undefined`), `replicates` (R), `q_defined` (D), `q_undefined` (U), `q_undefined_no_edges`, `q_undefined_beyond_scan`, `reach`, `width_observed`, `width_null_median`, `width_wider`, `width_equal`, `width_compared` (K), `weak_null` (D < R/2) and `rarely_assessable` (any Cluster in either arm).
- **`validation_clusters.csv`**: adds `size`, `dissolved_in_most` (replacing `dissolved`), `dissolution_frequency`, `wilson_low`, `wilson_high`, `borderline`, `assessable`, `recovered` (count with J > 0.75), `recovery_frequency`, `recovery_wilson_low`, `recovery_wilson_high`, `mean_jaccard_se` and `mean_whole_cluster_jaccard`. `mean_jaccard` and `at_most_half` are re-described as Hennig's Jaccard, and `present` as B*.
- **`validation_replicates.csv`**: adds `perturbation_share` (null arm), `beyond_scan`, `null_q_envelope` beside `null_q` (the final Q), `q_defined`, `edged_share` (subsample arms: the ARI's tag share) and `at_resolution_changed`.
- No per-replicate, per-Cluster table. The percentile spreads and the Whole-Cluster Jaccard's s.e. stay card-only.
- `method_versions.validation` in the export's metadata reads the new version.

### User Guide and methods paragraph

From [13](issues/13-guide-and-context-wording.md): every passage is verbatim in [guide-text.md](prototypes/13-guide-wording/guide-text.md), English and Bulgarian, with a change list against the current text.

- Chapter 3: **Null Comparison** and **Subsample Stability**, each with its In short, Columns, body, Why it matters, Example (the stored Overall 17/2 run), Bounds, Compare with and Exact definition. Each In short stays within 60 words.
- The methods paragraph's last two sentences, in `05-citing-and-reproducing.md` and in `selection_text.methods_paragraph` (both languages), which the guide tests require to be equal.
- Appendix A, Cluster-wise Jaccard stability: the bullet and "Why not here", correcting the attribution (Hennig's 0.5 and 0.75 apply per resample; the fpc bands apply to the mean).
- Knock-ons: a known-limitations bullet; "seven tables" → "eight" in `05-citing` and `02-app-controls`; `04-files` (three validation tables, a `validation_pairs.csv` section, new descriptions of the replicates and clusters tables); Appendix B regenerated; Wilson (1927) in Appendix C.
- `docs/i18n/bg-terms.md`: the "dissolved" row replaced and seven rows added. The superseded-word list is unchanged.
- The scope phrase "the per-pair procedure at the same Threshold Pair" goes into the `validation.py` docstring too. "Chosen pair" is not used for a validated pair.
- CONTEXT.md does not change.

### Tests

From [07](issues/07-versioning-reruns-and-tests.md).

- **Revised:**
  - `test_hennig_jaccard_on_the_comparison_set` asserts that an absent Cluster (B* = 0) is Not assessable.
  - `test_the_fixed_gamma_q_is_read_from_the_envelope` is split: γ past the scan end gives `beyond_scan`; the final Q comes from the explicit run.
  - The golden texts (`test_validation_block_golden_text`, `tests/fixtures/selection_report_*.md`) are regenerated with `STEAMSTUDY_WRITE_GOLDEN`, and the diff is reviewed in the issue.
- **Added:**
  - `summarise` unit tests on synthetic records, one per case: zero defined null Q; partly defined null Q (denominator D); a wholly absent Cluster; a low-B* Cluster; single-tag survival; width equality; exactly half dissolved (not labelled); a Wilson interval containing ½; the "no Cluster dissolved" sentence suppressed by a not-assessable Cluster.
  - One small-network test of the runs at γ_obs: observed and replicate sides use identical γ and seeds, and the runs never change a replicate's Selected Partition.
  - One app-render test of the `no_qualifying_pair` card note, and one of the Inspector's strip and badges.
  - One config test: `gamma_step = 0.025 → ConfigError`.
  - A layout test of the heatmap's `flex-shrink` if the CSS tests allow it.
  - The catalogue parity test covers every new string.

### New-Build rerun

From [05](issues/05-sensitivity-checks-and-scope.md), [07](issues/07-versioning-reruns-and-tests.md) and [12](issues/12-default-gamma-step.md). The spec's final issue. On the coming Build, rerun the three one-off scripts by hand (about 75 min): [08-mixing-check](prototypes/08-mixing-check/README.md), [09-clamp-bracket](prototypes/09-clamp-bracket/README.md) and [10-scan-step](prototypes/10-scan-step/README.md). Never at bundle time.

- **The reopen rule:** the default γ step reopens, as a fresh question on the Automatic Parameter Selection side, if any observed Selected Partition changes, an observed width crosses the null median, or k/K **falls** by 0.10 or more at 0.01.
- **Otherwise** only the guide quotes' figures, the 0.58–0.70 Perturbation Share range and the Overall 17/2 example figures are updated, in both languages.

### Resolved while writing this spec

These choices were implicit in the tickets and are made explicit here.

- **One run set at γ_obs per subsample serves both arms.** Ticket 03 said "in both arms", but both arms share one subsample network, so a second set would repeat the first.
- **The observed run lives in the validation file**, not in the grid's graph result, so the grid and its key stay untouched.
- **`validation_pairs.csv` also carries `resolution`, `observed_q` and `observed_q_selected`**, so the observed-runs note can be read from the export; and a recovery Wilson interval, because ticket 02 gives the recovery frequency one and ticket 07's column list named only the dissolution one.
- **Placeholder names follow the code** where a catalogue entry already exists (`{resolution}`, `{total}`, `{reselected}`, `{at}`). bg-strings.md's names are illustrative there.
- **The help keys stay** (`selection.verdict.dissolved`, `selection.verdict.q_not_above_null`, `selection.validate`); only their labels change.
- **The Validate button stays a static layout component** (its callback needs it), placed in a static Inspector container after `ps-inspector-body` that holds the Validation section; the callback still toggles it.
- **The run-time hint does not ship**, although bg-strings.md lists it.

## Out of scope

See the [map](map.md#out-of-scope): measuring the selection effect (a full-pipeline null or a cheap probe), alternative subsample fractions, running the sensitivity studies at bundle time or in the app, and a finer γ step for the Null Comparison's scans only. Also: migrating `ps-validation-1` caches, and any change to the Automatic Parameter Selection's grid, choice or step.

## Issues

Status `ready-for-agent`. Numbering continues after the map's decision tickets (01–13). The list order is a safe serial order; issues that touch the same files follow their **Blocked by** lines.

- [14: Straight fixes: the heatmap keeps 460 px, and `gamma_step` must be a multiple of 0.01](issues/14-heatmap-and-gamma-step-guard.md)
- [15: Validation records `ps-validation-2`, stored without a summary](issues/15-records-v2-and-derived-summary.md)
- [16: Derived summary: per-Cluster figures, statuses and the three-state Null Comparison](issues/16-derived-summary.md)
- [17: Card and report sentences, in English and Bulgarian](issues/17-card-and-report-sentences.md)
- [18: The validation card's Cluster list and header](issues/18-validation-card-layout.md)
- [19: The Inspector's Validation section](issues/19-inspector-validation-section.md)
- [20: Export schema 5: `validation_pairs.csv` and the new columns](issues/20-export-schema-5.md)
- [21: User Guide, methods paragraph and bg-terms](issues/21-guide-and-methods.md)
- [22: Rerun the three sensitivity studies on the new Build](issues/22-new-build-rerun.md)
