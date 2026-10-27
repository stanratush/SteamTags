# Metric reference

## How to read this chapter

Every number the software computes, displays or exports is explained here, in concept order: ranking and data, then the feature analysis, then the Tag Network, its clusters and their quality, their stability, and Removal Sensitivity. The [column index](appendix-b-column-index.md) lists every column name alphabetically with a link to its entry.

Every entry opens with an **In short** block, which the app shows as the tooltip where it displays the number: what the number is, which direction is which (**Higher →** or **Lower →**), why it is useful in this study (**Here:**) and the main **Caution:**. Each entry then says what the number measures and how to read it, and a *Why it matters here.* paragraph gives its use in this study of the most-played games. A worked example with made-up numbers follows. Then come the theoretical **bounds**, the **reference points and comparisons** to read it against, and one marked **Exact definition** line.

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

> **In short.** Columns that identify a row: a game's AppID, a tag's or genre's id with its name, the dataset, and the Network State's `state_id`.
>
> **Here:** lets every number be traced to the exact game, tag and Network State it describes.
>
> **Caution:** names are labels and can change; the software matches on ids.

Columns: `appid`, `name`, `dataset`, `state_id`, `tag_id` / `tag`, `tag_ids` / `tags`, `genre_ids` / `genres`, `genre_id` / `genre`, `member_tag_ids` / `members`, `source_tag_id` / `source_tag`, `target_tag_id` / `target_tag`, `tag_id_a` / `tag_a`, `tag_id_b` / `tag_b`, `top_strength_tag_id`.

These columns identify rows. A game is identified by its Steam AppID; a tag by its Steam tag id, always paired with the tag's name; a store genre by its genre id and description. `dataset` is the dataset key (`overall`, `puzzle`, `rpg`, `strategy`, `simulation`). `state_id` identifies the Network State a network row belongs to. List columns hold `;`-separated values, and an id list always comes with the matching name list in the same order (for example `tag_ids` and `tags` in display order). Names are labels: the software matches tags on their ids, because names can change or be misspelt.

*Why it matters here.* A finding about the most-played games can be checked only if each row can be traced: a tag by its id rather than its name, which can change or be misspelt, and a network number by its `state_id`. Quote ids, not only names, when a result must be reproduced.

*Example.* A `top100_overall.csv` row with `tag_ids` `87918;3964` and `tags` `Farming Sim;Pixel Graphics` means the game's store page shows Farming Sim first and Pixel Graphics second.

*Bounds.* Ids are positive integers; `state_id` is 12 hexadecimal characters.

*Compare with.* Nothing: these are identities, not measurements.

**Exact definition:** `state_id` = the first 12 hex characters of SHA-256 over the canonical JSON (sorted keys, no whitespace) of the Network State key.

### Monthly Avg. Players

> **In short.** Steam Charts' figure for one month: how many people played a game at the same moment, averaged over the month.
>
> **Higher →** more people playing at once.
>
> **Here:** the monthly figure behind Mean Monthly Players, the score that selects the most-played games.
>
> **Caution:** concurrent players, not different people or sales; long or idle sessions count more.

Columns: `avg_players`, `peak_players`, `month` in `monthly_players.csv`.

Steam Charts' figure for one game in one month: the mean number of people playing at the same moment (concurrent players), averaged over the month. Peak Players is the single highest moment of the month; it is stored but never used for ranking. It is not a count of different people and not sales. A missing month means Steam Charts did not track the game that month, not that nobody played, and it is never filled with zero. Concurrent players favour games played in long sessions or left running (idle games, Desktop Companion apps, which carry a Content Flag). `monthly_players.csv` holds exactly the months each Top-100 game's score averages, and is not published until the Steam Charts operator agrees.

*Why it matters here.* Every Top-100 Dataset rests on these monthly figures, so what they measure sets what "most-played" means in this study: how many people play at once, not how many own or buy a game. Games played in long sessions or left running, such as Desktop Companion apps, score higher on this measure than their number of players suggests; the Content Flags mark them.

*Example.* A row `2024-03, 30.0, 50` means that in March 2024 an average of 30 people were playing at any moment, and at most 50 at once.

*Bounds.* 0 upwards; no upper bound.

