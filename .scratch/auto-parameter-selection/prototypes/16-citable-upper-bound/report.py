"""Throwaway: tables for research 16 from scan_ends_gmK.json (all 765 Lift graphs) and scan_ends_jsf.json (sample).

    uv run python .scratch/auto-parameter-selection/prototypes/16-citable-upper-bound/report.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent


def q(a, ps=(0, 5, 50, 95, 100)):
    a = np.asarray([x for x in a if x is not None], dtype=float)
    return " ".join(f"{v:.2f}" for v in np.percentile(a, ps)) if len(a) else "-"


def sel_key(arm):
    s = arm["selected"]
    return None if s is None else s["key"]


def compare(recs, ref, other):
    same = diff = none_both = 0
    rows = []
    for r in recs:
        a, b = r["arms"].get(ref), r["arms"].get(other)
        if a is None or b is None:
            continue
        ka, kb = sel_key(a), sel_key(b)
        if ka is None and kb is None:
            none_both += 1
        elif ka == kb:
            same += 1
        else:
            diff += 1
            fa, fb = a["selected"], b["selected"]
            rows.append(f"    {r['dataset']} g={r['g']} s={r['s']}: {ref} "
                        + ("none (" + str(a["reason"]) + ")" if fa is None else
                           f"[{fa['a']:.3f}, {fa['b']:.3f}] {fa['n_multi']} MTC γ̂={fa['gamma_hat']:.3f}")
                        + f"  vs {other} "
                        + ("none (" + str(b["reason"]) + ")" if fb is None else
                           f"[{fb['a']:.3f}, {fb['b']:.3f}] {fb['n_multi']} MTC γ̂={fb['gamma_hat']:.3f}"))
    print(f"  {ref} vs {other}: same {same}, differ {diff}, none in both {none_both}")
    for x in rows:
        print(x)


def describe(name, recs, arms):
    print(f"\n=== {name}: {len(recs)} graphs, {sum(r['n_runs'] for r in recs)} runs, "
          f"{sum(r['n_capped'] for r in recs)} capped runs, scan {sum(r['scan_seconds'] for r in recs):.0f} worker-s")
    for arm in arms:
        xs = [r["arms"][arm] for r in recs if arm in r["arms"]]
        n_g = [x["n_gammas"] for x in xs]
        print(f"  {arm:7s} end: {q([x['scan_end'] for x in xs])} | champ_hi {q([x['champ_hi'] for x in xs])} | "
              f"n_gammas min {min(n_g)} med {int(np.median(n_g))} max {max(n_g)} sum {sum(n_g)} | "
              f"capped {sum(x['n_capped'] for x in xs)} | above_range {sum(x['n_above_range'] for x in xs)} | "
              f"no selection {sum(x['selected'] is None for x in xs)} | "
              f"selected clipped_high {sum(bool(x['selected'] and x['selected']['clipped_high']) for x in xs)}")
    print(f"  max stable γ̂ (pos arm): {q([r['arms']['pos']['max_stable_gamma_hat'] for r in recs])}")
    print(f"  max stable domain end b (pos arm): {q([r['arms']['pos']['max_stable_b'] for r in recs])}")
    ratio = [r["q0_stop"] / r["gamma_pos"] for r in recs if r["q0_stop"] is not None]
    print(f"  q0_stop / γ_pos: {q(ratio)}; q0_stop missing: {sum(r['q0_stop'] is None for r in recs)}")
    print(f"  q0_stop > 3.00: {sum(r['q0_stop'] is not None and r['q0_stop'] > 3.0 for r in recs)}")
    print(f"  GM22 §J.2 check: {sum(r['gm_check']['n'] for r in recs)} assortative partitions, "
          f"{sum(r['gm_check']['violations'] for r in recs)} violations, max γ̂/γ_max(K) "
          f"{max(r['gm_check']['max_ratio'] for r in recs):.4f}")
    o100 = [r for r in recs if r["first_over_100_conn"] is not None]
    print(f"  GM22 SNAP '> 100 communities' (groups with an edge) triggers on {len(o100)} graphs "
          f"(n_connected > 100 on {sum(r['n_connected'] > 100 for r in recs)}); at γ: {q([r['first_over_100_conn'] for r in o100])}"
          f"; as share of γ_max: {q([r['first_over_100_conn'] / r['gamma_max'] for r in o100])}")
    for ref, other in [("pos", x) for x in arms if x != "pos"] + ([("jsf", "jsf_q0")] if "jsf" in arms else []):
        compare(recs, ref, other)


def main():
    gm = json.loads((HERE / "scan_ends_gmK.json").read_text())
    describe("Lift, scan to max(γ_pos, γ_max(K))", gm, ["pos", "q0stop", "gmK"])
    p = HERE / "scan_ends_jsf.json"
    if p.exists():
        js = json.loads(p.read_text())
        describe("Lift sample, scan to γ_max", js, ["pos", "q0stop", "gmK", "jsf", "jsf_q0"])


if __name__ == "__main__":
    main()
