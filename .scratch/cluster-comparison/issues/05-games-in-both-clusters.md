# What are "the games in both Clusters" of a match?
Type: grilling
Status:
Blocked by:

## Question

Charted: similarity is on Tag sets only, but for a match the view may show the games that are in both Clusters, as the app shows games today. Today the inspector lists the games that have a given Tag (`tag_games` in `src/steamstudy/app/view.py`); the two datasets of a match mostly hold different games.

Decide:
- what makes a game belong to a Cluster: it has any Tag of the Cluster, a minimum number of them, or a share of them;
- what "in both" means across two datasets: the game is in both Top-N Datasets and belongs to both Clusters, or belongs to both Clusters by its Tags wherever it is ranked;
- which Tags count for belonging: all the Cluster's Tags or only the shared ones;
- what is shown beside the list: the game's rank in each dataset, a count, the games in only one of the two Clusters;
- what the view says when the two datasets share no games at all, so the list is empty for a reason unrelated to the Clusters.
