# Research 20: Interactive graph visualization alternatives for the Tag Network

Ticket: [../issues/20-graph-visualization-alternatives.md](../issues/20-graph-visualization-alternatives.md)
Researched: 2026-10-04. Versions, release dates and licences were read live on that date from the npm registry (`https://registry.npmjs.org/<pkg>`), PyPI JSON (`https://pypi.org/pypi/<pkg>/json`) and the GitHub REST API (`/repos/<owner>/<repo>`, `/releases`, `/commits`). Feature claims come from official docs, READMEs, published type declarations (`.d.ts` on unpkg) and source files. Bundle sizes are uncompressed bytes of the published minified file on unpkg. Nothing was installed or benchmarked. Anything marked *(inferred)* or *(unverified)* was not confirmed in a primary source.

This note does not repeat the framework comparison in [06](06-web-app-stack.md). It takes the [17 spike](../issues/17-dash-cytoscape-windows-spike.md) as the baseline: dash-cytoscape 1.0.2 passes every functional check, but it bundles Cytoscape.js 3.28.1 (canvas only), redraws the worst-case graph in a median 55 ms, and sends about 800 KB of elements per update.

## Question

Besides dash-cytoscape and a hand-wrapped Cytoscape.js in Panel, which graph libraries could render the **Tag Network** (~400 Tag nodes, up to ~5,000 weighted edges, cluster colours and cluster-centre styling, node **and** edge clicks reaching Python, Python-computed preset positions with tinted cluster-region backgrounds, layout switch without re-mounting, offline, Windows, permissive licence, maintained)? How do they compare, and how would each plug into Dash or Panel?

## Summary

- **Cytoscape.js itself has moved on.** The current release is 3.34.3 (2026-09-07). Since 3.31 it has an opt-in WebGL mode (`renderer: {name: 'canvas', webgl: true}`). The authors claim 20 → 100+ FPS on a 1,200-node / 16,000-edge network [C2]. All node and label styles are supported, so diamonds and borders keep working. Haystack, straight and bezier edges are supported. Dashed edges, edge overlays/underlays, gradients and non-triangle arrows are not [C2, C3]. The mode is still only documented in the 3.31 "preview" blog post and a design doc, not in the API docs [C7]. One user reported WebGL *slowing* an Intel integrated GPU from 25–40 to 3–4 FPS; the issue was closed as a probable driver problem [C4].
- **dash-cytoscape cannot simply be pointed at WebGL.** Its React layer (`react-cytoscapejs` 2.0.0) passes a fixed list of options to `new Cytoscape(...)` and has no `renderer` option [C9]. Getting WebGL means writing your own thin wrapper or forking. Useful detail for a quick hack: the 1.0.2 bundle sets `window.cy` to the instance [C10].
- **sigma.js 3 + graphology is the strongest pure-WebGL option.** It is MIT, active (3.0.3 on 2026-04-30; 4.0.0-beta.7 on 2026-10-02), 188 KB + 74 KB minified. It has node and edge click events (edge events off by default) and a contour layer (`createContoursProgram`) that can draw cluster regions [S2, S3, S4]. The gaps are in v3: there is no built-in diamond and no bordered non-circle node, so cluster centres need a custom node program or a circle + border. v4 (beta) adds `sdfDiamond` + `layerBorder` [S6]. No maintained Dash wrapper exists. ipysigma pins `sigma@3.0.0-alpha2` and loads from a CDN when used inside Panel [Y1, Y2, Y15].
- **AntV G6 5 has every feature built in**: a `diamond` node type, `hull` and `bubble-sets` plugins for cluster regions, `node:click`/`edge:click`, `setData`/`updateNodeData`, and an optional WebGL renderer [G2, G3, G4, G5]. It is MIT. But it is the heaviest bundle (1.38 MB min), the canvas renderer is the default, and its npm `latest` tag (5.1.1, 2026-05-08) sits next to two version entries (5.2.1, 5.3.1) that cannot be installed [G1]. There is no Python wrapper.
- **The rest fit worse.** vis-network 10 is canvas-only, with diamond/border and `beforeDrawing` hooks, but it brings no speed gain over Cytoscape canvas, and its Dash wrappers are stale (dashvis 2024-01, visdcc 2025-03 with vis CSS from a CDN). cosmos.gl 3 (MIT) is GPU-fast and has diamonds, link clicks and preset positions, but no built-in labels or node borders (stroke is in a 3.5 pre-release). Cosmograph's own packages are CC-BY-NC / GPL. force-graph, ECharts, Reagraph and D3 each lack one key piece, or would need a lot of DIY code. pyvis, gravis and netgraph are stale, display-only or GPL. yFiles, Ogma and KeyLines are commercial. yFiles Graphs for Jupyter's free licence forbids use outside Jupyter [Y12, M1–M3].
- **Payload is a separate lever from the renderer.** Any custom wrapper can keep AppID lists on the server and send only IDs, fetching AppIDs on click. Dash's `Patch` sends partial property updates (380 B vs 368 kB in Plotly's example) [Y14]. Whether `Patch` helps dash-cytoscape's `elements` is *(unverified)*.
- **Ranked shortlist:**
  1. **Cytoscape.js 3.34 with WebGL, in a thin custom wrapper.** This could be a Dash clientside module in `assets/` + `set_props`, or a Panel `JSComponent`. It reuses the spike's stylesheet, element JSON and tap semantics unchanged.
  2. **sigma.js 3 (+ graphology, @sigma/layer-webgl).** This is the performance fallback if Cytoscape WebGL is slow or buggy on the researcher's GPU. Move to v4 once it is stable for native diamonds and borders.
  3. **AntV G6 5.** Use it if built-in hulls and bubble-sets for cluster regions matter more than bundle size and English docs.
