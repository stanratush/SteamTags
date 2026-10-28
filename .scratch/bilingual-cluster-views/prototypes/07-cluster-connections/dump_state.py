"""PROTOTYPE, throwaway: dump the latest Build's Cluster connections for the cluster-connections prototype.

For the default Overall and Puzzle Network States, Overall under the lift Clustering Weight and Overall at γ = 2.5
(many Clusters), it builds the
`elements-base` store and the `graph-data` payload of both layouts exactly as the edge-appearance prototype did
(callbacks.render_graph, 1302 x 581 canvas), plus every `cluster_connections.csv` row with the five columns settled
in ticket 06 (ADR 0004): shared_weight, ratio, shared_ratio, share_of_a, share_of_b. Those five are computed HERE,
prototype-only, from the per-tag strengths; nothing in src/ changes. Writes data.js and inlines it into the HTML.
Read-only: it changes no Network State, cache or export.
Run: .venv/Scripts/python .scratch/bilingual-cluster-views/prototypes/07-cluster-connections/dump_state.py
"""
import dataclasses
import json
import math
import re
import sys
from pathlib import Path

from steamstudy.app.callbacks import render_graph
from steamstudy.app.loader import load_build
from steamstudy.app.renderer import cluster_color
from steamstudy.build.writer import resolve_build
from steamstudy.network.layout import layout_input
from steamstudy.network.state import compute_state
from steamstudy.network.tables import state_tables

CANVAS = {"w": 1302, "h": 581}
POOL = "one_tag_pool"


def measures(state):
    """Ticket 06's columns per connections row. Pool share uses cut_p = weight with at least one end in the pool,
    counted once (= k_p - w_pp), so the pool's shares also add up to 1 (PROTOTYPE choice, not settled in 06)."""
    g = state.graph
    group = {t: (c.label if c.size >= 2 else POOL) for c in state.clusters for t in c.members}
    k = {t: g.degree(t, weight="w") for t in g.nodes}
    ks = {t: g.degree(t, weight="shared") for t in g.nodes}
    two_m, two_ms = math.fsum(k.values()), math.fsum(ks.values())
    kg, ksg, sq, sqs = {}, {}, {}, {}
    for t, a in group.items():
        kg[a] = kg.get(a, 0.0) + k.get(t, 0.0)
        ksg[a] = ksg.get(a, 0.0) + ks.get(t, 0.0)
        sq[a] = sq.get(a, 0.0) + k.get(t, 0.0) ** 2
        sqs[a] = sqs.get(a, 0.0) + ks.get(t, 0.0) ** 2
    shared_w: dict[tuple[str, str], float] = {}
    for u, v, d in g.edges(data=True):
        a, b = group[u], group[v]
        shared_w[(a, b)] = shared_w.get((a, b), 0.0) + d["shared"]
        if a != b:
            shared_w[(b, a)] = shared_w.get((b, a), 0.0) + d["shared"]
    pool_pool = next((w for a, b, _, w in state.connections if a == b == POOL), 0.0)
    cut = {c.label: state.cluster_metrics[c.label].cut_weight for c in state.clusters if c.size >= 2}
    if POOL in kg:
        cut[POOL] = kg[POOL] - pool_pool

    def expect(a, b, kk, ss, tm):
        if not tm:
            return 0.0
        return (kk[a] ** 2 - ss[a]) / (2 * tm) if a == b else kk[a] * kk[b] / tm

    rows = []
    for a, b, n, w in state.connections:
        sw = shared_w.get((a, b), 0.0)
        e, es = expect(a, b, kg, sq, two_m), expect(a, b, ksg, sqs, two_ms)
        rows.append({"cluster_a": a, "cluster_b": b, "edge_count": n, "weight": w, "shared_weight": sw,
                     "ratio": w / e if e > 0 else None, "shared_ratio": sw / es if es > 0 else None,
                     "share_of_a": w / cut[a] if cut.get(a) else None,
                     "share_of_b": w / cut[b] if cut.get(b) else None})
    groups = {a: {"k": kg[a], "k_shared": ksg[a], "cut": cut.get(a)} for a in kg}
    return rows, groups, two_m


root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
build = resolve_build(root)
c = load_build(build)
out = {"build_id": c.build_id, "states": {}}
for name, key, change in (("overall", "overall", {}), ("puzzle", "puzzle", {}),
                          ("overall-lift", "overall", {"clustering_weight": "lift"}),
                          ("overall-g25", "overall", {"resolution": 2.5})):  # many Clusters, for the overviews
    s = dataclasses.replace(c.default_settings(key), **change)
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
    rows, groups, two_m = measures(state)
    out["states"][name] = {
        "label": c.dataset(key).label, "state_id": state.state_id, "weight": s.clustering_weight,
        "gamma": s.resolution, "two_m": two_m,
        "clusters": [{"cluster": r["cluster"], "kind": r["kind"], "size": r["size"],
                      "color": cluster_color(r["cluster"], r["kind"])} for r in tables["clusters.csv"]],
        "groups": groups,
        "connections": rows,
        "edges": base["edges"],
        "global": render_graph(base, "global", None, None, CANVAS),
        "separated": render_graph(base, "separated", None, None, CANVAS),
    }
    top = max((r["ratio"] or 0) for r in rows)
    print(name, state.state_id, len(base["nodes"]), "nodes", len(base["edges"]), "edges", len(rows), "rows",
          f"max ratio {top:.3f} vs gamma {s.resolution}")

here = Path(__file__).parent
dest = here / "data.js"
dest.write_text("window.DATA = " + json.dumps(out, default=str, allow_nan=False) + ";\n", encoding="utf-8")
print(dest, dest.stat().st_size)
html = here / "PROTOTYPE-cluster-connections.html"
if html.exists():  # inline the data too, so the page works as a single file
    text = html.read_text(encoding="utf-8")
    inline = "<!--DATA--><script>" + dest.read_text(encoding="utf-8").replace("</", r"<\/") + "</script><!--/DATA-->"
    html.write_text(re.sub(r"<!--DATA-->.*?<!--/DATA-->", lambda m: inline, text, flags=re.S), encoding="utf-8",
                    newline="\n")
