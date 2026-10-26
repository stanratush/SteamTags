"""PROTOTYPE (throwaway) — the Parameter Selection mode, ticket "Parameter Selection mode prototype".

Three structurally different layouts of the third app mode, switchable via `?variant=A|B|C` and the floating bar
(or ← / →). A second control in the bar simulates the run state: results cached, never run, or a run cancelled
midway. Run, Cancel, Continue and "Validate this pair" are simulated with a timer.

Real: the grid (ticket 05's run on Build 20261008T221504Z-7a23ae9f), the selection (ticket 06, recomputed on
Confirm), and an inspected pair's CHAMP plot and Clusters (computed live, 0.2-4 s). Illustrative: validation beyond
the ticket 07 pilot, and Apply (which only says what the Workbench would do).

    .venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/10-parameter-selection-mode/app.py

then open http://127.0.0.1:8060/?variant=A
"""

from __future__ import annotations

import threading
from urllib.parse import parse_qs

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

import data as D
import pieces as P

VARIANTS = {"A": "Three panes", "B": "Report page", "C": "Five side by side"}
SIM = {"cached": "Results cached", "never": "Never run", "cancelled": "Run cancelled midway"}
N = len(D.PAIRS)


def run_preset(name):
    if name == "never":
        return {"grid": {d: 0 for d in D.DATASETS}, "val": {d: 0 for d in D.DATASETS}, "active": False, "scope": []}
    if name == "cancelled":
        grid = {d: 0 for d in D.DATASETS} | {"overall": N, "puzzle": 87}
        return {"grid": grid, "val": {d: 0 for d in D.DATASETS}, "active": False, "scope": [], "cancelled": True}
    return {"grid": {d: N for d in D.DATASETS}, "val": {d: 200 for d in D.DATASETS}, "active": False, "scope": []}


# ----------------------------------------------------------------------------- shared state -> view model


def model(st):
    run, cons = st["run"], st["cons"]
    d = st["ds"]
    sels, defaults = {}, {}
    for x in D.DATASETS:
        n = run["grid"][x]
        if n == 0:
            sels[x] = None
        else:
            sels[x] = D.select(x, P.effective(cons, x), None if n >= N else P.done_set(run, x))
        defaults[x] = D.select(x, D.DEFAULTS)["chosen"]
    pair = st["pair"]
    if pair and pair[0] == d:
        inspected = (pair[1], pair[2])
    else:
        inspected = sels[d]["chosen"] if sels[d] and not sels[d]["partial"] else None
    return {"d": d, "sels": sels, "sel": sels[d], "defaults": defaults, "inspected": inspected}


def is_validated(st, m, d, g, s):
    return (st["run"]["val"][d] >= 200 and m["defaults"][d] == (g, s)) or [d, g, s] in st["validated"]


def ds_strip(st, m, *, cls="ps-strip"):
    out = []
    for d in D.DATASETS:
        sel = m["sels"][d]
        if sel is None:
            sub = "not run"
        elif sel["partial"]:
            sub = f"grid {st['run']['grid'][d]} of {N}"
        elif sel["chosen"]:
            r = D.grid()[(d, *sel["chosen"])]
            sub = f"★ {sel['chosen'][0]}·{sel['chosen'][1]}  NA {r['na_mean']:.2f}"
        else:
            sub = "no qualifying pair"
        custom = bool(D.is_custom(P.effective(st["cons"], d)))
        out.append(html.Button([html.B(d), html.Span(sub, className="small"),
                                html.Span("custom" if custom else "", className="ps-dot")],
                               id={"type": "ds", "d": d}, className="ps-ds" + (" on" if d == m["d"] else "")))
    return html.Div(out, className=cls)


def inspector_body(st, m, *, champ_h=260):
    d, sel, p = m["d"], m["sel"], m["inspected"]
    if p is None:
        return html.Div("Nothing to inspect until the grid is complete. Click a computed cell to inspect it.",
                        className="msg")
    g, s = p
    return html.Div([
        html.Div(f"{d} · {P.pair_txt(p)}", className="i-title"),
        P.status_badges(sel, d, g, s),
        P.apply_button(d, g, s),
        html.Div("Pair", className="i-h"), P.pair_metrics(d, g, s),
        html.Div("CHAMP", className="i-h"), P.champ(d, g, s, height=champ_h),
        html.Div("Clusters of the Selected Partition", className="i-h"), P.clusters_list(d, g, s),
        html.Div("Validation", className="i-h"),
        P.validation_block(d, g, s, is_validated(st, m, d, g, s), st["valjob"], default_pair=m["defaults"][d],
                           compact=True, where="insp"),
    ])


