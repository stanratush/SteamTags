"""The renderer boundary, Python half: the only Python module that knows how the graph is drawn.

The other half is `assets/graph.js`, which owns a vendored Cytoscape.js (`assets/cytoscape.min.js`).
Dash sends one store (`graph-data`): elements (ids, labels, cluster, colour, size, classes), target
positions computed in Python, regions, the selection and view commands. Taps on a node, an edge, a
region title or the background come back through `dash_clientside.set_props` on the `graph-event`
store. The payload carries only ids, labels and styling data; AppID lists stay on the server.
Replacing the renderer means replacing this module and `graph.js`.
"""

from __future__ import annotations

from typing import Any

from dash import ClientsideFunction, dcc, html

from steamstudy.i18n import Text
from steamstudy.network.layout import label_width

GRAPH_ID = "cy"
DATA_ID = "graph-data"
EVENT_ID = "graph-event"
ACK_ID = "graph-ack"
DRAGGED_ID = "graph-dragged"  # {basis, positions}: the nodes dragged in the Global layout, reported by graph.js
CANVAS_ID = "graph-canvas"  # the canvas's free area {w, h} in pixels, in steps, reported by graph.js
# Slightly muted cluster colours (prototype variant B); One-Tag Clusters stay grey.
PALETTE = ["#5b7fb0", "#d08a4e", "#6a9c64", "#c0646a", "#6ea8a5", "#c9ad4f", "#9a7fa8", "#d79aa4", "#8f7766",
           "#86aeb0", "#c27d9b", "#93bf88", "#a8945a", "#5f9592", "#e3b9c8", "#837b78"]
ONE_TAG_COLOR = "#b8b8b8"
REGION_COLOR = "#999999"

# graph.js registers this namespace; its `render` takes the `graph-data` store.
RENDER = ClientsideFunction(namespace="tagGraph", function_name="render")


def cluster_color(label: str, kind: str) -> str:
    if kind == "one_tag":
        return ONE_TAG_COLOR
    index = int(label[1:]) - 1 if label[1:].isdigit() else 0
    return PALETTE[index % len(PALETTE)]


def graph_component() -> list[Any]:
    """The canvas container plus the stores of the boundary. The canvas fills `.graph-canvas` (app.css) and
    follows its size."""
    return [html.Div(id=GRAPH_ID, className="graph-canvas"),
            dcc.Store(id=DATA_ID, data={}), dcc.Store(id=EVENT_ID), dcc.Store(id=ACK_ID), dcc.Store(id=CANVAS_ID),
            dcc.Store(id=DRAGGED_ID)]


def selection_ref(selection: dict[str, Any] | None) -> dict[str, str] | None:
    """What the canvas needs to know about the selection: its kind and element id."""
    if not selection or selection.get("kind") not in ("node", "edge", "cluster", "pair"):
        return None
    return {"kind": selection["kind"], "id": str(selection["id"])}


def priority(nodes: list[dict[str, Any]]) -> dict[str, int]:
    """Node id -> culling rank (0 first) of every label: the Cluster Centers, then the other tags, each by n_games
    (ties by tag id). The canvas ranks the selection and its neighbours above all."""
    ranked = sorted(nodes, key=lambda n: (not n["center"], -n["n_games"], int(n["id"])))
    return {n["id"]: rank for rank, n in enumerate(ranked)}


# Edge Appearance (spec: "Edge Appearance"): graph.js owns the look and draws it from each edge's raw values; these
# are its defaults, steps and bounds. The defaults draw exactly the links of before: 0.4 + 2.6 × value / largest px,
# one colour, 18% strength, 6% between Clusters in the Cluster-separated layout. A view choice only: never part of
# the Network State, an export or a cache key.
APPEARANCE: dict[str, Any] = {
    "defaults": {"width": [0.4, 3.0], "scale": "linear", "color": "one", "strength": 0.18, "between": 0.06},
    "steps": {"width": 1.25, "strength": 1.35, "between": 1.5},
    "limits": {"width_min": [0.1, 3.0], "width_max": [1.0, 12.0], "strength": [0.03, 1.0], "between": [0.0, 1.0]},
    "colors": {"one": "#8d95a3", "neutral": "#b3b8c2", "within": "#5b6478", "between": "#e08a3c",
               "ramp": ["#c9ced8", "#3b2f6b"], "dark": "#4a5262"},
}


