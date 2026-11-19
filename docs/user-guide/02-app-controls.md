# App controls

## Control reference

Each control below either sets a field of the Network State key (and so changes the `state_id` and recomputes everything) or only changes the view. Defaults come from the Build's `network.toml`; the values shown are the shipped defaults. Each analytical control links to its full entry under [Analytical controls explained](#analytical-controls-explained).

| Control | What it does | Range and default | Network State field | Which numbers change |
|---|---|---|---|---|
| Build | The Build's name in the header: switches this tab to another Build ([Switch Builds](01-getting-started.md#switch-builds)) | The Builds the app can see; the one the tab opened | `build_id` | All |
| Dataset | Loads one Top-N Dataset of the Build | The Build's datasets (the default Steam Build: Overall, Puzzle, RPG, Strategy, Simulation); Overall | `dataset` | All |
| [Minimum games per tag](#minimum-games-per-tag) | A tag becomes a node only if at least this many of the N games have it | 1–40; 8 | `min_games_per_tag` | Node set, and so everything in the network |
| [Minimum shared games](#minimum-shared-games) | An edge exists only if the two tags share at least this many games | 1–30; 8 | `min_shared_games` | Edge set, isolated tags (One-Tag Clusters), everything after |
| [Minimum Months Filter](#minimum-months-filter) | Drops games with fewer Months Observed before the network is built; never re-ranks or backfills | 0–60; 0 (off) | `min_months` | N, every `n_games`, every `lift`, the Global layout, everything after |
| [Hidden Genre Tags](#hidden-genre-tags) | Hides each ticked Genre Tag (the 11 Top-Level Genres) from the network, never from the dataset | 11 toggles; all hidden | `hidden_tag_ids` | Node set; not N, not any remaining edge's `lift` |
| [Hide defining tag](#hide-defining-tag) | Hides the dataset's defining tag (Puzzle, RPG, Strategy or Simulation) | toggle; hidden | `hidden_tag_ids` | As above |
| [Clustering weight](#clustering-weight) | What community detection runs on: shared games or lift. Edge thickness follows it; thresholds always use shared games | Shared games, Lift; Shared games | `clustering_weight` | Partition, every weighted metric, null model, Seed-Noise Floor, Global layout, edge thickness |
| [Clustering algorithm](#clustering-algorithm) | Louvain or Leiden (both seek high modularity) | Louvain, Leiden; Louvain | `algorithm` | Partition and everything computed from it |
| [Resolution γ](#resolution-γ) | Higher γ gives more, smaller clusters. Sends on Enter or when the box loses focus | ≥ 0.01, step 0.01; 1.00 | `resolution` | Partition, the value of Q |
| [Seed](#seed) | Seeds the clustering; the null-model and noise seeds derive from it. Sends on Enter or when the box loses focus | integer ≥ 0; config value | `seed` | Partition, null model, Seed-Noise Floor, Global layout |
| [Remove (node inspector), Restore, Reset all](#remove--restore) | Removes a tag from the network as a what-if, or brings it back | any node; none removed | `removed_tag_ids` | Node set; not N or any `lift` |
| [Global / Cluster-separated](#global--cluster-separated) | Moves nodes only: one layout for the whole network, or one region per cluster | Global | none | Positions only |
| [Tidy](#tidy) | Settles the Global layout from the current positions, keeping the nodes you dragged where you dropped them; kept until the dataset, filter, weight, seed or the visible tags change | none | none (`layout_source` in exports) | Positions only |
| Mode | Workbench, Analysis Report mode or [Parameter Selection](#parameter-selection-mode) | Workbench | none | none |
| [EN / BG](#interface-language) (header) | Shows the interface and this guide in English or Bulgarian; remembered per browser | English | none | none |
| « Controls / » Inspector / ▾ Tables (each panel's title bar) | Collapses that panel; the thin rail it leaves on its edge reopens it | all shown | none | none |
| Graph only (top right of the graph) | Switches to the narrowest form (pill bar, floating Inspector, bottom sheet) at any width; press again to leave it | off | none | none |
| Find a tag… (header) | Finds any tag of the dataset: a tag in the network is selected, centred and opened in the Inspector; a missing tag opens a "Not in the network" card | none | none (Restore / Unhide on the card change `removed_tag_ids` / `hidden_tag_ids`) | none until you press the card's button |
| Fit (⤢, top right of the graph) | Fits the whole graph back into view after you zoom or pan | none | none | Positions only |
| Run, Continue, Cancel, Run for this tag | Removal Sensitivity, as a background job | not run | none (results are cached per `state_id`) | `removal_sensitivity.csv` only |
| Export this state | Downloads one zip with every table and the full state key | none | none | none |
| Open Network State… | Reopens an export zip or its `export.json` | none | all key fields | All, recomputed |
| Clear app cache | Deletes cached Removal Sensitivity and Parameter Selection results (shipped ones included) | none | none | none |

Sliders send their value when you release them; the value beside the slider's label updates while you drag. The number of null-model replicates R and of noise seeds K are set in the Build's config only; they have no control.

The Controls panel is split into four sections: **Data** (dataset, Minimum Months Filter), **Filters** (the two thresholds, the hidden Genre Tags and the defining tag), **Clustering** (weight, algorithm, γ, seed) and **State** (removed tags, Reset all, Export, Open, Clear app cache). A struck-through Genre Tag chip is hidden from the network; click it to show the tag. The count beside the heading ("11 of 11") says how many are hidden.

### Interface language

> **In short.** Shows the app and this User Guide in English or Bulgarian; nothing else changes.
>
> **Here:** lets a Bulgarian-speaking reader work with the most-played games' tag network in their own language.
>
> **Caution:** exports, tag names, game titles and dataset labels stay English in both languages.

The EN | BG switch at the right of the header, in every mode; its `?` opens this entry. Default English. Not part of the Network State.

Switching relabels every label, message, tooltip and generated sentence at once, and opens this guide in the chosen language; nothing is recomputed and a running job carries on. Numbers on screen follow the language: Bulgarian writes 0,42 and 42%. Where a Bulgarian text is not written yet, the English one is shown in its place.

These stay English in both languages: every exported file (the CSV tables, `export.json`, `selection_report.md`), Steam tag names, game titles, Steam Genre values, the cluster labels `C1…`, the five dataset labels and the column names of the tables.

The choice is remembered per browser, in a cookie, so it survives closing the app and starting it on another port. Another browser, or a private window, starts in English.

*Why it matters here.* The numbers and the clusters of the most-played games are the same in both languages, so a reader can work in Bulgarian and cite an English export.

*Caution.* Quote column names, file names and tag names as the exports write them, in English, even when you read the interface in Bulgarian.

*Example.* Choose BG: the Controls become Настройки and Q 0.42 is shown as 0,42; an export made now has the same English files as before.

## Analytical controls explained

Each control below changes the Network State, and so the `state_id` and the numbers, except Global / Cluster-separated and Tidy, which move nodes only. In the app, the controls whose effect needs interpretation (Minimum Months Filter, Clustering weight, Clustering algorithm, Resolution γ and Seed) have a dotted label: hover over it or reach it with Tab for its short explanation, and click it for the entry below. The other controls are self-explanatory there and carry no tooltip; their entries are here for reference.

### Minimum Months Filter

> **In short.** Leaves out games with fewer Months Observed than this before the network is built.
>
> **Raising it →** fewer games (a smaller N), each with a longer player record; 0 = every game.
>
> **Here:** checks whether the clusters hold among the games tracked longest, not only among recent releases.
>
> **Caution:** it never re-ranks or adds games: N shrinks, so lift and some counts change.

Range 0–60 months; default 0 (off). Network State field: `min_months`.

Games are ranked by Mean Monthly Players over the months they were observed, so a game released shortly before the Snapshot is ranked on its launch months, when player counts are usually highest. Raising the filter drops such games from the loaded Top-N Dataset before anything is counted: N falls, every tag's game count and every lift is recounted over the remaining games, and the Global layout is redone. Lowering it back to 0 uses every game of the dataset. The Games number in the summary row shows how many games pass ("91 of 100").

*Why it matters here.* The study asks which characteristics recur among the most-played commercial games. A cluster that appears only while recent releases are included may reflect a few new games rather than a combination that holds over a longer player record; one that stays when the filter is raised rests on games with a long player record.

*Caution.* The filter never fills the gap with the next-ranked games, so a raised filter means a smaller network, not a different Top N. With fewer games, fewer tags reach the minimum games per tag and fewer pairs reach the minimum shared games, so compare Network States at the same thresholds and expect the numbers to shift with N alone. The feature analysis ignores the filter.

In an Import Build the slider carries the name of the Import's filter field and takes its range from the data; an Import without a filter field has no slider (see [What changes in an Import Build](08-imported-data.md#what-changes-in-an-import-build)).

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
> **Raising it →** fewer links, more isolated tags (One-Tag Clusters); clusters may split or reorganise.
>
> **Here:** sets how often two characteristics must occur together among the most-played games to count as linked.
>
> **Caution:** a missing link does not mean two tags never occur together.

Range 1–30; default 8. Network State field: `min_shared_games`.

Each pair of node tags sharing at least this many games gets a link. Raising the threshold removes the links with the fewest shared games first (the thinnest under the Shared games weight); a tag that loses all its links becomes isolated and forms a One-Tag Cluster. Lowering it adds links between tags that share few games, and the network becomes denser.

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

*Caution.* Hidden tags are listed in the Not in network table with the reason `genre_tag_hidden`. The list of Genre Tags is set in the Build's config. The dataset's defining tag has its own toggle: see [Hide defining tag](#hide-defining-tag).

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

With shared games, a link counts the games that carry both tags, so common tags carry the most weight and clusters tend to gather around them. With lift, each link is weighted by how much more often the pair occurs than the two tags' frequencies predict, so pairs of less common tags that go together carry more weight. Both thresholds always use shared games; [edge thickness](#edge-thickness) follows the weight.

*Why it matters here.* Shared games describes the most-played games as they are: which characteristics they carry together most often. Lift asks what they combine beyond popularity. Comparing the two weights shows which clusters reflect frequent tags and which reflect characteristics that go together.

*Caution.* Q, coverage, the active strength, conductance and the null model change with the weight, so never compare them across the two. Lift is inflated for pairs of rare tags, so read lift-based clusters with the shared-games counts beside them.

*Example.* A pair of tags each on 12 of 100 games and sharing 9 has lift 6.25: under lift, that pair weighs far more than two common tags sharing 40 games with lift 1.1.

### Clustering algorithm

> **In short.** The method that searches for the clusters: Louvain or Leiden, both seeking high modularity (neither guarantees the best).
>
> **Here:** running the second method on the same network shows whether the clusters depend on the method.
>
> **Caution:** Louvain can return a cluster in disconnected pieces; Leiden never does.

Louvain or Leiden; default Louvain. Network State field: `algorithm`.

Both algorithms search for the split with the highest modularity Q at the chosen γ, and both are randomised, so the seed matters for either. Leiden refines the clusters it finds and guarantees that each one is connected; Louvain is the default here.

*Why it matters here.* A group of characteristics that both methods find is less likely to be an artefact of one search procedure. Since both seek high values of the same Q, their Q can be compared directly at the same γ and Clustering Weight.

*Caution.* The two can give different splits with similar Q; that is a property of modularity, not a fault of either. Under Louvain, check the number of disconnected clusters in Cluster quality.

*Example.* Switch to Leiden and compare the multi-tag cluster count, Q and the disconnected-cluster count (always 0 under Leiden); quote both `state_id`s.

### Resolution γ

> **In short.** Sets the scale of the clusters: the resolution in the modularity that the clustering seeks to maximise.
>
> **Raising it →** tends to give more, smaller clusters; lowering it, fewer and larger ones.
>
> **Here:** shows whether the groups of characteristics hold at a finer or a coarser scale.
>
> **Caution:** Q at different γ is not comparable; compare the clusters instead.

Any value from 0.01 up, in steps of 0.01 (no maximum); default 1.00. Network State field: `resolution`. The box sends its value on Enter or when it loses focus.

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

*Caution.* Positions are drawn after every metric is computed and never feed back into one. Two tags drawn close together may share few games, and a tag can sit among another cluster's tags ([Position](#position)).

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

## Reading the graph

> **In short.** What the drawing shows: node size = games, link thickness = the Clustering Weight (shared games or lift), colour = Multi-Tag Cluster, grey = One-Tag Cluster.
>
> **Here:** lets the tag network of the most-played games be read at a glance, before the numbers.
>
> **Caution:** positions and distances on screen are not metrics.

The legend at the bottom left of the graph lists the Multi-Tag Clusters by colour, label and size ("C1 · 26"), then the number of One-Tag Clusters, and says what link thickness shows ("Edge thickness: shared games" or "Edge thickness: lift"). Click a cluster's chip to select the cluster; click **Key** for this section. ◆ marks a Cluster Center. Everything below describes the drawing only; every number it shows is in the Inspector and the tables.

*Why it matters here.* The drawing is the quickest way to see which characteristics the most-played games carry together and how the clusters touch. Knowing what each visual property encodes keeps it from being read as more than it is: a big node is a common tag, not a central one, and two tags drawn side by side may share few games.

### Node size

> **In short.** A node's size shows how many of the network's games carry the tag.
>
> **Higher →** bigger node: more games, relative to the dataset's most frequent tag.
>
> **Here:** shows at a glance which characteristics most of the most-played games carry.
>
> **Caution:** size reflects only the game count, never links, clusters or any other metric.

The diameter is 18 pixels plus up to 30 more, growing with the square root of the tag's game count relative to the most frequent tag of the dataset after the Minimum Months Filter, hidden tags included. Bigger nodes have more games, but the size is not proportional to them. The thresholds and hiding or removing tags never change it; the Minimum Months Filter does. In a Tag-Specific Dataset the most frequent tag is usually the hidden defining tag, so no visible node reaches the largest size.

*Why it matters here.* Common tags shape the whole network, so it helps to see them. A large node at the middle of a cluster is a frequent characteristic of the most-played games, and the cluster may gather around it partly for that reason; compare its Cluster Center and its game count in the Inspector.

*Example.* With the dataset's most frequent tag on 80 games, a tag on 20 games is drawn 18 + 30 × √(20 / 80) = 33 pixels across at 100 % zoom, and the most frequent tag 48 pixels.

### Edge appearance

> **In short.** A link's thickness shows the Clustering Weight: how many games carry both tags, or the pair's lift.
>
> **Higher →** thicker link: more shared games, or a higher lift, relative to the network's largest value.
>
> **Here:** the thickest links are the pairs the clustering weighs most.
>
> **Caution:** the legend says which one is drawn; never compare thicknesses across the two.

Under the Shared games weight, thickness shows shared games. Under Lift it shows lift; tick **show shared games** in the legend to draw shared games while the clustering still runs on lift. The legend always says which one is drawn: "Edge thickness: shared games" or "Edge thickness: lift". When the look differs from the default it says so too, for example "Edge thickness: shared games (√, 0.5–4 px) · 12 hidden".

By default every link is drawn thin and faint, from 0.4 pixels up to 3 pixels at 100 % zoom for the pair with the largest value in the network, so that the dense network stays readable; the first fit is never above 100 %, so links usually look thinner. Selecting a tag makes its links opaque (in one colour, darker). A link exists only when the pair reaches the minimum shared games, whatever thickness shows.

Press **Edges** beside the legend's key to open the Edge appearance card over the graph: a histogram of the drawn value per link, with the drawn width over it, and the controls below. Every control changes the drawing only, never the Network State, a threshold of the network or any number, and none of them is exported. The look (width, scaling, colour and the two strengths) is remembered per browser, like the [Interface language](#interface-language); **Reset all** leaves it alone, and the card's own **Reset** returns to the default look. The same look applies to both layouts and to Analysis Report mode.

*Why it matters here.* Drawn by the Clustering Weight, the thick links are the ones that pull tags into the same cluster, so the drawing and the clusters tell the same story. Shared-game thickness picks out the pairings that recur most among the most-played games, which mostly join common tags; lift thickness picks out pairings carried together more often than the tags' frequencies predict, which often join rarer tags. Under lift, switching to shared games shows how many games stand behind a thick link; read both numbers in the Inspector.

*Example.* If the most shared pair in the network shares 60 games, a link of 30 shared games is drawn 0.4 + 2.6 × 30 / 60 = 1.7 pixels wide at 100 % zoom. Under lift, with a largest lift of 8, a link of lift 2 is drawn 0.4 + 2.6 × 2 / 8 = 1.05 pixels wide.

#### Width

> **In short.** − and + make every link thinner or thicker, the thinnest and the thickest together, by a quarter each step.

The thinnest link stays between 0.1 and 3 pixels and the thickest between 1 and 12. The button's tooltip gives the current range.

*Why it matters here.* A figure for print or a large screen often needs heavier links than the dense default.

#### Scaling

> **In short.** How a link's value turns into its width: linear, square root or logarithmic.

Linear is the default: width grows in proportion to the value. Square root (√) and logarithmic (log, from the smallest value to the largest) widen the many low values, so that the differences among the weaker links show.

*Why it matters here.* On shared games a few pairs of common tags take most of the range; √ or log make the rest of the most-played games' pairings readable.

#### Colour

> **In short.** One colour; by Cluster (links inside a Multi-Tag Cluster in its colour); within vs between Clusters; or by value.

By value runs from light grey for the smallest drawn value to dark violet for the largest, on the same scale as the width. A selected tag's links keep their colour and become opaque.

*Why it matters here.* By Cluster and within vs between show at a glance which links hold a cluster together and which join two.

#### Strength

> **In short.** − and + make every link fainter or bolder (its opacity), by about a third each step, from 3 % to 100 %.

The default is 18 %, faint enough to read the tags through a dense network.

*Why it matters here.* A sparse network (a high minimum shared games) reads better with bolder links.

#### Links between Clusters

> **In short.** In the Cluster-separated layout, how faint the links between two Clusters are, from 0 % (not drawn) to 100 %.

The default is 6 %. Shown and applied only in the Cluster-separated layout, where those links cross between the regions.

*Why it matters here.* Raise it to see how the separated clusters of the most-played games' tags connect; lower it to read each region on its own.

#### Hide links below

> **In short.** Drag the handle on the histogram to stop drawing the links below a value; every number still counts them.
>
> **Caution:** a view choice only; **Minimum shared games** is the filter that changes the network.

The card always says how many links are hidden from the drawing. A hidden link is not drawn, cannot be clicked and does not light up when its tag is selected, but it still counts in the Inspector's connected tags, the Edges table and every number; a tag whose links are all hidden stays drawn. The value is in the drawn measure's units: it clears when the measure changes (the Clustering Weight, the show-shared switch or the dataset), is kept across other changes of the Network State, and is never remembered.

*Why it matters here.* It thins a crowded drawing of the most-played games' tag network without changing a single number, unlike Minimum shared games, which removes the links from the Network State.

### Cluster map

> **In short.** A small map of the clusters: a bubble per Multi-Tag Cluster, sized by its tags; a curve per linked pair.
>
> **Higher →** a thicker line: a higher [Connection Ratio](03-metric-reference.md#connection-ratio).
>
> **Here:** which clusters of the most-played games' tags connect, and how much for their sizes.
>
> **Caution:** the ring only orders the clusters by their links; distance on the map is not a metric.

Press **Cluster map** at the top right of the graph to open a card over it; press it again, or the card's ×, to close it. It stays open while the app runs and opens closed the next time. Each Multi-Tag Cluster is a bubble in its colour, with an area by its number of tags (never too small to click), placed evenly on a ring and labelled outside the bubble ("C1 · 15 tags"); hover over a bubble for its top tags. The ring does not copy the graph: it starts from the cluster with the most link weight and puts each next to the one it is most strongly linked to, so the same network always gives the same map. Only pairs with at least one link get a curve, drawn inside the ring so it never passes under a bubble. Its width is its ratio against the strongest link on this map, which the key under the map names together with the weakest; the weakest third of the links is drawn thin and faint. The One-Tag Clusters are a note under the map ("+ 13 one-tag clusters"). Click a bubble to select its cluster, or a curve to select the pair; any selection lights up on the map, with the ratio written on the selected pair and on the selected cluster's curves. The card never moves or re-draws the graph.

*Why it matters here.* The full graph shows every tag; the map shows the same clusters of the most-played games' characteristics as a handful of groups, so their connections can be read at once, then explored pair by pair in the Inspector.

### Cluster colour

> **In short.** Each Multi-Tag Cluster gets a colour by its label, C1 (the largest) first; the 16 colours repeat from C17.
>
> **Here:** shows which characteristics the clustering grouped together.
>
> **Caution:** labels and colours follow cluster size, so the same cluster can get another colour after a small change.

Colours come from a fixed palette of 16 in label order: C1 has the first colour, C2 the second, and so on; from C17 the colours repeat, so C17 has C1's colour. In the Cluster-separated layout each Multi-Tag Cluster also gets its own tinted region.

*Why it matters here.* A colour is the quickest way to see a candidate combination of characteristics among the most-played games. It says nothing about what the cluster means: read its members, its Cluster Center and its Membership Stability.

*Example.* After raising the minimum shared games, the second-largest cluster can become the largest: it is then labelled C1 and takes C1's colour.

### Position

> **In short.** A tag is drawn where its links pull it; its colour is the cluster the clustering gave it. The two can disagree.
>
> **Here:** a tag drawn among another cluster's tags is often a hub or a boundary characteristic of the most-played games.
>
> **Caution:** never read a tag's cluster from where it sits; read its colour and the Inspector.

In the Global layout every link pulls its two tags together, in proportion to its weight on the Clustering Weight in use, and every pair of tags pushes apart ([Layout positions](03-metric-reference.md#layout-positions)). The clustering asks something else: it puts a tag in the cluster where its links are strongest *compared with what the tags' game counts alone would give* ([Modularity Q](03-metric-reference.md#modularity-q)). So a tag can sit among one cluster's tags and carry another's colour. This is common, not an error; there are three usual reasons.

- **Most of its links go to another cluster's common tags.** Links to tags that are on many games count for less in the clustering, because such tags share games with almost everything; in the drawing they pull at full strength. In the Inspector, *Shared games in own cluster* (under Lift, *Lift in own cluster*) is then less than half of *Total shared games* (*Total lift*).
- **It is a hub.** A tag such as Singleplayer or Multiplayer links to almost every other tag, so it sits where all those pulls balance, rarely inside its own cluster. Tags with many links are also pulled less by each one and push each other apart harder, so hubs drift outwards, and tags whose only link is to a hub are drawn next to it. In the Inspector, most of its *Links · in own cluster* fall outside the own cluster, and *Spread across clusters* is high.
- **Its membership is uncertain.** With a low *Membership Stability*, other seeds often put the tag in another cluster: the drawing shows a boundary that really is blurred.

No layout setting removes this: a flat drawing cannot keep every cluster in one piece when a few tags link to all of them. The Cluster-separated layout always shows each cluster in one piece.

*Why it matters here.* Where a tag's colour and position disagree is where the clusters of the most-played games' characteristics meet, which is often the most telling part of the graph. Read which cluster a tag is in from its colour, and how firmly from the Inspector, never from its neighbours on screen.

*Example.* A tag shares 30 games with the tags of C2 and 50 with those of C1, but C1's tags are on many games each, so the clustering puts it in C2. The Inspector shows *Shared games in own cluster* 30 of *Total shared games* 80, and the Global layout draws it at the edge of C1, in C2's colour.

### Grey One-Tag Clusters

> **In short.** Grey nodes are One-Tag Clusters: tags left on their own, usually because no link reaches them.
>
> **Here:** shows characteristics that recur among the most-played games without sharing enough games to join a Multi-Tag Cluster.
>
> **Caution:** a One-Tag Cluster is usually an isolated tag, not a finding.

The legend's last chip gives their number ("4 one-tag"); click it for this entry. Most are isolated tags: they reach the minimum games per tag, but no pair with them reaches the minimum shared games. Occasionally the algorithm leaves a linked tag alone. In the Cluster-separated layout they share one grid region.

*Why it matters here.* A grey tag is in the network but in no group. Lowering the minimum shared games often lets it join a cluster, which shows which group of characteristics it is closest to.

*Example.* A tag on 9 games that shares at most 6 games with any other tag has no link at a minimum of 8 shared games, and is drawn grey.

## Find a tag

The search box in the middle of the header works in every mode and form, including Graph only. Type part of a tag's name; the list shows the tags **in the network** first (with their cluster colour, cluster and games), then every tag of the dataset that is **not in the network**, greyed out, with all its reasons in plain words: "Genre Tag hidden", "defining tag hidden", "removed", or "3 games, below 8" (fewer games than the Minimum games per tag). Use ↑ / ↓ and Enter to choose, Esc to close.

- Choosing a tag in the network selects it, centres the graph on it and opens it in the Inspector.
- Choosing a missing tag opens a **Not in the network** card with its reasons and its number of games. When exactly one action brings it back, the card offers it: **Restore** for a removed tag, **Unhide** for a hidden Genre Tag or defining tag. Nothing changes until you press it, and pressing it changes the Network State, exactly as the Restore button or the hidden-tag chips would. A tag below the minimum games, or one that would need two changes, gets no button.

## Window width and the three forms

The Workbench rearranges itself as the window narrows. Nothing is lost in a narrower form; every control is still one or two clicks away.

- **Wide (1280 px and more)**: three panes. Controls on the left, the graph in the centre, the Inspector on the right, the tables below the graph. Drag the bar between the graph and the tables to give either more room.
- **Medium (1024–1279 px)**: the Controls panel becomes a **pill bar** under the header. Each pill shows the current value ("Min games 8", "γ 1.00"); click it to open a small panel holding that control, and click anywhere else (or press Esc) to close it. The bar's last button, «, collapses it, and the bar it leaves under the header reopens it. The Inspector becomes a **floating card** over the right of the graph: it opens when you click a node, an edge or a cluster, and closes with ×. The graph refits so that nothing hides under the card.
- **Narrow (under 1024 px)**: as medium, and the tables become a **bottom sheet**: a strip of tabs along the bottom of the graph. Click a tab or the grip on the left to open the sheet, and the grip again to close it.

**Graph only** gives the narrow form at any width. Collapsing the Inspector in the wide form also makes it a floating card. The legend sits at the bottom left of the graph; the Global / Cluster-separated switch, Tidy, Cluster map, Fit and Graph only sit at the top right.

Each panel collapses from its own title bar: « on the Controls, » on the Inspector, ▾ on the tables' tab strip. A collapsed panel leaves a thin rail on its edge with its name; click the rail to bring the panel back. The graph refits into the room either way.

## Task recipes

### Check whether a cluster survives removing its center

1. Click the cluster's legend button. The inspector shows its members, its Cluster Center (◆) and the `top_strength_tag`.
2. Click the center node and press **Run for this tag**. When it finishes, read `rc_ari` and `rc_centers_lost` in the node inspector or the Removal sensitivity tab.
3. Compare `rc_ari` with the Seed-Noise Floor's `seed_ari_min`. Above it, the partition changed no more than the most different of the K seeds did. Below it, the row carries the screening flag. To see the new partition itself, press **Remove** instead and look at the clusters; **Restore** brings the tag back.

### Compare Louvain and Leiden

1. Note the Cluster-quality row and the Seed-Noise Floor under Louvain.
2. Switch **Clustering algorithm** to Leiden. Compare the multi-tag cluster count, Q (both seek high modularity, so Q is comparable at the same γ and weight) and `n_disconnected_clusters` (always 0 under Leiden).
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

### Compare the Clusters of two datasets

1. Run Automatic Parameter Selection for the datasets you want to compare (**Run all datasets** in the Parameter Selection mode), so each starts on its chosen pair.
2. Switch to **Cluster Comparison**. Every dataset is included; the pair with the highest ARI is chosen. Choose the dataset for each side in the two dropdowns above the diagram, or click a row under **Dataset pairs**.
3. Read the diagram: one curve per Cluster Match at or above the **Minimum Match Jaccard**, a badge on each Cluster with no such match. Click a curve to open the match, with its shared and unshared Tags and the games in both Clusters.
4. Before quoting a match, check each dataset's Seed-Noise Floor and NA in its row, and see whether the match survives another Threshold Pair ("Use in Cluster Comparison" on a neighbouring cell).
5. **Export CSV** records every pair; quote the `comparison_id` with every number you use.

## Parameter Selection mode

The third mode runs [Automatic Parameter Selection](03-metric-reference.md#how-automatic-parameter-selection-works) and shows its results. It has the Workbench's three panes: Controls on the left (Run, Selection settings), the dataset strip with the Pair Constraints under it, heatmap, "Why this pair" and validation card in the middle, and the Pair Inspector on the right. At medium and narrow widths the Controls become a pill bar and the Inspector a floating card, as in the Workbench; the Pair Constraints stay under the dataset strip at every width. In this mode the Controls (« in their title bar), the Pair Constraints (▴ beside their heading) and the Pair Inspector (») collapse the same way, each leaving a rail that reopens it; the heatmap widens into the room they leave.

### Run

> **In short.** Run searches the Parameter Grid of one dataset or of all five, chooses a pair for each and validates it, as a background job.
>
> **Here:** produces every number this mode shows; finished work is cached and never recomputed.
>
> **Caution:** a full run takes minutes; Cancel keeps finished pairs but discards an unfinished validation.

**Run all datasets** or **Run ‹dataset›** starts a background job; **Cancel** stops it. Each dataset's row shows its phase and progress: "grid 87 of 153 pairs", "validation 40 of 200 replicates", "grid done, not validated" or "not run". "All datasets" computes every grid before any validation. After a cancel, **Continue (k of 153 pairs)** resumes from the pairs already on disk; a cancelled validation starts again from the beginning. While a job runs, a loading panel says what is computed, why, where the job is and how long it should still take; it covers the middle column until the job ends, while the Controls, with Cancel, stay in reach.

The cache line names the Build, the settings key and the method version. When the results were computed elsewhere, a quiet **provenance line** says so, for example "Computed when this bundle was made: Python 3.14.0, Windows AMD64, 2026-10-26": an App Bundle ships each Build's results, computed when the bundle was made. **Clear app cache** replaces them with this computer's on the next Run. A recomputation on another Python version or operating system could in principle differ, but practically never does, because every library version is locked. If a library the app computes with is installed at a different version, a banner says so instead and suggests "Clear app cache and Run to recompute here".

*Why it matters here.* The grid is 153 pairs × up to several hundred γ values × 10 seeds per dataset, plus 200 validation replicates; caching it makes the mode instant after the first run.

*Caution.* Results belong to one Build and one set of Selection Settings; another set needs its own run.

*Example.* "Run all datasets" on a 12-worker computer fills the five heatmaps one dataset at a time, then validates each chosen pair.

### Pair Constraints

> **In short.** The Pair Constraints and the tolerance decide which pairs qualify and how close to the best Neighbour Agreement a pair must be; Confirm re-chooses from the cache.
>
> **Here:** lets you see how the choice depends on each constraint without rerunning anything.
>
> **Caution:** non-default values are labelled "Custom constraints"; the shipped validation stays with the default pair.

The Pair Constraints sit under the dataset strip, one pill per constraint, each showing its value, in two rows: first the ones most often changed (minimum Information Retention, maximum isolated share and the tolerance), then minimum LCC share, minimum comparable neighbours with a different graph and maximum Multi-Tag Clusters; a pill whose value differs from the default is highlighted. A pill opens its field, with the default beside it and a "changed" marker; an empty maximum means off. **All five datasets** or **this dataset only** chooses where the constraints apply. **Confirm** is enabled once something changed ("Unconfirmed changes" shows meanwhile) and recomputes the choice from the cache, with no job; **Reset to defaults** restores the configured values. The constraints label beside these buttons names each changed value. The definitions are in [Pair Constraints, Qualifying Pair and the selection rule](03-metric-reference.md#pair-constraints-qualifying-pair-and-the-selection-rule).

*Why it matters here.* A pick that moves under a small change of a constraint is a weaker reason to prefer it; the heatmap's reason letters show which constraint excludes which pair.

*Caution.* Validation is cached per pair and runs automatically only for the pair chosen under the default constraints; use Validate this pair for another.

*Example.* Raising the minimum retention to 0.60 and pressing Confirm moves the ★ in puzzle and labels the explanation "Custom constraints: Information Retention ≥ 0.60 (default 0.50)".

### Selection settings

> **In short.** The Selection Settings fix every pair's network and Selected Partition: hidden and removed tags, Minimum Months, the Clustering Weight and the minimum Multi-Tag Clusters.
>
> **Here:** run the selection under the settings you study, not only the defaults.
>
> **Caution:** a change needs its own run; Lift is the studied default.

Edits are staged: **Use these settings** switches the mode to that settings key and shows what the cache holds for it, or "not run"; no edit starts a job. **Reset to defaults** restores the configured values, and **Copy from Workbench** copies the Workbench's hidden tags, Minimum Months, Clustering Weight and removed tags (never g, s, γ or seed). Removed tags come from the tag picker, from Copy from Workbench, or from **Remove** on a tag in the Pair Inspector's Clusters. The settings last for the session; the app always opens on the defaults. The read-only settings are shown with their values: Leiden only (the scan and Apply's reproduction search are built on it), the Parameter Grid, the γ step, the 10 scan seeds, R and S. Lift is the studied default weight. Whichever weight is used, γ̂ is a heuristic outside unweighted multigraphs: [Resolution estimate and Stable Partition](03-metric-reference.md#resolution-estimate-and-stable-partition) explains why.

*Why it matters here.* A tag hidden or removed in the Workbench changes every network the selection would see; the selection under default settings says nothing about such a network.

*Caution.* Raising the minimum Multi-Tag Clusters above an active constraint maximum raises the maximum to match, as custom.

*Example.* Minimum Months 12 shows "Custom settings: Minimum Months 12 (default 0)" under the section and in the explanation.

### Dataset strip

> **In short.** Five buttons, one per dataset, each with its chosen pair and Neighbour Agreement or its status.
>
> **Here:** the only comparison between datasets this mode makes.
>
> **Caution:** different pairs in different datasets are not a disagreement.

Each button shows "★ 14·2 NA 0.98", "no qualifying pair", "not run" or "grid k of 153", with a "custom" marker when either label is custom (its tooltip says which). A click switches the dataset and resets the heatmap and Inspector to that dataset's ★ pair; the metric picker keeps its choice. Each dataset is selected on its own, from its own games and tags. Different pairs in different datasets are expected and are not a disagreement: the same pair builds networks of different sizes in different datasets.

*Why it matters here.* The datasets differ in which tags are common, so the thresholds that keep a coherent network differ too.

*Caution.* No agreement score between datasets is computed here; their Clusters are compared in the [Cluster Comparison mode](#cluster-comparison-mode).

*Example.* "★ 17·2 NA 0.97" for overall beside "★ 14·2 NA 0.98" for puzzle.

### Heatmap and reason letters

> **In short.** The g × s grid of one dataset, coloured by one metric, with the chosen pair, the near-best set and each pair's failing reasons marked.
>
> **Here:** shows where in the grid each number and each exclusion lies.
>
> **Caution:** Q is descriptive: not comparable across pairs, shown in grey with no best marker.

The metric picker chooses Neighbour Agreement, Information Retention, isolated share, Multi-Tag Clusters, Seed-Noise Floor or Q. ★ marks the chosen pair, orange outlines the near-best set and a dark outline the inspected pair. Each non-qualifying cell carries one letter per failing reason: **P** no Selected Partition, **A** no Neighbour Agreement, **N** too few comparable neighbours, **R** retention below the minimum, **I** isolated share above the maximum, **L** LCC share below the minimum, **K** too many Multi-Tag Clusters. Hovering shows the value, NA, tags, Multi-Tag Clusters and "✓ qualifies" or the reasons in words; clicking a cell inspects it, and "Why this pair" then explains that pair: whether it qualifies and, if it does, why another pair was selected (the ★ pair's own explanation shows until a cell is clicked). While a grid is unfinished, computed cells fill in as they arrive, a cell's NA appears once its neighbours are computed, and no ★ or outline is shown.

*Why it matters here.* Neighbour Agreement tends to rise with g; the heatmap shows that trend next to the retention it costs.

*Caution.* A cell's colour compares pairs only for the selection metrics; Q and the Seed-Noise Floor describe each pair on its own network.

*Example.* A cell marked "R I" keeps too little of the data and leaves too many tags isolated.

### Pair Inspector

> **In short.** Everything about one pair: its badges, Apply, its metrics, its neighbour links, the CHAMP plot, its Clusters and a compact validation.
>
> **Here:** shows why a pair qualifies or not, and what its Selected Partition is.
>
> **Caution:** the CHAMP plot is for inspection; only the Selected Partition can be applied.

It shows the dataset's ★ pair until you click a cell. Top to bottom: the title and status badges (qualifies or its reasons; `clipped_high`, `not_representable`, `not_reproduced`); **Apply to Workbench** with the Workbench γ and seed line; the metrics (NA with its neighbour counts, Retention, isolated and LCC share, Multi-Tag and One-Tag Clusters, the Seed-Noise Floor, the hit count, the domain, the Selected Resolution and the scan range), then the descriptive group (Q, Coverage, Silhouette) under "Descriptive: not comparable across pairs"; the neighbour links table (direction, status, ARI, tag overlap, [Edge Overlap](03-metric-reference.md#edge-overlap), identical-graph marker); the CHAMP plot (each Admissible Partition's Q(γ) line, the envelope, the domains, each γ̂ with an arrow to its map target, the Stable Partitions and the Selected Resolution, from 0 to γ_end); the Selected Partition's Clusters, with **Remove** on each tag; and the two verdict tags with the median ARIs.

*Why it matters here.* The heatmap shows where a pair stands; the Inspector shows the numbers behind it.

*Caution.* The descriptive group describes this pair only.

*Example.* A pair with an "N" letter shows, in its links table, which neighbours were missing or had an identical graph.

### Apply to Workbench

> **In short.** Opens the inspected pair's Selected Partition in the Workbench: its dataset, thresholds, Selection Settings, γ and seed.
>
> **Here:** turns a selected pair into a Network State with every Workbench metric and export.
>
> **Caution:** the Workbench's Seed-Noise Floor can differ from the one Parameter Selection reports.

Apply replaces every Workbench setting, as Open Network State… does: the dataset, g, s, Minimum Months, the hidden Genre Tags and defining tag, the removed tags, the Clustering Weight, the algorithm (Leiden), γ and seed. Tidy and the Removal Sensitivity view are cleared and the app switches to the Workbench, without asking. γ and seed are the pair's Workbench γ and seed: the two-decimal γ and the seed at which Leiden reproduces the Selected Partition. For a `not_reproduced` or `not_representable` pair, Apply uses the Selected Resolution rounded to two decimals and the main seed. The Workbench then shows "Applied from Parameter Selection: ‹dataset›, g=…, s=… — Selected Partition reproduced ✓", or the ARI of the partition it shows instead; the line stays until a setting changes, and an export made meanwhile records an `applied_from` block. Any pair with a Selected Partition can be applied.

The Build's [Workbench Seed Priority](03-metric-reference.md#workbench-seed-priority) sets the order in which the Workbench γ and seed are searched. **Closest γ to the midpoint** (the default) goes outwards from the two-decimal γ nearest the CHAMP midpoint and, at each γ, tries the main seed and then the scan seeds. **Prefer the main seed** first tries the main seed at every γ, and only then the scan seeds, again from the nearest γ. Both show the same Selected Partition whenever it can be reproduced; they differ only in the γ and seed it is shown at, and so in Q, the Connection Ratios, the Workbench's Seed-Noise Floor and Removal Sensitivity. Keep the default: it keeps γ nearest the midpoint, where the Selected Partition is furthest from being overtaken by another partition, and the seed has no meaning of its own, since every seed is an equivalent random draw and the scan seeds are derived from the main seed. On the reference Build, Prefer the main seed showed 92 of 667 pairs at a less central γ, a median 41% of the way from the midpoint to the domain's edge; none of the five default chosen pairs changed. Parameter Selection's Controls show the Build's value under the fixed settings; it is set when the Build is made ([Network defaults](07-making-builds.md#draft-network-defaults)) and is not a Selection Setting.

The Seed-Noise Floor can differ: when the Workbench seed is one of the scan seeds, the Workbench derives its noise seeds from that seed, while Parameter Selection derives them from the main seed and runs them at the exact, unrounded Selected Resolution. Prefer the main seed does not make the two floors agree: Parameter Selection's runs stay at the unrounded Selected Resolution, and on the reference Build the median gap between the floors grew from 0.000 to 0.027.

*Why it matters here.* Inspecting, removing tags from and exporting the selected network all happen in the Workbench.

*Caution.* The provenance line is display only: the Network State key and `state_id` are the same as for the same settings entered by hand.

*Example.* Applying puzzle g = 14, s = 2 sets γ 1.09 with a scan seed and shows "Selected Partition reproduced ✓".

### Use in Cluster Comparison

> **In short.** Put this cell into the Cluster Comparison for this dataset and switch there.
>
> **Here:** compares another cell's Selected Partition with the other datasets' Clusters.
>
> **Caution:** Available only when Parameter Selection's settings are the comparison's shared settings.

The button sits beside Apply to Workbench and is always shown. It is enabled under Apply's rule (a cell with a Selected Partition) and disabled when Parameter Selection's current settings differ from the Cluster Comparison's shared settings, including a shown defining tag; its tooltip then says "The Cluster Comparison uses other shared settings; this cell comes from a different run." Pressing it sets the cell as the dataset's values (its source line becomes "Selected Partition at g … · s …"), includes the dataset if it was left out, resolves the comparison and switches mode. Nothing is sent to the Workbench.

*Why it matters here.* A Cluster Match found at one pair is worth checking at a neighbouring pair; this is the way to put that pair into the comparison.

*Caution.* The comparison reads the cell's stored Selected Partition, never reclusters it.

*Example.* Inspecting RPG g = 8, s = 5 and pressing Use in Cluster Comparison shows RPG on that cell beside the other four datasets on their picks.

### Validate this pair

> **In short.** Runs the Null Comparison and Subsample Stability for the inspected pair, as a background job.
>
> **Here:** validates a near-best or hand-picked pair, not only the chosen one.
>
> **Caution:** all-or-nothing: Cancel discards it.

It is offered on any pair with a Selected Partition in a complete grid, also under `no_qualifying_pair`. It cannot run beside Run. Results are cached per pair, whatever the constraints. See [Null Comparison](03-metric-reference.md#null-comparison) and [Subsample Stability](03-metric-reference.md#subsample-stability).

*Why it matters here.* The validation card shows the default pair's validation; pairs you consider instead deserve the same check.

*Caution.* It never changes the chosen pair or its explanation.

*Example.* Under custom constraints the card notes "Validation ran for g = 17, s = 2, the pair chosen under the default constraints"; Validate this pair validates the new pick.

### Export tables

> **In short.** Writes one zip per settings key with eight tables, `parameter_selection.json` and a templated `selection_report.md`, for every dataset with a complete grid.
>
> **Here:** the record of a selection, for a paper's supplement.
>
> **Caution:** a record only: there is no way to open it back into the mode.

The zip is named `steamstudy_parameter-selection_<settings key>_<UTC>.zip`. Incomplete datasets are left out and listed in `parameter_selection.json`. The files are described in [chapter 4](04-files.md#parameter-selection-files); [Report a Parameter Selection](05-citing-and-reproducing.md#report-a-parameter-selection) says how to deposit and check it.

*Why it matters here.* Readers can recompute Neighbour Agreement and the choice from the tables without running Leiden.

*Caution.* The button is disabled until at least one dataset's grid is complete.

*Example.* An export after "Run all datasets" holds 765 rows in `pairs.csv`.

## Cluster Comparison mode

> **In short.** Matches the Multi-Tag Clusters of the Build's Top-N Datasets, two datasets at a time, on their Tags.
>
> **Here:** shows which Clusters of one dataset share Tags with which Clusters of another.
>
> **Caution:** a match is shared Tags, never evidence that the Clusters are real.

> **Caution.** A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is not evidence that the Clusters are real or that the datasets share a genre structure. A match can appear, vanish or change its Match Jaccard with the seed, with g and s, and with the resolution. Read it against each dataset's Seed-Noise Floor and Neighbour Agreement.

The fourth mode has a sidebar and a main column. The sidebar holds the shared settings with the `comparison_id`, then the datasets, then the dataset pairs; the main column shows the chosen pair as a link diagram with the match detail under it, and **Export CSV** beside the Minimum Jaccard slider. The sidebar is a drawer: « in its title collapses it to a thin rail on the left edge, and a click on the rail opens it again. It is open the first time you open the mode in a browser session and stays as you left it until the session ends. A notice from a shared-setting change shows at the top of the main column, so you see it with the drawer closed. At medium and narrow widths the sidebar collapses above the diagram as a pill bar, as the Workbench's Controls do, and the diagram keeps its two columns and scrolls. The comparison keeps everything you set (the included datasets and their values, the chosen pair and match, the minimum) across every mode switch; switching Build starts it afresh, every dataset on its pick. How the figures are computed is in [How a Cluster Comparison works](03-metric-reference.md#how-a-cluster-comparison-works).

*Why it matters here.* Each dataset is clustered on its own, from its own games, so the same genre combination may appear as a Cluster in several datasets. The mode lines them up by their Tags without merging the datasets.

### Shared settings

> **In short.** The Clustering Weight, algorithm, Minimum Months Filter, hidden Genre Tags and removed tags, one set for every dataset.
>
> **Here:** they decide which Automatic Parameter Selection run each dataset's pick comes from.
>
> **Caution:** a change resolves every dataset again and drops values set by hand.

The first section of the sidebar, with the `comparison_id` under it. They start from the Parameter Selection settings (Leiden, Lift, its Minimum Months Filter, its hidden Genre Tags and its removed tags), never from the Workbench's. Hidden Genre Tags is the same chip checklist as in Selection settings. There is no defining-tag control: each dataset's own defining tag is always hidden in that dataset, so a Parameter Selection run made with the defining tag shown never feeds the mode. Changing a shared setting resolves every dataset against the run for the new settings, on its pick if that run exists and with no run if not, and a notice says that values set by hand were dropped.

*Why it matters here.* A Selected Partition belongs to one set of Selection Settings; the comparison can only show it under the same settings.

*Caution.* With Louvain no Parameter Selection run can exist, so every dataset is clustered once at the network defaults.

*Example.* Unhiding one Genre Tag sends every dataset whose run under that setting is missing to "No Automatic Parameter Selection run".

### Datasets

> **In short.** One row per Top-N Dataset: include it, read where its partition comes from, and edit its g, s and γ.
>
> **Here:** each dataset shows its own partition at its own values.
>
> **Caution:** a dataset set by hand is one clustering with the main seed, not a Selected Partition.

Each row has an include checkbox, the dataset's name in its colour, and g, s and γ. Under the name, the **source line** says where the partition comes from, by Threshold Pair:

- "★ Selected Partition at g 9 · s 7 (chosen pair)": the run's pick under the Pair Constraints set in Parameter Selection;
- "Selected Partition at g 10 · s 6": another cell of the run, chosen in Parameter Selection or by typing its g and s;
- "Set by hand: one Leiden run, main seed": values that name no cell with a Selected Partition, or an edited γ;
- "No Automatic Parameter Selection run: network defaults, one Leiden run, main seed", with **Open Parameter Selection**; the line says so instead when the run has no qualifying pair, or when a selected cell's run is gone.

A dataset on a cell shows the cell's stored Selected Partition: it is read from the Parameter Selection cache, never reclustered, and has no seed of its own (the tooltip: it was found among the partitions of 10 scan seeds). A dataset set by hand or with no run is clustered once with the Build's main seed; the mode has no seed control. Under the source line, "Seed-Noise Floor 0.52 · NA 0.81" gives the run's floor and the cell's Neighbour Agreement, or the dataset's own floor and "—" off a cell. Typing g and s that name a cell with a Selected Partition selects that cell; any other pair, or an edited γ, sets the dataset by hand. The limits are the Workbench's. Each row links to Parameter Selection on that dataset with its cell highlighted. There is no route into the Workbench: to open a dataset there, use [Apply to Workbench](#apply-to-workbench) in Parameter Selection.

*Why it matters here.* The datasets differ in which tags are common, so each needs its own thresholds; the Selected Partition gives each a defensible one.

*Caution.* A changed Pair Constraint in Parameter Selection moves a dataset on its pick at the next resolve; a selected cell or values set by hand stay.

*Example.* With RPG set by hand to g 9, s 7, γ 1.20, its row reads "Set by hand: one Leiden run, main seed" and "Seed-Noise Floor … · NA —".

### Dataset pairs

> **In short.** Every pair of included datasets, ranked by ARI on their Comparable Tags, with the Comparable Tags and the games in common.
>
> **Here:** chooses which two datasets the diagram shows.
>
> **Caution:** ARI compares two partitions; it says nothing about any one match.

Each row shows ARI (comparable Tags) with a small bar, the number of Comparable Tags with their share of each network ("38 Comparable Tags: 76% of Overall's, 54% of Puzzle's") and the games in common. Clicking a row chooses the pair, its earlier dataset on the left; on first open the top pair is chosen. The two dropdowns above the diagram, Left ⇄ Right, choose each side directly from the included datasets: picking on one side the dataset already on the other swaps the two, and ⇄ swaps them too. Untick the dataset on one side and that side moves to the included dataset with the highest ARI against the other side, which stays put. With fewer than two datasets included, the list and the diagram say "Include at least two datasets to compare". See [ARI on Comparable Tags](03-metric-reference.md#ari-on-comparable-tags) and [Comparable Tags coverage](03-metric-reference.md#comparable-tags-coverage).

*Why it matters here.* A pair compared on a small share of either network can show few matches only because few Tags are in both.

*Caution.* The games in common are shown, never scored.

*Example.* On the full Build Strategy × Simulation leads with ARI 0.53 on 32 Comparable Tags (82% of Strategy's, 84% of Simulation's) and 48 games in common.

### Link diagram

> **In short.** The chosen pair's Multi-Tag Clusters in two columns, with a curve for each Cluster Match at or above the minimum.
>
> **Here:** shows at a glance which Clusters share Tags.
>
> **Caution:** a curve's width is Match Jaccard, not a measure of how alike the two genres are.

A's Multi-Tag Clusters stand in the left column and B's in the right, under headings naming each dataset; A is the dataset in the Left dropdown, B the one in the Right. Each box shows its label, its Tag count, its Tags (clipped to two lines), its flag as a badge, and a left border in the dataset's colour; a Cluster alone is always written with its dataset ("Overall C3"), since `C1…` labels mean nothing across datasets. Each curve's width and strength follow its Match Jaccard, written on it. Clicking a box shows only its curves and dims the Clusters it does not match; clicking it again shows all. Clicking a curve chooses the match. A line under the diagram counts each side's One-Tag Clusters, which are never matched. A pair with no Cluster Match says so.

*Why it matters here.* One Cluster can match several, and a split or merge between datasets shows as one box with curves to two.

*Caution.* The colours are the datasets', not the Workbench's Cluster colours.

*Example.* In Overall × RPG, Overall C1 has curves to RPG C5 (0.25) and RPG C2 (0.14).

### Minimum similarity and flags

> **In short.** The Minimum Match Jaccard hides weaker matches, and a badge marks each Cluster with no match at or above it.
>
> **Here:** keeps one-Tag overlaps from crowding the diagram.
>
> **Caution:** a view choice: it changes neither the `comparison_id` nor the export.

The **Minimum Match Jaccard** slider (short "Minimum Jaccard") starts at 0.10; **show weaker** draws the hidden matches dashed. Each Multi-Tag Cluster with no match on show carries one badge: "No match: outside Overall's network" (none of its Tags is a Comparable Tag), "No match: only One-Tag Clusters in Overall" (its Comparable Tags are each a One-Tag Cluster there; the tooltip counts them) or "No match above 0.10" (it has matches, all weaker). See [No-match flags](03-metric-reference.md#no-match-flags).

*Why it matters here.* On the full Build 58 of the 103 matches share a single Tag; the minimum 0.10 hides 51 of them.

*Caution.* A Cluster whose Tags are spread one each over several Clusters falls under "No match above".

*Example.* At 0.10, Overall C4 carries "No match above 0.10" against Puzzle (its best match is 0.07), and Puzzle C4 "No match: outside Overall's network".

### Match detail

> **In short.** One Cluster Match: its figures, its shared Tags, each Cluster's other Tags with where they sit, and the games in both Clusters.
>
> **Here:** says why two Clusters match and where the rest of their Tags went.
>
> **Caution:** Overlap vs. expected is descriptive: no p-value.

It names the two Clusters ("Overall C3 ~ Puzzle C1") and gives Match Jaccard, Shared % of A, Shared % of B and Jaccard (comparable) with the Comparable Tag counts, then the Overlap vs. expected sentence ("3 shared Tags: 2.4× the 1.25 expected from the Cluster sizes (N = 38 Comparable Tags)"). Three Tag columns follow: **Shared**, **Only in ‹A Cluster›** and **Only in ‹B Cluster›**, each unshared Tag with its group: "in Overall C5", "One-Tag Cluster in Overall", "not in Overall's network (2 games, minimum 5)" or "hidden in Strategy (its defining Tag)", the last set aside and in no figure. Before a match is chosen the detail asks you to click a curve. The figures are defined in [Match Jaccard and Jaccard on Comparable Tags](03-metric-reference.md#match-jaccard-and-jaccard-on-comparable-tags), [Shared share](03-metric-reference.md#shared-share) and [Overlap vs. expected](03-metric-reference.md#overlap-vs-expected).

*Why it matters here.* A low Match Jaccard can come from Tags the other network does not have at all; the Tag groups and Jaccard (comparable) show how much.

*Caution.* A defining tag hidden in one dataset is set aside for the pair and listed, never counted.

*Example.* Overall C4 ~ RPG C2 has 3 shared Tags, Match Jaccard 0.38 and Jaccard (comparable) 0.50; two of RPG C2's other Tags are not in Overall's network.

### Games in both Clusters

> **In short.** The games ranked in both datasets that have Tags of both Clusters of the match, most matched first.
>
> **Here:** shows the games behind a match.
>
> **Caution:** shown, never scored: the similarity is computed on Tags only.

A game is listed when it is in both Top-N Datasets after the shared Minimum Months Filter and has at least one Tag of each Cluster, as the Cluster Inspector counts a Cluster's games. The columns are Rank in A, Rank in B, Name, Matched in A (x / |a|), Matched in B (y / |b|) and the game's Tags from either Cluster, the shared ones marked. They are sorted by Matched in A plus Matched in B, then by Rank in A and Rank in B. A count line above says "Of **N** games in both datasets: **k** in both Clusters, **x** only in A, **y** only in B, **z** in neither." The first 10 rows are shown, then **Show all N**. With no games in common the list says "These two datasets have no games in common, so no game can be in both Clusters."; with games in common but none in both Clusters, "None of the **N** games in both datasets is in both Clusters."

*Why it matters here.* Two Top-N Datasets mostly hold different games, so a match rests on Tags, and the games in both show what it looks like in practice.

*Caution.* Puzzle has at most two games in common with any other dataset of the full Build, so its lists are nearly always empty.

*Example.* Strategy C2 ~ Simulation C1: of 48 games in both datasets, 42 are in both Clusters, 0 only in Strategy, 5 only in Simulation and 1 in neither.

### Export CSV

> **In short.** Download every dataset pair of this comparison, whatever is on screen, as six CSV tables and `comparison.json` in one zip named with the `comparison_id`.
>
> **Here:** the record of a comparison, for a paper's supplement.
>
> **Caution:** Record only: it cannot be reopened. Disabled while a dataset is still being computed.

Download every dataset pair of this comparison, whatever is on screen, as six CSV tables and `comparison.json` in one zip named with the `comparison_id`. Record only: it cannot be reopened. Disabled while a dataset is still being computed. The zip holds every Cluster Match regardless of the minimum, with A always the earlier dataset in the Build's order. [Cite a Cluster Comparison](05-citing-and-reproducing.md#cite-a-cluster-comparison) says how to quote it.

*Why it matters here.* Readers can recheck every figure, and apply any minimum of their own, from the tables.

*Caution.* Each dataset is rebuilt from its own record: its `state_id` when set by hand or with no run, or its run's settings key and Threshold Pair.

*Example.* With all five datasets on their picks the zip is named `steamstudy_cluster-comparison_7789f0b5d412_<UTC timestamp>.zip` and holds 10 pairs and 103 matches.