def chosen_validation(st, m):
    d, sel = m["d"], m["sel"]
    if not sel or sel["partial"] or not sel["chosen"]:
        return html.Div()
    g, s = sel["chosen"]
    return P.validation_block(d, g, s, is_validated(st, m, d, g, s), st["valjob"], default_pair=m["defaults"][d])


# ----------------------------------------------------------------------------- variant A: three panes


def variant_a(st, m):
    d, sel = m["d"], m["sel"]
    done = P.done_set(st["run"], d)
    if sel is None:
        centre = [html.Div([html.H3("No results for these settings yet"),
                            html.P("Run the grid for all five datasets (about 3 minutes on 12 workers), or just this "
                                   "one, from Run on the left.")], className="ps-empty")]
    else:
        centre = [
            html.Div(P.metric_picker(st["metric"]), className="row-inline ps-metric-row"),
            P.heatmap(d, st["metric"], sel, done, m["inspected"], height=560, partial_selection=False),
            P.heatmap_key(st["metric"]),
            html.Div([html.H4("Why this pair", className="ps-h"), P.explanation(sel)], className="ps-card"),
            html.Div(chosen_validation(st, m), className="ps-card"),
        ]
    return html.Div([
        html.Div([
            html.Div(html.B("Parameter Selection"), className="ctl-title"),
            html.H4("Run", className="ctl-h"), P.run_panel(st["run"], st["valjob"], d),
            html.H4("Pair Constraints", className="ctl-h"), P.constraints_panel(st["draft"], st["cons"], d),
            html.H4("Fixed settings", className="ctl-h"), P.fixed_settings(),
        ], className="controls ps-ctl"),
        html.Div([ds_strip(st, m), *centre], className="ps-main-a"),
        html.Div([html.Div(html.B("Pair Inspector"), className="insp-title"), inspector_body(st, m)],
                 className="inspector docked ps-insp"),
    ], className="app-body ps-body-a")


# ----------------------------------------------------------------------------- variant B: one report page


def cross_table(st, m):
    head = ["Dataset", "Chosen pair", "NA (min)", "Qualifying", "Near-best", "Tags", "Multi-Tag Clusters",
            "Retention", "Selected / Workbench γ", "Seed-Noise Floor", "Null", "Subsamples (median ARI)",
            "Constraints", ""]
    rows = []
    for d in D.DATASETS:
        sel = m["sels"][d]
        if sel is None or sel["partial"]:
            msg = "not run" if sel is None else f"grid {st['run']['grid'][d]} of {N} pairs"
            rows.append(html.Tr([html.Td(html.B(d)), html.Td(msg, colSpan=len(head) - 1, className="mute")]))
            continue
        if not sel["chosen"]:
            rows.append(html.Tr([html.Td(html.B(d)), html.Td("No pair qualifies", colSpan=len(head) - 2,
                                                              className="warning"),
                                 html.Td(P.constraints_label(sel["constraints"], short=True))]))
            continue
        g, s = sel["chosen"]
        r = D.grid()[(d, g, s)]
        wb = D.workbench(d, g, s)
        if is_validated(st, m, d, g, s):
            v = D.validation(d, g, s)
            null = "Q not above" if v["reach"] else "Q above all"
            sub = f"{D.med(v['resel']):.2f} / {D.med(v['fixed']):.2f}"
        else:
            null = sub = "not validated"
        rows.append(html.Tr([
            html.Td(html.B(d)), html.Td(f"g={g}, s={s}"), html.Td(f"{r['na_mean']:.2f} ({r['na_min']:.2f})", className="r"),
            html.Td(len(sel["qualifying"]), className="r"), html.Td(len(sel["near_best"]), className="r"),
            html.Td(r["Tags"], className="r"), html.Td(r["Multi-Tag Clusters (Selected Partition)"], className="r"),
            html.Td(f"{r['Information Retention']:.2f}", className="r"),
            html.Td(f"{r['Selected Resolution']:.3f} / {wb['gamma']:.2f}", className="r"),
            html.Td(f"{r['Seed-Noise Floor (min ARI)']:.2f}", className="r"), html.Td(null), html.Td(sub),
            html.Td(P.constraints_label(sel["constraints"], short=True)),
            html.Td(html.Button("Inspect", id={"type": "goto", **P.pk(d, g, s)}, className="btn")),
        ], className="ps-row-on" if d == m["d"] else ""))
    return html.Table([html.Tr([html.Th(h) for h in head]), *rows], className="tl ps-cross")


