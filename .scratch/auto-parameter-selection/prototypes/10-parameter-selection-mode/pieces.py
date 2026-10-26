"""PROTOTYPE (throwaway): the Parameter Selection mode's building blocks, shared by the three layout variants.

Every interactive component has a dict id with a "type", so the callbacks in app.py work whichever variant is
mounted. Pieces are content only; each variant decides where they sit and how much of each it shows.
"""

from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html

import data as D

ACC, NEAR, INK, WARN = "#2457d6", "#e8590c", "#1b2130", "#9a5b00"


def pk(d, g, s):
    return {"d": d, "g": g, "s": s}


def fmt(x, n=2, pct=False):
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if pct:
        return f"{x:.0%}"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{n}f}"


def pair_txt(p):
    return f"g = {p[0]}, s = {p[1]}"


# ----------------------------------------------------------------------------- run state


def done_set(run, d):
    return set(D.PAIRS[: run["grid"][d]])


def grid_complete(run, d):
    return run["grid"][d] >= len(D.PAIRS)


def busy(run, valjob):
    return run["active"] or bool(valjob)


def run_panel(run, valjob, dataset, *, compact=False):
    """Start, progress and cache status (ticket 08's job kinds and progress records)."""
    active = busy(run, valjob)
    incomplete = [d for d in D.DATASETS if not grid_complete(run, d)]
    partial = [d for d in D.DATASETS if 0 < run["grid"][d] < len(D.PAIRS)]
    btns = [html.Button("Run all datasets", id={"type": "run", "what": "all"}, className="btn primary",
                        disabled=active),
            html.Button(f"Run {dataset}", id={"type": "run", "what": "one"}, className="btn", disabled=active)]
    if run.get("cancelled") and partial and not active:
        d = partial[0]
        btns.append(html.Button(f"Continue ({run['grid'][d]} of {len(D.PAIRS)} pairs)",
                                id={"type": "run", "what": "continue"}, className="btn"))
    if active:
        btns.append(html.Button("Cancel", id={"type": "run", "what": "cancel"}, className="btn"))
    rows = []
    for i, d in enumerate(D.DATASETS):
        n, v = run["grid"][d], run["val"][d]
        if n >= len(D.PAIRS) and v >= 200:
            phase, val, mx = "grid and validation done", 1, 1
        elif n >= len(D.PAIRS):
            phase, val, mx = (f"validation {v} of 200 replicates" if v else "grid done, not validated"), v, 200
        else:
            phase, val, mx = (f"grid {n} of {len(D.PAIRS)} pairs" if n else "not run"), n, len(D.PAIRS)
        rows.append(html.Div([html.Span(f"{i + 1}/5 {d}", className="ps-run-ds"),
                              html.Progress(value=str(val), max=str(mx), className="ps-prog"),
                              html.Span(phase, className="mute small")], className="ps-run-row"))
    if valjob:
        d, g, s = valjob["pair"]
        rows.append(html.Div([html.Span(f"Validate {d} {pair_txt((g, s))}", className="ps-run-ds"),
                              html.Progress(value=str(valjob["n"]), max="200", className="ps-prog"),
                              html.Span(f"{valjob['n']} of 200 replicates", className="mute small")],
                             className="ps-run-row"))
    cache = ("Results from the app cache: Build " + D.BUILD_ID[:15] + "…, settings key 3fa2c1, method v1."
             if not incomplete else
             "Nothing cached for these settings yet." if not any(run["grid"].values()) else
             f"{5 - len(incomplete)} of 5 grids cached.")
    return html.Div([html.Div(btns, className="row-inline"), *([] if compact else rows),
                     html.Div(cache, className="msg")], className="ps-run")


