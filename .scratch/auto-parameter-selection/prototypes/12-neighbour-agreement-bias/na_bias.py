"""Throwaway: does Neighbour Agreement favour high g? (ticket 12)

Reads the raw per-dataset JSON written by ../05-grid-run/grid_run.py (memberships, links) and rebuilds each
pair's edge set with build_network (no clustering, no new grid run). Not production code; nothing imports it.

    .venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/12-neighbour-agreement-bias/na_bias.py \
        --runs <scratchpad>/runs05/parallel --out .scratch/auto-parameter-selection/prototypes/12-neighbour-agreement-bias
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import adjusted_rand_score

BUILD = Path("builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f")
DATASETS = ("overall", "puzzle", "rpg", "simulation", "strategy")
BANDS = ((3, 6), (7, 10), (11, 14), (15, 20))
N_PERM = 200
RNG = np.random.default_rng(12)


def band(g: int) -> str:
    for lo, hi in BANDS:
        if lo <= g <= hi:
            return f"{lo}–{hi}"
    raise ValueError(g)


def fmt(x, nd=3):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


# ----------------------------------------------------------------------------- inputs


def edge_sets(dataset: str) -> dict[tuple[int, int], set[tuple[str, str]]]:
    from steamstudy.app.loader import load_build
    from steamstudy.network.graph import build_network

    ctx = load_build(BUILD)
    base = ctx.default_settings(dataset).with_(clustering_weight="lift", algorithm="leiden", min_months=0)
    games, context = ctx.games(dataset), ctx.context(dataset)
    out = {}
    for g in range(3, 21):
        for s in range(2, min(g, 12) + 1):
            net = build_network(games, base.with_(min_games_per_tag=g, min_shared_games=s), context)
            out[(g, s)] = {tuple(sorted((e.u, e.v))) for e in net.edges}
    return out


def link_details(records, links, edges):
    """Every link with direction, graph change, and the yardstick checks."""
    out = []
    for x in links:
        p, q = tuple(x["p"]), tuple(x["q"])
        a, b = records[p], records[q]
        ea, eb = edges[p], edges[q]
        union = ea | eb
        d = {"p": p, "q": q, "g": p[0], "dir": "g" if q[0] != p[0] else "s", "ari": x["ari"],
             "status": x["status"], "identical": x["identical_graph"], "tag_jaccard": x["jaccard"],
             "edge_jaccard": len(ea & eb) / len(union) if union else 1.0, "n_compared": x["n_compared"]}
        if x["status"] == "ok":
            ia, ib = {t: i for i, t in enumerate(a["nodes"])}, {t: i for i, t in enumerate(b["nodes"])}
            shared = sorted(set(a["nodes"]) & set(b["nodes"]))
            compared = [t for t in shared if t in set(a["edged"]) or t in set(b["edged"])]
            la = np.array([a["selected"]["membership"][ia[t]] for t in compared])
            lb = np.array([b["selected"]["membership"][ib[t]] for t in compared])
            # chance baseline: neighbour's labels permuted over the compared tags (cluster sizes kept)
            perm = [adjusted_rand_score(la, RNG.permutation(lb)) for _ in range(N_PERM)]
            d["perm_mean"], d["perm_p99"] = float(np.mean(perm)), float(np.quantile(perm, 0.99))
            d["n_clusters_compared"] = len(set(la.tolist()))
            out.append(d)
        else:
            out.append(d)
    return out


def one_move_drop(rec) -> float | None:
    """Mean ARI after moving one random edged tag to another existing cluster: the yardstick's resolution."""
    sel = rec["selected"]
    if sel is None:
        return None
    m = np.array(sel["membership"])
    edged = [i for i, t in enumerate(rec["nodes"]) if t in set(rec["edged"])]
    m = m[edged]
    k = m.max() + 1
    if k < 2:
        return None
    vals = []
    for _ in range(N_PERM):
        m2 = m.copy()
        i = RNG.integers(len(m2))
        m2[i] = RNG.choice([c for c in range(k) if c != m2[i]])
        vals.append(adjusted_rand_score(m, m2))
    return 1 - float(np.mean(vals))


# ----------------------------------------------------------------------------- selection under variants


