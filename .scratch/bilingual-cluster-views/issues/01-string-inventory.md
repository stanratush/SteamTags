# String inventory
Type: task
Status: open
Blocked by: none

## Question

Before the [Translation mechanism](02-translation-mechanism.md) can be chosen: where does every user-visible string in the app come from, and how many are there? This is AFK work. The output is a table in `research/01-string-inventory.md`.

- By source: `app/layout.py`, `view.py`, `ps_view.py`, `callbacks.py` (including error and warning texts), `renderer.py`, `export.py`/`ps_export.py` (only the messages shown in the app), `network/selection_text.py`, `analysis/templates.py` (Analysis Report mode), `assets/graph.js` and `workbench.js`, `app.css` (`content:` strings), and the User Guide (`guide.py`/`help.py` lookups by file and heading anchor).
- For each source: the string count, whether strings are literals, f-strings or templates with live values, and whether a test pins the exact wording (`tests/test_guide.py`, `test_app.py`, phrase-pinning tests).
- Which strings are data and never get translated: tag names, game titles, Genre values, `C1…` labels, export column names.
- Which guide anchors are referenced from code, and how they are derived (heading slugs). A Bulgarian heading would change its slug.
