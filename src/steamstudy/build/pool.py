"""The Candidate Pool, read from the stored `/top` listing passes (shared by Collect and the Build)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from steamstudy.build.parse import ParseError, parse_top_page
from steamstudy.snapshot import LogEntry, StoredResponse

_PASS_KEY = re.compile(r"^steamcharts/top/pass-(\d+)/p-(\d+)\.html\.gz$")


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
    listing = Listing()
    for key in snapshot.keys("steamcharts/top/"):
        m = _PASS_KEY.match(key)
        resp = snapshot.response(key)
        if not m or resp is None:
            continue
        n = int(m.group(1))
        listing.rows_per_pass.setdefault(n, 0)
        listing.appids_per_pass.setdefault(n, set())
        if resp.outcome == "parse_failure":
            listing.parse_errors.append((key, "listing page structure not readable"))
            continue
        if resp.outcome != "ok":
            continue
        try:
            rows = parse_top_page(resp.body or b"")
        except ParseError as exc:
            listing.parse_errors.append((key, str(exc)))
            continue
        listing.rows_per_pass[n] += len(rows)
        for row in rows:
            listing.appids_per_pass[n].add(row.appid)
            listing.names.setdefault(row.appid, row.name)
            if row.appid not in listing.best_rank or row.rank < listing.best_rank[row.appid]:
                listing.best_rank[row.appid] = row.rank
    return listing


def pool_appids(snapshot: SnapshotLike) -> list[int]:
    """Every AppID in the stored listing passes, plus the test-mode edge cases."""
    extra = {int(a) for a in snapshot.meta.get("extra_appids", [])}
    return sorted(set(read_listing(snapshot).best_rank) | extra)
