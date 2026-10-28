# 23: A1 Bulgarian: layout, callbacks, JS words and widgets

**What to build:** the Bulgarian catalogue for every string issue 12 wired: the static layout, the callbacks' messages, the `OpenRefused` reasons, `ui-words` (the JS and CSS words, including the Edge appearance and Cluster map cards), ag-grid `localeText` and the schema header tooltips. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [x] Every key the parity scan finds for `layout`, `callbacks`, `refusals`, `ui_words`, `schema_tips` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `layout`, `callbacks`, `refusals`, `ui_words`, `schema_tips` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] **In the app, in BG**, at wide, medium and narrow widths: the header, the Controls column, every tab's labels and captions, the Edge appearance card, the Cluster map card and an Open Network State refusal. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.

## Comments

**2026-10-28, agent: done.** 205 entries: `layout` 136, `callbacks` 40, `refusals` 8, `schema_tips` 21. `ui_words` has no keys of its own: the JS and CSS words (the pill bar, the Edge appearance card, the Cluster map) are `tx` calls in `layout.py`, so they are in the `layout` catalogue. All five areas are on `CATALOGUE_DONE`.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R1:
- Domain terms: User Guide *ръководство за потребителя* (short *ръководството*); guide entry *статия*; defining tag *определящ таг*; replicate *повторение*; source / target tag *изходен / целеви таг*; tag id *идентификатор на таг*.
- Panels: Dataset *Набор от данни*; Export *Експорт*, *Експортирай състоянието на мрежата*; app cache *кеш на приложението*; Key *Легенда*.
- Short UI words: Run *Изпълни*, Cancel *Отказ*, Restore *Възстанови*, Reset *Нулирай*, Reset all *Нулирай всичко*, Close *Затвори*; Tidy *Подреди*; *Мин. игри*, *Мин. общи*, *Месеци ≥*; the drawing *изображението*; job *задача*.

**Choices for R1 to look at:**
- **"State" is always qualified**, per the table: the Controls section and its pill read *Състояние на мрежата*. The button is *Експортирай състоянието на мрежата*, and the refusals and the Open message say *състояние на мрежата*.
- **Counts with a possible 1 use a "label: n" order** in plain messages, so no plural form is needed: *скрити: {n}*, *грешки: {n}*, *тагове {done} от {total}*, *двойки прагове: {done} от {total}*.
- **Left as they are:**
  - exports' names and code words: `mode: test`, `parse_errors_allowed`, `--allow-parse-errors`, `state_id`, `schema_version`, `key_version`, `<UTC timestamp>`, `one_tag_pool`;
  - `px`, `ms` and `s`;
  - Louvain and Leiden.

**Two layout fixes the Bulgarian needed** (the English look is unchanged, checked in the app):
- **Export button.** *Експортирай състоянието на мрежата* overflowed the 264 px Controls column, because `.btn` never wraps. `.controls .btn` now wraps within the column (`app.css`), so the button takes two lines in BG and still one in EN.
- **Region titles in the Cluster-separated layout.** They were the English label from `network/layout.py` ("C1 · 26 tags"); only the pool's title was translated. Now the server sends every region's tag count (`render_graph`, test `test_every_region_sends_its_tag_count_for_a_title_in_the_interface_language`), and `graph.js` `regionTitle` titles each Cluster's region from `ui-words` `map.tags`: *C1 · 26 тага*. A language switch re-titles every region.

**Checked in the app in BG, at 1500, 1100 and 760 px.** Each check covered the header, the Controls column, the tabs, the graph's buttons, the legend's key, the Edge appearance card (both layouts, so *Ребра между клъстерите* shows too), the Cluster map card and an Open refusal (*Отказано: нито експортен zip файл, нито export.json*).
- **No English is left in these areas**, apart from never-translated words: tag names, dataset labels, Louvain/Leiden, `C1…` and file names.
- **No horizontal overflow at any width**, and no clipped text node. A script compared each element's box with the viewport and each text node's scroll width with its client width.
- **ag-grid's hidden pagination panel** still holds its English words ("Page Size:", "Page", "to", "of"). No grid paginates, so they are never shown, and they were left alone.
- **Still English, owned by other slices:** the summary row, the Network State sentence, the quality boxes and the Connections matrix toggles (`view.py`, issue 24).
- **Not caused by this slice:** at 1100 px, after a resize, the separated layout's region titles can overlap. English does the same.

**Screenshots** (in [screenshots/23/](../screenshots/23/)):
- `wide-controls-separated.jpg`: the Controls column with the wrapped Export button, and the separated layout.
- `wide-edge-card.jpg`: the Edge appearance card.
- `wide-open-refusal-before-wrap-fix.jpg`: an Open refusal, and the clipped Export button before the fix.
- `wide-open-refusal-and-clusters-tab.jpg`: the same refusal after the fix, with the wrapped Export button and the Clusters tab.
- `medium.jpg`: medium width.
- `narrow-pill-bar.jpg`: the header and the pill bar at narrow width.
- `narrow-edge-card-and-cluster-map.jpg`: both cards together at narrow width.

**Code review (2026-10-28), what changed:**
- **Bulgarian text:**
  - The Export caption's second *състояние* is now qualified: *състояние на мрежата*.
  - A list comma before *и* is gone.
  - The Selection Settings key reads *ключ на настройките на избора*.
  - Tidy's tooltip is now an imperative: *Подреди графа около преместените възли; само позициите*.
- **Tooltip register:** a rule in `bg-terms.md`, marked proposed. A tooltip that names a control's action uses the short imperative; one that tells the reader what to do with the mouse uses *вие*.
- **Proposed rows:**
  - *Отказ* is recorded as the one noun exception for Cancel.
  - New rows for Language, Search, Clear search, Graph only and the two "or equal to" ag-grid filters.
  - The User Guide row now says both of its words are proposed.
- **Code:**
  - `regionTitle` uses `graph.js`'s `fill`.
  - `render_graph` uses `V.POOL`.
  - The region-count test now checks against the Clusters table, not against the code's own expression.
  - `bg/ui_words.py` says why it is empty.
- **CSS checked in EN:** every Controls-column button stays on one line (Restore, Reset all, Export this state, Open Network State…, Clear app cache). The column is a fixed 264 px, so the result does not depend on the window width.
