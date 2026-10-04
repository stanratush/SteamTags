# Research 26: User Guide metric reference

Ticket: [User Guide metric reference](../issues/26-user-guide-metric-reference.md)
Date: 2026-10-04

**Question:** For every number the software computes, displays or exports, what should the User Guide say so that a researcher with no training in network analysis reads it correctly?

## How to read this file

- This is the **content** for the guide's metric reference, not its final wording. Layout, the amount of formula notation and whether to print rule-of-thumb bands are decided in [User Guide metric wording and interpretation bands](../issues/27-user-guide-wording-bands.md).
- The inventory was built from the resolved tickets. Where tickets disagree, the later ticket wins: [Seed stability reporting and consensus clustering](../issues/25-clustering-stability.md) overrides [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md), which overrides earlier tickets. Terms follow the glossary, [CONTEXT.md](../../../CONTEXT.md).
- Each metric has its **column name(s)**, its **source ticket**, and six headings:
  1. **Measures**: what it measures.
  2. **Calculation**: this project's exact definition, with a small worked example where the formula is not obvious.
  3. **Reading**: what high and low values mean.
  4. **Range**: theoretical bounds. Typical published values are given only where a cited source gives them. "No typical range published" means I found none.
  5. **Relevance**: why it matters for this study, which looks for recurring tags and tag combinations among the games with the highest **Mean Monthly Players**.
  6. **Limitations**: cases where the number can mislead.
- **Established** statements cite a source in square brackets, e.g. [NG04]. All sources, with how far each was verified, are listed at the end. Statements without a citation are either this project's own definitions (with a ticket link) or plain arithmetic I worked out myself. Worked examples use made-up numbers, not real data.
- "n/a" means an empty cell in the CSVs. A `<metric>_status` column gives the reason where the reason can vary ([Export schemas for the app and the feature analysis](../issues/24-export-schemas.md)).
- Three rules hold for every metric. The guide should state them once, at the top:
  - **No number here shows a cause.** A tag that is frequent among the highest-ranked games, or that co-occurs with another tag more often than chance, is not shown to *make* games reach the top. The Top 100 is a ranked selection, not a random sample, and nothing is compared with games that rank low.
  - **Clusters have no meaning attached.** `C1`, `C2` … are labels by size. The software never names a cluster, and the guide should not invite readers to do so as if it were a finding.
  - **Every network number belongs to one Network State.** The same dataset with different thresholds, hidden tags, Clustering Weight, algorithm, γ or seed gives different numbers. Always quote the `state_id` with a number.

---

## Settings that change the numbers

These are inputs, not metrics. Each changes some results. Values are the shipped defaults.

| Setting (column / config key) | Default | Where set | What it changes |
|---|---|---|---|
| Snapshot collection date → **Observation Window** | latest 60 complete months | fixed per Snapshot | Every score, rank and dataset. |
| Exclusion rules, rank limits, overrides, Manual Metadata Entries | see [Exclusion and genre-tag config contents](../issues/09-exclusion-genre-config.md) | config, per Build | Which games enter the Top-100 Datasets and the Eligible Pool. |
| Listing passes | 2 | `collection.toml` | Candidate Pool size (more passes can catch apps missed by one pass). |
| `max_itemset_size`, `min_support` | 3, 10 games | `analysis.toml` | Which combinations and which tag pairs appear in `combinations.csv` and `associations.csv`. `min_support` also changes how many pairs are tested, and so every `bh_q`. |
| Minimum Months Filter (`min_months`) | 0 (off), app range 0–60 | app | N (games the network is built from), every tag's `n_games`, every edge's `lift`, and so every network number. The feature analysis ignores it. |
| Minimum games per tag (`min_games_per_tag`) | 8, app 1–40 | config + app | Which tags become nodes. |
| Minimum shared games (`min_shared_games`) | 8, app 1–30 | config + app | Which edges exist; which tags end up isolated (One-Tag Clusters). |
| Hidden tags (`hidden_tag_ids`: Genre Tags, the defining tag) and removed tags (`removed_tag_ids`) | Genre Tags and defining tag hidden | config + app | The node set. They do **not** change N or any remaining edge's `lift`. |
| **Clustering Weight** (`clustering_weight`) | `shared_games` (option: `lift`) | config + app | The clustering and every weighted network number: modularity and its null model, coverage, densities, cut weight, conductance, `within_z`, `participation`, `top_strength_tag`, `active_strength`, layout. Not: the shown edge weight, thresholds, silhouette, `medoid_score` (these change only through the partition). |
| Clustering algorithm (`algorithm`) | `louvain` (option: `leiden`) | config + app | The partition and everything computed from it. |
| Resolution γ (`resolution`) | 1.00, app 0.1–3.0 | config + app | The partition (higher γ → more, smaller clusters) and the value of Q. |
| Seed (`seed`) | config value | config + app | The partition (Louvain and Leiden are randomised), the null-model and noise seeds derived from it, and the global layout. |
| Null-model replicates R (`null_replicates`) | 20 | config only | `q_null_mean`, `q_null_sd`, `modularity_z`. |
| Noise seeds K (`noise_seeds`) | 10 | config only | Every `seed_*` value, `membership_stability`, and the `beyond_noise` flags. |
| Resolution Sweep grid (`resolution_sweep`) | 0.50, 0.75, 1.00, 1.25, 1.50 | config, Build only | `resolution_sweep.csv`. |
| Release-month check threshold | 3 months | config | Which games appear in `release_month_check.csv`. |
| Layout (Global / Cluster-separated, Re-layout) | Global, default positions | app | Node positions only. Never any metric. |

---

## 1. Ranking and data

Sources: [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md), [Candidate pool definition](../issues/08-candidate-pool-definition.md), [Pipeline architecture and export schema](../issues/15-pipeline-architecture.md), [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md).

### 1.1 Monthly Avg. Players
Columns: `monthly_players.csv` avg and peak per AppID and month (not published until the Steam Charts operator agrees). Source: [Pipeline architecture and export schema](../issues/15-pipeline-architecture.md).

- **Measures:** Steam Charts' figure for one game in one month: the mean number of people playing at the same moment (concurrent players), averaged over that month. Peak Players is the single highest moment in the month and is stored but never used for ranking.
- **Calculation:** taken as published by Steam Charts. A month row with Avg. 0.00 **and** Peak 0 is a **Placeholder Row**: it is treated as if the row were missing. A row with Avg. 0.00 and Peak ≥ 1 is real data (someone played; the average rounds to zero).
- **Reading:** higher means more people playing at a typical moment that month. It is not a count of different people (not "monthly active users") and not sales.
- **Range:** 0 upwards. No upper bound.
- **Relevance:** the raw input to the success score.
- **Limitations:** a missing month means Steam Charts did not track the game, not that nobody played; it is never filled with zero. Concurrent players favour games that are played for long sessions or left running (e.g. idle games, Desktop Companion apps, which carry a Content Flag) over games played briefly. It says nothing about revenue.

### 1.2 Mean Monthly Players
Column: `mean_monthly_players` (6 decimals) in `top100_<dataset>.csv`. Source: [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md), glossary.

- **Measures:** the study's success score. One number per game.
- **Calculation:** the mean of the game's Monthly Avg. Players values over the months inside the Observation Window, from its Release Month on, that have a value. Missing Months and Placeholder Rows are skipped, not counted as zero.
  - *Example:* a game released in July 2026, in a window ending September 2026, with July 50,000, August 30,000 and September missing, scores (50,000 + 30,000) / 2 = 40,000, with Months Observed = 2.
- **Reading:** higher means more concurrent players on average over the months the game was tracked.
- **Range:** 0 upwards.
- **Relevance:** it decides which games are in each Top-100 Dataset, and so every later number.
- **Limitations:**
  - No minimum number of months is applied when ranking. A game released recently is averaged over its launch months only, when player counts are usually highest. A game released years before the window is averaged over 60 later months. Recent games can therefore rank higher than their long-run level would suggest. Always read the score next to `months_observed`.
  - Games released before the window are judged only on their later life, not their launch.
  - Free-to-Play Games are included (`is_free`). Free games can attract many concurrent players without sales, so "high Mean Monthly Players" is not "high revenue".
  - It describes what happened to these games; it does not show why.

### 1.3 Months Observed
Column: `months_observed`. Source: glossary, [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md).

- **Measures:** how many months the score is averaged over.
- **Calculation:** the number of months from the Release Month to the end of the Observation Window that have a Monthly Avg. Players value (Placeholder Rows and missing months not counted).
- **Reading:** high (close to 60) means the score covers a long stretch of the game's life. Low means a recent release, or a game Steam Charts often did not track.
- **Range:** 1 to 60 for any ranked game. (A game with 0 has no score and cannot rank.)
- **Relevance:** the main check on whether a high score reflects lasting play or a launch spike. The feature-analysis report shows its distribution per dataset. The app's Minimum Months Filter uses it to drop games.
- **Limitations:** a game can have few months because it is new *or* because Steam Charts stopped tracking it for a while. This number alone cannot tell the two apart.

### 1.4 Rank and ties
Columns: `rank` in `top100_<dataset>.csv`; `reports/ties.csv`. Source: [Pipeline architecture and export schema](../issues/15-pipeline-architecture.md).

- **Measures:** a game's position within one Top-100 Dataset.
- **Calculation:** sort by `mean_monthly_players` (highest first), then `months_observed` (more first), then AppID (lowest first). Always exactly 100 rows. Games outside the 100 whose score equals rank 100's are listed in `ties.csv`.
- **Reading:** 1 is the highest score in that dataset.
- **Range:** 1–100.
- **Relevance:** defines membership of the Top 100. Note that the feature analysis counts every game once; it never weights a game by its rank or score.
- **Limitations:** ranks are ordinal. The gap between rank 1 and rank 2 can be far larger than between rank 50 and rank 51. Rank in one dataset is not comparable with rank in another (each has its own Eligible Pool).

