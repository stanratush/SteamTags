# 25: User Guide entries and `selection.*` help keys

**What to build:** the User Guide content for Parameter Selection in the existing chapters, the shared methods template, the pinned statements and their tests, and the `selection.*` help keys the mode's `?` buttons will use. This lands before the mode, because the help tests require every key to resolve to a guide heading.

**Blocked by:** 22, 23

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Documentation and in-app help" (all but the Running Guide), "What it never claims", the fixed sentences in "The selection explanation" and "Validation block wording". Citation locators: [Research 01](../research/01-resolution-selection-formulas.md), [Research 02](../research/02-validation-methods.md), [Research 16](../research/16-citable-gamma-upper-bound.md).

- [x] **Ch. 1:** three modes.
- [x] **Ch. 2:** a "Parameter Selection mode" section with entries for:
  - Run, with the provenance-line paragraph;
  - Pair Constraints;
  - Selection settings, with the Lift / γ̂ heuristic sentence;
  - the dataset strip;
  - the heatmap and reason letters;
  - the Pair Inspector;
  - Apply to Workbench, with the Seed-Noise Floor paragraph;
  - Validate this pair;
  - Export tables.

  Each analytical control gets the parts the existing control-entry test requires.
- [x] **Ch. 3:** the "Parameter Selection" section.
  - "How Automatic Parameter Selection works" (the steps with links, and the dataset-strip sentence).
  - The eleven entries in the chapter's form: In short, Why it matters here, one **Exact definition**, *Example.*, *Bounds.* and *Compare with.* Examples use this Build's numbers from the spec.
  - "Three kinds of stability" at the top of the Stability section.
  - The descriptive paragraph added to Q, Coverage and Silhouette, and the Apply link added to the Seed-Noise Floor entry.
- [x] **Ch. 5:** "Report a Parameter Selection", including the methods paragraph with placeholders. **Ch. 6:** the new limitations.
- [x] **Appendix A:** the Cluster-wise Jaccard line on ≤ 0.5. **Appendix C:** Weir et al. 2017 and Gibson & Mucha 2022 with locators, and Hennig's §2.
- [x] `selection_text.METHODS_TEMPLATE`, with placeholders. It covers CHAMP, γ̂, Stable Partitions, the GM22 §J γ range with the unequal-size sentence, the widest-domain rule and the rejected alternatives, NA and its identical-graph rule, the constraints, both validation checks with the B* rule and floor scaling, why fpc's bands aren't applied, and the citations.
- [x] `HELP` gains `selection.*` keys for:
  - each heatmap metric;
  - Inspector label;
  - Pair Constraint field;
  - Selection Setting;
  - reason letter;
  - verdict tag;
  - Edge Overlap;
  - `selection.dataset_strip`;
  - `selection.run` (→ the ch. 3 overview);
  - `selection.apply` and `selection.validate` (→ ch. 2).
- [x] Tests:
  - `test_required_statements_in_the_metric_reference` and `test_known_limitations_chapter_holds_the_full_list` gain the spec's pinned strings.
  - The no-bands test allows only Hennig's "≤ 0.5 = dissolved" phrase in Appendix A.
  - A new test asserts that ch. 5's methods paragraph equals `METHODS_TEMPLATE` rendered with placeholders.
  - The existing help tests cover the new keys (each resolves to an entry with In short and Why it matters).
  - The no-unverified-sources test still passes.

## Comments

- 2026-10-27, implementation: Guide content in chapters 1–6 and Appendices A and C; `selection_text.METHODS_TEMPLATE` with `methods_paragraph()`; `selection.*` keys in `app/help.py` (`SELECTION_HELP`). The mode's hidden-tag and removed-tag help points at the ch. 2 Selection settings entry, because the Workbench's own hiding and removing controls deliberately carry no help.
