# Cross-dataset comparison
Type: grilling
Status: resolved
Blocked by: none

## Question

Does the Parameter Selection mode need any comparison between the five Top-100 Datasets beyond the dataset strip (each dataset's chosen pair and Neighbour Agreement; [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md))? If so, what exactly?

- Candidates: one Threshold Pair shown across all five datasets (g = 14, s = 2 qualifies in every dataset on this Build), agreement between datasets' Selected Partitions on shared tags, or nothing beyond the strip.
- If anything is added: where it sits in the three-pane layout, whether it enters the exports ([Exports and documentation](11-exports-and-documentation.md)), and whether it claims anything the method doesn't support (datasets have different tag sets and sizes).
- Re-measured picks to work from: overall 17,2 · puzzle 14,2 · rpg 7,5 · simulation 14,5 · strategy 14,2 ([Graph-specific γ scan](16-graph-specific-gamma-scan.md)).

Graduated from the map's Not yet specified on 2026-10-27, when it was the last patch of fog and the frontier was otherwise empty.

## Answer

Decided by the researcher, 2026-10-27, accepting all six recommendations of one grilling round. **No cross-dataset comparison beyond the dataset strip.**

- **The strip is the whole comparison.** Each dataset is selected on its own, from its own games, tags and graph, and the method claims nothing about how datasets relate. The strip stays as [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md) fixed it: ★ pair, Neighbour Agreement, the "custom" marker or the dataset's status, one click per dataset.
- **No "same pair in every dataset" view.** Two clicks (the dataset on the strip, then the cell) already show any pair in another dataset. Choosing *one* Threshold Pair for all datasets would be a different selection rule (for example, the highest minimum NA), not a view. It belongs to the later Build-adoption effort and is ruled out of scope on the map.
- **No agreement score between datasets' Selected Partitions.** ARI or Hennig's Jaccard between two datasets' Selected Partitions measures how the Cluster structure of different game populations differs. In this mode it would read as a fifth kind of stability next to the three kinds and the Null Comparison, and low agreement is the expected result, so it could not be read either way. Comparing datasets' Cluster structure is a study question for the feature-analysis report and is ruled out of scope on the map.
- **Switching dataset resets the heatmap and Pair Inspector to that dataset's ★ pair.** The metric picker keeps its choice, so the same metric can be compared across datasets' heatmaps. Before the grid is complete (no ★), the Inspector is empty, as in an unfinished grid.
- **One pinned sentence against reading the strip as disagreement.** A new help key `selection.dataset_strip` and the ch. 3 overview of the User Guide carry, pinned by a test like the other new phrases ([Exports and documentation](11-exports-and-documentation.md)): *"Each dataset is selected on its own, from its own games and tags. Different pairs in different datasets are expected and are not a disagreement: the same pair builds networks of different sizes in different datasets."* The rpg-specific explanation stays in that dataset's "Why this pair" ([Does Neighbour Agreement favour high g?](12-neighbour-agreement-high-g-bias.md)).
- **Exports unchanged.** No cross-dataset table and no cross-dataset field in `parameter_selection.json`. The seven tables are already stacked by `dataset`, so any comparison can be made offline.

## Comments

- 2026-10-27: Resolved in one grilling round. All six recommendations were accepted. No glossary term changed. This was the last ticket: the map's frontier and fog are now empty.
