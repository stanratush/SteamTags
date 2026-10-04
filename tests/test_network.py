"""Seam 3: `steamstudy.network` on small hand-built datasets (expected values worked out by hand)."""

from __future__ import annotations

import hashlib
import random
from collections import Counter

import pytest

from steamstudy.network import metrics as M
from steamstudy.network.cluster import Cluster, label_clusters
from steamstudy.network.graph import to_graph
from steamstudy.network.model import KEY_VERSION, Game, Settings, TagContext, canonical_key_json, state_id_of
from steamstudy.network.sensitivity import removal_sensitivity, run_order
from steamstudy.network.stability import curveball, noise_seeds, replicate_seeds
from steamstudy.network.state import compute_state
from steamstudy.network.sweep import resolution_sweep, sweep_grid
from steamstudy.network.tables import state_tables

A, B, C, D, E, F, G, H = 1, 2, 3, 4, 5, 6, 7, 8
NAMES = dict(zip((A, B, C, D, E, F, G, H), "ABCDEFGH"))


def _games(spec: list[tuple[tuple[int, ...], int]], months: list[int] | None = None) -> list[Game]:
    rows = [tags for tags, n in spec for _ in range(n)]
    months = months or [12] * len(rows)
    return [Game(1000 + i, f"game {i}", i + 1, months[i], tuple(t), tuple(NAMES.get(x, f"t{x}") for x in t))
            for i, t in enumerate(rows)]


# Two triangles and an isolated tag:
#   g1-g3: A B C    g4-g6: D E F    g7: G A    g8: G D    g9: H
# Tag counts A 4, B 3, C 3, D 4, E 3, F 3, G 2, H 1; N = 9.
# At 2/2 thresholds: edges A-B, A-C, B-C, D-E, D-F, E-F (3 shared games each); G isolated; H below 2 games.
TOY = _games([((A, B, C), 3), ((D, E, F), 3), ((G, A), 1), ((G, D), 1), ((H,), 1)])


def _settings(**kw) -> Settings:
    base = dict(build_id="B1", dataset="overall", min_games_per_tag=2, min_shared_games=2, seed=11,
                null_replicates=4, noise_seeds=4)
    base.update(kw)
    return Settings(**base)


@pytest.fixture(scope="module")
def toy():
    return compute_state(TOY, _settings())


# ----------------------------------------------------------------------------- network build


def test_thresholds_isolated_tags_and_not_in_network(toy):
    assert toy.nodes == [A, B, C, D, E, F, G]
    assert [(e.u, e.v, e.shared) for e in toy.network.edges] == [
        (A, B, 3), (A, C, 3), (B, C, 3), (D, E, 3), (D, F, 3), (E, F, 3)]
    assert toy.node_metrics[G].degree == 0
    assert [(n.tag_id, n.n_games, n.reasons) for n in toy.network.not_in_network] == [(H, 1, ("below_min_games",))]


def test_reasons_in_fixed_order():
    settings = _settings(hidden_tag_ids=(A, B), removed_tag_ids=(A, H))
    state = compute_state(TOY, settings, TagContext(defining_tag_id=A, genre_tag_ids=frozenset({A, B})))
    reasons = {n.tag_id: n.reasons for n in state.network.not_in_network}
    assert reasons[A] == ("removed", "defining_tag_hidden", "genre_tag_hidden")
    assert reasons[B] == ("genre_tag_hidden",)
    assert reasons[H] == ("removed", "below_min_games")


def test_minimum_months_filter_drops_games_without_backfill():
    games = _games([((A, B), 3), ((A, B), 2)], months=[30, 30, 30, 5, 5])
    state = compute_state(games, _settings(min_months=12))
    assert state.network.n_games == 3 and state.network.n(A) == 3
    emptied = compute_state(_games([((A,), 2), ((B,), 1)], months=[30, 30, 1]), _settings(min_months=12))
    assert [(n.tag_id, n.n_games) for n in emptied.network.not_in_network] == [(B, 0)]


def test_lift_formula_and_lift_unchanged_by_hiding_or_removing(toy):
    lifts = {(e.u, e.v): e.lift for e in toy.network.edges}
    assert lifts[(A, B)] == pytest.approx(3 * 9 / (4 * 3))  # 2.25
    assert lifts[(B, C)] == pytest.approx(3.0)
    hidden = compute_state(TOY, _settings(hidden_tag_ids=(D,), removed_tag_ids=(E,)))
    assert {(e.u, e.v): e.lift for e in hidden.network.edges}[(A, B)] == lifts[(A, B)]
    assert hidden.network.n_games == 9


