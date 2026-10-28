"""The Connection Ratio and the Connection Share between Clusters (spec: .scratch/bilingual-cluster-views/spec.md,
"Connection Ratio and Connection Share"; ADR 0004)."""

from __future__ import annotations

import itertools
import math

import networkx as nx
import pytest

from steamstudy.network import metrics as M
from steamstudy.network.cluster import Cluster

POOL = "one_tag_pool"


def _graph(edges: list[tuple[int, int, float, float]], nodes: list[int]) -> nx.Graph:
    """Edges as (u, v, w, shared): w is the Clustering Weight, shared the shared-game count."""
    g = nx.Graph()
    g.add_nodes_from(nodes)
    for u, v, w, shared in edges:
        g.add_edge(u, v, w=w, shared=shared, lift=w)
    return g


# Two Multi-Tag Clusters (C1 = 1,2,3; C2 = 4,5) and four One-Tag Clusters: 6 and 7 linked to the network, 8 linked
# only to 6 (a pool-pool link), 9 isolated.
CLUSTERS = [Cluster("C1", frozenset({1, 2, 3})), Cluster("C2", frozenset({4, 5})), Cluster("C3", frozenset({6})),
            Cluster("C4", frozenset({7})), Cluster("C5", frozenset({8})), Cluster("C6", frozenset({9}))]
EDGES = [(1, 2, 5.0, 5), (2, 3, 4.0, 4), (1, 3, 3.0, 3), (4, 5, 6.0, 6),  # inside
         (3, 4, 2.0, 2), (1, 5, 1.5, 3),  # C1-C2
         (2, 6, 1.0, 2), (5, 7, 2.5, 5), (6, 8, 0.5, 2)]  # to the pool, and pool-pool


def _brute(g: nx.Graph, clusters: list[Cluster], attr: str) -> dict[tuple[str, str], dict[str, float | None]]:
    """The measures straight from the definitions, one edge and one tag at a time."""
    group = {t: (c.label if c.size >= 2 else POOL) for c in clusters for t in c.members}
    k = {t: sum(d[attr] for _, _, d in g.edges(t, data=True)) for t in g.nodes}
    two_m = sum(k.values())
    out = {}
    labels = sorted({*group.values()} - {POOL}) + [POOL]
    for a, b in [*itertools.combinations(labels, 2), (POOL, POOL)]:
        w = sum(d[attr] for u, v, d in g.edges(data=True) if {group[u], group[v]} == {a, b}
                and (a != b or group[u] == group[v] == a))
        ka = sum(k[t] for t in group if group[t] == a)
        kb = sum(k[t] for t in group if group[t] == b)
        if a == b:
            expected = sum(k[s] * k[t] for s, t in itertools.combinations([t for t in group if group[t] == a], 2)) / two_m
        else:
            expected = ka * kb / two_m
        out[(a, b)] = {"w": w, "ratio": w / expected if expected else None}
    return out


def _cut(g: nx.Graph, clusters: list[Cluster], label: str) -> float:
    group = {t: (c.label if c.size >= 2 else POOL) for c in clusters for t in c.members}
    if label == POOL:  # every link touching a pool tag, pool-pool links once
        return sum(d["w"] for u, v, d in g.edges(data=True) if POOL in (group[u], group[v]))
    return sum(d["w"] for u, v, d in g.edges(data=True) if (group[u] == label) != (group[v] == label))


def test_every_column_matches_the_definitions_on_a_hand_built_graph():
    g = _graph(EDGES, list(range(1, 10)))
    rows = {(r.cluster_a, r.cluster_b): r for r in M.connections(g, CLUSTERS)}
    assert set(rows) == {("C1", "C2"), ("C1", POOL), ("C2", POOL), (POOL, POOL)}
    w, shared = _brute(g, CLUSTERS, "w"), _brute(g, CLUSTERS, "shared")
    for (a, b), r in rows.items():
        assert r.weight == pytest.approx(w[(a, b)]["w"]) and r.shared_weight == pytest.approx(shared[(a, b)]["w"])
        assert r.ratio == pytest.approx(w[(a, b)]["ratio"]) and r.shared_ratio == pytest.approx(shared[(a, b)]["ratio"])
        assert r.share_of_a == pytest.approx(r.weight / _cut(g, CLUSTERS, a))
        assert r.share_of_b == pytest.approx(r.weight / _cut(g, CLUSTERS, b))
    assert rows[("C1", "C2")].edge_count == 2 and rows[("C1", "C2")].weight == 3.5


