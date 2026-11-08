"""The Candidate Pool, read from the stored `/top` listing passes (shared by Collect and the Build)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from steamstudy.build.source import ListingPage, RawSource, SkippedEntry
from steamstudy.snapshot import LogEntry, StoredResponse


class SnapshotLike(Protocol):
    @property
    def meta(self) -> dict[str, Any]: ...

    def keys(self, prefix: str = "") -> list[str]: ...

    def response(self, key: str) -> StoredResponse | None: ...

    def entry(self, key: str) -> LogEntry | None: ...


@dataclass
class Listing:
    best_rank: dict[int, int] = field(default_factory=dict)  # appid -> best /top rank across passes
    names: dict[int, str] = field(default_factory=dict)
    rows_per_pass: dict[int, int] = field(default_factory=dict)
    appids_per_pass: dict[int, set[int]] = field(default_factory=dict)
    parse_errors: list[tuple[str, str]] = field(default_factory=list)  # (request_key, error)

    @property
    def listing_rows(self) -> int:
        return sum(self.rows_per_pass.values())


def read_listing(snapshot: SnapshotLike) -> Listing:
    return listing_from_pages(RawSource(snapshot).listing_pages())


def listing_from_pages(pages: list[ListingPage]) -> Listing:
    """The Candidate Pool's listing from its pages, in key order: best rank across passes, first-seen name."""
    listing = Listing()
    for page in pages:
        n = page.pass_n
        listing.rows_per_pass.setdefault(n, 0)
        listing.appids_per_pass.setdefault(n, set())
        if page.error is not None:
            listing.parse_errors.append((page.key, page.error))
            continue
        if page.outcome != "ok":
            continue
        listing.rows_per_pass[n] += len(page.rows)
        for row in page.rows:
            listing.appids_per_pass[n].add(row.appid)
            listing.names.setdefault(row.appid, row.name)
            if row.appid not in listing.best_rank or row.rank < listing.best_rank[row.appid]:
                listing.best_rank[row.appid] = row.rank
    return listing


def pool_appids(snapshot: SnapshotLike) -> list[int]:
    """Every AppID in the stored listing passes, plus the test-mode edge cases."""
    extra = {int(a) for a in snapshot.meta.get("extra_appids", [])}
    return sorted(set(read_listing(snapshot).best_rank) | extra)


def skipped_app_rows(snapshot: SnapshotLike) -> list[dict[str, Any]]:
    """Steam Charts app pages that kept failing to load or parse, and were skipped (outcome `skipped`)."""
    return skipped_rows(RawSource(snapshot).skipped(), read_listing(snapshot).names)


def skipped_rows(entries: list[SkippedEntry], names: dict[int, str]) -> list[dict[str, Any]]:
    """`skipped_apps.csv` rows from the skipped apps' log entries and the listing names."""
    rows = [{"appid": e.appid, "name": names.get(e.appid), "url": e.url, "reason": e.detail,
             "last_status": e.status, "timestamp": e.timestamp} for e in entries]
    return sorted(rows, key=lambda r: r["appid"])
