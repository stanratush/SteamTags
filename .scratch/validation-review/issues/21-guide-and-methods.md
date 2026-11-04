# 21: User Guide, methods paragraph and bg-terms

**What to build:** the User Guide documents the new Validation, in English and Bulgarian, with the agreed text verbatim: both chapter 3 entries, the methods paragraph (in the guide and in `selection_text.methods_paragraph`), Appendix A's corrected attribution, the knock-on edits and the bg-terms rows.

**Blocked by:** 17, 20

**Status:** done

Spec: [Validation review spec](../spec.md): "User Guide and methods paragraph". Verbatim text and change lists: [guide-text.md](../prototypes/13-guide-wording/guide-text.md) §§1–5 and §7. Source: [What do the User Guide's validation passages and CONTEXT.md entries say, in English and Bulgarian?](13-guide-and-context-wording.md).

- [x] **`03-metric-reference.md#null-comparison`** (en and `bg/`): guide-text.md §1, applying each K/R/X/+ mark. The anchor stays.
- [x] **`03-metric-reference.md#subsample-stability`** (en and `bg/`): guide-text.md §2. The anchor stays.
- [x] **Methods paragraph:** the last two sentences replaced by §3 in `05-citing-and-reproducing.md` (both languages) and in `selection_text.methods_paragraph` with its bg catalogue entry, so `test_the_guides_methods_paragraph_is_the_report_template` and its Bulgarian twin pass. The report golden texts are regenerated if the paragraph is in them.
- [x] **Appendix A**, Cluster-wise Jaccard stability (both languages): §4.
- [x] **Knock-ons** (§5): the known-limitations bullet; "eight tables" in `05-citing` and `02-app-controls`; `04-files` (three validation tables, the `validation_pairs.csv` section, the replicates and clusters descriptions); Wilson (1927) in Appendix C. Appendix B was regenerated in issue 20; regenerate again if anything here changed a label.
- [x] **`docs/i18n/bg-terms.md`:** §7 (the "dissolved" row replaced, seven rows added). The superseded-word list is unchanged.
- [x] Every In short block passes the 60-word check (en 51 / 59, bg 55 / 59 in the asset); every guide link and every help anchor resolves.
- [x] Every card sentence the guide quotes matches issue 17's rendered text in each language.
- [x] CONTEXT.md is not changed.
- [x] The guide tests (`test_guide.py`, `test_guide_bg.py`), the superseded-word scan and the full test suite pass.

## Comments

- 2026-11-05 (agent): Done in c2ffd8c. Chapter 3 (both entries), Appendix A, the methods paragraph, the known-limitations bullet, "eight tables", Wilson (1927) and the bg-terms rows are copied verbatim from guide-text.md. Every block was copied by script and checked against the source.
- Two deviations:
  - The methods paragraph says "‹scan_seeds› Leiden runs" instead of "10 Leiden runs" (standards review). The runs use the configurable scan seeds, and the template fills the same value as "‹scan_seeds› seeds" earlier. The guide quote, the report template and its bg entry follow.
  - The bg-terms rows leave out the prototype's "(point 4)" and "(point 5)" notes.
- `test_hennigs_dissolution_is_the_only_jaccard_cut` became `test_hennigs_cuts_apply_per_subsample_and_fpcs_bands_stay_unused`: Appendix A now applies 0.5 and 0.75 per subsample, and the fpc bands on the mean stay unused. The report goldens differ only in the methods paragraph.
- Every quoted card sentence matches issue 17's rendered text in EN and BG, on the demo Build's Overall 17/2. CONTEXT.md is unchanged.
- Not acted on (standards review): CONTEXT.md has no entries for borderline, Not assessable, rarely assessable or per-pair procedure. The spec says CONTEXT.md does not change.
- Full suite: 635 passed.
