# 06: Tag search

**What to build:** a searchable tag dropdown in the header that finds any tag. A visible tag is selected and centred. A missing tag shows where it went, plus the one action that brings it back.

**Blocked by:** 01, 02

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Focus cluster and tag search". Prototype: the search in [01-styling-directions](../prototypes/01-styling-directions/PROTOTYPE-styling-directions.html) (try "puz").

- [ ] The header search lists the visible tags first, each with a cluster swatch, its cluster and its games. Then it lists every `not_in_network` tag, greyed out, with all its reasons in plain words: "Genre Tag hidden", "defining tag hidden", "removed", "3 games, below 8". Typing filters the list; up/down, Enter and Escape work.
- [ ] Choosing a visible tag selects it, centres it (animated) and opens it in the Inspector. This works in every mode, including "Graph only".
- [ ] Choosing a missing tag opens a "Not in the network" card with its reasons and games count.
  - It offers **Restore** (removed) or **Unhide** (Genre Tag or defining tag hidden), but only when that one action brings the tag back.
  - The card says that pressing it changes the Network State.
  - Pressing it changes the controls exactly as the existing Restore button or checklist would.
- [ ] Tests:
  - The option list for a state contains every node, and every `not_in_network` row with its reasons.
  - Restore and Unhide produce the same settings as the existing controls.
- [ ] `docs/user-guide/02-app-controls.md` describes the search.

## Comments
