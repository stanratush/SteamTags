"""One-off: how much does the s′ = max(2, ⌊0.8 s⌋) clamp move Subsample Stability at s = 2?

Ticket: .scratch/validation-review/issues/09-threshold-clamp-bracket.md. At s = 2 the proportional threshold is
0.8 × 2 = 1.6, which no integer threshold matches; the clamp takes s′ = 2 (stricter). This brackets it with s′ = 1
(looser): every stored s = 2 validation's 100 subsamples are rerun under both, from the stored subsample seeds, so
the two are paired (the same games drawn, the same g′, only the edge threshold differs).

Each subsample runs the app's own procedure (`validation._procedure`: the γ scan, CHAMP, the Selected Partition
rule) for both arms, re-selected and at the observed Selected Resolution. Per Multi-Tag Cluster it scores the
figures decided in tickets 01 and 02, which the app does not compute yet:

- Hennig's Jaccard on the surviving tags C′, assessable when |C′| ≥ 2 (B* = the assessable subsamples);
- Whole-Cluster Jaccard max_D |C ∩ D′| / |C ∪ D′|, 0 when C is absent, over the non-degenerate subsamples;
- the dissolution (J ≤ 0.5) and good-recovery (J > 0.75) frequencies of Hennig's Jaccard, k of B*, with 95% Wilson;
- the status: Not assessable (B* = 0), Dissolved in most subsamples (J ≤ 0.5 in more than half of B*), borderline
  (the dissolution Wilson interval contains ½).

The s′ = 2 run doubles as a determinism check: its Hennig's Jaccard must equal the stored records' wherever both are
scored (the stored code also scored |C′| = 1).

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/09-clamp-bracket/clamp_bracket.py \
        --build builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f \
        --pairs puzzle:12:2 puzzle:14:2 overall:12:2 overall:17:2 strategy:14:2

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/09-clamp-bracket/clamp_bracket.py --report

Every stored validation of a listed pair is run (puzzle 14/2 has two, at min_multi_tag_clusters 2 and 3). Run from the
repo root. Writes results.json next to this file (`--out` to change) and the report beside it as results.md.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from collections import Counter
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
S_PRIMES = (2, 1)  # the clamp, then the looser bracket
ARMS = ("reselected", "at_resolution")
DISSOLVED, RECOVERED = 0.5, 0.75
Z = 1.959963984540054


# ----------------------------------------------------------------------------- one stored validation


def stored_runs(build: str, pairs: list[tuple[str, int, int]]) -> list[Path]:
    folder = Path(build) / "app_cache" / "parameter_selection" / "validation"
    out = []
    for path in sorted(folder.glob("*.json")):
        k = json.loads(path.read_text(encoding="utf-8"))["validation_key"]
        if (k["grid_key"]["dataset"], k["g"], k["s"]) in pairs:
            out.append(path)
    return out


def prepare(build: str, path: str) -> dict:
    """The stored run's tasks, rebuilt as the app built them, with every input checked against what was stored."""
    from steamstudy.app import ps_cache
    from steamstudy.app.loader import load_build
    from steamstudy.network import selection as SEL
    from steamstudy.network import validation as V

    stored = json.loads(Path(path).read_text(encoding="utf-8"))
    vkey = stored["validation_key"]
    gk = vkey["grid_key"]
    dataset, g, s = gk["dataset"], vkey["g"], vkey["s"]
    ctx = load_build(Path(build))
    context = ctx.context(dataset)
    sel = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    sel = sel.with_(min_multi_tag_clusters=gk["min_multi_tag_clusters"])
    if sel.grid_key(dataset, context) != gk:
        diff = {f: (gk.get(f), v) for f, v in sel.grid_key(dataset, context).items() if gk.get(f) != v}
        raise SystemExit(f"{Path(path).name}: the Build's defaults do not rebuild its grid key: {diff}")
    # This Build's cache predates "Short Parameter Selection cache names" (9aa40e6): its folders and files carry the
    # full 64-hex key hash, so read it at that length (a newer cache is found at either length).
    if not ps_cache.grid_dir(ctx.app_cache, gk).exists():
        ps_cache.NAME_LENGTH = 64
    loaded = ps_cache.load_grid(ctx.app_cache, gk, dataset)
    if loaded is None:
        raise SystemExit(f"{Path(path).name}: no complete grid cached for {dataset}")
    observed = loaded[0].at(g, s)
    tasks = [t for t in V.validation_tasks(ctx.games(dataset), sel, dataset, context, g, s, observed,
                                           SEL.selection_seeds(sel)) if t.kind == "subsample"]
    stored_subs = [r for r in stored["records"] if r["kind"] == "subsample"]
    if [t.seed for t in tasks] != [r["seed"] for r in stored_subs]:
        raise SystemExit(f"{Path(path).name}: subsample seeds differ from the stored records")
    obs = tasks[0].observed
    if [c["members"] for c in stored["summary"]["subsample"]["reselected"]["clusters"]] != obs.clusters:
        raise SystemExit(f"{Path(path).name}: the observed Multi-Tag Clusters differ from the stored ones")
    return {"dataset": dataset, "g": g, "s": s, "min_multi": gk["min_multi_tag_clusters"], "tasks": tasks,
            "stored": stored_subs, "file": Path(path).name}


