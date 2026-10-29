# 32: G4 Bulgarian guide: 03 opening sections and Ranking and data

**What to build:** the Bulgarian translation of `## How to read this chapter`, `## Settings that change the numbers` and `## Ranking and data` of `03-metric-reference.md` (~4.7k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 29

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add these three sections to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## How to read this chapter`, `## Settings that change the numbers` (with its table) and `## Ranking and data` (14 entries) are translated into `docs/user-guide/bg/03-metric-reference.md`, from the English as it stood on 2026-10-29.
- **The file carries the chapter title**, *Справочник на метриките*. The sections after Ranking and data stay English until G5–G9.
- **All three sections are on `GUIDE_DONE`.** Every heading has its twin, the labels and markers match, and every In short block passes the form and 60-word test. That test caught Impact report at 68 words, now shortened. The quality-word scan finds nothing.

**Choices for R2:**
- **Numbers:**
  - Thousands lose their separator in prose and in the worked example's arithmetic: *(50000 + 30000) / 2 = 40000*, *7412*, *10000*. English writes them with commas, which read as decimal commas in Bulgarian.
  - Decimals in that arithmetic and in the formulas keep their English form, as the conventions say. Quoted column values keep it too: *Avg. Players 0.00*, the CSV rows in code spans.
  - Prose decimals are Bulgarian: *0,60 и 0,53 средни играчи*, *0,3*.
- **Dates** are written the Bulgarian way: *26 февруари 2016 г.*, *през март 2024 г.*
- **Steam names stay English:** Peak Players and Avg. Players, the Steam Charts column names, are written as Steam shows them; the Bulgarian term is used for the study's own Monthly Avg. Players. *Top Games* and Desktop Companion stay English as Steam's names.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the section titles: *Как да четете тази глава*, *Настройки, които променят числата*, *Ранжиране и данни*;
- would-be rank *хипотетичен ранг*, near miss *близък пропуск*, impact report *доклад за въздействието*, completeness counts *бройки за пълнота*, depth check *проверка на дълбочината*;
- listing pass *преминаване през списъка*, listing rank *позиция в списъка*, a declined game *отслабнала*;
- concurrent players *едновременни играчи*, idle game *игра с изчакване*;
- tie *равенство*, tie-break *разрешаване на равенството*;
- tag vocabulary *речник на таговете*, parsers *програми за разбор*, SteamDB batch *партида от SteamDB*, reviewer *рецензент*.

**Checked in the app in BG:**
- **No direct entry point:** no app control opens these entries, because the ranking data is not on any app screen and identifier columns have no help. So there is no tooltip to check.
- **The modal**, opened from the Minimum Months Filter entry and then following in-guide links, shows *Наблюдавани месеци (Months Observed)* and *Как да четете тази глава* in Bulgarian.
- **The next section**, *Tag count and share*, still shows in English, as the partial-chapter fallback should.
