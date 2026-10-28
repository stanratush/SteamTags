# 16: Edge appearance card and guide entry

**What to build:** the user-facing Edge appearance controls (variant C), built on issue 15's engine. The legend's thickness key opens a floating card with a histogram of link values and every control. The English guide's **Edge thickness** entry becomes **Edge appearance**.

**Blocked by:** 15

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Edge Appearance". Prototype: [edge appearance, variant C](../prototypes/04-edge-appearance/PROTOTYPE-edge-appearance.html).

- [ ] **Collapsed key**: today's one-line thickness key plus an "Edges" toggle. When the appearance isn't the default, it summarises it, e.g. "Edge thickness: shared games (√, 0.5–4 px) · 12 hidden".
- [ ] **The card** is a transient overlay (`data-graph-transient`, like the floating Inspector). Opening or closing it never changes the canvas area, the layout or the fit. It contains:
  - a header with the drawn measure and **Show shared games** (offered only under Lift);
  - a histogram of the drawn measure's values per link, with the drawn width ramp over it;
  - a **Hide links below** handle on the histogram, with "N links hidden from the drawing" always shown. The line names **Minimum shared games** as the separate filter that is part of the Network State;
  - steppers for **Width**, **Strength** and **Links between Clusters** (the last only in the Cluster-separated layout), each with a tooltip giving its current value in the Interface Language's number format;
  - **Scaling** (linear, √, log) and **Colour** (one colour, By Cluster, within vs between, by value) choices;
  - the card's own **Reset**, which returns to today's look.
- [ ] The card works in the Workbench, in both layouts, and in Analysis Report mode.
- [ ] Every word goes through `tx` or `ui-words`, in English. Each control has a help key pointing to its guide paragraph.
- [ ] **Guide** (`02-app-controls.md`): the **Edge thickness** entry becomes **Edge appearance**, with one paragraph per control and per Hide links below behaviour.
  - The "never compare thicknesses across the two measures" caution stays.
  - The old `edge-thickness` anchor keeps resolving, from code, help keys and in-guide links, through an alias the guide parser and the link test understand.
- [ ] Tests:
  - Browser: each control redraws within 50 ms, with no `graph-data` request and no layout.
  - Opening or closing the card leaves the reported canvas size and the viewport unchanged.
  - The collapsed key's summary matches the state.
  - The hide handle's count matches the links below it, and shows "0 hidden" with none.
  - `#edge-thickness` and `#edge-appearance` both resolve. Every new help key resolves to a guide anchor.
