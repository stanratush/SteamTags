# 11: Help and User Guide lookups per language

**What to build:** the guide and help layers become language-aware. A Bulgarian `docs/user-guide/bg/` copy can be read through the same anchors as the English guide, falling back to English wherever it is missing. Tooltips reach the browser as structured lines, so the browser code no longer parses English labels. The guide structure parity test and its ratchet exist. No Bulgarian text is written here; `bg/` holds only a README stub.

**Blocked by:** 10

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "The Bulgarian User Guide", "Tests", "Guide slice conventions". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md), Guide labels.

- [x] **`guide.py`**:
  - A heading ending in `{#id}` uses `id` as its anchor, and the `{#id}` is stripped from the shown text. English headings keep their computed slugs.
  - `guide_dir(lang)`, and every lookup (`section`, `chapter`, `help_markdown_at`, `help_markdown`, `in_short_at`, `resolve_link`, `modal_links`) takes the language.
  - **Fallback**: a missing Bulgarian file or anchor gives the English one. A Bulgarian chapter missing some `##` sections shows the English section in each gap, in the English order.
- [x] **Label sets**: `in_short()` and `in_short_problems()` take the language's label set, with the same 60-word cap. Both sets live in one place in code. The Bulgarian set is the term table's Guide labels, including the entry markers ("Защо има значение тук", "Точна дефиниция", "В приложението се показва като …").
- [x] **`help.py`**:
  - `tip`, `attrs`, `column_line`, `column_help` and `column_attrs` take `tx` (required).
  - Tooltips are emitted as structured `[kind, text]` lines. `workbench.js` renders the kinds, and `TIP_LABEL` is removed.
  - The footer and the ⓘ `aria-label` come from `tx`.
  - `HELP`, `PANEL_SECTIONS` and `ENTRY_BY_COLUMN` are unchanged.
- [x] **Call sites**: every caller of `help` passes a translator. Where `lang` isn't available yet, it passes `text("en")` with a `# i18n: wire` marker, and issues 12–14 remove those markers.
- [x] **The guide modal** reads the `lang` store and shows that language's guide, re-rendering on a switch.
- [x] **`export/column_index.py`** can render Appendix B with a language's fixed labels (`GROUP_LABEL` and the header). The English output is byte-identical to today. The Bulgarian file is written by issue 38. The staleness test covers `bg/appendix-b-column-index.md` once that file exists.
- [x] **Guide structure parity** (`tests/test_guide_bg.py`). A `GUIDE_DONE` entry is a file (`03-metric-reference.md`) or one `##` section of a file (`03-metric-reference.md#feature-analysis`). For each entry:
  - every English heading id has a Bulgarian twin at the same level;
  - Bulgarian links resolve;
  - each entry has the same In short labels in the same order and the same markers.

  Wherever Bulgarian exists, its own links and ids are checked now.
- [x] **Verbatim per language**: the methods-paragraph test runs for Bulgarian once `selection_text` is on `CATALOGUE_DONE` and `05-citing-and-reproducing.md` is on `GUIDE_DONE`. It is skipped with a reason until then.
- [x] **English only**: the five content tests (interpretation bands, Hennig, never-cited sources, required statements, limitations) and the banned-words check read `docs/user-guide/*.md` only, never `bg/`. Their names or docstrings say so.
- [x] `docs/user-guide/bg/README.md`: a one-line stub saying the Bulgarian guide is being written and falls back to English. It is replaced by issue 27.
- [x] Tests:
  - A fixture `bg/` file with `{#id}` headings resolves through `section`, `in_short_at` and links.
  - A missing Bulgarian section falls back to English, and a partial chapter splices English sections into the gaps.
  - The tooltip line kinds round-trip.
  - The English guide's parsed anchors, In short blocks and Appendix B are unchanged.
  - The structure parity test fails on a fixture section that is on the done-list but missing a heading.

## Comments

**2026-10-28, implementation.** Done. Choices the ticket left open:

- **Which lookups take the language**: the ones that read a file: `chapter`, `entry_at`, `help_markdown_at`, `help_markdown` and `in_short_at`, each `(lang, file, …)`. `section`, `headings`, `resolve_link` and `modal_links` work on Markdown text or on targets, which are the same in both languages, so they take none. The modal opens a link's `file#anchor` in the language shown.
- **Tooltip lines** are `[kind, text]` in JSON (`data-tip`). The kinds are the In short kinds (`guide.IN_SHORT_KINDS`) plus `now`, `column`, `columns` and `field`. Each kind's label comes from the `ui-words` store (`tip`), with the footer (`more`) and the ⓘ aria-label (`info`). ag-grid's own `headerTooltip` stays plain text (`help.tip_text`).
- **Label sets** are `guide.LABELS` and `guide.MARKERS`. The Network State table's `Field:` line had no Bulgarian label in the term table, so `Поле:` was added there, marked "proposed", for the R1 review.
- `in_short_at` returns `(kind, text)` and reads English labels too, so an entry that falls back to English still gives its lines.
- Callers without the language yet use a module-level `WIRE = text("en")  # i18n: wire` (layout, callbacks, view, ps_view). Issues 12-14 replace it.
