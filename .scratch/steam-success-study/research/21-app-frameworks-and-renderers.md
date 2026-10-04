# Research 21: Alternative app frameworks and graph renderers (Python or JS/TS backend)

Ticket: [../issues/21-app-frameworks-and-renderers.md](../issues/21-app-frameworks-and-renderers.md)
Researched: 2026-10-04. Versions, release dates, licences and release counts were read live on that date from PyPI JSON (`https://pypi.org/pypi/<pkg>/json`), the npm registry (`https://registry.npmjs.org/<pkg>`, plus its search endpoint), the GitHub REST API (repo metadata, until the unauthenticated rate limit was hit) and raw source files on `raw.githubusercontent.com`. Pyodide package versions come from the published `pyodide-lock.json`, and its file sizes are byte counts of the downloaded files. Feature claims come from official docs, READMEs and source files. Nothing was installed or benchmarked. Anything marked *(inferred)* or *(unverified)* was not confirmed in a primary source. "12 mo" counts releases published since 2025-10-04.

This note builds on, and does not repeat:
- [06](06-web-app-stack.md): the first framework comparison (Dash, Panel/HoloViews, Streamlit, FastAPI/Flask + JS);
- [20](20-graph-visualization-alternatives.md): the renderer matrix. Cytoscape.js 3.34 WebGL is first, sigma.js 3 second, G6 5 third. dash-cytoscape cannot turn on WebGL;
- [05](05-graph-clustering-methods.md): Louvain vs Leiden, seeding, silhouette and centres in Python;
- the [17 spike](../issues/17-dash-cytoscape-windows-spike.md): Dash 4.4.1 + dash-cytoscape 1.0.2 passed every functional check. A full redraw at 400 nodes / 4,964 edges takes a median of 55 ms. Each background job pays ~4 s of Windows spawn;
- the [14 prototype](../issues/14-tag-network-app-prototype.md) Answer and addendum (the app behaviour).

Every stack below is assessed against three decisions already settled in [18](../issues/18-web-stack-selection.md):
1. **Offline + `127.0.0.1`**: all assets are bundled locally, with no CDN and no telemetry or version-check calls.
2. **AppIDs server-side**: the graph payload carries only ids and weights, and an edge's games are fetched on click.
3. **Backend positions**: positions for both layouts (Global, Cluster-separated) are computed in the backend and sent as preset positions.

It is also assessed against the shared-code rule. [15](../issues/15-pipeline-architecture.md) says `network` is a Python subpackage with a pure `build_network(...)` that both the app and the feature-analysis report call. [13](../issues/13-feature-analysis-definitions.md) says the report's Clusters row runs "the Tag Network's own clustering code".

## Question

Which application frameworks, together with which graph renderers, could build the **Tag Network** app if the backend may be **Python or JavaScript/TypeScript**, and how do they compare with the Dash + dash-cytoscape baseline that passed the [17 spike](../issues/17-dash-cytoscape-windows-spike.md)?

The app (from [14](../issues/14-tag-network-app-prototype.md)):
- It is local, single-user and runs on Windows. It loads one Top-100 CSV.
- The Tag Network has ~40–400 nodes and up to ~5,000 weighted edges.
- It re-clusters (Louvain or Leiden, fixed seed) on every filter change, and shows quality metrics (modularity, Jaccard silhouette) and centres.
- Clicking a node or an edge opens the inspector.
- Workbench and Analysis Report mode share one state.
- Global and Cluster-separated preset layouts, with tinted cluster regions.
- Sortable/filterable tables and CSV/JSON exports.
- An on-demand node-sensitivity job with progress, cancel and stale-marking.
- The Python feature-analysis report must produce the same clusters as the app.

## Summary

- **No framework changes the renderer choice.** Every stack can host Cytoscape.js 3.34 (WebGL), sigma.js 3 or G6 5 behind a thin wrapper, and the [20](20-graph-visualization-alternatives.md) ranking holds everywhere. A JS front end only removes the "events must reach Python" bridge.
- **A JS/TS backend is the expensive option, and it breaks the shared-code rule.**
  - JS has a solid seedable Louvain: `graphology-communities-louvain` 2.0.2, whose `rng` defaults to `Math.random` [GL1].
  - JS has no mature Leiden. graphology's own Leiden module is `private`, at 0.0.1, with a "TODO" README [GL2]. Its third-party repackaging defaults to **`weighted: false`** [GL4]. `ngraph.leiden` 0.3.0 and `leiden-ts` 0.1.0 are young [NL1, LT1].
  - No JS implementation reproduces NetworkX partitions from the same seed. Different algorithms and PRNGs mean parity could only be approximate (Q/ARI tolerances). That fails 13's "the Tag Network's own clustering code".
- **Python in the browser does not rescue it.** Pyodide 314.0.7 ships networkx **3.6.1**, where `leiden_communities` still needs a backend, and it has no leidenalg [PY1, NX1]. You would also have to vendor a ~12 MB runtime [PY2].
- **Python frameworks re-checked:**
  - **NiceGUI 3.17** and **Shiny 1.8** are the most credible Python alternatives to Dash.
    - Both take custom JS as plain local files with no build step [NG3, SH2].
    - NiceGUI bundles AG Grid and keeps **one process pool for the app's lifetime** [NG4], which avoids Dash's ~4 s per-job spawn (17).
    - But NiceGUI binds **`0.0.0.0` by default** [NG2], and in both progress and cancel are DIY. Shiny's `ExtendedTask` cancel stops the asyncio task, not the work running in an executor [SH1].
  - **Solara** proxies front-end assets through a CDN by default [SO2].
  - **Streamlit** and **Gradio** send usage statistics by default [ST1, GR1].
  - **Reflex** installs Bun on Windows via `powershell irm … | iex` and npm packages at init, and puts AG Grid in a proprietary package [RX4, RX5].
