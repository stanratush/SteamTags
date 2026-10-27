"""Throwaway: names the tags behind the extreme bounds (ticket 15).

For the graphs with the extreme γ_max and the lowest γ_min, prints the γ_max edge with its tags' names, shared
games and strengths, and the Fiedler sweep cut's small side.

    uv run python .scratch/auto-parameter-selection/prototypes/15-gamma-bounds/inspect_extremes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "05-grid-run"))
sys.path.insert(0, str(HERE))
import bounds as BD  # noqa: E402
import grid_run as GR  # noqa: E402

CASES = [("rpg", 3, 3), ("rpg", 18, 2), ("overall", 3, 2), ("strategy", 8, 8), ("puzzle", 3, 3), ("puzzle", 20, 2)]


def main():
    from steamstudy.network.graph import build_network

    B = {(r["dataset"], r["g"], r["s"]): r for r in json.loads((HERE / "bounds.json").read_text())["records"]}
    low = sorted(B.values(), key=lambda r: r["lift_jeub_upper"])[:5]
    cases = CASES + [(r["dataset"], r["g"], r["s"]) for r in low]
    GR.init_worker(tuple(sorted({c[0] for c in cases})))
    for d, g, s in dict.fromkeys(cases):
        games, context, base = GR._W["data"][d]
        net = build_network(games, base.with_(min_games_per_tag=g, min_shared_games=s), context)
        nodes = net.nodes
        n = len(nodes)
        idx = {t: i for i, t in enumerate(nodes)}
        u = np.array([idx[e.u] for e in net.edges])
        v = np.array([idx[e.v] for e in net.edges])
        w = np.array([e.lift for e in net.edges])
        k = BD.strengths(n, u, v, w)
        gm, ei = BD.gamma_max(u, v, w, k)
        e = net.edges[ei]
        nm = net.tag_names
        print(f"{d} g={g} s={s}: {n} tags, γ_max {gm:.2f} on {nm[e.u]} – {nm[e.v]} (shared {e.shared}, "
              f"n {net.n(e.u)} and {net.n(e.v)} games, Lift {e.lift:.2f}, strengths {k[u[ei]]:.2f}, {k[v[ei]]:.2f}; "
              f"2m {k.sum():.1f}); γ_pos {B[(d, g, s)]['lift_gamma_pos']:.2f}")
        # the best bipartition found by the sweep, small side
        comps = BD.components(n, u, v, k)
        cidx = max(comps, key=len)
        cu, cv, cw = BD.comp_arrays(cidx, u, v, w)
        W = np.zeros((len(cidx), len(cidx)))
        W[cu, cv] = cw
        W[cv, cu] = cw
        dg = W.sum(1)
        dm = 1 / np.sqrt(dg)
        L = np.eye(len(cidx)) - dm[:, None] * W * dm[None, :]
        _, vecs = np.linalg.eigh(L)
        f = dm * vecs[:, 1]
        order = np.argsort(f)
        best, best_j, volS = np.inf, None, 0.0
        inS = np.zeros(len(cidx), bool)
        for j, t in enumerate(order[:-1]):
            inS[t] = True
            volS += dg[t]
            cut = cw[inS[cu] != inS[cv]].sum()
            r = k.sum() * cut / (volS * (dg.sum() - volS))
            if r < best:
                best, best_j = r, j
        side = order[: best_j + 1]
        other = order[best_j + 1:]
        small = side if len(side) <= len(other) else other
        small_names = [nm[nodes[cidx[t]]] for t in small]
        print(f"   sweep γ_min upper {best:.3f}; Jeub {B[(d, g, s)]['lift_jeub_upper']:.3f}; small side "
              f"({len(small)} tags): {', '.join(small_names[:12])}{' …' if len(small) > 12 else ''}")


if __name__ == "__main__":
    main()
