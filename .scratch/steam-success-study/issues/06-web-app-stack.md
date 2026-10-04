# Python web app stack for the tag network
Type: research
Status: resolved
Blocked by: none

## Question

Which local Python-backed web stack best fits the interactive Tag Network app?

Candidates: Dash + dash-cytoscape, Panel/HoloViews, Streamlit (+ agraph/pyvis), FastAPI/Flask + a JS graph library (sigma.js, Cytoscape.js, vis-network).

Assess: interactive weighted graph rendering of up to ~400 nodes / several thousand edges; distinct styling for cluster centers; clicking nodes/edges to inspect; sortable/filterable tables; recompute-on-input-change wiring; CSV/JSON downloads; CSV file upload; long-running computation handling (progress, cancellation, caching); maintenance status and licence; ease of install on Windows.

## Answer

Use **Dash 4 + dash-cytoscape + dash-ag-grid**, with `DiskcacheManager` background callbacks for heavy recomputes.
- It is the only candidate with built-in progress, cancellation and argument-hashed result caching for long runs (Louvain, sensitivity).
- It has node **and** edge tap events (`tapNodeData` / `tapEdgeData`) and CSS-like stylesheet selectors for cluster centres.
- AG Grid covers sortable/filterable tables with CSV export; `dcc.Upload` / `dcc.Download` cover file input and output.
- All licences are permissive (MIT); everything installs from pip on Windows.

**Risk:** dash-cytoscape is in maintenance mode. Its last release was 1.0.2 in July 2024, before Dash 3 and 4, and a Dash 4 mount bug was reported in 2026 but not fixed.
- **Gate:** a short Windows spike (about 400 nodes and 5k edges, tap events, background callback with cancel under spawn, rapid threshold toggles) before the spec is locked.
- **Fallback:** Panel + Tabulator + a `JSComponent` that wraps current Cytoscape.js, bundled with esbuild for offline use. The same stylesheet and elements JSON carry over; cancellation becomes DIY.

**Rejected:**
- Streamlit: its graph components are stale (agraph 2023, pyvis 2023 and display-only), and the full-script rerun model fits graph inspection badly.
- FastAPI/Flask + JS: best rendering (sigma.js WebGL), but tables, jobs, progress, cancellation and wiring would all be DIY.
- HoloViews `Graph` alone: it highlights nodes *or* edges, not both.

Findings, matrix and citations: [../research/06-web-app-stack.md](../research/06-web-app-stack.md)
