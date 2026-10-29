# 35: G7 Bulgarian guide: 03 Clusters and partition quality

**What to build:** the Bulgarian translation of `## Clusters and partition quality` of `03-metric-reference.md` (~3.9k words on 2026-10-28, plus the Cluster connections changes and the Connection Ratio and Connection Share entries from issue 17), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 34

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] If the section has grown past ~5.5k words, translate up to a `###` entry boundary, open a follow-up issue for the rest (blocked by this one, blocking G8), and put only the translated entries' ids in the Comments; the section joins `GUIDE_DONE` when the follow-up finishes.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add this section to `GUIDE_DONE` (or, if split, leave that to the follow-up) in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## Clusters and partition quality` (its In short block, opening paragraphs and 14 entries, including Cluster connections, Connection Ratio, Connection Share and Games within a Cluster) is translated into `docs/user-guide/bg/03-metric-reference.md`, from the English as it stood on 2026-10-29. The section had 5367 words, under the ~5.5k split point, so it is one slice and joins `GUIDE_DONE` whole.
- **On `GUIDE_DONE`.** Every heading has its twin, the labels and markers match, and every In short block passes the form and 60-word test. That test caught eight blocks at 61–67 words (Modularity Q, Null-model baseline, Mean silhouette, Internal edges, Connection Ratio, Connection Share among them), now shortened.
- **"Shown in the app as" and quoted app lines** use the Bulgarian catalogue text: *„Клъстер“*, *„Игри“, „Тагове“, „Ребра“*, *„Покритие“*, *„Превишение над нулевия модел“*, *„Отношение“*, *„Дял“*, *„Съвпадащи“ и „от таговете ѝ“*, the null-model line *„Q … срещу нулевия модел … ± … (превишение …, z …; средният брой ребра в мрежите на нулевия модел е … срещу …)“*, the counts *„многотагови: 5 + еднотагови: 3“* and the silhouette label.
- ***Описателно: не е сравнимо между двойките.*** is the catalogue's wording; here *двойките* are Threshold Pairs, the one place the bare word is right.

**Choices for R2:**
- **Group without *група*:** the English says *groups* both for Clusters and for sets of tags or characteristics in general (*splits the tags into groups*, *groups of characteristics*, *the resolution limit's small groups*). *Група* is the Cluster's Avoid word, so these are *съвкупност* (*съвкупности от характеристики*), and *the grouping* is *структурата*. *Група игри* is kept as in G5 and G6.
- ***Връзка*** is used here, and only for Connections between Clusters (*Връзки между клъстерите*, *тежка връзка между два клъстера*), as the table reserves it.
- **Numbers:** as in G4–G6. Prose is Bulgarian (*0,31*, *от около −1,5 до 1,5*, *0,6875; 0,875 и 0,875*, *4120 общи игри*). Formulas keep the English form (*Q = 0.414*, *z = 0.12 / 0.01 = 12*, *1/21 ≈ 0.048*, *при γ = 1.00*). Quoted app text is Bulgarian as the app shows it (*„Q (γ = 1,00)“*, *„0,42 · превишение +0,11“*).
- **The Connection Ratio example** reads *Отношение 0,62 при γ = 1.00*: an expression with *=* keeps the English form under the rule used since G4. R2 may prefer *при γ 1,00*, as the app's pills write it.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the section and entry titles: *Клъстери и качество на разбиването*, *Етикети и брой на клъстерите*, *Размер на мрежата*, *Отправна стойност от нулевия модел*, *Превишение на модулярността и z-оценка*, *Покритие и дял на теглото между клъстерите*, *Несвързани клъстери*, *Среден силует*, *Вътрешни ребра, тегло и плътности*, *Тегло на среза и проводимост*, *Връзки между клъстерите*, *Игри в клъстера*;
- group *съвкупност*, grouping *структура*;
- resolution limit *граница на резолюцията*, objective *целева функция*, finding *находка*, pass mark *праг за преминаване*;
- cut weight *тегло на среза*, volume *обем*, edge density *плътност на ребрата*, weighted density *претеглена плътност*, induced subgraph *индуциран подграф*;
- permutation test *пермутационен тест*, sample SD *SD на извадката*.

**Checked in the app in BG** (after restarting the app, which caches the guide at start):
- **Tooltips:** the Cluster quality tab and the summary row carry the Bulgarian In short blocks of Cluster labels and counts, Network size, Modularity Q, Null-model baseline, Excess modularity, Coverage, Mean silhouette and Connection Ratio.
- **The modal:** clicking the Connections matrix's Ratio opens *Отношение на свързаност (Connection Ratio)* in Bulgarian; *Игри в клъстера (Games within a Cluster)* opens in Bulgarian too.
- **The next section**, *Stability*, still shows in English, as the partial-chapter fallback should.
