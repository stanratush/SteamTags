# 15: Edge appearance engine in `graph.js`

**What to build:** link appearance moves from Python into the browser. The canvas payload carries raw edge values. `graph.js` owns an appearance state (width, scaling, colour mode, strength, strength between Clusters, hide threshold) and applies it by restyling the elements already drawn. The state persists in a cookie, and the show-shared switch stops re-sending the graph. This issue changes no visible UI: at the defaults the canvas looks exactly as today. Issue 16 adds the card.

**Blocked by:** 12

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Edge Appearance" (Controls, Hide links below, Scope, Persistence, Architecture). Prototype, for reference only: [edge appearance](../prototypes/04-edge-appearance/PROTOTYPE-edge-appearance.html).

- [x] **`renderer.payload`**: each edge carries raw `shared`, `lift` and `intra` (whether both ends are in the same Multi-Tag Cluster) instead of `width`. `renderer.py` keeps the default appearance values and the legend wording.
- [x] **`graph.js` appearance state** and one restyle function, exposed as `setAppearance(partial)` / `getAppearance()` for the card and tests:
  - width range 0.4–3 px default, ×/÷ 1.25 per step, the minimum within 0.1–3 px and the maximum within 1–12 px;
  - scaling: linear 0.4 + 2.6 × v / largest (at the default range), √(v / largest), or log(v / smallest) / log(largest / smallest), mapped onto the width range;
  - colour: one colour `#8d95a3`; By Cluster (links within a Multi-Tag Cluster in its colour, others neutral); within vs between (slate and orange); by value (`#c9ced8` → `#3b2f6b`, checked in both themes);
  - strength (opacity) 18 % default, ×/÷ 1.35, within 3–100 %;
  - links between Clusters 6 % default, ×/÷ 1.5, within 0–100 %, applied only in the Cluster-separated layout;
  - the drawn measure: shared games or Lift, plus the show-shared switch under Lift.
- [x] **Selected links** keep their colour mode and only become opaque. Under one colour they darken, as today.
- [x] **Hide links below** (state only here; the handle is issue 16):
  - Hidden links are not drawn, cannot be tapped and are left out of a tag's neighbourhood highlight.
  - Nothing on the Python side changes (Inspector counts, Edges table, numbers).
  - A tag whose links are all hidden stays drawn.
  - The threshold clears when the measure or the dataset changes, is kept across other Network State changes, and never persists.
  - `getAppearance()` reports the hidden count.
- [x] **Show shared games** becomes browser-only. It changes the drawn measure, with no callback round-trip and no `render_graph` payload. It still unticks when the Clustering Weight changes.
- [x] **Persistence**: width, scaling, colour and the two strengths are written to the `steamstudy_edges` cookie and read on load. The threshold and the show-shared switch are not kept.
- [x] **Reset all** never changes the appearance.
- [x] Any word `graph.js` needs comes from the `ui-words` store (issue 12).
- [x] Tests:
  - Unit (Python): with the default appearance, the payload's raw values give every edge the width 0.4 + 2.6 × value / largest. The widths differ by 0 from today's `renderer.payload` on a test-Build state.
  - Browser: a `setAppearance` call redraws within 50 ms, with no `graph-data` request and no layout.
  - Toggling show-shared sends no request.
  - A hidden link can't be tapped and isn't lit by its tag's selection.
  - The cookie round-trips the look across a page reload.
  - The threshold clears on a Clustering Weight change and is kept across a γ change.

## Comments

**2026-10-28, implementation.** Done. Notes:

- **Payload**: each edge carries `shared`, `lift` and `intra`, and the payload carries the Clustering Weight (`weight`) and `renderer.APPEARANCE`: the defaults, steps, bounds and colours. `graph.js` writes each edge's drawn width, colour and strength into its data (`aw`, `ac`, `ao`), and the stylesheet reads them, so the selection classes still override. Hiding is the `hid` class (`display: none`). A tag's neighbourhood highlight uses its visible links only.
- **Show shared games** is a clientside callback (`tagGraph.edgeKey`). It sets the measure and writes the key's words from the `ui-words` store (`edges`). The server only shows or hides the switch (`thickness_legend`). The thickness key now has a line of its own in the legend overlay (`app.css`). Before, the longer "shared games" wording re-wrapped the overlay, which shrank the canvas and sent a re-layout.
- **Browser checks, by hand in the in-app browser** (the repo has no browser-test harness), on the Overall default state (332 links):
  - default widths equal 0.4 + 2.6 × shared / largest to 4e-16;
  - six `setAppearance` calls redrew in 17–41 ms with 0 requests;
  - a 10-game threshold hid 99 links, the count matched, hidden links had `display: none` and weren't lit by their tag's selection;
  - toggling the switch sent 0 requests and kept the overlay's height;
  - the look survived a reload through `steamstudy_edges`, and the threshold didn't;
  - the threshold was kept across a γ change and cleared by the Lift switch;
  - links between Clusters were drawn at 6% (then 9%) in the Cluster-separated layout.
- Python tests pin the payload contract (raw values, `APPEARANCE` defaults, and default widths equal to the old ones) and that the switch is clientside.
