"""Collect: the four stages in strict order (pool, history, store, taglist), resumable by rerunning."""

from __future__ import annotations

import datetime as dt
import time
from collections import Counter
import logging
import platform
from collections.abc import Callable
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

from steamstudy import __version__
from steamstudy import tag_source as T
from steamstudy.build.parse import ParseError, parse_steamcharts_app, parse_store_page, parse_tag_list, parse_top_page
from steamstudy.build.pool import pool_appids, skipped_app_rows
from steamstudy.collect.progress import Progress
from steamstudy.export import schema as S
from steamstudy.export.writer import write_csv
from steamstudy.build.score import Window, score
from steamstudy.collect.fetcher import Clock, Fetcher, LiveTransport, RealClock, SourcePolicy, Transport
from steamstudy.config import Config
from steamstudy.snapshot import SnapshotStore, observation_window, utc_now

log = logging.getLogger(__name__)

STAGES = ("pool", "history", "store", "taglist")
STEAMCHARTS = "https://steamcharts.com"
STORE = "https://store.steampowered.com"
TAGLIST_URL = "https://api.steampowered.com/IStoreService/GetTagList/v1/?language=english"
TAGLIST_KEY = "steam_api/GetTagList.json"
UA_PLACEHOLDER = "<fill in"
PROGRESS_SECONDS = 10.0


class CollectRefused(Exception):
    """Collection must not start (gate not met, closed Snapshot, missing contact, ...)."""


@dataclass
class Context:
    store: SnapshotStore
    fetcher: Fetcher
    config: Config
    meta: dict[str, Any]

    @property
    def test_mode(self) -> bool:
        return self.meta["mode"] == "test"

    @property
    def window(self) -> Window:
        w = self.meta["observation_window"]
        return Window(w["first"], w["last"])

    def save(self) -> None:
        self.store.save_meta(self.meta)


# ----------------------------------------------------------------------------- entry point


def snapshots_dir(root: Path) -> Path:
    return Path(root) / "snapshots"


def latest_snapshot_id(root: Path, *, mode: str | None = None, open_only: bool = False) -> str | None:
    import json

    best: tuple[str, str] | None = None
    base = snapshots_dir(root)
    if not base.is_dir():
        return None
    for path in base.iterdir():
        meta_path = path / "snapshot.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if mode and meta.get("mode") != mode:
            continue
        if open_only and meta.get("closed"):
            continue
        key = (str(meta.get("created_at", "")), path.name)
        if best is None or key > best:
            best = key
    return best[1] if best else None


