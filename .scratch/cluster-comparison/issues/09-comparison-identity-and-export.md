# What fixes one comparison, and what does its export hold?
Type: grilling
Status:
Blocked by: 03, 04, 10

## Question

A **Network State** fixes one Tag Network result and can be exported and reopened. A comparison is made of several.

Decide:
- what fixes one comparison result: the included datasets, each one's g, s and resolution, the shared settings, and whether the minimum similarity is part of it or a view choice;
- whether it gets a name in the glossary and an id, as a Network State has a `state_id`;
- the export: which files and columns (one row per Cluster Match with both Clusters' Tags, the shared and unique Tags, the percentages and the measures; one row per unmatched Cluster with its flag; the settings), following the export schema conventions in `src/steamstudy/export/schema.py`;
- whether an exported comparison can be reopened, like Open Network State, or is a record only;
- whether the export holds every pair of included datasets or only the pair on screen.
