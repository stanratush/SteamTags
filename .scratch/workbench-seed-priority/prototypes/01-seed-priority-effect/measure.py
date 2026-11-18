"""Throwaway: what would "Prefer the main seed" change against today's closest-γ-first Workbench search?

For every Threshold Pair of the latest Build's default Parameter Selection grid with a Selected Partition:
  closest  today's search (workbench_setting): two-decimal γ in the domain nearest the midpoint, main seed then
           the 10 scan seeds at each γ;
  main     the main seed at every candidate γ first (nearest first), then the scan seeds starting again nearest.
Both modes share the fallback. For every graph where the two modes disagree it also measures, at each mode's
(γ, seed): Q of the Selected Partition, the Workbench Seed-Noise Floor (noise seeds derived from that seed, at that
γ), and how far γ sits from the domain's edges.

    uv run python .scratch/workbench-seed-priority/prototypes/01-seed-priority-effect/measure.py

Run from the repo root. Reads the Build's cached grid (computes nothing that is missing) and writes results.json here.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score

from steamstudy.app import ps_cache
from steamstudy.app.loader import load_build
from steamstudy.network import champ as C
from steamstudy.network import metrics as M
from steamstudy.network import selection as SEL
from steamstudy.network.cluster import _leiden_graph, _leiden_passes, leiden_scan
from steamstudy.network.graph import build_network, to_graph
from steamstudy.network.stability import noise_seeds

HERE = Path(__file__).parent


def main_first(graph, target, a, b, mid, main_seed, scan_seeds):
    lg, weights = _leiden_graph(graph)
    target = np.asarray(target)
    cands = SEL.workbench_candidates(a, b, mid)

    def hit(gamma, seed):
        labels, _ = _leiden_passes(lg, weights, gamma, seed)
        return np.array_equal(C.canonical(labels), target)

    for gamma in cands:
        if hit(gamma, main_seed):
            return {"gamma": gamma, "seed": main_seed, "seed_kind": "main", "flag": None}
    for gamma in cands:
        for seed in scan_seeds:
            if hit(gamma, seed):
                return {"gamma": gamma, "seed": seed, "seed_kind": "scan", "flag": None}
    return None  # same fallback as today


def floor_at(graph, target, gamma, seed, k, r):
    runs = leiden_scan(graph, [gamma], noise_seeds(seed, k, r))
    aris = [float(adjusted_rand_score(target, x.membership)) for x in runs]
    exact = sum(bool(np.array_equal(C.canonical(x.membership), np.asarray(target))) for x in runs)
    return {"floor": min(aris), "mean": statistics.fmean(aris), "exact": exact, "runs": len(runs)}


def work(job):
    task, cached = job
    s = task.settings
    network = build_network(task.games, s, task.context)
    graph = to_graph(network.nodes, network.edges, s.clustering_weight)
    p = cached.selected_partition
    a, b, mid, target = p["a"], p["b"], cached.selected_resolution, list(p["membership"])
    closest = {k: cached.workbench[k] for k in ("gamma", "seed", "seed_kind", "flag")}
    # sanity: today's code still gives the cached answer
    now = SEL.workbench_setting(graph, target, a, b, mid, s.seed, task.scan_seeds)
    assert (now.gamma, now.seed, now.flag) == (closest["gamma"], closest["seed"], closest["flag"]), task.graph_hash
    main = main_first(graph, target, a, b, mid, s.seed, task.scan_seeds) or closest
    out = {"hash": task.graph_hash, "n_pairs": task.n_pairs, "a": a, "b": b, "mid": mid,
           "n_candidates": len(SEL.workbench_candidates(a, b, mid)), "closest": closest, "main": main,
           "ps_floor": cached.seed_noise["floor"]}
    if (main["gamma"], main["seed"]) != (closest["gamma"], closest["seed"]):
        clusters = SEL.clusters_of(network.nodes, target)
        for mode in ("closest", "main"):
            m = out[mode]
            m["q"] = M.modularity(graph, clusters, m["gamma"])
            m["edge_room"] = min(m["gamma"] - a, b - m["gamma"]) / ((b - a) / 2)  # 1 at midpoint, 0 at an edge
            m["noise"] = floor_at(graph, target, m["gamma"], m["seed"], s.noise_seeds, s.null_replicates)
    return out


def main():
    ctx = load_build(Path("builds/20261005T062558Z-full/20261109T064256Z-493c5375"))
    settings = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    jobs, chosen_hash, pair_hash_all = [], {}, {}
    started = time.perf_counter()
    pool = Pool(12)
    for d in (x.key for x in ctx.datasets):
        key = settings.grid_key(d, ctx.context(d))
        loaded = ps_cache.load_grid(ctx.app_cache, key, d)
        pair_hash, tasks = SEL.grid_tasks(ctx.games(d), settings, d, ctx.context(d))
        if loaded is None:  # computed in memory; the Build's cache is left alone
            t0 = time.perf_counter()
            run = SEL.run_grid(ctx.games(d), settings, d, ctx.context(d), map_fn=pool.imap_unordered)
            grid = SEL.Grid(d, run.pair_hash, run.results)
            na = SEL.neighbour_agreement(grid, SEL.neighbour_links(grid))
            print(f"{d}: grid computed in {time.perf_counter() - t0:.0f} s", flush=True)
        else:
            grid, _links, na = loaded
        pair_hash_all[d] = {f"{g},{s}": h for (g, s), h in pair_hash.items()}
        chosen = SEL.choose(grid, na, SEL.default_constraints(ctx.network)).chosen
        if chosen:
            chosen_hash[d] = [*chosen, pair_hash[chosen]]
        for t in tasks:
            r = grid.results[t.graph_hash]
            if r.selected_partition is not None:
                jobs.append((t, r))
    print(f"build {ctx.build_id}: {len(jobs)} graphs with a Selected Partition", flush=True)
    with pool:
        out = list(pool.imap_unordered(work, jobs))
    doc = {"build_id": ctx.build_id, "main_seed": settings.seed, "seconds": time.perf_counter() - started,
           "chosen": chosen_hash, "pair_hash": pair_hash_all, "graphs": sorted(out, key=lambda x: x["hash"])}
    (HERE / "results.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"done in {doc['seconds']:.0f} s")


if __name__ == "__main__":
    main()
