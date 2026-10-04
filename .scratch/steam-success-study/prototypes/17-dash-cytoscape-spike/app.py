"""Throwaway spike for ticket 17: does Dash 4 + dash-cytoscape + dash-ag-grid work on Windows?

Synthetic graph only (~400 tag nodes, ~5,000 weighted edges carrying AppID lists).
Checks: rendering + cluster-centre styling, node/edge tap events, background callback
with progress + cancel (Windows spawn), rapid threshold toggling, switching preset
layouts (Global / Cluster-separated + tinted region nodes) by updating `elements` only,
and mounting the graph from a callback (dash-cytoscape #229).
"""

import json
import math
import random
import time
from pathlib import Path

import dash
import dash_ag_grid as dag
import dash_cytoscape as cyto
import diskcache
import networkx as nx
from dash import DiskcacheManager, Input, Output, State, dcc, html

HERE = Path(__file__).parent
GRAPH_PATH = HERE / "synthetic_graph.json"
CACHE_DIR = HERE / ".cache"

PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
    "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d37295",
    "#8cd17d", "#b6992d", "#499894", "#fabfd2",
]


def build_synthetic_graph(seed=7):
    """Planted-partition graph: 400 nodes, 12 groups, ~5,000 edges with AppID lists."""
    rng = random.Random(seed)
    sizes = [34] * 8 + [32] * 4  # 400
    g = nx.random_partition_graph(sizes, 0.5, 0.025, seed=seed)
    nodes = [{"id": f"t{n}", "label": f"Tag {n}", "games": rng.randint(8, 100)} for n in g.nodes]
    edges = []
    for u, v in g.edges:
        w = min(100, int(rng.paretovariate(1.3) * 3))
        appids = rng.sample(range(10_000, 3_000_000), w)
        edges.append({"source": f"t{u}", "target": f"t{v}", "weight": w, "appids": appids})
    return {"nodes": nodes, "edges": edges}


def load_graph():
    if not GRAPH_PATH.exists():
        GRAPH_PATH.write_text(json.dumps(build_synthetic_graph()))
    return json.loads(GRAPH_PATH.read_text())


def to_nx(data, min_games, min_shared, removed=()):
    g = nx.Graph()
    keep = {n["id"] for n in data["nodes"] if n["games"] >= min_games and n["id"] not in removed}
    g.add_nodes_from(sorted(keep))
    for e in data["edges"]:
        if e["source"] in keep and e["target"] in keep and e["weight"] >= min_shared:
            g.add_edge(e["source"], e["target"], weight=e["weight"])
    return g


def cluster(g, seed):
    comms = nx.community.louvain_communities(g, weight="weight", seed=seed)
    comms = sorted((sorted(c) for c in comms), key=lambda c: (-len(c), c[0]))
    membership = {n: i for i, c in enumerate(comms) for n in c}
    centers = set()
    for c in comms:
        sub = g.subgraph(c)
        centers.add(max(c, key=lambda n: (sub.degree(n, weight="weight"), n)))
    return comms, membership, centers


DATA = load_graph()
NODE_BY_ID = {n["id"]: n for n in DATA["nodes"]}

