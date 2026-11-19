# 04: Cluster map: ring layout and readable labels

**What to build:** a Cluster map that stays readable with many Clusters and whatever the canvas looks like.

**Blocked by:** none

**Status:** done

Spec: [UI Declutter spec](../spec.md): "Cluster map", "Docs". Code: `src/steamstudy/app/assets/graph.js` (`MAP`, `mapPlaces`, `drawMap`, the map click handler), `assets/app.css` (`.cluster-map`), the `ui-words` map entries in `layout.py`.

- [x] Multi-tag Clusters sit evenly on a ring, ordered so strongly linked Clusters are neighbours (a deterministic order: same data, same picture). Canvas positions are no longer used.
- [x] Links are curved chords inside the ring and never pass under a bubble.
- [x] Each label sits outside its bubble: "C1 · 15 tags" (en and bg plural forms). The tooltip lists the Cluster's top tags. Bubble area follows tag count with a minimum radius.
- [x] The one-tag pool is not a bubble; a grey note under the map reads "+ N one-tag Clusters" (hidden when N = 0).
- [x] Line width is scaled against the strongest link on the map. A legend shows the thinnest and thickest widths with their ratio values. Links in the bottom third by ratio are faded. Hover and selection show the exact ratio as today.
- [x] The card is about 360×300, top-right over the graph, with a × close button that closes the map like the toolbar button (and updates `aria-expanded` and sessionStorage).
- [x] Clicking a bubble selects its Cluster and a link its pair; a selection lights up as today.
- [x] Readable in the browser with this Build's 3 Clusters and with a dataset of 8 or more Clusters (screenshot of each in Comments).
- [x] Every new string has a bg entry.
- [x] User Guide `02-app-controls.md` (en and bg) Cluster map paragraph matches.

## Comments

**2026-11-19, implementation.** graph.js: `mapPlaces` (canvas positions) is replaced by `ringOrder` and `ringPlaces`. `ringOrder` starts from the Cluster with the most link weight, then takes the unplaced Cluster most strongly linked to the last placed, with ties in label order. Each link is a quadratic curve bowed to 35% towards the centre (`chord`). A bubble's radius is 2.6·√size, at least 7 px and at most 40% of the gap between two places on the ring. Labels sit outside, anchored by angle. The tooltip shows the top 5 tags by the renderer's `prio`. Width is 1 + 6·ratio/max. The bottom third by ratio is faded and capped at 0.8 px (the first browser run, at opacity 0.3, was still dense at 8 Clusters). New ui-words: `top`, `weakest`, `strongest`, `one_tag`, with bg entries. `#map-close` sits in the card head and the same click handler closes the map (aria-expanded and sessionStorage follow). Card 360 px wide; svg 344×268.

Checked in the browser at 1440×900. γ 1, 3 Clusters: ring, labels outside, key "weakest link · ratio 0.62 / strongest link · ratio 0.66", "+ 13 one-tag clusters". γ 2.5, 8 Clusters and 27 links: readable after the fade fix; strongly linked Clusters sit side by side. A click on C3 opens it in the Inspector, lights its 6 curves with their ratios and fades the rest; the tooltip lists C3's top tags. × closes the map and the toolbar button reopens it. Afterwards γ was set back to 1 and the map closed. The guide's In short for the map had to stay within 60 words and avoid "strongly".

