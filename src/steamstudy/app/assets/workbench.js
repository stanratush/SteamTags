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

  // ------------------------------------------------------------------ metric help (spec: .scratch/metric-help)

  // Layer 1: an element's data-tip (its guide entry's In short lines, see help.py) in one floating box, on hover
  // or keyboard focus, never over the element itself. Layer 2: a click (or Enter) on a data-help element opens its
  // guide entry in the help modal through the help-target store. A touch tap goes straight to layer 2.
  const HELP_LINK = "#help:";  // guide.py HELP_LINK
  // guide.py IN_SHORT_LABELS, the Now line, help.py column_line and the dataset summary's Field line (view.py)
  const TIP_LABEL = /^(In short\.|Higher →|Lower →|Raising it →|Here:|Caution:|Now:|Columns?:|Field:)\s*/;
  let tipBox = null, tipFor = null, lastPointer = "mouse";

  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"})[c]);
  }

  function showTip(el) {
    if (!tipBox) {
      tipBox = document.createElement("div");
      tipBox.className = "tip";
      tipBox.setAttribute("role", "tooltip");
      tipBox.id = "help-tip";
      document.body.appendChild(tipBox);
    }
    tipBox.innerHTML = el.dataset.tip.split("\n").map((line) => {
      const m = line.match(TIP_LABEL);
      let cls = "";
      if (m && m[1] === "Now:") cls = ' class="now"';
      else if (m && (m[1].startsWith("Column") || m[1] === "Field:")) cls = ' class="col"';
      return m ? `<p${cls}><b>${escapeHtml(m[1])}</b> ${escapeHtml(line.slice(m[0].length))}</p>`
               : `<p>${escapeHtml(line)}</p>`;
    }).join("") + (el.dataset.help ? '<p class="more">Click for the full User Guide entry</p>' : "");
    tipFor = el;
    el.setAttribute("aria-describedby", "help-tip");
    tipBox.style.display = "block";
    const r = el.getBoundingClientRect(), t = tipBox.getBoundingClientRect(), gap = 8, margin = 8;
    const below = r.bottom + gap + t.height <= window.innerHeight - margin || r.top - gap - t.height < margin;
    const top = below ? r.bottom + gap : r.top - gap - t.height;
    const left = Math.min(Math.max(margin, r.left + r.width / 2 - t.width / 2), window.innerWidth - t.width - margin);
    tipBox.style.top = Math.max(margin, top) + "px";
    tipBox.style.left = left + "px";
  }

  function hideTip() {
    if (!tipFor) return;
    tipFor.removeAttribute("aria-describedby");
    tipFor = null;
    tipBox.style.display = "none";
  }

  function within(ev, selector) {
    return ev.target instanceof Element ? ev.target.closest(selector) : null;
  }

  function openHelp(el) {
    hideTip();
    window.dash_clientside.set_props("help-target", {data: {target: el.dataset.help, n: Date.now()}});
  }

  // A press hides the tooltip, so that it never covers what the press opens (a pill's popover, for example).
  document.addEventListener("pointerdown", (ev) => { lastPointer = ev.pointerType || "mouse"; hideTip(); }, true);
  document.addEventListener("mouseover", (ev) => {
    const el = within(ev, "[data-tip]");
    if (el === tipFor) return;
    // A grid header's ⓘ: on hover the header shows ag-grid's own tooltip.
    if (!el || lastPointer === "touch" || el.closest(".ag-header")) { hideTip(); return; }
    showTip(el);
  });
  document.addEventListener("mouseout", (ev) => {
    if (tipFor && !(ev.relatedTarget && tipFor.contains(ev.relatedTarget))) hideTip();
  });
  // Keyboard focus shows the tooltip; focus from a press does not (the press already opened what it opens).
  document.addEventListener("focusin", (ev) => {
    const el = within(ev, "[data-tip]");
    if (el && lastPointer !== "touch" && ev.target.matches(":focus-visible")) showTip(el); else hideTip();
  });
  document.addEventListener("focusout", hideTip);
  document.addEventListener("scroll", hideTip, true);
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") hideTip();
    const el = within(ev, "[data-help]");
    if (el && (ev.key === "Enter" || ev.key === " ") && el === ev.target) { ev.preventDefault(); openHelp(el); }
  });
  document.addEventListener("click", (ev) => {
    const el = within(ev, "[data-help]");
    if (el) openHelp(el);
    // A guide link inside the modal (guide.py points it at "#help:<file>#<anchor>") opens its entry there, on top
    // of the modal's history for ← Back. Other links keep their own behaviour.
    const link = within(ev, `#help-body a[href^="${HELP_LINK}"]`);
    if (link) {
      ev.preventDefault();
      const target = link.getAttribute("href").slice(HELP_LINK.length);
      window.dash_clientside.set_props("help-target", {data: {target, n: Date.now(), follow: true}});
    }
  });

  // Each newly opened entry starts at its top.
  function watchHelpBody() {
    const helpBody = document.getElementById("help-body");
    if (!helpBody) { setTimeout(watchHelpBody, 50); return; }
    new MutationObserver(() => { helpBody.parentElement.scrollTop = 0; }).observe(helpBody, {childList: true});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", watchHelpBody);
  else watchHelpBody();

  // A metric column's header (view.py `metric_header`): its name and an ⓘ that opens the guide entry. The ⓘ sits
  // inside the label that sorts, so its click and Enter are taken in the capture phase, before ag-grid sees them;
  // the rest of the header still sorts. On hover the header shows ag-grid's own tooltip (headerTooltip); the ⓘ's
  // data-tip is for keyboard focus only.
  function MetricHeader(props) {
    const h = window.React.createElement;
    return h(window.React.Fragment, null, props.displayName,
             h("span", {className: "hinfo", role: "button", tabIndex: 0, "data-help": props.help, "data-tip": props.tip,
                        "aria-label": `User Guide entry for ${props.displayName}`}, "ⓘ"));
  }
  window.dashAgGridComponentFunctions = Object.assign({}, window.dashAgGridComponentFunctions, {MetricHeader});

  function headerInfo(ev) {
    const el = within(ev, ".hinfo[data-help]");
    if (!el || (ev.type === "keydown" && (el !== ev.target || (ev.key !== "Enter" && ev.key !== " ")))) return;
    ev.preventDefault();
    ev.stopPropagation();
    if (ev.type !== "pointerdown") openHelp(el);
  }
  for (const type of ["pointerdown", "click", "keydown"]) document.addEventListener(type, headerInfo, true);

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
