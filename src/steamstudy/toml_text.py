"""TOML text of a settings file, for the draft dialog's editors (the standard library reads TOML but cannot write it;
ADR 0001 adds no dependency).

Covers what `config/*.toml` holds: tables, arrays of tables, scalars, arrays of scalars and arrays of inline tables.
`loads(dumps(x)) == x` for every such value.
"""

from __future__ import annotations

import json
import math
import re
import tomllib
from typing import Any

_BARE = re.compile(r"[A-Za-z0-9_-]+")


def _key(k: str) -> str:
    return k if _BARE.fullmatch(k) else json.dumps(k, ensure_ascii=False)


def _value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        if math.isinf(v):
            return "inf" if v > 0 else "-inf"
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{_key(k)} = {_value(x)}" for k, x in v.items()) + "}"
    raise TypeError(f"cannot write {type(v).__name__} as TOML")


def _is_table_array(v: Any) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(x, dict) for x in v)


def _table(data: dict[str, Any], path: list[str], out: list[str], *, array_item: bool = False) -> None:
    plain = {k: v for k, v in data.items() if not isinstance(v, dict) and not _is_table_array(v)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    arrays = {k: v for k, v in data.items() if _is_table_array(v)}
    if path and (plain or array_item or not (tables or arrays)):
        if out:
            out.append("")
        name = ".".join(_key(p) for p in path)
        out.append(f"[[{name}]]" if array_item else f"[{name}]")
    for k, v in plain.items():
        out.append(f"{_key(k)} = {_value(v)}")
    for k, v in tables.items():
        _table(v, [*path, k], out)
    for k, items in arrays.items():
        if array_item:  # a nested array of tables inside an array item: kept inline
            out.append(f"{_key(k)} = {_value(items)}")
            continue
        for item in items:
            nested = {ik: iv for ik, iv in item.items()}
            _table(nested, [*path, k], out, array_item=True)


def dumps(data: dict[str, Any]) -> str:
    out: list[str] = []
    _table(data, [], out)
    return "\n".join(out) + "\n"


def loads(text: str) -> dict[str, Any]:
    return tomllib.loads(text)
