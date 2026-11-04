# How does tag loss count in Cluster recovery?
Type: grilling
Status: resolved
Blocked by:

## Question

Subsample Stability scores each Multi-Tag Cluster by Hennig's Jaccard restricted to the surviving tags C′ (`validation.compare`). Here the resampled units are games and the clustered objects are tags, so a tag that falls below g′ is an outcome of the perturbation. Conditioning on survivors hides that loss, and a single surviving tag can score 1.0. See [Verified review](../research/01-verified-review.md) items 4, 6 and 15.

Decide:
- Is conditional J kept as the headline, with retention beside it? Or is an unconditional recovery J_full = |C ∩ D′| / |C ∪ D′| added, or used instead?
- What is a replicate where |C′| < 2? Not assessable, J_full only, or scored as is?
- How is a Cluster absent from every subsample, or assessable in fewer than some minimum B* subsamples, labelled? Is there a minimum B*?
- Is Cluster size (and retained-tag count) shown, and does a size caveat attach to 2–3-tag Clusters?

Facts:
- Mean retention is 0.92–1.00 on the 9 stored runs.
- Single-tag survival happens at most 9 of 100 times.
- J = 1 with lost tags happens up to 44 of 100.
- 12 of 13 "Dissolved" Cluster-runs have 2–4 tags (recounted in ticket 02; first stated as 10 of 11).
- J_full needs new replicate calculations, because |D′| is not stored.

## Answer

Decided by grilling with the researcher, 2026-11-04. Evidence: [Verified review](../research/01-verified-review.md), items 4, 6 and 15.

**Terms** (now in [CONTEXT.md](../../../CONTEXT.md)): **Hennig's Jaccard** and **Whole-Cluster Jaccard**.

**Figures**
- **Hennig's Jaccard** is unchanged: max_D |C′ ∩ D′| / |C′ ∪ D′| on the surviving tags C′. It stays comparable with Hennig 2007 and fpc.
- **Whole-Cluster Jaccard** is added: max_D |C ∩ D′| / |C ∪ D′|, where lost tags count as not recovered. It is ≤ Hennig's Jaccard, with equality when no tag is lost. It needs new replicate calculations, because |D′| is not stored.
- Both arms (re-selected and at resolution) compute and report the same figures.
- ARI stays on the comparison set, unchanged. There is no "ARI_full". The share of edged tags it covers (`edged_share`, already computed) is shown next to it.

**Edge cases, per subsample**
- **|C′| ≥ 2:** both figures are scored.
- **|C′| = 1:** Hennig's Jaccard is not assessable (left out of its mean, counted as "one tag left"). Whole-Cluster Jaccard is scored.
- **|C′| = 0 (absent):** Hennig's Jaccard is not assessable. Whole-Cluster Jaccard = 0. This narrows ticket 07's "absent is never scored 0" to Hennig's Jaccard only.
- **Degenerate subsample** (no edges; in the re-selected arm also no Selected Partition): left out of every figure, Whole-Cluster Jaccard included, and counted as "k of S", as in ticket 07.

**Assessability of Hennig's Jaccard** (B* = subsamples with |C′| ≥ 2)
- B* = 0: status "Not assessable". No "No Multi-Tag Cluster is dissolved" sentence while any Cluster has it.
- B* below half of the non-degenerate subsamples: the mean is shown with a "rarely assessable (B* of S)" flag.
- There is no other cutoff. Ticket 02's uncertainty figures cover small B*. Whole-Cluster Jaccard needs no such rule.

**Size**
- A Cluster size column (|C|) is added next to the mean retention.
- One help-text caveat: 2–3-tag Clusters can take only a few Jaccard values and drop sharply when they lose or move one tag.
- No minimum size, and no Cluster is excluded.

**Hand-offs**
- To [Which per-Cluster figures and verdict replace "Dissolved"?](02-cluster-figures-and-verdict.md): which Jaccard (or both) the frequencies, the verdict and the uncertainty figures are based on. Also the wording of "Not assessable" and "rarely assessable".
- To [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md):
  - Whole-Cluster Jaccard and the |C′| counts per replicate are a records change, so they need new replicate calculations;
  - the assessability statuses and the size column are summary changes;
  - regression cases: single-tag survival, wholly absent, and B* below half.
- To [How should the validation card and the Inspector's Validation section look?](06-validation-card-and-inspector-layout.md): the size column and the two Jaccard columns per arm.
