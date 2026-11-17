# Steam Success Study

Identifies recurring characteristics (tags, tag combinations, design patterns) of highly successful commercial Steam games, as a basis for later comparison with educational/STEM games.

## Language

**Mean Monthly Players**:
A game's success score: the mean of its monthly "Avg. Players" values (Steam Charts) over the post-release months that have data, within the **Observation Window**.
_Avoid_: average players, popularity, success (unqualified)

**Monthly Avg. Players**:
Steam Charts' per-month figure: the mean concurrent player count across that month. Distinct from monthly Peak Players.
_Avoid_: monthly players, MAU

**Observation Window**:
The latest complete 60 calendar months before the **Snapshot**'s collection date (e.g. Oct 2021 – Sep 2026 for a Snapshot started in Oct 2026). Months that end after the collection date are never part of it, even if a page fetched later shows them.

**Missing Month**:
A month inside the **Observation Window**, after release, with no Steam Charts value (no row, or only a **Placeholder Row**). Stays missing; never counted as zero. A gap means Steam Charts did not track the game that month, not that nobody played.
_Avoid_: zero month

**Placeholder Row**:
A Steam Charts month row with Avg. Players 0.00 and Peak Players 0, wherever it appears in a game's history. It is not data: it is treated as if the row were absent, so its month is never a zero and never a **Release Month**.
_Avoid_: zero month, empty month

**Release Month**:
The first month with a Steam Charts row that is not a **Placeholder Row**. Months before it are never part of the average. Small nonzero months before a game's launch still count as data.
_Avoid_: launch date, store release date (stored only as metadata)

**Months Observed**:
The number of post-release months inside the **Observation Window** that have a **Monthly Avg. Players** value. Reported for every game; no minimum is applied when ranking.

**Tag**:
A user-defined Steam tag. A game **has** a tag if the tag is within its **Tag Depth**: among the first K tags of its displayed store list (Steam displays at most 20), whatever the votes. **Exclusions** and **Content Flags** read the whole displayed list instead.

**Tag Depth**:
How many leading tags of each game's displayed list count; a game **has** only the tags within it. One value per **Build**. For Steam 2 to 20, where 20 (the default) means all; for an **Import** any number from 2, or all (the default). Called "tags per game" in the app and the User Guide.

**Genre**:
A value of the Steam store's developer-assigned genre field (e.g. Action, RPG, Strategy). Distinct from a **Tag** with the same name.
_Avoid_: genre tag (when meaning the store field)

**Genre Tag**:
A **Tag** listed in the configurable genre-tag list; can be hidden from the **Tag Network** (never from datasets).

**Tag Network**:
Weighted undirected graph built from one loaded **Top-N Dataset**: nodes are **Tags**, edge weight is the number of games having both tags, each edge keeps its AppIDs. The edge weight is always this shared-game count, whatever the **Clustering Weight**.

**Clustering Weight**:
The per-edge value that community detection runs on. Either the shared-game count (the default, which is the edge weight itself) or the edge's **Lift** (an optional mode). Choosing it never changes the edge weight (the shared-game count that is thresholded and inspected); edge thickness follows the Clustering Weight.
_Avoid_: edge weight (when meaning the lift mode), normalised weight

**Cluster**:
A group of **Tags** that community detection puts together in one **Tag Network** state. Labelled `C1…` by size, never given a semantic name. A **Multi-Tag Cluster** has two or more tags.
_Avoid_: community (except when citing methods literature), theme, category

**One-Tag Cluster**:
A **Cluster** with a single **Tag**: usually an isolated tag (it reaches the minimum games per tag but no edge reaches the minimum shared games), rarely a connected tag the algorithm left on its own. Stays in the network, but is counted apart from **Multi-Tag Clusters** and never enters a cluster-quality average as a cluster of its own.
_Avoid_: singleton, unclustered tag, noise

