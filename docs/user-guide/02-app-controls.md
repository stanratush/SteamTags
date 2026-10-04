# App controls

## Control reference

Each control below either sets a field of the Network State key (and so changes the `state_id` and recomputes everything) or only changes the view. Defaults come from the Build's `network.toml`; the values shown are the shipped defaults.

| Control | What it does | Range and default | Network State field | Which numbers change |
|---|---|---|---|---|
| Dataset | Loads one Top-100 Dataset of the Build | Overall, Puzzle, RPG, Strategy, Simulation; Overall | `dataset` | All |
| Minimum games per tag | A tag becomes a node only if at least this many of the N games have it | 1–40; 8 | `min_games_per_tag` | Node set, and so everything in the network |
| Minimum shared games | An edge exists only if the two tags share at least this many games | 1–30; 8 | `min_shared_games` | Edge set, isolated tags (One-Tag Clusters), everything after |
| Minimum Months Filter | Drops games with fewer Months Observed before the network is built; never re-ranks or backfills | 0–60; 0 (off) | `min_months` | N, every `n_games`, every `lift`, the Global layout, everything after |
| Hidden Genre Tags | Hides each ticked Genre Tag (the 11 Top-Level Genres) from the network, never from the dataset | 11 toggles; all hidden | `hidden_tag_ids` | Node set; not N, not any remaining edge's `lift` |
| Hide defining tag | Hides the dataset's defining tag (Puzzle, RPG, Strategy or Simulation) | toggle; hidden | `hidden_tag_ids` | As above |
| Clustering weight | What community detection runs on: shared games or lift. Edge thickness and thresholds always use shared games | Shared games, Lift; Shared games | `clustering_weight` | Partition, every weighted metric, null model, Seed-Noise Floor, Global layout |
| Clustering algorithm | Louvain or Leiden (both maximise modularity) | Louvain, Leiden; Louvain | `algorithm` | Partition and everything computed from it |
| Resolution γ | Higher γ gives more, smaller clusters. Sends on Enter or when the box loses focus | 0.1–3.0, step 0.05; 1.00 | `resolution` | Partition, the value of Q |
| Seed | Seeds the clustering; the null-model and noise seeds derive from it. Sends on Enter or when the box loses focus | integer ≥ 0; config value | `seed` | Partition, null model, Seed-Noise Floor, Global layout |
| Remove (node inspector), Restore, Reset all | Removes a tag from the network as a what-if, or brings it back | any node; none removed | `removed_tag_ids` | Node set; not N or any `lift` |
| Global / Cluster-separated | Moves nodes only: one layout for the whole network, or one region per cluster | Global | none | Positions only |
| Re-layout | Refines the positions from the current ones; kept until the dataset, filter, weight or seed changes | none | none (`layout_source` in exports) | Positions only |
| Mode | Workbench or Analysis Report mode | Workbench | none | none |
| Controls / Inspector / Tables, Graph only | Collapse panels | all shown | none | none |
| Run, Continue, Cancel, Run for this tag | Removal Sensitivity, as a background job | not run | none (results are cached per `state_id`) | `removal_sensitivity.csv` only |
| Export this state | Downloads one zip with every table and the full state key | none | none | none |
| Open Network State… | Reopens an export zip or its `export.json` | none | all key fields | All, recomputed |
| Clear app cache | Deletes cached Removal Sensitivity results | none | none | none |

Sliders send their value when you release them; the value label updates while you drag. The number of null-model replicates R and of noise seeds K are set in the Build's config only; they have no control.

## Task recipes

### Check whether a cluster survives removing its center

1. Click the cluster's legend button. The inspector shows its members, its Cluster Center (◆) and the `top_strength_tag`.
2. Click the center node and press **Run for this tag**. When it finishes, read `rc_ari` and `rc_centers_lost` in the node inspector or the Removal sensitivity tab.
3. Compare `rc_ari` with the Seed-Noise Floor's `seed_ari_min`. Above it, the partition changed no more than another seed would change it. Below it, the row carries the screening flag. To see the new partition itself, press **Remove** instead and look at the clusters; **Restore** brings the tag back.

### Compare Louvain and Leiden

1. Note the Cluster-quality row and the Seed-Noise Floor under Louvain.
2. Switch **Clustering algorithm** to Leiden. Compare the multi-tag cluster count, Q (both maximise modularity, so Q is comparable at the same γ and weight) and `n_disconnected_clusters` (always 0 under Leiden).
3. Quote both `state_id`s if you report the comparison.

### Check how much the clusters depend on γ

1. Change **Resolution γ** in steps of 0.05 and watch the cluster count. Q at different γ is not comparable; compare partitions instead.
2. For the report's settings the Build has already done this systematically: see `resolution_sweep.csv` and the Resolution Sweep sentence in `report.html`.

### See what the network leaves out

Open the **Not in network** tab (section 2 in Analysis Report mode). Every tag on at least one game of the dataset that is not a node is listed with all its reasons: `removed`, `defining_tag_hidden`, `genre_tag_hidden`, `below_min_games`. A tag can be absent and still be common; check `tag_frequency.csv`.

### Export a state for a paper

1. Set up the state, run Removal Sensitivity if you need it, and press **Export this state**.
2. Quote the `state_id` from the file name or from section 1 of Analysis Report mode with every number you use.
3. Deposit the zip with the paper. See [Citing and reproducing a Network State](05-citing-and-reproducing.md).
