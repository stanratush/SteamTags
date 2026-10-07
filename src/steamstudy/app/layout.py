"""The Tag Network app's layout: the Workbench and Analysis Report mode over one set of components.

The main column is a flex column whose blocks are re-ordered and shown or hidden by the mode, so the
graph, the tables and the inspector are single component instances shared by both modes. In the
Workbench the tables sit in one resizable pane (`tables-area`); in Analysis Report mode that pane is
`display: contents`, so its blocks take part in the page order.

The Workbench changes form with the window width (`assets/workbench.js` sets `body[data-form]`):
wide (>= 1280 px) is three panes; medium (1024-1279 px) turns the Controls into a pill bar and floats
the Inspector; narrow (< 1024 px, or "Graph only") also turns the tables into a bottom sheet.
"""

from __future__ import annotations

from typing import Any

import dash_ag_grid as dag
from dash import dcc, html

from steamstudy.app.loader import BuildContext
from steamstudy.app.renderer import graph_component
from steamstudy.app.view import column_defs
from steamstudy.export import schema as S

WB_TABS = [("quality", "Cluster quality"), ("clusters", "Clusters"), ("rs", "Removal sensitivity"),
           ("nodes", "Nodes"), ("edges", "Edges"), ("nin", "Not in network")]
SLIDERS = ("min-games", "min-shared", "min-months")
PILLS = ("dataset", "min-months", "min-games", "min-shared", "hidden", "weight", "algorithm", "gamma", "seed")


def _data(**attrs: str) -> dict[str, Any]:
    """HTML data-* attributes as Dash keyword arguments: `_data(graph_overlay="top")` -> data-graph-overlay."""
    return {"data-" + name.replace("_", "-"): value for name, value in attrs.items()}


def _slider(id_: str, label: str, lo: int, hi: int, value: int) -> list[Any]:
    """A slider whose label shows its value while dragging; the value itself is sent on release."""
    return [html.Label([label, html.B(str(value), id=f"{id_}-value", className="num")], htmlFor=id_,
                       className="sl-label"),
            dcc.Slider(id=id_, min=lo, max=hi, step=1, value=value, updatemode="mouseup", allow_direct_input=False,
                       tooltip=None, marks={lo: str(lo), hi: str(hi)}, className="sl")]


def _item(pill: str, pill_label: str, value: str, children: list[Any]) -> html.Div:
    """One control: shown inline in the Controls panel, or as a pill with a popover in the pill bar."""
    return html.Div([
        html.Button([f"{pill_label} " if pill_label else "", html.B(value, id=f"pill-{pill}", className="num")],
                    className="pill-btn", **_data(pill=pill)),
        html.Div(children, className="pill-pop"),
    ], className="ctl-item")


def _section(title: str, items: list[Any]) -> html.Div:
    return html.Div([html.H4(title, className="ctl-h"), *items], className="ctl-section")


def _seg(id_: str, options: list[tuple[str, str]], value: Any, **kw: Any) -> dcc.RadioItems:
    """RadioItems drawn as a segmented control."""
    return dcc.RadioItems(id=id_, options=[{"label": label, "value": v} for v, label in options], value=value,
                          inline=True, className="seg", **kw)


def _help(panel: str) -> html.Button:
    return html.Button("?", id={"type": "help", "panel": panel}, className="help", title="Open the User Guide section")


def _grid(id_: str, schema_key: str, columns: list[str] | None = None, height: str = "320px",
          extra: list[dict[str, Any]] | None = None, **kw: Any) -> dag.AgGrid:
    return dag.AgGrid(id=id_, columnDefs=column_defs(schema_key, columns, extra=extra), rowData=[],
                      defaultColDef={"sortable": True, "filter": True, "resizable": True},
                      dashGridOptions={"tooltipShowDelay": 300, "rowSelection": {"mode": "singleRow", "checkboxes": False, "enableClickSelection": True}, "animateRows": False},
                      style={"height": height, "width": "100%"}, className="grid", **kw)


def _block(id_: str, heading: str, children: list[Any], help_panel: str | None = None) -> html.Div:
    head: list[Any] = [heading]
    if help_panel:
        head.append(_help(help_panel))
    return html.Div([html.H3(head, className="section-heading"), *children], id=id_, className="panel")


