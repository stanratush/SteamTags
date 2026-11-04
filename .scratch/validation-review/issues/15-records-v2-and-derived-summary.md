# 15: Validation records `ps-validation-2`, stored without a summary

**What to build:** every replicate calculation this effort needs, in one records change. Subsamples store the Whole-Cluster Jaccard and |C′| per Cluster. Leiden runs at exactly γ_obs with the 10 scan seeds on the observed network and every replicate, for the fixed-γ arm only. The envelope no longer extrapolates (`beyond_scan`). Nulls store their Perturbation Share. The version goes to `ps-validation-2`. The cache stops storing the summary, and every reader derives it from the records. The summary's figures and the text stay as they are here; issue 16 changes them.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "Records (replicate calculations)", "Storage: records only", "Resolved while writing this spec". Sources: [How does tag loss count in Cluster recovery?](01-tag-loss-in-cluster-recovery.md), [Does the fixed-γ arm optimise at the observed resolution?](03-fixed-gamma-arm.md), [Which sensitivity checks run…?](05-sensitivity-checks-and-scope.md), [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md). Reference measurement, not to import: the mixing script's perturbation share in [`prototypes/08-mixing-check/mixing_check.py`](../prototypes/08-mixing-check/mixing_check.py).

- [ ] **Whole-Cluster Jaccard** in `validation.compare`: per observed Multi-Tag Cluster, max over subsample Clusters D′ of |C ∩ D′| / |C ∪ D′| on the comparison set, 0 when no tag of C survives. Also store `survivors` = |C′|. Hennig's Jaccard is stored only when |C′| ≥ 2 (`None` otherwise). Degenerate arms keep `None` everywhere.
- [ ] **No extrapolation:** `envelope_partition(result, γ)` returns `None` when γ > the result's `gamma_end`.
- [ ] **Runs at γ_obs:** a helper runs Leiden at exactly γ_obs with the task's `scan_seeds` on a network and returns the best partition and its Q.
  - Each null: `q_envelope` (envelope only) and `q_fixed` (best of envelope and runs), both `None` with `reason`/`q_reason` `no_edges` or `beyond_scan` as applicable.
  - Each subsample: one run set; the at-resolution arm compares the best of envelope and runs; `at_resolution_changed` records whether the runs changed it; the arm is degenerate `beyond_scan` when γ_obs exceeds the subsample's scan end.
  - The runs never feed a network's scan, CHAMP, γ̂ or Selected Partition.
- [ ] **The observed run:** `ps_run` runs the same helper on the observed network once per validation and stores `observed: {"q_selected", "q_runs"}` in the validation file.
- [ ] **Perturbation Share** per null: the share of the observed game × visible-tag table's 1-cells that are 0 after `shuffled_games`.
- [ ] **Version:** `VALIDATION_METHOD_VERSION = "ps-validation-2"` in `network/selection.py`.
- [ ] **Storage:** `ps_cache.write_validation` writes `validation_key`, `records`, `observed` and `computed_with`, no `summary`. `ps_view.validation_of` takes the observed `GraphResult` and returns the file with a derived `summary` added. `ps_export` (lines 174, 238) and `callbacks.py` (888–916) read through it. Nothing reads a stored summary any more.
- [ ] `summarise` keeps its current output shape, reading `q_fixed` and skipping `None` Jaccards, so the card and export work unchanged until issue 16.
- [ ] Tests:
  - `test_the_fixed_gamma_q_is_read_from_the_envelope` is split: γ past `gamma_end` gives `None`/`beyond_scan`; the final Q comes from the explicit run when that is higher.
  - On a small network: observed and replicate runs use identical γ and seeds; the runs never change a replicate's Selected Partition.
  - `compare` on a hand-built case: single-tag survival (Hennig `None`, Whole-Cluster scored) and a wholly absent Cluster (Whole-Cluster 0).
  - The Perturbation Share is 0 for an unshuffled table and in (0, 1] after a shuffle.
  - A `ps-validation-1` file is not read (the key misses) and the pair shows as not validated.
- [ ] One real validation runs end to end on the test Build; Comments give its time against the old one (the runs should add about 1%).
- [ ] The full test suite passes.
