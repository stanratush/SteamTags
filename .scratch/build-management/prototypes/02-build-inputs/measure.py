"""Ticket 02: what a Build reads from a Snapshot, how big those fields are, and how long each stage takes.

Usage (from the repo root):
    uv run python .scratch/build-management/prototypes/02-build-inputs/measure.py timing  [snapshot_id]
    uv run python .scratch/build-management/prototypes/02-build-inputs/measure.py extract [snapshot_id]

`timing` runs one Build exactly as `steamstudy build` does (same config, same functions), with timers wrapped
around the stage functions, and writes the Build to a temporary root that is deleted afterwards.
`extract` writes the fields the Build reads as plain CSV tables (and gzipped copies) to `out/<snapshot_id>/`,
and prints their sizes next to the Snapshot's.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from steamstudy import snapshot as SN  # noqa: E402
from steamstudy.analysis import network_stage as NS  # noqa: E402
from steamstudy.analysis import run as AR  # noqa: E402
from steamstudy.build import core as C  # noqa: E402
from steamstudy.network import state as ST  # noqa: E402

DEFAULT_SNAPSHOT = "20261005T062558Z-full"

TIMES: dict[str, float] = defaultdict(float)
CALLS: dict[str, int] = defaultdict(int)


def timed(label: str, module, name: str) -> None:
    original = getattr(module, name)

    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            TIMES[label] += time.perf_counter() - started
            CALLS[label] += 1

    setattr(module, name, wrapper)


# ----------------------------------------------------------------------------- timing


def timing(snapshot_id: str) -> None:
    from steamstudy.build.writer import write_build
    from steamstudy.config import load_config

    # Raw I/O (file read + gunzip) is counted apart from parsing, inside every stage that reads the archive.
    timed("io: read_archive (read + gunzip)", SN, "read_archive")
    timed("io: requests.sqlite latest entries", SN, "latest_entries")
    # Stages, in Build order. Names are looked up in the module that calls them.
    timed("1 pool: read_listing (/top pages)", C, "read_listing")
    timed("2 parse: Steam Charts histories + score", C, "_read_histories")
    timed("3 games: store page + appdetails (read_game)", C, "read_game")
    timed("4 exclusion: evaluate", C, "evaluate")
    timed("4 exclusion: content_flags", C, "content_flags")
    timed("5 datasets: rank_dataset", C, "rank_dataset")
    timed("6 assemble: skipped_app_rows (re-reads listing)", C, "skipped_app_rows")
    timed("7 analysis: feature tables", AR, "_feature_tables")
    timed("8 network: compute_state (total)", NS, "compute_state")
    timed("8 network:   null model (inside compute_state)", ST, "null_model")
    timed("8 network: layout_state", NS, "layout_state")
    timed("8 network: state_tables", NS, "state_tables")
    timed("8 network: removal_sensitivity", NS, "removal_sensitivity")
    timed("8 network: resolution_sweep", NS, "resolution_sweep")
    timed("8 network: network_outputs (total)", AR, "network_outputs")

    config = load_config(ROOT / "config")
    snap = SN.Snapshot(ROOT / "snapshots" / snapshot_id)

    # run_analysis, report_html and reports_html are imported inside build(); patch their home modules.
    from steamstudy.analysis import report as RP
    from steamstudy.build import summary as SU
    timed("7+8 run_analysis (total)", AR, "run_analysis")
    timed("9 reports: report_html", RP, "report_html")
    timed("9 reports: reports_html", SU, "reports_html")

    started = time.perf_counter()
    result = C.build(snap, config, C.new_build_id(config))
    total_build = time.perf_counter() - started

    tmp = Path(tempfile.mkdtemp(prefix="bm02-"))
    try:
        started = time.perf_counter()
        folder = write_build(result, tmp)
        write_seconds = time.perf_counter() - started
        written = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    named_before_analysis = sum(TIMES[k] for k in TIMES if k[0] in "123456")
    out = {
        "snapshot": snapshot_id,
        "build_seconds": round(total_build, 2),
        "write_seconds": round(write_seconds, 2),
        "written_bytes": written,
        "stages": {k: {"seconds": round(v, 2), "calls": CALLS[k]} for k, v in sorted(TIMES.items())},
        "residual_before_analysis_seconds": round(
            total_build - named_before_analysis - TIMES["7+8 run_analysis (total)"]
            - TIMES["9 reports: report_html"] - TIMES["9 reports: reports_html"], 2),
        "dataset_sizes": result.build_json["dataset_sizes"],
        "parse_error_count": result.build_json["parse_error_count"],
    }
    path = HERE / f"timing_{snapshot_id}.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


# ----------------------------------------------------------------------------- extract


def extract(snapshot_id: str) -> None:
    from steamstudy.build.games import read_game, read_vocabulary
    from steamstudy.build.parse import parse_steamcharts_app, parse_top_page
    from steamstudy.build.score import Window, release_month, score

    snap = SN.Snapshot(ROOT / "snapshots" / snapshot_id)
    meta = snap.meta
    window = Window(meta["observation_window"]["first"], meta["observation_window"]["last"])
    out = HERE / "out" / snapshot_id
    out.mkdir(parents=True, exist_ok=True)
    tables: dict[str, tuple[list[str], list[list]]] = {}

    # Listing: every row of every pass (pass counts, best rank, first-seen name).
    listing_rows = []
    for key in snap.keys("steamcharts/top/"):
        resp = snap.response(key)
        n_pass = int(key.split("/")[2].split("-")[1])
        page = int(key.split("/")[3].split("-")[1].split(".")[0])
        if resp is None or resp.outcome != "ok":
            listing_rows.append([n_pass, page, "", "", "", resp.outcome if resp else "missing"])
            continue
        for row in parse_top_page(resp.body or b""):
            listing_rows.append([n_pass, page, row.rank, row.appid, row.name, "ok"])
    tables["listing"] = (["pass", "page", "rank", "appid", "name", "outcome"], listing_rows)
    pool = sorted({r[3] for r in listing_rows if r[3] != ""} | {int(a) for a in meta.get("extra_appids", [])})

    # Steam Charts: outcome per pool app; month rows up to the window's last month (later rows are never read).
    outcomes, months_all, months_min = [], [], []
    scored = []
    for appid in pool:
        key = f"steamcharts/app/{appid}.html.gz"
        entry = snap.entry(key)
        if entry is None:
            outcomes.append([appid, "missing", "", "", "", ""])
            continue
        if entry.outcome == "skipped":
            outcomes.append([appid, "skipped", entry.url, entry.detail, entry.status, entry.timestamp])
            continue
        outcomes.append([appid, entry.outcome, "", "", "", ""])
        if entry.outcome != "ok":
            continue
        history = parse_steamcharts_app(SN.read_archive(snap.path, key) or b"", last_month=window.last)
        data = [r.month for r in history.rows if not r.is_placeholder]
        rel = release_month(history)
        for r in history.rows:
            row = [appid, r.month, repr(r.avg), r.peak]
            months_all.append(row)
            # Minimal: what score, Release Month, monthly_players.csv and placeholder_rows.csv need.
            if r.is_placeholder or r.month in window or r.month == rel or (data and r.month in (data[0], data[-1])):
                months_min.append(row)
        if score(history, window) is not None:
            scored.append(appid)
    tables["steamcharts_outcomes"] = (["appid", "outcome", "url", "detail", "last_status", "timestamp"], outcomes)
    tables["steamcharts_months_all"] = (["appid", "month", "avg_players", "peak_players"], months_all)
    tables["steamcharts_months_min"] = (["appid", "month", "avg_players", "peak_players"], months_min)

    # Store: page + appdetails for every scored app (read_game is called for each of them).
    apps, tags, genres = [], [], []
    for appid in scored:
        g = read_game(snap, appid, "", [])
        apps.append([appid, g.page_outcome, g.details_outcome, g.name if g.details else "", g.app_type,
                     g.is_free, g.release_date, g.adult_only, ";".join(map(str, g.descriptor_ids))])
        tags.extend([appid, t.position, t.tag_id, t.name] for t in g.tags)
        genres.extend([appid, x.genre_id, x.name] for x in g.genres)
    tables["store_apps"] = (["appid", "page_outcome", "details_outcome", "name", "app_type", "is_free",
                             "release_date", "adult_only", "descriptor_ids"], apps)
    tables["store_tags"] = (["appid", "position", "tag_id", "name"], tags)
    tables["store_genres"] = (["appid", "genre_id", "name"], genres)
    vocab = read_vocabulary(snap)
    tables["tag_vocabulary"] = (["tag_id", "name"], sorted([i, n] for i, n in (vocab.tags.items() if vocab else [])))

    sizes = {}
    for name, (header, rows) in tables.items():
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
        data = buf.getvalue().encode("utf-8")
        (out / f"{name}.csv").write_bytes(data)
        gz = gzip.compress(data, compresslevel=9, mtime=0)
        (out / f"{name}.csv.gz").write_bytes(gz)
        sizes[name] = {"rows": len(rows), "csv_bytes": len(data), "csv_gz_bytes": len(gz)}
    meta_keep = {k: meta.get(k) for k in ("id", "mode", "collection_date", "observation_window",
                                          "collection_config_hash", "taglist_version_hash", "store_country",
                                          "extra_appids", "closed")}
    meta_bytes = json.dumps(meta_keep, indent=2).encode("utf-8")
    (out / "snapshot_meta.json").write_bytes(meta_bytes)
    sizes["snapshot_meta.json"] = {"rows": 1, "csv_bytes": len(meta_bytes), "csv_gz_bytes": len(gzip.compress(meta_bytes))}

    snapshot_bytes = {
        "raw/" + p.relative_to(snap.path / "raw").parts[0] + "/" + p.relative_to(snap.path / "raw").parts[1]: 0
        for p in (snap.path / "raw").rglob("*") if p.is_file()}
    for p in (snap.path / "raw").rglob("*"):
        if p.is_file():
            rel = p.relative_to(snap.path / "raw").parts
            snapshot_bytes[f"raw/{rel[0]}/{rel[1]}"] += p.stat().st_size
    snapshot_bytes["requests.sqlite"] = (snap.path / "requests.sqlite").stat().st_size
    snapshot_bytes["snapshot.json"] = (snap.path / "snapshot.json").stat().st_size
    report = {"snapshot": snapshot_id, "pool_apps": len(pool), "scored_apps": len(scored), "tables": sizes,
              "snapshot_files_bytes": snapshot_bytes, "snapshot_total_bytes": sum(snapshot_bytes.values())}
    (HERE / f"sizes_{snapshot_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    command = sys.argv[1]
    snapshot = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SNAPSHOT
    {"timing": timing, "extract": extract}[command](snapshot)
