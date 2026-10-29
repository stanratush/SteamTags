# 25: A3 Bulgarian: Parameter Selection views

**What to build:** the Bulgarian catalogue for `ps_view.py` and the `ps_run` ETA and elapsed text: the Run section, the loading panel, the dataset strip, the heatmap's titles and hover text, the Pair Constraints and Selection settings sections, the Pair Inspector and the validation card. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [x] Every key the parity scan finds for `ps_view`, `ps_run` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `ps_view`, `ps_run` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] **In the app, in BG**, at wide, medium and narrow widths: the whole mode with a cached grid, a running job's progress and a pair with a validation card. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.

## Comments

**2026-10-29, agent: done.** The `ps_view` catalogue has 120 entries and `ps_run` 5. The other `ps_view` keys already had entries from issues 23 and 24 (`Run`, `Cancel`, `Close`, `Lift`, `Metrics`, `Clusters`, `Coverage`, `Silhouette` and so on). Both areas are on `CATALOGUE_DONE`.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R1:
- **Domain terms:**
  - isolated share *дял на изолираните тагове*, LCC share *дял на LCC* (LCC in Latin script, like ARI);
  - comparable neighbours *сравними съседи*, near-best *почти най-добри*, tolerance *допуск*;
  - NA (the heatmap's and the strip's short Neighbour Agreement) stays in Latin script;
  - scan *сканиране*, scan seed *начално число от сканирането*, scan range *обхват на сканирането*, hits *попадения*, the CHAMP envelope *обвивка*;
  - Validation *валидиране*, Validate this pair *Валидирай тази двойка*; Null Comparison keeps its own name, which avoids *валидиране*;
  - the Subsample Stability arms: arm *вариант*, re-selected *при нов избор*, at resolution *при резолюцията*;
  - dissolved *разпаднат*;
  - Neighbour links *сравнения със съседите*: *връзки* is Connections and *ребра* is edges, so neither fits a link between two grid cells;
  - qualifies *квалифицира се*.
- **Short UI words:** Pair Inspector *Инспектор на двойката*, Apply to Workbench *Приложи в работното място*, Copy from Workbench *Копирай от работното място*, Reset to defaults *Върни стойностите по подразбиране*, Confirm *Потвърди*, Use these settings *Използвай тези настройки*, and the pills' default / custom *по подразбиране* / *персонализирани* (plural, agreeing with *ограничения* and *настройки*; corrected in issue 26).

**Choices for R1 to look at:**
- **Number agreement**, as in issue 24: a count that can be 1 or that sits before a noun is written "label: n", e.g. *решетка: двойки {done} от {total}*, *начални числа за сканирането: {seeds}*, *стойности: {n}*. The loading panel's sentence puts each count in parentheses after its noun: *двойки прагове (153) × резолюции (91–327) × начални числа (10)*. The ETA reads *до края: около {n} min*, so no verb agrees with {n}.
- **Units** stay `min` and `s`, as `ms` and `s` already do in the callbacks' estimate.
- **Raw codes are left as they are**: the link status (`ok`), the Workbench flag (`not_representable`, `not_reproduced`), the `clipped_high` badge, the No Selected Partition reason, and the dataset key in the loading panel's *Набор 1 от 1 (puzzle)*. All are export values, and English shows them the same way.

**A code fix the Bulgarian needed:** the Pair Constraints' defaults beside each field were raw Python floats, so BG showed *по подразбиране 0.5*. `_default_text` now writes a float with `tx.fixed(value, "g")`: *по подразбиране 0,5* in BG, and *default 0.5* in EN exactly as before. Test: `test_a_pair_constraints_default_is_written_in_the_languages_number_format`.

**A layout fix:** the metric picker is one segmented row with `overflow: hidden`. In BG its options were 942 px in a 615 px row at 1300 px, so the Seed-Noise Floor and Q were cut off. Under `:lang(bg)` it now wraps onto a second row (`app.css`). English is unchanged. It is also cut there (672 in 615 px, Q hidden at 1300 px), which predates this slice and is left as it is.

**Checked in the app in BG, at 1300, 1024 and 700 px:**
- **The whole mode with a cached grid** (Overall): the Run section with its rows, the cache line, the Pair Constraints with their defaults, the Selection settings and their read-only lines, the strip, the metric picker, the heatmap's axes, colour bar and hover text, the key, and the Pair Inspector with badges, Metrics, the descriptive block, the neighbour table, CHAMP, Clusters and the compact validation line.
- **A running job's progress:** Run Puzzle, then *Изчисляване на избора на параметри*, the search sentence, *Набор 1 от 1 (puzzle): решетка, двойки 0 от 153.*, the one-off note and *оценяване… · изминало време: 0 s*. The run was cancelled before any pair finished, so the app cache gained nothing.
- **A pair with a validation card:** the Overall chosen pair g = 17, s = 2, with the cluster table, where *Разпаднат* fits in its cell.
- **Medium:** the pill bar (*Изпълни готови 1 от 5*, *Ограничения за двойката по подразбиране*), the Pair Constraints popover, and the floating Pair Inspector from a heatmap pick (g = 12, s = 11).
- **Narrow:** the pill bar wraps onto two rows, and the floating Pair Inspector fits. No horizontal page overflow at any width.

**Still English, owned by other slices:** every `selection_text` sentence (*Leiden only…*, "Why this pair", the caveats, the validation sentences, *Descriptive: not comparable across pairs*) and the *Default constraints* / *Default settings* labels: issue 26. The `?` tooltips come from the guide (G slices).

**Screenshots** (in [screenshots/25/](../screenshots/25/)):
- `wide-mode-cached-grid.jpg`: the whole mode, with the wrapped metric picker.
- `wide-validation-card-and-pair-inspector.jpg`: the validation card's cluster table, and the Pair Inspector's CHAMP, Clusters and Validation.
- `wide-running-job-loading-panel.jpg`: a running job's loading panel and Run rows.
- `medium-pair-constraints-pill.jpg`: the pill bar and the Pair Constraints popover.
- `medium-floating-pair-inspector.jpg`: the floating Pair Inspector.
- `narrow-pill-bar-and-pair-inspector.jpg`: narrow width.
