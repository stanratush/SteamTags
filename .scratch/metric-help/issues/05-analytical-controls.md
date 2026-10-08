# 05: Analytical controls

**What to build:** each analytical control has its own guide entry and the two-layer help, in the Controls panel and in the pill bar.

**Blocked by:** 01

**Status:** done

Spec: [Metric help spec](../spec.md): "The User Guide is the single source" (controls), "Layer 1", "Layer 2".

- [x] `02-app-controls.md` gains `## Analytical controls explained`, with one entry each for: Minimum Months Filter, Minimum games per tag, Minimum shared games, Hidden Genre Tags, Hide defining tag, Clustering weight, Clustering algorithm, Resolution γ, Seed, Remove / Restore, Global / Cluster-separated, Tidy. Each entry has: In short (with **Raising it →** where it applies); what raising or lowering it does; `*Why it matters here.*`; cautions; a short example.
- [x] Each analytical row of the Control reference table links to its entry.
- [x] Control labels and pill-bar pills carry the help. The γ label's bare "0.1–3.0" title goes away, and the range moves into the entry.
- [x] Test: every analytical control resolves to an entry with an In short.
- [x] Checked in the browser: the wide form and the pill bar.

## Comments

- 2026-10-08: Done. `02-app-controls.md` gains `## Analytical controls explained` with the twelve entries, each with In short (Raising it → where the control has a direction), a range / default / Network State field line, what raising or lowering it does, *Why it matters here.*, *Caution.* and *Example.*; each analytical row of the Control reference links to its entry. `help.py` has the `control.*` keys (`APP_CONTROLS`). In the Controls panel each control's label is dotted, focusable and opens its entry; the slider labels keep their live value. Controls without a label of their own get an ⓘ: Hide defining tag (beside its checkbox), Global / Cluster-separated and Tidy (in the graph overlay); the Tidy button also shows Tidy's In short on hover. Remove / Restore help is on the State section's "Removed tags" label; the Remove, Restore and Reset all buttons stay plain buttons. The γ label's "0.1–3.0" title is gone (the range is in the entry). Pills: each analytical pill shows its In short on hover or keyboard focus, but its click still opens its popover, whose dotted label then opens the entry. The spec asks for a pill's click to open the entry; that would leave the control itself unreachable in the pill bar, so the researcher should confirm this in the wording review (07). The tooltip now hides on any press and shows on focus only for keyboard focus (`:focus-visible`), so it never covers a popover that a press opened. After the two-axis review: Hide defining tag now says the tag is also a Genre Tag in all four Tag-Specific Datasets, so showing it takes both the toggle and its chip, and that hiding changes the Network State; "Network State" for "state"; Genre Tags no longer called the store's genres; study-use Here lines for Seed and Hide defining tag; only the active strength changes with the weight. Tests: the twelve entries with every part, the table links, every `control.*` key on the page, In short tips on the analytical pills. Checked in the browser: the wide form (labels and ⓘ open their entries, Tidy still tidies) and the pill bar (a pill's tip on hover and Tab, its click opens the popover, the popover's label opens the entry). Seen in passing, not changed: at 1100 px the γ pill's popover runs past the right edge of the window.
