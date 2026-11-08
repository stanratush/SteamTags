"""Ranking the Top-N Datasets from one shared set of scored, non-excluded games."""

from __future__ import annotations

import bisect
import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from steamstudy.build.games import Game
from steamstudy.build.score import Score
from steamstudy.config import DatasetDef


def sort_key(appid: int, s: Score) -> tuple[float, int, int]:
    """Steam: mean_monthly_players desc, months_observed desc, appid asc."""
    return (-s.mean_monthly_players, -s.months_observed, appid)


def steam_tie_value(s: Any) -> float | None:
    """The value that ties at the cutoff: Mean Monthly Players (an Import's score)."""
    return s.mean_monthly_players


RankKey = Callable[[int, Any], tuple[Any, ...]]


@dataclass
class RankedDataset:
    definition: DatasetDef
    eligible: list[int]  # the Eligible Pool, in rank order
    top: list[int]  # the dataset's List Size highest-ranked items
    ties: list[int]  # outside the top, tied with the last rank's score
    _keys: list[tuple[Any, ...]] = field(default_factory=list)
    rank_key: RankKey = sort_key

    @property
    def key(self) -> str:
        return self.definition.key


def in_scope(definition: DatasetDef, game: Game | None, depth: int | None = None) -> bool | None:
    """Whether a game belongs to the dataset's scope (it has the defining tag within Tag Depth); None when its
    tags are unknown."""
    if definition.defining_tag is None:
        return True
    if game is None or not game.has_data:
        return None
    return game.has_tag(definition.defining_tag.id, depth)


def rank_pool(
    definition: DatasetDef, scores: dict[int, Any], games: dict[int, Game], excluded: set[int],
    depth: int | None = None, key: RankKey = sort_key,
) -> RankedDataset:
    """The Eligible Pool in rank order, with nothing sliced off yet (`slice_top` does that). `key` orders the
    pool: Steam's `sort_key`, or an Import's own rank."""
    eligible = sorted(
        (a for a in scores if a not in excluded and in_scope(definition, games.get(a), depth)),
        key=lambda a: key(a, scores[a]),
    )
    ranked = RankedDataset(definition, eligible, [], [], rank_key=key)
    ranked._keys = [key(a, scores[a]) for a in eligible]
    return ranked


def slice_top(ranked: RankedDataset, scores: dict[int, Any], list_size: int | None = None,
              tie_value: Callable[[Any], float | None] = steam_tie_value) -> RankedDataset:
    """Cut the pool at List Size (default: the definition's), listing the ties at the cutoff (none when the
    items have no score)."""
    n = ranked.definition.list_size if list_size is None else list_size
    ranked.top = ranked.eligible[:n]
    ranked.ties = []
    if len(ranked.eligible) > n:
        cutoff = tie_value(scores[ranked.top[-1]])
        if cutoff is not None:
            ranked.ties = [a for a in ranked.eligible[n:] if tie_value(scores[a]) == cutoff]
    return ranked


def rank_dataset(
    definition: DatasetDef, scores: dict[int, Any], games: dict[int, Game], excluded: set[int],
    depth: int | None = None, key: RankKey = sort_key,
) -> RankedDataset:
    return slice_top(rank_pool(definition, scores, games, excluded, depth, key), scores)


def would_be_rank(
    ranked: RankedDataset, appid: int, scores: dict[int, Any], games: dict[int, Game], depth: int | None = None
) -> int | None:
    """The rank the game takes, or would take had it not been excluded; None outside the dataset's scope."""
    if appid not in scores or not in_scope(ranked.definition, games.get(appid), depth):
        return None
    key = ranked.rank_key(appid, scores[appid])
    position = bisect.bisect_left(ranked._keys, key)
    return position + 1


# ----------------------------------------------------------------------------- store release dates

_DATE_FORMATS = ("%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y", "%b %Y", "%B %Y", "%d %b %Y", "%Y-%m-%d")


def store_month_index(text: str) -> int | None:
    """year*12 + month of a store release date, or None when it cannot be read."""
    text = text.strip()
    for fmt in _DATE_FORMATS:
        try:
            d = dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
        return d.year * 12 + d.month
    return None


def month_index(yyyy_mm: str) -> int:
    year, month = yyyy_mm.split("-")
    return int(year) * 12 + int(month)