def run_collect(
    root: Path,
    config: Config,
    *,
    mode: str | None = None,
    snapshot_id: str | None = None,
    stage: str | None = None,
    tag_source: str | None = None,
    transport: Transport | None = None,
    clock: Clock | None = None,
    today: dt.date | None = None,
    now: Callable[[], dt.datetime] | None = None,
) -> str:
    """Run every stage (or one) on a new or resumed Snapshot; returns the Snapshot id.

    `tag_source` (`steam` or `steamdb`) is fixed when the Snapshot is created; None keeps a resumed Snapshot's
    source, or picks `steam` for a new one. Raises `CollectRefused` before any request, and `HardStop` when
    collection must stop.
    """
    if UA_PLACEHOLDER in config.collection.user_agent:
        raise CollectRefused("collection.toml: fill in the contact details in contact.user_agent first")
    if tag_source is not None and tag_source not in T.TAG_SOURCES:
        raise CollectRefused(f"unknown tag source {tag_source!r}: use one of {', '.join(T.TAG_SOURCES)}")

    if snapshot_id is None:
        snapshot_id = latest_snapshot_id(root, mode=mode, open_only=True)
    store_path = snapshots_dir(root) / snapshot_id if snapshot_id else None
    if store_path is None or not (store_path / "snapshot.json").is_file():
        if stage is not None and mode is None:
            raise CollectRefused("no open Snapshot to run this stage on; start one with --mode test|full")
        if mode is None:
            raise CollectRefused("--mode test|full is required to start a new Snapshot")
        _check_gate(config, mode)
        _check_tag_source(config, tag_source or T.STEAM)
        store, meta = _create(root, config, mode, snapshot_id, today or dt.datetime.now(dt.UTC).date(), now,
                              tag_source or T.STEAM)
    else:
        store = SnapshotStore(store_path)
        meta = store.load_meta()
        try:
            if mode is not None and meta["mode"] != mode:
                raise CollectRefused(f"Snapshot {meta['id']} is a {meta['mode']} Snapshot, not {mode}")
            if meta.get("closed"):
                raise CollectRefused(f"Snapshot {meta['id']} is closed; only --repair and collect steamdb may change it")
            if tag_source is not None and T.of(meta) != tag_source:
                raise CollectRefused(f"Snapshot {meta['id']} takes its tags from {T.of(meta)}, not {tag_source}; "
                                     "the tag source is fixed when a Snapshot is created")
            _check_gate(config, meta["mode"])
            _check_tag_source(config, T.of(meta))
        except CollectRefused:
            store.close()
            raise

    _record_rates(meta, config)
    fetcher = make_fetcher(store, config, meta, transport=transport, clock=clock)
    ctx = Context(store, fetcher, config, meta)
    ctx.save()
    resumed = bool(meta["stages"])
    log.info("%s %s Snapshot %s in %s (Observation Window %s to %s, tags from %s)",
             "Resuming" if resumed else "Starting", meta["mode"], meta["id"], store.path,
             meta["observation_window"]["first"], meta["observation_window"]["last"], T.of(meta))
    try:
        stages = STAGES if stage is None else (stage,)
        for name in stages:
            if stage is not None:
                _require_previous(ctx, name)
            STAGE_FUNCTIONS[name](ctx)
        if stage is None:
            meta["closed"] = True
            meta["closed_at"] = utc_now()
            log.info("Snapshot %s closed after %d requests in this run. Next: steamstudy build --snapshot %s",
                     meta["id"], fetcher.network_requests, meta["id"])
    finally:
        ctx.save()
        write_skipped_report(store)
        store.close()
    return str(meta["id"])


def write_skipped_report(store: SnapshotStore) -> Path | None:
    """`skipped_apps.csv` next to snapshot.json: every app whose Steam Charts page was skipped."""
    rows = skipped_app_rows(store)
    path = store.path / "skipped_apps.csv"
    if not rows and not path.exists():
        return None
    write_csv(path, S.SKIPPED_APPS_SNAPSHOT, rows)
    return path


def _check_gate(config: Config, mode: str) -> None:
    if mode != "full":
        return
    missing = []
    if not config.collection.operator_reply.recorded:
        missing.append("gate.operator_reply (reference and date)")
    if not config.collection.ethics_check.recorded:
        missing.append("gate.ethics_check (reference and date)")
    if missing:
        raise CollectRefused("full-run gate: collection.toml must record " + " and ".join(missing))


def _check_tag_source(config: Config, source: str) -> None:
    if source == T.STEAMDB and not config.collection.steamdb_permission.reference.strip():
        raise CollectRefused("collection.toml records no SteamDB permission reference: "
                             "the steamdb tag source is disabled")


def _create(
    root: Path, config: Config, mode: str, snapshot_id: str | None, today: dt.date,
    now: Callable[[], dt.datetime] | None, tag_source: str,
) -> tuple[SnapshotStore, dict[str, Any]]:
    started = (now or (lambda: dt.datetime.now(dt.UTC)))()
    snapshot_id = snapshot_id or f"{started.strftime('%Y%m%dT%H%M%SZ')}-{mode}"
    first, last = observation_window(today)
    store = SnapshotStore(snapshots_dir(root) / snapshot_id)
    c = config.collection
    meta: dict[str, Any] = {
        "id": snapshot_id,
        "mode": mode,
        "created_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collection_date": today.isoformat(),
        "observation_window": {"first": first, "last": last},
        "collection_config_hash": config.collection_config_hash,
        "user_agent": c.user_agent,
        "age_check_birth_date": age_check_birth_date(today).isoformat(),
        "store_country": None,
        "tag_source": tag_source,
        "taglist_version_hash": None,
        "extra_appids": list(c.edge_case_appids) if mode == "test" else [],
        "stages": {},
        "pool": {"passes": [], "one_pass_only_appids": None},
        "rates": [],
        "gate": {
            "operator_reply": {"reference": c.operator_reply.reference, "date": c.operator_reply.date},
            "ethics_check": {"reference": c.ethics_check.reference, "date": c.ethics_check.date},
        },
        "steamdb": {"permission_reference": c.steamdb_permission.reference, "batches": []},
        "repairs": [],
        "software_versions": software_versions(),
        "closed": False,
    }
    return store, meta