- **The hybrid (Vite SPA + FastAPI with the Python `network` package) is the only JS-flavoured option that keeps exact parity.** It gives full UI freedom, but costs uv + Node at development time and the most glue code. Node 22.14 is already installed on the researcher's machine.
- **Ranked shortlist:**
  1. **Dash 4 (keep).** Graph as a leaf: dash-cytoscape now, a Cytoscape.js 3.34 WebGL `assets/` module if a spike justifies it.
  2. **Hybrid C1: FastAPI + Vite/TS SPA.**
  3. **NiceGUI 3 (or Shiny 1.8).**
- **Recommendation for the Web stack selection grilling:** keep Dash and the Python-backed app with shared `network` code. Nothing found here challenges those decisions on facts. The one new lever is the per-job spawn: accept ~4 s per on-demand sensitivity run, or own a long-lived worker. If the researcher wants a TS front end, take the hybrid, never a JS backend.

## Comparison matrices

Legend: ✅ built in / first-class · 🟡 possible with moderate custom work or caveats · ❌ not supported / poor fit. "Graph" always means hosting a JS renderer from [20](20-graph-visualization-alternatives.md). No Python framework ships a maintained graph component that has Cytoscape.js ≥ 3.31 (WebGL) and node + edge events, so every stack needs a thin wrapper, or dash-cytoscape's canvas-only 3.28.1.

### A. Python stacks (the `network` subpackage is imported directly, so clustering parity is automatic)

| Criterion | **Dash 4** (baseline) | **Panel 1.9** | **Shiny for Python 1.8** | **NiceGUI 3.17** | **Solara 1.64** |
|---|---|---|---|---|---|
| Latest / licence / cadence | 4.4.1, 2026-07-21, MIT, 22 rel./12 mo; dash-cytoscape 1.0.2, 2024-07-15, 0 rel./12 mo [R] | 1.9.4, 2026-08-17, BSD-3, 42 rel./12 mo [R] | 1.8.0, 2026-09-13, MIT, 8 rel./12 mo [R] | 3.17.1, 2026-09-18, MIT, 28 rel./12 mo; 16k stars, 66 open issues [R] | 1.64.0, 2026-10-02, MIT, 29 rel./12 mo [R] |
| Hosting Cytoscape.js 3.34 WebGL (or sigma) | 🟡 vendored file in `assets/` + clientside callback + `dash_clientside.set_props` (20); or ✅ dash-cytoscape as is (canvas 3.28.1, proven in 17) | 🟡 `JSComponent` / `AnyWidgetComponent`. ESM imports come from esm.sh unless bundled with `panel compile` (npm + esbuild) (20 [P1]) | ✅ no build: `HTMLDependency` serves local JS files [SH2]; JS → Python via `Shiny.setInputValue(id, value, {priority: "event"})`; Python → JS via `session.send_custom_message` + `Shiny.addCustomMessageHandler` [SH3, SH4] | ✅ no build: `ui.element` subclass with `component='x.js'` (Vue), `dependencies=[local files]` and `esm={...}` [NG3]; also has `ui.anywidget` [NG5] | 🟡 ipywidgets / anywidget / ipyreact; front-end assets go through a CDN proxy by default (see offline row) [SO2] |
| Node **and** edge clicks to Python | ✅ dash-cytoscape `tapNodeData`/`tapEdgeData` (17); or `set_props` from own JS | ✅ `model.send_event` / `send_msg` (06) | ✅ `setInputValue` with `priority: "event"` | ✅ `$emit` → `.on(...)` handler *(inferred from the Vue element pattern)* | 🟡 widget traits / callbacks |
| Update without re-mount (positions, layout switch) | ✅ proven in 17 | ✅ parameter change → `model.on('change:...')` | ✅ custom message → JS calls `cy.json()` *(inferred)* | ✅ `run_method` / props update *(inferred)* | 🟡 *(unverified)* |
| Tables (sort, column filter) | ✅ dash-ag-grid 35.3.0 (AG Grid Community, MIT) | ✅ Tabulator: `header_filters`, `.download()` CSV/JSON (06) | 🟡 `render.DataGrid(filters=True)`, `selection_mode`; no built-in export [SH5] | ✅ `ui.aggrid` (AG Grid bundled) and `ui.table` (Quasar) [NG5] | 🟡 `DataFrame` component (basic) *(unverified)* |
| CSV/JSON download | ✅ `dcc.Download` | ✅ `FileDownload` | ✅ `@render.download` *(inferred from API name)* | ✅ `ui.download` [NG5] | ✅ `FileDownload` *(unverified)* |
| Two modes over one shared state | ✅ proven in 17 (hide/show, 6 rapid flips) | ✅ tabs/templates over `param` state | ✅ `navset_*` over reactive values *(inferred)* | ✅ tabs or `ui.sub_pages` over a state object *(inferred)* | ✅ reactive variables |
| Sensitivity job: progress / cancel | ✅ background callbacks `progress`/`cancel`/`running`. ❌ **~4 s spawn + re-import per job on Windows** (17) | 🟡 thread + `Progress` indicator; cancel is a DIY flag (06) | 🟡 `ExtendedTask` with `.cancel()`, which cancels the asyncio task [SH1]. Docs: `ProcessPoolExecutor` for CPU-bound work, threads are limited by the GIL [SH1]. No built-in progress for `ExtendedTask` [SH1]. A job already running in an executor keeps running after `cancel()` *(inferred)*, so you need a cooperative flag | 🟡 `run.cpu_bound` uses **one `ProcessPoolExecutor` created at startup** [NG4]: no per-job spawn after the first *(inferred from the executor reusing workers)*. Arguments must pickle [NG1]. Progress and cancel are DIY (Queue/Event) | ✅ `solara.lab.task`: a thread with a writable `.progress`, `.cancel()` and `is_current()` [SO1]. Threads are bound by the GIL *(inferred)* |
| Offline + `127.0.0.1` | ✅ default host `127.0.0.1` [DA1]; offline with `debug=False` (17) | 🟡 Bokeh server binds all interfaces when `address` is unset *(inferred from Tornado `bind_sockets(address=None)` [PA1])*, so pass `--address 127.0.0.1`; ESM wrapper must be compiled or vendored | ✅ `run_app(host='127.0.0.1')` default [SH6]; dependencies served locally [SH2] | 🟡 **default host `0.0.0.0`** unless `native=True` [NG2]. Must set `host='127.0.0.1'`. Assets local *(inferred: only "On Air" loads a CDN [NG2])* | 🟡 binds localhost [SO2], but the **CDN proxy is on by default** [SO2, SO3]. Offline needs the `solara-assets` package, whose 1.58.2 lags solara 1.64.0 [R] |
| Windows toolchains | uv only (assets wrapper); uv + Node only for a compiled Dash component | uv; + Node for `panel compile` | uv only | uv only. `native=True` (pywebview) is optional | uv only |
| Custom code beyond the `network` package *(estimate)* | lowest: proven skeleton in 17; +150–250 JS lines for a WebGL wrapper (20) | moderate: ~150–250 JS lines + `param` wiring | moderate: ~150–250 JS lines + one input/output binding | moderate: ~150–250 JS lines (Vue wrapper) | moderate–high |

