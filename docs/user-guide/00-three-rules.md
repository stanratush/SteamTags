# Three rules

Three rules hold for every number in this study. Read them before anything else.

## No number shows a cause

A tag that is common among the most-played games, or two tags that occur together more often than chance, are not shown to *make* games successful. The Top 100 is a ranked selection, not a random sample, and nothing in the study compares top games with games that rank low. Frequencies, co-occurrences, associations and clusters describe what the top games have in common. They do not explain why those games are popular.

## Clusters carry no meaning

The app and the reports label clusters `C1`, `C2`, … by size. The software never names a cluster, and a reader should not name one either as if the name were a finding. A cluster is the output of one community-detection run on one Network State. Different seeds, resolutions or thresholds can draw the boundaries differently (see [Stability](03-metric-reference.md#stability)).

## Quote the `state_id` with every network number

Every network number (modularity, a cluster's members, a tag's silhouette, a Removal Sensitivity row) belongs to one Network State: the loaded dataset and Build, the thresholds, the hidden and removed tags, the Clustering Weight, the algorithm, the resolution γ, the seed and the replicate counts. Change any of them and the numbers change. The `state_id` (12 hexadecimal characters) identifies the exact state. Quote it next to every network number you report, and deposit the export zip so others can reopen the state (see [Citing and reproducing a Network State](05-citing-and-reproducing.md)).
