"""Throwaway: re-measure Automatic Parameter Selection under ticket 16's γ scan rule (research 16, gmK).

Phases (each its own 12-worker pool, so the new-rule wall time compares with ticket 05's 95 s):

    ref     ticket 05 exactly (grid_run.compute_pair: 56 γ 0.25–3.00, n_iterations=-1, CHAMP on [0.25, 3.00]).
            Ticket 05's raw records are not on disk any more, so the reference is recomputed and checked
            against ticket 12's after-q3 table.
    new     γ = round(0.05·i, 2), i = 0 … ⌈γ_max(n_e)/0.05⌉; capped Leiden loop (≤ 1,000 passes);
            CHAMP on [0, last scan γ]; everything else as grid_run.compute_pair.
    search  ticket 09's Workbench γ/seed search on both arms' Selected Partitions.

    uv run python .scratch/auto-parameter-selection/prototypes/16-remeasure/remeasure.py --phase ref
    uv run python .scratch/auto-parameter-selection/prototypes/16-remeasure/remeasure.py --phase new
    uv run python .scratch/auto-parameter-selection/prototypes/16-remeasure/remeasure.py --phase search

Run from the repo root. Writes runs/<arm>/<dataset>.json and runs/search_<arm>.json next to this file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "05-grid-run"))
sys.path.insert(0, str(HERE.parent / "16-citable-upper-bound"))
import grid_run as GR  # noqa: E402
import scan_ends as SE  # noqa: E402

RUNS = HERE / "runs"
STEP = 0.05


def scan_gammas(n_e: int) -> list[float]:
    gk = SE.gamma_max_K(n_e)
    return [round(STEP * i, 2) for i in range(math.ceil(gk / STEP - 1e-9) + 1)]


def graph_of(dataset, g, s):
    import igraph as ig

    from steamstudy.network.graph import build_network

    games, context, base = GR._W["data"][dataset]
    settings = base.with_(min_games_per_tag=g, min_shared_games=s)
    net = build_network(games, settings, context)
    nodes = net.nodes
    idx = {t: i for i, t in enumerate(nodes)}
    u = np.array([idx[e.u] for e in net.edges], dtype=np.int64)
    v = np.array([idx[e.v] for e in net.edges], dtype=np.int64)
    w = np.array([e.lift for e in net.edges])
    deg = np.bincount(u, minlength=len(nodes)) + np.bincount(v, minlength=len(nodes))
    igg = ig.Graph(n=len(nodes), edges=list(zip(u.tolist(), v.tolist())))
    return settings, net, nodes, u, v, w, deg, igg


# ----------------------------------------------------------------------------- ref


def compute_ref(job):
    GR.LO, GR.HI = 0.25, 3.00
    rec = GR.compute_pair((job[0], job[1], job[2], False))
    return rec


# ----------------------------------------------------------------------------- new


def compute_new(job):
    from sklearn.metrics import adjusted_rand_score

    import networkx as nx

    from steamstudy.network import metrics as Mx
    from steamstudy.network.cluster import label_clusters, membership
    from steamstudy.network.graph import to_graph

    dataset, g, s = job
    t0 = time.perf_counter()
    settings, net, nodes, u, v, w, deg, igg = graph_of(dataset, g, s)
    graph_hash = hashlib.sha256(json.dumps([nodes, [(e.u, e.v, e.shared) for e in net.edges]]).encode()).hexdigest()
    hidden = set(settings.hidden_tag_ids) | set(settings.removed_tag_ids)
    visible = [t for t in net.tag_names if t not in hidden]
    denom = sum(net.n(t) for t in visible)
    edged = {nodes[i] for i in np.flatnonzero(deg > 0)}
    retention = sum(net.n(t) for t in edged) / denom if denom else None
    graph = to_graph(nodes, net.edges, "lift")
    comps = [c for c in nx.connected_components(graph) if len(c) >= 2]
    n_iso = int((deg == 0).sum())
    lcc = max((len(c) for c in comps), default=0)
    n_e = int((deg > 0).sum())
    rec = {
        "dataset": dataset, "g": g, "s": s, "graph_hash": graph_hash, "nodes": nodes,
        "n_tags": len(nodes), "n_edges": len(net.edges), "n_isolated": n_iso,
        "isolated_share": n_iso / len(nodes) if nodes else None, "n_components_2plus": len(comps),
        "lcc_tags": lcc, "lcc_share_non_isolated": lcc / (len(nodes) - n_iso) if len(nodes) > n_iso else None,
        "retention": retention, "edged": sorted(edged), "n_e": n_e,
    }
    if len(net.edges) == 0:
        rec.update({"no_selection_reason": "no_edges", "selected": None, "seconds": time.perf_counter() - t0})
        return rec
    weights = w.tolist()
    g_K = SE.gamma_max_K(n_e)
    gammas = scan_gammas(n_e)
    hi = gammas[-1]
    rec.update({"gamma_max_K": g_K, "scan_end": hi, "n_gammas": len(gammas)})

    t1 = time.perf_counter()
    index, parts, first, hits, capped_at = {}, [], [], [], []
    for gamma in gammas:
        for seed in GR._W["scan"]:
            m, capped = SE.leiden_capped(igg, weights, gamma, seed)
            if capped:
                capped_at.append([gamma, seed])
            key = m.tobytes()
            if key in index:
                hits[index[key]] += 1
            else:
                index[key] = len(parts)
                parts.append(m)
                first.append((gamma, seed))
                hits.append(1)
    rec["scan_seconds"] = time.perf_counter() - t1
    rec["n_scan_runs"] = len(gammas) * len(GR._W["scan"])
    rec["scan_capped"] = capped_at

    GR.LO, GR.HI = 0.0, hi
    res = GR.select(parts, first, hits, u, v, w, deg)
    sel = res["selected"]
    adm = res["admissible"]
    rec.update({k: res[k] for k in ("two_m", "n_unique", "n_twins", "n_admissible", "n_stable",
                                    "n_stable_qualifying", "no_selection_reason")})
    rec["reasons"] = {}
    for x in adm:
        rec["reasons"][str(x["reason"])] = rec["reasons"].get(str(x["reason"]), 0) + 1
    rec["n_estimate_above_range"] = sum(x["reason"] == "estimate_above_range" for x in adm)
    rec["n_estimate_below_range"] = sum(x["reason"] == "estimate_below_range" for x in adm)
    rec["max_gamma_hat"] = max((x["gamma_hat"] for x in adm if x["gamma_hat"] is not None), default=None)
    rec["n_stable_below_025"] = sum(x["stable"] and x["gamma_hat"] < 0.25 for x in adm)
    rec["n_stable_above_3"] = sum(x["stable"] and x["gamma_hat"] > 3.0 for x in adm)
    rec["selected"] = None
    rec["noise_capped"] = 0
    if sel is not None:
        m = parts[sel["part"]]
        wb = GR.workbench_resolution(sel["a"], sel["b"], sel["mid"])
        gamma = sel["mid"]
        noise_aris, exact = [], 0
        for seed in GR._W["noise"]:
            nm, capped = SE.leiden_capped(igg, weights, gamma, seed)
            rec["noise_capped"] += capped
            noise_aris.append(float(adjusted_rand_score(m, nm)))
            exact += bool(np.array_equal(nm, m))
        clusters = label_clusters([frozenset(nodes[i] for i in np.flatnonzero(m == c)) for c in range(m.max() + 1)])
        q = Mx.modularity(graph, clusters, gamma)
        dist = Mx.jaccard_distances(nodes, net.tag_games)
        sil = Mx.silhouette(nodes, clusters, net.tag_games, dist)
        rec["selected"] = {
            "membership": m.tolist(), "a": sel["a"], "b": sel["b"], "width": sel["width"],
            "selected_resolution": gamma, "workbench_resolution": wb, "not_representable": wb is None,
            "clipped_high": sel["clipped_high"], "a_is_zero": sel["a"] <= 0.0, "gamma_hat": sel["gamma_hat"],
            "n_multi": sel["n_multi"], "n_one": sel["n_one"], "n_one_isolated": sel["n_one_isolated"],
            "first": sel["first"], "hits": sel["hits"],
            "seed_noise_floor": min(noise_aris), "seed_noise_mean": statistics.fmean(noise_aris),
            "seed_noise_exact": exact, "Q": q, "coverage": Mx.coverage(graph, membership(clusters)),
            "silhouette": sil.mean,
        }
    rec["seconds"] = time.perf_counter() - t0
    return rec


# ----------------------------------------------------------------------------- search (ticket 09)


def search(job):
    dataset, g, s, memb, a, b, mid = job
    _, _, _, _, _, w, _, igg = graph_of(dataset, g, s)
    weights = w.tolist()
    m = np.asarray(memb)
    gam = [round(x / 100, 2) for x in range(math.ceil(a * 100 - 1e-9), math.floor(b * 100 + 1e-9) + 1)]
    gam = [x for x in gam if a <= x <= b]
    gam.sort(key=lambda x: (abs(x - mid), x))
    seeds = [GR._W["main_seed"], *GR._W["scan"]]
    runs = capped_n = 0
    for gi, x in enumerate(gam):
        for si, sd in enumerate(seeds):
            p, capped = SE.leiden_capped(igg, weights, x, sd)
            runs += 1
            capped_n += capped
            if np.array_equal(p, m):
                return {"dataset": dataset, "g": g, "s": s, "found": True, "gamma": x, "gamma_rank": gi,
                        "seed_idx": si, "n_gamma": len(gam), "runs": runs, "capped": capped_n}
    return {"dataset": dataset, "g": g, "s": s, "found": False, "n_gamma": len(gam), "runs": runs,
            "capped": capped_n}


# ----------------------------------------------------------------------------- driver


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["ref", "new", "search"], required=True)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--tag", default="", help="suffix for the output directory (timing re-runs)")
    args = ap.parse_args()
    ds = tuple(GR.DATASETS)
    import multiprocess as mp

    pool = mp.Pool(args.workers, initializer=GR.init_worker, initargs=(ds,))
    pool.map(lambda _: None, range(args.workers))  # warm-up: every worker has loaded the Build
    if args.phase in ("ref", "new"):
        jobs = [(d, g, s) for d in ds for g, s in GR.pairs()]
        if args.phase == "new":  # heaviest first (scheduling only)
            b = {(r["dataset"], r["g"], r["s"]): r for r in
                 json.loads((HERE.parent / "15-gamma-bounds" / "bounds.json").read_text())["records"]}
            jobs.sort(key=lambda j: -b[j]["n_edges"] * b[j]["lift_gamma_max_K"])
        fn = compute_ref if args.phase == "ref" else compute_new
        t0 = time.perf_counter()
        recs = pool.map(fn, jobs, chunksize=1)
        wall = time.perf_counter() - t0
        out = RUNS / (args.phase + args.tag)
        out.mkdir(parents=True, exist_ok=True)
        for d in ds:
            rd = [r for r in recs if r["dataset"] == d]
            records = {(r["g"], r["s"]): r for r in rd}
            links = GR.neighbour_agreement(records)
            doc = {"dataset": d, "workers": args.workers, "wall_seconds_all_datasets": wall,
                   "records": rd, "links": links}
            (out / f"{d}.json").write_text(json.dumps(doc), encoding="utf-8")
        print(f"{args.phase}: {len(recs)} pairs in {wall:.1f} s on {args.workers} workers", flush=True)
    else:
        for arm in ("new", "ref"):
            jobs = []
            for d in ds:
                doc = json.loads((RUNS / arm / f"{d}.json").read_text(encoding="utf-8"))
                for r in doc["records"]:
                    sel = r["selected"]
                    if sel is not None:
                        jobs.append((d, r["g"], r["s"], sel["membership"], sel["a"], sel["b"],
                                     sel["selected_resolution"]))
            t0 = time.perf_counter()
            res = pool.map(search, jobs, chunksize=1)
            wall = time.perf_counter() - t0
            (RUNS / f"search_{arm}.json").write_text(json.dumps({"wall_seconds": wall, "results": res}),
                                                     encoding="utf-8")
            print(f"search {arm}: {len(res)} pairs, {sum(r['found'] for r in res)} reproduced, {wall:.1f} s",
                  flush=True)
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()