def test_lift_below_one_edges_are_kept():
    # A on 8 of 10 games, B on 8: they share 6 (expected 6.4), lift 0.9375 < 1, still an edge.
    games = _games([((A, B), 6), ((A,), 2), ((B,), 2)])
    state = compute_state(games, _settings(clustering_weight="lift"))
    assert [(e.u, e.v, e.shared) for e in state.network.edges] == [(A, B, 6)]
    assert state.network.edges[0].lift == pytest.approx(0.9375)


def test_edge_appids_are_the_intersection_in_rank_order(toy):
    assert toy.network.edge_appids(A, B) == [1000, 1001, 1002]
    assert toy.network.edge_appids(G, A) == [1006]


# ----------------------------------------------------------------------------- clustering and labels


def test_clusters_labels_and_one_tag_clusters(toy):
    assert [(c.label, sorted(c.members)) for c in toy.clusters] == [("C1", [A, B, C]), ("C2", [D, E, F]), ("C3", [G])]


def test_label_tie_rule():
    clusters = label_clusters([frozenset({9}), frozenset({5, 6}), frozenset({2, 7}), frozenset({1}), frozenset({3, 4, 8})])
    assert [(c.label, sorted(c.members)) for c in clusters] == [
        ("C1", [3, 4, 8]), ("C2", [2, 7]), ("C3", [5, 6]), ("C4", [1]), ("C5", [9])]


def _random_games(seed: int, n: int = 100, tags: int = 40) -> list[Game]:
    rng = random.Random(seed)
    games = []
    for i in range(n):
        group = rng.randrange(4)
        pool = list(range(1 + group * 10, 11 + group * 10))
        chosen = set(rng.sample(pool, 5)) | set(rng.sample(range(1, tags + 1), 3))
        games.append(Game(i + 1, f"g{i}", i + 1, 12, tuple(sorted(chosen)), tuple(f"t{t}" for t in sorted(chosen))))
    return games


@pytest.mark.parametrize("algorithm", ["louvain", "leiden"])
def test_seeded_clustering_is_deterministic(algorithm):
    games = _random_games(3)
    settings = _settings(algorithm=algorithm, min_games_per_tag=5, min_shared_games=3, null_replicates=2, noise_seeds=2)
    first = compute_state(games, settings, with_positions=False)
    second = compute_state(list(reversed(games)), settings, with_positions=False)
    assert [sorted(c.members) for c in first.clusters] == [sorted(c.members) for c in second.clusters]
    assert first.modularity == second.modularity


def test_leiden_uses_the_modularity_objective(toy):
    leiden = compute_state(TOY, _settings(algorithm="leiden"))
    assert [sorted(c.members) for c in leiden.clusters] == [[A, B, C], [D, E, F], [G]]
    assert leiden.modularity == pytest.approx(0.5)  # same Q as Louvain: modularity, never CPM


def test_disconnected_cluster_is_flagged_not_split(toy):
    graph = to_graph(toy.nodes, toy.network.edges, "shared_games")
    joined = Cluster("C1", frozenset({A, B, C, D, E, F}))
    assert M.cluster_metrics(graph, joined).connected is False
    assert all(toy.cluster_metrics[c.label].connected for c in toy.clusters)


# ----------------------------------------------------------------------------- partition metrics


def test_modularity_coverage_and_conductance(toy):
    # m = 18; each triangle: internal weight 9, degree sum 18 -> Q = 2 * (9/18 - (18/36)^2) = 0.5
    assert toy.modularity == pytest.approx(0.5)
    assert toy.coverage == pytest.approx(1.0)
    c1, c3 = toy.cluster_metrics["C1"], toy.cluster_metrics["C3"]
    assert (c1.internal_edges, c1.internal_weight, c1.edge_density, c1.weighted_density) == (3, 9.0, 1.0, 3.0)
    assert c1.conductance == 0.0 and c1.cut_weight == 0.0
    assert (c3.conductance, c3.conductance_status, c3.edge_density) == (None, "isolated_tag", None)


