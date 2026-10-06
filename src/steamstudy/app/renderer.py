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

GRAPH_ID = "cy"
DATA_ID = "graph-data"
EVENT_ID = "graph-event"
ACK_ID = "graph-ack"
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f",
           "#86bcb6", "#d37295", "#8cd17d", "#b6992d", "#499894", "#fabfd2", "#79706e"]
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
            dcc.Store(id=DATA_ID, data={}), dcc.Store(id=EVENT_ID), dcc.Store(id=ACK_ID)]


def selection_ref(selection: dict[str, Any] | None) -> dict[str, str] | None:
    """What the canvas needs to know about the selection: its kind and element id."""
    if not selection or selection.get("kind") not in ("node", "edge", "cluster"):
        return None
    return {"kind": selection["kind"], "id": str(selection["id"])}


def payload(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], positions: dict[str, list[float]], *,
            dataset: str, layout: str = "global", regions: list[dict[str, Any]] | None = None,
            selection: dict[str, Any] | None = None, max_shared: int = 1) -> dict[str, Any]:
    """The `graph-data` store. nodes: {id, label, cluster, kind, n_games, center}; edges: {source, target, shared,
    intra}; positions: node id -> [x, y]; regions: {label, cluster, color, x, y, width, height} (top-left corner)."""
    separated = layout == "separated"
    biggest = max([n["n_games"] for n in nodes] + [1])
    out_nodes = []
    for n in nodes:
        classes = [n["kind"]] + (["center"] if n["center"] else [])
        out_nodes.append({"id": n["id"], "label": n["label"], "cluster": n["cluster"],
                          "color": cluster_color(n["cluster"], n["kind"]), "size": 12 + 26 * (n["n_games"] / biggest),
                          "classes": " ".join(classes)})
    out_edges = [{"id": f"{e['source']}-{e['target']}", "source": e["source"], "target": e["target"],
                  "width": 0.6 + 6 * (e["shared"] / max(max_shared, 1)),
                  "classes": ("intra" if e["intra"] else "inter") + (" separated" if separated else "")}
                 for e in edges]
    out_regions = [{"id": f"region-{r.get('cluster') or i}", "label": r["label"], "cluster": r.get("cluster", ""),
                    "color": r.get("color", REGION_COLOR), "x": r["x"] + r["width"] / 2, "y": r["y"] + r["height"] / 2,
                    "w": r["width"], "h": r["height"]} for i, r in enumerate(regions or [])]
    return {"dataset": dataset, "layout": layout, "nodes": out_nodes, "edges": out_edges,
            "positions": {n["id"]: list(positions.get(n["id"], (0.0, 0.0))) for n in nodes},
            "regions": out_regions, "selected": selection_ref(selection), "view": None}
