# App controls

## Control reference

Each control below either sets a field of the Network State key (and so changes the `state_id` and recomputes everything) or only changes the view. Defaults come from the Build's `network.toml`; the values shown are the shipped defaults. Each analytical control links to its full entry under [Analytical controls explained](#analytical-controls-explained).

| Control | What it does | Range and default | Network State field | Which numbers change |
|---|---|---|---|---|
| Dataset | Loads one Top-100 Dataset of the Build | Overall, Puzzle, RPG, Strategy, Simulation; Overall | `dataset` | All |
| [Minimum games per tag](#minimum-games-per-tag) | A tag becomes a node only if at least this many of the N games have it | 1–40; 8 | `min_games_per_tag` | Node set, and so everything in the network |
| [Minimum shared games](#minimum-shared-games) | An edge exists only if the two tags share at least this many games | 1–30; 8 | `min_shared_games` | Edge set, isolated tags (One-Tag Clusters), everything after |
| [Minimum Months Filter](#minimum-months-filter) | Drops games with fewer Months Observed before the network is built; never re-ranks or backfills | 0–60; 0 (off) | `min_months` | N, every `n_games`, every `lift`, the Global layout, everything after |
| [Hidden Genre Tags](#hidden-genre-tags) | Hides each ticked Genre Tag (the 11 Top-Level Genres) from the network, never from the dataset | 11 toggles; all hidden | `hidden_tag_ids` | Node set; not N, not any remaining edge's `lift` |
| [Hide defining tag](#hide-defining-tag) | Hides the dataset's defining tag (Puzzle, RPG, Strategy or Simulation) | toggle; hidden | `hidden_tag_ids` | As above |
| [Clustering weight](#clustering-weight) | What community detection runs on: shared games or lift. Edge thickness and thresholds always use shared games | Shared games, Lift; Shared games | `clustering_weight` | Partition, every weighted metric, null model, Seed-Noise Floor, Global layout |
| [Clustering algorithm](#clustering-algorithm) | Louvain or Leiden (both maximise modularity) | Louvain, Leiden; Louvain | `algorithm` | Partition and everything computed from it |
| [Resolution γ](#resolution-γ) | Higher γ gives more, smaller clusters. Sends on Enter or when the box loses focus | 0.1–3.0, step 0.05; 1.00 | `resolution` | Partition, the value of Q |
| [Seed](#seed) | Seeds the clustering; the null-model and noise seeds derive from it. Sends on Enter or when the box loses focus | integer ≥ 0; config value | `seed` | Partition, null model, Seed-Noise Floor, Global layout |
| [Remove (node inspector), Restore, Reset all](#remove--restore) | Removes a tag from the network as a what-if, or brings it back | any node; none removed | `removed_tag_ids` | Node set; not N or any `lift` |
| [Global / Cluster-separated](#global--cluster-separated) | Moves nodes only: one layout for the whole network, or one region per cluster | Global | none | Positions only |
| [Tidy](#tidy) | Settles the Global layout from the current positions, keeping the nodes you dragged where you dropped them; kept until the dataset, filter, weight, seed or the visible tags change | none | none (`layout_source` in exports) | Positions only |
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

## Analytical controls explained

Each control below changes the Network State, and so the `state_id` and the numbers, except Global / Cluster-separated and Tidy, which move nodes only. Hover over a control's label or its ⓘ, or reach it with Tab, for its short explanation; click it for the entry below.

### Minimum Months Filter

> **In short.** Leaves out games with fewer Months Observed than this before the network is built.
>
> **Raising it →** fewer games (a smaller N), each with a longer player record; 0 = every game.
>
> **Here:** checks whether the clusters hold among the games tracked longest, not only among recent releases.
>
> **Caution:** it never re-ranks or adds games, so N shrinks and every count and lift changes.

Range 0–60 months; default 0 (off). Network State field: `min_months`.

Games are ranked by Mean Monthly Players over the months they were observed, so a game released shortly before the Snapshot is ranked on its launch months, when player counts are usually highest. Raising the filter drops such games from the loaded Top-100 Dataset before anything is counted: N falls, every tag's game count and every lift is recounted over the remaining games, and the Global layout is redone. Lowering it back to 0 uses every game of the dataset. The Games number in the summary row shows how many games pass ("91 of 100").

*Why it matters here.* The study asks which characteristics recur among the most-played commercial games. A cluster that appears only while recent releases are included may reflect a few new games rather than a lasting combination; one that stays when the filter is raised rests on games with a long player record.

*Caution.* The filter never fills the gap with the next-ranked games, so a raised filter means a smaller network, not a different Top 100. With fewer games, fewer tags reach the minimum games per tag and fewer pairs reach the minimum shared games, so compare Network States at the same thresholds and expect the numbers to shift with N alone. The feature analysis ignores the filter.

*Example.* Months ≥ 12 drops every game with fewer than 12 observed months; the summary row then reads, for example, "91 of 100" Games.

### Minimum games per tag

> **In short.** A tag becomes a node only if at least this many of the network's games carry it.
>
> **Raising it →** fewer, more common tags; rarer characteristics leave the network.
>
> **Here:** decides which characteristics are frequent enough among the most-played games to be clustered at all.
>
> **Caution:** low values admit tags whose links rest on very few games.

Range 1–40; default 8. Network State field: `min_games_per_tag`.

Every tag of the dataset with at least this many of the N games becomes a node; the others are listed in the Not in network table with the reason `below_min_games`. Raising the threshold removes the rarest tags first, and with them their links. Lowering it brings rarer tags in: the network grows, and tags on only a few games join it.

*Why it matters here.* A characteristic shared by only two or three of the most-played games says little about what the most-played games have in common, and its links and lifts rest on those few games. The threshold keeps the clusters about characteristics that recur. Moving it shows which clusters depend on the rarer tags.

*Caution.* A tag left out here can still be common in another dataset or in the Eligible Pool; check `tag_frequency.csv`. Very high values leave mostly generic tags, which link to almost everything.

*Example.* At 8 with N = 100, a tag on 7 games is not a node; the search box lists it as "7 games, below 8".

### Minimum shared games

> **In short.** Two tags are linked only if at least this many of the network's games carry both.
>
> **Raising it →** fewer links, more isolated tags (One-Tag Clusters), and clusters that break apart.
>
> **Here:** sets how often two characteristics must occur together among the most-played games to count as linked.
>
> **Caution:** a missing link does not mean two tags never occur together.

Range 1–30; default 8. Network State field: `min_shared_games`.

Each pair of node tags sharing at least this many games gets a link, whose thickness shows the shared-games count. Raising the threshold removes the thinnest links first; a tag that loses all its links becomes isolated and forms a One-Tag Cluster. Lowering it adds links between tags that share few games, and the network becomes denser.

*Why it matters here.* The clusters are built from these links, so the threshold decides which co-occurrences count as a pattern among the most-played games. A pairing seen in only a few games is left out at the default, which keeps chance pairings from shaping the clusters.

*Caution.* Q, the null model and most other numbers depend on how dense the network is, so compare Network States with the same thresholds. The threshold always uses shared games, even when the Clustering Weight is lift.

*Example.* Two tags that share 7 games have no link at 8; lowering the threshold to 7 adds the link.

### Hidden Genre Tags

> **In short.** Hides the chosen Genre Tags, broad tags such as Action or RPG, from the network; their games stay.
>
> **Here:** keeps broad genre labels, which many of the most-played games carry, from swamping the clusters.
>
> **Caution:** it changes the Network State and the clusters, but not N or any remaining lift.

Eleven toggles, one per Genre Tag (Action, Adventure, Casual, Experimental, Puzzle, Racing, RPG, Simulation, Sports, Strategy, Tabletop); all hidden by default. Network State field: `hidden_tag_ids`.

A struck-through chip is hidden. Showing a Genre Tag adds it as a node, with links to the tags it shares enough games with; hiding it again takes the node and its links out. The games themselves are never removed, so every other tag keeps its game count and every remaining link its lift; the clusters and every number after them are recomputed.

*Why it matters here.* Genre Tags name broad categories that sit on a large share of the games and so link to almost every other tag. Left in, they pull the clusters around themselves; hidden, the clusters show the finer characteristics (mechanics, settings, styles) that the most-played games combine. Showing one Genre Tag at a time shows which cluster it belongs with.

*Caution.* Hidden tags are listed in the Not in network table with the reason `genre_tag_hidden`. The list of Genre Tags is set in the Build's config.

*Example.* Clicking the RPG chip in the Overall dataset adds the RPG tag as a node, linked to the tags it shares at least the minimum shared games with.

### Hide defining tag

> **In short.** Hides the tag that defines a Tag-Specific Dataset (Puzzle, RPG, Strategy or Simulation), which every game of that dataset carries.
>
> **Here:** keeps a tag that all of a dataset's most-played games carry from linking to every other tag.
>
> **Caution:** it is also a Genre Tag, so it shows only when its Genre Tag chip is shown too.

A toggle; hidden by default. Network State field: `hidden_tag_ids`.

In the RPG dataset every game has the RPG tag. Shown, it shares with each tag exactly that tag's games, so it is linked to almost every node and its lift with every tag is exactly 1. The tag stays hidden while either this toggle or its Genre Tag chip hides it. Hiding or showing it changes the Network State, so the clusters are recomputed; N and every other lift stay the same. The Overall dataset has no defining tag, and the toggle is disabled there ("no defining tag").

*Why it matters here.* In a Tag-Specific Dataset the question is which characteristics the most-played games of that kind combine; the defining tag is the same on all of them and carries no information about that.

*Caution.* In all four Tag-Specific Datasets the defining tag is also a Genre Tag, so unticking this toggle alone shows nothing: click its Genre Tag chip as well. While hidden it is listed in the Not in network table with both reasons.

*Example.* In the Puzzle dataset, untick the toggle and click the Puzzle chip: one node is added, linked to every tag on at least the minimum shared games, each link with lift 1.

### Clustering weight

> **In short.** What the clustering runs on: each link's shared-games count, or its lift.
>
> **Here:** shared games groups what the most-played games most often carry together; lift, what they combine more often than tag frequencies predict.
>
> **Caution:** the two answer different questions; Q and every weighted number differ between them.

Shared games or Lift; default Shared games. Network State field: `clustering_weight`.

With shared games, a link counts the games that carry both tags, so common tags carry the most weight and clusters tend to gather around them. With lift, each link is weighted by how much more often the pair occurs than the two tags' frequencies predict, so pairs of less common tags that go together carry more weight. Edge thickness and both thresholds always use shared games.

*Why it matters here.* Shared games describes the most-played games as they are: which characteristics they carry together most often. Lift asks what they combine beyond popularity. Comparing the two weights shows which clusters reflect frequent tags and which reflect characteristics that go together.

*Caution.* Q, coverage, the active strength, conductance and the null model change with the weight, so never compare them across the two. Lift is inflated for pairs of rare tags, so read lift-based clusters with the shared-games counts beside them.

*Example.* A pair of tags each on 12 of 100 games and sharing 9 has lift 6.25: under lift, that pair weighs far more than two common tags sharing 40 games with lift 1.1.

### Clustering algorithm

> **In short.** The method that searches for the clusters: Louvain or Leiden, both maximising modularity.
>
> **Here:** running the second method on the same network shows whether the clusters depend on the method.
>
> **Caution:** Louvain can return a cluster in disconnected pieces; Leiden never does.

Louvain or Leiden; default Louvain. Network State field: `algorithm`.

Both algorithms search for the split with the highest modularity Q at the chosen γ, and both are randomised, so the seed matters for either. Leiden refines the clusters it finds and guarantees that each one is connected; Louvain is the default here.

*Why it matters here.* A group of characteristics that both methods find is less likely to be an artefact of one search procedure. Since both maximise the same Q, the two can be compared directly at the same γ and Clustering Weight.

*Caution.* The two can give different splits with similar Q; that is a property of modularity, not a fault of either. Under Louvain, check the number of disconnected clusters in Cluster quality.

*Example.* Switch to Leiden and compare the multi-tag cluster count, Q and the disconnected-cluster count (always 0 under Leiden); quote both `state_id`s.

### Resolution γ

> **In short.** Sets the scale of the clusters: the resolution in the modularity that the clustering maximises.
>
> **Raising it →** more, smaller clusters; lowering it, fewer and larger ones.
>
> **Here:** shows whether the groups of characteristics hold at a finer or a coarser scale.
>
> **Caution:** Q at different γ is not comparable; compare the clusters instead.

Range 0.1–3.0 in steps of 0.05; default 1.00. Network State field: `resolution`. The box sends its value on Enter or when it loses focus.

γ weighs the "expected" part of modularity. At γ = 1 modularity has its standard form; above 1, splitting clusters pays off sooner, so the clusters become smaller and more numerous; below 1, they merge.

*Why it matters here.* There is no single right size for a group of characteristics. A cluster that stays together from γ 0.75 to 1.25 is a combination the most-played games show at several scales; one that appears only at one γ depends on that choice. The Build's Resolution Sweep does this systematically for the report's settings.

*Caution.* Q is computed at the chosen γ, so values from different γ must not be compared. Very high γ splits the network into many small clusters regardless of how the games combine tags.

*Example.* If a network has 5 multi-tag clusters at γ 1.00, at 1.50 the largest may split in two, and the summary row then shows 6.

### Seed

> **In short.** The random seed of the clustering; the null-model and noise seeds are derived from it.
>
> **Here:** lets a reported cluster of the most-played games' tags be reproduced exactly.
>
> **Caution:** never choose a seed for the clusters it gives; the Seed-Noise Floor already compares other seeds.

An integer of 0 or more; the default comes from the Build's config. Network State field: `seed`. The box sends its value on Enter or when it loses focus.

Louvain and Leiden visit the tags in a random order, so different seeds can give different clusters. The seed fixes that order, so the same Network State always gives the same clusters; the seeds of the null model and of the K extra noise seeds are derived from it.

*Why it matters here.* Results are only citable if they can be reproduced, and the seed is part of the `state_id`. Trying another seed is also the most direct way to see how much a cluster depends on chance, which the Seed-Noise Floor measures for K seeds at once.

*Caution.* Picking the seed whose clusters fit an expectation would make the result an artefact of that choice. Keep the config seed unless there is a reason to change it, and report the seed you used.

*Example.* Changing the seed from 20261003 to 1 reruns the clustering, the null model and the Seed-Noise Floor, and the `state_id` changes.

### Remove / Restore

> **In short.** Remove takes one tag out of the network as a what-if and recomputes everything; Restore brings it back.
>
> **Here:** shows the clusters of the most-played games without one characteristic, such as a generic tag linked to everything.
>
> **Caution:** it changes the Network State; Removal Sensitivity answers the same question without changing it.

Remove is in the node inspector; Restore (pick a removed tag) and Reset all are in the State section. Network State field: `removed_tag_ids`.

A removed tag leaves the network with its links and is listed in the Not in network table as `removed`. The games stay, so N and every remaining lift are unchanged; the clusters, Q and everything after are recomputed. Restore brings one removed tag back; Reset all brings back every removed tag.

*Why it matters here.* Some tags, such as Singleplayer, sit on so many of the most-played games that they link to almost every other tag. Removing one shows how the remaining characteristics group without it, as a new Network State that can be exported and cited.

*Caution.* Removing a tag removes its links too, so part of any change is mechanical. To compare many tags without changing the Network State, run Removal Sensitivity, which measures each removal against the Seed-Noise Floor.

*Example.* Removing Singleplayer recomputes the network without it; the search box then lists it as "removed", with Restore on its card.

### Global / Cluster-separated

> **In short.** How the graph is drawn: one layout for the whole network, or one region per Multi-Tag Cluster.
>
> **Here:** Global shows how the clusters of the most-played games' tags touch; Cluster-separated makes each cluster's members easy to read.
>
> **Caution:** moves nodes only; no number changes, and distance on screen is not a metric.

Global or Cluster-separated; default Global. Not part of the Network State.

The Global layout places all visible tags by their links on the Clustering Weight in use, so tags with heavy links tend to sit near each other and clusters that overlap sit side by side. Cluster-separated gives each Multi-Tag Cluster its own region, with its Cluster Center in the middle, and puts the One-Tag Clusters in a grid of their own.

*Why it matters here.* Global is the view to see how groups of characteristics connect; Cluster-separated is the view to read and screenshot one cluster's members.

*Caution.* Positions are drawn after every metric is computed and never feed back into one. Two tags drawn close together may share few games.

*Example.* Switch to Cluster-separated to read a large cluster's members without the other clusters' tags in between.

### Tidy

> **In short.** Settles the Global layout from where the nodes are now, keeping the nodes you dragged where you dropped them.
>
> **Here:** untangles a crowded part of the graph for reading or for a figure.
>
> **Caution:** moves nodes only; an export after Tidy records it in `layout_source`.

A button at the top right of the graph. Not part of the Network State.

Tidy re-runs the Global layout from the current positions, then the clamp and the label spacing, while the nodes you dragged stay fixed. The result is kept until the dataset, a filter, the weight, the seed or the visible tags change.

*Why it matters here.* A figure of the most-played games' tag network is easier to read when crowded labels are pulled apart by hand; Tidy lets the rest of the graph settle around those choices.

*Caution.* The tidied positions depend on what you dragged, so they are not reproducible from the `state_id` alone; an export made after Tidy records `layout_source` = `relayout` and keeps the positions.

*Example.* Drag two overlapping tags apart and press Tidy: their neighbours move to make room, and the two stay where you put them.

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