def fixed_settings():
    items = [("Hidden tags", "Genre Tags + the defining tag"), ("Minimum Months", "0"),
             ("Clustering Weight", "Lift"), ("Algorithm", "Leiden"), ("γ scan", "0.25–3.00, step 0.05 (56)"),
             ("Scan seeds", "10 (stream 3)"), ("Min Multi-Tag Clusters", "3"), ("Validation", "R = 100, S = 100")]
    return html.Dl([x for k, v in items for x in (html.Dt(k), html.Dd(v))], className="kv ps-fixed")


# ----------------------------------------------------------------------------- Pair Constraints


def constraints_panel(draft, confirmed, dataset, *, inline=False):
    """Edit, then confirm (ticket 06): nothing recomputes until Confirm."""
    eff = effective(confirmed, dataset)
    dirty = any(draft[k] != eff[k] for k in D.DEFAULTS)

    def field(k, step, lo, hi):
        default = D.DEFAULTS[k]
        return html.Div([
            html.Label(D.CONSTRAINT_LABEL[k], className="l"),
            html.Div([dcc.Input(id={"type": "cons", "k": k}, type="number", value=draft[k], min=lo, max=hi, step=step,
                                placeholder="off", debounce=True, className="ps-in"),
                      html.Span(f"default {fmt(default) if default is not None else 'off'}", className="mute small")],
                     className="row-inline"),
        ], className="ps-field" + (" changed" if draft[k] != default else ""))

    fields = [field("retention_min", 0.01, 0, 1), field("isolated_max", 0.01, 0, 1), field("lcc_min", 0.01, 0, 1),
              field("neighbours_min", 1, 0, 4), field("mtc_max", 1, 3, 99), field("tolerance", 0.01, 0, 1)]
    override = dataset in confirmed["override"]
    scope = dcc.RadioItems(id={"type": "cons-scope", "i": 0}, value="this" if override else "all", inline=True,
                           className="seg", options=[{"label": "All five datasets", "value": "all"},
                                                     {"label": f"{dataset} only", "value": "this"}])
    label = constraints_label(eff)
    return html.Div([
        html.Div(fields, className="ps-fields-inline" if inline else "ps-fields"),
        html.Div([html.Span("Apply to", className="mute small"), scope], className="row-inline"),
        html.Div([html.Button("Confirm", id={"type": "cons-confirm", "i": 0}, className="btn primary", disabled=not dirty),
                  html.Button("Reset to defaults", id={"type": "cons-reset", "i": 0}, className="btn"),
                  html.Span("Unconfirmed changes" if dirty else "", className="warning small" if dirty else "")],
                 className="row-inline"),
        label,
    ], className="ps-cons")


def effective(confirmed, dataset):
    return confirmed["override"].get(dataset, confirmed["shared"])


def constraints_label(c, short=False):
    changed = D.is_custom(c)
    if not changed:
        return html.Span("Default constraints", className="ps-tag")
    if short:
        return html.Span("Custom constraints", className="ps-tag custom")
    return html.Span(["Custom constraints: ", "; ".join(
        f"{D.CONSTRAINT_LABEL[k].lower()} {fmt(c[k]) if c[k] is not None else 'off'} "
        f"(default {fmt(D.DEFAULTS[k]) if D.DEFAULTS[k] is not None else 'off'})" for k in changed)],
        className="ps-tag custom")


# ----------------------------------------------------------------------------- heatmap


