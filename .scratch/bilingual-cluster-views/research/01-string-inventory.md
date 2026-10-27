# Research 01: String inventory

Answers [ticket 01](../issues/01-string-inventory.md). The question: where does every user-visible string in the app come from, how many are there, and what will a translation mechanism have to handle? The decision belongs to [ticket 02](../issues/02-translation-mechanism.md). Checked 2026-10-27 on branch `bilingual-cluster-views` at `bdd85fb`.

## Method

- Python sources: a throwaway AST pass (kept outside the repo) listed every string constant and f-string that looks like prose: docstrings, ids, CSS classes, dict keys and regexes were dropped. Then I filtered the lists by hand: component property names, HTML scaffolding and strings that only go into exports were removed.
- JS and CSS: read by hand.
- Counts are **approximate (±10%)**. They count string *sites*, so a label used in two places counts twice. They are for sizing the work, not for a checklist. The parity tests chosen in ticket 02 become the exact list.

## 1. Sources of visible strings

| Source | Shown where | Visible strings | Form | Tests that pin the wording |
|---|---|---|---|---|
| [`app/layout.py`](../../../src/steamstudy/app/layout.py) | Workbench and Analysis Report mode chrome: mode switch, tab names, control labels, buttons, dropdown placeholders, loading text, panel titles ("1 Dataset" … "7 Export") | ~88 | Literals. 3 f-strings, one with an English plural (`Genre Tag{'' if n == 1 else 's'}`) | `test_ps_app` (the mode labels as a list), `test_layout` (1) |
| [`app/view.py`](../../../src/steamstudy/app/view.py) | Inspector (node, edge, cluster, not-in-network), summary numbers, quality lines, Seed-Noise Floor line, Network State sentence, Analysis Report §1 table, the 28 `INSPECTOR_LABELS` | ~150 | ~95 literals, ~55 f-strings with live values. 4 inline plurals, also with verb agreement (`has`/`have`), and 1 `(s)`. `num()` formats 41 values with a decimal point and writes `n/a`, `yes`, `no` | `test_app` (most of its 29 phrase asserts, e.g. `reason_text(...) == "Genre Tag hidden"`). `test_guide`: each `INSPECTOR_LABELS` key must appear as `Shown in the app as “<label>”` in its guide entry |
| [`app/ps_view.py`](../../../src/steamstudy/app/ps_view.py) | The whole Parameter Selection mode: strip, pills, loading panel, heatmap hover and axis titles (Plotly), Pair Inspector, Validation block, reason letters | ~138 | ~110 literals, ~29 f-strings. 1 `(s)`. 19 `num()` calls. Plotly hover text is an f-string with `<br>` | `test_ps_app` (30 phrase asserts: `"not run"`, `"Searching 9 Threshold Pairs"`, `"Computed when this bundle was made: Python …"`, …) |
| [`app/callbacks.py`](../../../src/steamstudy/app/callbacks.py) | Banners (test Build, version drift, parse errors), Opened-state line, help for the export panel, empty Inspector states, Removal Sensitivity footers and stale notes, cache line, Continue buttons, `Refused: …` | ~34 | 15 literals, 19 f-strings | `test_app` (`"Continue (2 of N done)"`) |
| [`app/app_cache.py`](../../../src/steamstudy/app/app_cache.py) | The "Clear app cache" result | 1 | f-string with two `(s)` plurals | `test_app` (`startswith("Cleared 1 cached …")`) |
| [`app/renderer.py`](../../../src/steamstudy/app/renderer.py) | Legend line `Edge thickness: shared games` | 2 | f-string | — |
| [`app/export.py`](../../../src/steamstudy/app/export.py) | The 8 reasons Open Network State is refused, shown as `Refused: <reason>` | 8 | Mostly f-strings with paths and versions. Its 3 other prose strings (Cluster Center rule, label rule, null model) go into `export.json` and stay English | — |
| [`app/ps_export.py`](../../../src/steamstudy/app/ps_export.py) | Nothing in the app: all its text goes into the Parameter Selection export zip | 0 | — | — |
| [`app/ps_run.py`](../../../src/steamstudy/app/ps_run.py) | Progress: `estimating…`, `about N min left`, `N min N s elapsed` | 5 | f-strings | — |
| [`app/server.py`](../../../src/steamstudy/app/server.py) | Browser tab title `Tag Network` | 1 | Literal | — |
| [`app/help.py`](../../../src/steamstudy/app/help.py) | Tooltip lines `Now: …` and `Column:` / `Columns: … (file)` | 3 | f-strings. These labels are re-parsed by `workbench.js` (§3) | `test_guide` indirectly |
| [`app/guide.py`](../../../src/steamstudy/app/guide.py) | 2 help-modal fallbacks (file not installed, section not found). Plus the 6 In short labels, which are guide *syntax* read from the guide (§4) | 2 + 6 markers | f-strings | `test_guide` |
| [`network/selection_text.py`](../../../src/steamstudy/network/selection_text.py) | Parameter Selection explanations: "Why this pair", caveats, constraint phrases, null and subsample sentences, Validation title, methods paragraph | ~58 | ~26 literals (some are `.format` templates with named fields), ~32 f-strings. 3 `_n(count, one, many)` plurals, 3 inline `is`/`are`, and English list joining (`", and "`) | `test_guide` (3 of its sentences must appear verbatim in the guide), `test_selection` (5), `test_validation` (3), `test_ps_app` |
| [`assets/workbench.js`](../../../src/steamstudy/app/assets/workbench.js) | Tooltip footer `Click for the full User Guide entry`, column-header ⓘ `aria-label`, pill summaries (`N Genre Tags + defining`, `Lift`/`Shared games`, `N of M`) | ~6 | Template literals, 1 plural. The pills repeat `layout.py`'s words in JS | — |
| [`assets/graph.js`](../../../src/steamstudy/app/assets/graph.js) | None. Every node, region and cluster label it draws comes from Python as data | 0 | — | — |
| [`assets/app.css`](../../../src/steamstudy/app/assets/app.css) | `" copied"` after the state id is clicked (`.copy-id.copied::after`) | 1 | CSS `content:` | — |
| Third-party widgets | ag-grid (filter menus, "No Rows To Show"), `dcc.Dropdown` (empty-search text), Plotly | not counted | Each library's own locale option (ag-grid `localeText`), or left English | — |
| **App total** | | **~500** | | ~70 phrase asserts across `test_app`, `test_ps_app`, `test_selection`, `test_validation`, `test_app_only`, `test_layout` |

