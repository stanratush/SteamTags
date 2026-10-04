# Export schemas for the app and the feature analysis
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 23

## Question

What are the exact file names, formats (CSV vs. JSON), column names, types and metadata blocks of every export: the Tag Network app's exports (network with nodes/edges incl. x/y for both layout modes and AppID lists, cluster quality, clusters, cluster × cluster connections, nodes, tags not in the network, Removal Sensitivity) and the Build's feature-analysis CSVs (including the per-dataset Removal Sensitivity table)? How do they reuse the `build_id`, list conventions and provenance of `build.json` and the `top100_<dataset>.csv` contract, and how is the network-state key recorded so an export can be matched to a cached app state?

Graduated from the map's fog after [Node-removal sensitivity method](12-node-removal-sensitivity.md). Contents already fixed (only the layout is open):
- Starting export set: [Tag network app interaction prototype](14-tag-network-app-prototype.md). Top-100 CSV, Build folder, `build.json`: [Pipeline architecture and export schema](15-pipeline-architecture.md). Feature-analysis table contents: [Feature-analysis definitions](13-feature-analysis-definitions.md).
- x/y for both layout modes, AppID lists: [Web stack selection](18-web-stack-selection.md). `shared_games` + `lift` on edges, `strength_shared` + `strength_lift` on nodes, `clustering_weight`: [Edge weight used for clustering](19-edge-weight-for-clustering.md).
- `algorithm`, `resolution`, null-model R, library versions; Cluster-quality global row; per-cluster metrics; per-node silhouette; connection table: [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md).
- `center`, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength`; node metrics `n_games`, `degree`, `degree_intra`, `medoid_score`, `is_center`, `within_z`, `participation`; tie-break rule: [Cluster center and centrality measures](11-cluster-center-centrality.md).
- Removal Sensitivity rows (identity, reclustered ΔQ/Δsilhouette/Δk/Δs/ARI/centers lost, fixed-partition ΔQ/Δsilhouette, `beyond_noise`, silhouette n/a transitions) and metadata (noise-floor values, K, derived seeds, partial flag n of N, method version, state key): [Node-removal sensitivity method](12-node-removal-sensitivity.md).

Blocked by [Recompute turnaround and caching](23-recompute-budget-caching.md), which defines the network-state key exports must record.

Settled by [Recompute turnaround and caching](23-recompute-budget-caching.md):
- Network-state key: canonical JSON of `build_id`, `dataset`, `min_months`, `min_games_per_tag`, `min_shared_games`, `hidden_tagids`, `removed_tagids` (both sorted), `clustering_weight`, `algorithm`, `resolution` (`"1.00"`), `seed`, `null_replicates`, `key_version`; `state_id` = first 12 hex characters of its SHA-256. Every app export stores the full JSON and the `state_id`.
- Positions: the network export records `layout_source = "default" | "relayout"`. Q_null and z are always present (the null model runs inside every recompute), so no "pending" value is needed.

## Answer

Resolved 2026-10-04 with the researcher, over two rounds. Every export carries its own provenance, the app and the Build write network tables with one writer, and one schema module in code defines every file and column.

**Single source**: `steamstudy.export.schema` declares every file, column, type and one-line description (units, n/a meaning).
- Every writer validates its output against it.
- `export.json` and `analysis.json` each carry a `columns` block generated from it.
- A test fails if a writer emits an undeclared column or omits a declared one.
- Implementation may refine descriptions. Adding, removing or renaming a column bumps `schema_version`, an integer separate from the network-state key's `key_version` (which tracks results, not layout).

**Shared conventions** (all app and Build CSVs; extends the `top100_<dataset>.csv` contract of [Pipeline architecture and export schema](15-pipeline-architecture.md))
- UTF-8 with BOM, comma-delimited, `\n` line endings; every write passes `encoding="utf-8-sig"` explicitly ([Dash spike re-run on Python 3.14](22-dash-spike-python-314.md)). No metadata rows inside CSVs.
- **Ids**: `tag_id` / `tag_ids` everywhere, matching `tag_ids` and `genre_ids` in the Top-100 CSV. This renames the network-state key fields to `hidden_tag_ids` and `removed_tag_ids` (supersedes `hidden_tagids` / `removed_tagids` in [Recompute turnaround and caching](23-recompute-budget-caching.md)). Every tag column is an id + name pair (`tag_id` + `tag`); clusters are their `C1…` label.
- **Lists**: `;`-separated, as matching id and name lists (`member_tag_ids` / `members`). Edge AppID lists hold AppIDs only, in dataset rank order (game names may contain `;`; they join from the Top-100 CSV).
- Booleans `true` / `false`.
- **n/a** = empty cell. A `<metric>_status` column gives the reason only where it varies:
  - silhouette: `fewer_than_2_multi_tag_clusters`, `one_tag_cluster`;
  - center: `one_tag_cluster`, `two_tag_cluster`;
  - modularity: `no_edges`.

  Fixed-cause n/a values (e.g. conductance with vol(rest) = 0, `within_z`, `modularity_z` at sd = 0) stay empty with no status column; their cause can be derived from other columns.
- Floats: shortest round-trip `repr`, so app and Build values compare exactly. `mean_monthly_players` keeps its 6 decimals.
- **Cluster labels**: `C1…` by size descending, ties by smallest member `tag_id` ascending. Multi-Tag Clusters come first, One-Tag Clusters after them (ordered by `tag_id`).

**App export**
- One "Export this state" action (Workbench export area, Analysis Report mode section 7). The browser downloads `steamstudy_<dataset>_<state_id>_<UTC timestamp>.zip`. There are no per-table loose files, so no file leaves the app without its provenance.
- Nothing is written into the Build folder.
- No `network.json` and no GraphML: `nodes.csv` + `edges.csv` are the network.

| File | Rows |
|---|---|
| `export.json` | metadata (below) |
| `nodes.csv` | one per tag in the network |
| `edges.csv` | one per edge |
| `clusters.csv` | one per cluster, Multi-Tag and One-Tag |
| `cluster_quality.csv` | one row |
| `cluster_connections.csv` | every unordered pair of Multi-Tag Clusters (zero-edge pairs included), plus pairs with the pseudo-cluster `one_tag_pool` |
| `null_model.csv` | one per null-model replicate |
| `not_in_network.csv` | one per tag on ≥1 game of the loaded dataset that is not a node |
| `removal_sensitivity.csv` | one per tested tag, in run order |
| `removal_sensitivity_noise.csv` | one per noise seed |

**`export.json`**
- `schema_version`.
- `state_key` (the full canonical JSON) and `state_id`.
- `layout_source`, `exported_at`, the app's software versions.
- A **copy** of the loaded Build's `build.json` provenance (snapshot id, `build_id`, `build_config_hash`, Source Substitutions, attribution, `mode`, `parse_errors_allowed`), so the zip stands alone.
- `files`: per file, its row count and SHA-256.
- Method constants: R and the replicate seeds, K and the noise seeds, Removal Sensitivity method version, center tie-break rule, cluster-label rule, `"silhouette": "jaccard_game_set"`.
- `removal_sensitivity`:
  - `"not_run"` when no results exist for this exact state key; the two sensitivity files are then **left out**, never written empty;
  - otherwise the noise-floor summary (K, SD(Q), SD(silhouette), minimum ARI) and `partial` with `done` / `total`.

  Stale results belong to another key and are never exported.
- `columns`.

**Columns** (weighted values without a `_shared` / `_lift` suffix are on the active Clustering Weight)
- **`nodes.csv`** (sorted by cluster, `medoid_score`, `tag_id`):
  - identity: `tag_id`, `tag`, `cluster`, `n_games`, `is_isolated`;
  - degree and strength: `degree`, `degree_intra`, `strength_shared`, `strength_lift`, `strength_shared_intra`, `strength_lift_intra`;
  - silhouette: `silhouette`, `silhouette_status`;
  - center and roles: `medoid_score`, `is_center`, `within_z`, `participation`;
  - positions: `x_global`, `y_global`, `x_cluster_separated`, `y_cluster_separated`. The export always computes Cluster-separated positions, even when that layout isn't shown.
- **`edges.csv`** (sorted by `source_tag_id`, `target_tag_id`, source < target): `source_tag_id`, `source_tag`, `target_tag_id`, `target_tag`, `shared_games`, `lift`, `source_cluster`, `target_cluster`, `is_intra_cluster`, `appids`.
- **`clusters.csv`** (sorted by label):
  - `cluster`, `kind` (`multi_tag` / `one_tag`), `size`;
  - `member_tag_ids`, `members`: by `medoid_score`, then the center tie-break;
  - `connected`, `internal_edges`, `internal_weight`, `edge_density`, `weighted_density`, `cut_weight`, `conductance`;
  - `mean_silhouette`, `silhouette_status`;
  - `center_tag_id`, `center`, `center_medoid_score`, `center_status`;
  - `top_strength_tag_id`, `top_strength_tag`, `center_is_top_strength`.
- **`cluster_quality.csv`**:
  - `n_games` (N after the Minimum Months Filter), `n_nodes`, `n_edges`, `total_weight`;
  - `modularity`, `modularity_status`, `q_null_mean`, `q_null_sd`, `modularity_z`;
  - `coverage`, `inter_cluster_weight_share`;
  - `n_multi_tag_clusters`, `n_one_tag_clusters`, `n_disconnected_clusters`;
  - `mean_silhouette`, `silhouette_status`.
- **`cluster_connections.csv`**: `cluster_a`, `cluster_b`, `edge_count`, `weight`.
- **`null_model.csv`**: `replicate`, `seed`, `modularity`, `n_edges`.
- **`not_in_network.csv`**: `tag_id`, `tag`, `n_games` (after the Minimum Months Filter; 0 if the filter emptied it), `reasons`. `reasons` lists every reason that applies, as a `;`-list in fixed order `removed;defining_tag_hidden;genre_tag_hidden;below_min_games`.
- **`removal_sensitivity.csv`** (run order: active strength descending, then `tag_id`, so a partial file is a prefix of the full one; the UI's ARI sort is a view only):
  - identity: `run_order`, `tag_id`, `tag`, `cluster`, `is_center`, `active_strength`;
  - reclustered reading:
    - `rc_delta_modularity`;
    - `rc_silhouette_after`, `rc_silhouette_after_status`, `rc_delta_silhouette`;
    - `rc_delta_k`, `rc_delta_s`, `rc_ari`;
    - `rc_centers_lost_tag_ids`, `rc_centers_lost`;
    - `rc_beyond_noise`: a `;`-list of `ari`, `modularity`, `silhouette`;
  - fixed-partition reading: `fp_delta_modularity`, `fp_silhouette_after`, `fp_silhouette_after_status`, `fp_delta_silhouette`.

  A silhouette that moves between a value and n/a leaves the delta empty. The "before" value is in `cluster_quality.csv`, and the UI builds the "0.21 → n/a" text from these columns.
- **`removal_sensitivity_noise.csv`**: `noise_seed_index`, `seed`, `modularity`, `silhouette`, `silhouette_status`, `ari_vs_main`.

**Build `analysis/` folder** (`builds/<snapshot_id>/<build_id>/analysis/`)
- Feature-analysis tables ([Feature-analysis definitions](13-feature-analysis-definitions.md)), each with `dataset` first:
  - `tag_frequency.csv`: `tag_id`, `tag`, `count`, `share`, `median_position`, `defining_tag`, `baseline_count`, `baseline_share`, `share_ratio`, `archived_category`.
  - `genre_frequency.csv`: `genre_id`, `genre`, `kind`, `count`, `share`, `baseline_count`, `baseline_share`, `share_ratio`.
  - `combinations.csv`: `size`, `tag_ids`, `tags` (both sorted by `tag_id`), `support_count`, `support_share`, `lift`, `confidence_a_to_b`, `confidence_b_to_a` (pairs only).
  - `associations.csv`: `tag_id_a`, `tag_a`, `tag_id_b`, `tag_b` (a < b), `count_a`, `count_b`, `count_ab`, `phi`, `lift`, `jaccard`, `fisher_p`, `bh_q`.
  - `content_flags.csv` (long form, one row per dataset × flag × flagged game): `flag`, `appid`, `name`, `rank`.
- Network tables, written by **the same writer as the app export**, with the five datasets stacked and `dataset`, `state_id` as the first two columns:
  - `network_nodes.csv`, `network_edges.csv`, `network_clusters.csv`;
  - `network_cluster_quality.csv`, `network_cluster_connections.csv`, `network_null_model.csv`;
  - `network_not_in_network.csv`;
  - `removal_sensitivity.csv`, `removal_sensitivity_noise.csv`.

  These replace a separate "Clusters" table format.
- `analysis.json`:
  - `schema_version`, `build_id`;
  - per dataset: its `state_key` + `state_id`, `n_games`, Eligible Pool size, per-flag counts (zeros included), and the Removal Sensitivity noise-floor summary;
  - `columns`.

  It does not copy `build.json`, which sits next to it.
- `report.html`.
- **Equality test**: opening the app on a Build at the report's settings and exporting gives CSVs equal to that dataset's Build rows, minus `dataset` / `state_id`. This proves that the app and the report share one clustering.

Glossary updated: new **Network State** ([CONTEXT.md](../../../CONTEXT.md)).