### 1.5 Release Month and store release date
Columns: `release_month` (`YYYY-MM`), `store_release_date` (metadata only). Source: [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md).

- **Measures:** the first month Steam Charts has real data for the game.
- **Calculation:** the first month row that is not a Placeholder Row. Tiny nonzero months before the official launch (e.g. a beta) count as data. The store's own release date is stored but never used.
- **Reading / Range:** a calendar month; it can fall before or inside the Observation Window.
- **Relevance:** it fixes which months enter the score.
- **Limitations:** it can differ from the store date (Early Access games show the 1.0 date on the store; small pre-launch months move the Release Month earlier).

### 1.6 Release-month gap
Column: `months_apart` in `reports/release_month_check.csv`. Source: [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md).

- **Measures:** how many months the Release Month and the store release date are apart, for Top-100 members where they differ by more than the threshold (default 3).
- **Calculation:** months between `release_month` and `store_release_date`. Empty when the store date cannot be read (e.g. "Coming soon").
- **Reading:** a diagnostic list for checking data by hand. It never changes a score.
- **Range:** above the threshold by construction.
- **Relevance:** catches games whose score window may start earlier than expected.
- **Limitations:** noisy for Early Access games (e.g. Baldur's Gate 3). Whether the value is signed is not stated in the spec (see Open issues).

### 1.7 Listing rank and the depth check
Column: `top_listing_rank` in `top100_<dataset>.csv`; depth check in `completeness.csv`. Source: [Candidate pool definition](../issues/08-candidate-pool-definition.md), [Pipeline architecture and export schema](../issues/15-pipeline-architecture.md).

- **Measures:** where the game stood in Steam Charts' "Top Games" listing (sorted by *current* players) on the collection date. The best rank across listing passes.
- **Calculation:** read from the listing pages.
- **Reading:** a large number for a Top-100 member means the game ranks high on Mean Monthly Players but had few players at collection time (it has declined).
- **Range:** 1 to the listing length.
- **Relevance:** the depth check shows that declined games were caught, so the Top 100 is not limited to games popular today.
- **Limitations:** it is a snapshot of one day, not a success measure. Do not compare it with `rank`.

### 1.8 Completeness and exclusion counts
Files: `reports/completeness.csv`, `reports/exclusions.csv`, `reports/placeholder_rows.csv`. Source: [Candidate pool definition](../issues/08-candidate-pool-definition.md), [Placeholder rows and the Release Month definition](../issues/16-placeholder-rows-release-month.md), [Exclusion and genre-tag config contents](../issues/09-exclusion-genre-config.md).

- **Measures:** how much of the Candidate Pool reached the ranking, and why the rest did not.
- **Calculation:** counts of listing rows, scored apps and scored apps of type `game`; unscored apps split three ways (no month rows; only Placeholder Rows; rows but none in the window); Placeholder Row count; per listing pass: row count, timestamps and AppIDs seen in only one pass; exclusion counts per reason; for excluded games, the rank they would have had (`exclusions.csv`).
- **Reading:** large unscored counts are expected (the listing includes demos, tools and long-dead apps). The would-be ranks show which excluded games would otherwise be in a Top 100.
- **Range:** counts.
- **Relevance:** they show what the Top 100 is drawn from and how exclusion rules shape it.
- **Limitations:** the pool may hold fewer than 10,000 games of type `game`; this is reported, not fixed. A game counted under several exclusion reasons appears once per reason in `exclusions.csv`.

---

## 2. Feature analysis

Source: [Feature-analysis definitions](../issues/13-feature-analysis-definitions.md); columns from [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md).

Applies to every table here:
- Input is the **full** Top-100 Dataset (the Minimum Months Filter is not applied). N = 100.
- Every game counts once. No weighting by Mean Monthly Players.
- A game **has** a tag if the tag is anywhere in its displayed store tag list (at most 20 tags).
- In the four Tag-Specific Datasets the defining tag (Puzzle, RPG, Strategy, Simulation) is in every game. It is listed in the frequency table at 100% and left out of combinations, associations and clusters.

### 2.1 Tag count and share
Columns: `count`, `share` in `tag_frequency.csv` (also `genre_frequency.csv`).

- **Measures:** how many of the 100 games have the tag.
- **Calculation:** `count` = games with the tag; `share` = count / 100.
- **Reading:** high = the tag is common among these games.
- **Range:** count 1–100 (only tags on at least one game are listed); share 0.01–1.
- **Relevance:** the most direct answer to "which tags recur among the games with the highest Mean Monthly Players?".
- **Limitations:** generic tags (e.g. Singleplayer, Action) are common in every group of games, so a high share alone does not mark something special about the Top 100; read it with `share_ratio`. Tags are community-voted and reflect the store page at collection time, not at release.

### 2.2 Median tag position
Column: `median_position` in `tag_frequency.csv`.

- **Measures:** how prominently the tag is shown on the store pages of the games that have it.
- **Calculation:** for each game with the tag, its position in the displayed tag list (1 = first); then the median over those games.
- **Reading:** low (near 1) = the tag is usually near the front of the list. Steam shows the most-applied tags first and only the top 20 [STEAM-TAGS, via research 04].
- **Range:** 1–20.
- **Relevance:** separates tags that define a game (shown first) from tags that only appear lower down.
- **Limitations:** based on community votes, which include joke votes. For a tag on few games the median rests on very few values. Position does not affect whether a game "has" the tag.

### 2.3 Eligible Pool baseline
Columns: `baseline_count`, `baseline_share` (and the Eligible Pool size in `analysis.json`).

- **Measures:** how common the tag is among all games the Top 100 was drawn from.
- **Calculation:** the same count and share, over the dataset's **Eligible Pool** (all scored, non-excluded games for Overall; those with the defining tag for a Tag-Specific Dataset). The Top 100 is part of the Eligible Pool.
- **Reading:** the "expected" share if the Top 100 looked like the pool it came from.
- **Range:** baseline_share 0–1; baseline_count ≥ count.
- **Relevance:** the reference point that turns a raw share into a comparison.
- **Limitations:** the Eligible Pool includes many games with very few players. It is the pool the Top 100 was drawn from, not "all of Steam" or "all games".

### 2.4 Share ratio
Column: `share_ratio` = `share` / `baseline_share`.

- **Measures:** how over- or under-represented a tag is in the Top 100 compared with its Eligible Pool.
- **Calculation:** *example:* a tag on 63 of the 100 games (0.63) and on 21% of the Eligible Pool (0.21) has share_ratio 3.0.
- **Reading:** above 1 = more common in the Top 100 than in the pool; 1 = the same; below 1 = less common.
- **Range:** above 0; the maximum is (Eligible Pool size) / 100, reached by a tag found only on the 100 games. For a small Eligible Pool (some Tag-Specific Datasets) the ceiling is low.
- **Relevance:** the main frequency-corrected view of "what is typical of the top games".
- **Limitations:**
  - The Top 100 is inside the baseline, which pulls the ratio towards 1, more so when the pool is small.
  - A tag on 2 Top-100 games can show a large ratio by chance; always read it with `count`.
  - Over-representation is a description, not a cause. Games may share a tag because of their genre, their era or Steam's own recommendation system, not because the tag helped them.

### 2.5 Genre frequency
File: `genre_frequency.csv` (`genre_id`, `genre`, `kind`, plus the four measures above).

- **Measures:** the same count, share, baseline and ratio for the store's developer-assigned **Genre** field (not tags).
- **Calculation:** as 2.1–2.4. `kind` (`genre` / `business` / `software`) is a config label; headline sentences use `kind = genre` rows only.
- **Reading / Range / Relevance:** as above.
- **Limitations:** a Genre is not a Tag with the same name. "Puzzle" is not a store genre, so the Puzzle dataset shows no Puzzle genre (the report notes this). "Free to Play" and "Early Access" are business labels, not gameplay.

### 2.6 Combination support
Columns: `support_count`, `support_share` in `combinations.csv` (`size`, `tag_ids`, `tags`).

- **Measures:** how many games have **all** tags of a combination (pairs, triples, … up to `max_itemset_size`, default 3).
- **Calculation:** count of games with every tag in the set; share = count / 100. Only combinations with support ≥ `min_support` (default 10) are listed. A triple is dropped when its support equals that of one of its pairs (it adds no games).
- **Reading:** high = a combination that recurs among these games.
- **Range:** 10–100 for listed rows.
- **Relevance:** the direct answer to "which tag combinations recur?".
- **Limitations:** combinations of two common tags have high support simply because both are common. Use `lift` (2.7) and the association table to see whether they co-occur more than their frequencies predict. Combinations below 10 games are not listed at all.

### 2.7 Combination lift
Column: `lift` in `combinations.csv`.

- **Measures:** whether the tags in a combination occur together more often than their separate frequencies would predict.
- **Calculation:** for a pair, observed ÷ expected co-occurrence: `support_count × 100 / (count_a × count_b)` (equal to the pair lift in 2.11). Brin, Motwani and Silverstein call this "interest" and define it as P(A and B) / (P(A)·P(B)), "with the obvious extension to more than two sets" [BMS97, §3.1]. **The spec does not say which formula is used for triples** (see Open issues).
- **Reading:** above 1 = together more often than independence predicts; 1 = as predicted; below 1 = less often [BMS97, §3.1].
- **Range:** 0 upwards. For a pair, the maximum is 100 / (larger of the two counts).
- **Relevance:** separates combinations that are merely common from combinations that genuinely go together within the Top 100.
- **Limitations:** high lift values tend to come from rare tags ("the cells with high interest have low counts" [BMS97, §3.1]). The `min_support` cut-off of 10 games limits this but does not remove it.

### 2.8 Confidence
Columns: `confidence_a_to_b`, `confidence_b_to_a` (pairs only).

- **Measures:** among games with tag A, the share that also have tag B (and the reverse). This "confidence" is the standard association-rule term [AIS93]; it does not mean certainty.
- **Calculation:** `confidence_a_to_b` = support_count / count_a. *Example:* 40 games have Roguelike, 30 of them also have Action: 0.75. Action is on 70 games, so `confidence_b_to_a` = 30 / 70 = 0.43.
- **Reading:** high = when A is present, B usually is too, in this dataset.
- **Range:** 0–1.
- **Relevance:** shows one-way patterns that a symmetric measure hides (a niche tag that nearly always comes with a broad one).
- **Limitations:** confidence towards a very common tag is always high, whatever the link [BMS97]. "A → B" is a direction of reading, not of cause.

### 2.9 Pair counts
Columns: `count_a`, `count_b`, `count_ab` in `associations.csv`.

- **Measures:** games with tag A, with tag B, and with both. Every pair of tags that each appear on at least `min_support` games is listed, including pairs that never co-occur (`count_ab` = 0).
- **Reading / Range:** counts, 0–100.
- **Relevance:** the raw numbers behind phi, lift, Jaccard and Fisher p. Always shown so a reader can check that a striking measure is not based on a handful of games.
- **Limitations:** none beyond sample size; these are the facts the other four measures summarise.

### 2.10 Phi coefficient
Column: `phi` (the table is sorted by |phi|).

- **Measures:** how strongly two tags go together or apart across the 100 games, as a correlation between two yes/no variables.
- **Calculation:** with p_a = count_a/100, p_b = count_b/100, p_ab = count_ab/100: phi = (p_ab − p_a·p_b) / √(p_a(1−p_a)·p_b(1−p_b)).
  - *Example:* A on 20 games, B on 30, both on 12. Expected together: 6. phi = (0.12 − 0.06) / √(0.2·0.8·0.3·0.7) ≈ 0.33.
- **Reading:** positive = the tags co-occur more than independence predicts; 0 = no association; negative = they tend to exclude each other.
- **Range:** −1 to +1 in theory. In practice the reachable maximum depends on how common each tag is. For p_a ≤ p_b the largest possible phi is √(p_a(1−p_b) / (p_b(1−p_a))). *Example:* a tag on 10 games that **always** comes with a tag on 60 games has phi of only 0.27. Coefficients in this family differ mainly in how they handle the tags' frequencies; dividing phi by its maximum gives Loevinger's H [W08]. No typical range for tag data is published.
- **Relevance:** the primary association measure in the feature analysis. It uses all four cells of the table (both, only A, only B, neither), so it also captures "tends not to appear together".
- **Limitations:** phi is capped by unequal frequencies, so a rare niche tag tied to a common tag looks weak. It is not defined when a tag is on all 100 games (see Open issues). With N = 100, one or two games can move it noticeably.

### 2.11 Pair lift
Column: `lift` in `associations.csv`.

- **Measures:** observed ÷ expected co-occurrence for two tags.
- **Calculation:** `count_ab × 100 / (count_a × count_b)`. *Example (as in 2.10):* 12 × 100 / (20 × 30) = 2.0: they share twice as many games as independence predicts.
- **Reading:** above 1 = together more than chance; below 1 = less; 0 = never together [BMS97, §3.1].
- **Range:** 0 up to 100 / max(count_a, count_b). Two tags each on 10 games that always co-occur reach 10; a tag on 10 games that always comes with a tag on 60 reaches only 1.67.
- **Relevance:** the same quantity as the Clustering Weight's lift mode, so the table and the network agree (exactly when the Minimum Months Filter is 0). It is the "association strength" van Eck and Waltman recommend for normalising co-occurrence data [VEW09], up to a constant factor.
- **Limitations:** lift favours rare pairs; one extra shared game between two rare tags changes it a lot. It ignores games that have neither tag. It is symmetric and says nothing about direction.

### 2.12 Jaccard index
Column: `jaccard`.

- **Measures:** overlap of the two tags' game sets [J1912].
- **Calculation:** count_ab / (count_a + count_b − count_ab). *Example:* 12 / (20 + 30 − 12) ≈ 0.32.
- **Reading:** 1 = exactly the same games; 0 = no games in common.
- **Range:** 0–1. The maximum is min(count_a, count_b) / max(count_a, count_b): 0.17 for tags on 10 and 60 games.
- **Relevance:** an intuitive "how much do these tags overlap?" figure. The same quantity (as 1 − Jaccard) is the distance behind the silhouette, the Cluster Center and Membership Stability's logic, so learning it once helps read those.
- **Limitations:** van Eck and Waltman class Jaccard as a set-theoretic measure that, unlike lift, does not correct for how common each tag is [VEW09]; it is capped when frequencies differ.

### 2.13 Fisher exact p
Column: `fisher_p`.

- **Measures:** how surprising the observed co-occurrence would be if the two tags were placed on games independently, given how many games carry each.
- **Calculation:** two-sided Fisher exact test on the 2 × 2 table (both / only A / only B / neither). The two-sided p is the probability, under independence, of a table "with a probability equal to or less than" that of the observed table [SP-FE]. *Example (as in 2.10):* p ≈ 0.002.
- **Reading:** small = this much (or this little) co-occurrence would be unusual under independence **within these 100 games**.
- **Range:** 0–1.
- **Relevance:** a screen for which associations are larger than small-sample wobble.
- **Limitations:**
  - The Top 100 is not a random sample of anything, so p says nothing about Steam games in general ([Feature-analysis definitions](../issues/13-feature-analysis-definitions.md)).
  - Hundreds or thousands of pairs are tested, so small p values appear by chance; read `bh_q` instead.
  - With N = 100 the test is discrete: many pairs can only reach a few possible p values.
  - The templates never call a result "significant". There is no significance column.

### 2.14 Benjamini–Hochberg q
Column: `bh_q`.

- **Measures:** each pair's p value adjusted for the number of pairs tested in that dataset, using the Benjamini–Hochberg false-discovery-rate procedure [BH95].
- **Calculation:** sort the m p values from smallest to largest; the i-th gets p·m/i, then each value is replaced by the smallest value at or after its position. *Example with four p values* 0.001, 0.01, 0.03, 0.04: q = 0.004, 0.02, 0.04, 0.04. (Checked with SciPy's `false_discovery_control`; statsmodels `multipletests(method="fdr_bh")` implements the same procedure [SM-MT].)
- **Reading:** if you kept every pair with q ≤ 0.05, the expected share of those kept that are chance findings is at most about 5%, under the method's assumptions [BH95]. Lower q = stronger screen result.
- **Range:** 0–1; q ≥ p always.
- **Relevance:** the project's descriptive screen for "co-occurrence unlikely under independence within this dataset" ([Feature-analysis definitions](../issues/13-feature-analysis-definitions.md)).
- **Limitations:**
  - Descriptive only; the guide must not turn it into "significant / not significant".
  - Its value depends on how many pairs were tested, which depends on `min_support`.
  - BH controls the false discovery rate for independent tests and is described as robust under positive correlation [SM-MT]; tag pairs share tags, so the tests are not independent. Benjamini and Yekutieli give a version for arbitrary dependence [BY01]; it is not used here.
  - The column is a BH-adjusted p value. It is not Storey's "q-value", which is a different method.

### 2.15 Content Flag counts
File: `content_flags.csv` (one row per flagged game); per-flag counts in `analysis.json`.

- **Measures:** how many Top-100 games carry each Content Flag (e.g. `desktop_companion`, `sexual_content_tag`), and which.
- **Reading / Range:** counts, 0–100.
- **Relevance:** shows games whose player counts may be inflated by always-on use, or whose content is worth reporting, without excluding them.
- **Limitations:** a flag is not an Exclusion; flagged games are in every other analysis as normal.

---

## 3. Network nodes and edges

Sources: [Edge weight used for clustering](../issues/19-edge-weight-for-clustering.md), [Cluster center and centrality measures](../issues/11-cluster-center-centrality.md), [Silhouette space and cluster-quality metrics](../issues/10-silhouette-cluster-quality.md), [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md).

A short primer the guide needs before this section:
- The **Tag Network** has one node per tag and an edge between two tags when enough games have both.
- N = games in the loaded Top-100 Dataset after the Minimum Months Filter.
- A tag's **game set** is the set of those games that have it.
- **Jaccard distance** between two tags = 1 − Jaccard index of their game sets (2.12). 0 = same games; 1 = no games in common. Silhouette, `medoid_score` and the Cluster Center use it. It does not depend on edges, thresholds or the Clustering Weight.

### 3.1 Edge weight (shared games)
Columns: `shared_games` (and `appids`, `is_intra_cluster`, `source_cluster`, `target_cluster`) in `edges.csv`.

- **Measures:** how many games have both tags.
- **Calculation:** size of the intersection of the two game sets. An edge exists only if it reaches the minimum shared games (default 8). `is_intra_cluster` = both ends in the same cluster.
- **Reading:** thicker / higher = the tags share more games.
- **Range:** min_shared_games up to the smaller tag's `n_games`.
- **Relevance:** the network's basic fact, and the default Clustering Weight.
- **Limitations:** dominated by frequent tags: two tags each on 80 of 100 games share at least 60 games even if unrelated. This is why clusters on the default weight tend to gather around generic tags ([Edge weight used for clustering](../issues/19-edge-weight-for-clustering.md)). The threshold hides every pair below it, so a missing edge does not mean "never together".

### 3.2 Edge lift
Column: `lift` in `edges.csv`. The Clustering Weight in Lift mode.

- **Measures:** observed ÷ expected shared games for the pair, over the N games.
- **Calculation:** `shared_games × N / (n_i × n_j)`. Equal to the pair lift in `associations.csv` when the Minimum Months Filter is 0. Hiding or removing tags does not change it.
- **Reading / Range / Relevance:** as 2.11. Edges with lift below 1 that pass the shared-games threshold are kept, with their lift as weight.
- **Limitations:** as 2.11 (favours rare pairs). Clusters found on lift answer a different question from clusters on shared games: "which tags go together more than their frequency predicts?" rather than "which tags share the most games?".

### 3.3 Tag game count
Column: `n_games` in `nodes.csv` (also in `not_in_network.csv`).

- **Measures:** how many of the N games have the tag.
- **Range:** min_games_per_tag (default 8) up to N for a node; 0 upwards in `not_in_network.csv`.
- **Relevance:** the tag's frequency in the network's games; it drives edge weights and lift.
- **Limitations:** with the Minimum Months Filter at 0 it equals `count` in `tag_frequency.csv`; otherwise it is lower. Not the same as `n_games` in `cluster_quality.csv`, which is N (see Open issues).

### 3.4 Degree and isolated tags
Columns: `degree`, `degree_intra`, `is_isolated`.

- **Measures:** how many other tags a tag is linked to (in the whole network / inside its own cluster).
- **Calculation:** count of edges, ignoring their weight. `is_isolated` = degree 0 (the tag reaches the minimum games per tag but no edge reaches the minimum shared games); it becomes a One-Tag Cluster.
- **Reading:** high = linked to many tags.
- **Range:** 0 to (number of nodes − 1); `degree_intra` 0 to (cluster size − 1).
- **Relevance:** a simple, weight-free view of how broadly a tag combines.
- **Limitations:** tag networks are dense; common tags are linked to almost everything, so high degree mostly reflects frequency. Depends directly on the edge threshold.

### 3.5 Strength (weighted degree)
Columns: `strength_shared`, `strength_lift`, `strength_shared_intra`, `strength_lift_intra`.

- **Measures:** the sum of a tag's edge values, on shared games and on lift, over all edges / over edges inside its cluster [N04, via research 05].
- **Calculation:** *example:* a tag with three edges of 20, 15 and 10 shared games has `strength_shared` = 45. Both versions are always exported, whatever the Clustering Weight; the app shows the active one first.
- **Reading:** high `strength_shared` = shares many games with many tags (strongly tied to frequency). High `strength_lift` = many links that are stronger than chance.
- **Range:** 0 upwards.
- **Relevance:** the frequency-driven view of a tag's place in the network, kept visible on purpose to show how frequency shapes results.
- **Limitations:** `strength_shared` largely restates how common a tag is. `strength_lift` is inflated by rare tags. Neither is an "importance" score.

### 3.6 Per-tag silhouette
Columns: `silhouette`, `silhouette_status` in `nodes.csv`.

- **Measures:** whether a tag's game set is closer to the game sets of its own cluster than to those of the nearest other cluster [R87].
- **Calculation:** a = the tag's mean Jaccard distance to the other members of its cluster; b = the lowest mean Jaccard distance to the members of any other cluster (One-Tag Clusters count as other clusters); s = (b − a) / max(a, b) [R87].
  - *Example:* a = 0.60, b = 0.80 gives s = (0.80 − 0.60) / 0.80 = 0.25.
- **Reading:** near 1 = clearly closer to its own cluster; near 0 = between two clusters; negative = closer, on game overlap, to another cluster than to its own [SHR97].
- **Range:** −1 to 1 [SHR97]. n/a for a One-Tag Cluster member (`one_tag_cluster`) and for every tag when there are fewer than 2 Multi-Tag Clusters (`fewer_than_2_multi_tag_clusters`).
- **Relevance:** shows which tags sit firmly in their cluster and which sit on a border.
- **Limitations:** the clusters were chosen to maximise modularity on graph weights, not to maximise silhouette, so low or negative values are expected and do not prove the cluster wrong ([Graph clustering and quality methods](05-graph-clustering-methods.md) §2). Jaccard distance favours tags of similar frequency: a rare tag can never be close to a very common one (2.12).

### 3.7 Medoid score
Column: `medoid_score`.

- **Measures:** how typical a tag's game set is of its cluster.
- **Calculation:** the tag's mean Jaccard distance to the other members of its cluster (the a of 3.6). *Example:* distances 0.5, 0.6 and 0.7 to three fellow members give 0.6.
- **Reading:** **lower = more typical** (its games overlap most with the others' games).
- **Range:** 0–1. n/a for One-Tag Clusters.
- **Relevance:** the basis of the Cluster Center.
- **Limitations:** independent of the Clustering Weight and algorithm *for a given partition*; it changes whenever the partition changes. In a two-tag cluster both members always have the same score.

### 3.8 Cluster Center
Columns: `is_center` (nodes); `center_tag_id`, `center`, `center_medoid_score`, `center_status` (clusters).

- **Measures:** the most typical tag of a Multi-Tag Cluster of three or more tags.
- **Calculation:** the member with the lowest `medoid_score` (scores compared at 12 decimals; ties → more `n_games`, then lower `tag_id`). It works on disconnected clusters too.
- **Reading:** "the tag whose games overlap most with the other members' games". Not the most frequent, important or central tag in any other sense.
- **Range:** one per cluster of 3+ tags; n/a with `center_status` = `one_tag_cluster` or `two_tag_cluster`.
- **Relevance:** gives a reader one tag to orient by inside each cluster without naming the cluster.
- **Limitations:** with near-equal scores, a tiny data change can swap the center. A center is not a cluster name.

### 3.9 Top-strength tag
Columns: `top_strength_tag_id`, `top_strength_tag`, `center_is_top_strength` (clusters).

- **Measures:** the member with the highest intra-cluster strength on the active Clustering Weight; the frequency-driven alternative to the center.
- **Calculation:** same tie rule and n/a rule as the center.
- **Reading:** `center_is_top_strength = false` means the most typical tag and the most strongly linked tag differ; usually the top-strength tag is a common, generic tag.
- **Relevance:** shows the effect of tag frequency openly.
- **Limitations:** on shared games it mostly reflects frequency (3.5).

### 3.10 Within-cluster degree z-score
Column: `within_z`.

- **Measures:** how much more (or less) strongly a tag is tied to its own cluster than its fellow members are [GA05].
- **Calculation:** (the tag's intra-cluster strength − the cluster's mean intra-cluster strength) / the standard deviation of intra-cluster strength in the cluster [GA05, eq. 3], on the active Clustering Weight. *Example:* members with 10, 20, 30 and 40 give the top member z ≈ 1.34 (population SD) or 1.16 (sample SD); the spec does not say which (see Open issues).
- **Reading:** positive = more strongly tied inside the cluster than average; negative = less.
- **Range:** in a cluster of n tags the largest possible z is √(n−1) with a population SD, (n−1)/√n with a sample SD [SH88]: 1.41 or 1.15 for 3 tags; 3.0 or 2.85 for 10. n/a for One-Tag Clusters and when all members have the same intra-cluster strength (always the case in a two-tag cluster).
- **Relevance:** points to tags that carry their cluster's internal links.
- **Limitations:** small clusters cap the value, so z values from clusters of different sizes are not comparable. On shared games it again tracks frequency.

### 3.11 Participation coefficient
Column: `participation`.

- **Measures:** how evenly a tag's links are spread over clusters [GA05].
- **Calculation:** P = 1 − Σ_s (k_is / k_i)², where k_is is the tag's strength to cluster s and k_i its total strength, on the active Clustering Weight, over every cluster including One-Tag Clusters [GA05].
  - *Example:* strength 30 to its own cluster, 10 to C2 and 10 to C3 (total 50): P = 1 − (0.6² + 0.2² + 0.2²) = 0.56.
- **Reading:** 0 = all links inside its own cluster; higher = links spread over several clusters ("bridge" tags) [GA05].
- **Range:** 0 up to 1 − 1/(number of clusters). n/a at zero strength (isolated tags).
- **Relevance:** answers "which tags connect clusters?".
- **Limitations:** the maximum depends on the number of clusters, so values are not comparable across Network States with different cluster counts. Generic tags linked to everything score high on shared games.

### 3.12 Layout positions
Columns: `x_global`, `y_global`, `x_cluster_separated`, `y_cluster_separated`; `layout_source` in `export.json`.

- **Measures:** where each node is drawn.
- **Calculation:** a seeded force-directed layout (global), or cluster regions laid out separately (cluster-separated).
- **Reading:** a drawing aid only.
- **Range:** arbitrary units.
- **Relevance:** reproducible pictures.
- **Limitations:** distance on screen is **not** a metric. Two tags drawn close together may share few games. Never measure or report positions.

### 3.13 Tags not in the network
Columns: `tag_id`, `tag`, `n_games`, `reasons` in `not_in_network.csv`.

- **Measures:** every tag on at least one game of the loaded dataset that is not a node, and every reason why.
- **Calculation:** reasons in fixed order: `removed`, `defining_tag_hidden`, `genre_tag_hidden`, `below_min_games`.
- **Relevance:** shows what the network leaves out, so readers do not mistake "absent" for "unimportant".
- **Limitations:** a tag below the threshold can still be very common among top games in other datasets; check the frequency table.

---

## 4. Clusters and partition quality

Sources: [Silhouette space and cluster-quality metrics](../issues/10-silhouette-cluster-quality.md), [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md), [Graph clustering and quality methods](05-graph-clustering-methods.md).

A short primer: the clustering ("community detection" in the methods literature) splits the tags into groups that are more tightly linked inside than between. Louvain [B08] and Leiden [T19] both search for the split with the highest **modularity** (4.3). They are randomised searches: different seeds can give different, nearly equally good splits [GMC10]. The **partition** is the full list of which tag is in which cluster.

### 4.1 Cluster counts and sizes
Columns: `n_multi_tag_clusters`, `n_one_tag_clusters` (cluster quality); `kind`, `size` (clusters).

- **Measures:** how many clusters of two or more tags (k) and how many One-Tag Clusters (s) the partition has, and how big each is.
- **Calculation:** always reported as "k multi-tag + s one-tag", never one total.
- **Reading:** One-Tag Clusters are usually isolated tags, not a finding.
- **Range:** k ≥ 0, s ≥ 0.
- **Relevance:** the basic shape of the result.
- **Limitations:** k depends heavily on γ, the thresholds and the seed (see 5.4 and the Resolution Sweep, 5.7). Modularity cannot reliably separate groups whose internal weight is below roughly √(2 × total weight), so small groups can be merged into bigger clusters (the resolution limit [FB07, abstract and §IV]).

### 4.2 Network size
Columns: `n_games` (= N), `n_nodes`, `n_edges`, `total_weight` in `cluster_quality.csv`.

- **Measures:** games after the Minimum Months Filter, tags, edges, and the sum of the active Clustering Weight over all edges.
- **Relevance:** context for every other number; denser networks behave differently (4.4).
- **Limitations:** `total_weight` is in shared games or in summed lift depending on the Clustering Weight; values in the two modes are not comparable.

### 4.3 Modularity Q
Columns: `modularity`, `modularity_status` (`no_edges`).

- **Measures:** how much more of the network's weight falls inside clusters than would be expected if links were spread at random while keeping each tag's total strength [NG04; NX-Q via research 05].
- **Calculation:** Q = Σ over clusters [ (weight inside c) / m − γ · (summed strength of c / 2m)² ], with m = total weight, on the active Clustering Weight, at the active γ. Labelled "Q (γ = 1.00)".
  - *Example (γ = 1):* total weight 100; two clusters each with 40 inside and 20 between them. Each cluster's summed strength is 2·40 + 20 = 100, so Q = 2 × (0.40 − 0.25) = 0.30.
- **Reading:** higher = clusters capture more weight than chance would. 0 = no better than random for this split [NG04, §IV].
- **Range:** at γ = 1 on an unweighted network, −½ to 1 [BDG08, Lemma 3.1]; the maximum reachable value is below 1 and depends on the number of links [FB07, §III]. Isolated tags add nothing [BDG08, Cor. 3.2]. At other γ the value shifts and is not comparable. **Typical published values:** "in practice, values for such networks typically fall in the range from about 0.3 to 0.7. Higher values are rare" [NG04, §IV] (bands table below).
- **Relevance:** the objective the clustering maximises; the headline "how clustered is this network?" number.
- **Limitations:**
  - Random networks with no real groups also reach high Q [GSA04]; that is why the null model (4.4) exists.
  - Many different partitions reach almost the same Q [GMC10].
  - Q is not comparable across γ, Clustering Weights, thresholds or datasets.
  - n/a when the network has no edges.

### 4.4 Null-model baseline
Columns: `q_null_mean`, `q_null_sd` (cluster quality); `null_model.csv` (`replicate`, `seed`, `modularity`, `n_edges`).

- **Measures:** the Q this pipeline produces when the link between games and tags is scrambled, keeping how many tags each game has and how many games each tag has.
- **Calculation:** R = 20 times: shuffle the game–tag table with a curveball/swap randomisation (fixed row and column totals [STR14]), rebuild the network with the same thresholds, recluster with the same algorithm, γ and Clustering Weight, record Q. Report the mean and SD.
- **Reading:** "how much Q would tag frequencies alone produce?". The gap Q − `q_null_mean` is the part of Q not explained by frequency.
- **Range:** like Q.
- **Relevance:** essential with the default shared-games weight, where frequency alone creates structure.
- **Limitations:** the shuffled networks are rebuilt with the same thresholds, so they usually have a different number of edges (`n_edges`) from the real one, and Q depends on network density [GSA04]. 20 replicates give only a rough SD.

### 4.5 Modularity z-score
Column: `modularity_z`.

- **Measures:** how far the real Q is above the null-model mean, in null-model SDs.
- **Calculation:** (Q − `q_null_mean`) / `q_null_sd`. n/a when the SD is 0. *Example:* Q 0.32, null 0.20 ± 0.01 → z = 12.
- **Reading:** large positive = far more structure than tag frequencies alone produce.
- **Range:** any real number. No typical range published for this kind of null model.
- **Relevance:** the single comparison that tells whether the clustering reflects more than tag popularity.
- **Limitations:** with a small null SD, z can be very large even when Q − Q_null is modest; it is not a p value and the null values need not follow a normal curve. Read it with the plain difference (see Open issues).

### 4.6 Coverage and inter-cluster weight share
Columns: `coverage`, `inter_cluster_weight_share`.

- **Measures:** the share of total weight on edges inside clusters, and the rest [F10, via research 05].
- **Calculation:** coverage = intra-cluster weight / total weight; inter share = 1 − coverage. *Example (as in 4.3):* 80 / 100 = 0.80.
- **Reading:** high coverage = most weight is inside clusters.
- **Range:** 0–1.
- **Relevance:** an easy-to-read companion to Q.
- **Limitations:** it rises as clusters get fewer and bigger; one single cluster has coverage 1. Never read it alone.

### 4.7 Disconnected clusters
Columns: `connected` (clusters); `n_disconnected_clusters` (cluster quality).

- **Measures:** whether a cluster's tags can all reach each other through edges inside the cluster.
- **Reading:** `false` = the cluster is two or more separate pieces put under one label.
- **Range:** count ≥ 0. Always 0 in Leiden mode [T19].
- **Relevance:** Louvain can return disconnected clusters (in Traag et al.'s experiments up to 16% of communities [T19, abstract]). For an unweighted network there is always a best-modularity partition whose clusters are all connected [BDG08, Lemma 3.4], so a disconnected cluster is a known Louvain defect, not a finding. The app suggests the Leiden mode.
- **Limitations:** flagged, never split. Silhouette, center and densities are still computed over the whole cluster.

### 4.8 Mean silhouette
Columns: `mean_silhouette`, `silhouette_status` (cluster quality: mean over every Multi-Tag Cluster member; clusters: mean over that cluster's members).

- **Measures:** the average of the per-tag silhouettes (3.6).
- **Calculation:** One-Tag Cluster members are left out of every mean. The overall value averages tags, not clusters, so big clusters weigh more.
- **Reading:** higher = clusters are more separated in terms of game overlap.
- **Range:** −1 to 1. n/a with fewer than 2 Multi-Tag Clusters. Published bands for the related "silhouette coefficient" exist (see the bands table) but were made for a different setting.
- **Relevance:** an independent check on the clustering, using game overlap instead of graph weights. Labelled "descriptive diagnostic, not a selection criterion" ([Silhouette space and cluster-quality metrics](../issues/10-silhouette-cluster-quality.md)).
- **Limitations:** as 3.6. Comparing values across Network States is only indicative ([Graph clustering and quality methods](05-graph-clustering-methods.md) §2).

### 4.9 Internal edges, internal weight and densities
Columns: `internal_edges`, `internal_weight`, `edge_density`, `weighted_density`.

- **Measures:** how tightly linked a cluster is inside [F10, via research 05].
- **Calculation:** for a cluster of n tags there are n(n−1)/2 possible pairs. `edge_density` = internal edges / n(n−1)/2; `weighted_density` = internal weight / n(n−1)/2 (the average weight per possible pair, counting missing edges as 0). *Example:* 5 tags, 8 of 10 possible edges, total internal weight 120 → 0.8 and 12.
- **Reading:** edge density 1 = every pair linked.
- **Range:** edge density 0–1; weighted density 0 upwards (in shared games or lift).
- **Relevance:** shows whether a cluster is a tight group or a loose chain.
- **Limitations:** small clusters reach high density easily. Not defined for One-Tag Clusters (no pairs). Weighted density is in the units of the active Clustering Weight.

### 4.10 Cut weight and conductance
Columns: `cut_weight`, `conductance`.

- **Measures:** how much of a cluster's weight leaks to the rest of the network [KVV04].
- **Calculation:** cut weight = total weight of edges with one end in the cluster and one outside. Volume = sum of members' strengths. Conductance = cut / min(volume of cluster, volume of the rest) [NX-COND]. *Example (as in 4.3):* cut 20, volume 100 and 100 → 0.20.
- **Reading:** low = well separated; high = most of its links go outside.
- **Range:** 0–1. n/a when the rest of the network has zero volume. No typical range published for tag networks.
- **Relevance:** a per-cluster view of separation, which Q gives only for the whole network.
- **Limitations:** an isolated One-Tag Cluster has volume 0, where the formula divides by zero; the spec's n/a rule does not cover this case (see Open issues). On shared games, clusters holding very common tags leak a lot simply because common tags link to everything.

### 4.11 Cluster × cluster connections
Columns: `cluster_a`, `cluster_b`, `edge_count`, `weight` in `cluster_connections.csv`.

- **Measures:** how many edges and how much weight join each pair of Multi-Tag Clusters (zero pairs included), plus each cluster's links to the pooled One-Tag Clusters (`one_tag_pool`).
- **Reading:** large values = the two clusters overlap a lot in their games.
- **Relevance:** shows which clusters sit next to each other.
- **Limitations:** on shared games, big clusters of common tags have large connections to everything; compare with cluster sizes.

---

## 5. Stability

Source: [Seed stability reporting and consensus clustering](../issues/25-clustering-stability.md) (overrides [Node-removal sensitivity method](../issues/12-node-removal-sensitivity.md) on names and timing). Presentation rule already decided: **numbers only, no "stable/unstable" labels, colours or thresholds.**

### 5.1 Adjusted Rand index (ARI) and seed ARI
Columns: `seed_ari_min`, `seed_ari_mean` (cluster quality); `ari_vs_main` in `seed_noise.csv`.

- **Measures:** how similar two partitions of the same tags are, corrected for the agreement expected by chance [HA85]. Here: each of K = 10 extra seeds' partitions compared with the shown (main-seed) partition.
- **Calculation:** `sklearn.metrics.adjusted_rand_score`. Reported: the lowest and the mean of the 10 values. A network with no edges gives every seed the same partition, so all values are 1.
  - *Examples (computed):* 50 tags in 5 clusters of 10. Moving 1 tag to another cluster: ARI 0.95. Moving 2: 0.90. Moving 4: 0.80. Merging two clusters: 0.77. With only 12 tags in 2 clusters, moving 1 tag gives 0.66.
- **Reading:** 1 = identical partitions; about 0 = no more agreement than random labels; negative = less [SK-ARI].
- **Range:** −0.5 to 1 [SK-ARI].
- **Relevance:** shows how much the shown clusters depend on the seed. If another seed gives clearly different clusters, single-cluster findings should be held loosely.
- **Limitations:** ARI drops faster in small networks (the 12-tag example). It is a whole-partition number and does not say which tags moved (see 5.5). K = 10 is a sample of seeds, not all possible ones.

### 5.2 Seed spread of modularity
Column: `seed_modularity_sd`.

- **Measures:** how much Q varies across the 10 extra seeds at the active γ.
- **Reading:** small = the seeds find equally good partitions (they may still differ: see 5.1).
- **Range:** 0 upwards.
- **Relevance:** the yardstick for whether a change in Q (e.g. in Removal Sensitivity) is larger than seed noise.
- **Limitations:** an SD from 10 values is itself rough. Leiden often gives SD 0 or nearly 0, which makes every comparison against it very sensitive (see Open issues).

### 5.3 Seed spread of silhouette
Columns: `seed_silhouette_sd`, `seed_silhouette_status`.

- **Measures:** how much the mean silhouette varies across the seeds that have one.
- **Range:** 0 upwards; n/a when fewer than 2 seeds have a silhouette.
- **Relevance / Limitations:** as 5.2.

### 5.4 Seed range of cluster counts
Columns: `seed_k_min`, `seed_k_max` (cluster quality); `n_multi_tag_clusters`, `n_one_tag_clusters` per seed (`seed_noise.csv`).

- **Measures:** the lowest and highest number of Multi-Tag Clusters across the 10 extra seeds.
- **Reading:** e.g. "5–7" = some seeds split or merge clusters.
- **Relevance:** the most intuitive sign of seed dependence.
- **Limitations:** the count can stay the same while membership changes (read with ARI).

### 5.5 Membership Stability
Column: `membership_stability` in `nodes.csv`.

- **Measures:** how consistently a tag lands with the same other tags across the 10 extra seeds.
- **Calculation:** for each seed, the Jaccard index between the tag's cluster in the main partition (A) and in that seed (B), both including the tag itself: |A ∩ B| / |A ∪ B|. Then the mean over the seeds.
  - *Example:* main cluster {T, a, b, c}. In 8 seeds T's cluster is the same (1.0); in 2 seeds it is {T, a, b} (3/4 = 0.75). Membership Stability = (8 × 1.0 + 2 × 0.75) / 10 = 0.95.
- **Reading:** 1 = the tag's cluster never changed; lower = its companions depend on the seed.
- **Range:** above 0 up to 1.
- **Relevance:** says which individual tags' cluster assignment can be trusted to hold across seeds, and explains a low seed ARI.
- **Limitations:**
  - Descriptive only; it does not say whether a tag or cluster is "real".
  - Cluster size matters: losing one companion costs a two-tag cluster member 0.5 but a twenty-tag cluster member only 0.05.
  - An isolated tag is always alone, so it always scores 1 (see Open issues).
  - Literature bands for a related measure exist (Hennig's cluster-wise Jaccard; see the bands table) but come from a different procedure.

### 5.6 Mean Membership Stability per cluster
Column: `mean_membership_stability` in `clusters.csv`.

- **Measures:** the mean Membership Stability of a cluster's members.
- **Range / Reading:** as 5.5.
- **Limitations:** as 5.5; One-Tag Clusters of isolated tags always show 1.

### 5.7 Resolution Sweep
File: `analysis/resolution_sweep.csv` (Build only): `resolution`, `n_multi_tag_clusters`, `n_one_tag_clusters`, `modularity`, `mean_silhouette`, `silhouette_status`, `ari_vs_report`, `seed_ari_min`, `seed_ari_mean`.

- **Measures:** how the report's clustering changes when only γ changes (0.50–1.50).
- **Calculation:** recluster at each γ with all else fixed; compare with the γ = 1.00 partition by ARI; also compute a Seed-Noise Floor at each γ.
- **Reading:** if cluster counts and `ari_vs_report` change a lot over the grid, the cluster structure depends on the chosen resolution. Compare `ari_vs_report` with `seed_ari_min` at the same γ to see whether the change exceeds seed noise.
- **Range:** as the individual metrics.
- **Relevance:** makes visible that "the" clusters are one view among several (resolution limit [FB07]; degeneracy [GMC10]).
- **Limitations:** the `modularity` column is Q at that row's γ: **values in different rows must not be compared** ([Seed stability reporting and consensus clustering](../issues/25-clustering-stability.md)). Fixed grid, report settings only.

---

## 6. Removal Sensitivity

Source: [Node-removal sensitivity method](../issues/12-node-removal-sensitivity.md); columns from [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md); noise floor from [Seed stability reporting and consensus clustering](../issues/25-clustering-stability.md).

A short primer: for each tag, the software asks "what if this tag were not in the network?" twice, without touching the network you are looking at.
- **Reclustered** (`rc_` columns): drop the tag and its edges, then recluster from scratch with the same settings and main seed. Answers "does the partition depend on this tag?".
- **Fixed partition** (`fp_` columns): drop the tag but keep everyone else in their cluster. Answers "how much does this tag add to the quality of this partition?". No randomness.
- Comparisons use all tags except the removed one. Δ is assumed to be after − before (the spec should state this; see Open issues).
- It describes how much the clustering depends on a tag. It never measures a tag's importance or effect on games.

### 6.1 Identity columns
Columns: `run_order`, `tag_id`, `tag`, `cluster`, `is_center`, `active_strength`.

- **Measures:** which tag the row is about, and its strength on the active Clustering Weight (3.5).
- **Calculation:** tags are processed by `active_strength`, highest first, so a cancelled run has covered the most connected tags.
- **Limitations:** the run order is not a ranking of anything.

### 6.2 Reclustered change in modularity
Column: `rc_delta_modularity`.

- **Measures:** Q of the reclustered network without the tag minus Q of the current state.
- **Reading:** large |Δ| = the clustering's quality depends on this tag.
- **Range:** roughly −1 to 1; usually small.
- **Relevance:** one of three "did it matter?" readings.
- **Limitations:** removing a tag also removes its edges, so total weight drops; part of ΔQ is this mechanical change, not reorganisation (stated in the spec). Compare with `fp_delta_modularity`, which has no reclustering.

### 6.3 Reclustered silhouette after and change
Columns: `rc_silhouette_after`, `rc_silhouette_after_status`, `rc_delta_silhouette`.

- **Measures:** the mean silhouette after reclustering, and its change.
- **Calculation:** if the silhouette moves between a value and n/a, the delta is empty and the app shows e.g. "0.21 → n/a" with the reason.
- **Reading / Range:** as 4.8; Δ between −2 and 2 in theory, small in practice.
- **Limitations:** removing a tag also removes its own silhouette from the mean and changes its neighbours' a and b values, so some change happens even if no tag moves.

### 6.4 Reclustered change in cluster counts
Columns: `rc_delta_k` (Multi-Tag Clusters), `rc_delta_s` (One-Tag Clusters).

- **Measures:** how many clusters appear or disappear.
- **Reading:** e.g. Δk = −1, Δs = +1 can simply mean the tag was one of a two-tag cluster, leaving its partner alone. That is mechanical, not reorganisation.
- **Range:** integers.
- **Limitations:** no noise flag; check `seed_k_min`–`seed_k_max` to see whether such a change also happens across seeds.

### 6.5 Reclustered ARI
Column: `rc_ari`.

- **Measures:** how similar the reclustered partition is to the current one, over the remaining tags (5.1).
- **Reading:** 1 = nobody moved; lower = the partition reorganised without this tag. The table's default sort puts the lowest first.
- **Range:** −0.5 to 1.
- **Relevance:** the main "did removing it reorganise the clusters?" number.
- **Limitations:** removing a tag also changes the order in which the algorithm visits tags, so part of a low ARI can be seed-like noise. Read it against `seed_ari_min`.

### 6.6 Centers lost
Columns: `rc_centers_lost_tag_ids`, `rc_centers_lost`.

- **Measures:** current Cluster Centers (other than the removed tag) that are no longer centers after reclustering.
- **Range:** 0 up to the number of centers.
- **Limitations:** a center is also lost when its cluster shrinks below 3 tags, which can be mechanical. Centers with near-tied `medoid_score` swap easily.

### 6.7 Fixed-partition change in modularity
Column: `fp_delta_modularity`.

- **Measures:** Q without the tag, everyone else kept in place, minus current Q.
- **Reading:** negative = the tag added to the partition's quality; positive = Q is higher without it (the tag fit its cluster poorly).
- **Relevance:** a noise-free reading of the tag's contribution.
- **Limitations:** includes the same weight-loss effect as 6.2. No flag.

### 6.8 Fixed-partition silhouette after and change
Columns: `fp_silhouette_after`, `fp_silhouette_after_status`, `fp_delta_silhouette`.

- **Measures:** mean silhouette without the tag, partition fixed, and its change.
- **Reading:** positive Δ = the tag was pulling the mean down (it fit its cluster poorly on game overlap).
- **Limitations:** as 6.3, without the reclustering part.

### 6.9 Beyond-noise flag
Column: `rc_beyond_noise` (a `;`-list of `ari`, `modularity`, `silhouette`).

- **Measures:** which reclustered readings exceed the Seed-Noise Floor.
- **Calculation:**
  - modularity, silhouette: |Δ| > 2√2 × the seed SD (the difference of two single runs varies about √2 times as much as one run).
  - ARI: below `seed_ari_min`.
  - No flag on Δk, Δs, centers lost or the fixed-partition columns.
  - *Example:* `seed_modularity_sd` = 0.004 → threshold 2√2 × 0.004 ≈ 0.011.
- **Reading:** a **screening aid**: "look at this tag first". Not a significance test.
- **Range:** empty, or one to three names.
- **Relevance:** narrows a long table to the tags whose removal changed the clustering more than a seed change does.
- **Limitations:**
  - Some flags are expected by chance. If removing a tag acted only like another random seed, its ARI would fall below the lowest of 10 seed ARIs about 1 time in 11 (≈ 9%), so roughly 4–5 of 50 tags would be flagged on ARI alone. (This is my arithmetic, assuming the removal run behaves like an 11th seed.)
  - When the seed SD is 0, any non-zero ΔQ is flagged, and ΔQ is almost never 0 after a removal (6.2). See Open issues.

---

## Bands offered in the literature

Recorded so [User Guide metric wording and interpretation bands](../issues/27-user-guide-wording-bands.md) can decide whether to print any. **None of these was calibrated on tag co-occurrence networks.** Several clash with the decision that stability numbers carry no labels.

| Metric here | Band as published | Source (verification) | Caveats for this project |
|---|---|---|---|
| Modularity Q | "values for such networks typically fall in the range from about 0.3 to 0.7. Higher values are rare." | [NG04] §IV (full text checked) | Unweighted networks, γ = 1. Random networks also reach high Q [GSA04]. Max Q depends on network size [FB07]. Not valid at γ ≠ 1 or in lift mode without care. |
| Modularity Q | a value above about 0.3 is "a good indicator of significant community structure" | [CNM04] §II (full text checked) | Same caveats. Contradicted in spirit by [GSA04], which shows random graphs exceed such values. |
| Modularity Q | "Usually, a value of Q larger than 0.3 − 0.4 is a clear indication that the subgraphs of the corresponding partition are modules." | [FB07] §II, arXiv version (full text checked) | The same paper immediately warns that the maximum Q differs between networks and depends on the number of links. |
| Mean silhouette | Silhouette coefficient 0.71–1.00 strong structure; 0.51–0.70 reasonable; 0.26–0.50 weak, could be artificial; ≤ 0.25 no substantial structure | [SHR97] Table 2 (full text checked), citing [KR90] (page not checked) | Described by its authors as a "subjective interpretation". Made for the silhouette **coefficient** (the best average silhouette over several k) of partitioning methods such as PAM, not for one modularity partition scored on Jaccard distance. Expect lower values here, because the partition does not optimise silhouette. |
| ARI (seed ARI, `rc_ari`, `ari_vs_report`) | ≥ 0.90 excellent; 0.80–0.90 good; 0.65–0.80 moderate; < 0.65 poor recovery | [ST04] (bibliographic record checked; **band values seen only in secondary sources**, not in the article) | Calibrated for recovering known true clusters in simulations, not for agreement between seeds. In small networks one moved tag already drops ARI to "moderate" (12 tags: 0.66). Clashes with the no-label decision. |
| Membership Stability (analogue) | Cluster-wise mean Jaccard ≤ 0.5: "dissolved"; < 0.6 not to be trusted; 0.6–0.75 patterns but doubtful membership; ≥ 0.75 valid, stable; ≥ 0.85 highly stable | [H07] (full text preprint: ≤ 0.5 dissolution, > 0.75 "good recoveries, say"); [FPC] clusterboot documentation for the 0.6 / 0.75 / 0.85 wording | Hennig's measure is per cluster under bootstrap resampling of the data; ours is per tag across seeds on fixed data. Isolated tags always score 1 here. Clashes with the no-label decision. |
| `within_z`, `participation` | Hubs z ≥ 2.5; non-hubs: R1 P ≤ 0.05, R2 0.05–0.62, R3 0.62–0.80, R4 > 0.80; hubs: R5 P ≤ 0.30, R6 0.30–0.75, R7 > 0.75 | [GA05] (full text checked; the authors call the regions "heuristic") | Derived from metabolic networks with large modules. z ≥ 2.5 is impossible in clusters of fewer than 8 tags (population SD) or 9 (sample SD) [SH88]. Uses the word "hub", which the glossary avoids for Cluster Centers. |
| phi | Effect size w (= \|phi\| for a 2 × 2 table): 0.10 small, 0.30 medium, 0.50 large | [COH92] (bibliographic record checked; **values seen only in secondary sources**) | Made for power analysis in behavioural science. phi's ceiling depends on tag frequencies (2.10), so "small" may be the maximum possible for a rare tag. |
| Lift, phi, Fisher p, BH q | Reference points only: lift 1 and phi 0 = independence [BMS97]; conventional 0.05 cut-offs for p or q | [BMS97] §3.1; [BH95] | The spec already rules out significance cut-offs. Reference points are bounds, not bands. |
| Conductance, densities, coverage, Q z-score, Seed-Noise Floor SDs, `share_ratio`, `median_position` | **No bands found.** | — | — |

Typical values in comparable work: Li and Zhang (2020) built a Steam tag co-occurrence network and used Louvain [LZ20]. I could not access the full text, so I do not know whether it reports Q or other values. I found no other published Q, silhouette or ARI values for Steam tag networks.

---

## Open issues for the researcher

For [User Guide metric wording and interpretation bands](../issues/27-user-guide-wording-bands.md). Not decided here.

1. **The `beyond_noise` flag on modularity and silhouette compares unlike things.** A reclustered ΔQ or Δsilhouette always contains a mechanical part, because the network lost a tag and its edges (6.2, 6.3). The seed SD measures only seed noise on the unchanged network. So high-strength tags are likely to be flagged whatever happens to the clusters. When the seed SD is 0 (likely in Leiden mode, or in seed-stable states), **every** tag with a non-zero ΔQ is flagged. Options include: comparing the reclustered reading with the fixed-partition one, flagging rc − fp, or limiting the flag to ARI.
2. **Expected chance flags on ARI are not stated.** With K = 10, a removal that behaves like one more seed falls below `seed_ari_min` about 1 time in 11. That is about 9% of tags, or 4–5 of 50. The report sentence "how many tags are beyond noise" should give this, or the rule should change.
3. **Combination `lift` for triples is undefined.** [Feature-analysis definitions](../issues/13-feature-analysis-definitions.md) gives lift for itemsets up to size 3, but only the pair formula exists in the tickets. A common choice is support × N² / (count_a × count_b × count_c) [BMS97, §3.1 "obvious extension"]. Rule-based alternatives exist.
4. **The same column name means different things in different files.**
   - `lift`: combinations (itemset, full Top 100), associations (pair, full Top 100), edges (pair, after the Minimum Months Filter).
   - `n_games`: tag count in `nodes.csv` / `not_in_network.csv`, but N in `cluster_quality.csv`.
   - `mean_silhouette`: per cluster in `clusters.csv`, across all Multi-Tag Cluster members in `cluster_quality.csv`.
   - `modularity`: in `resolution_sweep.csv` it is at a different γ per row, and the rows must not be compared.

   Rename the columns, or rely on the guide and column descriptions?
5. **Conductance and density are undefined for One-Tag Clusters, and the spec does not cover it.** An isolated tag's cluster has volume 0, so `cut / min(vol(C), vol(rest))` divides by zero. NetworkX 3.4.2 `conductance` raises an error there (source checked [NX-COND]). The spec's n/a rule only names vol(rest) = 0. Edge and weighted density divide by n(n−1)/2 = 0 for a size-1 cluster. Probably meant to be "fixed-cause n/a", but the schema should say so.
6. **phi has no n/a rule.** It is undefined when a tag is on all 100 games. That is possible for common tags in a Tag-Specific Dataset (the defining tag itself is excluded). Lift and Jaccard stay defined. A `phi_status` column or a rule is needed.
7. **Unstated conventions the guide cannot explain until they are fixed:**
   - the sign of every Δ column (assumed after − before);
   - population or sample SD for `within_z`, `q_null_sd` and the `seed_*_sd` values;
   - whether `months_apart` is signed;
   - the reason code for `seed_silhouette_status`, which is missing from the status list in [Export schemas for the app and the feature analysis](../issues/24-export-schemas.md).
8. **`modularity_z` invites over-reading.** With R = 20 and a small null SD, z can be very large even when Q − Q_null is modest. The null networks also have different edge counts (`null_model.csv` `n_edges`). Should the UI and report show Q − `q_null_mean` and the null edge count beside z?
9. **Membership Stability is 1 for isolated tags.** It is structurally 1 for every isolated tag, and 1 for their One-Tag Cluster's `mean_membership_stability`. Tables sorted by stability will show these tags as the most stable. Should they be n/a? Also, the same single change costs small-cluster members far more (5.5).
10. **`within_z` in small clusters.** Its maximum is about √(n−1) (3.10). In the 3–7-tag clusters the defaults produce, values are compressed and not comparable across clusters. GA05's role bands cannot apply. Show it only for clusters above some size, or keep it with a warning?
11. **The `share_ratio` baseline includes the Top 100 itself** (2.4). This pulls ratios towards 1 and caps them at pool size / 100, which is low for small Tag-Specific Eligible Pools. Keep it (decided in [Feature-analysis definitions](../issues/13-feature-analysis-definitions.md)), or compare against the Eligible Pool minus the Top 100?
12. **The bands themselves.** If issue 27 prints silhouette bands, a modularity partition scored on Jaccard distance will often land in "weak" or "no substantial structure" by construction (4.8). The ARI and cluster-wise-Jaccard bands clash with the decided no-label rule for the Seed-Noise Floor and Membership Stability.

---

## Sources

Verification levels:
- **Full text**: I read the passage cited in the paper or official document.
- **Abstract**: I read the publisher's abstract only.
- **Bibliographic**: authors, year, title, venue, volume and pages were confirmed against Crossref, but the content cited was not checked in the original.
- **Not verified**: see the note.

| Key | Reference | Status |
|---|---|---|
| [AIS93] | Agrawal, R., Imieliński, T., Swami, A. (1993). Mining association rules between sets of items in large databases. *Proc. 1993 ACM SIGMOD*, 207–216. doi:10.1145/170035.170072 | Bibliographic. |
| [B08] | Blondel, V. D., Guillaume, J.-L., Lambiotte, R., Lefebvre, E. (2008). Fast unfolding of communities in large networks. *J. Stat. Mech.* P10008. doi:10.1088/1742-5468/2008/10/P10008 | Bibliographic (content checked in research 05). |
| [BDG08] | Brandes, U., Delling, D., Gaertler, M., Görke, R., Hoefer, M., Nikoloski, Z., Wagner, D. (2008). On modularity clustering. *IEEE Trans. Knowl. Data Eng.* 20(2), 172–188. doi:10.1109/TKDE.2007.190689 | Full text (author PDF): Lemma 3.1 (−½ ≤ Q ≤ 1, unweighted), Corollary 3.2, Lemma 3.4. |
| [BH95] | Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J. R. Stat. Soc. B* 57(1), 289–300. doi:10.1111/j.2517-6161.1995.tb02031.x | Bibliographic; procedure checked numerically against SciPy `false_discovery_control`. |
| [BMS97] | Brin, S., Motwani, R., Silverstein, C. (1997). Beyond market baskets: generalizing association rules to correlations. *Proc. 1997 ACM SIGMOD*, 265–276. doi:10.1145/253260.253327 | Full text: §3.1 (interest = P(A∧B)/(P(A)P(B)), extension to more sets, >1 / <1 reading, high interest with low counts). |
| [BY01] | Benjamini, Y., Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under dependency. *Ann. Stat.* 29(4), 1165–1188. doi:10.1214/aos/1013699998 | Bibliographic. |
| [CNM04] | Clauset, A., Newman, M. E. J., Moore, C. (2004). Finding community structure in very large networks. *Phys. Rev. E* 70, 066111. doi:10.1103/PhysRevE.70.066111 | Full text (arXiv cond-mat/0408187), §II quote. |
| [COH92] | Cohen, J. (1992). A power primer. *Psychol. Bull.* 112(1), 155–159. doi:10.1037/0033-2909.112.1.155 | Bibliographic. Band values (w = .10/.30/.50) **not verified** in the original; seen only in secondary sources. |
| [F10] | Fortunato, S. (2010). Community detection in graphs. *Physics Reports* 486(3–5), 75–174. doi:10.1016/j.physrep.2009.11.002 | Bibliographic. |
| [FB07] | Fortunato, S., Barthélemy, M. (2007). Resolution limit in community detection. *PNAS* 104(1), 36–41. doi:10.1073/pnas.0605965104 | Full text (arXiv physics/0607100v2): abstract (√(2L) scale), §II quote, §III (max Q depends on L). Section numbers are the arXiv version's. |
| [FPC] | Hennig, C. `fpc` R package, `clusterboot` reference page. https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html | Full text (stability wording). |
| [GA05] | Guimerà, R., Nunes Amaral, L. A. (2005). Functional cartography of complex metabolic networks. *Nature* 433, 895–900. doi:10.1038/nature03288 | Full text (arXiv q-bio/0502035): role regions, eq. 3 (z), participation definition. |
| [GMC10] | Good, B. H., de Montjoye, Y.-A., Clauset, A. (2010). Performance of modularity maximization in practical contexts. *Phys. Rev. E* 81, 046106. doi:10.1103/PhysRevE.81.046106 | Bibliographic (content checked in research 05). |
| [GSA04] | Guimerà, R., Sales-Pardo, M., Amaral, L. A. N. (2004). Modularity from fluctuations in random graphs and complex networks. *Phys. Rev. E* 70, 025101(R). doi:10.1103/PhysRevE.70.025101 | Full text (arXiv cond-mat/0403660): random and scale-free graphs have high modularity; modularity falls with density (Fig. 1). |
| [H07] | Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Comput. Stat. Data Anal.* 52(1), 258–271. doi:10.1016/j.csda.2006.11.025 | Full text (author preprint): dissolution ≤ 0.5, "good recoveries" > 0.75 "say". |
| [HA85] | Hubert, L., Arabie, P. (1985). Comparing partitions. *J. Classification* 2(1), 193–218. doi:10.1007/BF01908075 | Bibliographic (chance-correction behaviour via [SK-ARI]). |
| [J1912] | Jaccard, P. (1912). The distribution of the flora in the alpine zone. *New Phytologist* 11(2), 37–50. doi:10.1111/j.1469-8137.1912.tb05611.x | Bibliographic. |
| [KR90] | Kaufman, L., Rousseeuw, P. J. (1990). *Finding Groups in Data: An Introduction to Cluster Analysis*. Wiley. | **Not verified.** The silhouette bands are often cited to p. 88; I confirmed them only through [SHR97]. |
| [KVV04] | Kannan, R., Vempala, S., Vetta, A. (2004). On clusterings: good, bad and spectral. *J. ACM* 51(3), 497–515. doi:10.1145/990308.990313 | Bibliographic. |
| [LZ20] | Li, X., Zhang, B. (2020). A preliminary network analysis on Steam game tags. *Proc. 23rd Int. Conf. on Academic Mindtrek*, 65–73. doi:10.1145/3377290.3377300 | Bibliographic; full text not accessible. That it uses Louvain comes from a search-result summary only. |
| [N04] | Newman, M. E. J. (2004). Analysis of weighted networks. *Phys. Rev. E* 70, 056131. | Checked in research 05. |
| [NG04] | Newman, M. E. J., Girvan, M. (2004). Finding and evaluating community structure in networks. *Phys. Rev. E* 69, 026113. doi:10.1103/PhysRevE.69.026113 | Full text (arXiv cond-mat/0308217): §IV (Q = 0 no better than random; 0.3–0.7 typical). |
| [NX-COND] | NetworkX `conductance` documentation and source (3.4.2 installed here): `cut / min(volume_S, volume_T)`. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cuts.conductance.html | Full text and source. |
| [NX-Q] | NetworkX `modularity` documentation. | Checked in research 05. |
| [R87] | Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *J. Comput. Appl. Math.* 20, 53–65. doi:10.1016/0377-0427(87)90125-7 | Bibliographic; definition and range confirmed in [SHR97]. |
| [SH88] | Shiffler, R. E. (1988). Maximum Z scores and outliers. *Am. Stat.* 42(1), 79–80. doi:10.1080/00031305.1988.10475530 | Bibliographic; the bound was checked numerically here. |
| [SHR97] | Struyf, A., Hubert, M., Rousseeuw, P. J. (1997). Clustering in an object-oriented environment. *J. Stat. Softw.* 1(4), 1–30. doi:10.18637/jss.v001.i04 | Full text: s(i) definition, −1…1, Table 2 bands, "subjective interpretation". |
| [SK-ARI] | scikit-learn `adjusted_rand_score` documentation. https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html | Full text ("between -0.5 and 1.0"; random ≈ 0). Examples recomputed with scikit-learn 1.6.1. |
| [SM-MT] | statsmodels `multipletests` documentation. https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html | Full text (fdr_bh; robustness note). |
| [SP-FE] | SciPy `fisher_exact` documentation. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html | Full text (two-sided definition). Example recomputed with SciPy 1.15.2. |
| [ST04] | Steinley, D. (2004). Properties of the Hubert–Arabie adjusted Rand index. *Psychol. Methods* 9(3), 386–396. doi:10.1037/1082-989X.9.3.386 | Bibliographic. The ARI bands are **not verified** in the article; seen only in secondary sources. |
| [STEAM-TAGS] | Steamworks documentation, Steam Tags (as quoted in [Official Steam tag taxonomy extraction](04-steam-tag-taxonomy.md)). | Checked in research 04. |
| [STR14] | Strona, G., Nappo, D., Boccacci, F., Fattorini, S., San-Miguel-Ayanz, J. (2014). A fast and unbiased procedure to randomize ecological binary matrices with fixed row and column totals. *Nature Communications* 5, 4114. doi:10.1038/ncomms5114 | Bibliographic (all five authors and article number confirmed on Crossref). |
| [T19] | Traag, V. A., Waltman, L., van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. *Sci. Rep.* 9, 5233. doi:10.1038/s41598-019-41695-z | Full text (arXiv 1810.08473): abstract (25% / 16%), §II A. |
| [VEW09] | van Eck, N. J., Waltman, L. (2009). How to normalize cooccurrence data? An analysis of some well-known similarity measures. *JASIST* 60(8), 1635–1651. doi:10.1002/asi.21075 | Abstract (association strength probabilistic; Jaccard set-theoretic; probabilistic measures recommended). |
| [W08] | Warrens, M. J. (2008). On association coefficients for 2×2 tables and properties that do not depend on the marginal distributions. *Psychometrika* 73(4), 777–789. doi:10.1007/s11336-008-9070-3 | Abstract. The phi-maximum formula in 2.10 is my own derivation from the phi definition. |

Earlier research-05 references now checked: [GSA04] and [GA05] (full text); [HA85], [KVV04], [KLN08] and [RB06] (bibliographic); [VEW09] (abstract). Still unchecked: [KR90] (page) and [M07] (not cited here). [KLN08] is Karrer, B., Levina, E., Newman, M. E. J. (2008), *Phys. Rev. E* 77, 046119, doi:10.1103/PhysRevE.77.046119. [RB06] is Reichardt, J., Bornholdt, S. (2006), *Phys. Rev. E* 74, 016110, doi:10.1103/PhysRevE.74.016110. Neither is cited above.
