# Spec: Metric help for non-specialists

Settled in a grilling session on 2026-10-07. Glossary: [CONTEXT.md](../../CONTEXT.md). Builds on [User Guide metric wording and interpretation bands](../steam-success-study/issues/27-user-guide-wording-bands.md), whose rules it keeps.

## Goal

A researcher with no training in network analysis can tell, for every metric and analytical control in the Tag Network app, what the value means, which direction is which, why it is useful in this study of successful commercial games and what to be careful about, without leaving the app. Help comes in two layers:

- **Layer 1 (tooltip):** at most four short labelled lines, about 60 words, shown on hover or keyboard focus.
- **Layer 2 (expanded help):** the element's own User Guide entry, opened in the in-app help modal by a click.

No metric, column, export or `schema_version` changes.

## Facts found while grilling

- Layer 1 today is the native `title` attribute: controls ([layout.py](../../src/steamstudy/app/layout.py)), summary row and quality boxes (`summary_row`, `quality_boxes`, `SILHOUETTE_TIP`, `ari_tip` in [view.py](../../src/steamstudy/app/view.py)), Inspector labels (`label_tip`, `_kv`), legend chips (`callbacks.py`, "Select this cluster"). Grid headers use ag-grid's `headerTooltip` (`tooltipShowDelay` 300).
- Inspector labels and grid headers reuse the export schema's column `description`. That text is technical, and it also generates the Column Index ([Appendix B](../../docs/user-guide/appendix-b-column-index.md)).
- Layer 2 exists only per panel: each `?` (`_help(panel)`) opens one guide section in `help-modal` through `PANEL_SECTIONS` and `section()` in [guide.py](../../src/steamstudy/app/guide.py), which can already cut out any heading's section by its anchor.
- `#anchor` links inside the modal go nowhere.
- `INSPECTOR_LABELS` maps each plain name to schema columns, and the Column Index maps columns to guide entries. Each label's guide anchor is therefore derivable.
- Analysis Report mode reuses the Workbench blocks, so covering the blocks covers it too.
- The legend has one chip per Multi-Tag Cluster plus a static One-Tag chip. Nothing in the app or guide explains node size, edge thickness or colour.
- `tests/test_guide.py` already enforces the metric-entry form (`*Example.*`, `*Bounds.*`, `*Compare with.*`, one `**Exact definition:**`) and bans a short list of band phrases.

## Decisions

### Content rules
- Issue 27 stands: **no quality words and no cut-offs**. Tooltips give direction and reference points, e.g. "1 = no more than chance", "0 = no better than random".
- The layer-1 text has up to four labelled lines, in this order. A line is left out only when it has nothing to say.
  1. **In short.** a plain sentence: what it is and what it measures.
  2. **Higher →** / **Lower →** direction and reference point. For controls: **Raising it →**.
  3. **Here:** why it is useful in this study.
  4. **Caution:** the main limitation.
- Hard cap of 60 words over the four lines.
- **Banned words** in "In short" blocks (word-boundary, case-insensitive): good, bad, strong, strongly, weak, stable, robust, important, significant, reliable, excellent. Glossary terms (the `**Term**:` headings of CONTEXT.md) are exempt.
- The study framing covers the current study only: recurring characteristics of the most-played commercial Steam games. The later STEM/educational comparison may appear in the guide's longer paragraph where it fits, never in layer 1.
- Terms are the User Guide's and the glossary's (Tag, Cluster, One-Tag Cluster, Cluster Center, Seed-Noise Floor, Membership Stability, Removal Sensitivity, Clustering Weight, Lift, …). Avoided synonyms stay avoided (no "community", "hub", "importance", "confidence").

### The User Guide is the single source
- Every guide entry the app links to opens with an **In short** blockquote directly under its `###` heading, before `Columns:`. Lines are separated by empty `>` lines so they render as separate paragraphs:

  ```
  > **In short.** How much more often two tags share games than chance would predict.
  >
  > **Higher →** above 1: together more than chance; 1: no more than chance.
  >
  > **Here:** shows feature pairings typical of the most-played games, beyond what popularity alone explains.
  >
  > **Caution:** a pair of rare tags can get a high lift from two or three games.
  ```
- Those entries also get a `*Why it matters here.*` paragraph after the opening paragraph and before `*Example.*`. It holds the longer study-specific relevance and, where useful, a short example of reading the value.
- The schema `description`s and Appendix B do not change.
- **Controls:** a new `## Analytical controls explained` in `02-app-controls.md` with one `###` entry per analytical control: Minimum Months Filter, Minimum games per tag, Minimum shared games, Hidden Genre Tags, Hide defining tag, Clustering weight, Clustering algorithm, Resolution γ, Seed, Remove / Restore, Global / Cluster-separated, Tidy. Each entry has: In short; what raising or lowering it does; *Why it matters here.*; cautions; a short example. The Control reference table stays as the quick reference, and each analytical row links to its entry.
- **Legend:** a new `## Reading the graph` in `02-app-controls.md` with entries for node size (games), edge thickness (shared games), cluster colour and the grey One-Tag Clusters, each with an In short.
- Entries the app does not link to (ranking, feature analysis, Build diagnostics) are left as they are. A follow-up issue covers them.

