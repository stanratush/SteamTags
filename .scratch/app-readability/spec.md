# Spec: App readability

Settled in a grilling session on 2026-10-06. Glossary: [CONTEXT.md](../../CONTEXT.md). Prototype: [01-styling-directions](prototypes/01-styling-directions/PROTOTYPE-styling-directions.html) (variant A is the base; B supplies the graph look and the responsive behaviour; C supplies the Network State sentence).

## Goal

The Tag Network app is readable from the first view: labels can be read at the starting zoom, the first fit fills the canvas, no node hides another, clusters can be looked at one by one, and the numbers a researcher needs (a tag's games, its connected tags, the partition quality) are shown in plain words with a clear hierarchy. No analytical result changes: every Network State, `state_id`, Cluster and metric stays exactly as it is. Only positions, presentation and interaction change.

## Facts found while grilling

- dash-cytoscape 1.0.2 bundles Cytoscape.js 3.28.1 (no WebGL) and react-cytoscapejs 2.0.0, whose element patching re-applies positions and classes from the `elements` prop on every update, and whose `responsive` prop is off by default (the canvas is not told when its container resizes).
- The bad first fit has two causes: the fit runs before the container has its final size, and the Cluster-separated layout spans about 4,900 × 4,100 units against about 540 for Global (zoom 0.135 is that span in a 715 × 560 canvas). The prototype reproduced the first and fixed it with a ResizeObserver.
- Default Overall state of Build `20261006T062622Z-7a23ae9f`: 59 tags, 332 links, 3 multi-tag (26, 18, 11) + 4 one-tag clusters, Q 0.17 (excess +0.11), silhouette 0.04, seed ARI min 0.89. The Global layout is computed on 244 tags (the loosest network).
- Two hidden Genre Tags of the Overall dataset (Experimental 13782, Tabletop 17389) are on no game of the dataset, so the state knows them only by id; their names come from the Build's genre-tag list.
- The spec forbids stable/unstable labels anywhere (`steam-success-study` spec §82, §965; issue 27) and requires the silhouette qualifier "descriptive diagnostic, not a selection criterion" and Q to be shown against the null model.
- The app's `assets/` folder is inside the `steamstudy` package, so a vendored script there ships in the wheel and the App Bundle without packaging changes.

## Decisions

### Renderer
- The graph is drawn with plain **Cytoscape.js 3.34** (vendored, MIT, served from the app's `assets/`; never a CDN), in our own wrapper `assets/graph.js`. dash-cytoscape is removed from the dependencies. The canvas renderer stays; the WebGL mode stays off.
- `renderer.py` stays the only Python module that knows the renderer. Together with `graph.js` it is the renderer boundary: replacing the renderer means replacing those two files.
- Dash → graph: one store carries elements (ids, labels, cluster, size, classes), target positions, regions and view commands (fit, focus, center). Graph → Dash: taps on a node, an edge, a region title or the background are sent with `dash_clientside.set_props` to one `graph-event` store. AppID lists stay on the server.
- A ResizeObserver keeps the canvas in step with its container (panels opening and closing, the window resizing); the view refits until the user has zoomed or panned.
- Every fit targets where nodes **end up**, not where they are mid-animation, so the move and the fit run together.
- At render time, x is stretched by the canvas aspect ratio (capped at 1.6×) so the first fit fills a wide canvas. Exports keep the true coordinates.

### Layout (positions only; never part of the Network State)
- **No overlaps by default.** After the seeded spring layout, a deterministic overlap-removal pass pushes overlapping nodes apart with a 4-unit gap. It runs in Python on the full loose layout (so moving a threshold slider still never moves the graph), inside each Cluster-separated region, and after Re-layout.
- Node size becomes a fixed function of `n_games` relative to the dataset's most frequent tag (not of what is visible), so sizes and positions share model units and no visible set can overlap at any zoom.
- **Cluster-separated layout:** each region's side grows with √(members); members are laid out by a short seeded spring layout from their global positions with the Cluster Center pinned in the middle, then de-overlapped; regions are shelf-packed biggest first with small even gaps, rows aimed at the canvas aspect ratio; One-Tag Clusters share one compact grid region packed as the last box. Region titles ("C1 · 26 tags") are shown at a constant readable size.
- Inter-cluster links stay faint in Cluster-separated mode.
- `x_global`, `y_global`, `x_cluster_separated`, `y_cluster_separated` change value; the columns and `schema_version` do not change.
- **Dragging:** nodes can be dragged (users may overlap them on purpose). Dragged positions are view-only: kept while the layout basis is unchanged (like Re-layout), dropped when the dataset, Minimum Months Filter, Clustering Weight or seed changes, and never exported.

### Labels
- **Priority labels** are drawn at a constant on-screen size (about 11.5 px) at any zoom: the selected element and its neighbours, the Cluster Centers, the 15 largest tags by `n_games` (ties by tag id) and, in Cluster-separated mode, the largest tag of each cluster.
- After each zoom, a priority label whose box overlaps a higher-ranked one is hidden. Rank: the selected tag and its neighbours (never hidden), then Centers, then `n_games`.
- Every other label scales with zoom and is hidden below 7 px on screen.
- Priority labels have a white background (B), so they stay legible over edges.

### Motion (brief, never continuous physics)
- When the dataset stays the same and positions change (Minimum Months Filter, Clustering Weight, seed, Re-layout, the Global ↔ Cluster-separated switch, and algorithm or γ in Cluster-separated mode), nodes move from old to new positions over about 350 ms, ease-in-out.
- Tags that enter fade in; tags that leave fade out, then are removed. Colour changes cross-fade.
- A dataset change does not animate moves: it is a fresh set, so it only fits (animated).
- Selection: a tag dims everything except its closed neighbourhood, with a short pulse on the tag; an edge dims everything except itself and its two tags; a cluster dims everything except its members. Clicking the background clears the selection.
- Fit, focus cluster and search-to-tag animate zoom and pan.
- Under `prefers-reduced-motion`, everything jumps instantly. There is no in-app motion toggle.

### Focus cluster and tag search
- Clicking a legend chip, a region title or a row of the Clusters grid selects the cluster in the Inspector and zooms to it (its region, or its members' bounding box in Global).
- **Tag search** sits in the header, centred, so it works in every mode. Visible tags come first (with cluster and games); then every tag in `not_in_network`, greyed out with all its reasons, e.g. "Puzzle — Genre Tag hidden", "Chess — 3 games, below 8".
- Choosing a visible tag selects it, centres it (animated) and opens it in the Inspector. Choosing a missing tag opens a "Not in the network" card with its reasons and, only where one action fixes it, a button: **Restore** (removed) or **Unhide** (Genre Tag or defining tag hidden). Nothing changes until the button is pressed; the card says it changes the Network State. Tags below the minimum games get no button.

### Inspector
- **Tag view**, above the metrics: "N games in the network have this tag" (after the Minimum Months Filter), then the games (rank, name) — the first 10 and "Show all N"; then the connected tags (tag, cluster swatch, shared games, lift), sorted by shared games, each row selecting that edge (dims the rest, pans it into view). No external links.
- **Edge view** keeps "Games having both tags" with rank, AppID and name.
- Metrics are a two-column list with muted labels (the prototype's `.kv` grid). Labels are plain names; each label's tooltip gives the description and the column name. Glossary terms keep their glossary names. The words "hub" and "importance" are never used.
- The AG Grid tables keep the column names, since they mirror the export files the Column Index documents. The export is unchanged.

Plain names (the active Clustering Weight's strength is marked "used for clustering"; the other weight's values are shown without the mark):

| Shown in the app as | Column |
| --- | --- |
| Cluster | `cluster` |
| Games | `n_games` |
| Total shared games | `strength_shared` |
| Total lift | `strength_lift` |
| Shared games in own cluster | `strength_shared_intra` |
| Lift in own cluster | `strength_lift_intra` |
| Links · in own cluster | `degree` · `degree_intra` |
| Membership Stability | `membership_stability` |
| Prominence in own cluster (z), "max X in an n-tag cluster" | `within_z` |
| Spread across clusters | `participation` |
| Fit to own cluster (silhouette), "descriptive" | `silhouette` |
| Mean game-set distance to members | `medoid_score` |
| Cluster Center | `is_center` |
| Shared games (edge) | `shared_games` |
| Lift (edge) | `lift` |
| Cluster Center (cluster) | `center` |
| Center's game-set distance | `center_medoid_score` |
| Most-linked member | `top_strength_tag` |
| Center is the most-linked member | `center_is_top_strength` |
| Mean Membership Stability | `mean_membership_stability` |
| Boundary crossing (conductance) | `conductance` |
| Agreement after removal (ARI, reclustered) | `rc_ari` |
| Beyond seed noise — "screening flag, not a significance test" | `rc_ari_beyond_noise` |
| Change in Q (reclustered) | `rc_delta_modularity` |
| Silhouette after removal (reclustered) | `rc_delta_silhouette` / `rc_silhouette_after` |
| Change in multi-tag · one-tag clusters | `rc_delta_k` · `rc_delta_s` |
| Cluster Centers lost | `rc_centers_lost` |
| Change in Q (clusters kept) | `fp_delta_modularity` |
| Silhouette after removal (clusters kept) | `fp_delta_silhouette` / `fp_silhouette_after` |

### Summary row, Network State sentence and Cluster quality
- **Summary row** above the graph (Workbench), each value large with a muted label: Games "100 of 100" · Tags · Links · Clusters "3 + 4 multi-tag + one-tag" · Q "0.17 · excess +0.11" · Silhouette "0.04 · descriptive" (full qualifier in the tooltip). Every item has a tooltip.
- Under it, one muted line states the Network State as a sentence with the `state_id` (click to copy), e.g. "Overall Top 100, games with ≥ 0 months observed; tags on ≥ 8 games, links of ≥ 8 shared games; 11 Genre Tags hidden; Louvain on shared games, γ 1.00, seed 20261003 · 4ceb7990d20d".
- The Q / null-model / noise sentences leave the area above the graph. The **Cluster quality** tab shows five boxes with tooltips — Q (γ), Null-model excess (z, null mean ± SD), Coverage, Silhouette ("descriptive"), Seed noise (ARI min, mean) — then the two full sentences once, in small muted text, then the connections and replicate grids.
- **ARI** is shown as a number only. Its tooltip: "ARI (adjusted Rand index) compares two partitions: 1 = identical clusters, about 0 = no more agreement than chance. Here: each of the K noise seeds against the clusters shown; min is the seed that differed most." No bands, no stable/unstable words, no colours.
- Every slider's label shows its current value and updates while dragging ("Minimum games per tag 8").

### Styling and layout (variant A, with B's graph and responsive behaviour)
- Hand-written CSS in `assets/app.css` from the prototype's tokens (`--bg`, `--panel`, `--line`, `--ink`, `--mute`, `--acc`); system fonts only; tabular numerals for every number; no new dependency.
- Controls panel in sections (Data, Filters, Clustering, State); segmented buttons for every RadioItems; Genre Tags as toggle chips; tabs like the prototype's nav; buttons styled as in the prototype; AG Grid themed to the tokens (compact rows, muted headers, right-aligned numbers).
- From B: thin dark node borders, slightly muted cluster colours, lighter edges; the legend floating bottom-left over the graph; the layout switch and a Fit button top-right; every fit leaves room for open overlays.
- Collapsed Inspector, or a narrow window: the Inspector floats as a card over the right of the graph (closed with ×) and the graph refits around it.
- The tables pane can be resized with a drag handle; in the narrow form it is a bottom sheet with a grip.
- Breakpoints: ≥ 1280 px variant A as is; 1024–1279 px the Controls panel becomes a pill bar under the header (each pill shows its value, a popover holds the control) and the Inspector floats; < 1024 px additionally the tables become the bottom sheet. "Graph only" is the narrowest form at any width. Collapsible panels keep working as today.

### Analysis Report mode §1
- The Network State as a short table: dataset and Build; games after the filter (of 100); Minimum Months Filter; minimum games per tag; minimum shared games; hidden tags by name; removed tags by name; Clustering Weight; algorithm; γ; seed; R; K. The `state_id` on top, prominent. The raw JSON behind a "Show JSON" toggle (`<details>`) and in the export, never one tag id per line on the page.

## Overrides
- [Steam Success Study spec](../steam-success-study/spec.md) "Renderer boundary" and "Out of Scope": the move to Cytoscape.js 3.34 in our own wrapper happens now (canvas renderer; WebGL stays off). Positions are de-overlapped.
- [App Bundle spec](../app-bundle/spec.md) and [ADR 0001](../../docs/adr/0001-app-bundle-wheels-not-frozen.md): no dash-cytoscape wheel; the App Bundle follows the renderer switch (app-bundle 01 is blocked by issue 01 here).

## Out of scope
- Any change to clustering, metrics, the Network State or its `state_id`, the export schema.
- The WebGL renderer, continuous physics, exporting dragged positions.
- Semantic cluster names, interpretation bands, stable/unstable labels.

## Issues

- [01: Plain Cytoscape.js renderer](issues/01-plain-cytoscape-renderer.md)
- [02: Styling shell and responsive Workbench](issues/02-styling-shell-and-responsive-workbench.md)
- [03: Non-overlapping layouts and the packed Cluster-separated layout](issues/03-non-overlapping-layouts.md)
- [04: Graph labels and focus cluster](issues/04-graph-labels-and-focus-cluster.md)
- [05: Graph motion](issues/05-graph-motion.md)
- [06: Tag search](issues/06-tag-search.md)
- [07: Inspector content and plain metric names](issues/07-inspector-content-and-plain-names.md)
- [08: Summary row, Network State sentence and Cluster quality boxes](issues/08-summary-row-and-quality-boxes.md)
- [09: Readable Analysis Report §1](issues/09-report-network-state-table.md)
