"""Lightweight Snapshots: the parsed tables a Build reads, in one `snapshots/<snapshot_id>.light.zip`.

A Snapshot has two forms with one `snapshot_id`: **raw** (the folder of pages, request log and `snapshot.json`) and
**lightweight** (this zip). The lightweight form is made from a closed raw Snapshot by reading it through
`RawSource`, so `LightSource` gives the Build the same records and the Build is byte-identical apart from
`build.json`'s `snapshot_form`. It is never changed: repair, collect and SteamDB fetches act on the raw form, and
lightening again replaces the zip.

Staleness: `EXTRACT_VERSION` is bumped whenever a parser or the extracted field set changes. A zip of another
version is read only through the raw form (with a warning), and refused when the raw form is absent. The zip
records the raw form's repair count and SteamDB batch count; behind the raw form, it is stale and not used.
"""

from __future__ import annotations

import csv
import hashlib
import re
import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.builds import LIGHT_SUFFIX, light_path  # noqa: F401  (light_path re-exported)
from steamstudy.build.parse import (
    AppDetails,
    Genre,
    MonthlyHistory,
    MonthRow,
    StorePage,
    StoreTag,
    TagVocabulary,
    TopRow,
)
from steamstudy.build.pool import listing_from_pages
from steamstudy.build.source import (
    EXTRACT_VERSION,
    MISSING,
    BuildSource,
    ChartsRead,
    ListingPage,
    RawSource,
    SkippedEntry,
    SteamdbRead,
    StoreRead,
)

FORMAT_VERSION = 1
# EXTRACT_VERSION (re-exported from steamstudy.build.source): bump whenever a parser or the extracted field set changes.
SUFFIX = LIGHT_SUFFIX
# The `snapshot.json` keys a Build reads.
SNAPSHOT_KEYS = ("id", "mode", "observation_window", "collection_date", "collection_config_hash",
                 "taglist_version_hash", "store_country", "extra_appids")
_ZIP_TIME = (1980, 1, 1, 0, 0, 0)

# Table -> columns, in member order. Optional cells are JSON (`null` for none); booleans are 1 / 0.
TABLES: dict[str, tuple[str, ...]] = {
    "listing_pages.csv": ("key", "pass", "outcome", "error"),
    "listing_rows.csv": ("key", "rank", "appid", "name"),
    "charts.csv": ("appid", "outcome", "history_name", "url", "detail", "status", "timestamp"),
    "charts_errors.csv": ("appid", "error"),
    "months.csv": ("appid", "month", "avg", "peak"),
    "store_apps.csv": ("appid", "page_outcome", "page_present", "adult_only", "country", "page_error",
                       "details_outcome", "details_present", "app_type", "name", "is_free", "release_date",
                       "coming_soon", "descriptor_ids", "details_error"),
    "store_tags.csv": ("appid", "position", "tag_id", "name", "votes"),
    "store_genres.csv": ("appid", "genre_id", "name"),
    "vocabulary.csv": ("tag_id", "name"),
    "steamdb.csv": ("appid", "outcome", "batch", "tags_present", "error"),
    "steamdb_tags.csv": ("appid", "tag_id", "name"),
}


class LightweightError(Exception):
    """A Lightweight Snapshot cannot be made or used (not closed, tampered, stale with no raw form, ...)."""


def raw_counts(meta: dict[str, Any]) -> dict[str, int]:
    """The raw form's change counters: a lightweight form made before a later repair or SteamDB batch is stale."""
    return {"repairs": len(meta.get("repairs", [])), "steamdb_batches": len(meta.get("steamdb", {}).get("batches", []))}


# ----------------------------------------------------------------------------- cells


def _optional_cell(value: Any) -> str:
    """An optional value as a JSON cell (`null` for none), so None and "" stay apart."""
    return json.dumps(value, ensure_ascii=False)


def _from_optional_cell(cell: str) -> Any:
    return json.loads(cell)


def _bool(value: bool) -> str:
    return "1" if value else "0"


# ----------------------------------------------------------------------------- extract (raw -> tables)


