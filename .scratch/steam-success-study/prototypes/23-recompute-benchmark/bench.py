"""Recompute-cost benchmark for the Tag Network (ticket 23).

SYNTHETIC DATA ONLY. No real Steam games, tags or AppIDs are used, and nothing
here contacts Steam or any other site. Tag names are `syn_tag_NNN`; AppIDs are
random integers. Numbers measure cost, not structure.

Run (from this folder, with the Python 3.14 venv described in README.md):
    python bench.py                 # full run, writes results.json next to this file
    python bench.py --reps 5 --null-reps 3   # quick smoke run
    python bench.py --stats-only    # just print the synthetic dataset's shape
"""
import time

T_START = time.perf_counter()

import argparse
import gc
import gzip
import importlib
import importlib.metadata
import itertools
import json
import math
import os
import pickle
import platform
import random
import statistics
import subprocess
import sys
import tracemalloc
from collections import Counter
from pathlib import Path

IMPORT_MS = {}
for _m in ["numpy", "scipy", "networkx", "sklearn.metrics", "igraph", "leidenalg", "plotly.io.json"]:
    _t = time.perf_counter()
    importlib.import_module(_m)
    IMPORT_MS[_m] = (time.perf_counter() - _t) * 1000
IMPORT_MS["_total_to_ready"] = (time.perf_counter() - T_START) * 1000

import igraph as ig
import leidenalg as la
import networkx as nx
import numpy as np
from plotly.io.json import to_json_plotly
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score

HERE = Path(__file__).resolve().parent
SEED = 42
GAMMA = 1.0

# ----------------------------------------------------------------------------
# Synthetic dataset
# ----------------------------------------------------------------------------
# Calibration (from research/04-steam-tag-taxonomy.md and 09/09b):
# - live Steam vocabulary 446 tags, archived table 400 unique names -> vocab 400;
# - store pages show at most 20 tags and most sampled apps showed exactly 20;
#   a few show fewer (e.g. 9) and >= 5 are required at launch -> 85 % of games
#   have 20 tags, the rest 5..19 uniformly.
# Assumptions (not calibrated): Zipf exponent 1.0 over tag rank; 8 latent
# "genres", each boosting 30 random mid/long-tail tags x6 (mild planted
# structure so community detection is not run on pure noise); months_observed
# uniform 1..60, so a Minimum Months Filter of 13 drops ~20 % of games.


def make_synthetic(seed=2026, n_games=100, n_tags=400, zipf_s=1.0, n_genres=8,
                   genre_core=30, genre_boost=6.0, p_full=0.85):
    rng = random.Random(seed)
    tags = [f"syn_tag_{i:03d}" for i in range(1, n_tags + 1)]
    base = [1.0 / (r ** zipf_s) for r in range(1, n_tags + 1)]
    cores = [set(rng.sample(range(8, n_tags), genre_core)) for _ in range(n_genres)]
    appids = sorted(rng.sample(range(10_000, 3_500_000), n_games))
    games, months = {}, {}
    for a in appids:
        g = rng.randrange(n_genres)
        k = 20 if rng.random() < p_full else rng.randint(5, 19)
        w = [base[i] * (genre_boost if i in cores[g] else 1.0) for i in range(n_tags)]
        # weighted sampling without replacement (Efraimidis-Spirakis keys)
        keys = sorted(range(n_tags), key=lambda i: rng.random() ** (1.0 / w[i]), reverse=True)
        games[a] = frozenset(tags[i] for i in keys[:k])
        months[a] = rng.randint(1, 60)
    return games, months


def apply_mmf(games, months, min_months):
    return {a: ts for a, ts in games.items() if months[a] >= min_months}


# ----------------------------------------------------------------------------
# 1. Graph build
# ----------------------------------------------------------------------------

def tag_game_sets(games):
    tg = {}
    for a, ts in games.items():
        for t in ts:
            tg.setdefault(t, set()).add(a)
    return {t: frozenset(s) for t, s in tg.items()}


