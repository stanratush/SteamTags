"""`build(snapshot, config, build_id) -> BuildResult`: one deterministic derivation, never contacting a source.

The only inputs are the read-only Snapshot, in either form (`steamstudy.build.source`), and the config (plus the
`build_id` the caller chose).
`steamstudy.build.writer` lays the result out as a Build folder.
"""

from __future__ import annotations

import copy
import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from steamstudy.analysis.templates import wording
from steamstudy.build import assemble as A
from steamstudy.build.assemble import GameTable
from steamstudy.build.datasets import RankedDataset
from steamstudy.build.exclusion import (
    ExclusionListError,
    configured_tag_ids,
    content_flags,
    evaluate,
    rule_codes,
    validate_manual_exclusions,
    validate_overrides,
)
from steamstudy.build.games import (
    Game,
    ManualMetadataError,
    apply_manual_entry,
    read_game,
    read_vocabulary,
    validate_manual_entries,
)
from steamstudy.build.parse import MonthlyHistory, TagVocabulary
from steamstudy.build.pool import Listing, SnapshotLike, listing_from_pages, skipped_rows
from steamstudy.build.source import EXTRACT_VERSION, MISSING, BuildSource, as_source
from steamstudy.build.score import Score, Window, placeholder_rows, score, unscored_reason
from steamstudy.builds import BuildFailed, build_date  # noqa: F401  (re-exported: the pipeline's names)
from steamstudy.config import Config
from steamstudy.export import schema as S
from steamstudy.export.schema import FileSchema
from steamstudy.versions import software_versions

ATTRIBUTION = "Player data: Steam Charts; tags/metadata: Steam store"
SOURCE_SUBSTITUTIONS = [
    {"source": "Steam store page (displayed tag list, Adult Only notice)", "confirmed": "2026-10-03"},
    {"source": "Steam store appdetails (type, name, is_free, genres, release date, content descriptors)",
     "confirmed": "2026-10-03"},
    {"source": "Steam Web API IStoreService/GetTagList (tag vocabulary)", "confirmed": "2026-10-03"},
]


@dataclass
class AppRecord:
    appid: int
    listing_name: str | None
    top_listing_rank: int | None
    history_outcome: str  # ok / not_found / skipped / missing / parse_error
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
    # In-memory results for later Build stages (network tables, feature analysis); not written.
    ranked: dict[str, RankedDataset] = field(default_factory=dict)
    scores: dict[int, Score] = field(default_factory=dict)
    games: dict[int, Game] = field(default_factory=dict)
    network_states: dict[str, Any] = field(default_factory=dict)
    dataset_rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # the analysis reads these
    analysis_json: dict[str, Any] = field(default_factory=dict)

    def add(self, path: str, schema: FileSchema, rows: list[dict[str, Any]]) -> None:
        self.tables[path] = (schema, rows)

    def rows(self, path: str) -> list[dict[str, Any]]:
        return self.tables[path][1]


@dataclass(frozen=True)
class BuildIdentity:
    """What `build.json` says about a Build beside its settings; in neither `build_id` nor the config hash."""

    name: str | None = None  # None: the build_id
    description: str | None = None  # appended as the Build's own changelog entry
    parent_build_id: str | None = None  # "<source_id>/<build_id>" of the Build it was duplicated from
    changelog: tuple[dict[str, str], ...] | None = None  # inherited entries; None: config/CHANGELOG.md


