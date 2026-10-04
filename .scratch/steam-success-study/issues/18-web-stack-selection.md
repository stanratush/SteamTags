# Web stack selection
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 17, 20, 21

## Question

Given the spike results, is the app built on Dash + dash-cytoscape or on the Panel + Tabulator + custom Cytoscape.js fallback? Which versions are pinned? Must the app run fully offline (no CDN assets)? Which app-level constraints go into the spec (e.g. background-job inputs must be picklable: file paths and parameters, not live objects)?

Context: [Python web app stack for the tag network](06-web-app-stack.md), [Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md).

Surfaced by [Tag network app interaction prototype](14-tag-network-app-prototype.md):
- The stack must support two modes over one shared state (Workbench with collapsible inspector/table panels; scrolling Analysis report), switched inside the app, and an on-demand background job (node sensitivity) with progress, cancel and stale-marking. The prototype's Cytoscape.js elements/stylesheet JSON is what the graph component must accept.
- Graph layout modes (Global / Cluster-separated) switch without reclustering; decide whether positions are computed in the browser (Cytoscape.js, as in the prototype) or in Python and sent as a preset layout.

Surfaced by [Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md) (every functional check passed on Dash 4.4.1 + dash-cytoscape 1.0.2):
- Speed at the worst case: a full redraw at 400 nodes / ~5,000 edges takes ~55 ms (~18 fps pan/zoom), and dash-cytoscape exposes no `hideEdgesOnViewport` / `textureOnViewport` / `pixelRatio` props. Is that acceptable, given the shared defaults (8/8) give far smaller graphs? Or is a clientside workaround, or Panel + a current Cytoscape.js (3.31+ has a WebGL renderer), wanted?
- Edge AppID lists inside `elements` make each threshold change ship ~800 KB. Keep AppIDs in edge data, or keep them server-side and fetch them on tap?
- Each background job pays ~4 s of Windows spawn + re-import. That points to keeping the app module's import-time work minimal.
- Run Dash dev tools off (or with `dev_tools_disable_version_check`) to stay fully offline. Reset progress and mark old results stale when a job starts or is cancelled.

Surfaced by [Interactive graph visualization alternatives](20-graph-visualization-alternatives.md):
- Is the worst-case redraw (~55 ms) good enough on dash-cytoscape, perhaps with a `window.cy` tweak? Or should a short spike try Cytoscape.js 3.34 WebGL in our own thin wrapper (sigma.js 3 as the fallback)? If a wrapper, is it a Dash `assets/` clientside module or a custom component?

## Answer

Resolved 2026-10-04 with the researcher, over three rounds. Round 1 was paused for a wider survey, [Alternative app frameworks and graph renderers (Python or JS/TS backend)](21-app-frameworks-and-renderers.md), which found nothing that beats Dash and no JS clustering that matches the Python report.

**Stack**
- v1 is **Dash 4 + dash-cytoscape 1.0.2 + dash-ag-grid**, with `DiskcacheManager` background callbacks.
- A later version may move to the hybrid (FastAPI over the Python `network` package + a Vite/TypeScript front end). That is out of scope for this map. A JS/TS backend is ruled out: no JS clustering reproduces the Python report's clusters.
- The newer Cytoscape.js (3.34, WebGL) behind our own wrapper is a planned upgrade, not v1. Its spike runs only if panning feels slow on the first test Build, with real data at real thresholds. The `window.cy` speed hack is not used.

**Python and pins**
- **Python 3.14** (`requires-python = ">=3.14,<3.15"`; 3.14.8 is the latest stable as of 2026-09-30). This supersedes the 3.12 in [Pipeline architecture and export schema](15-pipeline-architecture.md); one interpreter for the whole `steamstudy` package.
  - Checked on PyPI 2026-10-04: every compiled dependency (numpy, scipy, scikit-learn, pandas, lxml, selectolax, psutil, igraph, leidenalg) has a Windows wheel for 3.14; `multiprocess` 0.70.19 has a `py314` wheel; networkx 3.7 excludes only 3.14.1.
  - The Dash packages declare support only up to 3.12 (stale metadata, not a known break). The pin holds only once [Dash spike re-run on Python 3.14](22-dash-spike-python-314.md) passes; if a check fails, fall back to 3.13 (verified by the original spike) and record why.
- `dash-cytoscape==1.0.2` pinned exactly (unmaintained; its bundled Cytoscape.js 3.28.1 is part of what was tested). Other dependencies use compatible ranges (e.g. `dash>=4.4,<5`, `dash-ag-grid>=35.3,<36`), with exact versions frozen in `uv.lock`.
- Any upgrade of dash, dash-cytoscape or dash-ag-grid re-runs the spike checklist first.

**Network and payload**
- Fully offline: every asset served locally, no CDN, no version-check calls. Dev tools off (`debug=False`); if ever turned on, `dev_tools_disable_version_check=True`.
- Listens only on `127.0.0.1`. A test checks that the served page loads nothing from outside `127.0.0.1`.
- Edge AppID lists stay on the server. The graph payload carries only ids, weights and styling data; an edge's games are looked up on click from the server-side network state. Exports still include the AppID lists.

**Layout**
- Node positions for both layout modes are computed in Python and sent as a `preset` layout.
- Global: weighted, seeded `networkx.spring_layout`, computed once per loaded dataset + Minimum Months Filter at the loosest thresholds, then reused as thresholds change (the graph doesn't jump). A **Re-layout** button re-runs it on the current graph, starting from the current positions.
- The layout uses the clustering seed, so one seed reproduces a whole view.
- Cluster-separated positions are cached per network state, as in [Tag network app interaction prototype](14-tag-network-app-prototype.md).
- x/y for both layout modes are included in the network export.

**Background jobs** (node sensitivity)
- Dash background callbacks with `DiskcacheManager`. Up to ~4 s startup per run (Windows spawn + re-import) is accepted. There is no long-lived worker.
- Threshold changes, layout switches and inspection are normal callbacks.
- Job inputs are plain picklable values (Build path, dataset name, settings, seed), never live objects.
- The app module does nothing at import beyond defining its layout: no data loading, no position computation.
- Starting or cancelling a job clears the progress bar and marks old results stale.
- The job cache lives in the Build folder (`<build>/app_cache/`), never in the Snapshot.

**Code boundary**
- The graph renderer is reached only through one module in `app` that takes nodes, edges, stylesheet and positions, so the renderer (or the whole front end) can be swapped.
