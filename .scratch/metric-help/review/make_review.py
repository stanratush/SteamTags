"""Generate the metric-help wording review page (issue 07) from the app and the User Guide.

Nothing here is retyped: the elements come from the app's own components (the layout and one recompute of the
latest Build's first dataset at its default settings), and every text comes from the guide. Corrections go into the
guide; then run this again from the repository root:

    .venv/Scripts/python.exe .scratch/metric-help/review/make_review.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple

from dash_ag_grid import AgGrid

from steamstudy.app import callbacks as CB
from steamstudy.app import help as H
from steamstudy.app import view as V
from steamstudy.app.guide import IN_SHORT_MAX_WORDS, chapter, headings, in_short_at, plain, section
from steamstudy.app.layout import build_layout
from steamstudy.app.loader import load_build

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("wording-review.md")
GUIDE_LINK = "../../../docs/user-guide/"
LABELS = r"^(In short\.|Higher →|Lower →|Raising it →|Here:|Caution:)\s*(.*)$"


class Row(NamedTuple):
    name: str     # the element as the app shows it
    tip: str      # its tooltip, as the app builds it
    entry: str    # the guide entry the tooltip's In short comes from (`<file>#<anchor>`)
    click: str    # what a click does instead of opening the entry ("" = it opens the entry)


# ----------------------------------------------------------------------------- the app's elements

def walk(component: Any):
    if isinstance(component, (list, tuple)):
        for c in component:
            yield from walk(c)
    elif component is not None and not isinstance(component, (str, int, float, dict)):
        yield component
        yield from walk(getattr(component, "children", None))


def text(component: Any) -> str:
    if isinstance(component, (str, int, float)):
        return str(component)
    if isinstance(component, (list, tuple)):
        return "".join(text(c) for c in component)
    return text(getattr(component, "children", None)) if component is not None else ""


def name(component: Any) -> str:
    """The element as the app shows it: its dotted term, the control an ⓘ belongs to, a pill's text, or its text."""
    aria = getattr(component, "aria-label", None)
    if aria:
        return aria.split(": ", 1)[-1] + " (ⓘ)"
    if getattr(component, "data-pill", None):
        return text(component).strip() + " (pill)"
    for c in walk(component):
        if c is not component and "term" in str(getattr(c, "className", "") or "").split():
            return text(c).strip()
    shown = text(component).strip()
    return shown if len(shown) <= 48 else shown[:45] + "…"


def with_help(tree: Any) -> list[Row]:
    """Every element in a tree that has a tooltip. A pill and the Tidy button show their control's In short, but a
    click opens the pill's popover or tidies the layout."""
    rows = []
    for c in walk(tree):
        if not getattr(c, "data-tip", None):
            continue
        opens = getattr(c, "data-help", None)
        pill = getattr(c, "data-pill", None)
        control = pill or {"relayout-btn": "tidy"}.get(str(getattr(c, "id", "")))
        shown = name(c) + (" (button)" if not opens and not pill else "")
        rows.append(Row(shown, getattr(c, "data-tip"), opens or H.target(f"control.{control}"),
                        "" if opens else ("opens the pill's popover" if pill else "tidies the layout")))
    return rows


def surfaces(build_path: Path) -> dict[str, list[Row]]:
    ctx = load_build(build_path)
    dataset = ctx.datasets[0].key
    values = CB.controls_from_settings(ctx, ctx.default_settings(dataset))
    out = CB.recompute(str(build_path), *[values[k] for k in CB.CONTROL_IDS], values["removed"], None)
    layout = build_layout(ctx)
    panel = next(c for c in walk(layout) if getattr(c, "id", None) == "controls-panel")
    overlay = [c for c in walk(layout) if "ov-tr" in str(getattr(c, "className", "") or "")]

    inspector = []
    for label, columns in V.INSPECTOR_LABELS.items():
        tip, entry = H.column_help(columns)
        inspector.append(Row(label, tip, entry, ""))

    grids = []
    for grid in (c for c in walk(layout) if isinstance(c, AgGrid)):
        by_entry: dict[str, list[dict]] = defaultdict(list)
        for d in grid.columnDefs:
            params = d.get("headerComponentParams", {}).get("innerHeaderComponentParams", {})
            if params.get("help"):
                by_entry[params["help"]].append(d)
        for entry, defs in by_entry.items():
            grids.append(Row(f"{grid.id}: " + ", ".join(d["headerName"] for d in defs), defs[0]["headerTooltip"],
                             entry, ""))

    settings = ctx.default_settings(dataset)
    export = [r for r in with_help(list(out)) if r.entry.endswith("#deposit-the-export-zip")]
    return {
        "Summary row (above the graph)": with_help(out[4]),
        "Cluster quality tab": with_help(out[6]),
        "Inspector (labels and table headers)": inspector,
        "Grid column headers (one row per entry and grid)": grids,
        # labels and ⓘ (which open the entry) first, then the pills and the Tidy button that show the same In short
        "Analytical controls (Controls panel, pill bar, graph overlay)": sorted(with_help([panel, overlay]),
                                                                               key=lambda r: bool(r.click)),
        "Legend": with_help(out[3]),
        "Dataset summary (Analysis Report §1) and Export": with_help(V.state_table(
            settings.key(), "…", "…", 0, 0, {})) + export,
    }


