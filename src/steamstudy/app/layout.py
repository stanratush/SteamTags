"""The Tag Network app's layout: the Workbench and Analysis Report mode over one set of components.

The main column is a flex column whose blocks are re-ordered and shown or hidden by the mode, so the
graph, the tables and the inspector are single component instances shared by both modes.
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

def _slider(id_: str, label: str, lo: int, hi: int, value: int) -> list[Any]:
    return [html.Label(label, htmlFor=id_),
            dcc.Slider(id=id_, min=lo, max=hi, step=1, value=value, updatemode="mouseup",
                       tooltip={"placement": "bottom", "always_visible": False}, marks={lo: str(lo), hi: str(hi)})]


def _help(panel: str) -> html.Button:
    return html.Button("?", id={"type": "help", "panel": panel}, className="help", title="Open the User Guide section")


def _grid(id_: str, schema_key: str, columns: list[str] | None = None, height: str = "320px",
          extra: list[dict[str, Any]] | None = None, **kw: Any) -> dag.AgGrid:
    return dag.AgGrid(id=id_, columnDefs=column_defs(schema_key, columns, extra=extra), rowData=[],
                      defaultColDef={"sortable": True, "filter": True, "resizable": True},
                      dashGridOptions={"tooltipShowDelay": 300, "rowSelection": {"mode": "singleRow", "checkboxes": False, "enableClickSelection": True}, "animateRows": False},
                      style={"height": height, "width": "100%"}, className="ag-theme-alpine", **kw)


def _block(id_: str, heading: str, children: list[Any], help_panel: str | None = None) -> html.Div:
    head: list[Any] = [heading]
    if help_panel:
        head.append(_help(help_panel))
    return html.Div([html.H3(head, className="section-heading"), *children], id=id_, className="panel")


def build_layout(ctx: BuildContext) -> html.Div:
    first = ctx.datasets[0].key
    s = ctx.default_settings(first)
    defining = ctx.dataset(first).defining_tag
    genre_ids = [t.id for t in ctx.genre_tags]
    controls = html.Div([
        html.Div([html.B("Controls"), _help("controls")]),
        html.Label("Dataset", htmlFor="dataset"),
        dcc.Dropdown(id="dataset", options=[{"label": d.label, "value": d.key} for d in ctx.datasets], value=first,
                     clearable=False),
        *_slider("min-games", "Minimum games per tag", 1, 40, s.min_games_per_tag),
        *_slider("min-shared", "Minimum shared games", 1, 30, s.min_shared_games),
        *_slider("min-months", "Minimum Months Filter", 0, 60, s.min_months),
        html.Label("Hidden Genre Tags"),
        dcc.Checklist(id="genre-hidden", options=[{"label": t.name, "value": t.id} for t in ctx.genre_tags],
                      value=[t for t in genre_ids if t in s.hidden_tag_ids], inline=True),
        dcc.Checklist(id="defining-hidden",
                      options=[{"label": f"hide defining tag ({defining.name})" if defining else "no defining tag",
                                "value": 1, "disabled": defining is None}],
                      value=[1] if defining and defining.id in s.hidden_tag_ids else []),
        html.Label("Clustering weight"),
        dcc.RadioItems(id="weight", options=[{"label": "Shared games", "value": "shared_games"},
                                             {"label": "Lift", "value": "lift"}], value=s.clustering_weight, inline=True),
        html.Label("Clustering algorithm"),
        dcc.RadioItems(id="algorithm", options=[{"label": "Louvain", "value": "louvain"},
                                                {"label": "Leiden", "value": "leiden"}], value=s.algorithm, inline=True),
        html.Label("Resolution γ (0.1–3.0)", htmlFor="gamma"),
        dcc.Input(id="gamma", type="number", min=0.1, max=3.0, step=0.05, value=s.resolution, debounce=True),
        html.Label("Seed", htmlFor="seed"),
        dcc.Input(id="seed", type="number", min=0, step=1, value=s.seed, debounce=True),
        html.Label("Removed tags"),
        dcc.Dropdown(id="restore-pick", options=[], placeholder="pick a removed tag"),
        html.Button("Restore", id="restore-btn"), html.Button("Reset all", id="reset-btn"),
        html.Hr(),
        html.Button("Re-layout", id="relayout-btn"),
        html.Hr(),
        html.Button("Export this state", id="export-btn"),
        dcc.Upload(html.Button("Open Network State…"), id="open-upload", accept=".zip,.json", multiple=False),
        dcc.Input(id="open-build-path", placeholder="Build folder (if it has moved)", style={"width": "100%"}),
        html.Div(id="open-message"),
        html.Hr(),
        html.Button("Clear app cache", id="clear-cache-btn"), html.Div(id="cache-message"),
    ], id="controls-panel", className="panel controls", style={"width": "280px", "flex": "0 0 280px"})

    graph_block = html.Div([
        html.H3(["3 Network", _help("network")], className="section-heading"),
        html.Div([
            dcc.RadioItems(id="layout-mode", options=[{"label": "Global", "value": "global"},
                                                      {"label": "Cluster-separated", "value": "separated"}],
                           value="global", inline=True),
            html.Div(id="legend", className="legend"),
        ]),
        html.Div(id="quality-line", className="qline"),
        html.Div(id="noise-line-top", className="qline"),
        html.Div([
            html.Div([graph_component()], style={"flex": "1 1 auto", "minWidth": "0"}),
            html.Div([
                html.Div([html.B("Inspector"), _help("inspector"),
                          html.Button("×", id="inspector-close", style={"float": "right"})]),
                html.Div(id="inspector-body"),
                html.Button("Remove this tag", id="remove-btn", style={"display": "none"}),
                html.Button("Run for this tag", id="rs-run-tag", style={"display": "none"}),
            ], id="inspector-panel", className="panel", style={"flex": "0 0 340px", "overflow": "auto"}),
        ], style={"display": "flex"}),
    ], id="blk-graph", className="panel")

    rs_block = _block("blk-rs", "5 Removal sensitivity", [
        html.Div([html.Button("Run", id="rs-run"), html.Button("Continue", id="rs-continue", style={"display": "none"}),
                  html.Button("Cancel", id="rs-cancel"), html.Span(id="rs-estimate", style={"marginLeft": "1em"})]),
        html.Progress(id="rs-progress", value="0", max="1", style={"width": "100%"}),
        html.Span(id="rs-progress-label", style={"fontSize": "0.8em"}), dcc.Store(id="rs-progress-store"),
        html.Div(id="rs-banner", className="warning", style={"display": "none"}),
        html.Div(id="noise-line-rs", className="qline"),
        dcc.Checklist(id="rs-beyond", options=[{"label": "beyond noise only", "value": 1}], value=[], inline=True),
        dcc.Dropdown(id="rs-cluster", options=[], placeholder="all clusters", style={"width": "200px"}),
        html.Div(_grid("rs-grid", "app_export/removal_sensitivity.csv", height="300px", extra=[{
            "field": "membership_stability", "headerName": "membership_stability (joined)",
            "headerTooltip": S.file("app_export/nodes.csv").column("membership_stability").description,
            "sortable": True, "filter": "agNumberColumnFilter"}]), id="rs-grid-wrap"),
        html.Div(id="rs-footer", className="qline"),
    ], help_panel="removal")

    blocks = [
        _block("blk-dataset", "1 Dataset", [html.Div(id="dataset-summary")], help_panel="dataset"),
        _block("blk-filters", "2 Filters", [html.Div(id="filters-summary"),
                                             _grid("nin-grid", "app_export/not_in_network.csv")], help_panel="filters"),
        graph_block,
        html.Div(dcc.RadioItems(id="wb-tab", options=[{"label": label, "value": key} for key, label in WB_TABS],
                                value="quality", inline=True), id="blk-tabs", className="panel"),
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
        _block("blk-export", "7 Export", [html.Button("Export this state", id="export-btn-report"),
                                         html.Div(id="export-summary")], help_panel="export"),
    ]

    stores = [
        dcc.Store(id="build-path", data=str(ctx.path)),
        dcc.Store(id="state-meta"), dcc.Store(id="state-tables"), dcc.Store(id="elements-base"),
        dcc.Store(id="relayout"), dcc.Store(id="selection"), dcc.Store(id="floating-open", data=False),
        dcc.Store(id="removed", data=[]), dcc.Store(id="rs-view"), dcc.Store(id="rs-request"),
        dcc.Store(id="rs-done"), dcc.Store(id="pending-open"), dcc.Store(id="verify"), dcc.Store(id="fitted"),
        dcc.Download(id="download"),
    ]
    header = html.Div([
        html.Div(id="banners"),
        html.Div([
            html.B("Tag Network"), html.Span(f" · Build {ctx.build_id}", style={"color": "#666"}),
            dcc.RadioItems(id="mode", options=[{"label": "Workbench", "value": "workbench"},
                                               {"label": "Analysis Report mode", "value": "report"}],
                           value="workbench", inline=True, style={"display": "inline-block", "marginLeft": "2em"}),
            dcc.Checklist(id="panels", options=[{"label": "Controls", "value": "controls"},
                                                {"label": "Inspector", "value": "inspector"},
                                                {"label": "Tables", "value": "tables"}],
                          value=["controls", "inspector", "tables"], inline=True,
                          style={"display": "inline-block", "marginLeft": "2em"}),
            html.Button("Graph only", id="graph-only"),
            html.Span(id="verify-result", style={"marginLeft": "2em"}),
            html.Span(id="error-message", style={"color": "#a00", "marginLeft": "1em"}),
        ], style={"padding": "6px 12px"}),
    ])
    help_modal = html.Div([html.Button("×", id="help-close", style={"float": "right"}),
                           dcc.Markdown(id="help-body", link_target="_blank")],
                          id="help-modal", className="panel floating", style={"display": "none", "width": "560px"})
    return html.Div([
        *stores, header,
        html.Div([controls, html.Div(blocks, id="main", style={"display": "flex", "flexDirection": "column",
                                                                 "flex": "1 1 auto", "minWidth": "0"})],
                 style={"display": "flex"}),
        help_modal,
    ], id="root")


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
