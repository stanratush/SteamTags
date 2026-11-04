"""One-off: are the Null Comparison's domain widths stable when the γ scan is finer than 0.05?

Ticket: .scratch/validation-review/issues/10-scan-step-width-sensitivity.md. Null median widths of 0.03–0.19 sit near
the 0.05 step, so a finer scan might find partitions that cut the widest domains. Per validated Threshold Pair, the
observed network and all R = 100 nulls (rebuilt from the stored stream-4 seeds, as `validation.shuffled_games` builds
them) are rescanned at γ steps 0.05 (a determinism check: it must reproduce the stored widths), 0.025 and 0.01.

Each network runs the app's own procedure: `champ.scan_gammas(n_e, step)`, `leiden_scan` with the 10 stream-3 scan
seeds, `dedup`, CHAMP over [0, last scan γ], and the Selected Partition rule. The scan runs once per network and step;
CHAMP then runs once per stored validation of that pair (puzzle 14/2 has two, at min_multi_tag_clusters 2 and 3,
which share the observed network and the null seeds).

`scan_gammas` rounds every γ to 2 decimals, so step 0.025 is the uneven grid 0, 0.03, 0.05, 0.08, 0.10, … (gaps of
0.02 and 0.03). That is what setting `gamma_step = 0.025` would run, so it is kept as the app has it.

Per pair and step it records the observed domain width, the null median width, "observed wider than k (equal to t) of
K" (ticket 04: ties are exact float equality, counted apart; .3f is display only; K = the nulls with a Selected Partition), whether the observed
Selected Partition changes, and, as a by-product, the envelope-only fixed-γ Q count at the step's own γ_obs. The
exact-γ_obs Leiden runs of ticket 03 are not implemented (nothing on this map is), so they are absent.

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/10-scan-step/scan_step.py \
        --build builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f \
        --pairs rpg:7:5 puzzle:12:2 puzzle:14:2 puzzle:11:5 overall:12:2 overall:17:2 strategy:14:2 simulation:14:5

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/10-scan-step/scan_step.py --report

Run from the repo root. Writes results.json next to this file (`--out` to change) and the report beside it as results.md.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).parent
STEPS = (0.05, 0.025, 0.01)


# ----------------------------------------------------------------------------- the stored validations


def stored_runs(build: str, pairs: list[tuple[str, int, int]]) -> list[Path]:
    folder = Path(build) / "app_cache" / "parameter_selection" / "validation"
    out = []
    for path in sorted(folder.glob("*.json")):
        k = json.loads(path.read_text(encoding="utf-8"))["validation_key"]
        if (k["grid_key"]["dataset"], k["g"], k["s"]) in pairs:
            out.append(path)
    return out


def prepare(build: str, path: str) -> dict:
    """The stored run's null tasks and observed GraphResult, rebuilt as the app built them and checked."""
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
    # This Build's cache predates "Short Parameter Selection cache names" (9aa40e6): full 64-hex key hashes.
    if not ps_cache.grid_dir(ctx.app_cache, gk).exists():
        ps_cache.NAME_LENGTH = 64
    loaded = ps_cache.load_grid(ctx.app_cache, gk, dataset)
    if loaded is None:
        raise SystemExit(f"{Path(path).name}: no complete grid cached for {dataset}")
    observed = loaded[0].at(g, s)
    tasks = [t for t in V.validation_tasks(ctx.games(dataset), sel, dataset, context, g, s, observed,
                                           SEL.selection_seeds(sel)) if t.kind == "null"]
    stored_nulls = [r for r in stored["records"] if r["kind"] == "null"]
    if [t.seed for t in tasks] != [r["seed"] for r in stored_nulls]:
        raise SystemExit(f"{Path(path).name}: null seeds differ from the stored records")
    return {"dataset": dataset, "g": g, "s": s, "min_multi": gk["min_multi_tag_clusters"], "tasks": tasks,
            "observed": observed, "stored": stored_nulls, "stored_null_summary": stored["summary"]["null"],
            "file": Path(path).name}


