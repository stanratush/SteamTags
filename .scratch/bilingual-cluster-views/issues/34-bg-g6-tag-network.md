# 34: G6 Bulgarian guide: 03 The Tag Network

**What to build:** the Bulgarian translation of `## The Tag Network` of `03-metric-reference.md` (~4.9k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 33

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add this section to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## The Tag Network` (its opening paragraph and 13 entries) is translated into `docs/user-guide/bg/03-metric-reference.md`, from the English as it stood on 2026-10-29. The later sections stay English until G7–G9.
- **On `GUIDE_DONE`.** Every heading has its twin, the labels and markers match, and every In short block passes the form and 60-word test.
- **"Shown in the app as" lines** quote the Bulgarian Inspector labels from the catalogue (*„Общи игри“*, *„Ребра · в своя клъстер“*, *„Изпъкване в своя клъстер (z)“*, …), so the guide and the screen use the same words.
- **Avoid words:** the English *groups of tags* (Participation coefficient) and *a group* (Top-strength tag) mean Clusters, so they are *клъстери*, since *група* is an Avoid word for Cluster. *Група игри* (any group of games) is kept, as in G5.

**Choices for R2:**
- **Numbers:** as in G4 and G5. Prose is Bulgarian (*лифт 2,0*, *поне на 0,92*, *11,5 px*, *до 0,55*, *1116 × 678 пиксела*, *мащабирано по 1000*, *70%*). Formulas and arithmetic keep the English form (*s = (0.80 − 0.60) / 0.80 = 0.25*, *z = 15 / 11.18 = 1.34*, *1.5 × 15 пиксела*, *√(2.5 × …)*). The within-z cap example quotes the Bulgarian Inspector text: *„1,2 (макс. 1,7 в клъстер с 4 тага)“*.
- **Layout names** are the app's: *„Общо“*, *„По клъстери“* and *„Подреди“* in quotes, as chapter 2 writes them; the old *Re-layout* button, which no longer exists, keeps its English name.
- **Code inside the exact definition** (`forceatlas2_layout(visible network, weight = active weight …)`) is a code span and stays English, with Bulgarian prose around it.
- **хъб** appears once more, in *потискане на хъбовете* (ForceAtlas2's hub dissuasion). It has the Position entry's sense, a tag linked to almost every other, never the Cluster Center.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the entry titles: *Тегло на реброто (общи игри)*, *Лифт на реброто*, *Брой игри на тага*, *Степен и изолирани тагове*, *Сила (претеглена степен)*, *Силует на тага*, *Оценка на медоида*, *Таг с най-голяма сила*, *z-оценка на силата в клъстера*, *Коефициент на участие* (as Appendix A already wrote), *Позиции в изгледа*, *Тагове извън мрежата*;
- game set *множество игри*, medoid *медоид*, within-module degree *степен в модула*, population SD *SD на съвкупността*, edge inspector *инспектор на ребрата*;
- layout *изглед*, loose layout *свободно разположение*, spring layout *пружинно разположение*, gravity *гравитация*, main component *основен компонент*, hub dissuasion *потискане на хъбовете*;
- label-aware pass *преминаване, съобразено с етикетите*, box *кутия*, graph area *областта на графа*, zoom *приближение*, zoomed out *отдалечен*, packed *подредени плътно*, canvas *платно*, reference canvas *еталонно платно*.

**Checked in the app in BG:**
- **Tooltips:** with Action RPG selected, the Inspector's *Общи игри*, *Игри*, *Сума на общите игри*, *Сума на лифта*, *Общи игри в своя клъстер* and *Лифт в своя клъстер* carry the Bulgarian In short block.
- **The modal:** clicking the silhouette metric opens *Силует на тага (Per-tag silhouette)* in Bulgarian.
- **The next section:** the Cluster quality tab's silhouette and seed-spread tooltips (Clusters and partition quality) are still English, as the partial-chapter fallback should be.
