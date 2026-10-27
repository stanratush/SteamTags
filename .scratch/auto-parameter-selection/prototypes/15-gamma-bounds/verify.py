"""Throwaway: brute-force check of the bound claims in research note 15 on small random weighted graphs.

Enumerates every set partition of n ≤ 9 nodes (Bell(9) = 21,147), with random positive weights, isolated
nodes and several components, and checks:

1. γ_max = max_edges 2m·w/(k_i k_j): below it some partition beats all-singletons, at and above it nothing does.
2. γ_min (components) = min over components c and bipartitions S of c of 2m·cut(S)/(vol S·vol(c∖S)):
   below it the component partition is optimal, above it something beats it; λ2 and the sweep cut bracket it.
3. Every partition's ω_in = Â/P̂ is ≤ γ_pos (root of F), γ_pos < γ_max, and every γ̂ < ω_in.

    uv run python .scratch/auto-parameter-selection/prototypes/15-gamma-bounds/verify.py
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import bounds as BD  # noqa: E402


def set_partitions(n):
    """All set partitions of range(n) as label arrays (restricted growth strings)."""
    def rec(i, labels, k):
        if i == n:
            yield np.array(labels)
            return
        for c in range(k + 1):
            labels.append(c)
            yield from rec(i + 1, labels, max(k, c + 1))
            labels.pop()
    yield from rec(0, [], 0)


def random_graph(rng, n):
    while True:
        p = rng.uniform(0.2, 0.7)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
        n_iso = rng.integers(0, 2)
        pairs = [(i, j) for i, j in pairs if i < n - n_iso and j < n - n_iso]
        if len(pairs) >= 2:
            break
    u = np.array([a for a, _ in pairs])
    v = np.array([b for _, b in pairs])
    w = rng.choice([rng.uniform(0.1, 5.0, len(u)), rng.integers(1, 6, len(u)).astype(float)])
    return u, v, w


def main():
    rng = np.random.default_rng(15)
    checked = 0
    for trial in range(60):
        n = int(rng.integers(5, 10))
        u, v, w = random_graph(rng, n)
        k = BD.strengths(n, u, v, w)
        two_m = k.sum()
        M = np.array(list(set_partitions(n)))
        same = M[:, u] == M[:, v]
        A = 2.0 * (same * w).sum(1)
        P = np.array([(np.bincount(m, k) ** 2).sum() / two_m for m in M])
        single = np.argmax([len(np.unique(m)) for m in M])  # all-singletons
        gmax, _ = BD.gamma_max(u, v, w, k)
        eps = 1e-7 * max(1.0, gmax)
        # 1. γ_max
        assert (A - (gmax - eps) * P).max() > A[single] - (gmax - eps) * P[single] + 1e-12
        for g in (gmax, gmax * 1.01, gmax * 3):
            assert (A - g * P).max() <= A[single] - g * P[single] + 1e-9 * two_m
        # 2. γ_min for the component partition
        comps = BD.components(n, u, v, k)
        cm = np.full(n, -1)
        for ci, idx in enumerate(comps):
            cm[idx] = ci
        nxt = len(comps)
        for i in np.flatnonzero(cm < 0):
            cm[i] = nxt
            nxt += 1
        a0, p0 = BD.coeffs(cm, u, v, w, k)
        exact, lam, sweep = math.inf, math.inf, math.inf
        for idx in comps:
            if len(idx) < 2:
                continue
            cu, cv, cw = BD.comp_arrays(idx, u, v, w)
            exact = min(exact, BD.exact_min_cut_ratio(len(idx), cu, cv, cw, two_m))
            lo, hi = BD.lam2_and_sweep(len(idx), cu, cv, cw, two_m)
            lam, sweep = min(lam, lo), min(sweep, hi)
        assert lam <= exact + 1e-9 and exact <= sweep + 1e-9
        for g in (exact * 0.5, exact * (1 - 1e-7)):
            assert (A - g * P).max() <= a0 - g * p0 + 1e-9 * two_m
        assert (A - exact * (1 + 1e-6) * P).max() > a0 - exact * (1 + 1e-6) * p0
        # brute-force γ_min from all partitions with more groups-with-strength than the component partition
        ngs = np.array([len(np.unique(m[k > 0])) for m in M])
        nontriv = (ngs > len(comps)) & (P < p0 - 1e-12)
        brute = ((a0 - A[nontriv]) / (p0 - P[nontriv])).min()
        assert abs(brute - exact) <= 1e-9 * max(1, exact), (brute, exact)
        # 3. γ_pos
        gpos = BD.gamma_pos(u, v, w, k)
        pos = P > 0
        omega_in = A[pos] / P[pos]
        assert omega_in.max() <= gpos + 1e-9 and gpos < gmax
        assert omega_in.max() >= 0
        for i in np.flatnonzero(pos & (A > P) & (ngs >= 2) & (A < two_m)):
            wi, wo = A[i] / P[i], (two_m - A[i]) / (two_m - P[i])
            gh = (wi - wo) / (math.log(wi) - math.log(wo))
            assert wo < gh < wi
        checked += 1
        if trial < 6:
            print(f"n={n} E={len(u)} comps={len(comps)} iso={(k == 0).sum()}: γ_min {exact:.4f} in [{lam:.4f}, {sweep:.4f}], "
                  f"max ω_in {omega_in.max():.4f} ≤ γ_pos {gpos:.4f} < γ_max {gmax:.4f}")
    print(f"all checks passed on {checked} random graphs")


if __name__ == "__main__":
    main()
