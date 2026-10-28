# Games within a Cluster
Type: grilling
Status: resolved
Blocked by: none

## Question

What exactly does the games list for a Cluster show? Uses `grilling` + `domain-modeling`.

- The game set: games in the Network State (after the Minimum Months Filter, as `view.tag_games`) that have at least one of the Cluster's Tags. Only visible member Tags count, never hidden or removed ones.
- Ranking: by the number of matching Cluster Tags, then which tie-break (Mean Monthly Players rank, name).
- Columns: matched Tags, matched count, % of the Cluster's Tags (matched / cluster size), and possibly the game's rank and AppID. For a large Cluster, is the matched-tags list shown in full or truncated?
- One-Tag Clusters: the list is then the tag's own games at 100%. Is that shown, or does it point to the tag inspector?
- Placement: a section of the Cluster Inspector, or a tab. List length (all games, possibly 100) against the Inspector's HTML-table performance note in `view.py`.
- Is it exported (fog on the map: exports for features 3 and 4)?

## Answer

Settled with the researcher on 2026-10-28, who accepted every recommendation in two grilling rounds. The numbers below were measured on the latest Build (Overall and Puzzle defaults, and Overall at γ = 2.5) with a read-only script. Nothing in `src/` changed.

- **Measured fact that shaped it**: "at least one of the Cluster's tags" covers almost every game. In the Overall default, C1 (26 tags) matches 99 of 100 games, C2 (18) 94 and C3 (11) 77. Puzzle gives 96, 83, 74 and 57. No game has every tag of a large Cluster: the best is 16 of 26. At γ = 2.5 each Cluster (2–7 tags) matches 37–78 games. Hidden, removed and below-minimum tags are never Cluster members, so only visible members can match, by construction.
- **Game set**: every game in the Network State (after the Minimum Months Filter) that has at least one of the Cluster's Tags, with no threshold and no assignment to a single Cluster. A lead line gives the breadth: "**94** of 100 games have at least one of its 18 tags".
- **Ranking**: matched-tag count, high to low, then Rank (Mean Monthly Players, most successful first). Rank is unique, so no further tie-break is needed.
- **Columns**: Rank · Name · Matched · of its tags · Tags.
  - **Matched** is "7 / 26". There is no separate percent of the Cluster's tags: it has the same denominator on every row, so it adds no information.
  - **of its tags** is matched ÷ the game's own tags in the Tag Network (hidden, removed and below-minimum tags don't count). It shows whether a game *mostly* sits in this Cluster and corrects for long tag lists. It is shown as a whole percent and never used to sort.
  - **Tags** lists the matched tags in full, wrapping, in the Members table's order (◆ Center first, then by game-set distance). It is never truncated: the real maximum is 16.
  - No AppID column (as in the tag view).
- **Placement**: a **Games** section of the Cluster Inspector, after Members and before the Connections section from [Cluster connections view](07-cluster-connections-view.md). It shows the first `GAMES_SHOWN` (10) rows, then "Show all N" in a `<details>`, the tag view's pattern. It is one escaped HTML block (`data-html`), per the Inspector performance note in `view.py`. Rows are inert.
- **One-Tag Clusters**: the same section, without the Matched and Tags columns (always "1 / 1" and the one tag), so Rank · Name · of its tags remain. The lead line reads "**N** games have its tag". "of its tags" still varies there.
- **No list** for `one_tag_pool` (not a Cluster) or for a pair view.
- **Clustering Weight**: none of these numbers depends on it (the list is the same under Lift).
- **Export**: a new additive `cluster_games.csv` in the Workbench export zip, in English. It has one row per Cluster (Multi-Tag and One-Tag; never the pool) × matching game, ordered by Cluster label and then the on-screen ranking. Its columns:
  `cluster` (str), `appid` (int), `name` (str), `rank` (int), `matched` (int), `cluster_size` (int), `network_tags` (int: the game's tags in the Tag Network), `share_of_game` (float, matched ÷ network_tags, full precision), `matched_tag_ids` (int_list, member order), `matched_tags` (str_list, matching).
  Each column is declared in `schema.py` and indexed in `guide_index` and the guide's column appendix. Open Network State… checks it like every other table (`recorded_table_hashes_match` recomputes it). Older exports without the file still open.
- **Schema version**: one shared `SCHEMA_VERSION` bump, from 3 to 4, covers both this table and the five `cluster_connections.csv` columns from [Inter-cluster measures](06-inter-cluster-measures.md).
- **Numbers on screen**: "of its tags" as a whole percent and Matched as "7 / 26". Bulgarian follows the Interface Language rule. The CSV keeps fractions.
- **Glossary**: no new CONTEXT.md term. CONTEXT.md already defines when a game **has** a Tag, and this is that relation counted over a Cluster. "Matched" and "of its tags" are explained in the guide's Inspector entry and the column appendix.
- **Tests (unit)**: for each Cluster, the list equals a brute-force count over the filtered games; the ordering is matched count high to low, then Rank. `share_of_game` uses only network tags. The pool and pairs get no rows. Each CSV row matches its on-screen row. An export with the new table round-trips through Open Network State….
- **Guide**: the Inspector entry in `02-app-controls.md` gains the Cluster's **Games** section; the export entry and the column appendix gain `cluster_games.csv`. The new strings go through the `tx` catalogue of [Translation mechanism](02-translation-mechanism.md).
- **Out of scope**: a game as a selection kind (for example, highlighting its tags on the canvas).