def test_conductance_of_a_connected_one_tag_cluster_is_one():
    from steamstudy.network.graph import Edge

    graph = to_graph([A, B, C], [Edge(A, B, 5, 1.0), Edge(A, C, 5, 1.0), Edge(B, C, 1, 1.0)], "shared_games")
    m = M.cluster_metrics(graph, Cluster("C2", frozenset({C})))
    assert m.conductance == pytest.approx(1.0) and m.conductance_status is None
    whole = M.cluster_metrics(graph, Cluster("C1", frozenset({A, B, C})))
    assert whole.conductance_status == "no_edges_outside_cluster"


def test_coverage_plus_inter_share_is_one():
    state = compute_state(_random_games(5), _settings(min_games_per_tag=5, min_shared_games=3), with_positions=False)
    row = state_tables(state, cluster_positions={})["cluster_quality.csv"][0]
    assert row["coverage"] + row["inter_cluster_weight_share"] == pytest.approx(1.0)


def test_silhouette_hand_values(toy):
    # B: a = (0.25 + 0)/2, b = 1 -> 0.875; A: a = 0.25, b = min(1, d(A,G) = 0.8) -> 0.6875
    s = toy.silhouette
    assert s.per_node[B] == pytest.approx(0.875) and s.per_node[A] == pytest.approx(0.6875)
    assert s.per_node[G] is None and s.node_status[G] == "one_tag_cluster"
    assert s.mean == pytest.approx((0.6875 + 0.875 + 0.875) / 3)
    assert s.per_cluster["C3"] is None and s.cluster_status["C3"] == "one_tag_cluster"


def test_silhouette_needs_two_multi_tag_clusters():
    state = compute_state(_games([((A, B, C), 3), ((G,), 2)]), _settings())
    assert state.silhouette.mean is None and state.silhouette.status == "fewer_than_2_multi_tag_clusters"
    assert state.silhouette.node_status[A] == "fewer_than_2_multi_tag_clusters"


def test_no_edges():
    state = compute_state(_games([((A,), 2), ((B,), 2)]), _settings())
    row = state_tables(state, cluster_positions={})["cluster_quality.csv"][0]
    assert row["modularity"] is None and row["modularity_status"] == "no_edges"
    assert row["seed_ari_min"] == 1.0 and row["seed_ari_mean"] == 1.0
    assert row["n_multi_tag_clusters"] == 0 and row["n_one_tag_clusters"] == 2


# ----------------------------------------------------------------------------- centers and node metrics


def test_medoid_with_tie_and_top_strength(toy):
    center = toy.centers["C1"]
    assert center.medoid_scores == pytest.approx({A: 0.25, B: 0.125, C: 0.125})
    assert center.center == B  # B and C tie at 0.125 with 3 games each: the lower tag_id wins
    assert center.top_strength == A  # all intra strengths are 6: A has more games
    row = next(r for r in state_tables(toy, cluster_positions={})["clusters.csv"] if r["cluster"] == "C1")
    assert row["member_tag_ids"] == [B, C, A] and row["center_is_top_strength"] is False


def test_two_tag_clusters_have_no_center_but_keep_medoid_scores():
    state = compute_state(_games([((A, B), 3), ((D, E), 3)]), _settings())
    center = state.centers["C1"]
    assert center.center is None and center.center_status == "two_tag_cluster"
    assert center.medoid_scores == {A: 0.0, B: 0.0}
    assert state.centers.get("C3") is None


def test_within_z_population_sd_and_cap():
    # A star inside one cluster: hub A with B, C, D. Intra strengths A=9, B=C=D=3 (shared weights).
    games = _games([((A, B), 3), ((A, C), 3), ((A, D), 3)])
    state = compute_state(games, _settings())
    values = [9, 3, 3, 3]
    mean, sd = sum(values) / 4, (sum((v - 4.5) ** 2 for v in values) / 4) ** 0.5
    assert state.node_metrics[A].within_z == pytest.approx((9 - mean) / sd)  # sqrt(3), the cap for n = 4
    assert state.node_metrics[A].within_z == pytest.approx(M.within_z_cap(4))
    assert compute_state(TOY, _settings()).node_metrics[A].within_z is None  # equal strengths


def test_participation_with_a_one_tag_cluster_neighbour():
    from steamstudy.network.graph import Edge

    graph = to_graph([A, B, C], [Edge(A, B, 6, 1.0), Edge(A, C, 2, 1.0)], "shared_games")
    clusters = [Cluster("C1", frozenset({A, B})), Cluster("C2", frozenset({C}))]
    metrics = M.node_metrics(graph, clusters, "shared_games")
    assert metrics[A].participation == pytest.approx(1 - (6 / 8) ** 2 - (2 / 8) ** 2)
    assert metrics[C].participation == pytest.approx(0.0)