- **Recommendation for the Web stack selection grilling:** keep Dash. The spike passed, and the default thresholds give about 1,359 edges, where the spike says the graph is "much lighter". Treat the renderer as a replaceable leaf. If worst-case smoothness matters, the next step is a **newer Cytoscape.js (WebGL) behind your own ~150–250-line wrapper, not a renderer switch**: it keeps every style, event and layout decision from 17, and costs one short spike. Switch to sigma.js only if that spike shows Cytoscape WebGL not beating 55 ms, or if it misbehaves on the researcher's GPU.

## Comparison matrix

Legend: ✅ built in / first-class · 🟡 possible with moderate custom work or caveats · ❌ not supported / poor fit. Edge-click events must reach Python, which always needs a wrapper (see "Integration paths"). The rows below rate what the JS library exposes.

### A. JS renderers, main contenders

| Criterion | Cytoscape.js 3.34 (WebGL mode) | sigma.js 3 + graphology | AntV G6 5 | vis-network 10 | cosmos.gl 3 |
|---|---|---|---|---|---|
| Renderer / scale (400 n, 5k e) | ✅ WebGL opt-in on top of canvas; falls back to canvas when zoomed very close [C3]; 1.2k n / 16k e at 100+ FPS claimed [C2]. 🟡 one integrated-GPU slowdown report [C4] | ✅ WebGL, instanced drawing, WebGL picking for hover/click [S5] | 🟡 Canvas by default; SVG or WebGL via `@antv/g-webgl` [G2] | 🟡 Canvas 2D only; no gain over current Cytoscape canvas *(inferred)* | ✅ All layout and drawing on GPU; "hundreds of thousands of points" [K1] |
| Cluster colours + cluster-centre styling (diamond + border) | ✅ same stylesheet as the spike; "all node and label styles are fully supported" [C2]; non-simple shapes drawn as textures [C3] | 🟡 per-node colour ✅; v3 has circle, `@sigma/node-square`, circle-only `@sigma/node-border` [S8]; diamond needs a custom program or an image. v4 beta: `sdfDiamond` + `layerBorder` [S6] | ✅ built-in `diamond` node type with stroke [G3] | ✅ `diamond` shape + `borderWidth` [V2] | 🟡 `setPointShapes` incl. Diamond [K2]; no border in 3.4.2 (stroke in `3.5.0-stroke.*` pre-release [K3]); `outlinedPointIndices` for highlight [K1] |
| Node + edge click events (JS side) | ✅ `tap` on nodes and edges (spike: haystack edges clickable); WebGL picking used for hit detection [C3] | ✅ `clickNode`, `clickEdge`; edges need `enableEdgeEvents: true` in 3.0.3 [S2, S3] | ✅ `node:click`, `edge:click` [G5] | ✅ `click` gives `{nodes, edges}` arrays [V1]; 🟡 a node click also selects its connected edges by default *(inferred, verify)* | ✅ `onPointClick`, `onLinkClick` (index-based) [K2] |
| Preset positions + tinted cluster-region background | ✅ `preset` layout; regions as locked background nodes (worked in 17) or `cytoscape-layers` / `cytoscape-bubblesets` [C8]; 🟡 these extensions are untested with WebGL | 🟡 x/y are node attributes ✅; regions via `createContoursProgram` WebGL layer [S4] or a custom canvas via `createCanvas` + `beforeRender` [S7] | ✅ positions in node `style.x/y`; `hull` and `bubble-sets` plugins [G3] | 🟡 `x`/`y` with physics off ✅; regions drawn by hand in `beforeDrawing` canvas hook [V1] | 🟡 `setPointPositions` + `enableSimulation: false` ✅ [K1, K2]; no background-shape API, needs overlay *(inferred)* |
| Update without re-mount | ✅ `cy.json()`, `eles.positions()`, `cy.batch()` | ✅ mutate the graphology graph or `setGraph` [S7] | ✅ `setData`, `updateNodeData`, `draw` [G4] | ✅ DataSet updates, `setData`, `moveNode` [V1] | ✅ `setPointPositions` with GPU transitions [K1] |
| Offline bundling | ✅ zero runtime deps; single ESM 434 KB min [U] | ✅ sigma 188 KB + graphology 74 KB min [U]; layer packages separate | 🟡 1.38 MB min UMD [U]; extra `@antv/g-webgl` for WebGL | ✅ standalone UMD 652 KB [U] | ✅ npm package; size not measured |
| Python integration path | 🟡 own wrapper (Dash clientside/custom component; Panel `JSComponent`); dash-cytoscape can't enable WebGL [C9] | 🟡 own wrapper; ipysigma is ipywidgets-only, sigma 3.0.0-alpha2 [Y2] | 🟡 own wrapper only | 🟡 dashvis / visdcc (stale) or own wrapper [Y7, Y8] | 🟡 own wrapper; Cosmograph widget is GPL/CC-BY-NC [Y4, K3] |
| Licence | ✅ MIT | ✅ MIT | ✅ MIT | ✅ Apache-2.0 OR MIT | ✅ MIT (`@cosmos.gl/graph`); ❌ `@cosmograph/*` CC-BY-NC-4.0 [K3] |
| Maintenance (latest, date) | ✅ 3.34.3, 2026-09-07; push 2026-10-02 | ✅ 3.0.3, 2026-04-30; 4.0.0-beta.7 2026-10-02 [S1] | 🟡 5.1.1, 2026-05-08; GitHub release 2026-04-17; 333 open issues [G1, G6] | ✅ 10.1.2, 2026-08-19; 351 open issues | ✅ 3.4.2, 2026-09-21 |