def test_each_clusters_shares_and_the_pools_add_up_to_one():
    g = _graph(EDGES, list(range(1, 10)))
    rows = M.connections(g, CLUSTERS)
    for label in ("C1", "C2", POOL):
        shares = [r.share_of_a for r in rows if r.cluster_a == label] + \
                 [r.share_of_b for r in rows if r.cluster_b == label and r.cluster_a != label]
        assert math.fsum(shares) == pytest.approx(1.0), label


def test_under_shared_games_the_shared_columns_equal_the_others():
    g = _graph([(u, v, float(s), s) for u, v, _, s in EDGES], list(range(1, 10)))
    for r in M.connections(g, CLUSTERS):
        assert r.shared_weight == r.weight and r.shared_ratio == pytest.approx(r.ratio)


def test_undefined_values_are_empty_never_zero():
    # a pool of isolated tags only: k_p = 0
    g = _graph([(1, 2, 1.0, 1), (3, 4, 1.0, 1), (2, 3, 1.0, 1)], [1, 2, 3, 4, 5, 6])
    clusters = [Cluster("C1", frozenset({1, 2})), Cluster("C2", frozenset({3, 4})), Cluster("C3", frozenset({5})),
                Cluster("C4", frozenset({6}))]
    rows = {(r.cluster_a, r.cluster_b): r for r in M.connections(g, clusters)}
    assert rows[("C1", POOL)].ratio is None and rows[(POOL, POOL)].ratio is None
    assert rows[("C1", POOL)].share_of_b is None and rows[("C1", "C2")].ratio is not None
    # fewer than two linked pool tags: E_pp = 0
    g = _graph([(1, 2, 1.0, 1), (2, 5, 1.0, 1)], [1, 2, 5, 6])
    clusters = [Cluster("C1", frozenset({1, 2})), Cluster("C2", frozenset({5})), Cluster("C3", frozenset({6}))]
    rows = {(r.cluster_a, r.cluster_b): r for r in M.connections(g, clusters)}
    assert rows[(POOL, POOL)].ratio is None and rows[("C1", POOL)].ratio is not None
    # a Cluster with no outside links: its shares are empty
    g = _graph([(1, 2, 1.0, 1), (3, 4, 1.0, 1)], [1, 2, 3, 4])
    rows = M.connections(g, [Cluster("C1", frozenset({1, 2})), Cluster("C2", frozenset({3, 4}))])
    assert rows[0].share_of_a is None and rows[0].share_of_b is None and rows[0].ratio == 0.0


@pytest.mark.parametrize("weight", ["shared_games", "lift"])
@pytest.mark.parametrize("gamma", [0.5, 1.0, 2.5])
def test_the_ratio_never_exceeds_the_resolution_on_test_build_states(tagged_build, weight, gamma):
    """The merge test Louvain passes: a pair above γ would have been merged (pool rows included)."""
    from steamstudy.app.loader import load_build
    from steamstudy.network.state import compute_state

    ctx = load_build(tagged_build)
    ratios = []
    for dataset in ("overall", "puzzle"):
        s = ctx.default_settings(dataset).with_(clustering_weight=weight, resolution=gamma, min_shared_games=3)
        state = compute_state(ctx.games(dataset), s, ctx.context(dataset))
        ratios += [r.ratio for r in state.connections if r.ratio is not None]
    assert ratios and max(ratios) <= gamma + 1e-6, max(ratios)