def compare(obs, nodes: list[int], edged: list[int], labels: list[int] | None) -> dict:
    """As `validation.compare`, plus |C′| and Whole-Cluster Jaccard; Hennig's Jaccard only when |C′| ≥ 2."""
    if labels is None:
        return {"ari": None, "hennig": None, "whole": None, "surviving": None, "hennig_1": None}
    from sklearn.metrics import adjusted_rand_score

    present = set(nodes)
    any_edge = set(obs.edged) | set(edged)
    comparison = [t for t in obs.nodes if t in present and t in any_edge]
    keep = set(comparison)
    mine = dict(zip(obs.nodes, obs.selected))
    theirs = dict(zip(nodes, labels))
    ari = (float(adjusted_rand_score([mine[t] for t in comparison], [theirs[t] for t in comparison]))
           if comparison else None)
    groups: dict[int, set[int]] = {}
    for t in comparison:
        groups.setdefault(theirs[t], set()).add(t)
    hennig, hennig_1, whole, surviving = [], [], [], []
    for cluster in obs.clusters:
        c = set(cluster)
        restricted = c & keep
        surviving.append(len(restricted))
        h = max(len(restricted & d) / len(restricted | d) for d in groups.values()) if restricted else None
        hennig_1.append(h)  # the stored code's rule (|C′| ≥ 1), for the determinism check
        hennig.append(h if len(restricted) >= 2 else None)
        whole.append(max(len(c & d) / len(c | d) for d in groups.values()) if restricted else 0.0)
    return {"ari": ari, "hennig": hennig, "whole": whole, "surviving": surviving, "hennig_1": hennig_1}


_PREPARED: dict = {}


def subsample(args: tuple) -> dict:
    """One stored subsample, rerun at threshold s′ (g′ as the app's clamp rule gives it)."""
    import random

    from steamstudy.network import validation as V
    from steamstudy.network.graph import filter_games

    build, path, index, s_prime = args
    prep = _PREPARED.get(path)
    if prep is None:
        prep = _PREPARED[path] = prepare(build, path)
    task = prep["tasks"][index]
    obs = task.observed
    games = filter_games(task.games, task.settings.min_months)
    rng = random.Random(task.seed)
    m, g2, s_clamp = V.subsample_thresholds(task.settings.min_games_per_tag, task.settings.min_shared_games, len(games))
    sample = sorted(rng.sample(games, m), key=lambda gm: gm.rank)
    settings = task.settings.with_(min_games_per_tag=g2, min_shared_games=s_prime)
    t0 = time.perf_counter()
    run = V._procedure(sample, settings, task.context, task)
    result = run["champ"]
    arms = {}
    if result is None:
        for arm in ARMS:
            arms[arm] = {"degenerate": "no_edges", **compare(obs, run["nodes"], run["edged"], None)}
    else:
        chosen = result.selected_partition
        arms["reselected"] = {"degenerate": None if chosen is not None else result.reason,
                              **compare(obs, run["nodes"], run["edged"],
                                        None if chosen is None else list(chosen.membership)),
                              "resolution": None if chosen is None else chosen.midpoint}
        top = V.envelope_partition(result, obs.resolution)
        arms["at_resolution"] = {"degenerate": None, **compare(obs, run["nodes"], run["edged"], list(top.membership))}
    return {"path": path, "index": task.index, "seed": task.seed, "s_prime": s_prime, "s_clamp": s_clamp, "m": m,
            "g": g2, "n_edges": run["n_edges"], "n_nodes": len(run["nodes"]), "scan_length": run["scan_length"],
            "seconds": time.perf_counter() - t0, "arms": arms}


