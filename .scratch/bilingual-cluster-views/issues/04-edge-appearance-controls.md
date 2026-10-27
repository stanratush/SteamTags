# Edge appearance controls
Type: prototype
Status: resolved
Blocked by: none

## Question

What edge appearance controls does the Workbench offer, and how do they look and behave? This is a HITL prototype (`prototype`, in `prototypes/04-edge-appearance/`).

- Today: width = 0.4 + 2.6 × value / the network's largest value (`renderer.payload`), measure from the Clustering Weight or the "show shared games" switch ([Edge thickness follows the Clustering Weight](../../edge-thickness/issues/01-thickness-follows-clustering-weight.md)), with intra/inter, dim, neighbour and selected opacities in `graph.js`.
- Candidate controls: width range (minimum and maximum), scaling (linear, square root, log, rank), colour (one neutral, by Cluster, intra vs inter, a gradient by value), opacity (overall, inter-cluster edges in the separated layout), and possibly a "hide edges below value" view filter. That filter must not be confused with Minimum shared games, which is part of the Network State.
- The defaults reproduce today's look exactly. All of it is a view choice: never part of the Network State, an export or any number. Does it reset with Reset, persist per browser, or apply per layout?
- Legend and help: how the legend says what is drawn and how it is scaled. Does each control get a guide entry?
- Performance budgets from the [Graph interaction spec](../../graph-interaction/spec.md): changing a control must not relayout or re-send the graph.

## Prototype

[prototypes/04-edge-appearance/](../prototypes/04-edge-appearance/PROTOTYPE-edge-appearance.html): three variants over the real Build's graph payloads (`?variant=A|B|C`). A: named looks in a legend popover. B: an "Edge appearance" section in the Controls panel with every knob. C: the thickness key as a live histogram-and-width card. The defaults reproduce today's widths exactly (max difference 0 against `renderer.payload`), and every change is a client-side restyle of 6–13 ms, with no payload and no layout.

## Answer

Settled with the researcher on 2026-10-27. The researcher picked variant C of the [prototype](../prototypes/04-edge-appearance/PROTOTYPE-edge-appearance.html), then accepted every recommendation in two grilling rounds. **Edge Appearance** is now a view choice in [CONTEXT.md](../../../CONTEXT.md).

- **Form (variant C)**: the legend's thickness key, collapsed by default to today's one-line key plus an "Edges" toggle. Expanded, it is a card with a histogram of the drawn measure's values per link, the drawn width ramp over it, and the controls. The card floats as a transient overlay (`data-graph-transient`, like the floating Inspector): opening or closing it never changes the canvas area, the layout or the fit. When the appearance is not the default, the collapsed key says so, e.g. "Edge thickness: shared games (√, 0.5–4 px) · 12 hidden".
- **Controls**:
  - **Width ±**: multiplies both ends by 1.25. The minimum stays within 0.1–3 px and the maximum within 1–12 px. Default 0.4–3 px.
  - **Scaling**: linear (default, today's 0.4 + 2.6 × value / largest), square root (√(v / largest)) or log (log(v / smallest) / log(largest / smallest)). There is no rank scaling: it would stop thickness from showing how far apart values are, and its curve would contradict the histogram's value axis.
  - **Colour**: one colour (default `#8d95a3`), By Cluster (links within a Multi-Tag Cluster in its colour, other links neutral), within vs between Clusters (slate and orange), or by value. The value ramp is light grey `#c9ced8` to dark slate-violet `#3b2f6b`, kept away from the selection blue `#2457d6`; check it against both themes when building. A tag's selected links keep their colour mode and only become opaque (one colour darkens them as today).
  - **Strength ±**: opacity × 1.35, within 3–100 %. Default 18 %.
  - **Links between Clusters ±**: opacity × 1.5, within 0–100 %. Default 6 %, shown and applied only in the Cluster-separated layout.
  - **Show shared games**: moves into the card's header. It is still offered only under Lift and still unticks when the Clustering Weight changes.
  - **Hide links below**: a handle on the histogram.
  - Each stepper's tooltip shows its current value. Numbers on screen follow the Interface Language's number format.
- **Hide links below**: a hidden link is not drawn, cannot be tapped, and does not light up in a tag's neighbourhood highlight. It still counts in the Inspector's connected tags, the Edges table and every number. A tag whose links are all hidden stays drawn. The card always shows "N links hidden from the drawing" and names **Minimum shared games** as the separate filter, which is part of the Network State. The threshold is in the drawn measure's units, so it clears when the measure (the Clustering Weight or the show-shared switch) or the dataset changes. It is kept across other Network State changes, and the count updates; with no link below it, the card shows "0 hidden". It never persists.
- **Scope**: one appearance for both layouts. It also applies in Analysis Report mode, which shows the same canvas. **Reset all** never touches it; the card's own reset returns to today's look.
- **Persistence**: the look (width, scaling, colour, the two strengths) is kept per browser in a cookie, the same mechanism as the Interface Language, so it survives restarts and `--port` changes. Browser storage was rejected because it is kept per origin, so the look would be lost whenever the port changed.
- **Architecture**: the `graph-data` payload carries each edge's raw `shared`, `lift` and `intra` instead of `width`. `graph.js` owns the appearance state and computes width, colour and hiding by restyling the elements already drawn. The show-shared switch becomes browser-only and stops re-sending the payload, which it does today through `render_graph`. `renderer.py` keeps the defaults and the legend wording. No appearance setting reaches Python, a Network State, an export or a cache key.
- **Guide**: the **Edge thickness** entry in `02-app-controls.md` becomes **Edge appearance**, with a paragraph per control. Each control's tooltip points to its paragraph. The old `edge-thickness` anchor stays as an alias, and the "never compare thicknesses across the two measures" caution stays.
- **Tests**:
  - Browser: any card control redraws within 50 ms, with no `graph-data` request and no layout. Opening or closing the card does not change the reported canvas.
  - Unit: with the default appearance, every edge's width equals 0.4 + 2.6 × value / largest.
  - The prototype measured 6–13 ms per restyle on the 332-link Overall state, with a width difference of 0 from `renderer.payload` at the defaults.