def age_check_birth_date(collection_date: dt.date) -> dt.date:
    try:
        return collection_date.replace(year=collection_date.year - 30)
    except ValueError:  # 29 February
        return collection_date.replace(year=collection_date.year - 30, day=28)


def age_check_cookie(birth: dt.date) -> str:
    """The standard logged-out age-check cookie (what the store sets after a visitor enters a birth date)."""
    epoch = int(dt.datetime(birth.year, birth.month, birth.day, tzinfo=dt.UTC).timestamp())
    return f"birthtime={epoch}; lastagecheckage={birth.day}-{birth.month - 1}-{birth.year}; wants_mature_content=1"


def make_fetcher(
    store: SnapshotStore,
    config: Config,
    meta: dict[str, Any],
    *,
    transport: Transport | None = None,
    clock: Clock | None = None,
    batch: str = "",
) -> Fetcher:
    c = config.collection
    birth = dt.date.fromisoformat(meta["age_check_birth_date"])
    policies = {
        "steamcharts": SourcePolicy("steamcharts", 1.0 / c.steamcharts_per_second),
        "store": SourcePolicy("store", c.store_seconds_per_request, age_check_cookie(birth)),
        "steamdb": SourcePolicy("steamdb", c.steamdb_seconds_per_request),
    }
    return Fetcher(
        store=store,
        transport=transport or LiveTransport(),
        policies=policies,
        user_agent=c.user_agent,
        timeout=(c.connect_timeout, c.read_timeout),
        retry_schedule=c.retry_schedule,
        parse_failure_limit=c.parse_failures_in_a_row,
        clock=clock or RealClock(),
        batch=batch,
    )


def _record_rates(meta: dict[str, Any], config: Config) -> None:
    c = config.collection
    current = {
        "steamcharts_per_second": c.steamcharts_per_second,
        "store_seconds_per_request": c.store_seconds_per_request,
        "steamdb_seconds_per_request": c.steamdb_seconds_per_request,
    }
    if not meta["rates"] or meta["rates"][-1]["values"] != current:
        meta["rates"].append({"from": utc_now(), "values": current})


def software_versions() -> dict[str, str]:
    versions = {"python": platform.python_version(), "steamstudy": __version__}
    for pkg in ("requests", "lxml"):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    return versions


def _require_previous(ctx: Context, name: str) -> None:
    order = STAGES.index(name)
    for earlier in STAGES[:order]:
        if earlier == "taglist":
            continue
        if not ctx.meta["stages"].get(earlier, {}).get("ended"):
            raise CollectRefused(f"stage {name} needs stage {earlier} to finish first")


def _stage_start(ctx: Context, name: str) -> None:
    stage = ctx.meta["stages"].setdefault(name, {})
    stage.setdefault("started", utc_now())
    stage.pop("ended", None)
    ctx.save()


def _stage_end(ctx: Context, name: str, **info: Any) -> None:
    stage = ctx.meta["stages"][name]
    stage.update(info)
    stage["ended"] = utc_now()
    ctx.save()


def _parses(parser: Callable[[bytes], Any]) -> Callable[[bytes], bool]:
    def check(body: bytes) -> bool:
        try:
            parser(body)
        except ParseError:
            return False
        return True

    return check


# ----------------------------------------------------------------------------- stages


