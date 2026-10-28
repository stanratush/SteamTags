# 21: Games within a Cluster

**What to build:** the Cluster Inspector gains a **Games** section. It lists every game that has at least one of the Cluster's Tags, ranked by matched-tag count and then Rank. The same rows go into a new additive `cluster_games.csv` in the Workbench export. The English guide documents both.

**Blocked by:** 13, 17

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Games within a Cluster", "Exports and the schema version", "Resolved while writing this spec" (older exports).

- [x] **Computation**, in a Dash-free module next to the other per-Cluster tables:
  - for each Cluster (Multi-Tag and One-Tag, never the pool), the games of the Network State, after the Minimum Months Filter, that have ≥ 1 of its tags;
  - `matched`, `cluster_size`, `network_tags` (the game's tags in the Tag Network) and `share_of_game` = matched / network_tags;
  - the matched tags in the Members order (◆ Center first, then by game-set distance);
  - ordered by matched high to low, then Rank.
- [x] **Games section** (after Members, before Connections):
  - The lead line reads "**94** of 100 games have at least one of its 18 tags", or for a One-Tag Cluster "**N** games have its tag".
  - Columns: Rank · Name · Matched ("7 / 26") · of its tags (whole percent) · Tags (in full, wrapping). One-Tag Clusters drop Matched and Tags.
  - The first `GAMES_SHOWN` = 10 rows, then "Show all N" in a `<details>`.
  - One escaped HTML block (`data-html`), with inert rows.
  - No section for the pool or a pair.
- [x] Words via `tx` and numbers via `tx.num`, in English.
- [x] **`cluster_games.csv`** in the Workbench export zip, under `SCHEMA_VERSION` 4 (bumped by issue 17).
  - Columns: `cluster`, `appid`, `name`, `rank`, `matched`, `cluster_size`, `network_tags`, `share_of_game`, `matched_tag_ids`, `matched_tags`, typed as in the spec.
  - Each column is declared in `schema.py`, indexed in `guide_index`, and in Appendix B.
  - Open Network State… checks it like every table. Exports without it still open and match.
- [x] **Guide**:
  - `02-app-controls.md`: the Inspector entry gains the **Games** section, explaining Matched and "of its tags".
  - `04-files.md`: the export entry gains `cluster_games.csv`.
  - Appendix B is regenerated.
- [x] Tests:
  - Unit: for each Cluster on two test-Build states, the list equals a brute-force count over the filtered games.
  - The order is matched, then Rank.
  - `share_of_game` uses network tags only (a hidden tag doesn't count).
  - The pool and pairs get no rows.
  - Each CSV row equals its on-screen row.
  - An export with the table round-trips through Open Network State… and `recorded_table_hashes_match`.
  - The schema, Appendix B staleness and guide link tests pass.

## Comments

**2026-10-28, implementation.** Done. Notes:

- `network/tables.cluster_games(games, members, network_tags)` is the one computation. `cluster_game_rows(state)` (the CSV) and the Cluster Inspector (`callbacks.inspector`, `view.cluster_games_section`) both call it, so a CSV row is its on-screen row (`test_each_csv_row_is_its_on_screen_row`).
- **Export only**: `cluster_games.csv` is written by `export_zip`, not by `state_tables`, which also feeds the Build's stacked `analysis/` tables. `schema.EXPORT_ONLY` keeps it out of `STACKED`, so no Build file changes.
- **Guide placement**: chapter 2 has no Workbench Inspector entry. The Inspector is documented in `01-getting-started.md` ("Inspect a node, an edge or a cluster", the Inspector's `?`), so the Games paragraph is there. Every export column needs a chapter 3 entry (`test_every_column_has_a_guide_entry_with_a_heading`), so `03-metric-reference.md` gains **Games within a Cluster** (`#games-within-a-cluster`), where Appendix B points. `04-files.md` gains `cluster_games.csv`.
- The worked example row in the chapter 3 entry is illustrative.
