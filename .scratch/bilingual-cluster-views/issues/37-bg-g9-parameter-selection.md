# 37: G9 Bulgarian guide: 03 Parameter Selection

**What to build:** the Bulgarian translation of `## Parameter Selection` of `03-metric-reference.md` (~4.4k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 36

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [ ] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [ ] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [ ] Add `03-metric-reference.md` as a whole file (replacing G4–G8's section entries) to `GUIDE_DONE` in `tests/i18n_done.py`.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [ ] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [ ] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.