| Criterion | **Streamlit 1.65** (recheck) | **Gradio 6.29** | **Reflex 0.9** | **FastAPI / Litestar + HTMX (+ vanilla-JS graph island)** |
|---|---|---|---|---|
| Latest / licence / cadence | 1.65.0, 2026-10-02, Apache-2.0, 21 rel./12 mo [R] | 6.29.1, 2026-10-02, Apache-2.0, 46 rel./12 mo [R] | 0.9.12, 2026-09-22, Apache-2.0, 91 rel./12 mo [R] | FastAPI 0.142.2 (2026-09-30, MIT); Litestar 2.24.0 (2026-06-11, MIT); htmx.org 2.0.11 `latest`, with **4.0.0 published 2026-08-28 under the `next` tag**, 0BSD [R, HX1] |
| Hosting the renderer | 🟡 Components v2: `st.components.v2.component(name, html, css, js)`, JS → Python via `setStateValue`/`setTriggerValue` and `on_<trigger>_change` callbacks [ST2] | 🟡 `gr.HTML(html_template, js_on_load)`, JS `trigger('event', data)` → Python listener; `watch` for backend prop changes [GR2] | 🟡 wraps **React** components only: `library="pkg@version"`, `tag`, `rx.EventHandler` [RX2]. Non-React libs are "very hard to wrap" [RX2]. `react-cytoscapejs` 2.0.0 (2022) has no `renderer` option (20 [C9]), so you write your own React wrapper | ✅ plain `<script>` of a vendored file; JS calls `fetch` for edge games |
| Node + edge clicks | 🟡 trigger values | 🟡 trigger events | ✅ via own wrapper | ✅ own code |
| Interaction model | ❌ whole-script rerun on interaction (06); fragments narrow it | 🟡 event → function → outputs; aimed at ML demos | ✅ State class + event handlers | ✅ explicit endpoints; HTMX swaps HTML fragments |
| Tables | 🟡 `st.dataframe` (sort/search, no column filters) (06) | 🟡 `gr.Dataframe` *(unverified filter UI)* | ❌/🟡 AG Grid only in **`reflex-enterprise`**, licence "LicenseRef-Proprietary" [RX5] | 🟡 vendored Tabulator 6.6.1 or AG Grid Community 36.2.0 (MIT) [R] |
| Sensitivity job | ❌ no job model; `st.progress` + reruns | ✅ queue with `gr.Progress` [GR3]; cancel via `cancels=` *(unverified for running sync functions)* | 🟡 `@rx.event(background=True)` runs as an async task in the same process, "not a durable job queue" [RX3]; CPU-bound work must be offloaded *(inferred)* | 🟡 DIY: a `ProcessPoolExecutor` started at app start (or a thread) + SSE (`sse-starlette` 3.5.0) or polling; a cancel flag or `Process.terminate()` *(design)* |
| Offline + `127.0.0.1` | 🟡 `browser.gatherUsageStats` **defaults to true**; `server.address` unset by default [ST1]. Set both | 🟡 `GRADIO_SERVER_NAME` defaults to `127.0.0.1`, but **`GRADIO_ANALYTICS_ENABLED` defaults to True** [GR1]; web fonts *(unverified)* | ❌ on Windows `install_bun()` runs `powershell -c "irm <bun install url> \| iex"` [RX4], and front-end packages are installed from the npm registry at init/compile *(inferred from [RX2, RX4])*. Docs recommend WSL on Windows [RX1] | ✅ uvicorn default host `127.0.0.1` [UV1]; everything vendored |
| Windows toolchains | uv only | uv only | uv + Bun (auto-installed) or Node (`REFLEX_USE_NPM`) [RX4] | uv only (no build step) |
| Fit | ❌ rerun model vs click-to-inspect (06 still holds) | ❌ demo framework; two modes and a workbench layout fight its block model *(inferred)* | ❌ two toolchains, internet at install, paid grid | 🟡 full control, but you write routing, state and job API yourself (06) |

**Other Python options noted, not assessed in depth:** Flet 1.0.3 (Flutter UI, Apache-2.0) has no web graph renderer to host Cytoscape.js *(inferred)*. marimo 0.25.1 is a notebook-first app runner that hosts anywidgets. anywidget 0.11.0 (MIT) matters because one anywidget ESM wrapper runs in Panel (`AnyWidgetComponent`, 20 [P2]), NiceGUI (`ui.anywidget` [NG5]), Solara, marimo and Jupyter *(inferred)*. Writing the Cytoscape wrapper as an anywidget would keep the renderer portable across these Python frameworks. Dash does not host anywidgets *(inferred)*.

### B. JS/TS stacks (a JS/TS backend replaces the Python `network` code; see "Graph computation if the backend is JS/TS")

