# 12: Translate-ready layout, callbacks, JS words and widgets

**What to build:** every visible string in `layout.py`, `callbacks.py`, the browser assets and the third-party widgets reaches the screen through `tx`, in English, so the A1 slice (issue 23) only has to fill a catalogue. The number rule is mirrored in the grids, Plotly and the pills.

**Blocked by:** 11

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Catalogue and translator", "Plurals and numbers", "JS, CSS and third-party widgets". Inventory: [research 01](../research/01-string-inventory.md) (the `layout.py`, `callbacks.py`, `workbench.js`, `app.css` and `export.py` rows).

- [ ] **`layout.py`**: every static label, placeholder, title and tooltip is registered through issue 10's relabel registry, or built with `tx` inside a layout function. No bare English literal stays visible.
- [ ] **`callbacks.py`**:
  - Every message it renders (status lines, banners, errors, the `Refused: …` line) goes through `tx`, from the `lang` store, following the Input/State rule.
  - English-style plurals become `tx.n`.
  - Its `view.num` calls become `tx.num`.
  - `# i18n: wire` markers from issue 11 in these files are gone.
- [ ] **`OpenRefused`** (`app/export.py`) carries a reason code plus parameters. `callbacks.py` renders it through `tx`. Terminal and CLI output keep today's English text.
- [ ] **`ui-words` store**: it supplies `workbench.js` and `graph.js` with the pill words, the tooltip footer, the ⓘ `aria-label` and any other word the JS shows, and re-sends them on a switch. The JS holds no English words.
- [ ] **CSS**: the `" copied"` text becomes `content: attr(data-copied)`, filled from `tx`.
- [ ] **Grids**:
  - ag-grid `localeText` carries only the strings our grids show, from the term table's Short UI words.
  - A `d3.formatLocale({decimal, thousands})` per language, with the column definitions re-sent on a switch.
  - Schema `description` header tooltips (identifier columns) pass through `tx`. They are declared as a non-literal source for the parity test (`schema_tips`).
- [ ] **Plotly**: our own titles and hover text go through `tx`, and `layout.separators` follows the language. The modebar stays English.
- [ ] **Dropdowns**: the placeholder and search props go through `tx`.
- [ ] Declare the `OpenRefused` reasons as a non-literal source for the parity test (`refusals`).
- [ ] Tests:
  - A pseudo-language test monkeypatches a catalogue that brackets every message. With `lang` = that language, every registered static prop and every rendered callback message is bracketed. Tag names, dataset labels, `C1…` and column names are not.
  - A Bulgarian number locale reaches the grid column definitions and Plotly `separators`.
  - The CSV and JSON exports are byte-identical before and after this issue for a fixed Network State.
  - Switching language triggers no recompute (no `graph-data` request).
  - The existing English app tests pass unchanged.