def variant_b(st, m):
    d, sel = m["d"], m["sel"]
    done = P.done_set(st["run"], d)
    ready = sel is not None and not sel["partial"]
    wait = html.Div(f"Appears when {d}'s grid is complete ({st['run']['grid'][d]} of {N} pairs).", className="msg")

    def sec(n, title, *children):
        return html.Section([html.H3(f"{n} {title}", className="ps-sec-h"), *children], className="ps-sec")

    grid_sec = wait
    if ready:
        mets = ["na", "retention", "isolated", "snf", "mtc", "q"]
        grid_sec = html.Div([
            html.Div([P.heatmap(d, k, sel, done, m["inspected"], height=330, text=False, idx=i,
                                title=D.METRICS[k][1] + (" — descriptive" if D.METRICS[k][2] else ""))
                      for i, k in enumerate(mets)], className="ps-multiples"),
            P.heatmap_key("na")])
    pair_sec = wait
    if ready and m["inspected"]:
        g, s = m["inspected"]
        pair_sec = html.Div([
            html.Div([html.Span(f"{d} · {P.pair_txt((g, s))}", className="i-title"), P.status_badges(sel, d, g, s)],
                     className="row-inline"),
            html.Div([html.Div(P.pair_metrics(d, g, s)), html.Div(P.champ(d, g, s, height=320))], className="ps-two"),
            html.Div("Clusters of the Selected Partition", className="i-h"), P.clusters_list(d, g, s),
            html.Div(P.apply_button(d, g, s, big=True), className="ps-apply-end"),
        ])
    val_sec = wait
    if ready and m["inspected"]:
        g, s = m["inspected"]
        val_sec = P.validation_block(d, g, s, is_validated(st, m, d, g, s), st["valjob"], default_pair=m["defaults"][d])
    return html.Div([
        html.Nav([html.A(t, href=f"#ps-s{i}") for i, t in enumerate(
            ["Run", "Five datasets", "Pair Constraints", "Selection", "Grid", "Pair", "Validation"], start=1)],
            className="ps-toc"),
        html.Div([
            html.Div(sec(1, "Run", P.run_panel(st["run"], st["valjob"], d), html.Details(
                [html.Summary("Fixed settings"), P.fixed_settings()])), id="ps-s1"),
            html.Div(sec(2, "Five datasets", cross_table(st, m)), id="ps-s2"),
            html.Div(sec(3, "Pair Constraints", P.constraints_panel(st["draft"], st["cons"], d, inline=True)), id="ps-s3"),
            html.Div(sec(4, "Selection", ds_strip(st, m, cls="ps-strip slim"),
                         P.explanation(sel) if ready else wait), id="ps-s4"),
            html.Div(sec(5, f"Grid: {d}", grid_sec), id="ps-s5"),
            html.Div(sec(6, "Inspected pair", pair_sec), id="ps-s6"),
            html.Div(sec(7, "Validation", val_sec), id="ps-s7"),
        ], className="ps-page"),
    ], className="ps-body-b")


# ----------------------------------------------------------------------------- variant C: five side by side


