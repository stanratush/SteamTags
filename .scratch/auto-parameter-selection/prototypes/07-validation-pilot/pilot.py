"""Throwaway pilot for the ticket "Validation design": the full procedure on curveball nulls and 80% subsamples
of each dataset's chosen pair (ticket 06), plus Q and the partition at the observed Selected Resolution read from
each replicate's own CHAMP envelope. Reuses ../05-grid-run/grid_run.py. Seeds are ad hoc (1000 + r, 2000 + r),
not the decided streams. Output: output.txt (5 nulls and 5 subsamples per dataset).

    .venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/07-validation-pilot/pilot.py 5
"""
import random
import sys
import time
from dataclasses import replace

import numpy as np

sys.path.insert(0, ".scratch/auto-parameter-selection/prototypes/05-grid-run")
import grid_run as G  # noqa: E402

from sklearn.metrics import adjusted_rand_score  # noqa: E402
from steamstudy.network.graph import build_network  # noqa: E402
from steamstudy.network.stability import curveball  # noqa: E402

CHOSEN = {"overall": (17, 2), "puzzle": (14, 2), "rpg": (14, 12), "simulation": (14, 5), "strategy": (14, 2)}
R = int(sys.argv[1]) if len(sys.argv) > 1 else 5

G.init_worker(G.DATASETS)
_CAP = {}
_orig_select = G.select
_orig_scan = G.scan


def _scan(*a, **k):
    out = _orig_scan(*a, **k)
    _CAP["parts"] = out[0]
    return out


def _select(parts, *a, **k):
    res = _orig_select(parts, *a, **k)
    _CAP["res"] = res
    return res


G.scan, G.select = _scan, _select


def env_at(gamma):
    res = _CAP["res"]
    best = max(res["admissible"], key=lambda x: x["A"] - gamma * x["P"])
    return (best["A"] - gamma * best["P"]) / res["two_m"], _CAP["parts"][best["part"]]


def run(dataset, games, g, s):
    _, context, base = G._W["data"][dataset]
    saved = G._W["data"][dataset]
    G._W["data"][dataset] = (games, context, base)
    try:
        return G.compute_pair((dataset, g, s, False))
    finally:
        G._W["data"][dataset] = saved


def champ_at(rec, gamma):
    best = None
    for x in rec.get("admissible", []):
        if x["a"] <= gamma <= x["b"]:
            best = x
    return best


for d, (g, s) in CHOSEN.items():
    games, context, base = G._W["data"][d]
    obs = run(d, games, g, s)
    sel = obs["selected"]
    nodes = obs["nodes"]
    names = {t: n for gm in games for t, n in zip(gm.tag_ids, gm.tags)}
    nodeset = set(nodes)
    print(f"\n== {d} g={g} s={s}: tags {obs['n_tags']} edges {obs['n_edges']} multi {sel['n_multi']} "
          f"width {sel['width']:.3f} mid {sel['selected_resolution']:.3f} scan {obs['scan_seconds']:.2f}s")
    # nulls
    rows = [frozenset(t for t in gm.tag_ids if t in nodeset) for gm in games]
    t0 = time.perf_counter()
    for r in range(R):
        sh = curveball(rows, 10 * len(rows), random.Random(1000 + r))
        fake = []
        for gm, row in zip(games, sh):
            other = [t for t in gm.tag_ids if t not in nodeset]
            ids = tuple(sorted(other + list(row)))
            fake.append(replace(gm, tag_ids=ids, tags=tuple(names[t] for t in ids)))
        rec = run(d, fake, g, s)
        ns = rec["selected"]
        qfix = env_at(sel["selected_resolution"])[0] if rec["n_edges"] else None
        print(f"  null Q@obs-gamma {qfix:.3f} |", end="")
        print(f"  null {r}: edges {rec['n_edges']} uniq {rec.get('n_unique')} adm {rec.get('n_admissible')} "
              f"stable {rec.get('n_stable')} reason {rec['no_selection_reason']} "
              + (f"multi {ns['n_multi']} width {ns['width']:.3f} mid {ns['selected_resolution']:.3f} Qsel {ns['Q']:.3f}"
                 if ns else "") + f"  obsQ {sel['Q']:.3f}  {rec['seconds']:.2f}s")
    tn = time.perf_counter() - t0
    # subsamples
    t0 = time.perf_counter()
    m_obs = dict(zip(nodes, sel["membership"]))
    for r in range(R):
        rng = random.Random(2000 + r)
        sub = rng.sample(games, (len(games) * 4) // 5)
        g2, s2 = (g * 4) // 5, max(2, (s * 4) // 5)
        rec = run(d, sub, g2, s2)
        ns = rec["selected"]
        mfix = dict(zip(rec["nodes"], env_at(sel["selected_resolution"])[1]))
        edged0 = set(obs["edged"]) | set(rec["edged"])
        sh0 = [t for t in nodes if t in mfix and t in edged0]
        afix = adjusted_rand_score([m_obs[t] for t in sh0], [mfix[t] for t in sh0])
        print(f"  fixed-gamma ARI {afix:.3f} |", end="")
        txt = f"reason {rec['no_selection_reason']}"
        if ns:
            m_sub = dict(zip(rec["nodes"], ns["membership"]))
            edged = set(obs["edged"]) | set(rec["edged"])
            shared = [t for t in nodes if t in m_sub and t in edged]
            ari = adjusted_rand_score([m_obs[t] for t in shared], [m_sub[t] for t in shared])
            txt = (f"tags {rec['n_tags']} shared {len(shared)}/{len(nodes)} multi {ns['n_multi']} "
                   f"mid {ns['selected_resolution']:.3f} ARI {ari:.3f}")
        print(f"  sub {r} (g'={g2}, s'={s2}): {txt}  {rec['seconds']:.2f}s")
    ts = time.perf_counter() - t0
    print(f"  time: {R} nulls {tn:.1f}s, {R} subsamples {ts:.1f}s")
