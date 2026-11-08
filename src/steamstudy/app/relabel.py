"""The relabel registry: static props of the layout in the Interface Language, set again on a language switch.

Every translated static prop is registered as (component id, prop, message) while a layout is built (`Labels`), in
the language of the page; one callback (callbacks.py `relabel`) sets them all again when the language is switched,
so a new static label needs no new wiring. A text without an id of its own gets a stable one (`i18n-<n>`, in build
order; `Labels(tx, prefix)` keeps two layouts' ids apart).

A message is English text marked `msg("…")` where it is written, so the catalogue parity test finds it like a
`tx("…")` literal; it is translated when the layout is built and on every switch.

The registry is shared by every tab, whatever its Build (ADR 0006), so a message never closes over a Build: one that
depends on it is a `PerBuild`, given the tab's Build when it is set again.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dash import html

from steamstudy.app import help as H
from steamstudy.i18n import Text

@dataclass(frozen=True)
class PerBuild:
    """A message that depends on the tab's Build: `fn(tx, build_context)`."""
    fn: Callable[[Text, Any], Any]


# A registered message: English text for `tx`, a function of the translator (a tooltip, a store's words), or a
# function of the translator and the tab's Build.
Message = str | Callable[[Text], Any] | PerBuild
# json([component id, prop]) -> (component id, prop, message), in the order first registered.
RELABEL: dict[str, tuple[Any, str, Message]] = {}


def msg(message: str) -> str:
    """Mark English text as a message the layout translates (the catalogue parity test reads these)."""
    return message


def message_value(message: Message, tx: Text, build: Any = None) -> Any:
    if isinstance(message, str):
        return tx(message)
    if isinstance(message, PerBuild):
        return message.fn(tx, build)
    return message(tx)


class Labels:
    """The page's translator and the relabel registry, for one build of a layout."""

    def __init__(self, tx: Text, prefix: str = "i18n", build: Any = None) -> None:
        self.tx = tx
        self.prefix = prefix
        self.build = build  # the page's BuildContext, for `PerBuild` messages
        self._n = 0

    def new_id(self) -> str:
        self._n += 1
        return f"{self.prefix}-{self._n}"

    def prop(self, id_: Any, prop: str, message: Message) -> Any:
        """A static prop of a component with an id: registered, in the page's language."""
        RELABEL.setdefault(json.dumps([id_, prop], sort_keys=True), (id_, prop, message))
        return message_value(message, self.tx, self.build)

    def span(self, message: Message, **kw: Any) -> html.Span:
        """A static text as a Span of its own, registered so that a language switch relabels it."""
        id_ = kw.pop("id", None) or self.new_id()
        return html.Span(self.prop(id_, "children", message), id=id_, **kw)

    def help(self, key: str) -> dict[str, Any]:
        """Both help layers for an element of its own id (`id` is in the result): the tooltip is registered."""
        id_ = self.new_id()
        return {"id": id_, "data-tip": self.prop(id_, "data-tip", lambda tx: H.tip(key, tx)),
                "data-help": H.target(key)}

    def term(self, message: Message, key: str, **kw: Any) -> html.Span:
        """A dotted term with both help layers: its text and its tooltip are registered."""
        attrs = self.help(key)
        return html.Span(self.prop(attrs["id"], "children", message), className=kw.pop("className", "term"),
                         tabIndex="0", **attrs, **kw)

    def options(self, id_: str, options: list[tuple[Any, str]]) -> list[dict[str, Any]]:
        """A RadioItems or Checklist's options, with registered labels."""
        return self.prop(id_, "options", lambda tx: [{"label": tx(label), "value": v} for v, label in options])
