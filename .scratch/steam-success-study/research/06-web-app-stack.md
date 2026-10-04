# Research 06: Python web app stack for the Tag Network

Ticket: [../issues/06-web-app-stack.md](../issues/06-web-app-stack.md)
Researched: 2026-10-03. All version, date and licence facts were read live from PyPI JSON (`https://pypi.org/pypi/<pkg>/json`), the npm registry and the GitHub REST API (`https://api.github.com/repos/<owner>/<repo>`) on that date. Nothing was installed or run; Windows behaviour is from docs and issue trackers, not a local smoke test.

## Question

Which local Python-backed web stack best fits the interactive **Tag Network** app (one loaded **Top-100 Dataset**; ~400 Tag nodes, several thousand weighted edges that keep their AppIDs; cluster-centre styling; node/edge inspection; tables; recompute when thresholds, hidden **Genre Tags**, removed nodes, **Minimum Months Filter** or seed change; CSV/JSON export; CSV upload of the pipeline's own export; long-running Louvain/sensitivity runs)?

## Summary

- **Dash 4 + dash-cytoscape + dash-ag-grid** covers every criterion out of the box, and it is the only candidate with built-in **progress + cancellation + result caching** for long callbacks. Its weak link is **dash-cytoscape**, which is in maintenance mode: last release 1.0.2 on 2024-07-15, before Dash 3 and Dash 4. A Dash 4 mount bug was reported in 2026, and the maintainers said they "likely won't be able to get to this soon".
- **Panel (+ Tabulator, + a small `JSComponent` that wraps current Cytoscape.js or sigma.js)** is the strongest alternative. It is very actively released, its tables and downloads are excellent, and it needs no build step. You write about 100 lines of JS for the graph, and cancellation is DIY. HoloViews `Graph` alone falls short on inspection: it highlights *either* nodes *or* edges, not both.
- **Streamlit** is poorly suited. Its ready-made graph components are stale (streamlit-agraph last released 2023-01; pyvis 2023-02, and pyvis embedded via `components.html` is display-only). Its full-script rerun model also fits a click-to-inspect graph badly. Components v2 could fix the graph, but then you are writing a custom component anyway.
- **FastAPI/Flask + JS** gives the best rendering (sigma.js WebGL) and full control. But you must build tables, upload/download, job progress and cancellation, and the reactive wiring yourself, in two languages. That is too much surface for a research tool.
- **Recommendation:** Dash 4 + dash-cytoscape + dash-ag-grid + `DiskcacheManager` background callbacks. Gate the choice with a one-hour Windows spike (see "Gating spike"). If the spike fails, fall back to Panel + Tabulator + a `JSComponent` around Cytoscape.js. Most graph code carries over, because the Cytoscape stylesheet and element JSON are the same in both.

## Comparison matrix

Legend: ✅ built in / first-class · 🟡 possible with moderate custom work or caveats · ❌ not supported / poor fit.

| Criterion | Dash + dash-cytoscape (+ dash-ag-grid) | Panel / HoloViews (+ Tabulator; graph via HoloViews or `JSComponent`) | Streamlit (+ agraph / pyvis) | FastAPI/Flask + JS (sigma.js / Cytoscape.js / vis-network) |
|---|---|---|---|---|
| ~400 nodes / several thousand weighted edges | ✅ Cytoscape.js canvas; follow its perf guide: haystack edges, no edge labels, `min-zoomed-font-size` [C3] | HoloViews/Bokeh 🟡 fine at this size [P1]; `JSComponent` + Cytoscape.js/sigma.js ✅ | agraph = vis-network 🟡 (physics layout; auto-clustering above 100 nodes when `improvedLayout` [J4]) | ✅ sigma.js WebGL, "thousands of nodes and edges" [J1]; Cytoscape.js ✅; vis-network 🟡 |
| Distinct cluster-centre styling | ✅ CSS-like `stylesheet` selectors on data/classes [D5] | ✅ HoloViews `dim()` mappings for node/edge colour/width [P2]; ✅ JS lib styling | 🟡 agraph per-node kwargs (vis-network options) [S6] | ✅ |
| Click nodes **and** edges to inspect | ✅ `tapNodeData`, `tapEdgeData`, `selectedNodeData`, hover variants [D4] | HoloViews 🟡: `selection_policy` / `inspection_policy` ∈ {`nodes`, `edges`, None}, one at a time [P3]; `JSComponent` ✅ via `model.send_event`/`send_msg` [P6] | agraph 🟡 returns the clicked node only (README shows no edge events) [S6]; pyvis ❌ (`components.html` is display-only) [S4] | ✅ sigma `clickNode`/`clickEdge`; edge events off by default, enable with `enableEdgeClickEvents` etc. [J2] |
| Sortable / filterable tables | ✅ dash-ag-grid (community, MIT): sort, column filters, quick filter, CSV export [D7] | ✅ Tabulator: sort, `header_filters`, `.add_filter()`, selection [P4] | 🟡 `st.dataframe`: sort, search, CSV; no per-column filter UI [S2] | 🟡 DIY with Tabulator.js / AG Grid JS |
| Recompute on input change | ✅ explicit callback graph | ✅ `pn.bind` / `param.depends` reactive | 🟡 whole script reruns on every interaction; fragments narrow it [S1] | ❌ DIY (fetch + state management) |
| CSV / JSON downloads | ✅ `dcc.Download` [D8]; AG Grid CSV export | ✅ `FileDownload` [P7]; Tabulator `.download()` / `.download_menu()` CSV/JSON [P4] | ✅ `st.download_button` [S7] | 🟡 DIY endpoints (easy) |
| CSV upload | ✅ `dcc.Upload` (base64 `contents` + `filename`, `max_size`) [D6] | ✅ `FileInput` [P8] | ✅ `st.file_uploader`; `server.maxUploadSize` [S3] | 🟡 DIY (easy) |
| Long runs: progress | ✅ background callbacks `progress=` / `set_progress`, `running=` [D1] | 🟡 `Progress` indicator [P9] + threading (`nthreads`) / async [P5]; wire it yourself | 🟡 `st.progress`; `show_time` spinner on cache miss [S5] | ❌ DIY; FastAPI `BackgroundTasks` is meant for "small background tasks" [F1] |
| Long runs: cancellation | ✅ `cancel=[Input(...)]` [D1] | ❌/🟡 no built-in; cooperative flag in a thread | 🟡 a new interaction interrupts the run (`runner.fastReruns`) [S3]; no explicit cancel API | ❌ DIY |
| Long runs: caching | ✅ `cache_by`, `cache_args_to_ignore`, `expire` on background callbacks [D2] | ✅ `pn.cache` (LRU/LFU/FIFO, `max_items`, `ttl`, `to_disk`) [P10] | ✅ `st.cache_data` (`max_entries`, `ttl`, `persist="disk"`) [S5] | 🟡 DIY (`functools.lru_cache`, diskcache) |
| Maintenance | Dash ✅ 4.4.1 (2026-07-21), 22 releases in 12 mo, major 4.0 on 2026-02-03. **dash-cytoscape 🟡/❌** 1.0.2 (2024-07-15); last commit 2025-08-09; open Dash 4 bug report closed unfixed [D9, D10]. dash-ag-grid ✅ 35.3.0 (2026-07-15) | Panel ✅ 1.9.4 (2026-08-17), 42 releases in 12 mo; HoloViews ✅ 1.23.2 (2026-08-24), 30 releases | Streamlit ✅ 1.65.0 (2026-10-02). **streamlit-agraph ❌** 0.0.45 (2023-01-28); **pyvis ❌** 0.3.2 (2023-02-24), last push 2024-04 | FastAPI ✅ 0.142.2 (2026-09-30); Flask ✅ 3.1.3; sigma 3.0.3 (npm 2026-04-30); cytoscape 3.34.3 (2026-09-07); vis-network 10.1.2 (2026-08-19) |
| Licence | Dash MIT; dash-cytoscape MIT; dash-ag-grid MIT (AG Grid Enterprise features need a commercial key; not needed here) [D7] | Panel BSD-3; HoloViews BSD-3 | Streamlit Apache-2.0; agraph MIT (GitHub); pyvis BSD-3 | FastAPI MIT; Flask BSD-3; sigma MIT; Cytoscape.js MIT; vis-network Apache-2.0 OR MIT |
| Windows install | ✅ pure-Python wheels; `dash[diskcache]` pulls diskcache, multiprocess, psutil (Windows wheel). 🟡 Windows uses process *spawn*, so callback inputs/closures must pickle (see Dash #2827) [D3] | ✅ pure-Python wheels (Panel, Bokeh 3.10, HoloViews); Python ≥3.10 | ✅ Python ≥3.10; pyarrow has Windows wheels | ✅ pure Python; JS via local files or a bundler |
| Offline / no CDN at runtime | ✅ `serve_locally=True` by default; component JS bundled in the wheel [D11] | 🟡 `JSComponent` ESM imports load from a CDN (esm.sh) unless bundled with `npm` + `esbuild` [P11] | ✅ (agraph bundled) | ✅ if vendored |

### Supporting stack notes

- **Clustering library is independent of the UI choice.** networkx 3.7 (pure Python, 2026-09-21) has Louvain with a `seed` argument. igraph 1.0.0 and leidenalg 0.12.0 ship Windows wheels on PyPI. The Louvain implementation choice belongs to the clustering ticket, not this one.
- **diskcache** backs both Dash's `DiskcacheManager` and Panel's `pn.cache(to_disk=True)`. Its last release is 5.6.3 (2023-08-31) and its last repo push was 2024-08-10. It is stable but quiet, which is low risk for a single-user local app.
- **Dash 4 + dash-cytoscape compatibility is unverified.** dash-cytoscape 1.0.2 bundles `react-cytoscapejs` 2.0.0 and React ^18.2 [D10]. Issue #228 (open, 2026-01) asks for a newer Cytoscape.js to fix a rendering bug that was fixed upstream in 3.30.3. Issue #229 reports `bb.h undefined` when Cytoscape is mounted from a callback under Dash 4.1. The maintainer confirmed it "seems to be real bug", and the reporter then closed it without a fix because they could not reproduce it minimally [D9]. Mitigation: render the `Cytoscape` component in the initial layout and update only its `elements`/`stylesheet` properties, rather than returning a new component from a callback.

## Recommendation

Use **Dash 4 + dash-cytoscape + dash-ag-grid**, with `DiskcacheManager` background callbacks for network build, Louvain and sensitivity runs.

Why it fits this study:
1. The heavy, parameterised recompute (dataset, thresholds, hidden genre tags, removed nodes, min months, seed) maps directly onto a background callback. `progress`, a `cancel` button and `cache_by` / argument hashing all come built in [D1, D2], which serves the open "Recompute performance budget" item on the map.
2. Node **and** edge tap events, with full data dictionaries, come out of the box [D4]. The edge's AppIDs can be stored in the edge `data` and shown in an AG Grid.
3. Every other criterion (tables, upload, download, licences, Windows) is first-class, and all licences are permissive.

The only material risk is dash-cytoscape's maintenance status. It is acceptable because the Cytoscape.js stylesheet and elements JSON are portable. If the wrapper breaks, the same graph spec moves into a Panel `JSComponent` that loads a current Cytoscape.js.

### Gating spike (before locking the spec)

On the researcher's Windows machine, in a clean venv with pinned versions:
1. Render about 400 nodes and about 5,000 weighted edges in dash-cytoscape (haystack edges, a cluster-centre class) and check that pan, zoom and tap stay smooth.
2. Click a node and an edge, and confirm that `tapNodeData` and `tapEdgeData` reach a callback.
3. Run a background callback with `progress` and `cancel` on Windows (spawn), passing only picklable inputs.
4. Toggle a threshold 10 times quickly, and confirm there are no #229-style errors under the pinned Dash 4.x.

If step 1, 2 or 4 fails, switch to **Panel + Tabulator + `JSComponent`(Cytoscape.js, bundled via esbuild for offline use)**. Long-run cancellation then becomes a cooperative flag checked between seeds or thresholds.

## Sources

Dash
- [D1] Background callbacks (progress, cancel, running, managers): https://dash.plotly.com/background-callbacks
- [D2] Background callback caching (`cache_by`, `cache_args_to_ignore`, `expire`): https://dash.plotly.com/background-callback-caching
- [D3] Dash issue #2827, Windows spawn pickling error with background callbacks: https://github.com/plotly/dash/issues/2827 ; `dash[diskcache]` extras from https://pypi.org/pypi/dash/json
- [D4] Dash Cytoscape events: https://dash.plotly.com/cytoscape/events
- [D5] Dash Cytoscape overview/styling: https://dash.plotly.com/cytoscape
- [D6] dcc.Upload: https://dash.plotly.com/dash-core-components/upload
- [D7] Dash AG Grid: https://dash.plotly.com/dash-ag-grid
- [D8] dcc.Download: https://dash.plotly.com/dash-core-components/download
- [D9] dash-cytoscape issues #228, #229: https://github.com/plotly/dash-cytoscape/issues/228 , https://github.com/plotly/dash-cytoscape/issues/229
- [D10] dash-cytoscape package.json (bundled deps): https://github.com/plotly/dash-cytoscape/blob/main/package.json ; repo/commits via GitHub API
- [D11] `serve_locally` default True: https://github.com/plotly/dash/blob/dev/dash/dash.py

Panel / HoloViews
- [P1] HoloViews network graphs guide: https://holoviews.org/user_guide/Network_Graphs.html
- [P2] HoloViews Graph (bokeh) reference: https://holoviews.org/reference/elements/bokeh/Graph.html
- [P3] `selection_policy` / `inspection_policy` options in source: https://github.com/holoviz/holoviews/blob/main/holoviews/plotting/bokeh/graphs.py
- [P4] Tabulator widget: https://panel.holoviz.org/reference/widgets/Tabulator.html
- [P5] Concurrency how-to: https://panel.holoviz.org/how_to/concurrency/index.html
- [P6] JSComponent: https://panel.holoviz.org/reference/custom_components/JSComponent.html
- [P7] FileDownload: https://panel.holoviz.org/reference/widgets/FileDownload.html
- [P8] FileInput: https://panel.holoviz.org/reference/widgets/FileInput.html
- [P9] Progress indicator: https://panel.holoviz.org/reference/indicators/Progress.html
- [P10] `pn.cache`: https://panel.holoviz.org/how_to/caching/memoization.html
- [P11] Compile and bundle ESM components: https://github.com/holoviz/panel/blob/main/doc/how_to/custom_components/esm/build.md

Streamlit
- [S1] Fragments / rerun model: https://docs.streamlit.io/develop/concepts/architecture/fragments
- [S2] st.dataframe: https://docs.streamlit.io/develop/api-reference/data/st.dataframe
- [S3] config.toml (`runner.fastReruns`, `server.maxUploadSize`): https://docs.streamlit.io/develop/api-reference/configuration/config.toml ; st.file_uploader: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- [S4] `st.components.v1.html` (display-only): https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html ; components v1 vs v2: https://docs.streamlit.io/develop/concepts/custom-components/overview , https://docs.streamlit.io/develop/concepts/custom-components/components-v2/communicate
- [S5] st.cache_data: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data ; st.progress: https://docs.streamlit.io/develop/api-reference/status/st.progress
- [S6] streamlit-agraph README: https://github.com/ChrisDelClea/streamlit-agraph
- [S7] st.download_button: https://docs.streamlit.io/develop/api-reference/widgets/st.download_button

JS / web frameworks
- [J1] sigma.js docs: https://www.sigmajs.org/docs/
- [J2] sigma.js events: https://www.sigmajs.org/docs/advanced/events
- [C3] Cytoscape.js performance guide: https://github.com/cytoscape/cytoscape.js/blob/master/documentation/md/performance.md ; WebGL preview (3.31, experimental): https://blog.js.cytoscape.org/2025/01/13/webgl-preview/
- [J4] vis-network layout options: https://visjs.github.io/vis-network/docs/network/layout.html
- [F1] FastAPI background tasks caveat: https://fastapi.tiangolo.com/tutorial/background-tasks/

Registry metadata (versions, upload dates, licences, Python requirements): PyPI JSON API, npm registry (`https://registry.npmjs.org/<pkg>`), GitHub REST API repo endpoints, all queried 2026-10-03.