### B. JS renderers, weaker fits

| Criterion | force-graph 1.52 | Apache ECharts 6 graph series | Reagraph 4.32 | D3 7 (custom canvas) | ngraph |
|---|---|---|---|---|---|
| Renderer / scale | 🟡 Canvas 2D, redraws every frame while the simulation runs [F1] | 🟡 Canvas or SVG (zrender); no `large` mode in graph series options [E1] | ✅ WebGL (three.js / react-three-fiber) [R1] | 🟡 Canvas; everything DIY | ❌ `ngraph.graph` is data only; the `ngraph.pixel` renderer was last released 2017 |
| Cluster-centre styling | 🟡 `nodeCanvasObject` custom paint [F1] | ✅ `symbol: 'diamond'`, `itemStyle.borderColor` [E1] | 🟡 `renderNode` custom three.js node [R2] | 🟡 DIY | ❌ |
| Node + edge clicks | ✅ `onNodeClick`, `onLinkClick` [F1] | ✅ click `params.dataType` is `'node'` or `'edge'` [E2] | ✅ `onNodeClick`, `onEdgeClick` [R2] | 🟡 DIY hit testing (quadtree for nodes; edges by hand) | ❌ |
| Preset positions + regions | 🟡 `fx`/`fy` + `cooldownTicks`; `onRenderFramePre` for backgrounds [F1] | 🟡 `layout: 'none'` with x/y ✅; regions need `cartesian2d` coords + a custom series, or `graphic` (doesn't pan) *(inferred)* [E1] | 🟡 `layoutType: 'custom'` + `layoutOverrides`; `clusterAttribute` [R2] | 🟡 DIY | ❌ |
| Licence / maintenance | ✅ MIT; 1.52.0 2026-09-28 | ✅ Apache-2.0; 6.1.0 2026-05-19 | ✅ Apache-2.0; 4.32.0 2026-06-25 | ✅ ISC; 7.9.0 2024-03-12 | ✅ BSD-3; 20.1.2 2026-02-14 |
| Python path | 🟡 graph-widget (anywidget + marimo, 0.1.17) [Y6]; dash-force-graph 0.0.1 is boilerplate only [Y10] | ✅ Panel `ECharts` pane with `on_event` [E3]; ❌ dash-echarts last release 2021-10 [Y9] | ❌ React-only; Dash component possible, Panel `ReactComponent` possible | ❌ | ❌ |
| Bundle | 173 KB min [U] | 1.12 MB min [U] | three.js + R3F + graphology stack [R1] | small | — |

### C. Python bindings and widgets

| Package | Renderer underneath | Events reach Python | Shapes / centre styling | Offline in a Dash/Panel app | Licence | Latest |
|---|---|---|---|---|---|---|
| dash-cytoscape (baseline) | Cytoscape.js 3.28.1, canvas | ✅ `tapNodeData`/`tapEdgeData` | ✅ | ✅ (17) | MIT | 1.0.2, 2024-07-15 |
| ipysigma | sigma `3.0.0-alpha2` [Y2] | 🟡 `selected_node`/`selected_edge` traits + getters [Y1] | 🟡 shapes "cannot be used with borders" [Y1] | ❌ in Panel, the ipywidgets bridge fetches third-party widget JS from a CDN [Y15] | MIT | 0.24.6, 2025-11-25 |
| ipycytoscape | Cytoscape.js `^3.14` at 2022 build time [Y3] | 🟡 ipywidgets callbacks | ✅ | ❌ same CDN issue | BSD-3 | 1.3.3, 2022-04-04 (last code commit 2023-05) ❌ |
| cosmograph (widget) | Cosmograph (anywidget) | 🟡 | 🟡 | 🟡 | ❌ GPL-3.0-or-later; JS CC-BY-NC [Y4, K3] | 0.5.3, 2025-11-04; 1.0.0b3 pre-release 2026-01-29 |
| anywidget-graph | sigma 3.0.0 + d3-force from `esm.sh` [Y5] | 🟡 anywidget | 🟡 | ❌ imports from CDN at runtime | Apache-2.0 | 0.3.1, 2026-03-16; 3 stars |
| dashvis / visdcc | vis-network (dashvis `^9.1.2`) [Y8] | ✅ selection props | ✅ vis shapes | 🟡 visdcc README loads vis CSS from cdnjs [Y7] | MIT | dashvis 0.1.14, 2024-01-12; visdcc 0.0.63, 2025-03-20 |
| Panel `ECharts` pane | ECharts | ✅ `on_event` [E3] | ✅ | 🟡 *(unverified)* whether Panel serves ECharts JS locally | BSD-3 (Panel) | Panel 1.9.4 |
| Plotly `dcc.Graph` (scattergl) | WebGL scatter | 🟡 nodes ✅ via `clickData`; edges drawn as one line trace with `None` gaps and `hoverinfo='none'` [Y13], so edge clicks need invisible midpoint markers *(inferred)* | ✅ marker `symbol` diamond; 🟡 per-edge width needs one trace per width bucket *(inferred)* | ✅ | MIT | plotly 7.1.0, 2026-09-15 |
| HoloViews `Graph` | Bokeh | 🟡 nodes *or* edges (see 06) | ✅ | ✅ | BSD-3 | 1.23.2 |
| pyvis | vis-network in static HTML | ❌ display-only (06) | ✅ | 🟡 | BSD-3 | 0.3.2, 2023-02-24 ❌ |
| gravis | d3 / vis / three in static HTML | ❌ | 🟡 | 🟡 | Apache-2.0 | 0.1.0, 2021-12-08 ❌ |
| netgraph | matplotlib | ❌ not a web renderer | 🟡 | — | ❌ GPL-3.0 | 4.13.2, 2023-12-11 |
| yfiles-jupyter-graphs | yFiles for HTML | 🟡 | ✅ | — | ❌ proprietary; "may not be used ... outside of the Jupyter System" [Y12] | 2.0.0, 2026-08-10 |

## Per-candidate notes

**Cytoscape.js 3.34 (WebGL).** Enable it with `renderer: {name: 'canvas', webgl: true}` [C2]. Tuning options are `webglTexSize`, `webglTexRows`, `webglTexRowsNodes`, `webglBatchSize` and `webglTexPerBatch` [C6]. It is a mode inside the canvas renderer: a `webgl2` layer under the normal canvas layers, and close zoom switches back to canvas drawing [C3]. Rectangles, round rectangles and ellipses are drawn directly as signed-distance shapes. Every other node shape, including the diamond, is rendered to a texture atlas [C3]. That is fine visually, but texture memory grows with the number of distinct node looks *(inferred)*. Haystack edges are drawn as straight instances [C3]. Bezier edges use 15 fixed segments [C3]. Open WebGL issues include "Arrow shape is always triangle" (#3374) and blurry compound nodes (#3376) [C5]; neither matters for the Tag Network. The WebGL fixes that shipped in 3.31.1–3.33.3 show active work [C5]. The canvas speed-ups (`hideEdgesOnViewport`, `textureOnViewport`, `pixelRatio`) are still in the API, which calls them "now largely moot" [C7]. Gotcha: none of this reaches dash-cytoscape. `react-cytoscapejs` 2.0.0 forwards only `headless`, `styleEnabled`, `hideEdgesOnViewport`, `textureOnViewport`, `motionBlur`, `motionBlurOpacity`, `wheelSensitivity` and `pixelRatio` to the constructor [C9], and dash-cytoscape does not even expose those as props (17). dash-cytoscape's bundle sets `window.cy = cy` [C10]. That allows a clientside hack against the live instance, but not a renderer switch, because the renderer is chosen at construction.

**sigma.js 3 + graphology.** It renders WebGL with instanced drawing, and it picks nodes and edges by WebGL picking [S5]. Edge events are behind `enableEdgeEvents` in 3.0.3 [S2]. The website docs now list three separate settings (`enableEdgeClickEvents`, …), which look like the v4 API [S3]. `hideEdgesOnMove` and `hideLabelsOnMove` exist for pan/zoom smoothness [S2]. Cluster regions: `@sigma/layer-webgl`'s `createContoursProgram` draws contour lines around a node set as a background layer [S4]. Alternatively, draw polygons on a `createCanvas` layer in `beforeRender` [S7]. Cluster-centre styling is the weak spot in v3. You get circles, squares (`@sigma/node-square`), circle borders (`@sigma/node-border`), images and pie charts [S8]. A bordered diamond needs a custom node program (GLSL) or a pictogram image. Sigma v4 rewrites programs as "primitives" with `sdfDiamond` and `layerBorder`, adds node opacity and label events, and drops WebGL 1 [S5, S6]. It is still beta (4.0.0-beta.7, 2026-10-02) [S1], and its docs site calls itself "alpha" [S6]. Edge width comes from the `size` attribute. Weighted edges map directly *(inferred from v3 attributes)*. Graphology 0.26.0 dates from 2025-01-26 but is a stable core [S9].

**AntV G6 5.** On paper it is the most complete: built-in `diamond`, `hull` and `bubble-sets` plugins, and a `background` plugin [G3]. It has `node:click`/`edge:click` [G5] and `setData`/`updateData`/`updateNodeData`/`translateElementTo` [G4]. You can switch the renderer per layer, e.g. WebGL for `main` [G2]. The costs are a 1.38 MB min bundle, canvas by default, documentation that is Chinese-first, and npm metadata that lists 5.2.1 and 5.3.1 publish times with no installable versions [G1]. The GitHub release cadence slowed in 2025–2026 (5.0.49 2025-06, then 5.1.1 2026-04) [G6]. WebGL rendering of hulls and bubble-sets is *(unverified)*.

**vis-network 10.** It is mature and well documented. It has a `diamond` shape with `borderWidth` [V2], a `click` event with node and edge ID arrays, `beforeDrawing` for custom background drawing, and `setData`/`moveNode`/DataSet updates [V1]. It is canvas-only, so it does not solve the 55 ms worst case. Both Dash wrappers are stale [Y7, Y8].

**cosmos.gl 3.** This is the MIT engine under Cosmograph, now at `@cosmos.gl/graph` [K1]. It has index-based events (`onPointClick`, `onLinkClick`), shapes including Diamond, preset positions with `enableSimulation: false`, and animated GPU transitions between position sets [K1, K2]. Those transitions would make the Global ↔ Cluster-separated switch look good. But it has no built-in labels: link sampling exists "for rendering labels or overlays" [K1], so you need a DOM or canvas label overlay. Point borders are only in a 3.5 pre-release [K3]. Its strength, GPU force layout for 100k+ points, is unused when Python computes positions. Do not confuse it with `@cosmograph/cosmograph`/`@cosmograph/cosmos` (CC-BY-NC-4.0) or the `cosmograph` PyPI widget (GPL-3.0) [K3, Y4].

**force-graph.** Canvas with full custom paint (`nodeCanvasObject`, `linkCanvasObject`, `onRenderFramePre`) and `onNodeClick`/`onLinkClick` [F1]. It is built around d3-force. Preset positions work by pinning `fx`/`fy`. It is good for small graphs and redraws each frame while the simulation runs [F1].

**Apache ECharts graph series.** It has `layout: 'none'` with node x/y, `symbol: 'diamond'`, categories for cluster colours [E1], and edge clicks via `dataType: 'edge'` [E2]. The graph series can sit in a `cartesian2d` coordinate system [E1], which in principle allows polygon series for regions *(inferred)*. It is the only candidate with a ready-made, maintained Panel pane that sends events to Python [E3]. Dash has no maintained wrapper [Y9].

**Reagraph.** WebGL via three.js, with `onEdgeClick`, a `custom` layout type and `clusterAttribute` [R1, R2]. It is React-only and pulls in three.js, react-three-fiber and drei. That is a heavy stack for 400 nodes.

**D3 custom canvas / ngraph.** Everything would be custom: hit testing for edges, zoom, labels, region drawing. Not worth it when Cytoscape.js and sigma already do it.

**Commercial (for completeness).** yFiles for HTML has annual term licences: Single Developer €9,200/yr, Project €18,400/yr, Site €55,200/yr, with discounted academic licences on request [M1]. Ogma (Linkurious) is "a commercial JavaScript library" with a WebGL-first engine and pricing by trial/quote [M2]. KeyLines and ReGraph (Cambridge Intelligence) are subscription-only with no public prices, a 21-day trial, and "We don't currently offer academic licenses" [M3]. None are needed.

## Integration paths (shortlist)

All three shortlisted renderers need the same small contract. Python sends `{nodes, edges, positions, style}`. JS renders, and it reports clicks back as `{kind: 'node'|'edge', id}`. Python then looks up the AppIDs in its own state, so edges in the browser need only `id`, `source`, `target`, `weight`, `cluster` *(design suggestion; cuts the ~800 KB payload)*.

### Dash

1. **Clientside module (no build step).** Vendor `cytoscape.esm.min.js` (or `sigma.min.js` + `graphology.umd.min.js`) into `assets/`. Dash serves `assets/` locally, so it stays offline. Use an `html.Div(id='graph')` as the mount point. A clientside callback on a `dcc.Store` (elements/positions) creates the instance once, keeps it on `window`, and later calls `cy.json(...)` / `eles.positions(...)` instead of re-mounting. JS click listeners call `dash_clientside.set_props('graph-event', {data: {...}})` (Dash ≥ 2.16) [D2], and a normal Python callback listens to that store. Expect about 150–250 lines of JS for Cytoscape.js and 250–400 for sigma (custom diamond program and contours) *(estimate)*. Gotchas: you own instance lifetime if the div is re-rendered, and Dash tooling does not type-check the store contract.
2. **Proper Dash component (`dash-component-boilerplate`).** Use the Cookiecutter template; it needs Node/npm [D1]. Write a React component that wraps the library, with props `elements`, `stylesheet`, `layoutPositions` and events `tapNode`/`tapEdge`. The JS is bundled into the Python package and served locally. It is more work than option 1 (build tooling, React lifecycle). Dash renderer source lists React 18.2, 18.3.1 and 19.2.4 as supported *(dev branch; confirm for 4.4.1)* [D3]. Forking dash-cytoscape to bump `cytoscape` and patch `react-cytoscapejs` to forward `renderer` is a variant of this path.
3. **Stay on dash-cytoscape, hack via `window.cy`.** This is the cheapest option and has no WebGL. It is fine if the default threshold graph is smooth enough.

### Panel

1. **`JSComponent` / `ReactiveESM`** with an `_esm` that imports the library and `_importmap` / `_bundle`. By default imports come from `esm.sh`. `panel compile` bundles them with npm + esbuild for offline use [P1]. Python → JS goes through parameters (`model.on('change:...')`). JS → Python goes through `model.send_event` / `send_msg` (06 [P6]). The JS size is similar to Dash option 1.
2. **`AnyWidgetComponent`** follows the anywidget front-end API (`model.get/set/on/save_changes`) [P2]. Writing the wrapper as an anywidget ESM would let the same JS also run in Jupyter or marimo. Panel cannot yet render *existing* anywidget packages natively. That is open PR #8428 (`pn.pane.AnyWidget`, last updated 2026-06-05) [P3]. Today, third-party ipywidgets such as ipysigma go through `ipywidgets_bokeh`, which fetches their JS from a CDN [Y15].
3. **ECharts pane** is the only no-JS path with node+edge events [E3]. Cluster regions and centre borders need care.

## Open questions / spike checklist

1. **Cytoscape.js 3.34 WebGL on the researcher's machine:** median full-redraw time at 400 nodes / 4,964 haystack edges, DPR 2, against the 55 ms baseline. Check which GPU Chrome/Edge uses (`chrome://gpu`), because of the integrated-GPU report [C4].
2. Does WebGL mode render the spike's stylesheet unchanged: diamond + border centres, `mapData` widths, labels with `min-zoomed-font-size`, and tinted locked region nodes behind edges? Are haystack edges still clickable (`tap` on edge)?
3. Does `cytoscape-layers` (or `cytoscape-bubblesets`) draw correctly with `webgl: true`, or should regions stay as background nodes?
4. Can `hideEdgesOnViewport` be toggled on an existing instance via `window.cy` in dash-cytoscape 1.0.2 (no WebGL), and does that alone make pan/zoom smooth enough?
5. Does `Patch` on dash-cytoscape `elements` cut the ~800 KB per update, or does `react-cytoscapejs` diffing undo the gain?
6. If sigma is tried: are the `createContoursProgram` regions readable as tinted cluster areas? How much GLSL does a bordered diamond take in v3, and is v4 stable by then?
7. Offline check for any custom wrapper: with the network disabled, confirm that no request leaves localhost (Panel `panel compile` output, or Dash `assets/`).

## Sources

Cytoscape.js
- [C1] npm registry `cytoscape` (3.34.3, 2026-09-07, MIT): https://registry.npmjs.org/cytoscape
- [C2] WebGL preview blog (3.31; enable option, FPS claims, supported/unsupported styles): https://blog.js.cytoscape.org/2025/01/13/webgl-preview/
- [C3] WebGL renderer design doc (canvas-mode layering, SDF shapes vs textures, haystack as straight, 15-segment beziers, picking): https://github.com/cytoscape/cytoscape.js/blob/unstable/documentation/webgl.md
- [C4] Issue #3436, WebGL slower on integrated GPU (closed 2026-04-15): https://github.com/cytoscape/cytoscape.js/issues/3436
- [C5] WebGL issues #3374, #3376 (open, known-issue), #3406, #3409, #3410 (fixed 3.33.x): https://github.com/cytoscape/cytoscape.js/issues?q=webgl
- [C6] WebGL option names and limits in source: https://github.com/cytoscape/cytoscape.js/blob/unstable/src/extensions/renderer/canvas/webgl/drawing-redraw-webgl.mjs
- [C7] Cytoscape.js API docs (rendering hints "now largely moot"; no WebGL section found when searched 2026-10-04): https://js.cytoscape.org/
- [C8] `cytoscape-layers` 3.1.0, `cytoscape-bubblesets` 4.1.0 (npm, MIT): https://registry.npmjs.org/cytoscape-layers , https://registry.npmjs.org/cytoscape-bubblesets
- [C9] `react-cytoscapejs` 2.0.0 constructor options: https://unpkg.com/react-cytoscapejs@2.0.0/src/component.js
- [C10] dash-cytoscape `window.cy = cy` (source line 165; present as `window.cy=e` in the 1.0.2 npm bundle): https://github.com/plotly/dash-cytoscape/blob/main/src/lib/components/Cytoscape.react.js , https://unpkg.com/dash-cytoscape@1.0.2/dash_cytoscape/dash_cytoscape.min.js
- [C11] dash-cytoscape package.json (react-cytoscapejs 2.0.0): https://github.com/plotly/dash-cytoscape/blob/main/package.json

sigma.js / graphology
- [S1] npm `sigma` dist-tags (latest 3.0.3 2026-04-30; beta 4.0.0-beta.7 2026-10-02): https://registry.npmjs.org/sigma
- [S2] sigma 3.0.3 settings typings (`enableEdgeEvents`, `hideEdgesOnMove`): https://unpkg.com/sigma@3.0.3/dist/declarations/src/settings.d.ts
- [S3] sigma events docs: https://www.sigmajs.org/docs/advanced/events
- [S4] `@sigma/layer-webgl` README (`createContoursProgram`): https://github.com/jacomyal/sigma.js/blob/main/packages/layer-webgl/README.md
- [S5] sigma changelog (3.0.0 picking + instancing; 4.0.0 rewrite): https://github.com/jacomyal/sigma.js/blob/main/CHANGELOG.md , https://github.com/jacomyal/sigma.js/blob/v4/CHANGELOG.md
- [S6] sigma v4 styles and primitives (`sdfDiamond`, `layerBorder`; site labelled alpha): https://v4.sigmajs.org/concepts/styles-and-primitives/
- [S7] sigma 3.0.3 class typings (`createCanvas`, `setGraph`) and events (`beforeRender`): https://unpkg.com/sigma@3.0.3/dist/declarations/src/sigma.d.ts , https://unpkg.com/sigma@3.0.3/dist/declarations/src/types.d.ts
- [S8] `@sigma/*` packages on npm (node-border, node-square, node-image, node-piechart, edge-curve, layer-webgl; all 3.x, 2024-12): https://www.npmjs.com/search?q=%40sigma%2F
- [S9] npm `graphology` 0.26.0 (2025-01-26, MIT): https://registry.npmjs.org/graphology

AntV G6
- [G1] npm `@antv/g6` (latest 5.1.1 2026-05-08; 5.2.1/5.3.1 time entries without versions): https://registry.npmjs.org/@antv/g6
- [G2] G6 renderer guide (Canvas default; SVG/WebGL): https://g6.antv.antgroup.com/en/manual/further-reading/renderer
- [G3] G6 built-in registry (diamond node; hull, bubble-sets, background plugins): https://github.com/antvis/G6/blob/v5/packages/g6/src/registry/build-in.ts
- [G4] G6 Graph API (`setData`, `updateData`, `updateNodeData`, `draw`, `translateElementTo`): https://github.com/antvis/G6/blob/v5/packages/g6/src/runtime/graph.ts
- [G5] G6 edge event constants (`edge:click`): https://github.com/antvis/G6/blob/v5/packages/g6/src/constants/events/edge.ts
- [G6] G6 GitHub releases: https://github.com/antvis/G6/releases

vis-network
- [V1] Network docs (click params, `beforeDrawing`, `setData`, `moveNode`): https://visjs.github.io/vis-network/docs/network/
- [V2] Node options (shapes incl. `diamond`, `borderWidth`, `x`/`y`, `fixed`): https://visjs.github.io/vis-network/docs/network/nodes.html

cosmos.gl / Cosmograph
- [K1] cosmos.gl README (v3 features, transitions, link sampling): https://github.com/cosmosgl/graph/blob/main/README.md
- [K2] cosmos.gl 3.4.2 typings (`onPointClick`, `onLinkClick`, `setPointShapes` incl. Diamond, `setPointPositions`): https://unpkg.com/@cosmos.gl/graph@3.4.2/dist/config.d.ts , https://unpkg.com/@cosmos.gl/graph@3.4.2/dist/index.d.ts
- [K3] npm `@cosmos.gl/graph` (MIT; `3.5.0-stroke.1` pre-release 2026-10-01), `@cosmograph/cosmos` and `@cosmograph/cosmograph` (CC-BY-NC-4.0): https://registry.npmjs.org/@cosmos.gl/graph , https://registry.npmjs.org/@cosmograph/cosmograph

Other JS
- [F1] force-graph README (API table): https://github.com/vasturiano/force-graph/blob/master/README.md
- [E1] ECharts graph series options (`layout`, coordinate systems, symbols): https://github.com/apache/echarts-doc/blob/master/en/option/series/graph.md
- [E2] ECharts events API (`dataType` 'node'/'edge'): https://github.com/apache/echarts-doc/blob/master/en/api/events.md
- [E3] Panel ECharts pane (`on_event`, `js_on_event`, canvas/svg): https://panel.holoviz.org/reference/panes/ECharts.html
- [R1] Reagraph README: https://github.com/reaviz/reagraph
- [R2] Reagraph 4.32.0 typings (`onEdgeClick`, `clusterAttribute`, `custom` layout): https://unpkg.com/reagraph@4.32.0/dist/GraphScene.d.ts , https://unpkg.com/reagraph@4.32.0/dist/layout/types.d.ts
- [U] Bundle sizes (uncompressed, unpkg): cytoscape@3.34.3 `dist/cytoscape.esm.min.mjs`; sigma@3.0.3 `dist/sigma.min.js`; graphology@0.26.0 `dist/graphology.umd.min.js`; vis-network@10.1.2 `standalone/umd/vis-network.min.js`; @antv/g6@5.1.1 `dist/g6.min.js`; echarts@6.1.0 `dist/echarts.min.js`; force-graph@1.52.0 `dist/force-graph.min.js`

Python bindings
- [Y1] ipysigma README (visual variables, `node_shape` limits, `selected_node`/`selected_edge`): https://github.com/medialab/ipysigma
- [Y2] npm `ipysigma` 0.24.6 dependencies (`sigma: 3.0.0-alpha2`): https://registry.npmjs.org/ipysigma
- [Y3] npm `jupyter-cytoscape` 1.3.3 dependencies: https://registry.npmjs.org/jupyter-cytoscape
- [Y4] PyPI `cosmograph` (GPL-3.0-or-later; anywidget): https://pypi.org/project/cosmograph/
- [Y5] anywidget-graph JS imports from esm.sh: https://github.com/GrafeoDB/anywidget-graph/blob/main/src/anywidget_graph/ui/index.js
- [Y6] PyPI `graph-widget` (anywidget force-graph): https://pypi.org/project/graph-widget/
- [Y7] visdcc README / PyPI: https://github.com/jimmybow/visdcc , https://pypi.org/project/visdcc/
- [Y8] dashvis PyPI and package.json (`vis-network ^9.1.2`): https://pypi.org/project/dashvis/ , https://github.com/lewkoo/dashvis
- [Y9] PyPI `dash-echarts` (0.0.12.9, 2021-10-25): https://pypi.org/project/dash-echarts/
- [Y10] PyPI `dash-force-graph` (0.0.1, boilerplate README): https://pypi.org/project/dash-force-graph/
- [Y11] PyPI `pyvis`, `gravis`, `netgraph`: https://pypi.org/project/pyvis/ , https://pypi.org/project/gravis/ , https://pypi.org/project/netgraph/
- [Y12] yfiles-jupyter-graphs licence text (PyPI metadata): https://pypi.org/project/yfiles-jupyter-graphs/
- [Y13] Plotly network graphs (edges as one line trace with `None` separators): https://plotly.com/python/network-graphs/
- [Y14] Dash partial property updates (`Patch`, Dash 2.9): https://dash.plotly.com/partial-properties
- [Y15] ipywidgets_bokeh loader (third-party widget bundles fetched from a CDN): https://github.com/bokeh/ipywidgets_bokeh/blob/main/ipywidgets_bokeh/src/loader.ts

Framework integration
- [D1] dash-component-boilerplate README: https://github.com/plotly/dash-component-boilerplate
- [D2] Dash clientside callbacks, `dash_clientside.set_props` (Dash 2.16): https://dash.plotly.com/clientside-callbacks
- [D3] Dash supported React versions (dev branch): https://github.com/plotly/dash/blob/dev/dash/_dash_renderer.py
- [P1] Panel: compile and bundle ESM components (`panel compile`, esm.sh default, `_bundle`): https://panel.holoviz.org/how_to/custom_components/esm/build.html
- [P2] Panel `AnyWidgetComponent`: https://panel.holoviz.org/reference/custom_components/AnyWidgetComponent.html
- [P3] Panel PR #8428, native `pn.pane.AnyWidget` (open): https://github.com/holoviz/panel/pull/8428

Commercial
- [M1] yFiles pricing: https://www.yfiles.com/pricing
- [M2] Ogma docs: https://doc.linkurious.com/ogma/latest/
- [M3] Cambridge Intelligence (KeyLines/ReGraph) pricing: https://cambridge-intelligence.com/pricing/

Registry metadata (versions, dates, licences, stars, last push): npm registry, PyPI JSON API and GitHub REST API, all queried 2026-10-04.