Runtimes, read 2026-10-04:
- Node: 24.21.0 "Krypton" is Active LTS and 22.23.3 "Jod" is Maintenance LTS [ND1]. The researcher's machine already has **Node v22.14.0** on `PATH` (observed with `node --version`; not on the current 22.x patch).
- Bun 1.4.2 (2026-09-05) [R].
- Deno 2.9.7 (2026-09-17) [R].

| Criterion | **Vite 8 SPA (React 19 / Svelte 5 / Vue 3.5) + Node API (Hono 4 / Fastify 5 / Express 5)** | **SvelteKit 3 / Next.js 16 (full-stack, Node adapter)** | **Electron 44 / Tauri 2 shell** (around either) | **Observable Framework 1.13** |
|---|---|---|---|---|
| Latest / licence | Vite 8.3.2 (2026-10-01), React 19.3.0, Svelte 5.57.1, Vue 3.5.43; Hono 4.13.13 (2026-10-04) + `@hono/node-server` 2.1.3; Fastify 5.12.5; Express 5.2.1 (2025-12-01). All MIT [R] | SvelteKit **3.0.0, released 2026-10-01** (three days old; 2.x ended at 2.70.3); Next 16.3.8 (2026-09-30). MIT [R] | Electron 44.5.1 (MIT); Tauri CLI 2.12.1 (Apache-2.0 OR MIT), 3.0 in alpha [R] | 1.13.4, 2026-03-02, ISC; **1 release in 12 mo**, last push 2026-05-15 [R] |
| Renderer fit | ✅ best of all stacks. Cytoscape.js / sigma / G6 used directly, with no Python bridge. `@react-sigma/core` 5.0.6 and Reagraph 4.32 (React-only, 20) become options. Node + edge clicks are plain JS handlers | ✅ same as the SPA (client components) | ✅ same | 🟡 JS in Markdown pages; renderer import is fine |
| Clustering location | Node API (TS) or browser Web Worker. **Not the Python `network` package** | same | same; or a Python sidecar (Tauri "Embedding External Binaries" [TA1]) | ❌ data loaders run **at build time** to "precompute static snapshots" [OF1]. Re-clustering on every filter change must then run in browser JS |
| Tables | ✅ AG Grid Community 36.2.0 (MIT), TanStack Table 9.2.5 (headless; **v9.0.0 only on 2026-08-04**), Tabulator 6.6.1 (MIT) [R] | ✅ same | ✅ same | 🟡 `Inputs.table` *(unverified for column filters)* |
| CSV/JSON download | ✅ Blob + `<a download>` in the browser, or an API endpoint | ✅ | ✅ native save dialogs | ✅ |
| Two modes over one shared state | ✅ client store (e.g. Zustand 5.0.15 / Svelte stores) + router | ✅ | ✅ | 🟡 multi-page site; shared state across pages is DIY |
| Sensitivity job | ✅ `worker_threads` (Node) or a Web Worker (browser): progress via `postMessage`, **hard cancel via `worker.terminate()`** [WK1, WK2], with no per-job import cost beyond the worker script *(inferred)*. Pools: piscina 5.3.2, workerpool 10.0.3 [R] | ✅ same | ✅ same | ✅ Web Worker |
| Offline + `127.0.0.1` | ✅ the built `dist/` is static; the API binds where told (`127.0.0.1`) | ✅ | ✅ no server at all for Electron IPC / Tauri commands | ✅ static build |
| Windows toolchains | Node (or Bun/Deno) + npm. The Python Build still needs uv, so **uv + Node** | uv + Node | + Electron: ~100+ MB Chromium per app *(inferred)*. Tauri: **Rust (rustup, MSVC) + MS C++ Build Tools + WebView2** [TA1] | uv + Node |
| Shared `network` code | ❌ re-implemented in TS; parity with the Python report only by test (see below) | ❌ same | 🟡 with a Python sidecar this becomes the hybrid (C) | ❌ |
| Custom code *(estimate)* | high: state, API, job runner, all `network` logic in TS (graph build, Louvain/Leiden wiring, Jaccard silhouette, centres, both layouts incl. cluster packing), plus parity tests | higher: SSR/routing machinery that a local single-user tool doesn't need *(inferred)* | highest | high, and it fights the build-time model |

### C. Hybrid: TS front end + Python compute

| Criterion | **C1. Vite + React/Svelte SPA ⇄ FastAPI/Litestar (Python `network`)** | **C2. FastAPI + HTMX + vanilla-JS graph module (no build)** | **C3. TS SPA + Pyodide in a Web Worker (no Python server)** | **C4. JS backend → Python subprocess for clustering** |
|---|---|---|---|---|
| Shared `network` code | ✅ imported directly; exact parity | ✅ exact parity | 🟡 same source, different runtime. Pyodide 314.0.7 ships **Python 3.14.2 + networkx 3.6.1**, and in 3.6.1 **`leiden_communities` is "backend required"** (`implemented_by_nx=False`) [PY1, NX1]. 3.7's pure-Python Leiden would have to be loaded as a wheel via micropip *(unverified)*. `igraph` 1.0.0 is in Pyodide, `leidenalg` is not [PY1] | ✅ exact parity, but two runtimes and an IPC protocol |
| Renderer fit | ✅ as B | ✅ Cytoscape.js loaded as a local ESM file; `fetch` for edge games | ✅ as B | ✅ as B |
| Tables / downloads | ✅ as B | 🟡 Tabulator/AG Grid vendored as UMD files; server-rendered tables via HTMX | ✅ as B | ✅ as B |
| Sensitivity job | 🟡 Python side as in A (FastAPI row): a pool started at app start avoids the per-job spawn *(design)*; SSE or polling for progress | 🟡 same; `hx-ext="sse"` or polling | ✅ Web Worker + `terminate()`, but networkx in WASM is slower than native *(inferred)* | 🟡 kill the subprocess = hard cancel |
| Offline | ✅ `dist/` served by `StaticFiles` | ✅ | 🟡 must vendor the Pyodide runtime: **~12.1 MB** (`pyodide.asm.wasm` 9.6 MB + `python_stdlib.zip` 2.5 MB) + networkx 1.1 MB + numpy 3.0 MB (+ scipy 14.0 MB if sklearn-style silhouette is used) [PY2] | ✅ |
| Windows toolchains | **uv + Node at dev time**. At run time uv only if `dist/` is committed or built into the package *(inferred)* | **uv only** | Node at dev time; uv still needed for the Build | uv + Node at run time |
| Custom code *(estimate)* | high: a REST/WS contract + a front-end state store + a job API. The renderer wrapper itself is trivial | moderate: no front-end build, but hand-written JS for the graph, tables and mode switch | high + Pyodide loading/packaging | highest; no benefit over C1 |