def qualifies(r) -> bool:
    na = r["neighbour_agreement"]
    if r["selected"] is None or na["status"] != "ok":
        return False
    diff = na["n_comparable"] - na["n_identical_comparable"]
    return (r["retention"] >= 0.50 and r["isolated_share"] <= 0.10
            and r["lcc_share_non_isolated"] >= 0.90 and diff >= 2)


def choose(records, score) -> tuple | None:
    q = {k: score[k] for k, r in records.items() if qualifies(r) and score.get(k) is not None}
    if not q:
        return None
    top = max(q.values())
    near = [k for k, v in q.items() if v >= top - 0.05 - 1e-12]
    return min(near), len(near), top


def variant_scores(records, lds):
    by = {k: [d for d in lds if d["status"] == "ok" and k in (d["p"], d["q"])] for k in records}

    def from_links(pred):
        return {k: mean([d["ari"] for d in ls if pred(d)]) for k, ls in by.items()}

    # graph-change adjusted: residual of link ARI against 1 − edge Jaccard (pooled OLS over the dataset)
    ok = [d for d in lds if d["status"] == "ok"]
    x = np.array([1 - d["edge_jaccard"] for d in ok])
    y = np.array([d["ari"] for d in ok])
    slope, icpt = np.polyfit(x, y, 1)
    for d in ok:
        d["resid"] = d["ari"] - (icpt + slope * (1 - d["edge_jaccard"]))
    resid = {k: mean([d["resid"] for d in ls]) for k, ls in by.items()}

    decided = {k: r["neighbour_agreement"]["mean"] for k, r in records.items()}
    # per-g normalisation: NA minus the median NA of its g column (all pairs with NA)
    col = {}
    for (g, s), v in decided.items():
        if v is not None:
            col.setdefault(g, []).append(v)
    per_g = {k: (v - statistics.median(col[k[0]]) if v is not None else None) for k, v in decided.items()}
    return {
        "as decided": decided,
        "without identical-graph links": from_links(lambda d: not d["identical"]),
        "s-links only": from_links(lambda d: d["dir"] == "s"),
        "g-links only": from_links(lambda d: d["dir"] == "g"),
        "graph-change residual": resid,
        "per-g normalised (NA − column median)": per_g,
    }, (slope, icpt)