# ----------------------------------------------------------------------------- null model and seeds


def test_curveball_preserves_every_degree():
    rng = random.Random(1)
    rows = [frozenset(rng.sample(range(30), rng.randint(3, 10))) for _ in range(60)]
    shuffled = curveball(rows, 600, random.Random(2))
    assert [len(r) for r in shuffled] == [len(r) for r in rows]
    assert Counter(t for r in shuffled for t in r) == Counter(t for r in rows for t in r)
    assert shuffled != rows


def test_null_model_rebuilds_with_the_same_node_set(toy):
    assert len(toy.null_replicates) == 4
    assert [r.seed for r in toy.null_replicates] == replicate_seeds(11, 4)


def test_replicate_and_noise_seeds_never_overlap():
    for main in (0, 1, 11, 20261003, 2**40 + 5):
        r, k = replicate_seeds(main, 50), noise_seeds(main, 50, 50)
        assert len(set(r)) == 50 and len(set(k)) == 50 and not set(r) & set(k)
        assert main not in r and main not in k


def test_membership_stability_values():
    from steamstudy.network.stability import membership_stability

    main = [Cluster("C1", frozenset({A, B, C})), Cluster("C2", frozenset({D}))]
    seed1 = [Cluster("C1", frozenset({A, B})), Cluster("C2", frozenset({C, D}))]
    seed2 = [Cluster("C1", frozenset({A, B, C})), Cluster("C2", frozenset({D}))]
    values = membership_stability([A, B, C, D], {A: 2, B: 2, C: 2, D: 0}, main, [seed1, seed2])
    # A: (2/3 + 1)/2; C: (|{C}| / |{A,B,C,D}| = 1/4 + 1)/2; D has degree 0: empty
    assert values[A] == pytest.approx((2 / 3 + 1) / 2)
    assert values[C] == pytest.approx((1 / 4 + 1) / 2)
    assert values[D] is None


def test_seed_noise_and_stability_on_the_toy(toy):
    summary = toy.seed_summary()
    assert summary["seed_ari_min"] == 1.0 and summary["seed_k_min"] == summary["seed_k_max"] == 2
    assert toy.membership_stability[A] == 1.0 and toy.membership_stability[G] is None
    tables = state_tables(toy, cluster_positions={})
    assert len(tables["seed_noise.csv"]) == 4
    c3 = next(r for r in tables["clusters.csv"] if r["cluster"] == "C3")
    assert c3["mean_membership_stability"] is None


# ----------------------------------------------------------------------------- key, positions, tables


def test_state_key_canonical_json_and_state_id():
    settings = _settings(hidden_tag_ids=(9, 1), resolution=1)
    key = settings.key()
    expected = ('{"algorithm":"louvain","build_id":"B1","clustering_weight":"shared_games","dataset":"overall",'
                '"hidden_tag_ids":[1,9],"key_version":%d,"min_games_per_tag":2,"min_months":0,"min_shared_games":2,'
                '"noise_seeds":4,"null_replicates":4,"removed_tag_ids":[],"resolution":"1.00","seed":11}') % KEY_VERSION
    assert canonical_key_json(key) == expected
    assert state_id_of(key) == hashlib.sha256(expected.encode("utf-8")).hexdigest()[:12]
    assert Settings.from_key(key) == settings


def test_global_positions_do_not_depend_on_thresholds_or_hidden_tags():
    games = _random_games(9)
    loose = compute_state(games, _settings(min_games_per_tag=3, min_shared_games=2, null_replicates=2, noise_seeds=2))
    tight = compute_state(games, _settings(min_games_per_tag=8, min_shared_games=5, hidden_tag_ids=(1, 2),
                                           null_replicates=2, noise_seeds=2))
    assert all(tight.positions[t] == loose.positions[t] for t in tight.nodes)
    other_seed = compute_state(games, _settings(min_games_per_tag=8, seed=12, null_replicates=2, noise_seeds=2))
    assert other_seed.positions != tight.positions


