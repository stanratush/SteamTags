"""Bulgarian: ui_words. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation.

Empty by design (issue 23): the `ui-words` store's words are `tx` calls in `app/layout.py`, so their entries are in
the `layout` catalogue. Only `help.py` and `guide.py` messages would land here."""

MESSAGES: dict[str, str | dict[str, str]] = {}
