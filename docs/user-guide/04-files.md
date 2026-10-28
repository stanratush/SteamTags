# What's in each file

Every CSV is UTF-8 with a byte-order mark, comma-separated, with one header row and no metadata rows. Booleans are `true` / `false`, lists are `;`-separated (an id list always comes with the matching name list), and an empty cell means n/a. Each column's meaning is in the [metric reference](03-metric-reference.md) and the [column index](appendix-b-column-index.md).

A Build folder (`builds/<snapshot_id>/<build_id>/`) holds `datasets/`, `reports/` and `analysis/`. The app's export zip holds one Network State's tables plus `export.json`.

## Build: datasets/

### `top100_<dataset>.csv`

One row is one game in one Top-100 Dataset (Overall, Puzzle, RPG, Strategy or Simulation), in rank order: its score, months observed, Release Month, store details, displayed tags and genres, Content Flags and best listing rank. It joins to every other file by `appid`, and to the network files through its tags (`tag_ids`). It is the published dataset and the app's only input.

### `monthly_players.csv`

One row is one month of one game that is a member of any Top-100 Dataset: the Monthly Avg. Players and Peak Players behind its score (only the months the score averages; never a Placeholder Row). It joins to `top100_<dataset>.csv` by `appid` and lets anyone recompute `mean_monthly_players`. It is not published until the Steam Charts operator agrees.

## Build: reports/

### `exclusions.csv`

One row is one excluded game and one exclusion rule it matched, with the rule's detail, the game's primary reason and the rank it would have taken in each dataset. It joins to the datasets by `appid`. It documents every Exclusion, and it doubles as the list of excluded games that would have scored inside a Top 100.

### `completeness.csv`

One row is one count: listing rows and passes, Candidate Pool size, scored and unscored apps by reason, Placeholder Rows, exclusion counts (overlapping and by primary reason) and the depth check per dataset. It joins to nothing; it is the evidence of what the Top 100 was drawn from.

### `placeholder_rows.csv`

One row is one Placeholder Row (Avg. 0.00 and Peak 0) of one app in the Candidate Pool, with its month and its position relative to the app's real data. It joins by `appid`. It lets readers audit the placeholder rule.

### `ties.csv`

One row is one game outside a Top 100 whose score equals rank 100's, with the position it takes after the tie-break. It joins to `top100_<dataset>.csv` by `dataset`. It shows how the cut at rank 100 falls.

### `skipped_apps.csv`

One row is one app skipped during collection because its Steam Charts page kept failing to load (every retry used up) or could not be parsed: its AppID, listing name, the page URL, the reason, the last HTTP status and when it was skipped. Collect writes it next to `snapshot.json`, and every Build copies it into `reports/`. Skipped apps have no score and cannot rank; `completeness.csv` counts them as `unscored_skipped`. It joins to the Snapshot's listing by `appid`.

### `parse_errors.csv`

One row is one response a parser could not read: which app, which kind of page, where it is in the Snapshot and the error. Any row fails the Build unless `--allow-parse-errors` was given. It is empty in a publishable Build.

### `release_month_check.csv`

One row is one Top-100 game whose Release Month and store release date are more than the configured number of months apart, or whose store date cannot be read. It joins by `appid`. It is a diagnostic for checking histories by hand and never changes a score.

### `tag_vocabulary.csv`

One row is one distinct tag or store genre seen on a scored app, with how many apps show it and, for tags, whether its id is in the `GetTagList` snapshot. It joins to the datasets through tag and genre ids. It catches config drift and spelling changes.

### `impact_removals.csv`

One row is one removal by one exclusion rule and one tag or signal, with the rank the game would otherwise have taken. It joins to `exclusions.csv` by `appid` and `rule`. It lets the researcher review what each rule removes.

### `impact_near_misses.csv`

One row is one exclusion tag that a scored game carries beyond its rank limit, so that it did not exclude the game, with its display position and the limit that applied. It joins by `appid`. It shows what a tighter or looser rank limit would change.

### `impact_adult_signals.csv`

One row is one scored game where Steam's Adult Only notice and content descriptor 3 disagree, with every adult-content signal and whether the game is excluded. It joins by `appid`. It documents the two signals' overlap.

### `impact_unexcluded.csv`

One row is one Top-100 member and one signal worth a second look although no rule excluded the game: content descriptor 1 or 4, a software store genre or a Content Flag. It joins to `top100_<dataset>.csv` by `dataset` and `appid`. It is a review list.

### `manual_metadata.csv`

One row is one field of one Manual Metadata Entry, with the supplied value, its source URL and retrieval date. It joins to the datasets by `appid` (those rows have `metadata_source` `manual` or `manual_tags`). It publishes the researcher's citations.

### `steamdb_crosscheck.csv`

One row is one Top-100 game with a SteamDB page in the Snapshot, comparing its store tags with the SteamDB tags. It exists only after a permitted SteamDB batch, joins by `appid`, and is a cross-check only: SteamDB values never enter a dataset.

### `reports.html`

A one-page summary of the reports above, rendered only from fixed sentence templates and checked for causal language. It carries the test and parse-error banners and the attribution line.

## Build: analysis/

