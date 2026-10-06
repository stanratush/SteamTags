# 06: Tag search

**What to build:** a searchable tag dropdown in the header that finds any tag. A visible tag is selected and centred. A missing tag shows where it went, plus the one action that brings it back.

**Blocked by:** 01, 02

**Status:** done

Spec: [App readability spec](../spec.md): "Focus cluster and tag search". Prototype: the search in [01-styling-directions](../prototypes/01-styling-directions/PROTOTYPE-styling-directions.html) (try "puz").

- [x] The header search lists the visible tags first, each with a cluster swatch, its cluster and its games. Then it lists every `not_in_network` tag, greyed out, with all its reasons in plain words: "Genre Tag hidden", "defining tag hidden", "removed", "3 games, below 8". Typing filters the list; up/down, Enter and Escape work.
- [x] Choosing a visible tag selects it, centres it (animated) and opens it in the Inspector. This works in every mode, including "Graph only".
- [x] Choosing a missing tag opens a "Not in the network" card with its reasons and games count.
  - It offers **Restore** (removed) or **Unhide** (Genre Tag or defining tag hidden), but only when that one action brings the tag back.
  - The card says that pressing it changes the Network State.
  - Pressing it changes the controls exactly as the existing Restore button or checklist would.
- [x] Tests:
  - The option list for a state contains every node, and every `not_in_network` row with its reasons.
  - Restore and Unhide produce the same settings as the existing controls.
- [x] `docs/user-guide/02-app-controls.md` describes the search.

## Comments

**2026-10-06 (implemented):** The header search is a searchable `dcc.Dropdown` (`tag-search`) whose options come from `view.search_options` with every recompute: a header row, the nodes by name with swatch, cluster and games, a header row, then every `not_in_network` row by games with all its reasons (`view.reason_text`). Picking `node:<id>` selects the tag with `pan: True`, which the selection patch turns into an animated `center` view command; picking `nin:<id>` opens `view.nin_inspector`. `view.nin_action` offers Restore only for exactly "removed" and Unhide only for Genre Tag / defining tag hidden (a defining tag that is also a Genre Tag comes back with one press); `nin_act` applies it to the same controls as the Restore button and the chips, then selects the tag. The value resets after each pick so the same tag can be picked again. Browser check: the in-app pane was hidden, so the scenario ran against the live app in headless Chrome over the DevTools protocol with real typing and keys: "shoot" filters to three tags in the network then four missing ones with reasons; ↓ + Enter selects and centres (zoom 1.2) and opens the Inspector; "strategy" → the Strategy card ("Genre Tag hidden", 24 games, Unhide); Unhide puts it in the network (hidden chips 10 of 11) and opens it; Esc closes the menu.
