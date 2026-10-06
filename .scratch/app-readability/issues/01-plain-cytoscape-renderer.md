# 01: Plain Cytoscape.js renderer

**What to build:** the graph is drawn by Cytoscape.js 3.34 through our own wrapper instead of dash-cytoscape. It behaves exactly as today (taps on tags, links, regions and the background; selection; legend; Global and Cluster-separated; Re-layout). It also gains a canvas that follows its container and a first fit that fills it.

**Blocked by:** none

**Status:** done

Spec: [App readability spec](../spec.md): "Renderer", "Facts found while grilling". Prototype: [01-styling-directions](../prototypes/01-styling-directions/PROTOTYPE-styling-directions.html) (graph code in `mountGraph`, `syncGraph`, `fitTo`, `targetBox`).

- [x] `cytoscape.min.js` 3.34.x is vendored in `src/steamstudy/app/assets/` with its licence. No page loads anything from outside 127.0.0.1 (the existing test still passes).
- [x] `assets/graph.js` owns the Cytoscape instance.
  - Dash sends one store: elements (ids, labels, cluster, size and classes), target positions, regions and view commands.
  - Taps on a node, an edge, a region title or the background come back through `dash_clientside.set_props` on a `graph-event` store.
  - `select()` and the inspector use that store instead of `tapNodeData` / `tapEdgeData`.
- [x] `renderer.py` stays the only Python module that knows the renderer, and its docstring names `graph.js` as the other half of the boundary. AppID lists never enter the payload.
- [x] A ResizeObserver resizes the canvas whenever its container changes size: a panel collapses or opens, "Graph only" is chosen, the window is resized. The view refits until the user has zoomed or panned.
- [x] Fits target the final positions (the bounding box of target positions and regions), not the current ones.
- [x] Render-time stretch: x is scaled by the canvas aspect ratio, capped at 1.6×, before the fit. Exported coordinates are untouched.
- [x] dash-cytoscape is removed from `pyproject.toml` (including its upgrade comment) and `uv.lock`. `FIT_JS` and the `_cyreg` lookup are gone. `docs/running-guide.md` names the vendored Cytoscape.js version, and says how to upgrade it (replace the file, rerun the browser checks), instead of dash-cytoscape.
- [x] The [Steam Success Study spec](../../steam-success-study/spec.md) "Renderer boundary" and the WebGL line of "Out of Scope" point here.
- [x] Tests:
  - The callbacks that build the graph payload are tested as functions: the payload has every visible node and edge, no AppIDs, and a position for every node.
  - The served page loads only local assets.
- [x] Browser checks on the real Build:
  - The first fit fills the canvas in both layouts at 1280 × 800, and again after each panel is collapsed.
  - Every tap kind opens the right inspector view.

## Comments

**2026-10-06 (implemented):** `renderer.py` builds the `graph-data` payload; `assets/graph.js` owns Cytoscape.js 3.34.3 (vendored with `cytoscape.LICENSE.txt`, integrity checked against the npm registry). Selection reaches the canvas as a `Patch` of `graph-data` (`selected`), so a click never resends the elements. Region titles are clickable through `text-events`; a tap elsewhere inside a region counts as a background tap. A background tap now clears the selection. Browser checks on Build `20261006T062622Z-7a23ae9f` at 1280 × 800: the first fit fills about 88 % of the canvas in both layouts and refits after each panel is collapsed (with the Inspector collapsed the canvas is 2.5 : 1, so the 1.6× stretch cap leaves the Cluster-separated layout at 62 % width until issue 03 packs it); a tag, a link, a region title and the background each open the right inspector view.