def stage_pool(ctx: Context) -> None:
    _stage_start(ctx, "pool")
    log.info("pool: reading the Steam Charts /top listing")
    passes = 1 if ctx.test_mode else ctx.config.collection.listing_passes
    max_pages = ctx.config.collection.test_listing_pages if ctx.test_mode else None
    seen: list[set[int]] = []
    pass_meta: list[dict[str, Any]] = ctx.meta["pool"]["passes"]
    for n in range(1, passes + 1):
        while len(pass_meta) < n:
            pass_meta.append({"pass": len(pass_meta) + 1})
        info = pass_meta[n - 1]
        info.setdefault("started", utc_now())
        appids: set[int] = set()
        rows = 0
        page = 1
        end = "page_limit"
        last_line = time.monotonic()
        while max_pages is None or page <= max_pages:
            key = f"steamcharts/top/pass-{n}/p-{page:04d}.html.gz"
            if time.monotonic() - last_line >= PROGRESS_SECONDS:
                last_line = time.monotonic()
                log.info("pool pass %d of %d: page %d, %s rows so far", n, passes, page, f"{rows:,}")
            resp = ctx.fetcher.fetch(key, f"{STEAMCHARTS}/top/p.{page}", check=_parses(parse_top_page))
            if resp.outcome == "end_of_listing":
                end = "404"
                break
            if resp.outcome == "ok":
                parsed = parse_top_page(resp.body or b"")
                if not parsed:
                    end = "empty_page"
                    break
                rows += len(parsed)
                appids.update(r.appid for r in parsed)
            page += 1
        info.update(ended=utc_now(), pages=page - 1, rows=rows, appids=len(appids), ended_by=end)
        seen.append(appids)
        ctx.save()
        log.info("pool pass %d of %d finished: %d pages, %s rows, %s apps (ended by %s)", n, passes, page - 1,
                 f"{rows:,}", f"{len(appids):,}", end)
    union = set().union(*seen) if seen else set()
    one_pass_only = sum(1 for a in union if sum(a in s for s in seen) == 1) if len(seen) > 1 else 0
    ctx.meta["pool"]["one_pass_only_appids"] = one_pass_only
    _stage_end(ctx, "pool", pool_size=len(union), extra_appids=len(ctx.meta["extra_appids"]))
    extra = set(ctx.meta["extra_appids"]) - union
    log.info("pool finished: Candidate Pool of %s apps (%s seen in only one pass, %d edge cases added)",
             f"{len(union) + len(extra):,}", f"{one_pass_only:,}", len(extra))


def stage_history(ctx: Context) -> None:
    """One Steam Charts page per pool app. A page that keeps failing to load or parse is skipped and
    reported in skipped_apps.csv; anti-bot signals still stop collection."""
    _stage_start(ctx, "history")
    appids = pool_appids(ctx.store)
    log.info("history: one Steam Charts page for each of %s apps", f"{len(appids):,}")
    progress = Progress("history", len(appids))
    outcomes: Counter[str] = Counter()
    for appid in appids:
        before = ctx.fetcher.network_requests
        resp = ctx.fetcher.fetch(f"steamcharts/app/{appid}.html.gz", f"{STEAMCHARTS}/app/{appid}",
                                 check=_parses(parse_steamcharts_app), skip_on_failure=True)
        outcomes[resp.outcome] += 1
        progress.step(fetched=ctx.fetcher.network_requests > before, skipped=resp.outcome == "skipped")
    progress.finish(_outcome_summary(outcomes))
    if outcomes["skipped"]:
        log.warning("history: %d apps skipped; see %s", outcomes["skipped"], ctx.store.path / "skipped_apps.csv")
    _stage_end(ctx, "history", apps=len(appids), skipped=outcomes["skipped"])


def _outcome_summary(outcomes: Counter[str]) -> str:
    ordered = sorted(outcomes.items(), key=lambda kv: -kv[1])
    return ", ".join(f"{n:,} {name.replace('_', ' ')}" for name, n in ordered)


