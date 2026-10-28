# 24: A2 Bulgarian: Workbench views

**What to build:** the Bulgarian catalogue for `view.py`: the Inspector views (tag, Cluster with its Games and Connections sections, pair, link, region), the Network State sentence, the quality lines, the tables' captions and the empty states. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [ ] Every key the parity scan finds for `view` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [ ] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [ ] Add `view` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [ ] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [ ] **In the app, in BG**, at wide, medium and narrow widths: each Inspector view, including a pair and a One-Tag Cluster, the Network State sentence and the quality lines. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.
