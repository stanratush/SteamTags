"""`Fetcher.fetch(request_key, url) -> StoredResponse`: every network request in the project.

The Fetcher hides all request handling: per-source rate and one kept-alive connection per source,
User-Agent and age-check cookie, retries, challenge detection and the hard stop, archiving and
the request log, and skipping requests that already have a final outcome on resume.

Two transports plug in underneath: `LiveTransport` (requests) and `FakeTransport` (tests).
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol

from steamstudy.snapshot import LogEntry, SnapshotStore, StoredResponse, utc_now

log = logging.getLogger(__name__)

HARD_STOP_STATUSES = frozenset({403, 429, 503})
CHALLENGE_MARKERS = (
    b"challenge-platform",
    b"cf_chl_opt",
    b"cf-chl-",
    b"<title>Just a moment...</title>",
    b"Attention Required! | Cloudflare",
)


class HardStop(Exception):
    """Collection must stop now; rerunning the same command resumes."""

    def __init__(self, reason: str, request_key: str = ""):
        super().__init__(f"{reason} ({request_key})" if request_key else reason)
        self.reason = reason
        self.request_key = request_key


class TransportError(Exception):
    """A timeout or connection failure, retried on the 10/30/90 s schedule."""

    def __init__(self, kind: str, message: str = ""):
        super().__init__(f"{kind}: {message}")
        self.kind = kind


@dataclass(frozen=True)
class RawResponse:
    status: int
    final_url: str
    body: bytes
    redirects: tuple[int, ...] = ()


class Transport(Protocol):
    def get(
        self, source: str, url: str, headers: Mapping[str, str], timeout: tuple[float, float]
    ) -> RawResponse: ...


class Clock(Protocol):
    def monotonic(self) -> float: ...

    def sleep(self, seconds: float) -> None: ...


class RealClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)


@dataclass(frozen=True)
class SourcePolicy:
    name: str
    min_interval: float  # seconds between request starts
    cookie: str = ""


@dataclass
class Fetcher:
    store: SnapshotStore
    transport: Transport
    policies: Mapping[str, SourcePolicy]
    user_agent: str
    timeout: tuple[float, float] = (10.0, 30.0)
    retry_schedule: tuple[float, ...] = (10.0, 30.0, 90.0)
    parse_failure_limit: int = 5
    clock: Clock = field(default_factory=RealClock)
    batch: str = ""
    _last_start: dict[str, float] = field(default_factory=dict)
    _parse_failures_in_a_row: int = 0
    network_requests: int = 0

    def fetch(
        self,
        request_key: str,
        url: str,
        *,
        check: Callable[[bytes], bool] | None = None,
        force: bool = False,
        skip_on_failure: bool = False,
    ) -> StoredResponse:
        """Fetch `url` into `request_key`, or return the archived response if it has a final outcome.

        `check` is the stage's parser: a response that fails it is a parse-structure failure.
        `force` refetches even a final outcome (only `--repair` uses it).
        `skip_on_failure`: when the page keeps failing to load (retries exhausted) or cannot be parsed, record
        the final outcome `skipped` and carry on instead of stopping. Anti-bot signals (403, 429, 503,
        challenge pages) always stop, whatever this says.
        """
        previous = self.store.latest(request_key)
        if previous is not None and previous.is_final and not force:
            return self.store.response(request_key)  # type: ignore[return-value]

        source = source_of(request_key)
        policy = self.policies[source]
        headers = {"User-Agent": self.user_agent}
        if policy.cookie:
            headers["Cookie"] = policy.cookie

        attempt = 0
        while True:
            self._wait_turn(policy)
            self.network_requests += 1
            try:
                raw = self.transport.get(source, url, headers, self.timeout)
            except TransportError as exc:
                if self._retry_or_give_up(request_key, url, attempt, None, str(exc), skip_on_failure):
                    return self._skip(request_key, url, None, f"failed to load after {attempt + 1} attempts: {exc}")
                attempt += 1
                continue

            outcome, detail = classify(request_key, raw)
            if outcome == "retryable_error":
                if self._retry_or_give_up(request_key, url, attempt, raw, detail, skip_on_failure):
                    return self._skip(request_key, url, raw, f"failed to load after {attempt + 1} attempts: {detail}")
                attempt += 1
                continue
            if outcome == "hard_stop":
                self._record(request_key, url, raw, "hard_stop", detail)
                raise HardStop(detail, request_key)

            if outcome == "ok" and check is not None:
                if check(raw.body):
                    self._parse_failures_in_a_row = 0
                elif skip_on_failure:
                    return self._skip(request_key, url, raw, "parser could not read the expected structure")
                else:
                    outcome, detail = "parse_failure", "parser could not read the expected structure"
                    self._parse_failures_in_a_row += 1
            stored = self._record(request_key, url, raw, outcome, detail)
            if self._parse_failures_in_a_row >= self.parse_failure_limit:
                raise HardStop(f"{self._parse_failures_in_a_row} parse-structure failures in a row", request_key)
            return stored

    # -- internals

    def _wait_turn(self, policy: SourcePolicy) -> None:
        last = self._last_start.get(policy.name)
        if last is not None:
            wait = last + policy.min_interval - self.clock.monotonic()
            if wait > 0:
                self.clock.sleep(wait)
        self._last_start[policy.name] = self.clock.monotonic()

    def _retry_or_give_up(self, key: str, url: str, attempt: int, raw: RawResponse | None, detail: str,
                          skip: bool) -> bool:
        """Log and wait for the next retry; True when the retries are used up and the caller may skip.
        Raises HardStop when they are used up and skipping is not allowed."""
        status = raw.status if raw is not None else None
        if attempt >= len(self.retry_schedule):
            if skip:
                return True
            if raw is not None:
                self._record(key, url, raw, "hard_stop", detail)
            else:
                self.store.log(LogEntry(key, url, None, None, utc_now(), None, "hard_stop", detail, self.batch))
            raise HardStop(f"gave up after {attempt + 1} attempts: {detail}", key)
        self.store.log(
            LogEntry(key, url, status, raw.final_url if raw else None, utc_now(), None, "retryable_error", detail, self.batch)
        )
        delay = self.retry_schedule[attempt]
        log.warning("retrying %s in %.0f s (attempt %d of %d): %s", url, delay, attempt + 2,
                    len(self.retry_schedule) + 1, detail)
        self.clock.sleep(delay)
        return False

    def _skip(self, key: str, url: str, raw: RawResponse | None, reason: str) -> StoredResponse:
        log.warning("skipped %s: %s", url, reason)
        if raw is not None:
            return self._record(key, url, raw, "skipped", reason)
        timestamp = utc_now()
        self.store.log(LogEntry(key, url, None, None, timestamp, None, "skipped", reason, self.batch))
        return StoredResponse(key, url, None, None, timestamp, None, "skipped", None)

    def _record(self, key: str, url: str, raw: RawResponse, outcome: str, detail: str) -> StoredResponse:
        sha = self.store.write_archive(key, raw.body)
        timestamp = utc_now()
        self.store.log(LogEntry(key, url, raw.status, raw.final_url, timestamp, sha, outcome, detail, self.batch))
        return StoredResponse(key, url, raw.status, raw.final_url, timestamp, sha, outcome, raw.body)


def source_of(request_key: str) -> str:
    head = request_key.split("/", 1)[0]
    if head == "steamcharts":
        return "steamcharts"
    if head in ("store", "steam_api"):
        return "store"
    if head == "steamdb":
        return "steamdb"
    raise ValueError(f"unknown source for request key {request_key!r}")


_APPID = re.compile(r"/(\d+)\.(?:html|json)(?:\.gz)?$")


def classify(request_key: str, raw: RawResponse) -> tuple[str, str]:
    """The retry/stop table: (outcome, detail) for one response."""
    status = raw.status
    if status in HARD_STOP_STATUSES:
        return "hard_stop", f"HTTP {status}"
    head = raw.body[:65536]
    if any(marker in head for marker in CHALLENGE_MARKERS):
        return "hard_stop", "challenge page"

    kind = kind_of(request_key)
    if kind == "top":
        if status == 404:
            return "end_of_listing", "HTTP 404"
    elif kind == "steamcharts_app":
        if status == 404:
            return "not_found", "HTTP 404"
    elif kind == "steamdb":
        if status == 404:
            return "not_found", "HTTP 404"
    elif kind == "store_page":
        if "/agecheck/" in raw.final_url:
            return "age_gate", "redirected to the age check"
        if status == 404:
            return "no_store_page", "HTTP 404"
    if 500 <= status < 600:
        return "retryable_error", f"HTTP {status}"
    if status != 200:
        return "hard_stop", f"unexpected HTTP {status}"

    if kind == "top":
        return ("ok", "") if b'id="top-games"' in raw.body else ("hard_stop", "listing structure marker missing")
    if kind == "steamcharts_app":
        return ("ok", "") if b'id="app-title"' in raw.body else ("hard_stop", "app page structure marker missing")
    if kind == "store_page":
        m = _APPID.search(request_key)
        if m and f"/app/{m.group(1)}" not in raw.final_url:
            return "no_store_page", f"redirected to {raw.final_url}"
        if b'id="agecheck_form"' in raw.body or b"app_agegate" in raw.body:
            return "age_gate", "age check still shown after the cookie"
        if b'id="application_config"' not in raw.body:
            return "hard_stop", "store page structure marker missing"
        if b"apphub_AppName" not in raw.body:
            return "no_store_page", "page has no app"
        return "ok", ""
    if kind in ("appdetails", "taglist"):
        try:
            data = json.loads(raw.body)
        except ValueError:
            return "hard_stop", "response is not JSON"
        if kind == "appdetails":
            m = _APPID.search(request_key)
            entry = data.get(m.group(1)) if (m and isinstance(data, dict)) else None
            if not isinstance(entry, dict) or "success" not in entry:
                return "hard_stop", "appdetails structure missing"
            return ("ok", "") if entry["success"] else ("no_appdetails", "success: false")
        if not isinstance(data, dict) or "tags" not in data.get("response", {}):
            return "hard_stop", "GetTagList structure missing"
        return "ok", ""
    if kind == "steamdb":
        return ("ok", "") if b'href="/tag/' in raw.body else ("hard_stop", "SteamDB page structure marker missing")
    return "ok", ""


def kind_of(request_key: str) -> str:
    if request_key.startswith("steamcharts/top/"):
        return "top"
    if request_key.startswith("steamcharts/app/"):
        return "steamcharts_app"
    if request_key.startswith("store/page/"):
        return "store_page"
    if request_key.startswith("store/appdetails/"):
        return "appdetails"
    if request_key.startswith("steam_api/GetTagList"):
        return "taglist"
    if request_key.startswith("steamdb/"):
        return "steamdb"
    return "other"


# ----------------------------------------------------------------------------- transports


class LiveTransport:
    """requests-based transport: one Session (one kept-alive connection) per source."""

    def __init__(self) -> None:
        import requests
        from requests.adapters import HTTPAdapter

        self._requests = requests
        self._sessions: dict[str, requests.Session] = {}
        self._adapter = HTTPAdapter

    def _session(self, source: str):
        if source not in self._sessions:
            s = self._requests.Session()
            adapter = self._adapter(pool_connections=1, pool_maxsize=1, max_retries=0)
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            self._sessions[source] = s
        return self._sessions[source]

    def get(self, source: str, url: str, headers: Mapping[str, str], timeout: tuple[float, float]) -> RawResponse:
        try:
            r = self._session(source).get(url, headers=dict(headers), timeout=timeout, allow_redirects=True)
        except self._requests.Timeout as exc:
            raise TransportError("timeout", str(exc)) from exc
        except self._requests.ConnectionError as exc:
            raise TransportError("connection", str(exc)) from exc
        return RawResponse(r.status_code, r.url, r.content, tuple(h.status_code for h in r.history))


@dataclass
class FakeCall:
    source: str
    url: str
    headers: dict[str, str]
    at: float


class FakeTransport:
    """Fixture-backed transport: each URL maps to a queue of responses (the last one repeats)."""

    def __init__(self, routes: Mapping[str, list[RawResponse | TransportError] | RawResponse], clock: Clock | None = None):
        self.routes = {url: (list(r) if isinstance(r, list) else [r]) for url, r in routes.items()}
        self.calls: list[FakeCall] = []
        self.clock = clock
        self.sessions: set[str] = set()

    def get(self, source: str, url: str, headers: Mapping[str, str], timeout: tuple[float, float]) -> RawResponse:
        self.sessions.add(source)
        self.calls.append(FakeCall(source, url, dict(headers), self.clock.monotonic() if self.clock else 0.0))
        queue = self.routes.get(url)
        if not queue:
            return RawResponse(404, url, b"not found")
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, TransportError):
            raise item
        return item


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds
