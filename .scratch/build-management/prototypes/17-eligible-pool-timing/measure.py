"""Ticket 17: how long the Eligible Pool and Top-N take to recompute from a lightweight Snapshot.

Usage (from the repo root):
    uv run python .scratch/build-management/prototypes/17-eligible-pool-timing/measure.py extract <out_dir> [snapshot_id]
    uv run python .scratch/build-management/prototypes/17-eligible-pool-timing/measure.py steam   <out_dir> [snapshot_id]
    uv run python .scratch/build-management/prototypes/17-eligible-pool-timing/measure.py import  <out_dir>

`extract` reads the raw Snapshot with the Build's own stage functions (read_listing, _read_histories, read_game),
writes the parsed fields a pool preview needs as a stand-in lightweight Snapshot (`light.zip`, gzipped CSV tables),
and saves a reference of the pools and Top-N lists computed from the raw records. `out_dir` must be outside the
repository: it holds Steam data.

`steam` loads `light.zip` into the Build's in-memory records (Score, Game), checks the pools against the reference,
then times a full preview (validation, Manual Metadata Entries, every Exclusion Rule, Content Flags, five datasets,
the games entering Overall) and the same after single edits, full against incremental.

`import` writes a synthetic Import at the warning limits (50,000 items, 5,000 attributes) and times reading it and
the same preview on it.
"""

from __future__ import annotations

import copy
import csv
import dataclasses
import gzip
import hashlib
import io
import json
import random
import statistics
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from steamstudy import snapshot as SN  # noqa: E402
from steamstudy.build import core as C  # noqa: E402
from steamstudy.build.datasets import TOP_N, RankedDataset, sort_key  # noqa: E402
from steamstudy.build.exclusion import (  # noqa: E402
    content_flags,
    evaluate,
    validate_manual_exclusions,
    validate_overrides,
)
from steamstudy.build.games import Game, apply_manual_entry, validate_manual_entries  # noqa: E402
from steamstudy.build.parse import AppDetails, Genre, MonthlyHistory, MonthRow, StorePage, StoreTag  # noqa: E402
from steamstudy.build.pool import read_listing  # noqa: E402
from steamstudy.build.score import Window, score  # noqa: E402
from steamstudy.config import DatasetDef, TagList, TagRef, load_config  # noqa: E402

DEFAULT_SNAPSHOT = "20261005T062558Z-full"
REPEATS = 7


def median_time(fn, repeats: int = REPEATS) -> tuple[float, object]:
    times, out = [], None
    for _ in range(repeats):
        t = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t)
    return round(statistics.median(times), 4), out


# ----------------------------------------------------------------------------- the preview itself


def in_scope(d: DatasetDef, g: Game | None, depth: int | None) -> bool | None:
    """datasets.in_scope, with Tag Depth: 'has' means within the first `depth` displayed tags (None = all)."""
    if d.defining_tag is None:
        return True
    if g is None or not g.has_data:
        return None
    return any(t.tag_id == d.defining_tag.id and (depth is None or t.position <= depth) for t in g.tags)


def rank(d: DatasetDef, scores, games, excluded, depth, n) -> RankedDataset:
    eligible = sorted((a for a in scores if a not in excluded and in_scope(d, games.get(a), depth)),
                      key=lambda a: sort_key(a, scores[a]))
    top = eligible[:n]
    ties = []
    if len(eligible) > n:
        cutoff = scores[top[-1]].mean_monthly_players
        ties = [a for a in eligible[n:] if scores[a].mean_monthly_players == cutoff]
    return RankedDataset(d, eligible, top, ties)


def preview(base, *, exclusions, datasets, manual_metadata=(), manual_exclusions=(), overrides=(),
            depth=None, n=TOP_N, baseline_overall=None):
    """Everything the Build menu would show for a draft: pool sizes, Top-N lists, entering/leaving Overall."""
    scores, pristine = base["scores"], base["games"]
    entries = validate_manual_entries(manual_metadata)
    manual = validate_manual_exclusions(manual_exclusions)
    over = validate_overrides(overrides)
    games = dict(pristine)
    for appid, entry in entries.items():
        if appid in games:
            games[appid] = copy.copy(games[appid])
            apply_manual_entry(games[appid], entry)
    evaluations = {a: evaluate(games[a], exclusions, manual, over) for a in sorted(games)}
    excluded = {a for a, ev in evaluations.items() if ev.excluded}
    flags = {a: content_flags(games[a], exclusions) for a in games}
    ranked = {d.key: rank(d, scores, games, excluded, depth, n) for d in datasets}
    out = {"evaluations": evaluations, "excluded": excluded, "flags": flags, "ranked": ranked}
    if baseline_overall is not None:
        top = set(ranked[datasets[0].key].top)
        out["entering"] = sorted(top - baseline_overall)
        out["leaving"] = sorted(baseline_overall - top)
    return out