def run(build: str, paths: list[Path], workers: int) -> dict:
    preps = {str(p): prepare(build, str(p)) for p in paths}
    jobs = [(build, str(p), i, sp) for p in paths for sp in S_PRIMES for i in range(len(preps[str(p)]["tasks"]))]
    t0 = time.perf_counter()
    with Pool(workers) as pool:
        results = pool.map(subsample, jobs, chunksize=5)
    out = {"build": build, "seconds": time.perf_counter() - t0, "runs": {}}
    for p, prep in preps.items():
        obs = prep["tasks"][0].observed
        mine = [r for r in results if r["path"] == p]
        # determinism: the s′ = 2 rerun against the stored records, on every Cluster both scored
        checked = mismatched = 0
        for rec in (r for r in mine if r["s_prime"] == 2):
            stored = prep["stored"][rec["index"] - 1]
            for arm in ARMS:
                for a, b in zip(rec["arms"][arm]["hennig_1"] or [], stored["arms"][arm]["jaccard"]):
                    if a is None and b is None:
                        continue
                    checked += 1
                    mismatched += a is None or b is None or abs(a - b) > 1e-12
        name = f"{prep['dataset']} {prep['g']}/{prep['s']} (min multi {prep['min_multi']})"
        out["runs"][name] = {
            "file": prep["file"], "dataset": prep["dataset"], "g": prep["g"], "s": prep["s"],
            "min_multi": prep["min_multi"], "resolution": obs.resolution, "labels": obs.labels,
            "sizes": [len(c) for c in obs.clusters], "observed_edges": obs.n_edges,
            "determinism": {"checked": checked, "mismatched": mismatched},
            "records": sorted(mine, key=lambda r: (r["s_prime"], r["index"])),
        }
    return out


# ----------------------------------------------------------------------------- report


def wilson(k: int, n: int) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return centre - half, centre + half


def cluster_figures(records: list[dict], arm: str, i: int) -> dict:
    good = [r["arms"][arm] for r in records if r["arms"][arm]["degenerate"] is None]
    h = [x["hennig"][i] for x in good if x["hennig"][i] is not None]
    w = [x["whole"][i] for x in good]
    b = len(h)
    k_d, k_r = sum(v <= DISSOLVED for v in h), sum(v > RECOVERED for v in h)
    ci = wilson(k_d, b)
    if b == 0:
        status = "not assessable"
    elif k_d > b / 2:
        status = "dissolved"
    else:
        status = "-"
    return {"n_good": len(good), "b_star": b, "mean_h": statistics.fmean(h) if h else None,
            "se_h": statistics.stdev(h) / math.sqrt(b) if b > 1 else None,
            "mean_w": statistics.fmean(w) if w else None, "k_dissolved": k_d, "k_recovered": k_r,
            "dissolution_ci": ci, "recovery_ci": wilson(k_r, b), "status": status,
            "borderline": ci is not None and ci[0] <= 0.5 <= ci[1], "rare": b < len(good) / 2}