# Positions are computed once on the full graph and reused across filter changes.
_full = to_nx(DATA, 0, 0)
_comms, _membership, _ = cluster(_full, seed=42)
GLOBAL_POS = {
    n: (x * 1400, y * 1400)
    for n, (x, y) in nx.spring_layout(_full, weight="weight", seed=42, iterations=60).items()
}
SEPARATED_POS, REGIONS = {}, []
_cols = math.ceil(math.sqrt(len(_comms)))
for i, comm in enumerate(_comms):
    cx, cy = (i % _cols) * 700, (i // _cols) * 700
    sub_pos = nx.spring_layout(_full.subgraph(comm), seed=42, iterations=50)
    for n, (x, y) in sub_pos.items():
        SEPARATED_POS[n] = (cx + x * 260, cy + y * 260)
    REGIONS.append({"cluster": i, "x": cx, "y": cy, "w": 620, "h": 620})


def make_elements(min_games, min_shared, layout, seed):
    g = to_nx(DATA, min_games, min_shared)
    comms, membership, centers = cluster(g, seed)
    pos = GLOBAL_POS if layout == "global" else SEPARATED_POS
    els = []
    if layout == "separated":
        for r in REGIONS:
            els.append({
                "data": {"id": f"region{r['cluster']}", "w": r["w"], "h": r["h"],
                         "color": PALETTE[r["cluster"] % len(PALETTE)]},
                "position": {"x": r["x"], "y": r["y"]},
                "classes": "region", "selectable": False, "grabbable": False, "locked": True,
            })
    for n in g.nodes:
        c = membership[n]
        x, y = pos[n]
        els.append({
            "data": {"id": n, "label": NODE_BY_ID[n]["label"], "games": NODE_BY_ID[n]["games"],
                     "cluster": c, "color": PALETTE[c % len(PALETTE)],
                     "degree": g.degree(n, weight="weight")},
            "position": {"x": x, "y": y},
            "classes": "center" if n in centers else "",
        })
    for e in DATA["edges"]:
        if g.has_edge(e["source"], e["target"]):
            els.append({"data": {"id": f"{e['source']}-{e['target']}", "source": e["source"],
                                 "target": e["target"], "weight": e["weight"],
                                 "appids": e["appids"]}})
    return els, g.number_of_nodes(), g.number_of_edges(), len(comms)


STYLESHEET = [
    {"selector": "node", "style": {
        "background-color": "data(color)", "label": "data(label)", "font-size": 9,
        "min-zoomed-font-size": 8, "width": "mapData(games, 8, 100, 10, 30)",
        "height": "mapData(games, 8, 100, 10, 30)", "z-index": 10}},
    {"selector": "node.center", "style": {
        "shape": "diamond", "border-width": 3, "border-color": "#111", "width": 34, "height": 34,
        "font-weight": "bold", "z-index": 20}},
    {"selector": "node.region", "style": {
        "shape": "round-rectangle", "width": "data(w)", "height": "data(h)",
        "background-color": "data(color)", "background-opacity": 0.12, "border-width": 0,
        "label": "", "z-index": 0, "events": "no"}},
    {"selector": "edge", "style": {
        "curve-style": "haystack", "haystack-radius": 0, "line-color": "#999",
        "opacity": 0.35, "width": "mapData(weight, 1, 100, 0.5, 6)"}},
    {"selector": ":selected", "style": {"border-width": 4, "border-color": "#e00", "line-color": "#e00", "opacity": 1}},
]

cache = diskcache.Cache(str(CACHE_DIR))
background_callback_manager = DiskcacheManager(cache)

app = dash.Dash(__name__, background_callback_manager=background_callback_manager)

graph_component = cyto.Cytoscape(
    id="cy", elements=[], stylesheet=STYLESHEET, layout={"name": "preset", "fit": True},
    style={"width": "100%", "height": "620px", "border": "1px solid #ccc"},
    minZoom=0.05, maxZoom=4,
)

controls = html.Div([
    html.Label("Min games per tag"),
    dcc.Slider(id="min-games", min=8, max=60, step=1, value=8, marks=None,
               tooltip={"placement": "bottom", "always_visible": True}),
    html.Label("Min shared games"),
    dcc.Slider(id="min-shared", min=1, max=40, step=1, value=8, marks=None,
               tooltip={"placement": "bottom", "always_visible": True}),
    dcc.RadioItems(id="layout", options=[{"label": "Global", "value": "global"},
                                         {"label": "Cluster-separated", "value": "separated"}],
                   value="global", inline=True),
    html.Div(id="stats"),
    html.Hr(),
    html.Button("Run sensitivity", id="run"), html.Button("Cancel", id="cancel"),
    html.Progress(id="progress", value="0", max="100", style={"width": "100%"}),
    html.Div(id="sens-result"),
], style={"width": "22%", "padding": "8px"})

workbench = html.Div([
    controls,
    html.Div([graph_component,
              html.Div(id="tap-node"), html.Div(id="tap-edge"),
              dag.AgGrid(id="edge-grid", columnDefs=[{"field": "appid", "filter": True, "sortable": True}],
                         rowData=[], style={"height": "200px"})],
             style={"width": "76%"}),
], id="workbench", style={"display": "flex"})

app.layout = html.Div([
    html.H3("Ticket 17 spike: Dash + dash-cytoscape on Windows"),
    html.Div([
        dcc.RadioItems(id="mode", options=["Workbench", "Analysis"], value="Workbench", inline=True),
        html.Span(" | callback-mounted graph test: "),
        html.Button("Mount graph from callback", id="mount"),
    ]),
    workbench,
    html.Div("Analysis report mode (graph hidden via CSS, component stays mounted).",
             id="analysis", style={"display": "none"}),
    html.Div(id="mounted-slot"),
    html.Div(id="versions"),
])


@app.callback(Output("workbench", "style"), Output("analysis", "style"), Input("mode", "value"))
def switch_mode(mode):
    wb = {"display": "flex"} if mode == "Workbench" else {"display": "none"}
    an = {"display": "block"} if mode == "Analysis" else {"display": "none"}
    return wb, an


@app.callback(Output("cy", "elements"), Output("stats", "children"),
              Input("min-games", "value"), Input("min-shared", "value"), Input("layout", "value"))
def update_graph(min_games, min_shared, layout):
    t0 = time.perf_counter()
    els, n, m, k = make_elements(min_games, min_shared, layout, seed=42)
    dt = (time.perf_counter() - t0) * 1000
    return els, f"{n} nodes, {m} edges, {k} clusters; build+cluster {dt:.0f} ms"


@app.callback(Output("tap-node", "children"), Input("cy", "tapNodeData"))
def show_node(d):
    if not d:
        return "Node: (none)"
    return f"Node tapped in Python: {d['label']} cluster={d['cluster']} games={d['games']}"


@app.callback(Output("tap-edge", "children"), Output("edge-grid", "rowData"), Input("cy", "tapEdgeData"))
def show_edge(d):
    if not d:
        return "Edge: (none)", []
    return (f"Edge tapped in Python: {d['source']}–{d['target']} weight={d['weight']} "
            f"appids={len(d['appids'])}", [{"appid": a} for a in d["appids"]])


@dash.callback(
    Output("sens-result", "children"),
    Input("run", "n_clicks"),
    State("min-games", "value"), State("min-shared", "value"),
    background=True,
    running=[(Output("run", "disabled"), True, False), (Output("cancel", "disabled"), False, True)],
    cancel=[Input("cancel", "n_clicks")],
    progress=[Output("progress", "value"), Output("progress", "max")],
    prevent_initial_call=True,
)
def run_sensitivity(set_progress, _n, min_games, min_shared):
    # Only picklable inputs cross the process boundary: a file path and ints.
    data = json.loads(GRAPH_PATH.read_text())
    g = to_nx(data, min_games, min_shared)
    base = len(cluster(g, 42)[0])
    nodes = sorted(g.nodes)[:40]
    deltas = []
    for i, n in enumerate(nodes, 1):
        h = g.copy()
        h.remove_node(n)
        deltas.append((n, len(cluster(h, 42)[0]) - base))
        set_progress((str(i), str(len(nodes))))
    changed = sum(1 for _, d in deltas if d)
    return f"Sensitivity done: {len(nodes)} nodes, {changed} changed cluster count (pid-separated job)"


@app.callback(Output("mounted-slot", "children"), Input("mount", "n_clicks"), prevent_initial_call=True)
def mount_from_callback(_n):
    els, *_ = make_elements(8, 8, "global", 42)
    return cyto.Cytoscape(id="cy2", elements=els, stylesheet=STYLESHEET, layout={"name": "preset"},
                          style={"width": "100%", "height": "300px"})


@app.callback(Output("versions", "children"), Input("mode", "value"))
def versions(_):
    import platform
    import sys
    return (f"Python {sys.version.split()[0]} on {platform.platform()} | dash {dash.__version__} | "
            f"dash-cytoscape {cyto.__version__} | dash-ag-grid {dag.__version__} | "
            f"diskcache {diskcache.__version__} | networkx {nx.__version__}")


if __name__ == "__main__":
    import sys
    app.run(debug="--debug" in sys.argv, port=8050, use_reloader=False)
