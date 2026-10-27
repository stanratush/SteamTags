"""Throwaway: graph-specific γ bounds for every Threshold Pair graph of the Build (ticket 15).

For each of the 765 pair graphs (5 datasets × 153 pairs; Lift weight, Genre Tags and the defining tag hidden,
Minimum Months 0), and for Shared games weights on the same graphs, computes:

- gamma_max: max over edges of 2m·w_ij/(k_i k_j) (Jeub et al. 2018 Eq. 3 and `gammaRange.m`), the smallest γ at
  which the all-One-Tag-Cluster partition is optimal (proof in the research note, §1).
- gamma_min bracket for "one Cluster per connected component": the exact value is the minimum over components c
  and bipartitions (S, c∖S) of 2m·cut(S)/(vol S · vol(c∖S)) (research note, §2).
    lam2_lower   min_c (2m/vol_c)·λ2(normalised Laplacian of c), a lower bound (Rayleigh quotient)
    sweep_upper  the best Fiedler sweep cut, an upper bound
    jeub_upper   Jeub et al.'s iteration (`gammaRange.m`) with Leiden and the 10 scan seeds, an upper bound
    exact        brute force over all bipartitions, only where the component has ≤ EXACT_MAX_NODES tags
- gamma_max_K: Gibson & Mucha's γ_max(K) bound on γ̂ for K equal-sized groups, at K = number of non-isolated tags.
- event sampling (Jeub et al. 2018 Eqs. 4–5): the 56 γ values equally spaced in β from β(jeub_upper) to 1.

    uv run python .scratch/auto-parameter-selection/prototypes/15-gamma-bounds/bounds.py --workers 12

Run from the repo root. Writes bounds.csv next to this file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "05-grid-run"))
import grid_run as GR  # noqa: E402  (BUILD, DATASETS, pairs(), init_worker, leiden, canon)

EXACT_MAX_NODES = 24
N_EVENT = 56
NUM_TOL = 1e-9  # as gammaRange.m


# ----------------------------------------------------------------------------- pure numpy bounds


def strengths(n, u, v, w):
    return np.bincount(u, w, n) + np.bincount(v, w, n)


def components(n, u, v, k):
    """Connected components of the non-isolated tags, as lists of node indices (isolated tags left out)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    adj = coo_matrix((np.ones(len(u)), (u, v)), shape=(n, n))
    _, lab = connected_components(adj, directed=False)
    out = []
    for c in np.unique(lab):
        idx = np.flatnonzero(lab == c)
        if len(idx) >= 2 or k[idx].sum() > 0:
            out.append(idx)
    return out


def gamma_max(u, v, w, k):
    two_m = k.sum()
    r = two_m * w / (k[u] * k[v])
    i = int(np.argmax(r))
    return float(r[i]), i


def gamma_pos(u, v, w, k):
    """Root of F(γ) = Σ_edges 2·max(w − γ k_i k_j/2m, 0) − γ Σ_i k_i²/2m, an upper bound on every partition's
    Q(γ) > 0 range, hence on every ω_in and every γ̂ (research note, §1.4). F is decreasing and piecewise linear."""
    two_m = k.sum()
    pij = k[u] * k[v] / two_m
    diag = (k ** 2).sum() / two_m
    lo, hi = 0.0, float((w / pij).max())
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        F = 2.0 * np.maximum(w - mid * pij, 0.0).sum() - mid * diag
        if F > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def comp_arrays(idx, u, v, w):
    pos = {int(t): j for j, t in enumerate(idx)}
    keep = np.isin(u, idx) & np.isin(v, idx)
    cu = np.array([pos[int(t)] for t in u[keep]], dtype=np.int64)
    cv = np.array([pos[int(t)] for t in v[keep]], dtype=np.int64)
    return cu, cv, w[keep]


def lam2_and_sweep(nc, cu, cv, cw, two_m):
    """Lower bound (2m/vol)·λ2 and the best Fiedler sweep cut 2m·cut/(volS·volT), for one component."""
    W = np.zeros((nc, nc))
    W[cu, cv] = cw
    W[cv, cu] = cw
    d = W.sum(1)
    vol = d.sum()
    dm = 1.0 / np.sqrt(d)
    L = np.eye(nc) - dm[:, None] * W * dm[None, :]
    vals, vecs = np.linalg.eigh(L)
    lam2 = float(vals[1])
    f = dm * vecs[:, 1]
    order = np.argsort(f)
    best = math.inf
    inS = np.zeros(nc, bool)
    volS = 0.0
    for j in order[:-1]:
        inS[j] = True
        volS += d[j]
        cut = cw[inS[cu] != inS[cv]].sum()
        best = min(best, two_m * cut / (volS * (vol - volS)))
    return (two_m / vol) * lam2, best