def build(
    snapshot: SnapshotLike | BuildSource, config: Config, build_id: str, *, allow_parse_errors: bool = False,
    identity: BuildIdentity | None = None,
) -> BuildResult:
    """The Build of a Snapshot: a raw Snapshot view, or a `BuildSource` of either form."""
    source = as_source(snapshot)
    meta = source.meta
    window = Window(meta["observation_window"]["first"], meta["observation_window"]["last"])
    result = BuildResult(snapshot_id=str(meta["id"]), build_id=build_id)
    parse_errors: list[dict[str, Any]] = []

    listing = listing_from_pages(source.listing_pages())
    for key, error in listing.parse_errors:
        parse_errors.append({"appid": None, "source": "top_page", "request_key": key, "error": error})

    apps = _read_histories(source, listing, window, parse_errors)
    scores = {a: r.score for a, r in apps.items() if r.score is not None}
    games = {a: read_game(source, a, apps[a].listing_name or "", parse_errors) for a in scores}

    if parse_errors and not allow_parse_errors:
        raise BuildFailed(f"{len(parse_errors)} parse error(s); see parse_errors.csv", parse_errors)

    vocabulary = read_vocabulary(source)
    result.warnings += _vocabulary_warnings(config, vocabulary)
    games, warnings = apply_manual_metadata(config, games)
    result.warnings += warnings
    manual_exclusions, overrides = steam_lists(config)
    chosen = select_datasets(config, scores, games, manual_exclusions, overrides)
    evaluations, excluded, flags, ranked = chosen.evaluations, chosen.excluded, chosen.flags, chosen.ranked

    depth = config.depth_cut
    for r in ranked.values():
        n = r.definition.list_size
        if len(r.top) < n:
            message = f"dataset {r.key} has only {len(r.eligible)} eligible games; every dataset must hold exactly {n}"
            if meta.get("mode") != "test":
                raise BuildFailed(message)
            result.warnings.append(message + " (allowed only in a test Build)")
    _check_list_names(games, ranked)

    histories = {a: apps[a].history for a in scores if apps[a].history is not None}
    t = GameTable(scores, games, histories, listing.best_rank, ranked, flags, depth)  # type: ignore[arg-type]
    excluded_evals = {a: ev for a, ev in evaluations.items() if ev.excluded}
    for key, r in ranked.items():
        result.add(f"datasets/top100_{key}.csv", S.TOP100, A.top100_rows(t, r))
    result.add("datasets/monthly_players.csv", S.MONTHLY_PLAYERS, A.monthly_players_rows(t, window))
    result.add("reports/parse_errors.csv", S.PARSE_ERRORS, parse_errors)
    result.add("reports/placeholder_rows.csv", S.PLACEHOLDER_ROWS, _placeholder_rows(apps))
    result.add("reports/ties.csv", S.TIES, A.ties_rows(t))
    keys = list(ranked)
    result.add("reports/exclusions.csv", S.EXCLUSIONS.for_datasets(keys), A.exclusion_rows(t, excluded_evals))
    result.add("reports/impact_removals.csv", S.IMPACT_REMOVALS.for_datasets(keys),
               A.impact_removal_rows(t, excluded_evals))
    result.add("reports/impact_near_misses.csv", S.IMPACT_NEAR_MISSES.for_datasets(keys),
               A.near_miss_rows(t, evaluations))
    result.add("reports/impact_adult_signals.csv", S.IMPACT_ADULT_SIGNALS.for_datasets(keys),
               A.adult_signal_rows(t, evaluations))
    result.add("reports/impact_unexcluded.csv", S.IMPACT_UNEXCLUDED, A.unexcluded_rows(t, config.genre_kind))
    result.add("reports/tag_vocabulary.csv", S.TAG_VOCABULARY, A.tag_vocabulary_rows(games, vocabulary))
    result.add("reports/release_month_check.csv", S.RELEASE_MONTH_CHECK,
               A.release_month_check_rows(t, config.analysis.release_month_check))
    result.add("reports/manual_metadata.csv", S.MANUAL_METADATA, A.manual_metadata_rows(games))
    result.add("reports/skipped_apps.csv", S.SKIPPED_APPS, skipped_rows(source.skipped(), listing.names))
    if source.has_steamdb():
        result.add("reports/steamdb_crosscheck.csv", S.STEAMDB_CROSSCHECK,
                   _steamdb_rows(source, games, A.members(t), parse_errors_allowed=allow_parse_errors,
                                 warnings=result.warnings))
    completeness = _completeness(source, listing, apps, window)
    completeness += _exclusion_counts(games, evaluations, config)
    completeness += A.depth_check_rows(t, wording(config)["top_h"])
    result.add("reports/completeness.csv", S.COMPLETENESS, completeness)

    result.build_json = _build_json(source, config, build_id, allow_parse_errors, len(parse_errors),
                                    identity or BuildIdentity())
    result.build_json["manual_metadata_entries"] = [
        {"appid": a, "kind": g.manual_entry["kind"]} for a, g in sorted(games.items()) if g.manual_entry]
    result.build_json["exclusion_overrides_applied"] = [
        {"appid": a, "rule": rule, "reason": overrides[(a, rule)]["reason"]}
        for a, ev in evaluations.items() for rule in ev.overridden]
    result.build_json["dataset_sizes"] = {k: {"rows": len(r.top), "eligible_pool": len(r.eligible)}
                                          for k, r in ranked.items()}
    result.build_json["warnings"] = list(result.warnings)
    result.ranked = ranked
    result.scores = scores
    result.games = games
    result.dataset_rows = {key: result.rows(f"datasets/top100_{key}.csv") for key in ranked}

    from steamstudy.analysis.report import report_html
    from steamstudy.analysis.run import run_analysis
    from steamstudy.analysis.templates import CausalLanguageError
    from steamstudy.build.summary import reports_html

    run_analysis(result, config)
    try:
        result.texts["analysis/report.html"] = report_html(result, config)
        result.texts["reports/reports.html"] = reports_html(result, config)
    except CausalLanguageError as exc:
        raise BuildFailed(str(exc)) from exc
    return result