def build_graph(games, min_games, min_shared):
    """Canonical order: nodes sorted, edges sorted by (u, v)."""
    tg = tag_game_sets(games)
    n = {t: len(s) for t, s in tg.items() if len(s) >= min_games}
    kept = sorted(n)
    pair = Counter()
    for ts in games.values():
        vis = sorted(t for t in ts if t in n)
        pair.update(itertools.combinations(vis, 2))
    N = len(games)
    G = nx.Graph()
    G.add_nodes_from((t, {"n_games": n[t]}) for t in kept)
    G.add_edges_from(
        (u, v, {"weight": c, "lift": c * N / (n[u] * n[v])})
        for (u, v), c in sorted(pair.items()) if c >= min_shared
    )
    return G, tg


# ----------------------------------------------------------------------------
# 2-4. Clustering
# ----------------------------------------------------------------------------

def canon_comms(comms):
    """Sort clusters by size desc, then by smallest member -> C1, C2, ..."""
    cs = [sorted(c) for c in comms]
    cs.sort(key=lambda c: (-len(c), c[0]))
    return cs


def louvain(G, weight="weight", seed=SEED, gamma=GAMMA):
    return canon_comms(nx.community.louvain_communities(
        G, weight=weight, resolution=gamma, seed=seed, threshold=1e-7))


def igraph_build(G, weight="weight"):
    nodes = list(G.nodes)  # already sorted
    idx = {t: i for i, t in enumerate(nodes)}
    edges = [(idx[u], idx[v]) for u, v in G.edges]
    g = ig.Graph(n=len(nodes), edges=edges, directed=False)
    w = [d[weight] for _, _, d in G.edges(data=True)]
    return g, nodes, w


def leiden(G, weight="weight", seed=SEED, gamma=GAMMA, prebuilt=None):
    g, nodes, w = prebuilt if prebuilt else igraph_build(G, weight)
    part = la.find_partition(g, la.RBConfigurationVertexPartition, weights=w,
                             resolution_parameter=gamma, n_iterations=-1, seed=seed)
    return canon_comms([[nodes[i] for i in c] for c in part])


def labels_of(G, comms):
    node_c = {}
    for ci, c in enumerate(comms):
        for t in c:
            node_c[t] = ci
    return np.array([node_c[t] for t in G.nodes]), node_c


def cluster_counts(comms):
    multi = sum(1 for c in comms if len(c) >= 2)
    return multi, len(comms) - multi


# ----------------------------------------------------------------------------
# 5. Jaccard + silhouette
# ----------------------------------------------------------------------------

def jaccard_matrix(tags, tg, game_index):
    B = np.zeros((len(tags), len(game_index)), dtype=np.float64)
    for i, t in enumerate(tags):
        B[i, [game_index[a] for a in tg[t]]] = 1.0
    inter = B @ B.T
    ng = B.sum(axis=1)
    union = ng[:, None] + ng[None, :] - inter
    D = 1.0 - inter / union
    np.fill_diagonal(D, 0.0)
    return D


def jaccard_python(tags, tg):
    n = len(tags)
    D = np.zeros((n, n))
    sets = [tg[t] for t in tags]
    for i in range(n):
        a = sets[i]
        for j in range(i + 1, n):
            b = sets[j]
            inter = len(a & b)
            D[i, j] = D[j, i] = 1.0 - inter / (len(a) + len(b) - inter)
    return D


def silhouette(D, labels):
    k = len(set(labels.tolist()))
    if k < 2 or k > len(labels) - 1:
        return None, None
    return silhouette_score(D, labels, metric="precomputed"), silhouette_samples(D, labels, metric="precomputed")


# ----------------------------------------------------------------------------
# 6. Per-state metrics (ticket 10 + 11 set)
# ----------------------------------------------------------------------------