## Graph computation if the backend is JS/TS

### Algorithm availability (npm, read 2026-10-04)

| Need (from 05/10/11/14) | JS package | State | Seeding / determinism | Python counterpart today |
|---|---|---|---|---|
| Louvain | `graphology-communities-louvain` 2.0.2 (2024-12-17, MIT, 0 releases in 12 mo; widely used) [R, GL1] | ✅ stable | `rng` option, **default `Math.random`**; `randomWalk` default `true`; `resolution`; `getEdgeWeight` default `'weight'` [GL1]. It is deterministic only if you pass a seeded PRNG, and the README itself points to `seedrandom` (3.0.5, last release 2019) [GL1, R] | `networkx.community.louvain_communities(seed=)` (05) |
| Leiden (05 recommends it) | upstream `graphology` repo: `src/communities-leiden` has **`"private": true`, version 0.0.1, README usage "TODO"**, and it is not on npm (404) [GL2] | ❌ unpublished | — | networkx 3.7 `leiden_communities` (pure Python), leidenalg 0.12.0, igraph 1.0.0 (05) |
| | `@aflsolutions/graphology-communities-leiden` 1.1.1 (2026-04-26, MIT): a third-party repackaging of that upstream code plus a `maxIterations` cap [GL4] | 🟡 a fork of unreleased code | `rng` default `Math.random`; **`weighted` defaults to `false`**, so edge weights are ignored unless you set it [GL4] | |
| | `ngraph.leiden` 0.3.0 (2026-06-02, MIT, by the ngraph author; on `ngraph.graph`) [R, NL1] | 🟡 young (0.x, one release in 12 mo) | `randomSeed` **default 42**; README: "repeated runs with the same seed and inputs are deterministic"; `quality: 'modularity'` default, CPM optional [NL1] | |
| | `leiden-ts` 0.1.0 (2026-04-26, MIT, single release) [R, LT1] | 🟡 brand new | `seed`, xoshiro128** PRNG, documented tie-breaking; quality is gated only as `Q_ours ≥ Q_graspologic − 0.05` [LT1] | |
| | `fast-leiden` 1.1.0: native binding to igraph/leidenalg, **GPL-3.0-or-later**, native addon [R] | ❌ native build on Windows *(inferred)* | | |
| Modularity, weighted degree, betweenness, closeness, eigenvector, PageRank, HITS, density | `graphology-metrics` 2.4.2 (2026-09-02, MIT) [R, GL3] | ✅ | deterministic | networkx |
| Jaccard silhouette (05/10), Jaccard medoid centre (05/11) | none maintained (`@robzzson/silhouette` 0.0.7, 2020) [R] | 🟡 DIY, small: ≤ 400 tags → ≤ 80k Jaccard pairs *(estimate)* | deterministic | sklearn `silhouette_score(metric='precomputed')` (05) |
| Layouts (Global, Cluster-separated) | `graphology-layout-forceatlas2` 0.10.1 (2022), `d3-force` 3.0.0 (2021) [R] | 🟡 stable but dormant; cluster packing is DIY in any language | seedable via initial positions *(inferred)* | networkx `spring_layout(seed=)` (17) |

### Parity with the Python feature-analysis report

- **Two implementations cannot be expected to give the same partition from the same seed.**
  - NetworkX's Louvain shuffles node order with Python's seeded `random` (05 [NX-LV]).
  - graphology uses whatever `rng` it is given, with its own traversal and queue [GL1].
  - ngraph.leiden and leiden-ts use their own PRNGs [NL1, LT1].

  No source claims partition equality across implementations. Even leiden-ts, which is built for parity, only gates on modularity within 0.05 of graspologic [LT1]. Same seed number ≠ same clusters *(inferred from the above)*. 05 already found that within Python, the seed alone is not enough: insertion order and library versions matter as well.
- **Ways to keep "the report produces the same clusters as the app" (13, 15):**
  1. **Python-only clustering (current decision).** It is exact by construction. Any Python stack (A), C1 and C2 keep it.
  2. **One implementation, called from both sides.**
     - JS clustering, with the Python Build shelling out to `node`: the Build gains a Node runtime dependency, and `network` is no longer a Python subpackage.
     - Python clustering, with a JS app calling Python: this is C1/C4, so it is the hybrid.
  3. **Parity test suite** (golden partitions from Python fixtures). Exact equality would need a line-for-line port of the NetworkX algorithm *and* of CPython's Mersenne Twister / `random.shuffle` behaviour *(inferred)*, which is fragile across library upgrades. Tolerance tests (Q within ε, ARI ≥ x) would not meet 13's "the Tag Network's own clustering code".
  4. **Python in the browser (Pyodide 314.0.7).** The same source runs, but in a different runtime:
     - networkx 3.6.1 in Pyodide vs 3.7 natively (version drift);
     - in 3.6.1 Leiden needs a backend [NX1];
     - leidenalg is missing;
     - a ~12 MB runtime has to be vendored [PY1, PY2].

     It also removes nothing: the Build still needs native Python.
