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
    const body = document.getElementById("inspector-body"), quality = document.getElementById("quality-detail");
    if (!body || !quality) { setTimeout(watchHtml, 50); return; }
    for (const el of [body, quality]) {
      new MutationObserver(() => { fillHtml(el); if (el === quality) applyMatrixChoices(); })
        .observe(el, {childList: true, subtree: true, attributes: true, attributeFilter: ["data-html"]});
      fillHtml(el);
    }
    applyMatrixChoices();
  }

  // ------------------------------------------------------------------ Connections matrix (Cluster quality tab)

  // View choices kept in the browser (no callback): Ratio or Share per cell, back to Ratio on a new dataset; and
  // Matrix or Table, the Table being the cluster_connections.csv grid.
  const matrix = {dataset: null, mode: "ratio", view: "matrix"};

  function applyMatrixChoices() {
    const cm = document.querySelector("#quality-detail .cm"), block = document.getElementById("blk-quality");
    if (cm) {
      if (cm.dataset.dataset !== matrix.dataset) { matrix.dataset = cm.dataset.dataset; matrix.mode = "ratio"; }
      if (cm.dataset.mode !== matrix.mode) cm.dataset.mode = matrix.mode;
      cm.querySelectorAll("[data-cm-mode]").forEach((b) => b.classList.toggle("on", b.dataset.cmMode === matrix.mode));
      cm.querySelectorAll("[data-cm-view]").forEach((b) => b.classList.toggle("on", b.dataset.cmView === matrix.view));
    }
    if (block) block.classList.toggle("cm-table-view", matrix.view === "table");
  }

  document.addEventListener("click", (ev) => {
    const btn = ev.target instanceof Element ? ev.target.closest("#quality-detail [data-cm-mode], #quality-detail [data-cm-view]") : null;
    if (!btn) return;
    if (btn.dataset.cmMode) matrix.mode = btn.dataset.cmMode;
    if (btn.dataset.cmView) matrix.view = btn.dataset.cmView;
    applyMatrixChoices();
  });

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
  // The tooltip lines' kinds styled apart (help.py: the Now line, the column line, the state table's Field line).
  const TIP_CLASS = {now: "now", column: "col", columns: "col", field: "col"};
  let tipBox = null, tipFor = null, lastPointer = "mouse";
  // The words this file shows, in the Interface Language (layout.py `ui_words`, through the ui-words store).
  let words = {tip: {}, more: "", info: "{name}"};

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
    // data-tip is help.py's structured lines, [[kind, text], ...]; each kind's label comes from the ui-words store.
    let lines;
    try { lines = JSON.parse(el.dataset.tip); } catch (e) { lines = [["", el.dataset.tip]]; }
    tipBox.innerHTML = lines.map(([kind, text]) => {
      const cls = TIP_CLASS[kind] ? ` class="${TIP_CLASS[kind]}"` : "";
      const label = words.tip[kind];
      return label ? `<p${cls}><b>${escapeHtml(label)}</b> ${escapeHtml(text)}</p>` : `<p>${escapeHtml(text)}</p>`;
    }).join("") + (el.dataset.help && words.more ? `<p class="more">${escapeHtml(words.more)}</p>` : "");
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
                        "aria-label": words.info.replace("{name}", props.displayName)}, "ⓘ"));
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

  // Fill "{n}"-style slots of a word from the ui-words store.
  function fill(word, values) {
    return Object.keys(values).reduce((s, k) => s.split(`{${k}}`).join(values[k]), word || "");
  }

  function pills(dataset, mgV, mgD, msV, msD, mmV, mmD, genre, defining, weight, algorithm, gamma, seed, uiWords,
                 datasetOptions, genreOptions) {
    const w = (uiWords && uiWords.pills) || {genre: ["{n}", "{n}"], defining: "{hidden}", lift: "", shared: "",
                                              of: "{n} / {total}"};
    const triggered = (window.dash_clientside.callback_context.triggered || []).map((t) => t.prop_id);
    // While a slider is dragged its label follows drag_value; the value is still sent on release.
    const live = (id, value, drag) => (triggered.includes(id + ".drag_value") && drag != null ? drag : value);
    const mg = String(live("min-games", mgV, mgD)), ms = String(live("min-shared", msV, msD));
    const mm = String(live("min-months", mmV, mmD));
    const ds = (datasetOptions || []).find((o) => o.value === dataset);
    const n = (genre || []).length, total = (genreOptions || []).length;
    const genreText = fill(w.genre[n === 1 ? 0 : 1], {n});
    const hidden = defining && defining.length ? fill(w.defining, {hidden: genreText}) : genreText;
    const decimal = (uiWords && uiWords.decimal) || ".";
    const g = gamma === null || gamma === undefined || gamma === "" ? "—" : Number(gamma).toFixed(2).replace(".", decimal);
    return [mg, ms, mm, ds ? ds.label : String(dataset), mm, mg, ms, hidden,
            weight === "lift" ? w.lift : w.shared, algorithm === "leiden" ? "Leiden" : "Louvain", g,
            seed === null || seed === undefined ? "—" : String(seed), fill(w.of, {n, total})];
  }

  // ------------------------------------------------------------------ Interface Language

  // The EN | BG switch: the choice is kept per browser in a cookie (i18n.COOKIE), which ignores the port, so it
  // survives restarts and --port changes; the server reads it when it serves the page.
  function language(lang) {
    document.cookie = `steamstudy_lang=${lang}; path=/; max-age=${400 * 24 * 3600}; SameSite=Lax`;
    return lang;
  }

  // The ui-words store (layout.py `ui_words`): the words of this file, the browser tab title and the page's lang
  // (screen readers; app.css `:lang(bg)` rules for longer Bulgarian labels).
  function uiWords(data) {
    if (!data) return;
    words = data;
    if (data.title) document.title = data.title;
    if (data.lang) document.documentElement.lang = data.lang;
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {workbench: {pills, language, uiWords}});
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
