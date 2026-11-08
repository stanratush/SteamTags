"""Imports: one wide UTF-8 CSV of items with ordered attributes, validated all-or-nothing and stored fixed.

`validate_import` is the one validation (the CLI and the Build menu both call it); it collects every problem in one
pass. `make_import` stores a valid file as `imports/<import_id>/` (the original verbatim, the normalised tables and
`import.json`), or writes `imports/failed/<attempt_id>/errors.csv` beside a copy of the input. An Import is never
changed afterwards. `load_import` reads the normalised tables back (the import adapter and the preview use it).

The file: `id,name,attributes[,score][,numeric fields...]`; `attributes` holds names separated by `;`, in order.
An optional `attributes.csv` (`id,name`) supplies attribute ids; without it attributes are numbered 1..k in
code-point name order. Rank is score descending, ties by file order; without a score, file order.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REQUIRED = ("id", "name", "attributes")
RESERVED = (*REQUIRED, "score")
MIN_ITEMS = 10
MANY_ITEMS = 50_000
MANY_ATTRIBUTES = 5_000
ATTRIBUTES_FILE = "attributes.csv"
ERRORS_COLUMNS = ("file", "row", "column", "code", "value", "message")

# Every code, with its English message. Errors refuse the Import; warnings are kept in import.json.
ERROR_CODES = {
    "not_csv_utf8": "The file is not UTF-8 text: save it as CSV UTF-8.",
    "not_comma_delimited": "The columns are not separated by commas: save it as CSV UTF-8.",
    "bad_csv": "The file is not valid CSV (a quote is not closed, or a stray quote).",
    "empty_file": "The file has no header row.",
    "missing_column": "A required column is missing.",
    "duplicate_column": "A column name appears twice in the header.",
    "unknown_filter_column": "The filter column is not a numeric column of the file.",
    "row_length": "The row has a different number of cells from the header.",
    "bad_id": "The id is not a positive whole number.",
    "duplicate_id": "Another item already has this id.",
    "empty_name": "The name is empty.",
    "empty_attributes": "The item has no attributes.",
    "empty_attribute": "An attribute between two ';' is empty.",
    "repeated_attribute": "The item lists the same attribute twice.",
    "bad_score": "The score is empty or not a finite number.",
    "bad_filter_value": "The filter value is empty or not a finite number.",
    "bad_field_value": "The value is not a finite number (leave the cell empty for none).",
    "attributes_bad_header": "attributes.csv must have exactly the columns id,name.",
    "attributes_bad_id": "The attribute id is not a positive whole number.",
    "attributes_duplicate_id": "Another attribute already has this id.",
    "attributes_duplicate_name": "Another attribute already has this name.",
    "attributes_empty_name": "The attribute name is empty.",
    "attributes_missing": "An attribute used by the items is not in attributes.csv.",
    "too_few_items": "An Import needs at least 10 items.",
}
WARNING_CODES = {
    "case_clash": "Attribute names that differ only by case are different attributes.",
    "duplicate_item_name": "Two items have the same name.",
    "attributes_unused": "A row of attributes.csv is not used by any item; it is dropped.",
    "many_items": "More than 50,000 items: Builds will be slow.",
    "many_attributes": "More than 5,000 distinct attributes: Builds will be slow.",
}

_NUMBER = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?")
_ID = re.compile(r"\+?\d+")


class ImportRefused(Exception):
    """The file was not imported: invalid (`errors`, written under `failed_folder`), or already imported."""

    def __init__(self, message: str, *, errors: list[Problem] | None = None, failed_folder: Path | None = None,
                 existing: str | None = None):
        super().__init__(message)
        self.errors = errors or []
        self.failed_folder = failed_folder
        self.existing = existing


@dataclass(frozen=True)
class Problem:
    file: str
    row: int | None  # spreadsheet row number (the header is row 1)
    column: str
    code: str
    value: str
    message: str

    def as_row(self) -> dict[str, Any]:
        return {"file": self.file, "row": "" if self.row is None else self.row, "column": self.column,
                "code": self.code, "value": self.value, "message": self.message}


@dataclass(frozen=True)
class ImportItem:
    id: int
    name: str
    rank: int
    score: float | None
    filter_value: float | None
    attribute_ids: tuple[int, ...]  # in the item's order


@dataclass
class ImportTables:
    """The normalised contents of an Import, in file order."""

    items: tuple[ImportItem, ...]
    attributes: dict[int, str]  # id -> name, every attribute used
    attribute_ids: str  # "supplied" (attributes.csv) or "numbered"
    score_present: bool
    filter_field: str | None
    extra_fields: tuple[str, ...]
    fields: dict[int, dict[str, float]]  # item id -> extra numeric fields (no entry for an empty cell)
    import_id: str | None = field(default=None, compare=False)

    def ranked(self) -> list[ImportItem]:
        return sorted(self.items, key=lambda i: i.rank)


@dataclass
class Validation:
    errors: list[Problem]
    warnings: list[Problem]
    tables: ImportTables | None  # None when there are errors

    @property
    def ok(self) -> bool:
        return not self.errors


# ----------------------------------------------------------------------------- reading


def _clean(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def _read_csv(path: Path, label: str, errors: list[Problem]) -> list[tuple[int, list[str]]] | None:
    """(Spreadsheet row number, cells) of the non-blank rows of a UTF-8, comma-delimited CSV (BOM stripped), or None after a fatal problem."""
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(Problem(label, None, "", "not_csv_utf8", "", f"{ERROR_CODES['not_csv_utf8']} ({exc.reason} "
                                                                  f"at byte {exc.start})"))
        return None
    text = text.removeprefix("﻿")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    rows: list[list[str]] = []
    try:
        for row in reader:
            rows.append(row)
    except csv.Error as exc:
        errors.append(Problem(label, len(rows) + 1, "", "bad_csv", "", f"{ERROR_CODES['bad_csv']} ({exc})"))
        return None
    # Blank lines carry nothing but keep their place: each row keeps its spreadsheet row number.
    numbered = [(i + 1, r) for i, r in enumerate(rows) if r != []]
    if not numbered:
        errors.append(Problem(label, None, "", "empty_file", "", ERROR_CODES["empty_file"]))
        return None
    line, first = numbered[0]
    if len(first) == 1 and any(sep in first[0] for sep in (";", "\t", "|")):
        errors.append(Problem(label, line, "", "not_comma_delimited", first[0], ERROR_CODES["not_comma_delimited"]))
        return None
    return numbered


def _number(text: str) -> float | None:
    """A finite decimal with '.' as the point, or None."""
    text = text.strip()
    if not _NUMBER.fullmatch(text):
        return None
    value = float(text)
    return value if math.isfinite(value) else None


def _positive_id(text: str) -> int | None:
    text = text.strip()
    if not _ID.fullmatch(text):
        return None
    value = int(text)
    return value if value > 0 else None


# ----------------------------------------------------------------------------- validation


def validate_import(path: Path, *, attributes_file: Path | None = None,
                    filter_field: str | None = None) -> Validation:
    """Every problem of the file (and its attributes.csv), collected in one pass; the tables when valid."""
    path = Path(path)
    label = path.name
    errors: list[Problem] = []
    warnings: list[Problem] = []

    def err(row: int | None, column: str, code: str, value: str = "", detail: str = "", file: str = label) -> None:
        errors.append(Problem(file, row, column, code, value, ERROR_CODES[code] + (f" {detail}" if detail else "")))

    def warn(row: int | None, column: str, code: str, value: str = "", detail: str = "", file: str = label) -> None:
        warnings.append(Problem(file, row, column, code, value,
                                WARNING_CODES[code] + (f" {detail}" if detail else "")))

    rows = _read_csv(path, label, errors)
    if rows is None:
        return Validation(errors, warnings, None)
    header = [h.strip() for h in rows[0][1]]
    for i, h in enumerate(header):
        if h in header[:i]:
            err(1, h, "duplicate_column", h)
    for h in REQUIRED:
        if h not in header:
            err(1, h, "missing_column", h)
    if filter_field is not None and (filter_field not in header or filter_field in RESERVED):
        err(1, filter_field, "unknown_filter_column", filter_field)
    if errors:
        return Validation(errors, warnings, None)

    col = {h: i for i, h in enumerate(header)}
    score_present = "score" in col
    extra = tuple(h for h in header if h not in RESERVED and h != filter_field)
    parsed: list[tuple[int, int, str, list[str], float | None, float | None, dict[str, float]]] = []
    seen_ids: dict[int, int] = {}
    for row, cells in rows[1:]:
        if len(cells) != len(header):
            err(row, "", "row_length", str(len(cells)), f"({len(cells)} cells, header has {len(header)})")
            continue
        raw_id = cells[col["id"]]
        item_id = _positive_id(raw_id)
        if item_id is None:
            err(row, "id", "bad_id", raw_id)
        elif item_id in seen_ids:
            err(row, "id", "duplicate_id", raw_id, f"(first on row {seen_ids[item_id]})")
        else:
            seen_ids[item_id] = row
        name = _clean(cells[col["name"]])
        if not name:
            err(row, "name", "empty_name", cells[col["name"]])
        raw_attrs = cells[col["attributes"]]
        attrs: list[str] = []
        if not raw_attrs.strip():
            err(row, "attributes", "empty_attributes", raw_attrs)
        else:
            parts = [_clean(p) for p in raw_attrs.split(";")]
            if any(not p for p in parts):
                err(row, "attributes", "empty_attribute", raw_attrs)
            repeated = sorted({p for p in parts if p and parts.count(p) > 1})
            if repeated:
                err(row, "attributes", "repeated_attribute", "; ".join(repeated))
            attrs = [p for p in parts if p]
        score = None
        if score_present:
            score = _number(cells[col["score"]])
            if score is None:
                err(row, "score", "bad_score", cells[col["score"]])
        filter_value = None
        if filter_field is not None:
            filter_value = _number(cells[col[filter_field]])
            if filter_value is None:
                err(row, filter_field, "bad_filter_value", cells[col[filter_field]])
        fields: dict[str, float] = {}
        for h in extra:
            text = cells[col[h]]
            if not text.strip():
                continue
            value = _number(text)
            if value is None:
                err(row, h, "bad_field_value", text)
            else:
                fields[h] = value
        parsed.append((row, item_id or 0, name, attrs, score, filter_value, fields))

    if len(rows) - 1 < MIN_ITEMS:
        err(None, "", "too_few_items", str(len(rows) - 1))

    used = sorted({a for p in parsed for a in p[3]})  # code-point order
    used_set = set(used)
    attribute_ids, ids = _attribute_ids(attributes_file, used, used_set, errors, warnings)

    by_folded: dict[str, list[str]] = {}
    for name in used:
        by_folded.setdefault(name.casefold(), []).append(name)
    for names in by_folded.values():
        if len(names) > 1:
            warn(None, "attributes", "case_clash", "; ".join(names))
    names_seen: dict[str, int] = {}
    for row, _id, name, *_ in parsed:
        if name and name in names_seen:
            warn(row, "name", "duplicate_item_name", name, f"(also on row {names_seen[name]})")
        names_seen.setdefault(name, row)
    if len(rows) - 1 > MANY_ITEMS:
        warn(None, "", "many_items", str(len(rows) - 1))
    if len(used) > MANY_ATTRIBUTES:
        warn(None, "attributes", "many_attributes", str(len(used)))

    if errors:
        return Validation(errors, warnings, None)
    order = sorted(range(len(parsed)), key=lambda k: (-(parsed[k][4] or 0.0), k)) if score_present \
        else list(range(len(parsed)))
    rank = {k: r + 1 for r, k in enumerate(order)}
    items = tuple(ImportItem(id=p[1], name=p[2], rank=rank[k], score=p[4], filter_value=p[5],
                             attribute_ids=tuple(ids[a] for a in p[3])) for k, p in enumerate(parsed))
    tables = ImportTables(items=items, attributes={ids[a]: a for a in used}, attribute_ids=attribute_ids,
                          score_present=score_present, filter_field=filter_field, extra_fields=extra,
                          fields={p[1]: p[6] for p in parsed if p[6]})
    tables.attributes = dict(sorted(tables.attributes.items()))
    return Validation(errors, warnings, tables)


def _attribute_ids(attributes_file: Path | None, used: list[str], used_set: set[str], errors: list[Problem],
                   warnings: list[Problem]) -> tuple[str, dict[str, int]]:
    if attributes_file is None:
        return "numbered", {name: i + 1 for i, name in enumerate(used)}  # `used` is in code-point order
    label = Path(attributes_file).name

    def err(row: int | None, column: str, code: str, value: str = "") -> None:
        errors.append(Problem(label, row, column, code, value, ERROR_CODES[code]))

    rows = _read_csv(Path(attributes_file), label, errors)
    if rows is None:
        return "supplied", {}
    if [h.strip() for h in rows[0][1]] != ["id", "name"]:
        err(rows[0][0], "", "attributes_bad_header", ",".join(rows[0][1]))
        return "supplied", {}
    ids: dict[str, int] = {}
    seen_ids: set[int] = set()
    for row, cells in rows[1:]:
        if len(cells) != 2:
            err(row, "", "row_length", str(len(cells)))
            continue
        attr_id = _positive_id(cells[0])
        name = _clean(cells[1])
        if attr_id is None:
            err(row, "id", "attributes_bad_id", cells[0])
        elif attr_id in seen_ids:
            err(row, "id", "attributes_duplicate_id", cells[0])
        if not name:
            err(row, "name", "attributes_empty_name", cells[1])
        elif name in ids:
            err(row, "name", "attributes_duplicate_name", name)
        if attr_id is not None:
            seen_ids.add(attr_id)
            if name and name not in ids:
                ids[name] = attr_id
                if name not in used_set:
                    warnings.append(Problem(label, row, "name", "attributes_unused", name,
                                            WARNING_CODES["attributes_unused"]))
    for name in used:
        if name not in ids:
            err(None, "name", "attributes_missing", name)
    return "supplied", {n: i for n, i in ids.items() if n in used_set}


# ----------------------------------------------------------------------------- storage


def imports_dir(root: Path) -> Path:
    return Path(root) / "imports"


def is_import(root: Path, source_id: str) -> bool:
    """Whether `source_id` names an Import (else a Snapshot)."""
    return (imports_dir(root) / source_id / "import.json").is_file()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _slug(text: str) -> str:
    return re.sub(r"[\W_]+", "-", text.casefold()).strip("-") or "import"


def _stamp(now: dt.datetime | None) -> str:
    return (now or dt.datetime.now(dt.UTC)).strftime("%Y%m%dT%H%M%SZ")


def make_import(root: Path, path: Path, *, attributes_file: Path | None = None, filter_field: str | None = None,
                now: dt.datetime | None = None) -> Path:
    """Validate and store an Import; returns `imports/<import_id>/`. Raises `ImportRefused`."""
    path = Path(path)
    base = imports_dir(root)
    sha = sha256_file(path)
    attrs_sha = sha256_file(attributes_file) if attributes_file else None
    for meta in list_imports(root):
        if meta.get("sha256") == sha and meta.get("attributes_sha256") == attrs_sha:
            raise ImportRefused(f"this file was already imported as {meta['import_id']}", existing=meta["import_id"])
    result = validate_import(path, attributes_file=attributes_file, filter_field=filter_field)
    stem = f"{_stamp(now)}-{_slug(path.stem)}"
    if not result.ok:
        failed = base / "failed" / stem
        failed.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, failed / path.name)
        if attributes_file:
            shutil.copyfile(attributes_file, failed / ATTRIBUTES_FILE)
        _write_rows(failed / "errors.csv", ERRORS_COLUMNS, [e.as_row() for e in result.errors])
        raise ImportRefused(f"{len(result.errors)} problem(s); see {failed / 'errors.csv'}",
                            errors=result.errors, failed_folder=failed)
    assert result.tables is not None
    folder = base / stem
    if folder.exists():
        raise ImportRefused(f"{folder} already exists")
    tmp = base / f".{stem}.partial"
    (tmp / "original").mkdir(parents=True)
    shutil.copyfile(path, tmp / "original" / path.name)
    if attributes_file:
        shutil.copyfile(attributes_file, tmp / "original" / ATTRIBUTES_FILE)
    _write_tables(tmp, result.tables)
    t = result.tables
    meta = {
        "import_id": stem, "source_file": path.name, "sha256": sha, "attributes_sha256": attrs_sha,
        "created_at": (now or dt.datetime.now(dt.UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": len(t.items), "attributes": len(t.attributes), "attribute_ids": t.attribute_ids,
        "longest_attribute_list": max(len(i.attribute_ids) for i in t.items),
        "score_present": t.score_present, "filter_field": t.filter_field, "extra_fields": list(t.extra_fields),
        "warnings": [w.as_row() for w in result.warnings],
    }
    (tmp / "import.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.rename(folder)
    return folder


def list_imports(root: Path) -> list[dict[str, Any]]:
    """`import.json` of every stored Import, oldest first."""
    base = imports_dir(root)
    if not base.is_dir():
        return []
    return [json.loads((p / "import.json").read_text(encoding="utf-8"))
            for p in sorted(base.iterdir()) if (p / "import.json").is_file()]


def _fmt(value: float | None) -> str:
    return "" if value is None else repr(value)


def _write_rows(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_tables(folder: Path, t: ImportTables) -> None:
    _write_rows(folder / "items.csv", ("id", "name", "rank", "score", "filter_value"),
                [{"id": i.id, "name": i.name, "rank": i.rank, "score": _fmt(i.score),
                  "filter_value": _fmt(i.filter_value)} for i in t.items])
    _write_rows(folder / "item_attributes.csv", ("item_id", "position", "attribute_id"),
                [{"item_id": i.id, "position": p + 1, "attribute_id": a}
                 for i in t.items for p, a in enumerate(i.attribute_ids)])
    _write_rows(folder / "attributes.csv", ("id", "name"),
                [{"id": a, "name": n} for a, n in t.attributes.items()])
    _write_rows(folder / "item_fields.csv", ("id", "field", "value"),
                [{"id": i, "field": f, "value": repr(v)} for i, fs in t.fields.items() for f, v in fs.items()])


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_import(folder: Path) -> ImportTables:
    """The normalised tables of a stored Import."""
    folder = Path(folder)
    meta = json.loads((folder / "import.json").read_text(encoding="utf-8"))
    attrs: dict[int, list[int]] = {}
    for r in _read_rows(folder / "item_attributes.csv"):  # written in item order, then position
        attrs.setdefault(int(r["item_id"]), []).append(int(r["attribute_id"]))
    fields: dict[int, dict[str, float]] = {}
    for r in _read_rows(folder / "item_fields.csv"):
        fields.setdefault(int(r["id"]), {})[r["field"]] = float(r["value"])

    def num(text: str) -> float | None:
        return float(text) if text else None

    items = tuple(ImportItem(id=int(r["id"]), name=r["name"], rank=int(r["rank"]), score=num(r["score"]),
                             filter_value=num(r["filter_value"]), attribute_ids=tuple(attrs.get(int(r["id"]), ())))
                  for r in _read_rows(folder / "items.csv"))
    return ImportTables(items=items,
                        attributes={int(r["id"]): r["name"] for r in _read_rows(folder / "attributes.csv")},
                        attribute_ids=meta["attribute_ids"], score_present=meta["score_present"],
                        filter_field=meta["filter_field"], extra_fields=tuple(meta["extra_fields"]),
                        fields=fields, import_id=meta["import_id"])