def scored_appids(store: SnapshotStore, meta: dict[str, Any]) -> list[int]:
    """Pool apps that `score()` scores: the only apps the store stage fetches."""
    w = meta["observation_window"]
    window = Window(w["first"], w["last"])
    out = []
    for appid in pool_appids(store):
        resp = store.response(f"steamcharts/app/{appid}.html.gz")
        if resp is None or resp.outcome != "ok":
            continue
        try:
            history = parse_steamcharts_app(resp.body or b"", last_month=window.last)
        except ParseError:
            continue
        if score(history, window) is not None:
            out.append(appid)
    return out


def stage_store(ctx: Context) -> None:
    stage_taglist(ctx)
    _stage_start(ctx, "store")
    appids = scored_appids(ctx.store, ctx.meta)
    source = T.of(ctx.meta)
    log.info("store: store page and appdetails%s for each of %s scored apps",
             " (and the SteamDB page for its tags)" if source == T.STEAMDB else "", f"{len(appids):,}")
    progress = Progress("store", len(appids))
    outcomes: Counter[str] = Counter()
    for appid in appids:
        before = ctx.fetcher.network_requests
        page = ctx.fetcher.fetch(
            f"store/page/{appid}.html.gz", f"{STORE}/app/{appid}/?l=english", check=_parses(parse_store_page)
        )
        if page.outcome == "ok" and ctx.meta.get("store_country") is None:
            ctx.meta["store_country"] = parse_store_page(page.body or b"").country
        details = ctx.fetcher.fetch(f"store/appdetails/{appid}.json.gz",
                                    f"{STORE}/api/appdetails?appids={appid}&l=english")
        outcomes[f"page {page.outcome}"] += 1
        outcomes[f"appdetails {details.outcome}"] += 1
        if (request := T.tag_request(source, appid)) is not None:
            tags = ctx.fetcher.fetch(request.request_key, request.url, check=_parses(request.parser))
            outcomes[f"{source} {tags.outcome}"] += 1
        progress.step(fetched=ctx.fetcher.network_requests > before)
    progress.finish(_outcome_summary(outcomes))
    _stage_end(ctx, "store", apps=len(appids))


def stage_taglist(ctx: Context) -> None:
    if ctx.meta["stages"].get("taglist", {}).get("ended"):
        return
    _stage_start(ctx, "taglist")
    resp = ctx.fetcher.fetch(TAGLIST_KEY, TAGLIST_URL, check=_parses(parse_tag_list))
    if resp.outcome == "ok":
        vocabulary = parse_tag_list(resp.body or b"")
        ctx.meta["taglist_version_hash"] = vocabulary.version_hash
        log.info("taglist: GetTagList vocabulary of %d tags (version_hash %s)", len(vocabulary.tags),
                 vocabulary.version_hash)
    _stage_end(ctx, "taglist")


STAGE_FUNCTIONS: dict[str, Callable[[Context], None]] = {
    "pool": stage_pool,
    "history": stage_history,
    "store": stage_store,
    "taglist": stage_taglist,
}


# ----------------------------------------------------------------------------- repair


