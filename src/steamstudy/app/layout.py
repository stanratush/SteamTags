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

import json
from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
from dash import dcc, html

from steamstudy.app import help as H
from steamstudy.app.guide import LABELS
from steamstudy.app.loader import BuildContext
from steamstudy.app.ps_view import mode_layout
from steamstudy.app.renderer import graph_component, thickness_key
from steamstudy.app.view import column_defs, metric_header
from steamstudy.i18n import LANGS, Text, text

WB_TABS = [("quality", "Cluster quality"), ("clusters", "Clusters"), ("rs", "Removal sensitivity"),
           ("nodes", "Nodes"), ("edges", "Edges"), ("nin", "Not in network")]
SLIDERS = ("min-games", "min-shared", "min-months")
PILLS = ("dataset", "min-months", "min-games", "min-shared", "hidden", "weight", "algorithm", "gamma", "seed")

# A registered message: English text for `tx`, or a function of the translator (a tooltip, a store's words).
Message = str | Callable[[Text], Any]
# json([component id, prop]) -> (component id, prop, message), in the order first registered.
RELABEL: dict[str, tuple[Any, str, Message]] = {}


def message_value(message: Message, tx: Text) -> Any:
    return tx(message) if isinstance(message, str) else message(tx)


def _t(tx: Text, id_: Any, prop: str, message: Message) -> Any:
    """Register a static prop for the relabel callback and return its value in the page's language."""
    RELABEL.setdefault(json.dumps([id_, prop], sort_keys=True), (id_, prop, message))
    return message_value(message, tx)


class Labels:
    """The page's translator and the relabel registry, for one build of the layout."""

    def __init__(self, tx: Text) -> None:
        self.tx = tx
        self._n = 0

    def new_id(self) -> str:
        self._n += 1
        return f"i18n-{self._n}"

    def prop(self, id_: Any, prop: str, message: Message) -> Any:
        """A static prop of a component with an id: registered, in the page's language."""
        return _t(self.tx, id_, prop, message)

    def span(self, message: Message, **kw: Any) -> html.Span:
        """A static text as a Span of its own, registered so that a language switch relabels it."""
        id_ = self.new_id()
        return html.Span(self.prop(id_, "children", message), id=id_, **kw)

    def help(self, key: str) -> dict[str, Any]:
        """Both help layers for an element of its own id (`id` is in the result): the tooltip is registered."""
        id_ = self.new_id()
        return {"id": id_, "data-tip": self.prop(id_, "data-tip", lambda tx: H.tip(key, tx)),
                "data-help": H.target(key)}

    def options(self, id_: str, options: list[tuple[Any, str]]) -> list[dict[str, Any]]:
        """A RadioItems or Checklist's options, with registered labels."""
        return self.prop(id_, "options", lambda tx: [{"label": tx(label), "value": v} for v, label in options])


