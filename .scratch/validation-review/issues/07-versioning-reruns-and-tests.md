# How are versions, reruns and tests staged?
Type: grilling
Status: resolved
Blocked by: 01, 02, 03, 04, 05, 08, 10, 12

## Question

The cache stores `summary` next to `records`, and the app reads the stored summary (`ps_view.validation_of`). `VALIDATION_METHOD_VERSION` sits in the validation key, so any change either goes unseen (old summaries) or forces a full replicate rerun. See [Verified review](../research/01-verified-review.md) items 23 and 24.

Decide:
- Whether to split the version into a records version (in the key) and a summary version (re-derived from records on read). Name exactly which decided changes bump which.
- How `steamstudy bundle` and shipped validations handle each bump.
- The export `SCHEMA_VERSION` change and its new columns.
- Which tests are revised: the absent-Cluster expectation, the extrapolation at `gamma_end + 1`, and the golden texts.
- Which regression cases are added:
  - zero or partly defined null Q;
  - wholly absent or low-B* Clusters;
  - single-tag survival;
  - `beyond_scan` or explicit fixed-γ optimisation;
  - width equality;
  - the `no_qualifying_pair` card note.

## Answer

Decided by grilling with the researcher, 2026-11-04, accepting every recommendation. Facts checked:
- `validation.summary_from_records(observed, records)` already exists (`validation.py:317`), and the records hold per-replicate, per-Cluster Jaccards.
- `ps_cache.write_validation` stores `summary` next to `records`. Readers take `validation["summary"]`: `ps_view.py:635, 788` and `ps_export.py:174, 238`.
- `bundle/make.py` (`ship_parameter_selection`) always recomputes every shipped grid and validation into the staging Build and ships its own wheel. `stale_files` compares the maker's cache with the fresh result, file by file.
- `SCHEMA_VERSION` is already 4 (`export/schema.py:17`, commit 80b0add). Schema 4 is on `bilingual-cluster-views` and `region-title-width`, not on `main`.
- No CSV carries the pair-level null verdict today.

**The summary is no longer stored. It is always derived from the records.**
- The validation file holds only `validation_key`, `records` (now including the observed network's fixed-γ run at γ_obs, from [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md)) and `computed_with`.
- Every reader derives the summary from the records: card, Inspector, export and report. `validation_of` takes the observed `GraphResult`.
- The review's two-version split (a stored `VALIDATION_SUMMARY_VERSION` re-derived when stale) was weighed and rejected. Deriving costs milliseconds over about 200 records, it removes a staleness branch and its tests, and a summary can never be stale. The one version left is the records version, in the key.

**Records version bump: `ps-validation-1` → `ps-validation-2`.** It is bumped for exactly three changes:
- the Whole-Cluster Jaccard ([How does tag loss count in Cluster recovery?](01-tag-loss-in-cluster-recovery.md));
- the explicit Leiden runs at γ_obs on the observed network and each replicate, with `beyond_scan` ([Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md));
- the per-replicate Perturbation Share ([Which sensitivity checks run, and as one-off studies or in-app?](05-sensitivity-checks-and-scope.md)).

Tickets 02, 04, 06 and 11 and the straight bugs #1–4 change only the derived summary or the display, so they need no bump. Ticket 12's γ-step guard needs none either. The selection `METHOD_VERSION` in the grid key stays put, because no grid changes.
- **There is one bump per release.** The first issue that changes records bumps the version. Later issues in the same release don't bump again, because no bundle ships in between and only dev caches are affected. Rule: bump when records first change after the last bundle was made.
- **Old `ps-validation-1` caches** (including the 9 stored runs on Build `20261008T221504Z-7a23ae9f`) miss on the new key. The app shows those pairs as not validated, and the user reruns them. There is no migration, no partial reading of old records and no automatic cleanup. A cache clear removes the old files.

**`steamstudy bundle` does not change.** A bundle recomputes into staging and ships its own code, so a shipped bundle's code and validations always match. Old bundles keep their old code, so there are no "old shipped validations" for new code to meet. Because the summary is no longer stored, `stale_files` flags only records that really differ. This closes the map's fog item on bundle handling.

**Export: `SCHEMA_VERSION` 4 → 5**, rather than folding the columns into the unreleased 4. The bump costs nothing, and it avoids two different "schema 4" zips existing if any were made from this branch.
- **New `validation_pairs.csv`**, one row per validated pair: the null state (above all D defined / reached / undefined), D, R, U and U's reasons, the k-of-K width with ties counted apart (`.3f`), the D < R/2 flag and the B*-below-half flag.
- **`validation_clusters.csv`**:
  - adds `size`, `dissolved_in_most` (replacing `dissolved`), `dissolution_frequency`, `wilson_low`, `wilson_high`, `borderline`, `assessable`, `recovered` (count with J > 0.75), `recovery_frequency`, `mean_jaccard_se` and `mean_whole_cluster_jaccard`;
  - re-describes `mean_jaccard` and `at_most_half` as Hennig's Jaccard.
- **`validation_replicates.csv`** adds `perturbation_share`, `beyond_scan`, `null_q_envelope` (envelope-only) next to `null_q` (the final Leiden Q), `q_defined`, and for subsamples the ARI's tag share.
- No per-replicate, per-Cluster table is exported. The raw Jaccards stay in the cache JSON.

**Revised tests**
- `test_hennig_jaccard_on_the_comparison_set` asserts that an absent Cluster (B* = 0) is **Not assessable**, not `dissolved False`.
- `test_the_fixed_gamma_q_is_read_from_the_envelope` is split into two tests:
  - γ past the scan end gives `beyond_scan`;
  - the final Q comes from the explicit Leiden run.
- The golden texts (`test_validation_block_golden_text` and `selection_report_*.md`, en and bg) are regenerated with `STEAMSTUDY_WRITE_GOLDEN`. Their diff is reviewed in the issue, so the unlabelled ranges and the "wider" wording visibly go.

**Added regression cases**
- `summarise` unit tests on synthetic records (no Leiden), one per case:
  - zero defined null Q;
  - partly defined null Q (denominator D);
  - a wholly absent Cluster;
  - a low-B* Cluster (flag);
  - single-tag survival (unscored by Hennig's Jaccard, 0 by Whole-Cluster Jaccard);
  - width equality (ties counted apart at `.3f`).
- One small-network test for the explicit fixed-γ optimisation at γ_obs.
- One app-render test for the `no_qualifying_pair` card note.
- One config test for the γ-step guard (`gamma_step = 0.025 → ConfigError`, from [Should the default γ step be finer than 0.05?](12-default-gamma-step.md)).
- The bg catalogue's parity test covers every new string (ADR 0003).

**New-Build rerun:** the spec's **final issue**, `ready-for-agent` and blocked by the implementation issues. On the coming Build it reruns the three one-off scripts (`prototypes/08-mixing-check/`, `09-clamp-bracket/`, `10-scan-step/`). It applies the reopen rule from [Should the default γ step be finer than 0.05?](12-default-gamma-step.md) as acceptance criteria and updates the guide quotes' figures.

No new glossary term. No ADR: storing records only and deriving the summary is cheap to reverse, so it fails the hard-to-reverse test.