def heatmap(d, metric, sel, done, inspected, *, height=520, text=True, idx=0, same_pair=None, title=None,
            partial_selection=True):
    col, label, descriptive, better = D.METRICS[metric]
    rows = D.grid()
    pairs = set(D.PAIRS)
    xs, ys = D.S_VALUES, D.G_VALUES
    needs_nb = metric in ("na", "na_min")
    z, pend, hover = [], [], []
    for g in ys:
        zr, pr, hr = [], [], []
        for s in xs:
            p = (g, s)
            row = rows[(d, g, s)] if p in pairs else None
            shown = p in done and (not needs_nb or D.neighbours_done(p, done))
            v = row[col] if row and shown else None
            zr.append(float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None)
            pr.append(1 if p in pairs and not shown else None)
            if row is None:
                hr.append("")
            elif not shown:
                hr.append(f"g={g}, s={s}<br>" + ("not computed yet" if p not in done else "waiting for neighbours"))
            else:
                why = sel["why"].get(p, []) if sel else []
                hr.append(f"<b>g={g}, s={s}</b><br>{label}: {fmt(v, 3)}<br>NA {fmt(row['na_mean'], 3)} · "
                          f"{row['Tags']} tags · {fmt(row['Multi-Tag Clusters (Selected Partition)'])} Multi-Tag Clusters"
                          + ("<br>" + "<br>".join("✗ " + D.REASONS[r][1] for r in why) if why else "<br>✓ qualifies"))
        z.append(zr), pend.append(pr), hover.append(hr)
    scale = "Greys" if descriptive else ("Blues" if better is not False else "Blues_r")
    fig = go.Figure()
    fig.add_trace(go.Heatmap(z=pend, x=xs, y=ys, colorscale=[[0, "#eceef2"], [1, "#eceef2"]], showscale=False,
                             hoverinfo="skip", xgap=2, ygap=2))
    fig.add_trace(go.Heatmap(z=z, x=xs, y=ys, colorscale=scale, xgap=2, ygap=2, text=hover, hoverinfo="text",
                             colorbar=dict(thickness=10, len=0.8, title=dict(text="", side="right")),
                             showscale=height > 300))
    cell = max(8, (height - 70) / len(ys))
    if sel:
        why = [(p, r) for p, r in sel["why"].items() if r and p in done]
        if why and text:
            fig.add_trace(go.Scatter(x=[p[1] for p, _ in why], y=[p[0] for p, _ in why], mode="text",
                                     text=["".join(D.REASONS[x][0] for x in r) for _, r in why],
                                     textfont=dict(size=max(7, cell * 0.36), color=WARN), hoverinfo="skip"))
        elif why:
            fig.add_trace(go.Scatter(x=[p[1] for p, _ in why], y=[p[0] for p, _ in why], mode="markers",
                                     marker=dict(symbol="x-thin", size=cell * 0.5, line=dict(width=1, color=WARN)),
                                     hoverinfo="skip"))
        if partial_selection or not sel["partial"]:
            nb = sel["near_best"]
            if nb:
                fig.add_trace(go.Scatter(x=[p[1] for p in nb], y=[p[0] for p in nb], mode="markers", hoverinfo="skip",
                                         marker=dict(symbol="square-open", size=cell * 0.92,
                                                     line=dict(width=2, color=NEAR))))
            if sel["chosen"]:
                c = sel["chosen"]
                fig.add_trace(go.Scatter(x=[c[1]], y=[c[0]], mode="markers", hoverinfo="skip",
                                         marker=dict(symbol="star", size=cell * 0.6, color=NEAR,
                                                     line=dict(width=1, color="#fff"))))
    for p, colr, dash_ in ((same_pair, "#7048e8", "dot"), (inspected, INK, "solid")):
        if p:
            fig.add_shape(type="rect", x0=p[1] - .5, x1=p[1] + .5, y0=p[0] - .5, y1=p[0] + .5,
                          line=dict(color=colr, width=2.5, dash=dash_))
    fig.update_layout(height=height, margin=dict(l=44, r=8, t=28 if title else 8, b=36), plot_bgcolor="#fff",
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False, clickmode="event",
                      title=dict(text=title, font=dict(size=13), x=0.02, y=0.98) if title else None,
                      font=dict(family="system-ui, Segoe UI, sans-serif", size=11, color="#3d4555"))
    fig.update_xaxes(title=dict(text="s · min shared games", font=dict(size=11)), dtick=1, showgrid=False,
                     zeroline=False, range=[1.5, 12.5])
    fig.update_yaxes(title=dict(text="g · min games per tag", font=dict(size=11)), dtick=1 if height > 300 else 3,
                     showgrid=False, zeroline=False, autorange="reversed")
    return dcc.Graph(id={"type": "hm", "ds": d, "i": idx}, figure=fig, config={"displayModeBar": False, "responsive": True}, style={"width": "100%"},
                     className="ps-hm")


