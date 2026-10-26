"""Throwaway: the decided Automatic Parameter Selection procedure over the full Parameter Grid.

Implements tickets 03 (Resolution-selection rules) and 04 (Per-pair metric definitions) as decided, for
the ticket "Exploratory grid run on the current Build". Not production code; nothing imports it.

    .venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/05-grid-run/grid_run.py \
        --workers 12 --out runs/parallel

Writes one JSON per dataset: every pair's record, the neighbour records, and wall-clock times.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from pathlib import Path

import numpy as np

BUILD = Path("builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f")
DATASETS = ("overall", "puzzle", "rpg", "simulation", "strategy")
G_RANGE = range(3, 21)
S_RANGE = range(2, 13)
LO, HI = 0.25, 3.00
GRID_56 = [round(0.25 + 0.05 * i, 2) for i in range(56)]
GRID_80 = [float(x) for x in np.linspace(0.25, 3.0, 80)]  # Research 01's input set, for comparison only
N_SCAN_SEEDS = 10
SCAN_STREAM = 3  # assumed: the next free stream after NULL_STREAM=1, NOISE_STREAM=2
MIN_MULTI = 3
RTOL = 1e-12


def pairs() -> list[tuple[int, int]]:
    return [(g, s) for g in G_RANGE for s in S_RANGE if s <= g]


# ----------------------------------------------------------------------------- worker state

_W: dict = {}


def init_worker(datasets: tuple[str, ...]) -> None:
    from steamstudy.app.loader import load_build
    from steamstudy.network.stability import derive_seeds, noise_seeds, replicate_seeds

    ctx = load_build(BUILD)
    _W["data"] = {}
    for d in datasets:
        base = ctx.default_settings(d).with_(clustering_weight="lift", algorithm="leiden", min_months=0)
        _W["data"][d] = (ctx.games(d), ctx.context(d), base)
    main = ctx.network.seed
    r = replicate_seeds(main, 20)
    noise = noise_seeds(main, 10, 20)
    _W["noise"] = noise
    _W["scan"] = derive_seeds(main, SCAN_STREAM, N_SCAN_SEEDS, exclude=set(r) | set(noise))
    _W["main_seed"] = main


# ----------------------------------------------------------------------------- the procedure


def canon(labels: np.ndarray) -> np.ndarray:
    _, first, inv = np.unique(labels, return_index=True, return_inverse=True)
    rank = np.empty(len(first), dtype=np.int64)
    rank[np.argsort(first)] = np.arange(len(first))
    return rank[inv]


def leiden(ig_graph, weights, gamma: float, seed: int) -> np.ndarray:
    import leidenalg as la

    p = la.find_partition(ig_graph, la.RBConfigurationVertexPartition, weights=weights,
                          resolution_parameter=gamma, n_iterations=-1, seed=seed)
    return canon(np.asarray(p.membership))


def champ_1d(A, P, lo, hi, tol):
    q = A - lo * P
    cand = np.flatnonzero(q >= q.max() - tol)
    cur = cand[np.argmin(P[cand])]
    start, out = lo, []
    while True:
        dP = P[cur] - P
        ok = dP > tol
        x = np.full(len(A), np.inf)
        x[ok] = (A[cur] - A[ok]) / dP[ok]
        x = np.maximum(x, start)
        nxt = x.min()
        if nxt >= hi:
            out.append((int(cur), start, hi))
            return out
        cand = np.flatnonzero(x <= nxt + tol)
        new = cand[np.argmin(P[cand])]
        if nxt > start + tol:
            out.append((int(cur), start, float(nxt)))
        cur, start = new, float(nxt)


def workbench_resolution(a: float, b: float, mid: float) -> float | None:
    r = round(mid, 2)
    if a <= r <= b:
        return r
    best = None
    for c in (math.floor(mid * 100) / 100, math.ceil(mid * 100) / 100, math.ceil(a * 100) / 100,
              math.floor(b * 100) / 100):
        c = round(c, 2)
        if a <= c <= b and (best is None or abs(c - mid) < abs(best - mid)):
            best = c
    return best


def select(parts: list[np.ndarray], first: list[tuple[float, int]], hits: list[int], u, v, w, deg) -> dict:
    """Ticket 03 on a deduplicated input set: CHAMP, γ̂ fixed-point test, the Selected Partition."""
    n_parts = len(parts)
    M = np.vstack(parts)
    k = np.bincount(u, w, len(deg)) + np.bincount(v, w, len(deg))
    two_m = float(k.sum())
    same = M[:, u] == M[:, v]
    A = 2.0 * (same * w).sum(axis=1)
    P = np.empty(n_parts)
    for i in range(n_parts):
        P[i] = (np.bincount(M[i], k) ** 2).sum() / two_m
    tol = RTOL * max(1.0, float(np.abs(A).max()), float(np.abs(P).max()) * HI)

    order = sorted(range(n_parts), key=lambda i: tuple(parts[i]))
    kept: list[int] = []
    for i in order:  # twins: identical (Â, P̂); the canonical membership sorting first stays
        if kept and np.any((np.abs(A[kept] - A[i]) <= tol) & (np.abs(P[kept] - P[i]) <= tol)):
            continue
        kept.append(i)
    kept_arr = np.array(sorted(kept))
    domains = champ_1d(A[kept_arr], P[kept_arr], LO, HI, tol)
    connected = deg > 0

    adm = []
    for j, a, b in domains:
        i = int(kept_arr[j])
        m = M[i]
        sizes = np.bincount(m)
        n_multi = int((sizes >= 2).sum())
        in_one = sizes[m] == 1
        one = np.flatnonzero(sizes == 1)
        one_isolated = int((in_one & ~connected).sum())
        groups_with_strength = len(np.unique(m[connected]))
        cross = bool((~same[i]).any())
        g_hat, reason = None, None
        if groups_with_strength < 2:
            reason = "one_group"
        elif not cross:
            reason = "no_cross_weight"
        elif A[i] <= P[i]:
            reason = "not_assortative"
        else:
            w_in = A[i] / P[i]
            w_out = (two_m - A[i]) / (two_m - P[i])
            g_hat = float((w_in - w_out) / (math.log(w_in) - math.log(w_out)))
            if g_hat > HI:
                reason = "estimate_above_range"
            elif g_hat < LO:
                reason = "estimate_below_range"
        stable = g_hat is not None and reason is None and a <= g_hat <= b
        adm.append({
            "part": i, "a": a, "b": b, "width": b - a, "mid": (a + b) / 2,
            "clipped_low": a <= LO, "clipped_high": b >= HI, "A": float(A[i]), "P": float(P[i]),
            "gamma_hat": g_hat, "reason": reason, "stable": stable, "n_multi": n_multi,
            "n_one": int(len(one)), "n_one_isolated": one_isolated, "first": first[i], "hits": hits[i],
        })
    for x in adm:
        g = x["gamma_hat"]
        if g is None:
            x["target"] = "none"
        elif g < LO:
            x["target"] = "below_range"
        elif g > HI:
            x["target"] = "above_range"
        else:
            x["target"] = next((y["part"] for y in adm if y["a"] <= g <= y["b"]), "none")

    stable = [x for x in adm if x["stable"]]
    qual = [x for x in stable if x["n_multi"] >= MIN_MULTI]
    sel, reason = None, None
    if not stable:
        reason = "no_stable_partition"
    elif not qual:
        reason = "too_few_multi_tag_clusters"
    else:
        widest = max(x["width"] for x in qual)
        ties = [x for x in qual if x["width"] >= widest - tol]
        sel = min(ties, key=lambda x: (x["mid"], tuple(parts[x["part"]])))
    return {"two_m": two_m, "n_unique": n_parts, "n_twins": n_parts - len(kept), "admissible": adm,
            "n_admissible": len(adm), "n_stable": len(stable), "n_stable_qualifying": len(qual),
            "selected": sel, "no_selection_reason": reason}


def scan(ig_graph, weights, gammas: list[float], seeds: list[int]):
    index: dict[bytes, int] = {}
    parts, first, hits = [], [], []
    for gamma in gammas:
        for seed in seeds:
            m = leiden(ig_graph, weights, gamma, seed)
            key = m.tobytes()
            if key in index:
                hits[index[key]] += 1
            else:
                index[key] = len(parts)
                parts.append(m)
                first.append((gamma, seed))
                hits.append(1)
    return parts, first, hits


def compute_pair(job: tuple[str, int, int, bool]) -> dict:
    import igraph as ig
    import networkx as nx
    from sklearn.metrics import adjusted_rand_score

    from steamstudy.network import metrics as Mx
    from steamstudy.network.cluster import label_clusters, membership
    from steamstudy.network.graph import build_network, to_graph

    dataset, g, s, compare80 = job
    games, context, base = _W["data"][dataset]
    t0 = time.perf_counter()
    settings = base.with_(min_games_per_tag=g, min_shared_games=s)
    net = build_network(games, settings, context)
    nodes = net.nodes
    idx = {t: i for i, t in enumerate(nodes)}
    u = np.array([idx[e.u] for e in net.edges], dtype=np.int64)
    v = np.array([idx[e.v] for e in net.edges], dtype=np.int64)
    w = np.array([e.lift for e in net.edges])
    deg = np.bincount(u, minlength=len(nodes)) + np.bincount(v, minlength=len(nodes))
    graph_hash = hashlib.sha256(json.dumps([nodes, [(e.u, e.v, e.shared) for e in net.edges]]).encode()).hexdigest()

    hidden = set(settings.hidden_tag_ids) | set(settings.removed_tag_ids)
    visible = [t for t in net.tag_names if t not in hidden]
    denom = sum(net.n(t) for t in visible)
    edged = {nodes[i] for i in np.flatnonzero(deg > 0)}
    retention = sum(net.n(t) for t in edged) / denom if denom else None
    games_with_edge = sum(any(t in edged for t in gm.tag_ids) for gm in net.games) / net.n_games

    graph = to_graph(nodes, net.edges, "lift")
    comps = [c for c in nx.connected_components(graph) if len(c) >= 2]
    n_iso = int((deg == 0).sum())
    lcc = max((len(c) for c in comps), default=0)
    rec = {
        "dataset": dataset, "g": g, "s": s, "graph_hash": graph_hash, "nodes": nodes,
        "n_tags": len(nodes), "n_edges": len(net.edges), "lift_below_1_share": float((w < 1).mean()) if len(w) else None,
        "n_isolated": n_iso, "isolated_share": n_iso / len(nodes) if nodes else None,
        "n_components_2plus": len(comps), "lcc_tags": lcc,
        "lcc_share_non_isolated": lcc / (len(nodes) - n_iso) if len(nodes) > n_iso else None,
        "retention": retention, "games_with_edged_tag_share": games_with_edge,
        "edged": sorted(edged),
    }
    if len(net.edges) == 0:
        rec.update({"no_selection_reason": "no_edges", "selected": None, "seconds": time.perf_counter() - t0})
        return rec

    ig_graph = ig.Graph(n=len(nodes), edges=list(zip(u.tolist(), v.tolist())))
    weights = w.tolist()
    t1 = time.perf_counter()
    parts, first, hits = scan(ig_graph, weights, GRID_56, _W["scan"])
    rec["scan_seconds"] = time.perf_counter() - t1
    res = select(parts, first, hits, u, v, w, deg)
    sel = res["selected"]
    rec.update({k: res[k] for k in ("two_m", "n_unique", "n_twins", "n_admissible", "n_stable",
                                    "n_stable_qualifying", "no_selection_reason")})
    rec["admissible"] = [{k: x[k] for k in x if k != "part"} | {"is_selected": x is sel} for x in res["admissible"]]
    rec["selected"] = None
    if sel is not None:
        m = parts[sel["part"]]
        wb = workbench_resolution(sel["a"], sel["b"], sel["mid"])
        gamma = sel["mid"]
        noise_aris, exact = [], 0
        for seed in _W["noise"]:
            nm = leiden(ig_graph, weights, gamma, seed)
            noise_aris.append(float(adjusted_rand_score(m, nm)))
            exact += bool(np.array_equal(nm, m))
        clusters = label_clusters([frozenset(nodes[i] for i in np.flatnonzero(m == c)) for c in range(m.max() + 1)])
        q = Mx.modularity(graph, clusters, gamma)
        dist = Mx.jaccard_distances(nodes, net.tag_games)
        sil = Mx.silhouette(nodes, clusters, net.tag_games, dist)
        rec["selected"] = {
            "membership": m.tolist(), "a": sel["a"], "b": sel["b"], "width": sel["width"],
            "selected_resolution": gamma, "workbench_resolution": wb, "not_representable": wb is None,
            "clipped_low": sel["clipped_low"], "clipped_high": sel["clipped_high"], "gamma_hat": sel["gamma_hat"],
            "n_multi": sel["n_multi"], "n_one": sel["n_one"], "n_one_isolated": sel["n_one_isolated"],
            "n_one_connected": sel["n_one"] - sel["n_one_isolated"], "first": sel["first"], "hits": sel["hits"],
            "seed_noise_floor": min(noise_aris), "seed_noise_mean": statistics.fmean(noise_aris),
            "seed_noise_exact": exact, "Q": q, "Q_champ": (sel["A"] - gamma * sel["P"]) / res["two_m"],
            "coverage": Mx.coverage(graph, membership(clusters)), "silhouette": sil.mean,
            "silhouette_status": sil.status,
        }
    if compare80:
        parts80, first80, hits80 = scan(ig_graph, weights, GRID_80, _W["scan"])
        r80 = select(parts80, first80, hits80, u, v, w, deg)
        s80 = r80["selected"]
        c = {"n_unique": r80["n_unique"], "n_admissible": r80["n_admissible"], "n_stable": r80["n_stable"],
             "n_stable_qualifying": r80["n_stable_qualifying"], "no_selection_reason": r80["no_selection_reason"]}
        if s80 is not None:
            m80 = parts80[s80["part"]]
            c.update({"width": s80["width"], "mid": s80["mid"], "n_multi": s80["n_multi"],
                      "identical_to_56": sel is not None and bool(np.array_equal(m80, parts[sel["part"]])),
                      "ari_vs_56": float(adjusted_rand_score(m80, parts[sel["part"]])) if sel is not None else None})
        # how many of the 56-grid stable partitions are found and stable on the 80-grid
        stable56 = {parts[x["part"]].tobytes() for x in res["admissible"] if x["stable"]}
        stable80 = {parts80[x["part"]].tobytes() for x in r80["admissible"] if x["stable"]}
        c["stable_shared"] = len(stable56 & stable80)
        rec["compare80"] = c
    rec["seconds"] = time.perf_counter() - t0
    return rec


# ----------------------------------------------------------------------------- Neighbour Agreement


def neighbour_agreement(records: dict[tuple[int, int], dict]) -> list[dict]:
    from sklearn.metrics import adjusted_rand_score

    links = []
    for (g, s) in records:
        for (g2, s2) in ((g + 1, s), (g, s + 1)):
            if (g2, s2) not in records:
                continue
            a, b = records[(g, s)], records[(g2, s2)]
            shared = sorted(set(a["nodes"]) & set(b["nodes"]))
            union = set(a["nodes"]) | set(b["nodes"])
            compared = [t for t in shared if t in set(a["edged"]) or t in set(b["edged"])]
            link = {"p": [g, s], "q": [g2, s2], "n_shared": len(shared),
                    "jaccard": len(shared) / len(union) if union else None, "n_compared": len(compared),
                    "identical_graph": a["graph_hash"] == b["graph_hash"], "ari": None}
            if a["selected"] is None or b["selected"] is None:
                link["status"] = "neighbour_has_no_selected_partition"
            elif len(compared) < 2:
                link["status"] = "too_few_compared_tags"
            else:
                ia, ib = {t: i for i, t in enumerate(a["nodes"])}, {t: i for i, t in enumerate(b["nodes"])}
                ma, mb = a["selected"]["membership"], b["selected"]["membership"]
                link["ari"] = float(adjusted_rand_score([ma[ia[t]] for t in compared], [mb[ib[t]] for t in compared]))
                link["status"] = "ok"
            links.append(link)
    for (g, s), r in records.items():
        mine = [x for x in links if tuple(x["p"]) == (g, s) or tuple(x["q"]) == (g, s)]
        ok = [x for x in mine if x["status"] == "ok"]
        na = {"n_in_grid": len(mine), "n_comparable": len(ok),
              "n_missing": sum(x["status"] == "neighbour_has_no_selected_partition" for x in mine),
              "n_too_few_tags": sum(x["status"] == "too_few_compared_tags" for x in mine),
              "n_identical_comparable": sum(x["identical_graph"] for x in ok),
              "n_identical_in_grid": sum(x["identical_graph"] for x in mine)}
        if r["selected"] is None:
            na.update({"mean": None, "min": None, "status": "no_selected_partition"})
        elif not ok:
            na.update({"mean": None, "min": None, "status": "no_comparable_neighbours"})
        else:
            na.update({"mean": statistics.fmean(x["ari"] for x in ok), "min": min(x["ari"] for x in ok), "status": "ok"})
        r["neighbour_agreement"] = na
    return links


# ----------------------------------------------------------------------------- driver


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--datasets", nargs="*", default=list(DATASETS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--compare80", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ds = tuple(args.datasets)

    pool = None
    t_init = time.perf_counter()
    init_worker(ds)
    if args.workers > 1:
        import multiprocess as mp

        pool = mp.Pool(args.workers, initializer=init_worker, initargs=(ds,))
        pool.map(lambda _: None, range(args.workers))  # warm up: workers have loaded the Build
    init_seconds = time.perf_counter() - t_init

    for d in ds:
        jobs = [(d, g, s, args.compare80) for g, s in pairs()]
        t0 = time.perf_counter()
        if pool is not None:
            recs = pool.map(compute_pair, jobs, chunksize=1)
        else:
            recs = [compute_pair(j) for j in jobs]
        t_pairs = time.perf_counter() - t0
        records = {(r["g"], r["s"]): r for r in recs}
        t1 = time.perf_counter()
        links = neighbour_agreement(records)
        t_na = time.perf_counter() - t1
        doc = {"dataset": d, "workers": args.workers, "compare80": args.compare80, "init_seconds": init_seconds,
               "pairs_seconds": t_pairs, "neighbour_seconds": t_na, "scan_seeds": _W.get("scan") or None,
               "records": recs, "links": links}
        (out / f"{d}.json").write_text(json.dumps(doc), encoding="utf-8")
        print(f"{d}: {len(recs)} pairs in {t_pairs:.1f} s (+{t_na:.2f} s neighbours), workers={args.workers}",
              flush=True)
    if pool is not None:
        pool.close()
        pool.join()


if __name__ == "__main__":
    main()
