# 13: Translate-ready Workbench views (`view.py`)

**What to build:** every text-rendering function in `app/view.py` takes a required `tx` and renders all its words and numbers through it, in English. This covers the Inspector views, the Network State sentence, the quality lines, the tables' captions and the empty states. The A2 slice (issue 24) then only fills a catalogue.

**Blocked by:** 12

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Catalogue and translator", "Plurals and numbers". Inventory: [research 01](../research/01-string-inventory.md) (`view.py` row).

- [ ] Every public text-rendering function in `view.py` takes `tx` (required, keyword). Every literal visible word goes through `tx` with named placeholders. There is no f-string concatenation of words around values.
- [ ] English-style plurals (`'s'`, `(s)`, `is/are`, `has/have`) become `tx.n` with two whole forms.
- [ ] `view.num` calls become `tx.num`. `view.num` stays only if callers remain outside this module. Issue 14 removes it once nothing calls it.
- [ ] The escaped HTML blocks (`data-html`) are built with the translated text. Numbers in them use `tx.num`.
- [ ] The callbacks that call `view` pass `text(lang)`, following the Input/State rule. A text-only re-render on a language switch never recomputes.
- [ ] No `# i18n: wire` marker is left in `view.py` or its callers.
- [ ] Tests:
  - The pseudo-language test from issue 12 extends to the Inspector (tag, Cluster, link and region views), the Network State sentence and the quality lines: every word is bracketed, and tag names, game titles and `C1…` are not.
  - The ~English phrase asserts in `test_app.py` still pass with `text("en")`.
  - A language switch with an Inspector open re-renders it and issues no `graph-data` request.