def heatmap_key(metric):
    col, label, descriptive, _ = D.METRICS[metric]
    bits = [html.Span([html.B("★", style={"color": NEAR}), " chosen"]),
            html.Span([html.Span("□", style={"color": NEAR, "fontWeight": 700}), " near-best set"]),
            html.Span([html.Span("▢", style={"fontWeight": 700}), " inspected"]),
            html.Span(["Letters: why a pair doesn't qualify — ",
                       ", ".join(f"{v[0]} {v[1]}" for v in D.REASONS.values())], className="mute")]
    if descriptive:
        bits.insert(0, html.Span("Descriptive: not comparable across pairs", className="ps-tag custom"))
    return html.Div(bits, className="ps-key")


def metric_picker(metric, *, dropdown=False):
    opts = [{"label": v[1] + (" (descriptive)" if v[2] else ""), "value": k} for k, v in D.METRICS.items()]
    if dropdown:
        return dcc.Dropdown(id={"type": "metric", "i": 0}, options=opts, value=metric, clearable=False, searchable=False,
                            className="ps-metric-dd")
    main = ["na", "retention", "isolated", "mtc", "snf", "q"]
    return dcc.RadioItems(id={"type": "metric", "i": 0}, value=metric, inline=True, className="seg ps-metric",
                          options=[{"label": D.METRICS[k][1].replace("Fragmentation: ", "")
                                    + (" (descr.)" if D.METRICS[k][2] else ""), "value": k} for k in main])


# ----------------------------------------------------------------------------- CHAMP plot


def champ(d, g, s, *, height=300):
    det = D.pair_detail(d, g, s)
    adm, two_m = det["admissible"], det["two_m"]
    fig = go.Figure()
    if not adm:
        return html.Div("No edges: nothing to plot.", className="msg")
    lo, hi = 0.25, 3.0
    env = [(x["A"] - x["a"] * x["P"]) / two_m for x in adm] + [(x["A"] - x["b"] * x["P"]) / two_m for x in adm]
    ymin, ymax = min(env), max(env)
    pad = (ymax - ymin) * 0.15 or 0.05
    for x in adm:  # faint full lines
        fig.add_trace(go.Scatter(x=[lo, hi], y=[(x["A"] - lo * x["P"]) / two_m, (x["A"] - hi * x["P"]) / two_m],
                                 mode="lines", line=dict(color="#d4d8df", width=1), hoverinfo="skip"))
    sel = next((x for x in adm if x["is_selected"]), None)
    if sel:
        fig.add_vrect(x0=sel["a"], x1=sel["b"], fillcolor=ACC, opacity=0.08, line_width=0)
        fig.add_vline(x=sel["mid"], line=dict(color=ACC, dash="dash", width=1.5))
    for x in adm:  # the envelope, one segment per Optimality Domain
        colr = ACC if x["is_selected"] else ("#2b8a3e" if x["stable"] else "#5c6370")
        width = 4 if x["is_selected"] else 2.5
        fig.add_trace(go.Scatter(
            x=[x["a"], x["b"]], y=[(x["A"] - x["a"] * x["P"]) / two_m, (x["A"] - x["b"] * x["P"]) / two_m],
            mode="lines", line=dict(color=colr, width=width), hoverinfo="text",
            text=(f"Domain {x['a']:.3f}–{x['b']:.3f} (width {x['width']:.3f})<br>{x['n_multi']} Multi-Tag Clusters · "
                  f"hits {x['hits']} of 560<br>γ̂ {fmt(x['gamma_hat'], 3)} · "
                  + ("Stable" if x["stable"] else (x["reason"] or "γ̂ outside its domain"))
                  + (" · <b>Selected</b>" if x["is_selected"] else ""))))
        gh = x["gamma_hat"]
        if gh is not None and lo <= gh <= hi:
            fig.add_trace(go.Scatter(x=[gh], y=[(x["A"] - gh * x["P"]) / two_m], mode="markers", hoverinfo="skip",
                                     marker=dict(size=7, color=colr if x["stable"] else "#fff",
                                                 line=dict(width=1.5, color=colr))))
    fig.update_layout(height=height, margin=dict(l=44, r=8, t=8, b=34), plot_bgcolor="#fff",
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                      font=dict(family="system-ui, Segoe UI, sans-serif", size=11, color="#3d4555"))
    fig.update_xaxes(title=dict(text="γ", font=dict(size=11)), range=[lo, hi], showgrid=False)
    fig.update_yaxes(title=dict(text="Q(γ)", font=dict(size=11)), range=[ymin - pad, ymax + pad], gridcolor="#eef0f3")
    n_stable = sum(x["stable"] for x in adm)
    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar": False, "responsive": True}, style={"width": "100%"}),
        html.Div([f"{len(adm)} Admissible Partitions, {n_stable} Stable. ",
                  html.Span("━ Selected", style={"color": ACC}), " · ", html.Span("━ Stable", style={"color": "#2b8a3e"}),
                  " · ━ other · ● γ̂ inside its domain, ○ outside · dashed: Selected Resolution"],
                 className="mute small"),
    ])


