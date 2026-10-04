"""Collect: the four stages in strict order (pool, history, store, taglist), resumable by rerunning."""

from __future__ import annotations

import datetime as dt
import logging
import platform
from collections.abc import Callable
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

from steamstudy import __version__
from steamstudy.build.parse import ParseError, parse_steamcharts_app, parse_store_page, parse_tag_list, parse_top_page
from steamstudy.build.pool import pool_appids
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
    transport: Transport | None = None,
    clock: Clock | None = None,
    today: dt.date | None = None,
    now: Callable[[], dt.datetime] | None = None,
) -> str:
    """Run every stage (or one) on a new or resumed Snapshot; returns the Snapshot id.

    Raises `CollectRefused` before any request, and `HardStop` when collection must stop.
    """
    if UA_PLACEHOLDER in config.collection.user_agent:
        raise CollectRefused("collection.toml: fill in the contact details in contact.user_agent first")

    if snapshot_id is None:
        snapshot_id = latest_snapshot_id(root, mode=mode, open_only=True)
    store_path = snapshots_dir(root) / snapshot_id if snapshot_id else None
    if store_path is None or not (store_path / "snapshot.json").is_file():
        if stage is not None and mode is None:
            raise CollectRefused("no open Snapshot to run this stage on; start one with --mode test|full")
        if mode is None:
            raise CollectRefused("--mode test|full is required to start a new Snapshot")
        _check_gate(config, mode)
        store, meta = _create(root, config, mode, snapshot_id, today or dt.datetime.now(dt.UTC).date(), now)
    else:
        store = SnapshotStore(store_path)
        meta = store.load_meta()
        try:
            if mode is not None and meta["mode"] != mode:
                raise CollectRefused(f"Snapshot {meta['id']} is a {meta['mode']} Snapshot, not {mode}")
            if meta.get("closed"):
                raise CollectRefused(f"Snapshot {meta['id']} is closed; only --repair and collect steamdb may change it")
            _check_gate(config, meta["mode"])
        except CollectRefused:
            store.close()
            raise

    _record_rates(meta, config)
    fetcher = make_fetcher(store, config, meta, transport=transport, clock=clock)
    ctx = Context(store, fetcher, config, meta)
    ctx.save()
    try:
        stages = STAGES if stage is None else (stage,)
        for name in stages:
            if stage is not None:
                _require_previous(ctx, name)
            STAGE_FUNCTIONS[name](ctx)
        if stage is None:
            meta["closed"] = True
            meta["closed_at"] = utc_now()
            log.info("Snapshot %s closed", meta["id"])
    finally:
        ctx.save()
        store.close()
    return str(meta["id"])


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


def _create(
    root: Path, config: Config, mode: str, snapshot_id: str | None, today: dt.date, now: Callable[[], dt.datetime] | None
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
        while max_pages is None or page <= max_pages:
            key = f"steamcharts/top/pass-{n}/p-{page:04d}.html.gz"
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
    union = set().union(*seen) if seen else set()
    one_pass_only = sum(1 for a in union if sum(a in s for s in seen) == 1) if len(seen) > 1 else 0
    ctx.meta["pool"]["one_pass_only_appids"] = one_pass_only
    _stage_end(ctx, "pool", pool_size=len(union), extra_appids=len(ctx.meta["extra_appids"]))


def stage_history(ctx: Context) -> None:
    _stage_start(ctx, "history")
    appids = pool_appids(ctx.store)
    for appid in appids:
        ctx.fetcher.fetch(
            f"steamcharts/app/{appid}.html.gz", f"{STEAMCHARTS}/app/{appid}", check=_parses(parse_steamcharts_app)
        )
    _stage_end(ctx, "history", apps=len(appids))


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
            history = parse_steamcharts_app(resp.body or b"")
        except ParseError:
            continue
        if score(history, window) is not None:
            out.append(appid)
    return out


def stage_store(ctx: Context) -> None:
    stage_taglist(ctx)
    _stage_start(ctx, "store")
    appids = scored_appids(ctx.store, ctx.meta)
    for appid in appids:
        page = ctx.fetcher.fetch(
            f"store/page/{appid}.html.gz", f"{STORE}/app/{appid}/?l=english", check=_parses(parse_store_page)
        )
        if page.outcome == "ok" and ctx.meta.get("store_country") is None:
            ctx.meta["store_country"] = parse_store_page(page.body or b"").country
        ctx.fetcher.fetch(f"store/appdetails/{appid}.json.gz", f"{STORE}/api/appdetails?appids={appid}&l=english")
    _stage_end(ctx, "store", apps=len(appids))


def stage_taglist(ctx: Context) -> None:
    if ctx.meta["stages"].get("taglist", {}).get("ended"):
        return
    _stage_start(ctx, "taglist")
    resp = ctx.fetcher.fetch(TAGLIST_KEY, TAGLIST_URL, check=_parses(parse_tag_list))
    if resp.outcome == "ok":
        ctx.meta["taglist_version_hash"] = parse_tag_list(resp.body or b"").version_hash
    _stage_end(ctx, "taglist")


STAGE_FUNCTIONS: dict[str, Callable[[Context], None]] = {
    "pool": stage_pool,
    "history": stage_history,
    "store": stage_store,
    "taglist": stage_taglist,
}
