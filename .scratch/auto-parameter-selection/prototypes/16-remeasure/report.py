"""Throwaway: facts for results.md from remeasure.py's runs/ (ref = ticket 05 procedure, new = ticket 16 rule).

    uv run python .scratch/auto-parameter-selection/prototypes/16-remeasure/report.py > .scratch/.../16-remeasure/report.txt
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "12-neighbour-agreement-bias"))
import after_q3 as AQ  # noqa: E402

RUNS = HERE / "runs"
DATASETS = ("overall", "puzzle", "rpg", "simulation", "strategy")
TOL = 0.05


def load(arm):
    out = {}
    for d in DATASETS:
        doc = json.loads((RUNS / arm / f"{d}.json").read_text(encoding="utf-8"))
        recs = {(r["g"], r["s"]): r for r in doc["records"]}
        AQ.renormalise(recs, doc["links"])
        out[d] = (recs, doc)
    return out


def choose(recs):
    q = {k: r for k, r in recs.items() if AQ.qualifies(r)}
    top = max(r["na12"][0] for r in q.values())
    at = sorted(k for k, r in q.items() if abs(r["na12"][0] - top) <= 1e-12)
    near = sorted(k for k, r in q.items() if r["na12"][0] >= top - TOL - 1e-12)
    return q, top, at, near, near[0]


def memb(r):
    return None if r["selected"] is None else tuple(r["selected"]["membership"])


def main():
    ref, new = load("ref"), load("new")
    wall = {a: json.loads((RUNS / a / "overall.json").read_text())["wall_seconds_all_datasets"] for a in ("ref", "new")}
    print(f"wall: ref {wall['ref']:.1f} s, new {wall['new']:.1f} s (12 workers, all 765 pairs)")

    # ---------------------------------------------------------------- 1. Selected Partitions
    print("\n## 1. Selected Partitions")
    allnew = [r for d in DATASETS for r in new[d][0].values()]
    allref = [r for d in DATASETS for r in ref[d][0].values()]
    print("with selection: ref", sum(r["selected"] is not None for r in allref), "new",
          sum(r["selected"] is not None for r in allnew))
    for r in allnew:
        if r["selected"] is None:
            print("  new no selection:", r["dataset"], r["g"], r["s"], r["no_selection_reason"])
    diffs = []
    for d in DATASETS:
        for k in sorted(ref[d][0]):
            a, b = ref[d][0][k], new[d][0][k]
            if memb(a) != memb(b):
                diffs.append((d, k, a, b))
    print("differ from ref:", len(diffs))
    for d, k, a, b in diffs:
        sa, sb = a["selected"], b["selected"]
        fa = "none" if sa is None else f"[{sa['a']:.3f},{sa['b']:.3f}] mid {sa['selected_resolution']:.3f} multi {sa['n_multi']} hits {sa['hits']}"
        fb = "none" if sb is None else f"[{sb['a']:.3f},{sb['b']:.3f}] mid {sb['selected_resolution']:.3f} multi {sb['n_multi']} hits {sb['hits']}"
        ari = None
        if sa is not None and sb is not None:
            from sklearn.metrics import adjusted_rand_score
            ari = adjusted_rand_score(sa["membership"], sb["membership"])
        print(f"  {d} g={k[0]} s={k[1]}: ref {fa} | new {fb} | ARI {ari if ari is None else round(ari, 3)}"
              f" | new n_admissible {b.get('n_admissible')} n_stable {b.get('n_stable')}")
    sels = [r["selected"] for r in allnew if r["selected"] is not None]
    print("clipped_high selected:", sum(s["clipped_high"] for s in sels))
    print("a == 0 selected:", sum(s["a_is_zero"] for s in sels))
    print("not_representable:", sum(s["not_representable"] for s in sels))
    print("estimate_above_range (all admissible):", sum(r.get("n_estimate_above_range", 0) for r in allnew),
          "below:", sum(r.get("n_estimate_below_range", 0) for r in allnew))
    reasons = {}
    for r in allnew:
        for k, v in r.get("reasons", {}).items():
            reasons[k] = reasons.get(k, 0) + v
    print("admissible reasons (new):", reasons, "admissible total", sum(r.get("n_admissible", 0) for r in allnew),
          "stable", sum(r.get("n_stable", 0) for r in allnew))
    print("admissible total (ref):", sum(r.get("n_admissible", 0) for r in allref),
          "stable", sum(r.get("n_stable", 0) for r in allref))
    print("stable partitions with γ̂ < 0.25:", sum(r.get("n_stable_below_025", 0) for r in allnew),
          "in pairs:", sum(r.get("n_stable_below_025", 0) > 0 for r in allnew),
          "| γ̂ > 3.0:", sum(r.get("n_stable_above_3", 0) for r in allnew),
          "in pairs:", sum(r.get("n_stable_above_3", 0) > 0 for r in allnew))
    print("max γ̂ / scan end ratio:", max(r["max_gamma_hat"] / r["scan_end"] for r in allnew if r.get("max_gamma_hat")))
    print("selected a < 0.25:", sum(s["a"] < 0.25 for s in sels), "b > 3.0:", sum(s["b"] > 3.0 for s in sels))

    # consistency with research 16's gmK arm (CHAMP top there = unrounded γ_max(K))
    gm = json.loads((HERE.parent / "16-citable-upper-bound" / "scan_ends_gmK.json").read_text())
    same = dif = 0
    for x in gm:
        r = new[x["dataset"]][0][(x["g"], x["s"])]
        ka = x["arms"]["gmK"]["selected"]
        kb = None if r["selected"] is None else np.asarray(r["selected"]["membership"], dtype=np.int64).tobytes().hex()
        ka = None if ka is None else ka["key"]
        same += ka == kb
        dif += ka != kb
    print(f"vs research 16 gmK arm: identical {same}, different {dif}")

    # ---------------------------------------------------------------- 2. chosen pairs
    print("\n## 2. Chosen pairs")
    for d in DATASETS:
        for arm, data in (("ref", ref), ("new", new)):
            recs = data[d][0]
            q, top, at, near, k = choose(recs)
            r = recs[k]
            sel = r["selected"]
            print(f"  {d} {arm}: qualifying {len(q)}, max {top:.3f} at {at}, near-best {len(near)}, chosen g={k[0]} s={k[1]}"
                  f" NA {r['na12'][0]:.3f} (n={r['na12'][2]}), multi {sel['n_multi']}, tags {r['n_tags']},"
                  f" mid {sel['selected_resolution']:.3f} wb {sel['workbench_resolution']}, floor {sel['seed_noise_floor']:.2f}")
        qa = {k for k, r in ref[d][0].items() if AQ.qualifies(r)}
        qb = {k for k, r in new[d][0].items() if AQ.qualifies(r)}
        _, _, _, na_, _ = choose(ref[d][0])
        _, _, _, nb_, _ = choose(new[d][0])
        print(f"  {d}: qualifying gained {sorted(qb - qa)}, lost {sorted(qa - qb)}; near-best ref {na_} new {nb_}")
        nachg = [(k, round(ref[d][0][k]['na12'][0], 3), round(new[d][0][k]['na12'][0], 3)) for k in sorted(qa & qb)
                 if abs(ref[d][0][k]['na12'][0] - new[d][0][k]['na12'][0]) > 1e-12]
        print(f"  {d}: NA changed on {len(nachg)} qualifying pairs: {nachg[:12]}{' ...' if len(nachg) > 12 else ''}")

    # ---------------------------------------------------------------- 3. Workbench search
    print("\n## 3. Workbench search (ticket 09)")
    for arm, data in (("ref", ref), ("new", new)):
        s = json.loads((RUNS / f"search_{arm}.json").read_text())
        res = s["results"]
        found = [x for x in res if x["found"]]
        print(f"  {arm}: {len(found)} of {len(res)} reproduced; at nearest γ (any seed) {sum(x['gamma_rank'] == 0 for x in found)};"
              f" main seed at nearest {sum(x['gamma_rank'] == 0 and x['seed_idx'] == 0 for x in found)};"
              f" search runs {sum(x['runs'] for x in res)}, capped {sum(x['capped'] for x in res)}, wall {s['wall_seconds']:.1f} s")
        for x in res:
            if not x["found"]:
                r = data[x["dataset"]][0][(x["g"], x["s"])]
                print(f"    not_reproduced {x['dataset']} g={x['g']} s={x['s']}: hits {r['selected']['hits']}, "
                      f"domain values {x['n_gamma']}, mid {r['selected']['selected_resolution']:.3f}")
        print(f"    found γ > 3.0: {sum(x['gamma'] > 3.0 for x in found)}, < 0.1: {sum(x['gamma'] < 0.1 for x in found)}")
    hi = [(r["dataset"], r["g"], r["s"], round(r["selected"]["selected_resolution"], 3), round(r["selected"]["a"], 3), round(r["selected"]["b"], 3))
          for r in allnew if r["selected"] and r["selected"]["selected_resolution"] > 3.0]
    lo = [(r["dataset"], r["g"], r["s"], round(r["selected"]["selected_resolution"], 3), round(r["selected"]["a"], 3), round(r["selected"]["b"], 3))
          for r in allnew if r["selected"] and r["selected"]["selected_resolution"] < 0.1]
    print("  Selected Resolution > 3.0:", hi)
    print("  Selected Resolution < 0.1:", lo)
    lo25 = [(r["dataset"], r["g"], r["s"], round(r["selected"]["selected_resolution"], 3))
            for r in allnew if r["selected"] and r["selected"]["selected_resolution"] < 0.25]
    print("  Selected Resolution < 0.25:", lo25)
    print("  Selected Resolution range new:", min(s["selected_resolution"] for s in sels), max(s["selected_resolution"] for s in sels))

    # ---------------------------------------------------------------- 4. cost
    print("\n## 4. Cost")
    ng = [r["n_gammas"] for r in allnew if "n_gammas" in r]
    print("γ values per graph: min", min(ng), "median", statistics.median(ng), "max", max(ng), "total", sum(ng))
    ends = [r["scan_end"] for r in allnew if "scan_end" in r]
    print("scan end: min", min(ends), "median", statistics.median(ends), "max", max(ends))
    print("scan runs new", sum(r["n_scan_runs"] for r in allnew), "ref", 765 * 560)
    print("noise runs", 10 * len(sels), "noise capped", sum(r["noise_capped"] for r in allnew))
    cap = [(r["dataset"], r["g"], r["s"], len(r["scan_capped"]), sorted({c[0] for c in r["scan_capped"]}))
           for r in allnew if r.get("scan_capped")]
    print("pass-capped scan runs:", sum(c[3] for c in cap), "in", len(cap), "graphs")
    for c in cap:
        print("   ", c)
    print("sum scan seconds new", round(sum(r["scan_seconds"] for r in allnew), 1), "ref",
          round(sum(r["scan_seconds"] for r in allref), 1), "| sum pair seconds new",
          round(sum(r["seconds"] for r in allnew), 1), "ref", round(sum(r["seconds"] for r in allref), 1))
    slow = sorted(allnew, key=lambda r: -r["seconds"])[:3]
    print("slowest pairs:", [(r["dataset"], r["g"], r["s"], round(r["seconds"], 1), r["n_gammas"]) for r in slow])


if __name__ == "__main__":
    main()
