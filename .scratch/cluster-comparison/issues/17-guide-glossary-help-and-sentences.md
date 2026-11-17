# 17: User Guide, glossary, `comparison.*` help keys and the sentences module

**What to build:** the documentation and shared wording the mode's tooltips and `?` buttons will point at, in English and Bulgarian. This lands before the mode, because the help tests require every key to resolve to a guide heading and `tests/test_guide.py` requires every CONTEXT.md term to be in the User Guide.

**Blocked by:** 15

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "Terms", "Readings", "Reading against seed and threshold dependence" (the caution), "Documentation and in-app help", the source lines and flag wording in "The Cluster Comparison mode" and "Matching", and "Moving between modes" (the `selection.use_in_comparison` text). Decision: ticket [11](11-names-and-readings.md).

- [ ] **CONTEXT.md:** Cluster Comparison, Cluster Match, Comparable Tags, Match Jaccard, Comparison State, each with its Avoid line. `docs/i18n/bg-terms.md` gains the five rows.
- [ ] **Ch. 1:** four modes.
- [ ] **Ch. 2:** `## Cluster Comparison mode` after Parameter Selection mode, opening with the caution as a callout; subsections Shared settings · Datasets · Dataset pairs · Link diagram · Minimum similarity and flags · Match detail · Games in both Clusters · Export CSV; task recipe "Compare the Clusters of two datasets"; Parameter Selection mode's section gains "Use in Cluster Comparison".
- [ ] **Ch. 3:** `## Cluster Comparison` after Parameter Selection, opening with "#### How a Cluster Comparison works" (holds the caution), with the nine entries the spec lists in the chapter's form (In short, Bounds, Compare with with the full Build's ranges as "seen on the full Build", one Exact definition). No wording bands, no p-value.
- [ ] **Ch. 5:** cite by `comparison_id`; record only. **Ch. 6:** one Build only; a Threshold Pair's partition depends on the Parameter Selection cache.
- [ ] Everything mirrored in `docs/user-guide/bg/`.
- [ ] **Help keys** `comparison.*` for every figure, label, flag badge, source state, the minimum slider, ⇄ and Export CSV, plus `selection.use_in_comparison`, each resolving to its entry's In short.
- [ ] **One sentences module** (as `selection_text` is for Parameter Selection) holding the readings, the caution, the four source lines and their tooltip, the flag labels and tooltip counts, the Tag-group labels, the Overlap vs. expected sentence, the games count line and empty-list sentences and the mode's empty states, each with its bg catalogue entry. The guide test checks the caution and readings against it.
- [ ] Chapter 4 and Appendix B are left to issue 23 (the columns do not exist yet).
- [ ] Guide, help, i18n parity and bg guide tests pass.
