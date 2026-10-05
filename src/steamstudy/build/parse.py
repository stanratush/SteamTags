"""Pure parsers: one stored response in, one typed record out. No I/O.

A parser raises `ParseError` when the page does not have the expected structure. Row-level problems
in a Steam Charts history (unknown labels, duplicate months) are returned as `errors` on the record,
so the Build can report every one of them.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field

from lxml import html as lxml_html

MONTHS = {
    name: i + 1
    for i, name in enumerate(
        ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
         "November", "December"]
    )
}
_MONTH_LABEL = re.compile(r"^([A-Z][a-z]+) (\d{4})$")
LAST_30_DAYS = "Last 30 Days"


class ParseError(ValueError):
    """The response does not have the structure the parser expects."""


# ----------------------------------------------------------------------------- Steam Charts


@dataclass(frozen=True)
class TopRow:
    rank: int
    appid: int
    name: str


def parse_top_page(body: bytes) -> list[TopRow]:
    """Rows of one `/top/p.N` listing page; an empty list for an empty page."""
    doc = _doc(body)
    tables = doc.xpath('//table[@id="top-games"]')
    if not tables:
        raise ParseError("no top-games table")
    rows: list[TopRow] = []
    for tr in tables[0].xpath("./tbody/tr"):
        cells = tr.xpath("./td")
        links = tr.xpath('.//td[contains(@class, "game-name")]//a/@href')
        if not cells or not links:
            raise ParseError("listing row without rank or app link")
        rank_text = cells[0].text_content().strip().rstrip(".")
        m = re.fullmatch(r"/app/(\d+)", links[0].strip())
        if not rank_text.isdigit() or not m:
            raise ParseError(f"unreadable listing row: rank {rank_text!r}, link {links[0]!r}")
        name = " ".join(tr.xpath('.//td[contains(@class, "game-name")]')[0].text_content().split())
        rows.append(TopRow(int(rank_text), int(m.group(1)), name))
    return rows


@dataclass(frozen=True)
class MonthRow:
    month: str  # YYYY-MM
    avg: float
    peak: int

    @property
    def is_placeholder(self) -> bool:
        return self.avg == 0.0 and self.peak == 0


@dataclass(frozen=True)
class MonthlyHistory:
    name: str
    rows: tuple[MonthRow, ...]  # chronological, oldest first
    errors: tuple[str, ...] = field(default=())


def parse_steamcharts_app(body: bytes, last_month: str | None = None) -> MonthlyHistory:
    """The monthly rows, oldest first. With `last_month` (YYYY-MM), rows for later months are ignored
    entirely: they are neither data nor parse errors."""
    doc = _doc(body)
    titles = doc.xpath('//h1[@id="app-title"]')
    if not titles:
        raise ParseError("no app-title")
    name = " ".join(titles[0].text_content().split())
    tables = doc.xpath('//table[contains(concat(" ", normalize-space(@class), " "), " common-table ")]')
    if not tables:
        raise ParseError("no monthly table")
    seen: dict[str, MonthRow] = {}
    errors: list[str] = []
    for tr in tables[0].xpath("./tbody/tr"):
        cells = [" ".join(td.text_content().split()) for td in tr.xpath("./td")]
        if len(cells) < 5:
            errors.append(f"row with {len(cells)} cells: {cells!r}")
            continue
        label = cells[0]
        if label == LAST_30_DAYS:
            continue
        m = _MONTH_LABEL.match(label)
        if not m or m.group(1) not in MONTHS:
            errors.append(f"unknown row label {label!r}")
            continue
        month = f"{int(m.group(2)):04d}-{MONTHS[m.group(1)]:02d}"
        if last_month is not None and month > last_month:
            continue
        try:
            row = MonthRow(month, float(cells[1].replace(",", "")), int(cells[4].replace(",", "")))
        except ValueError:
            errors.append(f"unreadable values in {label!r}: avg {cells[1]!r}, peak {cells[4]!r}")
            continue
        if month in seen:
            errors.append(f"duplicate month {label!r}")
            continue
        seen[month] = row
    rows = tuple(sorted(seen.values(), key=lambda r: r.month))
    return MonthlyHistory(name, rows, tuple(errors))


# ----------------------------------------------------------------------------- Steam store


@dataclass(frozen=True)
class StoreTag:
    tag_id: int
    name: str
    votes: int
    position: int  # 1-based display order


@dataclass(frozen=True)
class StorePage:
    tags: tuple[StoreTag, ...]
    adult_only: bool
    country: str | None


_TAG_MODAL = re.compile(r"InitAppTagModal\(\s*\d+\s*,\s*")
_COUNTRY = re.compile(r'"COUNTRY":"([A-Z]{2})"')
ADULT_ONLY_NOTICE = "marked as 'Adult Only'"


def parse_store_page(body: bytes) -> StorePage:
    text = body.decode("utf-8", errors="replace")
    if 'id="application_config"' not in text:
        raise ParseError("no application_config: not a store app page")
    tags: list[StoreTag] = []
    m = _TAG_MODAL.search(text)
    if m:
        try:
            items, _ = json.JSONDecoder().raw_decode(text, m.end())
        except ValueError as exc:
            raise ParseError(f"unreadable InitAppTagModal array: {exc}") from exc
        if not isinstance(items, list):
            raise ParseError("InitAppTagModal argument is not a list")
        for i, item in enumerate(items, start=1):
            try:
                tags.append(StoreTag(int(item["tagid"]), str(item["name"]), int(item.get("count", 0)), i))
            except (KeyError, TypeError, ValueError) as exc:
                raise ParseError(f"unreadable tag entry {item!r}") from exc
    country_match = _COUNTRY.search(html.unescape(text[: text.find('id="application_config"') + 4000]))
    return StorePage(
        tags=tuple(tags),
        adult_only=ADULT_ONLY_NOTICE in text.replace("&#39;", "'"),
        country=country_match.group(1) if country_match else None,
    )


@dataclass(frozen=True)
class Genre:
    genre_id: int
    name: str


@dataclass(frozen=True)
class AppDetails:
    app_type: str
    name: str
    is_free: bool
    genres: tuple[Genre, ...]
    release_date: str
    coming_soon: bool
    content_descriptor_ids: tuple[int, ...]


def parse_appdetails(body: bytes, appid: int) -> AppDetails | None:
    """The app's details, or None when `appdetails` returned `success: false`."""
    try:
        data = json.loads(body)
        entry = data[str(appid)]
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError(f"no appdetails entry for {appid}") from exc
    if not entry.get("success"):
        return None
    d = entry.get("data")
    if not isinstance(d, dict):
        raise ParseError("appdetails success without data")
    try:
        genres = tuple(Genre(int(g["id"]), str(g["description"])) for g in d.get("genres", []) or [])
        release = d.get("release_date") or {}
        descriptors = (d.get("content_descriptors") or {}).get("ids") or []
        return AppDetails(
            app_type=str(d["type"]),
            name=str(d["name"]),
            is_free=bool(d.get("is_free", False)),
            genres=genres,
            release_date=str(release.get("date", "")),
            coming_soon=bool(release.get("coming_soon", False)),
            content_descriptor_ids=tuple(int(i) for i in descriptors),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ParseError(f"unreadable appdetails: {exc}") from exc


@dataclass(frozen=True)
class TagVocabulary:
    version_hash: str
    tags: dict[int, str]


def parse_tag_list(body: bytes) -> TagVocabulary:
    try:
        response = json.loads(body)["response"]
        tags = {int(t["tagid"]): str(t["name"]) for t in response["tags"]}
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError(f"unreadable GetTagList: {exc}") from exc
    return TagVocabulary(str(response.get("version_hash", "")), tags)


def _doc(body: bytes):
    try:
        return lxml_html.fromstring(body)
    except (ValueError, lxml_html.etree.ParserError) as exc:
        raise ParseError(f"not HTML: {exc}") from exc


# ----------------------------------------------------------------------------- SteamDB (cross-check only)

_STEAMDB_TAG = re.compile(r"^/tag/(\d+)/?$")


def parse_steamdb_app(body: bytes) -> list[tuple[int, str]]:
    """Tags on a SteamDB app page as (tag id, name), in page order.

    Assumption (unverified, since SteamDB pages were never fetched without permission): the page links each
    tag as `<a href="/tag/<id>/">name</a>`. Replace the synthetic fixture with a page saved by hand once
    permission is granted, and adjust this parser to it.
    """
    doc = _doc(body)
    seen: dict[int, str] = {}
    for a in doc.xpath("//a[@href]"):
        m = _STEAMDB_TAG.match(a.get("href", "").split("?")[0])
        if m and int(m.group(1)) not in seen:
            seen[int(m.group(1))] = " ".join(a.text_content().split())
    if not seen:
        raise ParseError("no tag links found on the SteamDB page")
    return list(seen.items())