- **Speed is not a reason to move to JS.** 05 measured a full NetworkX removal sweep at ~74 s for ~350 nodes. The compiled options already exist in Python: igraph 1.0.0 / leidenalg 0.12.0, which have Windows wheels (05) and are **GPL** (fine for a local research tool that isn't distributed *(inferred)*). The JS implementations' speed was not measured here.
- Version note for pins (18 Q5): **networkx 3.7 requires Python `>=3.12, !=3.14.1`** [R]. 15 says Python 3.12; the 17 spike ran on 3.13.0. Both are compatible.

## Background work (node sensitivity: n reclusterings, progress, cancel, stale-marking)

| Model | Used by | Per-job start cost | Progress | Cancel |
|---|---|---|---|---|
| New process per job (Dash `DiskcacheManager`, Windows spawn) | Dash background callbacks | **~4 s measured** (17): spawn + re-import of the app module | ✅ built in | ✅ built in (terminates the job) |
| Long-lived process pool started with the app | NiceGUI `run.cpu_bound` [NG4]; DIY in FastAPI/Shiny (`ProcessPoolExecutor` [SH1]); possible in Dash with own code + `dcc.Interval` polling *(design)* | paid once per worker, then ≈ 0 *(inferred)* | DIY (Manager queue / shared value) | 🟡 cooperative flag. A running `concurrent.futures` task cannot be killed; for a hard stop, own a `multiprocessing.Process` and `terminate()` it |
| Thread in the server process | Solara `task` [SO1], Panel threads (06), Shiny `ExtendedTask` + thread | ≈ 0 | ✅ Solara `.progress`; others DIY | 🟡 cooperative (`is_current()`, flag). The GIL slows the UI during pure-Python networkx work *(inferred)* |
| Worker thread / Web Worker | all JS/TS stacks (B), C3 | ms *(inferred)* | ✅ `postMessage` | ✅ hard `terminate()` [WK1, WK2] |

**Stale-marking is application logic in every stack.** Store the settings hash (dataset, thresholds, hidden/removed tags, seed, algorithm) with each sensitivity result, and mark the result stale when the current hash differs (17 noted that Dash leaves the old result on screen). No framework provides this. The ~4 s Dash cost is specific to `DiskcacheManager`'s per-job spawn on Windows. Dash can avoid it by running the job in a thread or pool it owns and polling progress, at the cost of rebuilding what background callbacks give for free.

## Renderer fit per stack (updates to 20 only)

- **The 20 ranking holds in every stack.** Cytoscape.js 3.34 WebGL comes first, because it reuses the 17 stylesheet, elements and tap semantics. sigma.js 3 is the fallback if WebGL Cytoscape is slow on the researcher's GPU, and G6 5 is the option if built-in hulls/bubble-sets matter most.
- **What framework fit changes:**
  - **JS/TS stacks (B, C1, C3).** The "events must reach Python" constraint disappears, so sigma, G6 and Reagraph need no Python bridge. React wrappers (`@react-sigma/core` 5.0.6, Reagraph 4.32) become usable. This lowers sigma's integration cost but not its v3 gap (no bordered diamond until v4, 20).
  - **Shiny and NiceGUI.** Both take a vendored JS file with no build step (`HTMLDependency` [SH2]; `component=`/`dependencies=` [NG3]), the same effort as Dash's `assets/` route.
  - **Panel.** The ESM route needs `panel compile` (Node) or hand-vendoring for offline use (20 [P1]).
  - **Reflex.** Only React components can be wrapped, and `react-cytoscapejs` 2.0.0 cannot enable WebGL (20 [C9]), so you write your own React wrapper anyway.
  - **anywidget.** One anywidget ESM wrapper would serve Panel, NiceGUI, Solara and marimo *(inferred)*, but not Dash.
- **Settled decisions in every stack.**
  - With AppIDs server-side (18 Q3), the element payload shrinks from the ~800 KB measured in 17 to ids + weights + cluster. That is roughly 5k × (id, source, target, weight, cluster) ≈ a few hundred KB of JSON at the worst case *(estimate)*.
  - Backend positions (18 Q4) mean that a JS backend would also need its own layout code (ForceAtlas2/d3-force, plus Cluster-separated packing). A Python backend keeps the seeded `spring_layout` from 17.
  - Offline (18 Q2): vendor the renderer file. In 20, every shortlisted renderer is an npm package with no runtime CDN use.

## Ranked shortlist

1. **Dash 4 + dash-ag-grid, graph as a replaceable leaf (baseline, keep).**
   - It is the only stack proven on the researcher's machine (17).
   - It needs uv only, keeps `network` in Python, and is offline and `127.0.0.1` by default ([DA1], 17).
   - Renderer: dash-cytoscape 1.0.2 as it is now. Move to a ~150–250-line Cytoscape.js 3.34 WebGL module in `assets/` only if a short spike shows the gain (20).
   - The one weak spot this survey adds: **the ~4 s per-job Windows spawn is a property of `DiskcacheManager`**, not of the work. Other stacks avoid it with a pool or thread that lives with the app. Within Dash, you either accept it (sensitivity is on demand) or own a worker and poll progress.
2. **Hybrid C1: FastAPI (or Litestar) serving a Vite + Svelte/React SPA, with the Python `network` package behind a small JSON API.**
   - This is the choice if the researcher wants a JS-native UI: every renderer and table is first-class, with no Python bridge.
   - Parity stays exact, and Web Worker-style hard cancel is replaced by a Python pool.
   - Costs: **uv + Node** at development time (Node 22.14 is already installed), and the most glue code (API contract, client store, job endpoints).
   - Its no-build variant is **C2: FastAPI + HTMX + vanilla JS** (uv only), but hand-written tables and state make it less attractive than C1 or Dash *(inferred)*.
3. **NiceGUI 3.17 (alternatively Shiny 1.8): the Python-only alternative to Dash.**
   - Custom JS needs no build (`component=`/`dependencies=`; `HTMLDependency`).
   - AG Grid is built into NiceGUI.
   - NiceGUI's `run.cpu_bound` pool removes the per-job spawn.
   - Caveats: NiceGUI binds **`0.0.0.0` by default** (set `host='127.0.0.1'`); progress and cancel are DIY; Shiny's DataGrid has no export and `ExtendedTask` has no progress.
   - Panel, the fallback from 06, falls behind these two: offline ESM needs `panel compile` (Node) or vendoring, and its Bokeh server binds all interfaces unless `--address` is set *(inferred)*.

**Not recommended:**
- **A JS/TS backend (B)**: it breaks the shared `network` code (13, 15). The only JS Leiden options are a private upstream module, a fork with `weighted: false` by default, and two 0.x packages, and no JS implementation can reproduce the Python partitions.
- **Reflex**: Bun is fetched by `powershell irm | iex`, packages come from npm at init, and AG Grid is behind a proprietary package.
- **Streamlit**: the rerun model, and telemetry on by default.
- **Gradio**: a demo framework with analytics on by default.
- **Solara**: a CDN proxy by default, and `solara-assets` lags.
- **Observable Framework**: build-time data loaders; 1 release in 12 months.
- **SvelteKit/Next.js**: SSR machinery a local tool doesn't need, and SvelteKit 3.0 is days old.
- **Electron/Tauri**: a desktop shell adds Chromium or Rust + MSVC for no functional gain.
- **Pyodide (C3)**: networkx 3.6.1 has no built-in Leiden, plus a ~12 MB runtime.

**Recommendation for the Web stack selection grilling:**
- **Keep Dash and the Python-backed app.** Nothing in this survey beats the baseline on a fact that matters to the Tag Network.
- The wider frame confirms the earlier decisions:
  - the app stays Python-backed, because that is the only way to keep 13's "same clusters" exactly;
  - the `network` code stays shared, because JS Leiden is immature and cross-implementation partitions differ;
  - the renderer stays a leaf, because the 20 ranking is unchanged in every stack.
- Questions to put to the researcher:
  1. Is a ~4 s start per sensitivity run acceptable, or should the app own a long-lived worker?
  2. Should a short Cytoscape.js 3.34 WebGL wrapper spike happen now or later?
  3. If a TS front end is wanted for its own sake, use hybrid C1 (Python API). Never a JS backend.

## Open questions / spike checklist (only if the grilling reopens the stack)

1. C1: does a FastAPI app serving a committed `dist/` run with uv only (no Node at run time) and with no request leaving localhost?
2. NiceGUI: on Windows (spawn), how long does the first `run.cpu_bound` call take, and do later calls skip the re-import? Does `ui.run(host='127.0.0.1')` serve every Quasar/Vue asset locally with the network disabled?
3. Dash: does a module-level `ProcessPoolExecutor` (or thread) + `dcc.Interval` progress poll remove the 4 s per job without losing a clean cancel?
4. Only if a JS backend is ever reconsidered: run `graphology-communities-louvain` (seeded `rng`), `ngraph.leiden` and NetworkX on the same 17 fixture, and record Q and ARI between them, to quantify how far apart the partitions are.

## Sources

Registry metadata
- [R] PyPI JSON (`https://pypi.org/pypi/<pkg>/json`), npm registry and search (`https://registry.npmjs.org/<pkg>`, `https://registry.npmjs.org/-/v1/search`), GitHub REST API repo metadata; all queried 2026-10-04. Packages: dash, dash-cytoscape, dash-ag-grid, panel, shiny, shinywidgets, nicegui, solara, solara-assets, streamlit, gradio, reflex, reflex-enterprise, fastapi, litestar, starlette, uvicorn, sse-starlette, anywidget, flet, marimo, networkx, igraph, leidenalg, scikit-learn; vite, react, svelte, vue, @sveltejs/kit, next, hono, @hono/node-server, fastify, express, electron, @tauri-apps/cli, @observablehq/framework, htmx.org, bun, ag-grid-community, @tanstack/table-core, tabulator-tables, zustand, piscina, workerpool, @react-sigma/core, graphology, graphology-communities-louvain, graphology-metrics, graphology-layout-forceatlas2, d3-force, seedrandom, @aflsolutions/graphology-communities-leiden, ngraph.leiden, leiden-ts, fast-leiden, @robzzson/silhouette.
- [ND1] Node.js release index (24.21.0 "Krypton", 22.23.3 "Jod"): https://nodejs.org/dist/index.json

Dash / Panel
- [DA1] Dash `run()` default host `127.0.0.1`: https://github.com/plotly/dash/blob/dev/dash/dash.py
- [PA1] Bokeh server `bind_sockets(address, port)` with address unset: https://github.com/bokeh/bokeh/blob/branch-3.10/src/bokeh/server/server.py
- Prior notes: [06](06-web-app-stack.md), [20](20-graph-visualization-alternatives.md) (incl. 20 [P1] `panel compile`, [P2] `AnyWidgetComponent`, [C9] `react-cytoscapejs`), [05](05-graph-clustering-methods.md), [17 spike](../issues/17-dash-cytoscape-windows-spike.md)

Shiny for Python
- [SH1] Non-blocking operations (`ExtendedTask`, `.cancel()`, Thread/ProcessPoolExecutor, GIL caveat): https://shiny.posit.co/py/docs/nonblocking.html
- [SH2] Custom components, one-off (`HTMLDependency`, local `source`, output bindings): https://shiny.posit.co/py/docs/custom-component-one-off.html
- [SH3] `Session.send_custom_message`: https://shiny.posit.co/py/api/core/Session.html
- [SH4] `Shiny.setInputValue` (shared JS API, `priority: "event"`): https://shiny.posit.co/r/articles/build/communicating-with-js/
- [SH5] Data grid (`filters=True`, `selection_mode`): https://shiny.posit.co/py/components/outputs/data-grid/
- [SH6] `run_app` (`host='127.0.0.1'`): https://shiny.posit.co/py/api/core/run_app.html

NiceGUI
- [NG1] Action & events (`run.cpu_bound` pickling, start method): https://nicegui.io/documentation/section_action_events
- [NG2] Configuration & deployment (native mode, host default `0.0.0.0`, nicegui-pack, On Air CDN): https://nicegui.io/documentation/section_configuration_deployment ; https://github.com/zauberzeug/nicegui/blob/main/nicegui/ui_run.py
- [NG3] `Element.__init_subclass__(component=, dependencies=, esm=)`: https://github.com/zauberzeug/nicegui/blob/main/nicegui/element.py
- [NG4] `run.py` (one `ProcessPoolExecutor` created in `setup()`): https://github.com/zauberzeug/nicegui/blob/main/nicegui/run.py
- [NG5] `ui` exports (aggrid, table, echart, anywidget, download): https://github.com/zauberzeug/nicegui/blob/main/nicegui/ui.py

Solara
- [SO1] `solara.lab.task` (thread, `.progress`, `.cancel()`, `is_current()`): https://solara.dev/documentation/components/lab/task
- [SO2] Self-hosted deployment (CDN proxy on by default; binds localhost): https://solara.dev/documentation/getting_started/deploying/self-hosted
- [SO3] Server settings (`proxy_cache_dir`, `SOLARA_ASSETS_PROXY`): https://github.com/widgetti/solara/blob/master/solara/server/settings.py

Streamlit / Gradio / Reflex
- [ST1] config.toml (`browser.gatherUsageStats` default true; `server.address` unset): https://docs.streamlit.io/develop/api-reference/configuration/config.toml
- [ST2] Components v2 (`st.components.v2.component`, `setTriggerValue`, `on_<trigger>_change`): https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component ; https://docs.streamlit.io/develop/concepts/custom-components/components-v2
- [GR1] Gradio environment variables (`GRADIO_ANALYTICS_ENABLED` default True; `GRADIO_SERVER_NAME` 127.0.0.1): https://www.gradio.app/guides/environment-variables
- [GR2] Custom HTML components (`html_template`, `js_on_load`, `trigger`, `watch`): https://www.gradio.app/guides/custom_HTML_components
- [GR3] Progress bars (`gr.Progress`): https://www.gradio.app/guides/progress-bars
- [RX1] Reflex installation (WSL recommended on Windows; Bun needs VC++ runtime): https://reflex.dev/docs/getting-started/installation/
- [RX2] Wrapping React (`library`, `tag`, `EventHandler`; non-React libs "very hard to wrap"): https://reflex.dev/docs/wrapping-react/overview/
- [RX3] Background events (async task, "not a durable job queue"): https://reflex.dev/docs/events/background-events/
- [RX4] `install_bun()` (Windows: `powershell -c "irm ... | iex"`; `REFLEX_USE_NPM`): https://github.com/reflex-dev/reflex/blob/main/reflex/utils/js_runtimes.py
- [RX5] `reflex-enterprise` (AG Grid among paid features; LicenseRef-Proprietary): https://pypi.org/project/reflex-enterprise/

Web servers / JS stacks
- [UV1] uvicorn `Config(host="127.0.0.1")`: https://github.com/encode/uvicorn/blob/master/uvicorn/config.py
- [HX1] htmx.org npm dist-tags (`latest` 2.0.11, `next` 4.0.0) and GitHub release v4.0.0 (2026-08-28): https://registry.npmjs.org/htmx.org , https://github.com/bigskysoftware/htmx/releases
- [TA1] Tauri 2 prerequisites (MSVC Build Tools, WebView2, Rust; sidecars): https://v2.tauri.app/start/prerequisites/
- [OF1] Observable Framework README (static site generator; data loaders at build time): https://github.com/observablehq/framework/blob/main/README.md
- [WK1] Node.js `worker.terminate()`: https://nodejs.org/api/worker_threads.html#workerterminate
- [WK2] MDN `Worker.terminate()`: https://developer.mozilla.org/en-US/docs/Web/API/Worker/terminate

Graph computation
- [GL1] graphology-communities-louvain README (`rng` default `Math.random`, `randomWalk`, `getEdgeWeight`, `resolution`): https://github.com/graphology/graphology/blob/master/src/communities-louvain/README.md
- [GL2] graphology `src/communities-leiden` (`package.json` private 0.0.1; README usage "TODO"): https://github.com/graphology/graphology/tree/master/src/communities-leiden
- [GL3] graphology-metrics README (modularity, centralities): https://github.com/graphology/graphology/blob/master/src/metrics/README.md
- [GL4] `@aflsolutions/graphology-communities-leiden` README (origin, `weighted` default false, `maxIterations`): https://registry.npmjs.org/@aflsolutions%2Fgraphology-communities-leiden
- [NL1] ngraph.leiden README (`randomSeed` default 42; modularity default): https://registry.npmjs.org/ngraph.leiden
- [LT1] leiden-ts README (xoshiro128**, parity gates vs graspologic): https://registry.npmjs.org/leiden-ts
- [NX1] NetworkX `leiden.py` at tag networkx-3.6.1 ("backend required", `implemented_by_nx=False`) vs networkx-3.7 (pure Python): https://github.com/networkx/networkx/blob/networkx-3.6.1/networkx/algorithms/community/leiden.py , https://github.com/networkx/networkx/blob/networkx-3.7/networkx/algorithms/community/leiden.py
- [PY1] Pyodide 314.0.7 lock file (Python 3.14.2; networkx 3.6.1; igraph 1.0.0; scikit-learn 1.8.0; no leidenalg): https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json
- [PY2] Pyodide 314.0.7 file sizes, downloaded 2026-10-04: `pyodide.asm.wasm` 9,598,218 B; `python_stdlib.zip` 2,545,637 B; networkx wheel 1,084,840 B; igraph 1,072,087 B; numpy 2,960,568 B; scipy 14,029,750 B (same base URL)