def variant_c(st, m):
    pair = st["pair"]
    same = (pair[1], pair[2]) if pair else None
    cols = []
    for d in D.DATASETS:
        sel = m["sels"][d]
        n = st["run"]["grid"][d]
        head = html.Div([html.Button(html.B(d), id={"type": "ds", "d": d}, className="ps-link"),
                         html.Progress(value=str(n), max=str(N), className="ps-prog mini") if n < N else
                         P.constraints_label(sel["constraints"], short=True)], className="ps-col-h")
        if sel is None:
            cols.append(html.Div([head, html.Div("not run", className="ps-hm-empty")], className="ps-col"))
            continue
        hm = P.heatmap(d, st["metric"], sel, P.done_set(st["run"], d), same if pair and pair[0] == d else None,
                       height=400, text=False, same_pair=same if not pair or pair[0] != d else None)
        if sel["partial"]:
            card = html.Div(f"{n} of {N} pairs; selection when complete", className="msg")
        elif not sel["chosen"]:
            card = html.Div([html.B("No pair qualifies"), html.Div("Loosen a constraint or inspect a cell.",
                                                                   className="small")], className="ps-card-s")
        else:
            g, s = sel["chosen"]
            r = D.grid()[(d, g, s)]
            ver = []
            if is_validated(st, m, d, g, s):
                v = D.validation(d, g, s)
                ver = [html.Span("Q not above null" if v["reach"] else "Q > null", className="ps-tag" +
                                 (" bad" if v["reach"] else "")),
                       html.Span(f"sub ARI {D.med(v['resel']):.2f}", className="ps-tag")]
            else:
                ver = [html.Span("not validated", className="ps-tag")]
            card = html.Div([
                html.Div([html.Span("★", style={"color": P.NEAR}), html.B(f" g = {g}, s = {s}")]),
                html.Div(f"NA {r['na_mean']:.2f} · {r['Tags']} tags · {r['Multi-Tag Clusters (Selected Partition)']} "
                         f"Multi-Tag Clusters · retention {r['Information Retention']:.2f}", className="small"),
                html.Div(f"{len(sel['qualifying'])} qualify, {len(sel['near_best'])} near-best", className="small mute"),
                html.Div(ver, className="row-inline"),
                html.Button("Inspect", id={"type": "goto", **P.pk(d, g, s)}, className="btn"),
            ], className="ps-card-s")
        cols.append(html.Div([head, hm, card], className="ps-col" + (" on" if d == m["d"] else "")))
    across = html.Div()
    if same:
        cells = []
        for d in D.DATASETS:
            sel = m["sels"][d]
            r = D.grid()[(d, *same)]
            why = sel["why"].get(same) if sel else None
            cells.append(html.Div([html.B(d), html.Div(f"NA {P.fmt(r['na_mean'])} · {r['Tags']} tags · "
                                                       f"{P.fmt(r['Multi-Tag Clusters (Selected Partition)'])} MTC"),
                                   html.Div("qualifies" if why == [] else
                                            ("not computed" if why is None else
                                             " ".join(D.REASONS[x][0] for x in why)), className="small mute")],
                                  className="ps-across-c"))
        across = html.Div([html.Span(f"{P.pair_txt(same)} in every dataset", className="ps-across-h"), *cells],
                          className="ps-across")
    toolbar = html.Div([
        html.Div(P.metric_picker(st["metric"], dropdown=True), style={"width": "260px"}),
        html.Button([P.constraints_label(P.effective(st["cons"], m["d"]), short=True), " ▾"],
                    id={"type": "conspop", "i": 0}, className="btn"),
        P.run_panel(st["run"], st["valjob"], m["d"], compact=True),
        P.heatmap_key(st["metric"]),
    ], className="ps-toolbar")
    pop = html.Div([html.Div([html.B(f"Pair Constraints · {m['d']}"),
                              html.Button("×", id={"type": "conspop", "i": 1}, className="x")], className="row-inline"),
                    P.constraints_panel(st["draft"], st["cons"], m["d"])],
                   className="ps-pop", style={} if st["pop"] else {"display": "none"})
    sheet = html.Div()
    if pair and m["sels"][pair[0]]:
        d, g, s = pair
        sel = m["sels"][d]
        tabs = [("why", "Selection explained"), ("pair", "Pair"), ("champ", "CHAMP"), ("clusters", "Clusters"),
                ("val", "Validation")]
        tab = st["tab"]
        body = {
            "why": lambda: P.explanation(sel) if not sel["partial"] else html.Div("Grid not complete.", className="msg"),
            "pair": lambda: P.pair_metrics(d, g, s),
            "champ": lambda: P.champ(d, g, s, height=300),
            "clusters": lambda: P.clusters_list(d, g, s),
            "val": lambda: P.validation_block(d, g, s, is_validated(st, m, d, g, s), st["valjob"],
                                              default_pair=m["defaults"][d]),
        }[tab]()
        sheet = html.Div([
            html.Div([html.B(f"{d} · {P.pair_txt((g, s))}", className="i-title"), P.status_badges(sel, d, g, s),
                      html.Div(P.apply_button(d, g, s), className="ps-sheet-apply"),
                      html.Button("×", id={"type": "close-sheet", "i": 0}, className="x")], className="ps-sheet-h"),
            dcc.RadioItems(id={"type": "tab", "i": 0}, value=tab, inline=True, className="tabs-nav",
                           options=[{"label": t, "value": k} for k, t in tabs]),
            html.Div(body, className="ps-sheet-b"),
        ], className="ps-sheet")
    return html.Div([toolbar, pop, across, html.Div(cols, className="ps-cols"), sheet], className="ps-body-c")