def exact_min_cut_ratio(nc, cu, cv, cw, two_m, chunk_bits=20):
    """min over bipartitions of one component of 2m·cut(S)/(vol S·vol T), by enumeration (node nc−1 never in S)."""
    d = np.bincount(cu, cw, nc) + np.bincount(cv, cw, nc)
    vol = d.sum()
    n_free = nc - 1
    total = 1 << n_free
    best = math.inf
    step = 1 << min(chunk_bits, n_free)
    bits_idx = np.arange(n_free, dtype=np.int64)
    for start in range(1, total, step):
        s = np.arange(start, min(start + step, total), dtype=np.int64)
        B = ((s[:, None] >> bits_idx[None, :]) & 1).astype(np.int8)  # (chunk, n_free)
        B = np.concatenate([B, np.zeros((len(s), 1), np.int8)], axis=1)
        volS = B @ d
        cut = ((B[:, cu] ^ B[:, cv]) * cw).sum(1)
        r = two_m * cut / (volS * (vol - volS))
        best = min(best, float(r.min()))
    return best


def gamma_max_K(K: int) -> float:
    """Gibson & Mucha SI §J: max of γ̂(ω_in, ω_out) over ω_in + (K−1)ω_out = K, ω_in > ω_out (equal-sized groups)."""
    from scipy.optimize import minimize_scalar

    if K < 2:
        return math.nan

    def g(wo):
        wi = K - (K - 1) * wo
        return (wi - wo) / (math.log(wi) - math.log(wo))

    res = minimize_scalar(lambda wo: -g(wo), bounds=(1e-12, 1 - 1e-12), method="bounded",
                          options={"xatol": 1e-12})
    return float(-res.fun)


def event_samples(n, u, v, w, k, gmin, gmax, n_samples=N_EVENT):
    """Jeub et al. Eqs. (4)-(5): γ values equally spaced in β from β(gmin) to 1 (β by bisection on γ)."""
    nz = np.flatnonzero(k > 0)
    two_m = k.sum()
    iu, ju = np.triu_indices(len(nz), 1)
    Pij = k[nz][iu] * k[nz][ju] / two_m
    pos = {int(t): j for j, t in enumerate(nz)}
    Aful = np.zeros((len(nz), len(nz)))
    Aful[[pos[int(t)] for t in u], [pos[int(t)] for t in v]] = w
    Aful = Aful + Aful.T
    Aij = Aful[iu, ju]

    def beta(g):
        B = Aij - g * Pij
        den = np.abs(B).sum()
        return float(np.abs(B[B < 0]).sum() / den)

    def inv(b):
        lo, hi = 0.0, gmax
        if b >= 1.0:
            return gmax
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if beta(mid) < b:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    b0 = beta(gmin)
    return [inv(b) for b in np.linspace(b0, 1.0, n_samples)], b0


# ----------------------------------------------------------------------------- Leiden-based upper bound on γ_min


def coeffs(memb, u, v, w, k):
    two_m = k.sum()
    same = memb[u] == memb[v]
    a = 2.0 * w[same].sum()
    p = (np.bincount(memb, k) ** 2).sum() / two_m
    return a, p


def jeub_gamma_min(ig_graph, weights, n, u, v, w, k, comp_memb, gmax, seeds):
    """`gammaRange.m`: start at γ = 1 (InitialGuess), sample at γ_min − NUM_TOL until only the trivial partition."""
    a0, p0 = coeffs(comp_memb, u, v, w, k)
    n_trivial_groups = len(np.unique(comp_memb[k > 0]))

    def bound(gamma):
        best, n_runs = math.inf, 0
        for seed in seeds:
            m = GR.leiden(ig_graph, weights, gamma, seed)
            n_runs += 1
            if len(np.unique(m[k > 0])) > n_trivial_groups:
                a, p = coeffs(m, u, v, w, k)
                best = min(best, (a0 - a) / (p0 - p))
        return best, n_runs

    guess, runs = 1.0, 0
    gmin = math.inf
    while gmin == math.inf:
        gmin, r = bound(guess - NUM_TOL)
        runs += r
        guess = min(2 * guess, gmax - NUM_TOL)
    new = gmin
    gmin = math.inf
    iters = 0
    while new < gmin:
        gmin = new
        new, r = bound(gmin - NUM_TOL)
        runs += r
        iters += 1
    return float(gmin), iters, runs


# ----------------------------------------------------------------------------- per pair


