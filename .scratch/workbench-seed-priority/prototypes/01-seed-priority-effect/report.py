"""Throwaway: facts from measure.py's results.json, counted by Threshold Pair (graphs weighted by their pairs).

    uv run python .scratch/workbench-seed-priority/prototypes/01-seed-priority-effect/report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def main():
    doc = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    gs = doc["graphs"]
    pairs = lambda sel: sum(g["n_pairs"] for g in sel)  # noqa: E731
    print(f"build {doc['build_id']}, {len(gs)} graphs = {pairs(gs)} pairs with a Selected Partition, "
          f"{doc['seconds']:.0f} s")
    for mode in ("closest", "main"):
        rep = [g for g in gs if g[mode]["flag"] is None]
        main = [g for g in rep if g[mode]["seed_kind"] == "main"]
        at_mid = [g for g in rep if g[mode]["gamma"] == min(
            (round(i / 100, 2) for i in range(1, 10000) if g["a"] <= i / 100 <= g["b"]),
            key=lambda x: (abs(x - g["mid"]), x))]
        print(f"{mode:8} reproduced {pairs(rep)}, with main seed {pairs(main)}, at nearest-to-midpoint γ {pairs(at_mid)}")
    ch = [g for g in gs if (g["main"]["gamma"], g["main"]["seed"]) != (g["closest"]["gamma"], g["closest"]["seed"])]
    print(f"\nmodes disagree: {len(ch)} graphs = {pairs(ch)} pairs")
    if not ch:
        return
    dg = [abs(g["main"]["gamma"] - g["mid"]) - abs(g["closest"]["gamma"] - g["mid"]) for g in ch]
    rel = [abs(g["main"]["gamma"] - g["mid"]) / ((g["b"] - g["a"]) / 2) for g in ch]
    print(f"extra distance from midpoint (main − closest): median {statistics.median(dg):.3f}, "
          f"p90 {q(dg, .9):.3f}, max {max(dg):.3f}")
    print(f"main-mode γ position, share of half-domain from midpoint: median {statistics.median(rel):.2f}, "
          f"p90 {q(rel, .9):.2f}, max {max(rel):.2f}")
    print(f"edge room (1 = midpoint, 0 = edge): closest median {statistics.median(g['closest']['edge_room'] for g in ch):.2f}"
          f", main median {statistics.median(g['main']['edge_room'] for g in ch):.2f}, "
          f"main min {min(g['main']['edge_room'] for g in ch):.2f}")
    dq = [g["main"]["q"] - g["closest"]["q"] for g in ch]
    print(f"ΔQ (main − closest): median {statistics.median(dq):+.4f}, range {min(dq):+.4f} … {max(dq):+.4f}")
    for k in ("floor", "mean"):
        c = [g["closest"]["noise"][k] for g in ch]
        m = [g["main"]["noise"][k] for g in ch]
        d = [y - x for x, y in zip(c, m)]
        print(f"Workbench seed-noise {k}: closest median {statistics.median(c):.3f}, main median "
              f"{statistics.median(m):.3f}; Δ median {statistics.median(d):+.3f}, range {min(d):+.3f} … {max(d):+.3f}, "
              f"main lower in {sum(x < 0 for x in d)}/{len(d)} graphs")
    for mode in ("closest", "main"):
        gap = [abs(g[mode]["noise"]["floor"] - g["ps_floor"]) for g in ch]
        print(f"|Workbench floor − Parameter Selection floor|, {mode}: median {statistics.median(gap):.3f}, "
              f"max {max(gap):.3f}")
    print("\nchosen pairs (default constraints):")
    by = {g["hash"]: g for g in gs}
    for d, (g_, s_, h) in doc["chosen"].items():
        r = by.get(h)
        if r is None:
            print(f"  {d} {g_},{s_}: no Selected Partition")
            continue
        c, m = r["closest"], r["main"]
        same = (c["gamma"], c["seed"]) == (m["gamma"], m["seed"])
        line = f"  {d} {g_},{s_}: mid {r['mid']:.3f} [{r['a']:.3f}, {r['b']:.3f}]; closest γ {c['gamma']} {c['seed_kind']}"
        line += " = main mode" if same else f"; main γ {m['gamma']} {m['seed_kind']}"
        if not same:
            line += (f"; Q {c['q']:.4f} → {m['q']:.4f}; floor {c['noise']['floor']:.3f} → {m['noise']['floor']:.3f}"
                     f" (PS {r['ps_floor']:.3f})")
        print(line)


if __name__ == "__main__":
    main()
