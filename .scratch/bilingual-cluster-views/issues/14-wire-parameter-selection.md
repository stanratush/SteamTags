# 14: Translate-ready Parameter Selection text (`ps_view`, `ps_run`, `selection_text`)

**What to build:** the Parameter Selection mode's text goes through `tx`. That covers `ps_view.py`, `ps_run.eta_text` / `elapsed_text` and every `selection_text` sentence. The export and the CLI keep calling it with `text("en")`, so `selection_report.md` stays byte-identical. Afterwards no `# i18n: wire` marker and no `view.num` is left.

**Blocked by:** 13

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Catalogue and translator", "Plurals and numbers". Inventory: [research 01](../research/01-string-inventory.md) (`ps_view.py`, `selection_text.py` rows and "One source, two languages").

- [x] **`ps_view.py`**:
  - every rendering function takes `tx`;
  - every visible word goes through it;
  - plurals become `tx.n`;
  - numbers use `tx.num`;
  - the heatmap's Plotly titles and hover text are translated, and `separators` follows the language.
- [x] **`ps_run.eta_text` and `elapsed_text`** take `tx`. Running jobs keep reporting raw numbers, so a language switch mid-run just re-renders the progress rows.
- [x] **`network/selection_text.py`**:
  - every sentence function takes `tx`;
  - `_pct`, `_range` and `_signed` use `tx.num`;
  - the three `_n(count, one, many)` plurals and the inline `is`/`are` become `tx.n`;
  - English list joining becomes `tx.join`.
- [x] **English callers** pass `text("en")`: `ps_export`'s `selection_report.md`, `bundle/make.py` and any CLI path.
- [x] `view.num` is deleted once `grep` finds no caller.
- [x] No `# i18n: wire` marker is left anywhere in `src/`.
- [x] Tests:
  - `selection_report.md` for a fixed cached grid is byte-identical before and after this issue.
  - The methods-paragraph verbatim test still passes in English.
  - The pseudo-language test covers the mode's loading panel, the dataset strip, "Why this pair", the Pair Inspector and the validation card.
  - A language switch during a running job keeps the job running and re-renders its rows.
  - The `test_selection`, `test_validation` and `test_ps_app` English phrase asserts pass with `text("en")`.

## Comments

**2026-10-28, implementation.** Done. Notes:

- **Byte-identical report**: `tests/fixtures/selection_report_default.md` and `selection_report_none_qualifies.md` were written from the code before this issue. `test_selection_report_stays_byte_identical` compares the export against them. Keeping English exact needed `tx.join(items, serial=True)`: the report has always written a serial comma ("…, and ≥ 2 neighbours"), and Bulgarian never does.
- **Labels**: `network/selection.py`'s `settings_label` and `constraints_label` also reach the screen, so they take `tx` (the export passes `text("en")`). Their catalogue area is `selection_text`.
- **The sentence constants** (`NA_CAVEAT`, `HIGH_G_CAVEAT`, `DATASET_STRIP_SENTENCE`, …) stay English constants, because the guide tests quote them, and are shown through `tx`. They are a declared parity source (`selection_text.SENTENCES`).
- **Static layout words** are marked `msg("…")` (`app/relabel.py`), so the parity scan finds them like `tx("…")`. This also applies to issue 12's `layout.py`, which had registered its labels unmarked. The registry moved from `layout.py` to `relabel.py`, because `layout` imports `ps_view`.
- **Plotly**: the heatmap and the CHAMP figure set `layout.separators` (English `.,`, Plotly's default; Bulgarian `,`), with their titles, hover text and trace names through `tx`. The modebar stays English.
- **Not translated**: export codes shown as values (`ok`, `not_reproduced`, `clipped_high`, a Link's status), the same as column values.
