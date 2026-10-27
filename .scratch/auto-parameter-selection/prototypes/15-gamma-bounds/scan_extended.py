"""Throwaway: does a graph-specific γ range change anything on this Build? (ticket 15, measured part)

For every Lift pair graph, scans Leiden on a 0.05 grid (the 10 scan seeds) from min(0.25, the λ2 lower bound on
γ_min, rounded down) up to gamma_pos (the provable end of the Q > 0 region, rounded up), then runs ticket 03's
selection twice on the same runs:

    fixed     input = runs at the 56 values 0.25..3.00, CHAMP on [0.25, 3.00]   (reproduces ticket 05)
    extended  input = every run, CHAMP on [scan start, gamma_pos]

and records what differs. Needs bounds.json from bounds.py.

    uv run python .scratch/auto-parameter-selection/prototypes/15-gamma-bounds/scan_extended.py --workers 12
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "05-grid-run"))
import grid_run as GR  # noqa: E402

STEP = 0.05
MAX_ITER = 1000
_CAPPED: list[tuple[float, int]] = []


def leiden_capped(ig_graph, weights, gamma: float, seed: int) -> np.ndarray:
    """`grid_run.leiden` (find_partition with n_iterations=-1) as an explicit loop, stopped after MAX_ITER passes.

    leidenalg's n_iterations=-1 repeats while a pass improves quality by > 0. At high γ, float noise (gains of
    ~1e-14) keeps it going for ever on some graphs (measured: simulation g=5 s=5 at γ = 6.2). Identical to
    find_partition whenever that terminates; capped runs are recorded."""
    import leidenalg as la

    p = la.RBConfigurationVertexPartition(ig_graph, weights=weights, resolution_parameter=gamma)
    opt = la.Optimiser()
    opt.set_rng_seed(seed)
    for _ in range(MAX_ITER):
        if opt.optimise_partition(p, n_iterations=1) <= 0:
            break
    else:
        _CAPPED.append((gamma, seed))
    return GR.canon(np.asarray(p.membership))


def summarise(res, parts, two_m):
    adm = res["admissible"]
    sel = res["selected"]
    stable = [x for x in adm if x["stable"]]
    g_hats = [x["gamma_hat"] for x in adm if x["gamma_hat"] is not None]
    pos_q = [x for x in adm if x["A"] - x["a"] * x["P"] > 0]
    return {
        "n_unique": res["n_unique"], "n_admissible": res["n_admissible"], "n_stable": res["n_stable"],
        "n_stable_qualifying": res["n_stable_qualifying"], "reason": res["no_selection_reason"],
        "max_gamma_hat": max(g_hats) if g_hats else None,
        "n_above_range": sum(x["reason"] == "estimate_above_range" for x in adm),
        "n_below_range": sum(x["reason"] == "estimate_below_range" for x in adm),
        "stable_domains": [[x["a"], x["b"], x["gamma_hat"], x["n_multi"]] for x in stable],
        "max_omega_in": max((x["A"] / x["P"] for x in adm if x["P"] > 0), default=None),
        "last_positive_b": max((x["b"] for x in pos_q), default=None),
        "selected": None if sel is None else {
            "a": sel["a"], "b": sel["b"], "mid": sel["mid"], "n_multi": sel["n_multi"],
            "gamma_hat": sel["gamma_hat"], "clipped_low": sel["clipped_low"], "clipped_high": sel["clipped_high"],
            "key": parts[sel["part"]].tobytes().hex()},
    }


def compute(job):
    import igraph as ig

    from steamstudy.network.graph import build_network

    dataset, g, s, b = job
    games, context, base = GR._W["data"][dataset]
    t0 = time.perf_counter()
    net = build_network(games, base.with_(min_games_per_tag=g, min_shared_games=s), context)
    nodes = net.nodes
    n = len(nodes)
    idx = {t: i for i, t in enumerate(nodes)}
    u = np.array([idx[e.u] for e in net.edges], dtype=np.int64)
    v = np.array([idx[e.v] for e in net.edges], dtype=np.int64)
    w = np.array([e.lift for e in net.edges])
    deg = np.bincount(u, minlength=n) + np.bincount(v, minlength=n)
    ig_graph = ig.Graph(n=n, edges=list(zip(u.tolist(), v.tolist())))
    weights = w.tolist()

    lo_i = min(5, math.floor(b["lift_lam2_lower"] / STEP))  # 5·0.05 = 0.25
    hi_i = math.ceil(b["lift_gamma_pos"] / STEP)
    gammas = [round(STEP * i, 2) for i in range(max(lo_i, 1), hi_i + 1)]
    grid56 = set(GR.GRID_56)

    index, parts, runs = {}, [], []  # runs: (γ, seed, part index)
    _CAPPED.clear()
    for gamma in gammas:
        for seed in GR._W["scan"]:
            m = leiden_capped(ig_graph, weights, gamma, seed)
            key = m.tobytes()
            if key not in index:
                index[key] = len(parts)
                parts.append(m)
            runs.append((gamma, seed, index[key]))

    def select_on(run_subset, lo, hi):
        sub_idx, first, hits, local = {}, [], [], []
        for gamma, seed, p in run_subset:
            if p not in sub_idx:
                sub_idx[p] = len(local)
                local.append(parts[p])
                first.append((gamma, seed))
                hits.append(0)
            hits[sub_idx[p]] += 1
        GR.LO, GR.HI = lo, hi
        res = GR.select(local, first, hits, u, v, w, deg)
        return summarise(res, local, res["two_m"])

    fixed = select_on([r for r in runs if r[0] in grid56], 0.25, 3.00)
    ext = select_on(runs, gammas[0], b["lift_gamma_pos"])
    # the highest scan γ at which some run is not the all-One-Tag-Cluster partition (sanity: ≤ gamma_max)
    nontriv = [gm for gm, _, p in runs if len(np.unique(parts[p][deg > 0])) < int((deg > 0).sum())]
    same = (fixed["selected"] is not None and ext["selected"] is not None
            and fixed["selected"]["key"] == ext["selected"]["key"])
    return {"dataset": dataset, "g": g, "s": s, "scan_lo": gammas[0], "scan_hi": gammas[-1],
            "n_gammas": len(gammas), "n_runs": len(runs), "gamma_pos": b["lift_gamma_pos"],
            "fixed": fixed, "extended": ext, "same_selected": same, "capped_runs": list(_CAPPED),
            "max_nontrivial_scan_gamma": max(nontriv) if nontriv else None,
            "seconds": time.perf_counter() - t0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--bounds", default=str(HERE / "bounds.json"))
    ap.add_argument("--out", default=str(HERE / "scan_extended.json"))
    args = ap.parse_args()
    bounds = {(r["dataset"], r["g"], r["s"]): r for r in json.loads(Path(args.bounds).read_text())["records"]}
    ds = tuple(GR.DATASETS)
    GR.init_worker(ds)
    jobs = [(d, g, s, bounds[(d, g, s)]) for d in ds for g, s in GR.pairs()]
    jobs.sort(key=lambda j: -j[3]["n_edges"] * j[3]["lift_gamma_pos"])  # heaviest first
    t0 = time.perf_counter()
    if args.workers > 1:
        import multiprocess as mp

        with mp.Pool(args.workers, initializer=GR.init_worker, initargs=(ds,)) as pool:
            recs = pool.map(compute, jobs, chunksize=1)
    else:
        recs = [compute(j) for j in jobs]
    Path(args.out).write_text(json.dumps(recs), encoding="utf-8")
    print(f"{len(recs)} graphs in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