# ----------------------------------------------------------------------------- the selection explained


def explanation(sel, *, short=False):
    d = sel["dataset"]
    c = sel["constraints"]
    rows = D.grid()
    default = not D.is_custom(c)
    which = "the default constraints" if default else "custom constraints"
    caveat = html.P(html.I("Neighbour Agreement measures how little the clustering changes when g or s moves by one. "
                           "It does not show that the Clusters are real."), className="ps-caveat")
    if sel["partial"]:
        return html.Div([html.P([html.B("No selection yet. "),
                                 f"{sel['n_pairs']} of {len(D.PAIRS)} pairs are computed; the selection needs the "
                                 "whole grid."])], className="ps-expl")
    if sel["status"] == "no_qualifying_pair":
        tbl = html.Table([html.Tr([html.Th("Pair Constraint"), html.Th("alone", className="r"),
                                   html.Th("cumulative", className="r")])] +
                         [html.Tr([html.Td(D.REASONS[k][1]), html.Td(sel["alone"][k], className="r"),
                                   html.Td(sel["cumulative"][k], className="r")]) for k in D.REASONS], className="tl")
        return html.Div([
            html.P([html.B("No pair qualifies"), f" under {which}. {sel['n_with_partition']} of {sel['n_pairs']} pairs "
                    "have a Selected Partition. Excluded by each constraint, alone (cumulative):"]), tbl,
            html.P("Loosen a constraint, or inspect any pair in the grid and apply it by hand."),
            constraints_label(c)], className="ps-expl none")
    ch = sel["chosen"]
    row = rows[(d, *ch)]
    wb = D.workbench(d, *ch)
    parts = [f"Information Retention ≥ {c['retention_min']:.2f}", f"isolated tags ≤ {c['isolated_max']:.0%}",
             f"largest component ≥ {c['lcc_min']:.0%} of the tags with an edge",
             f"≥ {c['neighbours_min']} neighbours with a different graph"]
    if c["mtc_max"] is not None:
        parts.append(f"≤ {c['mtc_max']} Multi-Tag Clusters")
    zero = [k for k in ("lcc_share_below_min", "isolated_share_above_max", "retention_below_min") if sel["alone"][k] == 0]
    names = {"lcc_share_below_min": "LCC", "isolated_share_above_max": "isolated-share", "retention_below_min": "retention"}
    zn = [names[k] for k in zero]
    zero_txt = (f" The {' and '.join([', '.join(zn[:-1]), zn[-1]] if len(zn) > 1 else zn)} constraint"
                f"{'s' if len(zn) > 1 else ''} excluded no pair." if zn else "")
    mx = "; ".join(pair_txt(p) for p in sel["max_at"])
    nb = len(sel["near_best"])
    head = html.P([html.B(f"Selected: {pair_txt(ch)}"),
                   f", resolution {row['Selected Resolution']:.3f} (Workbench {fmt(wb['gamma'])})."])
    if short:
        return html.Div([head, html.P(f"NA {row['na_mean']:.2f}, best among {len(sel['qualifying'])} Qualifying Pairs "
                                      f"within {c['tolerance']:.2f}; {nb} near-best, smallest g then s."),
                         constraints_label(c, short=True)], className="ps-expl")
    body = [head,
            html.P(f"{sel['n_with_partition']} of {sel['n_pairs']} pairs have a Selected Partition. "
                   f"{len(sel['qualifying'])} qualify under {which}: {', '.join(parts[:-1])}, and {parts[-1]}.{zero_txt}"),
            html.P(f"The highest Neighbour Agreement among them is {sel['max_na']:.2f} ({mx}). "
                   f"{nb} pair{'s are' if nb != 1 else ' is'} within {c['tolerance']:.2f} of it, and of these the one "
                   "with the smallest g, then the smallest s, is selected."),
            html.P(f"Its Neighbour Agreement is {row['na_mean']:.2f} over {row['na_comparable']} neighbours"
                   + (f" ({row['na_identical_comparable']} with an identical graph)." if row['na_identical_comparable']
                      else ".")),
            ]
    snf = row["Seed-Noise Floor (min ARI)"]
    if snf is not None and snf < 0.5:
        body.append(html.P(f"The Seed-Noise Floor at this resolution is {snf:.2f}: the clustering also depends "
                           "noticeably on the seed."))
    body += [caveat, constraints_label(c)]
    return html.Div(body, className="ps-expl")


