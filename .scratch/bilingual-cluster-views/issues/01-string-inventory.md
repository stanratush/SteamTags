# String inventory
Type: task
Status: resolved
Blocked by: none

## Question

Before the [Translation mechanism](02-translation-mechanism.md) can be chosen: where does every user-visible string in the app come from, and how many are there? This is AFK work. The output is a table in `research/01-string-inventory.md`.

- By source: `app/layout.py`, `view.py`, `ps_view.py`, `callbacks.py` (including error and warning texts), `renderer.py`, `export.py`/`ps_export.py` (only the messages shown in the app), `network/selection_text.py`, `analysis/templates.py` (Analysis Report mode), `assets/graph.js` and `workbench.js`, `app.css` (`content:` strings), and the User Guide (`guide.py`/`help.py` lookups by file and heading anchor).
- For each source: the string count, whether strings are literals, f-strings or templates with live values, and whether a test pins the exact wording (`tests/test_guide.py`, `test_app.py`, phrase-pinning tests).
- Which strings are data and never get translated: tag names, game titles, Genre values, `C1…` labels, export column names.
- Which guide anchors are referenced from code, and how they are derived (heading slugs). A Bulgarian heading would change its slug.

## Answer

- **App: about 500 string sites**, about 3 in 10 with live values. Most are in `view.py` (~150), `ps_view.py` (~138), `layout.py` (~88), `selection_text.py` (~58) and `callbacks.py` (~34). `workbench.js` has ~6 plus a tooltip regex keyed on English labels, and `graph.js` has none. `app.css` has one (`" copied"`). About 10 plural sites are written English style (`'s'`, `(s)`, `is`/`are`). About 60 number-format calls go through `view.num()` and `selection_text` helpers, and the grids use `d3.format`. About 70 test asserts pin English wording.
- **Correction to this ticket's list:** `analysis/templates.py` is not Analysis Report mode. It renders the Build's `report.html` files, which are exported files and stay English. Analysis Report mode is `layout.py` + `view.py`. Errors from `network`/`build` never reach the screen. Only the 8 Open Network State refusals in `app/export.py` do.
- **One source, two languages:** `selection_text.py` feeds the app and the English `selection_report.md` export, and 3 of its sentences must appear verbatim in the guide. The language must be a parameter, not process-wide.
- **Guide: 50,316 words, 225 headings.** Code references 109 distinct anchors (`PANEL_SECTIONS`, `HELP`, the schema's `guide_entry`), and the guide links to itself 433 times. All anchors are slugs of English heading text. The In short labels and entry markers (`*Why it matters here.*`, `**Exact definition:**`, `Shown in the app as “…”`) are parsed or tested by their English words. Appendix B is generated from the schema. `bg/` would ship in the wheel and the App Bundle with no packaging change.
- **Never translated:** tag names, game titles, Genre values, `C1…`, export column and file names. Grid headers *are* column names, so they stay English. Open: dataset labels (`Overall`, `Puzzle`, …) go to [Bulgarian terminology](03-bulgarian-terminology.md). The schema `description` shown as identifier-column tooltips goes to [Translation mechanism](02-translation-mechanism.md).
- Full inventory: [research/01-string-inventory.md](../research/01-string-inventory.md).
