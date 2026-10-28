# 38: G10 Bulgarian guide: 04, 05, Appendix B and the end of the ratchet

**What to build:** the last guide slice: `04-files.md` and `05-citing-and-reproducing.md`, and the generated Bulgarian Appendix B. Then the ratchet ends: the done-list is deleted, so every completeness check runs everywhere, and the release gate it guarded is removed.

**Blocked by:** 31, 37

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions; Strictness ratchet; Visibility and the release gate), "The Bulgarian User Guide" (Appendix B). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [ ] **Translate** `04-files.md` (~2.6k words on 2026-10-28, plus `cluster_games.csv` and the new connection columns) and `05-citing-and-reproducing.md` (~1.2k) into `docs/user-guide/bg/`, following the Guide slice conventions.
  - The methods paragraph in chapter 5 is exactly what `selection_text.methods_paragraph(text("bg"))` renders.
  - Column and file names, and quoted export text, stay English.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for R2.
- [ ] **Appendix B**: generate `docs/user-guide/bg/appendix-b-column-index.md` with `export/column_index.py`'s Bulgarian fixed labels. The staleness test now checks both files.
- [ ] **End of the ratchet**:
  - Delete `tests/i18n_done.py`. The catalogue and guide parity tests check completeness for every module and every guide file.
  - The Bulgarian verbatim test runs unconditionally.
  - Any skip that existed only for the ratchet is gone.
- [ ] **Release gate**: remove the "No release while `tests/i18n_done.py` exists" step from `docs/releasing-an-app-bundle.md`.
- [ ] The full test suite passes, including the superseded-word scan and the English content tests.
- [ ] In the app, in BG: every guide link from the app (each ⓘ, each column header with help) opens Bulgarian text. A script walks `HELP`, `PANEL_SECTIONS` and `ENTRY_BY_COLUMN` and confirms none falls back to English. Its output goes in the Comments.
