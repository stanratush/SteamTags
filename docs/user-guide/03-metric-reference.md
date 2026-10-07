# Metric reference

## How to read this chapter

Every number the software computes, displays or exports is explained here, in concept order: ranking and data, then the feature analysis, then the Tag Network, its clusters and their quality, their stability, and Removal Sensitivity. The [column index](appendix-b-column-index.md) lists every column name alphabetically with a link to its entry.

Each entry opens with what the number measures and how to read it, followed by a worked example with made-up numbers. Then come the theoretical **bounds**, the **reference points and comparisons** to read it against, and one marked **Exact definition** line.

The guide never says that a value is "good", "strong" or "stable". Published rules of thumb such as "Q above 0.3" were made for other kinds of data and other procedures; [Appendix A](appendix-a-rules-of-thumb.md) lists them and explains why they do not transfer. Read every value against:

- its **bounds** (what is possible);
- its **reference points**: lift 1 and phi 0 mean independence; an ARI of 1 means identical partitions and an ARI near 0 means chance agreement; Q 0 means no better than random;
- the project's own **comparisons**: the null model (what tag frequencies alone produce), the Seed-Noise Floor (what another random seed produces) and the Eligible Pool (what the games the Top 100 was drawn from look like).

An empty cell is "n/a". Where the reason can vary, a `<metric>_status` column names it; otherwise the reason follows from other columns and is given in the entry. Citations in parentheses refer to [Appendix C](appendix-c-references.md).

## Settings that change the numbers

These are inputs, not metrics. Values are the shipped defaults.

| Setting | Default | Set in | What it changes |
|---|---|---|---|
| Snapshot collection date (Observation Window) | the latest 60 complete months | fixed per Snapshot | Every score, rank and dataset |
| Exclusion rules, rank limits, overrides, Manual Metadata Entries | see `exclusions.toml` | config, per Build | Which games enter the Top-100 Datasets and the Eligible Pools |
| `max_itemset_size`, `min_support` | 3, 10 games | `analysis.toml` | Which rows `combinations.csv` and `associations.csv` list; `min_support` also sets how many pairs are tested, and so every `bh_q` |
| Minimum Months Filter (`min_months`) | 0 (off) | app, `network.toml` | N, every `n_games` and edge `lift`, every network number. The feature analysis ignores it |
| Minimum games per tag, minimum shared games | 8, 8 | app, `network.toml` | Which tags are nodes, which edges exist, which tags are isolated |
| Hidden and removed tags | Genre Tags and the defining tag hidden | app, `network.toml` | The node set; not N or any remaining edge's `lift` |
| Clustering Weight | shared games | app, `network.toml` | The partition and every weighted network number; not the shown edge weight, thresholds, silhouette or `medoid_score` (except through the partition) |
| Algorithm, resolution γ, seed | Louvain, 1.00, config seed | app, `network.toml` | The partition and everything computed from it |
| Null-model replicates R, noise seeds K | 20, 10 | `network.toml` only | `q_null_*`, `modularity_z`; every `seed_*` value, `membership_stability`, the beyond-noise flag |
| Resolution Sweep grid | 0.50, 0.75, 1.00, 1.25, 1.50 | `network.toml`, Build only | `resolution_sweep.csv` |
| Layout and Tidy | Global, default positions | app | Node positions only, never a metric |

## Ranking and data

### Identifiers, names and lists

Columns: `appid`, `name`, `dataset`, `state_id`, `tag_id` / `tag`, `tag_ids` / `tags`, `genre_ids` / `genres`, `genre_id` / `genre`, `member_tag_ids` / `members`, `source_tag_id` / `source_tag`, `target_tag_id` / `target_tag`, `tag_id_a` / `tag_a`, `tag_id_b` / `tag_b`, `top_strength_tag_id`.

These columns identify rows. A game is identified by its Steam AppID; a tag by its Steam tag id, always paired with the tag's name; a store genre by its genre id and description. `dataset` is the dataset key (`overall`, `puzzle`, `rpg`, `strategy`, `simulation`). `state_id` identifies the Network State a network row belongs to. List columns hold `;`-separated values, and an id list always comes with the matching name list in the same order (for example `tag_ids` and `tags` in display order). Names are labels: the software matches tags on their ids, because names can change or be misspelt.

*Example.* A `top100_overall.csv` row with `tag_ids` `87918;3964` and `tags` `Farming Sim;Pixel Graphics` means the game's store page shows Farming Sim first and Pixel Graphics second.

*Bounds.* Ids are positive integers; `state_id` is 12 hexadecimal characters.

*Compare with.* Nothing: these are identities, not measurements.

**Exact definition:** `state_id` = the first 12 hex characters of SHA-256 over the canonical JSON (sorted keys, no whitespace) of the Network State key.

### Monthly Avg. Players

Columns: `avg_players`, `peak_players`, `month` in `monthly_players.csv`.

Steam Charts' figure for one game in one month: the mean number of people playing at the same moment (concurrent players), averaged over the month. Peak Players is the single highest moment of the month; it is stored but never used for ranking. It is not a count of different people and not sales. A missing month means Steam Charts did not track the game that month, not that nobody played, and it is never filled with zero. Concurrent players favour games played in long sessions or left running (idle games, Desktop Companion apps, which carry a Content Flag). `monthly_players.csv` holds exactly the months each Top-100 game's score averages, and is not published until the Steam Charts operator agrees.

*Example.* A row `2024-03, 30.0, 50` means that in March 2024 an average of 30 people were playing at any moment, and at most 50 at once.

*Bounds.* 0 upwards; no upper bound.

