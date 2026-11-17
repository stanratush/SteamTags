"""Cluster Comparison: resolving each dataset's partition from its source (ticket 16).

On the Parameter Selection test Build (grid g 15–17 × s 2–4, filled by Run): Overall's run picks (15, 3) and every
cell has a Selected Partition; Puzzle's run is complete but has no Selected Partition anywhere."""

from __future__ import annotations

import pytest

from steamstudy.app import cc_view as CC
from steamstudy.app import ps_view as PV
from steamstudy.app.loader import load_build
from steamstudy.network import comparison as CMP
from steamstudy.network import selection as SEL
from steamstudy.network.model import Settings, state_id_of
from steamstudy.network.state import light_partition
from test_ps_app import empty_build, ps_build, ps_template  # noqa: F401  (fixtures)


def _view(ctx, dataset, constraints=None):
    settings, defaults = PV.defaults_of(ctx)
    return settings, PV.dataset_view(ctx, settings, dataset, constraints or defaults, defaults)


def test_shared_settings_start_from_the_parameter_selection_settings(ps_build):
    ctx = load_build(ps_build)
    settings, _ = PV.defaults_of(ctx)
    shared = CC.shared_defaults(ctx)
    assert shared == CMP.SharedSettings("lift", "leiden", settings.min_months, settings.genre_hidden, ())
    # A run made with the defining Tag shown never feeds the comparison: its runs are looked up with it hidden.
    assert CC.selection_settings(ctx, shared).hide_defining_tag is True


def test_a_dataset_on_its_pick_reads_the_stored_selected_partition(ps_build):
    ctx = load_build(ps_build)
    settings, view = _view(ctx, "overall")
    stored = view.result((15, 3))
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("overall", "pick"), SEL.default_constraints(ctx.network))
    assert r.values == CMP.DatasetValues("overall", "pick", 15, 3, stored.selected_resolution,
                                         selection_key=settings.settings_key())
    assert r.partition.clusters == tuple(SEL.clusters_of(stored.nodes, stored.selected))
    assert r.partition.edged == frozenset(stored.edged)
    assert r.partition.min_games_per_tag == 15
    assert ctx.context("overall").defining_tag_id is None or ctx.context("overall").defining_tag_id in r.partition.hidden
    assert set(settings.genre_hidden) <= r.partition.hidden
    assert (r.seed_noise_floor, r.neighbour_agreement) == (stored.seed_noise["floor"], view.na[(15, 3)].value)
    assert r.state_id is None and not r.run_gone
    assert len(r.partition.games) == len(ctx.games("overall"))


def test_a_selected_cell_reads_that_cell(ps_build):
    ctx = load_build(ps_build)
    _, view = _view(ctx, "overall")
    stored = view.result((16, 2))
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("overall", "cell", 16, 2),
                   SEL.default_constraints(ctx.network))
    assert (r.values.source, r.values.g, r.values.s, r.values.resolution) == ("cell", 16, 2, stored.selected_resolution)
    assert r.partition.clusters == tuple(SEL.clusters_of(stored.nodes, stored.selected))


def test_the_pick_follows_the_pair_constraints_and_falls_to_no_run_without_one(ps_build):
    ctx = load_build(ps_build)
    strict = SEL.Constraints(**{**SEL.default_constraints(ctx.network).__dict__, "max_multi_tag_clusters": 3})
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("overall", "pick"), strict)
    assert (r.values.source, r.fallback) == ("no_run", "no_pick")


def _network_settings(ctx, dataset, shared, g, s, gamma):
    """An independent oracle for `CC.network_settings`, written from the spec's rule."""
    n = ctx.network
    hidden = set(shared.genre_hidden) | {ctx.context(dataset).defining_tag_id} - {None}
    return Settings(build_id=ctx.build_id, dataset=dataset, min_months=shared.min_months, min_games_per_tag=g,
                    min_shared_games=s, hidden_tag_ids=tuple(hidden), removed_tag_ids=shared.removed_tag_ids,
                    clustering_weight=shared.clustering_weight, algorithm=shared.algorithm, resolution=gamma,
                    seed=n.seed, null_replicates=n.null_replicates, noise_seeds=n.noise_seeds)


def test_a_hand_set_dataset_is_clustered_once_with_the_main_seed(ps_build):
    ctx = load_build(ps_build)
    shared = CC.shared_defaults(ctx)
    r = CC.resolve(ctx, shared, CC.Request("puzzle", "hand", 9, 7, 1.2), SEL.default_constraints(ctx.network))
    expected = _network_settings(ctx, "puzzle", shared, 9, 7, 1.2)
    light = light_partition(ctx.games("puzzle"), expected, ctx.context("puzzle"))
    assert r.values == CMP.DatasetValues("puzzle", "hand", 9, 7, 1.2, seed=ctx.network.seed)
    assert r.partition.clusters == tuple(light.clusters)
    assert r.seed_noise_floor == light.seed_noise_floor and r.neighbour_agreement is None
    assert r.state_id == state_id_of(expected.key())


def test_a_dataset_without_a_pick_starts_from_the_network_defaults(ps_build):
    ctx = load_build(ps_build)  # Puzzle's run is complete, but no cell has a Selected Partition
    n = ctx.network
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("puzzle", "pick"), SEL.default_constraints(n))
    assert r.values == CMP.DatasetValues("puzzle", "no_run", n.min_games_per_tag, n.min_shared_games, n.resolution,
                                         seed=n.seed)
    assert r.fallback == "no_pick" and r.state_id is not None


def test_a_cell_whose_run_is_gone_falls_to_the_network_defaults_and_says_so(empty_build):
    ctx = load_build(empty_build)
    n = ctx.network
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("overall", "cell", 16, 2), SEL.default_constraints(n))
    assert (r.values.source, r.values.g, r.values.s, r.values.resolution) == (
        "no_run", n.min_games_per_tag, n.min_shared_games, n.resolution)
    assert r.run_gone and r.fallback == "run_gone"


def test_a_pick_without_a_run_falls_to_the_network_defaults_without_saying_the_run_is_gone(empty_build):
    ctx = load_build(empty_build)
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("overall", "pick"), SEL.default_constraints(ctx.network))
    assert (r.values.source, r.fallback) == ("no_run", "no_run")


def test_a_selected_cell_without_a_selected_partition_says_the_run_changed(ps_build):
    ctx = load_build(ps_build)  # the run is complete, but Puzzle (16, 2) has no Selected Partition
    r = CC.resolve(ctx, CC.shared_defaults(ctx), CC.Request("puzzle", "cell", 16, 2),
                   SEL.default_constraints(ctx.network))
    assert (r.values.source, r.fallback) == ("no_run", "run_gone")


def test_shared_settings_without_a_run_never_read_the_cache(ps_build):
    ctx = load_build(ps_build)
    louvain = CMP.SharedSettings(**{**CC.shared_defaults(ctx).__dict__, "algorithm": "louvain"})
    r = CC.resolve(ctx, louvain, CC.Request("overall", "pick"), SEL.default_constraints(ctx.network))
    assert (r.values.source, r.fallback) == ("no_run", "no_run")
