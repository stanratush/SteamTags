# Alternative app frameworks and graph renderers (Python or JS/TS backend)
Type: research
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

Which application frameworks, together with which graph/network renderers, could build the Tag Network app if the backend may be **Python or JavaScript/TypeScript**, and how do they compare with the Dash + dash-cytoscape baseline that passed the [Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md)?

Requested by the researcher during [Web stack selection](18-web-stack-selection.md) (2026-10-04). [Interactive graph visualization alternatives](20-graph-visualization-alternatives.md) already compared renderers *inside Dash/Panel*; this ticket widens the frame to whole stacks and only updates the renderer findings where framework fit changes them.

- **Python frameworks** not yet assessed (or assessed only briefly in [Python web app stack for the tag network](06-web-app-stack.md)): e.g. Shiny for Python, NiceGUI, Reflex, Solara, Panel 1.x, Streamlit (recheck), Gradio, FastAPI/Litestar + HTMX or + a JS SPA.
- **JS/TS stacks**: e.g. a Vite + React/Svelte/Vue SPA with a Node/Bun/Deno backend (Hono, Fastify, Express), SvelteKit, Next.js, Electron/Tauri desktop shells, Observable Framework; and a **hybrid**: TS frontend + Python compute API.
- **Graph computation if the backend is JS/TS**: Louvain/Leiden availability and determinism (seeding) in JS (e.g. graphology-communities-louvain, any Leiden port), modularity, silhouette, centralities; and how the app would stay consistent with the Python feature-analysis report, which by [Feature-analysis definitions](13-feature-analysis-definitions.md) and [Pipeline architecture and export schema](15-pipeline-architecture.md) runs "the Tag Network's own clustering code" from the Python `network` subpackage. Options include one implementation called from both sides, a parity test suite, or Python in the browser (Pyodide/WASM).
- **Background work**: progress, cancel and stale-marking for node sensitivity (Web Workers, worker threads, job queues vs. Dash's ~4 s Windows spawn).
- **Per stack**: renderer fit (Cytoscape.js 3.34 WebGL, sigma.js 3/4, G6 5, Reagraph...) with node **and** edge clicks, preset positions, tinted cluster regions, update without re-mount; tables (AG Grid, TanStack Table, Tabulator); CSV/JSON download; two modes over one shared state; fully offline bundling; Windows install for one researcher (number of toolchains: uv only vs. uv + Node); licence; maintenance; amount of custom code.

Note: the app was settled as "local Python-backed" while charting. A JS/TS backend would reopen that decision and the shared `network` code; this ticket only gathers the facts.

## Answer

**Keep Dash and the Python-backed app with shared `network` code.** The wider survey found nothing that beats the baseline on facts that matter here. A JS/TS backend would cost a lot and break the "same clusters" rule.

- **Renderer choice doesn't depend on the framework.** Every stack can host Cytoscape.js 3.34 (WebGL), sigma.js 3 or G6 5 behind a thin wrapper, so the ranking in [20](20-graph-visualization-alternatives.md) still holds. A JS front end only removes the bridge back to Python.
- **JS graph computation is not ready for this study.**
  - Louvain is fine: `graphology-communities-louvain` can be seeded through `rng`, which defaults to `Math.random`.
  - Leiden is not. graphology's own Leiden is unpublished (`private`, 0.0.1). Its third-party fork ignores edge weights by default (`weighted: false`). `ngraph.leiden` 0.3.0 and `leiden-ts` 0.1.0 are young.
  - No JS implementation reproduces NetworkX's partitions from the same seed. Parity could only be approximate, which fails [13](13-feature-analysis-definitions.md)'s "own clustering code".
- **Python in the browser doesn't fix that either.** Pyodide 314.0.7 ships networkx 3.6.1, where Leiden still needs a backend, and it has no leidenalg. It would also add ~12 MB of runtime to vendor.
- **Python frameworks re-checked:**
  - NiceGUI 3.17 and Shiny 1.8 are the credible alternatives to Dash. Custom JS is plain local files with no build step. NiceGUI includes AG Grid and keeps one process pool for the life of the app, so jobs don't pay a spawn each time.
  - Caveats: NiceGUI listens on `0.0.0.0` by default, and progress/cancel are DIY in both.
  - The rest fall away. Solara loads assets through a CDN proxy by default, and Streamlit and Gradio send usage statistics by default. Reflex fetches Bun with `powershell irm | iex`, installs npm packages at init and sells AG Grid in a paid package.
- **Hybrid** (Vite SPA + FastAPI calling the Python `network` package): the only TS-front-end option that keeps exact parity. It costs uv + Node at development time (Node 22.14 is already installed) and the most glue code.
- **Background work:** Dash's ~4 s per sensitivity job comes from `DiskcacheManager` starting a new process for each job on Windows. A pool or thread that lives with the app avoids it, at the cost of rebuilding progress and cancel. Stale-marking is app logic in every stack.
- **Ranked shortlist:** (1) Dash 4, with the graph as a replaceable leaf; (2) hybrid FastAPI + Vite/TS SPA; (3) NiceGUI 3 (or Shiny 1.8). Not recommended: a JS backend, Reflex, Streamlit, Gradio, Solara, Observable Framework, SvelteKit/Next.js, Electron/Tauri, and Pyodide.
- **For the grilling:**
  1. Is a ~4 s start per sensitivity run acceptable, or should the app own a long-lived worker?
  2. Should the WebGL wrapper spike run now or later?
  3. If a TS front end is wanted, take the hybrid, never a JS backend.

Details, matrices and citations: [../research/21-app-frameworks-and-renderers.md](../research/21-app-frameworks-and-renderers.md)