# ----------------------------------------------------------------------------- report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lines = ["# Does Neighbour Agreement favour high g? Checks over the ticket 05 grid run", "",
             f"Build `{BUILD.name}`, default fixed settings, raw records from the ticket 05 run. "
             f"Permutation baselines use {N_PERM} draws (seed 12). Generated by `na_bias.py`.", ""]
    summary = {}
    for ds in DATASETS:
        doc = json.loads((Path(args.runs) / f"{ds}.json").read_text(encoding="utf-8"))
        records = {(r["g"], r["s"]): r for r in doc["records"]}
        edges = edge_sets(ds)
        lds = link_details(records, doc["links"], edges)
        with_na = [r for r in records.values() if r["neighbour_agreement"]["status"] == "ok"]
        na = np.array([r["neighbour_agreement"]["mean"] for r in with_na])
        rho = {k: spearmanr(na, [f(r) for r in with_na]).statistic for k, f in
               (("g", lambda r: r["g"]), ("s", lambda r: r["s"]), ("tags", lambda r: r["n_tags"]),
                ("edged tags", lambda r: len(r["edged"])), ("Multi-Tag Clusters", lambda r: r["selected"]["n_multi"]))}
        lines += [f"## {ds}", "", "**Spearman ρ of NA with**: " +
                  ", ".join(f"{k} {v:+.2f}" for k, v in rho.items()) + f" (n = {len(with_na)})", ""]

        lines += ["| g band | pairs | mean NA | mean edged tags | mean Multi-Tag Clusters | at the 3-Cluster minimum | "
                  "one-tag-move ARI cost |", "|---|---:|---:|---:|---:|---:|---:|"]
        for lo, hi in BANDS:
            rs = [r for r in with_na if lo <= r["g"] <= hi]
            lines.append(f"| {lo}–{hi} | {len(rs)} | {fmt(mean([r['neighbour_agreement']['mean'] for r in rs]))} | "
                         f"{fmt(mean([len(r['edged']) for r in rs]), 1)} | "
                         f"{fmt(mean([r['selected']['n_multi'] for r in rs]), 1)} | "
                         f"{sum(r['selected']['n_multi'] == 3 for r in rs)} | "
                         f"{fmt(mean([one_move_drop(r) for r in rs]))} |")
        lines.append("")

        ok = [d for d in lds if d["status"] == "ok"]
        lines += ["| g band | direction | links | identical graph | mean tag Jaccard | mean edge Jaccard | "
                  "mean ARI | mean ARI, non-identical | chance ARI (mean / p99) |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---|"]
        for lo, hi in BANDS:
            for dr in ("g", "s"):
                ls = [d for d in ok if lo <= d["g"] <= hi and d["dir"] == dr]
                if not ls:
                    continue
                ni = [d["ari"] for d in ls if not d["identical"]]
                lines.append(f"| {lo}–{hi} | {dr} | {len(ls)} | {sum(d['identical'] for d in ls)} | "
                             f"{fmt(mean([d['tag_jaccard'] for d in ls]))} | {fmt(mean([d['edge_jaccard'] for d in ls]))} | "
                             f"{fmt(mean([d['ari'] for d in ls]))} | {fmt(mean(ni))} | "
                             f"{fmt(mean([d['perm_mean'] for d in ls]))} / {fmt(max(d['perm_p99'] for d in ls))} |")
        lines.append("")

        # matched graph change: ARI by g band within edge-Jaccard bins (non-identical links)
        ni = [d for d in ok if not d["identical"]]
        cuts = np.quantile([d["edge_jaccard"] for d in ni], [0.25, 0.5, 0.75])
        bins = [(0.0, cuts[0]), (cuts[0], cuts[1]), (cuts[1], cuts[2]), (cuts[2], 1.0001)]
        lines += ["Mean link ARI at matched graph change (non-identical links, edge-Jaccard quartiles; links in cell):", "",
                  "| edge Jaccard | " + " | ".join(f"g {lo}–{hi}" for lo, hi in BANDS) + " |",
                  "|---|" + "---:|" * len(BANDS)]
        for blo, bhi in bins:
            cells = []
            for lo, hi in BANDS:
                ls = [d["ari"] for d in ni if blo <= d["edge_jaccard"] < bhi and lo <= d["g"] <= hi]
                cells.append(f"{fmt(mean(ls))} ({len(ls)})" if ls else "–")
            lines.append(f"| {blo:.2f}–{min(bhi, 1):.2f} | " + " | ".join(cells) + " |")
        rho_ej = spearmanr([d["edge_jaccard"] for d in ni], [d["ari"] for d in ni]).statistic
        rho_g = spearmanr([d["g"] for d in ni], [d["ari"] for d in ni]).statistic
        lines += ["", f"Link level (non-identical): ρ(ARI, edge Jaccard) {rho_ej:+.2f}, ρ(ARI, g) {rho_g:+.2f}, "
                  f"ρ(edge Jaccard, g) {spearmanr([d['g'] for d in ni], [d['edge_jaccard'] for d in ni]).statistic:+.2f}.", ""]

        variants, (slope, icpt) = variant_scores(records, lds)
        lines += [f"Chosen pair under default constraints, by NA variant (residual fit: ARI ≈ {icpt:.3f} + "
                  f"{slope:.3f}·(1 − edge Jaccard)):", "",
                  "| NA variant | chosen (g, s) | near-best set | max | Multi-Tag Clusters | edged tags |", "|---|---|---:|---:|---:|---:|"]
        for name, sc in variants.items():
            c = choose(records, sc)
            if c is None:
                lines.append(f"| {name} | none | – | – | – | – |")
                continue
            k, n, top = c
            r = records[k]
            lines.append(f"| {name} | g={k[0]}, s={k[1]} | {n} | {fmt(top)} | {r['selected']['n_multi']} | {len(r['edged'])} |")
            summary.setdefault(name, {})[ds] = k
        lines.append("")
        print(ds, "done", flush=True)

    lines += ["## Chosen pair by variant, all datasets", "",
              "| NA variant | " + " | ".join(DATASETS) + " |", "|---|" + "---|" * len(DATASETS)]
    for name, by in summary.items():
        lines.append(f"| {name} | " + " | ".join(f"{by[d][0]},{by[d][1]}" if d in by else "none" for d in DATASETS) + " |")
    Path(args.out, "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
