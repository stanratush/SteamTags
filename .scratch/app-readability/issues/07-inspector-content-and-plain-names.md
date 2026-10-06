# 07: Inspector content and plain metric names

**What to build:** the tag Inspector answers "which games, and which connected tags" before showing the metrics. Every Inspector metric gets a plain name in a two-column list. The column name stays in its tooltip, in the help and in the export.

**Blocked by:** 01, 02

**Status:** done

Spec: [App readability spec](../spec.md): "Inspector" (including the plain-names table).

- [x] Tag view, in this order:
  1. "N games in the network have this tag" (after the Minimum Months Filter).
  2. The games (rank, name): the first 10, then "Show all N".
  3. The connected tags (tag, cluster swatch, shared games, lift), sorted by shared games. Clicking a row selects that edge, dims the rest and pans the edge into view.
  4. The metrics.
- [x] The edge view keeps "Games having both tags" (rank, AppID, name) and uses the plain names.
- [x] The tag, edge, cluster and Removal Sensitivity views show the plain names from the spec table, in a `.kv` two-column list with muted labels.
  - The active weight's strength is marked "used for clustering".
  - Within-z keeps its cap text, silhouette keeps "descriptive", and the beyond-noise flag keeps "screening flag, not a significance test".
  - No "hub", no "importance".
- [x] Each label's tooltip gives the schema description and the column name. AG Grid headers, the export and the Column Index keep the column names.
- [x] Each metric entry in `docs/user-guide/03-metric-reference.md` gains "Shown in the app as …". A test checks that every Inspector label maps to a schema column with a guide entry that names that label.
- [x] Tests:
  - The tag view lists exactly the games of the filtered dataset that have the tag, and the connected tags in shared-games order.
  - The guide consistency checks pass.

## Comments

**2026-10-06 (implemented):** `view.INSPECTOR_LABELS` is the single table of plain names → schema columns; `_kv` renders the `.kv` list, and each label's tooltip is built from the schema (description + column + file). The tag view leads with the games (`view.tag_games`, after the Minimum Months Filter; first 10 then a "Show all N" disclosure), then `view.connected_tags` (rows with pattern ids; a click selects the link with `pan`, so it dims the rest and is centred), then the metrics, where both weights' strengths are shown and the active ones say "used for clustering". The edge view keeps rank, AppID and name; the cluster member table uses short headers whose tooltips are the plain names'. 22 entries of `03-metric-reference.md` gained a "Shown in the app as …" line; `test_guide` checks every label against them. Browser check in headless Chrome against the live app (the pane was hidden): Shooter shows "32 games…", 10 games + "Show all 32", 20 connected tags by shared games, tooltips ending "Column: strength_shared (nodes.csv)."; clicking the top row selects Shooter — Multiplayer, dims 388 elements and centres the link; no "hub" or "importance" anywhere in the Inspector.
