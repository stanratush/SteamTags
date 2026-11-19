# Spec: UI Declutter

Settled with the researcher on 2026-11-18 in two grilling rounds, with no map: nothing was left undecided. Glossary: [CONTEXT.md](../../CONTEXT.md). Constraints: ADR 0003 (every new or changed string has a bg catalogue entry, and the bg User Guide follows the en one).

## Goal

The app's chrome takes too much room and some views are hard to read:

- At 1440 px the header wraps onto two lines (brand + Build, four modes, Language, Find a tag, the panel toggles, Graph only).
- In Cluster Comparison the Shared settings block across the top takes about 100 px. A pair is chosen from the Dataset pairs list at the bottom of the sidebar, below every dataset row, so it has to be scrolled to.
- The Cluster map is unreadable with many Clusters, or when Clusters overlap on the canvas: bubbles clump, small bubbles hide their labels, lines pass under the one-tag pool bubble, most strong links have the same width, and the fixed 280×190 card covers the graph.

**What it never changes:** any computation, cache key, export file or the Network State. Every change here is a view choice. Panel open/closed state keeps the meaning and storage it has today.

## Decisions

### Header (issue 01)

- The header holds, in this order: brand + Build menu · the four mode buttons · Find a tag (only in modes that use it, as today) · a compact **EN | BG** switch at the far right. It fits on **one line at 1280 px or wider**.
- The switch loses the visible word "Language". Its explanation (`header.lang`) moves to the switch's tooltip, which still opens the help entry.
- "Analysis Report mode" becomes **"Analysis Report"** on the mode button (bg shortened to match). Other labels stay.
- The `panels` and `ps-panels` checklists leave the header. **Each panel gets a collapse button in its own title bar**: « on Controls, » on Inspector, ▾ on the Tables tab strip, and the same for Parameter Selection's Controls, Pair Constraints and Inspector. A collapsed panel leaves a thin **rail** on its edge with its name (rotated for side panels, horizontal for Tables); clicking the rail reopens it.
- **Graph only** moves into the graph toolbar beside Global / Cluster-separated / Tidy / Cluster map / ⤢.
- `verify-result` and `error-message` stay at the header's right.

### Cluster Comparison layout (issue 02)

- The top block (`cc-head`: Shared settings, `comparison_id`) moves into the left sidebar as a **Shared settings** section above Datasets.
- The sidebar becomes a **drawer** that collapses to a rail on the left edge, by the same mechanism as the panels in 01. It starts **open** on the first visit in a browser session and remembers open/closed for the rest of that session (sessionStorage, like the Cluster map).
- **Export CSV** moves to the pair header row of the main area, to the right of the Minimum Jaccard slider.
- The shared-settings notice (`cc-notice`) shows at the **top of the main area**, so it is seen with the drawer closed.

### Choosing the pair (issue 03)

- The "Overall × RPG ⇄" title becomes **Left [▾] ⇄ Right [▾]**: two dropdowns above the diagram. Each lists only the included (ticked) datasets, each name in its dataset colour. ⇄ still swaps the sides.
- Picking on one side the dataset already on the other side **swaps** the two sides.
- Unticking the dataset on a side moves that side to the remaining included dataset with the **highest ARI** against the other side.
- The **Dataset pairs** list stays in the sidebar as a ranked overview by ARI; clicking a pair sets both dropdowns (its A on Left, B on Right).

### Cluster map (issue 04)

- **Ring layout**: multi-tag Clusters sit evenly on a ring, ordered so strongly linked Clusters are neighbours, and links are curved chords inside the ring. The map no longer copies canvas positions, so it reads the same whatever the canvas looks like.
- **Labels outside the bubble**: "C1 · 15 tags". The tooltip lists the Cluster's top tags. Bubble area still shows tag count, with a minimum radius.
- **The one-tag pool** is not drawn as a bubble; a grey note under the map reads "+ 13 one-tag Clusters".
- **Line width** is scaled against the strongest link on this map (not ratio ÷ γ capped at 1). A two-line legend shows thin = weak and thick = strong with their ratio values. Links in the bottom third by ratio are faded. Hover and selection still show the exact ratio.
- **The card** stays a top-right overlay on the graph, grows to about 360×300, and gets its own × close button (it closes the map as the toolbar's Cluster map button does).
- Clicking a bubble or a link still selects the Cluster or the pair, and any selection still lights up on the map.

## Docs

Each issue updates what it changes in `docs/user-guide/02-app-controls.md` and its bg twin (and `01-getting-started.md` where it names header controls), the help entries in `steamstudy/app/help.py`, and `docs/running-guide.md`'s browser check ("after each panel is collapsed").

## Out of scope

Narrow-width behaviour beyond what the panels already do; any change to Graph only's narrowest form; any change to what the Cluster map computes (`cluster-connections` store).
