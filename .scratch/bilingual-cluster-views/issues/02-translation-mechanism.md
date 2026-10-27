# Translation mechanism
Type: grilling
Status: open
Blocked by: 01

## Question

How does the app show English or Bulgarian? This ticket decides the mechanism. Features 2–4 are then built with it from the start. Uses `grilling` + `domain-modeling` + `codebase-design`. Works from the [String inventory](01-string-inventory.md).

- Catalogue format: Python dict modules keyed by message id, or gettext `.po`/`.mo` (does that add a runtime dependency? [ADR 0001](../../../docs/adr/0001-app-bundle-wheels-not-frozen.md)). How strings with live values and plurals are written. How JS strings in `graph.js`/`workbench.js` get their text.
- Switching: a live callback re-render from a language store, or a page reload. What the switch keeps (the Network State, the selection, the open mode and tab, any running job). Where the switch sits, the default (English), and whether the choice is remembered per browser.
- The Bulgarian User Guide: a parallel `docs/user-guide/bg/` copy, with explicit stable anchor ids so `help.py` keys and code references stay language-independent. What happens when a Bulgarian entry is missing (fall back to English, or a test fails).
- Parity tests: every message id exists in both languages, every guide anchor exists in both, and the pinned-phrase tests run per language.
- Errors: the inventory found that `network`/`build` errors never reach the screen. Only the 8 Open Network State refusals in `app/export.py` do, shown as `Refused: …`. How do those get their Bulgarian text?
- Surfaced by the inventory:
  - `selection_text.py` renders the app (translated) and the English `selection_report.md` export in one process, so how is the language passed in?
  - Plurals: ~10 English-style sites, and Bulgarian needs a count form.
  - Numbers: `view.num()`, the `selection_text` number helpers and the grids' `d3.format`.
  - `workbench.js`: the `TIP_LABEL` regex and `pills()` clientside callback are keyed on English words.
  - The guide's In short labels and entry markers are parsed and tested by their English words. Do they stay as neutral markers or become a label set per language?
  - Appendix B is generated: is a Bulgarian copy generated too?
  - Schema `description` text shows as identifier-column header tooltips: translated, or left English as schema text?
  - Third-party widget text (ag-grid `localeText`, `dcc.Dropdown`, Plotly).
- Must not change any Network State key, export or cache key (map Notes).
