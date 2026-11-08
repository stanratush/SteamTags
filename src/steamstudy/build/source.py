"""What a Build reads from a Snapshot, as parsed records: the source seam between the two Snapshot forms.

A Build reads its Snapshot only through a `BuildSource`: the listing pages, each app's Steam Charts read and store
read, the tag vocabulary, the skipped apps' log entries and the SteamDB pages, plus `meta` (the `snapshot.json`
keys). `RawSource` parses the raw pages (today's parsers, unchanged); `steamstudy.lightweight.LightSource` rebuilds
the same records from a Lightweight Snapshot, which is made by reading a `RawSource`. Equal records give a
byte-identical Build.

An app the Snapshot never looked up reads as outcome `missing`, in both forms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from steamstudy.build.parse import (
    AppDetails,
    MonthlyHistory,
    ParseError,
    StorePage,
    TagVocabulary,
    TopRow,
    parse_appdetails,
    parse_steamcharts_app,
    parse_steamdb_app,
    parse_store_page,
    parse_tag_list,
    parse_top_page,
)

MISSING = "missing"
# The parsers and the extracted field set a Lightweight Snapshot holds (`steamstudy.lightweight`): bump whenever a
# parser or that field set changes. Every Build records it in `build.json`.
EXTRACT_VERSION = 1
PAGE_NOT_READABLE = "page structure not readable"
LISTING_NOT_READABLE = "listing page structure not readable"
_PASS_KEY = re.compile(r"^steamcharts/top/pass-(\d+)/p-(\d+)\.html\.gz$")


@dataclass(frozen=True)
class ListingPage:
    """One `/top` listing page: its outcome and rows, or the parse error that stopped it."""

    key: str
    pass_n: int
    outcome: str
    rows: tuple[TopRow, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class ChartsRead:
    """One app's Steam Charts page. `history` (month rows up to the window's end) only when it parsed cleanly;
    `errors` holds every parse error otherwise."""

    outcome: str  # the request outcome, or "missing"
    history: MonthlyHistory | None = None
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class StoreRead:
    """One app's store page and appdetails. A parsed record is present only for an `ok` request that parsed;
    `details` is also None when appdetails said `success: false`."""

    page_outcome: str
    details_outcome: str
    page: StorePage | None = None
    page_error: str | None = None
    details: AppDetails | None = None
    details_error: str | None = None


@dataclass(frozen=True)
class SkippedEntry:
    """The request-log entry of a Steam Charts app page that was skipped during collection."""

    appid: int
    url: str
    detail: str
    status: int | None
    timestamp: str


@dataclass(frozen=True)
class SteamdbRead:
    """One SteamDB app page (cross-check only): its tags when it parsed, and the log batch it came from."""

    outcome: str
    batch: str
    tags: tuple[tuple[int, str], ...] | None = None
    error: str | None = None


class BuildSource(Protocol):
    form: str  # "raw" or "lightweight"

    @property
    def meta(self) -> dict[str, Any]: ...

    def listing_pages(self) -> list[ListingPage]: ...

    def charts(self, appid: int) -> ChartsRead: ...

    def store(self, appid: int) -> StoreRead: ...

    def vocabulary(self) -> TagVocabulary | None: ...

    def skipped(self) -> list[SkippedEntry]: ...

    def has_steamdb(self) -> bool: ...

    def steamdb(self, appid: int) -> SteamdbRead | None: ...


class RawSource:
    """A `BuildSource` over the raw form: the stored pages, parsed as the Build always parsed them."""

    form = "raw"

    def __init__(self, snapshot: Any):  # a Snapshot or SnapshotStore (keys / response / entry / meta)
        self.snapshot = snapshot

    @property
    def meta(self) -> dict[str, Any]:
        return self.snapshot.meta

    def listing_pages(self) -> list[ListingPage]:
        pages = []
        for key in self.snapshot.keys("steamcharts/top/"):
            m = _PASS_KEY.match(key)
            resp = self.snapshot.response(key)
            if not m or resp is None:
                continue
            n = int(m.group(1))
            if resp.outcome == "parse_failure":
                pages.append(ListingPage(key, n, resp.outcome, error=LISTING_NOT_READABLE))
            elif resp.outcome != "ok":
                pages.append(ListingPage(key, n, resp.outcome))
            else:
                try:
                    pages.append(ListingPage(key, n, resp.outcome, tuple(parse_top_page(resp.body or b""))))
                except ParseError as exc:
                    pages.append(ListingPage(key, n, resp.outcome, error=str(exc)))
        return pages

    def charts(self, appid: int) -> ChartsRead:
        resp = self.snapshot.response(f"steamcharts/app/{appid}.html.gz")
        if resp is None:
            return ChartsRead(MISSING)
        if resp.outcome == "parse_failure":
            return ChartsRead(resp.outcome, errors=(PAGE_NOT_READABLE,))
        if resp.outcome != "ok":
            return ChartsRead(resp.outcome)
        try:
            history = parse_steamcharts_app(resp.body or b"", last_month=self.meta["observation_window"]["last"])
        except ParseError as exc:
            return ChartsRead(resp.outcome, errors=(str(exc),))
        if history.errors:
            return ChartsRead(resp.outcome, errors=tuple(history.errors))
        return ChartsRead(resp.outcome, history=history)

    def store(self, appid: int) -> StoreRead:
        page_resp = self.snapshot.response(f"store/page/{appid}.html.gz")
        details_resp = self.snapshot.response(f"store/appdetails/{appid}.json.gz")
        page_outcome = page_resp.outcome if page_resp else MISSING
        details_outcome = details_resp.outcome if details_resp else MISSING
        page = details = None
        page_error = details_error = None
        if page_resp is not None and page_resp.outcome == "ok":
            try:
                page = parse_store_page(page_resp.body or b"")
            except ParseError as exc:
                page_error = str(exc)
        elif page_resp is not None and page_resp.outcome == "parse_failure":
            page_error = PAGE_NOT_READABLE
        if details_resp is not None and details_resp.outcome == "ok":
            try:
                details = parse_appdetails(details_resp.body or b"", appid)
            except ParseError as exc:
                details_error = str(exc)
        return StoreRead(page_outcome, details_outcome, page, page_error, details, details_error)

    def vocabulary(self) -> TagVocabulary | None:
        resp = self.snapshot.response("steam_api/GetTagList.json")
        if resp is None or resp.outcome != "ok" or not resp.body:
            return None
        return parse_tag_list(resp.body)

    def skipped(self) -> list[SkippedEntry]:
        out = []
        for key in self.snapshot.keys("steamcharts/app/"):
            entry = self.snapshot.entry(key)
            if entry is None or entry.outcome != "skipped":
                continue
            appid = appid_of_key(key)
            out.append(SkippedEntry(appid, entry.url, entry.detail, entry.status, entry.timestamp))
        return out

    def has_steamdb(self) -> bool:
        return bool(self.snapshot.keys("steamdb/"))

    def logged_appids(self, prefix: str) -> set[int]:
        """The apps the request log has a key for under `prefix` (e.g. `store/page/`): every app a read can find."""
        return {appid_of_key(k) for k in self.snapshot.keys(prefix)}

    def steamdb(self, appid: int) -> SteamdbRead | None:
        key = f"steamdb/app/{appid}.html.gz"
        resp = self.snapshot.response(key)
        if resp is None:
            return None
        entry = self.snapshot.entry(key)
        batch = entry.batch if entry else ""
        if resp.outcome != "ok":
            return SteamdbRead(resp.outcome, batch)
        try:
            return SteamdbRead(resp.outcome, batch, tags=tuple(parse_steamdb_app(resp.body or b"")))
        except ParseError as exc:
            return SteamdbRead(resp.outcome, batch, error=str(exc))


def appid_of_key(key: str) -> int:
    """The AppID in a per-app request key: `steamcharts/app/698670.html.gz` -> 698670."""
    return int(key.rsplit("/", 1)[1].split(".", 1)[0])


def as_source(snapshot_or_source: Any) -> BuildSource:
    """A `BuildSource` as is; a Snapshot (or anything with keys / response / entry / meta) read raw."""
    if hasattr(snapshot_or_source, "form") and hasattr(snapshot_or_source, "charts"):
        return snapshot_or_source
    return RawSource(snapshot_or_source)