_PREPARED: dict = {}


def _prep(build: str, path: str) -> dict:
    if path not in _PREPARED:
        _PREPARED[path] = prepare(build, path)
    return _PREPARED[path]


def network_job(args: tuple) -> dict:
    """One network (index 0 = observed, else null replicate `index`) at one step: scan once, CHAMP per min_multi."""
    from steamstudy.network import champ as C
    from steamstudy.network import validation as V
    from steamstudy.network.cluster import leiden_scan
    from steamstudy.network.graph import build_network, filter_games, to_graph
    from steamstudy.network.selection import edge_arrays_of

    build, paths, index, step = args  # paths: every stored run of this pair (same network, same null seeds)
    preps = [_prep(build, p) for p in paths]
    task = preps[0]["tasks"][max(0, index - 1)]
    games = filter_games(task.games, task.settings.min_months)
    if index > 0:
        games = V.shuffled_games(games, task.observed.nodes, task.seed)
    t0 = time.perf_counter()
    network = build_network(games, task.settings, task.context)
    out: dict = {"index": index, "step": step, "n_edges": len(network.edges), "by_min_multi": {}}
    if not network.edges:
        for prep in preps:
            out["by_min_multi"][str(prep["min_multi"])] = {"reason": "no_edges", "selected": None, "envelope": []}
        out["seconds"] = time.perf_counter() - t0
        return out
    graph = to_graph(network.nodes, network.edges, task.settings.clustering_weight)
    arrays = edge_arrays_of(network, task.settings.clustering_weight)
    gammas = C.scan_gammas(arrays.n_e, step)
    scan = C.dedup(leiden_scan(graph, gammas, list(task.scan_seeds)))
    out.update({"scan_length": len(gammas), "gamma_end": gammas[-1], "n_unique": len(scan.memberships)})
    for prep in preps:
        result = C.champ(scan, arrays, gammas[-1], prep["min_multi"])
        p = result.selected_partition
        out["by_min_multi"][str(prep["min_multi"])] = {
            "reason": result.reason, "two_m": result.two_m,
            "envelope": [[q.a_hat, q.p_hat, q.a, q.b] for q in result.admissible],
            "selected": None if p is None else {
                "a": p.a, "b": p.b, "width": p.width, "midpoint": p.midpoint, "n_multi": p.n_multi,
                "clipped_high": p.clipped_high, "a_hat": p.a_hat, "p_hat": p.p_hat,
                "membership": list(p.membership) if index == 0 else None},
        }
    out["seconds"] = time.perf_counter() - t0
    return out


def run(build: str, paths: list[Path], workers: int, steps: tuple[float, ...], limit: int | None) -> dict:
    preps = {str(p): prepare(build, str(p)) for p in paths}
    groups: dict[tuple[str, int, int], list[str]] = {}
    for p, prep in preps.items():
        groups.setdefault((prep["dataset"], prep["g"], prep["s"]), []).append(p)
    for key, ps in groups.items():  # runs sharing a pair must share its nulls for one scan to serve them all
        seeds = {tuple(t.seed for t in preps[p]["tasks"]) for p in ps}
        if len(seeds) > 1:
            raise SystemExit(f"{key}: stored runs of one pair have different null seeds")
    jobs = []
    for key, ps in groups.items():
        n = len(preps[ps[0]]["tasks"]) if limit is None else limit
        jobs += [(build, ps, i, st) for st in steps for i in range(n + 1)]
    jobs.sort(key=lambda j: -j[3] ** -1)  # finest step first: the heaviest jobs start early
    t0 = time.perf_counter()
    with Pool(workers) as pool:
        results = pool.map(network_job, jobs, chunksize=1)
    out = {"build": build, "seconds": time.perf_counter() - t0, "steps": list(steps), "pairs": {}}
    for (d, g, s), ps in groups.items():
        mine = [r for r, j in zip(results, jobs) if j[1] == ps]
        runs = {}
        for p in ps:
            prep = preps[p]
            obs = prep["observed"]
            runs[str(prep["min_multi"])] = {
                "file": prep["file"], "stored_null_summary": prep["stored_null_summary"],
                "stored_widths": [r["width"] for r in prep["stored"]],
                "stored_q_fixed": [r["q_fixed"] for r in prep["stored"]],
                "stored_observed": {"width": obs.selected_partition["b"] - obs.selected_partition["a"],
                                    "resolution": obs.selected_resolution, "membership": obs.selected,
                                    "gamma_end": obs.gamma_end, "n_multi": obs.n_multi},
            }
        out["pairs"][f"{d} {g}/{s}"] = {
            "dataset": d, "g": g, "s": s, "runs": runs, "n_tags": len(preps[ps[0]]["observed"].nodes),
            "records": sorted(mine, key=lambda r: (r["step"], r["index"])),
        }
    return out


