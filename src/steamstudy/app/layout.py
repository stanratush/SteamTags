"""The Tag Network app's layout: the Workbench and Analysis Report mode over one set of components, and the
Parameter Selection mode (`ps_view`) beside them.

The main column is a flex column whose blocks are re-ordered and shown or hidden by the mode, so the
graph, the tables and the inspector are single component instances shared by both modes. In the
Workbench the tables sit in one resizable pane (`tables-area`); in Analysis Report mode that pane is
`display: contents`, so its blocks take part in the page order.

The layout is built in the Interface Language of the page (`steamstudy.i18n`, read from the cookie when the page is
served). Every translated static prop is registered in `RELABEL` as (component id, prop, message) while it is built
(`Labels`); one callback (callbacks.py `relabel`) sets them all again when the language is switched, so a new static
label needs no new wiring. A text without an id of its own gets a stable one (`i18n-<n>`, in build order).

The Workbench changes form with the window width (`assets/workbench.js` sets `body[data-form]`):
wide (>= 1280 px) is three panes; medium (1024-1279 px) turns the Controls into a pill bar and floats
the Inspector; narrow (< 1024 px, or "Graph only") also turns the tables into a bottom sheet.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
from dash import dcc, html

from steamstudy.app import help as H
from steamstudy.app.guide import LABELS
from steamstudy.app.loader import BuildContext
from steamstudy.app.relabel import RELABEL, Labels, Message, message_value, msg  # noqa: F401
from steamstudy.app.ps_view import mode_layout
from steamstudy.app.renderer import graph_component, thickness_key
from steamstudy.app.view import column_defs, metric_header
from steamstudy.i18n import LANGS, Text, text

WB_TABS = [("quality", msg("Cluster quality")), ("clusters", msg("Clusters")), ("rs", msg("Removal sensitivity")),
           ("nodes", msg("Nodes")), ("edges", msg("Edges")), ("nin", msg("Not in network"))]
SLIDERS = ("min-games", "min-shared", "min-months")
PILLS = ("dataset", "min-months", "min-games", "min-shared", "hidden", "weight", "algorithm", "gamma", "seed")

def ui_words(tx: Text) -> dict[str, Any]:
    """The words the browser code shows (the `ui-words` store): JS and CSS hold none of their own. `tip` labels each
    kind of tooltip line (help.py), `more` is the tooltip's footer and `info` the ⓘ's aria-label; `pills` are the
    pill bar's words (workbench.js `pills`), `{…}` filled in the browser; `decimal` is the language's decimal mark
    and `lang` its code, for the page's lang attribute."""
    genre = lambda n: tx.n(n, one="{n} Genre Tag", other="{n} Genre Tags", n="{n}")  # noqa: E731
    return {"title": tx("Tag Network"), "lang": tx.lang, "tip": LABELS[tx.lang],
            "more": tx("Click for the full User Guide entry"),
            "info": tx("User Guide entry for {name}", name="{name}"), "decimal": tx.decimal,
            "pills": {"genre": [genre(1), genre(2)], "defining": tx("{hidden} + defining", hidden="{hidden}"),
                      "lift": tx("Lift"), "shared": tx("Shared games"),
                      "of": tx("{n} of {total}", n="{n}", total="{total}")},
            "edges": edge_words(tx),
            "map": {"title": tx("Cluster map"), "pool": tx("pool"),
                    "tags": [tx.n(1, one="{n} tag", other="{n} tags", n="{n}"),
                             tx.n(2, one="{n} tag", other="{n} tags", n="{n}")],
                    "ratio": tx("ratio {value}", value="{value}"),
                    "pool_region": [tx.n(1, one="one-tag clusters · {n} tag", other="one-tag clusters · {n} tags",
                                         n="{n}"),
                                    tx.n(2, one="one-tag clusters · {n} tag", other="one-tag clusters · {n} tags",
                                         n="{n}")],
                    "empty": tx("No links between clusters."),
                    "help": {"tip": H.tip("graph.cluster_map", tx), "help": H.target("graph.cluster_map")}}}


# The Cluster map toggle's state for assistive technology (graph.js keeps aria-expanded current).
MAP_ARIA: dict[str, Any] = {"aria-expanded": "false", "aria-controls": "cluster-map"}

