"""Each panel's own collapse button and, while the panel is collapsed, the rail that reopens it.

The `panels` (Workbench and Analysis Report mode) and `ps-panels` (Parameter Selection) checklists are still the
panels' state, kept hidden, and the `cc-panels` session store holds Cluster Comparison's drawer. callbacks.py
`toggle_panel` turns a click on a button or a rail into a change of their value, so everything that reads them (the
root classes, the block styles, the Inspector's form) is unchanged.
app.css shows a rail only while its panel is off.
"""

from __future__ import annotations

from typing import Any

from dash import html

from steamstudy.app.relabel import Labels, msg

# (group, panel) -> the panel's name, as its title bar shows it.
NAMES = {("wb", "controls"): msg("Controls"), ("wb", "inspector"): msg("Inspector"), ("wb", "tables"): msg("Tables"),
         ("ps", "controls"): msg("Controls"), ("ps", "constraints"): msg("Pair Constraints"),
         ("ps", "inspector"): msg("Pair Inspector"), ("cc", "controls"): msg("Cluster Comparison")}
# The collapse button's arrow points the way the panel goes.
GLYPHS = {"controls": "«", "inspector": "»", "tables": "▾", "constraints": "▴"}
# group -> the component and prop that hold its panels' state: a checklist each for the Workbench and Parameter
# Selection; Cluster Comparison's drawer is a store that workbench.js `ccPanels` keeps in sessionStorage.
STATE = {"wb": ("panels", "value"), "ps": ("ps-panels", "value"), "cc": ("cc-panels", "data")}


def button_id(group: str, panel: str, opens: bool) -> dict[str, Any]:
    return {"type": "panel-btn", "group": group, "panel": panel, "opens": int(opens)}


def collapse_button(L: Labels, group: str, panel: str) -> html.Button:
    """The panel's collapse button, for its title bar."""
    id_, name = button_id(group, panel, False), NAMES[(group, panel)]
    title = L.prop(id_, "title", lambda tx: tx("Hide {panel}", panel=tx(name)))
    label = L.prop(id_, "aria-label", lambda tx: tx("Hide {panel}", panel=tx(name)))
    return html.Button(GLYPHS[panel], id=id_, className=f"pcoll pcoll-{panel}", n_clicks=0, title=title,
                       **{"aria-label": label, "aria-expanded": "true"})


def rail(L: Labels, group: str, panel: str) -> html.Button:
    """The thin bar a collapsed panel leaves on its edge; a click reopens the panel."""
    id_, name = button_id(group, panel, True), NAMES[(group, panel)]
    title = L.prop(id_, "title", lambda tx: tx("Show {panel}", panel=tx(name)))
    aria: dict[str, Any] = {"aria-expanded": "false"}
    return html.Button(L.span(name, className="rail-name"), id=id_, className=f"rail rail-{panel}", n_clicks=0,
                       title=title, **aria)


def toggled(value: list[str] | None, panel: str, opens: bool) -> list[str]:
    """The panels' new value after a click: the panel added (a rail) or taken away (a collapse button)."""
    value = [p for p in (value or []) if p != panel]
    return value + [panel] if opens else value
