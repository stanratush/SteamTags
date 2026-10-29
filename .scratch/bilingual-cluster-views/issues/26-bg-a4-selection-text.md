# 26: A4 Bulgarian: selection text, In short labels and markers

**What to build:** the Bulgarian catalogue for every `selection_text` sentence ("Why this pair", the caveats, the constraint phrases, the null and subsample sentences, the Validation title, the methods paragraph), and a check that the Bulgarian In short label set and entry markers from issue 11 match the term table's Guide labels. All of it is written by the agent, in the register the term table sets.

**Blocked by:** 22

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md). Inventory: [research 01](../research/01-string-inventory.md).

- [x] Every key the parity scan finds for `selection_text` has a Bulgarian entry. Placeholders are kept, both plural forms are written (`other` in the count form, `{n} тага`), and numbers are left to `tx.num`.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `selection_text` to `CATALOGUE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] **In the app, in BG**, at wide, medium and narrow widths: "Why this pair" for a chosen pair, a pair with caveats and a validated pair. No English is left in these areas, apart from the never-translated words and third-party text without a prop. No label is clipped or overflows. Where Bulgarian is longer, the layout copes (wrap or ellipsis with a tooltip), without changing the English look. A screenshot of each area goes in the Comments.

## Comments

**2026-10-29, agent: done.** The `selection_text` catalogue has 82 entries: every sentence of `network/selection_text.py`, the settings and constraints labels of `network/selection.py`, the methods paragraph and the ten declared sentences. `selection_text` is on `CATALOGUE_DONE`. The English `selection_report.md` is unchanged: the golden report tests pass.

**The In short labels and markers:** a new test, `test_the_bulgarian_in_short_labels_and_markers_are_the_term_tables_guide_labels`, reads the term table's Guide labels and checks every Bulgarian `guide.LABELS` and `guide.MARKERS` word against it. All of them match. A marker is the label without its colon (*Внимание* for *Внимание:*).

**A code fix the parity scan needed:** the Null Comparison's "{k} of {r} also have a Selected Partition…" sentence reached `tx` through a variable, so the scan could not see its two forms, and they would have stayed English with no test failing. Both are now literal `tx(…)` calls, with the same English text.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R1:
- Default / Custom constraints *Ограничения по подразбиране* / *Персонализирани ограничения*, and the same for settings.
- robustness *робастност* (not *устойчивост*, which the table avoids for the stability terms), a coarser split *по-едро разбиване* (not *разделяне*).
- subset *подмножество*.
- The methods paragraph: adjusted Rand index *коригиран индекс на Rand*, self-consistent resolution *самосъгласувана резолюция*, upper envelope *горна обвивка*, curveball trades *размени curveball*, scaled by floor *мащабирани със закръгляне надолу*, mean best-match Jaccard *среден индекс на Jaccard за най-добро съвпадение*. Cauchy–Schwarz, Rand and Hennig stay in Latin script.
- Correction to issue 25: the pills' *custom* is *персонализирани*. It agrees with the plural *ограничения* and *настройки*, and the strip's marker takes the same word.

**Choices for R1 to look at:**
- **Number agreement**, as in issues 24 and 25:
  - Counts are written "label: n" wherever they could be 1: *Двойки с избрано разбиване: 153 от 153*, *разбъркани мрежи, които го достигат: {reach} от {r}*, *без ребра: {n}*.
  - The dissolved-cluster lead reads *Многотагови клъстери, разпаднати при нов избор (среден индекс на Jaccard ≤ 0,5): 1 от 4 — C4 (…)*.
  - *{n} qualify under {under}: {constraints}.* became *Квалифицирани при {under}: {n} ({constraints}).*
- **A shared key:** the constraint name "Multi-Tag Cluster" is also the Cluster view's subtitle, and catalogue keys are shared across areas. Its one Bulgarian entry is the subtitle's *Многотагов клъстер*. The sentence therefore puts the names after a colon: *Ограничения, които не изключиха нито една двойка: запазване на информацията, LCC и сравними съседи.* When the Multi-Tag Cluster constraint is on and excludes no pair, the list will read *… и Многотагов клъстер*, with a capital and in the singular. Fixing that needs either a context mechanism the catalogue does not have, or new English wording.
- **The other constraint names** are the Pair Constraints' own words (*запазване на информацията*, *дял на изолираните тагове*, *сравними съседи*), not the English short forms (retention, isolated-share, neighbour).
- **Raw numbers:** the methods paragraph writes *1000 прохода* and *0,5* in the Bulgarian number format in prose. The formulas (*⌊0.8·n⌋*) and section references keep their English form, as the Guide slice conventions require; the code review caught *⌊0,8·n⌋*.

**Checked in the app in BG** (Overall, the cached grid):
- **"Why this pair" for the chosen pair** g = 17, s = 2, with the labels line, the qualify and pick sentences, its own Neighbour Agreement and both caveats, at 1300 and 1024 px.
- **A pair with caveats:** the same view shows both NA caveats. The validation card shows the Null and Subsample caveats.
- **A validated pair:** the validation card's title, both paragraphs and the dissolved lead, at all three widths.
- **No qualifying pair:** Minimum Information Retention set to 1 and confirmed, in the page's store only, which a reload clears. The view showed *Нито една двойка не се квалифицира при персонализираните ограничения…* with the exclusion table, *Персонализирани ограничения: запазване на информацията ≥ 1 (по подразбиране 0,50)* and the strip's *няма квалифицирана двойка* with its marker.
- **The read-only lines** of the Selection settings: *Само Leiden: …*.
- **Layout:** no English is left in these areas, apart from tag names, dataset labels, ARI, LCC and the formulas. At 1300, 1024 and 700 px the page, `#ps-why`, `#ps-validation` and the strip have no horizontal overflow, and no clipped element (measured in the DOM).
- **Third-party text:** the number fields' stepper buttons carry Dash's English aria labels (*Decrease value*, *Increase value*). They have no prop, so they stay English.

**Screenshots** (in [screenshots/26/](../screenshots/26/)):
- `wide-why-this-pair.jpg`: "Why this pair" and the start of the validation card.
- `medium-why-this-pair.jpg`: the same at medium width, with the pill bar.
- `narrow-no-qualifying-pair.jpg`: no qualifying pair under custom constraints, and the exclusion table.
- `narrow-custom-constraints-no-qualifying-pair-strip.jpg`: the strip and pills under custom constraints. It was taken before the *персонализирани* correction, so it still shows *персонализирано*.
- `narrow-validation-card.jpg`: the validation card.