def ui_words(tx: Text) -> dict[str, Any]:
    """The words the browser code shows (the `ui-words` store): JS and CSS hold none of their own. `tip` labels each
    kind of tooltip line (help.py), `more` is the tooltip's footer and `info` the ⓘ's aria-label; `pills` are the
    pill bar's words (workbench.js `pills`), `{…}` filled in the browser; `decimal` is the language's decimal mark."""
    genre = lambda n: tx.n(n, one="{n} Genre Tag", other="{n} Genre Tags", n="{n}")  # noqa: E731
    return {"title": tx("Tag Network"), "tip": LABELS[tx.lang], "more": tx("Click for the full User Guide entry"),
            "info": tx("User Guide entry for {name}", name="{name}"), "decimal": tx.decimal,
            "pills": {"genre": [genre(1), genre(2)], "defining": tx("{hidden} + defining", hidden="{hidden}"),
                      "lift": tx("Lift"), "shared": tx("Shared games"),
                      "of": tx("{n} of {total}", n="{n}", total="{total}")}}


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
        html.Span(L.prop("lang-term", "children", "Language"), id="lang-term", className="term", tabIndex="0",
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
    return html.Button("?", id=id_, className="help", title=L.prop(id_, "title", "Open the User Guide section"))


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
    data = _section(L, "Data", [
        _item(L, "dataset", "", ctx.dataset(first).label, [
            html.Label(L.span("Dataset"), htmlFor="dataset", className="l"),
            dcc.Dropdown(id="dataset", options=[{"label": d.label, "value": d.key} for d in ctx.datasets],
                         value=first, clearable=False, searchable=False)]),
        _item(L, "min-months", "Months ≥", str(s.min_months),
              _slider(L, "min-months", "Minimum Months Filter", 0, 60, s.min_months)),
    ])
    filters = _section(L, "Filters", [
        _item(L, "min-games", "Min games", str(s.min_games_per_tag),
              _slider(L, "min-games", "Minimum games per tag", 1, 40, s.min_games_per_tag)),
        _item(L, "min-shared", "Min shared", str(s.min_shared_games),
              _slider(L, "min-shared", "Minimum shared games", 1, 30, s.min_shared_games)),
        _item(L, "hidden", "Hidden", tx("{hidden} + defining", hidden=hidden_pill) if hides_defining else hidden_pill, [
            html.Label([L.span("Hidden Genre Tags"), " ",
                        html.Span(tx("{n} of {total}", n=len(hidden), total=len(genre_ids)), id="genre-count",
                                  className="mute num")], className="l"),
            dcc.Checklist(id="genre-hidden", options=[{"label": t.name, "value": t.id} for t in ctx.genre_tags],
                          value=hidden, inline=True, className="chips"),
            dcc.Checklist(id="defining-hidden", options=defining_options(defining, tx),
                          value=[1] if hides_defining else [], className="check"),
        ]),
    ])
    clustering = _section(L, "Clustering", [
        _item(L, "weight", "Weight", tx("Shared games") if s.clustering_weight == "shared_games" else tx("Lift"), [
            _label(L, "Clustering weight", "control.weight"),
            _seg("weight", L.options("weight", [("shared_games", "Shared games"), ("lift", "Lift")]),
                 s.clustering_weight)]),
        _item(L, "algorithm", "", s.algorithm.capitalize(), [
            _label(L, "Clustering algorithm", "control.algorithm"),
            _seg("algorithm", [{"label": "Louvain", "value": "louvain"}, {"label": "Leiden", "value": "leiden"}],
                 s.algorithm)]),
        html.Div([
            _item(L, "gamma", "γ", tx.fixed(s.resolution, ".2f"), [
                _label(L, "Resolution γ", "control.gamma", htmlFor="gamma"),
                dcc.Input(id="gamma", type="number", min=0.01, step=0.01, value=s.resolution, debounce=True)]),
            _item(L, "seed", "Seed", str(s.seed), [
                _label(L, "Seed", "control.seed", htmlFor="seed"),
                dcc.Input(id="seed", type="number", min=0, step=1, value=s.seed, debounce=True)]),
        ], className="two"),
    ])
    state = _section(L, "State", [
        _item(L, "state", "State", "…", [
            html.Label(L.span("Removed tags"), className="l"),
            html.Div([dcc.Dropdown(id="restore-pick", options=[],
                                   placeholder=L.prop("restore-pick", "placeholder", "pick a removed tag")),
                      _button(L, "restore-btn", "Restore")], className="row-inline"),
            html.Div([_button(L, "reset-btn", "Reset all"),
                      _button(L, "export-btn", "Export this state", "btn primary")], className="stack"),
            dcc.Upload(_button(L, "open-btn", "Open Network State…", "btn wide"), id="open-upload", accept=".zip,.json",
                       multiple=False),
            html.Div(id="open-message", className="msg"),
            _button(L, "clear-cache-btn", "Clear app cache", "btn quiet"),
            html.Div(id="cache-message", className="msg"),
        ]),
    ])
    return html.Div([
        html.Div([html.B(L.span("Controls")), _help(L, "controls")], className="ctl-title"),
        data, filters, clustering, state,
    ], id="controls-panel", className="controls")


def _thickness_legend(L: Labels, ctx: BuildContext) -> html.Div:
    """What edge width shows (`thickness_key`, kept current by a callback), and the switch that shows shared games
    while the clustering runs on lift. A view choice only: never part of the Network State."""
    label, style = thickness_key(ctx.default_settings(ctx.datasets[0].key).clustering_weight, False, L.tx)
    return html.Div([
        html.Span(label, id="thickness-label", className="lkey term", tabIndex="0",
                  **{"data-tip": L.prop("thickness-label", "data-tip", lambda tx: H.tip("legend.thickness", tx)),
                     "data-help": H.target("legend.thickness")}),
        dcc.Checklist(id="thickness-shared", options=L.options("thickness-shared", [(1, "show shared games")]),
                      value=[], className="check", style=style),
    ], className="legend thickness-key")


def build_layout(ctx: BuildContext, lang: str = "en") -> html.Div:
    """The page in the Interface Language `lang` (read from the cookie when it is served)."""
    L = Labels(text(lang))
    language = _language(L, lang)
    graph_block = html.Div([
        html.H3([L.span("3 Network"), _help(L, "network")], className="section-heading"),
        html.Div(id="summary-row", className="sumrow"),
        html.Div(id="state-sentence", className="state-line"),
        html.Div([
            *graph_component(),
            html.Div([_seg("layout-mode", L.options("layout-mode", [("global", "Global"),
                                                                    ("separated", "Cluster-separated")]), "global"),
                      _button(L, "relayout-btn", "Tidy",
                              title="Settle the graph around the nodes you dragged; positions only"),
                      html.Button("⤢", id="fit-btn", className="btn",
                                  title=L.prop("fit-btn", "title", "Fit the graph to the view"))],
                     className="ov ov-tr", **_data(graph_overlay="top")),
            html.Div([html.Div(id="legend", className="legend"), _thickness_legend(L, ctx)], className="ov ov-bl",
                     **_data(graph_overlay="bottom")),
            # Shown while a callback runs (callbacks.py: `running`); never a graph overlay, so it never resizes the
            # canvas the layout is made for. role="status" is a polite live region: screen readers announce the label.
            html.Div([html.Span(L.prop("busy-clustering", "children", "Clustering…"), id="busy-clustering",
                                hidden=True),
                      html.Span(L.prop("busy-layout", "children", "Laying out…"), id="busy-layout", hidden=True)],
                     className="busy graph-busy", role="status"),
        ], className="graph-stage"),
    ], id="blk-graph", className="panel graph-block")

    rs_block = _block(L, "blk-rs", "5 Removal sensitivity", [
        html.Div([_button(L, "rs-run", "Run", "btn primary"),
                  html.Button(id="rs-continue", className="btn", style={"display": "none"}),
                  _button(L, "rs-cancel", "Cancel"),
                  html.Span(id="rs-estimate", className="mute")], className="row-inline"),
        html.Progress(id="rs-progress", value="0", max="1", style={"width": "100%"}),
        html.Span(id="rs-progress-label", className="mute small"), dcc.Store(id="rs-progress-store"),
        html.Div(id="rs-banner", className="warning", style={"display": "none"}),
        html.Div(id="noise-line-rs", className="qline"),
        html.Div([dcc.Checklist(id="rs-beyond", options=L.options("rs-beyond", [(1, "beyond noise only")]), value=[],
                                inline=True, className="check"),
                  dcc.Dropdown(id="rs-cluster", options=[], style={"width": "200px"},
                               placeholder=L.prop("rs-cluster", "placeholder", "all clusters"))],
                 className="row-inline"),
        html.Div(_grid(L, "rs-grid", height="300px"), id="rs-grid-wrap"),
        html.Div(id="rs-footer", className="qline"),
    ], help_panel="removal")

    tables = html.Div([
        html.Div([html.Span(id="sheet-grip", className="grip",
                            title=L.prop("sheet-grip", "title", "Open or close the tables")),
                  dcc.RadioItems(id="wb-tab", options=L.options("wb-tab", WB_TABS), value="quality", inline=True,
                                 className="tabs-nav")],
                 id="blk-tabs", className="panel"),
        _block(L, "blk-filters", "2 Filters", [html.Div(id="filters-summary"), _grid(L, "nin-grid")],
               help_panel="filters"),
        _block(L, "blk-quality", "4 Cluster quality", [
            html.Div(id="quality-detail", className="qline"),
            _grid(L, "connections-grid", height="200px"),
            html.Details([html.Summary(L.span("Null model and seed-noise replicates")),
                          _grid(L, "null-grid", height="200px"),
                          _grid(L, "seed-grid", height="200px")]),
        ], help_panel="quality"),
        _block(L, "blk-clusters", "Clusters", [_grid(L, "clusters-grid")], help_panel="clusters"),
        rs_block,
        _block(L, "blk-nodes", "6 All nodes and edges", [_grid(L, "nodes-grid")], help_panel="nodes"),
        _block(L, "blk-edges", "Edges", [_grid(L, "edges-grid")], help_panel="edges"),
    ], id="tables-area", className="tables-area", **_data(graph_overlay="bottom"))

    main = html.Div([
        _block(L, "blk-dataset", "1 Dataset", [html.Div(id="dataset-summary")], help_panel="dataset"),
        graph_block,
        html.Div(id="tables-handle", className="tables-handle",
                 title=L.prop("tables-handle", "title", "Drag to resize the tables")),
        tables,
        _block(L, "blk-export", "7 Export", [_button(L, "export-btn-report", "Export this state", "btn primary"),
                                            html.Div(id="export-summary")], help_panel="export"),
    ], id="main", className="main")

    inspector = html.Div([
        html.Div([html.B(L.span("Inspector")), _help(L, "inspector"),
                  # Shown while a selection, then the Inspector's content for it, is on its way (callbacks.py:
                  # `running`).
                  html.Div([html.Span(L.prop("busy-selecting", "children", "Selecting…"), id="busy-selecting",
                                      hidden=True),
                            html.Span(L.prop("busy-inspector", "children", "Loading…"), id="busy-inspector",
                                      hidden=True)], className="busy insp-busy", role="status"),
                  html.Button("×", id="inspector-close", className="x",
                              title=L.prop("inspector-close", "title", "Close"))], className="insp-title"),
        html.Div(id="inspector-body"),
        html.Div([_button(L, "remove-btn", "Remove this tag", style={"display": "none"}),
                  _button(L, "rs-run-tag", "Run for this tag", style={"display": "none"})],
                 className="row-inline"),
    ], id="inspector-panel", className="inspector docked", **_data(graph_overlay="right", graph_transient="yes"))

    stores = [
        dcc.Store(id="build-path", data=str(ctx.path)),
        dcc.Store(id="builds-root", data=str(ctx.path.resolve().parents[1])),  # <root>/builds: where exports' Builds are found
        dcc.Store(id="state-meta"), dcc.Store(id="state-tables"), dcc.Store(id="elements-base"),
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
        html.Div([html.B(L.prop("brand-title", "children", "Tag Network"), id="brand-title", className="title"),
                  html.Span(L.prop("brand-build", "children", lambda tx: tx("Build {build_id}", build_id=ctx.build_id)),
                            id="brand-build", className="mute")],
                 className="brand"),
        _seg("mode", L.options("mode", [("workbench", "Workbench"), ("report", "Analysis Report mode"),
                                        ("selection", "Parameter Selection")]), "workbench"),
        language,
        html.Div(dcc.Dropdown(id="tag-search", options=[], searchable=True, clearable=False, className="tag-search",
                              placeholder=L.prop("tag-search", "placeholder", "Find a tag…"),
                              labels=L.prop("tag-search", "labels", dropdown_labels)),
                 id="search-slot", className="search-slot"),
        html.Div([
            html.Span(id="verify-result", className="small"),
            html.Span(id="error-message", className="error small"),
            dcc.Checklist(id="panels", options=L.options("panels", [("controls", "Controls"),
                                                                   ("inspector", "Inspector"), ("tables", "Tables")]),
                          value=["controls", "inspector", "tables"], inline=True, className="seg toggles"),
            _button(L, "graph-only", "Graph only", title="The narrowest form at any width"),
        ], className="hdr-right"),
    ], className="app-header")
    # ← Back and × sit in a header that never scrolls; only the entry below it does.
    help_modal = html.Div([html.Div([_button(L, "help-back", "← Back", "btn back", style={"display": "none"}),
                                     html.Button("×", id="help-close", className="x",
                                                 title=L.prop("help-close", "title", "Close"))], className="help-head"),
                           html.Div(dcc.Markdown(id="help-body", link_target="_blank"), className="help-scroll")],
                          id="help-modal", className="help-modal", style={"display": "none"})
    return html.Div([
        *stores, html.Div(id="banners"), header,
        html.Div([_controls(L, ctx), main, inspector], id="app-body", className="app-body"),
        mode_layout(ctx),
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
