# Dash + dash-cytoscape Windows spike
Type: task
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

Does the recommended stack (Dash 4 + dash-cytoscape 1.0.2 + dash-ag-grid, background callbacks) actually work on the researcher's Windows machine? dash-cytoscape has not been released since July 2024 and has a confirmed, unfixed Dash 4 mount bug. Throwaway spike, in a scratch folder, checking:

- smooth rendering of ~400 nodes / ~5,000 weighted edges with distinct cluster-center styling;
- node and edge click events reaching Python;
- a background callback with progress and cancellation (Windows uses a separate process, so inputs must be picklable);
- rapid threshold toggling without errors or stale renders;
- switching between two sets of preset node positions (Global vs. Cluster-separated layout, plus tinted cluster-region background nodes) by updating `elements`/positions only, without re-mounting the component;
- which Dash 4.x / dash-cytoscape versions were used.

Record pass/fail per check and the versions. If it fails, record the failure mode for the Panel fallback decision.

Context: [Python web app stack for the tag network](06-web-app-stack.md).

## Answer

**Pass, with one soft spot (render speed at the worst-case graph size).** Every functional check passed on the researcher's Windows machine. Nothing hit the dash-cytoscape Dash 4 mount bug (#229). Run on 2026-10-04 with synthetic data only: 400 nodes, 4,964 weighted edges, each edge carrying its AppID list. Spike code: [../prototypes/17-dash-cytoscape-spike/app.py](../prototypes/17-dash-cytoscape-spike/app.py). It regenerates its own data; run it with `--debug` for Dash dev tools.

**Versions:** Python 3.13.0 (Windows 11 Pro 10.0.26200), dash 4.4.1, dash-cytoscape 1.0.2 (bundles Cytoscape.js 3.28.1, so no WebGL renderer), dash-ag-grid 35.3.0, diskcache 5.6.3, multiprocess 0.70.19, psutil 7.2.2, Flask 3.1.3, Werkzeug 3.1.9, plotly 7.1.0, networkx 3.7, numpy 2.5.3, scipy 1.18.1. Browser: the Chromium pane in the Claude desktop app, devicePixelRatio 2.

| Check | Result | Notes |
|---|---|---|
| Render ~400 nodes / ~5,000 edges with cluster-centre styling | **Pass (functional); soft on speed** | Haystack edges with `mapData` width and per-cluster `data(color)`; centres drawn as a ◆ with a border. A forced full redraw takes a median of 55 ms (p95 77 ms), about 18 fps during pan/zoom. Edges are almost all of that cost: nodes only took 10 ms, and turning labels off saved about 7 ms. At 1,359 edges (shared-games threshold 8) the graph is much lighter. dash-cytoscape 1.0.2 does **not** expose `hideEdgesOnViewport`, `textureOnViewport` or `pixelRatio` as props, so the usual Cytoscape.js speed-ups need a clientside hack. |
| Node and edge clicks reach Python | **Pass** | Real mouse clicks. `tapNodeData` and `tapEdgeData` arrived with the full data dict. A 68-AppID edge list was shown in dash-ag-grid. Haystack edges are clickable. |
| Background callback with progress + cancel (Windows spawn) | **Pass** | `DiskcacheManager`, inputs were only ints plus a file path read inside the job. Progress ran 0→40/40 and `running` toggled the buttons. Cancel froze progress and restored the buttons, and no orphaned worker process was left. Each job spends about **4 s starting up** before its first progress update, because spawn re-imports the app module (1.5 s for libraries plus 1 s of module-level layout work in the spike). The old result and progress value stay on screen until something overwrites them. |
| Rapid threshold toggling | **Pass** | 34 rapid slider key steps; 30 interleaved slider and layout toggles at 40 ms gaps; three bursts of 7–11 layout clicks at 25 ms. The final graph always matched the final control state, with no console errors and no dev-tools errors. One mid-burst read showed the previous layout for a few seconds before it caught up: callbacks queue, they are not dropped. |
| Switch Global / Cluster-separated preset positions without re-mounting | **Pass** | Positions are computed in Python (seeded spring layout) and sent in `elements` with `layout={"name": "preset"}`. Node positions changed and the tinted, locked, non-interactive region nodes appeared and disappeared, while the same Cytoscape instance survived every switch. Positions computed once on the full graph were reused across threshold changes, so the graph doesn't jump. |
| Mount from a callback / hide-show (the #229 scenario) | **Pass** | A Cytoscape component returned from a callback (six remounts) rendered with no `bb.h` error. The Workbench was hidden with `display: none` during a mode switch (6 rapid flips). Thresholds and layout were changed while it was hidden, and the graph showed correctly afterwards on the same instance. A graph mounted from a callback with `preset` layout is not fitted to the view unless `fit` is set. |
| Offline / no CDN | **Pass (production mode)** | With `debug=False` every asset came from localhost: 4.1 MB total, of which dash-cytoscape `.min.js` is 484 KB. With `debug=True`, Dash dev tools call `dash-version.plotly.com` to check the version. |

**Facts for the stack decision ([Web stack selection](18-web-stack-selection.md)):**
- Each `elements` update sends the whole element list. With AppID lists inside edge data it was **~800 KB per threshold change** at 4,964 edges. Server-side build and cluster took 46–305 ms per change.
- Each background job costs about 4 s of spawn and re-import on Windows. Module-level work in the app module runs again in every job process.
- The only console warning was dash-cytoscape's built-in "custom wheel sensitivity" warning, which does no harm.
- Not tested: hand-feel of panning in the researcher's everyday browser; `cache_by` memoisation; dash-ag-grid with thousands of rows.
