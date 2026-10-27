# 21: Per-graph procedure and the grid driver

**What to build:** `run_graph`, the self-contained grid task (network → scan → CHAMP → Workbench γ/seed search → per-pair metrics), and `run_grid`, the driver that dedups graphs in the parent, dispatches heaviest first through an injected `map_fn`, and returns a deterministic grid result.

**Blocked by:** 18, 19, 20

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "The per-pair procedure" (all of it), "Parallelism and determinism". Reference code: [grid_run.py](../prototypes/05-grid-run/grid_run.py), [remeasure.py](../prototypes/16-remeasure/remeasure.py), [apply_search.py](../prototypes/09-apply-reproduction/apply_search.py).

- [x] `GraphTask`: picklable, self-contained. It carries the dataset's games, the `TagContext`, the pair's `Settings`, the scan seeds, the γ step, the minimum Multi-Tag Clusters, the main seed, and the expected graph hash and weight. No Build path, no initializer.
- [x] `run_graph(task) -> GraphResult`:
  - rebuilds the network and checks the hash;
  - with no edges, gives `no_edges` without a scan;
  - otherwise derives n_e, γ_max(n_e) and the scan values, then runs `leiden_scan` and dedups;
  - runs `champ` (Admissible Partitions, γ̂, the Selected Partition or its reason);
  - runs the **Workbench γ and seed search** (two-decimal values ≥ 0.01 inside [a, b], nearest the midpoint first, ties to the lower; main seed, then scan seeds; exact reproduction), setting `not_representable` / `not_reproduced`;
  - computes the Seed-Noise Floor at the exact Selected Resolution (`noise_seeds(main, noise_seeds, null_replicates)`, ARI over all nodes: minimum, mean and exact count);
  - computes Information Retention (and the share of games with an edged tag), Fragmentation, the graph counts (tags, edges, n_e, Lift < 1 share, γ_max(n_e), γ_end, scan length, `pass_capped_runs`, unique partitions, twins) and the descriptive Q, Coverage and Silhouette (reusing `metrics.py`).
- [x] `GraphResult` is a plain record holding every field of the spec's graph file, including the edge list (for Edge Overlap later). It serialises to canonical JSON.
- [x] `run_grid(games, settings, context, *, map_fn, on_result, should_stop, skip=frozenset())`:
  - builds every pair's network in the parent and makes one task per distinct hash, skipping hashes in `skip` (for resume);
  - dispatches in descending weight (edges × scan length);
  - calls `on_result(hash, result, pairs_ticked, weight)` per result;
  - stops dispatching when `should_stop()`;
  - returns the (g, s) → hash map and the results sorted by hash.
- [x] No Dash, app, loader or cache import anywhere in `network/`.
- [x] Tests:
  - On the test Build, one dataset at g 15–17, s 2–4: `run_grid` serially and with a `multiprocess` pool of 2 gives byte-identical canonical JSON (timings aside).
  - Every pair with a Selected Partition has its Workbench (γ, seed) reproduce it through `detect`, or carries a flag. A monkeypatched case exercises `not_representable` (a domain with no two-decimal value) and `not_reproduced`.
  - The descriptive Q equals CHAMP's (Â − γP̂)/2m at the Selected Resolution to ≤ 1e-12.
  - Information Retention counts visible tags below g in the denominator, and removed and hidden tags in neither.
  - `should_stop` stops dispatch, and `skip` skips the listed hashes.
  - Performance smoke: one dataset's grid on the test Build finishes within a generous bound on 2 workers.

## Comments

- 2026-10-27, implementation: Implemented in `network/selection.py` (`GraphTask`, `run_graph`, `GraphResult`, `grid_tasks`, `run_grid`, `workbench_setting`). The flag cases are exercised on `workbench_setting` directly (a domain with no two-decimal value, and a membership Leiden never returns) rather than by monkeypatching `run_graph`.
