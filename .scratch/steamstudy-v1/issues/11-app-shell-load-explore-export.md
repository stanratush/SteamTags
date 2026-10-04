# 11: App shell: load, explore, export

**What to build:** `steamstudy app` opens the Tag Network Workbench at `http://127.0.0.1:<port>`, fully offline. The researcher picks a dataset from a Build and moves the threshold, filter, Genre Tag, defining-tag, Clustering Weight, algorithm, γ and seed controls. They see the graph coloured by Cluster, remove, restore or reset tags, read the Nodes, Edges and Not-in-network tables, and download the state as one self-contained zip. A test proves the app gives exactly the Build's network tables.

**Blocked by:** 06

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Stack and process, Renderer boundary, Recompute model, Controls, Graph, Banners), "Export schemas" (App export).

- [ ] `steamstudy app [--build <id>]` (default: latest) listens only on `127.0.0.1` and opens the browser at `127.0.0.1`, never `localhost`. Runs with `debug=False`, and no request leaves `127.0.0.1` (tested).
- [ ] The app module does nothing at import beyond defining its layout.
- [ ] The graph renderer is reached through one module taking nodes, edges, stylesheet and positions. It uses a `preset` layout, re-fits explicitly once the first elements arrive, and sends no AppID lists.
- [ ] Controls are initialised from `network.toml`, with ranges as in the spec. Sliders send on release; seed and γ on Enter or blur; toggles immediately. Every change recomputes the whole Network State, with no server-side state.
- [ ] Nodes are coloured by cluster, with edge width mapped from `shared_games`. Tabs: Nodes, Edges, Not in network (with reasons), sortable and filterable.
- [ ] Remove (on a node), restore and reset all work without touching the dataset files.
- [ ] Banners appear for `mode: test` and `parse_errors_allowed`.
- [ ] "Export this state" downloads `steamstudy_<dataset>_<state_id>_<UTC timestamp>.zip`. It contains the network CSVs available so far and `export.json`: `schema_version`, full `state_key`, `state_id`, `layout_source`, `exported_at`, software versions, a copy of the Build's `build.json` provenance, `files` (row counts + SHA-256), the method constants available so far, and `columns`. Nothing is written into the Build folder.
- [ ] Equality test: the app at the report's settings exports CSVs equal to that dataset's Build rows minus `dataset` / `state_id`.
