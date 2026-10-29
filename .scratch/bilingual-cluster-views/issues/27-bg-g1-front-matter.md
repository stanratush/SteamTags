# 27: G1 Bulgarian guide: front matter, limitations, appendices A and C

**What to build:** the Bulgarian translation of `00-three-rules.md`, `01-getting-started.md`, `README.md`, `06-known-limitations.md`, `appendix-a-rules-of-thumb.md` and `appendix-c-references.md`, whole (~4.3k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent. `bg/README.md` replaces issue 11's stub.

**Blocked by:** 23, 24, 25, 26

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add each of these files to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** All six files are translated whole into `docs/user-guide/bg/`, from the English as it stood on 2026-10-29 (unchanged since 2026-10-28). `bg/README.md` replaces issue 11's stub. All six are on `GUIDE_DONE`. The structure parity, link and superseded-word tests pass.

**How the conventions applied here:**
- **Headings:** every heading has the English slug as its `{#id}`, at the same level and in the same order. G1 has no glossary entries and no In short blocks, so no heading carries the English term and no label set is used.
- **Links:** in-guide links keep their targets. A link out of the guide gains one `../`, because `bg/` sits one level deeper, so it reaches the same file: `../../running-guide.md#the-app`, `../../../CONTEXT.md`. The Running Guide and CONTEXT.md stay English, and the README says so: *(на английски)*.
- **The app's words** are written as the BG app shows them, from the catalogues:
  - the summary row: *„100 от 100“*, *„0,17 · превишение +0,11“*;
  - the two quality sentences, in their Bulgarian form with the English example's numbers;
  - the tabs, the Connections matrix's *Отношение* / *Дял (ред → колона)* / *Таблица*, and *Покажи всички*, *Съвпадащи*, *от таговете ѝ*;
  - the buttons: *← Назад*, *Подреди*, *Премахни тага*, *Изпълни за този таг*, *Приложи в работното място*, *Скрий ребрата под*;
  - *скрито от изображението* and *покажи двойката клъстери*.
- **Messages that stay English:** the launcher's refusal message (*„This App Bundle needs Python 3.12, 3.13 or 3.14“*) is quoted in English, because the launcher has no Interface Language. macOS's Open is given as *Open или Отвори*.
- **Numbers** in prose are in the Bulgarian format: *0,3*, *10000*, *80%*. Version numbers, ports and code spans are unchanged.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R1:
- rule of thumb *емпирично правило*, band *гранична зона*, cut-off *гранична стойност*, reference point *отправна точка*; *праг* is avoided here, because it is the thresholds g and s;
- pipeline *конвейер*, repository *хранилище*, parse errors *грешки при разбора*, feature analysis *анализ на характеристиките*;
- delisted *премахнат от магазина*, region-locked *с регионални ограничения*;
- the UI shapes: summary row *ред с обобщението*, dotted label *пунктиран етикет*, pill bar *лента с бутони*, floating card *плаваща карта*, bottom sheet *долен панел*;
- the chapter titles in Contents (*Три правила*, *Първи стъпки*, *Настройки на приложението*, *Справочник на метриките*, *Какво има във всеки файл*, *Цитиране и възпроизвеждане на състояние на мрежата*, *Известни ограничения*), which later slices should use for their `#` headings;
- **References:** the bibliographic entries stay as published, and only the guide's locators are Bulgarian (*резюме*, *табл.*, *ур.*, *фиг.*, *с.*, *теорема*, *лема*, *следствие*, *твърдение*, *деф.*). The methods paragraph in `selection_text` now uses *фиг.* to match.

**Choices for R1 to look at:**
- **Quotations from the literature** (Appendix A, and *„субективно тълкуване“*) are translated into Bulgarian in „…“, with the citation kept. The alternative is to keep the English original and add a translation.
- ***консенсусно разбиване*** is in the Avoid column as a wrong word for the Stable Partition. Chapter 6 uses it in its literal sense: "No consensus partition is computed."
- ***разделения*** for "divisions" in Newman's quotation: *разделяне* is in the Avoid column for partition, but this word translates the source's own word.
- ***хъб*** appears in Appendix A for Guimerà and Amaral's term, and the text says the guide avoids it for Cluster Centers, as the English does.

**Checked in the app in BG:**
- **The Inspector panel's `?`** opens the modal on *Разгледайте възел, ребро или клъстер* with the Bulgarian text.
- **Its in-guide links** go to `#help:03-metric-reference.md#games-within-a-cluster` and similar. Clicked, the modal shows that section in English, because G6 has not translated it yet, with *← Назад* in Bulgarian.
- **The Dataset panel's `?`** opens *Заредете набор от данни* in Bulgarian.
- **Other panels** (Network, Filters, Export) open their English sections, which are later slices.
- **Tooltips:** none of these six files has an In short entry, so no tooltip comes from G1.
- **No screenshot:** the browser pane was hidden while this was checked, so screenshots failed. The modal's text was read from the page instead.

**Word count:** about 4.9k Bulgarian words, against 4.8k English words.

**Code review (2026-10-29), what changed across issues 25–27:**
- **Appendix A:**
  - "weak and possibly artificial" is now *слаба и възможно изкуствена*; *вероятно* had changed the band's meaning to "probably".
  - "partitioning methods" is now *методи за разбиване*, not *разделяне*, which is an Avoid word.
  - Hennig's "dissolved" is *„разпаднат“*, the table's term.
- **Chapter 6:** *пропуски в проследяването*. *покритие* is the Coverage metric.
- **Chapter 1:**
  - dropped an added aside, *(бутонът „Премахни тага“; …)*;
  - restored the bold on *режима*.
- **The methods paragraph** (`selection_text`):
  - the formula is *⌊0.8·n⌋* again, since formulas keep their English form;
  - bands are *гранични зони*;
  - *със {constraints}* and *определящия таг* for the grammar.
- **The cluster table:** its *absent* header is the noun *отсъствия*.
- **`_default_text`** writes a float default as `tx.figure(str(value))`. The earlier `format(value, "g")` would have turned an English "default 1.0" into "default 1". The test now covers 1.0.
- **`bg-terms.md`:**
  - its header now says that two tests read it;
  - the ETA's Latin `min` / `s` are recorded as proposed.
- **Left for R1:**
  - the shared "Multi-Tag Cluster" key (issue 26);
  - the raw codes on screen (`ok`, `not_representable`, `clipped_high`);
  - *общности* inside the translated quotations of Appendix A (*структура от общности*). The table exempts only *откриване на общности*, and community structure is the sources' own term.

