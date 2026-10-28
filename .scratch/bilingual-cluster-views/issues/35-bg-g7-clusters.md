# 35: G7 Bulgarian guide: 03 Clusters and partition quality

**What to build:** the Bulgarian translation of `## Clusters and partition quality` of `03-metric-reference.md` (~3.9k words on 2026-10-28, plus the Cluster connections changes and the Connection Ratio and Connection Share entries from issue 17), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 34

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [ ] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [ ] If the section has grown past ~5.5k words, translate up to a `###` entry boundary, open a follow-up issue for the rest (blocked by this one, blocking G8), and put only the translated entries' ids in the Comments; the section joins `GUIDE_DONE` when the follow-up finishes.
- [ ] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [ ] Add this section to `GUIDE_DONE` (or, if split, leave that to the follow-up) in `tests/i18n_done.py`.
- [ ] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [ ] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [ ] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.
