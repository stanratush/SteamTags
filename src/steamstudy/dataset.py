"""The dataset seam: `read_dataset(build, key) -> Dataset`, the one way a consumer reads a Top-N Dataset.

The app, the network, Parameter Selection and validation all read a dataset through here (ADR 0005). An adapter
chosen by `build.json` `source` (absent = Steam) turns a Build's files into items in rank order. Steam facts that
are not part of the contract (store genres, `is_free`, Content Flags, ...) stay in the Build stage.

Files keep each game's full displayed tag list; this reader applies Tag Depth once, so everything downstream sees
only the counted tags. The full list stays on the item for display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from steamstudy.config import DatasetDef, TagRef
from steamstudy.export import schema as S
from steamstudy.export.writer import read_typed_csv
from steamstudy.network.model import Game, TagContext, games_from_rows

@dataclass(frozen=True)
class FilterField:
    """The one numeric field a dataset's items can be filtered on (`>=`, off at the minimum)."""

    label: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class Item:
    id: int
    name: str
    rank: int
    attribute_ids: tuple[int, ...]  # the counted attributes (within Tag Depth), in display order
    attribute_names: tuple[str, ...]
    all_attribute_ids: tuple[int, ...]  # the full displayed list, for the inspector
    all_attribute_names: tuple[str, ...]
    filter_value: float | None = None
    fields: dict[str, float] = field(default_factory=dict)

    @property
    def not_counted(self) -> tuple[str, ...]:
        """Names of the attributes beyond Tag Depth."""
        return self.all_attribute_names[len(self.attribute_ids):]


@dataclass(frozen=True)
class Dataset:
    key: str
    items: tuple[Item, ...]  # in rank order
    defining_attribute: int | None
    genre_attribute_ids: frozenset[int]
    tag_depth: int | None  # None = every attribute counts
    filter_field: FilterField | None
    id_label: str = "AppID"
    _games: tuple[Game, ...] = ()

    def games(self) -> list[Game]:
        """The items as the network reads them (counted attributes only), in rank order."""
        return list(self._games)

    def context(self) -> TagContext:
        return TagContext(self.defining_attribute, self.genre_attribute_ids)

    @property
    def size(self) -> int:
        return len(self.items)


class BuildLike(Protocol):
    """What the reader needs of a Build (the app's `BuildContext` satisfies it)."""

    @property
    def path(self) -> Path: ...

    @property
    def build_json(self) -> dict[str, Any]: ...

    @property
    def datasets(self) -> tuple[DatasetDef, ...]: ...

    @property
    def genre_tags(self) -> tuple[TagRef, ...]: ...

    @property
    def depth_cut(self) -> int | None: ...


def read_dataset(build: BuildLike, key: str) -> Dataset:
    source = build.build_json.get("source", "steam")
    if source == "steam":
        return _read_steam(build, key)
    raise NotImplementedError(f"Build source {source!r} has no dataset adapter yet")


# ----------------------------------------------------------------------------- the Steam adapter


def steam_games(rows: list[dict[str, Any]], depth: int | None) -> list[Game]:
    """The network's games from typed `top100_<dataset>.csv` rows, Tag Depth applied. The Steam adapter and the
    Build stage (which holds the rows in memory) both read rows through this."""
    if depth is not None:
        rows = [{**r, "tag_ids": (r["tag_ids"] or [])[:depth], "tags": (r["tags"] or [])[:depth]} for r in rows]
    return games_from_rows(rows)


def _read_steam(build: BuildLike, key: str) -> Dataset:
    definition = next(d for d in build.datasets if d.key == key)
    path = build.path / "datasets" / f"top100_{key}.csv"
    rows = read_typed_csv(path, S.TOP100) if path.is_file() else []
    depth = build.depth_cut
    games = steam_games(rows, depth)
    by_id = {int(r["appid"]): r for r in rows}
    items = []
    for g in games:
        row = by_id[g.appid]
        items.append(Item(
            id=g.appid, name=g.name, rank=g.rank, attribute_ids=g.tag_ids, attribute_names=g.tags,
            all_attribute_ids=tuple(int(t) for t in row["tag_ids"] or ()),
            all_attribute_names=tuple(str(t) for t in row["tags"] or ()),
            filter_value=float(g.months_observed), fields={}))
    defining = definition.defining_tag
    return Dataset(
        key=key, items=tuple(items), defining_attribute=defining.id if defining else None,
        genre_attribute_ids=frozenset(t.id for t in build.genre_tags), tag_depth=depth,
        filter_field=FilterField("Minimum Months Filter", 0, 60), id_label="AppID", _games=tuple(games))
