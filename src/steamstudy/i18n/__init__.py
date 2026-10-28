"""The Interface Language: English or Bulgarian on screen, never in an export (ADR 0003).

A translator `tx = text(lang)` is an explicit, required argument of every function that renders visible text.
Exports and the CLI pass `text("en")`; there is no process-wide setting. The catalogue is keyed by the English
text with named `{placeholders}` only; a missing Bulgarian entry falls back to the English text at runtime.

- `tx("…", **values)`: one message.
- `tx.n(count, one=…, other=…, **values)`: a counted message, two whole forms; `{n}` is the count. Its catalogue
  entry is keyed by the English `one` form and holds both Bulgarian forms, `{"one": …, "other": …}`.
- `tx.join(items)`: a list in the language's way ("a, b and c").
- `tx.num(value, digits)` and `tx.pct(fraction, digits)`: the language's number rule on screen. English is the
  app's rule before the Interface Language; Bulgarian has a decimal comma, no thousands separator and an attached %.
"""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any

LANGS = ("en", "bg")
DEFAULT = "en"
COOKIE = "steamstudy_lang"  # written client-side (assets/workbench.js), read when the layout is served

# One Bulgarian catalogue module per area under `steamstudy/i18n/bg/`.
AREAS = ("layout", "callbacks", "view", "ps_view", "ps_run", "selection_text", "refusals", "schema_tips",
         "ui_words")

Entry = str | dict[str, str]

_WORDS = {"en": {"n/a": "n/a", "yes": "yes", "no": "no", "and": "and"},
          "bg": {"n/a": "н/д", "yes": "да", "no": "не", "and": "и"}}


def lang_of(value: Any) -> str:
    """A language from a store or a cookie: one of `LANGS`, English for anything else."""
    return value if value in LANGS else DEFAULT


@lru_cache(maxsize=None)
def areas(lang: str) -> dict[str, dict[str, Entry]]:
    """Area -> its catalogue dict, for a language with catalogues (English has none: it is the keys)."""
    if lang == "en":
        return {}
    return {area: importlib.import_module(f"steamstudy.i18n.{lang}.{area}").MESSAGES for area in AREAS}


@lru_cache(maxsize=None)
def catalogue(lang: str) -> dict[str, Entry]:
    """Every area's entries of a language in one dict (keys are unique across areas)."""
    merged: dict[str, Entry] = {}
    for messages in areas(lang).values():
        merged.update(messages)
    return merged


def _format(message: str, values: dict[str, Any]) -> str:
    return message.format(**values) if values else message


class Text:
    """The translator of one language."""

    def __init__(self, lang: str) -> None:
        if lang not in LANGS:
            raise ValueError(f"unknown Interface Language {lang!r}; expected one of {LANGS}")
        self.lang = lang
        self._words = _WORDS[lang]

    def _entry(self, key: str) -> Entry | None:
        return None if self.lang == "en" else catalogue(self.lang).get(key)

    def __call__(self, message: str, **values: Any) -> str:
        entry = self._entry(message)
        return _format(entry if isinstance(entry, str) else message, values)

    def n(self, count: int, *, one: str, other: str, **values: Any) -> str:
        entry = self._entry(one)
        form = "one" if count == 1 else "other"
        chosen = entry.get(form) if isinstance(entry, dict) else None
        return _format(chosen or (one if count == 1 else other), {"n": count, **values})

    def join(self, items: list[Any]) -> str:
        items = [str(i) for i in items]
        if len(items) < 2:
            return "".join(items)
        return f"{', '.join(items[:-1])} {self._words['and']} {items[-1]}"

    def _decimal(self, text: str) -> str:
        return text.replace(".", ",") if self.lang == "bg" else text

    def word(self, key: str) -> str:
        """n/a, yes or no in the language."""
        return self._words[key]

    def num(self, value: Any, digits: int = 2) -> str:
        if value is None:
            return self._words["n/a"]
        if isinstance(value, bool):
            return self._words["yes" if value else "no"]
        if isinstance(value, int):
            return str(value)
        return self._decimal(f"{value:.{digits}f}")

    def fixed(self, value: float, spec: str) -> str:
        """A number formatted with a format spec (`".0f"`, `"+.2f"`, `"g"`), with the language's decimal mark."""
        return self._decimal(format(value, spec))

    def pct(self, fraction: float, digits: int | None = None) -> str:
        """A fraction as a percent: `g` (shortest) unless `digits` is given; the sign is attached in both languages."""
        return self._decimal(f"{fraction * 100:g}" if digits is None else f"{fraction * 100:.{digits}f}") + "%"


@lru_cache(maxsize=None)
def text(lang: str) -> Text:
    """The translator for `lang` ("en" or "bg")."""
    return Text(lang)