def report(data: dict) -> str:
    lines = [f"# 09 Threshold clamp bracket at s = 2: results", "",
             f"Build `{Path(data['build']).name}`, {sum(len(r['records']) for r in data['runs'].values())} subsample "
             f"runs in {data['seconds']:.0f} s.", ""]
    moved = total = 0
    summary_rows = []
    for name, run_ in data["runs"].items():
        by = {sp: [r for r in run_["records"] if r["s_prime"] == sp] for sp in S_PRIMES}
        det = run_["determinism"]
        e2 = statistics.median(r["n_edges"] for r in by[2])
        e1 = statistics.median(r["n_edges"] for r in by[1])
        lines += [f"## {name}", "",
                  f"γ_obs = {run_['resolution']:.3f}; observed network {run_['observed_edges']} edges; median subsample "
                  f"network {e2:.0f} edges at s′ = 2, {e1:.0f} at s′ = 1 (g′ = {by[2][0]['g']}, m = {by[2][0]['m']}). "
                  f"Determinism: {det['checked'] - det['mismatched']} of {det['checked']} stored Hennig's Jaccard "
                  f"values reproduced at s′ = 2.", ""]
        for arm in ARMS:
            deg = {sp: Counter(r["arms"][arm]["degenerate"] for r in by[sp] if r["arms"][arm]["degenerate"]) for sp in S_PRIMES}
            aris = {sp: [r["arms"][arm]["ari"] for r in by[sp] if r["arms"][arm]["ari"] is not None] for sp in S_PRIMES}
            lines += [f"**{arm.replace('_', ' ')}** — degenerate: s′ = 2 {sum(deg[2].values())}, s′ = 1 "
                      f"{sum(deg[1].values())}; median ARI {statistics.median(aris[2]):.3f} → "
                      f"{statistics.median(aris[1]):.3f}", "",
                      "| Cluster | size | B* (2 → 1) | mean Hennig's J (2 → 1) | mean Whole-Cluster J (2 → 1) | "
                      "dissolution k/B* (2 → 1) | recovery k/B* (2 → 1) | status (2 → 1) |",
                      "|---|---|---|---|---|---|---|---|"]
            for i, (label, size) in enumerate(zip(run_["labels"], run_["sizes"])):
                f2, f1 = cluster_figures(by[2], arm, i), cluster_figures(by[1], arm, i)

                def num(x: float | None) -> str:
                    return "–" if x is None else f"{x:.3f}"

                def st(f: dict) -> str:
                    tags = [f["status"]] + (["borderline"] if f["borderline"] else []) + (["rare"] if f["rare"] else [])
                    return ", ".join(t for t in tags if t != "-") or "–"

                total += 1
                changed = (f2["status"] == "dissolved") != (f1["status"] == "dissolved")  # the label flips
                moved += changed
                summary_rows.append((name, arm, label, f2, f1, changed))
                lines.append(
                    f"| {label} | {size} | {f2['b_star']} → {f1['b_star']} | {num(f2['mean_h'])} → {num(f1['mean_h'])} "
                    f"| {num(f2['mean_w'])} → {num(f1['mean_w'])} | {f2['k_dissolved']}/{f2['b_star']} → "
                    f"{f1['k_dissolved']}/{f1['b_star']} | {f2['k_recovered']}/{f2['b_star']} → "
                    f"{f1['k_recovered']}/{f1['b_star']} | {st(f2)} → {st(f1)}{' **moved**' if changed else ''} |")
            lines.append("")
    lines += ["## Totals", "", f"Status moved in {moved} of {total} Cluster-arm rows."]
    for arm in ARMS:
        rows = [r for r in summary_rows if r[1] == arm]
        lab2 = sum(r[3]["status"] == "dissolved" for r in rows)
        lab1 = sum(r[4]["status"] == "dissolved" for r in rows)
        mv = sum(r[5] for r in rows)
        lines.append(f"- {arm}: {mv} of {len(rows)} statuses move; Dissolved in most subsamples {lab2} at s′ = 2, "
                     f"{lab1} at s′ = 1.")
        for r in rows:
            if r[5]:
                lines.append(f"  - {r[0]} {r[2]}: {r[3]['status']} → {r[4]['status']}")
    deltas = {arm: [r[4]["mean_h"] - r[3]["mean_h"] for r in summary_rows
                    if r[1] == arm and r[3]["mean_h"] is not None and r[4]["mean_h"] is not None] for arm in ARMS}
    wdeltas = {arm: [r[4]["mean_w"] - r[3]["mean_w"] for r in summary_rows
                     if r[1] == arm and r[3]["mean_w"] is not None and r[4]["mean_w"] is not None] for arm in ARMS}
    for arm in ARMS:
        if deltas[arm]:
            lines.append(f"- {arm}: mean Hennig's J change (s′ = 1 minus s′ = 2) median {statistics.median(deltas[arm]):+.3f}, "
                         f"range {min(deltas[arm]):+.3f} to {max(deltas[arm]):+.3f}; Whole-Cluster J median "
                         f"{statistics.median(wdeltas[arm]):+.3f}, range {min(wdeltas[arm]):+.3f} to "
                         f"{max(wdeltas[arm]):+.3f}.")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build")
    ap.add_argument("--pairs", nargs="*", default=[])
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(HERE / "results.json"))
    ap.add_argument("--report", action="store_true", help="only rewrite the report from --out")
    a = ap.parse_args()
    out = Path(a.out)
    if not a.report:
        pairs = []
        for p in a.pairs:
            d, g, s = p.split(":")
            pairs.append((d, int(g), int(s)))
        paths = stored_runs(a.build, pairs)
        if not paths:
            sys.exit("no stored validation of those pairs")
        data = run(a.build, paths, a.workers)
        out.write_text(json.dumps(data), encoding="utf-8")
    data = json.loads(out.read_text(encoding="utf-8"))
    out.with_suffix(".md").write_text(report(data), encoding="utf-8")
    sys.stdout.buffer.write(out.with_suffix(".md").read_bytes())


if __name__ == "__main__":
    main()
