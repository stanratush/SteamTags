# What are "the games in both Clusters" of a match?
Type: grilling
Status: resolved
Blocked by:

## Question

Charted: similarity is on Tag sets only, but for a match the view may show the games that are in both Clusters, as the app shows games today. Today the inspector lists the games that have a given Tag (`tag_games` in `src/steamstudy/app/view.py`); the two datasets of a match mostly hold different games.

Decide:
- what makes a game belong to a Cluster: it has any Tag of the Cluster, a minimum number of them, or a share of them;
- what "in both" means across two datasets: the game is in both Top-N Datasets and belongs to both Clusters, or belongs to both Clusters by its Tags wherever it is ranked;
- which Tags count for belonging: all the Cluster's Tags or only the shared ones;
- what is shown beside the list: the game's rank in each dataset, a count, the games in only one of the two Clusters;
- what the view says when the two datasets share no games at all, so the list is empty for a reason unrelated to the Clusters.

## Answer

Decided with the researcher in two grilling rounds, 2026-11-17. Names are working names. Nothing here enters CONTEXT.md: **games in both Clusters** and **games in common** are display phrases, not glossary terms.

**What the list is**

- A game is in **games in both Clusters** of a match of Cluster A (dataset A) and Cluster B (dataset B) when it is in **both Top-N Datasets** after the shared Minimum Months Filter, has **at least one Tag of Cluster A** as counted in dataset A's Network State, and has **at least one Tag of Cluster B** as counted in dataset B's. A game in only one of the two datasets is never judged against the other dataset's Cluster, because a Cluster exists only inside its own dataset's network.
- Belonging is the Cluster Inspector's rule (`cluster_games` in `src/steamstudy/network/tables.py`: at least one of the Cluster's Tags, counting only Tags in that Tag Network). No minimum number or share is added, so a Cluster has one game list everywhere in the app. A weak belonging shows in the matched counts and the sort order.
- **All** of each Cluster's Tags count, not only the match's shared Tags. If only the shared Tags counted, the test would be the same in both datasets and would say nothing about either Cluster as a whole.
- It is always called **games in both Clusters** (heading, export, guide), never "shared games". The glossary already uses "shared games" for an edge (the games having both Tags; "minimum shared games").
- It is display only, never part of a similarity. This is unchanged from charting.

**What is shown**

- Columns: **Rank in A · Rank in B · Name · Matched in A (x / a) · Matched in B (y / b) · Tags**. Tags lists the game's Tags from either Cluster, with the match's shared Tags marked. The Inspector's "of its tags" share is dropped: its denominator, the game's network Tags, differs between the two networks.
- Sort: Matched in A + Matched in B, descending, then Rank in A, then Rank in B. A is the left dataset of the pair as the view shows it.
- A count line above the list: "Of **N** games in both datasets: **k** in both Clusters, **x** only in A, **y** only in B, **z** in neither." The three other groups are counted, never listed: listing them would turn the view into a game comparison, which is out of scope.
- Length: the Inspector's pattern, the first `GAMES_SHOWN` rows, then "Show all N".

**When the list is empty**, the view says which of two reasons applies:

- No games in common: "These two datasets have no games in common, so no game can be in both Clusters." This is a property of the pair, not of the Clusters.
- Games in common, but none in both Clusters: "None of the **N** games in both datasets is in both Clusters."
- The pair overview shows the number of **games in common** beside the Common Tags count. This adds to the overview set by [Which measures survive on the real Builds?](04-measures-on-real-builds.md).

**Context** (full Build `20261008T221504Z-7a23ae9f`, from the defining-Tag game counts in the [measures report](../prototypes/04-measures-on-real-builds/report.md)): Overall has 1 game in common with Puzzle, 38 with RPG, 24 with Strategy and 28 with Simulation. These are exact, because a game of a Tag-Specific Dataset that is in Overall's top 100 also ranks within that dataset's top 100. Between two Tag-Specific Datasets the counts are only approximate (they count games of one dataset that have the other's defining Tag): Puzzle at most 1–2 with each of the others, RPG–Strategy about 21, RPG–Simulation about 15, Strategy–Simulation about 48. So for every Puzzle pair the list is almost always empty for the first reason.

**Handed on**

- [What does the Cluster Comparison mode look like?](06-look-of-the-mode.md): where the list sits in a match's detail, and the games-in-common count in the pair overview.
- [What fixes one comparison, and what does its export hold?](09-comparison-identity-and-export.md): whether the export carries games in both Clusters (a file like `cluster_games.csv`, one row per match × game) or only the counts.
