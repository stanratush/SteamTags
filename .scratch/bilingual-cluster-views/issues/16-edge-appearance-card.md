# 16: Edge appearance card and guide entry

**What to build:** the user-facing Edge appearance controls (variant C), built on issue 15's engine. The legend's thickness key opens a floating card with a histogram of link values and every control. The English guide's **Edge thickness** entry becomes **Edge appearance**.

**Blocked by:** 15

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Edge Appearance". Prototype: [edge appearance, variant C](../prototypes/04-edge-appearance/PROTOTYPE-edge-appearance.html).

- [x] **Collapsed key**: today's one-line thickness key plus an "Edges" toggle. When the appearance isn't the default, it summarises it, e.g. "Edge thickness: shared games (√, 0.5–4 px) · 12 hidden".
- [x] **The card** is a transient overlay (`data-graph-transient`, like the floating Inspector). Opening or closing it never changes the canvas area, the layout or the fit. It contains:
  - a header with the drawn measure and **Show shared games** (offered only under Lift);
  - a histogram of the drawn measure's values per link, with the drawn width ramp over it;
  - a **Hide links below** handle on the histogram, with "N links hidden from the drawing" always shown. The line names **Minimum shared games** as the separate filter that is part of the Network State;
  - steppers for **Width**, **Strength** and **Links between Clusters** (the last only in the Cluster-separated layout), each with a tooltip giving its current value in the Interface Language's number format;
  - **Scaling** (linear, √, log) and **Colour** (one colour, By Cluster, within vs between, by value) choices;
  - the card's own **Reset**, which returns to today's look.
- [x] The card works in the Workbench, in both layouts, and in Analysis Report mode.
- [x] Every word goes through `tx` or `ui-words`, in English. Each control has a help key pointing to its guide paragraph.
- [x] **Guide** (`02-app-controls.md`): the **Edge thickness** entry becomes **Edge appearance**, with one paragraph per control and per Hide links below behaviour.
  - The "never compare thicknesses across the two measures" caution stays.
  - The old `edge-thickness` anchor keeps resolving, from code, help keys and in-guide links, through an alias the guide parser and the link test understand.
- [x] Tests:
  - Browser: each control redraws within 50 ms, with no `graph-data` request and no layout.
  - Opening or closing the card leaves the reported canvas size and the viewport unchanged.
  - The collapsed key's summary matches the state.
  - The hide handle's count matches the links below it, and shows "0 hidden" with none.
  - `#edge-thickness` and `#edge-appearance` both resolve. Every new help key resolves to a guide anchor.

## Comments

**2026-10-28, implementation.** Done. Notes:

- **Card**: `layout._edge_card` is a Dash shell, a transient overlay (`data-graph-transient`, `data-graph-overlay="bottom"`). Its header holds the title, the show-shared switch (moved here from the legend) and Reset. `graph.js` `renderCard` fills the body: the histogram with the drawn width band, the hide handle, the hidden-count line naming Minimum shared games, the Width / Strength / Links between Clusters steppers (each with its current value as its tooltip, in the Interface Language's number format) and the Scaling and Colour choices. Each control's name carries its help (`help.py` `edges.*`, through the `ui-words` store's `edges.help`).
- **Key summary** (`keyText`): "Edge thickness: shared games (√, 0,5–3,8 px, within vs between, 13,3%) · 316 hidden", or the plain key at the default look.
- **Guide**: `### Edge appearance`, with a `####` paragraph per control so each tooltip has an anchor. `guide.ALIASES` keeps `edge-thickness` resolving: code, help keys, in-guide links and the link test all use it. One in-guide link still uses `#edge-thickness` on purpose.
- `elements-base` and the payload carry `min_shared`, for the card's line about the separate filter.
- **Browser checks, by hand** (no browser-test harness):
  - five controls redrew in 19–30 ms with 0 requests;
  - opening and closing the card left the reported canvas, pan and zoom unchanged;
  - a drag hid 316 links, matching the 316 below the handle, and the key said "· 316 hidden";
  - Reset returned to the default look with "0 links hidden";
  - the card opens in Analysis Report mode;
  - no console errors.
