# 02: Styling shell and responsive Workbench

**What to build:** the Workbench looks like prototype variant A, with B's responsive behaviour. Controls, panels, tabs and tables are styled, slider values show live, and the layout changes form as the window narrows: a pill bar, then a floating Inspector, then a bottom sheet.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Styling and layout". Prototype: [01-styling-directions](../prototypes/01-styling-directions/PROTOTYPE-styling-directions.html), variant A (and B for the narrow forms).

- [ ] `assets/app.css` defines the prototype's tokens and styles. System fonts only, tabular numerals for numbers, no new dependency.
- [ ] Controls:
  - The Controls panel is split into sections: Data, Filters, Clustering, State.
  - Every RadioItems is a segmented control.
  - Hidden Genre Tags are toggle chips with a count ("11 of 11").
  - Buttons, inputs and the dataset dropdown use the prototype's styles.
- [ ] Every slider label shows its current value and updates while dragging ("Minimum games per tag 8"). Values are still sent on release.
- [ ] Workbench tabs are styled like the prototype's nav. AG Grid is themed to the tokens: compact rows, muted headers (column names kept), right-aligned tabular numbers.
- [ ] Graph overlays: the legend bottom-left; the Global / Cluster-separated switch and a Fit button top-right; a search slot in the header, centred (filled by 06).
- [ ] With the Inspector collapsed, or below 1280 px, the Inspector opens as a floating card over the right of the graph, closed with ×. The graph refits around it.
- [ ] Panes and breakpoints:
  - The tables pane can be resized with a drag handle.
  - 1024–1279 px: the Controls panel becomes a pill bar under the header. Each pill shows its value and opens a popover with the control.
  - Below 1024 px: the tables also become a bottom sheet with a grip. It animates, and is instant under reduced motion.
  - "Graph only" gives the narrowest form at any width.
  - Panels still collapse independently.
- [ ] `block_styles` and the mode and panel tests still pass. Analysis Report mode uses the same tokens.
- [ ] Browser checks at 1440, 1200 and 900 px wide: nothing overlaps or scrolls sideways, and every control works in each form.
- [ ] `docs/user-guide/02-app-controls.md` describes the pill bar, the floating Inspector and the bottom sheet.

## Comments
