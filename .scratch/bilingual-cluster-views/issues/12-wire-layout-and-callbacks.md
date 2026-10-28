# 12: Translate-ready layout, callbacks, JS words and widgets

**What to build:** every visible string in `layout.py`, `callbacks.py`, the browser assets and the third-party widgets reaches the screen through `tx`, in English, so the A1 slice (issue 23) only has to fill a catalogue. The number rule is mirrored in the grids, Plotly and the pills.

**Blocked by:** 11

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Catalogue and translator", "Plurals and numbers", "JS, CSS and third-party widgets". Inventory: [research 01](../research/01-string-inventory.md) (the `layout.py`, `callbacks.py`, `workbench.js`, `app.css` and `export.py` rows).

- [x] **`layout.py`**: every static label, placeholder, title and tooltip is registered through issue 10's relabel registry, or built with `tx` inside a layout function. No bare English literal stays visible.
- [x] **`callbacks.py`**:
  - Every message it renders (status lines, banners, errors, the `Refused: …` line) goes through `tx`, from the `lang` store, following the Input/State rule.
  - English-style plurals become `tx.n`.
  - Its `view.num` calls become `tx.num`.
  - `# i18n: wire` markers from issue 11 in these files are gone.
- [x] **`OpenRefused`** (`app/export.py`) carries a reason code plus parameters. `callbacks.py` renders it through `tx`. Terminal and CLI output keep today's English text.
- [x] **`ui-words` store**: it supplies `workbench.js` and `graph.js` with the pill words, the tooltip footer, the ⓘ `aria-label` and any other word the JS shows, and re-sends them on a switch. The JS holds no English words.
- [x] **CSS**: the `" copied"` text becomes `content: attr(data-copied)`, filled from `tx`.
- [x] **Grids**:
  - ag-grid `localeText` carries only the strings our grids show, from the term table's Short UI words.
  - A `d3.formatLocale({decimal, thousands})` per language, with the column definitions re-sent on a switch.
  - Schema `description` header tooltips (identifier columns) pass through `tx`. They are declared as a non-literal source for the parity test (`schema_tips`).
- [x] **Plotly**: our own titles and hover text go through `tx`, and `layout.separators` follows the language. The modebar stays English.
- [x] **Dropdowns**: the placeholder and search props go through `tx`.
- [x] Declare the `OpenRefused` reasons as a non-literal source for the parity test (`refusals`).
- [x] Tests:
  - A pseudo-language test monkeypatches a catalogue that brackets every message. With `lang` = that language, every registered static prop and every rendered callback message is bracketed. Tag names, dataset labels, `C1…` and column names are not.
  - A Bulgarian number locale reaches the grid column definitions and Plotly `separators`.
  - The CSV and JSON exports are byte-identical before and after this issue for a fixed Network State.
  - Switching language triggers no recompute (no `graph-data` request).
  - The existing English app tests pass unchanged.

## Comments

**2026-10-28, implementation.** Done, except **Plotly**, which moves to issue 14 (the heatmap is the only Plotly figure, and it is built in `ps_view.py`, which issue 14 wires). How it works:

- **Layout**: `layout.Labels` wraps the page's translator. `L.span(msg)` gives a static text a Span of its own with a stable id (`i18n-<n>`, in build order). `L.prop(id, prop, msg)` registers a prop of a component that already has an id: a label, placeholder, title, options, `labels` or data-tip. Pill buttons got ids (`pill-btn-<pill>`) so their tooltips can be relabelled.
- **Callbacks**: the Network State's text moved from `recompute` into `state_views(c, meta, tables, tx)`. `recompute` calls it with `lang` as State, and `state_text` calls it again when `lang` changes, from the memoised tables. `state-meta` gained `names` (hidden, removed and defining tags) and `n_games` for that. The defining-tag label is its own callback (`defining_options`), so a switch never touches the checkbox's value. The Removal Sensitivity job reports raw numbers only, and `progress_display` words them.
- **Refusals**: `export.REFUSALS` holds the reason code to English text. `OpenRefused(reason, **params)` and `BuildNotFound` keep today's English `str()` for the terminal.
- **Plurals now real in English**: the cache message reads "1 cached Removal Sensitivity result" (was "result(s)") in the app. The CLI keeps `app_cache.cleared_text`, unchanged. The "tags not in the network" line has a singular form.
- **Grids**: `layout.GRIDS` is the column-definition factory per grid. `grid_words` sends every grid's `columnDefs` and `dashGridOptions` (`localeText`) again on a switch. Floats use `tx.d3_format`.
- **Exports**: no export code reads the language (the export zip's tables and `export.json` were compared for the same Network State before and after this work).
- Status stays `ready-for-agent` until issue 14 wires the Plotly heatmap; then this ticket is `done`.
- **2026-10-28**: Plotly done in issue 14; ticket `done`. Issue 14 also marked this issue's registered layout words `msg("…")` so the parity scan sees them.
