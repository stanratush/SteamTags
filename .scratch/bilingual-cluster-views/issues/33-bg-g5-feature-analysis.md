# 33: G5 Bulgarian guide: 03 Feature analysis

**What to build:** the Bulgarian translation of `## Feature analysis` of `03-metric-reference.md` (~4.5k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 32

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add this section to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## Feature analysis` (its opening paragraph and 17 entries) is translated into `docs/user-guide/bg/03-metric-reference.md`, from the English as it stood on 2026-10-29. The later sections stay English until G6–G9.
- **On `GUIDE_DONE`.** Every heading has its twin, the labels and markers match, and every In short block passes the form and 60-word test. That test caught Genre frequency at 63 words, now shortened; the longest blocks are Phi coefficient and Benjamini-Hochberg q at 59.
- **Avoid words:** *връзка* is never used for a relation between tags (it is Connections): *каквато и да е зависимостта между двата тага*, *рядък таг, който винаги идва с чест*. *Общност* is avoided too: community-voted is *поставят с гласуване от потребителите на Steam*. *Сила на асоциацията* appears only in the van Eck & Waltman citation, as the table allows.

**Choices for R2:**
- ***етикет* for labels other than `C1…`**: `kind` is *етикет от конфигурацията*, and Free To Play is a *търговски етикет*, following the chip row ("*етикет*, which is a label"). R2 should say whether a Genre value next to *етикет* reads too much like a tag.
- **Numbers:** prose decimals are Bulgarian (*Дял 0,63*, *0,17 за тагове на 10 и 60 игри*). Arithmetic and formulas keep the English form (*0.63 / 0.21 = 3.0*, *30 / 70 = 0.43*, *q ≤ 0.05*, *phi = 0.27*, *p = 0.002*, and the BH example *q = 0.004, 0.02, 0.04, 0.04*), as in G4. A value written right after a column name in backticks is a quoted column value and keeps it too (*`share` 0.63*, *`baseline_share` 0.21*).
- **Tag pairs** are *двойка тагове*, because *двойка* alone is the Threshold Pair. The bare word is kept only for the pairs inside a combination (*тройка отпада, когато подкрепата ѝ е равна на тази на някоя от нейните двойки*) and in the sentence right after a qualified mention. The term table's row says the same.
- **Tag names stay English** inside examples: *„23 от 100-те игри носят едновременно Roguelike, Action и Pixel Graphics“* replaces the English *pixel-art action roguelikes*, which would need translated tag names. Steam's archived category names (Genres, Themes & Moods, …) and Genre values (Indie, Free To Play, Early Access) stay English.
- **Quotations** are translated in „…“: Brin et al.'s *„клетките с висок интерес имат ниски бройки“*.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the entry titles: *Брой и дял на тага*, *Медианна позиция на тага*, *Базово ниво в пула на годните игри*, *Отношение на дяловете* (as Appendix A already wrote), *Архивна категория на тага*, *Честота на жанровете*, *Подкрепа на комбинацията*, *Лифт на комбинацията*, *Достоверност*, *Бройки за двойка тагове*, *Лифт на двойка тагове*;
- combination *комбинация*, support *подкрепа*, confidence *достоверност*, association rule *асоциативно правило*, *двойки и тройки тагове*;
- co-occurrence *съвместно срещане*, independence *независимост*, interest *интерес*, association table *таблица на асоциациите*;
- *коефициент phi*, *стойност p от точния тест на Fisher* (short *p на Fisher*), *q на Benjamini-Hochberg*, *H на Loevinger*, false discovery rate *очакван дял на фалшивите открития*;
- screen *отсяване*, chance finding *случайна находка*, over- / under-represented *свръхпредставен* / *недостатъчно представен*;
- generic tag *широк таг* (not *общ*, which means shared), medoid score *оценка на медоида*, business label *търговски етикет*, gameplay genre *жанр на геймплея*.

**Checked in the app in BG:**
- **No ⓘ entry point:** no app control or column header opens these entries; the feature-analysis tables are not on any app screen. So there is no tooltip to check.
- **The modal**, driven to `#share-ratio`, `#phi-coefficient` and `#benjamini-hochberg-q`, shows the Bulgarian entries.
- **The next section**, *The Tag Network*, still shows in English, as the partial-chapter fallback should. Its *Jaccard index* link opens the Bulgarian *Индекс на Jaccard (Jaccard index)*.
