# Build settings by layer

Every setting a Build reads, as of commit `1961b66` (2026-11-05), grouped by what changing it does. A Build reads eight config files (`BUILD_FILES` in `src/steamstudy/config.py`), all copied into `build.json`. `collection.toml` belongs to Collect only and is not a Build setting.

## 0. Fixed by the Snapshot (no setting)

| Rule | Value | Where |
|---|---|---|
| Observation Window | the latest complete 60 months before the collection date (2021-10 to 2026-09) | `snapshot.py:251`; the 60 is hard-coded |
| Store country, tag vocabulary version | `BG`, taglist hash `711684454` | `snapshot.json` |

## 1. Changes which games make the Top-N (needs the Snapshot)

| File | Setting | Value |
|---|---|---|
| `datasets.toml` | `dataset[]`: `key`, `label`, `defining_tag` | Overall (none), Puzzle 1664, RPG 122, Strategy 9, Simulation 599 |
| `exclusions.toml` | `allowed_app_types` | `["game"]` |
| | `global_rank_limit` | `20` (anywhere) |
| | `per_tag_rank_limit` | empty |
| | `adult_content.content_descriptor_ids`, `.tags` | `[3]`, Hentai |
| | `software_tag.tags`, `.name_only` | 9 tags; GameMaker, RPGMaker, Web Publishing |
| | `dating_sim_tag.tags` | Dating Sim |
| `manual_exclusions.toml` | `exclusion[]` | empty |
| `exclusion_overrides.toml` | `override[]` | empty |
| `manual_metadata.toml` | `entry[]` | empty |
| hard-coded | list size | `TOP_N = 100` (`build/datasets.py:13`) |
| | ranking score | Mean Monthly Players |
| | scoring rules | Placeholder Rows ignored, Release Month, Missing Months |
| | "a game has a tag" | anywhere in its displayed list (max 20); no setting |

## 2. Reports and flags only (the Top-N is unchanged)

| File | Setting | Value | Affects |
|---|---|---|---|
| `exclusions.toml` | `content_flags.desktop_companion` | Desktop Companion | Content Flag |
| | `content_flags.sexual_content_tag` | Sexual Content, Nudity, Sexual Themes; NSFW | Content Flag |
| `genres.toml` | `genre_tags` | the 11 Top-Level Genres | which tags the app can hide |
| | `genre_kind` | store genre id → genre / business / software | `genre_frequency.csv` |
| `analysis.toml` | `max_itemset_size` | `3` | `combinations.csv` |
| | `min_support` | `10` | `combinations.csv`, `associations.csv` |
| | `release_month_check` | `3` | `release_month_check.csv` |
| | `causal_words` | drives, leads to, … | the Build fails if a report uses one |

Content Flags and the Eligible Pool baselines (`tag_frequency.csv`, `genre_frequency.csv`) read tags of games outside the Top-N, so they also need the Snapshot.

## 3. Network defaults (`network.toml`)

| Setting | Value | Used by |
|---|---|---|
| `min_games_per_tag`, `min_shared_games`, `min_months` | `8`, `8`, `0` | Build report; app start values |
| `hide_genre_tags`, `hide_defining_tag` | `true`, `true` | same |
| `clustering_weight`, `algorithm`, `resolution`, `seed` | `shared_games`, `louvain`, `1.0`, `20261003` | same |
| `null_replicates`, `noise_seeds` | `20`, `10` | same |
| `resolution_sweep` | `[0.50, 0.75, 1.00, 1.25, 1.50]` | Build report only |
| `parameter_selection` Selection Settings | `lift`, `min_months 0`, `min_multi_tag_clusters 3`, `g_range [3,20]`, `s_range [2,12]`, `gamma_step 0.05`, `scan_seeds 10`, `null_replicates 100`, `subsamples 100`, `workers 0` | Parameter Selection mode, bundle maker; in the cache key |
| `parameter_selection` Pair Constraints | `tolerance 0.05`, `min_retention 0.50`, `max_isolated_share 0.10`, `min_lcc_share 0.90`, `min_comparable_neighbours 2`, `max_multi_tag_clusters 0` | same; never in a cache key |

## What a Build keeps from its Snapshot

Measured on the full Build `20261008T221504Z-7a23ae9f`: the five Top-100 Datasets (352 distinct games, each with its full ordered tag list); monthly players for those 352 games; Eligible Pool tag totals only (Overall pool 8,776 games), not each pool game's tags. So no layer-1 setting can be rebuilt from a Build alone. The Snapshot is 509 MB (store 422 MB, Steam Charts 78 MB); a Build is 4–30 MB.
