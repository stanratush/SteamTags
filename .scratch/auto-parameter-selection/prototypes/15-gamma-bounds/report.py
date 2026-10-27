"""Throwaway: summarises bounds.json and scan_extended.json into results.md (ticket 15).

    uv run python .scratch/auto-parameter-selection/prototypes/15-gamma-bounds/report.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
DATASETS = ("overall", "puzzle", "rpg", "simulation", "strategy")
LO, HI = 0.25, 3.00


def q(xs):
    a = np.asarray([x for x in xs if x is not None], float)
    p = np.quantile(a, [0, 0.05, 0.25, 0.5, 0.75, 0.95, 1])
    return " | ".join(f"{x:.3f}" for x in p), len(a)


def row(name, xs):
    s, n = q(xs)
    a = np.asarray([x for x in xs if x is not None], float)
    return f"| {name} | {n} | {s} | {(a < LO).sum()} | {(a > HI).sum()} |"


def tag_name_map():
    try:
        import sys
        sys.path.insert(0, str(HERE.parent / "05-grid-run"))
        import grid_run as GR
        from steamstudy.app.loader import load_build
        ctx = load_build(GR.BUILD)
        for attr in ("tag_names", "tags"):
            m = getattr(ctx, attr, None)
            if isinstance(m, dict):
                return {int(k): (v if isinstance(v, str) else getattr(v, "name", str(v))) for k, v in m.items()}
    except Exception:  # noqa: BLE001
        pass
    return {}


def main():
    B = json.loads((HERE / "bounds.json").read_text())["records"]
    out = ["# Ticket 15 measurements", "",
           "Produced by [bounds.py](bounds.py), [scan_extended.py](scan_extended.py) and this script. "
           "Build `20261008T221504Z-7a23ae9f`; Genre Tags and the defining tag hidden, Minimum Months 0; "
           "765 pair graphs. Quantile columns: min, 5%, 25%, median, 75%, 95%, max. "
           "The last two columns count graphs below 0.25 and above 3.00.", ""]
    names = tag_name_map()
    for wname, label in (("lift", "Lift"), ("shared", "Shared games")):
        p = wname + "_"
        out += [f"## {label} weights", "",
                "| Bound | graphs | min | 5% | 25% | median | 75% | 95% | max | < 0.25 | > 3.00 |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        out.append(row("γ_max = max 2m·w/(k_i k_j)", [r[p + "gamma_max"] for r in B]))
        out.append(row("γ_pos (root of F, Q > 0 ends)", [r[p + "gamma_pos"] for r in B]))
        out.append(row("GM22 γ_max(K), K = non-isolated tags", [r[p + "gamma_max_K"] for r in B]))
        out.append(row("γ_min lower: (2m/vol)·λ2", [r[p + "lam2_lower"] for r in B]))
        out.append(row("γ_min upper: Fiedler sweep cut", [r[p + "sweep_upper"] for r in B]))
        out.append(row("γ_min upper: Jeub iteration (Leiden, 10 seeds)", [r[p + "jeub_upper"] for r in B]))
        best = [min(r[p + "sweep_upper"], r[p + "jeub_upper"]) for r in B]
        out.append(row("γ_min upper: min(sweep, Jeub)", best))
        ex = [r for r in B if r[p + "exact"] is not None]
        out.append(row(f"γ_min exact (brute force, components ≤ 24 tags)", [r[p + "exact"] for r in ex]))
        out.append("")
        ratio = [min(r[p + "sweep_upper"], r[p + "jeub_upper"]) / r[p + "lam2_lower"] for r in B]
        out.append(f"- Bracket width, upper/lower: median {np.median(ratio):.3f}, max {max(ratio):.3f}.")
        if ex:
            tol = 1e-9
            sw = sum(abs(r[p + "sweep_upper"] - r[p + "exact"]) <= tol * max(1, r[p + "exact"]) for r in ex)
            jb = sum(abs(r[p + "jeub_upper"] - r[p + "exact"]) <= tol * max(1, r[p + "exact"]) for r in ex)
            either = sum(abs(min(r[p + "sweep_upper"], r[p + "jeub_upper"]) - r[p + "exact"]) <= tol * max(1, r[p + "exact"]) for r in ex)
            gap = max(min(r[p + "sweep_upper"], r[p + "jeub_upper"]) / r[p + "exact"] for r in ex)
            out.append(f"- Exact γ_min on {len(ex)} graphs: the sweep cut hits it on {sw}, Jeub's iteration on {jb}, "
                       f"either on {either}; worst upper/exact {gap:.4f}.")
        sw_better = sum(r[p + "sweep_upper"] < r[p + "jeub_upper"] - 1e-9 for r in B)
        jb_better = sum(r[p + "jeub_upper"] < r[p + "sweep_upper"] - 1e-9 for r in B)
        out.append(f"- Sweep cut lower than Jeub on {sw_better} graphs, Jeub lower on {jb_better}.")
        out.append(f"- Graphs with more than one component of ≥ 2 tags: "
                   f"{sum(r[p + 'n_components'] > 1 for r in B)}; with an isolated tag: "
                   f"{sum(r[p + 'n_isolated'] > 0 for r in B)}.")
        jr = [r[p + "jeub_runs"] for r in B]
        out.append(f"- Jeub iteration: {min(jr)}–{max(jr)} Leiden runs per graph (median {np.median(jr):.0f}).")
        ev3 = [r[p + "event_n_above_3"] for r in B]
        ev_in = [r[p + "event_n_in_025_3"] for r in B]
        out.append(f"- Event sampling, 56 values from β(γ_min upper) to 1: values above 3.00 per graph "
                   f"median {np.median(ev3):.0f} (range {min(ev3)}–{max(ev3)}); inside [0.25, 3.00] median "
                   f"{np.median(ev_in):.0f} (range {min(ev_in)}–{max(ev_in)}). Median event γ: "
                   f"{np.median([r[p + 'event_gamma_q'][2] for r in B]):.3f}.")
        ratio_pm = [r[p + "gamma_pos"] / r[p + "gamma_max"] for r in B]
        out.append(f"- γ_pos/γ_max: median {np.median(ratio_pm):.3f}, range {min(ratio_pm):.3f}–{max(ratio_pm):.3f}.")
        out.append("")
        out.append("Extremes:")
        out.append("")
        for key, lab in (("gamma_max", "γ_max"), ("gamma_pos", "γ_pos"), ("lam2_lower", "γ_min lower")):
            lo_r = min(B, key=lambda r: r[p + key])
            hi_r = max(B, key=lambda r: r[p + key])
            for which, r in (("lowest", lo_r), ("highest", hi_r)):
                extra = ""
                if key == "gamma_max":
                    a, b = r[p + "gamma_max_edge"]
                    extra = (f"; edge {names.get(a, a)}–{names.get(b, b)}, shared {r[p + 'gamma_max_edge_shared']}, "
                             f"w {r[p + 'gamma_max_edge_w']:.3g}, strengths {r[p + 'gamma_max_edge_k'][0]:.3g} and "
                             f"{r[p + 'gamma_max_edge_k'][1]:.3g}, 2m {r[p + 'two_m']:.4g}")
                out.append(f"- {lab} {which}: {r[p + key]:.3f} at {r['dataset']} g={r['g']} s={r['s']} "
                           f"({r['n_tags']} tags){extra}")
        out.append("")
        out += ["By dataset (medians):", "",
                "| Dataset | γ_min lower | γ_min upper | γ_pos | γ_max | γ_max(K) |", "|---|---:|---:|---:|---:|---:|"]
        for d in DATASETS:
            rs = [r for r in B if r["dataset"] == d]
            out.append(f"| {d} | {np.median([r[p + 'lam2_lower'] for r in rs]):.3f} | "
                       f"{np.median([min(r[p + 'sweep_upper'], r[p + 'jeub_upper']) for r in rs]):.3f} | "
                       f"{np.median([r[p + 'gamma_pos'] for r in rs]):.3f} | "
                       f"{np.median([r[p + 'gamma_max'] for r in rs]):.3f} | "
                       f"{np.median([r[p + 'gamma_max_K'] for r in rs]):.3f} |")
        out.append("")

    se = HERE / "scan_extended.json"
    if se.is_file():
        S = json.loads(se.read_text())
        ref = {}
        with open(HERE.parent / "05-grid-run" / "pairs.csv", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                ref[(r["dataset"], int(r["g"]), int(r["s"]))] = r
        repro = sum(
            (r["fixed"]["selected"] is None and ref[(r["dataset"], r["g"], r["s"])]["Selected Resolution"] == "")
            or (r["fixed"]["selected"] is not None and ref[(r["dataset"], r["g"], r["s"])]["Selected Resolution"] != ""
                and abs(r["fixed"]["selected"]["mid"] - float(ref[(r["dataset"], r["g"], r["s"])]["Selected Resolution"])) < 1e-5)
            for r in S)
        same = sum(r["same_selected"] for r in S)
        both_none = sum(r["fixed"]["selected"] is None and r["extended"]["selected"] is None for r in S)
        out += ["## Extended scan (Lift): fixed [0.25, 3.00] against [scan start, γ_pos]", ""]
        out.append(f"- Graphs: {len(S)}; scan values per graph {min(r['n_gammas'] for r in S)}–"
                   f"{max(r['n_gammas'] for r in S)} (median {np.median([r['n_gammas'] for r in S]):.0f}); "
                   f"scan start below 0.25 on {sum(r['scan_lo'] < 0.25 for r in S)} graphs.")
        out.append(f"- The fixed arm reproduces ticket 05's Selected Resolution (to 1e-5) on {repro} of {len(S)}.")
        out.append(f"- Same Selected Partition in both arms: {same}; no selection in both: {both_none}; "
                   f"differ: {len(S) - same - both_none}.")
        diffs = [r for r in S if not r["same_selected"] and not (r["fixed"]["selected"] is None and r["extended"]["selected"] is None)]
        for r in diffs[:30]:
            f, e = r["fixed"]["selected"], r["extended"]["selected"]
            fs = "none" if f is None else f"[{f['a']:.3f}, {f['b']:.3f}] K={f['n_multi']}"
            es = "none" if e is None else f"[{e['a']:.3f}, {e['b']:.3f}] K={e['n_multi']} clip_hi={e['clipped_high']}"
            out.append(f"  - {r['dataset']} g={r['g']} s={r['s']}: fixed {fs} ({r['fixed']['reason']}); "
                       f"extended {es} ({r['extended']['reason']})")
        st_above = [r for r in S if any(dm[1] > 3.0 for dm in r["extended"]["stable_domains"])]
        st_start_above = [r for r in S if any(dm[0] > 3.0 for dm in r["extended"]["stable_domains"])]
        gh_above = [r for r in S if any(dm[2] > 3.0 for dm in r["extended"]["stable_domains"])]
        out.append(f"- Extended arm: graphs with a stable domain reaching above 3.00: {len(st_above)}; "
                   f"starting above 3.00: {len(st_start_above)}; with a stable γ̂ above 3.00: {len(gh_above)}.")
        mg = [r["extended"]["max_gamma_hat"] for r in S if r["extended"]["max_gamma_hat"] is not None]
        out.append(f"- Largest γ̂ of any Admissible Partition (extended): median {np.median(mg):.3f}, max {max(mg):.3f}; "
                   f"graphs with any γ̂ > 3.00: {sum(x > 3 for x in mg)}.")
        out.append(f"- Fixed arm `estimate_above_range`: {sum(r['fixed']['n_above_range'] for r in S)}, "
                   f"`estimate_below_range`: {sum(r['fixed']['n_below_range'] for r in S)}; extended arm: "
                   f"{sum(r['extended']['n_above_range'] for r in S)} and {sum(r['extended']['n_below_range'] for r in S)}.")
        moi = [r["extended"]["max_omega_in"] / r["gamma_pos"] for r in S if r["extended"]["max_omega_in"]]
        out.append(f"- Found envelope zero crossing (max ω_in over Admissible Partitions) / γ_pos: median "
                   f"{np.median(moi):.3f}, range {min(moi):.3f}–{max(moi):.3f}.")
        nst = [(r["fixed"]["n_stable"], r["extended"]["n_stable"]) for r in S]
        out.append(f"- Stable Partitions per graph, fixed vs extended: mean {np.mean([a for a, _ in nst]):.2f} vs "
                   f"{np.mean([b for _, b in nst]):.2f}; graphs where the count differs: {sum(a != b for a, b in nst)}.")
        capped = [(r["dataset"], r["g"], r["s"], c) for r in S for c in r.get("capped_runs", [])]
        cg = sorted({c[3][0] for c in capped})
        out.append(f"- Leiden runs that hit the 1000-pass cap (n_iterations=-1 would not stop): {len(capped)} on "
                   f"{len({c[:3] for c in capped})} graphs; γ from {min(cg) if cg else '–'} to {max(cg) if cg else '–'}; "
                   f"at γ ≤ 3.00: {sum(c[3][0] <= 3.0 for c in capped)}.")
        sec = sum(r["seconds"] for r in S)
        out.append(f"- Leiden runs: {sum(r['n_runs'] for r in S)} in total against {len(S) * 560} for the fixed scan; "
                   f"summed worker time {sec:.0f} s.")
        out.append("")
    (HERE / "results.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
