# 27: G1 Bulgarian guide: front matter, limitations, appendices A and C

**What to build:** the Bulgarian translation of `00-three-rules.md`, `01-getting-started.md`, `README.md`, `06-known-limitations.md`, `appendix-a-rules-of-thumb.md` and `appendix-c-references.md`, whole (~4.3k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent. `bg/README.md` replaces issue 11's stub.

**Blocked by:** 23, 24, 25, 26

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [ ] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [ ] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [ ] Add each of these files to `GUIDE_DONE` in `tests/i18n_done.py`.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [ ] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [ ] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.