### Not app strings, contrary to the ticket's list

- [`analysis/templates.py`](../../../src/steamstudy/analysis/templates.py) is **not** Analysis Report mode. It renders two Build files at build time: `analysis/report.html` (via `analysis/report.py`) and `reports/reports.html` (via `build/summary.py`). The app never shows them. They are exported files, so they **stay English**. Its causal-language check (`CausalLanguageError`) is an English word list from config, and it stays English with them. Analysis Report mode is `layout.py` + `view.py` reusing the Workbench components (`view.py` "Analysis Report §1").
- [`app/loader.py`](../../../src/steamstudy/app/loader.py): its 2 errors are raised at server start-up and show in the terminal. That is the CLI, which stays English.
- Errors raised deep in `network/` and `build/` (15 `raise …Error(f"…")` sites) never reach the screen as text. `callbacks.py` catches only `BuildNotFound` and `OpenRefused`, both from `app/export.py` (8 reasons, counted above). Anything else is an internal guard (e.g. `ps_run.py`'s `validation needs a complete grid`).

### Shared with English-only exports

These strings feed both the app (to be translated) and an exported file (stays English). The mechanism must render them in both languages from one source:

- `selection_text.py` → the app's Parameter Selection mode **and** `selection_report.md` in the Parameter Selection export zip (`ps_export.py`) **and** the guide (`test_the_guides_methods_paragraph_is_the_report_template` requires `methods_paragraph()` verbatim in chapter 5).
- `view.py`'s Network State sentence and quality lines are view only. The export carries the numbers, not these sentences. Confirm in ticket 02.

## 2. Strings that are data and are never translated

| Data | Where it comes from | Note |
|---|---|---|
| Steam tag names | Build datasets | Also the Inspector titles, `Find a tag…` options, legend chips |
| Game titles, AppIDs | Build datasets | Inspector game lists |
| Steam Genre values | Build datasets | "Hidden Genre Tags" options |
| Cluster labels `C1…` | `metrics` | Also the region titles in `graph.js` |
| Export column and file names | [`export/schema.py`](../../../src/steamstudy/export/schema.py) | The grids' `headerName` **is** the column name (`view.column_defs`), so grid headers stay English. The tooltip's `Column: n_games (nodes.csv)` line keeps the names but its `Column:` label is translated |
| Dataset labels `Overall`, `Puzzle`, `RPG`, `Strategy`, `Simulation` | [`config/datasets.toml`](../../../config/datasets.toml) | **Open**: config data, but read as words. Ticket 03's term table decides. They also appear in exports |
| Algorithm names `Louvain`, `Leiden`, `CHAMP`, `ARI`, `LCC`, `Q`, `γ`, `R`, `K` | literals | Names and symbols, presumably kept. Ticket 03 confirms |
| `state_id`, Build ids, versions, file paths | live values | Never translated |

A grey zone for ticket 02: schema column `description` text appears as the **header tooltip** of identifier columns (`view.column_defs`, `headerTooltip: col.description`). It is English documentation in `export/schema.py`. About 120 app-export columns, part of them identifiers. Either it gets a translation path or it stays English as schema text.

## 3. JS that parses English

- `workbench.js` `TIP_LABEL = /^(In short\.|Higher →|Lower →|Raising it →|Here:|Caution:|Now:|Columns?:|Field:)\s*/` turns tooltip lines into styled paragraphs. With Bulgarian labels the regex must accept them (or the tooltip should arrive as structured data rather than labelled text).
- `workbench.js` `pills()` is a clientside callback that rebuilds pill text in JS from raw values, repeating `layout.py`'s words. It needs the language as an input, or must receive its words from Python.
- `HELP_LINK = "#help:"` is language-neutral.

## 4. The User Guide

| File | Lines | Words | Headings | Internal links | In short blocks |
|---|---:|---:|---:|---:|---:|
| `00-three-rules.md` | 15 | 255 | 4 | 2 | 0 |
| `01-getting-started.md` | 48 | 1,437 | 5 | 5 | 0 |
| `02-app-controls.md` | 554 | 8,573 | 39 | 28 | 27 |
| `03-metric-reference.md` | 2,062 | 26,972 | 92 | 44 | 85 |
| `04-files.md` | 239 | 2,553 | 61 | 2 | 0 |
| `05-citing-and-reproducing.md` | 49 | 1,248 | 6 | 1 | 2 |
| `06-known-limitations.md` | 42 | 683 | 5 | 0 | 0 |
| `appendix-a-rules-of-thumb.md` | 42 | 791 | 7 | 1 | 0 |
| `appendix-b-column-index.md` (generated) | 343 | 6,723 | 1 | 338 | 0 |
| `appendix-c-references.md` | 46 | 894 | 3 | 0 | 0 |
| `README.md` | 23 | 187 | 2 | 12 | 0 |
| **Total** | **3,463** | **50,316** | **225** | **433** | **114** |

About 43,600 words to translate by hand. Appendix B is generated by [`export/column_index.py`](../../../src/steamstudy/export/column_index.py) from the schema. It is mostly column names, file names and links, with a few fixed labels (`GROUP_LABEL`, its header). A Bulgarian Appendix B means generating it a second time with Bulgarian labels, not translating the file. `test_committed_column_index_is_not_stale` compares the committed file byte for byte.

### Anchors: how code finds guide text

- `guide.slug()` derives the anchor from the heading text, GitHub style. Its `\w` is Unicode, so a Cyrillic heading gives a valid but **different** slug. A translated heading breaks every lookup below unless anchors are made explicit.
- Code references **109 distinct anchors**:
  - `guide.PANEL_SECTIONS`: 11 panels → (file, anchor).
  - `help.HELP`: 81 keys → 49 distinct (file, anchor) pairs, together with `PANEL_SECTIONS`.
  - The export schema's `guide_entry`: 80 distinct chapter-3 anchors, from [`export/guide_index.py`](../../../src/steamstudy/export/guide_index.py) `ENTRY_BY_COLUMN`. They are reused by `help.column_entry` (Inspector labels, grid header ⓘ) and by Appendix B's links.
- The guide links to itself 433 times by `file.md#anchor`. The help modal follows those links (`guide.modal_links`, `test_every_in_guide_link_the_modal_follows_points_to_an_existing_heading`).
- Tests also pin headings **by text**: `CONTROL_ENTRIES` (12 headings under "Analytical controls explained", in order), `GRAPH_ENTRIES` (5 under "Reading the graph"), and the three `##` headings in `00-three-rules.md`. They check the anchor by passing the English heading through `slug()`.

### English syntax the parsers and tests rely on

- `guide.IN_SHORT_LABELS` = `In short.`, `Higher →`, `Lower →`, `Raising it →`, `Here:`, `Caution:`. `in_short()` finds them as `**label**` in the blockquote under a heading, and `in_short_problems()` checks their order and a 60-word cap. Both the parser and the tooltip regex (§3) are keyed on the English words.
- Entry markers that tests require: `*Why it matters here.*`, `**Exact definition:**`, `*Example.*`, `*Bounds.*`, `*Compare with.*`, `*Caution.*`, `Shown in the app as “…”`.
- Content tests read English: the banned quality words (`good`, `strong`, `stable`, … in In short blocks, glossary terms exempt), "no interpretation bands", required statements (~20 phrases in chapter 3, ~22 in chapter 6), the Hennig ≤ 0.5 sentence in Appendix A, sources that must never be cited, and the three `selection_text` sentences that must appear verbatim. Ticket 02 decides which of these run per language, which are structural (marker present) and which stay English-only.

### Packaging

- `pyproject.toml` force-includes the whole `docs/user-guide` folder as `steamstudy/guide`, so a `bg/` subfolder would ship in the wheel with no change.
- `bundle/make.py` copies `docs/user-guide` into the App Bundle as `User Guide/`, so a `bg/` subfolder would appear there too, beside the English files.

## 5. Facts for the mechanism decision (ticket 02)

1. **Volume.** ~500 app string sites, roughly 3 in 10 with live values. ~10 plural sites, all written English style (`'' if n == 1 else 's'`, `(s)`, `is`/`are`, `has`/`have`). Bulgarian needs singular/plural plus a count form for masculine nouns (`2 тага`), so plurals need a real rule, not a suffix.
2. **Numbers.** `view.num()` (60 calls across `view.py`, `ps_view.py`, `callbacks.py`) and `selection_text._pct`/`_range`/`_signed` format with `f"{x:.Nf}"`. Grids format with `d3.format('.3~f')` in JS. A decimal comma on screen touches these three helpers plus the grid formatter. Exports never call them.
3. **One source, two languages at once.** `selection_text.py` renders the app (translated) and `selection_report.md` (English) in the same process, so the language has to be a parameter, not a process-wide setting.
4. **JS.** Only `workbench.js` holds English: 1 regex, 1 footer, 1 aria-label, the pill words. `graph.js` holds none.
5. **Guide anchors.** 109 code-referenced anchors plus 433 in-guide links are derived from English heading text. A Bulgarian guide needs explicit, language-independent anchor ids on its headings, or a heading map, before any heading is translated.
6. **Guide syntax.** The In short labels and entry markers are parsed or tested by their English words. Either the Bulgarian guide keeps language-neutral markers, or the parser takes a label set per language.
7. **Tests.** ~70 English phrase asserts in the app tests and ~15 English content tests in `test_guide.py`. They pin English today; ticket 02 decides how they run per language.
8. **Tooling side note.** This machine's console code page is cp1251 (Cyrillic). Printing `γ` or `≥` from Python without `PYTHONIOENCODING=utf-8` raised `UnicodeEncodeError`. Cyrillic itself encodes in cp1251, so Bulgarian text is safe there. The symbols the strings already use (`γ`, `≥`, `→`, `−`) are not. The app writes through Dash, not the console, so this only matters for scripts and test output that print strings.
