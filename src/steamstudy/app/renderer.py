"""The renderer boundary: the only module that knows the graph is drawn with dash-cytoscape.

It takes nodes, edges, a stylesheet and positions, sends a `preset` layout with positions computed in
Python, and re-fits explicitly once elements arrive. The payload carries only ids, weights and styling
data; AppID lists stay on the server. Replacing the renderer (planned: Cytoscape.js 3.34 with WebGL)
means replacing this module.
"""

from __future__ import annotations

from typing import Any

import dash_cytoscape as cyto

GRAPH_ID = "cy"
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f",
           "#86bcb6", "#d37295", "#8cd17d", "#b6992d", "#499894", "#fabfd2", "#79706e"]
ONE_TAG_COLOR = "#b8b8b8"


def cluster_color(label: str, kind: str) -> str:
    if kind == "one_tag":
        return ONE_TAG_COLOR
    index = int(label[1:]) - 1 if label[1:].isdigit() else 0
    return PALETTE[index % len(PALETTE)]


def stylesheet() -> list[dict[str, Any]]:
    return [
        {"selector": "node", "style": {
            "background-color": "data(color)", "label": "data(label)", "font-size": 10, "min-zoomed-font-size": 7,
            "width": "data(size)", "height": "data(size)", "z-index": 10, "color": "#222",
            "text-outline-color": "#fff", "text-outline-width": 1}},
        {"selector": "node.one_tag", "style": {"opacity": 0.7}},
        {"selector": "node.center", "style": {
            "shape": "diamond", "border-width": 3, "border-color": "#111", "font-weight": "bold", "z-index": 20}},
        {"selector": "node.region", "style": {
            "shape": "round-rectangle", "width": "data(w)", "height": "data(h)", "background-color": "data(color)",
            "background-opacity": 0.1, "border-width": 1, "border-color": "data(color)", "border-opacity": 0.4,
            "label": "data(label)", "text-valign": "top", "text-halign": "center", "font-size": 14,
            "color": "#555", "text-outline-width": 0, "z-index": 0, "events": "no"}},
        {"selector": "edge", "style": {
            "curve-style": "haystack", "haystack-radius": 0, "line-color": "#8a8a8a", "opacity": 0.45,
            "width": "data(width)"}},
        {"selector": "edge.inter.separated", "style": {"opacity": 0.08}},
        {"selector": ":selected", "style": {"border-width": 4, "border-color": "#d00", "line-color": "#d00",
                                            "opacity": 1}},
    ]


def graph_component(height: str = "62vh") -> cyto.Cytoscape:
    return cyto.Cytoscape(
        id=GRAPH_ID, elements=[], stylesheet=stylesheet(), layout={"name": "preset", "fit": False},
        style={"width": "100%", "height": height, "border": "1px solid #ddd", "background": "#fff"},
        minZoom=0.05, maxZoom=5, boxSelectionEnabled=False, autoRefreshLayout=False,
    )


def elements(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], positions: dict[str, list[float]],
             *, separated: bool = False, regions: list[dict[str, Any]] | None = None, selected: str | None = None,
             max_shared: int = 1) -> list[dict[str, Any]]:
    """Cytoscape elements. nodes: {id, label, cluster, kind, n_games, center}; edges: {source, target, shared, intra}."""
    out: list[dict[str, Any]] = []
    for i, r in enumerate(regions or []):
        out.append({"data": {"id": f"region-{i}", "label": r["label"], "w": r["width"], "h": r["height"],
                             "color": r.get("color", "#999"), "cluster": r.get("cluster", "")},
                    "position": {"x": r["x"] + r["width"] / 2, "y": r["y"] + r["height"] / 2},
                    "classes": "region", "selectable": False, "grabbable": False, "locked": True})
    biggest = max([n["n_games"] for n in nodes] + [1])
    for n in nodes:
        x, y = positions.get(n["id"], (0.0, 0.0))
        node_classes = [n["kind"]] + (["center"] if n["center"] else [])
        out.append({"data": {"id": n["id"], "label": n["label"], "cluster": n["cluster"],
                             "color": cluster_color(n["cluster"], n["kind"]),
                             "size": 12 + 26 * (n["n_games"] / biggest)},
                    "position": {"x": x, "y": y}, "classes": " ".join(node_classes), "selected": n["id"] == selected})
    for e in edges:
        classes = ("intra" if e["intra"] else "inter") + (" separated" if separated else "")
        out.append({"data": {"id": f"{e['source']}-{e['target']}", "source": e["source"], "target": e["target"],
                             "shared": e["shared"], "width": 0.6 + 6 * (e["shared"] / max(max_shared, 1))},
                    "classes": classes, "selected": f"{e['source']}-{e['target']}" == selected})
    return out


# Clientside: re-fit once elements arrive for a new dataset (the preset layout's own `fit` is not relied on).
FIT_JS = """
function(elements, fitKey, fitted) {
    if (!elements || elements.length === 0 || fitted === fitKey) { return window.dash_clientside.no_update; }
    const root = document.getElementById('%s');
    if (!root) { return window.dash_clientside.no_update; }
    const holders = [root, ...root.querySelectorAll('div')];
    const holder = holders.find(el => el._cyreg && el._cyreg.cy);
    if (!holder) { return window.dash_clientside.no_update; }
    setTimeout(() => holder._cyreg.cy.fit(undefined, 30), 50);
    return fitKey;
}
""" % GRAPH_ID