def rerank_only(base, games, excluded, datasets, depth, n):
    return {d.key: rank(d, base["scores"], games, excluded, depth, n) for d in datasets}


def summary(result) -> dict:
    ranked = result["ranked"]
    digest = hashlib.sha256(json.dumps({k: [r.eligible, r.top, r.ties] for k, r in ranked.items()}).encode())
    return {"pool_sizes": {k: len(r.eligible) for k, r in ranked.items()},
            "excluded": len(result["excluded"]), "lists_sha256": digest.hexdigest()}


# ----------------------------------------------------------------------------- extract (raw Snapshot)


def extract(out_dir: Path, snapshot_id: str) -> None:
    config = load_config(ROOT / "config")
    snap = SN.Snapshot(ROOT / "snapshots" / snapshot_id)
    meta = snap.meta
    window = Window(meta["observation_window"]["first"], meta["observation_window"]["last"])
    t = time.perf_counter()
    listing = read_listing(snap)
    errors: list = []
    apps = C._read_histories(snap, listing, window, errors)
    scores = {a: r.score for a, r in apps.items() if r.score is not None}
    games = {a: C.read_game(snap, a, apps[a].listing_name or "", errors) for a in scores}
    raw_seconds = time.perf_counter() - t

    tables = {
        "listing.csv": (["appid", "best_rank", "name"],
                        [[a, listing.best_rank[a], listing.names.get(a, "")] for a in sorted(listing.best_rank)]),
        "steamcharts_outcomes.csv": (["appid", "outcome"], [[a, r.history_outcome] for a, r in sorted(apps.items())]),
        "steamcharts_months.csv": (["appid", "month", "avg_players", "peak_players"],
                                   [[a, m.month, repr(m.avg), m.peak] for a, r in sorted(apps.items())
                                    if r.history for m in r.history.rows]),
        "store_apps.csv": (["appid", "page_outcome", "details_outcome", "name", "app_type", "is_free",
                            "release_date", "adult_only", "descriptor_ids"],
                           [[a, g.page_outcome, g.details_outcome, g.name, g.app_type, int(g.is_free),
                             g.release_date, int(g.adult_only), ";".join(map(str, g.descriptor_ids))]
                            for a, g in sorted(games.items())]),
        "store_tags.csv": (["appid", "position", "tag_id", "name"],
                           [[a, x.position, x.tag_id, x.name] for a, g in sorted(games.items()) for x in g.tags]),
        "store_genres.csv": (["appid", "genre_id", "name"],
                             [[a, x.genre_id, x.name] for a, g in sorted(games.items()) for x in g.genres]),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_dir / "light.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, (header, rows) in tables.items():
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            w.writerow(header)
            w.writerows(rows)
            z.writestr(name, buf.getvalue())
        z.writestr("meta.json", json.dumps({"id": meta["id"], "observation_window": meta["observation_window"]}))

    base = {"scores": scores, "games": games}
    ref = summary(preview(base, exclusions=config.exclusions, datasets=config.datasets,
                          manual_metadata=config.manual_metadata, manual_exclusions=config.manual_exclusions,
                          overrides=config.exclusion_overrides))
    ref["raw_read_seconds"] = round(raw_seconds, 2)
    ref["light_zip_bytes"] = (out_dir / "light.zip").stat().st_size
    (out_dir / "reference.json").write_text(json.dumps(ref, indent=2), encoding="utf-8")
    print(json.dumps(ref, indent=2))


# ----------------------------------------------------------------------------- load the lightweight tables


def _rows(z: zipfile.ZipFile, name: str):
    with z.open(name) as f:
        r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", newline=""))
        next(r)
        yield from r


def load_light(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        meta = json.loads(z.read("meta.json"))
        window = Window(meta["observation_window"]["first"], meta["observation_window"]["last"])
        months: dict[int, list[MonthRow]] = {}
        for a, month, avg, peak in _rows(z, "steamcharts_months.csv"):
            months.setdefault(int(a), []).append(MonthRow(month, float(avg), int(peak)))
        scores = {}
        for a, rows in months.items():
            s = score(MonthlyHistory("", tuple(rows)), window)
            if s is not None:
                scores[a] = s
        tags: dict[int, list[StoreTag]] = {}
        for a, pos, tid, name in _rows(z, "store_tags.csv"):
            tags.setdefault(int(a), []).append(StoreTag(int(tid), name, 0, int(pos)))
        genres: dict[int, list[Genre]] = {}
        for a, gid, name in _rows(z, "store_genres.csv"):
            genres.setdefault(int(a), []).append(Genre(int(gid), name))
        games = {}
        for a, po, do, name, typ, free, rel, adult, desc in _rows(z, "store_apps.csv"):
            a = int(a)
            g = Game(a, name, po, do)
            t, gs, ds = tuple(tags.get(a, ())), tuple(genres.get(a, ())), tuple(int(x) for x in desc.split(";") if x)
            if po == "ok":
                g.page = StorePage(t, adult == "1", None)
                g.tags, g.adult_only = t, adult == "1"
            if do == "ok":
                g.details = AppDetails(typ, name, free == "1", gs, rel, False, ds)
                g.app_type, g.is_free, g.genres, g.release_date, g.descriptor_ids = typ, free == "1", gs, rel, ds
            games[a] = g
    return {"scores": scores, "games": games}


# ----------------------------------------------------------------------------- the edits


def evidence(appid, name, **extra):
    return {"appid": appid, "name": name, "reason": "timing", "added": "2026-11-07",
            "evidence": [{"url": "https://example.invalid", "retrieved": "2026-11-07"}], **extra}


def time_edits(base, config, datasets, exclusions, label: str) -> dict:
    out: dict = {}
    default = dict(exclusions=exclusions, datasets=datasets, manual_metadata=config.get("manual_metadata", ()),
                   manual_exclusions=config.get("manual_exclusions", ()), overrides=config.get("overrides", ()))
    secs, res = median_time(lambda: preview(base, **default))
    baseline = set(res["ranked"][datasets[0].key].top)
    out["full_preview"] = secs
    out["summary"] = summary(res)

    # Stage costs inside one full preview.
    games, scores = base["games"], base["scores"]
    out["stage_evaluate_all_rules"] = median_time(
        lambda: {a: evaluate(games[a], exclusions, {}, {}) for a in sorted(games)})[0]
    out["stage_content_flags"] = median_time(lambda: {a: content_flags(games[a], exclusions) for a in games})[0]
    out["stage_rank_all_datasets"] = median_time(
        lambda: rerank_only(base, games, res["excluded"], datasets, None, TOP_N))[0]

    top_appid = res["ranked"][datasets[0].key].top[0]
    top_name = games[top_appid].name
    # A tag every pool game is likely to carry somewhere: the most common tag at positions 6..20.
    counts: dict[tuple[int, str], int] = {}
    for g in games.values():
        for t in g.tags:
            if 6 <= t.position <= 20:
                counts[(t.tag_id, t.name)] = counts.get((t.tag_id, t.name), 0) + 1
    (common_id, common_name), _ = max(counts.items(), key=lambda kv: kv[1])
    rule_field = "software_tags"
    old = getattr(exclusions, rule_field)
    edited_rule = dataclasses.replace(exclusions, **{rule_field: TagList(old.tags + (TagRef(common_id, common_name),),
                                                                         old.name_only)})
    edits = {
        "rule_tags_add_one_tag": dict(default, exclusions=edited_rule),
        "global_rank_limit_minus_5": dict(default, exclusions=dataclasses.replace(
            edited_rule, global_rank_limit=exclusions.global_rank_limit - 5)),
        "tag_depth_10": dict(default, depth=10),
        "manual_exclusion_one_game": dict(default, manual_exclusions=(evidence(top_appid, top_name),)),
        "override_one_game": dict(default, overrides=(evidence(top_appid, top_name, rule="software_tag"),),
                                  exclusions=edited_rule),
        "list_size_500": dict(default, n=500),
    }
    out["edits_full_recompute"] = {}
    for name, kwargs in edits.items():
        secs, r = median_time(lambda kw=kwargs: preview(base, baseline_overall=baseline, **kw))
        out["edits_full_recompute"][name] = {"seconds": secs, "pool_sizes": summary(r)["pool_sizes"],
                                             "entering_overall": len(r["entering"])}

    # Incremental paths: reuse the evaluations of the unedited draft.
    evals = res["evaluations"]
    inc: dict = {}

    def one_game(appid, manual, over, excl):
        ev = dict(evals)
        ev[appid] = evaluate(games[appid], excl, manual, over)
        excluded = {a for a, e in ev.items() if e.excluded}
        return rerank_only(base, games, excluded, datasets, None, TOP_N)

    inc["manual_exclusion_one_game"] = median_time(
        lambda: one_game(top_appid, validate_manual_exclusions((evidence(top_appid, top_name),)), {}, exclusions))[0]
    inc["list_size_500 (re-slice only)"] = median_time(
        lambda: {k: r.eligible[:500] for k, r in res["ranked"].items()})[0]
    inc["tag_depth_10 (rerank only)"] = median_time(
        lambda: rerank_only(base, games, res["excluded"], datasets, 10, TOP_N))[0]

    # A rule edit re-runs that rule's tag matching only; the other matches are reused.
    from steamstudy.build.exclusion import _tag_rule

    def one_rule():
        hits = {a for a, g in games.items() if g.has_data and _tag_rule("software_tag", g, edited_rule.software_tags,
                                                                        edited_rule)[0]}
        excluded = res["excluded"] | hits
        return rerank_only(base, games, excluded, datasets, None, TOP_N)

    inc["rule_tags_add_one_tag (one rule, then rerank)"] = median_time(one_rule)[0]
    out["edits_incremental"] = inc
    print(label, json.dumps(out, indent=2))
    return out


def steam(out_dir: Path, snapshot_id: str) -> None:
    config = load_config(ROOT / "config")
    ref = json.loads((out_dir / "reference.json").read_text(encoding="utf-8"))
    loads = []
    for _ in range(3):
        t = time.perf_counter()
        base = load_light(out_dir / "light.zip")
        loads.append(time.perf_counter() - t)
    result = time_edits(base, {"manual_metadata": config.manual_metadata,
                               "manual_exclusions": config.manual_exclusions,
                               "overrides": config.exclusion_overrides},
                        config.datasets, config.exclusions, "steam")
    same = {k: result["summary"][k] == ref[k] for k in ("pool_sizes", "excluded", "lists_sha256")}
    report = {"snapshot": snapshot_id, "scored_apps": len(base["scores"]), "light_zip_bytes": ref["light_zip_bytes"],
              "raw_read_seconds": ref["raw_read_seconds"],
              "load_light_seconds": {"runs": [round(x, 2) for x in loads], "median": round(statistics.median(loads), 2)},
              "matches_raw_reference": same, **result}
    (HERE / f"steam_{snapshot_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- synthetic Import


def import_(out_dir: Path) -> None:
    rnd = random.Random(17)
    n_items, n_attr = 50_000, 5_000
    names = [f"attr{i:04d}" for i in range(n_attr)]
    weights = [1 / (i + 1) for i in range(n_attr)]  # Zipf-like: a few common attributes, a long tail
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "items.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "name", "attributes", "score", "year"])
        for i in range(1, n_items + 1):
            k = rnd.randint(5, 30)
            attrs = list(dict.fromkeys(rnd.choices(names, weights, k=k)))
            w.writerow([i, f"item {i}", ";".join(attrs), round(rnd.lognormvariate(5, 2), 3), rnd.randint(1990, 2026)])

    def read():
        from steamstudy.build.score import Score
        scores, games = {}, {}
        with path.open(encoding="utf-8", newline="") as f:
            r = csv.reader(f)
            next(r)
            for row_no, (i, name, attrs, sc, year) in enumerate(r):
                a = int(i)
                tags = tuple(StoreTag(int(x[4:]), x, 0, p)
                             for p, x in enumerate(attrs.split(";"), start=1))
                g = Game(a, name, "ok", "ok", page=StorePage(tags, False, None),
                         details=AppDetails("game", name, False, (), year, False, ()))
                g.tags, g.app_type = tags, "game"
                games[a] = g
                scores[a] = Score(float(sc), 1, year)
        return {"scores": scores, "games": games}

    loads = []
    for _ in range(3):
        t = time.perf_counter()
        base = read()
        loads.append(time.perf_counter() - t)
    # Import-shaped settings: two attribute rules, no Content Flags, Overall plus four defining attributes.
    exclusions = load_config(ROOT / "config").exclusions
    exclusions = dataclasses.replace(
        exclusions, allowed_app_types=("game",), adult_descriptor_ids=(),
        adult_tags=TagList((TagRef(4000, "attr4000"),)), software_tags=TagList((TagRef(40, "attr0040"),)),
        dating_sim_tags=TagList((TagRef(400, "attr0400"),)), content_flags={})
    datasets = (DatasetDef("overall", "Overall", None),
                *(DatasetDef(f"a{i}", f"attr{i:04d}", TagRef(i, f"attr{i:04d}")) for i in (1, 5, 20, 100)))
    result = time_edits(base, {}, datasets, exclusions, "import")
    report = {"items": n_items, "attributes": n_attr, "csv_bytes": path.stat().st_size,
              "mean_attributes_per_item": round(sum(len(g.tags) for g in base["games"].values()) / n_items, 1),
              "read_import_seconds": {"runs": [round(x, 2) for x in loads], "median": round(statistics.median(loads), 2)},
              **result}
    (HERE / "import_synthetic.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cmd, out = sys.argv[1], Path(sys.argv[2])
    snapshot = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_SNAPSHOT
    {"extract": lambda: extract(out, snapshot), "steam": lambda: steam(out, snapshot), "import": lambda: import_(out)}[cmd]()
