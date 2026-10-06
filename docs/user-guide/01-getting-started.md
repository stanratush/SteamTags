# Getting started

## Open the app

The Tag Network app runs on your own computer and needs no internet connection. Someone who has run the pipeline starts it with

```bash
uv run steamstudy app
```

It opens the latest Build at `http://127.0.0.1:8050` in your browser (`--build <id>` picks another Build; `--port` another port). The app only reads the pipeline's own Top-100 Datasets; it never loads other files.

A yellow banner at the top warns when the Build comes from a test Snapshot (`mode: test`) or was made with parse errors allowed (`parse_errors_allowed`). Never publish numbers from such a Build.

## Load a dataset

Pick one of the five Top-100 Datasets in the **Dataset** selector: Overall, Puzzle, RPG, Strategy or Simulation. The app builds the Tag Network of that dataset at the shared defaults (the same settings the feature-analysis report uses) and clusters it. Every control change recomputes the whole Network State: network, clusters, null model, Seed-Noise Floor and all metrics. At loose thresholds a change can take several seconds.

The line under the graph is the Cluster-quality row, for example

> Q (γ = 1.00) 0.42 vs null 0.31 ± 0.01 (excess 0.11, z 11; null networks average 640 edges vs 702) · coverage 0.81 · 5 multi-tag + 3 one-tag · silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion 0.21

and the line below it is the Seed-Noise Floor:

> Seed-noise floor (K = 10): ARI vs. main min 0.84, mean 0.93 · multi-tag clusters 5–7 · SD Q 0.004 · SD silhouette 0.01

Each number is explained in the [metric reference](03-metric-reference.md). The `?` button on each panel opens the matching guide section inside the app, and hovering over a column header shows its one-line description.

## The two modes

The **Mode** control at the top switches between two views of the same Network State. Settings, removed tags and results carry over when you switch.

- **Workbench**: controls on the left, the graph in the centre with a cluster legend and the Global / Cluster-separated layout switch, the inspector on the right, and tabbed tables below (Cluster quality, Clusters, Removal sensitivity, Nodes, Edges, Not in network). Controls, Inspector and Tables collapse independently; **Graph only** switches to the narrowest form, with the controls as a pill bar, a floating inspector and the tables as a bottom sheet (see [Window width and the three forms](02-app-controls.md#window-width-and-the-three-forms)).
- **Analysis Report mode**: one scrolling page of numbered sections over the same state: 1 Dataset · 2 Filters (every tag left out of the network, with its reasons) · 3 Network and inspector · 4 Cluster quality · 5 Removal sensitivity · 6 All nodes and edges · 7 Export. It is meant for reading one Network State top to bottom. It is not the generated feature-analysis report (`report.html`), which the Build writes.

## Inspect a node, an edge or a cluster

Click a node to see its metrics, an edge to see the games that have both tags, or a cluster (its legend button, its row in the Clusters table, or its region title in the Cluster-separated layout) to see its members ranked by how typical they are; the graph also zooms to that cluster (⤢ fits the whole graph again).

The labels you can always read are the Cluster Centers, the 15 tags on the most games and, in the Cluster-separated layout, each cluster's largest tag, plus whatever you have selected and its neighbours. They keep the same size at any zoom; where two would overlap, the less important one is hidden until you zoom in. Every other label grows as you zoom in and appears once it is large enough to read. With the inspector collapsed, or in a window narrower than 1280 px, a click opens it as a floating card over the right of the graph; close it with ×.

From a node's inspector you can **Remove** the tag (a what-if: the source dataset never changes) or start **Run for this tag** (its Removal Sensitivity).
