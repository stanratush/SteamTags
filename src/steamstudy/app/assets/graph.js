/* The renderer boundary, browser half (the Python half is renderer.py).

   Owns the Cytoscape.js instance (vendored cytoscape.min.js, never a CDN). Dash sends one store,
   `graph-data`: elements, target positions, regions, the selection and view commands. Taps on a node,
   an edge, a region title or the background come back on the `graph-event` store through
   dash_clientside.set_props.

   The canvas follows its container (a ResizeObserver), and the view refits until the user zooms or
   pans. Every fit targets where the nodes end up. At render time x is stretched by the canvas aspect
   ratio (at most 1.6x) so the first fit fills a wide canvas; exported coordinates are untouched.
*/
(function () {
  "use strict";
  const PAD = 30, MAX_STRETCH = 1.6, LABEL_ROOM = 14, TITLE_ROOM = 22;
  const G = {cy: null, el: null, data: null, sig: null, moveSig: null, stretch: 1, userMoved: false,
             quietUntil: 0, viewNonce: null};

  function style() {
    return [
      {selector: "node", style: {
        "background-color": "data(color)", "label": "data(label)", "font-size": 10, "min-zoomed-font-size": 7,
        "width": "data(size)", "height": "data(size)", "color": "#222", "text-outline-color": "#fff",
        "text-outline-width": 1, "z-index-compare": "manual", "z-index": 10}},
      {selector: "node.one_tag", style: {"opacity": 0.7}},
      {selector: "node.center", style: {
        "shape": "diamond", "border-width": 3, "border-color": "#111", "font-weight": "bold", "z-index": 20}},
      {selector: "node.region", style: {
        "shape": "round-rectangle", "width": "data(w)", "height": "data(h)", "background-color": "data(color)",
        "background-opacity": 0.1, "border-width": 1, "border-color": "data(color)", "border-opacity": 0.4,
        "label": "data(label)", "text-valign": "top", "text-halign": "center", "font-size": 14, "color": "#555",
        "text-outline-width": 0, "z-index": 0, "text-events": "yes"}},
      {selector: "edge", style: {
        "curve-style": "haystack", "haystack-radius": 0, "line-color": "#8a8a8a", "opacity": 0.45,
        "width": "data(width)", "z-index-compare": "manual", "z-index": 5}},
      {selector: "edge.inter.separated", style: {"opacity": 0.08}},
      {selector: "node.sel", style: {"border-width": 4, "border-color": "#d00", "opacity": 1}},
      {selector: "edge.sel", style: {"line-color": "#d00", "opacity": 1}},
    ];
  }

  function emit(event) {
    event.nonce = Date.now() + Math.random();  // repeated taps on the same element still fire
    window.dash_clientside.set_props("graph-event", {data: event});
  }

  // Programmatic viewport changes are "quiet"; any other viewport change is the user zooming or panning.
  function quiet(ms) { G.quietUntil = Math.max(G.quietUntil, performance.now() + ms + 60); }

  function onTitle(region, p) {
    const b = region.boundingBox({includeNodes: false, includeLabels: true, includeOverlays: false});
    return p.x >= b.x1 && p.x <= b.x2 && p.y >= b.y1 && p.y <= b.y2;
  }

  function mount(el) {
    const cy = cytoscape({container: el, style: style(), elements: [], minZoom: 0.05, maxZoom: 5,
                          boxSelectionEnabled: false, autounselectify: true});
    cy.on("tap", "node", (ev) => {
      const n = ev.target;
      if (!n.hasClass("region")) emit({kind: "node", id: n.id()});
      else if (onTitle(n, ev.position)) emit({kind: "region", cluster: n.data("cluster")});
      else emit({kind: "background"});  // only a region's title is clickable
    });
    cy.on("tap", "edge", (ev) => {
      const e = ev.target;
      emit({kind: "edge", id: e.id(), source: e.data("source"), target: e.data("target")});
    });
    cy.on("tap", (ev) => { if (ev.target === cy) emit({kind: "background"}); });
    cy.on("viewport", () => { if (performance.now() > G.quietUntil) G.userMoved = true; });
    new ResizeObserver(() => {
      cy.resize();
      if (G.data && !G.userMoved) { place(); fit(); }
    }).observe(el);
    return cy;
  }

  // ------------------------------------------------------------------ geometry

  function box(data, stretch) {
    let x1 = Infinity, x2 = -Infinity, y1 = Infinity, y2 = -Infinity;
    for (const n of data.nodes) {
      const p = data.positions[n.id];
      if (!p) continue;
      const r = n.size / 2;
      x1 = Math.min(x1, p[0] * stretch - r); x2 = Math.max(x2, p[0] * stretch + r);
      y1 = Math.min(y1, p[1] - r); y2 = Math.max(y2, p[1] + r + LABEL_ROOM);
    }
    for (const r of data.regions) {
      x1 = Math.min(x1, (r.x - r.w / 2) * stretch); x2 = Math.max(x2, (r.x + r.w / 2) * stretch);
      y1 = Math.min(y1, r.y - r.h / 2 - TITLE_ROOM); y2 = Math.max(y2, r.y + r.h / 2);
    }
    if (!isFinite(x1)) return {x1: -1, x2: 1, y1: -1, y2: 1};
    return {x1, x2, y1, y2};
  }

  function stretchFor(data) {
    const w = G.cy.width(), h = G.cy.height(), bb = box(data, 1);
    if (!w || !h) return 1;
    const want = (w / h) / (Math.max(bb.x2 - bb.x1, 1) / Math.max(bb.y2 - bb.y1, 1));
    return Math.max(1, Math.min(MAX_STRETCH, want));
  }

  function at(id) {
    const p = G.data.positions[id] || [0, 0];
    return {x: p[0] * G.stretch, y: p[1]};
  }

  function fit() {
    const cy = G.cy, w = cy.width(), h = cy.height();
    if (!w || !h || !G.data) return;
    const bb = box(G.data, G.stretch);
    const bw = Math.max(bb.x2 - bb.x1, 1), bh = Math.max(bb.y2 - bb.y1, 1);
    const zoom = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), Math.min((w - 2 * PAD) / bw, (h - 2 * PAD) / bh)));
    quiet(0);
    cy.viewport({zoom, pan: {x: w / 2 - zoom * (bb.x1 + bb.x2) / 2, y: h / 2 - zoom * (bb.y1 + bb.y2) / 2}});
  }

  // Re-apply the target positions with the current stretch (after a resize).
  function place() {
    G.stretch = stretchFor(G.data);
    G.cy.batch(() => {
      for (const n of G.data.nodes) G.cy.getElementById(n.id).position(at(n.id));
      for (const r of G.data.regions) {
        const el = G.cy.getElementById(r.id);
        el.data("w", r.w * G.stretch);
        el.unlock().position({x: r.x * G.stretch, y: r.y}).lock();
      }
    });
  }

  // ------------------------------------------------------------------ elements, selection, view

  function nodeData(n) { return {id: n.id, label: n.label, cluster: n.cluster, color: n.color, size: n.size}; }

  function sync(data, fresh, moved) {
    const cy = G.cy;
    G.stretch = stretchFor(data);
    const nodeIds = new Set(data.nodes.map((n) => n.id)), edgeIds = new Set(data.edges.map((e) => e.id));
    cy.batch(() => {
      if (fresh) cy.elements().remove();
      cy.edges().filter((e) => !edgeIds.has(e.id())).remove();
      cy.nodes().filter((n) => n.hasClass("region") || !nodeIds.has(n.id())).remove();
      for (const r of data.regions) {
        cy.add({group: "nodes", data: {id: r.id, label: r.label, cluster: r.cluster, color: r.color,
                                       w: r.w * G.stretch, h: r.h},
                position: {x: r.x * G.stretch, y: r.y}, classes: "region", grabbable: false, selectable: false,
                locked: true, pannable: true});
      }
      for (const n of data.nodes) {
        const el = cy.getElementById(n.id);
        if (el.nonempty()) { el.data(nodeData(n)); el.classes(n.classes); el.position(at(n.id)); }
        else cy.add({group: "nodes", data: nodeData(n), classes: n.classes, position: at(n.id)});
      }
      for (const e of data.edges) {
        const el = cy.getElementById(e.id);
        if (el.nonempty()) { el.data("width", e.width); el.classes(e.classes); }
        else cy.add({group: "edges", data: {id: e.id, source: e.source, target: e.target, width: e.width},
                     classes: e.classes});
      }
    });
    if (fresh || moved) G.userMoved = false;
    if (!G.userMoved) fit();
  }

  function applySelection(sel) {
    const cy = G.cy;
    cy.elements().removeClass("sel");
    if (sel && (sel.kind === "node" || sel.kind === "edge")) cy.getElementById(sel.id).addClass("sel");
  }

  function runView(view) {
    if (!view || view.nonce === G.viewNonce) return;
    G.viewNonce = view.nonce;
    if (view.cmd === "fit") { G.userMoved = false; fit(); }
  }

  function render(data) {
    const noUpdate = window.dash_clientside.no_update;
    const el = document.getElementById("cy");
    if (!data || !data.nodes || !el) return noUpdate;
    if (!G.cy || G.el !== el) {
      if (G.cy) G.cy.destroy();
      G.el = el; G.cy = mount(el); G.data = null; G.sig = null; G.moveSig = null;
    }
    const prev = G.data;
    G.data = data;
    const moveSig = JSON.stringify([data.layout, data.positions, data.regions]);
    const sig = JSON.stringify([data.dataset, data.nodes, data.edges, moveSig]);
    if (sig !== G.sig) {
      sync(data, !prev || prev.dataset !== data.dataset, moveSig !== G.moveSig);
      G.sig = sig; G.moveSig = moveSig;
    }
    applySelection(data.selected);
    runView(data.view);
    return Date.now();
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {tagGraph: {render}});
  window.tagGraph = G;  // for inspection in the browser console and browser checks
})();
