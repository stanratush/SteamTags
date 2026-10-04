"""Seed streams, the game–tag shuffle null model, the Seed-Noise Floor and Membership Stability."""

from __future__ import annotations

import random
import statistics
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import adjusted_rand_score

from steamstudy.network.cluster import Cluster, detect, label_clusters
from steamstudy.network.graph import shared_edges, to_graph
from steamstudy.network.model import Game

NULL_STREAM, NOISE_STREAM = 1, 2
TRADES_PER_GAME = 10
SEED_MASK = 0x7FFFFFFF  # seeds stay within a signed 32-bit int for both clustering libraries


def derive_seeds(main_seed: int, stream: int, n: int, exclude: set[int] | frozenset[int] = frozenset()) -> list[int]:
    """n distinct seeds from the main seed through their own stream, avoiding `exclude`."""
    if main_seed < 0:
        raise ValueError("the seed must be a non-negative integer")
    out: list[int] = []
    taken = set(exclude) | {main_seed}
    batch = 0
    while len(out) < n:
        entropy = [main_seed & 0xFFFFFFFF, main_seed >> 32, stream, batch]
        for value in np.random.SeedSequence(entropy).generate_state(n * 2):
            seed = int(value) & SEED_MASK
            if seed not in taken:
                taken.add(seed)
                out.append(seed)
                if len(out) == n:
                    break
        batch += 1
    return out


def replicate_seeds(main_seed: int, r: int) -> list[int]:
    return derive_seeds(main_seed, NULL_STREAM, r)


def noise_seeds(main_seed: int, k: int, r: int) -> list[int]:
    """Noise seeds never share a seed with the null-model replicate seeds."""
    return derive_seeds(main_seed, NOISE_STREAM, k, exclude=set(replicate_seeds(main_seed, r)))


# ----------------------------------------------------------------------------- null model


def curveball(rows: list[frozenset[int]], trades: int, rng: random.Random) -> list[frozenset[int]]:
    """Curveball trades on a game–tag table: every game's tag count and every tag's game count are preserved."""
    table = [set(r) for r in rows]
    n = len(table)
    if n < 2:
        return [frozenset(r) for r in table]
    for _ in range(trades):
        i = rng.randrange(n)
        j = rng.randrange(n - 1)
        if j >= i:
            j += 1
        a, b = table[i], table[j]
        a_only, b_only = a - b, b - a
        if not a_only or not b_only:
            continue
        pool = sorted(a_only | b_only)
        rng.shuffle(pool)
        shared = a & b
        table[i] = shared | set(pool[:len(a_only)])
        table[j] = shared | set(pool[len(a_only):])
    return [frozenset(r) for r in table]


@dataclass(frozen=True)
class NullReplicate:
    replicate: int
    seed: int
    modularity: float | None
    n_edges: int


def null_model(games: list[Game], nodes: list[int], min_shared: int, settings_weight: str, algorithm: str,
               resolution: float, seeds: list[int],
               modularity_fn: Callable[..., float | None]) -> list[NullReplicate]:
    """Shuffle the game–tag table over the same games and visible tags, rebuild, recluster, record Q."""
    visible = set(nodes)
    rows = [frozenset(t for t in g.tag_ids if t in visible) for g in games]
    out = []
    for i, seed in enumerate(seeds, start=1):
        shuffled = curveball(rows, TRADES_PER_GAME * len(rows), random.Random(seed))
        fake = [Game(g.appid, g.name, g.rank, g.months_observed, tuple(sorted(r)), ()) for g, r in zip(games, shuffled)]
        tag_games: dict[int, set[int]] = {t: set() for t in nodes}
        for g in fake:
            for t in g.tag_ids:
                tag_games[t].add(g.appid)
        edges = shared_edges(fake, nodes, {t: frozenset(s) for t, s in tag_games.items()}, min_shared)
        graph = to_graph(nodes, edges, settings_weight)
        clusters = label_clusters(detect(graph, algorithm, resolution, seed))
        out.append(NullReplicate(i, seed, modularity_fn(graph, clusters, resolution), len(edges)))
    return out


def sample_sd(values: list[float]) -> float | None:
    return statistics.stdev(values) if len(values) >= 2 else None


# ----------------------------------------------------------------------------- seed noise


def ari(nodes: list[int], a: dict[int, str], b: dict[int, str]) -> float:
    if not nodes:
        return 1.0
    return float(adjusted_rand_score([a[t] for t in nodes], [b[t] for t in nodes]))


def membership_stability(nodes: list[int], degree: dict[int, int], main: list[Cluster],
                         seeds: list[list[Cluster]]) -> dict[int, float | None]:
    """Mean over seeds of |A ∩ B| / |A ∪ B| for v's main cluster A and seed cluster B (both include v)."""
    main_of = {t: c.members for c in main for t in c.members}
    out: dict[int, float | None] = {}
    seed_maps = [{t: c.members for c in clusters for t in c.members} for clusters in seeds]
    for t in nodes:
        if degree[t] == 0:
            out[t] = None
            continue
        a = main_of[t]
        values = [len(a & m[t]) / len(a | m[t]) for m in seed_maps]
        out[t] = statistics.fmean(values) if values else None
    return out