def metrics(G, comms, D, weight="weight", gamma=GAMMA):
    nodes = list(G.nodes)
    pos_of = {t: i for i, t in enumerate(nodes)}
    labels, node_c = labels_of(G, comms)
    k = len(comms)
    multi = [len(c) >= 2 for c in comms]
    pool = [ci if multi[ci] else -1 for ci in range(k)]  # one-tag clusters pooled
    strength = dict.fromkeys(nodes, 0.0)
    s_intra = dict.fromkeys(nodes, 0.0)
    deg_intra = dict.fromkeys(nodes, 0)
    k_is = {t: {} for t in nodes}
    int_e, int_w, cut = [0] * k, [0.0] * k, [0.0] * k
    table = {}
    total_w = 0.0
    for u, v, d in G.edges(data=True):
        w = d[weight]
        total_w += w
        cu, cv = node_c[u], node_c[v]
        strength[u] += w
        strength[v] += w
        k_is[u][cv] = k_is[u].get(cv, 0.0) + w
        k_is[v][cu] = k_is[v].get(cu, 0.0) + w
        if cu == cv:
            int_e[cu] += 1
            int_w[cu] += w
            s_intra[u] += w
            s_intra[v] += w
            deg_intra[u] += 1
            deg_intra[v] += 1
        else:
            cut[cu] += w
            cut[cv] += w
            key = tuple(sorted((pool[cu], pool[cv])))
            e = table.setdefault(key, [0, 0.0])
            e[0] += 1
            e[1] += w
    degree = dict(G.degree())
    vol = [sum(strength[t] for t in c) for c in comms]
    tot_vol = 2 * total_w
    if total_w > 0:
        Q = nx.community.modularity(G, comms, weight=weight, resolution=gamma)
        coverage = sum(int_w) / total_w
    else:
        Q = coverage = None
    clusters = []
    medoid_score = {}
    for ci, c in enumerate(comms):
        n = len(c)
        pairs = n * (n - 1) / 2
        rest = tot_vol - vol[ci]
        denom = min(vol[ci], rest)
        rec = {
            "id": f"C{ci + 1}", "size": n, "internal_edges": int_e[ci],
            "edge_density": int_e[ci] / pairs if pairs else None,
            "weighted_density": int_w[ci] / pairs if pairs else None,
            "cut_weight": cut[ci],
            "conductance": cut[ci] / denom if denom > 0 else None,
            "connected": nx.is_connected(G.subgraph(c)) if n >= 2 else None,
        }
        if n >= 2:
            ids = np.array([pos_of[t] for t in c])
            sub = D[np.ix_(ids, ids)]
            scores = sub.sum(axis=1) / (n - 1)
            for t, s in zip(c, scores):
                medoid_score[t] = float(s)
            if n >= 3:
                rec["center"] = min(c, key=lambda t: (round(medoid_score[t], 12), -G.nodes[t]["n_games"], t))
                rec["top_strength_tag"] = min(c, key=lambda t: (-s_intra[t], -G.nodes[t]["n_games"], t))
            # within-module z (multi-tag clusters only)
            vals = [s_intra[t] for t in c]
            mu = sum(vals) / n
            sd = math.sqrt(sum((x - mu) ** 2 for x in vals) / n)
            for t in c:
                G.nodes[t]["_z"] = (s_intra[t] - mu) / sd if sd > 0 else None
        clusters.append(rec)
    node_rows = []
    for t in nodes:
        s = strength[t]
        part = 1.0 - sum((x / s) ** 2 for x in k_is[t].values()) if s > 0 else None
        node_rows.append({
            "tag": t, "n_games": G.nodes[t]["n_games"], "degree": degree[t],
            "degree_intra": deg_intra[t], "strength": s, "strength_intra": s_intra[t],
            "within_z": G.nodes[t].pop("_z", None), "participation": part,
            "medoid_score": medoid_score.get(t),
        })
    return {"Q": Q, "coverage": coverage, "clusters": clusters, "nodes": node_rows,
            "table": {f"{a}|{b}": v for (a, b), v in sorted(table.items())}}


# ----------------------------------------------------------------------------
# 7. Null model (bipartite curveball)
# ----------------------------------------------------------------------------

def curveball(games, trades, rng):
    keys = list(games)
    rows = [set(games[a]) for a in keys]
    n = len(rows)
    done = 0
    for _ in range(trades):
        i = rng.randrange(n)
        j = rng.randrange(n - 1)
        if j >= i:
            j += 1
        a, b = rows[i], rows[j]
        a_only, b_only = a - b, b - a
        if not a_only or not b_only:
            continue
        pool_ = sorted(a_only | b_only)
        rng.shuffle(pool_)
        na = len(a_only)
        shared = a & b
        rows[i] = shared | set(pool_[:na])
        rows[j] = shared | set(pool_[na:])
        done += 1
    return {a: frozenset(r) for a, r in zip(keys, rows)}, done


