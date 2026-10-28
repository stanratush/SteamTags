"""Catalogue parity: every `tx("…")` / `tx.n(…)` literal in the source against the Bulgarian catalogue.

Correctness is strict wherever an entry exists: placeholder names match, a counted message has both forms, no key
is orphaned. Completeness (a missing entry) is checked only for the areas on the done-list (`i18n_done`).
"""

from __future__ import annotations

import ast
import string
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from steamstudy import i18n

SRC = Path(__file__).resolve().parents[1] / "src" / "steamstudy"

# Source file (relative to src/steamstudy) -> the catalogue area its messages belong to.
AREA_OF = {
    "app/layout.py": "layout", "app/renderer.py": "layout",
    "app/callbacks.py": "callbacks",
    "app/view.py": "view",
    "app/ps_view.py": "ps_view",
    "app/ps_run.py": "ps_run",
    "network/selection_text.py": "selection_text",
    "app/export.py": "refusals",
    "app/help.py": "ui_words", "app/guide.py": "ui_words",
}

def _refusals() -> Iterable[str]:
    from steamstudy.app.export import REFUSALS

    return REFUSALS.values()


def _schema_tips() -> Iterable[str]:
    """The schema descriptions the grids show as header tooltips (identifier columns: `view.column_defs`)."""
    from steamstudy.app.layout import GRIDS
    from steamstudy.i18n import text

    en = text("en")
    return sorted({d["headerTooltip"] for grid in GRIDS.values() for d in grid(en)
                   if "headerComponentParams" not in d})


# Text that reaches `tx` as a variable, by area: the declared non-literal sources (schema descriptions shown as
# header tooltips, the OpenRefused reasons). The In short label sets are the guide's (guide.LABELS), not catalogued.
def _inspector_labels() -> Iterable[str]:
    from steamstudy.app.view import INSPECTOR_LABELS

    return INSPECTOR_LABELS


NON_LITERAL: dict[str, Callable[[], Iterable[str]]] = {"refusals": _refusals, "schema_tips": _schema_tips,
                                                       "view": _inspector_labels}


@dataclass(frozen=True)
class Message:
    area: str
    key: str  # the English text; for a counted message, its `one` form
    other: str | None  # a counted message's English `other` form
    where: str


def _str(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _messages(tree: ast.AST, area: str, rel: str) -> Iterable[Message]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        where = f"{rel}:{node.lineno}"
        if isinstance(f, ast.Name) and f.id == "tx" and node.args and _str(node.args[0]) is not None:
            yield Message(area, _str(node.args[0]), None, where)
        elif isinstance(f, ast.Attribute) and f.attr == "n" and isinstance(f.value, ast.Name) and f.value.id == "tx":
            kw = {k.arg: _str(k.value) for k in node.keywords}
            if kw.get("one") is not None and kw.get("other") is not None:
                yield Message(area, kw["one"], kw["other"], where)


def scan(root: Path = SRC) -> list[Message]:
    """Every translatable literal under `root`, in file then line order."""
    found: list[Message] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("i18n/"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits = sorted(_messages(tree, AREA_OF.get(rel, "?"), rel), key=lambda m: int(m.where.rsplit(":", 1)[1]))
        found += hits
    if root == SRC:  # the declared sources belong to the real source tree
        for area, source in NON_LITERAL.items():
            found += [Message(area, key, None, f"declared source {area}") for key in source()]
    return found


def fields(message: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(message) if name}


def problems(found: list[Message], areas: dict[str, dict[str, i18n.Entry]], done: set[str]) -> list[str]:
    """What breaks parity between the English literals and the Bulgarian catalogues."""
    out = []
    merged: dict[str, i18n.Entry] = {}
    for area, messages in areas.items():
        for key, value in messages.items():
            if key in merged and merged[key] != value:
                out.append(f"{key!r}: two different entries (one in {area})")
            merged[key] = value
    for m in found:
        if m.area == "?":
            out.append(f"{m.where}: a file with no catalogue area (add it to AREA_OF)")
            continue
        entry = merged.get(m.key)
        if entry is None:
            if m.area in done:
                out.append(f"{m.where}: {m.key!r} missing from the Bulgarian {m.area} catalogue")
            continue
        if m.other is None:
            if not isinstance(entry, str):
                out.append(f"{m.where}: {m.key!r} is a plain message but its entry has plural forms")
            elif fields(entry) != fields(m.key):
                out.append(f"{m.where}: {m.key!r} placeholder names differ: {sorted(fields(entry))}")
        else:
            if not isinstance(entry, dict) or set(entry) != {"one", "other"}:
                out.append(f"{m.where}: {m.key!r} counted message needs both forms, one and other")
                continue
            allowed = fields(m.key) | fields(m.other)
            for form, text in entry.items():
                if not fields(text) <= allowed:
                    out.append(f"{m.where}: {m.key!r} placeholder names differ in {form}: {sorted(fields(text))}")
            if fields(entry["other"]) != fields(m.other):
                out.append(f"{m.where}: {m.key!r} placeholder names differ in other: {sorted(fields(entry['other']))}")
    used = {m.key for m in found}
    out += [f"{key!r}: orphaned (no tx literal or declared source uses it)" for key in merged if key not in used]
    return out
