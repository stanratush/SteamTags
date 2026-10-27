"""PROTOTYPE, throwaway: dump the graph payloads of the latest Build for the edge-appearance prototype.

For the default Overall and Puzzle Network States, and Overall under the lift Clustering Weight, it builds the
`elements-base` store exactly as callbacks.recompute does and the `graph-data` payload of both layouts exactly as
callbacks.render_graph does (for a 1302 x 581 canvas, the Workbench's "Graph only" view at 1440 x 900), then writes
data.js and inlines it into the HTML. Read-only: it changes no Network State, cache or export.
Run: .venv/Scripts/python .scratch/bilingual-cluster-views/prototypes/04-edge-appearance/dump_state.py
"""
import dataclasses
import json
import re
import sys
from pathlib import Path

from steamstudy.app.callbacks import render_graph
from steamstudy.app.loader import load_build
from steamstudy.build.writer import resolve_build
from steamstudy.network.layout import layout_input
from steamstudy.network.state import compute_state
from steamstudy.network.tables import state_tables

CANVAS = {"w": 1302, "h": 581}
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
build = resolve_build(root)
c = load_build(build)
out = {"build_id": c.build_id, "states": {}}
for name, key, weight in (("overall", "overall", None), ("puzzle", "puzzle", None), ("overall-lift", "overall", "lift")):
    s = c.default_settings(key)
    if weight:
        s = dataclasses.replace(s, clustering_weight=weight)
    state = compute_state(c.games(key), s, c.context(key))
    tables = state_tables(state)
    inp = layout_input(state)
    kind_of = {r["cluster"]: r["kind"] for r in tables["clusters.csv"]}
    base = {
        "nodes": [{"id": str(r["tag_id"]), "label": r["tag"], "cluster": r["cluster"], "kind": kind_of[r["cluster"]],
                   "n_games": r["n_games"], "center": r["is_center"], "size": inp.sizes[r["tag_id"]]}
                  for r in tables["nodes.csv"]],
        "edges": [{"source": str(e.u), "target": str(e.v), "shared": e.shared, "lift": e.lift,
                   "intra": state.cluster_of[e.u] == state.cluster_of[e.v]} for e in state.network.edges],
        "start": {str(t): list(p) for t, p in inp.start.items()},
        "basis": [key, s.min_months, s.clustering_weight, s.seed],
        "weight": s.clustering_weight, "seed": s.seed, "dataset": key,
    }
    out["states"][name] = {
        "label": c.dataset(key).label, "state_id": state.state_id, "weight": s.clustering_weight,
        "clusters": [{"cluster": r["cluster"], "kind": r["kind"], "size": r["size"]} for r in tables["clusters.csv"]],
        "edges": base["edges"],
        "global": render_graph(base, "global", None, None, CANVAS),
        "separated": render_graph(base, "separated", None, None, CANVAS),
    }
    print(name, state.state_id, len(base["nodes"]), "nodes", len(base["edges"]), "edges")

here = Path(__file__).parent
dest = here / "data.js"
dest.write_text("window.DATA = " + json.dumps(out, default=str, allow_nan=False) + ";\n", encoding="utf-8")
print(dest, dest.stat().st_size)
html = here / "PROTOTYPE-edge-appearance.html"
if html.exists():  # inline the data too, so the page works as a single file
    text = html.read_text(encoding="utf-8")
    inline = "<!--DATA--><script>" + dest.read_text(encoding="utf-8").replace("</", r"<\/") + "</script><!--/DATA-->"
    html.write_text(re.sub(r"<!--DATA-->.*?<!--/DATA-->", lambda m: inline, text, flags=re.S), encoding="utf-8",
                    newline="\n")
