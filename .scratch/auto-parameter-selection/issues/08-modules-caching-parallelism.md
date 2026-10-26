# Modules, caching and parallelism
Type: grilling
Status: resolved
Blocked by: 03, 07

## Question

What are the module boundaries and interfaces, how is work cached and shared, and how does it run in parallel, consistent with the existing architecture? (Also consult `codebase-design`.)

- New modules under `steamstudy.network` (e.g. `champ.py` for the envelope and γ estimate, `selection.py` for the grid, metrics and choice, `validation.py`), and which existing functions they call (`build_network`, `shared_edges`, `to_graph`, `detect`, `metrics`, `curveball`, `ari`, `derive_seeds`). Should `detect` build the igraph once per pair instead of once per run (the scan makes 560 calls per pair: 56 γ × 10 seeds, per [Resolution-selection rules](03-resolution-selection-rules.md))?
- Reuse: neighbouring pairs often give identical graphs. Deduplicate by a graph hash so each distinct graph is scanned once; the Selected Partition depends only on the graph and the settings.
- The cache: key = Build, dataset, fixed settings (including the minimum Multi-Tag Clusters), grid, seeds and method version. Pair Constraints and the tolerance are **not** in the key: the selection is a cheap post-step over the cached per-pair results ([Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md)), and their defaults live in `[parameter_selection]` in `config/network.toml`; incremental per-pair results so a job can resume; how it sits beside `rs_cache.py` in `app_cache/`.
- Background job: the `multiprocess` pool, progress reporting (per dataset, per pair, per validation replicate), cancellation, and running all five datasets vs one.
- Determinism: the same settings always give the same results, whatever the process count or order.
- The scan seed stream: [Exploratory grid run on the current Build](05-exploratory-grid-run.md) assumed `derive_seeds` stream 3; [Validation design](07-validation-design.md) fixed it at 3, with 4 for null shuffles and 5 for subsample draws. That run's timings, graph sharing (66 of 765 scans saved) and serial/parallel determinism are in its [results](../prototypes/05-grid-run/results.md) §4–5.

## Answer

Decided by grilling with the researcher, 2026-10-26. Checked against the code as it stands (`network/cluster.py`, `state.py`, `stability.py`, `sensitivity.py`, `app/rs_cache.py`, `rs_job` in `app/callbacks.py`, `app/server.py`) and the [grid-run prototype](../prototypes/05-grid-run/grid_run.py).

**Facts checked while deciding**
- Dash's `DiskcacheManager` starts each background job as a plain (non-daemonic) `multiprocess.Process`, so the job may start its own `multiprocess.Pool`. Cancel goes through `psutil` and kills the job's children recursively, so pool workers die with it.
- Building all 153 networks of one dataset in one process takes 0.56 s (overall and rpg), so deduplication can happen in the parent before any scan.

**Modules.** None imports Dash, the app, the loader or a cache, so the Build can call them later, like `compute_state`.
- `steamstudy.network.champ`: pure numpy, no Leiden. It takes a scan's unique memberships and the graph's edge arrays. It returns the Admissible Partitions (Â, P̂, Optimality Domain, clipped flags, γ̂ and reason) and the Selected Partition or its reason code. The `modularitypruning` cross-check tests this module.
- `steamstudy.network.selection`:
  - `SelectionSettings`;
  - `pair_networks(...)`: all pairs' networks and graph hashes;
  - `run_graph(...)`: network → scan → `champ` → Seed-Noise Floor, Information Retention, Fragmentation, descriptive metrics;
  - `neighbour_agreement(...)` over a finished grid;
  - `choose(grid, constraints)`: the Qualifying Pairs and the pick;
  - one driver, `run_grid(..., map_fn, on_result, should_stop)`;
  - `METHOD_VERSION = "parameter-selection-1"`.
- `steamstudy.network.validation`: `null_replicate(...)` and `subsample_replicate(...)`, each returning one small record, and `summarise(...)`. It reuses `curveball` and the procedure inside `run_graph`. `METHOD_VERSION = "ps-validation-1"`.
- `cluster.py` gains a private `_leiden_graph(graph)`, which builds the igraph and weights in `detect`'s current node and edge order, and a new `leiden_scan(graph, gammas, seeds)`. `detect` keeps its interface and uses the same construction, so a Workbench call at (γ, seed) gives exactly the scan's partition there. A test asserts the two agree.
- App side, following Removal Sensitivity:
  - `app/ps_cache.py` beside `rs_cache.py`, with the job functions in `callbacks.py`;
  - a new `app/app_cache.py` with `clear_all(root) → {kind: count}`, which calls `rs_cache.clear` and `ps_cache.clear`. The "Clear app cache" button and `steamstudy app --clear-cache` both use it, and the message reports both counts;
  - the "only persistent cache" docstring in `rs_cache.py` is corrected.

**Settings and keys**
- `SelectionSettings` is frozen and holds:
  - the base `Settings` minus g, s and resolution: Minimum Months, hidden and removed tags, Clustering Weight, algorithm, main seed, `null_replicates`, `noise_seeds`;
  - the g and s ranges, the γ scan (0.25, 3.00, 0.05), the scan seed count (10) and the minimum Multi-Tag Clusters (3);
  - R and S.

  `TRADES_PER_GAME` and the 80% fraction are constants.