def _steamdb_rows(source: BuildSource, games: dict[int, Game], members: list[int], *,
                  parse_errors_allowed: bool, warnings: list[str]) -> list[dict[str, Any]]:
    rows = []
    for appid in members:
        read = source.steamdb(appid)
        if read is None or read.outcome != "ok":
            continue
        if read.tags is None:
            warnings.append(f"SteamDB page for appid {appid} not readable: {read.error}")
            continue
        steamdb = read.tags
        store_ids = [t.tag_id for t in games[appid].tags]
        steamdb_ids = [t for t, _ in steamdb]
        rows.append({
            "appid": appid, "name": games[appid].name, "steamdb_batch": read.batch,
            "store_tag_ids": store_ids, "steamdb_tag_ids": steamdb_ids, "steamdb_tags": [n for _, n in steamdb],
            "only_store_tag_ids": [t for t in store_ids if t not in steamdb_ids],
            "only_steamdb_tag_ids": [t for t in steamdb_ids if t not in store_ids],
            "same_tag_set": set(store_ids) == set(steamdb_ids),
        })
    return rows


def apply_manual_metadata(config: Config, games: dict[int, Game]) -> tuple[dict[int, Game], list[str]]:
    """The games with the Manual Metadata Entries applied (an entry's game is copied first, so `games` is left as
    it was: the Eligible Pool preview reuses it), and the warnings for entries not used."""
    out, warnings = dict(games), []
    try:
        entries = validate_manual_entries(config.manual_metadata)
        for appid, entry in sorted(entries.items()):
            if appid not in out:
                warnings.append(f"Manual Metadata Entry for appid {appid} not used: the app has no score")
                continue
            out[appid] = copy.deepcopy(out[appid])
            apply_manual_entry(out[appid], entry)
    except ManualMetadataError as exc:
        raise BuildFailed(str(exc)) from exc
    return out, warnings


def steam_lists(config: Config) -> tuple[dict[int, dict[str, Any]], dict[tuple[int, str], dict[str, Any]]]:
    """A Steam Build's Manual Exclusions and Exclusion Overrides, validated; BuildFailed when they are not."""
    try:
        return (validate_manual_exclusions(config.manual_exclusions),
                validate_overrides(config.exclusion_overrides, config.exclusions))
    except ExclusionListError as exc:
        raise BuildFailed(str(exc)) from exc


@dataclass
class Selection:
    """Which games every rule excludes and each dataset's ranked pool: the Build stage's own step, which the Eligible
    Pool preview calls too (one implementation)."""

    evaluations: dict[int, Any]
    excluded: set[int]
    flags: dict[int, list[str]]
    ranked: dict[str, RankedDataset]


def select_datasets(config: Config, scores: dict[int, Any], games: dict[int, Game], manual: dict[int, Any],
                    overrides: dict[Any, Any], *, key: Any = None,
                    tie_value: Callable[[Any], float | None] | None = None) -> Selection:
    """Evaluate every rule on every game, then rank each dataset's Eligible Pool and cut it at its List Size."""
    from steamstudy.build.datasets import rank_pool, slice_top, sort_key, steam_tie_value

    evaluations = {a: evaluate(games[a], config.exclusions, manual, overrides) for a in sorted(games)}
    excluded = {a for a, ev in evaluations.items() if ev.excluded}
    flags = {a: content_flags(games[a], config.exclusions) for a in games}
    ranked = {d.key: slice_top(rank_pool(d, scores, games, excluded, config.depth_cut, key or sort_key), scores,
                               tie_value=tie_value or steam_tie_value) for d in config.datasets}
    return Selection(evaluations, excluded, flags, ranked)


def _vocabulary_warnings(config: Config, vocabulary: TagVocabulary | None) -> list[str]:
    if vocabulary is None:
        return ["no GetTagList snapshot: configured tag ids could not be checked"]
    named = configured_tag_ids(config.exclusions)
    named += [("genres.genre_tags", t.id, t.name) for t in config.genre_tags]
    named += [(f"datasets.{d.key}.defining_tag", d.defining_tag.id, d.defining_tag.name)
              for d in config.datasets if d.defining_tag]
    return [f"{where}: tag id {tag_id} ({name}) is not in the GetTagList snapshot"
            for where, tag_id, name in named if tag_id not in vocabulary.tags]