def extract(raw: RawSource) -> tuple[dict[str, list[list[str]]], dict[str, Any]]:
    """Every record a Build can read from the raw form, as tables, plus the Snapshot keys and counts."""
    t: dict[str, list[list[str]]] = {name: [] for name in TABLES}
    pages = raw.listing_pages()
    for page in pages:
        t["listing_pages.csv"].append([page.key, str(page.pass_n), page.outcome, _optional_cell(page.error)])
        t["listing_rows.csv"] += [[page.key, str(r.rank), str(r.appid), r.name] for r in page.rows]
    listing = listing_from_pages(pages)
    extra = {int(a) for a in raw.meta.get("extra_appids", [])}
    chart_ids = sorted(set(listing.best_rank) | extra | raw.logged_appids("steamcharts/app/"))
    skipped = {e.appid: e for e in raw.skipped()}
    for appid in chart_ids:
        read = raw.charts(appid)
        if read.outcome == MISSING:
            continue
        s = skipped.get(appid)
        t["charts.csv"].append([str(appid), read.outcome, _optional_cell(read.history.name if read.history else None),
                                s.url if s else "", s.detail if s else "", _optional_cell(s.status if s else None),
                                s.timestamp if s else ""])
        t["charts_errors.csv"] += [[str(appid), e] for e in read.errors]
        if read.history is not None:
            t["months.csv"] += [[str(appid), r.month, repr(r.avg), str(r.peak)] for r in read.history.rows]
    store_ids = sorted(raw.logged_appids("store/page/") | raw.logged_appids("store/appdetails/"))
    for appid in store_ids:
        sr = raw.store(appid)
        p, d = sr.page, sr.details
        t["store_apps.csv"].append([
            str(appid), sr.page_outcome, _bool(p is not None), _bool(p.adult_only if p else False),
            _optional_cell(p.country if p else None), _optional_cell(sr.page_error),
            sr.details_outcome, _bool(d is not None), d.app_type if d else "", d.name if d else "",
            _bool(d.is_free if d else False), d.release_date if d else "", _bool(d.coming_soon if d else False),
            _optional_cell(list(d.content_descriptor_ids) if d else []), _optional_cell(sr.details_error)])
        if p is not None:
            t["store_tags.csv"] += [[str(appid), str(tag.position), str(tag.tag_id), tag.name, str(tag.votes)]
                                    for tag in p.tags]
        if d is not None:
            t["store_genres.csv"] += [[str(appid), str(g.genre_id), g.name] for g in d.genres]
    vocabulary = raw.vocabulary()
    if vocabulary is not None:
        t["vocabulary.csv"] = [[str(i), name] for i, name in vocabulary.tags.items()]
    for appid in sorted(raw.logged_appids("steamdb/app/")):
        db = raw.steamdb(appid)
        if db is None:
            continue
        t["steamdb.csv"].append([str(appid), db.outcome, db.batch, _bool(db.tags is not None), _optional_cell(db.error)])
        t["steamdb_tags.csv"] += [[str(appid), str(i), name] for i, name in (db.tags or ())]
    info = {
        "snapshot": {k: raw.meta[k] for k in SNAPSHOT_KEYS if k in raw.meta},
        "created_at": raw.meta.get("created_at", ""),
        "raw_counts": raw_counts(raw.meta),
        "vocabulary": None if vocabulary is None else {"version_hash": vocabulary.version_hash},
        "has_steamdb": raw.has_steamdb(),
    }
    return t, info