# ----------------------------------------------------------------------------- app


app = Dash(__name__, suppress_callback_exceptions=True, title="Tag Network — Parameter Selection (PROTOTYPE)")
APP_CSS = (D.REPO / "src/steamstudy/app/assets/app.css").read_text(encoding="utf-8")
app.index_string = app.index_string.replace("{%css%}", "{%css%}<style>" + APP_CSS + "</style>")

STORES = {"ds": "overall", "metric": "na", "pair": None, "cons": {"shared": dict(D.DEFAULTS), "override": {}},
          "draft": dict(D.DEFAULTS), "run": run_preset("cached"), "valjob": None, "validated": [], "applied": None,
          "pop": False, "tab": "why", "stop": 0}

header = html.Header([
    html.Div([html.B("Tag Network", className="title"), html.Span(f"Build {D.BUILD_ID}", className="mute")],
             className="brand"),
    html.Div([html.Span("Workbench", className="ps-mode"), html.Span("Analysis Report mode", className="ps-mode"),
              html.Span("Parameter Selection", className="ps-mode on")], className="ps-modes"),
    html.Div(html.Span("PROTOTYPE", className="ps-proto"), className="hdr-right"),
], className="app-header")

bar = html.Div([
    html.Button("◀", id="v-prev", className="ps-bar-btn"), html.Span(id="v-label", className="ps-bar-label"),
    html.Button("▶", id="v-next", className="ps-bar-btn"), html.Span("|", className="ps-bar-sep"),
    dcc.Dropdown(id="sim", options=[{"label": v, "value": k} for k, v in SIM.items()], value="cached",
                 clearable=False, searchable=False, className="ps-bar-dd"),
], className="ps-bar")

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    *[dcc.Store(id=f"st-{k}", data=v) for k, v in STORES.items()],
    dcc.Interval(id="tick", interval=500, disabled=True),
    header, html.Div(id="toast"), html.Div(id="page"), bar,
], id="root", className="ps-root controls-on inspector-on tables-on")


def variant_of(search):
    v = parse_qs((search or "").lstrip("?")).get("variant", ["A"])[0].upper()
    return v if v in VARIANTS else "A"


@app.callback(Output("page", "children"), Output("v-label", "children"), Output("toast", "children"),
              Input("url", "search"), *[Input(f"st-{k}", "data") for k in STORES])
def render(search, *vals):
    st = dict(zip(STORES, vals))
    v = variant_of(search)
    m = model(st)
    page = {"A": variant_a, "B": variant_b, "C": variant_c}[v](st, m)
    toast = html.Div()
    if st["applied"]:
        d, g, s = st["applied"]
        wb = D.workbench(d, g, s)
        line = (f"Applied from Parameter Selection: {d}, g={g}, s={s} — Selected Partition reproduced ✓"
                if wb["reproduced"] else
                f"Applied from Parameter Selection: {d}, g={g}, s={s} — shows a different partition from the Selected "
                f"Partition: ARI {wb['ari']:.2f}")
        toast = html.Div([html.B("PROTOTYPE · Apply → "), f"the app would switch to the Workbench with {d}, g = {g}, "
                          f"s = {s}, Months ≥ 0, Genre Tags + defining tag hidden, Lift, Leiden, γ {wb['gamma']:.2f}, "
                          f"{wb['seed']}. Its provenance line: “{line}”"], className="banner")
    return page, f"{v} · {VARIANTS[v]}", toast


@app.callback(Output("url", "search"), Input("v-prev", "n_clicks"), Input("v-next", "n_clicks"),
              State("url", "search"), prevent_initial_call=True)