# ----------------------------------------------------------------------------- validation


def validation_block(d, g, s, validated, valjob, *, default_pair=None, compact=False, where="main"):
    head = html.H4(f"Validation of {pair_txt((g, s))}", className="ps-h")
    row = D.grid()[(d, g, s)]
    if not row["has_partition"]:
        return html.Div([head, html.P("No Selected Partition: nothing to validate.", className="msg")])
    if not validated:
        running = valjob and tuple(valjob["pair"]) == (d, g, s)
        note = []
        if default_pair and tuple(default_pair) != (g, s):
            note = [html.P(f"Validation ran for {pair_txt(default_pair)}, the pair chosen under the default "
                           "constraints.", className="msg")]
        return html.Div([head, html.P([html.B("Not validated. "), "Null Comparison and Subsample Stability take about "
                                       "40 s for one pair."]), *note,
                         html.Div([html.Button("Validate this pair", id={"type": "validate", **pk(d, g, s), "w": where},
                                               className="btn", disabled=bool(valjob)),
                                   html.Progress(value=str(valjob["n"]), max="200", className="ps-prog")
                                   if running else None], className="row-inline")], className="ps-val")
    v = D.validation(d, g, s)
    gam = row["Selected Resolution"]
    R, S = 100, 100
    k_null = round(v["n_null_with"] / v["n_null"] * R)
    reach = round(v["reach"] / v["n_null"] * R)
    q_lo, q_hi = min(v["null_q"]), max(v["null_q"])
    null_txt = (f"Q at resolution {gam:.3f} is {v['obs_q']:.3f}; "
                + ("no shuffled network reaches it" if not reach else f"{reach} of {R} shuffled networks reach it")
                + f" ({q_lo:.3f} to {q_hi:.3f}). {k_null} of {R} also have a Selected Partition, with narrower domains "
                f"(median {D.med(v['null_w']):.3f} against {v['obs_w']:.3f}; wider than "
                + ("all " + str(k_null) if v["wider_than"] == v["n_null_with"] else f"{v['wider_than']} of {k_null}") + ").")
    rs = v["resel"]
    ok = round(len(rs) / v["n_sub"] * S)
    sub_txt = (f"Re-selected: median ARI {D.med(rs):.2f} ({D.pct(rs, .1):.2f}–{D.pct(rs, .9):.2f}) over {ok} of {S} "
               "subsamples" + (f"; {S - ok} had no Selected Partition." if ok < S else ".")
               + f" At resolution {gam:.3f}: median ARI {D.med(v['fixed']):.2f} "
               f"({D.pct(v['fixed'], .1):.2f}–{D.pct(v['fixed'], .9):.2f}).")
    det = D.pair_detail(d, g, s)
    jac = D.cluster_jaccard(d, g, s, [c["label"] for c in det["clusters"]])
    dissolved = [j for j in jac if j["resel"] <= 0.5]
    tags = {c["label"]: c["tags"] for c in det["clusters"]}
    tbl = html.Table([html.Tr([html.Th("Cluster"), html.Th("tags"), html.Th("Jaccard, re-selected", className="r"),
                               html.Th("at γ", className="r"), html.Th("≤ 0.5 in", className="r"),
                               html.Th("retention", className="r"), html.Th("absent", className="r"), html.Th("")])] +
                     [html.Tr([html.Td(j["label"]), html.Td(", ".join(tags[j["label"]][:4])
                                                             + (" …" if len(tags[j["label"]]) > 4 else ""),
                                                             className="name small"),
                               html.Td(f"{j['resel']:.2f}", className="r"), html.Td(f"{j['fixed']:.2f}", className="r"),
                               html.Td(f"{j['low_resel']} of {S - j['absent']}", className="r"),
                               html.Td(f"{j['retention']:.2f}", className="r"), html.Td(j["absent"], className="r"),
                               html.Td(html.Span("Dissolved", className="ps-tag bad") if j["resel"] <= .5 else "")])
                      for j in jac], className="tl")
    src = (html.Div("PROTOTYPE: illustrative numbers." if v["illustrative"] else
                    "PROTOTYPE: ticket 07 pilot (5 nulls, 5 subsamples) scaled to R = S = 100; Cluster Jaccard "
                    "illustrative.", className="ps-proto-note"))
    verdicts = html.Div([
        html.Span("Q not above the null" if reach else f"Q above all {R} null replicates",
                  className="ps-tag " + ("bad" if reach else "")),
        html.Span(f"{len(dissolved)} of {len(jac)} Clusters dissolved when re-selected",
                  className="ps-tag " + ("bad" if dissolved else "")),
    ], className="row-inline")
    if compact:
        return html.Div([head, verdicts, html.P(f"Subsamples: re-selected median ARI {D.med(rs):.2f}, at γ "
                                                f"{D.med(v['fixed']):.2f}.", className="small"), src], className="ps-val")
    return html.Div([
        head, verdicts,
        html.P([html.B("Null Comparison"), f" ({R} shuffled networks, same g and s). ", null_txt]),
        html.P(html.I("This shows only that the network is not random, not that its Clusters are real."),
               className="ps-caveat"),
        html.P([html.B("Subsample Stability"), f" ({S} random 80% subsets of the games, g′ = {v['gs'][0]}, "
                f"s′ = {v['gs'][1]}). ", sub_txt]),
        tbl,
        html.P(html.I("This measures how much the clustering depends on which games are in the dataset. It does not "
                      "show that the Clusters are real either."), className="ps-caveat"),
        src,
    ], className="ps-val")