def compute(job):
    import igraph as ig

    from steamstudy.network.graph import build_network

    dataset, g, s = job
    games, context, base = GR._W["data"][dataset]
    t0 = time.perf_counter()
    net = build_network(games, base.with_(min_games_per_tag=g, min_shared_games=s), context)
    nodes = net.nodes
    n = len(nodes)
    idx = {t: i for i, t in enumerate(nodes)}
    u = np.array([idx[e.u] for e in net.edges], dtype=np.int64)
    v = np.array([idx[e.v] for e in net.edges], dtype=np.int64)
    graph_hash = hashlib.sha256(json.dumps([nodes, [(e.u, e.v, e.shared) for e in net.edges]]).encode()).hexdigest()
    rec = {"dataset": dataset, "g": g, "s": s, "graph_hash": graph_hash[:12], "n_tags": n, "n_edges": len(u)}
    ig_graph = ig.Graph(n=n, edges=list(zip(u.tolist(), v.tolist())))
    for wname, w in (("lift", np.array([e.lift for e in net.edges])),
                     ("shared", np.array([float(e.shared) for e in net.edges]))):
        k = strengths(n, u, v, w)
        two_m = float(k.sum())
        comps = components(n, u, v, k)
        n_iso = int((k == 0).sum())
        gmax, ei = gamma_max(u, v, w, k)
        lam_lo, sweep_hi, exact = math.inf, math.inf, math.inf
        exact_ok = True
        comp_memb = np.full(n, -1, dtype=np.int64)
        for ci, cidx in enumerate(comps):
            comp_memb[cidx] = ci
            cu, cv, cw = comp_arrays(cidx, u, v, w)
            lo, hi = lam2_and_sweep(len(cidx), cu, cv, cw, two_m)
            lam_lo, sweep_hi = min(lam_lo, lo), min(sweep_hi, hi)
            if len(cidx) <= EXACT_MAX_NODES:
                exact = min(exact, exact_min_cut_ratio(len(cidx), cu, cv, cw, two_m))
            else:
                exact_ok = False
        nxt = len(comps)
        for i in np.flatnonzero(comp_memb < 0):  # isolated tags: their own groups
            comp_memb[i] = nxt
            nxt += 1
        jeub, iters, runs = jeub_gamma_min(ig_graph, w.tolist(), n, u, v, w, k, comp_memb, gmax, GR._W["scan"])
        ev, b0 = event_samples(n, u, v, w, k, jeub, gmax)
        ev = np.array(ev)
        K = n - n_iso
        p = f"{wname}_"
        rec.update({
            p + "two_m": two_m, p + "n_isolated": n_iso, p + "n_components": len(comps),
            p + "gamma_max": gmax, p + "gamma_pos": gamma_pos(u, v, w, k),
            p + "gamma_max_edge": [nodes[int(u[ei])], nodes[int(v[ei])]],
            p + "gamma_max_edge_w": float(w[ei]), p + "gamma_max_edge_k": [float(k[u[ei]]), float(k[v[ei]])],
            p + "gamma_max_edge_shared": int(net.edges[ei].shared),
            p + "lam2_lower": lam_lo, p + "sweep_upper": sweep_hi, p + "jeub_upper": jeub,
            p + "jeub_iters": iters, p + "jeub_runs": runs,
            p + "exact": exact if exact_ok else None,
            p + "K_nonisolated": K, p + "gamma_max_K": gamma_max_K(K),
            p + "event_beta_min": b0, p + "event_n_above_3": int((ev > 3.0).sum()),
            p + "event_n_below_025": int((ev < 0.25).sum()),
            p + "event_gamma_q": [float(x) for x in np.quantile(ev, [0, 0.25, 0.5, 0.75, 1])],
            p + "event_n_in_025_3": int(((ev >= 0.25) & (ev <= 3.0)).sum()),
        })
    rec["seconds"] = time.perf_counter() - t0
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--datasets", nargs="*", default=list(GR.DATASETS))
    ap.add_argument("--out", default=str(HERE / "bounds.json"))
    args = ap.parse_args()
    ds = tuple(args.datasets)
    GR.init_worker(ds)
    jobs = [(d, g, s) for d in ds for g, s in GR.pairs()]
    t0 = time.perf_counter()
    if args.workers > 1:
        import multiprocess as mp

        with mp.Pool(args.workers, initializer=GR.init_worker, initargs=(ds,)) as pool:
            recs = pool.map(compute, jobs, chunksize=1)
    else:
        recs = [compute(j) for j in jobs]
    Path(args.out).write_text(json.dumps({"scan_seeds": GR._W["scan"], "records": recs}), encoding="utf-8")
    print(f"{len(recs)} graphs in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
