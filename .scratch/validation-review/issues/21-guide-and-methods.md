# 21: User Guide, methods paragraph and bg-terms

**What to build:** the User Guide documents the new Validation, in English and Bulgarian, with the agreed text verbatim: both chapter 3 entries, the methods paragraph (in the guide and in `selection_text.methods_paragraph`), Appendix A's corrected attribution, the knock-on edits and the bg-terms rows.

**Blocked by:** 17, 20

**Status:** ready-for-agent

Spec: [Validation review spec](../spec.md): "User Guide and methods paragraph". Verbatim text and change lists: [guide-text.md](../prototypes/13-guide-wording/guide-text.md) §§1–5 and §7. Source: [What do the User Guide's validation passages and CONTEXT.md entries say, in English and Bulgarian?](13-guide-and-context-wording.md).

- [ ] **`03-metric-reference.md#null-comparison`** (en and `bg/`): guide-text.md §1, applying each K/R/X/+ mark. The anchor stays.
- [ ] **`03-metric-reference.md#subsample-stability`** (en and `bg/`): guide-text.md §2. The anchor stays.
- [ ] **Methods paragraph:** the last two sentences replaced by §3 in `05-citing-and-reproducing.md` (both languages) and in `selection_text.methods_paragraph` with its bg catalogue entry, so `test_the_guides_methods_paragraph_is_the_report_template` and its Bulgarian twin pass. The report golden texts are regenerated if the paragraph is in them.
- [ ] **Appendix A**, Cluster-wise Jaccard stability (both languages): §4.
- [ ] **Knock-ons** (§5): the known-limitations bullet; "eight tables" in `05-citing` and `02-app-controls`; `04-files` (three validation tables, the `validation_pairs.csv` section, the replicates and clusters descriptions); Wilson (1927) in Appendix C. Appendix B was regenerated in issue 20; regenerate again if anything here changed a label.
- [ ] **`docs/i18n/bg-terms.md`:** §7 (the "dissolved" row replaced, seven rows added). The superseded-word list is unchanged.
- [ ] Every In short block passes the 60-word check (en 51 / 59, bg 55 / 59 in the asset); every guide link and every help anchor resolves.
- [ ] Every card sentence the guide quotes matches issue 17's rendered text in each language.
- [ ] CONTEXT.md is not changed.
- [ ] The guide tests (`test_guide.py`, `test_guide_bg.py`), the superseded-word scan and the full test suite pass.
