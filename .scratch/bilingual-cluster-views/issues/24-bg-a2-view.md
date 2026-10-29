# 24: A2 Bulgarian: Workbench views

**What to build:** the Bulgarian catalogue for `view.py`: the Inspector views (tag, Cluster with its Games and Connections sections, pair, link, region), the Network State sentence, the quality lines, the tables' captions and the empty states. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [x] Every key the parity scan finds for `view` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `view` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] **In the app, in BG**, at wide, medium and narrow widths: each Inspector view, including a pair and a One-Tag Cluster, the Network State sentence and the quality lines. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.

## Comments

**2026-10-29, agent: done.** The `view` catalogue has 167 entries. The other 16 `view` keys already had entries from issue 23 (`Shared games`, `Lift`, `Seed`, `pool` and so on), and catalogue keys are shared across areas. `view` is on `CATALOGUE_DONE`.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R1:
- **Domain terms:**
  - null-model excess *превишение над нулевия модел*, null mean *средно за нулевия модел*, shuffled networks *разбъркани мрежи*;
  - game-set distance *разстояние по игри* (in full, *разстояние на Jaccard между множествата игри*);
  - reclustered *при нова клъстеризация*, clusters kept *запазени клъстери*;
  - screening flag *отметка за проверка*, flagged *отбелязан* (*флаг* is the Content Flag);
  - member *член*, partner *партньор*;
  - SD stays in Latin script.
- **Inspector plain names:** *Сума на общите игри*, *Сума на лифта*, *Изпъкване в своя клъстер (z)*, *Разпръснатост между клъстерите*, *Съответствие със своя клъстер (силует)*, *Пресичане на границата (проводимост)*, *Най-свързан член*. The guide slices must give the same names in "Shown in the app as".
- **Short UI words:** Unhide *Покажи*, Show JSON *Покажи JSON*, copied *копирано*.

**Choices for R1 to look at:**
- **Number agreement:**
  - A count that can be 1, before a noun with a count form, is written "label: n" in plain messages: *Отбелязани тагове: {flagged} от {n}*. The app check found "0 от 1 тага" in the Removal Sensitivity footer after a one-tag run, and this fixed it.
  - "{n} of the dataset's {total} games pass…" became *Филтърът за минимум месеци пропуска {n} от {total} игри в набора*, so no verb has to agree with {n}.
- **The Network State sentence** uses *Топ-{rows}* (as in *набор Топ-100*) and *наблюдавани месеци ≥ {months}*.
- **Status codes are left as they are** inside *н/д ({status})* and *няма ({status})*, e.g. `too_few`. They are values of an export column.

**Checked in the app in BG, at 1300, 1024 and 700 px.** Each view was checked from the page's text, filtered for English words; the only Latin text left is tag names, game titles, dataset labels, Louvain/Leiden, ids and column names.
- **Tag view:**
  - *Таг 3859 · C1 (26 тага)*;
  - *77 игри в мрежата имат този таг*;
  - the Metrics labels, with notes such as *използва се за клъстеризацията* and *макс. 5,0 в клъстер с 26 тага…*;
  - its Removal Sensitivity section, after a run for that tag.
- **Link view:** *Между C1 и C2*, and *Игри с двата тага*.
- **Multi-Tag Cluster:**
  - *C1 · 26 тага · Многотагов клъстер* and its metrics;
  - Members;
  - Games, with *99 от 100 игри имат поне един от неговите 26 тага* and *Покажи всички 99*;
  - Connections, with *по отношение на свързаност*.
- **One-Tag Cluster:** *C4 · 1 таг · Еднотагов клъстер*, *9 игри имат неговия таг*, and its Games table without the constant columns.
- **Pair view:** *Двойка клъстери*, both *Дял на свързаност* rows, and *Ребра между тях*.
- **Missing tag:** *Таг 9 · извън мрежата · скрит жанров таг · 24 игри от набора имат този таг · Покажи*.
- **Search options:** *В мрежата · 59*, *C2 · 14 игри*.
- **Summary row, Network State sentence, quality boxes and lines, Network State table, Connections matrix:** in Bulgarian.
- **No horizontal page overflow at any width.**
- **Wide Inspector tables:** they are wider than the 304 px Inspector in English too (Members: 507 px in EN, 598 px in BG), and the Inspector scrolls sideways for them in both languages, so nothing new is clipped.
- **Wrapping:** at 1300 px the tab bar and the quality boxes wrap onto a second row, and the pair view's *0,69 от γ = 1,00* wraps inside its cell.

**Still English, owned by other slices:** the help tooltips' text, which comes from the guide (G slices), and ag-grid's hidden pagination words.

**Screenshots** (in [screenshots/24/](../screenshots/24/)):
- `wide-cluster-view-summary-quality.jpg`: the Multi-Tag Cluster view, the summary row, the sentence and the quality boxes.
- `wide-pair-view.jpg`: the pair view.
- `medium-floating-inspector-quality.jpg`: medium width, with the floating Inspector and the quality lines.
- `narrow-pair-view.jpg`: the pair view at narrow width.
- `wide-tag-view-metrics-and-removal-sensitivity.jpg`: the tag view's Metrics and Removal Sensitivity, after the fix below.
- `wide-tag-view-before-kv-fix.jpg`: the same view before the fix.
- `wide-link-view.jpg`: the link view.
- `wide-one-tag-cluster.jpg`: the One-Tag Cluster view.
- `wide-missing-tag.jpg`: the missing-tag view.
- `narrow-tag-view-metrics.jpg`: the tag view's Metrics at narrow width.
- `wide-cluster-view-EN-for-comparison.jpg`: the Members table in English, clipped by the Inspector edge the same way as in BG.

**Code review (2026-10-29), what changed:**
- **Number agreement:**
  - The quality line's cluster counts now read *многотагови: {multi} + еднотагови: {one}*.
  - The footer reads *очакваният среден брой отбелязани би бил около {expected}*.
  - The two average edge counts are *средният брой ребра в … е {n}*.
  - None of them can now read "1 многотагови" or "1 ребра".
- **The pool after a preposition:** *Таг ({group})* and *Дял на свързаност: {group}*. *пул на еднотаговите клъстери* would otherwise need its article after *в* or *на*.
- **Wording:**
  - Unhide is *Покажи отново*.
  - Total is *Сума*, as in *Сума на общите игри*.
  - The Connections note is *по отношението на свързаност*.
  - The silhouette note is *не е критерий за избор*.
- **`bg-terms.md`:** the Inspector names row moved to "Metric and method names".
- **The tag view's Metrics were squeezed.** In BG the longer labels left the value column 43 px wide, so notes such as *използва се за клъстеризацията* wrapped one word per line (`wide-tag-view-before-kv-fix.jpg`). The fix:
  - `ui_words` now carries the language code, and `workbench.js` `uiWords` sets `<html lang>`, which also helps screen readers.
  - `app.css` caps the label column at 58% under `:lang(bg)`.
  - In BG the columns are now 176 px for labels and 116 px for values; in EN they stay 214 / 78 px.
  - Test: `test_the_ui_words_carry_the_language_for_the_pages_lang_attribute`.
- **Left for R1:**
  - Status codes such as `too_few` show raw in *н/д ({status})*, in BG and in EN alike. They are values of export columns, and translating them would mean a code change in `view.py`.
  - *Louvain по лифт* / *по общи игри*: the weight word comes from the shared `lift` / `shared games` entries.