# The Edge appearance card's controls and the help key of each (help.py `edges.*`).
EDGE_HELP = {"width": "edges.width", "scale": "edges.scale", "color": "edges.color", "strength": "edges.strength",
             "between": "edges.between", "hide": "edges.hide"}


def edge_words(tx: Text) -> dict[str, Any]:
    """The legend key's and the Edge appearance card's words (graph.js `edgeKey`, `renderCard`), `{…}` filled in the
    browser, and each control's two help layers."""
    def hidden(n: int) -> str:
        return tx.n(n, one="{n} link hidden from the drawing", other="{n} links hidden from the drawing", n="{n}")

    return {"key": tx("Edge thickness: {measure}", measure="{measure}"), "shared": tx("shared games"),
            "lift": tx("lift"), "hidden_short": tx("{n} hidden", n="{n}"), "hidden": [hidden(1), hidden(2)],
            "px": tx("{lo}–{hi} px", lo="{lo}", hi="{hi}"),
            "filter": tx("Minimum shared games ({n}) is the separate filter, part of the Network State.", n="{n}"),
            "axis": tx("{measure} per link · {n} links", measure="{measure}", n="{n}"),
            "drag": tx("Drag the handle to stop drawing the links below a value (view only)."),
            "hidden_link": tx("hidden from the drawing"),
            "width": tx("Width"), "strength": tx("Strength"), "between": tx("Links between Clusters"),
            "scale": tx("Scaling"), "color": tx("Colour"), "hide": tx("Hide links below"),
            "less": tx("Less"), "more": tx("More"),
            "scales": {"linear": tx("linear"), "sqrt": "√", "log": "log"},
            "colors": {"one": tx("one colour"), "cluster": tx("By Cluster"), "within": tx("within vs between"),
                       "value": tx("by value")},
            "help": {name: {"tip": H.tip(key, tx), "help": H.target(key)} for name, key in EDGE_HELP.items()}}


def grid_locale(tx: Text) -> dict[str, str]:
    """ag-grid's `localeText`: only the words our grids show (the filter menus and the empty grid)."""
    return {"contains": tx("Contains"), "notContains": tx("Not contains"), "equals": tx("Equals"),
            "notEqual": tx("Not equal"), "startsWith": tx("Starts with"), "endsWith": tx("Ends with"),
            "lessThan": tx("Less than"), "lessThanOrEqual": tx("Less than or equal to"),
            "greaterThan": tx("Greater than"), "greaterThanOrEqual": tx("Greater than or equal to"),
            "inRange": tx("In range"), "blank": tx("Blank"), "notBlank": tx("Not blank"),
            "andCondition": tx("AND"), "orCondition": tx("OR"), "filterOoo": tx("Filter..."),
            "noRowsToShow": tx("No Rows To Show")}


def grid_options(tx: Text) -> dict[str, Any]:
    return {"tooltipShowDelay": 300, "rowSelection": {"mode": "singleRow", "checkboxes": False,
                                                       "enableClickSelection": True},
            "animateRows": False, "localeText": grid_locale(tx)}


def _rs_extra(tx: Text) -> list[dict[str, Any]]:
    return [{"field": "membership_stability", "headerName": "membership_stability (joined)",
             **metric_header("app_export/nodes.csv", "membership_stability", tx=tx),
             "sortable": True, "filter": "agNumberColumnFilter", "type": "rightAligned"}]


def _edge_columns() -> list[str]:
    return ["source_tag_id", "source_tag", "target_tag_id", "target_tag", "shared_games", "lift", "source_cluster",
            "target_cluster", "is_intra_cluster"]


# grid id -> its column definitions in a language; a language switch sends them again (callbacks.py `grid_words`).
GRIDS: dict[str, Callable[[Text], list[dict[str, Any]]]] = {
    "nin-grid": lambda tx: column_defs("app_export/not_in_network.csv", tx=tx),
    "connections-grid": lambda tx: column_defs("app_export/cluster_connections.csv", tx=tx),
    "null-grid": lambda tx: column_defs("app_export/null_model.csv", tx=tx),
    "seed-grid": lambda tx: column_defs("app_export/seed_noise.csv", tx=tx),
    "clusters-grid": lambda tx: column_defs("app_export/clusters.csv", tx=tx),
    "rs-grid": lambda tx: column_defs("app_export/removal_sensitivity.csv", tx=tx, extra=_rs_extra(tx)),
    "nodes-grid": lambda tx: column_defs("app_export/nodes.csv", tx=tx),
    "edges-grid": lambda tx: column_defs("app_export/edges.csv", _edge_columns(), tx=tx),
}


