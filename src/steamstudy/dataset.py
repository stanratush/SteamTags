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
    if source == "import":
        return _read_import(build, key)
    raise NotImplementedError(f"Build source {source!r} has no dataset adapter yet")


# ----------------------------------------------------------------------------- the Steam adapter


def steam_games(rows: list[dict[str, Any]], depth: int | None) -> list[Game]:
    """The network's games from typed `top100_<dataset>.csv` rows, Tag Depth applied. The Steam adapter and the
    Build stage (which holds the rows in memory) both read rows through this."""
    if depth is not None:
        rows = [{**r, "tag_ids": (r["tag_ids"] or [])[:depth], "tags": (r["tags"] or [])[:depth]} for r in rows]
    return games_from_rows(rows)


def import_games(rows: list[dict[str, Any]], depth: int | None) -> list[Game]:
    """The network's games from an Import Build's dataset rows (`top100` shape in memory, or `topn` rows read back,
    whose `id` / `filter_value` stand for `appid` / `months_observed`); the filter value stays a decimal, 0 without
    a filter field."""
    games = []
    for r in rows:
        tag_ids = tuple(int(t) for t in r["tag_ids"] or ())
        tags = tuple(str(t) for t in r["tags"] or ())
        if depth is not None:
            tag_ids, tags = tag_ids[:depth], tags[:depth]
        value = r.get("months_observed", r.get("filter_value"))
        games.append(Game(int(r["appid"] if "appid" in r else r["id"]), str(r["name"]), int(r["rank"]),
                          float(value) if value is not None else 0.0, tag_ids, tags))
    return sorted(games, key=lambda g: g.rank)


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


# ----------------------------------------------------------------------------- the import adapter


def _read_import(build: BuildLike, key: str) -> Dataset:
    """`topn_<key>.csv` and `item_fields.csv` of an Import Build. The filter slider takes the field's name and
    its range from the data; without a filter field it is hidden and every item is kept."""
    import math

    definition = next(d for d in build.datasets if d.key == key)
    path = build.path / "datasets" / f"topn_{key}.csv"
    rows = read_typed_csv(path, S.TOPN) if path.is_file() else []
    fields_path = build.path / "datasets" / "item_fields.csv"
    fields: dict[int, dict[str, float]] = {}
    if fields_path.is_file():
        for r in read_typed_csv(fields_path, S.ITEM_FIELDS):
            fields.setdefault(int(r["id"]), {})[str(r["field"])] = float(r["value"])
    depth = build.depth_cut
    games = import_games(rows, depth)
    by_id = {int(r["id"]): r for r in rows}
    items = []
    for g in games:
        row = by_id[g.appid]
        items.append(Item(
            id=g.appid, name=g.name, rank=g.rank, attribute_ids=g.tag_ids, attribute_names=g.tags,
            all_attribute_ids=tuple(int(t) for t in row["tag_ids"] or ()),
            all_attribute_names=tuple(str(t) for t in row["tags"] or ()),
            filter_value=None if row["filter_value"] is None else float(row["filter_value"]),
            fields=fields.get(g.appid, {})))
    field_name = build.build_json.get("filter_field")
    values = [i.filter_value for i in items if i.filter_value is not None]
    filter_field = (FilterField(str(field_name), math.floor(min(values)), math.ceil(max(values)))
                    if field_name and values else None)
    defining = definition.defining_tag
    return Dataset(
        key=key, items=tuple(items), defining_attribute=defining.id if defining else None,
        genre_attribute_ids=frozenset(t.id for t in build.genre_tags), tag_depth=depth,
        filter_field=filter_field, id_label="ID", _games=tuple(games))