# ----------------------------------------------------------------------------- report


def f3(x: float) -> str:
    return f"{x:.3f}"


def figures(records: list[dict], mm: str, step: float) -> dict:
    """The Null Comparison's width and Q figures at one step, from one min_multi's CHAMP results."""
    at = [r for r in records if r["step"] == step]
    obs = next(r for r in at if r["index"] == 0)["by_min_multi"][mm]
    nulls = [r["by_min_multi"][mm] for r in at if r["index"] > 0]
    sel = obs["selected"]
    widths = [n["selected"]["width"] for n in nulls if n["selected"] is not None]
    out = {"observed": sel, "widths": widths, "K": len(widths), "R": len(nulls),
           "reasons": {}, "scan_length": next(r for r in at if r["index"] == 0).get("scan_length")}
    for n in nulls:
        if n["selected"] is None:
            out["reasons"][n["reason"]] = out["reasons"].get(n["reason"], 0) + 1
    if sel is not None:
        w = sel["width"]  # ticket 04: ties are exact float equality; .3f is display only
        out["wider"] = sum(x < w for x in widths)
        out["equal"] = sum(x == w for x in widths)
        g_obs = sel["midpoint"]
        q_obs = (sel["a_hat"] - g_obs * sel["p_hat"]) / obs["two_m"]
        qs = [max(a - g_obs * p for a, p, *_ in n["envelope"]) / n["two_m"] for n in nulls if n["envelope"]]
        out.update({"q_obs": q_obs, "D": len(qs), "reach": sum(q >= q_obs for q in qs),
                    "q_null_median": statistics.median(qs) if qs else None})
    out["median"] = statistics.median(widths) if widths else None
    return out


