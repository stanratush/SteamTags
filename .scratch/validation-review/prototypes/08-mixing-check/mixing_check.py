"""One-off: does the Curveball null mix by TRADES_PER_GAME = 10 at the validated Threshold Pairs?

Ticket: .scratch/validation-review/issues/08-mixing-check-at-validated-pairs.md. Rewrites the lost `mixing_check.py`
of Research 02 §A.4 (.scratch/auto-parameter-selection/research/02-validation-methods.md) with the same design:

- per pair, CHAINS independent chains from the observed game × visible-tag table (the pair's network tags, as
  `validation.shuffled_games` restricts it), run with the project's `curveball()`;
- chain r uses `random.Random(1000 + r)` throughout, Leiden uses seed 7 + r;
- statistics at cumulative checkpoints of 0.25 … 200 trades per game, the 200 checkpoint being the reference;
- perturbation share, mean Stone–Roberts C-score, edge count at s, Q and Multi-Tag Clusters of Leiden on Lift at
  γ = 1, and the memory slope. Added here: Q at the pair's observed Selected Resolution γ_obs (read from the stored
  validation, when there is one), the γ the Null Comparison's fixed-γ arm uses.

Each statistic but memory is reported as (mean at T − reference mean) / reference SD. Memory is the least-squares
slope of (chain-mean shared count per tag pair at T − reference mean) on (observed − reference mean); both have
mean 0 over the pairs, because Curveball keeps every game's tag count and so the total of the shared counts.

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/08-mixing-check/mixing_check.py \
        --build builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f \
        --pairs rpg:7:5 puzzle:12:2 puzzle:14:2 puzzle:11:5 overall:12:2 overall:17:2 strategy:14:2 simulation:14:5

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/08-mixing-check/mixing_check.py --report

Run from the repo root. Writes results.json next to this file (`--out` to change) and the report beside it as results.md.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
CHECKPOINTS = (0.25, 0.5, 1, 2, 3, 5, 10, 20, 50, 100, 200)
REFERENCE = 200
CHAINS = 100
BAND = 0.3  # |z| ≤ 0.3 ≈ 2 SE of a difference of two 100-chain means (Research 02 §A.4)
WOBBLE = 0.42  # 3 SE: a later excursion beyond this counts as drift, not chance
STATS = ("perturbation", "c_score", "edges", "q_1", "n_multi_1", "q_obs")


# ----------------------------------------------------------------------------- one pair


def load_pair(build: str, dataset: str, g: int, s: int) -> dict:
    from steamstudy.app.loader import load_build
    from steamstudy.network import selection as SEL
    from steamstudy.network.graph import build_network, filter_games

    ctx = load_build(Path(build))
    sel = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    context = ctx.context(dataset)
    settings = sel.for_pair(dataset, context, g, s)
    games = filter_games(ctx.games(dataset), settings.min_months)
    nodes = build_network(games, settings, context).nodes
    # γ_obs from a stored validation of this pair. The exact key first; else any stored validation whose network
    # settings match (a selection-only field such as min_multi_tag_clusters may differ, the table does not).
    key = sel.validation_key(dataset, context, g, s)
    folder = ctx.app_cache / "parameter_selection" / "validation"
    exact = folder / f"{SEL.key_hash(key)}.json"
    network_fields = ("build_id", "dataset", "hidden_tag_ids", "removed_tag_ids", "min_months", "clustering_weight")
    candidates = [exact] if exact.is_file() else sorted(folder.glob("*.json")) if folder.is_dir() else []
    gamma_obs, found = None, None
    for path in candidates:
        stored = json.loads(path.read_text(encoding="utf-8"))
        k = stored["validation_key"]
        if (k["g"], k["s"]) == (g, s) and all(k["grid_key"][f] == key["grid_key"][f] for f in network_fields):
            gamma_obs = stored["summary"]["null"]["resolution"]["observed"]
            found = path.name if path == exact else f"{path.name} (network settings match, key differs)"
            break
    return {"games": games, "nodes": nodes, "settings": settings, "gamma_obs": gamma_obs,
            "validation_file": found, "build_id": ctx.build_id}


def chain(args: tuple) -> dict:
    """One chain: the statistics at every checkpoint, plus the shared count per tag pair."""
    from steamstudy.network.cluster import detect, label_clusters
    from steamstudy.network.graph import shared_edges, to_graph
    from steamstudy.network.metrics import modularity
    from steamstudy.network.stability import curveball

    build, dataset, g, s, r = args
    pair = _PAIR_CACHE.get((build, dataset, g, s))
    if pair is None:
        pair = _PAIR_CACHE[(build, dataset, g, s)] = load_pair(build, dataset, g, s)
    games, nodes, settings, gamma_obs = pair["games"], pair["nodes"], pair["settings"], pair["gamma_obs"]
    names = {t: n for gm in games for t, n in zip(gm.tag_ids, gm.tags)}
    col = {t: i for i, t in enumerate(nodes)}
    visible = set(nodes)
    rows = [frozenset(t for t in gm.tag_ids if t in visible) for gm in games]
    n = len(rows)
    iu = np.triu_indices(len(nodes), 1)

    def matrix(table: list[frozenset[int]]) -> np.ndarray:
        b = np.zeros((n, len(nodes)), dtype=np.int64)
        for i, row in enumerate(table):
            for t in row:
                b[i, col[t]] = 1
        return b

    b0 = matrix(rows)
    rng = random.Random(1000 + r)
    table, done = rows, 0
    out: dict = {"stats": {}, "shared": {}}
    for cp in CHECKPOINTS:
        target = round(cp * n)
        table = curveball(table, target - done, rng)
        done = target
        b = matrix(table)
        shared = (b.T @ b)[iu]
        deg = b.sum(axis=0)
        c_score = float(np.mean((deg[iu[0]] - shared) * (deg[iu[1]] - shared)))
        fake = [replace(gm, tag_ids=tuple(sorted(row)), tags=tuple(names[t] for t in sorted(row)))
                for gm, row in zip(games, table)]
        tag_games = {t: frozenset(gm.appid for gm in fake if t in gm.tag_ids) for t in nodes}
        edges = shared_edges(fake, nodes, tag_games, settings.min_shared_games)
        graph = to_graph(nodes, edges, settings.clustering_weight)
        stats = {"perturbation": 1.0 - float((b & b0).sum()) / float(b0.sum()), "c_score": c_score,
                 "edges": len(edges)}
        for tag, gamma in (("1", 1.0), ("obs", gamma_obs)):
            if gamma is None or not edges:
                stats[f"q_{tag}"] = None
                if tag == "1":
                    stats["n_multi_1"] = None
                continue
            clusters = label_clusters(detect(graph, settings.algorithm, gamma, 7 + r))
            stats[f"q_{tag}"] = modularity(graph, clusters, gamma)
            if tag == "1":
                stats["n_multi_1"] = sum(1 for c in clusters if c.size >= 2)
        out["stats"][str(cp)] = stats
        out["shared"][str(cp)] = shared.tolist()
    if r == 0:
        out["observed_shared"] = ((b0.T @ b0)[iu]).tolist()
    return out


_PAIR_CACHE: dict = {}


def run(build: str, pairs: list[tuple[str, int, int]], workers: int, chains: int) -> dict:
    jobs = [(build, d, g, s, r) for d, g, s in pairs for r in range(chains)]
    t0 = time.perf_counter()
    with Pool(workers) as pool:
        results = pool.map(chain, jobs, chunksize=max(1, chains // 4))
    seconds = time.perf_counter() - t0
    out = {"build": build, "chains": chains, "checkpoints": CHECKPOINTS, "seconds": seconds, "pairs": {}}
    for k, (d, g, s) in enumerate(pairs):
        info = load_pair(build, d, g, s)
        block = results[k * chains:(k + 1) * chains]
        out["build_id"] = info["build_id"]
        out["pairs"][f"{d} {g}/{s}"] = {
            "dataset": d, "g": g, "s": s, "n_games": len(info["games"]), "n_tags": len(info["nodes"]),
            "row_sums": sorted(len([t for t in gm.tag_ids if t in set(info["nodes"])]) for gm in info["games"]),
            "gamma_obs": info["gamma_obs"], "validation_file": info["validation_file"],
            "observed_shared": block[0]["observed_shared"],
            "stats": [c["stats"] for c in block],
            "shared": {cp: np.mean([c["shared"][cp] for c in block], axis=0).tolist() for cp in block[0]["shared"]},
            "shared_var": {cp: np.var([c["shared"][cp] for c in block], axis=0, ddof=1).tolist()
                           for cp in block[0]["shared"]},
        }
    return out


# ----------------------------------------------------------------------------- report


def summarise(pair: dict, chains: int) -> dict:
    ref = str(REFERENCE)
    table: dict[str, dict[str, float | None]] = {}
    for name in STATS:
        vals = {cp: [c[cp][name] for c in pair["stats"] if c[cp][name] is not None] for cp in pair["stats"][0]}
        if len(vals[ref]) < 2:
            continue
        mu, sd = statistics.fmean(vals[ref]), statistics.stdev(vals[ref])
        table[name] = {cp: (statistics.fmean(v) - mu) / sd if sd > 0 and v else None for cp, v in vals.items()}
    x = np.array(pair["observed_shared"], float) - np.array(pair["shared"][ref])
    xx = float(x @ x)
    # x and y both subtract the same reference mean, so at a mixed T the slope's expectation is not 0 but
    # Σ var(reference mean) / Σ x²: the floor (Research 02's "noise floor ≈ 0.005").
    floor = float(np.sum(pair["shared_var"][ref])) / chains / xx
    memory, memory_se = {}, {}
    for cp, mean in pair["shared"].items():
        y = np.array(mean) - np.array(pair["shared"][ref])
        memory[cp] = float(x @ y) / xx
        var = (np.array(pair["shared_var"][cp]) + np.array(pair["shared_var"][ref])) / chains
        memory_se[cp] = math.sqrt(float((x * x) @ var)) / xx
    table["memory"] = memory
    within = {}
    for cp in pair["stats"][0]:
        if cp == ref:
            continue
        z_ok = all(abs(table[k][cp]) <= BAND for k in table if k != "memory" and table[k][cp] is not None)
        within[cp] = z_ok and memory[cp] <= floor + 2 * memory_se[cp]
    cps = [cp for cp in pair["stats"][0] if cp != ref]
    first = next((cp for cp in cps if within[cp]), None)
    later = [cp for cp in cps if first is not None and float(cp) > float(first)]
    drift = [(k, cp, table[k][cp]) for cp in later for k in table
             if k != "memory" and table[k][cp] is not None and abs(table[k][cp]) > WOBBLE]
    drift += [("memory", cp, memory[cp]) for cp in later if memory[cp] > floor + 3 * memory_se[cp]]
    wobble = [(k, cp, table[k][cp]) for cp in later for k in table
              if k != "memory" and table[k][cp] is not None and BAND < abs(table[k][cp]) <= WOBBLE]
    return {"table": table, "memory_se": memory_se, "floor": floor, "within": within, "first": first, "drift": drift,
            "wobble": wobble}


def report(results: dict) -> str:
    lines = [f"Build {results['build_id']}, {results['chains']} chains per pair, "
             f"{results['seconds']:.0f} s wall time.", ""]
    shown = ("0.25", "1", "2", "3", "5", "10", "20", "50", "100")
    summary_rows = []
    for label, pair in results["pairs"].items():
        s = summarise(pair, results["chains"])
        rs = pair["row_sums"]
        g_obs = f"{pair['gamma_obs']:.3f}" if pair["gamma_obs"] is not None else "none"
        lines.append(f"## {label} ({pair['n_tags']} tags, {pair['n_games']} games; visible row sums "
                     f"{rs[0]}/{statistics.median(rs):g}/{rs[-1]}; γ_obs {g_obs}; validation {pair['validation_file']})")
        lines.append("")
        lines.append("| Statistic | " + " | ".join(f"T = {c}" for c in shown) + " |")
        lines.append("|---|" + "---|" * len(shown))
        for name, row in s["table"].items():
            fmt = "{:.3f}" if name == "memory" else "{:+.2f}"
            lines.append(f"| {name} | " + " | ".join("–" if row.get(c) is None else fmt.format(row[c]) for c in shown)
                         + " |")
        lines.append("| memory floor + 2 SE | " + " | ".join(f"{s['floor'] + 2 * s['memory_se'][c]:.3f}" for c in shown)
                     + " |")
        lines.append("")
        lines.append(f"First checkpoint with every statistic within noise: T = {s['first']}. "
                     f"Later excursions beyond 3 SE: {s['drift'] or 'none'}. "
                     f"Later 2–3 SE wobbles: {[(k, c, round(v, 2)) for k, c, v in s['wobble']] or 'none'}.")
        lines.append("")
        summary_rows.append((label, s["first"], bool(s["drift"]), len(s["wobble"])))
    lines.append("## Summary")
    lines.append("")
    lines.append("| Pair | Within noise from T = | Plateaued by T = 10? | Later 2–3 SE wobbles |")
    lines.append("|---|---|---|---|")
    for label, first, drift, wob in summary_rows:
        ok = first is not None and float(first) <= 10 and not drift
        lines.append(f"| {label} | {first} | {'yes' if ok else 'NO'} | {wob} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", help="the Build folder")
    ap.add_argument("--pairs", nargs="*", default=[], help="dataset:g:s")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--chains", type=int, default=CHAINS)
    ap.add_argument("--out", default=str(HERE / "results.json"))
    ap.add_argument("--report", action="store_true", help="only print the report of an existing --out")
    args = ap.parse_args()
    if not args.report:
        pairs = [(p.split(":")[0], int(p.split(":")[1]), int(p.split(":")[2])) for p in args.pairs]
        Path(args.out).write_text(json.dumps(run(args.build, pairs, args.workers, args.chains)), encoding="utf-8")
    text = report(json.loads(Path(args.out).read_text(encoding="utf-8")))
    Path(args.out).with_suffix(".md").write_text(text + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
