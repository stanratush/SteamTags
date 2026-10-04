# 25: User Guide: metric reference

**What to build:** Chapter 3 of the User Guide explains every exported metric to a non-specialist, in concept order. Each entry has prose and a worked example; bounds, reference points and the project's own comparisons (null model, Seed-Noise Floor, Eligible Pool); and one closing "Exact definition" line. No entry uses interpretation bands. The source is the metric-reference draft from the wayfinding effort, corrected by its citation verification.

**Blocked by:** 23

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "User Guide and Running Guide" (chapter 3 and its required content).

- [x] Concept order: ranking and data → feature analysis → network → clusters and partition quality → stability → Removal Sensitivity. Every `guide_entry` anchor in the schema has its entry, and the ticket 23 tests pass.
- [x] Each entry: prose, then a worked example, then bounds, then reference points (lift 1 / phi 0 = independence; ARI 1 identical, ≈0 chance; Q 0 = no better than random) and the project's own comparisons, then one marked "Exact definition" line. No bands anywhere.
- [x] Content comes from the wayfinding metric-reference draft (ticket 26 research: 63 entries and the settings table), with every "Required change" from the citation-verification research (ticket 30) applied first.
- [x] Required statements:
  - the Membership Stability size effect (2-tag 0.5 vs 20-tag 0.05);
  - `within_z` not comparable across sizes, with the √(n−1) cap as a derivation;
  - the `share_ratio` pull towards 1 and its ceiling;
  - triple lift possibly inherited from one pair;
  - ΔQ including lost edge weight;
  - expected chance flags;
  - `modularity_z` never read alone (Karrer et al. 2008 §I);
  - weighted adaptations of unweighted originals (Fortunato 2010, Guimerà & Amaral 2005);
  - the Li & Zhang 2020 Q facts as the only "typical values" context.
- [x] Every number in a worked example is recomputed against the implemented code or a hand calculation, not copied unchecked from the draft.

## Comments

- 2026-10-04 (agent): Written: docs/user-guide/03-metric-reference.md, 71 entries in concept order with example / bounds / compare-with / exact definition, research-30 corrections and tickets 27-28 decisions applied. Worked examples rechecked in code (Fisher p, BH, ARI, phi max, within_z, triple lift, Q); the draft's 'moving 4 tags: ARI 0.80' is 0.83 for the configuration described and was corrected.