**Connection Ratio**:
For two **Clusters**: the link weight between them divided by the weight their total link weight alone would predict, in the **Clustering Weight**. 1 = as predicted; it never exceeds the resolution γ, because a pair above γ would have been merged into one **Cluster**. It describes how the clustering split the tags, not independent evidence about the games.
_Avoid_: connection strength (a tag's strength is its summed link weight), affinity, association strength, Lift, density

**Connection Share**:
Of all the link weight leaving a **Cluster**, the part that goes to one other **Cluster**. A Cluster's shares add up to 1. Big Clusters take large shares just by being big; the **Connection Ratio** judges strength.
_Avoid_: connection strength, proportion of cut

**Cluster Center**:
The member of a **Multi-Tag Cluster** of three or more **Tags** whose games overlap most with the other members' games (the smallest mean Jaccard distance between game sets). It marks the cluster's most typical **Tag**, not its most frequent or most important one. A **One-Tag Cluster** or a two-tag cluster has none.
_Avoid_: hub, leader, representative tag, core tag

**Removal Sensitivity**:
How much the **Tag Network**'s clustering changes when one **Tag** is hypothetically removed: once with the network reclustered, once with every other tag kept in its **Cluster**. A what-if measure: it never removes the tag from the network the user is looking at. Read against the **Seed-Noise Floor**; describes dependence of the clustering on a tag, never a tag's importance or effect.
_Avoid_: node sensitivity, influence, importance

**Seed-Noise Floor**:
How much the clustering varies across random seeds on the unchanged **Tag Network**: each extra seed's **Clusters** compared with the ones shown. Part of every **Network State**'s result, not only of a **Removal Sensitivity** run. A **Removal Sensitivity** smaller than this cannot be told apart from seed noise.
_Avoid_: error bar, confidence interval, seed stability

**Membership Stability**:
How consistently one **Tag** is put with the same other **Tags** across the seeds of the **Seed-Noise Floor**: 1 means its **Cluster** never changes. A **Cluster** has the mean over its members. Describes how much a tag's assignment depends on the seed, never whether a tag or **Cluster** is real or important.
_Avoid_: confidence, certainty, robustness, core-ness

**Resolution Sweep**:
The feature-analysis report's clustering repeated at a fixed set of resolution values, everything else unchanged, and compared with the reported **Clusters**. Shows how much the result depends on the chosen resolution. Part of the **Build** only, not of the app.
_Avoid_: γ stability test, robustness check

**Threshold Pair**:
One combination of minimum games per tag (g) and minimum shared games (s), with every other **Network State** setting held fixed. Edges are kept by count alone (shared games ≥ s), so a Threshold Pair's edges carry no claim of statistical significance.
_Avoid_: configuration, cell (except when talking about the heatmap), parameter set

**Parameter Grid**:
Every **Threshold Pair** searched for one **Top-N Dataset**: g and s each over a range set per Build (by default g from 3 to 20 and s from 2 to 12), with s ≤ g. The ranges count games, the same for every dataset of the Build whatever its size.
_Avoid_: multiverse (except when citing Steegen et al.), search space

**Automatic Parameter Selection**:
The procedure that picks one **Threshold Pair** and a resolution for a **Top-N Dataset**: for every pair in the **Parameter Grid** it chooses a **Selected Partition**, and then it picks among the **Qualifying Pairs** by **Neighbour Agreement**. A choice of settings to look at, never a claim that the resulting **Clusters** are real.
_Avoid_: optimisation, optimal parameters, auto-tuning

**Admissible Partition**:
A partition, found at some resolution in a **Threshold Pair**'s scan, that gives the highest modularity over some interval of resolutions among all partitions found there (CHAMP, Weir et al. 2017). That interval, never extended beyond the scanned resolutions, is its **Optimality Domain**.
_Avoid_: candidate partition, optimal partition (unqualified)

**Stable Partition**:
An **Admissible Partition** whose self-consistent resolution estimate (Newman 2016; Gibson & Mucha 2022) lies inside its own **Optimality Domain**. Gibson & Mucha's term: stable means self-consistent under that estimate, not reproducible across seeds or data.
_Avoid_: robust partition, consensus partition

**Selected Partition**:
The **Stable Partition** that **Automatic Parameter Selection** keeps for a **Threshold Pair**: the one with the widest **Optimality Domain** among those with at least the minimum number of **Multi-Tag Clusters** (three by default; **One-Tag Clusters** never count). A **Threshold Pair** may have none. Its **Selected Resolution** is the midpoint of that domain.
_Avoid_: best partition, final clustering

**Neighbour Agreement**:
How similar a **Threshold Pair**'s **Selected Partition** is to those of its adjacent pairs in the **Parameter Grid** (g ± 1, s ± 1), compared on the **Tags** they share that have an edge in at least one of the two networks (a tag isolated in both agrees trivially and is left out). Adjacent pairs without a **Selected Partition** are missing, never counted as disagreement, and adjacent pairs with an identical network are left out, since a step that changes nothing tests nothing. Measures parameter stability: dependence on the thresholds, not on the seed or the games. Tends to be higher at large g, where one step changes the network less (see **Edge Overlap**).
_Avoid_: grid stability, robustness, smoothness

**Edge Overlap**:
How much of the network two adjacent **Threshold Pairs** share: the Jaccard overlap of their edge sets, each tag pair counted once and weights ignored. Describes how large a step in the **Parameter Grid** is; reported next to **Neighbour Agreement**, never used to pick a pair.
_Avoid_: edge stability, graph similarity

**Subsample Stability**:
How well a **Selected Partition** is recovered when the network is rebuilt and reclustered from random 80% subsets of the games, with the thresholds scaled to match: re-selected by the same per-pair procedure, and also read at the original **Selected Resolution**. Measures data stability: dependence on which games are in the dataset, not on the seed or the thresholds.
_Avoid_: bootstrap confidence, robustness (unqualified)

**Hennig's Jaccard**:
How well one **Multi-Tag Cluster** is recovered in one subsample of **Subsample Stability**, judged only on its **Tags** that survive in the subsample: the best overlap with any subsample **Cluster**, on those tags. It needs at least two surviving tags. With fewer, the subsample cannot judge the Cluster. Losing tags does not lower it; see **Whole-Cluster Jaccard**.
_Avoid_: stability score, bootstrap Jaccard

**Whole-Cluster Jaccard**:
The counterpart of **Hennig's Jaccard** that counts lost tags as not recovered: the best overlap of the whole **Multi-Tag Cluster** with any subsample **Cluster**. It is never higher than Hennig's Jaccard, and the two are equal when no tag is lost. It is 0 when no tag survives.
_Avoid_: recovery Jaccard, full Jaccard

**Dissolved in most subsamples**:
A **Multi-Tag Cluster** whose **Hennig's Jaccard** is 0.5 or less in more than half of the subsamples that can judge it. The 0.5 cut for one subsample is Hennig's; the majority over subsamples is this study's rule. It says the Cluster depends on which games are in the dataset, not that it is wrong.
_Avoid_: dissolved (mean ≤ 0.5), unstable cluster

**Null Comparison**:
The **Selected Partition**'s structure compared with networks rebuilt, at the same **Threshold Pair**, from game–tag tables shuffled so that every game keeps its tag count and every **Tag** its game count, each put through the per-pair procedure at that **Threshold Pair** (its own γ scan and **Selected Partition** rule), not the **Parameter Grid** or the choice of pair. Shows only that the network is not random, never that its **Clusters** are real.
_Avoid_: significance test, p-value, validation (unqualified)

**Q not above the null**:
The **Null Comparison**'s verdict when at least one of its shuffled networks that has a Q reaches the observed Q at the **Selected Resolution**. Says Q gives no evidence of structure beyond the tag and game counts, not that the **Clusters** are random.
_Avoid_: not significant, p > 0.05

**Perturbation Share**:
For one shuffled network of the **Null Comparison**, the share of the observed game–tag assignments that the shuffle moved. It shows how far the shuffle got from the observed data. It is a diagnostic, never part of a verdict.
_Avoid_: mixing score, randomness

**Information Retention**:
The share of the visible **Tags**' game–tag assignments (hidden and removed tags never count) that belong to **Tags** with at least one edge in the **Tag Network** of a **Threshold Pair**, counted over the games left after the **Minimum Months Filter**. Describes how much of the data the network still represents.
_Avoid_: coverage (that is the partition metric), data loss

**Fragmentation**:
How broken up a **Threshold Pair**'s **Tag Network** is: the number and share of isolated **Tags**, the size of the largest connected component (as a share of the **Tags** that have an edge, so it never double-counts isolation), and the number of **Clusters**.
_Avoid_: sparsity, connectivity (unqualified)

**Pair Constraint**:
A rule a **Threshold Pair** must meet before **Automatic Parameter Selection** may pick it: a minimum **Information Retention**, a maximum share of isolated **Tags**, a minimum largest-connected-component share, a minimum number of adjacent pairs it is compared with, or a maximum number of **Multi-Tag Clusters**. Each has a documented default the user can change. A guard against unusable networks, not an objective.
_Avoid_: eligibility criterion, filter (unqualified)

**Selection Settings**:
The choices that fix every **Threshold Pair**'s **Selected Partition** before any pair is picked: the hidden and removed **Tags**, the **Minimum Months Filter**, the Clustering Weight, the algorithm and the minimum number of **Multi-Tag Clusters**. Changing one needs a new run; changing a **Pair Constraint** does not.
_Avoid_: fixed settings, configuration, parameters (unqualified)

**Qualifying Pair**:
A **Threshold Pair** that has a **Selected Partition** and a **Neighbour Agreement** and meets every **Pair Constraint**. **Automatic Parameter Selection** picks only among Qualifying Pairs.
_Avoid_: eligible pair (that word belongs to the **Eligible Pool**), valid pair, admissible pair

**Cluster Comparison**:
The **Tag Network** app's mode that matches the **Multi-Tag Clusters** of the **Top-N Datasets** of one **Build**, two datasets at a time. Each dataset shows its own partition, on its **Selected Partition** or clustered once at values set by hand; similarity is computed on **Tag** sets only, and games are shown, never scored.
_Avoid_: cluster tracking, cross-dataset clustering

**Cluster Match**:
Two **Multi-Tag Clusters**, one from each of two datasets, that share at least one **Tag**. One **Cluster** can have several. It says that two **Clusters**, each found at its dataset's settings, share **Tags**; never that they are the same group, that the **Clusters** are real or that the datasets share a genre structure.
_Avoid_: correspondence, same cluster, shared cluster

**Comparable Tags**:
The **Tags** in both networks of a dataset pair: visible and reaching the minimum games per tag in each (**One-Tag Clusters** count). The only **Tags** the **Cluster Comparison** can judge a **Cluster** on; a **Tag** hidden in only one of the two datasets (its defining tag) is set aside for that pair.
_Avoid_: common Tags, surviving Tags

**Match Jaccard**:
The shared **Tags** of a **Cluster Match** as a share of all **Tags** in either **Cluster** (set-aside **Tags** excluded). A **Tag** missing from the other network counts against it. Ranks the matches and takes the Minimum Match Jaccard.
_Avoid_: Whole-Cluster Jaccard (that name belongs to **Subsample Stability**), similarity (unqualified)

**Comparison State**:
Everything that fixes one **Cluster Comparison** result: the **Build**, the shared settings (Clustering Weight, algorithm, **Minimum Months Filter**, hidden Genre Tags, removed **Tags**) and, for each included dataset, its **Threshold Pair** and **Selected Resolution** on a run's cell, or its thresholds, resolution and seed when set by hand or with no run. Named by its `comparison_id`. The Minimum Match Jaccard, the chosen pair and match and which dataset is on the left are view choices, not part of it.
_Avoid_: comparison (unqualified), session, view

**Lift**:
For two tags: how often they share games, divided by how often they would if tags were assigned independently (observed ÷ expected co-occurrence), counted over the games the network is built from (the loaded **Top-N Dataset** after the **Minimum Months Filter**). Above 1 = they occur together more than chance would predict. A frequency-corrected measure of association, not a cause.
_Avoid_: association strength (use only when citing van Eck & Waltman), affinity

**Minimum Months Filter**:
A **Tag Network** control that drops games whose **Months Observed** is below the threshold from the loaded dataset before the network is built. It never re-ranks or backfills.

**Network State**:
Everything that fixes one **Tag Network** result: the loaded **Top-N Dataset** and its **Build**, the **Minimum Months Filter**, the minimum games per tag and minimum shared games, the hidden and removed **Tags**, the **Clustering Weight**, the clustering algorithm, the resolution, the seed, the number of null-model replicates and the number of noise seeds. The same Network State always gives the same **Clusters** and metrics. The graph layout is not part of it.
_Avoid_: view, session, configuration, state (unqualified)

**Interface Language**:
The language (English or Bulgarian) in which the **Tag Network** app's text and the User Guide are shown. A view choice: never part of a **Network State**, an export or any number. The Bulgarian form of every term here is in [docs/i18n/bg-terms.md](docs/i18n/bg-terms.md).
_Avoid_: locale, translation mode

**Edge Appearance**:
How the **Tag Network** app draws its links: their thickness range and scaling, colour, strength, and which weak links are hidden from the drawing. A view choice: never part of a **Network State**, an export or any number. Hiding a link only stops drawing it; which links exist is decided by the minimum shared games.
_Avoid_: edge style, edge filter

**Analysis Report mode**:
The **Tag Network** app's second mode: one scrolling page of numbered sections over the same state as the graph workbench. Distinct from the generated feature-analysis report.
_Avoid_: report (unqualified)

**App Bundle**:
A self-contained folder, made from the repository, that lets a researcher run the **Tag Network** app on another computer with only Python installed and no internet access: the app, the User Guide, the **Builds** it opens and every library the app needs, at the exact versions the **Builds** were made with. It never collects or builds; it only opens the **Builds** it carries. The pipeline itself is not part of it.
_Avoid_: visualization tool, standalone app, portable version, offline bundle

**Free-to-Play Game**:
Included in all datasets; flagged with `is_free`.

**Candidate Pool**:
Every app in the full Steam Charts "Top Games" listing at collection time, with no cutoff by current players. Its size is reported, not enforced. Apps without a **Monthly Avg. Players** value in the **Observation Window** have no score and so never reach a **Top-N Dataset**; this is not an **Exclusion**.
_Avoid_: scraped games

**Eligible Pool**:
The scored, non-excluded games (every non-excluded item, for an **Import**) a **Top-N Dataset** is drawn from: all of them for Overall, those that **have** the defining tag for a **Tag-Specific Dataset**. Serves as the baseline that the dataset's tag frequencies are compared against.
_Avoid_: population, all games, Steam

**Top-N Dataset**:
One of a **Build**'s ranked lists, Overall or a **Tag-Specific Dataset**, of the N non-excluded games with the highest score, N being the dataset's **List Size**. The score is **Mean Monthly Players** in a Steam Build; in an Import Build it is the Import's score, or the file order when the Import has none. A game may appear in several.
_Avoid_: Top-100 Dataset, top list

**List Size**:
The N of a **Top-N Dataset**: how many games it holds. Set per dataset, 100 by default. A dataset whose **Eligible Pool** holds fewer games than its List Size cannot be built.
_Avoid_: top count, cutoff, list length

**Exclusion**:
Removal of a game from all **Top-N Datasets** because it matches an **Exclusion Rule**, recorded with every rule it matches (not only the first); the first in order is its primary reason. Rank limits count positions in the whole displayed list, whatever the **Tag Depth**.

**Exclusion Rule**:
A ground for **Exclusion**. *Fixed rules*, the same in every Build: non-`game` Steam app type; store data unavailable (no tags/metadata obtainable from the Steam store, e.g. delisted, region-locked or login-only apps, and no **Manual Metadata Entry** supplied); no tags (the store page exists but displays no tags), all three checked first; and manual (a game the researcher lists individually, with a written reason and evidence), checked last. *Named rules*, set per Build and checked in order between them: a list of tags, each counting only within its rank limit, plus for Steam content descriptors and the "Adult Only" notice. The default named rules are adult sexual content (games whose content is mainly sexual, identified by Steam's own "Adult Only" marking or the Hentai tag; not mainstream games with some nudity or sex scenes), software tags, and dating sims (games that are mainly dating sims, not games with a dating side-system such as Stardew Valley). Maturity tags (Mature, Gore, Violent, etc.), Romance, Otome and the Education tag are not grounds in the default rules. A Build may have no named rules.
_Avoid_: filter, blacklist

**Exclusion Override**:
A researcher decision, with a written reason and evidence, that a specific game is not excluded by a specific named, app-type or no-tags **Exclusion Rule** it matches (e.g. a farming sim whose Dating Sim tag ranks high). Published alongside the datasets.
_Avoid_: whitelist, manual inclusion

**Content Flag**:
A per-game marker for a characteristic worth reporting but not an **Exclusion** ground (e.g. Desktop Companion apps, whose always-on use inflates concurrent player counts): a named tag list, matched anywhere in the displayed tags.
_Avoid_: soft exclusion, warning

**Tag-Specific Dataset**:
A **Top-N Dataset** restricted to games that **have** the exact tag (e.g. Puzzle, RPG); sub-genre tags (e.g. RTS, 4X) do not qualify.

**Source Substitution**:
Use of a public data source other than the named ones (Steam Charts, SteamDB). Only permitted after explicit confirmation by the researcher. Confirmed: the Steam store (store page tags and app details).

**Manual Metadata Entry**:
Tags and store details supplied by the researcher for a game the Steam store cannot provide, each field citing its source and retrieval date. Two kinds: a full entry for a game with no store data, and a tags-only entry for a game whose store page shows no tags (its other details still come from the store). Never allowed for a game the store does provide (a Build with such an entry fails). Counts as the researcher's confirmation of that source for that game; the game is then treated like any other and flagged as manually sourced.
_Avoid_: manual override, hand-filled data

**Snapshot**:
Everything collected in one collection: every raw response from Steam Charts and the Steam store, with a fixed collection date (the day collection starts). Fixes the **Observation Window**. Either a test Snapshot (a small subset) or a full Snapshot. Never changed after collection ends, except by a logged repair. Comes in two forms sharing one id: the raw form (every raw response, as collected) and, once collection has ended, a **Lightweight Snapshot**. Only the raw form can be repaired.
_Avoid_: run, scrape, crawl

**Lightweight Snapshot**:
The form of a **Snapshot** that holds only what a **Build** reads from it, as tables: the listing, every app's monthly player counts, the store fields and tags of every scored app, and the outcome of every lookup. Made from the raw form of a Snapshot after collection ends, and made again after a repair; never changed itself. A Build from it is identical to a Build from the raw form with the same settings, so it is both the form that moves between machines and the faster one to build from. Fixes the parsing in force when it was made.
_Avoid_: snapshot extract, export, light copy

**Import**:
A fixed set of items, each with an ordered list of attributes, supplied by the researcher as a file instead of collected from Steam. Plays the **Snapshot**'s role for the Builds made from it: raw, identified once, never changed afterwards; a corrected file is a new Import. One Import can define several **Top-N Datasets**, one per defining attribute. In the app's Steam wording, an item is a Game and an attribute is a Tag.
_Avoid_: imported dataset, upload, external dataset

**Build**:
One deterministic derivation from one **Snapshot** (a Steam Build) or one **Import** (an Import Build) and one config version: its **Top-N Datasets**, their reports and the feature analysis. An Import Build has only the reports and analysis that do not depend on Steam. Never contacts a source. A Snapshot can have many Builds (e.g. before and after an exclusion-list change), even two with the same settings. Never changed once written: its id, name and description are fixed then. The name is unique among the Snapshot's Builds and **Build Drafts**; the description says why the Build exists and joins the config changelog. A Build started from another Build records it as its parent, for information only; deleting a Build leaves its children as they are. A run that fails is not a Build.
_Avoid_: run, analysis run

**Build Draft**:
The complete settings of a **Build** not yet made, with the name and description it will carry, kept for one **Snapshot** until it is built or discarded. Started from the default config or copied from an existing Build, then edited; a copy, so later changes to its source do not reach it. A failed run leaves the draft, with the reason it failed.
_Avoid_: unsaved Build, pending Build, template
