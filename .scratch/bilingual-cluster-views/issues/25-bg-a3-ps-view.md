# 25: A3 Bulgarian: Parameter Selection views

**What to build:** the Bulgarian catalogue for `ps_view.py` and the `ps_run` ETA and elapsed text: the Run section, the loading panel, the dataset strip, the heatmap's titles and hover text, the Pair Constraints and Selection settings sections, the Pair Inspector and the validation card. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [ ] Every key the parity scan finds for `ps_view`, `ps_run` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [ ] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [ ] Add `ps_view`, `ps_run` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [ ] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [ ] **In the app, in BG**, at wide, medium and narrow widths: the whole mode with a cached grid, a running job's progress and a pair with a validation card. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.
