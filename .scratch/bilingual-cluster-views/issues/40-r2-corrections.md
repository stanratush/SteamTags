# 40: Apply the final corrections

**What to build:** every correction and term decision from the final review lands in the term table, the catalogue and the Bulgarian guide. The term table then has no "proposed" row, and the bilingual interface is ready to release.

**Blocked by:** 39

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Corrections flow through the term table". Source: [R2 Final review](39-r2-final-review.md), its Resolution and Comments.

- [ ] **Term decisions first**: each row is updated in `bg-terms.md`, and no "proposed" mark remains. For each changed term, the old word goes to its Avoid cell and to **Superseded words**.
- [ ] **The sweep**: the superseded-word scan passes, inflected forms included.
- [ ] **Wording corrections**: each one marked in the review is applied. Where the same fault recurs, it is fixed everywhere, and this issue's Comments list it.
- [ ] If a correction touches a sentence `selection_text` renders, the catalogue and the guide are changed together, so the verbatim test passes.
- [ ] Appendix B (Bulgarian) is regenerated if a fixed label changed.
- [ ] The full test suite passes. The app is checked in BG on the screens the corrections touched.