The feature-analysis and network files stack the five datasets, with `dataset` as the first column. The network files also carry the `state_id` of the report's Network State for each dataset, so each block can be reopened in the app at the same settings.

### `tag_frequency.csv`

One row is one tag on at least one game of a full Top-100 Dataset: its count and share, median display position, whether it is the defining tag, its Eligible Pool baseline and share ratio, and its archived category. It joins to `top100_<dataset>.csv` through `tag_id`. It answers which tags recur among the top games.

### `genre_frequency.csv`

One row is one store-genre value on at least one game of a dataset, with its config `kind` and the same count, share and baseline columns. It joins through `genre_id`. It covers the developer-assigned Genre field, which is not a tag.

### `combinations.csv`

One row is one combination of 2 up to `max_itemset_size` tags with at least `min_support` games, with its support, lift and, for pairs, both confidences. It joins to `tag_frequency.csv` through its `tag_ids`. It answers which tag combinations recur.

### `associations.csv`

One row is one pair of tags that each reach `min_support` games, including pairs that never co-occur: the pair counts, phi, lift, Jaccard, Fisher p and the within-dataset BH q. It joins to `tag_frequency.csv` through `tag_id_a` and `tag_id_b`. It is a descriptive screen of co-occurrence.

### `content_flags.csv`

One row is one dataset, one Content Flag and one flagged game, with the game's rank. It joins to `top100_<dataset>.csv` by `appid`. It lists the games behind the per-flag counts in `analysis.json`.

### `network_nodes.csv`

The app's `nodes.csv` for the report's Network State of each dataset, stacked. One row is one tag of the network.

### `network_edges.csv`

The app's `edges.csv`, stacked. One row is one edge.

### `network_clusters.csv`

The app's `clusters.csv`, stacked. One row is one cluster; the report's cluster list comes from it.

### `network_cluster_quality.csv`

The app's `cluster_quality.csv`, stacked. One row per dataset; the report's Q-vs-null and stability sentences come from it.

### `network_cluster_connections.csv`

The app's `cluster_connections.csv`, stacked. One row is one pair of clusters.

### `network_null_model.csv`

The app's `null_model.csv`, stacked. One row is one null-model replicate.

### `network_seed_noise.csv`

The app's `seed_noise.csv`, stacked. One row is one noise seed.

### `network_not_in_network.csv`

The app's `not_in_network.csv`, stacked. One row is one tag left out of the network, with its reasons.

### `removal_sensitivity.csv`

In the Build: the complete Removal Sensitivity table of each dataset's report Network State, stacked, one row per tag in run order. In the app zip: the rows computed for the exported state (see below).

### `resolution_sweep.csv`

One row is one dataset and one resolution γ of the grid: cluster counts, Q at that γ (not comparable across rows), the mean silhouette, ARI against the report's partition and the seed ARIs at that γ. It joins to `network_cluster_quality.csv` by `dataset`. It shows how much the clusters depend on γ.

### `report.html`

The feature-analysis report: one section per dataset (frequencies, Content Flags, clusters, Q vs null, stability, Resolution Sweep and Removal Sensitivity sentences), a methods section and a fixed limitations paragraph. Every sentence comes from a fixed template and every number from the files above; the Build fails if a causal word appears.

## App export zip

`steamstudy_<dataset>_<state_id>_<UTC timestamp>.zip` holds one Network State. Its tables have the same columns as the Build's stacked files, without `dataset` and `state_id`.

### `nodes.csv`

One row is one tag of the network: its cluster, game count, degrees and strengths, silhouette, medoid score and center flag, within-cluster z-score, participation, Membership Stability, and its positions in both layouts. It joins to `edges.csv` and `clusters.csv` through `tag_id` and `cluster`.

### `edges.csv`

One row is one edge: the two tags (source < target), shared games, lift, both clusters and the AppIDs of the games having both tags. It joins to `nodes.csv` through the tag ids and to `top100_<dataset>.csv` through `appids`.

### `clusters.csv`

One row is one cluster: its members by medoid score, connectedness, internal edges and weight, densities, cut weight, conductance, mean silhouette, center and top-strength tag, and mean Membership Stability. It joins to `nodes.csv` through `cluster`.

### `cluster_quality.csv`

One row for the whole Network State: network size, modularity against its null model, coverage, cluster counts, disconnected clusters, mean silhouette and the Seed-Noise Floor. It is the Cluster-quality row of the app.

### `cluster_connections.csv`

One row is one pair of Multi-Tag Clusters (or a cluster and the pooled One-Tag Clusters), with the edges and weight between them. It joins to `clusters.csv` through the labels.

### `cluster_games.csv`

