# 14: Translate-ready Parameter Selection text (`ps_view`, `ps_run`, `selection_text`)

**What to build:** the Parameter Selection mode's text goes through `tx`. That covers `ps_view.py`, `ps_run.eta_text` / `elapsed_text` and every `selection_text` sentence. The export and the CLI keep calling it with `text("en")`, so `selection_report.md` stays byte-identical. Afterwards no `# i18n: wire` marker and no `view.num` is left.

**Blocked by:** 13

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Catalogue and translator", "Plurals and numbers". Inventory: [research 01](../research/01-string-inventory.md) (`ps_view.py`, `selection_text.py` rows and "One source, two languages").

- [ ] **`ps_view.py`**:
  - every rendering function takes `tx`;
  - every visible word goes through it;
  - plurals become `tx.n`;
  - numbers use `tx.num`;
  - the heatmap's Plotly titles and hover text are translated, and `separators` follows the language.
- [ ] **`ps_run.eta_text` and `elapsed_text`** take `tx`. Running jobs keep reporting raw numbers, so a language switch mid-run just re-renders the progress rows.
- [ ] **`network/selection_text.py`**:
  - every sentence function takes `tx`;
  - `_pct`, `_range` and `_signed` use `tx.num`;
  - the three `_n(count, one, many)` plurals and the inline `is`/`are` become `tx.n`;
  - English list joining becomes `tx.join`.
- [ ] **English callers** pass `text("en")`: `ps_export`'s `selection_report.md`, `bundle/make.py` and any CLI path.
- [ ] `view.num` is deleted once `grep` finds no caller.
- [ ] No `# i18n: wire` marker is left anywhere in `src/`.
- [ ] Tests:
  - `selection_report.md` for a fixed cached grid is byte-identical before and after this issue.
  - The methods-paragraph verbatim test still passes in English.
  - The pseudo-language test covers the mode's loading panel, the dataset strip, "Why this pair", the Pair Inspector and the validation card.
  - A language switch during a running job keeps the job running and re-renders its rows.
  - The `test_selection`, `test_validation` and `test_ps_app` English phrase asserts pass with `text("en")`.