# ----------------------------------------------------------------------------- the page

def entry_title(entry: str) -> str:
    file, anchor = entry.split("#")
    return next((t for _, t, a in headings(chapter(file) or "") if a == anchor), anchor)


def link(entry: str) -> str:
    return f"[{plain(entry_title(entry))}]({GUIDE_LINK}{entry})"


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def in_short_lines(tip: str) -> tuple[list[str], list[str]]:
    """A tooltip's In short lines (labels bold) and the lines the app adds (Now, Column, Field), apart."""
    guide: list[str] = []
    app: list[str] = []
    for line in tip.split("\n"):
        m = re.match(LABELS, line)
        (guide if m else app).append(f"**{m.group(1)}** {m.group(2)}" if m else f"*{line}*")
    return guide, app


def words(entry: str) -> int:
    return sum(len(t.split()) for _, t in in_short_at(*entry.split("#")))


def why(entry: str) -> str:
    file, anchor = entry.split("#")
    m = re.search(r"^\*Why it matters here\.\* (.*)$", section(chapter(file) or "", anchor) or "", flags=re.M)
    return m.group(1) if m else "(missing)"


def page(build_path: Path) -> str:
    groups = surfaces(build_path)
    entries = sorted({r.entry for rows in groups.values() for r in rows}, key=lambda e: (e.split("#")[0], e))
    successful = [e for e in entries if re.search(r"\bsuccess", " ".join(t for _, t in in_short_at(*e.split("#")))
                                                  + " " + why(e), flags=re.I)]
    out = [
        "# Metric help: wording review",
        "",
        f"Generated on {date.today().isoformat()} from Build `{build_path.name}` (first dataset, default settings) by "
        "`make_review.py`, from the app's own components and the User Guide. **Do not edit this page**: correct the "
        "guide entry it links to, then run the script again.",
        "",
        "How to review (spec: *Review*; issue 07):",
        "",
        "- Each surface lists every element of the app that has help: its tooltip (layer 1) and the guide entry a "
        "click opens (layer 2). Labels are bold; a line the app adds below the guide text (a **Now:** line of live "
        "values, the column or Network State field) is in italics.",
        "- A tooltip is written out in full the first time its entry appears; later elements with the same entry say "
        "so and show only the lines the app adds.",
        f"- Words: the In short block's length, against the cap of {IN_SHORT_MAX_WORDS}.",
        "- The appendix gives every linked entry's *Why it matters here.* paragraph once.",
        "- Write a correction as a comment under issue 07, or edit the guide entry directly. Tick a surface when its "
        "wording is approved.",
        "",
        "## Decisions",
        "",
        "- [x] **\"the most-played games\"**, not \"successful games\" (decided 2026-10-08). Entries the app links to "
        "that still say \"success…\" in their In short or Why it matters: "
        + (", ".join(link(e) for e in successful) or "none") + ".",
        "- [x] **Self-explanatory controls carry no help** (decided 2026-10-08): the minimum games per tag, the minimum "
        "shared games, Hidden Genre Tags, Hide defining tag, Remove / Restore, Global / Cluster-separated and Tidy. "
        "Their entries stay in the guide, linked from the Control reference; Tidy keeps a native title.",
        "- [ ] **A pill's click** (pill bar, medium and narrow forms) opens its popover, whose dotted label then opens "
        "the entry; hover and Tab show the In short. The spec asked for the click to open the entry (issue 05).",
        "",
    ]
    first: dict[str, str] = {}
    for n, (title, rows) in enumerate(groups.items(), 1):
        out += [f"## {n} {title}", "", "- [ ] Approved", "",
                "| Element | Tooltip (layer 1) | Entry (layer 2) | Words |", "|---|---|---|---|"]
        for row in rows:
            guide, app = in_short_lines(row.tip)
            if row.entry in first:
                shown = [f"*Same In short as {first[row.entry]}.*", *app]
            else:
                first[row.entry] = f"{row.name} ({title.split(' (')[0]})"
                shown = guide + app
            opens = link(row.entry) + (f"; a click {row.click}" if row.click else "")
            out.append(f"| {cell(row.name)} | {'<br>'.join(cell(x) for x in shown)} | {opens} | {words(row.entry)} |")
        out.append("")
    out += ["## Appendix: *Why it matters here.* of every linked entry", ""]
    for entry in entries:
        out += [f"### {plain(entry_title(entry))}", "", f"{link(entry)} · In short {words(entry)} words", "",
                why(entry), ""]
    return "\n".join(out)


if __name__ == "__main__":
    build = ROOT / "builds" / (ROOT / "builds" / "latest").read_text(encoding="utf-8").strip()
    OUT.write_text(page(build), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
