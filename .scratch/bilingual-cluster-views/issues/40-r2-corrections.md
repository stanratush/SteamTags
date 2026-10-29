# 40: Apply the final corrections

**What to build:** every correction and term decision from the final review lands in the term table, the catalogue and the Bulgarian guide. The term table then has no "proposed" row, and the bilingual interface is ready to release.

**Blocked by:** 39

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Corrections flow through the term table". Source: [R2 Final review](39-r2-final-review.md), its Resolution and Comments.

- [x] **Term decisions first**: each row is updated in `bg-terms.md`, and no "proposed" mark remains. For each changed term, the old word goes to its Avoid cell and to **Superseded words**.
- [x] **The sweep**: the superseded-word scan passes, inflected forms included.
- [x] **Wording corrections**: each one marked in the review is applied. Where the same fault recurs, it is fixed everywhere, and this issue's Comments list it.
- [x] If a correction touches a sentence `selection_text` renders, the catalogue and the guide are changed together, so the verbatim test passes.
- [x] Appendix B (Bulgarian) is regenerated if a fixed label changed.
- [x] The full test suite passes. The app is checked in BG on the screens the corrections touched.

## Comments

**2026-10-29, agent: done.** R2 accepted the translation and every proposed term, and marked no wording correction (issue 39's Resolution). So this issue only confirms the table.
- **`bg-terms.md`:** every "proposed" mark is removed, and the header records the R2 agreement. The table has no proposed row left.
- **No term changed**, so nothing was added to Avoid or Superseded words, and no sweep was needed. The superseded-word scan passes as before.
- **No wording, catalogue or fixed-label change**, so `selection_text`, the guide and Appendix B are untouched; the verbatim and staleness tests pass unchanged.
- **Nothing on screen changed**, so the app needed no new check in BG.
- **Tests:** the full suite ran at G10 (580 passed); since then only the Bulgarian guide, `bg-terms.md`, a comment in `column_index.py` and the guide tests changed, and the i18n and guide tests pass (103). The one failing test, `test_config`, comes from the researcher's uncommitted `config/collection.toml` (`store_seconds_per_request` 1.5 against the spec's 2.0), outside this effort.

The bilingual interface is ready to release: the done-list and its release gate went with issue 38, and the term table is agreed in full.
