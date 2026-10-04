# Interactive graph visualization alternatives
Type: research
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

Besides dash-cytoscape (Dash) and Panel + a hand-wrapped Cytoscape.js, which interactive graph/network visualization libraries and tools could render the Tag Network, and how do they compare?

The app needs: ~400 tag nodes and up to ~5,000 weighted edges (worst case; the 8/8 defaults give far fewer); per-cluster colours and distinct cluster-centre styling; node **and** edge click events with the event reaching Python (edge data carries AppID lists); preset positions computed in Python (Global / Cluster-separated layouts, with tinted cluster-region backgrounds) switchable without re-mounting; smooth pan/zoom; fully offline; Windows; permissive licence; active maintenance.

Cover JS renderers (e.g. Cytoscape.js 3.31+ WebGL, sigma.js + graphology, vis-network, AntV G6, cosmos.gl/Cosmograph, force-graph, ECharts graph series, D3), their Python bindings or widgets (e.g. ipysigma, ipycytoscape, anywidget-based widgets, Plotly/Bokeh/HoloViews), framework fit (Dash custom component, Panel `JSComponent`/`ReactiveESM`/`AnyWidgetComponent`, Streamlit components v2), and commercial options only for completeness.

Context: [Python web app stack for the tag network](06-web-app-stack.md), [Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md).

## Answer

**Keep Dash. Treat the graph renderer as a replaceable leaf.** If the worst-case graph needs to be smoother, the next step is current Cytoscape.js with WebGL behind a thin wrapper of our own, not a different renderer.

- **Cytoscape.js 3.34.3** (2026-09-07) has an opt-in WebGL mode (since 3.31). It keeps all node and label styles and haystack edges, so the spike's stylesheet, elements and tap handling carry over. Caveats: it is still documented only as a "preview", and one integrated-GPU user saw it get slower (closed as a likely driver issue).
- **dash-cytoscape can't use it.** 1.0.2 bundles Cytoscape.js 3.28.1, which predates WebGL, and its React layer passes no `renderer` option. That was checked against the installed bundle. It does set `window.cy`, which allows small clientside tweaks such as hiding edges during pan/zoom.
- **Shortlist:** (1) Cytoscape.js 3.34 with WebGL in a ~150–250-line wrapper (Dash `assets/` + `set_props`, or a Panel `JSComponent`); (2) sigma.js 3 + graphology if (1) is slow or buggy on the researcher's GPU (no built-in diamond or bordered shape until v4, now in beta; no maintained Dash wrapper); (3) AntV G6 5 (every feature built in, including hull/bubble-set cluster regions, but a 1.38 MB bundle and messy npm tags).
- **Ruled out:** vis-network (canvas only, so no speed gain; its Dash wrappers are stale), cosmos.gl (no labels or borders yet), force-graph / ECharts / Reagraph / D3 (each misses a key piece or needs a lot of DIY code), pyvis / gravis / netgraph (stale, display-only or GPL), Cosmograph packages (CC-BY-NC/GPL), yFiles / Ogma / KeyLines (commercial).
- **Payload is a separate lever from the renderer.** Keep AppID lists on the server and fetch them on click. Whether Dash `Patch` shrinks dash-cytoscape `elements` updates is untested.

Details, matrices and citations: [../research/20-graph-visualization-alternatives.md](../research/20-graph-visualization-alternatives.md)