def null_model(games, G, min_games, min_shared, R, trades_per_game, algo="louvain", weight="weight"):
    vis = set(G.nodes)
    restricted = {a: frozenset(t for t in ts if t in vis) for a, ts in games.items()}
    trades = trades_per_game * len(restricted)
    qs = []
    t_shuffle = t_build = t_cluster = t_q = 0.0
    for r in range(R):
        rng = random.Random(SEED * 1000 + r)
        t0 = time.perf_counter()
        shuffled, _ = curveball(restricted, trades, rng)
        t1 = time.perf_counter()
        Gn, _ = build_graph(shuffled, min_games, min_shared)
        t2 = time.perf_counter()
        comms = louvain(Gn, weight) if algo == "louvain" else leiden(Gn, weight)
        t3 = time.perf_counter()
        qs.append(nx.community.modularity(Gn, comms, weight=weight, resolution=GAMMA) if Gn.number_of_edges() else 0.0)
        t4 = time.perf_counter()
        t_shuffle += t1 - t0
        t_build += t2 - t1
        t_cluster += t3 - t2
        t_q += t4 - t3
    return qs, {"shuffle": t_shuffle, "build": t_build, "cluster": t_cluster, "Q": t_q}, trades


# ----------------------------------------------------------------------------
# 8-9. Layouts
# ----------------------------------------------------------------------------

def global_layout(G, weight="weight", pos=None, iterations=50):
    return nx.spring_layout(G, weight=weight, seed=SEED, pos=pos, iterations=iterations)