def cycle(_p, _n, search):
    keys = list(VARIANTS)
    i = keys.index(variant_of(search)) + (1 if ctx.triggered_id == "v-next" else -1)
    return f"?variant={keys[i % len(keys)]}"  # drops ?run=, so cycling keeps the current run state


@app.callback(Output("sim", "value"), Input("url", "search"), State("sim", "value"))
def sim_from_url(search, cur):
    v = parse_qs((search or "").lstrip("?")).get("run", [None])[0]
    return v if v in SIM and v != cur else no_update


def fired():
    t = ctx.triggered[0] if ctx.triggered else None
    return t is not None and t["value"] not in (None, 0, [])


@app.callback(Output("st-ds", "data"), Output("st-draft", "data", allow_duplicate=True),
              Input({"type": "ds", "d": ALL}, "n_clicks"), State("st-cons", "data"), prevent_initial_call=True)
def pick_ds(_, cons):
    if not fired():
        return no_update, no_update
    d = ctx.triggered_id["d"]
    return d, dict(P.effective(cons, d))


@app.callback(Output("st-metric", "data"), Input({"type": "metric", "i": ALL}, "value"), State("st-metric", "data"),
              prevent_initial_call=True)
def pick_metric(vals, cur):
    v = ctx.triggered[0]["value"] if ctx.triggered else None
    return v if v and v != cur else no_update


@app.callback(Output("st-pair", "data"), Output("st-ds", "data", allow_duplicate=True),
              Output("st-draft", "data", allow_duplicate=True), Output("st-tab", "data", allow_duplicate=True),
              Input({"type": "hm", "ds": ALL, "i": ALL}, "clickData"), Input({"type": "goto", "d": ALL, "g": ALL,
                                                                            "s": ALL}, "n_clicks"),
              State("st-cons", "data"), State("st-ds", "data"), prevent_initial_call=True)
def pick_pair(_c, _g, cons, cur):
    if not fired():
        return (no_update,) * 4
    t = ctx.triggered_id
    if t["type"] == "hm":
        pt = ctx.triggered[0]["value"]["points"][0]
        d, g, s = t["ds"], int(pt["y"]), int(pt["x"])
        if (g, s) not in set(D.PAIRS):
            return (no_update,) * 4
    else:
        d, g, s = t["d"], t["g"], t["s"]
    draft = dict(P.effective(cons, d)) if d != cur else no_update
    return [d, g, s], d, draft, ("pair" if t["type"] == "hm" else "why")


@app.callback(Output("st-pair", "data", allow_duplicate=True), Input({"type": "close-sheet", "i": ALL}, "n_clicks"),
              prevent_initial_call=True)
def close_sheet(_):
    return None if fired() else no_update


@app.callback(Output("st-tab", "data"), Input({"type": "tab", "i": ALL}, "value"), State("st-tab", "data"),
              prevent_initial_call=True)
def pick_tab(vals, cur):
    v = ctx.triggered[0]["value"] if ctx.triggered else None
    return v if v and v != cur else no_update


@app.callback(Output("st-pop", "data"), Input({"type": "conspop", "i": ALL}, "n_clicks"), State("st-pop", "data"),
              prevent_initial_call=True)
def toggle_pop(_, cur):
    return (not cur) if fired() else no_update


@app.callback(Output("st-draft", "data"), Input({"type": "cons", "k": ALL}, "value"), State("st-draft", "data"),
              prevent_initial_call=True)
def edit_draft(vals, draft):
    keys = [i["id"]["k"] for i in ctx.inputs_list[0]]
    if not keys:
        return no_update
    new = dict(draft)
    for k, v in zip(keys, vals):
        if k == "mtc_max":
            new[k] = int(v) if v not in (None, "") else None
        elif k == "neighbours_min":
            new[k] = int(v) if v is not None else draft[k]
        else:
            new[k] = float(v) if v is not None else draft[k]
    return new if new != draft else no_update


@app.callback(Output("st-cons", "data"), Output("st-draft", "data", allow_duplicate=True),
              Input({"type": "cons-confirm", "i": ALL}, "n_clicks"), Input({"type": "cons-reset", "i": ALL}, "n_clicks"),
              State({"type": "cons-scope", "i": ALL}, "value"), State("st-draft", "data"), State("st-cons", "data"),
              State("st-ds", "data"), prevent_initial_call=True)