def _language(L: Labels, lang: str) -> html.Div:
    """The EN | BG switch: writes the `lang` store and the cookie (workbench.js `language`). Its dotted label carries
    both help layers, like an analytical control's; its tooltip is the registry's first entry."""
    tip = L.prop("lang-term", "data-tip", lambda tx: H.tip("header.lang", tx))
    return html.Div([
        html.Span(L.prop("lang-term", "children", msg("Language")), id="lang-term", className="term", tabIndex="0",
                  **{"data-tip": tip, "data-help": H.target("header.lang")}),
        _seg("lang-switch", [{"label": code.upper(), "value": code} for code in LANGS], lang),
    ], id="lang-box", className="lang-box")


def _data(**attrs: str) -> dict[str, Any]:
    """HTML data-* attributes as Dash keyword arguments: `_data(graph_overlay="top")` -> data-graph-overlay."""
    return {"data-" + name.replace("_", "-"): value for name, value in attrs.items()}


def _term(L: Labels, text_: str, key: str) -> tuple[list[Any], dict[str, Any]]:
    """A control's label text, dotted, and the attributes that give the label both help layers."""
    return [L.span(text_, className="term")], {"tabIndex": "0", **L.help(key)}


def _control_key(control: str) -> str | None:
    """A control's help key (`steamstudy.app.help`), if its effect needs interpretation."""
    return f"control.{control}" if f"control.{control}" in H.HELP else None


def _label(L: Labels, text_: str, key: str, *extra: Any, **kw: Any) -> html.Label:
    """A control's label with both help layers: hover or focus shows its In short, a click opens its entry."""
    children, help_ = _term(L, text_, key)
    return html.Label([*children, *extra], className="l", **help_, **kw)


def _slider(L: Labels, id_: str, label: str, lo: int, hi: int, value: int) -> list[Any]:
    """A slider whose label shows its value while dragging; the value itself is sent on release."""
    key = _control_key(id_)
    children, help_ = _term(L, label, key) if key else ([L.span(label)], {})
    return [html.Label([*children, html.B(str(value), id=f"{id_}-value", className="num")], htmlFor=id_,
                       className="sl-label", **help_),
            dcc.Slider(id=id_, min=lo, max=hi, step=1, value=value, updatemode="mouseup", allow_direct_input=False,
                       tooltip=None, marks={lo: str(lo), hi: str(hi)}, className="sl")]


def _item(L: Labels, pill: str, pill_label: str, value: str, children: list[Any]) -> html.Div:
    """One control: shown inline in the Controls panel, or as a pill with a popover in the pill bar. The pill of a
    control with help shows its In short on hover or focus; its click opens the popover, whose label opens the entry.
    The pill's value is kept current by workbench.js `pills`."""
    key = _control_key(pill)
    btn_id = f"pill-btn-{pill}"
    tip = _data(tip=L.prop(btn_id, "data-tip", lambda tx: H.tip(key, tx))) if key else {}
    label: list[Any] = [L.span(pill_label), " "] if pill_label else []
    return html.Div([
        html.Button([*label, html.B(value, id=f"pill-{pill}", className="num")], id=btn_id,
                    className="pill-btn", **_data(pill=pill), **tip),
        html.Div(children, className="pill-pop"),
    ], className="ctl-item")


def _section(L: Labels, title: str, items: list[Any]) -> html.Div:
    return html.Div([html.H4(L.span(title), className="ctl-h"), *items], className="ctl-section")


def _seg(id_: str, options: list[dict[str, Any]], value: Any, **kw: Any) -> dcc.RadioItems:
    """RadioItems drawn as a segmented control."""
    return dcc.RadioItems(id=id_, options=options, value=value, inline=True, className="seg", **kw)


def _help(L: Labels, panel: str) -> html.Button:
    id_ = {"type": "help", "panel": panel}
    return html.Button("?", id=id_, className="help", title=L.prop(id_, "title", msg("Open the User Guide section")))