def report(data: dict) -> str:
    steps = data["steps"]
    n_jobs = sum(len(p["records"]) for p in data["pairs"].values())
    lines = ["# 10 Domain-width sensitivity to the scan step: results", "",
             f"Build `{Path(data['build']).name}`, {n_jobs} network scans in {data['seconds']:.0f} s.", ""]
    summary = []
    for name, pair in data["pairs"].items():
        for mm, run_ in pair["runs"].items():
            recs = pair["records"]
            label = f"{name} (min multi {mm})" if len(pair["runs"]) > 1 else name
            # determinism at 0.05
            base = figures(recs, mm, 0.05) if 0.05 in steps else None
            det = ""
            if base is not None:
                at05 = sorted((r for r in recs if r["step"] == 0.05 and r["index"] > 0), key=lambda r: r["index"])
                got = [None if r["by_min_multi"][mm]["selected"] is None else r["by_min_multi"][mm]["selected"]["width"]
                       for r in at05]
                ref = run_["stored_widths"][:len(got)]
                bad = sum((a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12) for a, b in zip(got, ref))
                so = run_["stored_observed"]
                same_obs = base["observed"] is not None and base["observed"]["membership"] == so["membership"] \
                    and abs(base["observed"]["width"] - so["width"]) < 1e-12
                det = (f"Determinism at 0.05: {len(got) - bad} of {len(got)} stored null widths reproduced; observed "
                       f"Selected Partition and width {'reproduced' if same_obs else 'NOT reproduced'}.")
            ref_membership = run_["stored_observed"]["membership"]
            lines += [f"## {label}", "", f"{pair['n_tags']} tags. {det}", "",
                      "| Step | scan length | γ_obs | observed width | clipped | Selected Partition | null median width "
                      "| null p10–p90 | wider than k (equal t) of K | K of R | Q reached (D) |",
                      "|---|---|---|---|---|---|---|---|---|---|---|"]
            row_figs = {}
            for st in steps:
                f = figures(recs, mm, st)
                row_figs[st] = f
                o = f["observed"]
                if o is None:
                    lines.append(f"| {st} | {f['scan_length']} | – | – | – | none | – | – | – | {f['K']} of {f['R']} | – |")
                    continue
                same = "unchanged" if o["membership"] == ref_membership else f"CHANGED ({o['n_multi']} Multi-Tag)"
                ws = sorted(f["widths"])
                p10 = ws[int(0.1 * (len(ws) - 1))] if ws else None
                p90 = ws[int(0.9 * (len(ws) - 1))] if ws else None
                lines.append(
                    f"| {st} | {f['scan_length']} | {o['midpoint']:.3f} | {o['width']:.3f} | "
                    f"{'yes' if o['clipped_high'] else 'no'} | {same} | "
                    f"{'–' if f['median'] is None else f3(f['median'])} | "
                    f"{'–' if p10 is None else f3(p10) + '–' + f3(p90)} | {f['wider']} ({f['equal']}) of {f['K']} | "
                    f"{f['K']} of {f['R']} | {f['reach']} of {f['D']} |")
            lines.append("")
            summary.append((label, row_figs, ref_membership))
    lines += ["## Summary", "",
              "| Pair | observed width (" + " / ".join(map(str, steps)) + ") | null median (same) | wider than k of K "
              "(same) | Selected Partition |", "|---|---|---|---|---|"]
    for label, figs, ref in summary:
        def cell(key: str) -> str:
            vals = []
            for st in steps:
                f = figs[st]
                if key == "width":
                    vals.append("–" if f["observed"] is None else f3(f["observed"]["width"]))
                elif key == "median":
                    vals.append("–" if f["median"] is None else f3(f["median"]))
                else:
                    vals.append("–" if f["observed"] is None else f"{f['wider']} of {f['K']}")
            return " / ".join(vals)
        changed = [str(st) for st in steps if figs[st]["observed"] is None or figs[st]["observed"]["membership"] != ref]
        lines.append(f"| {label} | {cell('width')} | {cell('median')} | {cell('wider')} | "
                     f"{'changes at ' + ', '.join(changed) if changed else 'unchanged'} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build")
    ap.add_argument("--pairs", nargs="*", default=[], help="dataset:g:s")
    ap.add_argument("--steps", nargs="*", type=float, default=list(STEPS))
    ap.add_argument("--limit", type=int, default=None, help="only the first N nulls per pair (a timing test)")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(HERE / "results.json"))
    ap.add_argument("--report", action="store_true", help="only rewrite the report from --out")
    a = ap.parse_args()
    out = Path(a.out)
    if not a.report:
        pairs = [(p.split(":")[0], int(p.split(":")[1]), int(p.split(":")[2])) for p in a.pairs]
        paths = stored_runs(a.build, pairs)
        if not paths:
            sys.exit("no stored validation of those pairs")
        out.write_text(json.dumps(run(a.build, paths, a.workers, tuple(a.steps), a.limit)), encoding="utf-8")
    data = json.loads(out.read_text(encoding="utf-8"))
    out.with_suffix(".md").write_text(report(data), encoding="utf-8")
    sys.stdout.buffer.write(out.with_suffix(".md").read_bytes())


if __name__ == "__main__":
    main()
