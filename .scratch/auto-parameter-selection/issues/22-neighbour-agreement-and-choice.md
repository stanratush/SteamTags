# 22: Neighbour Agreement, Edge Overlap, choosing the pair and its explanation

**What to build:** over a complete grid, the neighbour links (with Edge Overlap) and each pair's Neighbour Agreement. `choose` picks the pair under given constraints. The fixed sentences of the selection explanation start a new `selection_text` module.

**Blocked by:** 21

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "Neighbour Agreement and Edge Overlap", "Choosing the pair", "The selection explanation", "Modules" (`selection_text`).

- [ ] `neighbour_links(grid)`: one record per unordered neighbour pair inside the grid. It holds the status (`ok`, `neighbour_has_no_selected_partition` or `too_few_compared_tags`; `outside_grid` is reported per direction), shared tags and their Jaccard overlap, compared tags (shared, with an edge in at least one graph), `identical_graph`, the ARI on the compared tags, and Edge Overlap (unweighted Jaccard of the edge sets).
- [ ] `neighbour_agreement(grid)` per pair:
  - the mean ARI over `ok` links with a **different graph**;
  - counts of neighbours in the grid, comparable, comparable with a different graph, identical-graph and missing;
  - the minimum ARI over the counted links;
  - `no_comparable_neighbours` when nothing counts.

  It is independent of the constraints.
- [ ] `choose(grid, na, constraints) -> Choice`:
  - the Qualifying Pairs, and every failing reason code per pair;
  - the near-best set (NA ≥ max − tolerance, 1e-12 float tolerance), then the pick by smallest g, then smallest s;
  - `no_qualifying_pair`, with the exclusion table (alone and cumulative, in the constraint table's order);
  - the constraint values and tolerance it used, and which constraints excluded no pair.
- [ ] `steamstudy.network.selection_text`:
  - `explanation(choice, pair, settings_label, constraints_label, minimum_k)`: the template word for word, with each conditional sentence, the `not_representable` / `not_reproduced` variants and both caveats;
  - `no_qualifying_message(...)`;
  - `DESCRIPTIVE_CAPTION` and `DESCRIPTIVE_HELP`;
  - `HIGH_G_CAVEAT`;
  - `DATASET_STRIP_SENTENCE`.

  It returns structured text (paragraphs with bold and italic spans) that both Dash and Markdown can render.
- [ ] Tests:
  - Synthetic grid: missing neighbours are never 0; identical-graph links are flagged but excluded from the mean; too few compared tags; `no_comparable_neighbours`.
  - Edge Overlap on hand-built edge sets, including edges of tags dropped by a g-step.
  - `choose`: every reason code; inclusive bounds; the tolerance edge (exactly max − 0.05 is in); tie-breaks; `no_qualifying_pair` with correct alone and cumulative counts; constraint changes need no grid data beyond the cached results.
  - Explanation: golden text for a chosen pair with every conditional sentence on, for one with all of them off, and for the no-qualifying message.
  - **Real-Build regression** (marked slow, skipped without the full Build): default settings and constraints give the spec's five chosen pairs (overall 17,2 · puzzle 14,2 · rpg 7,5 · simulation 14,5 · strategy 14,2) and their NA.