def confirm(_c, _r, scope, draft, cons, d):
    if not fired():
        return no_update, no_update
    cons = {"shared": dict(cons["shared"]), "override": dict(cons["override"])}
    if ctx.triggered_id["type"] == "cons-reset":
        cons["override"].pop(d, None)
        cons["shared"] = dict(D.DEFAULTS)
        return cons, dict(D.DEFAULTS)
    if scope and scope[0] == "this":
        cons["override"][d] = dict(draft)
    else:
        cons["override"].pop(d, None)
        cons["shared"] = dict(draft)
    return cons, no_update


@app.callback(Output("st-run", "data"), Output("st-valjob", "data"), Output("st-validated", "data"),
              Input({"type": "run", "what": ALL}, "n_clicks"), Input("sim", "value"), Input("tick", "n_intervals"),
              Input({"type": "validate", "d": ALL, "g": ALL, "s": ALL, "w": ALL}, "n_clicks"),
              State("st-run", "data"), State("st-valjob", "data"), State("st-validated", "data"), State("st-ds", "data"),
              State("st-stop", "data"), prevent_initial_call=True)
def jobs(_r, sim, _t, _v, run, valjob, validated, d, stop):
    t = ctx.triggered_id
    if t == "sim":
        return {**run_preset(sim), "stopped": stop}, None, []
    if stop > run.get("stopped", 0):
        # Cancel (its own store, so a tick in flight can't undo it): a cancelled grid keeps its pairs; a cancelled
        # validation is discarded
        val = {x: (v if v >= 200 else 0) for x, v in run["val"].items()}
        return {**run, "val": val, "active": False, "cancelled": True, "stopped": stop}, None, no_update
    if t == "tick":
        if valjob:
            valjob = dict(valjob, n=valjob["n"] + 40)
            if valjob["n"] >= 200:
                return no_update, None, validated + [valjob["pair"]]
            return no_update, valjob, no_update
        run = {**run, "grid": dict(run["grid"]), "val": dict(run["val"])}
        todo = [x for x in run["scope"] if run["grid"][x] < N]  # every grid before any validation (ticket 08)
        if todo:
            run["grid"][todo[0]] = min(N, run["grid"][todo[0]] + 19)
        else:
            vtodo = [x for x in run["scope"] if run["val"][x] < 200]
            if vtodo:
                run["val"][vtodo[0]] = min(200, run["val"][vtodo[0]] + 50)
            else:
                run["active"] = False
        return run, no_update, no_update
    if not fired():
        return no_update, no_update, no_update
    if t["type"] == "validate":
        return no_update, {"pair": [t["d"], t["g"], t["s"]], "n": 0}, no_update
    what = t["what"]
    if what == "cancel":
        return no_update, no_update, no_update
    run = {**run, "grid": dict(run["grid"]), "val": dict(run["val"])}
    scope = list(D.DATASETS) if what in ("all", "continue") else [d]
    if what == "one":
        run["grid"][d] = 0 if run["grid"][d] >= N else run["grid"][d]
    return {**run, "active": True, "scope": scope, "cancelled": False}, no_update, no_update


@app.callback(Output("st-stop", "data"), Input({"type": "run", "what": ALL}, "n_clicks"), State("st-stop", "data"),
              prevent_initial_call=True)
def cancel(_, stop):
    return stop + 1 if fired() and ctx.triggered_id["what"] == "cancel" else no_update


@app.callback(Output("tick", "disabled"), Input("st-run", "data"), Input("st-valjob", "data"))
def ticking(run, valjob):
    return not (run["active"] or valjob)


@app.callback(Output("st-applied", "data"), Input({"type": "apply", "d": ALL, "g": ALL, "s": ALL}, "n_clicks"),
              prevent_initial_call=True)
def apply(_):
    if not fired():
        return no_update
    t = ctx.triggered_id
    return [t["d"], t["g"], t["s"]]


def _warm():  # the five chosen pairs, so the first view doesn't wait on Leiden
    for d in D.DATASETS:
        D.pair_detail(d, *D.select(d, D.DEFAULTS)["chosen"])


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8060
    D._init()
    threading.Thread(target=_warm, daemon=True).start()
    app.run(debug=False, port=port, host="127.0.0.1")