def _csv(columns: tuple[str, ...], rows: list[list[str]]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def write_light(path: Path, tables: dict[str, list[list[str]]], info: dict[str, Any]) -> Path:
    """Write the zip deterministically: fixed member order and timestamps, `meta.json` last with every table's
    sha256."""
    members = {name: _csv(TABLES[name], tables[name]) for name in TABLES}
    meta = {"format_version": FORMAT_VERSION, "extract_version": EXTRACT_VERSION, **info,
            "tables": {name: hashlib.sha256(data).hexdigest() for name, data in members.items()}}
    members["meta.json"] = (json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w") as zf:
        for name, data in members.items():
            zi = zipfile.ZipInfo(name, date_time=_ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 0
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)
    tmp.replace(path)
    return path


def lighten(snapshot_path: Path) -> Path:
    """Make `<snapshot_id>.light.zip` beside a closed raw Snapshot folder (replacing an older one); the raw form is
    only read."""
    from steamstudy.snapshot import Snapshot

    snapshot = Snapshot(snapshot_path)
    if not snapshot.meta.get("closed"):
        raise LightweightError(f"Snapshot {snapshot.id} is not closed: only a closed Snapshot can be lightened")
    tables, info = extract(RawSource(snapshot))
    return write_light(light_path(Path(snapshot_path).parent, snapshot.id), tables, info)


# ----------------------------------------------------------------------------- read (tables -> records)


def read_light_meta(path: Path) -> dict[str, Any]:
    """`meta.json` of a Lightweight Snapshot zip; an unreadable zip raises `LightweightError`."""
    try:
        with zipfile.ZipFile(path) as zf:
            meta: dict[str, Any] = json.loads(zf.read("meta.json"))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        raise LightweightError(f"{Path(path).name} is not a readable Lightweight Snapshot: {exc}") from exc
    return meta


def read_light_vocabulary(path: Path) -> dict[int, str]:
    """The GetTagList vocabulary of a Lightweight Snapshot zip (tag id -> name), without opening its other tables;
    empty when the Snapshot had none."""
    try:
        with zipfile.ZipFile(path) as zf:
            rows = _rows(zf.read("vocabulary.csv"), TABLES["vocabulary.csv"], "vocabulary.csv")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise LightweightError(f"{Path(path).name} is not a readable Lightweight Snapshot: {exc}") from exc
    return {int(i): name for i, name in rows}


def _rows(data: bytes, columns: tuple[str, ...], name: str) -> list[list[str]]:
    rows = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
    if not rows or tuple(rows[0]) != columns:
        raise LightweightError(f"{name}: unexpected columns")
    return rows[1:]


@dataclass
class LightSource:
    """A `BuildSource` over a Lightweight Snapshot zip; every table's sha256 is checked on open."""

    path: Path
    form: str = "lightweight"
    info: dict[str, Any] = field(default_factory=dict)
    _pages: list[ListingPage] = field(default_factory=list)
    _charts: dict[int, ChartsRead] = field(default_factory=dict)
    _skipped: list[SkippedEntry] = field(default_factory=list)
    _store: dict[int, StoreRead] = field(default_factory=dict)
    _vocabulary: TagVocabulary | None = None
    _steamdb: dict[int, SteamdbRead] = field(default_factory=dict)

    @classmethod
    def from_zip(cls, path: Path) -> LightSource:
        try:
            with zipfile.ZipFile(path) as zf:
                info = json.loads(zf.read("meta.json"))
                data = {name: zf.read(name) for name in TABLES}
        except (OSError, KeyError, ValueError, zipfile.BadZipFile) as exc:
            raise LightweightError(f"{path.name} is not a readable Lightweight Snapshot: {exc}") from exc
        if info.get("format_version") != FORMAT_VERSION:
            raise LightweightError(f"{path.name}: format version {info.get('format_version')}, this software reads "
                                   f"{FORMAT_VERSION}")
        for name, content in data.items():
            if hashlib.sha256(content).hexdigest() != info.get("tables", {}).get(name):
                raise LightweightError(f"{path.name}: {name} does not match its recorded sha256 (the file was changed)")
        source = cls(Path(path), info=info)
        source._load({name: _rows(content, TABLES[name], name) for name, content in data.items()})
        return source

    @property
    def meta(self) -> dict[str, Any]:
        return self.info["snapshot"]

    @property
    def extract_version(self) -> int:
        return int(self.info["extract_version"])

    def _load(self, t: dict[str, list[list[str]]]) -> None:
        rows_by_key: dict[str, list[TopRow]] = {}
        for key, rank, appid, name in t["listing_rows.csv"]:
            rows_by_key.setdefault(key, []).append(TopRow(int(rank), int(appid), name))
        self._pages = [ListingPage(key, int(n), outcome, tuple(rows_by_key.get(key, ())), _from_optional_cell(error))
                       for key, n, outcome, error in t["listing_pages.csv"]]
        months: dict[int, list[MonthRow]] = {}
        for appid, month, avg, peak in t["months.csv"]:
            months.setdefault(int(appid), []).append(MonthRow(month, float(avg), int(peak)))
        errors: dict[int, list[str]] = {}
        for appid, error in t["charts_errors.csv"]:
            errors.setdefault(int(appid), []).append(error)
        for appid_s, outcome, history_name, url, detail, status, timestamp in t["charts.csv"]:
            aid = int(appid_s)
            title = _from_optional_cell(history_name)
            history = None if title is None else MonthlyHistory(title, tuple(months.get(aid, ())))
            self._charts[aid] = ChartsRead(outcome, history, tuple(errors.get(aid, ())))
            if outcome == "skipped":
                self._skipped.append(SkippedEntry(aid, url, detail, _from_optional_cell(status), timestamp))
        tags: dict[int, list[StoreTag]] = {}
        for appid, position, tag_id, name, votes in t["store_tags.csv"]:
            tags.setdefault(int(appid), []).append(StoreTag(int(tag_id), name, int(votes), int(position)))
        genres: dict[int, list[Genre]] = {}
        for appid, genre_id, name in t["store_genres.csv"]:
            genres.setdefault(int(appid), []).append(Genre(int(genre_id), name))
        for (appid_s, page_outcome, page_present, adult_only, country, page_error, details_outcome, details_present,
             app_type, name, is_free, release_date, coming_soon, descriptor_ids, details_error) in t["store_apps.csv"]:
            aid = int(appid_s)
            page = StorePage(tuple(tags.get(aid, ())), adult_only == "1", _from_optional_cell(country)) \
                if page_present == "1" else None
            details = AppDetails(app_type, name, is_free == "1", tuple(genres.get(aid, ())), release_date,
                                 coming_soon == "1", tuple(_from_optional_cell(descriptor_ids))) if details_present == "1" else None
            self._store[aid] = StoreRead(page_outcome, details_outcome, page, _from_optional_cell(page_error), details,
                                           _from_optional_cell(details_error))
        vocabulary = self.info.get("vocabulary")
        if vocabulary is not None:
            self._vocabulary = TagVocabulary(vocabulary["version_hash"],
                                             {int(i): name for i, name in t["vocabulary.csv"]})
        db_tags: dict[int, list[tuple[int, str]]] = {}
        for appid, tag_id, name in t["steamdb_tags.csv"]:
            db_tags.setdefault(int(appid), []).append((int(tag_id), name))
        for appid_s, outcome, batch, tags_present, error in t["steamdb.csv"]:
            aid = int(appid_s)
            self._steamdb[aid] = SteamdbRead(outcome, batch, tuple(db_tags.get(aid, ()))
                                               if tags_present == "1" else None, _from_optional_cell(error))

    def listing_pages(self) -> list[ListingPage]:
        return list(self._pages)

    def charts(self, appid: int) -> ChartsRead:
        return self._charts.get(appid, ChartsRead(MISSING))

    def store(self, appid: int) -> StoreRead:
        return self._store.get(appid, StoreRead(MISSING, MISSING))

    def vocabulary(self) -> TagVocabulary | None:
        return self._vocabulary

    def skipped(self) -> list[SkippedEntry]:
        return list(self._skipped)

    def has_steamdb(self) -> bool:
        return bool(self.info.get("has_steamdb"))

    def steamdb(self, appid: int) -> SteamdbRead | None:
        return self._steamdb.get(appid)


# ----------------------------------------------------------------------------- choosing a form


@dataclass
class OpenedSource:
    source: BuildSource
    warnings: list[str] = field(default_factory=list)


def open_build_source(snapshots_root: Path, snapshot_id: str, *, from_raw: bool = False) -> OpenedSource:
    """The form a Build reads: the lightweight one when present, of this software's extract version and not
    behind the raw form; else the raw form. `from_raw` forces the raw pages."""
    from steamstudy.snapshot import Snapshot

    raw_path = Path(snapshots_root) / snapshot_id
    raw = Snapshot(raw_path) if (raw_path / "snapshot.json").is_file() else None
    light = light_path(snapshots_root, snapshot_id)
    if from_raw or not light.is_file():
        if raw is None:
            raise LightweightError(f"Snapshot {snapshot_id} has no raw form under {snapshots_root}"
                                   + ("" if light.is_file() else " and no lightweight form"))
        return OpenedSource(RawSource(raw))
    meta = read_light_meta(light)
    version = meta.get("extract_version")
    if version != EXTRACT_VERSION:
        gap = f"{light.name} has extract version {version}, this software reads {EXTRACT_VERSION}"
        if raw is None:
            raise LightweightError(f"{gap}, and the raw form is absent: the Build cannot read it")
        return OpenedSource(RawSource(raw), [f"{gap}: built from the raw form; run steamstudy snapshot lighten "
                                             f"{snapshot_id} to make it again"])
    if raw is not None and meta.get("raw_counts") != raw_counts(raw.meta):
        return OpenedSource(RawSource(raw), [f"{light.name} is stale (the raw form was repaired or gained SteamDB "
                                             f"pages since): built from the raw form; run steamstudy snapshot lighten "
                                             f"{snapshot_id}"])
    return OpenedSource(LightSource.from_zip(light))


def latest_source_snapshot_id(snapshots_root: Path) -> str | None:
    """The newest Snapshot by `created_at` in either form (a lightweight-only Snapshot counts)."""
    root = Path(snapshots_root)
    if not root.is_dir():
        return None
    best: tuple[str, str] | None = None
    for path in root.iterdir():
        if (path / "snapshot.json").is_file():
            key = (str(json.loads((path / "snapshot.json").read_text(encoding="utf-8")).get("created_at", "")),
                   path.name)
        elif path.name.endswith(SUFFIX) and path.is_file():
            try:
                key = (str(read_light_meta(path).get("created_at", "")), path.name[: -len(SUFFIX)])
            except LightweightError:
                continue  # an unreadable zip names no Snapshot; opening it explains why
        else:
            continue
        if best is None or key > best:
            best = key
    return best[1] if best else None


def verify_light(snapshots_root: Path, snapshot_id: str, config: Any, build_id: str = "20000101T000000Z-verify00",
                 ) -> list[str]:
    """Build from both forms with one `build_id` in a temporary folder and compare every file; returns the
    differences (empty when identical), ignoring `build.json`'s `snapshot_form`. Refuses a lightweight form a Build
    would not read (another extract version, stale). Parse errors are allowed in both Builds, so a Snapshot with
    some still compares."""
    import tempfile

    from steamstudy.build.core import build
    from steamstudy.build.writer import write_build
    from steamstudy.snapshot import Snapshot

    opened = open_build_source(snapshots_root, snapshot_id)
    if not isinstance(opened.source, LightSource):
        reason = opened.warnings[0] if opened.warnings else f"Snapshot {snapshot_id} has no lightweight form"
        raise LightweightError(reason)
    light = opened.source
    raw = RawSource(Snapshot(Path(snapshots_root) / snapshot_id))
    with tempfile.TemporaryDirectory() as tmp:
        folders = [write_build(build(src, config, build_id, allow_parse_errors=True), Path(tmp) / src.form)
                   for src in (raw, light)]
        return compare_build_folders(*folders)


def compare_build_folders(a: Path, b: Path) -> list[str]:
    """Files that differ between two Build folders, ignoring `build.json`'s `snapshot_form`."""
    files = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file()}
    files |= {p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file()}
    diffs = []
    for rel in sorted(files):
        pa, pb = a / rel, b / rel
        if not (pa.is_file() and pb.is_file()):
            diffs.append(f"{rel}: only in one form")
            continue
        da, db = pa.read_bytes(), pb.read_bytes()
        if rel.endswith("build.json"):
            da, db = without_snapshot_form(da), without_snapshot_form(db)
        if da != db:
            diffs.append(f"{rel}: differs" + (" beyond snapshot_form" if rel.endswith("build.json") else ""))
    return diffs


_SNAPSHOT_FORM_LINE = re.compile(rb'^\s*"snapshot_form": "(raw|lightweight)",\r?\n', re.M)


def without_snapshot_form(build_json: bytes) -> bytes:
    """`build.json`'s bytes with its one `snapshot_form` line removed (the only byte the two forms may differ in)."""
    out, n = _SNAPSHOT_FORM_LINE.subn(b"", build_json, count=1)
    if n != 1:
        raise ValueError("build.json has no snapshot_form line")
    return out
