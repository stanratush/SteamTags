"""Per-game store data, read from the Snapshot and completed by Manual Metadata Entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Sequence
from typing import Any

from steamstudy.build.parse import AppDetails, Genre, StorePage, StoreTag, TagVocabulary
from steamstudy.build.source import BuildSource

MANUAL_FULL_FIELDS = ("tags", "app_type", "genres", "is_free", "release_date", "adult_only")
MANUAL_OPTIONAL_FIELDS = ("name",)


class ManualMetadataError(ValueError):
    """A Manual Metadata Entry is invalid; the Build fails."""


@dataclass
class Game:
    """Everything the exclusion rules, datasets and reports need about one scored app."""

    appid: int
    name: str
    page_outcome: str  # outcome of the store page request ("missing" when never fetched)
    details_outcome: str
    page: StorePage | None = None
    details: AppDetails | None = None
    tags: tuple[StoreTag, ...] = ()
    app_type: str = ""
    is_free: bool = False
    genres: tuple[Genre, ...] = ()
    release_date: str = ""
    adult_only: bool = False
    descriptor_ids: tuple[int, ...] = ()
    metadata_source: str = "store"
    manual_entry: dict[str, Any] | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_store_data(self) -> bool:
        return self.page is not None and self.details is not None

    @property
    def has_data(self) -> bool:
        return self.has_store_data or self.metadata_source == "manual"

    @property
    def tag_ids(self) -> set[int]:
        return {t.tag_id for t in self.tags}

    def has_tag(self, tag_id: int, depth: int | None = None) -> bool:
        """'Has tag' for datasets and the network: among the first `depth` displayed tags (all when None),
        whatever the rank limits."""
        return any(t.tag_id == tag_id for t in counted_tags(self.tags, depth))

    def store_detail(self) -> str:
        return f"store page: {self.page_outcome}; appdetails: {self.details_outcome}"


def counted_tags(tags: Sequence[Any], depth: int | None) -> Sequence[Any]:
    """The tags that count as "had" under Tag Depth: the first `depth` of the displayed list (all when None).

    The one definition of "has" for Tag-Specific Dataset membership, the Eligible Pool and its baselines and the
    feature analysis. Exclusions, Content Flags and rank limits read the full list instead.
    """
    return tags if depth is None else tags[:depth]


def read_vocabulary(source: BuildSource) -> TagVocabulary | None:
    return source.vocabulary()


def read_game(source: BuildSource, appid: int, fallback_name: str, parse_errors: list[dict[str, Any]]) -> Game:
    page_key, details_key = f"store/page/{appid}.html.gz", f"store/appdetails/{appid}.json.gz"
    read = source.store(appid)
    game = Game(appid, fallback_name, read.page_outcome, read.details_outcome, page=read.page, details=read.details)
    if read.page_error is not None:
        game.page_outcome = "parse_error"
        parse_errors.append({"appid": appid, "source": "store_page", "request_key": page_key,
                             "error": read.page_error})
    if read.details_error is not None:
        game.details_outcome = "parse_error"
        parse_errors.append({"appid": appid, "source": "appdetails", "request_key": details_key,
                             "error": read.details_error})
    if game.page is not None:
        game.tags = game.page.tags
        game.adult_only = game.page.adult_only
    if game.details is not None:
        d = game.details
        game.name, game.app_type, game.is_free = d.name, d.app_type, d.is_free
        game.genres, game.release_date, game.descriptor_ids = d.genres, d.release_date, d.content_descriptor_ids
    return game


# ----------------------------------------------------------------------------- Manual Metadata Entries


def validate_manual_entries(entries: tuple[dict[str, Any], ...]) -> dict[int, dict[str, Any]]:
    """Validate `manual_metadata.toml` entries; every field must carry a source and a retrieval date."""
    by_appid: dict[int, dict[str, Any]] = {}
    for i, entry in enumerate(entries):
        where = f"manual_metadata.toml entry {i + 1}"
        appid = entry.get("appid")
        if not isinstance(appid, int) or isinstance(appid, bool):
            raise ManualMetadataError(f"{where}: appid must be an integer")
        kind = entry.get("kind")
        if kind not in ("full", "tags_only"):
            raise ManualMetadataError(f"{where} (appid {appid}): kind must be 'full' or 'tags_only'")
        allowed = set(MANUAL_FULL_FIELDS) | set(MANUAL_OPTIONAL_FIELDS) if kind == "full" else {"tags"}
        required = set(MANUAL_FULL_FIELDS) if kind == "full" else {"tags"}
        fields = {k for k in entry if k not in ("appid", "kind")}
        if missing := required - fields:
            raise ManualMetadataError(f"{where} (appid {appid}): missing field(s) {sorted(missing)}")
        if extra := fields - allowed:
            raise ManualMetadataError(f"{where} (appid {appid}): field(s) {sorted(extra)} not allowed for a {kind} entry")
        for name in fields:
            value = entry[name]
            if not isinstance(value, dict) or "value" not in value:
                raise ManualMetadataError(f"{where} (appid {appid}): field {name} must be {{value, source_url, retrieved}}")
            for key in ("source_url", "retrieved"):
                if not str(value.get(key, "")).strip():
                    raise ManualMetadataError(f"{where} (appid {appid}): field {name} has no {key}")
        _check_values(entry, where)
        if appid in by_appid:
            raise ManualMetadataError(f"{where}: a second entry for appid {appid}")
        by_appid[appid] = entry
    return by_appid


def _check_values(entry: dict[str, Any], where: str) -> None:
    tags = entry["tags"]["value"]
    if not isinstance(tags, list) or not all(isinstance(t, dict) and isinstance(t.get("id"), int)
                                             and isinstance(t.get("name"), str) for t in tags):
        raise ManualMetadataError(f"{where}: tags value must be a list of {{id, name}} in display order")
    if "genres" in entry:
        genres = entry["genres"]["value"]
        if not isinstance(genres, list) or not all(isinstance(g, dict) and "id" in g and "name" in g for g in genres):
            raise ManualMetadataError(f"{where}: genres value must be a list of {{id, name}}")
    for name in ("is_free", "adult_only"):
        if name in entry and not isinstance(entry[name]["value"], bool):
            raise ManualMetadataError(f"{where}: {name} value must be true or false")


def apply_manual_entry(game: Game, entry: dict[str, Any]) -> None:
    """Apply an entry after store parsing, before exclusion. Raises if the store does provide the data."""
    kind = entry["kind"]
    if kind == "full":
        if game.has_store_data:
            raise ManualMetadataError(
                f"Manual Metadata Entry for appid {game.appid}: the Steam store provides this app ({game.store_detail()})")
        game.tags = tuple(StoreTag(int(t["id"]), str(t["name"]), 0, i)
                          for i, t in enumerate(entry["tags"]["value"], start=1))
        game.app_type = str(entry["app_type"]["value"])
        game.genres = tuple(Genre(int(g["id"]), str(g["name"])) for g in entry["genres"]["value"])
        game.is_free = bool(entry["is_free"]["value"])
        game.release_date = str(entry["release_date"]["value"])
        game.adult_only = bool(entry["adult_only"]["value"])
        game.descriptor_ids = ()
        if "name" in entry:
            game.name = str(entry["name"]["value"])
        game.metadata_source = "manual"
    else:
        if not (game.has_store_data and not game.tags):
            raise ManualMetadataError(
                f"tags-only Manual Metadata Entry for appid {game.appid}: allowed only for a game whose store page "
                f"shows no tags ({game.store_detail()}, {len(game.tags)} tags)")
        game.tags = tuple(StoreTag(int(t["id"]), str(t["name"]), 0, i)
                          for i, t in enumerate(entry["tags"]["value"], start=1))
        game.metadata_source = "manual_tags"
    game.manual_entry = entry
    for name in sorted(k for k in entry if k not in ("appid", "kind")):
        value = entry[name]["value"]
        text = ";".join(f"{v['id']}:{v['name']}" for v in value) if isinstance(value, list) else str(value).lower() \
            if isinstance(value, bool) else str(value)
        game.citations.append({"appid": game.appid, "entry_kind": kind, "field": name, "value": text,
                               "source_url": str(entry[name]["source_url"]),
                               "retrieved": str(entry[name]["retrieved"])})