def _controls(ctx: BuildContext) -> html.Div:
    first = ctx.datasets[0].key
    s = ctx.default_settings(first)
    defining = ctx.dataset(first).defining_tag
    genre_ids = [t.id for t in ctx.genre_tags]
    hidden = [t for t in genre_ids if t in s.hidden_tag_ids]
    data = _section("Data", [
        _item("dataset", "", ctx.dataset(first).label, [
            html.Label("Dataset", htmlFor="dataset", className="l"),
            dcc.Dropdown(id="dataset", options=[{"label": d.label, "value": d.key} for d in ctx.datasets],
                         value=first, clearable=False, searchable=False)]),
        _item("min-months", "Months ≥", str(s.min_months),
              _slider("min-months", "Minimum Months Filter", 0, 60, s.min_months)),
    ])
    filters = _section("Filters", [
        _item("min-games", "Min games", str(s.min_games_per_tag),
              _slider("min-games", "Minimum games per tag", 1, 40, s.min_games_per_tag)),
        _item("min-shared", "Min shared", str(s.min_shared_games),
              _slider("min-shared", "Minimum shared games", 1, 30, s.min_shared_games)),
        _item("hidden", "Hidden", f"{len(hidden)} Genre Tag{'' if len(hidden) == 1 else 's'}"
              + (" + defining" if defining and defining.id in s.hidden_tag_ids else ""), [
            html.Label(["Hidden Genre Tags ", html.Span(f"{len(hidden)} of {len(genre_ids)}", id="genre-count",
                                                          className="mute num")], className="l"),
            dcc.Checklist(id="genre-hidden", options=[{"label": t.name, "value": t.id} for t in ctx.genre_tags],
                          value=hidden, inline=True, className="chips"),
            dcc.Checklist(id="defining-hidden",
                          options=[{"label": f"hide defining tag ({defining.name})" if defining else "no defining tag",
                                    "value": 1, "disabled": defining is None}],
                          value=[1] if defining and defining.id in s.hidden_tag_ids else [], className="check"),
        ]),
    ])
    clustering = _section("Clustering", [
        _item("weight", "Weight", "Shared games" if s.clustering_weight == "shared_games" else "Lift", [
            html.Label("Clustering weight", className="l"),
            _seg("weight", [("shared_games", "Shared games"), ("lift", "Lift")], s.clustering_weight)]),
        _item("algorithm", "", s.algorithm.capitalize(), [
            html.Label("Clustering algorithm", className="l"),
            _seg("algorithm", [("louvain", "Louvain"), ("leiden", "Leiden")], s.algorithm)]),
        html.Div([
            _item("gamma", "γ", f"{s.resolution:.2f}", [
                html.Label("Resolution γ", htmlFor="gamma", className="l", title="0.1–3.0"),
                dcc.Input(id="gamma", type="number", min=0.1, max=3.0, step=0.05, value=s.resolution, debounce=True)]),
            _item("seed", "Seed", str(s.seed), [
                html.Label("Seed", htmlFor="seed", className="l"),
                dcc.Input(id="seed", type="number", min=0, step=1, value=s.seed, debounce=True)]),
        ], className="two"),
    ])
    state = _section("State", [
        _item("state", "State", "…", [
            html.Label("Removed tags", className="l"),
            html.Div([dcc.Dropdown(id="restore-pick", options=[], placeholder="pick a removed tag"),
                      html.Button("Restore", id="restore-btn", className="btn")], className="row-inline"),
            html.Div([html.Button("Reset all", id="reset-btn", className="btn"),
                      html.Button("Export this state", id="export-btn", className="btn primary")], className="stack"),
            dcc.Upload(html.Button("Open Network State…", className="btn wide"), id="open-upload", accept=".zip,.json",
                       multiple=False),
            html.Div(id="open-message", className="msg"),
            html.Button("Clear app cache", id="clear-cache-btn", className="btn quiet"),
            html.Div(id="cache-message", className="msg"),
        ]),
    ])
    return html.Div([
        html.Div([html.B("Controls"), _help("controls")], className="ctl-title"),
        data, filters, clustering, state,
    ], id="controls-panel", className="controls")