### Layer 1: one custom tooltip
- Each element with help carries `data-tip` (the rendered lines) and `data-help` (`<guide file>#<anchor>`). Elements that cannot otherwise take focus get `tabindex="0"`.
- `workbench.js` has one delegated `mouseover`/`focusin` listener and one floating tooltip div. It shows the labelled lines with the labels in bold, and hides on `mouseout`/`focusout`/Esc/scroll. It sits inside the viewport and never covers the element.
- The same function renders the text for Dash components (`data-tip` on `html.*`) and for the escaped-HTML blocks (`_kv`, `_html`). These stay one component each, as the Inspector performance work requires.
- **Now:** line: the app may add one generated line of live values below the guide text, e.g. "Now: γ = 1.00; null mean 0.31 ± 0.01 from R = 20 null networks". It counts toward neither the 60 words nor the banned-word check.
- **Grid headers:** ag-grid `headerTooltip` gets the same text as plain lines plus "Column: `name`".
- Native `title` stays only on UI-only buttons (⤢ Fit, ×, Restore, Reset all, Clear app cache, the grip and handle) and on identifier columns, unchanged.
- The old tooltip texts (`SILHOUETTE_TIP`, `ari_tip`, `label_tip`, the literal strings in `summary_row`, `quality_boxes` and the controls) are replaced by the guide text.

- **Revised 2026-10-08 (wording review, issue 07):** self-explanatory controls carry no help of their own: the minimum games per tag, the minimum shared games, Hidden Genre Tags, Hide defining tag, Remove / Restore, Global / Cluster-separated and Tidy (Tidy keeps a native `title`, as a UI-only button). Their guide entries stay and are linked from the Control reference. Help stays on every metric and on the controls whose effect needs interpretation: Minimum Months Filter, Clustering weight, Clustering algorithm, Resolution γ and Seed. The ⓘ is used only in grid headers.

### Layer 2: click to open the entry
- Metric labels and control labels (Inspector `dt`s, summary-row and quality-box labels, control labels and pills, legend key) get a dotted underline and `cursor: help`. A click, or Enter on focus, opens the `data-help` entry in `help-modal`.
- Grid headers get a small ⓘ in the header that opens the entry. Clicking the header itself still sorts.
- A legend cluster chip's click still selects the cluster. The legend's help sits on a separate "Key" label.
- The panel `?` buttons stay as they are.
- On touch (`pointerType` touch), a tap on an underlined term opens the entry straight away. Layer 1 appears only with hover and focus.
- `workbench.js` sends the target through a `help-target` store (`dash_clientside.set_props`). `show_help` renders `help_markdown_at(file, anchor)`.

### Links inside the modal
- `#anchor` and `<chapter>.md#anchor` links inside the modal open their target entry in the same modal. A **← Back** button returns to the previous entry, as a stack that clears when the modal closes.
- A link to a chapter without an anchor opens the chapter's first section.
- External links still open in a new tab.

### Tests (`tests/test_guide.py`, `tests/test_app.py`)
- A parser test covers the In short blockquote: labels, order, optional lines, the 60-word cap.
- The banned words appear nowhere in any In short block, with the glossary exempt.
- Every element the app gives help to resolves to an entry that exists and has an In short. That covers every `INSPECTOR_LABELS` label, every summary-row and quality-box item, every control, every metric column of the five grids, the legend key, the dataset summary and Export. Each entry linked from the app also has `*Why it matters here.*`.
- Every in-guide link that resolves inside the modal points to an existing heading.
- The existing guide tests still pass.

### Review
- All the In short and Why-it-matters texts are drafted in the guide. One review page lists every app element with its layer-1 text and a link to its entry. The researcher approves or corrects the wording before the feature counts as done.

## Out of scope
- UI-only buttons and identifier columns.
- The generated feature-analysis report (`report.html`).
- Guide entries the app does not link to (follow-up issue).
- Plain names for grid column headers: grids keep the column names, as the App readability spec decided.

## Documentation
- [Getting started](../../docs/user-guide/01-getting-started.md): "Hover over any of them for what it means" and "hovering over a column header shows its one-line description" describe the two layers: hover or focus for the short explanation, click a dotted term or ⓘ for the full entry, and Back inside the help.
- [README](../../docs/user-guide/README.md) and `03-metric-reference.md` "How to read this chapter": each entry now opens with an In short block and has a "Why it matters here" paragraph.
