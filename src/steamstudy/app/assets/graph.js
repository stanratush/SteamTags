/* The renderer boundary, browser half (the Python half is renderer.py).

   Owns the Cytoscape.js instance (vendored cytoscape.min.js, never a CDN). Dash sends one store,
   `graph-data`: elements, target positions, regions, the selection and view commands. Taps on a node,
   an edge, a region title or the background come back on the `graph-event` store through
   dash_clientside.set_props.

   The canvas follows its container (a ResizeObserver), and the view refits until the user zooms or
   pans. Every fit targets where the nodes end up, and leaves room for the overlays drawn over the
   canvas (elements marked data-graph-overlay="top|right|bottom|left", e.g. the floating Inspector). At
   render time x is stretched by the canvas aspect ratio (at most 1.6x) so the first fit fills a wide
   canvas; exported coordinates are untouched.

   Labels: priority labels (classes `pri` from Python, `hot` for the selection and its neighbours) keep a
   constant on-screen size; after every zoom one that overlaps a higher-ranked one is hidden (rank: `hot`,
   then the `prio` sent by Python: Centers, then n_games). Other labels scale with zoom and hide below 7 px.

   Motion is brief and never continuous: moves, fades, the selection pulse and animated fits take about
   350 ms, and all of it is instant under prefers-reduced-motion. A new dataset only fits (animated).
   Dragged positions are view-only: kept while the layout basis is the same and the layout has not moved
   that node, never sent back.
*/
(function () {
  "use strict";
  const PAD = 30, MAX_STRETCH = 1.6, LABEL_ROOM = 14, TITLE_ROOM = 22;
  const PRI_PX = 11.5, TITLE_PX = 12.5;  // constant on-screen sizes of priority labels and region titles
  const SIZED = "font-size text-margin-y text-background-padding";
  const MOTION = 350, EASE = "ease-in-out-cubic";
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const G = {cy: null, el: null, data: null, sig: null, moveSig: null, stretch: 1, userMoved: false,
             quietUntil: 0, viewNonce: null, labelFrame: 0, selected: null, basis: null,
             dragged: {global: {}, separated: {}}};

  function dur() { return reduced.matches ? 0 : MOTION; }

  function style() {
    return [
      {selector: "node", style: {
        "background-color": "data(color)", "label": "data(label)", "font-size": 6.5, "min-zoomed-font-size": 7,
        "font-family": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", "color": "#1b2130",
        "text-valign": "bottom", "text-margin-y": 2, "text-outline-color": "#fff", "text-outline-width": 1.2,
        "text-outline-opacity": 0.9, "width": "data(size)", "height": "data(size)", "border-width": 1.2,
        "border-color": "#00000040", "z-index-compare": "manual", "z-index": 10}},
      {selector: "node.pri, node.hot", style: {
        "min-zoomed-font-size": 0, "font-weight": 500, "text-outline-width": 0, "text-background-color": "#fff", "z-index": 15,
        "text-background-opacity": 0.85, "text-background-padding": 2, "text-background-shape": "round-rectangle"}},
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
        "curve-style": "haystack", "haystack-radius": 0, "line-color": "#8d95a3", "opacity": 0.3,
        "width": "data(width)", "z-index-compare": "manual", "z-index": 5}},
      {selector: "edge.inter.separated", style: {"opacity": 0.06}},
      {selector: "node.dim", style: {"opacity": 0.12}},
      {selector: "edge.dim", style: {"opacity": 0.04}},
      {selector: "edge.nb", style: {"opacity": 0.6}},
      {selector: "node.sel", style: {"border-width": 3, "border-color": "#2457d6", "z-index": 30}},
      {selector: "edge.sel", style: {"line-color": "#2457d6", "opacity": 0.95}},
      {selector: "node.lbl-off", style: {"text-opacity": 0, "text-background-opacity": 0}},
      // Colour changes and dimming cross-fade (off under reduced motion, see transitions()).
      {selector: "node, edge", style: {"transition-property": "background-color, line-color, opacity",
                                       "transition-duration": 0, "transition-timing-function": "ease-in-out"}},
    ];
  }

  // Style transitions follow prefers-reduced-motion, also when it changes while the page is open.
  function transitions() {
    if (G.cy && G.transition !== dur()) {
      G.transition = dur();
      G.cy.style().selector("node, edge").style("transition-duration", G.transition / 1000).update();
    }
  }
  reduced.addEventListener("change", transitions);

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
      if (n.hasClass("leaving")) return;
      if (!n.hasClass("region")) emit({kind: "node", id: n.id()});
      else if (onTitle(n, ev.position)) emit({kind: "region", cluster: n.data("cluster")});
      else emit({kind: "background"});  // only a region's title is clickable
    });
    cy.on("tap", "edge", (ev) => {
      const e = ev.target;
      if (!e.hasClass("leaving")) emit({kind: "edge", id: e.id(), source: e.data("source"), target: e.data("target")});
    });
    cy.on("tap", (ev) => { if (ev.target === cy) emit({kind: "background"}); });
    cy.on("dragfree", "node", (ev) => {  // a dragged position, kept in unstretched units
      const n = ev.target, target = G.data && G.data.positions[n.id()];
      if (!target || n.hasClass("region")) return;
      G.dragged[G.data.layout][n.id()] = {x: n.position("x") / G.stretch, y: n.position("y"), target};
    });
    cy.on("viewport", () => { if (performance.now() > G.quietUntil) G.userMoved = true; });
    cy.on("zoom", () => {  // re-size and re-cull the labels once per frame
      if (!G.labelFrame) G.labelFrame = requestAnimationFrame(() => { G.labelFrame = 0; sizeLabels(); });
    });
    const ro = new ResizeObserver(() => {
      cy.resize();
      if (G.data && !G.userMoved) { place(); fit(false); }
    });
    ro.observe(el);
    document.querySelectorAll("[data-graph-overlay]").forEach((o) => ro.observe(o));
    return cy;
  }

  // ------------------------------------------------------------------ geometry

  // The canvas area left free by the overlays that cover it, as insets from each side.
  function insets() {
    const c = G.el.getBoundingClientRect(), pad = {top: PAD, right: PAD, bottom: PAD, left: PAD};
    for (const o of document.querySelectorAll("[data-graph-overlay]")) {
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

  // Where a node ends up, unstretched: its dragged position while the layout has not moved it, else its target.
  function spot(data, id) {
    const target = data.positions[id];
    const drag = G.dragged[data.layout][id];
    if (drag && target && drag.target[0] === target[0] && drag.target[1] === target[1]) return [drag.x, drag.y];
    return target;
  }

  function box(data, stretch) {
    let x1 = Infinity, x2 = -Infinity, y1 = Infinity, y2 = -Infinity;
    for (const n of data.nodes) {
      const p = spot(data, n.id);
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
    if (!G.cy.width() || !G.cy.height()) return 1;
    const a = freeArea(), bb = box(data, 1);
    const want = (a.w / a.h) / (Math.max(bb.x2 - bb.x1, 1) / Math.max(bb.y2 - bb.y1, 1));
    return Math.max(1, Math.min(MAX_STRETCH, want));
  }

  function at(id) {
    const p = spot(G.data, id) || [0, 0];
    return {x: p[0] * G.stretch, y: p[1]};
  }

  function viewport(zoom, pan, animate) {
    const ms = animate ? dur() : 0;
    quiet(ms);
    G.cy.stop(true, false);
    if (ms) G.cy.animate({zoom, pan}, {duration: ms, easing: EASE});
    else G.cy.viewport({zoom, pan});
  }

  function fit(animate) {
    if (G.data) fitBox(box(G.data, G.stretch), animate);
  }

  function fitBox(bb, animate) {
    const cy = G.cy, w = cy.width(), h = cy.height();
    if (!w || !h) return;
    const a = freeArea();
    const bw = Math.max(bb.x2 - bb.x1, 1), bh = Math.max(bb.y2 - bb.y1, 1);
    const zoom = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), Math.min(a.w / bw, a.h / bh)));
    viewport(zoom, {x: a.cx - zoom * (bb.x1 + bb.x2) / 2, y: a.cy - zoom * (bb.y1 + bb.y2) / 2}, animate);
  }

  // Centre the free area on some elements, zooming in to at least 1.2 (search, a connected-tag row).
  function centerOn(eles) {
    if (eles.empty()) return;
    const b = eles.boundingBox({includeLabels: false, includeOverlays: false}), a = freeArea();
    const zoom = Math.min(G.cy.maxZoom(), Math.max(G.cy.zoom(), 1.2));
    viewport(zoom, {x: a.cx - zoom * (b.x1 + b.x2) / 2, y: a.cy - zoom * (b.y1 + b.y2) / 2}, true);
    G.userMoved = true;
  }

  // Re-apply the target positions with the current stretch (after a resize).
  function place() {
    G.stretch = stretchFor(G.data);
    G.cy.batch(() => {
      for (const n of G.data.nodes) {
        const el = G.cy.getElementById(n.id);
        if (!el.animated()) el.position(at(n.id));
      }
      for (const r of G.data.regions) {
        const el = region(r.cluster);
        el.data("w", r.w * G.stretch);
        el.unlock().position({x: r.x * G.stretch, y: r.y}).lock();
      }
    });
  }

  // ------------------------------------------------------------------ labels

  function sizeLabels() {
    const cy = G.cy, z = cy.zoom();
    cy.batch(() => {
      cy.nodes(".pri, .hot").style({"font-size": PRI_PX / z, "text-margin-y": 2 / z,
                                    "text-background-padding": 2 / z});
      cy.nodes(".region").style({"font-size": TITLE_PX / z, "text-margin-y": -4 / z});
    });
    cull();
  }

  // Hide each priority label that overlaps a higher-ranked one; the selection and its neighbours always show.
  function cull() {
    const cy = G.cy;
    const labelled = cy.nodes(".pri, .hot").not(".region, .leaving");
    const hot = labelled.filter(".hot");
    const rest = labelled.not(".hot").sort((a, b) => a.data("prio") - b.data("prio"));
    const area = (n) => n.boundingBox({includeNodes: false, includeEdges: false, includeLabels: true,
                                       includeOverlays: false});
    const hits = (a, b) => a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2;
    const kept = hot.map(area);
    cy.batch(() => {
      hot.removeClass("lbl-off");
      rest.forEach((n) => {
        const b = area(n);
        if (kept.some((k) => hits(k, b))) n.addClass("lbl-off");
        else { kept.push(b); n.removeClass("lbl-off"); }
      });
    });
  }

  // ------------------------------------------------------------------ elements

  function nodeData(n) {
    return {id: n.id, label: n.label, cluster: n.cluster, color: n.color, size: n.size, prio: n.prio};
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
    const cy = G.cy;
    if (JSON.stringify(data.basis) !== JSON.stringify(G.basis)) G.dragged = {global: {}, separated: {}};
    G.basis = data.basis;
    G.stretch = stretchFor(data);
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
                                                     color: r.color, w: r.w * G.stretch, h: r.h},
                              position: {x: r.x * G.stretch, y: r.y}, classes: "region", grabbable: false,
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
      cy.nodes().not(".pri").removeStyle(SIZED);
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

  // A tag dims all but its closed neighbourhood (and pulses once), an edge all but itself and its two tags,
  // a cluster all but its members.
  function applySelection(sel, changed) {
    const cy = G.cy;
    let pulse = null;
    cy.batch(() => {
      cy.nodes(".hot").not(".pri").removeStyle(SIZED);
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
          pulse = el;
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
    if (pulse && changed && dur()) {
      const s = pulse.data("size");
      pulse.animate({style: {width: s * 1.45, height: s * 1.45}}, {duration: 140,
        complete: () => pulse.animate({style: {width: s, height: s}}, {duration: 200,
          complete: () => pulse.removeStyle("width height")})});
    }
  }

  // Zoom to a cluster: its region in Cluster-separated mode, its members' bounding box in Global.
  function focusCluster(cluster) {
    const r = region(cluster);
    const eles = r.nonempty() ? r : members(cluster);
    if (eles.empty()) return;
    const b = eles.boundingBox({includeLabels: false, includeOverlays: false});
    fitBox({x1: b.x1, x2: b.x2, y1: b.y1 - (r.nonempty() ? TITLE_ROOM : 0), y2: b.y2 + LABEL_ROOM}, true);
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
      G.el = el; G.cy = mount(el); G.data = null; G.sig = null; G.moveSig = null; G.transition = null;
    }
    transitions();
    const prev = G.data;
    G.data = data;
    const moveSig = JSON.stringify([data.layout, data.positions, data.regions]);
    const sig = JSON.stringify([data.dataset, data.nodes, data.edges, moveSig]);
    if (sig !== G.sig) {
      const fresh = !prev || prev.dataset !== data.dataset, moved = moveSig !== G.moveSig;
      sync(data, fresh);
      if (fresh || moved) G.userMoved = false;
      if (!G.userMoved) fit(!!prev);  // the move and the fit run together; a new dataset only fits
      G.sig = sig; G.moveSig = moveSig;
    }
    const selSig = JSON.stringify(data.selected);
    applySelection(data.selected, selSig !== G.selected);
    G.selected = selSig;
    runView(data.view);
    return Date.now();
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {tagGraph: {render}});
  window.tagGraph = G;  // for inspection in the browser console and browser checks
})();