def build_layout(ctx: BuildContext) -> html.Div:
    graph_block = html.Div([
        html.H3(["3 Network", _help("network")], className="section-heading"),
        html.Div(id="summary-row", className="sumrow"),
        html.Div(id="state-sentence", className="state-line"),
        html.Div([
            *graph_component(),
            html.Div([_seg("layout-mode", [("global", "Global"), ("separated", "Cluster-separated")], "global"),
                      html.Button("Tidy", id="relayout-btn", className="btn",
                                  title="Settle the graph around the nodes you dragged; positions only"),
                      html.Button("⤢", id="fit-btn", className="btn", title="Fit the graph to the view")],
                     className="ov ov-tr", **_data(graph_overlay="top")),
            html.Div(html.Div(id="legend", className="legend"), className="ov ov-bl",
                     **_data(graph_overlay="bottom")),
        ], className="graph-stage"),
    ], id="blk-graph", className="panel graph-block")

    rs_block = _block("blk-rs", "5 Removal sensitivity", [
        html.Div([html.Button("Run", id="rs-run", className="btn primary"),
                  html.Button("Continue", id="rs-continue", className="btn", style={"display": "none"}),
                  html.Button("Cancel", id="rs-cancel", className="btn"),
                  html.Span(id="rs-estimate", className="mute")], className="row-inline"),
        html.Progress(id="rs-progress", value="0", max="1", style={"width": "100%"}),
        html.Span(id="rs-progress-label", className="mute small"), dcc.Store(id="rs-progress-store"),
        html.Div(id="rs-banner", className="warning", style={"display": "none"}),
        html.Div(id="noise-line-rs", className="qline"),
        html.Div([dcc.Checklist(id="rs-beyond", options=[{"label": "beyond noise only", "value": 1}], value=[],
                                inline=True, className="check"),
                  dcc.Dropdown(id="rs-cluster", options=[], placeholder="all clusters", style={"width": "200px"})],
                 className="row-inline"),
        html.Div(_grid("rs-grid", "app_export/removal_sensitivity.csv", height="300px", extra=[{
            "field": "membership_stability", "headerName": "membership_stability (joined)",
            "headerTooltip": S.file("app_export/nodes.csv").column("membership_stability").description,
            "sortable": True, "filter": "agNumberColumnFilter", "type": "rightAligned"}]),
                 id="rs-grid-wrap"),
        html.Div(id="rs-footer", className="qline"),
    ], help_panel="removal")

    tables = html.Div([
        html.Div([html.Span(id="sheet-grip", className="grip", title="Open or close the tables"),
                  dcc.RadioItems(id="wb-tab", options=[{"label": label, "value": key} for key, label in WB_TABS],
                                 value="quality", inline=True, className="tabs-nav")],
                 id="blk-tabs", className="panel"),
        _block("blk-filters", "2 Filters", [html.Div(id="filters-summary"),
                                             _grid("nin-grid", "app_export/not_in_network.csv")], help_panel="filters"),
        _block("blk-quality", "4 Cluster quality", [
            html.Div(id="quality-detail", className="qline"),
            _grid("connections-grid", "app_export/cluster_connections.csv", height="200px"),
            html.Details([html.Summary("Null model and seed-noise replicates"),
                          _grid("null-grid", "app_export/null_model.csv", height="200px"),
                          _grid("seed-grid", "app_export/seed_noise.csv", height="200px")]),
        ], help_panel="quality"),
        _block("blk-clusters", "Clusters", [_grid("clusters-grid", "app_export/clusters.csv")], help_panel="clusters"),
        rs_block,
        _block("blk-nodes", "6 All nodes and edges", [_grid("nodes-grid", "app_export/nodes.csv")], help_panel="nodes"),
        _block("blk-edges", "Edges", [_grid("edges-grid", "app_export/edges.csv",
                                            [c for c in _edge_columns()])], help_panel="edges"),
    ], id="tables-area", className="tables-area", **_data(graph_overlay="bottom"))

    main = html.Div([
        _block("blk-dataset", "1 Dataset", [html.Div(id="dataset-summary")], help_panel="dataset"),
        graph_block,
        html.Div(id="tables-handle", className="tables-handle", title="Drag to resize the tables"),
        tables,
        _block("blk-export", "7 Export", [html.Button("Export this state", id="export-btn-report", className="btn primary"),
                                         html.Div(id="export-summary")], help_panel="export"),
    ], id="main", className="main")

    inspector = html.Div([
        html.Div([html.B("Inspector"), _help("inspector"),
                  html.Button("×", id="inspector-close", className="x", title="Close")], className="insp-title"),
        html.Div(id="inspector-body"),
        html.Div([html.Button("Remove this tag", id="remove-btn", className="btn", style={"display": "none"}),
                  html.Button("Run for this tag", id="rs-run-tag", className="btn", style={"display": "none"})],
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
        dcc.Download(id="download"),
    ]
    header = html.Header([
        html.Div([html.B("Tag Network", className="title"), html.Span(f"Build {ctx.build_id}", className="mute")],
                 className="brand"),
        _seg("mode", [("workbench", "Workbench"), ("report", "Analysis Report mode")], "workbench"),
        html.Div(dcc.Dropdown(id="tag-search", options=[], placeholder="Find a tag…", searchable=True,
                              clearable=False, className="tag-search"), id="search-slot", className="search-slot"),
        html.Div([
            html.Span(id="verify-result", className="small"),
            html.Span(id="error-message", className="error small"),
            dcc.Checklist(id="panels", options=[{"label": "Controls", "value": "controls"},
                                                {"label": "Inspector", "value": "inspector"},
                                                {"label": "Tables", "value": "tables"}],
                          value=["controls", "inspector", "tables"], inline=True, className="seg toggles"),
            html.Button("Graph only", id="graph-only", className="btn", title="The narrowest form at any width"),
        ], className="hdr-right"),
    ], className="app-header")
    help_modal = html.Div([html.Button("×", id="help-close", className="x"),
                           html.Button("← Back", id="help-back", className="btn back", style={"display": "none"}),
                           dcc.Markdown(id="help-body", link_target="_blank")],
                          id="help-modal", className="help-modal", style={"display": "none"})
    return html.Div([
        *stores, html.Div(id="banners"), header,
        html.Div([_controls(ctx), main, inspector], id="app-body", className="app-body"),
        help_modal,
    ], id="root", className="workbench controls-on inspector-on tables-on")


def _edge_columns() -> list[str]:
    return ["source_tag_id", "source_tag", "target_tag_id", "target_tag", "shared_games", "lift", "source_cluster",
            "target_cluster", "is_intra_cluster"]


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
    classes = ["report" if mode == "report" else "workbench"]
    classes += [f"{p}-on" for p in ("controls", "inspector", "tables") if p in panels]
    if graph_only:
        classes.append("graph-only")
    return " ".join(classes)
