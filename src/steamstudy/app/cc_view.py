"""The Cluster Comparison mode: resolving each dataset's partition, then (issue 18 on) the mode's components.

A dataset on a cell (its pick, or another selected cell) shows the cell's stored Selected Partition, read from the
Parameter Selection cache and never re-clustered. A dataset set by hand, or one with no Automatic Parameter
Selection run under the shared settings, is clustered once with the Build's main seed (`light_partition`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from steamstudy.app import ps_view as PV
from steamstudy.app.loader import BuildContext
from steamstudy.network import comparison as CMP
from steamstudy.network import selection as SEL
from steamstudy.network.graph import filter_games
from steamstudy.network.model import Settings
from steamstudy.network.state import light_partition

# ----------------------------------------------------------------------------- resolving a dataset


def shared_defaults(ctx: BuildContext) -> CMP.SharedSettings:
    """The mode's shared settings start from the Parameter Selection settings, never the Workbench's."""
    settings, _ = PV.defaults_of(ctx)
    return CMP.SharedSettings(settings.clustering_weight, settings.algorithm, settings.min_months,
                              settings.genre_hidden, settings.removed_tag_ids)


def selection_settings(ctx: BuildContext, shared: CMP.SharedSettings) -> SEL.SelectionSettings | None:
    """The Parameter Selection settings whose runs feed the comparison: the shared settings with each dataset's
    defining Tag hidden. None when no run can exist for them (Parameter Selection runs Leiden only)."""
    if shared.algorithm != "leiden":
        return None
    settings, _ = PV.defaults_of(ctx)
    return settings.with_(genre_hidden=tuple(shared.genre_hidden), removed_tag_ids=tuple(shared.removed_tag_ids),
                          min_months=shared.min_months, clustering_weight=shared.clustering_weight,
                          hide_defining_tag=True)


@dataclass(frozen=True)
class Request:
    """What the comparison asks of one dataset: its source and, off the pick, its values."""

    dataset: str
    source: str  # pick | cell | hand | no_run
    g: int | None = None  # cell and hand
    s: int | None = None
    resolution: float | None = None  # hand only


@dataclass(frozen=True)
class Resolved:
    """One dataset's resolved partition with the figures its row shows."""

    partition: CMP.Partition
    values: CMP.DatasetValues
    seed_noise_floor: float | None  # the run's stored floor on a cell; its own noise-seed runs otherwise
    neighbour_agreement: float | None  # the cell's; None off a cell
    state_id: str | None  # hand and no run only: rebuilds the dataset in the Workbench's terms
    # Why a dataset asked for on a cell has source no_run: "no_run" (no Automatic Parameter Selection run under the
    # shared settings), "no_pick" (a run, but no qualifying pair under its Pair Constraints) or "run_gone" (the
    # selected cell vanished: cache cleared, run changed). None otherwise.
    fallback: str | None = None

    @property
    def run_gone(self) -> bool:
        return self.fallback == "run_gone"


def resolve(ctx: BuildContext, shared: CMP.SharedSettings, request: Request, constraints: SEL.Constraints,
            cache_root: Path | None = None) -> Resolved:
    """`constraints` are the Pair Constraints set in Parameter Selection for this dataset: they fix its pick."""
    if request.source in ("pick", "cell"):
        on_cell = _on_cell(ctx, shared, request, constraints, cache_root)
        if isinstance(on_cell, Resolved):
            return on_cell
        return _off_cell(ctx, shared, Request(request.dataset, "no_run"), fallback=on_cell)
    return _off_cell(ctx, shared, request)


def _on_cell(ctx: BuildContext, shared: CMP.SharedSettings, request: Request, constraints: SEL.Constraints,
             cache_root: Path | None) -> Resolved | str:
    """The cell's stored Selected Partition, or why there is none (a `Resolved.fallback` code)."""
    settings = selection_settings(ctx, shared)
    if settings is None:
        return "no_run"
    dataset = request.dataset
    view = PV.dataset_view(ctx, settings, dataset, constraints, SEL.default_constraints(ctx.network), cache_root)
    if view.status != "complete":
        return "run_gone" if request.source == "cell" else "no_run"
    if request.source == "pick":
        if view.star is None:
            return "no_pick"
        pair = view.star
    else:
        assert request.g is not None and request.s is not None
        pair = (request.g, request.s)
    result = view.result(pair)
    if result is None or result.selected is None or result.selected_resolution is None:
        return "run_gone"
    g, s = pair
    na = view.na.get(pair)
    partition = CMP.Partition(
        dataset=dataset, clusters=tuple(SEL.clusters_of(result.nodes, result.selected)),
        edged=frozenset(result.edged), hidden=frozenset(settings.hidden_tag_ids(ctx.context(dataset))),
        games=tuple(filter_games(ctx.games(dataset), shared.min_months)), min_games_per_tag=g)
    values = CMP.DatasetValues(dataset, request.source, g, s, result.selected_resolution,
                               selection_key=settings.settings_key())
    return Resolved(partition, values, (result.seed_noise or {}).get("floor"),
                    None if na is None else na.value, None)


def network_settings(ctx: BuildContext, shared: CMP.SharedSettings, dataset: str, g: int, s: int,
                     resolution: float) -> Settings:
    """A hand-set or no-run dataset's Network State settings: the shared settings, its own defining Tag hidden,
    the Build's main seed and seed counts."""
    n = ctx.network
    defining = ctx.context(dataset).defining_tag_id
    hidden = set(shared.genre_hidden) | ({defining} if defining is not None else set())
    return Settings(build_id=ctx.build_id, dataset=dataset, min_months=shared.min_months, min_games_per_tag=g,
                    min_shared_games=s, hidden_tag_ids=tuple(hidden), removed_tag_ids=tuple(shared.removed_tag_ids),
                    clustering_weight=shared.clustering_weight, algorithm=shared.algorithm, resolution=resolution,
                    seed=n.seed, null_replicates=n.null_replicates, noise_seeds=n.noise_seeds)


def _off_cell(ctx: BuildContext, shared: CMP.SharedSettings, request: Request,
              fallback: str | None = None) -> Resolved:
    n = ctx.network
    if request.source == "hand":
        assert request.g is not None and request.s is not None and request.resolution is not None
        g, s, gamma = request.g, request.s, request.resolution
    else:
        g, s, gamma = n.min_games_per_tag, n.min_shared_games, n.resolution
    dataset = request.dataset
    settings = network_settings(ctx, shared, dataset, g, s, gamma)
    light = light_partition(ctx.games(dataset), settings, ctx.context(dataset))
    partition = CMP.Partition(dataset=dataset, clusters=tuple(light.clusters), edged=light.edged,
                              hidden=frozenset(settings.hidden_tag_ids), games=tuple(light.network.games),
                              min_games_per_tag=g)
    values = CMP.DatasetValues(dataset, request.source, g, s, settings.resolution, seed=settings.seed)
    return Resolved(partition, values, light.seed_noise_floor, None, light.state_id, fallback)