def cluster_layout(G, comms, gpos, weight="weight", gap=0.6):
    boxes = []
    singles = []
    for c in comms:
        if len(c) < 2:
            singles.extend(c)
            continue
        sub = G.subgraph(c)
        p = nx.spring_layout(sub, pos={t: gpos[t] for t in c}, weight=weight, seed=SEED)
        arr = np.array([p[t] for t in c], dtype=float)
        arr -= arr.mean(axis=0)
        span = np.abs(arr).max() or 1.0
        side = math.sqrt(len(c))
        arr = arr / span * side / 2
        boxes.append((c, arr, side, side))
    if singles:
        cols = max(1, math.ceil(math.sqrt(len(singles))))
        arr = np.array([[(i % cols) * 0.5, (i // cols) * 0.5] for i in range(len(singles))], dtype=float)
        arr -= arr.mean(axis=0)
        side = cols * 0.5
        boxes.append((singles, arr, side, side))
    total_area = sum((w + gap) * (h + gap) for _, _, w, h in boxes)
    row_w = math.sqrt(total_area) * 1.3
    out = {}
    x = y = row_h = 0.0
    for members, arr, w, h in boxes:  # shelf packing, boxes already size-ordered
        if x > 0 and x + w > row_w:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        cx, cy = x + w / 2, y + h / 2
        for t, (px, py) in zip(members, arr):
            out[t] = (cx + px, cy + py)
        x += w + gap
        row_h = max(row_h, h)
    return out


# ----------------------------------------------------------------------------
# 11. Cytoscape payload
# ----------------------------------------------------------------------------
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
           "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]


def elements(G, comms, pos, tg=None, short_edge_ids=False):
    _, node_c = labels_of(G, comms)
    els = []
    for t in G.nodes:
        ci = node_c[t]
        multi = len(comms[ci]) >= 2
        x, y = pos[t]
        els.append({"data": {"id": t, "label": t, "cluster": f"C{ci + 1}",
                             "color": PALETTE[ci % len(PALETTE)] if multi else "#cccccc",
                             "size": round(8 + 2 * math.sqrt(G.nodes[t]["n_games"]), 1)},
                    "position": {"x": round(float(x) * 100, 1), "y": round(float(y) * 100, 1)}})
    for i, (u, v, d) in enumerate(G.edges(data=True)):
        data = {"id": f"e{i}" if short_edge_ids else f"{u}|{v}", "source": u, "target": v, "weight": d["weight"]}
        if tg is not None:
            data["appids"] = sorted(tg[u] & tg[v])
        els.append({"data": data})
    return els


# ----------------------------------------------------------------------------
# Timing helpers
# ----------------------------------------------------------------------------

def p95(xs):
    s = sorted(xs)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)]


def timeit(fn, reps):
    """Returns (first_call_ms, median_ms, p95_ms, last_result). First call is not in the stats."""
    t = time.perf_counter()
    res = fn()
    first = (time.perf_counter() - t) * 1000
    xs = []
    for _ in range(reps):
        t = time.perf_counter()
        res = fn()
        xs.append((time.perf_counter() - t) * 1000)
    return first, statistics.median(xs), p95(xs), res


# ----------------------------------------------------------------------------
# Pipelines (end-to-end, timed as one unit)
# ----------------------------------------------------------------------------

def recompute(games, mg, ms, algo, weight, gpos, D_full=None, full_index=None):
    """One settings change: build -> cluster -> Jaccard(+silhouette) -> metrics -> cluster layout -> payload JSON.
    Global positions are an input (cached per dataset + filter + weight mode).
    If D_full is given, the Jaccard matrix is subset from it; otherwise computed for the visible tags."""
    G, tg = build_graph(games, mg, ms)
    comms = louvain(G, weight) if algo == "louvain" else leiden(G, weight)
    D = subset_or_compute(G, tg, games, D_full, full_index)
    labels, _ = labels_of(G, comms)
    _, samples = silhouette_from_samples(D, labels)
    m = metrics(G, comms, D, weight)
    pos = cluster_layout(G, comms, gpos, weight)
    payload = to_json_plotly(elements(G, comms, pos))
    return G, tg, comms, D, samples, m, pos, payload


def recluster(G, D, algo, weight, gpos, seed=SEED, gamma=GAMMA):
    """Seed / gamma / algorithm change on an unchanged graph + Jaccard matrix."""
    comms = louvain(G, weight, seed, gamma) if algo == "louvain" else leiden(G, weight, seed, gamma)
    labels, _ = labels_of(G, comms)
    silhouette_from_samples(D, labels)
    m = metrics(G, comms, D, weight, gamma)
    pos = cluster_layout(G, comms, gpos, weight)
    return to_json_plotly(elements(G, comms, pos))


def subset_or_compute(G, tg, games, D_full, full_index):
    nodes = list(G.nodes)
    if D_full is not None:
        ids = np.array([full_index[t] for t in nodes], dtype=np.intp)
        return D_full[np.ix_(ids, ids)]
    gi = {a: i for i, a in enumerate(sorted(games))}
    return jaccard_matrix(nodes, tg, gi)


def silhouette_from_samples(D, labels):
    k = len(set(labels.tolist()))
    if k < 2 or k > len(labels) - 1:
        return None, None
    s = silhouette_samples(D, labels, metric="precomputed")
    return float(s.mean()), s


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

SETTINGS = [(8, 8), (3, 3), (1, 1)]  # default first, so its first-call column carries the cold cost


def fmt(x, d=2):
    return "n/a" if x is None else f"{x:.{d}f}"


def dataset_stats(games, months):
    tg = tag_game_sets(games)
    tpg = [len(t) for t in games.values()]
    top = sorted(tg.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:5]
    return {
        "games": len(games), "distinct_tags_used": len(tg),
        "tags_per_game_mean": statistics.mean(tpg), "tags_per_game_min": min(tpg),
        "games_with_20_tags": sum(1 for x in tpg if x == 20),
        "top5_tag_share": [(t, len(s) / len(games)) for t, s in top],
        "tags_on_1_game": sum(1 for s in tg.values() if len(s) == 1),
        "tags_on_ge8_games": sum(1 for s in tg.values() if len(s) >= 8),
        "mmf13_games_kept": sum(1 for m in months.values() if m >= 13),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--null-reps", type=int, default=20, help="repetitions of the whole R=20 null baseline")
    ap.add_argument("--R", type=int, default=20)
    ap.add_argument("--trades-per-game", type=int, default=10)
    ap.add_argument("--mmf", type=int, default=13)
    ap.add_argument("--stats-only", action="store_true")
    args = ap.parse_args()
    reps = args.reps

    games_all, months = make_synthetic()
    st = dataset_stats(games_all, months)
    print("SYNTHETIC dataset:", json.dumps(st, indent=1))
    if args.stats_only:
        return

    env = {
        "python": sys.version.split()[0], "gil_enabled": getattr(sys, "_is_gil_enabled", lambda: True)(),
        "platform": platform.platform(), "cpu": platform.processor(), "cpu_count": os.cpu_count(),
        "versions": {p: importlib.metadata.version(p) for p in
                     ["networkx", "numpy", "scipy", "scikit-learn", "python-igraph", "igraph", "leidenalg", "plotly"]},
        "import_ms_in_process_sequential": IMPORT_MS,
    }
    # bare interpreter start, for comparison with import cost
    xs = []
    for _ in range(5):
        t = time.perf_counter()
        subprocess.run([sys.executable, "-c", "pass"], check=True)
        xs.append((time.perf_counter() - t) * 1000)
    env["bare_interpreter_start_ms_median"] = statistics.median(xs)
    print("ENV:", json.dumps(env, indent=1))

    results = {"synthetic": True, "dataset": st, "env": env, "args": vars(args), "settings": {}}
    games = games_all  # main table: Minimum Months Filter off (100 games)
    N = len(games)
    game_index = {a: i for i, a in enumerate(sorted(games))}
    tg_all = tag_game_sets(games)
    all_tags = sorted(tg_all)
    full_index = {t: i for i, t in enumerate(all_tags)}

    # Global layout on the loosest graph (once per dataset + filter + weight mode)
    G11, _ = build_graph(games, 1, 1)
    lay = {}
    lay["global_spring_50it"] = timeit(lambda: global_layout(G11), reps)
    gpos = lay["global_spring_50it"][3]
    lay["relayout_from_pos_50it"] = timeit(lambda: global_layout(G11, pos=gpos), reps)
    lay["relayout_from_pos_10it"] = timeit(lambda: global_layout(G11, pos=gpos, iterations=10), reps)
    lay["global_spring_lift_50it"] = timeit(lambda: global_layout(G11, weight="lift"), reps)
    # Full Jaccard once for ALL tags of the (filtered) dataset
    jfull = timeit(lambda: jaccard_matrix(all_tags, tg_all, game_index), reps)
    D_full = jfull[3]
    results["layout"] = {k: v[:3] for k, v in lay.items()}
    results["jaccard_full_all_tags"] = {"tags": len(all_tags), "timing": jfull[:3], "bytes": D_full.nbytes}

    for mg, ms in SETTINGS:
        key = f"{mg}/{ms}"
        print(f"\n=== setting {key} (SYNTHETIC, {N} games) ===", flush=True)
        r = {}
        T = {}
        T["1_build"] = timeit(lambda: build_graph(games, mg, ms), reps)
        G, tg = T["1_build"][3]
        T["2_louvain_shared"] = timeit(lambda: louvain(G, "weight"), reps)
        comms = T["2_louvain_shared"][3]
        T["3a_igraph_build"] = timeit(lambda: igraph_build(G, "weight"), reps)
        pre = T["3a_igraph_build"][3]
        T["3b_leiden_partition_only"] = timeit(lambda: leiden(G, "weight", prebuilt=pre), reps)
        T["3_leiden_build+partition"] = timeit(lambda: leiden(G, "weight"), reps)
        comms_leiden = T["3_leiden_build+partition"][3]
        T["4_louvain_lift"] = timeit(lambda: louvain(G, "lift"), reps)
        comms_lift = T["4_louvain_lift"][3]
        nodes = list(G.nodes)
        labels, _ = labels_of(G, comms)
        T["5a_jaccard_per_state_numpy"] = timeit(lambda: jaccard_matrix(nodes, tg, game_index), reps)
        D = T["5a_jaccard_per_state_numpy"][3]
        T["5b_jaccard_subset_of_full"] = timeit(lambda: subset_or_compute(G, tg, games, D_full, full_index), reps)
        assert np.allclose(T["5b_jaccard_subset_of_full"][3], D)
        T["5c_jaccard_per_state_python_sets"] = timeit(lambda: jaccard_python(nodes, tg), max(5, reps // 3))
        assert np.allclose(T["5c_jaccard_per_state_python_sets"][3], D)
        k_lab = len(set(labels.tolist()))
        ok = 2 <= k_lab <= len(labels) - 1
        T["5d_silhouette_score"] = timeit(lambda: silhouette_score(D, labels, metric="precomputed") if ok else None, reps)
        T["5e_silhouette_samples"] = timeit(lambda: silhouette_samples(D, labels, metric="precomputed") if ok else None, reps)
        T["6_metrics_all"] = timeit(lambda: metrics(G, comms, D, "weight"), reps)
        m = T["6_metrics_all"][3]
        T["6a_nx_modularity_only"] = timeit(lambda: nx.community.modularity(G, comms, weight="weight", resolution=GAMMA), reps)
        # 7. null model
        nr = max(1, args.null_reps)
        tot = []
        parts_acc = None
        first_null = None
        for i in range(nr + 1):
            t = time.perf_counter()
            qs, parts, trades = null_model(games, G, mg, ms, args.R, args.trades_per_game)
            el = (time.perf_counter() - t) * 1000
            if i == 0:
                first_null = el
            else:
                tot.append(el)
                parts_acc = parts
        T["7_null_R20_louvain"] = (first_null, statistics.median(tot), p95(tot), None)
        Q = m["Q"]
        sd = statistics.pstdev(qs)
        r["null"] = {"R": args.R, "trades_per_replicate": trades, "Q": Q, "Q_null_mean": statistics.mean(qs),
                     "Q_null_sd": sd, "z": (Q - statistics.mean(qs)) / sd if sd else None,
                     "last_run_breakdown_ms": {k: v * 1000 for k, v in parts_acc.items()},
                     "per_replicate_median_ms": statistics.median(tot) / args.R}
        # informational: null with Leiden (fewer repetitions)
        tl = []
        for _ in range(max(3, nr // 4)):
            t = time.perf_counter()
            null_model(games, G, mg, ms, args.R, args.trades_per_game, algo="leiden")
            tl.append((time.perf_counter() - t) * 1000)
        T["7b_null_R20_leiden"] = (None, statistics.median(tl), p95(tl), None)
        # curveball alone, per 1000 trades
        vis = set(G.nodes)
        restr = {a: frozenset(t for t in ts if t in vis) for a, ts in games.items()}
        T["7c_curveball_1000_trades"] = timeit(lambda: curveball(restr, 1000, random.Random(1)), reps)
        # 9. cluster-separated layout
        T["9_cluster_layout"] = timeit(lambda: cluster_layout(G, comms, gpos), reps)
        cpos = T["9_cluster_layout"][3]
        # 10. seed-noise floor
        def seed_noise():
            return [adjusted_rand_score(labels, labels_of(G, louvain(G, "weight", seed=SEED + 1 + i))[0]) for i in range(10)]
        T["10_seed_noise_K10"] = timeit(seed_noise, max(5, reps // 3))
        aris = T["10_seed_noise_K10"][3]
        # 11. payload
        T["11a_elements_build+to_json_plotly"] = timeit(lambda: to_json_plotly(elements(G, comms, cpos)), reps)
        js = T["11a_elements_build+to_json_plotly"][3]
        T["11b_same_with_appids"] = timeit(lambda: to_json_plotly(elements(G, comms, cpos, tg)), reps)
        js_ids = T["11b_same_with_appids"][3]
        js_short = to_json_plotly(elements(G, comms, cpos, short_edge_ids=True))
        r["payload_bytes"] = {
            "no_appids_short_edge_ids": len(js_short.encode()),
            "no_appids_json_dumps_default_separators": len(json.dumps(elements(G, comms, cpos)).encode()),
            "no_appids": len(js.encode()), "no_appids_gzip": len(gzip.compress(js.encode())),
            "with_appids": len(js_ids.encode()), "with_appids_gzip": len(gzip.compress(js_ids.encode())),
        }
        # 12. edge AppID lookup on click
        edges = list(G.edges)
        lk = []
        for _ in range(3):
            for u, v in edges:
                t = time.perf_counter_ns()
                sorted(tg[u] & tg[v])
                lk.append((time.perf_counter_ns() - t) / 1000)
        r["edge_lookup_us"] = {"median": statistics.median(lk), "p95": p95(lk), "max": max(lk), "n": len(lk)}
        # 13. memory of one full state
        gc.collect()
        tracemalloc.start()
        b0 = tracemalloc.get_traced_memory()[0]
        Gm, tgm = build_graph(games, mg, ms)
        cm = louvain(Gm, "weight")
        Dm = subset_or_compute(Gm, tgm, games, D_full, full_index)
        lm, _ = labels_of(Gm, cm)
        sm = silhouette_from_samples(Dm, lm)
        mm = metrics(Gm, cm, Dm, "weight")
        pm = cluster_layout(Gm, cm, gpos)
        state = {"G": Gm, "tag_games": tgm, "comms": cm, "labels": lm, "D": Dm, "sil": sm, "metrics": mm, "pos": pm}
        b1 = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        del state["tag_games"]
        r["memory"] = {"tracemalloc_bytes_incl_tag_game_sets": b1 - b0, "jaccard_bytes": Dm.nbytes,
                       "pickle_bytes_excl_tag_game_sets": len(pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)),
                       "pickle_bytes_tag_game_sets": len(pickle.dumps(tgm, protocol=pickle.HIGHEST_PROTOCOL))}
        del state, Gm, tgm, Dm
        # end-to-end pipelines
        T["E1_full_recompute_louvain_cachedJ"] = timeit(
            lambda: recompute(games, mg, ms, "louvain", "weight", gpos, D_full, full_index), reps)
        T["E2_full_recompute_louvain_perstateJ"] = timeit(
            lambda: recompute(games, mg, ms, "louvain", "weight", gpos), reps)
        T["E3_full_recompute_leiden_cachedJ"] = timeit(
            lambda: recompute(games, mg, ms, "leiden", "weight", gpos, D_full, full_index), reps)
        T["E4_full_recompute_louvain_lift_cachedJ"] = timeit(
            lambda: recompute(games, mg, ms, "louvain", "lift", gpos, D_full, full_index), reps)
        T["E5_recluster_only_louvain"] = timeit(lambda: recluster(G, D, "louvain", "weight", gpos, seed=7), reps)
        T["E6_recluster_only_leiden"] = timeit(lambda: recluster(G, D, "leiden", "weight", gpos, seed=7), reps)

        r["graph"] = {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
                      "isolated": nx.number_of_isolates(G),
                      "louvain_shared": cluster_counts(comms), "leiden_shared": cluster_counts(comms_leiden),
                      "louvain_lift": cluster_counts(comms_lift),
                      "disconnected_louvain_clusters": sum(1 for c in m["clusters"] if c["connected"] is False),
                      "Q_louvain_shared": Q, "coverage": m["coverage"],
                      "seed_noise_ARI_mean": statistics.mean(aris), "seed_noise_ARI_min": min(aris)}
        r["timings_ms"] = {k: {"first": v[0], "median": v[1], "p95": v[2]} for k, v in T.items()}
        results["settings"][key] = r
        for k, v in T.items():
            print(f"{k:40s} first {fmt(v[0]):>9s}  median {fmt(v[1]):>9s}  p95 {fmt(v[2]):>9s}", flush=True)
        print(json.dumps({k: r[k] for k in ["graph", "null", "payload_bytes", "edge_lookup_us", "memory"]}, indent=1, default=str))

    # Minimum Months Filter on: global layout + full Jaccard must be redone, then the default-setting recompute
    gf = apply_mmf(games_all, months, args.mmf)
    gif = {a: i for i, a in enumerate(sorted(gf))}
    tgf = tag_game_sets(gf)
    tags_f = sorted(tgf)
    fidx = {t: i for i, t in enumerate(tags_f)}
    mmf = {"min_months": args.mmf, "games": len(gf)}
    Gf11, _ = build_graph(gf, 1, 1)
    lf = timeit(lambda: global_layout(Gf11), reps)
    jf = timeit(lambda: jaccard_matrix(tags_f, tgf, gif), reps)
    mmf["global_layout"] = lf[:3]
    mmf["jaccard_full"] = jf[:3]
    for mg, ms in SETTINGS:
        Gx, _ = build_graph(gf, mg, ms)
        e = timeit(lambda: recompute(gf, mg, ms, "louvain", "weight", lf[3], jf[3], fidx), reps)
        ln = []
        for _ in range(max(3, args.null_reps // 4)):
            t = time.perf_counter()
            null_model(gf, Gx, mg, ms, args.R, args.trades_per_game)
            ln.append((time.perf_counter() - t) * 1000)
        mmf[f"{mg}/{ms}"] = {"nodes": Gx.number_of_nodes(), "edges": Gx.number_of_edges(),
                             "louvain_shared": cluster_counts(louvain(Gx)),
                             "full_recompute_louvain_cachedJ": e[:3],
                             "null_R20_louvain": (None, statistics.median(ln), p95(ln))}
    results["mmf"] = mmf
    print("\nMMF:", json.dumps(mmf, indent=1))
    results["layout"] = {k: v[:3] for k, v in lay.items()}
    (HERE / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print(f"\nwrote {HERE / 'results.json'}; wall {time.perf_counter() - T_START:.1f}s")


if __name__ == "__main__":
    main()
