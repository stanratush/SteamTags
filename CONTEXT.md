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
A user-defined Steam tag. A game **has** a tag if the tag appears anywhere in its displayed store tag list (Steam displays at most 20), regardless of rank or votes.

**Genre**:
A value of the Steam store's developer-assigned genre field (e.g. Action, RPG, Strategy). Distinct from a **Tag** with the same name.
_Avoid_: genre tag (when meaning the store field)

**Genre Tag**:
A **Tag** listed in the configurable genre-tag list; can be hidden from the **Tag Network** (never from datasets).

**Tag Network**:
Weighted undirected graph built from one loaded **Top-100 Dataset**: nodes are **Tags**, edge weight is the number of games having both tags, each edge keeps its AppIDs. The edge weight is always this shared-game count, whatever the **Clustering Weight**.

**Clustering Weight**:
The per-edge value that community detection runs on. Either the shared-game count (the default, which is the edge weight itself) or the edge's **Lift** (an optional mode). Choosing it never changes the edge weight that is shown or thresholded.
_Avoid_: edge weight (when meaning the lift mode), normalised weight

**Cluster**:
A group of **Tags** that community detection puts together in one **Tag Network** state. Labelled `C1…` by size, never given a semantic name. A **Multi-Tag Cluster** has two or more tags.
_Avoid_: community (except when citing methods literature), theme, category

**One-Tag Cluster**:
A **Cluster** with a single **Tag**: usually an isolated tag (it reaches the minimum games per tag but no edge reaches the minimum shared games), rarely a connected tag the algorithm left on its own. Stays in the network, but is counted apart from **Multi-Tag Clusters** and never enters a cluster-quality average as a cluster of its own.
_Avoid_: singleton, unclustered tag, noise

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

**Lift**:
For two tags: how often they share games, divided by how often they would if tags were assigned independently (observed ÷ expected co-occurrence), counted over the games the network is built from (the loaded **Top-100 Dataset** after the **Minimum Months Filter**). Above 1 = they occur together more than chance would predict. A frequency-corrected measure of association, not a cause.
_Avoid_: association strength (use only when citing van Eck & Waltman), affinity

**Minimum Months Filter**:
A **Tag Network** control that drops games whose **Months Observed** is below the threshold from the loaded dataset before the network is built. It never re-ranks or backfills.

**Network State**:
Everything that fixes one **Tag Network** result: the loaded **Top-100 Dataset** and its **Build**, the **Minimum Months Filter**, the minimum games per tag and minimum shared games, the hidden and removed **Tags**, the **Clustering Weight**, the clustering algorithm, the resolution, the seed, the number of null-model replicates and the number of noise seeds. The same Network State always gives the same **Clusters** and metrics. The graph layout is not part of it.
_Avoid_: view, session, configuration, state (unqualified)

**Analysis Report mode**:
The **Tag Network** app's second mode: one scrolling page of numbered sections over the same state as the graph workbench. Distinct from the generated feature-analysis report.
_Avoid_: report (unqualified)

**Free-to-Play Game**:
Included in all datasets; flagged with `is_free`.

**Candidate Pool**:
Every app in the full Steam Charts "Top Games" listing at collection time, with no cutoff by current players. Its size is reported, not enforced. Apps without a **Monthly Avg. Players** value in the **Observation Window** have no score and so never reach a **Top-100 Dataset**; this is not an **Exclusion**.
_Avoid_: top-N games, scraped games

**Eligible Pool**:
The scored, non-excluded games a **Top-100 Dataset** is drawn from: all of them for Overall, those that **have** the defining tag for a **Tag-Specific Dataset**. Serves as the baseline that Top-100 frequencies are compared against.
_Avoid_: population, all games, Steam

**Top-100 Dataset**:
One of five ranked lists (Overall, Puzzle, RPG, Strategy, Simulation) of the 100 non-excluded games with the highest **Mean Monthly Players**. A game may appear in several.

**Exclusion**:
Removal of a game from all **Top-100 Datasets** because of a configured rule, recorded with every rule it matches (not only the first). Rule kinds: non-`game` Steam app type; adult sexual content (games whose content is mainly sexual, identified by Steam's own "Adult Only" marking or the Hentai tag; not mainstream games with some nudity or sex scenes); software tags; dating sims (games that are mainly dating sims, not games with a dating side-system such as Stardew Valley); store data unavailable (no tags/metadata obtainable from the Steam store, e.g. delisted, region-locked or login-only apps, and no **Manual Metadata Entry** supplied); no tags (the store page exists but displays no tags); manual (a game the researcher lists individually, with a written reason and evidence). Maturity tags (Mature, Gore, Violent, etc.), Romance, Otome and the Education tag are not exclusion grounds.

**Exclusion Override**:
A researcher decision, with a written reason and evidence, that a specific game is not excluded by a specific rule it matches (e.g. a farming sim whose Dating Sim tag ranks high). Published alongside the datasets.
_Avoid_: whitelist, manual inclusion

**Content Flag**:
A per-game marker for a characteristic worth reporting but not an **Exclusion** ground (e.g. Desktop Companion apps, whose always-on use inflates concurrent player counts).
_Avoid_: soft exclusion, warning

**Tag-Specific Dataset**:
A **Top-100 Dataset** restricted to games that **have** the exact tag (Puzzle, RPG, Strategy, Simulation); sub-genre tags (e.g. RTS, 4X) do not qualify.

**Source Substitution**:
Use of a public data source other than the named ones (Steam Charts, SteamDB). Only permitted after explicit confirmation by the researcher. Confirmed: the Steam store (store page tags and app details).

**Manual Metadata Entry**:
Tags and store details supplied by the researcher for a game the Steam store cannot provide, each field citing its source and retrieval date. Two kinds: a full entry for a game with no store data, and a tags-only entry for a game whose store page shows no tags (its other details still come from the store). Never allowed for a game the store does provide (a Build with such an entry fails). Counts as the researcher's confirmation of that source for that game; the game is then treated like any other and flagged as manually sourced.
_Avoid_: manual override, hand-filled data

**Snapshot**:
Everything collected in one collection: every raw response from Steam Charts and the Steam store, with a fixed collection date (the day collection starts). Fixes the **Observation Window**. Either a test Snapshot (a small subset) or a full Snapshot. Never changed after collection ends, except by a logged repair.
_Avoid_: run, scrape, crawl

**Build**:
One deterministic derivation from one **Snapshot** and one config version: the five **Top-100 Datasets**, their reports and the feature analysis. Never contacts a source. A Snapshot can have many Builds (e.g. before and after an exclusion-list change).
_Avoid_: run, analysis run