# ----------------------------------------------------------------------------- an inspected pair


def status_badges(sel, d, g, s):
    p = (g, s)
    why = sel["why"].get(p) if sel else None
    out = []
    if sel and sel.get("chosen") == p:
        out.append(html.Span("★ Chosen", className="ps-tag chosen"))
    elif sel and p in sel.get("near_best", []):
        out.append(html.Span("Near-best", className="ps-tag near"))
    if why == []:
        out.append(html.Span("Qualifying Pair", className="ps-tag"))
    for r in why or []:
        out.append(html.Span(f"{D.REASONS[r][0]} {r}", className="reason mono"))
    return html.Div(out, className="row-inline")


def apply_button(d, g, s, *, big=False):
    wb = D.workbench(d, g, s)
    if not wb["ok"]:
        return html.Div([html.Button("Apply to Workbench", className="btn", disabled=True),
                         html.Span(f"No Selected Partition: {wb['reason']}", className="reason mono")],
                        className="row-inline")
    line = (f"Workbench γ {wb['gamma']:.2f}, {wb['seed']}: reproduces the Selected Partition ✓" if wb["reproduced"]
            else f"Workbench γ {wb['gamma']:.2f}, {wb['seed']}: not_reproduced, shows a different partition "
                 f"(ARI {wb['ari']:.2f})")
    return html.Div([html.Button("Apply to Workbench", id={"type": "apply", **pk(d, g, s)},
                                 className="btn primary" + (" ps-big" if big else "")),
                     html.Span(line, className="small " + ("mute" if wb["reproduced"] else "warning"))],
                    className="row-inline")


