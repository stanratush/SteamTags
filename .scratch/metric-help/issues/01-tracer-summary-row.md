# 01: Tracer: two-layer help on the summary row

**What to build:** the whole path for the six summary-row items (Games, Tags, Links, Clusters, Q, Silhouette): an In short block in the guide is read by the app, shown as the custom tooltip on hover or focus, and a click opens the entry in the help modal.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Metric help spec](../spec.md): "The User Guide is the single source", "Layer 1", "Layer 2", "Tests".

- [ ] `guide.py` parses an entry's In short blockquote into labelled lines (In short, Higher/Lower/Raising it, Here, Caution), and `help_markdown_at(file, anchor)` returns any entry.
- [ ] One app-side help registry maps each help key to `(guide file, anchor)` and builds `data-tip` / `data-help`. Guide text is read once per process.
- [ ] The guide entries behind the six items (Network size, Cluster labels and counts, Modularity Q, Null-model baseline / Excess modularity, Mean silhouette, and the Minimum Months Filter text for "Games") have an In short block and a `*Why it matters here.*` paragraph.
- [ ] `workbench.js`: one delegated hover/focus tooltip that shows the lines with bold labels and stays inside the viewport. A click or Enter on `[data-help]` sets the `help-target` store. A touch tap opens the entry directly.
- [ ] `show_help` opens the modal at `help-target`. The panel `?` buttons still work.
- [ ] Summary-row labels are dotted-underlined and focusable. Q shows a **Now:** line (γ, null mean ± SD, R).
- [ ] Tests: the parser (order, optional lines, 60-word cap), banned words with the glossary exempt, and all six items resolving to an entry with an In short.
- [ ] Checked in the browser: hover, keyboard focus, click to modal, and the narrow form.

## Comments