def _check_list_names(games: dict[int, Game], ranked: dict[str, RankedDataset]) -> None:
    for appid in sorted({a for r in ranked.values() for a in r.top}):
        g = games[appid]
        for name in [t.name for t in g.tags] + [x.name for x in g.genres]:
            if ";" in name:
                raise BuildFailed(f"appid {appid}: tag or genre name {name!r} contains ';', which the list format cannot hold")


def _exclusion_counts(games: dict[int, Game], evaluations: dict[int, Any], config: Config) -> list[dict[str, Any]]:
    rows = [{"section": "scoring", "item": "scored_game_apps",
             "dataset": "", "value": sum(g.app_type == "game" for g in games.values() if g.has_data),
             "note": "scored apps whose app type is game"}]
    codes = rule_codes(config.exclusions)
    overlapping = {rule: 0 for rule in codes}
    primary = {rule: 0 for rule in codes}
    for ev in evaluations.values():
        for m in ev.matches:
            overlapping[m.rule] += 1
        if ev.primary_reason:
            primary[ev.primary_reason] += 1
    rows += [{"section": "exclusions_overlapping", "item": rule, "dataset": "", "value": n,
              "note": "excluded games matching this rule (a game can match several)"} for rule, n in overlapping.items()]
    rows += [{"section": "exclusions_primary", "item": rule, "dataset": "", "value": n,
              "note": "excluded games whose primary_reason is this rule"} for rule, n in primary.items()]
    rows.append({"section": "exclusions_primary", "item": "excluded_games", "dataset": "",
                 "value": sum(primary.values()), "note": "scored games excluded by any rule"})
    return rows


# ----------------------------------------------------------------------------- histories and scores


def _read_histories(
    source: BuildSource, listing: Listing, window: Window, parse_errors: list[dict[str, Any]]
) -> dict[int, AppRecord]:
    extra = {int(a) for a in source.meta.get("extra_appids", [])}
    apps: dict[int, AppRecord] = {}
    for appid in sorted(set(listing.best_rank) | extra):
        record = AppRecord(appid, listing.names.get(appid), listing.best_rank.get(appid), "missing")
        apps[appid] = record
        key = f"steamcharts/app/{appid}.html.gz"
        read = source.charts(appid)
        if read.outcome == MISSING:
            continue
        if read.outcome in ("not_found", "skipped"):
            record.history_outcome = read.outcome
            continue
        if read.errors:
            record.history_outcome = "parse_error"
            for error in read.errors:
                parse_errors.append({"appid": appid, "source": "steamcharts_app", "request_key": key, "error": error})
            continue
        if read.outcome != "ok" or read.history is None:
            continue
        record.history_outcome = "ok"
        record.history = read.history
        record.score = score(read.history, window)
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
    source: BuildSource, listing: Listing, apps: dict[int, AppRecord], window: Window
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
    extra = len(source.meta.get("extra_appids", []))
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
                          ("skipped", "unscored: Steam Charts page kept failing to load or parse (skipped_apps.csv)"),
                          ("missing", "unscored: app page never fetched (incomplete Snapshot)"),
                          ("parse_error", "unscored: parse error (only with --allow-parse-errors)")):
        rows.append(row("scoring", f"unscored_{outcome}", sum(a.history_outcome == outcome for a in apps.values()), note))
    n_placeholders = sum(len(placeholder_rows(a.history)) for a in apps.values() if a.history is not None)
    rows.append(row("scoring", "placeholder_rows", n_placeholders, "Placeholder Rows in the pool (placeholder_rows.csv)"))
    return rows


# ----------------------------------------------------------------------------- build.json


def _build_json(
    source: BuildSource, config: Config, build_id: str, allow_parse_errors: bool, n_parse_errors: int,
    identity: BuildIdentity,
) -> dict[str, Any]:
    meta = source.meta
    n = config.network
    changelog = list(identity.changelog) if identity.changelog is not None else config.changelog_entries()
    name = identity.name or build_id
    if identity.description:
        changelog.append({"date": build_date(build_id), "title": name, "text": identity.description})
    return {
        "snapshot_id": meta["id"],
        "snapshot_form": source.form,
        "extract_version": EXTRACT_VERSION,  # the parsers and extracted fields this software reads
        "build_id": build_id,
        "name": name,
        "description": identity.description,
        "parent_build_id": identity.parent_build_id,
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
        "changelog": changelog,
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
    }


def new_build_id(config: Config | str, now: dt.datetime | None = None) -> str:
    """UTC timestamp + the first 8 characters of `build_config_hash` (a Config, or the hash itself)."""
    now = now or dt.datetime.now(dt.UTC)
    config_hash = config if isinstance(config, str) else config.build_config_hash
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{config_hash[:8]}"
