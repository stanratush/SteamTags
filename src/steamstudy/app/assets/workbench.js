/* Workbench chrome that needs no server round trip: the responsive form, the pill popovers, the tables
   pane's drag handle, the bottom sheet, and the live slider and pill values.

   The form is set on body[data-form]: "wide" (>= 1280 px), "medium" (1024-1279 px: Controls as a pill
   bar, floating Inspector) or "narrow" (< 1024 px, or "Graph only": the tables also become a bottom
   sheet). app.css does the layout from it.
*/
(function () {
  "use strict";
  const WIDE = 1280, MEDIUM = 1024;
  const body = document.body;

  function root() { return document.getElementById("root"); }

  function updateForm() {
    const r = root();
    if (!r) return;
    const w = window.innerWidth;
    const form = r.classList.contains("graph-only") || w < MEDIUM ? "narrow" : w < WIDE ? "medium" : "wide";
    if (body.dataset.form !== form) {
      body.dataset.form = form;
      if (form !== "narrow") delete body.dataset.sheet;
      closePills();
    }
    // Where the graph stage sits inside the body grid: the floating Inspector is placed over it.
    const stage = r.querySelector(".graph-stage"), grid = document.getElementById("app-body");
    if (stage && grid) {
      const s = stage.getBoundingClientRect(), g = grid.getBoundingClientRect();
      grid.style.setProperty("--stage-top", Math.max(0, s.top - g.top) + "px");
      grid.style.setProperty("--stage-bottom", Math.max(0, g.bottom - s.bottom) + "px");
    }
  }

  function init() {
    const r = root();
    if (!r) { setTimeout(init, 50); return; }
    new MutationObserver(updateForm).observe(r, {attributes: true, attributeFilter: ["class"]});
    const ro = new ResizeObserver(updateForm);
    for (const id of ["app-body", "main"]) { const el = document.getElementById(id); if (el) ro.observe(el); }
    const stage = r.querySelector(".graph-stage");
    if (stage) ro.observe(stage);
    window.addEventListener("resize", updateForm);
    updateForm();
    watchHtml();
  }

  // ------------------------------------------------------------------ HTML blocks

  // The Inspector's long lists arrive as one escaped HTML string each (view.py `_html`, in data-html) and are put
  // in place here, in one step: no Markdown parsing and no React element per cell. React keeps the element (and
  // may only change its data-html) when the next selection has the same shape, so changes are watched too.
  function fillHtml(root) {
    root.querySelectorAll("[data-html]").forEach((el) => {
      if (el.htmlShown !== el.dataset.html) { el.innerHTML = el.dataset.html; el.htmlShown = el.dataset.html; }
    });
  }

  function watchHtml() {
    const body = document.getElementById("inspector-body");
    if (!body) { setTimeout(watchHtml, 50); return; }
    new MutationObserver(() => fillHtml(body)).observe(body, {childList: true, subtree: true, attributes: true,
                                                               attributeFilter: ["data-html"]});
    fillHtml(body);
  }

  // ------------------------------------------------------------------ pills

  function closePills(except) {
    document.querySelectorAll(".ctl-item.open").forEach((o) => { if (o !== except) o.classList.remove("open"); });
  }

  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".pill-btn");
    if (btn) {
      const item = btn.parentElement;
      closePills(item);
      item.classList.toggle("open");
      return;
    }
    // Dropdown menus render in a portal outside the popover; a click there is still inside.
    if (!ev.target.closest(".ctl-item.open, [data-radix-popper-content-wrapper]")) closePills();
    if (ev.target.closest("#sheet-grip")) {
      if (body.dataset.sheet === "open") delete body.dataset.sheet; else body.dataset.sheet = "open";
    } else if (ev.target.closest("#wb-tab label") && body.dataset.form === "narrow") {
      body.dataset.sheet = "open";
    }
  });
  document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closePills(); });

  // ------------------------------------------------------------------ click a state_id to copy it

  document.addEventListener("click", (ev) => {
    const id = ev.target.closest(".copy-id");
    if (!id || !navigator.clipboard) return;
    navigator.clipboard.writeText(id.textContent.trim()).then(() => {
      id.classList.add("copied");
      setTimeout(() => id.classList.remove("copied"), 1200);
    });
  });

  // ------------------------------------------------------------------ tables pane drag handle

  document.addEventListener("pointerdown", (ev) => {
    const handle = ev.target.closest("#tables-handle");
    if (!handle) return;
    const main = document.getElementById("main");
    ev.preventDefault();
    handle.setPointerCapture(ev.pointerId);
    const move = (e) => {
      const b = main.getBoundingClientRect();
      const px = Math.max(120, Math.min(b.height - 220, b.bottom - e.clientY));
      main.style.setProperty("--tables-h", px + "px");
    };
    const up = () => { handle.removeEventListener("pointermove", move); handle.removeEventListener("pointerup", up); };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up);
  });

  // ------------------------------------------------------------------ live values (clientside callback)

  function pills(dataset, mgV, mgD, msV, msD, mmV, mmD, genre, defining, weight, algorithm, gamma, seed,
                 datasetOptions, genreOptions) {
    const triggered = (window.dash_clientside.callback_context.triggered || []).map((t) => t.prop_id);
    // While a slider is dragged its label follows drag_value; the value is still sent on release.
    const live = (id, value, drag) => (triggered.includes(id + ".drag_value") && drag != null ? drag : value);
    const mg = String(live("min-games", mgV, mgD)), ms = String(live("min-shared", msV, msD));
    const mm = String(live("min-months", mmV, mmD));
    const ds = (datasetOptions || []).find((o) => o.value === dataset);
    const n = (genre || []).length, total = (genreOptions || []).length;
    const hidden = `${n} Genre Tag${n === 1 ? "" : "s"}${defining && defining.length ? " + defining" : ""}`;
    const g = gamma === null || gamma === undefined || gamma === "" ? "—" : Number(gamma).toFixed(2);
    return [mg, ms, mm, ds ? ds.label : String(dataset), mm, mg, ms, hidden,
            weight === "lift" ? "Lift" : "Shared games", algorithm === "leiden" ? "Leiden" : "Louvain", g,
            seed === null || seed === undefined ? "—" : String(seed), `${n} of ${total}`];
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {workbench: {pills}});
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
