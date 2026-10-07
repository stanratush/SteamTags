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
| Tidy | Settles the Global layout from the current positions, keeping the nodes you dragged where you dropped them; kept until the dataset, filter, weight, seed or the visible tags change | none | none (`layout_source` in exports) | Positions only |
| Mode | Workbench or Analysis Report mode | Workbench | none | none |
| Controls / Inspector / Tables | Collapse each panel independently | all shown | none | none |
| Graph only | Switches to the narrowest form (pill bar, floating Inspector, bottom sheet) at any width; press again to leave it | off | none | none |
| Find a tag… (header) | Finds any tag of the dataset: a tag in the network is selected, centred and opened in the Inspector; a missing tag opens a "Not in the network" card | none | none (Restore / Unhide on the card change `removed_tag_ids` / `hidden_tag_ids`) | none until you press the card's button |
| Fit (⤢, top right of the graph) | Fits the whole graph back into view after you zoom or pan | none | none | Positions only |
| Run, Continue, Cancel, Run for this tag | Removal Sensitivity, as a background job | not run | none (results are cached per `state_id`) | `removal_sensitivity.csv` only |
| Export this state | Downloads one zip with every table and the full state key | none | none | none |
| Open Network State… | Reopens an export zip or its `export.json` | none | all key fields | All, recomputed |
| Clear app cache | Deletes cached Removal Sensitivity results | none | none | none |

Sliders send their value when you release them; the value beside the slider's label updates while you drag. The number of null-model replicates R and of noise seeds K are set in the Build's config only; they have no control.

The Controls panel is split into four sections: **Data** (dataset, Minimum Months Filter), **Filters** (the two thresholds, the hidden Genre Tags and the defining tag), **Clustering** (weight, algorithm, γ, seed) and **State** (removed tags, Reset all, Export, Open, Clear app cache). A struck-through Genre Tag chip is hidden from the network; click it to show the tag. The count beside the heading ("11 of 11") says how many are hidden.

## Find a tag

The search box in the middle of the header works in every mode and form, including Graph only. Type part of a tag's name; the list shows the tags **in the network** first (with their cluster colour, cluster and games), then every tag of the dataset that is **not in the network**, greyed out, with all its reasons in plain words: "Genre Tag hidden", "defining tag hidden", "removed", or "3 games, below 8" (fewer games than the Minimum games per tag). Use ↑ / ↓ and Enter to choose, Esc to close.

- Choosing a tag in the network selects it, centres the graph on it and opens it in the Inspector.
- Choosing a missing tag opens a **Not in the network** card with its reasons and its number of games. When exactly one action brings it back, the card offers it: **Restore** for a removed tag, **Unhide** for a hidden Genre Tag or defining tag. Nothing changes until you press it, and pressing it changes the Network State, exactly as the Restore button or the hidden-tag chips would. A tag below the minimum games, or one that would need two changes, gets no button.

## Window width and the three forms

The Workbench rearranges itself as the window narrows. Nothing is lost in a narrower form; every control is still one or two clicks away.

- **Wide (1280 px and more)**: three panes. Controls on the left, the graph in the centre, the Inspector on the right, the tables below the graph. Drag the bar between the graph and the tables to give either more room.
- **Medium (1024–1279 px)**: the Controls panel becomes a **pill bar** under the header. Each pill shows the current value ("Min games 8", "γ 1.00"); click it to open a small panel holding that control, and click anywhere else (or press Esc) to close it. The Inspector becomes a **floating card** over the right of the graph: it opens when you click a node, an edge or a cluster, and closes with ×. The graph refits so that nothing hides under the card.
- **Narrow (under 1024 px)**: as medium, and the tables become a **bottom sheet**: a strip of tabs along the bottom of the graph. Click a tab or the grip on the left to open the sheet, and the grip again to close it.

**Graph only** gives the narrow form at any width. Collapsing the Inspector in the wide form also makes it a floating card. The legend sits at the bottom left of the graph; the Global / Cluster-separated switch, Tidy and Fit sit at the top right.

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