One row is one cluster and one game that has at least one of its tags (the cluster inspector's Games section): how many of the cluster's tags it has, its own tags in the network, that share, and the matched tags. It is in the export zip only, never in a Build. It joins to `clusters.csv` through `cluster` and to `top100_<dataset>.csv` through `appid`.

### `null_model.csv`

One row is one null-model replicate: its seed, Q and edge count. It is the source of `q_null_mean`, `q_null_sd` and `null_n_edges_mean`.

### `seed_noise.csv`

One row is one noise seed: its seed, Q, mean silhouette, ARI against the shown partition and cluster counts. It is always written and is the source of every `seed_*` value.

### `not_in_network.csv`

One row is one tag on at least one game of the dataset that is not a node, with its game count after the filter and every reason. It joins to `tag_frequency.csv` through `tag_id`.

### `export.json`

The zip's metadata: `schema_version`, the full Network State key and its `state_id`, `layout_source`, the export time and software versions, the Build folder path (informational only: Open Network State finds the Build by its identity, not by this path) and a copy of the Build's `build.json`, each file's row count and SHA-256, the method constants (R and the replicate seeds, K and the noise seeds, the Removal Sensitivity method version, the center tie-break and cluster-label rules, the silhouette distance), the Removal Sensitivity status (`not_run`, or `partial` / `complete` with `done` and `total`) and the `columns` block describing every column. Open Network State reads it to reproduce the state.

## Parameter Selection files

**Export tables** in the Parameter Selection mode writes one zip per settings key. Every table is stacked by a `dataset` column and covers only the datasets whose grid is complete; the two validation tables hold rows for validated pairs only.

### `pairs.csv`

One row is one Threshold Pair of one dataset, 153 per dataset: its network size and graph hash, the γ scan (γ_max(n_e), the last scan γ, the scan length, capped runs), the Selected Partition's domain and Selected Resolution, the Workbench γ and seed with `reproduced` or the ARI, Neighbour Agreement with its neighbour counts, Information Retention, the isolated and LCC shares, the cluster counts, the Seed-Noise Floor, the descriptive Q, Coverage and Silhouette, and `qualifies`, its failing reasons, `near_best` and `chosen` under the export's constraints.

### `admissible_partitions.csv`

One row is one Admissible Partition of one pair: Â, P̂, its Optimality Domain, `clipped_high`, ω_in, ω_out, γ̂ or its reason, the map target, `stable`, its cluster counts, the first (γ, seed) that found it, its hit count and whether it is the Selected Partition. It joins to `pairs.csv` through `dataset`, `g` and `s`.

### `neighbour_links.csv`

One row is one pair and one of its four directions (g−, g+, s−, s+): the neighbour, the link's status, the shared and compared tags, the ARI and the Edge Overlap. Directions outside the grid have status `outside_grid`.

### `selected_partitions.csv`

One row is one tag of one pair's network with its Cluster in the Selected Partition (empty without one), so Neighbour Agreement can be recomputed without Leiden.

### `selection.csv`

One row per dataset: the chosen pair or `no_qualifying_pair`, the highest Neighbour Agreement, the tolerance, the near-best set, the tie-break used, the constraints label and the settings label.

### `validation_replicates.csv`

One row is one validation replicate and arm (`null`, `subsample_reselected`, `subsample_at_resolution`) of a validated pair: its seed, whether it had a Selected Partition or was degenerate and why, its ARI against the Selected Partition, Q at the observed resolution (null arm), the scan length and capped runs.

### `validation_clusters.csv`

One row is one Multi-Tag Cluster of a validated pair's Selected Partition in one Subsample Stability arm: the mean Jaccard, the subsamples with a Jaccard ≤ 0.5 out of those where it is present, the mean retention share, the absent count and `dissolved`.

### `parameter_selection.json`

The zip's metadata, mirroring `export.json`: `schema_version`, the settings key and each dataset's grid key and validated pair's validation key with their hashes, the Selection Settings and both labels, the grid (ranges, γ step, the scan-end rule `gm22_gamma_max_n_e`, scan seeds, pass cap), every seed stream with its seeds, R, S and each validated pair's g′ and s′, the Pair Constraints and tolerance, method and software versions, a copy of `build.json`, each dataset's status (complete, "partial, k of 153" or "not run") and `computed_with` blocks, each file's rows and SHA-256, and the `columns` block.

### `selection_report.md`

A short report: per dataset, the selection explanation with its caveats and the validation sentences, then the methods paragraph with citations. Every sentence comes from the same templates as the app.

## Metadata files

### `snapshot.json`

In `snapshots/<snapshot_id>/`: what was collected and how. The id and mode, collection date and Observation Window, per-stage and per-pass times and counts, the request rates actually used, the User-Agent, the age-check birth date, the store-reported country, the `GetTagList` `version_hash`, the collection config hash, the operator-reply and ethics-check references, SteamDB permission and batches, repairs and software versions.

### `build.json`

In a Build's `datasets/`: the Snapshot id and `build_id`, the build config hash with a copy of every config file the Build read and the config changelog, the Source Substitutions used, the attribution line, the network defaults and seed, software versions, the mode, whether parse errors were allowed (and how many), the Manual Metadata Entries and Exclusion Overrides used, dataset sizes and any warnings.

### `analysis.json`

In a Build's `analysis/`: `schema_version` and `build_id`; per dataset the report's Network State key and `state_id`, the game count, the Eligible Pool size, the per-flag Content Flag counts (zeros included), the Seed-Noise Floor summary, the Removal Sensitivity summary and the Resolution Sweep ranges; the Resolution Sweep grid; and the `columns` block.
