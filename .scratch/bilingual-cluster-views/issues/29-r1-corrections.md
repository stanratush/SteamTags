# 29: Apply the calibration corrections

**What to build:** every correction and term decision from the calibration review lands in the term table, the catalogue and G1. Any new instruction for the guide slices lands in the spec. G2–G10 start from the result.

**Blocked by:** 28

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Corrections flow through the term table", "Guide slice conventions". Source: [R1 Calibration review](28-r1-calibration-review.md), its Resolution and Comments.

- [ ] **Term decisions first**: each changed or confirmed row is updated in `bg-terms.md`, and its "proposed" mark is removed. For each changed term, the old word goes to its Avoid cell and to **Superseded words**, with allowed phrases where needed.
- [ ] **The sweep**: the superseded-word scan passes, so every old word is replaced in `src/steamstudy/i18n/bg/` and `docs/user-guide/bg/`, inflected forms included.
- [ ] **Wording corrections**: each one marked in the review is applied. Where the same fault recurs elsewhere in the catalogue or G1, it is fixed there too, and this issue's Comments list it.
- [ ] Any new instruction for the guide slices is added to the spec's Guide slice conventions, and the affected G issues are updated.
- [ ] The parity tests, the scan and the English tests pass. The app is checked in BG on the screens the corrections touched.
