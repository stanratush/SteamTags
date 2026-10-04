"""`build(snapshot, config, build_id) -> BuildResult`: one deterministic derivation, never contacting a source.

The only inputs are the read-only Snapshot and the config (plus the `build_id` the caller chose).
`steamstudy.build.writer` lays the result out as a Build folder.
"""

from __future__ import annotations

import datetime as dt
import platform
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any

from steamstudy import __version__
from steamstudy.build.parse import MonthlyHistory, ParseError, parse_steamcharts_app
from steamstudy.build.pool import Listing, SnapshotLike, read_listing
from steamstudy.build.score import Score, Window, placeholder_rows, score, unscored_reason
from steamstudy.config import Config
from steamstudy.export import schema as S
from steamstudy.export.schema import FileSchema

ATTRIBUTION = "Player data: Steam Charts; tags/metadata: Steam store"
SOURCE_SUBSTITUTIONS = [
    {"source": "Steam store page (displayed tag list, Adult Only notice)", "confirmed": "2026-10-03"},
    {"source": "Steam store appdetails (type, name, is_free, genres, release date, content descriptors)",
     "confirmed": "2026-10-03"},
    {"source": "Steam Web API IStoreService/GetTagList (tag vocabulary)", "confirmed": "2026-10-03"},
]


class BuildFailed(Exception):
    """The Build must not be written (parse errors without --allow-parse-errors, invalid config entries, ...)."""

    def __init__(self, message: str, parse_errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.parse_errors = parse_errors or []


@dataclass
class AppRecord:
    appid: int
    listing_name: str | None
    top_listing_rank: int | None
    history_outcome: str  # ok / not_found / missing / parse_error
    history: MonthlyHistory | None = None
    score: Score | None = None


@dataclass
class BuildResult:
    snapshot_id: str
    build_id: str
    tables: dict[str, tuple[FileSchema, list[dict[str, Any]]]] = field(default_factory=dict)  # path -> rows
    texts: dict[str, str] = field(default_factory=dict)  # path -> text file content
    build_json: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def add(self, path: str, schema: FileSchema, rows: list[dict[str, Any]]) -> None:
        self.tables[path] = (schema, rows)

    def rows(self, path: str) -> list[dict[str, Any]]:
        return self.tables[path][1]


def build(
    snapshot: SnapshotLike, config: Config, build_id: str, *, allow_parse_errors: bool = False
) -> BuildResult:
    meta = snapshot.meta
    window = Window(meta["observation_window"]["first"], meta["observation_window"]["last"])
    result = BuildResult(snapshot_id=str(meta["id"]), build_id=build_id)
    parse_errors: list[dict[str, Any]] = []

    listing = read_listing(snapshot)
    for key, error in listing.parse_errors:
        parse_errors.append({"appid": None, "source": "top_page", "request_key": key, "error": error})

    apps = _read_histories(snapshot, listing, window, parse_errors)

    if parse_errors and not allow_parse_errors:
        raise BuildFailed(f"{len(parse_errors)} parse error(s); see parse_errors.csv", parse_errors)

    result.add("reports/parse_errors.csv", S.PARSE_ERRORS, parse_errors)
    result.add("reports/placeholder_rows.csv", S.PLACEHOLDER_ROWS, _placeholder_rows(apps))
    result.add("reports/completeness.csv", S.COMPLETENESS, _completeness(snapshot, listing, apps, window))
    result.build_json = _build_json(snapshot, config, build_id, allow_parse_errors, len(parse_errors))
    return result


# ----------------------------------------------------------------------------- histories and scores


def _read_histories(
    snapshot: SnapshotLike, listing: Listing, window: Window, parse_errors: list[dict[str, Any]]
) -> dict[int, AppRecord]:
    extra = {int(a) for a in snapshot.meta.get("extra_appids", [])}
    apps: dict[int, AppRecord] = {}
    for appid in sorted(set(listing.best_rank) | extra):
        record = AppRecord(appid, listing.names.get(appid), listing.best_rank.get(appid), "missing")
        apps[appid] = record
        key = f"steamcharts/app/{appid}.html.gz"
        resp = snapshot.response(key)
        if resp is None:
            continue
        if resp.outcome == "not_found":
            record.history_outcome = "not_found"
            continue
        if resp.outcome == "parse_failure":
            record.history_outcome = "parse_error"
            parse_errors.append({"appid": appid, "source": "steamcharts_app", "request_key": key,
                                 "error": "page structure not readable"})
            continue
        if resp.outcome != "ok":
            continue
        try:
            history = parse_steamcharts_app(resp.body or b"")
        except ParseError as exc:
            record.history_outcome = "parse_error"
            parse_errors.append({"appid": appid, "source": "steamcharts_app", "request_key": key, "error": str(exc)})
            continue
        if history.errors:
            record.history_outcome = "parse_error"
            for error in history.errors:
                parse_errors.append({"appid": appid, "source": "steamcharts_app", "request_key": key, "error": error})
            continue
        record.history_outcome = "ok"
        record.history = history
        record.score = score(history, window)
    return apps


def _placeholder_rows(apps: dict[int, AppRecord]) -> list[dict[str, Any]]:
    rows = []
    for appid, record in apps.items():
        if record.history is None:
            continue
        for month, position in placeholder_rows(record.history):
            rows.append({"appid": appid, "month": month, "position": position})
    return rows


def _completeness(
    snapshot: SnapshotLike, listing: Listing, apps: dict[int, AppRecord], window: Window
) -> list[dict[str, Any]]:
    def row(section: str, item: str, value: int, note: str, dataset: str = "") -> dict[str, Any]:
        return {"section": section, "item": item, "dataset": dataset, "value": value, "note": note}

    rows = [row("listing", "listing_rows", listing.listing_rows, "rows read across every listing pass")]
    for n in sorted(listing.rows_per_pass):
        rows.append(row("listing", f"pass_{n}_rows", listing.rows_per_pass[n], "rows read in this pass"))
        rows.append(row("listing", f"pass_{n}_appids", len(listing.appids_per_pass[n]), "distinct AppIDs in this pass"))
    if len(listing.appids_per_pass) > 1:
        sets = list(listing.appids_per_pass.values())
        union = set().union(*sets)
        once = sum(1 for a in union if sum(a in s for s in sets) == 1)
        rows.append(row("listing", "one_pass_only_appids", once, "AppIDs seen in only one pass"))
    rows.append(row("listing", "listing_appids", len(listing.best_rank), "distinct AppIDs across passes"))
    extra = len(snapshot.meta.get("extra_appids", []))
    if extra:
        rows.append(row("listing", "extra_appids", extra, "test-mode edge-case AppIDs added to the pool"))
    rows.append(row("listing", "candidate_pool", len(apps), "Candidate Pool size (reported, not enforced)"))

    scored = [a for a in apps.values() if a.score is not None]
    rows.append(row("scoring", "scored_apps", len(scored), f"apps with a value in the window {window.first}..{window.last}"))
    unscored: dict[str, int] = {"no_month_rows": 0, "only_placeholder_rows": 0, "no_month_in_window": 0}
    for a in apps.values():
        if a.score is None and a.history_outcome == "ok":
            unscored[unscored_reason(a.history, window)] += 1
    notes = {
        "no_month_rows": "unscored: the Steam Charts page has no month rows",
        "only_placeholder_rows": "unscored: only Placeholder Rows",
        "no_month_in_window": "unscored: month rows, but none in the Observation Window",
    }
    for reason, count in unscored.items():
        rows.append(row("scoring", f"unscored_{reason}", count, notes[reason]))
    for outcome, note in (("not_found", "unscored: Steam Charts app page returned 404"),
                          ("missing", "unscored: app page never fetched (incomplete Snapshot)"),
                          ("parse_error", "unscored: parse error (only with --allow-parse-errors)")):
        rows.append(row("scoring", f"unscored_{outcome}", sum(a.history_outcome == outcome for a in apps.values()), note))
    n_placeholders = sum(len(placeholder_rows(a.history)) for a in apps.values() if a.history is not None)
    rows.append(row("scoring", "placeholder_rows", n_placeholders, "Placeholder Rows in the pool (placeholder_rows.csv)"))
    return rows


# ----------------------------------------------------------------------------- build.json


def software_versions() -> dict[str, str]:
    versions = {"python": platform.python_version(), "steamstudy": __version__}
    for pkg in ("networkx", "leidenalg", "igraph", "python-igraph", "numpy", "scipy", "scikit-learn", "pandas",
                "lxml", "dash", "dash-cytoscape", "dash-ag-grid"):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    return versions


def _build_json(
    snapshot: SnapshotLike, config: Config, build_id: str, allow_parse_errors: bool, n_parse_errors: int
) -> dict[str, Any]:
    meta = snapshot.meta
    n = config.network
    return {
        "snapshot_id": meta["id"],
        "build_id": build_id,
        "mode": meta.get("mode", ""),
        "parse_errors_allowed": allow_parse_errors,
        "parse_error_count": n_parse_errors,
        "collection_date": meta.get("collection_date"),
        "observation_window": meta.get("observation_window"),
        "collection_config_hash": meta.get("collection_config_hash"),
        "taglist_version_hash": meta.get("taglist_version_hash"),
        "store_country": meta.get("store_country"),
        "build_config_hash": config.build_config_hash,
        "config": {name: config.files[name] for name in sorted(config.files) if name != "collection"},
        "changelog": config.changelog_entries(),
        "source_substitutions": SOURCE_SUBSTITUTIONS,
        "attribution": ATTRIBUTION,
        "network_defaults": {
            "min_games_per_tag": n.min_games_per_tag,
            "min_shared_games": n.min_shared_games,
            "min_months": n.min_months,
            "clustering_weight": n.clustering_weight,
            "algorithm": n.algorithm,
            "resolution": n.resolution,
            "seed": n.seed,
            "null_replicates": n.null_replicates,
            "noise_seeds": n.noise_seeds,
            "resolution_sweep": list(n.resolution_sweep),
        },
        "software_versions": software_versions(),
        "manual_metadata_entries": [],
        "monthly_players_publishable": False,
    }


def new_build_id(config: Config, now: dt.datetime | None = None) -> str:
    """UTC timestamp + the first 8 characters of `build_config_hash`."""
    now = now or dt.datetime.now(dt.UTC)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{config.build_config_hash[:8]}"
