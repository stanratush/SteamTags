# Games within a Cluster
Type: grilling
Status: open
Blocked by: none

## Question

What exactly does the games list for a Cluster show? Uses `grilling` + `domain-modeling`.

- The game set: games in the Network State (after the Minimum Months Filter, as `view.tag_games`) that have at least one of the Cluster's Tags. Only visible member Tags count, never hidden or removed ones.
- Ranking: by the number of matching Cluster Tags, then which tie-break (Mean Monthly Players rank, name).
- Columns: matched Tags, matched count, % of the Cluster's Tags (matched / cluster size), and possibly the game's rank and AppID. For a large Cluster, is the matched-tags list shown in full or truncated?
- One-Tag Clusters: the list is then the tag's own games at 100%. Is that shown, or does it point to the tag inspector?
- Placement: a section of the Cluster Inspector, or a tab. List length (all games, possibly 100) against the Inspector's HTML-table performance note in `view.py`.
- Is it exported (fog on the map: exports for features 3 and 4)?
