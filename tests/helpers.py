"""Fixture helpers: real pages captured on 2026-10-04, and pages derived from them.

Real pages live in `tests/fixtures/raw/` under the Snapshot raw layout (see `capture.json` there).
Steam Charts returned HTTP 500 for Black Hole Simulator, Bold Blade and Dadish 3D at capture time,
so those three cases are *derived*: the real Scorn page with its monthly table replaced.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

from steamstudy.collect.fetcher import RawResponse
from steamstudy.snapshot import LogEntry, SnapshotStore

FIXTURES = Path(__file__).resolve().parent / "fixtures"
RAW = FIXTURES / "raw"
CAPTURE = json.loads((RAW / "capture.json").read_text(encoding="utf-8"))

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]


def raw(key: str) -> bytes:
    data = (RAW / key).read_bytes()
    return gzip.decompress(data) if key.endswith(".gz") else data


def captured(key: str) -> RawResponse:
    info = CAPTURE[key]
    return RawResponse(info["status"], info["final_url"], raw(key))


# ----------------------------------------------------------------------------- derived pages


def _month_label(month: str) -> str:
    year, m = month.split("-")
    return f"{MONTH_NAMES[int(m) - 1]} {year}"


def steamcharts_page(rows: list[tuple[str, float, int]], *, name: str = "Derived App", last30: bool = True,
                     extra_labels: list[str] = ()) -> bytes:
    """The real Scorn page with its title and monthly rows replaced. rows: (YYYY-MM, avg, peak), any order."""
    base = raw("steamcharts/app/698670.html.gz").decode("utf-8")
    body = []
    if last30:
        body.append('<tr class="odd"><td class="month-cell left italic">Last 30 Days</td>'
                    '<td class="right num-f italic">0.07</td><td class="right num-p gainorloss italic">-</td>'
                    '<td class="right gainorloss italic">-</td><td class="right num italic">1</td></tr>')
    labelled = [(_month_label(m), a, p) for m, a, p in sorted(rows, reverse=True)]
    labelled += [(label, 1.0, 1) for label in extra_labels]
    for label, avg, peak in labelled:
        body.append(f'<tr><td class="month-cell left">\n{label}\n</td><td class="right num-f">{avg:.2f}</td>'
                    f'<td class="right num-p gainorloss">-</td><td class="right gainorloss">-</td>'
                    f'<td class="right num">{peak}</td></tr>')
    page = re.sub(r"(<tbody>).*?(</tbody>)", lambda m: m.group(1) + "\n".join(body) + m.group(2), base, count=1,
                  flags=re.S)
    page = page.replace(">Scorn</a></h1>", f">{name}</a></h1>")
    return page.encode("utf-8")


def top_page(rows: list[tuple[int, int, str]]) -> bytes:
    """The real /top/p.1 page with its rows replaced. rows: (rank, appid, name)."""
    base = raw("steamcharts/top/pass-1/p-0001.html.gz").decode("utf-8")
    body = [
        f'<tr><td>{rank}.</td><td class="game-name left"><a href="/app/{appid}">\n{name}\n</a></td>'
        f'<td class="num">1</td><td class="chart period-col"></td><td class="num period-col">1</td>'
        f'<td class="num period-col">1</td></tr>'
        for rank, appid, name in rows
    ]
    page = re.sub(r"(<table id=\"top-games\".*?<tbody>).*?(</tbody>)",
                  lambda m: m.group(1) + "\n".join(body) + m.group(2), base, count=1, flags=re.S)
    return page.encode("utf-8")


def store_page(appid: int, tags: list[tuple[int, str]], *, adult_only: bool = False, name: str = "Derived") -> bytes:
    """The real Stardew Valley store page with its tag list (and optionally the Adult Only notice) replaced."""
    base = raw("store/page/413150.html.gz").decode("utf-8")
    items = json.dumps([{"tagid": t, "name": n, "count": 100 - i, "browseable": True} for i, (t, n) in enumerate(tags)])
    page = re.sub(r"InitAppTagModal\( 413150,\s*\[.*?\],", f"InitAppTagModal( {appid},\n\t\t\t\t{items},", base,
                  count=1, flags=re.S)
    if adult_only:
        page = page.replace("<body", "<body", 1).replace(
            '<div class="apphub_AppName"',
            "<div class=\"mature_content_notice\">This game is marked as 'Adult Only'. You are seeing this game "
            "because you have agreed to continue to this page.</div><div class=\"apphub_AppName\"", 1)
    return page.encode("utf-8")


def appdetails(appid: int, *, app_type: str = "game", name: str = "Derived", is_free: bool = False,
               genres: list[tuple[int, str]] = ((1, "Action"),), release_date: str = "1 Jan, 2020",
               descriptors: list[int] = (), success: bool = True) -> bytes:
    if not success:
        return json.dumps({str(appid): {"success": False}}).encode("utf-8")
    data = {
        "type": app_type, "name": name, "steam_appid": appid, "is_free": is_free,
        "genres": [{"id": str(i), "description": d} for i, d in genres],
        "release_date": {"coming_soon": False, "date": release_date},
        "content_descriptors": {"ids": list(descriptors), "notes": None},
    }
    return json.dumps({str(appid): {"success": True, "data": data}}).encode("utf-8")


def mini_store_page(appid: int, tags: list[tuple[int, str]], *, adult_only: bool = False) -> bytes:
    """A small synthetic store page with just the structures the parser reads (for large synthetic pools)."""
    items = json.dumps([{"tagid": t, "name": n, "count": 100 - i, "browseable": True} for i, (t, n) in enumerate(tags)])
    notice = ("<div class=\"mature_content_notice\">This game is marked as 'Adult Only'. You are seeing this game "
              "because you have agreed to continue to this page.</div>") if adult_only else ""
    return (f'<html><body><div id="application_config" data-config="{{&quot;COUNTRY&quot;:&quot;BG&quot;}}"></div>'
            f'{notice}<div class="apphub_AppName">App {appid}</div>'
            f'<script>InitAppTagModal( {appid},\n\t\t{items},\n\t\t[], "x" );</script></body></html>').encode("utf-8")


class World:
    """A synthetic Candidate Pool, written as a Snapshot: listing pages, histories and store responses."""

    def __init__(self) -> None:
        self.responses: dict[str, tuple[str, bytes | None]] = {}
        self.listing: list[tuple[int, str]] = []

    def add(self, appid: int, *, avg: float = 100.0, months: int = 12, history: bytes | None = None,
            tags: list[tuple[int, str]] = ((19, "Action"),), app_type: str = "game", is_free: bool = False,
            genres: list[tuple[int, str]] = ((1, "Action"),), release_date: str = "1 Jan, 2024",
            adult_only: bool = False, descriptors: list[int] = (), page: str = "ok", details: str = "ok",
            name: str | None = None, listed: bool = True, page_body: bytes | None = None,
            details_body: bytes | None = None) -> "World":
        name = name or f"Game {appid}"
        if listed:
            self.listing.append((appid, name))
        if history is None:
            rows = [(_month_back("2026-09", i), avg, int(avg) + 1) for i in range(months)]
            history = steamcharts_page(rows, name=name)
        self.responses[f"steamcharts/app/{appid}.html.gz"] = ("ok", history)
        if page != "skip":
            body = page_body if page_body is not None else mini_store_page(appid, list(tags), adult_only=adult_only)
            self.responses[f"store/page/{appid}.html.gz"] = (page, body if page == "ok" else b"")
        if details != "skip":
            body = details_body if details_body is not None else appdetails(
                appid, app_type=app_type, name=name, is_free=is_free, genres=list(genres), release_date=release_date,
                descriptors=list(descriptors), success=details == "ok")
            self.responses[f"store/appdetails/{appid}.json.gz"] = (details, body)
        return self

    def real(self, appid: int, *, history: bytes | None = None) -> "World":
        """A game from the real fixtures (store page, appdetails and, if captured, the Steam Charts page)."""
        key = f"steamcharts/app/{appid}.html.gz"
        hist = history if history is not None else raw(key)
        self.listing.append((appid, f"Real {appid}"))
        self.responses[key] = ("ok", hist)
        self.responses[f"store/page/{appid}.html.gz"] = ("ok", raw(f"store/page/{appid}.html.gz"))
        self.responses[f"store/appdetails/{appid}.json.gz"] = ("ok", raw(f"store/appdetails/{appid}.json.gz"))
        return self

    def snapshot(self, path: Path, **kw) -> Path:
        responses = dict(self.responses)
        for page in range(0, max(1, len(self.listing)), 25):
            chunk = self.listing[page:page + 25]
            rows = [(page + i + 1, appid, name) for i, (appid, name) in enumerate(chunk)]
            responses[f"steamcharts/top/pass-1/p-{page // 25 + 1:04d}.html.gz"] = ("ok", top_page(rows))
        responses["steam_api/GetTagList.json"] = ("ok", raw("steam_api/GetTagList.json"))
        return make_snapshot(path, responses, **kw)


def _month_back(month: str, n: int) -> str:
    year, m = (int(x) for x in month.split("-"))
    index = year * 12 + (m - 1) - n
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


# ----------------------------------------------------------------------------- fixture Snapshot


def make_snapshot(path: Path, responses: dict[str, tuple[str, bytes | None]], *, mode: str = "test",
                  collection_date: str = "2026-10-04", window: tuple[str, str] = ("2021-10", "2026-09"),
                  extra_appids: list[int] = (), meta: dict | None = None) -> Path:
    """A closed Snapshot on disk. responses: request_key -> (outcome, body)."""
    store = SnapshotStore(path)
    for key, (outcome, body) in responses.items():
        sha = store.write_archive(key, body) if body is not None else None
        status = {"ok": 200, "not_found": 404, "end_of_listing": 404}.get(outcome, 200)
        store.log(LogEntry(key, f"https://example.invalid/{key}", status, f"https://example.invalid/{key}",
                           "2026-10-04T00:00:00Z", sha, outcome))
    snapshot_meta = {
        "id": path.name, "mode": mode, "created_at": f"{collection_date}T00:00:00Z",
        "collection_date": collection_date, "observation_window": {"first": window[0], "last": window[1]},
        "collection_config_hash": "0" * 64, "user_agent": "test", "age_check_birth_date": "1996-10-04",
        "store_country": "BG", "taglist_version_hash": "711684454", "extra_appids": list(extra_appids),
        "stages": {}, "pool": {"passes": [], "one_pass_only_appids": 0}, "rates": [], "gate": {},
        "steamdb": {"permission_reference": "", "batches": []}, "repairs": [], "software_versions": {},
        "closed": True,
    }
    snapshot_meta.update(meta or {})
    store.save_meta(snapshot_meta)
    store.close()
    return path