def _grid(L: Labels, id_: str, height: str = "320px", **kw: Any) -> dag.AgGrid:
    return dag.AgGrid(id=id_, columnDefs=GRIDS[id_](L.tx), rowData=[],
                      defaultColDef={"sortable": True, "filter": True, "resizable": True},
                      dashGridOptions=grid_options(L.tx), style={"height": height, "width": "100%"}, className="grid",
                      **kw)


def _block(L: Labels, id_: str, heading: str, children: list[Any], help_panel: str | None = None) -> html.Div:
    head: list[Any] = [L.span(heading)]
    if help_panel:
        head.append(_help(L, help_panel))
    return html.Div([html.H3(head, className="section-heading"), *children], id=id_, className="panel")


def _button(L: Labels, id_: str, label: str, className: str = "btn", title: str | None = None, **kw: Any) -> html.Button:
    """A button with a registered label (and title)."""
    if title:
        kw["title"] = L.prop(id_, "title", title)
    return html.Button(L.prop(id_, "children", label), id=id_, className=className, **kw)


def defining_options(defining: Any, tx: Text) -> list[dict[str, Any]]:
    """The defining-tag checkbox: its label names the dataset's defining tag (callbacks.py `defining_options`)."""
    return [{"label": tx("hide defining tag ({tag})", tag=defining.name) if defining else tx("no defining tag"),
             "value": 1, "disabled": defining is None}]


def _controls(L: Labels, ctx: BuildContext) -> html.Div:
    tx = L.tx
    first = ctx.datasets[0].key
    s = ctx.default_settings(first)
    defining = ctx.dataset(first).defining_tag
    genre_ids = [t.id for t in ctx.genre_tags]
    hidden = [t for t in genre_ids if t in s.hidden_tag_ids]
    hides_defining = bool(defining and defining.id in s.hidden_tag_ids)
    hidden_pill = tx.n(len(hidden), one="{n} Genre Tag", other="{n} Genre Tags")
    data = _section(L, msg("Data"), [
        _item(L, "dataset", "", ctx.dataset(first).label, [
            html.Label(L.span(msg("Dataset")), htmlFor="dataset", className="l"),
            dcc.Dropdown(id="dataset", options=[{"label": d.label, "value": d.key} for d in ctx.datasets],
                         value=first, clearable=False, searchable=False)]),
        _item(L, "min-months", msg("Months ≥"), str(s.min_months),
              _slider(L, "min-months", msg("Minimum Months Filter"), 0, 60, s.min_months)),
    ])
    filters = _section(L, msg("Filters"), [
        _item(L, "min-games", msg("Min games"), str(s.min_games_per_tag),
              _slider(L, "min-games", msg("Minimum games per tag"), 1, 40, s.min_games_per_tag)),
        _item(L, "min-shared", msg("Min shared"), str(s.min_shared_games),
              _slider(L, "min-shared", msg("Minimum shared games"), 1, 30, s.min_shared_games)),
        _item(L, "hidden", msg("Hidden"), tx("{hidden} + defining", hidden=hidden_pill) if hides_defining else hidden_pill, [
            html.Label([L.span(msg("Hidden Genre Tags")), " ",
                        html.Span(tx("{n} of {total}", n=len(hidden), total=len(genre_ids)), id="genre-count",
                                  className="mute num")], className="l"),
            dcc.Checklist(id="genre-hidden", options=[{"label": t.name, "value": t.id} for t in ctx.genre_tags],
                          value=hidden, inline=True, className="chips"),
            dcc.Checklist(id="defining-hidden", options=defining_options(defining, tx),
                          value=[1] if hides_defining else [], className="check"),
        ]),
    ])
    clustering = _section(L, msg("Clustering"), [
        _item(L, "weight", msg("Weight"), tx("Shared games") if s.clustering_weight == "shared_games" else tx("Lift"), [
            _label(L, msg("Clustering weight"), "control.weight"),
            _seg("weight", L.options("weight", [("shared_games", msg("Shared games")), ("lift", msg("Lift"))]),
                 s.clustering_weight)]),
        _item(L, "algorithm", "", s.algorithm.capitalize(), [
            _label(L, msg("Clustering algorithm"), "control.algorithm"),
            _seg("algorithm", [{"label": "Louvain", "value": "louvain"}, {"label": "Leiden", "value": "leiden"}],
                 s.algorithm)]),
        html.Div([
            _item(L, "gamma", msg("γ"), tx.fixed(s.resolution, ".2f"), [
                _label(L, msg("Resolution γ"), "control.gamma", htmlFor="gamma"),
                dcc.Input(id="gamma", type="number", min=0.01, step=0.01, value=s.resolution, debounce=True)]),
            _item(L, "seed", msg("Seed"), str(s.seed), [
                _label(L, msg("Seed"), "control.seed", htmlFor="seed"),
                dcc.Input(id="seed", type="number", min=0, step=1, value=s.seed, debounce=True)]),
        ], className="two"),
    ])
    state = _section(L, msg("State"), [
        _item(L, "state", msg("State"), "…", [
            html.Label(L.span(msg("Removed tags")), className="l"),
            html.Div([dcc.Dropdown(id="restore-pick", options=[],
                                   placeholder=L.prop("restore-pick", "placeholder", msg("pick a removed tag"))),
                      _button(L, "restore-btn", msg("Restore"))], className="row-inline"),
            html.Div([_button(L, "reset-btn", msg("Reset all")),
                      _button(L, "export-btn", msg("Export this state"), "btn primary")], className="stack"),
            dcc.Upload(_button(L, "open-btn", msg("Open Network State…"), "btn wide"), id="open-upload", accept=".zip,.json",
                       multiple=False),
            html.Div(id="open-message", className="msg"),
            _button(L, "clear-cache-btn", msg("Clear app cache"), "btn quiet"),
            html.Div(id="cache-message", className="msg"),
        ]),
    ])
    return html.Div([
        html.Div([html.B(L.span(msg("Controls"))), _help(L, "controls")], className="ctl-title"),
        data, filters, clustering, state,
    ], id="controls-panel", className="controls")


