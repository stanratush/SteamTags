# 38: G10 Bulgarian guide: 04, 05, Appendix B and the end of the ratchet

**What to build:** the last guide slice: `04-files.md` and `05-citing-and-reproducing.md`, and the generated Bulgarian Appendix B. Then the ratchet ends: the done-list is deleted, so every completeness check runs everywhere, and the release gate it guarded is removed.

**Blocked by:** 31, 37

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions; Strictness ratchet; Visibility and the release gate), "The Bulgarian User Guide" (Appendix B). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] **Translate** `04-files.md` (~2.6k words on 2026-10-28, plus `cluster_games.csv` and the new connection columns) and `05-citing-and-reproducing.md` (~1.2k) into `docs/user-guide/bg/`, following the Guide slice conventions.
  - The methods paragraph in chapter 5 is exactly what `selection_text.methods_paragraph(text("bg"))` renders.
  - Column and file names, and quoted export text, stay English.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for R2.
- [x] **Appendix B**: generate `docs/user-guide/bg/appendix-b-column-index.md` with `export/column_index.py`'s Bulgarian fixed labels. The staleness test now checks both files.
- [x] **End of the ratchet**:
  - Delete `tests/i18n_done.py`. The catalogue and guide parity tests check completeness for every module and every guide file.
  - The Bulgarian verbatim test runs unconditionally.
  - Any skip that existed only for the ratchet is gone.
- [x] **Release gate**: remove the "No release while `tests/i18n_done.py` exists" step from `docs/releasing-an-app-bundle.md`.
- [x] The full test suite passes, including the superseded-word scan and the English content tests.
- [x] In the app, in BG: every guide link from the app (each ⓘ, each column header with help) opens Bulgarian text. A script walks `HELP`, `PANEL_SECTIONS` and `ENTRY_BY_COLUMN` and confirms none falls back to English. Its output goes in the Comments.

## Comments

**2026-10-29, agent: done.** The last guide slice and the end of the ratchet.
- **Translated:** `04-files.md` (every `##` group and all 55 file entries, `cluster_games.csv` and the connection columns included) and `05-citing-and-reproducing.md` into `docs/user-guide/bg/`. File headings stay as file names with their English slug (``### `edges.csv` {#edgescsv}``), and chapter 4's group headings (*Компилация: datasets/*) carry no English gloss, being places rather than terms; chapter 5's `##` headings give the English once, as entry headings do.
- **The methods paragraph** in chapter 5 is written from `selection_text.methods_paragraph(text("bg"))` itself, so it is the rendered text character for character; the verbatim test now runs unconditionally and passes. A sentence before it says `selection_report.md` stays English and this is the same paragraph in Bulgarian.
- **Appendix B:** `export/column_index.py` has `FIXED["bg"]`: the title with its `{#appendix-b-column-index}`, the introduction, the table header, the file-group labels and the schema's 18 app panels in Bulgarian. A report's own section names (`report.html: Clusters`, …) stay English, as the reports do; only *none* becomes *няма*. `python -m steamstudy.export.column_index` wrote `bg/appendix-b-column-index.md`; the English file is unchanged. The staleness test checks both files, and a new test fails on an app panel without a Bulgarian label.
- **End of the ratchet:** `tests/i18n_done.py` is deleted.
  - Catalogue parity (`i18n_parity.problems`) reports a missing entry in every area; its `done` parameter is gone.
  - Guide parity (`test_guide_bg.problems`) checks every English file: a missing Bulgarian file, or a missing twin of any heading, fails, and so do different In short labels or markers. The In short form and word-cap test runs over every Bulgarian file.
  - The methods-paragraph test lost its `skipif`. The tests that exercised "not done yet" now test the strict behaviour; the runtime fallback tests (splicing English into a partial chapter) stay, since the app still falls back at runtime.
- **Release gate:** the "No release while `tests/i18n_done.py` exists" step is gone from `docs/releasing-an-app-bundle.md`.

**Choices for R2:**
- **Quoted export text stays English:** the attribution line *"Player data: Steam Charts; tags/metadata: Steam store"*, the `parameter_selection.json` statuses *"partial, k of 153"* and *"not run"*, and *Avg. 0.00 and Peak 0*.
- **App labels are the catalogue's:** *„Експортирай състоянието на мрежата“*, *„Експортирай таблиците“*, *„Отвори състояние на мрежата…“*, *„Подреди“*, *„Заредени от експорт (не са изпълнени отново).“*, *„Настройки по подразбиране“ / „Персонализирани настройки: …“*. *The Cluster-quality row* is *редът от „Качество на клъстерите“*, as chapter 2 writes it.
- **Appendix B's file groups** are lowercase in their parentheses (*компилация: datasets/*), since they follow a file name.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the headings of chapters 4 and 5: *Компилация: datasets/* (and *reports/*, *analysis/*), *Експортиран zip на приложението*, *Файлове от избора на параметри*, *Файлове с метаданни*, *Посочете state_id*, *Депозирайте експортирания zip*, *Цитирайте софтуера и източниците*, *Отворете отново състояние*, *Отчетете избор на параметри*;
- byte-order mark *знак за реда на байтовете (BOM)*, header row *заглавен ред*, stacked *подредени един под друг*, joins to *свързва се с*, settings key *ключ на настройките*, record-only *само за документиране*;
- content descriptor *описател на съдържанието*, Adult Only notice *известието Adult Only*, config drift *отклонение в конфигурацията*, causal language *причинен език*, banner *предупредителна лента*, attribution line *ред за признание на източниците*;
- deposit *депозирам*, supplementary material *допълнителни материали*, self-contained *самодостатъчен*, fingerprint *пръстов отпечатък*, placeholder *заместител*;
- Appendix B's columns and file groups: *Панел в приложението*, *Раздел на доклада*, *Обяснена в*, *експортиран zip на приложението*, *папка на моментната снимка*, *zip от избора на параметри*.

**Every guide link from the app, in BG.** A script walks `HELP`, `PANEL_SECTIONS`, `ENTRY_BY_COLUMN` and `ENTRY_BY_FILE`, reads each target's own Bulgarian section and compares what the modal shows in BG and in EN. Its output:

```
HELP 91 keys, PANEL_SECTIONS 11, ENTRY_BY_COLUMN 194, ENTRY_BY_FILE 42: 119 distinct targets; English in BG: 0
```

**Checked in the app in BG** (after a restart): the Edges table's help popover shows the Bulgarian `edges.csv` entry; the modal shows *Отчетете избор на параметри (Report a Parameter Selection)* and *Приложение B. Индекс на колоните* in Bulgarian.
