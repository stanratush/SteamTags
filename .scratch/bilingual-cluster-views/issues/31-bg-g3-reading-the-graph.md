# 31: G3 Bulgarian guide: 02 Reading the graph to Parameter Selection mode

**What to build:** the Bulgarian translation of the rest of `02-app-controls.md`: `## Reading the graph`, `## Find a tag`, `## Window width and the three forms`, `## Task recipes` and `## Parameter Selection mode` (~4.6k words on 2026-10-28, plus the Inspector's Games, Connections and pair view and the Cluster quality tab's Connections matrix and Cluster map paragraphs), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 30

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `02-app-controls.md` as a whole file (replacing G2's section entries) to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** The rest of `02-app-controls.md` is translated: `## Reading the graph` (with Edge appearance and its six controls, Cluster map, Cluster colour, Position and Grey One-Tag Clusters), `## Find a tag`, `## Window width and the three forms`, `## Task recipes` and `## Parameter Selection mode` (nine entries). The source is the English as it stood on 2026-10-29. `bg/02-app-controls.md` is now the whole chapter, and `GUIDE_DONE` lists it as one file in place of G2's two sections.

**How the conventions applied:**
- **Entry headings:** every heading with an In short block gives the English term once, the `####` Edge appearance controls included (`#### Дебелина (Width) {#width}`). The task recipes and the plain `##` sections have no In short block, so they carry no English term.
- **Every In short block** passes the new form and word-cap test.
- **Quality words:** a scan for the banned words finds only glossary terms. *почти най-добри* is near-best, in the Heatmap and Validate entries, and *стабилност при подизвадки* is Subsample Stability. *претегля най-силно* became *дава най-голямо тегло*.
- **The app's words** are quoted as the BG app shows them:
  - *„Дебелина на ребрата: общи игри (√, 0,5–4 px) · скрити: 12“*, *„4 еднотагови“*, *„Мин. игри 8“*, *„γ 1,00“*;
  - the search reasons (*„скрит жанров таг“*, *„3 игри, под 8“*);
  - the Run rows, *Продължи (двойки прагове: k от 153)*, the provenance line, the strip's *„★ 14·2 NA 0,98“*;
  - the custom labels (*„Персонализирани ограничения: запазване на информацията ≥ 0,60 (по подразбиране 0,50)“*), the Apply line and the validation note.
- **Formulas keep their English number form**, as the conventions say, while the prose around them is Bulgarian: *0.4 + 2.6 × 30 / 60 = 1.7 пиксела*, *18 + 30 × √(20 / 80) = 33*.
- **Remove in the Pair Inspector** is the × button with the tooltip *Премахни (…)*, so the text writes *× („Премахни“)*.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the section titles: *Как се чете графът*, *Намерете таг*, *Ширина на прозореца и трите форми*, *Рецепти за задачи*;
- heatmap *топлинна карта*, reason letters *букви за причини*, dataset strip *лента с наборите*, the near-best set *множеството на почти най-добрите*;
- bubble *мехур*, histogram *хистограма*, handle *дръжка*;
- badge *значка*, verdict *извод*, provenance line *ред за произхода*, loading panel *панел за зареждане*;
- hub *хъб*, only in the Position entry, for a tag linked to almost every other one, and never for the Cluster Center.

**Checked in the app in BG:**
- **Tooltips:** the legend's Key, the Cluster map button, the one-tag chip and the thickness key carry the Bulgarian In short lines.
- **The guide modal** opens *Вид на ребрата (Edge appearance)*, *Сиви еднотагови клъстери (Grey One-Tag Clusters)*, *Топлинна карта и букви за причини (Heatmap and reason letters)* and *Приложи в работното място (Apply to Workbench)* in Bulgarian.