def _thickness_legend(L: Labels, ctx: BuildContext) -> html.Div:
    """What edge width shows (`thickness_key`; graph.js `edgeKey` keeps it current and sums up a look that is not
    the default) and the Edges toggle that opens the Edge appearance card. A view choice only: never part of the
    Network State."""
    label, _ = thickness_key(ctx.default_settings(ctx.datasets[0].key).clustering_weight, False, L.tx)
    aria: dict[str, Any] = {"aria-expanded": "false", "aria-controls": "edge-card"}  # graph.js keeps it current
    return html.Div([
        html.Span(label, id="thickness-label", className="lkey term", tabIndex="0",
                  **{"data-tip": L.prop("thickness-label", "data-tip", lambda tx: H.tip("legend.thickness", tx)),
                     "data-help": H.target("legend.thickness")}),
        html.Button(L.prop("edge-card-toggle", "children", msg("Edges")), id="edge-card-toggle", className="lchip",
                    title=L.prop("edge-card-toggle", "title", msg("Edge appearance: width, scaling, colour, strength")),
                    **aria),
    ], className="legend thickness-key")


def _edge_card(L: Labels, ctx: BuildContext) -> html.Div:
    """The Edge appearance card (variant C): a transient overlay over the graph, so opening or closing it never
    changes the canvas, the layout or the fit. Its header holds the show-shared switch (offered only under lift) and
    the card's Reset; graph.js fills the body (the histogram, the hide handle and the controls) from the ui-words
    store."""
    _, style = thickness_key(ctx.default_settings(ctx.datasets[0].key).clustering_weight, False, L.tx)
    return html.Div([
        html.Div([html.B(L.span(msg("Edge appearance"))),
                  dcc.Checklist(id="thickness-shared",
                                options=L.options("thickness-shared", [(1, msg("show shared games"))]), value=[],
                                className="check", style=style),
                  html.Button(L.prop("edge-card-reset", "children", msg("Reset")), id="edge-card-reset",
                              className="btn small", title=L.prop("edge-card-reset", "title",
                                                                  msg("Back to the default look")))],
                 className="edge-card-head"),
        html.Div(id="edge-card-body", className="edge-card-body"),
    ], id="edge-card", className="ov edge-card", role="dialog",
        **_data(graph_overlay="bottom", graph_transient="yes"))


