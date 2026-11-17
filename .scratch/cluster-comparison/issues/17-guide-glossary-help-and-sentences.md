# 17: User Guide, glossary, `comparison.*` help keys and the sentences module

**What to build:** the documentation and shared wording the mode's tooltips and `?` buttons will point at, in English and Bulgarian. This lands before the mode, because the help tests require every key to resolve to a guide heading and `tests/test_guide.py` requires every CONTEXT.md term to be in the User Guide.

**Blocked by:** 15

**Status:** done

Spec: [Cluster Comparison spec](../spec.md): "Terms", "Readings", "Reading against seed and threshold dependence" (the caution), "Documentation and in-app help", the source lines and flag wording in "The Cluster Comparison mode" and "Matching", and "Moving between modes" (the `selection.use_in_comparison` text). Decision: ticket [11](11-names-and-readings.md).

- [x] **CONTEXT.md:** Cluster Comparison, Cluster Match, Comparable Tags, Match Jaccard, Comparison State, each with its Avoid line. `docs/i18n/bg-terms.md` gains the five rows.
- [x] **Ch. 1:** four modes.
- [x] **Ch. 2:** `## Cluster Comparison mode` after Parameter Selection mode, opening with the caution as a callout; subsections Shared settings · Datasets · Dataset pairs · Link diagram · Minimum similarity and flags · Match detail · Games in both Clusters · Export CSV; task recipe "Compare the Clusters of two datasets"; Parameter Selection mode's section gains "Use in Cluster Comparison".
- [x] **Ch. 3:** `## Cluster Comparison` after Parameter Selection, opening with "#### How a Cluster Comparison works" (holds the caution), with the nine entries the spec lists in the chapter's form (In short, Bounds, Compare with with the full Build's ranges as "seen on the full Build", one Exact definition). No wording bands, no p-value.
- [x] **Ch. 5:** cite by `comparison_id`; record only. **Ch. 6:** one Build only; a Threshold Pair's partition depends on the Parameter Selection cache.
- [x] Everything mirrored in `docs/user-guide/bg/`.
- [x] **Help keys** `comparison.*` for every figure, label, flag badge, source state, the minimum slider, ⇄ and Export CSV, plus `selection.use_in_comparison`, each resolving to its entry's In short.
- [x] **One sentences module** (as `selection_text` is for Parameter Selection) holding the readings, the caution, the four source lines and their tooltip, the flag labels and tooltip counts, the Tag-group labels, the Overlap vs. expected sentence, the games count line and empty-list sentences and the mode's empty states, each with its bg catalogue entry. The guide test checks the caution and readings against it.
- [x] Chapter 4 and Appendix B are left to issue 23 (the columns do not exist yet).
- [x] Guide, help, i18n parity and bg guide tests pass.

## Comments

- 2026-11-17, implementation:
  - The sentences module is `network/comparison_text.py` (catalogue area `comparison_text`, Bulgarian in `i18n/bg/comparison_text.py`; its constants are a declared parity source). It also holds the source lines for the `no_pick` and `run_gone` fallbacks of issue 16, the shared-settings-changed notice (issue 21) and the disabled "Use in Cluster Comparison" tooltip (issue 22). Source lines name the algorithm through a placeholder ("one {algorithm} run"), since a Louvain comparison clusters with Louvain.
  - Guide: ch. 1 "The four modes" (renamed from "The three modes"; nothing linked the old anchor); ch. 2 the recipe, "Use in Cluster Comparison" under Parameter Selection mode and `## Cluster Comparison mode` with its eight subsections; the Dataset strip's caution now points to the new mode; ch. 3 `## Cluster Comparison` with "How a Cluster Comparison works" and the nine entries (examples from the full Build: Strategy C2 ~ Simulation C1, Overall C4 ~ RPG C2, `comparison_id` 7789f0b5d412); ch. 5 "Cite a Cluster Comparison"; ch. 6 `## Cluster Comparison`. All mirrored in `bg/`.
  - Help: `COMPARISON_HELP` in `app/help.py` (32 keys). The Seed-Noise Floor label points at the Adjusted Rand index entry, as the Workbench's does.
  - Tests: `tests/test_comparison_text.py` (the spec's example strings in both languages) and two tests in `tests/test_guide.py` (the caution opens both sections; each reading is its entry's In short line; the five terms are in CONTEXT.md and the guide).
  - The Jaccard (comparable) reading does not fit as a second In short block of its shared entry (60-word cap), so it leads its own paragraph there, and its tooltip key shows the Match Jaccard entry's In short. If it needs a tooltip of its own, split the entry in two.
- 2026-11-18, code review:
  - Fixed: the "Use in Cluster Comparison" and Export CSV In short lines now carry the spec's help text word for word (so the tooltips do); ch. 2 quotes both empty-list sentences; the games count line bolds N, k, x, y and z; the full Build's ranges sit under *Compare with.*, not *Bounds.*; the scan-seeds tooltip is lowercase as in the spec; the Bulgarian "{n} not in its network" has a singular form; "minimum similarity" in CONTEXT.md and ch. 3 prose is now "Minimum Match Jaccard" (the ch. 2 heading keeps the spec's "Minimum similarity and flags"); "common Tags" in a ch. 3 sentence became "frequent Tags".
  - Kept as the spec fixes them: "Праг на шума 0,52 · NA 0,81" (bg-terms gives the full form for the term, the spec gives this short form for the row), "основно начално число" in the source lines (bg-terms row "main seed" says *главно*; ps_view already uses *основно*: the term table and the app disagree and need one decision), and the Bulgarian caution's "индекса си на Jaccard".
  - Open: the four `comparison.source.*` help keys share the ch. 2 "Datasets" entry, which describes every source state in one list; separate tooltips per state would need four guide entries.
  - Ch. 6 lists three limitations beyond the two the ticket names (Tag sets only, one dataset pair at a time, no significance or bands), each from the spec's "What it never claims" and "Out of scope".
