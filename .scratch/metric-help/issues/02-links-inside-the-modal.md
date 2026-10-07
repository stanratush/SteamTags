# 02: Links inside the help modal

**What to build:** guide links inside the help modal open their target entry in the modal, with ← Back.

**Blocked by:** 01

**Status:** done

Spec: [Metric help spec](../spec.md): "Links inside the modal".

- [x] `#anchor` and `<chapter>.md#anchor` links open that entry in the modal. A chapter link without an anchor opens the chapter's first section.
- [x] ← Back walks a stack of opened entries. The stack clears when the modal closes.
- [x] External links still open in a new tab.
- [x] Test: every in-guide link the modal can follow points to an existing heading.
- [x] Checked in the browser: follow "Compare with" links from Modularity Q to the Null-model baseline and back.

## Comments

- 2026-10-07: Done. `guide.py` gains `resolve_link` (an `#anchor` or `<chapter>.md[#anchor]` link -> its modal target; links outside the guide folder and external links -> None), `modal_links` (points in-guide links at `#help:<target>`, sharing the `LINK` pattern with the test) and `first_section` (a bare chapter link shows the title, the introduction and the first `##` section); `help_markdown_at` applies both and takes an optional anchor. `show_help` keeps a `help-history` store: an app click or a panel `?` starts it afresh, a link inside the modal (`follow`) pushes (not twice for the entry already shown), ← Back (`help-back`, shown from two entries up) pops, closing clears it. `workbench.js` intercepts `#help:` links in `#help-body` and sets `help-target` with `follow: true`; other links keep `target=_blank`. Each newly rendered entry scrolls the modal to its top. Modularity Q's *Compare with.* now links to the Null-model baseline and to the seed spread entry, so there is a link to follow. Tests: link resolution, the rewrite, the first section, every in-guide link in every chapter resolving to an existing heading (over 200 links), and the Back stack through `show_help`. Checked in the browser: Q -> null model -> excess -> Back -> Back, close clears the stack, a chapter link (Load a dataset -> Metric reference), and external links (python.org) still open in a new tab; no console errors. Full suite: 347 passed; `test_shipped_config_loads_with_spec_defaults` still fails from the researcher's uncommitted `config/collection.toml`. Left as is: `../running-guide.md` links point outside the packaged guide and still go nowhere in the app.