def build_layout(ctx: BuildContext, lang: str = "en") -> html.Div:
    """The page in the Interface Language `lang` (read from the cookie when it is served)."""
    L = Labels(text(lang))
    language = _language(L, lang)
    graph_block = html.Div([
        html.H3([L.span(msg("3 Network")), _help(L, "network")], className="section-heading"),
        html.Div(id="summary-row", className="sumrow"),
        html.Div(id="state-sentence", className="state-line"),
        html.Div([
            *graph_component(),
            html.Div([_seg("layout-mode", L.options("layout-mode", [("global", msg("Global")),
                                                                    ("separated", msg("Cluster-separated"))]), "global"),
                      _button(L, "relayout-btn", msg("Tidy"),
                              title=msg("Settle the graph around the nodes you dragged; positions only")),
                      html.Button(L.prop("map-toggle", "children", msg("Cluster map")), id="map-toggle",
                                  className="btn", title=L.prop("map-toggle", "title",
                                                                msg("A map of the clusters and how they connect")),
                                  **MAP_ARIA),
                      html.Button("⤢", id="fit-btn", className="btn",
                                  title=L.prop("fit-btn", "title", msg("Fit the graph to the view")))],
                     className="ov ov-tr", **_data(graph_overlay="top")),
            # The Cluster map card (graph.js `drawMap`): a transient overlay, like the Edge appearance card.
            html.Div([html.Div([html.B(L.term(msg("Cluster map"), "graph.cluster_map"))], className="map-head"),
                      html.Div(id="cluster-map-body")],
                     id="cluster-map", className="ov cluster-map", role="dialog",
                     **_data(graph_overlay="top", graph_transient="yes")),
            html.Div([html.Div(id="legend", className="legend"), _thickness_legend(L, ctx)], className="ov ov-bl",
                     **_data(graph_overlay="bottom")),
            _edge_card(L, ctx),
            # Shown while a callback runs (callbacks.py: `running`); never a graph overlay, so it never resizes the
            # canvas the layout is made for. role="status" is a polite live region: screen readers announce the label.
            html.Div([html.Span(L.prop("busy-clustering", "children", msg("Clustering…")), id="busy-clustering",
                                hidden=True),
                      html.Span(L.prop("busy-layout", "children", msg("Laying out…")), id="busy-layout", hidden=True)],
                     className="busy graph-busy", role="status"),
        ], className="graph-stage"),
    ], id="blk-graph", className="panel graph-block")

    rs_block = _block(L, "blk-rs", msg("5 Removal sensitivity"), [
        html.Div([_button(L, "rs-run", msg("Run"), "btn primary"),
                  html.Button(id="rs-continue", className="btn", style={"display": "none"}),
                  _button(L, "rs-cancel", msg("Cancel")),
                  html.Span(id="rs-estimate", className="mute")], className="row-inline"),
        html.Progress(id="rs-progress", value="0", max="1", style={"width": "100%"}),
        html.Span(id="rs-progress-label", className="mute small"), dcc.Store(id="rs-progress-store"),
        html.Div(id="rs-banner", className="warning", style={"display": "none"}),
        html.Div(id="noise-line-rs", className="qline"),
        html.Div([dcc.Checklist(id="rs-beyond", options=L.options("rs-beyond", [(1, msg("beyond noise only"))]), value=[],
                                inline=True, className="check"),
                  dcc.Dropdown(id="rs-cluster", options=[], style={"width": "200px"},
                               placeholder=L.prop("rs-cluster", "placeholder", msg("all clusters")))],
                 className="row-inline"),
        html.Div(_grid(L, "rs-grid", height="300px"), id="rs-grid-wrap"),
        html.Div(id="rs-footer", className="qline"),
    ], help_panel="removal")

    tables = html.Div([
        html.Div([html.Span(id="sheet-grip", className="grip",
                            title=L.prop("sheet-grip", "title", msg("Open or close the tables"))),
                  dcc.RadioItems(id="wb-tab", options=L.options("wb-tab", WB_TABS), value="quality", inline=True,
                                 className="tabs-nav")],
                 id="blk-tabs", className="panel"),
        _block(L, "blk-filters", msg("2 Filters"), [html.Div(id="filters-summary"), _grid(L, "nin-grid")],
               help_panel="filters"),
        _block(L, "blk-quality", msg("4 Cluster quality"), [
            html.Div(id="quality-detail", className="qline"),
            _grid(L, "connections-grid", height="200px"),
            html.Details([html.Summary(L.span(msg("Null model and seed-noise replicates"))),
                          _grid(L, "null-grid", height="200px"),
                          _grid(L, "seed-grid", height="200px")]),
        ], help_panel="quality"),
        _block(L, "blk-clusters", msg("Clusters"), [_grid(L, "clusters-grid")], help_panel="clusters"),
        rs_block,
        _block(L, "blk-nodes", msg("6 All nodes and edges"), [_grid(L, "nodes-grid")], help_panel="nodes"),
        _block(L, "blk-edges", msg("Edges"), [_grid(L, "edges-grid")], help_panel="edges"),
    ], id="tables-area", className="tables-area", **_data(graph_overlay="bottom"))

    main = html.Div([
        _block(L, "blk-dataset", msg("1 Dataset"), [html.Div(id="dataset-summary")], help_panel="dataset"),
        graph_block,
        html.Div(id="tables-handle", className="tables-handle",
                 title=L.prop("tables-handle", "title", msg("Drag to resize the tables"))),
        tables,
        _block(L, "blk-export", msg("7 Export"), [_button(L, "export-btn-report", msg("Export this state"), "btn primary"),
                                            html.Div(id="export-summary")], help_panel="export"),
    ], id="main", className="main")

    inspector = html.Div([
        html.Div([html.B(L.span(msg("Inspector"))), _help(L, "inspector"),
                  # Shown while a selection, then the Inspector's content for it, is on its way (callbacks.py:
                  # `running`).
                  html.Div([html.Span(L.prop("busy-selecting", "children", msg("Selecting…")), id="busy-selecting",
                                      hidden=True),
                            html.Span(L.prop("busy-inspector", "children", msg("Loading…")), id="busy-inspector",
                                      hidden=True)], className="busy insp-busy", role="status"),
                  html.Button("×", id="inspector-close", className="x",
                              title=L.prop("inspector-close", "title", msg("Close")))], className="insp-title"),
        html.Div(id="inspector-body"),
        html.Div([_button(L, "remove-btn", msg("Remove this tag"), style={"display": "none"}),
                  _button(L, "rs-run-tag", msg("Run for this tag"), style={"display": "none"})],
                 className="row-inline"),
    ], id="inspector-panel", className="inspector docked", **_data(graph_overlay="right", graph_transient="yes"))

    stores = [
        dcc.Store(id="build-path", data=str(ctx.path)),
        dcc.Store(id="builds-root", data=str(ctx.path.resolve().parents[1])),  # <root>/builds: where exports' Builds are found
        dcc.Store(id="state-meta"), dcc.Store(id="state-tables"), dcc.Store(id="elements-base"),
        dcc.Store(id="cluster-connections"),  # the Cluster map's rows (graph.js `drawMap`), written by the recompute
        dcc.Store(id="relayout"), dcc.Store(id="selection"), dcc.Store(id="floating-open", data=False),
        dcc.Store(id="graph-only-on", data=False),
        dcc.Store(id="removed", data=[]), dcc.Store(id="rs-view"), dcc.Store(id="rs-request"),
        dcc.Store(id="rs-done"), dcc.Store(id="pending-open"), dcc.Store(id="verify"),
        # {"target": "<guide file>#<anchor>", "n": click time, "follow": a link inside the modal}, set by workbench.js
        dcc.Store(id="help-target"),
        dcc.Store(id="help-history", data=[]),  # the entries opened in the modal, for ← Back
        dcc.Store(id="lang", data=lang),  # the Interface Language: a view choice, never part of the Network State
        dcc.Store(id="ui-words", data=L.prop("ui-words", "data", ui_words)),
        dcc.Download(id="download"),
    ]
    header = html.Header([
        html.Div([html.B(L.prop("brand-title", "children", msg("Tag Network")), id="brand-title", className="title"),
                  html.Span(L.prop("brand-build", "children", lambda tx: tx("Build {build_id}", build_id=ctx.build_id)),
                            id="brand-build", className="mute")],
                 className="brand"),
        _seg("mode", L.options("mode", [("workbench", msg("Workbench")), ("report", msg("Analysis Report mode")),
                                        ("selection", msg("Parameter Selection"))]), "workbench"),
        language,
        html.Div(dcc.Dropdown(id="tag-search", options=[], searchable=True, clearable=False, className="tag-search",
                              placeholder=L.prop("tag-search", "placeholder", msg("Find a tag…")),
                              labels=L.prop("tag-search", "labels", dropdown_labels)),
                 id="search-slot", className="search-slot"),
        html.Div([
            html.Span(id="verify-result", className="small"),
            html.Span(id="error-message", className="error small"),
            dcc.Checklist(id="panels", options=L.options("panels", [
                ("controls", msg("Controls")), ("inspector", msg("Inspector")), ("tables", msg("Tables"))]),
                          value=["controls", "inspector", "tables"], inline=True, className="seg toggles"),
            # Parameter Selection's own panels (shown in that mode only): off gives the heatmap the room.
            dcc.Checklist(id="ps-panels", options=L.options("ps-panels", [
                ("controls", msg("Controls")), ("constraints", msg("Pair Constraints")),
                ("inspector", msg("Inspector"))]),
                          value=["controls", "constraints", "inspector"], inline=True, className="seg toggles"),
            _button(L, "graph-only", msg("Graph only"), title=msg("The narrowest form at any width")),
        ], className="hdr-right"),
    ], className="app-header")
    # ← Back and × sit in a header that never scrolls; only the entry below it does.
    help_modal = html.Div([html.Div([_button(L, "help-back", msg("← Back"), "btn back", style={"display": "none"}),
                                     html.Button("×", id="help-close", className="x",
                                                 title=L.prop("help-close", "title", msg("Close")))], className="help-head"),
                           html.Div(dcc.Markdown(id="help-body", link_target="_blank"), className="help-scroll")],
                          id="help-modal", className="help-modal", style={"display": "none"})
    return html.Div([
        *stores, html.Div(id="banners"), header,
        html.Div([_controls(L, ctx), main, inspector], id="app-body", className="app-body"),
        mode_layout(ctx, L),
        help_modal,
    ], id="root", className="workbench controls-on inspector-on tables-on")