*Compare with.* A row with Avg. 0.00 and Peak 0 is a Placeholder Row and treated as missing (see [Placeholder Rows](#placeholder-rows)); a row with Avg. 0.00 and Peak ≥ 1 is real data.

**Exact definition:** as published in the Steam Charts monthly table; `monthly_players.csv` keeps the non-placeholder months from the Release Month on, inside the Observation Window.

### Mean Monthly Players

Column: `mean_monthly_players` in `top100_<dataset>.csv`, `ties.csv`, `exclusions.csv`.

The study's success score, one number per game: the mean of its Monthly Avg. Players over the months the game was tracked inside the 60-month Observation Window, from its Release Month on. Missing Months and Placeholder Rows are skipped, never counted as zero. No minimum number of months applies when ranking, so a recent release is averaged over its launch months, when player counts are usually highest, while a game released years earlier is judged on 60 later months. Always read it with `months_observed`. Free-to-Play Games are included (`is_free`), so a high score is not a high revenue. It is written with 6 decimals, and the ranking uses that rounded value, so the published value reproduces the rank.

*Example.* A game released in July 2026, with the window ending in September 2026, July 50,000, August 30,000 and September missing, scores (50,000 + 30,000) / 2 = 40,000 with `months_observed` 2.

*Bounds.* 0 upwards.

*Compare with.* The game's `months_observed` and `release_month`; other games in the same dataset.

**Exact definition:** mean of Monthly Avg. Players over the months m with Release Month ≤ m, m inside the Observation Window and a non-placeholder row, rounded to 6 decimals.

### Months Observed

Column: `months_observed` in `top100_<dataset>.csv`, `ties.csv`.

How many months the score averages. Close to 60 means the score covers a long stretch of the game's life; a low value means a recent release or a game Steam Charts often did not track. The number alone cannot tell the two apart. The feature-analysis report shows its distribution per dataset, and the app's Minimum Months Filter drops games below a threshold.

*Example.* Scorn's Steam Charts table has a Placeholder Row in September 2017 and real rows from October 2022 to September 2026: its Release Month is 2022-10 and, in the window October 2021 – September 2026, `months_observed` is 48.

*Bounds.* 1 to 60 for any ranked game; a game with no month in the window has no score and cannot rank.

*Compare with.* 60, the full window; the dataset's distribution in `report.html`.

**Exact definition:** the number of months used in the Mean Monthly Players mean.

### Rank and ties

Columns: `rank` in `top100_<dataset>.csv`; `position`, `mean_monthly_players`, `months_observed` in `ties.csv`.

A game's position in one Top-100 Dataset, 1 being the highest score. Ranks are ordinal: the gap between ranks 1 and 2 can be far larger than between ranks 50 and 51. A rank in one dataset is not comparable with a rank in another, since each dataset has its own Eligible Pool. The feature analysis counts every game once; it never weights a game by its rank. Games outside the 100 whose score equals rank 100's are listed in `ties.csv` with the position they take after the tie-break.

*Example.* Two games tie on score at ranks 99–100; the one with more `months_observed` takes rank 99. A third game with the same score but fewer months is listed in `ties.csv` at position 101.

*Bounds.* 1–100. Every dataset of a full Build has exactly 100 rows; a Build whose Eligible Pool is too small fails. Only a test Build may be shorter, with a warning.

*Compare with.* `ties.csv` for the cut at 100.

**Exact definition:** sort the Eligible Pool by `mean_monthly_players` descending, then `months_observed` descending, then AppID ascending; `rank` = position; ties = games after position 100 with the score of position 100.

### Release Month and store release date

Columns: `release_month`, `store_release_date` in `top100_<dataset>.csv`.

The Release Month is the first month for which Steam Charts has real data for the game. Small nonzero months before the official launch (a beta, for instance) count. The store's own release date is stored as given but never used. The two can differ: Early Access games show the 1.0 date on the store, and small pre-launch months move the Release Month earlier.

*Example.* Stardew Valley's Steam Charts table starts with 0.60 and 0.53 average players in December 2015 and January 2016, before its store date of 26 February 2016: its Release Month is 2015-12.

*Bounds.* A calendar month (`YYYY-MM`); it can fall before or inside the Observation Window.

*Compare with.* `store_release_date`; [Release-month gap](#release-month-gap).

**Exact definition:** the earliest month with a Steam Charts row that is not a Placeholder Row.

### Release-month gap

Columns: `months_apart`, `release_month`, `store_release_date` in `release_month_check.csv`.

A diagnostic list, never a rule: Top-100 games whose Release Month and store release date are more than the configured number of months apart (default 3), plus games whose store date cannot be read (empty `months_apart`). It helps to check unusual histories by hand. It is noisy for Early Access games.

*Example.* Baldur's Gate 3 has Steam Charts data from October 2020 (Early Access) and the store date 3 August 2023: `months_apart` = (2023 × 12 + 8) − (2020 × 12 + 10) = 34.

*Bounds.* Any integer; listed rows have |`months_apart`| above the threshold or an empty value.

*Compare with.* The threshold in `analysis.toml`.

**Exact definition:** `months_apart` = (year × 12 + month) of the store date − (year × 12 + month) of the Release Month; positive = the store date is later.

### Placeholder Rows

Columns: `month`, `position` in `placeholder_rows.csv`; the count in `completeness.csv`.

A Steam Charts month row with Avg. Players 0.00 and Peak Players 0 is a Placeholder Row: it is not data and is treated as if the row were absent, wherever it is. Every one in the Candidate Pool is listed so the rule's effect can be checked. `position` says where it sits relative to the game's real data rows: `leading` (before the Release Month), `interior` (between data rows) or `trailing` (after the last data row).

*Example.* Scorn's September 2017 row (0.00 / 0) is a leading Placeholder Row: it neither starts the game's history in 2017 nor lowers its score.

*Bounds.* Any month; three positions.

*Compare with.* The game's Release Month.

**Exact definition:** a month row with Avg. Players = 0.00 and Peak Players = 0.

### Store metadata

Columns: `is_free`, `app_type`, `metadata_source`, `content_flags` in `top100_<dataset>.csv`.

Facts about each game from the Steam store: `is_free` is the store's free-to-play flag, `app_type` its app type (only `game` can rank). `metadata_source` says where the tags and details come from: `store`, `manual` (a full Manual Metadata Entry for a game the store no longer provides) or `manual_tags` (a tags-only entry for a game whose store page shows no tags). Rows with `manual` or `manual_tags` depend on the researcher's sourcing; their citations are in `manual_metadata.csv`. `content_flags` lists the Content Flags the game carries; a Content Flag never removes a game.

*Example.* A row with `is_free` true, `metadata_source` store and `content_flags` `desktop_companion` is a free game whose store tags include Desktop Companion.

*Bounds.* `is_free` true / false; `metadata_source` one of three codes.

*Compare with.* `content_flags.csv` for counts per dataset.

**Exact definition:** `is_free`, `type` from `appdetails` (`l=english`); Content Flags matched by tag id anywhere in the displayed tags.

### Listing rank and the depth check

Column: `top_listing_rank` in `top100_<dataset>.csv`; the depth-check rows in `completeness.csv`.

Where the game stood in Steam Charts' "Top Games" listing, which is sorted by *current* players, on the collection date: the best rank across the listing passes. A large number for a Top-100 member means the game scores high on Mean Monthly Players but had few players at collection time, so it has declined. The depth check in `completeness.csv` (deepest and median listing rank of each dataset's members, members beyond ranks 1,000, 5,000 and 10,000) shows that declined games were caught. Empty for test-mode edge cases added outside the listing.

*Example.* A member with `top_listing_rank` 7,412 had few current players but enough earlier in the window to rank.

*Bounds.* 1 to the listing length.

*Compare with.* It is a one-day snapshot, not a success measure; do not compare it with `rank`.

**Exact definition:** minimum over listing passes of the game's row number in the `/top` listing.

### Completeness counts

Columns: `section`, `item`, `dataset`, `value`, `note` in `completeness.csv`.

One count per row, showing what the Top 100 was drawn from and why the rest did not reach it: listing rows per pass and AppIDs seen in only one pass; the Candidate Pool size; scored apps and scored apps of type `game`; unscored apps split into no month rows, only Placeholder Rows, or month rows but none in the window (plus Steam Charts 404s and skipped pages); the Placeholder Row count; exclusion counts per rule, overlapping and partitioned by primary reason; and the depth check. Large unscored counts are expected, since the listing includes demos, tools and long-dead apps.

*Example.* `scoring, unscored_only_placeholder_rows, , 37` means 37 apps in the pool have nothing but Placeholder Rows.

*Bounds.* Counts (ranks for the depth-check rows).

*Compare with.* The Candidate Pool size, which is reported, not enforced; a pool of fewer than 10,000 `game` apps is reported here and in [Known limitations](06-known-limitations.md).

**Exact definition:** counts over the Snapshot's listing pages, Steam Charts pages and the Build's exclusion evaluation.

### Exclusions and would-be ranks

Columns: `reason`, `detail`, `primary_reason`, `would_be_rank_<dataset>` in `exclusions.csv`.

One row per excluded game and matched rule, so a game matching several rules appears once per rule. Rules are evaluated in a fixed order: `store_data_unavailable`, `app_type`, `no_tags`, `adult_content`, `software_tag`, `dating_sim_tag`, `manual`. The first two stop the evaluation, because nothing else can be checked. `primary_reason` is the first match. `detail` says what matched: the app type, the tags with their display positions, the adult-content signals (Adult Only notice, content descriptor 3, the Hentai tag), or the manual reason. The would-be ranks show which excluded games would otherwise be in a Top 100, so the cost of each rule is visible.

*Example.* A farming game with Dating Sim at display position 17 is excluded by `dating_sim_tag` at the default rank limit, with `would_be_rank_overall` 1: it would otherwise top the Overall dataset. An Exclusion Override can keep it in.

*Bounds.* Would-be ranks from 1 upwards; empty when the game is outside that dataset's scope (no defining tag) or its tags are unknown (no store data).

*Compare with.* The impact report, which breaks removals down by tag and signal.

**Exact definition:** would-be rank = 1 + the number of Eligible Pool games of that dataset that rank above the game by the ranking order.

### Impact report

Columns: `rule`, `signal`, `is_primary_reason`, `rank_limit`, `position`, `excluded`, `adult_only_notice`, `content_descriptor_3`, `hentai_tag`, `rank` (impact) in the `impact_*.csv` files.

The impact report lets the researcher review each rule before the lists are frozen. `impact_removals.csv` lists every removal per rule and per tag or signal, with would-be ranks. `impact_near_misses.csv` lists exclusion tags present on a scored game beyond their rank limit (so they did not exclude it), with the tag's `position` and the `rank_limit` that applied, and whether another rule excluded the game anyway. `impact_adult_signals.csv` lists games where the Adult Only notice and content descriptor 3 disagree. `impact_unexcluded.csv` lists Top-100 members that no rule excluded but that carry content descriptor 1 or 4, a software store genre or a Content Flag.

*Example.* A near-miss row `dating_sim_tag, 9551, Dating Sim, …, 17, 10, false` means Dating Sim sits at position 17, beyond a per-tag limit of 10, so it did not exclude the game.

*Bounds.* Positions 1–20; rank limits 1–20.

*Compare with.* `exclusions.csv`; the rank-limit settings in `exclusions.toml`.

**Exact definition:** a tag counts for an exclusion rule only if its display position ≤ its rank limit (per-tag limit, else the global limit, default 20).

### Build diagnostics

Columns: `source`, `request_key`, `error` (`parse_errors.csv`); `url`, `reason`, `last_status`, `timestamp` (`skipped_apps.csv`); `kind`, `id`, `app_count`, `in_vocabulary` (`tag_vocabulary.csv`); `entry_kind`, `field`, `value`, `source_url`, `retrieved` (`manual_metadata.csv`); `steamdb_batch`, `store_tag_ids`, `steamdb_tag_ids`, `steamdb_tags`, `only_store_tag_ids`, `only_steamdb_tag_ids`, `same_tag_set` (`steamdb_crosscheck.csv`).

Files that document how the data was read rather than describing games. `skipped_apps.csv` lists the apps whose Steam Charts page kept failing to load or parse during collection: they were skipped so that collection could go on, and they have no score. `parse_errors.csv` lists every response the parsers could not read; any row fails the Build unless `--allow-parse-errors` was given, and such Builds are never published. `tag_vocabulary.csv` lists every tag and store genre seen, with how many scored apps show it and, for tags, whether the id is in the `GetTagList` snapshot. `manual_metadata.csv` copies the source and retrieval date of every field of every Manual Metadata Entry. `steamdb_crosscheck.csv` compares store tags with SteamDB tags per game when a permitted SteamDB batch exists; SteamDB values never enter a dataset.

*Example.* A `tag_vocabulary.csv` row `tag, 19, Action, 812, true` means 812 scored apps show the Action tag.

*Bounds.* Counts and codes.

*Compare with.* `build.json`, which records the vocabulary `version_hash` and any warnings.

**Exact definition:** as described per file in [What's in each file](04-files.md).

## Feature analysis

Every table here uses the **full** Top-100 Dataset: the Minimum Months Filter does not apply, N = 100, and every game counts once, never weighted by its score. A game **has** a tag if the tag appears anywhere in its displayed store tag list (at most 20 tags). In the four Tag-Specific Datasets the defining tag is on every game; it is listed in the frequency table at 100% and left out of combinations, associations and clusters.

### Tag count and share

Columns: `count`, `share` in `tag_frequency.csv` and `genre_frequency.csv`.

How many of the 100 games have the tag, and that as a share. This is the most direct answer to "which tags recur among the games with the highest Mean Monthly Players?". Generic tags such as Singleplayer are common in any group of games, so a high share alone does not mark the Top 100 as special; read it with the [share ratio](#share-ratio). Tags are community-voted and reflect the store page at collection time, not at release.

*Example.* A tag on 63 of the 100 games: `count` 63, `share` 0.63.

*Bounds.* `count` 1–100 (only tags on at least one game are listed); `share` 0.01–1.

*Compare with.* The Eligible Pool baseline (`baseline_share`).

**Exact definition:** `count` = games with the tag anywhere in their displayed list; `share` = `count` / number of games in the dataset.

### Median tag position

Column: `median_position` in `tag_frequency.csv`.

How prominently the tag is shown on the store pages of the games that have it. Steam shows the most-applied tags first, and only the top 20. A low value means the tag is usually near the front. For a tag on few games the median rests on very few values, and position never affects whether a game "has" the tag.

*Example.* A tag at positions 1, 2, 5 and 9 on four games has median position (2 + 5) / 2 = 3.5.

*Bounds.* 1–20.

*Compare with.* Other tags' positions in the same dataset.

**Exact definition:** median of the tag's 1-based display position over the games that have it.

### Defining tag

Column: `defining_tag` in `tag_frequency.csv`.

Marks the tag that defines a Tag-Specific Dataset (Puzzle, RPG, Strategy or Simulation). It is on every game of that dataset by construction, so it is listed at 100% and left out of combinations, associations, clusters, the Resolution Sweep and the Build's Removal Sensitivity, where it would dominate. Only the exact tag qualifies; sub-genre tags such as RTS or 4X do not.

*Example.* In the Puzzle dataset the Puzzle row has `count` 100, `share` 1.0 and `defining_tag` true.

*Bounds.* true / false.

*Compare with.* Nothing.

**Exact definition:** `defining_tag` = the tag id equals the dataset's configured defining tag id.

### Eligible Pool baseline

Columns: `baseline_count`, `baseline_share` in `tag_frequency.csv` and `genre_frequency.csv`; the Eligible Pool size in `analysis.json`.

How common the tag (or genre) is among all the games the Top 100 was drawn from: every scored, non-excluded game for Overall, and those with the defining tag for a Tag-Specific Dataset. The Top 100 itself is part of the Eligible Pool. The baseline is the share one would expect if the Top 100 looked like its pool. The pool includes many games with very few players; it is not "all of Steam".

*Example.* A tag on 840 of 4,000 Eligible Pool games has `baseline_share` 0.21.

*Bounds.* `baseline_share` 0–1; `baseline_count` ≥ `count`.

*Compare with.* `share`, through the [share ratio](#share-ratio).

**Exact definition:** `baseline_count` = Eligible Pool games with the tag; `baseline_share` = `baseline_count` / Eligible Pool size.

### Share ratio

Column: `share_ratio` in `tag_frequency.csv` and `genre_frequency.csv`.

How over- or under-represented a tag is in the Top 100 compared with its Eligible Pool: above 1 means more common among the top games. Because the Top 100 is inside its own baseline, the ratio is pulled towards 1, more so the smaller the pool, and it cannot exceed (Eligible Pool size) / 100; the report prints the pool size so this ceiling is visible. A tag on 2 Top-100 games can show a large ratio by chance; always read it with `count`. Over-representation is a description: games may share a tag because of their genre, their era or Steam's recommendation system.

*Example.* A tag on 63 of the 100 games (0.63) and on 21% of the Eligible Pool (0.21) has `share_ratio` 0.63 / 0.21 = 3.0. With an Eligible Pool of 4,000 games, no tag can exceed 40.

*Bounds.* Above 0, at most Eligible Pool size / 100; empty when `baseline_share` is 0.

*Compare with.* 1 (the same share as the pool); `count`.

**Exact definition:** `share_ratio` = `share` / `baseline_share`.

### Archived tag category

Column: `archived_category` in `tag_frequency.csv`.

An information column: the category the tag had in Steam's archived Steamworks tag table (Top-Level Genres, Genres, Sub-Genres, Visuals & Viewpoint, Themes & Moods, Features, Players, …). A few tags appear in two categories, joined with " / ". Tags added after the table was archived have none. It is never used in any calculation.

*Example.* Farming Sim → `Genres`; Base Building → `Genres / Features`.

*Bounds.* A category name or empty.

*Compare with.* Nothing.

**Exact definition:** the category list for the tag's name in the archived table (see research note 04 of the planning effort).

### Genre frequency

Columns: `genre_id`, `genre`, `kind` and the count, share and baseline columns in `genre_frequency.csv`.

The same count, share, baseline and ratio for the store's developer-assigned **Genre** field, which is distinct from tags with the same name. Every observed genre value is listed with its id; nothing is dropped. `kind` is a config label (`genre`, `business`, `software`, or `unmapped` for a value the config does not know); headline sentences in the report use `kind = genre` rows only, so labels such as Free To Play or Early Access do not headline as gameplay genres. Puzzle is not a store genre, so the Puzzle dataset shows no Puzzle genre; the report says so.

*Example.* Store genre Indie (id 23, kind `business`) on 48 of the 100 games: `count` 48.

*Bounds.* As for tags.

*Compare with.* The Eligible Pool baseline.

**Exact definition:** as [Tag count and share](#tag-count-and-share) and the following entries, over `appdetails` genre ids.

### Combination support

Columns: `size`, `support_count`, `support_share` in `combinations.csv`.

How many games have **all** tags of a combination: pairs, triples and so on up to `max_itemset_size` (default 3). Only combinations on at least `min_support` games (default 10) are listed, and a triple is dropped when its support equals that of one of its pairs, because it adds no games. Every pair of a listed triple is listed too. Two common tags have high support simply because both are common; use [lift](#combination-lift) and the association table for whether they go together more than their frequencies predict.

*Example.* 23 games have Roguelike, Action and Pixel Graphics together: `size` 3, `support_count` 23, `support_share` 0.23.

*Bounds.* `support_count` from `min_support` to 100.

*Compare with.* The member tags' counts in `tag_frequency.csv`.

**Exact definition:** `support_count` = number of games having every member tag; `support_share` = `support_count` / number of games.

### Combination lift

Column: `lift` in `combinations.csv`.

Whether the tags of a combination occur together more often than their separate frequencies predict: observed ÷ expected under independence, the "interest" of Brin, Motwani and Silverstein (1997, §3.1), extended to more than two tags as they describe. Above 1 means together more often than chance. High values tend to come from rare tags ("the cells with high interest have low counts", Brin et al. 1997, §3.1); the 10-game minimum limits this but does not remove it. A high triple lift can be inherited from one strong pair inside it; look up the pair rows, which are always listed.

*Example.* Tags A, B and C are on 60, 50 and 40 of the 100 games, and all three are on 20: lift = 20 × 100² / (60 × 50 × 40) = 1.67. For a pair on 40 games with counts 60 and 50: 40 × 100 / (60 × 50) = 1.33.

*Bounds.* 0 upwards; a pair's maximum is 100 / (larger count).

*Compare with.* 1 = independence.

**Exact definition:** `lift` = `support_count` × N^(k−1) / (product of the k member tags' counts), with N = 100 and k = `size`.

### Confidence

Columns: `confidence_a_to_b`, `confidence_b_to_a` in `combinations.csv` (pairs only).

Among games with tag A (the lower tag id), the share that also have tag B, and the reverse. "Confidence" is the standard association-rule term (Agrawal, Imieliński & Swami 1993, §2); it does not mean certainty, and "A → B" is a direction of reading, not of cause. Confidence towards a very common tag is always high, whatever the link.

*Example.* 40 games have Roguelike and 30 of them also have Action: 0.75. Action is on 70 games, so the other direction is 30 / 70 = 0.43.

*Bounds.* 0–1; empty for triples.

*Compare with.* The other tag's `share`: confidence equal to it is what independence gives.

**Exact definition:** `confidence_a_to_b` = `support_count` / count(A); `confidence_b_to_a` = `support_count` / count(B).

### Pair counts

Columns: `count_a`, `count_b`, `count_ab` in `associations.csv`.

Games with tag A, with tag B, and with both. Every pair of tags that each reach `min_support` games is listed, including pairs that never co-occur (`count_ab` = 0). These are the raw numbers behind phi, lift, Jaccard and Fisher p; check them before trusting a striking measure.

*Example.* A on 20 games, B on 30, both on 12.

*Bounds.* 0–100.

*Compare with.* The expected co-occurrence count_a × count_b / 100 (6 in the example).

**Exact definition:** counts over the dataset's games, with the defining tag excluded.

### Phi coefficient

Column: `phi` in `associations.csv` (the table is sorted by |phi|, empty values last).

The correlation between two yes/no variables, "has tag A" and "has tag B", over the 100 games. Positive means the tags co-occur more than independence predicts, negative that they tend to exclude each other. It uses all four cells of the table (both, only A, only B, neither). Its reachable maximum depends on how common each tag is: a rare tag tied to a common one looks weak. With N = 100, one or two games can move it noticeably. It is empty when either tag is on all 100 games (then the row keeps lift 1, a defined Jaccard and Fisher p 1).

*Example.* A on 20 games, B on 30, both on 12: phi = (0.12 − 0.20 × 0.30) / √(0.20 × 0.80 × 0.30 × 0.70) = 0.33. A tag on 10 games that **always** comes with a tag on 60 games reaches only phi = 0.27, its maximum.

*Bounds.* −1 to 1 in principle; for p_a ≤ p_b the maximum is √(p_a(1 − p_b) / (p_b(1 − p_a))) (Warrens 2008, §3.2, eq. 7). Dividing phi by this maximum gives Loevinger's H (Warrens 2008, Proposition 2).

*Compare with.* 0 = independence.

**Exact definition:** phi = (n₁₁n₀₀ − n₁₀n₀₁) / √(count_a (N − count_a) count_b (N − count_b)), with n the four cell counts and N = 100.

### Pair lift

Column: `lift` in `associations.csv`.

Observed ÷ expected co-occurrence for two tags. It is the same quantity as the network's lift Clustering Weight, so the table and the network agree exactly when the Minimum Months Filter is 0. Van Eck and Waltman recommend this "association strength" for normalising co-occurrence data (2009, eq. 5 and §6), up to a constant factor. Lift favours rare pairs: one extra shared game between two rare tags changes it a lot. It ignores games that have neither tag and has no direction.

*Example.* 12 × 100 / (20 × 30) = 2.0: the two tags share twice as many games as independence predicts. Two tags on 10 games each that always co-occur reach 10; a tag on 10 games that always comes with a tag on 60 reaches only 1.67.

*Bounds.* 0 up to 100 / max(count_a, count_b).

*Compare with.* 1 = independence.

**Exact definition:** `lift` = `count_ab` × N / (`count_a` × `count_b`), N = 100.

### Jaccard index

Column: `jaccard` in `associations.csv`.

The overlap of the two tags' game sets (Jaccard 1912, p. 39): 1 means exactly the same games, 0 none in common. The same quantity, as 1 − Jaccard, is the distance behind the silhouette, the medoid score and the Cluster Center, so it is worth learning once. Van Eck and Waltman class it as a set-theoretic measure that, unlike lift, does not correct for how common each tag is (2009, §3–4); its maximum is capped when the two frequencies differ.

*Example.* 12 / (20 + 30 − 12) = 0.32.

*Bounds.* 0 to min(count_a, count_b) / max(count_a, count_b), for example 0.17 for tags on 10 and 60 games.

*Compare with.* Its own maximum for the two counts.

**Exact definition:** `jaccard` = `count_ab` / (`count_a` + `count_b` − `count_ab`).

### Fisher exact p

Column: `fisher_p` in `associations.csv`.

How surprising the observed co-occurrence would be if the two tags had been placed on games independently, given how many games carry each: the two-sided Fisher exact test on the 2 × 2 table. Small means this much (or this little) co-occurrence would be unusual under independence **within these 100 games**. The Top 100 is not a random sample of anything, so p says nothing about Steam games in general. Hundreds of pairs are tested, so small p values appear by chance; read `bh_q` instead. With N = 100 the test is discrete. The study never calls a result significant.

*Example.* A on 20 games, B on 30, both on 12: p = 0.002.

*Bounds.* 0–1.

*Compare with.* `bh_q`, which accounts for the number of pairs tested.

**Exact definition:** SciPy `fisher_exact` on [[n₁₁, n₁₀], [n₀₁, n₀₀]], `alternative="two-sided"` (the probability, under independence, of tables at most as likely as the observed one).

### Benjamini-Hochberg q

Column: `bh_q` in `associations.csv`.

Each pair's p value adjusted for the number of pairs tested in that dataset, by the Benjamini–Hochberg procedure (Benjamini & Hochberg 1995, §3.1). If you kept every pair with q ≤ 0.05, the expected share of chance findings among those kept would be at most about 5%, under the method's assumptions (1995, Theorem 1). It is the project's descriptive screen for "co-occurrence unlikely under independence within this dataset". Its value depends on how many pairs were tested, which depends on `min_support`. Tag pairs share tags, so the tests are not independent; BH also controls the false discovery rate under positive regression dependency (Benjamini & Yekutieli 2001, Theorem 1.2), but tag-pair tests are not shown to satisfy it. The column is a BH-adjusted p value, not Storey's q-value.

*Example.* Four p values 0.001, 0.01, 0.03, 0.04 become q = 0.004, 0.02, 0.04, 0.04.

*Bounds.* 0–1; q ≥ p.

*Compare with.* Nothing else; never turn it into "significant / not significant".

**Exact definition:** sort the m p values ascending; q₍ᵢ₎ = min over j ≥ i of p₍ⱼ₎ m / j, capped at 1; within one dataset.

### Content Flag counts

Columns: `flag`, `rank` in `content_flags.csv`; per-flag counts in `analysis.json`.

How many Top-100 games carry each Content Flag (`desktop_companion`, `sexual_content_tag`), and which ones. A flag marks a characteristic worth reporting, such as Desktop Companion apps whose always-on use inflates concurrent players. It is never an Exclusion: flagged games are in every other analysis as normal.

*Example.* `desktop_companion: 2 games` means two Top-100 games carry the Desktop Companion tag.

*Bounds.* 0–100.

*Compare with.* The dataset size.

**Exact definition:** a game carries a flag if any of the flag's configured tags appears anywhere in its displayed tags.

## The Tag Network

The Tag Network has one node per tag and an edge between two tags when enough games have both. N is the number of games in the loaded Top-100 Dataset after the Minimum Months Filter. A tag's **game set** is the set of those games that have it. The **Jaccard distance** between two tags is 1 − the [Jaccard index](#jaccard-index) of their game sets: 0 for the same games, 1 for none in common. Silhouette, `medoid_score` and the Cluster Center use it; it does not depend on edges, thresholds or the Clustering Weight.

### Edge weight (shared games)

Columns: `shared_games`, `appids`, `is_intra_cluster`, `source_cluster`, `target_cluster` in `edges.csv`.

Shown in the app as “Shared games” (Inspector; tables and exports keep the column names).

How many games have both tags: the network's basic fact. An edge exists only if it reaches the minimum shared games (default 8). Edge thickness, the thresholds and the edge inspector always use this count, whatever the Clustering Weight. `appids` lists the games having both tags, in dataset rank order. The count is dominated by frequent tags: two tags each on 80 of 100 games share at least 60 even if unrelated, which is why clusters on the default weight tend to gather around generic tags. A missing edge does not mean "never together"; the pair may simply be below the threshold.

*Example.* Two tags shared by 12 games, with a threshold of 8: an edge of weight 12. `is_intra_cluster` is true when both ends are in the same cluster.

*Bounds.* From the minimum shared games up to the smaller tag's `n_games`.

*Compare with.* The two tags' `n_games`; the edge's lift.

**Exact definition:** `shared_games` = |G_u ∩ G_v| over the N games.

### Edge lift

Column: `lift` in `edges.csv` (the Clustering Weight in lift mode).

Shown in the app as “Lift” (Inspector; tables and exports keep the column names).

Observed ÷ expected shared games for the pair over the N games. It equals the pair lift in `associations.csv` when the Minimum Months Filter is 0. Hiding or removing tags does not change it. Edges with lift below 1 that pass the shared-games threshold are kept, with their lift as weight. Clusters found on lift answer a different question from clusters on shared games: "which tags go together more than their frequency predicts?" rather than "which tags share the most games?".

*Example.* 12 shared games, tags on 20 and 30 of N = 100: 12 × 100 / (20 × 30) = 2.0.

*Bounds.* 0 up to N / max(n_u, n_v).

*Compare with.* 1 = independence.

**Exact definition:** `lift` = `shared_games` × N / (n_u × n_v).

### Tag game count

Column: `n_games` in `nodes.csv` and `not_in_network.csv`.

Shown in the app as “Games” (Inspector; tables and exports keep the column names).

How many of the N games have the tag. It drives the edge weights and lifts. With the Minimum Months Filter at 0 it equals `count` in `tag_frequency.csv`; otherwise it can be lower. In `not_in_network.csv` it can be 0, when the filter removed every game that had the tag. N itself is `n_dataset_games` in `cluster_quality.csv`.

*Example.* A tag on 30 of the 100 games, with the filter dropping 4 of them: `n_games` 26.

*Bounds.* From the minimum games per tag up to N for a node; 0 upwards in `not_in_network.csv`.

*Compare with.* N.

**Exact definition:** `n_games` = |G_t| over the N games.

### Degree and isolated tags

Columns: `degree`, `degree_intra`, `is_isolated` in `nodes.csv`.

Shown in the app as “Links · in own cluster” (Inspector; tables and exports keep the column names).

How many other tags a tag is linked to, in the whole network and inside its own cluster, ignoring edge weights. `is_isolated` means the tag reaches the minimum games per tag but no edge reaches the minimum shared games; it stays in the network as a One-Tag Cluster. Tag networks are dense, and common tags link to almost everything, so a high degree mostly reflects frequency. Degree depends directly on the edge threshold.

*Example.* A tag with edges to 9 tags, 5 of them in its own cluster: `degree` 9, `degree_intra` 5.

*Bounds.* `degree` 0 to (nodes − 1); `degree_intra` 0 to (cluster size − 1).

*Compare with.* The number of nodes.

**Exact definition:** `degree` = number of edges at the tag; `is_isolated` = `degree` = 0.

### Strength (weighted degree)

Columns: `strength_shared`, `strength_lift`, `strength_shared_intra`, `strength_lift_intra` in `nodes.csv`.

Shown in the app as “Total shared games”, “Total lift”, “Shared games in own cluster”, “Lift in own cluster” (Inspector; tables and exports keep the column names).

The sum of a tag's edge values, on shared games and on lift, over all its edges and over the edges inside its cluster (Newman 2004, §II.A, eq. 5). Both versions are always exported, whatever the Clustering Weight; the app shows the active one first. `strength_shared` largely restates how common a tag is, and `strength_lift` is inflated by rare tags. Neither is an importance score; both are kept visible to show how frequency shapes the results.

*Example.* A tag with three edges of 20, 15 and 10 shared games: `strength_shared` 45.

*Bounds.* 0 upwards.

*Compare with.* Other tags of the same network and weight.

**Exact definition:** `strength_shared` = Σ over the tag's edges of `shared_games`; `strength_lift` = Σ `lift`; the `_intra` versions sum only edges inside the tag's cluster.

### Per-tag silhouette

Columns: `silhouette`, `silhouette_status` in `nodes.csv`.

Shown in the app as “Fit to own cluster (silhouette)” (Inspector; tables and exports keep the column names).

Whether a tag's game set is closer to the game sets of its own cluster than to those of the nearest other cluster. Near 1 means clearly closer to its own cluster, near 0 between two clusters, negative closer to another cluster on game overlap (Struyf, Hubert & Rousseeuw 1997, pp. 9–10). The clusters maximise modularity on graph weights, not silhouette, so low or negative values are expected and do not prove a cluster wrong. Jaccard distance favours tags of similar frequency: a rare tag can never be close to a very common one. One-Tag Clusters count as "other clusters" when finding the nearest cluster.

*Example.* A mean distance a = 0.60 to its own cluster and b = 0.80 to the nearest other cluster give s = (0.80 − 0.60) / 0.80 = 0.25.

*Bounds.* −1 to 1. Empty for a One-Tag Cluster member (`one_tag_cluster`; scikit-learn gives such points 0, which is left out of every mean) and for every tag when there are fewer than 2 Multi-Tag Clusters (`fewer_than_2_multi_tag_clusters`).

*Compare with.* Other members of the same cluster; 0.

**Exact definition:** s = (b − a) / max(a, b), with a = mean Jaccard distance to the other members of its cluster and b = the smallest mean Jaccard distance to the members of any other cluster (scikit-learn `silhouette_samples`, precomputed distances).

### Medoid score

Column: `medoid_score` in `nodes.csv`.

Shown in the app as “Mean game-set distance to members” (Inspector; tables and exports keep the column names).

How typical a tag's game set is of its cluster: its mean Jaccard distance to the other members. **Lower is more typical.** It is the basis of the Cluster Center. It does not depend on the Clustering Weight or the algorithm for a given partition, but it changes whenever the partition changes. In a two-tag cluster both members always have the same score.

*Example.* Distances 0.5, 0.6 and 0.7 to three fellow members give 0.6.

*Bounds.* 0–1; empty for One-Tag Clusters.

*Compare with.* The other members' scores.

**Exact definition:** `medoid_score` = mean over the other members m of (1 − |G_t ∩ G_m| / |G_t ∪ G_m|).

### Cluster Center

Columns: `is_center` (nodes); `center_tag_id`, `center`, `center_medoid_score`, `center_status` (clusters).

Shown in the app as “Cluster Center”, “Center's game-set distance” (Inspector; tables and exports keep the column names).

The most typical tag of a Multi-Tag Cluster of three or more tags: the member whose games overlap most with the other members' games, which is the medoid (Struyf, Hubert & Rousseeuw 1997, §2.1, eq. 2.1). It is drawn as ◆ with a heavier outline. It gives one tag to orient by inside a cluster; it is not the most frequent, important or central tag in any other sense, and it is not a cluster name. With near-equal scores, a tiny data change can swap the center.

*Example.* Members with scores 0.25, 0.125 and 0.125: the two at 0.125 tie; the one with more games wins, and if they have the same number of games, the lower tag id.

*Bounds.* One per cluster of 3+ tags; empty otherwise, with `center_status` `one_tag_cluster` or `two_tag_cluster`.

*Compare with.* The [top-strength tag](#top-strength-tag).

**Exact definition:** the member with the smallest `medoid_score` compared at 12 decimals; ties → more `n_games`, then lower `tag_id`.

### Top-strength tag

Columns: `top_strength_tag_id`, `top_strength_tag`, `center_is_top_strength` (clusters).

Shown in the app as “Most-linked member”, “Center is the most-linked member” (Inspector; tables and exports keep the column names).

The member with the highest intra-cluster strength on the active Clustering Weight: the frequency-driven alternative to the center, shown beside it. `center_is_top_strength` false means the most typical tag and the most strongly linked tag differ; usually the top-strength tag is then a common, generic tag. On shared games it mostly reflects frequency.

*Example.* All members have intra-cluster strength 6, but one tag is on more games: it is the top-strength tag.

*Bounds.* One per cluster of 3+ tags, as for the center.

*Compare with.* The center.

**Exact definition:** the member with the largest intra-cluster strength (active weight) compared at 12 decimals; ties → more `n_games`, then lower `tag_id`.

### Within-cluster strength z-score

Column: `within_z` in `nodes.csv`.

Shown in the app as “Prominence in own cluster (z)” (Inspector; tables and exports keep the column names).

How much more (or less) strongly a tag is tied to its own cluster than its fellow members are: its intra-cluster strength as a z-score within the cluster, on the active Clustering Weight. This is a strength-based adaptation of the within-module degree of Guimerà and Amaral (2005, eq. 3), who counted links. In a cluster of n tags the largest possible value is √(n − 1): that is reached when all members but one share the same strength (a derivation: with one value x above n − 1 equal values, the population z of x is √(n − 1)). Small clusters therefore cap the value, and **values from clusters of different sizes are not comparable**; the inspector shows the cap, for example "within-z 1.2 (max 1.7 in a 4-tag cluster)". The Guimerà–Amaral role regions are not used here (see [Appendix A](appendix-a-rules-of-thumb.md)).

*Example.* Members with intra-cluster strengths 10, 20, 30 and 40: mean 25, population SD 11.18, so the top member has z = 15 / 11.18 = 1.34; the cap for 4 tags is √3 = 1.73.

*Bounds.* −√(n − 1) to √(n − 1). Empty for One-Tag Clusters and when every member has the same intra-cluster strength (always so in a two-tag cluster).

*Compare with.* The cap √(n − 1) for the cluster's size.

**Exact definition:** `within_z` = (k_t − mean_C k) / SD_C(k) with k = intra-cluster strength on the active weight and the population SD (ddof = 0) over the members of C.

### Participation coefficient

Column: `participation` in `nodes.csv`.

Shown in the app as “Spread across clusters” (Inspector; tables and exports keep the column names).

How evenly a tag's links are spread over clusters: 0 means all its weight is inside its own cluster, higher values mean links spread over several clusters. It is a strength-based adaptation of Guimerà and Amaral's participation coefficient (2005, eq. 4), counted over every cluster including One-Tag Clusters, on the active Clustering Weight. The maximum depends on the number of clusters, so values are not comparable across Network States with different cluster counts. Generic tags linked to everything score high on shared games.

*Example.* Strength 30 to its own cluster, 10 to C2 and 10 to C3 (total 50): P = 1 − (0.6² + 0.2² + 0.2²) = 0.56.

*Bounds.* 0 up to 1 − 1/(number of clusters it could link to); empty at zero strength (isolated tags).

*Compare with.* Other tags in the same Network State.

**Exact definition:** `participation` = 1 − Σ_s (k_ts / k_t)², with k_ts the tag's strength to cluster s and k_t its total strength, both on the active weight.

### Layout positions

Columns: `x_global`, `y_global`, `x_cluster_separated`, `y_cluster_separated` in `nodes.csv`; `layout_source` in `export.json`.

Where each node is drawn. Positions are computed after, and never used by, any metric; gravity, canvas size and Tidy change only coordinates. Distance on screen is **not** a metric: two tags drawn close together may share few games. Never measure or report positions.

The **Global** layout is ForceAtlas2 (NetworkX `forceatlas2_layout`) on the **visible** network, weighted by the active Clustering Weight, with gravity and hub dissuasion. It starts from the dataset's fixed loose layout (a seeded spring layout of every tag at the loosest thresholds), so similar visible sets start alike and end up alike. Moving a threshold slider, hiding a tag or removing one does move the graph: the nodes glide to their new places. Gravity pulls tags without a visible link towards the graph, and a **clamp** then keeps every tag within the main component's reach plus one and a half label heights, so unlinked tags sit just outside it and nothing ends up far away.

The layout leaves room for every label. Each node and its label below it form one box, with the label's width taken from a fixed table of character widths at 11.5 px (the same on every machine). A **label-aware** pass pushes boxes apart until no two overlap. The layout is made for the size of the graph area the app actually has, so one unit is one screen pixel at the first fit and the first fit never zooms past 100 %. Opening or closing a panel can therefore move the graph. When the boxes do not fit at 100 %, the labels are spaced for a lower zoom (down to 0.55). A very large network, at loose thresholds, keeps that spacing and is first shown zoomed out further, with the less important labels hidden until you zoom in. A node's drawn size depends only on how many games have the tag, relative to the dataset's most frequent tag (never on which tags are visible).

The **Cluster-separated** layout gives each Multi-Tag Cluster its own region. A region's area is two and a half times its members' node-plus-label boxes (more if the members need it), and the Cluster Center sits exactly in its middle. Inside, the members are laid out the Global way (ForceAtlas2 from their Global positions, the clamp and the label-aware pass). One-Tag Clusters share one grid region whose cells are as wide as its longest label. The regions are **packed** in rows, aimed at the shape of the graph area. This layout needs about twice the room of the Global one, so in a small graph area it is shown zoomed out and some labels stay hidden until you zoom in.

**Tidy** settles the Global layout from what you see. It re-runs ForceAtlas2, the clamp and the label-aware pass from the current positions, and the nodes you dragged stay exactly where you dropped them. Its result depends on what you dragged, so an export made after Tidy records `layout_source` = `relayout`. Dragged positions on their own are never exported.

Exports are laid out for a fixed **reference canvas**, the graph area of a 1440 × 900 window with the Tables and the Inspector closed (1,116 × 678 pixels), so the same state exports the same coordinates on every machine; the app draws the same layout for its own graph area, so what you see can differ from the exported coordinates. An export made after Tidy (or after the older Re-layout) reopens with its positions kept in shape, scaled into the reference canvas, clamped and spaced for their labels.

*Example.* Two exports of the same state with the default layout have identical positions. Exporting it with 10 times the gravity changes only these four columns: every other byte of the export is the same.

*Bounds.* Model units: one unit is one pixel at the zoom the labels are spaced for.

*Compare with.* Nothing.

**Exact definition:** Global = `forceatlas2_layout(visible network, weight = active weight scaled to at most 1, gravity = 1, distributed_action = true, 100 iterations)` started from the loose layout (`spring_layout(weight = active weight, seed = seed)` at minimum games 1 and minimum shared games 1, scaled by 1,000), scaled to 70 % of the canvas (at most 1.6 times stretched per axis), clamped per axis to the main component's half-extent plus 1.5 × 15 pixels, then the label-aware pass: boxes as wide as max(node diameter, label width) and as tall as the node diameter plus 2 + 15 pixels for the label, kept 2 pixels apart, at the highest zoom from 1 down to 0.55 that fits the canvas. Node diameter = 18 + 30 × √(`n_games` / largest `n_games` of the dataset). Cluster-separated: per Multi-Tag Cluster, a square of side √(2.5 × the members' box area) around the Cluster Center (larger if the members need it), members by the same ForceAtlas2, clamp and label-aware pass from their Global positions; one-tag grid; shelf-packed rows aimed at the canvas aspect. Exports use the 1,116 × 678 reference canvas.

### Tags not in the network

Columns: `reasons` (with `tag_id`, `tag`, `n_games`) in `not_in_network.csv`.

Every tag on at least one game of the loaded dataset that is not a node, with every reason why, so that nothing disappears unexplained. Reasons appear in a fixed order: `removed` (removed in the app), `defining_tag_hidden`, `genre_tag_hidden`, `below_min_games`. A tag below the threshold can still be very common in another dataset; check the frequency table.

*Example.* The Puzzle tag in the Puzzle dataset: `defining_tag_hidden;genre_tag_hidden` (it is both the defining tag and a Genre Tag).

*Bounds.* One to four reasons.

*Compare with.* `tag_frequency.csv`.

**Exact definition:** a tag is a node if it has at least `min_games_per_tag` of the N games and is neither hidden nor removed; every other tag of the dataset is listed.

## Clusters and partition quality

The clustering (community detection in the methods literature) splits the tags into groups that are more tightly linked inside than between. Louvain (Blondel et al. 2008) and Leiden (Traag, Waltman & van Eck 2019) both search for the split with the highest **modularity**. They are randomised searches: different seeds can give different, nearly equally good splits (Good, de Montjoye & Clauset 2010). The **partition** is the full list of which tag is in which cluster.

### Cluster labels and counts

> **In short.** Groups of tags more linked to each other than to the rest; C1 is the largest.
>
> **Higher →** more multi-tag clusters: the tags split into more, smaller groups.
>
> **Here:** each cluster is a candidate bundle of features that recurs among the most-played games.
>
> **Caution:** the count depends on γ, the thresholds and the seed; one-tag clusters are usually isolated tags, not findings.

Columns: `cluster`, `kind`, `size`, `member_tag_ids` / `members` (clusters and nodes); `n_multi_tag_clusters`, `n_one_tag_clusters` (cluster quality).

Shown in the app as “Cluster” (Inspector; tables and exports keep the column names).

Clusters are labelled `C1`, `C2`, … by size, largest first, never named. `kind` is `multi_tag` (two or more tags) or `one_tag`. Counts are always reported as "k multi-tag + s one-tag", never as one total; One-Tag Clusters are usually isolated tags, not a finding. Members are listed by medoid score. k depends heavily on γ, the thresholds and the seed. Modularity cannot reliably separate groups smaller than a scale set by the network's total weight (the resolution limit; Fortunato & Barthélemy 2007, abstract and §IV), so small groups can be merged into bigger clusters.

*Why it matters here.* A Multi-Tag Cluster is the study's unit of "a recurring combination of characteristics": tags that the most-played games of the dataset tend to carry together. Read a cluster through its members and its Cluster Center, not through its label: `C1` only means "largest in this Network State", and the same group of tags can be `C2` after a small change. Before treating a cluster as a finding, check that it survives other seeds (Membership Stability, the Seed-Noise Floor) and other γ values (the Resolution Sweep).

*Example.* "5 multi-tag + 3 one-tag": five clusters of two or more tags and three single tags.

*Bounds.* k ≥ 0, s ≥ 0; sizes ≥ 1.

*Compare with.* `seed_k_min`–`seed_k_max` and the [Resolution Sweep](#resolution-sweep).

**Exact definition:** labels by size descending, ties by the smallest member `tag_id`; Multi-Tag Clusters first, then One-Tag Clusters by `tag_id`.

### Network size

> **In short.** How big the network is: the games it is built from, the tags shown as nodes, and the links between tags that share enough games.
>
> **Higher →** more tags and links: a denser network, usually from looser thresholds.
>
> **Here:** shows how much of the dataset and its tags the clusters describe.
>
> **Caution:** most other numbers shift with size; compare states of similar size.

Columns: `n_dataset_games`, `n_nodes`, `n_edges`, `total_weight` in `cluster_quality.csv`.

Shown in the app as “Games”, “Tags”, “Links” (summary row above the graph).

Context for every other number: N (games after the Minimum Months Filter), the number of tags and edges, and the sum of the active Clustering Weight over all edges. Denser networks behave differently (see the null model). `total_weight` is in shared games or in summed lift, depending on the Clustering Weight, and the two are not comparable.

*Why it matters here.* Every pattern the network shows is a pattern among these N games and these tags only. "100 of 100" games means the whole Top-100 Dataset is in the network; a lower N (from the Minimum Months Filter) means the clusters describe only the games tracked long enough. Tags below the minimum games per tag are left out entirely, so a characteristic shared by only a handful of successful games cannot appear in any cluster; the Not in network table lists them.

*Example.* 100 games, 54 tags, 312 edges, total weight 4,120 shared games.

*Bounds.* Counts; `total_weight` ≥ 0.

*Compare with.* `null_n_edges_mean` for the edge count.

**Exact definition:** `total_weight` = Σ over edges of the active weight.

### Modularity Q

> **In short.** How much more of the link weight falls inside clusters than a random split would put there.
>
> **Higher →** clusters more separated from each other; 0 = no better than random.
>
> **Here:** the clustering's own score; read it through its excess over the null model.
>
> **Caution:** random networks also reach high Q; not comparable across γ, weights, thresholds or datasets.

Columns: `modularity`, `modularity_status` in `cluster_quality.csv`.

Shown in the app as “Q” (summary row and Cluster quality).

How much more of the network's weight falls inside clusters than would be expected if links were spread at random while keeping each tag's total strength (Newman & Girvan 2004; weighted form, Newman 2004, §II.C). It is the objective the clustering maximises, reported at the γ that was optimised ("Q (γ = 1.00)"). Random networks with no real groups also reach high Q (Guimerà, Sales-Pardo & Amaral 2004), which is why the null model exists; many different partitions reach almost the same Q; and Q is not comparable across γ, Clustering Weights, thresholds or datasets. The only published Steam tag network found reports Q = 0.414 after pruning the five most common tags and 0.150 with them kept (Li & Zhang 2020, §5.2): context for how much near-universal tags lower Q, not a benchmark, since its network was built differently.

*Why it matters here.* Q says how clearly the tags of these successful games fall into separate groups, but on its own it cannot tell real feature bundles from the groups that tag popularity alone would produce. That is why the app always shows it with its excess over the null model: "Q 0.42 · excess +0.11" means the null model already reaches about 0.31, and only the remaining 0.11 is structure that tag frequencies do not explain. Use Q to compare states that differ only in the seed or the algorithm, never across datasets.

*Example.* Total weight 100, two clusters each with 40 inside and 20 between them: each cluster's summed strength is 2 × 40 + 20 = 100, so Q = 2 × (40 / 100 − (100 / 200)²) = 0.30.

*Bounds.* At γ = 1 on an unweighted network, −½ to 1 (Brandes et al. 2008, Lemma 3.1); the reachable maximum is below 1 and depends on the network (Fortunato & Barthélemy 2007, §III). Isolated tags add nothing. Empty when the network has no edges (`modularity_status` `no_edges`).

*Compare with.* 0 = no better than random (Newman & Girvan 2004, §IV); the [null model](#null-model-baseline) (`q_null_mean`); the Seed-Noise Floor ([`seed_modularity_sd`](#seed-spread-of-modularity-and-silhouette)).

**Exact definition:** Q = Σ_c [ L_c / m − γ (d_c / 2m)² ], with L_c the active weight inside cluster c, d_c the summed strength of its members and m the total weight (NetworkX `modularity`).

### Null-model baseline

> **In short.** The Q the same procedure reaches when each game's tags are shuffled, keeping how common every tag is.
>
> **Higher →** tag popularity alone already produces much of the clustering.
>
> **Here:** separates how features combine in successful games from the fact that some tags are everywhere.
>
> **Caution:** the SD from 20 shuffles is rough; shuffled networks differ in link count.

Columns: `q_null_mean`, `q_null_sd`, `null_n_edges_mean` (cluster quality); `replicate`, `seed`, `modularity`, `n_edges` in `null_model.csv`.

The Q this pipeline produces when the link between games and tags is scrambled, keeping how many tags each game has and how many games each tag has. It answers "how much Q would tag frequencies alone produce?". This matters most with the default shared-games weight, where frequency alone creates structure. The shuffled networks are rebuilt with the same thresholds, so they usually have a different number of edges from the real one, and Q depends on density (Guimerà, Sales-Pardo & Amaral 2004): compare `null_n_edges_mean` with `n_edges`. Twenty replicates give only a rough SD.

*Why it matters here.* Tags such as Singleplayer or Indie appear on a large share of the games, so they share many games with almost every other tag, and that alone creates groups. The null model keeps every tag exactly as common as it is and every game with as many tags as it has, but pairs them at random. Whatever Q the shuffled networks still reach is what popularity explains; only Q above it says something about which features successful games combine.

*Example.* "null 0.31 ± 0.01 … null networks average 640 edges vs 702": the scrambled networks reach Q 0.31 on average, with a sample SD of 0.01, and have fewer edges than the real one.

*Bounds.* Like Q.

*Compare with.* The real Q, through the [excess](#excess-modularity-and-z-score).

**Exact definition:** R times (default 20): curveball trades (10 per game) on the game–tag table of the N games restricted to the network's tags (Strona et al. 2014), preserving every row and column total; rebuild with the same thresholds; recluster with the same algorithm, γ and weight, using the replicate's seed; record Q. `q_null_sd` is the sample SD (ddof = 1). Replicate seeds derive from the main seed through their own stream.

### Excess modularity and z-score

> **In short.** Q minus the null-model mean: the part of the clustering not explained by how common tags are.
>
> **Higher →** more structure than tag frequencies alone produce; 0 = none beyond them.
>
> **Here:** the main check that clusters reflect how features combine, not just popularity.
>
> **Caution:** the z-score can be large for a modest excess; never read it alone.

Columns: `q_excess`, `modularity_z` in `cluster_quality.csv`.

Shown in the app as “excess” (summary row) and “Null-model excess” (Cluster quality).

`q_excess` is the part of Q not explained by tag frequencies: Q minus the null-model mean. `modularity_z` expresses the same gap in null-model SDs. The z-score is never shown alone: with a small null SD, z can be very large even when the excess is modest, it is not a p value, and z-scores of modularity against random graphs have "a number of problems" (Karrer, Levina & Newman 2008, §I). The app and the report always show it inside the full line "Q … vs null … ± … (excess …, z …; null networks average … edges vs …)".

*Why it matters here.* The excess is the most direct answer to "do these successful games combine features in recognisable groups, beyond popular tags being everywhere?". An excess near 0 means the clusters could be an artefact of tag popularity; a clearly positive excess means the grouping carries information about how the games combine features. It still says nothing about which cluster is meaningful: for that, read the clusters themselves and their stability.

*Example.* Q 0.32, null 0.20 ± 0.01: excess 0.12, z = 0.12 / 0.01 = 12.

*Bounds.* `q_excess` from about −1.5 to 1.5; `modularity_z` any real number, empty when the null SD is 0.

*Compare with.* 0 (no more structure than frequencies produce); the Seed-Noise Floor's `seed_modularity_sd`.

**Exact definition:** `q_excess` = Q − `q_null_mean`; `modularity_z` = (Q − `q_null_mean`) / `q_null_sd`.

### Coverage and inter-cluster weight share

Columns: `coverage`, `inter_cluster_weight_share` in `cluster_quality.csv`.

The share of the total weight on edges inside clusters, and the rest. These are weighted analogues of Fortunato's coverage, which counts edges (2010, §III.C.2); the inter-cluster share is Kannan, Vempala and Vetta's ε (2004, Def. 2.1). Coverage rises as clusters get fewer and bigger, and a single cluster has coverage 1, so never read it alone.

*Example.* 80 of 100 units of weight inside clusters: coverage 0.80, inter-cluster share 0.20.

*Bounds.* 0–1; the two sum to 1. Empty when the network has no edges.

*Compare with.* Q, which corrects for what a random split would capture.

**Exact definition:** `coverage` = (active weight on intra-cluster edges) / (total weight); `inter_cluster_weight_share` = 1 − `coverage`.

### Disconnected clusters

Columns: `connected` (clusters); `n_disconnected_clusters` (cluster quality).

Whether a cluster's tags can all reach each other through edges inside the cluster. `false` means the cluster is two or more separate pieces under one label. Louvain can return such clusters (Traag, Waltman & van Eck 2019, abstract); for unweighted networks some best-modularity partition always has connected clusters (Brandes et al. 2008, Lemma 3.4), so a disconnected cluster is a known Louvain defect, not a finding. The software flags it and never splits it; the app suggests the Leiden mode, which guarantees connected clusters.

*Example.* A cluster of six tags in two groups of three with no edge between them: `connected` false.

*Bounds.* `n_disconnected_clusters` ≥ 0; always 0 under Leiden.

*Compare with.* The same state under Leiden.

**Exact definition:** `connected` = the subgraph induced by the cluster's tags is connected (a one-tag cluster is connected).

### Mean silhouette

> **In short.** Whether each tag's games overlap more with its own cluster than with the nearest other; descriptive diagnostic, not a selection criterion.
>
> **Higher →** clearer separation on game overlap; 0 = between clusters; below 0 = closer to another.
>
> **Here:** an independent check using the games themselves, not link weights.
>
> **Caution:** the clustering does not optimise it, so low values are expected.

Columns: `mean_silhouette`, `silhouette_status` in `cluster_quality.csv` (over every Multi-Tag Cluster member) and `clusters.csv` (over one cluster's members).

Shown in the app as “Silhouette” (summary row and Cluster quality).

The average of the per-tag silhouettes: an independent check on the clustering that uses game overlap instead of graph weights. It is labelled "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion". One-Tag Cluster members are left out of every mean, and the overall value averages tags, not clusters, so big clusters weigh more. Comparing values across Network States is only indicative.

*Why it matters here.* Clusters are found from link weights; the silhouette asks a different question of the same result: do the games that carry a cluster's tags really overlap more with each other than with the games of the next cluster? A value near 0 is common here, because many successful games carry tags from several clusters at once (an open-world RPG with crafting and survival tags, for example). Use it to compare clusters with each other or one state with a close variant, not as a pass mark.

*Example.* Three members with silhouettes 0.6875, 0.875 and 0.875 have a mean of 0.8125.

*Bounds.* −1 to 1. Empty with fewer than 2 Multi-Tag Clusters (`fewer_than_2_multi_tag_clusters`) and for One-Tag Clusters in `clusters.csv` (`one_tag_cluster`).

*Compare with.* 0; `seed_silhouette_sd`.

**Exact definition:** mean of `silhouette` over the members of the Multi-Tag Clusters concerned.

### Internal edges, weight and densities

Columns: `internal_edges`, `internal_weight`, `edge_density`, `weighted_density` in `clusters.csv`.

How tightly linked a cluster is inside. For a cluster of n tags there are n(n − 1)/2 possible pairs. Edge density is the share of those pairs that are linked; weighted density is the average active weight per possible pair, missing edges counting as 0. These are weighted analogues of Fortunato's intra-cluster density (2010, §III.B.1, eq. 1), which counts edges. Small clusters reach high density easily, and weighted density is in the units of the active Clustering Weight.

*Example.* 5 tags with 8 of their 10 possible edges and a total internal weight of 120: edge density 0.8, weighted density 12.

*Bounds.* Edge density 0–1; weighted density 0 upwards. Both empty for one-tag clusters (no pairs).

*Compare with.* The same cluster's conductance.

**Exact definition:** `edge_density` = `internal_edges` / (n(n − 1)/2); `weighted_density` = `internal_weight` / (n(n − 1)/2).

### Cut weight and conductance

Columns: `cut_weight`, `conductance`, `conductance_status` in `clusters.csv`.

Shown in the app as “Boundary crossing (conductance)” (Inspector; tables and exports keep the column names).

How much of a cluster's weight leaks to the rest of the network. The cut weight is the active weight of edges with one end inside the cluster and one outside. Conductance divides it by the smaller of the cluster's volume (its members' total strength) and the rest's volume (Fortunato 2010, eq. 20; Kannan, Vempala & Vetta 2004, §2). Low means well separated. On shared games, clusters holding very common tags leak a lot simply because common tags link to everything.

*Example.* Cut 20, cluster volume 100, rest volume 100: conductance 0.20. A tag left alone by the algorithm but linked to other clusters has conductance 1.0.

*Bounds.* 0–1. Empty with `conductance_status` `isolated_tag` (the cluster's volume is 0) or `no_edges_outside_cluster` (the rest's volume is 0).

*Compare with.* Other clusters of the same state.

**Exact definition:** conductance = cut(C) / min(vol(C), vol(V ∖ C)), vol = summed strength on the active weight.

### Cluster connections

Columns: `cluster_a`, `cluster_b`, `edge_count`, `weight` in `cluster_connections.csv`.

How many edges and how much weight join each pair of Multi-Tag Clusters, zero pairs included, plus each cluster's links to the pooled One-Tag Clusters (`one_tag_pool`). Large values mean the two clusters overlap a lot in their games. On shared games, big clusters of common tags are strongly connected to everything; compare with cluster sizes.

*Example.* `C1, C2, 7, 58`: seven edges with a total weight of 58 shared games join C1 and C2.

*Bounds.* Counts and weights ≥ 0.

*Compare with.* The clusters' `cut_weight`.

**Exact definition:** sums over the edges whose two ends lie in the two clusters (or in different One-Tag Clusters, for `one_tag_pool`).

## Stability

Every number here is shown as a plain number, with no "stable / unstable" label, colour or threshold.

### Adjusted Rand index

Columns: `seed_ari_min`, `seed_ari_mean` (cluster quality); `noise_seed_index`, `seed`, `ari_vs_main` in `seed_noise.csv`.

How similar two partitions of the same tags are, corrected for the agreement expected by chance (Meilă 2007, §2.1, eq. 6). Here each of K = 10 extra seeds' partitions is compared with the shown (main-seed) partition: this is the **Seed-Noise Floor**. If another seed gives clearly different clusters, single-cluster findings should be held loosely. ARI drops faster in small networks, and it does not say which tags moved (see [Membership Stability](#membership-stability)). K = 10 is a sample of seeds, not all of them.

*Example.* 50 tags in 5 clusters of 10. Moving 1 tag to another cluster: ARI 0.95; moving 2: 0.90; moving 4 into the same other cluster: 0.83; merging two clusters: 0.77. With only 12 tags in 2 clusters, moving 1 tag gives 0.66.

*Bounds.* −0.5 to 1 (scikit-learn); a network with no edges gives every seed the same partition, so all values are 1.

*Compare with.* 1 = identical partitions; about 0 = no more agreement than random labels.

**Exact definition:** `ari_vs_main` = scikit-learn `adjusted_rand_score` between a noise seed's labels and the main partition's labels over the network's tags; `seed_ari_min` / `seed_ari_mean` = minimum / mean over the K noise seeds. Noise seeds derive from the main seed through a stream separate from the null-model seeds; the two never share a seed.

### Seed spread of modularity and silhouette

Columns: `seed_modularity_sd`, `seed_silhouette_sd`, `seed_silhouette_status` (cluster quality); `modularity`, `silhouette`, `silhouette_status` in `seed_noise.csv`.

How much Q and the mean silhouette vary across the K extra seeds on the unchanged network. A small SD means the seeds find equally good partitions, which may still differ (see ARI). It is the yardstick for whether a change in Q, for example a Removal Sensitivity ΔQ, is larger than seed noise. An SD from 10 values is itself rough, and Leiden often gives an SD of 0.

*Example.* Seed Q values spread with sample SD 0.004: "SD Q 0.004" in the Seed-Noise Floor line.

*Bounds.* 0 upwards. `seed_silhouette_sd` is empty when fewer than 2 seeds have a silhouette (`fewer_than_2_seeds_with_silhouette`).

*Compare with.* Removal Sensitivity's ΔQ and Δsilhouette.

**Exact definition:** sample SD (ddof = 1) of the seeds' Q, and of the seeds' mean silhouettes over the seeds that have one.

### Seed range of cluster counts

Columns: `seed_k_min`, `seed_k_max` (cluster quality); `n_multi_tag_clusters`, `n_one_tag_clusters` in `seed_noise.csv`.

The lowest and highest number of Multi-Tag Clusters across the K extra seeds: the most intuitive sign of seed dependence. The count can stay the same while membership changes, so read it with ARI.

*Example.* "multi-tag clusters 5–7": some seeds split or merge clusters.

*Bounds.* Integers ≥ 0.

*Compare with.* The shown partition's `n_multi_tag_clusters`.

**Exact definition:** minimum and maximum over the noise seeds of the number of clusters with 2+ tags.

### Membership Stability

Columns: `membership_stability` (nodes); `mean_membership_stability` (clusters).

Shown in the app as “Membership Stability”, “Mean Membership Stability” (Inspector; tables and exports keep the column names).

How consistently a tag lands with the same other tags across the K extra seeds: 1 means its cluster never changed. A cluster's value is the mean over its members. It explains a low seed ARI by showing which tags move. Cluster size matters: losing one companion costs a member of a two-tag cluster 0.5 but a member of a twenty-tag cluster only 0.05. It is descriptive only: it does not say whether a tag or cluster is real or important. A related published measure, Hennig's cluster-wise Jaccard stability, comes from a different procedure (see Appendix A).

*Example.* Main cluster {T, a, b, c}. In 8 seeds T's cluster is the same (1.0); in 2 seeds it is {T, a, b} (3/4 = 0.75). Membership Stability = (8 × 1.0 + 2 × 0.75) / 10 = 0.95.

*Bounds.* Above 0 up to 1. Empty for every isolated tag (`degree` 0), which is always alone and so carries no information, and so also for its One-Tag Cluster's mean. Empty values sort last.

*Compare with.* 1; the Seed-Noise Floor's ARI.

**Exact definition:** `membership_stability` = mean over noise seeds of |A ∩ B| / |A ∪ B|, where A and B are the tag's cluster (including the tag) in the main partition and in the seed's partition.

### Resolution Sweep

Columns: `resolution`, `ari_vs_report` and the counts, modularity, silhouette and seed ARIs in `resolution_sweep.csv` (Build only).

How the feature-analysis report's clustering changes when only γ changes: the clustering is repeated at each γ of a fixed grid (default 0.50–1.50; the report's γ is always a row), with everything else held at the report's settings, so the node set is identical across rows. If cluster counts and `ari_vs_report` change a lot over the grid, the cluster structure depends on the chosen resolution; compare `ari_vs_report` with `seed_ari_min` at the same γ to see whether the change exceeds seed noise. This makes visible that "the" clusters are one view among several (Fortunato & Barthélemy 2007; Good et al. 2010). The `modularity` column is Q at that row's γ: **values in different rows must not be compared**.

*Example.* "Between γ = 0.50 and 1.50 the number of multi-tag clusters ranged from 3 to 9; agreement with the γ = 1.00 partition ranged from 0.61 to 1.00 (ARI)."

*Bounds.* As the individual metrics; `ari_vs_report` is 1 in the report's own row.

*Compare with.* `seed_ari_min` in the same row.

**Exact definition:** for each γ in the grid (plus the config γ): cluster with the main seed, compute Q at that γ, the mean silhouette, ARI against the report's partition, and ARI of each noise seed against that γ's partition (min and mean).

## Removal Sensitivity

For each tag, the software asks "what if this tag were not in the network?" twice, without touching the network you are looking at:

- **reclustered** (`rc_` columns): drop the tag and its edges, then recluster from scratch with the same settings and the main seed. It answers "does the partition depend on this tag?";
- **fixed partition** (`fp_` columns): drop the tag but keep everyone else in their cluster. It answers "how much does this tag add to the quality of this partition?". No randomness is involved.

Comparisons use all tags except the removed one. Every Δ is after removal − before. Removal Sensitivity describes how much the clustering depends on a tag; it never measures a tag's importance or effect on games. Read it against the Seed-Noise Floor.

### Run order and identity

Columns: `run_order`, `active_strength` (with `tag_id`, `tag`, `cluster`, `is_center`) in `removal_sensitivity.csv`.

Which tag the row is about, and its strength on the active Clustering Weight. Tags are processed by active strength, highest first, then by tag id, so a cancelled or partial run has covered the most strongly linked tags and is a prefix of the full run. The run order is not a ranking of anything.

*Example.* `run_order` 1 is the tag with the largest active strength.

*Bounds.* 1 to the number of tags tested.

*Compare with.* Nothing.

**Exact definition:** order by `active_strength` descending, then `tag_id` ascending.

### Reclustered change in modularity

Column: `rc_delta_modularity`.

Shown in the app as “Change in Q (reclustered)” (Inspector; tables and exports keep the column names).

Q of the reclustered network without the tag, minus Q of the current state. Removing a tag also removes its edges, so the total weight drops: part of ΔQ is this mechanical change, not reorganisation. Compare it with `fp_delta_modularity`, which has no reclustering, and with `seed_modularity_sd`. It carries no flag.

*Example.* Q 0.42 before and 0.40 after: Δ = −0.02.

*Bounds.* Roughly −1 to 1, usually small; empty when either Q is empty.

*Compare with.* `seed_modularity_sd`; `fp_delta_modularity`.

**Exact definition:** `rc_delta_modularity` = Q(reclustered network without the tag) − Q(current state).

### Reclustered silhouette

Columns: `rc_silhouette_after`, `rc_silhouette_after_status`, `rc_delta_silhouette`.

Shown in the app as “Silhouette after removal (reclustered)” (Inspector; tables and exports keep the column names).

The mean silhouette after reclustering, and its change. Removing a tag also removes its own silhouette from the mean and changes its neighbours' distances to clusters, so some change happens even if no tag moves. If the silhouette moves between a value and n/a, the Δ is empty and the app shows, for example, "0.21 → n/a" with the reason.

*Example.* 0.21 before, 0.24 after: Δ = +0.03.

*Bounds.* As the mean silhouette; Δ in −2 to 2 in theory, small in practice.

*Compare with.* `seed_silhouette_sd`.

**Exact definition:** `rc_delta_silhouette` = mean silhouette(reclustered) − mean silhouette(current); empty if either is n/a.

### Reclustered change in cluster counts

Columns: `rc_delta_k` (Multi-Tag Clusters), `rc_delta_s` (One-Tag Clusters).

Shown in the app as “Change in multi-tag · one-tag clusters” (Inspector; tables and exports keep the column names).

How many clusters appear or disappear after reclustering. Δk = −1 with Δs = +1 can simply mean the tag was one of a two-tag cluster, leaving its partner alone: a mechanical change, not reorganisation. Removing an isolated tag gives Δs = −1. No noise flag; check `seed_k_min`–`seed_k_max`.

*Example.* A bridge tag whose removal splits its cluster in two: Δk = +1.

*Bounds.* Integers.

*Compare with.* The seed range of cluster counts.

**Exact definition:** after − before, for the number of clusters with 2+ tags and with 1 tag.

### Reclustered ARI

Column: `rc_ari`.

Shown in the app as “Agreement after removal (ARI, reclustered)” (Inspector; tables and exports keep the column names).

How similar the reclustered partition is to the current one, over the remaining tags: 1 means nobody moved, lower means the partition reorganised without this tag. The Removal sensitivity table's default sort puts the lowest first. Removing a tag also changes the order in which the algorithm visits tags, so part of a low ARI can be seed-like noise; read it against `seed_ari_min`.

*Example.* A bridge tag tying two groups into one cluster: without it the cluster splits and `rc_ari` = 0.

*Bounds.* −0.5 to 1.

*Compare with.* `seed_ari_min`, through the [beyond-noise flag](#beyond-noise-flag).

**Exact definition:** `rc_ari` = `adjusted_rand_score` between the current and the reclustered labels over every tag except the removed one.

### Centers lost

Columns: `rc_centers_lost_tag_ids`, `rc_centers_lost`.

Shown in the app as “Cluster Centers lost” (Inspector; tables and exports keep the column names).

Current Cluster Centers, other than the removed tag, that are no longer centers after reclustering. A center is also lost when its cluster shrinks below three tags, which can be mechanical, and centers with near-tied medoid scores swap easily.

*Example.* Removing a tag splits a 6-tag cluster whose center lands in a 2-tag piece: that center is lost.

*Bounds.* 0 up to the number of centers.

*Compare with.* The cluster's members' medoid scores.

**Exact definition:** current centers ∖ {removed tag} ∖ centers of the reclustered partition.

### Fixed-partition change in modularity

Column: `fp_delta_modularity`.

Shown in the app as “Change in Q (clusters kept)” (Inspector; tables and exports keep the column names).

Q without the tag, everyone else kept in their cluster, minus the current Q. Negative means the tag added to the partition's quality; positive means Q is higher without it (the tag fitted its cluster poorly). It is deterministic, but it includes the same weight-loss effect as the reclustered reading. No flag.

*Example.* Q 0.42 before, 0.43 with the tag dropped and the partition fixed: Δ = +0.01.

*Bounds.* Roughly −1 to 1; empty when either Q is empty.

*Compare with.* `rc_delta_modularity`.

**Exact definition:** `fp_delta_modularity` = Q(network without the tag, other tags in their current clusters) − Q(current state).

### Fixed-partition silhouette

Columns: `fp_silhouette_after`, `fp_silhouette_after_status`, `fp_delta_silhouette`.

Shown in the app as “Silhouette after removal (clusters kept)” (Inspector; tables and exports keep the column names).

The mean silhouette without the tag, partition fixed, and its change. A positive Δ means the tag was pulling the mean down: it fitted its cluster poorly on game overlap. Removing a member of a two-tag cluster can leave fewer than two Multi-Tag Clusters, and then the silhouette after is n/a and the Δ empty.

*Example.* 0.21 before, 0.19 after: Δ = −0.02.

*Bounds.* As the mean silhouette.

*Compare with.* `seed_silhouette_sd`.

**Exact definition:** `fp_delta_silhouette` = mean silhouette(partition fixed, tag dropped) − mean silhouette(current); empty if either is n/a.

### Beyond-noise flag

Column: `rc_ari_beyond_noise`.

Shown in the app as “Beyond seed noise” (Inspector; tables and exports keep the column names).

A screening flag, not a significance test: true when the reclustered ARI is below the lowest ARI among the K seeds of the Seed-Noise Floor, meaning that removing the tag changed the partition more than any of the extra seeds did. It narrows a long table to the tags to look at first. Only ARI is flagged: ΔQ and Δsilhouette always contain the mechanical effect of losing the tag's edges, so they stay plain numbers beside `seed_modularity_sd` and `seed_silhouette_sd`. When every seed agrees (`seed_ari_min` = 1), any removal that moves a tag is flagged, which is correct, because seed noise is then zero. Some flags are expected by chance: if a removal acted only like one more random seed, its ARI would fall below the lowest of K seed ARIs about 1 time in K + 1, so the app and the report state "if removals acted only like another seed, at most about n / (K + 1) would be".

*Example.* 50 tags tested with K = 10: "7 of 50 tags flagged; if removals acted only like another seed, at most about 5 would be".

*Bounds.* true / false.

*Compare with.* n / (K + 1), the expected chance count.

**Exact definition:** `rc_ari_beyond_noise` = `rc_ari` < `seed_ari_min`.
