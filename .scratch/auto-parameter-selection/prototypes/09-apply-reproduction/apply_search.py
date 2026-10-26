import json, math, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(".scratch/auto-parameter-selection/prototypes/05-grid-run").resolve()))
import grid_run as G

def job(r):
    import igraph as ig
    from steamstudy.network.graph import build_network
    d, g, s = r["dataset"], r["g"], r["s"]
    rec = G.compute_pair((d, g, s, False))
    m = np.array(rec["selected"]["membership"])
    games, context, base = G._W["data"][d]
    net = build_network(games, base.with_(min_games_per_tag=g, min_shared_games=s), context)
    idx = {t: i for i, t in enumerate(net.nodes)}
    igg = ig.Graph(n=len(net.nodes), edges=[(idx[e.u], idx[e.v]) for e in net.edges])
    w = [e.lift for e in net.edges]
    gam = [round(x / 100, 2) for x in range(math.ceil(r["a"] * 100), math.floor(r["b"] * 100) + 1)]
    gam.sort(key=lambda x: (abs(x - r["mid"]), x))
    seeds = [G._W["main_seed"], *G._W["scan"]]
    for gi, x in enumerate(gam):
        for si, sd in enumerate(seeds):
            if np.array_equal(G.leiden(igg, w, x, sd), m):
                return {**r, "found": True, "gamma": x, "seed_idx": si, "dist": abs(x - r["mid"]), "n_gamma": len(gam)}
    return {**r, "found": False, "n_gamma": len(gam)}

if __name__ == "__main__":
    res = json.loads(Path(sys.argv[1]).read_text())
    fail = [r for r in res if r["selected"] and not r["main_exact"] and r["scan_exact_at_wb"] == 0]
    with Pool(12, initializer=G.init_worker, initargs=(G.DATASETS,)) as p:
        out = p.map(job, fail, chunksize=1)
    f = [o for o in out if o["found"]]
    print("failing:", len(out), "rescued:", len(f))
    print("gamma shift from midpoint (rescued):", sorted(round(o["dist"], 3) for o in f))
    print("unrescued hits:", sorted(o["hits"] for o in out if not o["found"]))
    print("unrescued domain grid size:", sorted(o["n_gamma"] for o in out if not o["found"]))
    print("all failing hits:", sorted(o["hits"] for o in out))
