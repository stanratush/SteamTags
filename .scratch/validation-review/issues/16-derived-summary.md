# 16: Derived summary: per-Cluster figures, statuses and the three-state Null Comparison

**What to build:** `validation.summarise` computes every figure and status this effort decided, from the records alone. Per Cluster and arm: B*, both Jaccards with s.e. and spreads, the dissolution and recovery frequencies with Wilson intervals, size, and the statuses Not assessable, Dissolved in most subsamples and borderline, plus the rarely-assessable flag. For the Null Comparison: D, U and its reasons, the three-state verdict, the weak flag, the observed Q actually compared, the Multi-Tag Cluster spread and the width count with ties. This issue changes the summary's shape; the sentences that read it come in issue 17.

**Blocked by:** 15

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "Per-Cluster figures and statuses (derived)", "Null Comparison (derived)", "Tests". Sources: [How does tag loss count in Cluster recovery?](01-tag-loss-in-cluster-recovery.md), [Which per-Cluster figures and verdict replace "Dissolved"?](02-cluster-figures-and-verdict.md), [What does the Null Comparison state, and by which rule?](04-null-comparison-rule-and-wording.md).

- [ ] **Per Cluster, per arm** (over the S non-degenerate subsamples): `size`, `assessable_subsamples` (B*), `one_tag_left`, `absent`, `mean_retention`; Hennig's `mean_jaccard`, `mean_jaccard_se` (sd/√B*, `None` when B* < 2), `p10`/`p90`; `at_most_half`, `dissolution_frequency`, `wilson_low`/`wilson_high` (95%, z = 1.96); `recovered` (J > 0.75), `recovery_frequency` and its Wilson bounds; Whole-Cluster `mean_whole_cluster_jaccard`, its s.e. and `p10`/`p90` over S.
- [ ] **Statuses:** `assessable` (B* > 0), `dissolved_in_most` (`at_most_half` > B*/2), `borderline` (`wilson_low` ≤ 0.5 ≤ `wilson_high`, only when assessable), `rarely_assessable` (B* < S/2).
- [ ] `verdicts.dissolved` becomes `verdicts.dissolved_in_most` (labels per arm), plus `verdicts.borderline` and `verdicts.not_assessable` per arm.
- [ ] **Null:** `q_defined` (D), `q_undefined` with reasons (`no_edges`, `beyond_scan`), `reach` over D, `verdicts.null_q` in {`above_all_defined`, `reached`, `undefined`} replacing `q_not_above_null`, `weak` (D < R/2), the Q spread over D.
- [ ] **Observed Q:** the summary carries `q.observed_selected` and `q.observed`, the higher of it and the stored observed runs; `q.observed_from_runs` is true when the runs won. Reach compares against `q.observed`.
- [ ] **Width:** `width.wider` (strictly) and `width.equal` (exact float equality) over the K nulls with a Selected Partition, replacing `narrower`. **Multi-Tag Clusters:** observed, plus median, min and max over the same K.
- [ ] The `DISSOLVED` comment and the module docstring: Hennig's 0.5 is per subsample, the majority is this study's rule, and the scope is "the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the Selected Partition rule), not the Parameter Grid or the choice of pair".
- [ ] The current card and export keep working on the new shape (minimal adaptations only; they are rewritten in 17, 18 and 20).
- [ ] `summarise` unit tests on synthetic records, no Leiden, one per case:
  - zero defined null Q (state `undefined`, no TypeError);
  - partly defined null Q (denominator D; `weak` when D < R/2);
  - a wholly absent Cluster (Not assessable);
  - a low-B* Cluster (`rarely_assessable`);
  - single-tag survival (unscored by Hennig's Jaccard, scored by the Whole-Cluster Jaccard);
  - exactly half dissolved (not labelled);
  - a Wilson interval containing ½ (borderline), and one that does not;
  - width ties counted apart;
  - the observed runs beating the Selected Partition's Q.
- [ ] `test_hennig_jaccard_on_the_comparison_set` asserts that an absent Cluster is Not assessable, not `dissolved False`.
- [ ] On the 9 stored runs' records (rerun or recomputed on the test Build where available), Comments report how many Cluster-runs are labelled and borderline, against ticket 02's 19 and 8.
- [ ] The full test suite passes.
