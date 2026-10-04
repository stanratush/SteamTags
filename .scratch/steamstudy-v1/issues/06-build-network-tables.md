# 06: Build network tables

**What to build:** Every Build runs the Network State core on each of the five Top-100 Datasets at the feature-analysis report's settings (shared network defaults, defining tag out, config algorithm / γ / seed / Clustering Weight). It writes the network tables, stacked by dataset, into the Build's `analysis/` folder through the same declared writer the app export will use.

**Blocked by:** 04, 05

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network", "Export schemas" (Build `analysis/` folder, App export column lists).

- [x] `network.toml` shared defaults are applied: 8/8/0, Genre Tags (the 11 Top-Level Genres from `genres.toml`) hidden, defining tag hidden, `shared_games`, `louvain`, γ 1.0, the config seed.
- [x] One network writer serves both outputs: the app zip (one dataset, no prefix columns) and the Build (five datasets stacked, with `dataset` and `state_id` as the first two columns).
- [x] The Build writes `network_nodes.csv`, `network_edges.csv`, `network_clusters.csv` and `network_not_in_network.csv`, with the columns this ticket can fill. Columns added by later tickets are declared then, each bumping `schema_version`.
- [x] `edges.csv` rows are sorted by source/target `tag_id` with source < target, and carry both `shared_games` and `lift` plus `appids` in dataset rank order.
- [x] `analysis.json` is started: `schema_version`, `build_id`, and per dataset the `state_key`, `state_id` and `n_games`, plus `columns`.
- [x] `build.json` records the seed, the network defaults, and the pinned versions of both clustering libraries.
- [x] A test builds the fixture Snapshot twice and gets byte-identical network tables.

## Comments

- 2026-10-04 (agent): Implemented: analysis/network_stage.py runs the report Network State per dataset; network/tables.py is the single writer (app rows; stack() adds dataset/state_id). All network columns are declared at schema_version 1, since nothing was published under an earlier schema.
