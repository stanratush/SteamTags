# 11: App shell: load, explore, export

**What to build:** `steamstudy app` opens the Tag Network Workbench at `http://127.0.0.1:<port>`, fully offline. The researcher picks a dataset from a Build and moves the threshold, filter, Genre Tag, defining-tag, Clustering Weight, algorithm, γ and seed controls. They see the graph coloured by Cluster, remove, restore or reset tags, read the Nodes, Edges and Not-in-network tables, and download the state as one self-contained zip. A test proves the app gives exactly the Build's network tables.

**Blocked by:** 06

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Stack and process, Renderer boundary, Recompute model, Controls, Graph, Banners), "Export schemas" (App export).

- [x] `steamstudy app [--build <id>]` (default: latest) listens only on `127.0.0.1` and opens the browser at `127.0.0.1`, never `localhost`. Runs with `debug=False`, and no request leaves `127.0.0.1` (tested).
- [x] The app module does nothing at import beyond defining its layout.
- [x] The graph renderer is reached through one module taking nodes, edges, stylesheet and positions. It uses a `preset` layout, re-fits explicitly once the first elements arrive, and sends no AppID lists.
- [x] Controls are initialised from `network.toml`, with ranges as in the spec. Sliders send on release; seed and γ on Enter or blur; toggles immediately. Every change recomputes the whole Network State, with no server-side state.
- [x] Nodes are coloured by cluster, with edge width mapped from `shared_games`. Tabs: Nodes, Edges, Not in network (with reasons), sortable and filterable.
- [x] Remove (on a node), restore and reset all work without touching the dataset files.
- [x] Banners appear for `mode: test` and `parse_errors_allowed`.
- [x] "Export this state" downloads `steamstudy_<dataset>_<state_id>_<UTC timestamp>.zip`. It contains the network CSVs available so far and `export.json`: `schema_version`, full `state_key`, `state_id`, `layout_source`, `exported_at`, software versions, a copy of the Build's `build.json` provenance, `files` (row counts + SHA-256), the method constants available so far, and `columns`. Nothing is written into the Build folder.
- [x] Equality test: the app at the report's settings exports CSVs equal to that dataset's Build rows minus `dataset` / `state_id`.

## Comments

- 2026-10-04 (agent): App implemented in steamstudy.app (loader, renderer boundary, layout, callbacks, export/open, rs_cache, server). Tested via the export zip (app equals Build, round trip, refusals), the served page (no external URLs) and the callbacks as functions; also exercised live in the browser on a demo Build (node/edge/cluster inspectors, remove, layout switch, Re-layout, background Removal Sensitivity run with stale/current display, Analysis Report mode on the same renderer instance, floating inspector). Open Network State also re-exports and can compare table hashes (recorded_table_hashes_match).
