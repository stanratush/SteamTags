"""Ticket 09 fact-finding: does the Workbench (one seed, two-decimal gamma) reproduce the Selected Partition?"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(".scratch/auto-parameter-selection/prototypes/05-grid-run").resolve()))
import grid_run as G  # noqa: E402


def job(args):
    import igraph as ig
    from sklearn.metrics import adjusted_rand_score
    from steamstudy.network.graph import build_network

    d, g, s = args
    rec = G.compute_pair((d, g, s, False))
    sel = rec.get("selected")
    if not sel:
        return {"dataset": d, "g": g, "s": s, "selected": False}
    games, context, base = G._W["data"][d]
    net = build_network(games, base.with_(min_games_per_tag=g, min_shared_games=s), context)
    idx = {t: i for i, t in enumerate(net.nodes)}
    u = [idx[e.u] for e in net.edges]
    v = [idx[e.v] for e in net.edges]
    igg = ig.Graph(n=len(net.nodes), edges=list(zip(u, v)))
    w = [e.lift for e in net.edges]
    m = np.array(sel["membership"])
    wb = sel["workbench_resolution"]
    out = {"dataset": d, "g": g, "s": s, "selected": True, "wb": wb, "mid": sel["selected_resolution"],
           "a": sel["a"], "b": sel["b"], "first": sel["first"], "hits": sel["hits"]}
    fg, fs = sel["first"]
    out["first_in_domain"] = sel["a"] <= fg <= sel["b"]
    if wb is None:
        return out
    main = G.leiden(igg, w, wb, G._W["main_seed"])
    out["main_exact"] = bool(np.array_equal(main, m))
    out["main_ari"] = float(adjusted_rand_score(m, main))
    scan_hits = [i for i, sd in enumerate(G._W["scan"]) if np.array_equal(G.leiden(igg, w, wb, sd), m)]
    out["scan_exact_at_wb"] = len(scan_hits)
    out["first_scan_seed_at_wb"] = scan_hits[0] if scan_hits else None
    return out


if __name__ == "__main__":
    jobs = [(d, g, s) for d in G.DATASETS for g, s in G.pairs()]
    with Pool(12, initializer=G.init_worker, initargs=(G.DATASETS,)) as pool:
        res = pool.map(job, jobs, chunksize=4)
    Path(sys.argv[1]).write_text(json.dumps(res))
    sel = [r for r in res if r["selected"] and r.get("wb") is not None]
    print("pairs with selection & representable:", len(sel))
    print("first (gamma,seed) inside domain:", sum(r["first_in_domain"] for r in res if r["selected"]))
    print("main seed exact at wb:", sum(r["main_exact"] for r in sel))
    print("some scan seed exact at wb:", sum(r["scan_exact_at_wb"] > 0 for r in sel))
    print("neither main nor scan exact:", sum((not r["main_exact"]) and r["scan_exact_at_wb"] == 0 for r in sel))
    aris = sorted(r["main_ari"] for r in sel if not r["main_exact"])
    if aris:
        print("main ARI when not exact: min %.3f median %.3f" % (aris[0], aris[len(aris) // 2]))
    picks = {("overall", 17, 2), ("puzzle", 14, 2), ("rpg", 14, 12), ("simulation", 14, 5), ("strategy", 14, 2)}
    for r in sel:
        if (r["dataset"], r["g"], r["s"]) in picks:
            print(r)