def test_table_sorting_and_edges(toy):
    tables = state_tables(toy)
    nodes = tables["nodes.csv"]
    assert [r["tag_id"] for r in nodes] == [B, C, A, E, F, D, G]  # by cluster, then medoid_score, then tag_id
    edges = tables["edges.csv"]
    assert all(r["source_tag_id"] < r["target_tag_id"] for r in edges)
    assert edges[0] == {"source_tag_id": A, "source_tag": "A", "target_tag_id": B, "target_tag": "B",
                        "shared_games": 3, "lift": 2.25, "source_cluster": "C1", "target_cluster": "C1",
                        "is_intra_cluster": True, "appids": [1000, 1001, 1002]}
    assert tables["cluster_connections.csv"] == [
        {"cluster_a": "C1", "cluster_b": "C2", "edge_count": 0, "weight": 0.0},
        {"cluster_a": "C1", "cluster_b": "one_tag_pool", "edge_count": 0, "weight": 0.0},
        {"cluster_a": "C2", "cluster_b": "one_tag_pool", "edge_count": 0, "weight": 0.0}]
    assert all(r["x_cluster_separated"] is not None for r in nodes)


# ----------------------------------------------------------------------------- Removal Sensitivity

BRIDGE = _games([((A, B, E), 4), ((C, D, E), 4)])  # E co-occurs with everything; A-B and C-D only via their games


def test_bridge_tag_removal_splits_the_cluster_and_is_flagged():
    state = compute_state(BRIDGE, _settings(resolution=0.5))
    assert [sorted(c.members) for c in state.clusters] == [[A, B, C, D, E]]
    rows = {r["tag_id"]: r for r in removal_sensitivity(state)}
    assert rows[E]["rc_ari"] == 0.0 and rows[E]["rc_delta_k"] == 1 and rows[E]["rc_ari_beyond_noise"] is True
    assert rows[A]["rc_ari"] == 1.0 and rows[A]["rc_ari_beyond_noise"] is False
    assert rows[E]["is_center"] is True and rows[E]["cluster"] == "C1"


def test_reclustered_delta_equals_a_fresh_state_without_the_tag(toy):
    rows = {r["tag_id"]: r for r in removal_sensitivity(toy)}
    for tag in (A, G):
        without = compute_state(TOY, _settings(removed_tag_ids=(tag,)), with_positions=False)
        assert rows[tag]["rc_delta_modularity"] == pytest.approx(without.modularity - toy.modularity)
        assert rows[tag]["rc_silhouette_after"] == pytest.approx(without.silhouette.mean)
    assert rows[G]["rc_ari"] == 1.0 and rows[G]["rc_delta_s"] == -1


def test_silhouette_na_transition_leaves_the_delta_empty():
    state = compute_state(_games([((A, B), 3), ((D, E), 3)]), _settings())
    row = next(r for r in removal_sensitivity(state) if r["tag_id"] == A)
    assert row["fp_silhouette_after"] is None
    assert row["fp_silhouette_after_status"] == "fewer_than_2_multi_tag_clusters"
    assert row["fp_delta_silhouette"] is None and row["rc_delta_silhouette"] is None


def test_partial_run_is_a_prefix_and_state_is_unchanged(toy):
    before = state_tables(toy, cluster_positions={})
    full = removal_sensitivity(toy)
    calls = []
    partial = removal_sensitivity(toy, progress=lambda done, total: calls.append((done, total)),
                                  should_stop=lambda: len(calls) >= 3)
    assert partial == full[:3] and calls[-1] == (3, 7)
    assert [r["tag_id"] for r in full] == run_order(toy)
    assert state_tables(toy, cluster_positions={}) == before
    one = removal_sensitivity(toy, tags=[D])
    assert one[0] == next(r for r in full if r["tag_id"] == D)


def test_flag_when_seed_ari_min_is_one(toy):
    assert toy.seed_summary()["seed_ari_min"] == 1.0
    rows = {r["tag_id"]: r for r in removal_sensitivity(toy)}
    assert all(r["rc_ari_beyond_noise"] == (r["rc_ari"] < 1.0) for r in rows.values())


# ----------------------------------------------------------------------------- Resolution Sweep


def test_sweep_grid_includes_the_config_gamma():
    assert sweep_grid([0.5, 0.75, 1.25], 1.0) == [0.5, 0.75, 1.0, 1.25]
    assert sweep_grid([0.5, 1.0], 1.0) == [0.5, 1.0]


def test_resolution_sweep_holds_everything_else(toy):
    rows = resolution_sweep(toy, [0.5, 1.0])
    report = next(r for r in rows if r["resolution"] == 1.0)
    assert report["ari_vs_report"] == 1.0 and report["modularity"] == pytest.approx(toy.modularity)
    assert report["n_multi_tag_clusters"] == 2
