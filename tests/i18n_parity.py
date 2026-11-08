"""Catalogue parity: every `tx("…")` / `tx.n(…)` literal in the source against the Bulgarian catalogue.

Every literal needs an entry, placeholder names match, a counted message has both forms, and no key is orphaned.
The app still falls back to English at runtime for a missing entry; the tests leave no room for one.

The superseded-word scan (issue 22) checks every Bulgarian text, catalogue and guide, against the Superseded words
of the term table (`docs/i18n/bg-terms.md`).
"""

from __future__ import annotations

import ast
import re
import string
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from steamstudy import i18n

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "steamstudy"
TERMS = REPO / "docs" / "i18n" / "bg-terms.md"
GUIDE_BG = REPO / "docs" / "user-guide" / "bg"

# Source file (relative to src/steamstudy) -> the catalogue area its messages belong to.
AREA_OF = {
    "app/layout.py": "layout", "app/renderer.py": "layout", "app/server.py": "layout",
    "app/callbacks.py": "callbacks",
    "app/view.py": "view",
    "app/ps_view.py": "ps_view",
    "app/ps_run.py": "ps_run",
    "network/selection_text.py": "selection_text",
    "app/export.py": "refusals",
    "app/help.py": "ui_words", "app/guide.py": "ui_words", "app/relabel.py": "layout",
    "network/selection.py": "selection_text", "app/ps_export.py": "selection_text",
    "app/build_menu.py": "build_menu", "app/draft_dialog.py": "build_menu", "app/preview.py": "build_menu",
}

def _refusals() -> Iterable[str]:
    from steamstudy.app.export import REFUSALS

    return REFUSALS.values()


def _import_codes() -> Iterable[str]:
    """Every Import error and warning code's message (Import data… shows them in the Interface Language)."""
    from steamstudy.imports import ERROR_CODES, WARNING_CODES

    return [*ERROR_CODES.values(), *WARNING_CODES.values()]


def _schema_tips() -> Iterable[str]:
    """The schema descriptions the grids show as header tooltips (identifier columns: `view.column_defs`)."""
    from steamstudy.app.layout import GRIDS
    from steamstudy.i18n import text

    en = text("en")
    return sorted({d["headerTooltip"] for grid in GRIDS.values() for kind in ("steam", "import")
                   for d in grid(en, kind=kind) if "headerComponentParams" not in d})


# Text that reaches `tx` as a variable, by area: the declared non-literal sources (schema descriptions shown as
# header tooltips, the OpenRefused reasons). The In short label sets are the guide's (guide.LABELS), not catalogued.
def _inspector_labels() -> Iterable[str]:
    from steamstudy.app.view import INSPECTOR_LABELS

    return INSPECTOR_LABELS


def _selection_sentences() -> Iterable[str]:
    from steamstudy.network.selection_text import SENTENCES

    return SENTENCES


NON_LITERAL: dict[str, Callable[[], Iterable[str]]] = {"refusals": _refusals, "schema_tips": _schema_tips,
                                                       "view": _inspector_labels,
                                                       "selection_text": _selection_sentences,
                                                       "build_menu": _import_codes}


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
        if isinstance(f, ast.Name) and f.id in ("tx", "msg") and node.args and _str(node.args[0]) is not None:
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


def problems(found: list[Message], areas: dict[str, dict[str, i18n.Entry]]) -> list[str]:
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


# ----------------------------------------------------------------------------- the superseded-word scan


def superseded(terms: Path = TERMS) -> list[tuple[str, tuple[str, ...]]]:
    """The term table's Superseded words: (stem, allowed phrases) per row. Phrases are `;`-separated, `*` and `—`
    are decoration."""
    section = re.search(r"^## Superseded words\n(.*?)(?=^## |\Z)", terms.read_text(encoding="utf-8"), re.M | re.S)
    if section is None:
        raise ValueError(f"{terms}: no Superseded words section")
    rows = []
    table = [line for line in section.group(1).splitlines() if line.startswith("|")]
    for line in table[2:]:  # past the header and its separator
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 2 or not cells[0]:
            continue
        phrases = tuple(p.strip(" *") for p in cells[1].split(";") if p.strip(" *—"))
        rows.append((cells[0].strip("*"), phrases))
    return rows


def bulgarian_texts() -> dict[str, str]:
    """Every Bulgarian text, by where it is: each catalogue entry (each plural form) and each guide file."""
    out = {}
    for area, messages in i18n.areas("bg").items():
        for key, entry in messages.items():
            for form, text in (entry.items() if isinstance(entry, dict) else [("", entry)]):
                out[f"{area}: {key}" + (f" [{form}]" if form else "")] = text
    for path in sorted(GUIDE_BG.rglob("*")):
        if path.is_file():
            out[path.relative_to(REPO).as_posix()] = path.read_text(encoding="utf-8")
    return out


def superseded_hits(texts: dict[str, str], table: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    """Each word of `texts` that starts with a superseded stem (case-insensitive), outside the stem's allowed
    phrases: `"<where>: <word> (superseded: <stem>)"`."""
    out = []
    for where, text in texts.items():
        for stem, phrases in table:
            allowed = [m.span() for p in phrases for m in re.finditer(re.escape(p), text, re.I)]
            for m in re.finditer(rf"\b{re.escape(stem)}\w*", text, re.I):
                if not any(a <= m.start() < b for a, b in allowed):
                    out.append(f"{where}: {m.group()} (superseded: {stem})")
    return out
