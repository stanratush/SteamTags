"""Throwaway: which citable upper end for the γ scan, and does it change the Selected Partition? (research 16)

For every Lift pair graph, scans Leiden (RBConfiguration, the 10 scan seeds, the capped pass loop of research 15)
on the grid round(0.05·i, 2) from 0 up to TOP, then applies ticket 03's selection to prefixes of the same runs:

    pos      scan to γ_pos (rounded up),        CHAMP on [0, γ_pos]            reference: the rejected own inference
    q0stop   scan until every partition found so far has Q(γ) ≤ 0 at the current γ (CHAMP 2.1.0's Q ≥ 0 hull cut
             used as a stopping rule), CHAMP on [0, max ω_in found]   (= where CHAMP's own code ends the hull)
    gmK      scan to Gibson & Mucha's γ_max(K), K = number of tags with an edge, CHAMP on [0, γ_max(K)]
    jsf      scan to γ_max = max 2m·w/(k k) (Jeub et al. 2018; Bazzi et al. 2016's γ+), CHAMP on [0, γ_max]
    jsf_q0   the jsf runs, CHAMP on [0, max ω_in found]  (the jsf range with CHAMP's Q ≥ 0 cut)

TOP = γ_max when --top jsf (default), else max(γ_pos, γ_max(K)) and the jsf arms are skipped.
Also checks Gibson & Mucha SI §J.2 (γ̂ ≤ γ_max(K) for every assortative partition with K groups of positive
strength, any sizes) on every distinct partition found, and records where GM22's SNAP practice (stop once a
partition has > 100 communities) would stop.

    uv run python .scratch/auto-parameter-selection/prototypes/16-citable-upper-bound/scan_ends.py --workers 12

Run from the repo root. Needs ../15-gamma-bounds/bounds.json. Writes scan_ends.json next to this file.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "05-grid-run"))
import grid_run as GR  # noqa: E402

STEP = 0.05
MAX_ITER = 1000


@lru_cache(maxsize=None)
def gamma_max_K(K: int) -> float:
    """GM22 SI §J: max of γ̂(ω_in, ω_out) on ω_in + (K−1)ω_out = K, ω_in > ω_out (as SNAP_boxplot.py, but exact)."""
    from scipy.optimize import minimize_scalar

    if K < 2:
        return math.nan

    def g(wo):
        wi = K - (K - 1) * wo
        return (wi - wo) / (math.log(wi) - math.log(wo))

    res = minimize_scalar(lambda wo: -g(wo), bounds=(1e-12, 1 - 1e-12), method="bounded", options={"xatol": 1e-12})
    return float(-res.fun)


def leiden_capped(ig_graph, weights, gamma: float, seed: int):
    import leidenalg as la

    p = la.RBConfigurationVertexPartition(ig_graph, weights=weights, resolution_parameter=gamma)
    opt = la.Optimiser()
    opt.set_rng_seed(seed)
    capped = True
    for _ in range(MAX_ITER):
        if opt.optimise_partition(p, n_iterations=1) <= 0:
            capped = False
            break
    return GR.canon(np.asarray(p.membership)), capped


def summarise(res, parts):
    adm = res["admissible"]
    sel = res["selected"]
    stable = [x for x in adm if x["stable"]]
    return {
        "n_unique": res["n_unique"], "n_admissible": res["n_admissible"], "n_stable": res["n_stable"],
        "n_stable_qualifying": res["n_stable_qualifying"], "reason": res["no_selection_reason"],
        "n_above_range": sum(x["reason"] == "estimate_above_range" for x in adm),
        "max_stable_gamma_hat": max((x["gamma_hat"] for x in stable), default=None),
        "max_stable_b": max((x["b"] for x in stable), default=None),
        "selected": None if sel is None else {
            "a": sel["a"], "b": sel["b"], "mid": sel["mid"], "n_multi": sel["n_multi"],
            "gamma_hat": sel["gamma_hat"], "clipped_high": sel["clipped_high"],
            "key": parts[sel["part"]].tobytes().hex()},
    }


def compute(job):
    import igraph as ig

    from steamstudy.network.graph import build_network

    dataset, g, s, b, top_mode = job
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
    k = np.bincount(u, w, n) + np.bincount(v, w, n)
    two_m = float(k.sum())
    connected = deg > 0
    n_conn = int(connected.sum())
    ig_graph = ig.Graph(n=n, edges=list(zip(u.tolist(), v.tolist())))
    weights = w.tolist()

    g_pos, g_max = b["lift_gamma_pos"], b["lift_gamma_max"]
    g_K = gamma_max_K(n_conn)
    top = g_max if top_mode == "jsf" else max(g_pos, g_K)
    n_top = math.ceil(top / STEP - 1e-9)
    gammas = [round(STEP * i, 2) for i in range(n_top + 1)]

    index, parts, Acoef, Pcoef, runs = {}, [], [], [], []  # runs: (γ, seed, part index)
    capped_at = []
    first_over_100_all = first_over_100_conn = None
    t_scan = time.perf_counter()
    for gamma in gammas:
        for seed in GR._W["scan"]:
            m, capped = leiden_capped(ig_graph, weights, gamma, seed)
            if capped:
                capped_at.append(gamma)
            key = m.tobytes()
            if key not in index:
                index[key] = len(parts)
                parts.append(m)
                same = m[u] == m[v]
                Acoef.append(2.0 * float(w[same].sum()))
                Pcoef.append(float((np.bincount(m, k) ** 2).sum() / two_m))
            p = index[key]
            runs.append((gamma, seed, p))
            if first_over_100_all is None and len(np.unique(m)) > 100:
                first_over_100_all = gamma
            if first_over_100_conn is None and len(np.unique(m[connected])) > 100:
                first_over_100_conn = gamma
    t_scan = time.perf_counter() - t_scan
    A, P = np.array(Acoef), np.array(Pcoef)

    # q0stop: first γ (> 0) after whose runs every partition found so far has A − γP ≤ 0
    tolq = 1e-12 * max(1.0, two_m)
    seen = np.zeros(len(parts), dtype=bool)
    q0_stop = None
    by_gamma: dict[float, list[int]] = {}
    for gamma, _, p in runs:
        by_gamma.setdefault(gamma, []).append(p)
    for gamma in gammas:
        seen[by_gamma[gamma]] = True
        if gamma > 0 and float((A[seen] - gamma * P[seen]).max()) <= tolq:
            q0_stop = gamma
            break

    def select_on(max_gamma, lo, hi):
        sub_idx, first, hits, local = {}, [], [], []
        for gamma, seed, p in runs:
            if gamma > max_gamma + 1e-9:
                continue
            if p not in sub_idx:
                sub_idx[p] = len(local)
                local.append(parts[p])
                first.append((gamma, seed))
                hits.append(0)
            hits[sub_idx[p]] += 1
        GR.LO, GR.HI = lo, hi
        res = GR.select(local, first, hits, u, v, w, deg)
        out = summarise(res, local)
        out["scan_end"] = max_gamma
        out["champ_hi"] = hi
        out["n_gammas"] = int(sum(1 for x in gammas if x <= max_gamma + 1e-9))
        out["n_capped"] = int(sum(1 for x in capped_at if x <= max_gamma + 1e-9))
        return out

    def omega_in_max(max_gamma):
        ps = sorted({p for gamma, _, p in runs if gamma <= max_gamma + 1e-9})
        return float(max(A[ps] / P[ps]))

    arms = {}
    end_pos = round(STEP * math.ceil(g_pos / STEP - 1e-9), 2)
    arms["pos"] = select_on(end_pos, 0.0, g_pos)
    if q0_stop is not None:
        arms["q0stop"] = select_on(q0_stop, 0.0, omega_in_max(q0_stop))
    end_K = round(STEP * math.ceil(g_K / STEP - 1e-9), 2)
    arms["gmK"] = select_on(end_K, 0.0, g_K)
    if top_mode == "jsf":
        arms["jsf"] = select_on(gammas[-1], 0.0, g_max)
        arms["jsf_q0"] = select_on(gammas[-1], 0.0, omega_in_max(gammas[-1]))

    # GM22 SI §J.2 check on every distinct partition found: γ̂ ≤ γ_max(K), K = groups with positive strength
    n_checked = n_viol = 0
    worst = 0.0
    for i, m in enumerate(parts):
        K = len(np.unique(m[connected]))
        if K < 2 or A[i] <= P[i] or A[i] >= two_m:
            continue
        wi = A[i] / P[i]
        wo = (two_m - A[i]) / (two_m - P[i])
        gh = (wi - wo) / (math.log(wi) - math.log(wo))
        n_checked += 1
        ratio = gh / gamma_max_K(K)
        worst = max(worst, ratio)
        if ratio > 1 + 1e-9:
            n_viol += 1

    return {"dataset": dataset, "g": g, "s": s, "n_tags": n, "n_connected": n_conn,
            "gamma_pos": g_pos, "gamma_max": g_max, "gamma_max_K": g_K, "q0_stop": q0_stop,
            "omega_in_max_all": float(max(A / P)),
            "first_over_100_all": first_over_100_all, "first_over_100_conn": first_over_100_conn,
            "top": gammas[-1], "n_runs": len(runs), "n_unique": len(parts), "n_capped": len(capped_at),
            "gm_check": {"n": n_checked, "violations": n_viol, "max_ratio": worst},
            "arms": arms, "scan_seconds": t_scan, "seconds": time.perf_counter() - t0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--top", choices=["jsf", "gmK"], default="jsf")
    ap.add_argument("--sample", type=int, default=0, help="random sample of pairs (0 = all 765)")
    ap.add_argument("--include", nargs="*", default=[], help="with --sample: also these pairs, as dataset/g/s")
    ap.add_argument("--bounds", default=str(HERE.parent / "15-gamma-bounds" / "bounds.json"))
    ap.add_argument("--out", default=str(HERE / "scan_ends.json"))
    args = ap.parse_args()
    bounds = {(r["dataset"], r["g"], r["s"]): r for r in json.loads(Path(args.bounds).read_text())["records"]}
    ds = tuple(GR.DATASETS)
    GR.init_worker(ds)
    jobs = [(d, g, s, bounds[(d, g, s)], args.top) for d in ds for g, s in GR.pairs()]
    if args.sample:
        extra = {tuple(x.split("/")) for x in args.include}
        extra = [j for j in jobs if (j[0], str(j[1]), str(j[2])) in extra]
        jobs = random.Random(16).sample(jobs, args.sample)
        jobs += [j for j in extra if j not in jobs]
    key = "lift_gamma_max" if args.top == "jsf" else "lift_gamma_max_K"
    jobs.sort(key=lambda j: -j[3]["n_edges"] * j[3][key])  # heaviest first
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