def dropdown_labels(tx: Text) -> dict[str, str]:
    """The Dropdown's own words that it shows us: an empty search and its clear button."""
    return {"no_options_found": tx("No tags found"), "search": tx("Search"), "clear_search": tx("Clear search")}


def block_styles(mode: str, tab: str, panels: list[str]) -> dict[str, dict[str, Any]]:
    """Order and visibility of every main-column block for the mode, the Workbench tab and collapsed panels."""
    report = mode == "report"
    tables = "tables" in panels
    order_report = {"blk-dataset": 1, "blk-filters": 2, "blk-graph": 3, "blk-quality": 4, "blk-clusters": 5,
                    "blk-rs": 6, "blk-nodes": 7, "blk-edges": 8, "blk-export": 9, "blk-tabs": 99}
    order_wb = {"blk-graph": 1, "blk-tabs": 2, "blk-quality": 3, "blk-clusters": 4, "blk-rs": 5, "blk-nodes": 6,
                "blk-edges": 7, "blk-filters": 8, "blk-dataset": 98, "blk-export": 99}
    tab_of = {"blk-quality": "quality", "blk-clusters": "clusters", "blk-rs": "rs", "blk-nodes": "nodes",
              "blk-edges": "edges", "blk-filters": "nin"}
    styles = {}
    for block in order_report:
        if report:
            visible = True if block != "blk-tabs" else False
            order = order_report[block]
        else:
            order = order_wb[block]
            if block == "blk-graph":
                visible = True
            elif block == "blk-tabs":
                visible = tables
            elif block in tab_of:
                visible = tables and tab == tab_of[block]
            else:
                visible = False
        styles[block] = {"order": order, "display": "block" if visible else "none"}
    return styles


def root_class(mode: str, panels: list[str], graph_only: bool) -> str:
    """The root's classes: the mode, which panels are open, and "Graph only" (read by app.css and workbench.js)."""
    classes = [{"report": "report", "selection": "workbench selection"}.get(mode, "workbench")]
    classes += [f"{p}-on" for p in ("controls", "inspector", "tables") if p in panels]
    if graph_only:
        classes.append("graph-only")
    return " ".join(classes)
