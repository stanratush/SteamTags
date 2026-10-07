# 01: Tracer: two-layer help on the summary row

**What to build:** the whole path for the six summary-row items (Games, Tags, Links, Clusters, Q, Silhouette): an In short block in the guide is read by the app, shown as the custom tooltip on hover or focus, and a click opens the entry in the help modal.

**Blocked by:** none

**Status:** done

Spec: [Metric help spec](../spec.md): "The User Guide is the single source", "Layer 1", "Layer 2", "Tests".

- [x] `guide.py` parses an entry's In short blockquote into labelled lines (In short, Higher/Lower/Raising it, Here, Caution), and `help_markdown_at(file, anchor)` returns any entry.
- [x] One app-side help registry maps each help key to `(guide file, anchor)` and builds `data-tip` / `data-help`. Guide text is read once per process.
- [x] The guide entries behind the six items (Network size, Cluster labels and counts, Modularity Q, Null-model baseline / Excess modularity, Mean silhouette, and the Minimum Months Filter text for "Games") have an In short block and a `*Why it matters here.*` paragraph.
- [x] `workbench.js`: one delegated hover/focus tooltip that shows the lines with bold labels and stays inside the viewport. A click or Enter on `[data-help]` sets the `help-target` store. A touch tap opens the entry directly.
- [x] `show_help` opens the modal at `help-target`. The panel `?` buttons still work.
- [x] Summary-row labels are dotted-underlined and focusable. Q shows a **Now:** line (γ, null mean ± SD, R).
- [x] Tests: the parser (order, optional lines, 60-word cap), banned words with the glossary exempt, and all six items resolving to an entry with an In short.
- [x] Checked in the browser: hover, keyboard focus, click to modal, and the narrow form.

## Comments

- 2026-10-07: Done. `guide.py` gains `chapter` (cached read), `help_markdown_at`, `in_short`, `in_short_at` and `in_short_problems`. The new `steamstudy.app.help` holds the `HELP` registry (help key -> guide file and anchor) with `tip`, `target` and `attrs`. Six entries in `03-metric-reference.md` (Cluster labels and counts, Network size, Modularity Q, Null-model baseline, Excess modularity and z-score, Mean silhouette) gain an In short block, a `*Why it matters here.*` paragraph and, where missing, a "Shown in the app as" line. Each summary item is focusable, has a dotted label and `data-tip` / `data-help`, and gets a Now line where one adds something: null link count for Links, seed range for Clusters, γ / null mean ± SD / R for Q, seed SD for Silhouette. `workbench.js` has the delegated tooltip (hover and focus, never over the element, inside the viewport, hidden on touch) and opens the entry on click, Enter or Space through the `help-target` store (`dash_clientside.set_props`, which works in Dash 4.4.1). `show_help` takes `help-target`; the panel `?` buttons are unchanged. Help modal blockquotes get a quiet card style. Tests: the parser, the form and banned words over every In short block in the guide (glossary terms exempt), and every `HELP` key resolving to an entry with In short and Why it matters; `_texts` in `test_app.py` now also reads `data-tip`. Checked in the browser at 900 px (narrow form) and full width: the tooltip shows the five lines with bold labels and doesn't overlap the element; mouseout, focus and blur behave; clicks, Enter and a touch tap open the entry; the panel `?` still opens Control reference. Full suite: 335 passed. 1 failed: `test_shipped_config_loads_with_spec_defaults`, from the researcher's uncommitted `config/collection.toml` (store rate 1.5 vs 2.0), unrelated.
