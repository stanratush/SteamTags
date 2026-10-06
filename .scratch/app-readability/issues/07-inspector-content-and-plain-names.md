# 07: Inspector content and plain metric names

**What to build:** the tag Inspector answers "which games, and which connected tags" before showing the metrics. Every Inspector metric gets a plain name in a two-column list. The column name stays in its tooltip, in the help and in the export.

**Blocked by:** 01, 02

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Inspector" (including the plain-names table).

- [ ] Tag view, in this order:
  1. "N games in the network have this tag" (after the Minimum Months Filter).
  2. The games (rank, name): the first 10, then "Show all N".
  3. The connected tags (tag, cluster swatch, shared games, lift), sorted by shared games. Clicking a row selects that edge, dims the rest and pans the edge into view.
  4. The metrics.
- [ ] The edge view keeps "Games having both tags" (rank, AppID, name) and uses the plain names.
- [ ] The tag, edge, cluster and Removal Sensitivity views show the plain names from the spec table, in a `.kv` two-column list with muted labels.
  - The active weight's strength is marked "used for clustering".
  - Within-z keeps its cap text, silhouette keeps "descriptive", and the beyond-noise flag keeps "screening flag, not a significance test".
  - No "hub", no "importance".
- [ ] Each label's tooltip gives the schema description and the column name. AG Grid headers, the export and the Column Index keep the column names.
- [ ] Each metric entry in `docs/user-guide/03-metric-reference.md` gains "Shown in the app as …". A test checks that every Inspector label maps to a schema column with a guide entry that names that label.
- [ ] Tests:
  - The tag view lists exactly the games of the filtered dataset that have the tag, and the connected tags in shared-games order.
  - The guide consistency checks pass.

## Comments
