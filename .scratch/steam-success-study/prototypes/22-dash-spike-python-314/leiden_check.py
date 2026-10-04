import json, sys, warnings
warnings.simplefilter("default")
import igraph as ig, leidenalg as la
sys.path.insert(0, ".")
data = json.load(open("synthetic_graph.json"))
ids = [n["id"] for n in data["nodes"]]; idx = {v: i for i, v in enumerate(ids)}
g = ig.Graph(n=len(ids), edges=[(idx[e["source"]], idx[e["target"]]) for e in data["edges"]])
g.es["weight"] = [e["weight"] for e in data["edges"]]
runs = []
for _ in range(2):
    p = la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight",
                          resolution_parameter=1.0, n_iterations=-1, seed=42)
    runs.append(list(p.membership)); print(f"clusters={len(p)} Q={p.quality():.4f} modularity={g.modularity(p.membership, weights='weight'):.4f}")
print("identical memberships:", runs[0] == runs[1], "| nodes", g.vcount(), "edges", g.ecount())
