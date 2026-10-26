# Parameter Selection mode: UI prototype (throwaway)

For [Parameter Selection mode prototype](../../issues/10-parameter-selection-mode-prototype.md). Nothing imports it.

**Question:** how should the third app mode look and behave? Three structurally different layouts of the same content, switchable with the floating bar (or ← / →):

| Variant | Shape | Cross-dataset view | Pair Constraints | Inspecting a pair | Apply | A partial grid shows |
|---|---|---|---|---|---|---|
| **A · Three panes** | Workbench-shaped: Controls column, one big heatmap, docked Pair Inspector | a strip of five dataset buttons (chosen pair, NA) | always open in the left column | right pane: metrics, CHAMP, Clusters, compact validation | top of the Inspector | computed cells fill in; no selection marks or explanation until the grid is complete |
| **B · Report page** | Analysis-Report-shaped: one scrolling page, numbered sections with a table of contents | a table, one row per dataset, with validation verdicts and Inspect | an inline section | a section: metrics beside a larger CHAMP plot, then Clusters | at the end of the pair section | nothing: each section says "appears when the grid is complete (k of 153)" |
| **C · Five side by side** | five heatmaps in a row, one metric at a time | the layout itself, plus a "g, s in every dataset" row for the inspected cell | a popover from the toolbar | a bottom sheet with tabs (Selection explained, Pair, CHAMP, Clusters, Validation) | sheet header | the five heatmaps fill in live; selection marks only on complete grids |

## Run it

```
.venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/10-parameter-selection-mode/app.py
```

Open http://127.0.0.1:8060/?variant=A (B, C). The bar's dropdown, or `&run=never` / `&run=cancelled` / `&run=cached` in the URL, sets the simulated run state. Startup takes about 10 s (it loads the Build).

## What is real

- The grid: every pair's metrics and Neighbour Agreement from [the ticket 05 run](../05-grid-run/results.md) (Build `20261008T221504Z-7a23ae9f`).
- The selection: ticket 06's Pair Constraints, near-best set and tie-break, recomputed on Confirm. It reproduces ticket 06's table for all five datasets.
- An inspected pair's CHAMP plot (every Admissible Partition's Q(γ), the envelope, γ̂, the Selected Resolution) and its Clusters, computed live by [grid_run.py](../05-grid-run/grid_run.py) (0.2–4 s on first view).
- The explanation and validation wording: ticket 06's and ticket 07's templates.

## What is not

- Run, Cancel, Continue and "Validate this pair" are simulated with a timer. Every grid finishes before any validation; a cancelled grid keeps its pairs and a cancelled validation is discarded, as decided.
- Validation numbers: the ticket 07 pilot (5 nulls, 5 subsamples) scaled to R = S = 100 for the five default pairs. Any other pair, and every per-Cluster Jaccard, uses seeded illustrative numbers. Both are labelled.
- The Workbench seed is the main seed for every pair except puzzle g=14, s=2 (scan seed 2, from ticket 09). rpg g=9, s=7 is an invented `not_reproduced` example.
- Apply only shows a banner describing what the Workbench would receive, and its provenance line.
- The header's other two modes are inert.