*Compare with.* A row with Avg. 0.00 and Peak 0 is a Placeholder Row and treated as missing (see [Placeholder Rows](#placeholder-rows)); a row with Avg. 0.00 and Peak ≥ 1 is real data.

**Exact definition:** as published in the Steam Charts monthly table; `monthly_players.csv` keeps the non-placeholder months from the Release Month on, inside the Observation Window.

### Mean Monthly Players

> **In short.** The score that ranks games: the mean of a game's Monthly Avg. Players over its observed months in the Observation Window.
>
> **Higher →** more people playing at once, on average.
>
> **Here:** decides which games are the most-played ones in each Top-100 Dataset.
>
> **Caution:** recent releases are averaged over their launch months, when counts are usually highest; read it with Months Observed.

Column: `mean_monthly_players` in `top100_<dataset>.csv`, `ties.csv`, `exclusions.csv`.

The study's success score, one number per game: the mean of its Monthly Avg. Players over the months the game was tracked inside the 60-month Observation Window, from its Release Month on. Missing Months and Placeholder Rows are skipped, never counted as zero. No minimum number of months applies when ranking, so a recent release is averaged over its launch months, when player counts are usually highest, while a game released years earlier is judged on 60 later months. Always read it with `months_observed`. Free-to-Play Games are included (`is_free`), so a high score is not a high revenue. It is written with 6 decimals, and the ranking uses that rounded value, so the published value reproduces the rank.

*Why it matters here.* Everything else in the study describes the games this score selects. It favours games that keep many concurrent players over the years and, because no minimum number of months applies, also recent releases measured on their busiest months. Free-to-Play Games are included, so a high score says how many people play, not how much a game earns.

*Example.* A game released in July 2026, with the window ending in September 2026, July 50,000, August 30,000 and September missing, scores (50,000 + 30,000) / 2 = 40,000 with `months_observed` 2.

*Bounds.* 0 upwards.

*Compare with.* The game's `months_observed` and `release_month`; other games in the same dataset.

**Exact definition:** mean of Monthly Avg. Players over the months m with Release Month ≤ m, m inside the Observation Window and a non-placeholder row, rounded to 6 decimals.

### Months Observed

> **In short.** How many months a game's Mean Monthly Players averages, out of the 60-month Observation Window.
>
> **Higher →** the score covers more of the game's life; 60 = the whole window.
>
> **Here:** tells a long-running game from a recent release whose score rests on a few months.
>
> **Caution:** a low value can also come from months Steam Charts did not track.

Column: `months_observed` in `top100_<dataset>.csv`, `ties.csv`.

How many months the score averages. Close to 60 means the score covers a long stretch of the game's life; a low value means a recent release or a game Steam Charts often did not track. The number alone cannot tell the two apart. The feature-analysis report shows its distribution per dataset, and the app's Minimum Months Filter drops games below a threshold.

*Why it matters here.* The most-played games include both long-running titles and recent releases. Months Observed shows which is which, and the app's Minimum Months Filter uses it to check whether a pattern holds among the games with a long player record.

*Example.* Scorn's Steam Charts table has a Placeholder Row in September 2017 and real rows from October 2022 to September 2026: its Release Month is 2022-10 and, in the window October 2021 – September 2026, `months_observed` is 48.

*Bounds.* 1 to 60 for any ranked game; a game with no month in the window has no score and cannot rank.

*Compare with.* 60, the full window; the dataset's distribution in `report.html`.

**Exact definition:** the number of months used in the Mean Monthly Players mean.

### Rank and ties

> **In short.** A game's position in one Top-100 Dataset by Mean Monthly Players; 1 is the highest.
>
> **Lower →** a higher score in that dataset.
>
> **Here:** decides which games are among the most-played; ties at rank 100 are listed so the cut is visible.
>
> **Caution:** ranks are ordinal and not comparable across datasets; the feature analysis never weights games by rank.

Columns: `rank` in `top100_<dataset>.csv`; `position`, `mean_monthly_players`, `months_observed` in `ties.csv`.

A game's position in one Top-100 Dataset, 1 being the highest score. Ranks are ordinal: the gap between ranks 1 and 2 can be far larger than between ranks 50 and 51. A rank in one dataset is not comparable with a rank in another, since each dataset has its own Eligible Pool. The feature analysis counts every game once; it never weights a game by its rank. Games outside the 100 whose score equals rank 100's are listed in `ties.csv` with the position they take after the tie-break.

*Why it matters here.* The study treats the Top 100 as a group: every game counts once, whatever its rank. The rank matters for who is in the group, which is why games tied with rank 100 are listed in `ties.csv` with the tie-break that decided them.

*Example.* Two games tie on score at ranks 99–100; the one with more `months_observed` takes rank 99. A third game with the same score but fewer months is listed in `ties.csv` at position 101.

*Bounds.* 1–100. Every dataset of a full Build has exactly 100 rows; a Build whose Eligible Pool is too small fails. Only a test Build may be shorter, with a warning.

*Compare with.* `ties.csv` for the cut at 100.

**Exact definition:** sort the Eligible Pool by `mean_monthly_players` descending, then `months_observed` descending, then AppID ascending; `rank` = position; ties = games after position 100 with the score of position 100.

### Release Month and store release date

> **In short.** The first month Steam Charts has real data for a game, beside the store's own release date, which is stored but not used.
>
> **Here:** sets where a game's score starts, and so how many months it averages.
>
> **Caution:** pre-launch and Early Access months move it earlier than the store date.

Columns: `release_month`, `store_release_date` in `top100_<dataset>.csv`.

The Release Month is the first month for which Steam Charts has real data for the game. Small nonzero months before the official launch (a beta, for instance) count. The store's own release date is stored as given but never used. The two can differ: Early Access games show the 1.0 date on the store, and small pre-launch months move the Release Month earlier.

*Why it matters here.* A game's score averages its months from the Release Month on, so this month decides whether its launch months fall inside the Observation Window. Early Access and beta months count, which is why it can differ from the store date by years, as for Baldur's Gate 3.

*Example.* Stardew Valley's Steam Charts table starts with 0.60 and 0.53 average players in December 2015 and January 2016, before its store date of 26 February 2016: its Release Month is 2015-12.

*Bounds.* A calendar month (`YYYY-MM`); it can fall before or inside the Observation Window.

*Compare with.* `store_release_date`; [Release-month gap](#release-month-gap).

**Exact definition:** the earliest month with a Steam Charts row that is not a Placeholder Row.

### Release-month gap

> **In short.** Top-100 games whose Release Month and store release date are more than a set number of months apart (default 3).
>
> **Here:** points to unusual histories worth checking by hand before a game's score is used.
>
> **Caution:** a diagnostic list, not a rule; noisy for Early Access games.

Columns: `months_apart`, `release_month`, `store_release_date` in `release_month_check.csv`.

A diagnostic list, never a rule: Top-100 games whose Release Month and store release date are more than the configured number of months apart (default 3), plus games whose store date cannot be read (empty `months_apart`). It helps to check unusual histories by hand. It is noisy for Early Access games.

*Why it matters here.* Large gaps usually mean Early Access or a long beta, so the score includes months before the official launch. Checking the listed games confirms that each score covers the history the researcher expects.

*Example.* Baldur's Gate 3 has Steam Charts data from October 2020 (Early Access) and the store date 3 August 2023: `months_apart` = (2023 × 12 + 8) − (2020 × 12 + 10) = 34.

*Bounds.* Any integer; listed rows have |`months_apart`| above the threshold or an empty value.

*Compare with.* The threshold in `analysis.toml`.

**Exact definition:** `months_apart` = (year × 12 + month) of the store date − (year × 12 + month) of the Release Month; positive = the store date is later.

### Placeholder Rows

> **In short.** Steam Charts month rows with 0.00 average and 0 peak players, which are not data and are treated as absent.
>
> **Here:** keeps empty rows from starting a game's history early or pulling its score down.
>
> **Caution:** a row with 0.00 average but a peak of 1 or more is real data and counts.

Columns: `month`, `position` in `placeholder_rows.csv`; the count in `completeness.csv`.

A Steam Charts month row with Avg. Players 0.00 and Peak Players 0 is a Placeholder Row: it is not data and is treated as if the row were absent, wherever it is. Every one in the Candidate Pool is listed so the rule's effect can be checked. `position` says where it sits relative to the game's real data rows: `leading` (before the Release Month), `interior` (between data rows) or `trailing` (after the last data row).

*Why it matters here.* Without this rule, an empty row years before launch would start a game's history in the wrong month and add zeros to its mean. Every Placeholder Row is listed, so the rule's effect on the most-played games can be checked.

*Example.* Scorn's September 2017 row (0.00 / 0) is a leading Placeholder Row: it neither starts the game's history in 2017 nor lowers its score.

*Bounds.* Any month; three positions.

*Compare with.* The game's Release Month.

**Exact definition:** a month row with Avg. Players = 0.00 and Peak Players = 0.

### Store metadata

> **In short.** Facts from the Steam store: the free-to-play flag, the app type, where the tags come from, and the game's Content Flags.
>
> **Here:** shows which of the most-played games are free to play and whose tags come from manual entries.
>
> **Caution:** manual and tags-only entries rest on the researcher's sourcing; check `manual_metadata.csv`.

Columns: `is_free`, `app_type`, `metadata_source`, `content_flags` in `top100_<dataset>.csv`.

Facts about each game from the Steam store: `is_free` is the store's free-to-play flag, `app_type` its app type (only `game` can rank). `metadata_source` says where the tags and details come from: `store`, `manual` (a full Manual Metadata Entry for a game the store no longer provides) or `manual_tags` (a tags-only entry for a game whose store page shows no tags). Rows with `manual` or `manual_tags` depend on the researcher's sourcing; their citations are in `manual_metadata.csv`. `content_flags` lists the Content Flags the game carries; a Content Flag never removes a game.

*Why it matters here.* Free-to-Play Games are part of the study, so a high score is not a high revenue; `is_free` lets them be told apart. Tags from a Manual Metadata Entry are cited in `manual_metadata.csv`, so any finding that depends on such a game can be traced to its source.

*Example.* A row with `is_free` true, `metadata_source` store and `content_flags` `desktop_companion` is a free game whose store tags include Desktop Companion.

*Bounds.* `is_free` true / false; `metadata_source` one of three codes.

*Compare with.* `content_flags.csv` for counts per dataset.

**Exact definition:** `is_free`, `type` from `appdetails` (`l=english`); Content Flags matched by tag id anywhere in the displayed tags.

### Listing rank and the depth check

> **In short.** Where a game stood in Steam Charts' Top Games listing, by current players, on the collection date.
>
> **Higher →** fewer current players: the game has declined since its busiest months.
>
> **Here:** the depth check shows that declined games were still found and scored.
>
> **Caution:** a one-day snapshot, not a score; never compare it with the rank.

Column: `top_listing_rank` in `top100_<dataset>.csv`; the depth-check rows in `completeness.csv`.

Where the game stood in Steam Charts' "Top Games" listing, which is sorted by *current* players, on the collection date: the best rank across the listing passes. A large number for a Top-100 member means the game scores high on Mean Monthly Players but had few players at collection time, so it has declined. The depth check in `completeness.csv` (deepest and median listing rank of each dataset's members, members beyond ranks 1,000, 5,000 and 10,000) shows that declined games were caught. Empty for test-mode edge cases added outside the listing.

*Why it matters here.* The Top 100 is chosen by mean players over five years, not by who is playing today. Members found far down the current listing show that the collection reached deep enough to include games that were among the most-played earlier in the Observation Window and have since declined.

*Example.* A member with `top_listing_rank` 7,412 had few current players but enough earlier in the window to rank.

*Bounds.* 1 to the listing length.

*Compare with.* It is a one-day snapshot, not a success measure; do not compare it with `rank`.

**Exact definition:** minimum over listing passes of the game's row number in the `/top` listing.

### Completeness counts

> **In short.** One count per row: how many apps were listed, scored and excluded, and why the rest did not reach the Top 100.
>
> **Here:** shows what the most-played games were drawn from and that no large group was lost on the way.
>
> **Caution:** large unscored counts are expected: the listing includes demos, tools and long-dead apps.

Columns: `section`, `item`, `dataset`, `value`, `note` in `completeness.csv`.

One count per row, showing what the Top 100 was drawn from and why the rest did not reach it: listing rows per pass and AppIDs seen in only one pass; the Candidate Pool size; scored apps and scored apps of type `game`; unscored apps split into no month rows, only Placeholder Rows, or month rows but none in the window (plus Steam Charts 404s and skipped pages); the Placeholder Row count; exclusion counts per rule, overlapping and partitioned by primary reason; and the depth check. Large unscored counts are expected, since the listing includes demos, tools and long-dead apps.

*Why it matters here.* A Top-100 Dataset is only as complete as the pool it was drawn from. These counts show how big that pool was, how many apps could not be scored and why, and how many each exclusion rule removed, so the coverage of the study can be reported.

*Example.* `scoring, unscored_only_placeholder_rows, , 37` means 37 apps in the pool have nothing but Placeholder Rows.

*Bounds.* Counts (ranks for the depth-check rows).

*Compare with.* The Candidate Pool size, which is reported, not enforced; a pool of fewer than 10,000 `game` apps is reported here and in [Known limitations](06-known-limitations.md).

**Exact definition:** counts over the Snapshot's listing pages, Steam Charts pages and the Build's exclusion evaluation.

### Exclusions and would-be ranks

> **In short.** One row per excluded game and matched rule, with the rank the game would otherwise have had in each dataset.
>
> **Here:** shows what each exclusion rule costs: which of the most-played games it keeps out.
>
> **Caution:** a game matching several rules appears once per rule; its primary reason is the first match.

Columns: `reason`, `detail`, `primary_reason`, `would_be_rank_<dataset>` in `exclusions.csv`.

One row per excluded game and matched rule, so a game matching several rules appears once per rule. Rules are evaluated in a fixed order: `store_data_unavailable`, `app_type`, `no_tags`, `adult_content`, `software_tag`, `dating_sim_tag`, `manual`. The first two stop the evaluation, because nothing else can be checked. `primary_reason` is the first match. `detail` says what matched: the app type, the tags with their display positions, the adult-content signals (Adult Only notice, content descriptor 3, the Hentai tag), or the manual reason. The would-be ranks show which excluded games would otherwise be in a Top 100, so the cost of each rule is visible.

*Why it matters here.* Exclusions decide which apps count as commercial games for this study. The would-be ranks make each decision visible: a rule that removes a game at rank 1 changes the Top 100 far more than one that removes games far below it, and an Exclusion Override can keep a game in.

*Example.* A farming game with Dating Sim at display position 17 is excluded by `dating_sim_tag` at the default rank limit, with `would_be_rank_overall` 1: it would otherwise top the Overall dataset. An Exclusion Override can keep it in.

*Bounds.* Would-be ranks from 1 upwards; empty when the game is outside that dataset's scope (no defining tag) or its tags are unknown (no store data).

*Compare with.* The impact report, which breaks removals down by tag and signal.

**Exact definition:** would-be rank = 1 + the number of Eligible Pool games of that dataset that rank above the game by the ranking order.

### Impact report

> **In short.** Tables for reviewing each exclusion rule before the datasets are frozen: removals, near misses, disagreeing adult-content signals and borderline games no rule removed.
>
> **Here:** lets the researcher check that the rules keep out what they should and nothing more.
>
> **Caution:** a tag counts for a rule only within its rank limit; near misses show where that limit cuts.

Columns: `rule`, `signal`, `is_primary_reason`, `rank_limit`, `position`, `excluded`, `adult_only_notice`, `content_descriptor_3`, `hentai_tag`, `rank` (impact) in the `impact_*.csv` files.

The impact report lets the researcher review each rule before the lists are frozen. `impact_removals.csv` lists every removal per rule and per tag or signal, with would-be ranks. `impact_near_misses.csv` lists exclusion tags present on a scored game beyond their rank limit (so they did not exclude it), with the tag's `position` and the `rank_limit` that applied, and whether another rule excluded the game anyway. `impact_adult_signals.csv` lists games where the Adult Only notice and content descriptor 3 disagree. `impact_unexcluded.csv` lists Top-100 members that no rule excluded but that carry content descriptor 1 or 4, a software store genre or a Content Flag.

*Why it matters here.* The exclusion rules shape which games are in the study, and tag-based rules can misfire. The impact report shows each rule's effect from both sides, the games it removed and the ones it nearly removed, so the researcher can adjust rank limits or add an Exclusion Override with the evidence in hand.

*Example.* A near-miss row `dating_sim_tag, 9551, Dating Sim, …, 17, 10, false` means Dating Sim sits at position 17, beyond a per-tag limit of 10, so it did not exclude the game.

*Bounds.* Positions 1–20; rank limits 1–20.

*Compare with.* `exclusions.csv`; the rank-limit settings in `exclusions.toml`.

**Exact definition:** a tag counts for an exclusion rule only if its display position ≤ its rank limit (per-tag limit, else the global limit, default 20).

### Build diagnostics

> **In short.** Files that document how the data was read: skipped apps, parse errors, the tag vocabulary, Manual Metadata sources and the SteamDB cross-check.
>
> **Here:** makes every gap and manual source in the data behind the most-played games traceable.
>
> **Caution:** a Build with parse errors is never published; skipped apps have no score.

Columns: `source`, `request_key`, `error` (`parse_errors.csv`); `url`, `reason`, `last_status`, `timestamp` (`skipped_apps.csv`); `kind`, `id`, `app_count`, `in_vocabulary` (`tag_vocabulary.csv`); `entry_kind`, `field`, `value`, `source_url`, `retrieved` (`manual_metadata.csv`); `steamdb_batch`, `store_tag_ids`, `steamdb_tag_ids`, `steamdb_tags`, `only_store_tag_ids`, `only_steamdb_tag_ids`, `same_tag_set` (`steamdb_crosscheck.csv`).

Files that document how the data was read rather than describing games. `skipped_apps.csv` lists the apps whose Steam Charts page kept failing to load or parse during collection: they were skipped so that collection could go on, and they have no score. `parse_errors.csv` lists every response the parsers could not read; any row fails the Build unless `--allow-parse-errors` was given, and such Builds are never published. `tag_vocabulary.csv` lists every tag and store genre seen, with how many scored apps show it and, for tags, whether the id is in the `GetTagList` snapshot. `manual_metadata.csv` copies the source and retrieval date of every field of every Manual Metadata Entry. `steamdb_crosscheck.csv` compares store tags with SteamDB tags per game when a permitted SteamDB batch exists; SteamDB values never enter a dataset.

*Why it matters here.* These files show where the data is incomplete or comes from a manual source: an app skipped during collection cannot be in any Top 100, and a tag missing from the vocabulary would point to a reading problem. They let a reviewer check that the data behind the most-played games was read in full.

*Example.* A `tag_vocabulary.csv` row `tag, 19, Action, 812, true` means 812 scored apps show the Action tag.

*Bounds.* Counts and codes.

*Compare with.* `build.json`, which records the vocabulary `version_hash` and any warnings.

**Exact definition:** as described per file in [What's in each file](04-files.md).

## Feature analysis

Every table here uses the **full** Top-100 Dataset: the Minimum Months Filter does not apply, N = 100, and every game counts once, never weighted by its score. A game **has** a tag if the tag appears anywhere in its displayed store tag list (at most 20 tags). In the four Tag-Specific Datasets the defining tag is on every game; it is listed in the frequency table at 100% and left out of combinations, associations and clusters.

### Tag count and share

> **In short.** How many of the 100 games have the tag, and that as a share.
>
> **Higher →** a characteristic that more of the most-played games carry.
>
> **Here:** the most direct answer to which characteristics recur among the most-played games.
>
> **Caution:** generic tags are common in any group of games; read it with the share ratio.

Columns: `count`, `share` in `tag_frequency.csv` and `genre_frequency.csv`.

How many of the 100 games have the tag, and that as a share. This is the most direct answer to "which tags recur among the games with the highest Mean Monthly Players?". Generic tags such as Singleplayer are common in any group of games, so a high share alone does not mark the Top 100 as special; read it with the [share ratio](#share-ratio). Tags are community-voted and reflect the store page at collection time, not at release.

*Why it matters here.* This is the plainest description of the Top 100: which characteristics most of these games carry. A share of 0.63 means 63 of the 100 games show the tag on their store page. Whether that is more than among the games they were drawn from is the share ratio's question.

*Example.* A tag on 63 of the 100 games: `count` 63, `share` 0.63.

*Bounds.* `count` 1–100 (only tags on at least one game are listed); `share` 0.01–1.

*Compare with.* The Eligible Pool baseline (`baseline_share`).

**Exact definition:** `count` = games with the tag anywhere in their displayed list; `share` = `count` / number of games in the dataset.

### Median tag position

> **In short.** Where the tag usually sits in the store tag lists of the games that have it.
>
> **Lower →** the tag is usually near the front of the list.
>
> **Here:** separates characteristics central to how players describe a game from ones listed in passing.
>
> **Caution:** rests on few values for rare tags; it never decides whether a game has the tag.

Column: `median_position` in `tag_frequency.csv`.

How prominently the tag is shown on the store pages of the games that have it. Steam shows the most-applied tags first, and only the top 20. A low value means the tag is usually near the front. For a tag on few games the median rests on very few values, and position never affects whether a game "has" the tag.

*Why it matters here.* Two tags on the same number of games can differ in how prominent they are: one near the front of most lists is a characteristic players name first, one near position 20 is mentioned in passing. Read it beside the count when describing what the most-played games are known for.

*Example.* A tag at positions 1, 2, 5 and 9 on four games has median position (2 + 5) / 2 = 3.5.

*Bounds.* 1–20.

*Compare with.* Other tags' positions in the same dataset.

**Exact definition:** median of the tag's 1-based display position over the games that have it.

### Defining tag

> **In short.** Marks the tag that defines a Tag-Specific Dataset (Puzzle, RPG, Strategy or Simulation), on every game of it by construction.
>
> **Here:** keeps the dataset's own tag from dominating combinations, associations and clusters.
>
> **Caution:** only the exact tag qualifies; sub-genre tags such as RTS or 4X do not.

Column: `defining_tag` in `tag_frequency.csv`.

Marks the tag that defines a Tag-Specific Dataset (Puzzle, RPG, Strategy or Simulation). It is on every game of that dataset by construction, so it is listed at 100% and left out of combinations, associations, clusters, the Resolution Sweep and the Build's Removal Sensitivity, where it would dominate. Only the exact tag qualifies; sub-genre tags such as RTS or 4X do not.

*Why it matters here.* In the RPG dataset every game is an RPG, so the RPG tag says nothing about which characteristics those games combine. Marking it keeps it at 100% in the frequency table and out of every analysis of combinations.

*Example.* In the Puzzle dataset the Puzzle row has `count` 100, `share` 1.0 and `defining_tag` true.

*Bounds.* true / false.

*Compare with.* Nothing.

**Exact definition:** `defining_tag` = the tag id equals the dataset's configured defining tag id.

### Eligible Pool baseline

> **In short.** How common the tag is among all the games the Top 100 was drawn from.
>
> **Here:** the reference that shows whether a characteristic is more common among the most-played games than among the games they were drawn from.
>
> **Caution:** the pool includes many games with very few players; it is not all of Steam.

Columns: `baseline_count`, `baseline_share` in `tag_frequency.csv` and `genre_frequency.csv`; the Eligible Pool size in `analysis.json`.

How common the tag (or genre) is among all the games the Top 100 was drawn from: every scored, non-excluded game for Overall, and those with the defining tag for a Tag-Specific Dataset. The Top 100 itself is part of the Eligible Pool. The baseline is the share one would expect if the Top 100 looked like its pool. The pool includes many games with very few players; it is not "all of Steam".

*Why it matters here.* A tag on 63 of the 100 games stands out only if it is less common in the pool; Singleplayer, for example, is common everywhere. The baseline gives that reference share, and the share ratio compares the two.

*Example.* A tag on 840 of 4,000 Eligible Pool games has `baseline_share` 0.21.

*Bounds.* `baseline_share` 0–1; `baseline_count` ≥ `count`.

*Compare with.* `share`, through the [share ratio](#share-ratio).

**Exact definition:** `baseline_count` = Eligible Pool games with the tag; `baseline_share` = `baseline_count` / Eligible Pool size.

### Share ratio

> **In short.** A tag's share in the Top 100 divided by its share in the Eligible Pool.
>
> **Higher →** above 1: more common among the most-played games than in their pool.
>
> **Here:** points to characteristics that set the most-played games apart from their pool.
>
> **Caution:** pulled towards 1, since the Top 100 is part of its pool; read it with the count.

Column: `share_ratio` in `tag_frequency.csv` and `genre_frequency.csv`.

How over- or under-represented a tag is in the Top 100 compared with its Eligible Pool: above 1 means more common among the top games. Because the Top 100 is inside its own baseline, the ratio is pulled towards 1, more so the smaller the pool, and it cannot exceed (Eligible Pool size) / 100; the report prints the pool size so this ceiling is visible. A tag on 2 Top-100 games can show a large ratio by chance; always read it with `count`. Over-representation is a description: games may share a tag because of their genre, their era or Steam's recommendation system.

*Why it matters here.* It is the study's main comparison for single characteristics: a share ratio of 3 means the tag is three times as common among the most-played games as among all eligible games. It describes and does not explain: games may share a tag because of their genre, their era or Steam's recommendations.

*Example.* A tag on 63 of the 100 games (0.63) and on 21% of the Eligible Pool (0.21) has `share_ratio` 0.63 / 0.21 = 3.0. With an Eligible Pool of 4,000 games, no tag can exceed 40.

*Bounds.* Above 0, at most Eligible Pool size / 100; empty when `baseline_share` is 0.

*Compare with.* 1 (the same share as the pool); `count`.

**Exact definition:** `share_ratio` = `share` / `baseline_share`.

### Archived tag category

> **In short.** The category the tag had in Steam's archived tag table, such as Genres, Themes & Moods or Features.
>
> **Here:** groups tags by kind when describing the most-played games' characteristics.
>
> **Caution:** information only, never used in a calculation; newer tags have none.

Column: `archived_category` in `tag_frequency.csv`.

An information column: the category the tag had in Steam's archived Steamworks tag table (Top-Level Genres, Genres, Sub-Genres, Visuals & Viewpoint, Themes & Moods, Features, Players, …). A few tags appear in two categories, joined with " / ". Tags added after the table was archived have none. It is never used in any calculation.

*Why it matters here.* A list of tags mixes genres, visual styles, moods and features. The archived categories let a write-up say, for example, which features rather than which genres recur among the most-played games, without the software inventing its own classification.

*Example.* Farming Sim → `Genres`; Base Building → `Genres / Features`.

*Bounds.* A category name or empty.

*Compare with.* Nothing.

**Exact definition:** the category list for the tag's name in the archived table (see research note 04 of the planning effort).

### Genre frequency

> **In short.** Count, share, baseline and share ratio for the store's developer-assigned Genre field, not the tags of the same name.
>
> **Here:** a second description of the most-played games, from what developers chose rather than what players voted.
>
> **Caution:** some values are business labels such as Free To Play or Early Access; headlines use only `kind` = genre rows.

Columns: `genre_id`, `genre`, `kind` and the count, share and baseline columns in `genre_frequency.csv`.

The same count, share, baseline and ratio for the store's developer-assigned **Genre** field, which is distinct from tags with the same name. Every observed genre value is listed with its id; nothing is dropped. `kind` is a config label (`genre`, `business`, `software`, or `unmapped` for a value the config does not know); headline sentences in the report use `kind = genre` rows only, so labels such as Free To Play or Early Access do not headline as gameplay genres. Puzzle is not a store genre, so the Puzzle dataset shows no Puzzle genre; the report says so.

*Why it matters here.* Tags are voted by players; the Genre field is set by the developer. Comparing the two shows whether both describe the most-played games the same way. The `kind` column keeps labels such as Free To Play or Early Access from being read as gameplay genres.

*Example.* Store genre Indie (id 23, kind `business`) on 48 of the 100 games: `count` 48.

*Bounds.* As for tags.

*Compare with.* The Eligible Pool baseline.

**Exact definition:** as [Tag count and share](#tag-count-and-share) and the following entries, over `appdetails` genre ids.

### Combination support

> **In short.** How many games have all tags of a combination (pairs and triples by default).
>
> **Higher →** more of the most-played games carry the whole combination.
>
> **Here:** shows which combinations of characteristics actually occur together on the same games.
>
> **Caution:** two common tags have high support just by being common; read it with the combination's lift.

Columns: `size`, `support_count`, `support_share` in `combinations.csv`.

How many games have **all** tags of a combination: pairs, triples and so on up to `max_itemset_size` (default 3). Only combinations on at least `min_support` games (default 10) are listed, and a triple is dropped when its support equals that of one of its pairs, because it adds no games. Every pair of a listed triple is listed too. Two common tags have high support simply because both are common; use [lift](#combination-lift) and the association table for whether they go together more than their frequencies predict.

*Why it matters here.* Unlike a cluster, which can join tags that only meet in pairs, a combination counts games that carry every tag at once. That makes it the direct evidence for a statement such as "23 of the 100 games are pixel-art action roguelikes".

*Example.* 23 games have Roguelike, Action and Pixel Graphics together: `size` 3, `support_count` 23, `support_share` 0.23.

*Bounds.* `support_count` from `min_support` to 100.

*Compare with.* The member tags' counts in `tag_frequency.csv`.

**Exact definition:** `support_count` = number of games having every member tag; `support_share` = `support_count` / number of games.

### Combination lift

> **In short.** How many times more often the tags of a combination occur together than their separate frequencies predict.
>
> **Higher →** above 1: together more often than chance; 1: as chance predicts.
>
> **Here:** shows combinations that go together beyond how common each tag is.
>
> **Caution:** high values come mostly from rare tags; a triple can inherit its lift from one pair inside it.

Column: `lift` in `combinations.csv`.

Whether the tags of a combination occur together more often than their separate frequencies predict: observed ÷ expected under independence, the "interest" of Brin, Motwani and Silverstein (1997, §3.1), extended to more than two tags as they describe. Above 1 means together more often than chance. High values tend to come from rare tags ("the cells with high interest have low counts", Brin et al. 1997, §3.1); the 10-game minimum limits this but does not remove it. A high triple lift can be inherited from one strong pair inside it; look up the pair rows, which are always listed.

*Why it matters here.* Support alone favours common tags. Lift corrects for that, so a combination with lift well above 1 is one the most-played games carry together more often than their frequencies would produce. Check the pair rows of a high triple before describing the triple as a combination in its own right.

*Example.* Tags A, B and C are on 60, 50 and 40 of the 100 games, and all three are on 20: lift = 20 × 100² / (60 × 50 × 40) = 1.67. For a pair on 40 games with counts 60 and 50: 40 × 100 / (60 × 50) = 1.33.

*Bounds.* 0 upwards; a pair's maximum is 100 / (larger count).

*Compare with.* 1 = independence.

**Exact definition:** `lift` = `support_count` × N^(k−1) / (product of the k member tags' counts), with N = 100 and k = `size`.

### Confidence

> **In short.** Among the games with tag A, the share that also have tag B, and the reverse.
>
> **Higher →** more of A's games also carry B.
>
> **Here:** reads a combination in one direction: how often one characteristic comes with another.
>
> **Caution:** a direction of reading, not of cause; confidence towards a very common tag is always high.

Columns: `confidence_a_to_b`, `confidence_b_to_a` in `combinations.csv` (pairs only).

Among games with tag A (the lower tag id), the share that also have tag B, and the reverse. "Confidence" is the standard association-rule term (Agrawal, Imieliński & Swami 1993, §2); it does not mean certainty, and "A → B" is a direction of reading, not of cause. Confidence towards a very common tag is always high, whatever the link.

*Why it matters here.* Confidence answers questions such as "of the most-played roguelikes, how many are also action games?". Compare it with the other tag's share: if confidence equals that share, the two tags are independent and the high value says only that the second tag is common.

*Example.* 40 games have Roguelike and 30 of them also have Action: 0.75. Action is on 70 games, so the other direction is 30 / 70 = 0.43.

*Bounds.* 0–1; empty for triples.

*Compare with.* The other tag's `share`: confidence equal to it is what independence gives.

**Exact definition:** `confidence_a_to_b` = `support_count` / count(A); `confidence_b_to_a` = `support_count` / count(B).

### Pair counts

> **In short.** How many games have tag A, tag B, and both.
>
> **Here:** the raw numbers behind phi, lift, Jaccard and Fisher p for each pair of tags.
>
> **Caution:** check them before trusting a striking measure; small counts move every measure a lot.

Columns: `count_a`, `count_b`, `count_ab` in `associations.csv`.

Games with tag A, with tag B, and with both. Every pair of tags that each reach `min_support` games is listed, including pairs that never co-occur (`count_ab` = 0). These are the raw numbers behind phi, lift, Jaccard and Fisher p; check them before trusting a striking measure.

*Why it matters here.* Every association measure is computed from these three counts and the 100 games. A lift of 5 from 2 shared games and one from 30 shared games say very different things about the most-played games; the counts show which is which.

*Example.* A on 20 games, B on 30, both on 12.

*Bounds.* 0–100.

*Compare with.* The expected co-occurrence count_a × count_b / 100 (6 in the example).

**Exact definition:** counts over the dataset's games, with the defining tag excluded.

### Phi coefficient

> **In short.** The correlation between "has tag A" and "has tag B" over the 100 games.
>
> **Higher →** above 0: together more than independence predicts; below 0: they tend to exclude each other.
>
> **Here:** a pair measure that also counts the games with neither tag.
>
> **Caution:** its maximum depends on the two frequencies, so a rare tag tied to a common one scores low.

Column: `phi` in `associations.csv` (the table is sorted by |phi|, empty values last).

The correlation between two yes/no variables, "has tag A" and "has tag B", over the 100 games. Positive means the tags co-occur more than independence predicts, negative that they tend to exclude each other. It uses all four cells of the table (both, only A, only B, neither). Its reachable maximum depends on how common each tag is: a rare tag tied to a common one looks weak. With N = 100, one or two games can move it noticeably. It is empty when either tag is on all 100 games (then the row keeps lift 1, a defined Jaccard and Fisher p 1).

*Why it matters here.* Phi is the association table's sort order, so it decides which pairs of characteristics of the most-played games come first. Because it favours pairs of similar frequency, a niche tag that always comes with a common one can rank low; read lift and Jaccard beside it.

*Example.* A on 20 games, B on 30, both on 12: phi = (0.12 − 0.20 × 0.30) / √(0.20 × 0.80 × 0.30 × 0.70) = 0.33. A tag on 10 games that **always** comes with a tag on 60 games reaches only phi = 0.27, its maximum.

*Bounds.* −1 to 1 in principle; for p_a ≤ p_b the maximum is √(p_a(1 − p_b) / (p_b(1 − p_a))) (Warrens 2008, §3.2, eq. 7). Dividing phi by this maximum gives Loevinger's H (Warrens 2008, Proposition 2).

*Compare with.* 0 = independence.

**Exact definition:** phi = (n₁₁n₀₀ − n₁₀n₀₁) / √(count_a (N − count_a) count_b (N − count_b)), with n the four cell counts and N = 100.

### Pair lift

> **In short.** Shared games divided by the number expected if the two tags were independent.
>
> **Higher →** above 1: together more often than chance; 1: as chance predicts.
>
> **Here:** the same measure as the network's lift weight, over the full Top 100.
>
> **Caution:** rare pairs change a lot with one extra shared game; it ignores games with neither tag.

Column: `lift` in `associations.csv`.

Observed ÷ expected co-occurrence for two tags. It is the same quantity as the network's lift Clustering Weight, so the table and the network agree exactly when the Minimum Months Filter is 0. Van Eck and Waltman recommend this "association strength" for normalising co-occurrence data (2009, eq. 5 and §6), up to a constant factor. Lift favours rare pairs: one extra shared game between two rare tags changes it a lot. It ignores games that have neither tag and has no direction.

*Why it matters here.* Lift is the clearest reading of "which characteristics go together more than their frequencies predict" among the most-played games, and it links the association table to the Tag Network's lift Clustering Weight. Read it with `count_ab`: a lift of 10 from two tags on 10 games each rests on those 10 games.

*Example.* 12 × 100 / (20 × 30) = 2.0: the two tags share twice as many games as independence predicts. Two tags on 10 games each that always co-occur reach 10; a tag on 10 games that always comes with a tag on 60 reaches only 1.67.

*Bounds.* 0 up to 100 / max(count_a, count_b).

*Compare with.* 1 = independence.

**Exact definition:** `lift` = `count_ab` × N / (`count_a` × `count_b`), N = 100.

### Jaccard index

> **In short.** The overlap of two tags' game sets: shared games divided by the games with either tag.
>
> **Higher →** 1: exactly the same games; 0: none in common.
>
> **Here:** the same overlap that lies behind the silhouette, the medoid score and the Cluster Center.
>
> **Caution:** does not correct for frequency; its maximum is capped when the two counts differ.

Column: `jaccard` in `associations.csv`.

The overlap of the two tags' game sets (Jaccard 1912, p. 39): 1 means exactly the same games, 0 none in common. The same quantity, as 1 − Jaccard, is the distance behind the silhouette, the medoid score and the Cluster Center, so it is worth learning once. Van Eck and Waltman class it as a set-theoretic measure that, unlike lift, does not correct for how common each tag is (2009, §3–4); its maximum is capped when the two frequencies differ.

*Why it matters here.* Jaccard is the network's measure of how alike two characteristics are in the games that carry them: 1 − Jaccard is the distance used to find each cluster's most typical tag. Learning it once explains the silhouette and the Cluster Center as well.

*Example.* 12 / (20 + 30 − 12) = 0.32.

*Bounds.* 0 to min(count_a, count_b) / max(count_a, count_b), for example 0.17 for tags on 10 and 60 games.

*Compare with.* Its own maximum for the two counts.

**Exact definition:** `jaccard` = `count_ab` / (`count_a` + `count_b` − `count_ab`).

### Fisher exact p

> **In short.** How unusual the co-occurrence would be if the two tags were placed on games independently.
>
> **Lower →** this much (or this little) co-occurrence is more unusual under independence.
>
> **Here:** a screen for pairs whose co-occurrence among these 100 games is unlikely by chance.
>
> **Caution:** hundreds of pairs are tested, so read `bh_q`; it says nothing beyond these 100 games.

Column: `fisher_p` in `associations.csv`.

How surprising the observed co-occurrence would be if the two tags had been placed on games independently, given how many games carry each: the two-sided Fisher exact test on the 2 × 2 table. Small means this much (or this little) co-occurrence would be unusual under independence **within these 100 games**. The Top 100 is not a random sample of anything, so p says nothing about Steam games in general. Hundreds of pairs are tested, so small p values appear by chance; read `bh_q` instead. With N = 100 the test is discrete. The study never calls a result significant.

*Why it matters here.* Some pairs of characteristics co-occur among the most-played games by chance. Fisher p measures how surprising each pair would be under independence within these 100 games; because the Top 100 is not a random sample, it describes this group of games and does not generalise to others.

*Example.* A on 20 games, B on 30, both on 12: p = 0.002.

*Bounds.* 0–1.

*Compare with.* `bh_q`, which accounts for the number of pairs tested.

**Exact definition:** SciPy `fisher_exact` on [[n₁₁, n₁₀], [n₀₁, n₀₀]], `alternative="two-sided"` (the probability, under independence, of tables at most as likely as the observed one).

### Benjamini-Hochberg q

> **In short.** Each pair's Fisher p adjusted for how many pairs were tested in the dataset.
>
> **Lower →** keeping pairs up to this value, at most about that share would be chance findings.
>
> **Here:** the screen for pairs of characteristics whose co-occurrence is unlikely under independence.
>
> **Caution:** depends on how many pairs were tested; never turn it into a yes/no verdict.

Column: `bh_q` in `associations.csv`.

Each pair's p value adjusted for the number of pairs tested in that dataset, by the Benjamini–Hochberg procedure (Benjamini & Hochberg 1995, §3.1). If you kept every pair with q ≤ 0.05, the expected share of chance findings among those kept would be at most about 5%, under the method's assumptions (1995, Theorem 1). It is the project's descriptive screen for "co-occurrence unlikely under independence within this dataset". Its value depends on how many pairs were tested, which depends on `min_support`. Tag pairs share tags, so the tests are not independent; BH also controls the false discovery rate under positive regression dependency (Benjamini & Yekutieli 2001, Theorem 1.2), but tag-pair tests are not shown to satisfy it. The column is a BH-adjusted p value, not Storey's q-value.

*Why it matters here.* With hundreds of tag pairs tested in each dataset, some small p values are expected by chance. The q value accounts for that, so a list of pairs with q at or below a chosen level describes the co-occurrences of the most-played games while keeping the expected share of chance findings in view.

*Example.* Four p values 0.001, 0.01, 0.03, 0.04 become q = 0.004, 0.02, 0.04, 0.04.

*Bounds.* 0–1; q ≥ p.

*Compare with.* Nothing else; never turn it into "significant / not significant".

**Exact definition:** sort the m p values ascending; q₍ᵢ₎ = min over j ≥ i of p₍ⱼ₎ m / j, capped at 1; within one dataset.

### Content Flag counts

> **In short.** How many Top-100 games carry each Content Flag, such as Desktop Companion.
>
> **Here:** reports characteristics of the most-played games that may affect their scores, without removing them.
>
> **Caution:** a flag is never an Exclusion; flagged games count in every analysis.

Columns: `flag`, `rank` in `content_flags.csv`; per-flag counts in `analysis.json`.

How many Top-100 games carry each Content Flag (`desktop_companion`, `sexual_content_tag`), and which ones. A flag marks a characteristic worth reporting, such as Desktop Companion apps whose always-on use inflates concurrent players. It is never an Exclusion: flagged games are in every other analysis as normal.

*Why it matters here.* Desktop Companion apps run in the background for hours, which inflates concurrent players and so Mean Monthly Players. Flagging such games instead of excluding them keeps them in the study while making their number visible, so a reader can judge how much they shape the results.

*Example.* `desktop_companion: 2 games` means two Top-100 games carry the Desktop Companion tag.

*Bounds.* 0–100.

*Compare with.* The dataset size.

**Exact definition:** a game carries a flag if any of the flag's configured tags appears anywhere in its displayed tags.

## The Tag Network

The Tag Network has one node per tag and an edge between two tags when enough games have both. N is the number of games in the loaded Top-100 Dataset after the Minimum Months Filter. A tag's **game set** is the set of those games that have it. The **Jaccard distance** between two tags is 1 − the [Jaccard index](#jaccard-index) of their game sets: 0 for the same games, 1 for none in common. Silhouette, `medoid_score` and the Cluster Center use it; it does not depend on edges, thresholds or the Clustering Weight.

### Edge weight (shared games)

> **In short.** How many games carry both tags.
>
> **Higher →** the two tags appear together on more of the games; a link exists only from the minimum shared games up.
>
> **Here:** the plain count behind every link: which characteristics the most-played games carry together.
>
> **Caution:** common tags share many games just by being common; read it with Lift.

Columns: `shared_games`, `appids`, `is_intra_cluster`, `source_cluster`, `target_cluster` in `edges.csv`.

Shown in the app as “Shared games” (Inspector; tables and exports keep the column names).

How many games have both tags: the network's basic fact. An edge exists only if it reaches the minimum shared games (default 8). The thresholds and the edge inspector always use this count, whatever the Clustering Weight; edge thickness shows it under the Shared games weight, or under Lift when the legend's switch asks for it. `appids` lists the games having both tags, in dataset rank order. The count is dominated by frequent tags: two tags each on 80 of 100 games share at least 60 even if unrelated, which is why clusters on the default weight tend to gather around generic tags. A missing edge does not mean "never together"; the pair may simply be below the threshold.

*Why it matters here.* Shared games is the closest the network comes to the raw data: 12 shared games means that 12 of the network's games carry both tags, and the edge inspector lists them. It answers which characteristics the most-played games actually combine, counted in games. Because a tag on most of the Top 100 shares many games with almost every other tag, a large count alone does not show that two tags belong together; the edge's lift corrects for that.

*Example.* Two tags shared by 12 games, with a threshold of 8: an edge of weight 12. `is_intra_cluster` is true when both ends are in the same cluster.

*Bounds.* From the minimum shared games up to the smaller tag's `n_games`.

*Compare with.* The two tags' `n_games`; the edge's lift.

**Exact definition:** `shared_games` = |G_u ∩ G_v| over the N games.

### Edge lift

> **In short.** Shared games divided by the number expected if the two tags were independent.
>
> **Higher →** above 1: together more often than chance; 1: as chance predicts; below 1: less often.
>
> **Here:** shows pairings these games carry more often than the two tags' frequencies predict.
>
> **Caution:** pairs of rare tags reach high values from a few games; association within these games, not a test.

Column: `lift` in `edges.csv` (the Clustering Weight in lift mode, and then what edge thickness shows).

Shown in the app as “Lift” (Inspector; tables and exports keep the column names).

Observed ÷ expected shared games for the pair over the N games. It equals the pair lift in `associations.csv` when the Minimum Months Filter is 0. Hiding or removing tags does not change it. Edges with lift below 1 that pass the shared-games threshold are kept, with their lift as weight. Clusters found on lift answer a different question from clusters on shared games: "which tags go together more than their frequency predicts?" rather than "which tags share the most games?".

*Why it matters here.* Two tags can share many games simply because both are on most of the Top 100. Lift divides that out: a lift of 2.0 means the pair occurs twice as often as the two tags' frequencies predict if they were unrelated. That makes it the closer reading of "which characteristics do the most-played games combine?" beyond popularity. Read it beside the shared-games count: a lift of 3 from 4 games rests on far fewer games than a lift of 1.5 from 30.

*Example.* 12 shared games, tags on 20 and 30 of N = 100: 12 × 100 / (20 × 30) = 2.0.

*Bounds.* 0 up to N / max(n_u, n_v).

*Compare with.* 1 = independence.

**Exact definition:** `lift` = `shared_games` × N / (n_u × n_v).

### Tag game count

> **In short.** How many of the network's games carry the tag.
>
> **Higher →** a more common characteristic among these games.
>
> **Here:** the most direct answer to how often a characteristic recurs among the most-played games.
>
> **Caution:** generic tags are common in any group of games; the share ratio in the feature analysis compares with the Eligible Pool.

Column: `n_games` in `nodes.csv` and `not_in_network.csv`.

Shown in the app as “Games” (Inspector; tables and exports keep the column names).

How many of the N games have the tag. It drives the edge weights and lifts. With the Minimum Months Filter at 0 it equals `count` in `tag_frequency.csv`; otherwise it can be lower. In `not_in_network.csv` it can be 0, when the filter removed every game that had the tag. N itself is `n_dataset_games` in `cluster_quality.csv`.

*Why it matters here.* Node size in the graph shows this count. It is the starting point for every other number of a tag: a tag on 60 of the 100 games shares games with almost every other tag, so it has many links and a high strength whatever it means for the games. Check how common a tag is before reading anything else about it; whether that frequency is unusual among the most-played games is answered by the share ratio in the feature analysis, not here.

*Example.* A tag on 30 of the 100 games, with the filter dropping 4 of them: `n_games` 26.

*Bounds.* From the minimum games per tag up to N for a node; 0 upwards in `not_in_network.csv`.

*Compare with.* N.

**Exact definition:** `n_games` = |G_t| over the N games.

### Degree and isolated tags

> **In short.** How many other tags this tag is linked to, in the whole network and inside its own cluster.
>
> **Higher →** linked to more tags; 0 = isolated, shown as a One-Tag Cluster.
>
> **Here:** shows how widely a characteristic combines with others among the most-played games.
>
> **Caution:** mostly follows how common the tag is, and depends directly on the minimum shared games.

Columns: `degree`, `degree_intra`, `is_isolated` in `nodes.csv`.

Shown in the app as “Links · in own cluster” (Inspector; tables and exports keep the column names).

How many other tags a tag is linked to, in the whole network and inside its own cluster, ignoring edge weights. `is_isolated` means the tag reaches the minimum games per tag but no edge reaches the minimum shared games; it stays in the network as a One-Tag Cluster. Tag networks are dense, and common tags link to almost everything, so a high degree mostly reflects frequency. Degree depends directly on the edge threshold.

*Why it matters here.* A tag linked to most others is usually a generic characteristic, such as Singleplayer, that appears with almost anything; a tag with few links combines with a narrow set of other characteristics. The second number shows how many of those links stay inside the tag's cluster. Degree counts links, not games: for how many games stand behind the links, read the strength.

*Example.* A tag with edges to 9 tags, 5 of them in its own cluster: `degree` 9, `degree_intra` 5.

*Bounds.* `degree` 0 to (nodes − 1); `degree_intra` 0 to (cluster size − 1).

*Compare with.* The number of nodes.

**Exact definition:** `degree` = number of edges at the tag; `is_isolated` = `degree` = 0.

### Strength (weighted degree)

> **In short.** The sum of a tag's links, in shared games or in lift, over all its links or those inside its cluster.
>
> **Higher →** more, or heavier, links to other tags.
>
> **Here:** how much of the network's weight a characteristic carries on the Clustering Weight in use.
>
> **Caution:** on shared games it largely restates how common the tag is; on lift, rare tags inflate it.

Columns: `strength_shared`, `strength_lift`, `strength_shared_intra`, `strength_lift_intra` in `nodes.csv`.

Shown in the app as “Total shared games”, “Total lift”, “Shared games in own cluster”, “Lift in own cluster” (Inspector; tables and exports keep the column names).

The sum of a tag's edge values, on shared games and on lift, over all its edges and over the edges inside its cluster (Newman 2004, §II.A, eq. 5). A game is counted once for every link it supports, so the total is not a number of games. Both versions are always exported, whatever the Clustering Weight; the app shows the active one first. `strength_shared` largely restates how common a tag is, and `strength_lift` is inflated by rare tags. Neither is an importance score; both are kept visible to show how frequency shapes the results.

*Why it matters here.* The clustering works on these weights, so strength shows how much a tag pulls on the clusters; the Inspector marks the version used for clustering. A tag with a high total but a low own-cluster strength is linked mainly to other clusters (compare Spread across clusters). Neither total says that a characteristic matters more for how many people play a game: it describes the network of tags, not the games' player numbers.

*Example.* A tag with three edges of 20, 15 and 10 shared games: `strength_shared` 45.

*Bounds.* 0 upwards.

*Compare with.* Other tags of the same network and weight.

**Exact definition:** `strength_shared` = Σ over the tag's edges of `shared_games`; `strength_lift` = Σ `lift`; the `_intra` versions sum only edges inside the tag's cluster.

### Per-tag silhouette

> **In short.** Whether the tag's games overlap more with its own cluster than with the nearest other cluster.
>
> **Higher →** near 1: clearly closer to its own cluster; 0: in between; below 0: closer to another cluster.
>
> **Here:** checks each member against the games themselves, not the link weights.
>
> **Caution:** the clustering does not optimise it; rare tags never sit close to common ones.

Columns: `silhouette`, `silhouette_status` in `nodes.csv`.

Shown in the app as “Fit to own cluster (silhouette)” (Inspector; tables and exports keep the column names).

Whether a tag's game set is closer to the game sets of its own cluster than to those of the nearest other cluster. Near 1 means clearly closer to its own cluster, near 0 between two clusters, negative closer to another cluster on game overlap (Struyf, Hubert & Rousseeuw 1997, pp. 9–10). Most tag pairs are far apart, which pulls silhouettes toward 0; low or negative values do not prove a cluster wrong. Jaccard distance favours tags of similar frequency: a rare tag can never be close to a very common one. Jaccard similarity is at most n_small / n_large, so a tag on 5 games is at least 0.92 from one on 60. One-Tag Clusters count as "other clusters" when finding the nearest cluster.

*Why it matters here.* A member with a negative value shares more games with another cluster's tags than with its own: its links placed it, but its games point elsewhere. Such tags are where a cluster's boundary is least clear, and they are the first to check before describing a cluster as a recurring combination of characteristics. Compare the members of one cluster with each other rather than across clusters.

*Example.* A mean distance a = 0.60 to its own cluster and b = 0.80 to the nearest other cluster give s = (0.80 − 0.60) / 0.80 = 0.25.

*Bounds.* −1 to 1. Empty for a One-Tag Cluster member (`one_tag_cluster`; scikit-learn gives such points 0, which is left out of every mean) and for every tag when there are fewer than 2 Multi-Tag Clusters (`fewer_than_2_multi_tag_clusters`).

*Compare with.* Other members of the same cluster; 0.

**Exact definition:** s = (b − a) / max(a, b), with a = mean Jaccard distance to the other members of its cluster and b = the smallest mean Jaccard distance to the members of any other cluster (scikit-learn `silhouette_samples`, precomputed distances).

### Medoid score

> **In short.** How different the tag's games are, on average, from the games of the other members of its cluster.
>
> **Lower →** more typical of its cluster; the lowest is the Cluster Center.
>
> **Here:** orders a cluster's members from most to least typical of the games behind it.
>
> **Caution:** changes whenever the membership changes; in a two-tag cluster both members score the same.

Column: `medoid_score` in `nodes.csv`.

Shown in the app as “Mean game-set distance to members” (Inspector; tables and exports keep the column names).

How typical a tag's game set is of its cluster: its mean Jaccard distance to the other members. **Lower is more typical.** It is the basis of the Cluster Center. It does not depend on the Clustering Weight or the algorithm for a given partition, but it changes whenever the partition changes. In a two-tag cluster both members always have the same score.

*Why it matters here.* A cluster's Members list is sorted by this score, so its first tags are the ones whose games overlap most with the rest. When describing a cluster in words, start from those tags; tags at the end of the list are on games that the other members rarely share. The score uses game overlap only: the Clustering Weight changes it only by changing the clusters.

*Example.* Distances 0.5, 0.6 and 0.7 to three fellow members give 0.6.

*Bounds.* 0–1; empty for One-Tag Clusters.

*Compare with.* The other members' scores.

**Exact definition:** `medoid_score` = mean over the other members m of (1 − |G_t ∩ G_m| / |G_t ∪ G_m|).

### Cluster Center

> **In short.** The most typical tag of a Multi-Tag Cluster of three or more tags: the member with the lowest mean game-set distance to the other members (the medoid).
>
> **Here:** gives one tag to orient by when reading a cluster of the most-played games.
>
> **Caution:** not a cluster name and not the most common tag; near-tied scores can swap it.

Columns: `is_center` (nodes); `center_tag_id`, `center`, `center_medoid_score`, `center_status` (clusters).

Shown in the app as “Cluster Center”, “Center's game-set distance” (Inspector; tables and exports keep the column names).

The most typical tag of a Multi-Tag Cluster of three or more tags: the member with the lowest mean game-set distance to the other members, which is the medoid (Struyf, Hubert & Rousseeuw 1997, §2.1, eq. 2.1). It is drawn as ◆ with a heavier outline. It gives one tag to orient by inside a cluster; it is not the most frequent, important or central tag in any other sense, and it is not a cluster name. With near-equal scores, a tiny data change can swap the center.

*Why it matters here.* A cluster of twelve tags is hard to hold in mind; the Cluster Center, drawn as ◆, gives a concrete starting point. It is chosen by game overlap rather than by links, so it tends to be a characteristic typical of the cluster's games rather than a generic tag linked to everything; the most-linked member shows that alternative. Write "the cluster around X" at most, never use the center as the cluster's name, and check its Membership Stability before building on it.

*Example.* Members with scores 0.25, 0.125 and 0.125: the two at 0.125 tie; the one with more games wins, and if they have the same number of games, the lower tag id.

*Bounds.* One per cluster of 3+ tags; empty otherwise, with `center_status` `one_tag_cluster` or `two_tag_cluster`.

*Compare with.* The [top-strength tag](#top-strength-tag).

**Exact definition:** the member with the smallest `medoid_score` compared at 12 decimals; ties → more `n_games`, then lower `tag_id`.

### Top-strength tag

> **In short.** The member with the most link weight inside its cluster, shown beside the Cluster Center.
>
> **Here:** shows whether a cluster's most typical tag is also its most linked one.
>
> **Caution:** on shared games it is usually a common, generic tag.

Columns: `top_strength_tag_id`, `top_strength_tag`, `center_is_top_strength` (clusters).

Shown in the app as “Most-linked member”, “Center is the most-linked member” (Inspector; tables and exports keep the column names).

The member with the highest intra-cluster strength on the active Clustering Weight: the frequency-driven alternative to the center, shown beside it. `center_is_top_strength` false means the most typical tag and the most strongly linked tag differ; usually the top-strength tag is then a common, generic tag. On shared games it mostly reflects frequency.

*Why it matters here.* When the Cluster Center and the most-linked member are the same tag, the cluster has one reference point. When they differ, the most-linked member is often a tag that is common across the most-played games, and so linked to everything, while the center is the member whose games are closest to the other members'. Showing both keeps a frequent tag from being mistaken for the characteristic that sets a group apart.

*Example.* All members have intra-cluster strength 6, but one tag is on more games: it is the top-strength tag.

*Bounds.* One per cluster of 3+ tags, as for the center.

*Compare with.* The center.

**Exact definition:** the member with the largest intra-cluster strength (active weight) compared at 12 decimals; ties → more `n_games`, then lower `tag_id`.

### Within-cluster strength z-score

> **In short.** How far the tag's link weight inside its cluster lies from the members' average, in standard deviations.
>
> **Higher →** above 0: more than the average member; below 0: less.
>
> **Here:** shows which members carry most of a cluster's links.
>
> **Caution:** cannot exceed √(n − 1) in a cluster of n tags; not comparable across cluster sizes.

Column: `within_z` in `nodes.csv`.

Shown in the app as “Prominence in own cluster (z)” (Inspector; tables and exports keep the column names).

How much more (or less) strongly a tag is tied to its own cluster than its fellow members are: its intra-cluster strength as a z-score within the cluster, on the active Clustering Weight. This is a strength-based adaptation of the within-module degree of Guimerà and Amaral (2005, eq. 3), who counted links. In a cluster of n tags the largest possible value is √(n − 1): that is reached when all members but one share the same strength (a derivation: with one value x above n − 1 equal values, the population z of x is √(n − 1)). Small clusters therefore cap the value, and **values from clusters of different sizes are not comparable**; the inspector shows the cap, for example "within-z 1.2 (max 1.7 in a 4-tag cluster)". The Guimerà–Amaral role regions are not used here (see [Appendix A](appendix-a-rules-of-thumb.md)).

*Why it matters here.* Inside a cluster, a few members usually hold most of the link weight. A high value marks such a member, and on shared games it is often a common tag. The Inspector shows the cap for the cluster's size beside the value, because a member of a 4-tag cluster cannot exceed 1.7: compare the members of one cluster with each other, not values from clusters of different sizes.

*Example.* Members with intra-cluster strengths 10, 20, 30 and 40: mean 25, population SD 11.18, so the top member has z = 15 / 11.18 = 1.34; the cap for 4 tags is √3 = 1.73.

*Bounds.* −√(n − 1) to √(n − 1). Empty for One-Tag Clusters and when every member has the same intra-cluster strength (always so in a two-tag cluster).

*Compare with.* The cap √(n − 1) for the cluster's size.

**Exact definition:** `within_z` = (k_t − mean_C k) / SD_C(k) with k = intra-cluster strength on the active weight and the population SD (ddof = 0) over the members of C.

### Participation coefficient

> **In short.** How evenly a tag's links are spread over the clusters.
>
> **Higher →** links spread over several clusters; 0 = all its links in a single cluster, normally its own.
>
> **Here:** finds characteristics that the most-played games combine with several different groups of tags.
>
> **Caution:** generic tags score high on shared games; the maximum depends on the number of clusters.

Column: `participation` in `nodes.csv`.

Shown in the app as “Spread across clusters” (Inspector; tables and exports keep the column names).

How evenly a tag's links are spread over clusters: 0 means all its weight is inside its own cluster, higher values mean links spread over several clusters. It is a strength-based adaptation of Guimerà and Amaral's participation coefficient (2005, eq. 4), counted over every cluster including One-Tag Clusters, on the active Clustering Weight. The maximum depends on the number of clusters, so values are not comparable across Network States with different cluster counts. Generic tags linked to everything score high on shared games.

*Why it matters here.* A tag with a high value sits between clusters: games carry it together with tags from several groups. That can mark a cross-cutting characteristic (a multiplayer tag, for example, can go with many kinds of game) or simply a very common tag. A tag near 0 belongs to one group. Compare values within one Network State only.

*Example.* Strength 30 to its own cluster, 10 to C2 and 10 to C3 (total 50): P = 1 − (0.6² + 0.2² + 0.2²) = 0.56.

*Bounds.* 0 up to 1 − 1/(number of clusters it could link to); empty at zero strength (isolated tags).

*Compare with.* Other tags in the same Network State.

**Exact definition:** `participation` = 1 − Σ_s (k_ts / k_t)², with k_ts the tag's strength to cluster s and k_t its total strength, both on the active weight.

### Layout positions

> **In short.** Where each tag is drawn; computed after, and never used by, any metric.
>
> **Here:** a map for finding the most-played games' characteristics and their clusters.
>
> **Caution:** distance on screen is not a metric; never measure or report positions.

Columns: `x_global`, `y_global`, `x_cluster_separated`, `y_cluster_separated` in `nodes.csv`; `layout_source` in `export.json`.

Where each node is drawn. Positions are computed after, and never used by, any metric; gravity, canvas size and Tidy change only coordinates. Distance on screen is **not** a metric: two tags drawn close together may share few games. Never measure or report positions.

The **Global** layout is ForceAtlas2 (NetworkX `forceatlas2_layout`) on the **visible** network, weighted by the active Clustering Weight, with gravity and hub dissuasion. It starts from the dataset's fixed loose layout (a seeded spring layout of every tag at the loosest thresholds), so similar visible sets start alike and end up alike. Moving a threshold slider, hiding a tag or removing one does move the graph: the nodes glide to their new places. Gravity pulls tags without a visible link towards the graph, and a **clamp** then keeps every tag within the main component's reach plus one and a half label heights, so unlinked tags sit just outside it and nothing ends up far away.

The layout leaves room for every label. Each node and its label below it form one box, with the label's width taken from a fixed table of character widths at 11.5 px (the same on every machine). A **label-aware** pass pushes boxes apart until no two overlap. The layout is made for the size of the graph area the app actually has, so one unit is one screen pixel at the first fit and the first fit never zooms past 100 %. Opening or closing a panel can therefore move the graph. When the boxes do not fit at 100 %, the labels are spaced for a lower zoom (down to 0.55). A very large network, at loose thresholds, keeps that spacing and is first shown zoomed out further, with the less important labels hidden until you zoom in. A node's drawn size depends only on how many games have the tag, relative to the dataset's most frequent tag (never on which tags are visible).

The **Cluster-separated** layout gives each Multi-Tag Cluster its own region. A region's area is two and a half times its members' node-plus-label boxes (more if the members need it), and the Cluster Center sits exactly in its middle. Inside, the members are laid out the Global way (ForceAtlas2 from their Global positions, the clamp and the label-aware pass). One-Tag Clusters share one grid region whose cells are as wide as its longest label. The regions are **packed** in rows, aimed at the shape of the graph area. This layout needs about twice the room of the Global one, so in a small graph area it is shown zoomed out and some labels stay hidden until you zoom in.

**Tidy** settles the Global layout from what you see. It re-runs ForceAtlas2, the clamp and the label-aware pass from the current positions, and the nodes you dragged stay exactly where you dropped them. Its result depends on what you dragged, so an export made after Tidy records `layout_source` = `relayout`. Dragged positions on their own are never exported.

Exports are laid out for a fixed **reference canvas**, the graph area of a 1440 × 900 window with the Tables and the Inspector closed (1,116 × 678 pixels), so the same state exports the same coordinates on every machine; the app draws the same layout for its own graph area, so what you see can differ from the exported coordinates. An export made after Tidy (or after the older Re-layout) reopens with its positions kept in shape, scaled into the reference canvas, clamped and spaced for their labels.

*Why it matters here.* The drawing helps to find tags and to see the clusters, but two tags drawn close together may share few games, a tag can sit among another cluster's tags ([why](02-app-controls.md#position)), and the picture changes with gravity, open panels and Tidy. Read how tags relate from the links, the Inspector and the tables, never from where they sit in the drawing.

*Example.* Two exports of the same state with the default layout have identical positions. Exporting it with 10 times the gravity changes only these four columns: every other byte of the export is the same.

*Bounds.* Model units: one unit is one pixel at the zoom the labels are spaced for.

*Compare with.* Nothing.

**Exact definition:** Global = `forceatlas2_layout(visible network, weight = active weight scaled to at most 1, gravity = 1, distributed_action = true, 100 iterations)` started from the loose layout (`spring_layout(weight = active weight, seed = seed)` at minimum games 1 and minimum shared games 1, scaled by 1,000), scaled to 70 % of the canvas (at most 1.6 times stretched per axis), clamped per axis to the main component's half-extent plus 1.5 × 15 pixels, then the label-aware pass: boxes as wide as max(node diameter, label width) and as tall as the node diameter plus 2 + 15 pixels for the label, kept 2 pixels apart, at the highest zoom from 1 down to 0.55 that fits the canvas. Node diameter = 18 + 30 × √(`n_games` / largest `n_games` of the dataset). Cluster-separated: per Multi-Tag Cluster, a square of side √(2.5 × the members' box area) around the Cluster Center (larger if the members need it), members by the same ForceAtlas2, clamp and label-aware pass from their Global positions; one-tag grid; shelf-packed rows aimed at the canvas aspect. Exports use the 1,116 × 678 reference canvas.

### Tags not in the network

> **In short.** Every tag of the dataset that is not in the network, with each reason why.
>
> **Here:** shows which characteristics of the most-played games the network leaves out, and why.
>
> **Caution:** a tag below the minimum games here can be common in another dataset.

Columns: `reasons` (with `tag_id`, `tag`, `n_games`) in `not_in_network.csv`.

Every tag on at least one game of the loaded dataset that is not a node, with every reason why, so that nothing disappears unexplained. Reasons appear in a fixed order: `removed` (removed in the app), `defining_tag_hidden`, `genre_tag_hidden`, `below_min_games`. A tag below the threshold can still be very common in another dataset; check the frequency table.

*Why it matters here.* The network describes only the tags it contains. A characteristic that only a handful of the Top 100 share falls below the minimum games per tag and cannot appear in any cluster; hidden and removed tags are left out by choice. Before writing that a characteristic is missing from the clusters, check here whether it was in the network at all.

*Example.* The Puzzle tag in the Puzzle dataset: `defining_tag_hidden;genre_tag_hidden` (it is both the defining tag and a Genre Tag).

*Bounds.* One to four reasons.

*Compare with.* `tag_frequency.csv`.

**Exact definition:** a tag is a node if it has at least `min_games_per_tag` of the N games and is neither hidden nor removed; every other tag of the dataset is listed.

## Clusters and partition quality

> **In short.** How the tags split into clusters and how clearly: Q with its excess over the null model, coverage, the cluster counts and the silhouette.
>
> **Here:** together they show whether the most-played games' tags fall into groups beyond the shuffled baseline.
>
> **Caution:** each number answers a different question; read them together, never one alone.

The clustering (community detection in the methods literature) splits the tags into groups that are more tightly linked inside than between. Louvain (Blondel et al. 2008) and Leiden (Traag, Waltman & van Eck 2019) both search for the split with the highest **modularity**. They are randomised searches: different seeds can give different, nearly equally good splits (Good, de Montjoye & Clauset 2010). The **partition** is the full list of which tag is in which cluster.

*Why it matters here.* These numbers describe the clustering as a whole, before any single cluster is read. Q says how separated the clusters are, the null-model excess how far it exceeds the shuffled baseline, coverage how much link weight the clusters hold, and the silhouette whether the games themselves agree. If the excess is near 0, the clusters say more about which tags are common among the most-played games than about how those games combine characteristics.

### Cluster labels and counts

> **In short.** Groups of tags linked more among themselves than chance predicts; C1 is the largest.
>
> **Higher →** more multi-tag clusters: the tags split into more, smaller groups.
>
> **Here:** each cluster is a candidate group of characteristics that co-occur in pairs among the most-played games.
>
> **Caution:** the count depends on γ, the thresholds and the seed; one-tag clusters are usually isolated tags, not findings.

Columns: `cluster`, `kind`, `size`, `member_tag_ids` / `members` (clusters and nodes); `n_multi_tag_clusters`, `n_one_tag_clusters` (cluster quality).

Shown in the app as “Cluster” (Inspector; tables and exports keep the column names).

Clusters are labelled `C1`, `C2`, … by size, largest first, never named. `kind` is `multi_tag` (two or more tags) or `one_tag`. Counts are always reported as "k multi-tag + s one-tag", never as one total; One-Tag Clusters are usually isolated tags, not a finding. Members are listed by medoid score. k depends heavily on γ, the thresholds and the seed. Modularity cannot reliably separate groups smaller than a scale set by the network's total weight (the resolution limit; Fortunato & Barthélemy 2007, abstract and §IV), so small groups can be merged into bigger clusters.

*Why it matters here.* A Multi-Tag Cluster is the study's unit of "a recurring combination of characteristics": tags that the most-played games of the dataset tend to carry together in pairs: A, B and C can form a cluster even if no game carries all three. Read a cluster through its members and its Cluster Center, not through its label: `C1` only means "largest in this Network State", and the same group of tags can be `C2` after a small change. Before treating a cluster as a finding, check that it survives other seeds (Membership Stability, the Seed-Noise Floor) and other γ values (the Resolution Sweep).

*Example.* "5 multi-tag + 3 one-tag": five clusters of two or more tags and three single tags.

*Bounds.* k ≥ 0, s ≥ 0; sizes ≥ 1.

*Compare with.* `seed_k_min`–`seed_k_max` and the [Resolution Sweep](#resolution-sweep).

**Exact definition:** labels by size descending, ties by the smallest member `tag_id`; Multi-Tag Clusters first, then One-Tag Clusters by `tag_id`.

### Network size

> **In short.** How big the network is: the games it is built from, the tags shown as nodes, and the links between tags that share enough games.
>
> **Higher →** more tags and links: a larger network, usually from looser thresholds.
>
> **Here:** shows how much of the dataset and its tags the clusters describe.
>
> **Caution:** most other numbers shift with size; compare Network States of similar size.

Columns: `n_dataset_games`, `n_nodes`, `n_edges`, `total_weight` in `cluster_quality.csv`.

Shown in the app as “Games”, “Tags”, “Links” (summary row above the graph).

Context for every other number: N (games after the Minimum Months Filter), the number of tags and edges, and the sum of the active Clustering Weight over all edges. Denser networks behave differently (see the null model). `total_weight` is in shared games or in summed lift, depending on the Clustering Weight, and the two are not comparable.

*Why it matters here.* Every pattern the network shows is a pattern among these N games and these tags only. "100 of 100" games means the whole Top-100 Dataset is in the network; a lower N (from the Minimum Months Filter) means the clusters describe only the games tracked long enough. Tags below the minimum games per tag are left out entirely, so a characteristic shared by only a handful of the most-played games cannot appear in any cluster; the Not in network table lists them.

*Example.* 100 games, 54 tags, 312 edges, total weight 4,120 shared games.

*Bounds.* Counts; `total_weight` ≥ 0.

*Compare with.* `null_n_edges_mean` for the edge count.

**Exact definition:** `total_weight` = Σ over edges of the active weight.

### Modularity Q

> **In short.** How much more link weight falls inside clusters than if links were placed at random, keeping each tag's total weight.
>
> **Higher →** more weight inside clusters than that expectation; 0 = no more than expected.
>
> **Here:** the clustering's target score; read it through its excess over the null model.
>
> **Caution:** random networks also reach high Q; not comparable across γ, weights, thresholds or datasets.

Columns: `modularity`, `modularity_status` in `cluster_quality.csv`.

Shown in the app as “Q” (summary row and Cluster quality).

How much more of the network's weight falls inside clusters than would be expected if links were spread at random while keeping each tag's total strength (Newman & Girvan 2004; weighted form, Newman 2004, §II.C). It is the objective the clustering maximises, reported at the γ that was optimised ("Q (γ = 1.00)"). Random networks with no real groups also reach high Q (Guimerà, Sales-Pardo & Amaral 2004), which is why the null model exists; many different partitions reach almost the same Q; and Q is not comparable across γ, Clustering Weights, thresholds or datasets. The only published Steam tag network found reports Q = 0.414 after pruning the five most common tags and 0.150 with them kept (Li & Zhang 2020, §5.2): context for how much near-universal tags lower Q, not a benchmark, since its network was built differently.

*Why it matters here.* Q says how clearly the tags of the most-played games fall into separate groups, but on its own it cannot tell combinations of characteristics from the grouping that tag popularity alone would produce. That is why the app always shows it with its excess over the null model: "Q 0.42 · excess +0.11" means the shuffled networks reach about 0.31 on average and the observed network 0.11 more. Use Q to compare Network States that differ only in the seed or the algorithm, never across datasets.

*Example.* Total weight 100, two clusters each with 40 inside and 20 between them: each cluster's summed strength is 2 × 40 + 20 = 100, so Q = 2 × (40 / 100 − (100 / 200)²) = 0.30.

*Bounds.* At γ = 1 on an unweighted network, −½ to 1 (Brandes et al. 2008, Lemma 3.1); the reachable maximum is below 1 and depends on the network (Fortunato & Barthélemy 2007, §III). Isolated tags add nothing. Empty when the network has no edges (`modularity_status` `no_edges`).

*Compare with.* 0 = no more weight inside clusters than expected at random (Newman & Girvan 2004, §IV); the [null model](#null-model-baseline) (`q_null_mean`); the Seed-Noise Floor ([`seed_modularity_sd`](#seed-spread-of-modularity-and-silhouette)).

*Descriptive: not comparable across pairs.* The Parameter Selection mode shows Q at the exact Selected Resolution for each Threshold Pair's Selected Partition on its own network. Pairs differ in tags and edges, so a higher value at one pair does not make it a better choice; Parameter Selection never uses it to choose a pair (see [the selection rule](#pair-constraints-qualifying-pair-and-the-selection-rule)).

**Exact definition:** Q = Σ_c [ L_c / m − γ (d_c / 2m)² ], with L_c the active weight inside cluster c, d_c the summed strength of its members and m the total weight (NetworkX `modularity`).

### Null-model baseline

> **In short.** The Q the same procedure reaches after shuffling which games carry which tags, keeping every tag's game count and every game's tag count.
>
> **Higher →** the shuffled data already produce much of the clustering.
>
> **Here:** separates how characteristics combine among the most-played games from some tags being everywhere.
>
> **Caution:** the SD from 20 shuffles is rough; shuffled networks differ in link count.

Columns: `q_null_mean`, `q_null_sd`, `null_n_edges_mean` (cluster quality); `replicate`, `seed`, `modularity`, `n_edges` in `null_model.csv`.

The Q this pipeline produces when the link between games and tags is scrambled, keeping how many tags each game has and how many games each tag has. It answers "how much Q would tag frequencies alone produce?". This matters most with the default shared-games weight, where frequency alone creates structure. The shuffled networks are rebuilt with the same thresholds, so they usually have a different number of edges from the real one, and Q depends on density (Guimerà, Sales-Pardo & Amaral 2004): compare `null_n_edges_mean` with `n_edges`. Twenty replicates give only a rough SD.

*Why it matters here.* Tags such as Singleplayer or Indie appear on a large share of the games, so they share many games with almost every other tag, and that alone creates groups. The null model keeps every tag exactly as common as it is and every game with as many tags as it has, but pairs them at random. The Q the shuffled networks reach is what those counts alone can produce; only Q clearly above it suggests the most-played games combine characteristics in ways the counts do not.

*Example.* "null 0.31 ± 0.01 … null networks average 640 edges vs 702": the scrambled networks reach Q 0.31 on average, with a sample SD of 0.01, and have fewer edges than the real one.

*Bounds.* Like Q.

*Compare with.* The real Q, through the [excess](#excess-modularity-and-z-score).

**Exact definition:** R times (default 20): curveball trades (10 per game) on the game–tag table of the N games restricted to the network's tags (Strona et al. 2014), preserving every row and column total; rebuild with the same thresholds; recluster with the same algorithm, γ and weight, using the replicate's seed; record Q. `q_null_sd` is the sample SD (ddof = 1). Replicate seeds derive from the main seed through their own stream.

### Excess modularity and z-score

> **In short.** Q minus the shuffled networks' mean Q: how far Q exceeds what the preserved tag and game counts give.
>
> **Higher →** more modularity than the shuffled data; 0 = no more.
>
> **Here:** the main check that clusters reflect how characteristics combine, not just popularity.
>
> **Caution:** not a share of causes; z is not a p value and can be large for a modest excess.

Columns: `q_excess`, `modularity_z` in `cluster_quality.csv`.

Shown in the app as “excess” (summary row) and “Null-model excess” (Cluster quality).

`q_excess` is Q minus the null-model mean. `modularity_z` expresses the same gap in null-model SDs. The z-score is never shown alone: with a small null SD, z can be very large even when the excess is modest, it is not a p value, and z-scores of modularity against random graphs have "a number of problems" (Karrer, Levina & Newman 2008, §I). With R = 20 shuffles a permutation test could not give p below 1/21 ≈ 0.048 (Phipson & Smyth 2010). The shuffled networks are rebuilt with the same thresholds and usually have a different number of links (shown in the line); Q of random networks depends on density (Guimerà, Sales-Pardo & Amaral 2004), so part of the excess can reflect that difference. The app and the report always show it inside the full line "Q … vs null … ± … (excess …, z …; null networks average … edges vs …)".

*Why it matters here.* The excess is the most direct answer to "do the most-played games combine characteristics in recognisable groups, beyond popular tags being everywhere?". An excess near 0 means shuffled data with the same tag and game counts give as much modularity, so the clusters could come from those counts alone; a clearly positive excess means the grouping goes beyond them. It still says nothing about which cluster is meaningful: for that, read the clusters themselves and their stability.

*Example.* Q 0.32, null 0.20 ± 0.01: excess 0.12, z = 0.12 / 0.01 = 12.

*Bounds.* `q_excess` from about −1.5 to 1.5; `modularity_z` any real number, empty when the null SD is 0.

*Compare with.* 0 (no more structure than frequencies produce); the Seed-Noise Floor's `seed_modularity_sd`.

**Exact definition:** `q_excess` = Q − `q_null_mean`; `modularity_z` = (Q − `q_null_mean`) / `q_null_sd`.

### Coverage and inter-cluster weight share

> **In short.** The share of all link weight that falls inside clusters.
>
> **Higher →** more of the weight inside clusters; 1 = all of it, which a single cluster also gives.
>
> **Here:** shows how much of the tags' co-occurrence the clusters account for.
>
> **Caution:** rises as clusters get fewer and bigger; never read it alone.

Columns: `coverage`, `inter_cluster_weight_share` in `cluster_quality.csv`.

Shown in the app as “Coverage” (Cluster quality).

The share of the total weight on edges inside clusters, and the rest. These are weighted analogues of Fortunato's coverage, which counts edges (2010, §III.C.2); the inter-cluster share is Kannan, Vempala and Vetta's ε (2004, Def. 2.1). Coverage rises as clusters get fewer and bigger, and a single cluster has coverage 1, so never read it alone.

*Why it matters here.* Coverage says how much of the co-occurrence among the most-played games' tags the clusters capture; the rest is weight between clusters. Unlike Q, it does not correct for what any split would capture, so compare it only between Network States with similar cluster counts, and read Q and its excess over the null model first.

*Example.* 80 of 100 units of weight inside clusters: coverage 0.80, inter-cluster share 0.20.

*Bounds.* 0–1; the two sum to 1. Empty when the network has no edges.

*Compare with.* Q, which corrects for what a random split would capture.

*Descriptive: not comparable across pairs.* The Parameter Selection mode shows weighted Coverage for each Threshold Pair's Selected Partition on its own network. Pairs differ in tags and edges, so a higher value at one pair does not make it a better choice; Parameter Selection never uses it to choose a pair (see [the selection rule](#pair-constraints-qualifying-pair-and-the-selection-rule)).

**Exact definition:** `coverage` = (active weight on intra-cluster edges) / (total weight); `inter_cluster_weight_share` = 1 − `coverage`.

### Disconnected clusters

> **In short.** Whether all of a cluster's tags are joined by links inside the cluster.
>
> **Here:** keeps two separate groups of characteristics from being read as one cluster.
>
> **Caution:** a known defect of Louvain, not a finding; Leiden never produces it.

Columns: `connected` (clusters); `n_disconnected_clusters` (cluster quality).

Whether a cluster's tags can all reach each other through edges inside the cluster. `false` means the cluster is two or more separate pieces under one label. Louvain can return such clusters (Traag, Waltman & van Eck 2019, abstract); for unweighted networks some best-modularity partition always has connected clusters (Brandes et al. 2008, Lemma 3.4), so a disconnected cluster is a known Louvain defect, not a finding. The software flags it and never splits it; the app suggests the Leiden mode, which guarantees connected clusters.

*Why it matters here.* A disconnected cluster would be described as one combination of characteristics when it is really two groups that happen to share a label. The Inspector warns about it and suggests the Leiden mode; switch to Leiden before describing such a cluster.

*Example.* A cluster of six tags in two groups of three with no edge between them: `connected` false.

*Bounds.* `n_disconnected_clusters` ≥ 0; always 0 under Leiden.

*Compare with.* The same state under Leiden.

**Exact definition:** `connected` = the subgraph induced by the cluster's tags is connected (a one-tag cluster is connected).

### Mean silhouette

> **In short.** On average, whether tags' games overlap more with their own cluster than with the nearest other; descriptive diagnostic, not a selection criterion.
>
> **Higher →** clearer separation; 0 = between clusters; below 0 = closer to another.
>
> **Here:** a second view, from game overlap; the links come from the same games.
>
> **Caution:** tag distances are mostly near 1, so values near 0 are common.

Columns: `mean_silhouette`, `silhouette_status` in `cluster_quality.csv` (over every Multi-Tag Cluster member) and `clusters.csv` (over one cluster's members).

Shown in the app as “Silhouette” (summary row and Cluster quality).

The average of the per-tag silhouettes: a check on the clustering from game overlap rather than link weights, not independent of them, since both come from the same game sets. It is labelled "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion". One-Tag Cluster members are left out of every mean, and the overall value averages tags, not clusters, so big clusters weigh more. Comparing values across Network States is only indicative.

*Why it matters here.* Clusters are found from link weights; the silhouette asks a different question of the same result: do the games that carry a cluster's tags really overlap more with each other than with the games of the next cluster? A value near 0 is common here, because Jaccard distances between tags are mostly near 1 and many of the most-played games carry tags from several clusters at once (an open-world RPG with crafting and survival tags, for example). Use it to compare clusters with each other or one Network State with a close variant, not as a pass mark.

*Example.* Three members with silhouettes 0.6875, 0.875 and 0.875 have a mean of 0.8125.

*Bounds.* −1 to 1. Empty with fewer than 2 Multi-Tag Clusters (`fewer_than_2_multi_tag_clusters`) and for One-Tag Clusters in `clusters.csv` (`one_tag_cluster`).

*Compare with.* 0; `seed_silhouette_sd`.

*Descriptive: not comparable across pairs.* The Parameter Selection mode shows the mean Jaccard silhouette for each Threshold Pair's Selected Partition on its own network. Pairs differ in tags and edges, so a higher value at one pair does not make it a better choice; Parameter Selection never uses it to choose a pair (see [the selection rule](#pair-constraints-qualifying-pair-and-the-selection-rule)).

**Exact definition:** mean of `silhouette` over the members of the Multi-Tag Clusters concerned.

### Internal edges, weight and densities

> **In short.** How tightly a cluster's tags are linked among themselves: links and link weight, also per possible pair.
>
> **Higher →** more of the members' pairs linked, or more heavily; edge density 1 = every pair linked.
>
> **Here:** whether a cluster's characteristics occur together pairwise or through a few common tags.
>
> **Caution:** small clusters reach high density easily; weighted density is in Clustering Weight units.

Columns: `internal_edges`, `internal_weight`, `edge_density`, `weighted_density` in `clusters.csv`.

How tightly linked a cluster is inside. For a cluster of n tags there are n(n − 1)/2 possible pairs. Edge density is the share of those pairs that are linked; weighted density is the average active weight per possible pair, missing edges counting as 0. These are weighted analogues of Fortunato's intra-cluster density (2010, §III.B.1, eq. 1), which counts edges. Small clusters reach high density easily, and weighted density is in the units of the active Clustering Weight.

*Why it matters here.* An edge density near 1 means almost every pair of the cluster's tags shares at least the minimum shared games: the most-played games carry these characteristics together pair by pair. A low density means the cluster hangs together through a few members that link to the rest. Compare clusters of similar size, and read it with the conductance, which says how much the cluster links outward.

*Example.* 5 tags with 8 of their 10 possible edges and a total internal weight of 120: edge density 0.8, weighted density 12.

*Bounds.* Edge density 0–1; weighted density 0 upwards. Both empty for one-tag clusters (no pairs).

*Compare with.* The same cluster's conductance.

**Exact definition:** `edge_density` = `internal_edges` / (n(n − 1)/2); `weighted_density` = `internal_weight` / (n(n − 1)/2).

### Cut weight and conductance

> **In short.** How much of a cluster's link weight crosses to tags outside it, as a share of its members' total strength (or the rest's, if smaller).
>
> **Higher →** more of its weight crosses to other clusters; 0 = none.
>
> **Here:** shows which clusters are separate groups and which overlap with the rest.
>
> **Caution:** on shared games, clusters of common tags cross a lot.

Columns: `cut_weight`, `conductance`, `conductance_status` in `clusters.csv`.

Shown in the app as “Boundary crossing (conductance)” (Inspector; tables and exports keep the column names).

How much of a cluster's weight leaks to the rest of the network. The cut weight is the active weight of edges with one end inside the cluster and one outside. Conductance divides it by the smaller of the cluster's volume (its members' total strength) and the rest's volume (Fortunato 2010, eq. 20; Kannan, Vempala & Vetta 2004, §2). Low means well separated. On shared games, clusters holding very common tags leak a lot simply because common tags link to everything.

*Why it matters here.* A cluster with low conductance is a set of characteristics that the most-played games mostly carry among themselves; a cluster with high conductance shares many games with other clusters, so its boundary is a matter of degree. Compare clusters of the same Network State. A tag left on its own but linked elsewhere has conductance 1.

*Example.* Cut 20, cluster volume 100, rest volume 100: conductance 0.20. A tag left alone by the algorithm but linked to other clusters has conductance 1.0.

*Bounds.* 0–1. Empty with `conductance_status` `isolated_tag` (the cluster's volume is 0) or `no_edges_outside_cluster` (the rest's volume is 0).

*Compare with.* Other clusters of the same state.

**Exact definition:** conductance = cut(C) / min(vol(C), vol(V ∖ C)), vol = summed strength on the active weight.

### Cluster connections

> **In short.** How many links, and how much link weight, join each pair of clusters.
>
> **Higher →** more links, or more weight on the Clustering Weight in use, between the two clusters; 0 = none.
>
> **Here:** shows which groups of characteristics the most-played games tend to combine with each other.
>
> **Caution:** on shared games, big clusters of common tags connect to everything; compare with cluster sizes.

Columns: `cluster_a`, `cluster_b`, `edge_count`, `weight` in `cluster_connections.csv`.

How many edges and how much weight join each pair of Multi-Tag Clusters, zero pairs included, plus each cluster's links to the pooled One-Tag Clusters (`one_tag_pool`). Large values mean the two clusters overlap a lot in their games. On shared games, big clusters of common tags are strongly connected to everything; compare with cluster sizes.

*Why it matters here.* Clusters are not sealed off from each other: a game often carries tags from several of them. A heavy connection between two clusters means many games combine the two groups of characteristics, so describe them as overlapping rather than as separate kinds of game. The `one_tag_pool` rows show how much the pooled One-Tag Clusters link to each cluster.

*Example.* `C1, C2, 7, 58`: seven edges with a total weight of 58 shared games join C1 and C2.

*Bounds.* Counts and weights ≥ 0.

*Compare with.* The clusters' `cut_weight`.

**Exact definition:** sums over the edges whose two ends lie in the two clusters (or in different One-Tag Clusters, for `one_tag_pool`).

## Stability

> **In short.** The Seed-Noise Floor: how much the clusters and their scores vary when only the random seed changes.
>
> **Here:** separates findings about the games from accidents of one run of the clustering.
>
> **Caution:** the K extra seeds are a sample, not every possible run.

Every number here is shown as a plain number, with no "stable / unstable" label, colour or threshold.

*Why it matters here.* The clustering is a randomised search, and other seeds can give different splits with nearly the same Q. Every number in this section compares the shown clusters with K extra runs on the unchanged network. Read other differences, between settings or after removing a tag, against this floor: a difference of similar size to the seeds' own spread is what another run of the clustering can give.

#### Three kinds of stability

> **In short.** The study reports three kinds of stability, each answering its own question, plus a separate check against random networks.
>
> **Here:** keeps a result about seeds, thresholds or games from standing in for the others.
>
> **Caution:** never combined into one score.

- **Algorithmic: the [Seed-Noise Floor](#adjusted-rand-index).** The same data and settings, clustered again with other seeds. Does the partition depend on the random seed?
- **Parameter: [Neighbour Agreement](#neighbour-agreement).** Neighbouring thresholds, one step in g or s. Does the partition depend on the exact thresholds?
- **Data: [Subsample Stability](#subsample-stability).** 80% of the games, drawn at random. Does the partition depend on which games are in the dataset?
- **And separately, the [Null Comparison](#null-comparison).** Is there more structure than in random networks with the same tag and game counts?

They answer different questions and are never combined into one score. A high value on one says nothing about the others: a partition can be identical for every seed and still dissolve without a fifth of the games.

*Why it matters here.* Parameter Selection reports all four for its chosen pair, side by side, so a reader can see which question each number answers and which it leaves open.

### Adjusted Rand index

> **In short.** ARI (adjusted Rand index): how similar two clusterings of the same tags are, corrected for chance.
>
> **Higher →** 1 = identical clusters; about 0 = no more agreement than chance.
>
> **Here:** the Seed-Noise Floor: how much the clusters change when only the random seed changes.
>
> **Caution:** drops faster in small networks, and does not say which tags moved.

Columns: `seed_ari_min`, `seed_ari_mean` (cluster quality); `noise_seed_index`, `seed`, `ari_vs_main` in `seed_noise.csv`.

Shown in the app as “Seed noise” (Cluster quality).

How similar two partitions of the same tags are, corrected for the agreement expected by chance (Meilă 2007, §2.1, eq. 6). Here each of K = 10 extra seeds' partitions is compared with the shown (main-seed) partition: this is the **Seed-Noise Floor**. If another seed gives clearly different clusters, single-cluster findings should be held loosely. ARI drops faster in small networks, and it does not say which tags moved (see [Membership Stability](#membership-stability)). K = 10 is a sample of seeds, not all of them.

*Why it matters here.* Before a cluster is described as a recurring combination of characteristics, it should be clear that it is not an accident of the random seed. If the lowest ARI is close to 1, every tested seed finds nearly the same clusters; if it is much lower, some clusters depend on the seed, and Membership Stability shows which tags move. The minimum is also the yardstick for Removal Sensitivity: a removal is flagged as beyond seed noise only when its ARI falls below it.

*Example.* 50 tags in 5 clusters of 10. Moving 1 tag to another cluster: ARI 0.95; moving 2: 0.90; moving 4 into the same other cluster: 0.83; merging two clusters: 0.77. With only 12 tags in 2 clusters, moving 1 tag gives 0.66.

*Bounds.* −0.5 to 1 (scikit-learn); a network with no edges gives every seed the same partition, so all values are 1.

*Compare with.* 1 = identical partitions; about 0 = no more agreement than random labels.

Parameter Selection reports a Seed-Noise Floor for each pair at its exact Selected Resolution; after [Apply to Workbench](02-app-controls.md#apply-to-workbench) the Workbench's own floor can differ.

**Exact definition:** `ari_vs_main` = scikit-learn `adjusted_rand_score` between a noise seed's labels and the main partition's labels over the network's tags; `seed_ari_min` / `seed_ari_mean` = minimum / mean over the K noise seeds. Noise seeds derive from the main seed through a stream separate from the null-model seeds; the two never share a seed.

### Seed spread of modularity and silhouette

> **In short.** How much Q and the mean silhouette vary when only the random seed changes.
>
> **Higher →** the seeds find splits that score more differently; 0 = all score the same.
>
> **Here:** the scale of seed noise for reading changes in Q across this study's Network States.
>
> **Caution:** an SD from K seeds is rough; Leiden often gives 0.

Columns: `seed_modularity_sd`, `seed_silhouette_sd`, `seed_silhouette_status` (cluster quality); `modularity`, `silhouette`, `silhouette_status` in `seed_noise.csv`.

How much Q and the mean silhouette vary across the K extra seeds on the unchanged network. A small SD means the seeds find equally good partitions, which may still differ (see ARI). It is the yardstick for whether a change in Q, for example a Removal Sensitivity ΔQ, is larger than seed noise. An SD from 10 values is itself rough, and Leiden often gives an SD of 0.

*Why it matters here.* Read a change in Q or the silhouette, between Network States or after removing a tag, beside this SD: a change of similar size is what another run of the clustering can give. It is a scale, not a test: a removal's change in Q always includes the mechanical loss of the tag's links, and an SD of 0, common under Leiden, does not make every change meaningful. A small SD does not mean that the seeds find the same clusters; the adjusted Rand index answers that.

*Example.* Seed Q values spread with sample SD 0.004: "SD Q 0.004" in the Seed-Noise Floor line.

*Bounds.* 0 upwards. `seed_silhouette_sd` is empty when fewer than 2 seeds have a silhouette (`fewer_than_2_seeds_with_silhouette`).

*Compare with.* Removal Sensitivity's ΔQ and Δsilhouette.

**Exact definition:** sample SD (ddof = 1) of the seeds' Q, and of the seeds' mean silhouettes over the seeds that have one.

### Seed range of cluster counts

> **In short.** The fewest and the most Multi-Tag Clusters found when only the random seed changes.
>
> **Higher →** a wider range: the count depends more on the seed.
>
> **Here:** check it before reporting how many groups the most-played games' characteristics form.
>
> **Caution:** the count can stay the same while members move; read it with the ARI.

Columns: `seed_k_min`, `seed_k_max` (cluster quality); `n_multi_tag_clusters`, `n_one_tag_clusters` in `seed_noise.csv`.

The lowest and highest number of Multi-Tag Clusters across the K extra seeds: the most intuitive sign of seed dependence. The count can stay the same while membership changes, so read it with ARI.

*Why it matters here.* Writing "the tags fall into five groups" holds only when other seeds also give five. If the range is 4–7, report the range, or that the count depends on the seed. The shown partition's own count lies within or at the edge of this range.

*Example.* "multi-tag clusters 5–7": some seeds split or merge clusters.

*Bounds.* Integers ≥ 0.

*Compare with.* The shown partition's `n_multi_tag_clusters`.

**Exact definition:** minimum and maximum over the noise seeds of the number of clusters with 2+ tags.

### Membership Stability

> **In short.** How much of the tag's cluster, on average, stays the same when the clustering is repeated with other seeds.
>
> **Higher →** 1: always with the same tags; lower: its companions change between seeds.
>
> **Here:** shows which tags keep their cluster before it is described as a recurring combination.
>
> **Caution:** small clusters lose more per moved tag; descriptive only.

Columns: `membership_stability` (nodes); `mean_membership_stability` (clusters).

Shown in the app as “Membership Stability”, “Mean Membership Stability” (Inspector; tables and exports keep the column names).

How consistently a tag lands with the same other tags across the K extra seeds: 1 means its cluster never changed. A cluster's value is the mean over its members. It explains a low seed ARI by showing which tags move. Cluster size matters: losing one companion costs a member of a two-tag cluster 0.5 but a member of a twenty-tag cluster only 0.05. It is descriptive only: it does not say whether a tag or cluster is real or important. A related published measure, Hennig's cluster-wise Jaccard stability, comes from a different procedure (see Appendix A).

*Why it matters here.* The clustering is a randomised search, so another seed can place some tags differently. A tag near 1 sits with the same companions across the tested seeds, and a cluster's mean shows how much of the whole group holds together. Tags with low values are the ones to leave out, or mention with care, when describing a cluster in a write-up. The Seed-Noise Floor gives the same picture for the whole partition at once.

*Example.* Main cluster {T, a, b, c}. In 8 seeds T's cluster is the same (1.0); in 2 seeds it is {T, a, b} (3/4 = 0.75). Membership Stability = (8 × 1.0 + 2 × 0.75) / 10 = 0.95.

*Bounds.* Above 0 up to 1. Empty for every isolated tag (`degree` 0), which is always alone and so carries no information, and so also for its One-Tag Cluster's mean. Empty values sort last.

*Compare with.* 1; the Seed-Noise Floor's ARI.

**Exact definition:** `membership_stability` = mean over noise seeds of |A ∩ B| / |A ∪ B|, where A and B are the tag's cluster (including the tag) in the main partition and in the seed's partition.

### Resolution Sweep

> **In short.** The report's clustering repeated at each γ of a fixed grid (default 0.50–1.50), everything else unchanged.
>
> **Here:** shows whether the clusters of the most-played games' tags hold at finer and coarser scales.
>
> **Caution:** Q at different γ must not be compared; compare cluster counts and the agreement with the report's clusters.

Columns: `resolution`, `ari_vs_report` and the counts, modularity, silhouette and seed ARIs in `resolution_sweep.csv` (Build only).

How the feature-analysis report's clustering changes when only γ changes: the clustering is repeated at each γ of a fixed grid (default 0.50–1.50; the report's γ is always a row), with everything else held at the report's settings, so the node set is identical across rows. If cluster counts and `ari_vs_report` change a lot over the grid, the cluster structure depends on the chosen resolution; compare `ari_vs_report` with `seed_ari_min` at the same γ to see whether the change exceeds seed noise. This makes visible that "the" clusters are one view among several (Fortunato & Barthélemy 2007; Good et al. 2010). The `modularity` column is Q at that row's γ: **values in different rows must not be compared**.

*Why it matters here.* There is no single right resolution, so a cluster reported at γ = 1 is one view among several. If the cluster counts and the agreement with the report's partition change little across the grid, the reported clusters do not depend on that choice; if they change a lot, the report should say so. Compare `ari_vs_report` with `seed_ari_min` at the same γ to see whether a change exceeds seed noise.

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

> **In short.** The order in which Removal Sensitivity tests the tags: by active strength (link weight on the Clustering Weight), highest first.
>
> **Here:** a partial run has covered the most linked of the most-played games' tags.
>
> **Caution:** an order for running the tests, not a ranking of importance.

Columns: `run_order`, `active_strength` (with `tag_id`, `tag`, `cluster`, `is_center`) in `removal_sensitivity.csv`.

Which tag the row is about, and its strength on the active Clustering Weight. Tags are processed by active strength, highest first, then by tag id, so a cancelled or partial run has covered the most strongly linked tags and is a prefix of the full run. The run order is an order for running the tests, not a ranking of importance.

*Why it matters here.* Testing every tag takes time, so the run starts with the tags that carry the most link weight. If you stop early, the rows you have are for those tags; the others are untested, not unaffected.

*Example.* `run_order` 1 is the tag with the largest active strength.

*Bounds.* 1 to the number of tags tested.

*Compare with.* Nothing.

**Exact definition:** order by `active_strength` descending, then `tag_id` ascending.

### Reclustered change in modularity

> **In short.** How much Q changes when the tag is removed and the clustering is run again.
>
> **Higher →** above 0: Q higher without the tag; below 0: lower.
>
> **Here:** shows how much the clustering's overall score depends on one characteristic.
>
> **Caution:** part of the change is mechanical, from losing the tag's links; compare with the seeds' SD of Q.

Column: `rc_delta_modularity`.

Shown in the app as “Change in Q (reclustered)” (Inspector; tables and exports keep the column names).

Q of the reclustered network without the tag, minus Q of the current state. Removing a tag also removes its edges, so the total weight drops: part of ΔQ is this mechanical change, not reorganisation. Compare it with `fp_delta_modularity`, which has no reclustering, and with `seed_modularity_sd`. It carries no flag.

*Why it matters here.* Removal Sensitivity asks whether a cluster finding hangs on a single tag. A change in Q within the spread across seeds (`seed_modularity_sd`) is no more than another run of the clustering gives. A larger change can come from the clusters reorganising without the tag or simply from losing its links; the fixed-partition change, which keeps the clusters, helps tell the two apart. It never says that the characteristic matters for how many people play a game.

*Example.* Q 0.42 before and 0.40 after: Δ = −0.02.

*Bounds.* Roughly −1 to 1, usually small; empty when either Q is empty.

*Compare with.* `seed_modularity_sd`; `fp_delta_modularity`.

**Exact definition:** `rc_delta_modularity` = Q(reclustered network without the tag) − Q(current state).

### Reclustered silhouette

> **In short.** The mean silhouette after the tag is removed and the clustering is run again, and its change.
>
> **Higher →** a change above 0: the remaining tags separate more clearly on game overlap.
>
> **Here:** shows whether a characteristic blurs or sharpens the groups on game overlap.
>
> **Caution:** some change happens even when no tag moves; compare with the seeds' SD.

Columns: `rc_silhouette_after`, `rc_silhouette_after_status`, `rc_delta_silhouette`.

Shown in the app as “Silhouette after removal (reclustered)” (Inspector; tables and exports keep the column names).

The mean silhouette after reclustering, and its change. Removing a tag also removes its own silhouette from the mean and changes its neighbours' distances to clusters, so some change happens even if no tag moves. If the silhouette moves between a value and n/a, the Δ is empty and the app shows, for example, "0.21 → n/a" with the reason.

*Why it matters here.* A positive change means the remaining tags, reclustered, separate more clearly on the games they share; a negative change, less clearly. Part of any change comes from the removed tag leaving: its own value leaves the mean and the other tags' distances to its cluster change, even if no tag moves. Read it against `seed_silhouette_sd`: small changes are within what another seed gives.

*Example.* 0.21 before, 0.24 after: Δ = +0.03.

*Bounds.* As the mean silhouette; Δ in −2 to 2 in theory, small in practice.

*Compare with.* `seed_silhouette_sd`.

**Exact definition:** `rc_delta_silhouette` = mean silhouette(reclustered) − mean silhouette(current); empty if either is n/a.

### Reclustered change in cluster counts

> **In short.** How many multi-tag and one-tag clusters appear or disappear when the tag is removed and the clustering is run again.
>
> **Higher →** above 0: more clusters without the tag; below 0: fewer.
>
> **Here:** finds tags that join two groups into one or hold a group together.
>
> **Caution:** often mechanical: removing one tag of a two-tag cluster leaves its partner alone.

Columns: `rc_delta_k` (Multi-Tag Clusters), `rc_delta_s` (One-Tag Clusters).

Shown in the app as “Change in multi-tag · one-tag clusters” (Inspector; tables and exports keep the column names).

How many clusters appear or disappear after reclustering. Δk = −1 with Δs = +1 can simply mean the tag was one of a two-tag cluster, leaving its partner alone: a mechanical change, not reorganisation. Removing an isolated tag gives Δs = −1. No noise flag; check `seed_k_min`–`seed_k_max`.

*Why it matters here.* A tag whose removal adds a Multi-Tag Cluster may have been linking two groups, and one whose removal removes one may have been separating them. The change can also come from the whole network shifting, because removing a tag changes every expected weight; look at the new clusters (Remove) before describing it. Compare with the seed range of cluster counts, because other seeds alone can change the count.

*Example.* A bridge tag whose removal splits its cluster in two: Δk = +1.

*Bounds.* Integers.

*Compare with.* The seed range of cluster counts.

**Exact definition:** after − before, for the number of clusters with 2+ tags and with 1 tag.

### Reclustered ARI

> **In short.** How similar the clusters are, over the remaining tags, after the tag is removed and the clustering rerun.
>
> **Higher →** 1 = no tag moved; lower: the clusters reorganised without it.
>
> **Here:** the main reading of Removal Sensitivity: does a cluster finding depend on this tag?
>
> **Caution:** part of a low value can be seed-like noise; compare with the lowest seed ARI.

Column: `rc_ari`.

Shown in the app as “Agreement after removal (ARI, reclustered)” (Inspector; tables and exports keep the column names).

How similar the reclustered partition is to the current one, over the remaining tags: 1 means nobody moved, lower means the partition reorganised without this tag. The Removal sensitivity table's default sort puts the lowest first. Removing a tag also changes the order in which the algorithm visits tags, so part of a low ARI can be seed-like noise; read it against `seed_ari_min`.

*Why it matters here.* If removing a single tag reorganises the clusters, a description of those clusters rests on that one characteristic, and should say so. The Removal sensitivity table sorts by this value, lowest first, and the Beyond seed noise flag marks values below the Seed-Noise Floor. A value above the floor is within the range the K seeds gave; that does not show the removal had no effect.

*Example.* A bridge tag tying two groups into one cluster: without it the cluster splits and `rc_ari` = 0.

*Bounds.* −0.5 to 1.

*Compare with.* `seed_ari_min`, through the [beyond-noise flag](#beyond-noise-flag).

**Exact definition:** `rc_ari` = `adjusted_rand_score` between the current and the reclustered labels over every tag except the removed one.

### Centers lost

> **In short.** Current Cluster Centers that are no longer centers after the tag is removed and the clustering is run again.
>
> **Here:** shows whether the tags used to describe clusters depend on this tag.
>
> **Caution:** a center is also lost when its cluster shrinks below three tags, and near-tied centers swap easily.

Columns: `rc_centers_lost_tag_ids`, `rc_centers_lost`.

Shown in the app as “Cluster Centers lost” (Inspector; tables and exports keep the column names).

Current Cluster Centers, other than the removed tag, that are no longer centers after reclustering. A center is also lost when its cluster shrinks below three tags, which can be mechanical, and centers with near-tied medoid scores swap easily.

*Why it matters here.* Clusters are described through their Cluster Centers, so a removal that changes them changes how the clusters would be described. If many centers are lost, describe the clusters through several members rather than one center. "none" means every other center stayed.

*Example.* Removing a tag splits a 6-tag cluster whose center lands in a 2-tag piece: that center is lost.

*Bounds.* 0 up to the number of centers.

*Compare with.* The cluster's members' medoid scores.

**Exact definition:** current centers ∖ {removed tag} ∖ centers of the reclustered partition.

### Fixed-partition change in modularity

> **In short.** How Q changes when the tag is dropped but every other tag stays in its cluster.
>
> **Higher →** above 0: Q higher without it; below 0: the tag added to Q.
>
> **Here:** shows how much one characteristic contributes to the separation of the clusters as they are.
>
> **Caution:** includes the mechanical loss of the tag's links; no noise flag.

Column: `fp_delta_modularity`.

Shown in the app as “Change in Q (clusters kept)” (Inspector; tables and exports keep the column names).

Q without the tag, everyone else kept in their cluster, minus the current Q. Negative means the tag added to the partition's quality; positive means Q is higher without it (the tag fitted its cluster poorly). It is deterministic, but it includes the same weight-loss effect as the reclustered reading. Removing a tag also lowers the total weight and every cluster's strength, so Q moves even for clusters it was not in. No flag.

*Why it matters here.* This reading keeps the clusters exactly as shown, so it has no reclustering noise; it still includes the loss of the tag's links. A clearly negative value suggests a tag whose links hold its cluster together; a positive value, one that sits loosely in its cluster. Compare with the reclustered change to see whether the clustering would also reorganise.

*Example.* Q 0.42 before, 0.43 with the tag dropped and the partition fixed: Δ = +0.01.

*Bounds.* Roughly −1 to 1; empty when either Q is empty.

*Compare with.* `rc_delta_modularity`.

**Exact definition:** `fp_delta_modularity` = Q(network without the tag, other tags in their current clusters) − Q(current state).

### Fixed-partition silhouette

> **In short.** The mean silhouette when the tag is dropped but every other tag stays in its cluster, and its change.
>
> **Higher →** a change above 0: the remaining tags fit their unchanged clusters better on average.
>
> **Here:** finds members whose games point away from their cluster.
>
> **Caution:** includes changes to the other tags' distances; n/a when fewer than two multi-tag clusters remain.

Columns: `fp_silhouette_after`, `fp_silhouette_after_status`, `fp_delta_silhouette`.

Shown in the app as “Silhouette after removal (clusters kept)” (Inspector; tables and exports keep the column names).

The mean silhouette without the tag, partition fixed, and its change. A positive Δ means the remaining tags' mean rose. Two effects mix: the tag's own value leaves the mean, and the other tags' distances change without its games. A two-tag cluster's partner becomes a One-Tag Cluster and leaves the mean. Removing a member of a two-tag cluster can leave fewer than two Multi-Tag Clusters, and then the silhouette after is n/a and the Δ empty.

*Why it matters here.* A clearly positive change suggests the tag fitted its cluster poorly on game overlap, but the change also includes the other tags' distances shifting without its games. Its per-tag silhouette shows its own fit directly; a negative one means its games overlap more with another cluster.

*Example.* 0.21 before, 0.19 after: Δ = −0.02.

*Bounds.* As the mean silhouette.

*Compare with.* `seed_silhouette_sd`.

**Exact definition:** `fp_delta_silhouette` = mean silhouette(partition fixed, tag dropped) − mean silhouette(current); empty if either is n/a.

### Beyond-noise flag

> **In short.** Whether removing the tag changed the clusters more than any of the K extra seeds did.
>
> **Here:** narrows the Removal Sensitivity table to the tags to look at first.
>
> **Caution:** a screening flag, not a test; if removals acted only like another seed, about n / (K + 1) would be flagged on average, and the actual count varies widely.

Column: `rc_ari_beyond_noise`.

Shown in the app as “Beyond seed noise” (Inspector; tables and exports keep the column names).

A screening flag, not a significance test: true when the reclustered ARI is below the lowest ARI among the K seeds of the Seed-Noise Floor, meaning that removing the tag changed the partition more than any of the extra seeds did. It narrows a long table to the tags to look at first. Only ARI is flagged: ΔQ and Δsilhouette always contain the mechanical effect of losing the tag's edges, so they stay plain numbers beside `seed_modularity_sd` and `seed_silhouette_sd`. When every seed agrees (`seed_ari_min` = 1), any removal that moves a tag is flagged, which is correct, because seed noise is then zero. Some flags are expected by chance: if a removal acted only like one more random seed, its ARI would fall below the lowest of K seed ARIs about 1 time in K + 1, so the app and the report state "if removals acted only like another seed, about n / (K + 1) would be flagged on average". All removals are compared with the same seed minimum, so flags rise and fall together; and a removal changes the network, so it need not behave like a seed.

*Why it matters here.* With dozens of tags tested, some flags are expected by chance, and the footer under the table gives that expected count. A flagged tag is one whose absence reorganises the clusters more than any of the K seeds did, so descriptions of its clusters should be checked without it. Unflagged tags can still change Q or the silhouette, which carry no flag.

*Example.* 50 tags tested with K = 10: "7 of 50 tags flagged; if removals acted only like another seed, about 5 would be flagged on average".

*Bounds.* true / false.

*Compare with.* n / (K + 1), the expected chance count.

**Exact definition:** `rc_ari_beyond_noise` = `rc_ari` < `seed_ari_min`.

## Parameter Selection

> **In short.** Automatic Parameter Selection: for each dataset, a search over the thresholds that picks a Threshold Pair and a resolution γ by fixed, published rules.
>
> **Here:** gives each Top-100 Dataset a defensible starting point instead of the shared defaults.
>
> **Caution:** a choice of settings to look at, not a claim that the Clusters are real.

#### How Automatic Parameter Selection works

> **In short.** The steps in order: grid, γ scan, CHAMP, γ̂ and Stable Partitions, the Selected Partition, Neighbour Agreement, the constraints and the choice, then validation.
>
> **Here:** shows how the Parameter Selection mode arrives at one pair per dataset.
>
> **Caution:** each step has its own entry; read the caveats there.

The Parameter Selection mode runs the same procedure for each Top-100 Dataset, one dataset at a time.

1. **Grid.** It builds the Tag Network at every [Threshold Pair](#threshold-pair-and-parameter-grid) of the Parameter Grid (g 3–20, s 2–12, s ≤ g: 153 pairs), under one set of Selection Settings.
2. **γ scan.** On each distinct graph it runs Leiden with 10 seeds at every γ from 0 to Gibson and Mucha's bound, in steps of 0.05 (see [Admissible Partition and Optimality Domain](#admissible-partition-and-optimality-domain)).
3. **CHAMP.** It keeps the partitions that are best at some γ, each with the γ range where it is best.
4. **γ̂ and Stable Partitions.** It asks of each such partition whether its own estimated resolution falls inside that range ([Resolution estimate and Stable Partition](#resolution-estimate-and-stable-partition)).
5. **Selected Partition.** Among the Stable Partitions with enough Multi-Tag Clusters it takes the one with the widest range ([Selected Partition and Selected Resolution](#selected-partition-and-selected-resolution)).
6. **Neighbour Agreement.** It compares each pair's Selected Partition with those of the pairs one step away ([Neighbour Agreement](#neighbour-agreement), [Edge Overlap](#edge-overlap)).
7. **Constraints and choice.** Among the pairs that meet the Pair Constraints ([Information Retention](#information-retention), [Isolated share and LCC share](#isolated-share-and-lcc-share)), it chooses by Neighbour Agreement ([Pair Constraints, Qualifying Pair and the selection rule](#pair-constraints-qualifying-pair-and-the-selection-rule)).
8. **Validation.** It compares the chosen pair with shuffled networks ([Null Comparison](#null-comparison)) and with 80% subsets of the games ([Subsample Stability](#subsample-stability)).

Each dataset is selected on its own, from its own games and tags. Different pairs in different datasets are expected and are not a disagreement: the same pair builds networks of different sizes in different datasets.

*Why it matters here.* The thresholds and γ decide which tags are nodes and how finely they are grouped, and the shared defaults were not chosen per dataset. The procedure replaces a hand choice with rules that can be stated, rerun and checked, and it shows every number behind its choice. What it gives is a defensible choice, not the true structure: the three kinds of stability it reports (see [Three kinds of stability](#three-kinds-of-stability)) and the Null Comparison each answer a narrower question.

### Threshold Pair and Parameter Grid

> **In short.** A Threshold Pair is one (g, s): minimum games per tag g and minimum shared games s. The Parameter Grid is every pair searched.
>
> **Higher →** larger g keeps fewer, more common tags; larger s keeps fewer edges.
>
> **Here:** the settings Parameter Selection chooses between for each dataset.
>
> **Caution:** count thresholds only; an edge's count alone carries no significance claim.

Columns: `g`, `s`, `n_tags`, `n_edges`, `n_e`, `graph_hash` in `pairs.csv`.

A Threshold Pair (g, s) fixes the Tag Network's two thresholds: a tag is a node when at least g of the dataset's games have it, and two nodes are linked when they share at least s games. The Parameter Grid is g = 3…20 and s = 2…12 with s ≤ g, 153 pairs per dataset, all under the same Selection Settings. Within a dataset, (g + 1, s) is (g, s) restricted to tags with at least g + 1 games, and (g, s + 1) has the same tags as (g, s) with some edges removed. Pairs whose graphs are identical (the same tags, edges and weights) share every result except their (g, s); the mode computes each distinct graph once. An edge's count alone carries no significance claim: the thresholds decide what is drawn, not what is more than chance.

*Why it matters here.* The two thresholds trade coverage against noise: low thresholds keep rare tags and chance co-occurrences, high ones keep a small core of common tags. Searching the grid makes that trade-off visible pair by pair instead of fixing it once.

*Example.* In puzzle, g = 14, s = 2 keeps 31 tags (the tags on at least 14 of the 100 games) and links any two of them that share two games.

*Bounds.* g from 3 to 20, s from 2 to 12, s ≤ g; 153 pairs.

*Compare with.* The shared defaults (8, 8) of `network.toml`, used by the Workbench and the feature-analysis report.

**Exact definition:** `pairs.csv` has one row per (dataset, g, s) of the grid; `graph_hash` = SHA-256 of the sorted node list and the sorted (u, v, shared count, Clustering Weight) edge list.

### Admissible Partition and Optimality Domain

> **In short.** An Admissible Partition is one that is the best found at some range of γ (its Optimality Domain), on the upper envelope of every partition's line Q(γ).
>
> **Here:** reduces hundreds of scanned partitions to the few that are ever optimal.
>
> **Caution:** optimal among the partitions found, not among every possible partition.

Columns: `a_hat`, `p_hat`, `domain_low`, `domain_high`, `clipped_high` in `admissible_partitions.csv`; `gamma_max_n_e`, `gamma_end`, `scan_length`, `pass_capped_runs` in `pairs.csv`.

Every partition σ of a graph has a modularity that is a straight line in γ: Q_σ(γ) = Â_σ − γ·P̂_σ, where Â is twice the weight inside Clusters and P̂ = Σ κ_c² / 2m sums the squared Cluster strengths (Weir et al. 2017, §2, eqs. 1–4). The γ scan runs Leiden with 10 seeds at every γ from 0 to Gibson and Mucha's bound γ_max(K) at K = n_e, the number of tags with an edge, on the 0.05 grid (Gibson & Mucha 2022, SI §J); no estimate γ̂ on the graph can lie above it, so the scan covers every γ where a partition can be stable. CHAMP keeps the upper envelope of the unique partitions' lines over [0, γ_end]: each partition on top over a range of positive width is admissible, and that range is its Optimality Domain [a, b]. A domain that reaches the scan's end is marked `clipped_high`; it keeps its clipped width. Leiden runs a pass loop capped at 1,000 passes; runs that hit the cap are counted in `pass_capped_runs`.

*Why it matters here.* Leiden at nearby γ values and seeds returns many partitions that differ only by a few tags. CHAMP keeps only those that are best somewhere, with the exact γ range where each is best, so the next steps work on a short list with exact boundaries instead of on the scan's grid.

*Example.* Puzzle g = 14, s = 2 has 31 tags with an edge, so γ_max(31) = 5.14 and the scan runs over 104 γ values (0 to 5.15) × 10 seeds, 1,040 Leiden runs. They find 48 unique partitions, of which 35 are admissible; the Selected Partition owns [1.046, 1.138].

*Bounds.* Domains partition [0, γ_end] without overlap; the first one starts at 0 and belongs to the partition with every connected component as one Cluster. γ_end runs from 3.80 to 17.75 on this Build.

*Compare with.* The Workbench's single γ: it shows the partition Leiden finds there, which need not be admissible.

**Exact definition:** Â = 2·Σ internal edge weights, P̂ = Σ_c κ_c²/2m over all tags (isolated tags add 0); the envelope over [0, γ_end] with γ_end the last scan γ, `round(0.05·i, 2)` for i = 0 … ⌈γ_max(n_e)/0.05 − 1e-9⌉; ties at a breakpoint go to the smaller P̂, single-point domains are dropped, and partitions with identical (Â, P̂) keep the one whose canonical membership sorts first.

### Resolution estimate and Stable Partition

> **In short.** γ̂ is the resolution a partition itself implies, from its internal and external edge weight. A Stable Partition is one whose γ̂ falls inside its own Optimality Domain.
>
> **Here:** narrows the admissible partitions to those that agree with their own γ.
>
> **Caution:** with Lift or shared-game weights, γ̂ has no likelihood behind it.

Columns: `omega_in`, `omega_out`, `gamma_hat`, `gamma_hat_reason`, `map_target`, `stable` in `admissible_partitions.csv`.

For a partition with Â and P̂ on a graph of total weight 2m, ω_in = Â / P̂ and ω_out = (2m − Â) / (2m − P̂), and γ̂ = (ω_in − ω_out) / (ln ω_in − ln ω_out) (Newman 2016, §III.A, eqs. 15–18). It is evaluated once per Admissible Partition, as Gibson and Mucha's fixed-point test (Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3); Newman's iteration is never run. A partition is stable when a ≤ γ̂ ≤ b. There is no estimate, and so no stability, when the graph has no edges (`no_edges`), fewer than two groups have edges (`one_group`), no edge crosses between groups (`no_cross_weight`) or Â ≤ P̂ (`not_assortative`). The map target is the Admissible Partition whose domain holds γ̂; the CHAMP plot draws an arrow to it.

*Why it matters here.* Newman showed that maximising modularity at γ̂ is equivalent to fitting a degree-corrected planted-partition model to a multigraph of counts. A Stable Partition is a fixed point of that correspondence. Our weights are Lift or shared-game counts, not a multigraph, so γ̂ is a heuristic here: the formulas are well defined, but there is no likelihood behind them.

*Example.* A partition with Â = 12, P̂ = 7 on a graph with 2m = 14 has ω_in = 12/7, ω_out = 2/7 and γ̂ = 0.80; if its domain is [0.29, 2.63], it is stable. In puzzle g = 14, s = 2, 1 of the 35 Admissible Partitions is stable: γ̂ = 1.103 lies in its domain [1.046, 1.138].

*Bounds.* γ̂ > 0 for every assortative partition, and γ̂ ≤ γ_max(n_e) ≤ γ_end (Gibson & Mucha 2022, SI §J.2).

*Compare with.* Its domain [a, b]: γ̂ inside means stable.

**Exact definition:** `gamma_hat` = (ω_in − ω_out)/(ln ω_in − ln ω_out) with ω_in = Â/P̂, ω_out = (2m − Â)/(2m − P̂); empty with `gamma_hat_reason` ∈ {`no_edges`, `one_group`, `no_cross_weight`, `not_assortative`}; `stable` = domain_low ≤ γ̂ ≤ domain_high.

### Selected Partition and Selected Resolution

> **In short.** The Selected Partition is the pair's Stable Partition with the widest Optimality Domain, among those with enough Multi-Tag Clusters; the Selected Resolution is that domain's midpoint.
>
> **Here:** gives each Threshold Pair one partition and one γ to compare and to apply.
>
> **Caution:** a rule of this study, not of the sources; a pair may have none.

Columns: `selected_low`, `selected_high`, `selected_resolution`, `clipped_high`, `workbench_gamma`, `workbench_seed`, `reproduced`, `workbench_ari`, `not_representable`, `not_reproduced`, `selection_reason` in `pairs.csv`; `selected` in `admissible_partitions.csv`; `selected_partitions.csv`.

Among the Stable Partitions with at least the minimum Multi-Tag Clusters (a Selection Setting, default 3, counting only Clusters with 2 or more tags), the one with the widest domain b − a wins; equal widths go to the lower midpoint. The minimum is applied after stability, never to CHAMP's input. The Selected Resolution is the exact midpoint (a + b)/2. Without one, the pair records why: `no_edges`, `no_stable_partition` or `too_few_multi_tag_clusters`. The **Workbench γ and seed** are what Apply to Workbench enters: the two-decimal γ inside the domain nearest the midpoint at which Leiden with the main seed, or else one of the 10 scan seeds, gives exactly the Selected Partition. When no two-decimal value lies in the domain the pair is `not_representable`; when none reproduces it, `not_reproduced`, and Apply uses the rounded midpoint with the main seed.

*Why it matters here.* A wide domain means the partition stays optimal over a large range of γ, so it is not an artefact of one exact resolution. The width is in plain γ units; rescaling it to log γ or to Gibson and Mucha's γ-scaled area was considered and not used.

*Example.* Puzzle g = 14, s = 2: the Selected Partition has 4 Multi-Tag Clusters and the domain [1.046, 1.138], so the Selected Resolution is 1.092; Workbench γ 1.09 with a scan seed reproduces it. On this Build 764 of 765 pairs have a Selected Partition, and the Workbench γ and seed reproduce 758 of them.

*Bounds.* The Selected Resolution lies in (0, γ_end].

*Compare with.* The other Stable Partitions in `admissible_partitions.csv`, and the Workbench's partition at the same γ and seed, which is identical when `reproduced` is true.

**Exact definition:** the Stable Partition with `n_multi` ≥ the minimum and the largest domain_high − domain_low (ties within 1e-12 relative: lower midpoint, then canonical membership); `selected_resolution` = (domain_low + domain_high)/2, unrounded.

### Neighbour Agreement

> **In short.** Neighbour Agreement: the mean ARI between a pair's Selected Partition and those of its one-step neighbours in g or s with a different graph.
>
> **Higher →** the Clusters change less when a threshold moves by one.
>
> **Here:** the objective of the rule that chooses each dataset's pair.
>
> **Caution:** higher at large g partly by construction; not evidence that the Clusters are real.

Columns: `neighbour_agreement`, `na_status`, `n_comparable`, `n_different_graph`, `n_identical_graph`, `n_missing` in `pairs.csv`; `neighbour_links.csv`.

The neighbours of (g, s) are (g − 1, s), (g + 1, s), (g, s − 1) and (g, s + 1) inside the grid. For each link the two Selected Partitions are compared with the adjusted Rand index on the **compared tags**: the tags in both networks with an edge in at least one of them. A tag isolated in both is left out; a tag isolated in one and clustered in the other counts as a disagreement. A link is not comparable when either pair has no Selected Partition (the neighbour is **missing, never 0**) or fewer than 2 tags are compared. A link between identical graphs is flagged and left out of the mean: a step that removes nothing perturbs nothing. Neighbour Agreement measures parameter stability, not correctness: it says how little the clustering changes when g or s moves by one, not that the Clusters are real.

Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, particularly s, generally produces a smaller change in the graph. This can increase agreement independently of the robustness of the Clusters. Choosing the smallest g among near-best pairs partially counterbalances this tendency.

*Why it matters here.* A Cluster that appears at one threshold and dissolves at the next depends on an arbitrary choice; one that persists across neighbouring thresholds does not. That is the property the selection rule looks for, and the only one it looks for.

*Example.* Puzzle g = 14, s = 2: Neighbour Agreement 0.98 over 3 neighbours with a different graph.

*Bounds.* −0.5 to 1, as ARI; empty (`no_comparable_neighbours`) without a comparable different-graph neighbour, and empty for a pair without a Selected Partition.

*Compare with.* The pair's Seed-Noise Floor (another seed, same thresholds) and its Subsample Stability (other games): see [Three kinds of stability](#three-kinds-of-stability).

**Exact definition:** `neighbour_agreement` = mean of scikit-learn `adjusted_rand_score` over the in-grid neighbour links with status `ok` and different graph hashes, each on the compared tags; computed once per complete grid, independent of the Pair Constraints.

### Edge Overlap

> **In short.** Edge Overlap: the share of edges two neighbouring pairs' graphs have in common, as a Jaccard overlap of their edge sets.
>
> **Higher →** the step in g or s changed fewer edges; 1 = the same edges.
>
> **Here:** shows how large a perturbation each neighbour link was.
>
> **Caution:** reported only; never enters selection.

Columns: `edge_overlap` in `neighbour_links.csv`.

Edge Overlap is |E₁ ∩ E₂| / |E₁ ∪ E₂| over the two graphs' unweighted edge sets, each tag pair counted once. Edges of tags that a g-step drops count as differences. Edge Overlap describes how much the graph changed, not whether the Clusters are right. A link with Edge Overlap near 1 and a high ARI says little: the clustering had little reason to change.

*Why it matters here.* It puts each link's ARI in context: agreement after a large change of the graph means more than agreement after a small one, which is why Neighbour Agreement tends to be higher at large g.

*Example.* A step that keeps 2 of 3 edges and adds none has Edge Overlap 2/3.

*Bounds.* 0 to 1; empty when neither graph has an edge.

*Compare with.* The link's ARI in `neighbour_links.csv` and its `identical_graph` flag (Edge Overlap 1 with the same tags).

**Exact definition:** `edge_overlap` = |E_p ∩ E_q| / |E_p ∪ E_q| with E the set of (u, v) tag pairs with an edge.

### Information Retention

> **In short.** Information Retention: the share of the dataset's visible tag–game assignments that belong to tags with an edge in the pair's network.
>
> **Higher →** the network keeps more of what the games' tags say.
>
> **Here:** a Pair Constraint (≥ 0.50 by default) keeps the choice from shrinking to a tiny core of tags.
>
> **Caution:** counts assignments, so common tags weigh more than rare ones.

Columns: `retention`, `retention_status`, `games_with_edged_tag_share` in `pairs.csv`.

The numerator sums, over the tags with at least one edge, the number of games that have the tag; the denominator sums the same over the visible tags: every tag of the dataset except hidden and removed ones, including tags below g. Games are counted after the Minimum Months Filter. `games_with_edged_tag_share`, descriptive only, is the share of games with at least one tag that has an edge.

*Why it matters here.* High thresholds give clean, agreeing Clusters by dropping most of the data. Retention measures what is dropped, so the choice cannot win by keeping almost nothing.

*Example.* Puzzle g = 14, s = 2 keeps 31 tags with Retention 0.517: about half of the dataset's visible tag assignments.

*Bounds.* 0 to 1; empty with `no_visible_tags` when nothing is visible.

*Compare with.* The Pair Constraint's minimum, 0.50 by default.

**Exact definition:** `retention` = Σ_{tags with ≥ 1 edge} n_games(t) / Σ_{visible tags} n_games(t), after the Minimum Months Filter.

### Isolated share and LCC share

> **In short.** The isolated share is the share of the network's tags with no edge; the LCC share is the share of tags with an edge that sit in the largest connected component.
>
> **Higher →** isolated share: more tags left alone; LCC share: the network hangs together more.
>
> **Here:** two Pair Constraints keep the chosen network in one piece.
>
> **Caution:** describe the graph, not the Clusters.

Columns: `n_isolated`, `isolated_share`, `n_components`, `lcc_tags`, `lcc_share`, `n_one_isolated`, `n_one_connected` in `pairs.csv`.

These are the pair's Fragmentation figures. Isolated tags are nodes with no edge; each becomes a One-Tag Cluster. The LCC share divides the largest connected component's tags by the tags with an edge, not by all tags, so isolated tags do not count twice. The pair also reports connected components with 2 or more tags, and, from the Selected Partition, its One-Tag Clusters split into isolated and connected ones.

*Why it matters here.* A network in several disconnected pieces is clustered piece by piece, and its Clusters say nothing about how the pieces relate. The constraints (isolated share ≤ 0.10, LCC share ≥ 0.90 by default) keep the choice among networks that hang together.

*Example.* Puzzle g = 14, s = 2: 31 tags, none isolated (isolated share 0), all in one component (LCC share 1.0, as on every pair of this Build). With 1 of 31 tags isolated the share would be 0.03.

*Bounds.* Both 0 to 1; the LCC share is empty without edges.

*Compare with.* The Pair Constraint values.

**Exact definition:** `isolated_share` = tags with no edge / tags; `lcc_share` = tags in the largest connected component / tags with ≥ 1 edge.

### Pair Constraints, Qualifying Pair and the selection rule

> **In short.** A Qualifying Pair has a Selected Partition and meets every Pair Constraint; the chosen pair has the smallest g, then s, among those within the tolerance of the highest Neighbour Agreement.
>
> **Here:** turns the grid into one pair per dataset by a stated rule.
>
> **Caution:** Q, Coverage and Silhouette never enter the choice.

Columns: `qualifies`, `reasons`, `near_best`, `chosen` in `pairs.csv`; `selection.csv`.

The Pair Constraints, all inclusive: Information Retention ≥ 0.50; isolated share ≤ 0.10; LCC share ≥ 0.90; at least 2 comparable neighbours with a different graph; and, off by default, at most a maximum number of Multi-Tag Clusters. The Seed-Noise Floor and the hit count are not constraints. The **near-best set** is every Qualifying Pair whose Neighbour Agreement is at least the highest minus the tolerance (0.05 by default); from it the pair with the smallest g, then the smallest s, is chosen. Every failing reason of a pair is recorded: `no_selected_partition`, `no_neighbour_agreement`, `too_few_comparable_neighbours`, `retention_below_min`, `isolated_share_above_max`, `lcc_share_below_min`, `too_many_clusters` (the heatmap's letters P, A, N, R, I, L, K). When nothing qualifies the status is `no_qualifying_pair`: no pair is chosen and nothing is relaxed. Changing a constraint only re-chooses from the cached grid; non-default values are labelled "Custom constraints". Q, Coverage and Silhouette are descriptive here: not comparable across pairs and never select a pair, because pairs differ in tags and edges.

*Why it matters here.* The constraints rule out pairs that agree with their neighbours only because they keep little data or fall apart; the tolerance and the smallest-g tie-break prefer the larger network among nearly equal pairs, which partly counterbalances Neighbour Agreement's lean towards large g.

*Example.* Under the defaults the chosen pairs are overall g = 17, s = 2; puzzle 14, 2; rpg 7, 5; simulation 14, 5; strategy 14, 2.

*Bounds.* At most one chosen pair per dataset; none under `no_qualifying_pair`.

*Compare with.* The near-best set (orange outlines on the heatmap): the pairs the rule considered nearly equal.

**Exact definition:** near-best = {Qualifying Pairs with NA ≥ max NA − tolerance − 1e-12}; chosen = the near-best pair with the smallest (g, s) in lexicographic order.

### Null Comparison

> **In short.** The chosen pair's procedure repeated on 100 networks whose game–tag table was shuffled, keeping every tag's and game's count.
>
> **Here:** shows whether the dataset's tags have more structure than random tagging with the same counts.
>
> **Caution:** shows that the network is not random, not that its Clusters are real.

Columns: `null_q`, `has_selected_partition`, `reason` in `validation_replicates.csv` (arm `null`).

Each of R = 100 replicates shuffles the games × the pair's network tags with curveball trades (10 per game), exactly as the Workbench's null model, so every tag keeps its number of games and every game its number of tags; the weight is recomputed from the shuffled table. The whole per-pair procedure then runs at the same (g, s): its own scan range, the same 10 scan seeds, CHAMP, γ̂ and the Selected Partition rule (Karrer, Levina & Newman 2008, abstract, §III and §VI: a null is analysed identically). A second arm reads Q at the observed Selected Resolution from each replicate's own envelope, with no extra Leiden runs. The verdict "Q not above the null" appears when at least one replicate reaches the observed Q; otherwise the text says the observed Q is above all replicates. No z-score or p-value is given.

*Why it matters here.* Tag frequencies alone create clusters of a sort: common tags co-occur by chance. If shuffled networks reach the same Q at the same γ, the observed Clusters are no more than what the counts produce.

*Example.* Q at resolution 1.151 is 0.067; no shuffled network reaches it (−0.021 to −0.012); 79 of 100 also have a Selected Partition, with narrower domains.

*Bounds.* Counts are 0 to R.

*Compare with.* The Workbench's null-model baseline (20 replicates at one γ).

**Exact definition:** replicate r shuffles with `random.Random(seed_r)`, seed_r from stream 4 of the main seed; reach = #{r : Q_r(γ_obs) ≥ Q_obs} with Q_r(γ) = (Â − γP̂)/2m of the replicate's envelope partition at γ.

### Subsample Stability

> **In short.** How much the chosen pair's Clusters change when the procedure runs on random 80% subsets of the games, in two arms.
>
> **Higher →** the Clusters depend less on which games are in the dataset.
>
> **Here:** separates Clusters the whole Top 100 carries from those a few games create.
>
> **Caution:** not evidence that the Clusters are real; absent Clusters are never scored 0.

Columns: `ari`, `degenerate`, `degenerate_reason` in `validation_replicates.csv`; `mean_jaccard`, `at_most_half`, `present`, `mean_retention`, `absent`, `dissolved` in `validation_clusters.csv`.

Each of S = 100 subsamples draws m = ⌊0.8·n⌋ of the n games without replacement, with thresholds scaled by floor: g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋). In the **re-selected** arm (the headline) the whole procedure runs again at (g′, s′); **at the Selected Resolution**, the subsample's envelope partition at the observed γ is used. Both are compared with the Selected Partition on the tags in both networks with an edge in either: by ARI, and per Multi-Tag Cluster by Hennig's Jaccard, the best match over every subsample Cluster on those tags, averaged over the B* subsamples where the Cluster has a tag (Hennig 2007, §2). The retention share is the part of each Cluster's tags that are present. A Cluster with no tag present is absent: left out of its mean and counted. Subsamples without edges, or (re-selected arm) without a Selected Partition, are degenerate: counted as "k of S" and left out. A Cluster is "Dissolved" when its mean Jaccard is ≤ 0.5, the only cut used (see [Appendix A](appendix-a-rules-of-thumb.md#cluster-wise-jaccard-stability)).

*Why it matters here.* The Top 100 is one ranked list; a few games more or less should not redraw a combination of characteristics that many games share. A Cluster that dissolves without 20% of the games rests on few of them.

*Example.* Re-selected: median ARI 0.69 (0.57–0.86) over 99 of 100 subsamples; 1 of 4 Multi-Tag Clusters dissolved (mean Jaccard ≤ 0.5).

*Bounds.* ARI −0.5 to 1; Jaccard and retention share 0 to 1.

*Compare with.* Neighbour Agreement (other thresholds, same games) and the Seed-Noise Floor (another seed): see [Three kinds of stability](#three-kinds-of-stability).

**Exact definition:** subsample r draws `random.Random(seed_r).sample(games, m)`, seed_r from stream 5; per Cluster C, J_r = max_D |C′ ∩ D′| / |C′ ∪ D′| over the subsample Clusters D, primes meaning restriction to the comparison set; `mean_jaccard` = mean of J_r over the B* present subsamples; `dissolved` = `mean_jaccard` ≤ 0.5.