def edge_thickness(weight: str, show_shared: bool) -> str:
    """What edge width shows: the Clustering Weight, unless the switch asks for shared games under lift."""
    return "shared_games" if show_shared else weight


def thickness_key(weight: str, show_shared: bool, tx: Text) -> tuple[str, dict[str, str]]:
    """The legend's name for what edge width shows, and the switch's style: offered only under lift. The browser
    renames it when the switch is toggled (graph.js `edgeKey`, with the same words from the ui-words store)."""
    measure = tx("shared games") if edge_thickness(weight, show_shared) == "shared_games" else tx("lift")
    return tx("Edge thickness: {measure}", measure=measure), {} if weight == "lift" else {"display": "none"}


def payload(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], positions: dict[str, list[float]], *,
            dataset: str, layout: str = "global", regions: list[dict[str, Any]] | None = None,
            selection: dict[str, Any] | None = None, weight: str = "shared_games",
            basis: list[Any] | None = None, zoom: float = 1.0, min_shared: int | None = None) -> dict[str, Any]:
    """The `graph-data` store. nodes: {id, label, cluster, kind, size, center}; edges: {source, target, shared,
    lift, intra}; positions: node id -> [x, y]; regions: {label, cluster, color, x, y, width, height} (top-left corner).
    A node's size comes from the layout (fixed by its games, in the positions' units), never from what is visible;
    `lw` is its label's width on screen (`label_width`), for the fit. `basis` (dataset, Minimum Months Filter,
    Clustering Weight, seed) tells the canvas when to drop dragged positions. `zoom` is the zoom the labels are
    spaced for: zoomed out further, the canvas hides labels that would overlap. An edge carries its raw values
    (shared games, lift, and whether it lies inside one Cluster); graph.js draws its width, colour and strength from
    them, by the Clustering Weight `weight` (or shared games, when the legend's switch asks for them under lift)."""
    separated = layout == "separated"
    ranks = priority(nodes)
    out_nodes = []
    for n in nodes:
        classes = [n["kind"]] + (["center"] if n["center"] else [])
        out_nodes.append({"id": n["id"], "label": n["label"], "cluster": n["cluster"],
                          "color": cluster_color(n["cluster"], n["kind"]), "size": n["size"],
                          "lw": label_width(n["label"]),
                          "classes": " ".join(classes), "prio": ranks[n["id"]]})
    out_edges = [{"id": f"{e['source']}-{e['target']}", "source": e["source"], "target": e["target"],
                  "shared": e["shared"], "lift": e["lift"], "intra": bool(e["intra"]),
                  "classes": ("intra" if e["intra"] else "inter") + (" separated" if separated else "")}
                 for e in edges]
    out_regions = [{"id": f"region-{r.get('cluster') or i}", "label": r["label"], "cluster": r.get("cluster", ""),
                    "color": r.get("color", REGION_COLOR), "x": r["x"] + r["width"] / 2, "y": r["y"] + r["height"] / 2,
                    "w": r["width"], "h": r["height"], **({"count": r["count"]} if "count" in r else {})}
                   for i, r in enumerate(regions or [])]
    return {"dataset": dataset, "layout": layout, "basis": list(basis or [dataset]), "nodes": out_nodes,
            "edges": out_edges, "weight": weight, "appearance": APPEARANCE, "min_shared": min_shared,
            "positions": {n["id"]: list(positions.get(n["id"], (0.0, 0.0))) for n in nodes},
            "regions": out_regions, "selected": selection_ref(selection), "view": None, "zoom": zoom}
