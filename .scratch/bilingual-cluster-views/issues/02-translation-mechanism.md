# Translation mechanism
Type: grilling
Status: resolved
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

## Answer

Settled with the researcher on 2026-10-27, in two grilling rounds plus a final confirmation. The record is [ADR 0003](../../../docs/adr/0003-bulgarian-is-a-view-only-translation.md) and the glossary term **Interface Language** in [CONTEXT.md](../../../CONTEXT.md).

- **Switching is live, not a reload.** A `lang` store drives everything:
  - `build_layout` records each translated static prop as (component, prop, message) in a registry. One relabel callback sets them with `set_props`, so a new static label needs no new wiring.
  - Callbacks that render text take `lang` as an Input. Callbacks that compute numbers take it only as State, so a switch never recomputes a Network State.
  - Running jobs carry on. Their progress is raw numbers rendered in `ps_view`, so it simply re-renders in the new language.
  - The browser tab title is relabelled client-side.
- **The switch**: an EN | BG segmented control in the header, beside the mode switch, in all three modes. English is the default. The choice is remembered per browser in a cookie, and the layout becomes a function that reads the cookie when the page is served, so the first paint is already in that language.
- **Catalogue**: plain Python dicts keyed by the **English text**, with named `{placeholders}` only. Bulgarian lives in one module per area (e.g. `i18n/bg/*.py`). No gettext and no new dependency, so ADR 0001 is untouched.
- **Passing the language**: an explicit, **required** translator `tx = text(lang)` holds the messages, plurals, `tx.join` and `tx.num`.
  - `view`, `ps_view`, `selection_text`, `help` and `ps_run.eta_text`/`elapsed_text` take `tx`.
  - Exports and the CLI (`ps_export`'s `selection_report.md`, `bundle/make.py`) pass `text("en")`.
  - No process-wide setting and no contextvar.
- **Plurals**: a counted message is two whole forms, `one` and `other`, with verb agreement inside the form, so no `(s)`, `is/are` or `has/have` stitching is left in code. Bulgarian `other` is written in the count form (`{n} тага`), because the numeral always comes first.
- **Numbers**: one rule per language, owned by `tx.num()`. `tx.num()` replaces `view.num()` and also translates `n/a`, `yes` and `no`. The `selection_text` helpers use `tx`. The rule is mirrored in three places:
  - the grids' `d3.formatLocale({decimal, thousands})`, with the column definitions re-sent on a switch,
  - Plotly `layout.separators`,
  - `pills()`, through `ui-words`.

  The rule itself is [Bulgarian terminology](03-bulgarian-terminology.md)'s to set. Exports never call these, so no exported number can change.
- **JS and CSS hold no words**:
  - A `ui-words` store supplies the pill words, the tooltip footer and the ⓘ `aria-label` to `workbench.js`.
  - The CSS `" copied"` becomes `content: attr(data-copied)`.
  - Tooltips reach JS as structured `[kind, text]` lines, so the `TIP_LABEL` regex goes away.
- **The Bulgarian User Guide**: a parallel `docs/user-guide/bg/` copy with the same file names.
  - Every Bulgarian heading ends with `{#<english-slug>}`. The parser strips it from the shown heading and uses it as the anchor.
  - The English guide is unchanged.
  - `help.HELP`, `PANEL_SECTIONS`, `ENTRY_BY_COLUMN` and all in-guide `file.md#anchor` links stay language-independent. A lookup becomes (lang, file, anchor).
  - It ships in the wheel and the App Bundle with no packaging change.
- **In short labels and entry markers**: one label set per language. `in_short()` and `in_short_problems()` take the language's set, with the same 60-word cap. The Bulgarian words come from [Bulgarian terminology](03-bulgarian-terminology.md).
- **Appendix B** is generated a second time by `export/column_index.py` with Bulgarian fixed labels. The staleness test checks both files.
- **Open Network State refusals**: `OpenRefused` carries a reason code plus parameters, and `callbacks.py` renders `Refused: …` through `tx`. Terminal and CLI errors stay English.
- **Schema `description` header tooltips** are translated on screen through the catalogue. `export/schema.py` and every export keep the English text.
- **Third-party widgets**: only what a widget exposes as an option is translated. That means ag-grid `localeText` (just the strings our grids show), our own Plotly titles and hover text, and the Dropdown placeholder and search props. The Plotly modebar and any built-in text without a prop stay English.
- **Tests**:
  - **Catalogue parity**: an AST scan checks that every `tx("…")` literal has a Bulgarian entry, that placeholder names match, that counted messages have both forms, and that no Bulgarian key is orphaned.
  - **Guide structure parity**: each English heading id has a Bulgarian twin at the same level in the same file, Bulgarian links resolve, and each entry has the same In short labels in the same order and the same markers.
  - **Verbatim per language**: the `selection_text` sentences rendered with `text("bg")` must appear verbatim in the Bulgarian guide.
  - **English only**: the ~70 app phrase asserts and the five English content tests (interpretation bands, Hennig, never-cited sources, required statements, limitations).
  - **Strictness**: correctness checks are strict from the start. **Completeness** checks turn strict when the bulk translation finishes, and until then a missing Bulgarian entry falls back to English at runtime. Staging that is left to the bulk-translation fog on the map.
- **Facts confirmed**: the Network State sentence and the quality lines are view-only, and no export calls `state_sentence`.
