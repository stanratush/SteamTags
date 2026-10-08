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
      {selector: "edge", style: {
        "curve-style": "haystack", "haystack-radius": 0, "line-color": "#8d95a3", "opacity": 0.18,
        "width": "data(width)", "z-index-compare": "manual", "z-index": 5}},
      {selector: "edge.inter.separated", style: {"opacity": 0.06}},
      {selector: "node.dim", style: {"opacity": 0.12}},
      {selector: "edge.dim", style: {"opacity": 0.04}},
      {selector: "edge.nb", style: {"line-color": "#4a5262", "opacity": 0.9}},
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
        const added = cy.add({group: "nodes", data: {id: r.id + "~" + G.regionSeq, label: r.label, cluster: r.cluster,
                                                     color: r.color, w: r.w, h: r.h},
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
        if (el.nonempty()) { el.data("width", e.width); el.classes(e.classes); }
        else {
          fadeIn(cy.add({group: "edges", data: {id: e.id, source: e.source, target: e.target, width: e.width},
                         classes: e.classes}), ms);
        }
      }
    });
  }

  // Region ids carry a sequence suffix so a fading old region and its replacement can coexist.
  function region(cluster) {
    return G.cy.nodes(".region").not(".leaving").filter((r) => r.data("cluster") === cluster);
  }

  function members(cluster) {
    return G.cy.nodes().not(".region, .leaving").filter((n) => n.data("cluster") === cluster);
  }

  // ------------------------------------------------------------------ selection and view

  // A tag dims all but its closed neighbourhood (and rings once), an edge all but itself and its two tags,
  // a cluster all but its members.
  function applySelection(sel, changed) {
    const cy = G.cy;
    let ringed = null;
    cy.batch(() => {
      cy.elements().removeClass("sel hot dim nb");
      if (!sel) return;
      let keep = cy.collection();
      if (sel.kind === "node" || sel.kind === "edge") {
        const el = cy.getElementById(sel.id);
        if (el.empty() || el.hasClass("leaving")) return;
        el.addClass("sel");
        if (el.isNode()) {
          keep = el.closedNeighborhood();
          el.connectedEdges().addClass("nb");
          ringed = el;
        } else {
          keep = el.union(el.connectedNodes());
        }
      } else if (sel.kind === "cluster") {
        keep = members(sel.id);
        keep = keep.union(keep.edgesWith(keep));
      }
      keep.nodes().addClass("hot");
      cy.elements().not(keep).not(".region, .leaving").addClass("dim");
    });
    sizeLabels();
    if (ringed && changed && dur()) ring(ringed);
  }

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

  function runView(view) {
    if (!view || view.nonce === G.viewNonce) return;
    G.viewNonce = view.nonce;
    if (view.cmd === "fit") { G.userMoved = false; fit(true); }
    else if (view.cmd === "focus") focusCluster(view.cluster);
    else if (view.cmd === "center") {
      const el = G.cy.getElementById(view.id);
      centerOn(el.nonempty() && el.isEdge() ? el.union(el.connectedNodes()) : el);
    }
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
    if (elementsChanged) {
      const fresh = !prev || prev.dataset !== data.dataset, moved = moveSig !== G.moveSig;
      sync(data, fresh);
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
    emit({kind: "edge", id: row.dataset.edge, source, target, pan: true});
    selectNow({kind: "edge", id: row.dataset.edge});
  }
  document.addEventListener("click", selectLink);
  document.addEventListener("keydown", selectLink);

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

  window.dash_clientside = Object.assign({}, window.dash_clientside, {tagGraph: {render}});
  window.tagGraph = G;  // for inspection in the browser console and browser checks
})();