def run_repair(
    root: Path,
    config: Config,
    appid: int,
    reason: str,
    *,
    snapshot_id: str | None = None,
    transport: Transport | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Refetch one app into a closed Snapshot (its Steam Charts page, and its store data and Tag Source page
    if it is scored), logged as a repair in `snapshot.json`. The only change a closed Snapshot accepts besides
    SteamDB batches."""
    if not reason or not reason.strip():
        raise CollectRefused("--repair needs a written --reason")
    if UA_PLACEHOLDER in config.collection.user_agent:
        raise CollectRefused("collection.toml: fill in the contact details in contact.user_agent first")
    snapshot_id = snapshot_id or latest_snapshot_id(root)
    if snapshot_id is None or not (snapshots_dir(root) / snapshot_id / "snapshot.json").is_file():
        raise CollectRefused("no Snapshot to repair")
    store = SnapshotStore(snapshots_dir(root) / snapshot_id)
    meta = store.load_meta()
    try:
        if not meta.get("closed"):
            raise CollectRefused(f"Snapshot {snapshot_id} is still open: rerun collect to resume instead of repairing")
        if appid not in pool_appids(store):
            raise CollectRefused(f"AppID {appid} is not in Snapshot {snapshot_id}'s Candidate Pool")
        _check_tag_source(config, T.of(meta))
        batch = f"repair-{len(meta['repairs']) + 1}"
        fetcher = make_fetcher(store, config, meta, transport=transport, clock=clock, batch=batch)
        started = utc_now()
        outcomes: dict[str, str] = {}
        history = fetcher.fetch(f"steamcharts/app/{appid}.html.gz", f"{STEAMCHARTS}/app/{appid}",
                                check=_parses(parse_steamcharts_app), force=True, skip_on_failure=True)
        outcomes[history.request_key] = history.outcome
        if appid in scored_appids(store, meta) or store.latest(f"store/page/{appid}.html.gz") is not None:
            requests: list[tuple[str, str, Callable[[bytes], bool] | None]] = [
                (f"store/page/{appid}.html.gz", f"{STORE}/app/{appid}/?l=english", _parses(parse_store_page)),
                (f"store/appdetails/{appid}.json.gz", f"{STORE}/api/appdetails?appids={appid}&l=english", None),
            ]
            if (request := T.tag_request(T.of(meta), appid)) is not None:
                requests.append((request.request_key, request.url, _parses(request.parser)))
            for key, url, check in requests:
                outcomes[key] = fetcher.fetch(key, url, check=check, force=True).outcome
        repair = {"appid": appid, "reason": reason.strip(), "batch": batch, "started": started, "ended": utc_now(),
                  "outcomes": outcomes}
        meta["repairs"].append(repair)
        store.save_meta(meta)
        write_skipped_report(store)
        return repair
    finally:
        store.close()


# ----------------------------------------------------------------------------- SteamDB cross-check


def run_steamdb(
    root: Path,
    config: Config,
    build_id: str,
    *,
    transport: Transport | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Fetch SteamDB pages for one Build's Top-100 members only, as a logged batch of that Build's Snapshot.

    Refuses before any request unless `collection.toml` records a SteamDB permission reference.
    SteamDB values never enter a dataset; the next Build writes reports/steamdb_crosscheck.csv. Refused for a
    Snapshot whose Tag Source is SteamDB, which already has a SteamDB page for every scored app.
    """
    permission = config.collection.steamdb_permission
    if not permission.reference.strip():
        raise CollectRefused("collection.toml records no SteamDB permission reference: the cross-check is disabled")
    if UA_PLACEHOLDER in config.collection.user_agent:
        raise CollectRefused("collection.toml: fill in the contact details in contact.user_agent first")
    from steamstudy.build.writer import resolve_build
    from steamstudy.export import schema as S
    from steamstudy.export.writer import read_typed_csv

    folder = resolve_build(root, build_id)
    snapshot_id = folder.parent.name
    members: set[int] = set()
    for key in S.DATASET_KEYS:
        path = folder / "datasets" / f"top100_{key}.csv"
        if path.is_file():
            members.update(int(r["appid"]) for r in read_typed_csv(path, S.TOP100))
    store = SnapshotStore(snapshots_dir(root) / snapshot_id)
    meta = store.load_meta()
    try:
        if T.of(meta) == T.STEAMDB:
            raise CollectRefused(f"Snapshot {snapshot_id} already takes its tags from SteamDB: every scored app has "
                                 "a SteamDB page, and each Build writes the cross-check")
        batch = f"steamdb-{len(meta['steamdb']['batches']) + 1}"
        fetcher = make_fetcher(store, config, meta, transport=transport, clock=clock, batch=batch)
        started = utc_now()
        outcomes: Counter[str] = Counter()
        for appid in sorted(members):
            outcomes[fetcher.fetch(T.steamdb_key(appid), f"{T.STEAMDB_URL}/app/{appid}/", force=True).outcome] += 1
        record = {"batch": batch, "build_id": folder.name, "permission_reference": permission.reference,
                  "permission_date": permission.date, "started": started, "ended": utc_now(),
                  "apps": len(members), "outcomes": dict(outcomes)}
        meta["steamdb"]["batches"].append(record)
        store.save_meta(meta)
        return record
    finally:
        store.close()
