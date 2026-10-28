# 10: Interface Language core: translator, catalogue, switch and cookie

**What to build:** the `steamstudy.i18n` package and the EN | BG switch. Afterwards a translator exists, the switch changes a `lang` store live in all three modes, the choice survives restarts by cookie, and the parity test and its done-list are in place. No module is wired yet (issues 12–14), and every Bulgarian catalogue is empty, so the app still shows English everywhere except the tab title.

**Blocked by:** none

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Interface Language" (The switch and its persistence; Catalogue and translator; Plurals and numbers; Tests), "Bulk translation and review" (Strictness ratchet; Visibility and the release gate). Record: [ADR 0003](../../../docs/adr/0003-bulgarian-is-a-view-only-translation.md).

- [x] **`steamstudy/i18n/`**: `text(lang)` returns a translator `tx` for `"en"` or `"bg"`.
  - `tx("…", **values)` looks up the English key in the language's catalogue, falls back to the English text when it is missing, and formats named placeholders only.
  - `tx.n(count, one=…, other=…, **values)` picks the form. Both forms are whole messages, and the catalogue entry holds both.
  - `tx.join(items)` joins a list in the language's way (English: "a, b and c"; Bulgarian: "a, b и c").
  - `tx.num(value, digits)` follows the language's number rule. English is exactly today's `view.num()`. Bulgarian has a decimal comma, no thousands separator and an attached `%`. `n/a`, `yes` and `no` become н/д, да and не.
- [x] **`steamstudy/i18n/bg/`**: one module per area (`layout`, `callbacks`, `view`, `ps_view`, `ps_run`, `selection_text`, `refusals`, `schema_tips`, `ui_words`), each an empty dict for now.
- [x] **The switch**: an EN | BG segmented control in the header, beside the mode switch, in all three modes.
  - It writes the `lang` store and the `steamstudy_lang` cookie client-side.
  - `app.layout` becomes a function that reads the cookie when the page is served (default `en`).
  - The browser tab title is set client-side from the store: Tag Network / Мрежа от тагове.
- [x] **Relabel registry**: `build_layout` gets a way to register a static prop as (component id, prop, message). One relabel callback, on `lang`, sets every registered prop with `set_props`. The switch's own tooltip uses it, as the first entry.
- [x] **Text vs numbers**: a short module docstring (or a comment at the callback registry) states the rule. Callbacks that render text take `lang` as an Input. Callbacks that compute take it only as State.
- [x] **Parity test** (`tests/test_i18n.py`):
  - An AST scan of `src/steamstudy` finds every `tx("…")` / `tx.n(…)` literal.
  - Completeness: a missing Bulgarian entry fails only for modules on the done-list. Correctness is checked wherever an entry exists, and is strict now: placeholder names match, counted messages have both forms, no orphaned keys.
  - It reads the declared non-literal sources (left empty here; issues 11 and 12 add them).
- [x] **`tests/i18n_done.py`**: `CATALOGUE_DONE` and `GUIDE_DONE`, both empty, with a comment pointing to the spec's ratchet.
- [x] **Release gate**: `docs/releasing-an-app-bundle.md` gains a step: "No release while `tests/i18n_done.py` exists (the Bulgarian translation is unfinished)".
- [x] **Guide** (English): `02-app-controls.md` Control reference gains an **Interface language** entry: the switch, what stays English (exports, tag names, game titles, Genre values, `C1…`, dataset labels), and that the choice is remembered per browser. A help key points the switch's ⓘ to it.
- [x] Tests:
  - `text("en")` is the identity on keys. `text("bg")` falls back to English for a missing key. Placeholders format in both.
  - `tx.num` in English equals `view.num` on a table of values, including `None`, ints, floats, `%` and the `n/a` / `yes` / `no` words. Bulgarian gives 0,42, 12345, 42% and н/д.
  - `tx.n` picks `one` for 1 and `other` otherwise, in both languages.
  - The parity test passes with an empty done-list, and fails on a monkeypatched done module with a missing entry, on a placeholder mismatch, and on an orphaned key.
  - App (`dash_http`): the page served with `steamstudy_lang=bg` has `lang` = `bg` in its first layout. Switching the store fires the relabel callback and no Network State recompute.

## Comments

**2026-10-28, implementation.** Done as specified, with two choices the ticket left open:

- The switch's help sits on a dotted **Language** label beside it, like an analytical control's label, not on an ⓘ: the app keeps ⓘ marks for grid headers only (`test_only_controls_that_need_interpretation_carry_help`). Its help key is `header.lang`, because `control.*` keys are the analytical controls. The label's tooltip is the registry's first entry.
- The tab title comes from a `ui-words` store (layout.py `ui_words`), registered like any static prop, so issue 12 extends the same store with the JS words. `tx.pct` and `tx.fixed` sit beside `tx.num` for the percent and format-spec numbers that `selection_text` and `ps_view` write.
- The parity checker lives in `tests/i18n_parity.py` (`scan`, `problems`, `AREA_OF`, `NON_LITERAL`), so issues 11-14 extend it.
