"""The shared network defaults as a Network State: used by the Build's report and by the app's initial state."""

from __future__ import annotations

from collections.abc import Iterable

from steamstudy.config import NetworkDefaults
from steamstudy.network.model import Settings, TagContext


def default_settings(build_id: str, dataset: str, defining_tag_id: int | None, genre_tag_ids: Iterable[int],
                     n: NetworkDefaults) -> tuple[Settings, TagContext]:
    """`network.toml` defaults with Genre Tags and the defining tag hidden as configured."""
    genre_ids = frozenset(genre_tag_ids)
    hidden = set(genre_ids) if n.hide_genre_tags else set()
    if defining_tag_id is not None and n.hide_defining_tag:
        hidden.add(defining_tag_id)
    settings = Settings(
        build_id=build_id, dataset=dataset, min_months=n.min_months, min_games_per_tag=n.min_games_per_tag,
        min_shared_games=n.min_shared_games, hidden_tag_ids=tuple(sorted(hidden)), removed_tag_ids=(),
        clustering_weight=n.clustering_weight, algorithm=n.algorithm, resolution=n.resolution, seed=n.seed,
        null_replicates=n.null_replicates, noise_seeds=n.noise_seeds,
    )
    return settings, TagContext(defining_tag_id=defining_tag_id, genre_tag_ids=genre_ids)
