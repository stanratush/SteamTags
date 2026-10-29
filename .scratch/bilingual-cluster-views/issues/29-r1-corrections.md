# 29: Apply the calibration corrections

**What to build:** every correction and term decision from the calibration review lands in the term table, the catalogue and G1. Any new instruction for the guide slices lands in the spec. G2–G10 start from the result.

**Blocked by:** 28

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Corrections flow through the term table", "Guide slice conventions". Source: [R1 Calibration review](28-r1-calibration-review.md), its Resolution and Comments.

- [x] **Term decisions first**: each changed or confirmed row is updated in `bg-terms.md`, and its "proposed" mark is removed. For each changed term, the old word goes to its Avoid cell and to **Superseded words**, with allowed phrases where needed.
- [x] **The sweep**: the superseded-word scan passes, so every old word is replaced in `src/steamstudy/i18n/bg/` and `docs/user-guide/bg/`, inflected forms included.
- [x] **Wording corrections**: each one marked in the review is applied. Where the same fault recurs elsewhere in the catalogue or G1, it is fixed there too, and this issue's Comments list it.
- [x] Any new instruction for the guide slices is added to the spec's Guide slice conventions, and the affected G issues are updated.
- [x] The parity tests, the scan and the English tests pass. The app is checked in BG on the screens the corrections touched.

## Comments

**2026-10-29, agent: done.** R1 accepted every proposed term and marked no wording correction (issue 28's Resolution). So this issue only confirms the table.
- **`bg-terms.md`:**
  - every "proposed" mark is removed, including the register note on tooltips (from issue 23) and the References note (from issue 27);
  - the header records the R1 agreement.
- **No term changed**, so nothing was added to Avoid or Superseded words, and no sweep was needed. The superseded-word scan passes as before.
- **No new instruction** for the guide slices: the spec's Guide slice conventions and issues 30–38 are unchanged.
- **Nothing on screen changed**, so the app needed no new check in BG. The parity, scan and English tests pass.
