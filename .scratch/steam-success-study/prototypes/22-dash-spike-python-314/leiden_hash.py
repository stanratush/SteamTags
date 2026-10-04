import json, hashlib, igraph as ig, leidenalg as la
with open("synthetic_graph.json", encoding="utf-8") as f: data = json.load(f)
ids = [n["id"] for n in data["nodes"]]; idx = {v: i for i, v in enumerate(ids)}
g = ig.Graph(n=len(ids), edges=[(idx[e["source"]], idx[e["target"]]) for e in data["edges"]]); g.es["weight"] = [e["weight"] for e in data["edges"]]
p = la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight", resolution_parameter=1.0, n_iterations=-1, seed=42)
print(hashlib.sha256(json.dumps(p.membership).encode()).hexdigest()[:16])
