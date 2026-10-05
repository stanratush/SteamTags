"""The Tag Source: where a Snapshot's game tags come from, chosen when the Snapshot is created.

`steam` (the default) reads the tag list displayed on the Steam store page, which the store stage fetches
anyway for the store metadata. `steamdb` reads each scored app's SteamDB page instead, fetched by the store
stage next to the store responses. Store metadata (type, genres, Adult Only, ...) always comes from the store.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from steamstudy.build.parse import ParseError, StorePage, StoreTag, parse_steamdb_app
from steamstudy.build.pool import SnapshotLike

STEAM = "steam"
STEAMDB = "steamdb"
TAG_SOURCES = (STEAM, STEAMDB)
STEAMDB_URL = "https://steamdb.info"
LABELS = {STEAM: "store page", STEAMDB: "SteamDB page"}


@dataclass(frozen=True)
class TagRequest:
    """The one extra request a Tag Source needs per scored app."""

    request_key: str
    url: str
    parser: Callable[[bytes], Any]


def of(meta: Mapping[str, Any]) -> str:
    """The Snapshot's Tag Source; Snapshots from before the choice existed used the store page."""
    return str(meta.get("tag_source") or STEAM)


def steamdb_request(appid: int) -> TagRequest:
    """An app's SteamDB page: the Tag Source page of a `steamdb` Snapshot, and the cross-check's page."""
    return TagRequest(f"steamdb/app/{appid}.html.gz", f"{STEAMDB_URL}/app/{appid}/", parse_steamdb_app)


def tag_request(source: str, appid: int) -> TagRequest | None:
    """What Collect fetches for this app's tags beyond the store page (nothing for `steam`)."""
    return steamdb_request(appid) if source == STEAMDB else None


def read_tags(snapshot: SnapshotLike, appid: int, source: str, page: StorePage | None,
              parse_errors: list[dict[str, Any]], warnings: list[str]) -> tuple[StoreTag, ...]:
    """The app's tags from its Tag Source, in display order; () when the source shows none.
    An unreadable SteamDB page is added to `parse_errors`; a SteamDB page that was never collected
    (not found, skipped, missing) adds a warning, since the app then has no tags."""
    if source != STEAMDB:
        return page.tags if page is not None else ()
    key = steamdb_request(appid).request_key
    resp = snapshot.response(key)
    if resp is None or resp.outcome not in ("ok", "parse_failure"):
        warnings.append(f"no SteamDB page for appid {appid} ({resp.outcome if resp else 'missing'}): it has no tags")
        return ()
    try:
        if resp.outcome == "parse_failure":
            raise ParseError("page structure not readable")
        pairs = parse_steamdb_app(resp.body or b"")
    except ParseError as exc:
        parse_errors.append({"appid": appid, "source": "steamdb_page", "request_key": key, "error": str(exc)})
        return ()
    return tuple(StoreTag(tag_id, name, 0, i) for i, (tag_id, name) in enumerate(pairs, start=1))
