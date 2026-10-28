/* The renderer boundary, browser half (the Python half is renderer.py).

   Owns the Cytoscape.js instance (vendored cytoscape.min.js, never a CDN). Dash sends one store,
   `graph-data`: elements, target positions, regions, the selection and view commands. Taps on a node,
   an edge, a region title or the background come back on the `graph-event` store through
   dash_clientside.set_props.

   The canvas follows its container (a ResizeObserver), and the view refits until the user zooms or
   pans. Every fit targets where the nodes and their labels end up, never zooms past 100 %, and leaves
   room for the overlays drawn over the canvas (elements marked data-graph-overlay="top|right|bottom|left").
   Python lays the graph out for the free area this canvas reports, so one model unit is one screen pixel at
   the first fit (layout.py's fit_zoom fits the same way). Transient overlays (also data-graph-transient: the
   floating Inspector, shown only with a selection) never change the layout or the fit; when one covers the
   selected tag, the view pans to show it.

   Labels: every label keeps a constant 11.5 px on screen, with a white halo; the selection and its
   neighbours (`hot`) get a solid white box and bold type. Python spaces the layout so no label overlaps
   at the zoom it sends (`zoom`) and above. Zoomed out below that (or below the first fit), a label that
   overlaps a higher-ranked one is hidden after every zoom (rank: `hot`, then the `prio` sent by Python:
   Centers, then n_games).

   Motion is brief and never continuous: moves, fades and animated fits take about 350 ms; a selected tag
   gets one 320 ms ring that CSS animates over the canvas (smooth even while the main thread is busy). All of
   it is instant (or absent) under prefers-reduced-motion. A new dataset only fits (animated).
   A tap is drawn at once (selectNow); the server's matching answer changes nothing, and an answer for an
   earlier tap is dropped. Selecting never asks for a layout or any analysis.
   Dragged positions are view-only: kept (per layout) while the layout basis is the same, dropped when the
   dataset, Minimum Months Filter, Clustering Weight or seed changes. Those dragged in the Global layout go
   back on the `graph-dragged` store only for Tidy, which keeps them where they were dropped. The canvas reports its
   free area {w, h} on the `graph-canvas` store, each side rounded down to steps of 8 % from the reference
   canvas (1116 x 678), so small resizes never trigger a new layout and the layout always fits the real area.
*/
(function () {
  "use strict";
  const PAD = 30, TITLE_ROOM = 22;
  const LABEL_H = 15, LABEL_MARGIN = 2;  // a label's box below its node, in pixels (layout.py's LABEL_HEIGHT, LABEL_MARGIN)
  const REF = {w: 1116, h: 678}, STEP = 1.08;  // the reference canvas and the canvas report's steps
  const REPORT_SETTLE = 150, LABEL_SETTLE = 120;  // ms a size or a zoom must stay put before acting on it
  const LABEL_PX = 11.5, TITLE_PX = 12.5, HALO = 2;  // constant on-screen sizes of labels and region titles
  const MOTION = 350, EASE = "ease-in-out-cubic";
  const DASH_QUIET = 50;  // ms without a Dash update before a view animation starts (whenDashIdle)
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const G = {cy: null, el: null, data: null, sig: null, moveSig: null, userMoved: false,
             quietUntil: 0, viewNonce: null, labelFrame: 0, selected: null, basis: null,
             dragged: {global: {}, separated: {}}};

  function dur() { return reduced.matches ? 0 : MOTION; }

  function style() {
    return [
      {selector: "node", style: {
        "background-color": "data(color)", "label": "data(label)", "font-size": LABEL_PX, "min-zoomed-font-size": 0,
        "font-family": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", "color": "#1b2130",
        "text-valign": "bottom", "text-margin-y": 2, "text-outline-color": "#fff", "text-outline-width": HALO,
        "text-outline-opacity": 0.95, "width": "data(size)", "height": "data(size)", "border-width": 1.2,
        "border-color": "#00000040", "z-index-compare": "manual", "z-index": 10}},
      {selector: "node.hot", style: {
        "font-weight": 700, "text-outline-width": 0, "text-background-color": "#fff", "z-index": 15,
        "text-background-opacity": 1, "text-background-padding": 2, "text-background-shape": "round-rectangle"}},
      {selector: "node.one_tag", style: {"opacity": 0.8}},
      {selector: "node.center", style: {
        "shape": "diamond", "border-width": 2, "border-color": "#1b2130", "font-weight": 650, "z-index": 20}},
      {selector: "node.region", style: {
        "shape": "round-rectangle", "width": "data(w)", "height": "data(h)", "background-color": "data(color)",
        "background-opacity": 0.07, "border-width": 1, "border-color": "data(color)", "border-opacity": 0.35,
        "label": "data(label)", "text-valign": "top", "text-halign": "center", "font-size": 12.5,
        "min-zoomed-font-size": 0, "font-weight": 600, "color": "#3d4555", "text-outline-width": 0,
        "z-index": 0, "text-events": "yes"}},
      // An edge's width, colour and strength are the Edge Appearance's (restyle); the classes below override them.
      {selector: "edge", style: {
        "curve-style": "haystack", "haystack-radius": 0, "line-color": "data(ac)", "opacity": "data(ao)",
        "width": "data(aw)", "z-index-compare": "manual", "z-index": 5}},
      {selector: "node.dim", style: {"opacity": 0.12}},
      {selector: "edge.dim", style: {"opacity": 0.04}},
      // A tag's (or a pair's) links keep their colour and become opaque; under one colour they darken.
      {selector: "edge.nb", style: {"opacity": 0.9}},
      {selector: "edge.nbdark", style: {"line-color": "#4a5262"}},
      {selector: "edge.hid", style: {"display": "none"}},
      {selector: "node.sel", style: {"border-width": 3, "border-color": "#2457d6", "z-index": 30}},
      {selector: "edge.sel", style: {"line-color": "#2457d6", "opacity": 0.95}},
      {selector: "node.lbl-off", style: {"text-opacity": 0, "text-background-opacity": 0}},
      // No style cross-fades: a selection dims or lights up every element at once, and fading them all costs
      // more per frame than the change itself.
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
    // A tap is sent to the server (which still decides the selection and fills the Inspector) and drawn at once
    // (selectNow) while the request is on its way; the server's matching answer then changes nothing.
    cy.on("tap", "node", (ev) => {
      const n = ev.target;
      if (n.hasClass("leaving")) return;
      if (!n.hasClass("region")) {
        emit({kind: "node", id: n.id()});
        selectNow({kind: "node", id: n.id()});
      } else if (onTitle(n, ev.position)) {
        emit({kind: "region", cluster: n.data("cluster")});
        if (n.data("cluster") !== "one_tag_pool") selectNow({kind: "cluster", id: n.data("cluster")});
      } else {
        emit({kind: "background"});  // only a region's title is clickable
        selectNow(null);
      }
    });
    cy.on("tap", "edge", (ev) => {
      const e = ev.target;
      if (e.hasClass("leaving")) return;
      emit({kind: "edge", id: e.id(), source: e.data("source"), target: e.data("target")});
      selectNow({kind: "edge", id: e.id()});
    });
    cy.on("tap", (ev) => { if (ev.target === cy) { emit({kind: "background"}); selectNow(null); } });
    cy.on("dragfree", "node", (ev) => {  // a dragged position, kept per layout
      const n = ev.target;
      if (!G.data || !G.data.positions[n.id()] || n.hasClass("region")) return;
      G.dragged[G.data.layout][n.id()] = {x: n.position("x"), y: n.position("y")};
      if (G.data.layout === "global") reportDragged();
    });
    cy.on("viewport", () => {
      dropRing();  // it would no longer sit on its node
      if (performance.now() > G.quietUntil) G.userMoved = true;
    });
    // Labels are re-sized and re-culled once a zoom settles, not on every frame: a new font size makes every
    // label redraw from scratch, about twice the cost of a frame. While zooming they scale with the graph.
    cy.on("zoom", () => {
      clearTimeout(G.labelTimer);
      G.labelTimer = setTimeout(sizeLabels, LABEL_SETTLE);
    });
    // After a resize: refit at once, and report the canvas once the size has settled.
    G.refresh = () => {
      cy.resize();
      scheduleReport();
      if (G.data && !G.userMoved) fit(false);
      if (G.data) sizeLabels();
    };
    const ro = new ResizeObserver(() => G.refresh());
    ro.observe(el);
    document.querySelectorAll("[data-graph-overlay]:not([data-graph-transient])").forEach((o) => ro.observe(o));
    // A transient overlay (the floating Inspector) never changes the layout or the fit; it only makes sure the
    // selected tag is not hidden under it.
    const shown = new ResizeObserver(() => revealSelection());
    document.querySelectorAll("[data-graph-transient]").forEach((o) => shown.observe(o));
    return cy;
  }

  // ------------------------------------------------------------------ geometry

  // The canvas area left free by the overlays that cover it, as insets from each side. Transient overlays
  // (data-graph-transient: the floating Inspector, shown only with a selection) are not counted, so selecting
  // and deselecting never re-lays out or refits the graph.
  function insets() {
    const c = G.el.getBoundingClientRect(), pad = {top: PAD, right: PAD, bottom: PAD, left: PAD};
    for (const o of document.querySelectorAll("[data-graph-overlay]:not([data-graph-transient])")) {
      const r = o.getBoundingClientRect(), side = o.dataset.graphOverlay;
      if (!r.width || !r.height || r.right <= c.left || r.left >= c.right || r.bottom <= c.top || r.top >= c.bottom) {
        continue;
      }
      const depth = {top: r.bottom - c.top, right: c.right - r.left, bottom: c.bottom - r.top, left: r.right - c.left};
      if (depth[side] < (side === "top" || side === "bottom" ? c.height : c.width) * 0.6) {
        pad[side] = Math.max(pad[side], depth[side] + 12);
      }
    }
    return pad;
  }

  function freeArea() {
    const p = insets(), w = G.cy.width(), h = G.cy.height();
    return {w: Math.max(w - p.left - p.right, 40), h: Math.max(h - p.top - p.bottom, 40),
            cx: p.left + (w - p.left - p.right) / 2, cy: p.top + (h - p.top - p.bottom) / 2};
  }

  // Where a node ends up: its dragged position (same layout basis), else its target.
  function spot(data, id) {
    const drag = G.dragged[data.layout][id];
    return drag && data.positions[id] ? [drag.x, drag.y] : data.positions[id];
  }

  // Tell Dash the nodes dragged in the Global layout, for Tidy (which keeps them where they were dropped).
  function reportDragged() {
    const positions = {};
    for (const [id, p] of Object.entries(G.dragged.global)) positions[id] = [p.x, p.y];
    window.dash_clientside.set_props("graph-dragged", {data: {basis: G.basis, positions}});
  }

  // Tell Dash the free canvas area whenever its step changes: each side rounded down to REF * STEP^k (a side
  // up to about 1 % short of a step still counts as that step).
  // Report once the canvas size has stayed put for REPORT_SETTLE ms: a panel opening animates through many
  // sizes, and each report costs a layout on the server.
  function scheduleReport() {
    clearTimeout(G.reportTimer);
    G.reportTimer = setTimeout(reportCanvas, G.canvas ? REPORT_SETTLE : 0);
  }

  // Pan the selected tag into view when a transient overlay (the floating Inspector) covers it.
  function revealSelection() {
    if (!G.cy || !G.selected || !G.cy.width()) return;
    const panel = document.getElementById("inspector-panel");
    if (panel && panel.dataset.pending) { G.revealLater = true; return; }  // after the content lands (smoother)
    const sel = JSON.parse(G.selected);
    if (!sel || sel.kind !== "node") return;
    const n = G.cy.getElementById(sel.id);
    if (n.empty()) return;
    const c = G.el.getBoundingClientRect(), p = n.renderedPosition(), r = n.renderedWidth() / 2;
    for (const o of document.querySelectorAll("[data-graph-transient]")) {
      const b = o.getBoundingClientRect();
      if (!b.width || !b.height) continue;
      const x1 = b.left - c.left, x2 = b.right - c.left, y1 = b.top - c.top, y2 = b.bottom - c.top;
      if (p.x + r < x1 || p.x - r > x2 || p.y + r < y1 || p.y - r > y2) continue;
      // Just far enough to clear the overlay's left edge (labels need about one label width of room).
      const target = Math.max(PAD + r, x1 - r - Math.max(n.data("lw") || 0, 40));
      const pan = G.cy.pan();
      viewport(G.cy.zoom(), {x: pan.x + (target - p.x), y: pan.y}, true);
      return;
    }
  }

  function reportCanvas() {
    if (!G.cy || !G.cy.width() || !G.cy.height()) return;
    const a = freeArea();
    const step = (v, ref) => Math.round(ref * Math.pow(STEP, Math.floor(Math.log(v / ref) / Math.log(STEP) + 0.15)));
    const size = {w: step(a.w, REF.w), h: step(a.h, REF.h)};
    if (!G.canvas || size.w !== G.canvas.w || size.h !== G.canvas.h) {
      G.canvas = size;
      window.dash_clientside.set_props("graph-canvas", {data: size});
    }
  }

  // What the graph covers at a zoom, in model units: nodes, their labels (constant on screen) and regions.
  function box(data, zoom) {
    let x1 = Infinity, x2 = -Infinity, y1 = Infinity, y2 = -Infinity;
    for (const n of data.nodes) {
      const p = spot(data, n.id);
      if (!p) continue;
      const r = n.size / 2, half = Math.max(r, (n.lw || 0) / 2 / zoom);
      x1 = Math.min(x1, p[0] - half); x2 = Math.max(x2, p[0] + half);
      y1 = Math.min(y1, p[1] - r); y2 = Math.max(y2, p[1] + r + (LABEL_MARGIN + LABEL_H) / zoom);
    }
    for (const r of data.regions) {
      x1 = Math.min(x1, r.x - r.w / 2); x2 = Math.max(x2, r.x + r.w / 2);
      y1 = Math.min(y1, r.y - r.h / 2 - TITLE_ROOM / zoom); y2 = Math.max(y2, r.y + r.h / 2);
    }
    if (!isFinite(x1)) return {x1: -1, x2: 1, y1: -1, y2: 1};
    return {x1, x2, y1, y2};
  }

  // The first fit: the largest zoom, at most 1, at which the whole graph is inside the free area.
  function fitZoom(data) {
    const a = freeArea();
    const fits = (z) => { const b = box(data, z); return (b.x2 - b.x1) * z <= a.w && (b.y2 - b.y1) * z <= a.h; };
    if (fits(1)) return 1;
    let lo = G.cy.minZoom(), hi = 1;
    for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; if (fits(mid)) lo = mid; else hi = mid; }
    return lo;
  }

  function at(id) {
    const p = spot(G.data, id) || [0, 0];
    return {x: p[0], y: p[1]};
  }

  function viewport(zoom, pan, animate) {
    const ms = animate ? dur() : 0;
    quiet(ms);
    G.cy.stop(true, false);
    if (ms) G.cy.animate({zoom, pan}, {duration: ms, easing: EASE});
    else G.cy.viewport({zoom, pan});
  }

  function fit(animate) {
    if (!G.data || !G.cy.width() || !G.cy.height()) return;
    const zoom = fitZoom(G.data);
    G.fitZoom = zoom;
    centre(box(G.data, zoom), zoom, animate);
  }

  function centre(bb, zoom, animate) {
    const a = freeArea();
    viewport(zoom, {x: a.cx - zoom * (bb.x1 + bb.x2) / 2, y: a.cy - zoom * (bb.y1 + bb.y2) / 2}, animate);
  }

  function fitBox(bb, animate) {
    const cy = G.cy, w = cy.width(), h = cy.height();
    if (!w || !h) return;
    const a = freeArea();
    const bw = Math.max(bb.x2 - bb.x1, 1), bh = Math.max(bb.y2 - bb.y1, 1);
    centre(bb, Math.max(cy.minZoom(), Math.min(cy.maxZoom(), Math.min(a.w / bw, a.h / bh))), animate);
  }

  // Centre the free area on some elements, zooming in to at least 1.2 (search, a connected-tag row).
  function centerOn(eles) {
    if (eles.empty()) return;
    const b = eles.boundingBox({includeLabels: false, includeOverlays: false}), a = freeArea();
    const zoom = Math.min(G.cy.maxZoom(), Math.max(G.cy.zoom(), 1.2));
    viewport(zoom, {x: a.cx - zoom * (b.x1 + b.x2) / 2, y: a.cy - zoom * (b.y1 + b.y2) / 2}, true);
    G.userMoved = true;
  }

  // ------------------------------------------------------------------ labels

  // Label sizes follow the zoom; they are set again only when it (or the set of elements) changed, so a new
  // selection only re-culls.
  function sizeLabels() {
    const cy = G.cy, z = cy.zoom();
    if (z !== G.sizedZoom) {
      cy.batch(() => {
        cy.nodes().not(".region").style({"font-size": LABEL_PX / z, "text-margin-y": 2 / z,
                                         "text-outline-width": HALO / z, "text-background-padding": 2 / z});
        cy.nodes(".region").style({"font-size": TITLE_PX / z, "text-margin-y": -4 / z});
      });
      G.sizedZoom = z;
    }
    cull();
  }

  // Zoomed out below the zoom the layout spaced the labels for (or below the first fit), hide each label that
  // overlaps a higher-ranked one or another tag's node; the selection and its neighbours always show. Otherwise
  // every label shows.
  function cull() {
    const cy = G.cy;
    const labelled = cy.nodes().not(".region, .leaving");
    const roomy = G.data && cy.zoom() >= Math.max(G.data.zoom || 1, G.fitZoom || 0) * 0.99;
    if (roomy) {
      cy.batch(() => labelled.removeClass("lbl-off"));
      return;
    }
    const hot = labelled.filter(".hot");
    const rest = labelled.not(".hot").sort((a, b) => a.data("prio") - b.data("prio"));
    const halo = HALO / cy.zoom();
    const area = (n) => {  // the label's text box with its halo (boundingBox() pads labels by several pixels)
      const b = n.boundingBox({includeNodes: false, includeEdges: false, includeLabels: true, includeOverlays: false});
      const r = n._private.rstyle;
      if (r.labelX == null) return b;
      return {x1: r.labelX - r.labelWidth / 2 - halo, x2: r.labelX + r.labelWidth / 2 + halo,
              y1: r.labelY - r.labelHeight / 2 - halo, y2: r.labelY + r.labelHeight / 2 + halo};
    };
    const hits = (a, b) => a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2;
    const kept = hot.map(area);
    const nodes = labelled.map((n) => ({id: n.id(), box: n.boundingBox({includeLabels: false, includeOverlays: false})}));
    cy.batch(() => {
      hot.removeClass("lbl-off");
      rest.forEach((n) => {  // a label also never covers another tag's node
        const b = area(n);
        if (kept.some((k) => hits(k, b)) || nodes.some((o) => o.id !== n.id() && hits(o.box, b))) n.addClass("lbl-off");
        else { kept.push(b); n.removeClass("lbl-off"); }
      });
    });
  }

  // ------------------------------------------------------------------ elements

  function nodeData(n) {
    return {id: n.id, label: n.label, cluster: n.cluster, color: n.color, size: n.size, prio: n.prio, lw: n.lw};
  }

  function fadeIn(el, ms) {
    if (!ms) return;
    const to = parseFloat(el.style("opacity"));  // the stylesheet's opacity for this element
    el.style("opacity", 0);
    el.animate({style: {opacity: to}}, {duration: ms, complete: () => el.removeStyle("opacity")});
  }

  function fadeOut(eles, ms) {
    eles.addClass("leaving");
    if (!ms) { eles.remove(); return; }
    eles.forEach((el) => el.animate({style: {opacity: 0}}, {duration: ms,
      complete: () => { if (el.hasClass("leaving")) el.remove(); }}));
  }

  // Take back an element that was fading out (it came back before it was removed).
  function revive(el) {
    if (el.nonempty() && el.hasClass("leaving")) {
      el.stop(true, false);
      el.removeClass("leaving").removeStyle("opacity");
    }
    return el;
  }

  function sync(data, fresh) {
    G.sizedZoom = null;  // new elements need their label sizes
    const cy = G.cy;
    if (JSON.stringify(data.basis) !== JSON.stringify(G.basis)) {
      G.dragged = {global: {}, separated: {}};
      G.basis = data.basis;
      reportDragged();
    }
    const ms = fresh ? 0 : dur();
    const nodeIds = new Set(data.nodes.map((n) => n.id)), edgeIds = new Set(data.edges.map((e) => e.id));
    cy.batch(() => {
      if (fresh) { cy.elements().stop(true, false); cy.elements().remove(); }
      fadeOut(cy.edges().not(".leaving").filter((e) => !edgeIds.has(e.id())), ms);
      fadeOut(cy.nodes().not(".leaving").filter((n) => !n.hasClass("region") && !nodeIds.has(n.id())), ms);
      fadeOut(cy.nodes(".region").not(".leaving"), ms);
      G.regionSeq = (G.regionSeq || 0) + 1;
      for (const r of data.regions) {
        const added = cy.add({group: "nodes", data: {id: r.id + "~" + G.regionSeq, label: regionTitle(r),
                                                     cluster: r.cluster, count: r.count, color: r.color, w: r.w, h: r.h},
                              position: {x: r.x, y: r.y}, classes: "region", grabbable: false,
                              selectable: false, locked: true, pannable: true});
        fadeIn(added, ms);
      }
      for (const n of data.nodes) {
        const el = revive(cy.getElementById(n.id)), to = at(n.id);
        if (el.nonempty()) {
          el.data(nodeData(n));
          el.classes(n.classes);
          const from = el.position();
          if (Math.abs(from.x - to.x) > 1e-6 || Math.abs(from.y - to.y) > 1e-6) {
            el.stop(true, false);
            if (ms) el.animate({position: to}, {duration: ms, easing: EASE}); else el.position(to);
          }
        } else {
          fadeIn(cy.add({group: "nodes", data: nodeData(n), classes: n.classes, position: to}), ms);
        }
      }
      for (const e of data.edges) {
        const el = revive(cy.getElementById(e.id));
        const edgeData = {shared: e.shared, lift: e.lift, intra: e.intra};
        if (el.nonempty()) { el.data(edgeData); el.classes(e.classes); }
        else {
          // A new link starts in the look of the others (restyle runs right after this batch).
          fadeIn(cy.add({group: "edges", data: Object.assign({id: e.id, source: e.source, target: e.target,
                                                              aw: 0.4, ac: "#8d95a3", ao: 0.18}, edgeData),
                         classes: e.classes}), ms);
        }
      }
    });
  }

  // ------------------------------------------------------------------ Edge Appearance

  // The look of the links (spec: "Edge Appearance"): width, scaling, colour, strength, strength between Clusters
  // and a view-only threshold below which links are not drawn. Drawn here from each edge's raw values (the
  // payload's `shared`, `lift`, `intra`), so no control re-sends the graph; renderer.py `APPEARANCE` holds the
  // defaults, steps and bounds. The look (not the threshold) is kept per browser in a cookie, which ignores the
  // port. It is never part of the Network State, an export or a number.
  const EDGE_COOKIE = "steamstudy_edges";
  const LOOK = ["width", "scale", "color", "strength", "between"];
  const A = {look: null, hideBelow: null, measureKey: null, showShared: false, hidden: 0, config: null, ui: null};

  function readLook() {
    const m = document.cookie.match(new RegExp("(?:^|; )" + EDGE_COOKIE + "=([^;]*)"));
    if (!m) return {};
    try { return JSON.parse(decodeURIComponent(m[1])) || {}; } catch (e) { return {}; }
  }

  function writeLook() {
    const look = {};
    for (const k of LOOK) look[k] = A.look[k];
    document.cookie = `${EDGE_COOKIE}=${encodeURIComponent(JSON.stringify(look))}; path=/; ` +
                      `max-age=${400 * 24 * 3600}; SameSite=Lax`;
  }

  const clamp = (v, [lo, hi]) => Math.min(hi, Math.max(lo, v));

  // A look within the bounds: an unknown or out-of-range value (an old cookie, a bad call) falls back or is clamped.
  function bounded(look) {
    const d = A.config.defaults, lim = A.config.limits, out = {};
    const w = Array.isArray(look.width) && look.width.length === 2 ? look.width.map(Number) : d.width;
    out.width = [clamp(w[0], lim.width_min), clamp(w[1], lim.width_max)];
    if (out.width[1] < out.width[0]) out.width[1] = out.width[0];
    out.scale = ["linear", "sqrt", "log"].includes(look.scale) ? look.scale : d.scale;
    out.color = ["one", "cluster", "within", "value"].includes(look.color) ? look.color : d.color;
    out.strength = clamp(Number.isFinite(look.strength) ? look.strength : d.strength, lim.strength);
    out.between = clamp(Number.isFinite(look.between) ? look.between : d.between, lim.between);
    return out;
  }

  // What width shows: the Clustering Weight, or shared games when the legend's switch asks for them under lift.
  function measure() {
    if (!G.data) return "shared";
    return G.data.weight === "lift" && !A.showShared ? "lift" : "shared";
  }

  function hexRgb(h) { return [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)); }
  function mix(a, b, t) {
    const x = hexRgb(a), y = hexRgb(b);
    return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, "0")).join("");
  }

  // Where a value sits on the drawn scale, 0..1 (also the "by value" colour's position).
  function scaled(v, top, low) {
    if (!(top > 0)) return 0;
    if (A.look.scale === "sqrt") return Math.sqrt(Math.max(v, 0) / top);
    if (A.look.scale === "log") {
      if (!(low > 0) || top <= low) return 1;
      return Math.max(0, Math.log(Math.max(v, low) / low) / Math.log(top / low));
    }
    return v / top;
  }

  // Every drawn link's width, colour, strength and visibility, from the look, in one batch (no layout, no request).
  function restyle() {
    if (!G.cy || !A.config) return;
    const cy = G.cy, key = measure() === "lift" ? "lift" : "shared", c = A.config.colors;
    const edges = cy.edges().not(".leaving");
    const values = edges.map((e) => e.data(key));
    const top = Math.max(0, ...values), low = Math.min(...values.filter((v) => v > 0), Infinity);
    const [w0, w1] = A.look.width, separated = G.data && G.data.layout === "separated";
    let hidden = 0;
    cy.batch(() => {
      edges.forEach((e) => {
        const v = e.data(key), t = scaled(v, top, low), intra = e.data("intra");
        let col = c.one;
        if (A.look.color === "cluster") col = intra ? (e.source().data("color") || c.neutral) : c.neutral;
        else if (A.look.color === "within") col = intra ? c.within : c.between;
        else if (A.look.color === "value") col = mix(c.ramp[0], c.ramp[1], t);
        const hide = A.hideBelow !== null && v < A.hideBelow;
        if (hide) hidden += 1;
        e.data({aw: w0 + (w1 - w0) * t, ac: col, ao: separated && !intra ? A.look.between : A.look.strength});
        if (hide) e.addClass("hid"); else e.removeClass("hid");
      });
    });
    A.hidden = hidden;
  }

  // The card and the tests drive the look through these. A change redraws at once and keeps the look in the cookie;
  // the threshold (`hideBelow`, in the drawn measure's units, null for none) is never kept.
  function setAppearance(partial) {
    if (!A.config) return getAppearance();
    const next = Object.assign({}, A.look);
    for (const k of LOOK) if (partial && k in partial) next[k] = partial[k];
    A.look = bounded(next);
    if (partial && "hideBelow" in partial) A.hideBelow = partial.hideBelow === null ? null : Number(partial.hideBelow);
    if (partial && "showShared" in partial) A.showShared = !!partial.showShared;
    writeLook();
    restyle();
    if (G.selected) applySelection(JSON.parse(G.selected), false);
    renderCard();
    updateKey();
    markHiddenLinks();
    return getAppearance();
  }

  function getAppearance() {
    return Object.assign({}, A.look, {hideBelow: A.hideBelow, showShared: A.showShared, measure: measure(),
                                      hidden: A.hidden, defaults: A.config && A.config.defaults});
  }

  // A new payload: take renderer.py's defaults once, then the browser's own look; the threshold clears when what it
  // is measured in changes (the dataset, or the measure through the Clustering Weight or the switch).
  function adoptAppearance(data) {
    if (!A.config) {
      A.config = data.appearance;
      A.look = bounded(Object.assign({}, A.config.defaults, readLook()));
    }
    const key = JSON.stringify([data.dataset, measure()]);
    if (key !== A.measureKey) { A.hideBelow = null; A.measureKey = key; }
  }

  // The legend's show-shared switch (browser-only: no request) and the key's words, from the ui-words store.
  function edgeKey(switchValue, base, words) {
    A.showShared = !!(switchValue && switchValue.length);
    if (words) A.ui = words;
    if (G.data) { adoptAppearance(G.data); restyle(); renderCard(); markHiddenLinks(); }
    if (G.cy) {  // a language switch re-titles the regions
      G.cy.nodes(".region").forEach((n) => {
        n.data("label", regionTitle({cluster: n.data("cluster"), count: n.data("count"), label: n.data("label")}));
      });
    }
    return keyText();
  }

  // ------------------------------------------------------------------ the Cluster map card

  // One bubble per Cluster (area by tag count) where its tags are drawn now (their centroid in Global, the region's
  // centre in Cluster-separated), nudged apart; the pool as a grey bubble; a line for each pair with a link, 0.6-7.6
  // px by ratio / γ. From the `cluster-connections` store and the positions this file already holds: redrawn in the
  // browser, never a request. A bubble selects its Cluster, a line its pair; any selection lights up here.
  const MAP = {w: 280, h: 190, pad: 18};
  const M = {data: null, open: false};
  try { M.open = window.sessionStorage.getItem("steamstudy_map") === "1"; } catch (e) { M.open = false; }

  function mapData(data, words) {
    M.data = data || null;
    if (words) A.ui = words;
    drawMap();
    return Date.now();
  }

  // Where each group sits on the canvas now, mapped into the card and nudged apart.
  function mapPlaces(groups) {
    const raw = {};
    for (const g of groups) {
      const r = region(g.cluster), nodes = members(g.cluster);
      let p = null;
      if (r.nonempty()) p = r.position();
      else if (nodes.nonempty()) {
        const xs = nodes.map((n) => n.position("x")), ys = nodes.map((n) => n.position("y"));
        p = {x: xs.reduce((a, b) => a + b, 0) / xs.length, y: ys.reduce((a, b) => a + b, 0) / ys.length};
      }
      if (p) raw[g.cluster] = {x: p.x, y: p.y};
    }
    const ids = Object.keys(raw);
    if (!ids.length) return {};
    const xs = ids.map((k) => raw[k].x), ys = ids.map((k) => raw[k].y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const sx = (MAP.w - 2 * MAP.pad) / ((x1 - x0) || 1), sy = (MAP.h - 2 * MAP.pad) / ((y1 - y0) || 1), s = Math.min(sx, sy);
    const out = {};
    for (const k of ids) {
      out[k] = {x: MAP.pad + (raw[k].x - x0) * s + ((MAP.w - 2 * MAP.pad) - (x1 - x0) * s) / 2,
                y: MAP.pad + (raw[k].y - y0) * s + ((MAP.h - 2 * MAP.pad) - (y1 - y0) * s) / 2};
    }
    const radius = Object.fromEntries(groups.map((g) => [g.cluster, g.r]));
    for (let it = 0; it < 40; it++) {  // nudge overlapping bubbles apart
      let moved = false;
      for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
        const a = out[ids[i]], b = out[ids[j]], need = radius[ids[i]] + radius[ids[j]] + 3;
        const dx = b.x - a.x || 0.01, dy = b.y - a.y, d = Math.hypot(dx, dy);
        if (d < need) {
          const push = (need - d) / 2, ux = dx / d, uy = dy / d;
          a.x -= ux * push; a.y -= uy * push; b.x += ux * push; b.y += uy * push; moved = true;
        }
      }
      if (!moved) break;
    }
    for (const k of ids) {
      out[k].x = Math.max(radius[k], Math.min(MAP.w - radius[k], out[k].x));
      out[k].y = Math.max(radius[k], Math.min(MAP.h - radius[k], out[k].y));
    }
    return out;
  }

  // `current`: the selection being drawn (applySelection passes it before it is recorded); else the recorded one.
  function drawMap(current) {
    const body = document.getElementById("cluster-map-body"), card = document.getElementById("cluster-map");
    const toggle = document.getElementById("map-toggle");
    if (card) card.classList.toggle("open", M.open);
    if (toggle) toggle.setAttribute("aria-expanded", String(M.open));
    if (!body || !M.open || !M.data || !G.cy || !A.ui) return;
    const w = A.ui.map, gamma = M.data.gamma || 1;
    const multi = M.data.clusters.filter((c) => c.kind === "multi_tag");
    const poolSize = M.data.clusters.filter((c) => c.kind !== "multi_tag").length;
    const radius = (n) => 3.4 * Math.sqrt(n);  // area by tag count
    const groups = multi.map((c) => ({cluster: c.cluster, size: c.size, r: radius(c.size)}));
    if (poolSize) groups.push({cluster: "one_tag_pool", size: poolSize, r: radius(poolSize)});
    const at = mapPlaces(groups);
    const sel = current !== undefined ? current : (G.selected ? JSON.parse(G.selected) : null);
    const selPair = sel && sel.kind === "pair" ? sel.id : null, selCluster = sel && sel.kind === "cluster" ? sel.id : null;
    const color = (c) => { const n = members(c).first(); return n.nonempty() ? n.data("color") : "#b8b8b8"; };
    let lines = "", labels = "", any = false;
    for (const r of M.data.rows) {
      const a = at[r.cluster_a], b = at[r.cluster_b];
      if (!r.edge_count || !a || !b || r.cluster_a === r.cluster_b) continue;
      any = true;
      const id = `${r.cluster_a}|${r.cluster_b}`, on = id === selPair;
      const lit = on || (selCluster && (r.cluster_a === selCluster || r.cluster_b === selCluster));
      const width = 0.6 + 7 * Math.min(Math.max((r.ratio || 0) / gamma, 0), 1);
      lines += `<line class="map-link" data-pair="${esc(id)}" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" ` +
               `stroke="${on ? "#2457d6" : "#3b2f6b"}" stroke-width="${width.toFixed(2)}" ` +
               `stroke-opacity="${lit || !sel ? 0.85 : 0.25}"><title>${esc(fill(w.ratio, {value: decimal((r.ratio || 0).toFixed(2))}))}</title></line>`;
      if (lit && r.ratio !== null) {
        labels += `<text x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2 - 3}" font-size="10" text-anchor="middle" ` +
                  `class="map-ratio">${esc(decimal(r.ratio.toFixed(2)))}</text>`;
      }
    }
    let bubbles = "";
    for (const g of groups) {
      const p = at[g.cluster];
      if (!p) continue;
      const pool = g.cluster === "one_tag_pool";
      const on = g.cluster === selCluster || (selPair && selPair.split("|").includes(g.cluster));
      const label = pool ? String(g.size) : g.cluster;
      const title = pool ? `${w.pool}: ${fill(w.tags[g.size === 1 ? 0 : 1], {n: g.size})}`
                         : `${g.cluster}: ${fill(w.tags[g.size === 1 ? 0 : 1], {n: g.size})}`;
      bubbles += `<g class="${pool ? "map-pool" : "map-bubble"}"${pool ? "" : ` data-cluster="${esc(g.cluster)}"`}>` +
                 `<circle cx="${p.x}" cy="${p.y}" r="${g.r}" fill="${pool ? "#b8b8b8" : color(g.cluster)}" ` +
                 `stroke="${on ? "#2457d6" : "#fff"}" stroke-width="${on ? 2.5 : 1}"><title>${esc(title)}</title></circle>` +
                 `<text x="${p.x}" y="${p.y + 3}" font-size="9.5" text-anchor="middle" fill="#1b2130">${esc(label)}</text></g>`;
    }
    body.innerHTML = `<svg width="${MAP.w}" height="${MAP.h}" class="map-svg">${lines}${bubbles}${labels}</svg>` +
                     (any ? "" : `<div class="mute small">${esc(w.empty)}</div>`);
  }

  document.addEventListener("click", (ev) => {
    const t = ev.target instanceof Element ? ev.target : null;
    if (!t) return;
    if (t.closest("#map-toggle")) {
      M.open = !M.open;
      try { window.sessionStorage.setItem("steamstudy_map", M.open ? "1" : "0"); } catch (e) { /* session only */ }
      drawMap();
      return;
    }
    const bubble = t.closest("#cluster-map-body [data-cluster]");
    if (bubble) {
      emit({kind: "region", cluster: bubble.dataset.cluster});
      selectNow({kind: "cluster", id: bubble.dataset.cluster});
      return;
    }
    const link = t.closest("#cluster-map-body [data-pair]");
    if (link) {
      emit({kind: "pair", id: link.dataset.pair});
      selectNow({kind: "pair", id: link.dataset.pair});
    }
  });

  // ------------------------------------------------------------------ the Edge appearance card

  // The legend's Edges toggle opens it; a transient overlay (data-graph-transient), so it never changes the canvas,
  // the layout or the fit. Its words come from the ui-words store (layout.py `edge_words`), its numbers in the
  // Interface Language's decimal mark. Every control calls setAppearance: a restyle, no request.
  const HIST = {w: 300, h: 92, pad: 8, base: 66, bins: 24};
  const fill = (word, values) => Object.keys(values).reduce((s, k) => s.split(`{${k}}`).join(values[k]), word || "");
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"})[c]);

  function decimal(text) { return text.replace(".", (A.ui && A.ui.decimal) || "."); }
  function fmtValue(v) { return measure() === "lift" ? decimal(v.toFixed(2)) : String(Math.round(v)); }
  function fmtPx(v) { return decimal(String(+v.toFixed(1))); }
  function fmtPct(v) { return decimal(String(+(v * 100).toFixed(1))) + "%"; }

  function isDefault(key) {
    const d = A.config.defaults;
    return JSON.stringify(A.look[key]) === JSON.stringify(d[key]);
  }

  // The legend's key: what is drawn, then a short summary of a look that is not the default and of hidden links.
  function keyText() {
    const w = (A.ui && A.ui.edges) || {key: "{measure}", shared: "shared games", lift: "lift"};
    let text = fill(w.key, {measure: measure() === "lift" ? w.lift : w.shared});
    if (!A.config) return text;
    const parts = [];
    if (!isDefault("scale")) parts.push(w.scales[A.look.scale]);
    if (!isDefault("width")) parts.push(fill(w.px, {lo: fmtPx(A.look.width[0]), hi: fmtPx(A.look.width[1])}));
    if (!isDefault("color")) parts.push(w.colors[A.look.color]);
    if (!isDefault("strength")) parts.push(fmtPct(A.look.strength));
    if (parts.length) text += ` (${parts.join(", ")})`;
    if (A.hideBelow !== null) text += " · " + fill(w.hidden_short, {n: A.hidden});
    return text;
  }

  function updateKey() {
    if (window.dash_clientside && window.dash_clientside.set_props) {
      window.dash_clientside.set_props("thickness-label", {children: keyText()});
    }
  }

  function cardOpen() {
    const card = document.getElementById("edge-card");
    return !!card && card.classList.contains("open");
  }

  // A control's name with both help layers (its guide paragraph), as workbench.js reads them.
  function term(name) {
    const w = A.ui.edges, h = w.help[name];
    return `<span class="term" tabindex="0" data-tip="${esc(h.tip)}" data-help="${esc(h.help)}">${esc(w[name])}</span>`;
  }

  function stepper(name, value) {
    const w = A.ui.edges, title = esc(`${w[name]}: ${value}`);
    return `<span class="ea-step">${term(name)} <button data-act="${name}-" title="${title}" aria-label="${esc(w.less)}">−</button>` +
           `<button data-act="${name}+" title="${title}" aria-label="${esc(w.more)}">+</button></span>`;
  }

  function choices(name, options, current) {
    return `<span class="ea-choice">${term(name)} ` + options.map(([v, label]) =>
      `<button data-act="${name}=${v}" class="${v === current ? "on" : ""}">${esc(label)}</button>`).join("") + "</span>";
  }

  function renderCard() {
    const body = document.getElementById("edge-card-body");
    if (!body || !cardOpen() || !G.cy || !A.config || !A.ui) return;
    const w = A.ui.edges, key = measure() === "lift" ? "lift" : "shared";
    const vals = G.cy.edges().not(".leaving").map((e) => e.data(key));
    if (!vals.length) { body.innerHTML = ""; return; }
    const lo = Math.min(...vals), hi = Math.max(...vals), low = Math.min(...vals.filter((v) => v > 0), Infinity);
    const {w: W, pad, base, bins} = HIST, span = hi - lo || 1;
    const xOf = (v) => pad + (v - lo) / span * (W - 2 * pad);
    const counts = new Array(bins).fill(0);
    for (const v of vals) counts[Math.min(bins - 1, Math.floor((v - lo) / span * bins))] += 1;
    const cmax = Math.max(...counts), bw = (W - 2 * pad) / bins, cut = A.hideBelow === null ? lo : A.hideBelow;
    const bars = counts.map((c, i) => {
      const off = A.hideBelow !== null && lo + (i + 1) / bins * span <= A.hideBelow;
      return `<rect x="${pad + i * bw + 0.5}" y="${base - c / cmax * 30}" width="${Math.max(bw - 1, 0.5)}" ` +
             `height="${c / cmax * 30}" fill="${off ? "#e5e7eb" : "#cbd5e1"}"/>`;
    }).join("");
    // The drawn width along the values: a band as thick as the link (×1.5 for legibility).
    const [w0, w1] = A.look.width, pts = [];
    for (let i = 0; i <= 40; i++) { const v = lo + i / 40 * span; pts.push([xOf(v), w0 + (w1 - w0) * scaled(v, hi, low)]); }
    const band = pts.map(([x, t]) => `${x},${16 - t * 1.5}`).concat(pts.slice().reverse().map(([x, t]) => `${x},${16 + t * 1.5}`)).join(" ");
    const colors = A.config.colors, ramp = A.look.color === "value";
    const svg = `<svg id="edge-hist" width="${W}" height="${HIST.h}" style="cursor:ew-resize">` +
      `<defs><linearGradient id="ea-ramp"><stop offset="0" stop-color="${colors.ramp[0]}"/><stop offset="1" stop-color="${colors.ramp[1]}"/></linearGradient></defs>` +
      `<polygon points="${band}" fill="${ramp ? "url(#ea-ramp)" : colors.one}" opacity="${Math.min(1, A.look.strength * 2.6)}"/>` +
      `<text x="${pad}" y="34" font-size="10" fill="#6b7280">${fmtPx(w0)} px</text>` +
      `<text x="${W - pad}" y="34" font-size="10" fill="#6b7280" text-anchor="end">${fmtPx(w1)} px</text>${bars}` +
      `<line x1="${pad}" y1="${base}" x2="${W - pad}" y2="${base}" stroke="#9aa1ad"/>` +
      (A.hideBelow !== null ? `<rect x="${pad}" y="10" width="${Math.max(0, xOf(cut) - pad)}" height="${base - 10}" fill="#fff" opacity="0.55"/>` : "") +
      `<line x1="${xOf(cut)}" y1="8" x2="${xOf(cut)}" y2="${base + 4}" stroke="${A.hideBelow === null ? "#c0c6d0" : "#2457d6"}" stroke-width="2"/>` +
      `<rect x="${xOf(cut) - 5}" y="${base - 2}" width="10" height="12" rx="2" fill="${A.hideBelow === null ? "#fff" : "#2457d6"}" stroke="#2457d6"/>` +
      `<text x="${pad}" y="${HIST.h - 4}" font-size="10" fill="#6b7280">${fmtValue(lo)}</text>` +
      `<text x="${W / 2}" y="${HIST.h - 4}" font-size="10" fill="#6b7280" text-anchor="middle">${esc(fill(w.axis, {measure: w[key], n: vals.length}))}</text>` +
      `<text x="${W - pad}" y="${HIST.h - 4}" font-size="10" fill="#6b7280" text-anchor="end">${fmtValue(hi)}</text></svg>`;
    const separated = G.data && G.data.layout === "separated";
    body.innerHTML = svg +
      `<div class="ea-line">${term("hide")}: ${esc(fill(w.hidden[A.hidden === 1 ? 0 : 1], {n: A.hidden}))}. ` +
      `${esc(fill(w.filter, {n: G.data && G.data.min_shared != null ? G.data.min_shared : "…"}))}</div>` +
      `<div class="ea-line mute">${esc(w.drag)}</div>` +
      `<div class="ea-row">${stepper("width", fill(w.px, {lo: fmtPx(w0), hi: fmtPx(w1)}))}` +
      `${stepper("strength", fmtPct(A.look.strength))}` +
      (separated ? stepper("between", fmtPct(A.look.between)) : "") + `</div>` +
      `<div class="ea-row">${choices("scale", ["linear", "sqrt", "log"].map((s) => [s, w.scales[s]]), A.look.scale)}</div>` +
      `<div class="ea-row">${choices("color", ["one", "cluster", "within", "value"].map((c) => [c, w.colors[c]]), A.look.color)}</div>`;
    body.dataset.lo = lo; body.dataset.hi = hi;
  }

  // The steppers: width by both ends, the strengths by a factor, within renderer.py's bounds (setAppearance clamps).
  function act(name) {
    const s = A.config.steps, look = A.look;
    const [k, op] = name.endsWith("+") || name.endsWith("-") ? [name.slice(0, -1), name.slice(-1)] : name.split("=");
    if (op === "+" || op === "-") {
      const f = k === "width" ? s.width : s[k], m = op === "+" ? f : 1 / f;
      if (k === "width") return setAppearance({width: look.width.map((x) => +(x * m).toFixed(3))});
      return setAppearance({[k]: +Math.max(k === "between" && op === "+" ? 0.02 : 0, look[k] * m).toFixed(4)});
    }
    return setAppearance({[k]: op});
  }

  function dragTo(ev) {
    const body = document.getElementById("edge-card-body"), svg = document.getElementById("edge-hist");
    if (!svg) return;
    const lo = +body.dataset.lo, hi = +body.dataset.hi, r = svg.getBoundingClientRect();
    const x = Math.max(HIST.pad, Math.min(HIST.w - HIST.pad, ev.clientX - r.left));
    let v = lo + (x - HIST.pad) / (HIST.w - 2 * HIST.pad) * (hi - lo);
    v = measure() === "lift" ? Math.round(v * 20) / 20 : Math.round(v);
    setAppearance({hideBelow: v <= lo ? null : v});
  }

  document.addEventListener("click", (ev) => {
    const t = ev.target instanceof Element ? ev.target : null;
    if (!t) return;
    const toggle = t.closest("#edge-card-toggle");
    if (toggle) {
      const card = document.getElementById("edge-card");
      card.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(card.classList.contains("open")));
      renderCard();
      return;
    }
    if (t.closest("#edge-card-reset") && A.config) {
      setAppearance(Object.assign({}, A.config.defaults, {hideBelow: null}));
      return;
    }
    const btn = t.closest("#edge-card-body button[data-act]");
    if (btn && A.config) act(btn.dataset.act);
  });
  document.addEventListener("pointerdown", (ev) => {
    const svg = ev.target instanceof Element && ev.target.closest("#edge-hist");
    if (!svg) return;
    ev.preventDefault();
    dragTo(ev);
    const move = (e) => dragTo(e), up = () => {
      window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  });
  document.addEventListener("keydown", (ev) => {
    const card = document.getElementById("edge-card");
    if (ev.key === "Escape" && card && card.classList.contains("open")) {
      card.classList.remove("open");
      const toggle = document.getElementById("edge-card-toggle");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }
  });


  // A region's title in the Interface Language: "C1 · 26 tags" (ui-words `map.tags`), the pool's from
  // `map.pool_region`; the label as sent until the words arrive.
  function regionTitle(r) {
    const map = A.ui && A.ui.map;
    if (!map || !map.tags || !map.pool_region || r.count === undefined) return r.label;
    const count = (forms) => fill(forms[r.count === 1 ? 0 : 1], {n: r.count});
    return r.cluster === "one_tag_pool" ? count(map.pool_region) : r.cluster + " · " + count(map.tags);
  }

  // Region ids carry a sequence suffix so a fading old region and its replacement can coexist.
  function region(cluster) {
    return G.cy.nodes(".region").not(".leaving").filter((r) => r.data("cluster") === cluster);
  }

  function members(cluster) {
    // "one_tag_pool" (a pair's group) is every One-Tag Cluster's tag
    if (cluster === "one_tag_pool") return G.cy.nodes(".one_tag").not(".region, .leaving");
    return G.cy.nodes().not(".region, .leaving").filter((n) => n.data("cluster") === cluster);
  }

  // A pair's two groups and the drawn links between them (the pool with itself: links between two pool tags).
  function pairParts(id) {
    const [a, b] = String(id).split("|"), ma = members(a), mb = members(b);
    const links = a === b ? ma.edgesWith(ma).filter((e) => e.source().data("cluster") !== e.target().data("cluster"))
                          : ma.edgesWith(mb);
    return {a, b, nodes: ma.union(mb), links: links.not(".hid, .leaving")};
  }

  // ------------------------------------------------------------------ selection and view

  // A tag dims all but its closed neighbourhood (and rings once), an edge all but itself and its two tags,
  // a cluster all but its members.
  function applySelection(sel, changed) {
    const cy = G.cy;
    let ringed = null;
    const dark = !A.look || A.look.color === "one";
    cy.batch(() => {
      cy.elements().removeClass("sel hot dim nb nbdark");
      if (!sel) return;
      let keep = cy.collection();
      if (sel.kind === "node" || sel.kind === "edge") {
        const el = cy.getElementById(sel.id);
        if (el.empty() || el.hasClass("leaving")) return;
        el.addClass("sel");
        if (el.isNode()) {
          // Links hidden from the drawing are left out of the neighbourhood (they still count everywhere else).
          const links = el.connectedEdges().not(".hid");
          keep = el.union(links).union(links.connectedNodes());
          links.addClass(dark ? "nb nbdark" : "nb");
          ringed = el;
        } else {
          keep = el.union(el.connectedNodes());
        }
      } else if (sel.kind === "cluster") {
        keep = members(sel.id);
        keep = keep.union(keep.edgesWith(keep));
      } else if (sel.kind === "pair") {
        // Both groups and the links between them, opaque in their colour mode (darker under one colour), in both
        // layouts; links hidden from the drawing stay hidden.
        const p = pairParts(sel.id);
        p.links.addClass(dark ? "nb nbdark" : "nb");
        keep = p.nodes.union(p.links);
      }
      keep.nodes().addClass("hot");
      cy.elements().not(keep).not(".region, .leaving").addClass("dim");
    });
    sizeLabels();
    markMatrix(sel);
    drawMap(sel || null);
    if (ringed && changed && dur()) ring(ringed);
  }

  // The Connections matrix shows the selection too: the selected pair's cells, or the selected Cluster's row and
  // column (and the pair's two rows and columns).
  function markMatrix(sel) {
    const root = document.querySelector("#quality-detail .cm");
    if (!root) return;
    root.querySelectorAll(".cm-sel, .cm-hl").forEach((el) => el.classList.remove("cm-sel", "cm-hl"));
    if (!sel) return;
    const groups = sel.kind === "cluster" ? [sel.id] : sel.kind === "pair" ? String(sel.id).split("|") : [];
    for (const g of groups) {
      root.querySelectorAll(`[data-row="${CSS.escape(g)}"], [data-col="${CSS.escape(g)}"]`)
        .forEach((el) => el.classList.add("cm-hl"));
    }
    if (sel.kind === "pair") {
      root.querySelectorAll(`td[data-pair="${CSS.escape(String(sel.id))}"]`).forEach((el) => el.classList.add("cm-sel"));
    }
  }
  // A new matrix (a recompute) shows the selection that is already drawn.
  function watchMatrix() {
    const quality = document.getElementById("quality-detail");
    if (!quality) { setTimeout(watchMatrix, 50); return; }
    new MutationObserver(() => {
      const root = quality.querySelector(".cm");
      if (root && root.dataset.marked !== G.selected) {
        root.dataset.marked = G.selected;
        markMatrix(G.selected ? JSON.parse(G.selected) : null);
      }
    }).observe(quality, {childList: true, subtree: true});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", watchMatrix);
  else watchMatrix();

  // The selected tag's ring: a DOM element over the canvas that only CSS animates (transform and opacity), so the
  // compositor runs it smoothly even while Dash applies the Inspector, and the canvas never redraws for it.
  function ring(node) {
    dropRing();
    const p = node.renderedPosition(), d = node.renderedOuterWidth();
    const el = document.createElement("div");
    el.className = "sel-ring";
    el.style.cssText = `left:${G.el.offsetLeft + p.x - d / 2}px;top:${G.el.offsetTop + p.y - d / 2}px;` +
                       `width:${d}px;height:${d}px`;
    el.addEventListener("animationend", dropRing);
    G.el.parentElement.appendChild(el);
    G.ring = el;
  }

  function dropRing() {
    if (G.ring) { G.ring.remove(); G.ring = null; }
  }

  // Zoom to a cluster: its region in Cluster-separated mode, its members' bounding box in Global.
  function focusCluster(cluster) {
    const r = region(cluster);
    const eles = r.nonempty() ? r : members(cluster);
    if (eles.empty()) return;
    const b = eles.boundingBox({includeLabels: false, includeOverlays: false});
    fitBox({x1: b.x1, x2: b.x2, y1: b.y1 - (r.nonempty() ? TITLE_ROOM : 0), y2: b.y2 + LABEL_MARGIN + LABEL_H}, true);
    G.userMoved = true;  // a resize (e.g. the floating Inspector opening) keeps the focus
  }

  // Fit to both groups of a pair (their regions in Cluster-separated mode), like a Cluster's focus.
  function focusPair(a, b) {
    let eles = G.cy.collection();
    for (const g of [a, b]) { const r = region(g); eles = eles.union(r.nonempty() ? r : members(g)); }
    if (eles.empty()) return;
    const bb = eles.boundingBox({includeLabels: false, includeOverlays: false});
    fitBox({x1: bb.x1, x2: bb.x2, y1: bb.y1 - TITLE_ROOM, y2: bb.y2 + LABEL_MARGIN + LABEL_H}, true);
    G.userMoved = true;
  }

  function runView(view) {
    if (!view || view.nonce === G.viewNonce) return;
    G.viewNonce = view.nonce;
    whenDashIdle(() => {
      if (view.cmd === "fit") { G.userMoved = false; fit(true); }
      else if (view.cmd === "focus") focusCluster(view.cluster);
      else if (view.cmd === "focus_pair") focusPair(view.a, view.b);
      else if (view.cmd === "center") {
        const el = G.cy.getElementById(view.id);
        centerOn(el.nonempty() && el.isEdge() ? el.union(el.connectedNodes()) : el);
      }
    });
  }

  // A view command arrives with the first answer to a selection, while Dash still applies the others (the
  // Inspector, its form) and then tidies its callback records. Every Dash update makes each of the page's few
  // hundred components re-check its props, which took most of an animated zoom's frames on a slower machine; so
  // the zoom starts once Dash is idle and has made no update for DASH_QUIET ms (`window.store` is the Dash
  // renderer's store; without it, at once). A newer command replaces a waiting one.
  function whenDashIdle(run) {
    if (G.idleCancel) G.idleCancel();
    const store = window.store;
    if (!store || !store.getState || !store.subscribe) { run(); return; }
    let quiet = null;
    const stop = () => { unsubscribe(); clearTimeout(quiet); clearTimeout(cap); G.idleCancel = null; };
    const go = () => { stop(); requestAnimationFrame(run); };
    const settle = () => { clearTimeout(quiet); if (!store.getState().isLoading) quiet = setTimeout(go, DASH_QUIET); };
    const unsubscribe = store.subscribe(settle);
    const cap = setTimeout(go, 1000);  // never wait long
    G.idleCancel = stop;
    settle();
  }

  function render(data) {
    const noUpdate = window.dash_clientside.no_update;
    const el = document.getElementById("cy");
    if (!data || !data.nodes || !el) return noUpdate;
    if (!G.cy || G.el !== el) {
      if (G.cy) G.cy.destroy();
      G.el = el; G.cy = mount(el); G.data = null; G.sig = null; G.moveSig = null; G.local = [];
    }
    if (!G.canvas) reportCanvas(); else scheduleReport();
    const prev = G.data;
    G.data = data;
    const moveSig = JSON.stringify([data.layout, data.positions, data.regions]);
    const sig = JSON.stringify([data.dataset, data.nodes, data.edges, moveSig]);
    const elementsChanged = sig !== G.sig;
    adoptAppearance(data);
    if (elementsChanged) {
      const fresh = !prev || prev.dataset !== data.dataset, moved = moveSig !== G.moveSig;
      sync(data, fresh);
      restyle();
      renderCard();
      updateKey();  // the summary follows a cleared threshold and a new hidden count
      // the map follows the bubbles' new places once the nodes have moved
      clearTimeout(G.mapTimer);
      G.mapTimer = setTimeout(() => drawMap(), dur() + 30);
      if (fresh || moved) G.userMoved = false;
      if (!G.userMoved) fit(!!prev);  // the move and the fit run together; a new dataset only fits
      G.sig = sig; G.moveSig = moveSig;
    }
    // The answer for a selection already drawn at the tap changes nothing: re-applying it would only take main
    // thread time while the selection ring is still running.
    const selSig = JSON.stringify(data.selected);
    if (!staleAnswer(selSig) && (selSig !== G.selected || elementsChanged)) {
      applySelection(data.selected, selSig !== G.selected);
      G.selected = selSig;
    }
    runView(data.view);
    return Date.now();
  }

  // ------------------------------------------------------------------ instant selection

  // Draw a tapped selection at once, before the server answers, and mark the Inspector as waiting for it.
  function selectNow(ref) {
    const sig = JSON.stringify(ref);
    G.local = (G.local || []).concat([sig]).slice(-8);  // drawn here, not yet confirmed by the server
    if (sig === G.selected) return;
    applySelection(ref, true);  // at once: drawing later only competes with Dash handling the answers
    G.selected = sig;
    inspectorWaiting(ref !== null);
  }

  // The server answers taps in order. An answer for an earlier tap than the last one drawn here is stale: drop
  // it (and everything before it) instead of flashing back to it. Any other answer stands.
  function staleAnswer(sig) {
    const local = G.local || [], i = local.lastIndexOf(sig);
    if (i < 0) { G.local = []; return false; }
    G.local = local.slice(i + 1);
    return i < local.length - 1;
  }

  // Until the Inspector's new content arrives, app.css fades the old one slightly (after 60 ms, so a quick answer
  // never flickers) and opens a floating card at once. Any change of its content ends the wait.
  function inspectorWaiting(on) {
    const panel = document.getElementById("inspector-panel"), body = document.getElementById("inspector-body");
    if (!panel || !body) return;
    clearTimeout(G.waitTimer);
    if (!on) { delete panel.dataset.pending; return; }
    panel.dataset.pending = "1";
    if (!G.waitObserver) {
      G.waitObserver = new MutationObserver(() => {
        if (!panel.dataset.pending) return;
        delete panel.dataset.pending;
        clearTimeout(G.waitTimer);
        // Now the main thread is free: show the selected tag if the (possibly already open) card covers it.
        G.revealLater = false;
        setTimeout(revealSelection, 0);
      });
      G.waitObserver.observe(body, {childList: true, subtree: true, characterData: true});
    }
    G.waitTimer = setTimeout(() => {  // never wait visibly for long
      delete panel.dataset.pending;
      if (G.revealLater) { G.revealLater = false; revealSelection(); }
    }, 3000);
  }

  // A row of the Inspector's connected tags (one HTML block, see view.py) selects its link, like a tap on it.
  function selectLink(ev) {
    const row = ev.target.closest && ev.target.closest("#inspector-body tr[data-edge]");
    if (!row || (ev.type === "keydown" && ev.key !== "Enter" && ev.key !== " ")) return;
    if (ev.type === "keydown") ev.preventDefault();
    const [source, target] = row.dataset.edge.split("-");
    const event = {kind: "edge", id: row.dataset.edge, source, target, pan: true};
    if (row.dataset.fromPair) event.from_pair = row.dataset.fromPair;
    emit(event);
    selectNow({kind: "edge", id: row.dataset.edge});
  }
  document.addEventListener("click", selectLink);
  document.addEventListener("keydown", selectLink);

  // A pair from the Inspector (a Connections row, "show this pair", "← C1 ↔ C2"): drawn at once, like a tap.
  function selectPair(ev) {
    const cluster = ev.target.closest && ev.target.closest("#quality-detail [data-cluster]");
    if (cluster && (ev.type !== "keydown" || ev.key === "Enter" || ev.key === " ")) {  // a matrix row header
      if (ev.type === "keydown") ev.preventDefault();
      emit({kind: "region", cluster: cluster.dataset.cluster});
      selectNow({kind: "cluster", id: cluster.dataset.cluster});
      return;
    }
    const el = ev.target.closest && ev.target.closest("#inspector-body [data-pair], #quality-detail [data-pair]");
    if (!el || (ev.type === "keydown" && ev.key !== "Enter" && ev.key !== " ")) return;
    if (ev.type === "keydown") ev.preventDefault();
    emit({kind: "pair", id: el.dataset.pair});
    selectNow({kind: "pair", id: el.dataset.pair});
  }
  document.addEventListener("click", selectPair);
  document.addEventListener("keydown", selectPair);

  // In a pair's list of links, mark the ones hidden from the drawing (Hide links below: a browser-only choice).
  function markHiddenLinks() {
    const body = document.getElementById("inspector-body");
    if (!body || !G.cy) return;
    const word = (A.ui && A.ui.edges && A.ui.edges.hidden_link) || "";
    body.querySelectorAll("tr[data-from-pair][data-edge]").forEach((row) => {
      const hidden = G.cy.getElementById(row.dataset.edge).hasClass("hid");
      const cell = row.cells[0], mark = cell.querySelector(".hid-mark");
      // Only real changes are written: the observer below would otherwise see its own writes.
      if (hidden === row.classList.contains("hidden-link") && (!mark || mark.textContent === word)) return;
      row.classList.toggle("hidden-link", hidden);
      if (hidden && !mark) cell.insertAdjacentHTML("beforeend", ` <small class="hid-mark mute">${esc(word)}</small>`);
      else if (hidden && mark.textContent !== word) mark.textContent = word;  // the words arrived (or changed language)
      if (!hidden && mark) mark.remove();
    });
  }

  // A pair's list arrives as an escaped HTML block (workbench.js fills it): mark it once it is in place.
  function watchPairLinks() {
    const body = document.getElementById("inspector-body");
    if (!body) { setTimeout(watchPairLinks, 50); return; }
    new MutationObserver(() => markHiddenLinks()).observe(body, {childList: true, subtree: true});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", watchPairLinks);
  else watchPairLinks();

  // A cluster's legend chip (Dash id {"type": "legend", "cluster": <label>}) is drawn at once too, like a tap on its
  // region title; Dash still sends the click, and the server's answer confirms it.
  function selectLegendChip(ev) {
    const chip = ev.target.closest && ev.target.closest("#legend button.lchip");
    if (!chip || !G.cy) return;
    let id;
    try { id = JSON.parse(chip.id); } catch (e) { return; }
    if (id && id.type === "legend" && id.cluster) selectNow({kind: "cluster", id: id.cluster});
  }
  document.addEventListener("click", selectLegendChip);

  window.dash_clientside = Object.assign({}, window.dash_clientside, {tagGraph: {render, edgeKey, mapData}});
  window.tagGraph = G;  // for inspection in the browser console and browser checks
  G.setAppearance = setAppearance;  // for the Edge appearance card and browser checks
  G.getAppearance = getAppearance;
})();