- `grid_key()` is everything except R and S, plus `selection.METHOD_VERSION`.
- `validation_key(g, s)` is `grid_key()` plus g, s, R, S, trades, the fraction and `validation.METHOD_VERSION`, so a grid change also invalidates validation.
- Defaults come from `[parameter_selection]` in `config/network.toml`. The base settings come from the network defaults, overridden to Lift, Leiden and Minimum Months 0. The Pair Constraints, the tolerance and the worker count live in the same table but never enter a key.

**Seeds**
- Streams off the main seed: 3 = scan, 4 = null shuffles, 5 = subsample draws (ticket 07).
- Exclusion is cumulative: each stream excludes every lower stream's seeds. The scan excludes streams 1–2, stream 4 excludes 1–3 and stream 5 excludes 1–4, through one helper, `selection_seeds(main, settings, R, S)`.
- The scan seeds therefore depend on `null_replicates` and `noise_seeds`, which are in the key.

**Parallelism**
- **Grid work: one task per distinct graph.**
  - The parent builds every pair's network, hashes its nodes and edges (with shared counts) and makes one task per hash.
  - Every per-pair output depends only on the graph, so pairs that share a graph share one result. Only the (g, s) → hash map is per pair.
  - Ticket 04's `identical_graph` flag comes free.
  - This saves 66 of 765 scans on the current Build.
- **Validation work: one task per replicate.** A task is a single null or a single subsample and carries its seed, the pair's games and settings, and the observed Selected Resolution. A pair is 200 tasks.
- **Tasks are self-contained and picklable.** Each carries the dataset's games, the `TagContext`, the pair's `Settings` and the seed lists, a few KB in all. There is no worker initializer and no Build path in the pool. The worker rebuilds the network (≈4 ms) and checks it against the parent's hash.
- **The pool is injected.** `run_grid` and the validation driver take an unordered `map_fn`. The app job creates one `multiprocess.Pool` and passes `imap_unordered`; tests and a future Build pass the serial `map`. The worker count is `[parameter_selection] workers`, where 0 means `os.cpu_count() − 1`.

**Determinism**
- Each task is a pure function of its inputs. The parent sorts results by graph hash, then (g, s), and replicates by index, before Neighbour Agreement, `choose` or `summarise` run.
- The promise: the same Build, settings and code give byte-identical cached JSON, timings aside, for any worker count or arrival order.
- The test runs one dataset at g 15–17, s 2–4, serially and with a pool of 2, and compares the two.

**Cache** (`<build>/app_cache/parameter_selection/`)
```
grids/<grid_key_hash>/
  manifest.json              key, (g,s) → graph hash, total; Neighbour Agreement once complete
  graphs/<graph_hash>.json   one per finished distinct graph, atomic (tmp + replace)
validation/<validation_key_hash>.json   one per (dataset, pair), written only when complete
```
- A graph file holds:
  - the nodes and the edged tags;
  - every Admissible Partition: Â, P̂, domain, clipped flags, γ̂ and reason, Multi-Tag and One-Tag counts, membership, first (γ, seed) and hits;
  - the scan's unique-partition count;
  - the Selected Partition's index, or its reason code;
  - the Seed-Noise Floor, Retention, Fragmentation and descriptive metrics.

  Non-admissible partitions are not kept.
- Neighbour Agreement is computed once the grid is complete and stored in the manifest, since it ignores the constraints. `choose` is never cached.
- Only the job's parent process writes. Two tabs running the same job write identical bytes, so the race is harmless.
- Entries are never evicted automatically. An old method version's directory is unreachable until "Clear app cache".

**Background jobs**
- Two job kinds, each a Dash background callback. They exclude each other within the mode but may run beside a Removal Sensitivity job.
  - **Run**: one dataset, or "All datasets" one after another through one pool. Each dataset goes through phase 1 (the grid, then Neighbour Agreement and `choose` under the default constraints) and phase 2 (validation of the chosen pair). "All datasets" runs every grid before any validation. Cached work is skipped.
  - **Validate this pair**: offered only on a complete cached grid. It reads the pair's Selected Partition and Selected Resolution from the graph file.
- **Progress:** one `set_progress` record per finished task, `{dataset, dataset_index, n_datasets, phase: "grid" | "validation", done, total}`.
  - Grid units are pairs: a finished graph ticks all of its pairs, and the total is 153.
  - Validation units are replicates, out of R + S.
- **Cancel:**
  - Finished graph files survive. Reopening offers **Continue (k of 153 pairs)**, which skips graphs already on disk.
  - Neighbour Agreement, `choose` and the pick exist only for a complete grid.
  - Validation is all-or-nothing per pair. Cancel discards it, at most ~20 s of work on 12 workers, so no summary ever covers k < R replicates.

**Handed on**
- To [Apply-to-Workbench semantics](09-apply-to-workbench.md): `detect` and `leiden_scan` share one igraph construction, so Leiden at the Selected Partition's first (γ, seed) reproduces it exactly. Each Admissible Partition stores its first (γ, seed) and hit count.
- To [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md):
  - the progress record;
  - the two job kinds and their exclusivity;
  - the "All datasets" order (grids first);
  - the Continue offer, and what (if anything) a partial grid shows;
  - "Validate this pair" offered only on a complete grid.
- To [Shipping Parameter Selection results in an App Bundle](13-shipping-results-in-an-app-bundle.md): the cache layout above.