def pair_metrics(d, g, s):
    r = D.grid()[(d, g, s)]
    items = [
        ("Neighbour Agreement", f"{fmt(r['na_mean'])} (min {fmt(r['na_min'])}) over {r['na_comparable']} neighbours"
         + (f", {r['na_identical_comparable']} identical" if r["na_identical_comparable"] else "")),
        ("Information Retention", fmt(r["Information Retention"])),
        ("Tags · edges", f"{r['Tags']} · {r['Edges']}"),
        ("Isolated share", fmt(r["Isolated share of tags"], pct=True)),
        ("LCC share", fmt(r["LCC share of non-isolated tags"])),
        ("Multi-Tag Clusters", fmt(r["Multi-Tag Clusters (Selected Partition)"])),
        ("Selected Resolution", f"{fmt(r['Selected Resolution'], 3)} (domain width {fmt(r['Domain width (b − a)'], 3)})"),
        ("Hits", f"{fmt(r['Hits of the Selected Partition (of 560)'])} of 560 scan runs"),
        ("Seed-Noise Floor", f"{fmt(r['Seed-Noise Floor (min ARI)'])} ({r['Seed-noise exact reproductions (of 10)']} of 10 exact)"),
    ]
    desc = [("Q", fmt(r["Q at the Selected Resolution (descriptive)"], 3)),
            ("Weighted Coverage", fmt(r["Weighted Coverage (descriptive)"])),
            ("Jaccard silhouette", fmt(r["Jaccard silhouette (descriptive)"], 3))]
    return html.Div([
        html.Dl([x for k, v in items for x in (html.Dt(k), html.Dd(v))], className="kv"),
        html.Div("Descriptive: not comparable across pairs", className="i-h"),
        html.Dl([x for k, v in desc for x in (html.Dt(k), html.Dd(v))], className="kv"),
    ])


def clusters_list(d, g, s, *, limit=None):
    det = D.pair_detail(d, g, s)
    cl = det["clusters"][:limit] if limit else det["clusters"]
    return html.Div([
        html.Div([html.Div([html.B(c["label"]), html.Span(f" {len(c['tags'])} tags", className="mute small")]),
                  html.Div(", ".join(c["tags"]), className="small")], className="ps-cluster") for c in cl
    ] + [html.Div(f"+ {det['n_one']} One-Tag Clusters", className="mute small")])
