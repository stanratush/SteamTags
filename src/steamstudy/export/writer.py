"""Validated CSV writers: the only way the package writes a CSV.

Conventions (all app and Build CSVs): UTF-8 with BOM written with an explicit `utf-8-sig` encoding,
comma-delimited, `\\n` line endings, `true`/`false`, n/a as an empty cell, shortest round-trip floats,
`;`-separated lists, no metadata rows. A row with an undeclared column, or missing a declared one,
is an error.
"""

from __future__ import annotations

import csv
import io
import math
import numbers
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from steamstudy.export.schema import FileSchema

CSV_ENCODING = "utf-8-sig"


class SchemaError(ValueError):
    """A row does not match its file's declared columns or types."""


def format_value(column_type: str, value: Any, where: str = "") -> str:
    if value is None:
        return ""
    match column_type:
        case "str":
            if not isinstance(value, str):
                raise SchemaError(f"{where}: expected str, got {type(value).__name__}")
            return value
        case "int":
            if isinstance(value, bool) or not isinstance(value, numbers.Integral):
                raise SchemaError(f"{where}: expected int, got {type(value).__name__}")
            return str(int(value))
        case "float":
            return repr(_finite(value, where))
        case "float6":
            return f"{_finite(value, where):.6f}"
        case "bool":
            if not isinstance(value, bool) and type(value).__name__ != "bool":  # numpy.bool
                raise SchemaError(f"{where}: expected bool, got {type(value).__name__}")
            return "true" if value else "false"
        case "str_list" | "int_list":
            if isinstance(value, str) or not isinstance(value, Iterable):
                raise SchemaError(f"{where}: expected a list, got {type(value).__name__}")
            item_type = "str" if column_type == "str_list" else "int"
            items = [format_value(item_type, v, where) for v in value]
            for item in items:
                if ";" in item:
                    raise SchemaError(f"{where}: list item {item!r} contains ';'")
            return ";".join(items)
    raise SchemaError(f"{where}: unknown column type {column_type!r}")


def _finite(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise SchemaError(f"{where}: expected float, got {type(value).__name__}")
    f = float(value)
    if not math.isfinite(f):
        raise SchemaError(f"{where}: non-finite float {f!r}; use None for n/a")
    return f


def render_rows(schema: FileSchema, rows: Iterable[Mapping[str, Any]]) -> list[list[str]]:
    declared = schema.column_names
    declared_set = set(declared)
    out: list[list[str]] = []
    for i, row in enumerate(rows):
        keys = set(row.keys())
        if extra := keys - declared_set:
            raise SchemaError(f"{schema.name} row {i}: undeclared column(s) {sorted(extra)}")
        if missing := declared_set - keys:
            raise SchemaError(f"{schema.name} row {i}: missing declared column(s) {sorted(missing)}")
        out.append([format_value(c.type, row[c.name], f"{schema.name} row {i} {c.name}") for c in schema.columns])
    return out


def render_csv(schema: FileSchema, rows: Iterable[Mapping[str, Any]]) -> str:
    """The CSV text (without BOM); `csv_bytes` adds the BOM."""
    rendered = render_rows(schema, rows)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(schema.column_names)
    writer.writerows(rendered)
    return buf.getvalue()


def csv_bytes(schema: FileSchema, rows: Iterable[Mapping[str, Any]]) -> bytes:
    return render_csv(schema, rows).encode(CSV_ENCODING)


def write_csv(path: str | Path, schema: FileSchema, rows: Iterable[Mapping[str, Any]]) -> int:
    """Validate and write; returns the number of data rows."""
    rows = list(rows)
    text = render_csv(schema, rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=CSV_ENCODING, newline="") as fh:
        fh.write(text)
    return len(rows)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Raw string rows of a CSV written by `write_csv` (BOM stripped)."""
    with Path(path).open("r", encoding=CSV_ENCODING, newline="") as fh:
        return list(csv.DictReader(fh))


def parse_value(column_type: str, text: str) -> Any:
    """Inverse of `format_value` for reading the package's own CSVs."""
    if text == "":
        return None
    match column_type:
        case "str":
            return text
        case "int":
            return int(text)
        case "float" | "float6":
            return float(text)
        case "bool":
            if text not in ("true", "false"):
                raise SchemaError(f"not a bool: {text!r}")
            return text == "true"
        case "str_list":
            return text.split(";")
        case "int_list":
            return [int(v) for v in text.split(";")]
    raise SchemaError(f"unknown column type {column_type!r}")


def read_typed_csv(path: str | Path, schema: FileSchema) -> list[dict[str, Any]]:
    rows = read_csv(path)
    if rows and tuple(rows[0].keys()) != schema.column_names:
        raise SchemaError(f"{path}: columns {list(rows[0].keys())} do not match {schema.name}")
    return [{c.name: parse_value(c.type, row[c.name]) for c in schema.columns} for row in rows]
