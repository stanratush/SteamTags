"""The Snapshot on disk: raw archive, request log and `snapshot.json`.

Collect writes through `SnapshotStore`; the Build reads through the read-only `Snapshot` view
(`response(key)`, `meta`), so a Build never needs, or gets, network access.

Request keys are archive paths relative to `raw/`, e.g. `steamcharts/app/698670.html.gz`.
Keys ending in `.gz` are stored gzipped.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Request outcomes. Final outcomes are skipped on resume; the rest are fetched again.
FINAL_OUTCOMES = frozenset(
    {"ok", "not_found", "no_store_page", "age_gate", "no_appdetails", "end_of_listing", "parse_failure"}
)
RETRY_OUTCOMES = frozenset({"retryable_error", "hard_stop"})

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_key TEXT NOT NULL,
    url TEXT NOT NULL,
    status INTEGER,
    final_url TEXT,
    timestamp TEXT NOT NULL,
    sha256 TEXT,
    outcome TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    batch TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS requests_key ON requests(request_key);
"""


@dataclass(frozen=True)
class LogEntry:
    request_key: str
    url: str
    status: int | None
    final_url: str | None
    timestamp: str
    sha256: str | None
    outcome: str
    detail: str = ""
    batch: str = ""

    @property
    def is_final(self) -> bool:
        return self.outcome in FINAL_OUTCOMES


@dataclass(frozen=True)
class StoredResponse:
    request_key: str
    url: str
    status: int | None
    final_url: str | None
    timestamp: str
    sha256: str | None
    outcome: str
    body: bytes | None
    from_archive: bool = False

    def text(self) -> str:
        return (self.body or b"").decode("utf-8", errors="replace")


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Snapshot:
    """Read-only view used by the Build."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not (self.path / "snapshot.json").is_file():
            raise FileNotFoundError(f"not a Snapshot: {self.path}")
        self.meta: dict[str, Any] = json.loads((self.path / "snapshot.json").read_text(encoding="utf-8"))
        self._latest: dict[str, LogEntry] | None = None

    @property
    def id(self) -> str:
        return str(self.meta["id"])

    def _entries(self) -> dict[str, LogEntry]:
        if self._latest is None:
            self._latest = latest_entries(self.path / "requests.sqlite")
        return self._latest

    def keys(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._entries() if k.startswith(prefix))

    def entry(self, key: str) -> LogEntry | None:
        return self._entries().get(key)

    def response(self, key: str) -> StoredResponse | None:
        entry = self.entry(key)
        if entry is None:
            return None
        return StoredResponse(
            request_key=key,
            url=entry.url,
            status=entry.status,
            final_url=entry.final_url,
            timestamp=entry.timestamp,
            sha256=entry.sha256,
            outcome=entry.outcome,
            body=read_archive(self.path, key),
            from_archive=True,
        )


class SnapshotStore:
    """Writable Snapshot used by Collect."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "raw").mkdir(exist_ok=True)
        self._db = sqlite3.connect(self.path / "requests.sqlite")
        self._db.executescript(_SCHEMA)
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    # -- snapshot.json

    @property
    def meta_path(self) -> Path:
        return self.path / "snapshot.json"

    def load_meta(self) -> dict[str, Any]:
        if not self.meta_path.is_file():
            return {}
        return json.loads(self.meta_path.read_text(encoding="utf-8"))

    def save_meta(self, meta: dict[str, Any]) -> None:
        tmp = self.meta_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")
        tmp.replace(self.meta_path)

    # -- request log

    def latest(self, key: str) -> LogEntry | None:
        row = self._db.execute(
            "SELECT request_key, url, status, final_url, timestamp, sha256, outcome, detail, batch "
            "FROM requests WHERE request_key = ? ORDER BY id DESC LIMIT 1",
            (key,),
        ).fetchone()
        return LogEntry(*row) if row else None

    def log(self, entry: LogEntry) -> None:
        self._db.execute(
            "INSERT INTO requests (request_key, url, status, final_url, timestamp, sha256, outcome, detail, batch) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.request_key,
                entry.url,
                entry.status,
                entry.final_url,
                entry.timestamp,
                entry.sha256,
                entry.outcome,
                entry.detail,
                entry.batch,
            ),
        )
        self._db.commit()

    def keys(self, prefix: str = "") -> list[str]:
        rows = self._db.execute(
            "SELECT DISTINCT request_key FROM requests WHERE substr(request_key, 1, ?) = ? ORDER BY request_key",
            (len(prefix), prefix),
        ).fetchall()
        return [r[0] for r in rows]

    @property
    def meta(self) -> dict[str, Any]:
        return self.load_meta()

    def all_entries(self) -> list[LogEntry]:
        rows = self._db.execute(
            "SELECT request_key, url, status, final_url, timestamp, sha256, outcome, detail, batch "
            "FROM requests ORDER BY id"
        ).fetchall()
        return [LogEntry(*r) for r in rows]

    # -- archive

    def write_archive(self, key: str, body: bytes) -> str:
        path = self.path / "raw" / key
        path.parent.mkdir(parents=True, exist_ok=True)
        data = gzip.compress(body, mtime=0) if key.endswith(".gz") else body
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
        return hashlib.sha256(body).hexdigest()

    def read_archive(self, key: str) -> bytes | None:
        return read_archive(self.path, key)

    def response(self, key: str) -> StoredResponse | None:
        entry = self.latest(key)
        if entry is None:
            return None
        return StoredResponse(
            key, entry.url, entry.status, entry.final_url, entry.timestamp, entry.sha256, entry.outcome,
            self.read_archive(key), from_archive=True,
        )


def read_archive(snapshot_path: Path, key: str) -> bytes | None:
    path = snapshot_path / "raw" / key
    if not path.is_file():
        return None
    data = path.read_bytes()
    return gzip.decompress(data) if key.endswith(".gz") else data


def latest_entries(db_path: Path) -> dict[str, LogEntry]:
    db = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "SELECT request_key, url, status, final_url, timestamp, sha256, outcome, detail, batch "
            "FROM requests WHERE id IN (SELECT MAX(id) FROM requests GROUP BY request_key)"
        ).fetchall()
    finally:
        db.close()
    return {r[0]: LogEntry(*r) for r in rows}


# ----------------------------------------------------------------------------- months


def observation_window(collection_date: dt.date) -> tuple[str, str]:
    """The latest complete 60 calendar months before the collection date, as (first, last) `YYYY-MM`."""
    last_year, last_month = collection_date.year, collection_date.month - 1
    if last_month == 0:
        last_year, last_month = last_year - 1, 12
    index = last_year * 12 + (last_month - 1) - 59
    first_year, first_month = divmod(index, 12)
    return f"{first_year:04d}-{first_month + 1:02d}", f"{last_year:04d}-{last_month:02d}"
