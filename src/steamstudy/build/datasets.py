"""Ranking the five Top-100 Datasets from one shared set of scored, non-excluded games."""

from __future__ import annotations

import bisect
import datetime as dt
from dataclasses import dataclass, field

from steamstudy.build.games import Game
from steamstudy.build.score import Score
from steamstudy.config import DatasetDef

TOP_N = 100


def sort_key(appid: int, s: Score) -> tuple[float, int, int]:
    """mean_monthly_players desc, months_observed desc, appid asc."""
    return (-s.mean_monthly_players, -s.months_observed, appid)


@dataclass
class RankedDataset:
    definition: DatasetDef
    eligible: list[int]  # the Eligible Pool, in rank order
    top: list[int]
    ties: list[int]  # outside the top, tied with rank 100's score
    _keys: list[tuple[float, int, int]] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.definition.key


def in_scope(definition: DatasetDef, game: Game | None) -> bool | None:
    """Whether a game belongs to the dataset's scope; None when its tags are unknown."""
    if definition.defining_tag is None:
        return True
    if game is None or not game.has_data:
        return None
    return game.has_tag(definition.defining_tag.id)


def rank_dataset(
    definition: DatasetDef, scores: dict[int, Score], games: dict[int, Game], excluded: set[int]
) -> RankedDataset:
    eligible = sorted(
        (a for a in scores if a not in excluded and in_scope(definition, games.get(a))),
        key=lambda a: sort_key(a, scores[a]),
    )
    top = eligible[:TOP_N]
    ties: list[int] = []
    if len(eligible) > TOP_N:
        cutoff = scores[top[-1]].mean_monthly_players
        ties = [a for a in eligible[TOP_N:] if scores[a].mean_monthly_players == cutoff]
    ranked = RankedDataset(definition, eligible, top, ties)
    ranked._keys = [sort_key(a, scores[a]) for a in eligible]
    return ranked


def would_be_rank(ranked: RankedDataset, appid: int, scores: dict[int, Score], games: dict[int, Game]) -> int | None:
    """The rank the game takes, or would take had it not been excluded; None outside the dataset's scope."""
    if appid not in scores or not in_scope(ranked.definition, games.get(appid)):
        return None
    key = sort_key(appid, scores[appid])
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
