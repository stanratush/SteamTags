# 26: A4 Bulgarian: selection text, In short labels and markers

**What to build:** the Bulgarian catalogue for every `selection_text` sentence ("Why this pair", the caveats, the constraint phrases, the null and subsample sentences, the Validation title, the methods paragraph), and a check that the Bulgarian In short label set and entry markers from issue 11 match the term table's Guide labels. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [ ] Every key the parity scan finds for `selection_text` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [ ] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [ ] Add `selection_text` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [ ] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [ ] **In the app, in BG**, at wide, medium and narrow widths: "Why this pair" for a chosen pair, a pair with caveats and a validated pair. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.
