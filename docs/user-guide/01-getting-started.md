# Getting started

## Open the app

The Tag Network app runs on your own computer and needs no internet connection. You get it as an **App Bundle**: one zip that holds the app, the libraries it needs, this User Guide and one or more Builds. You only need Python 3.12, 3.13 or 3.14 (but not 3.14.1) from [python.org](https://www.python.org/downloads/). A bundle is made for Windows (x64), macOS (Apple silicon) or Linux (x86_64); its `READ ME FIRST.txt` says which.

1. **Extract the whole zip** to a folder on your own disk. The app refuses to start from inside the zip, or from a read-only folder (a network share, a CD): copy the folder to your own disk first.
2. **Start it.** Windows: double-click `Start Tag Network.bat`. macOS: double-click `Start Tag Network.command` (if macOS blocks it, right-click it and choose Open). Linux: run `python3 start_tag_network.py` in the folder.
3. **The first start takes about a minute**: it sets up a private environment inside the folder from the bundled files, with no internet. Later starts take a few seconds. If you move the folder or install another Python, the next start sets it up again.
4. The app opens in your browser at `http://127.0.0.1:8050`, or at the next free port (8051, …) if 8050 is taken. Keep the window open while you work; closing it stops the app.

It opens the latest Build in the bundle; add `--build <build id>` to the start command to open another one it carries. If it refuses to start, it says why and what to do (for example "This App Bundle needs Python 3.12, 3.13 or 3.14"). The app only reads the pipeline's own Top-100 Datasets; it never loads other files. (If you run the pipeline yourself, start the app from the repository instead, as the [Running Guide](../running-guide.md#the-app) describes.)

A yellow banner at the top warns when the Build comes from a test Snapshot (`mode: test`) or was made with parse errors allowed (`parse_errors_allowed`). Never publish numbers from such a Build. Another banner appears when a library the app computes with (for example networkx or numpy) is installed at a different version from the one the Build was made with, naming each library with both versions: the numbers may then differ from the Build's own reports. An App Bundle installs exactly the Build's versions, so you should not see it there.

## Load a dataset

Pick one of the five Top-100 Datasets in the **Dataset** selector: Overall, Puzzle, RPG, Strategy or Simulation. The app builds the Tag Network of that dataset at the shared defaults (the same settings the feature-analysis report uses) and clusters it. Every control change recomputes the whole Network State: network, clusters, null model, Seed-Noise Floor and all metrics. At loose thresholds a change can take several seconds.

Above the graph, the summary row shows the key numbers large: the games left after the Minimum Months Filter ("100 of 100"), tags, links, clusters ("3 + 4" multi-tag + one-tag), Q with its excess over the null model ("0.17 · excess +0.11") and the mean silhouette ("0.04 · descriptive"). Hover over any of them, or reach it with Tab, for a short explanation; click its dotted label for the full guide entry. Under it, one line states the Network State as a sentence that ends with its `state_id`; click the id to copy it.

The **Cluster quality** tab shows five boxes (Q, Null-model excess, Coverage, Silhouette, Seed noise), then the two full sentences, for example

> Q (γ = 1.00) 0.42 vs null 0.31 ± 0.01 (excess 0.11, z 11; null networks average 640 edges vs 702) · coverage 0.81 · 5 multi-tag + 3 one-tag · silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion 0.21

> Seed-noise floor (K = 10): ARI vs. main min 0.84, mean 0.93 · multi-tag clusters 5–7 · SD Q 0.004 · SD silhouette 0.01

Each number is explained in the [metric reference](03-metric-reference.md), and the app shows that help in two layers. Hover over a dotted label or a metric column header, or reach it with Tab, for a short explanation: what the value is, which direction is which, why it matters in this study and the main caution. Click the dotted label or the header's ⓘ, or press Enter, to open its full guide entry inside the app; links inside the help open their entries there too, and **← Back** returns to the previous one. Clicking a column header's name still sorts the table. The `?` button on each panel opens the matching guide section.

## The two modes

The **Mode** control at the top switches between two views of the same Network State. Settings, removed tags and results carry over when you switch.

- **Workbench**: controls on the left, the graph in the centre with a cluster legend and the Global / Cluster-separated layout switch, the inspector on the right, and tabbed tables below (Cluster quality, Clusters, Removal sensitivity, Nodes, Edges, Not in network). Controls, Inspector and Tables collapse independently; **Graph only** switches to the narrowest form, with the controls as a pill bar, a floating inspector and the tables as a bottom sheet (see [Window width and the three forms](02-app-controls.md#window-width-and-the-three-forms)).
- **Analysis Report mode**: one scrolling page of numbered sections over the same state: 1 Dataset · 2 Filters (every tag left out of the network, with its reasons) · 3 Network and inspector · 4 Cluster quality · 5 Removal sensitivity · 6 All nodes and edges · 7 Export. It is meant for reading one Network State top to bottom. It is not the generated feature-analysis report (`report.html`), which the Build writes.

## Inspect a node, an edge or a cluster

Click a node to see its metrics, an edge to see the games that have both tags, or a cluster (its legend button, its row in the Clusters table, or its region title in the Cluster-separated layout) to see its members ranked by how typical they are; the graph also zooms to that cluster (⤢ fits the whole graph again).

Every tag's label is shown at the same readable size at any zoom, with a white halo; the graph is laid out with room for all of them in the graph area you have. A selected tag and its neighbours get bold labels on a white box. Only when you zoom out further than the first view (or when a very large network cannot hold every label) are the less important labels hidden, Cluster Centers and tags on the most games kept first, until you zoom in again.

Selecting a tag fades everything except the tag and the tags linked to it; selecting a link keeps only the link and its two tags; selecting a cluster keeps its members. Click empty background to clear the selection. When a setting moves the nodes (a threshold, a hidden or removed tag, the Minimum Months Filter, the Clustering Weight, the seed, Tidy, the layout switch, opening or closing a panel, or the algorithm or γ in the Cluster-separated layout), they glide to their new places for about a third of a second; tags that leave or join the network fade out or in. If your system asks for reduced motion, all of this happens instantly.

You can drag nodes to arrange a view. Dragged positions belong to the view: they stay while you change thresholds or hidden tags, are dropped when the dataset, the Minimum Months Filter, the Clustering Weight or the seed changes, and are never exported on their own. Press **Tidy** to settle the rest of the graph around the nodes you dragged: they stay exactly where you put them, and an export afterwards records the tidied positions. A dragged node also stays where you put it when you switch between the layouts and back. With the inspector collapsed, or in a window narrower than 1280 px, a click opens it as a floating card over the right of the graph; close it with ×. The card never moves or re-draws the graph; if it covers the tag you selected, the view slides just far enough to show it.

From a node's inspector you can **Remove** the tag (a what-if: the source dataset never changes) or start **Run for this tag** (its Removal Sensitivity).
