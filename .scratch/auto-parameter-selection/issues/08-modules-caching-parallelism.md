# Modules, caching and parallelism
Type: grilling
Status: open
Blocked by: 03

## Question

What are the module boundaries and interfaces, how is work cached and shared, and how does it run in parallel, consistent with the existing architecture? (Also consult `codebase-design`.)

- New modules under `steamstudy.network` (e.g. `champ.py` for the envelope and γ estimate, `selection.py` for the grid, metrics and choice, `validation.py`), and which existing functions they call (`build_network`, `shared_edges`, `to_graph`, `detect`, `metrics`, `curveball`, `ari`, `derive_seeds`). Should `detect` build the igraph once per pair instead of once per run (the scan makes 560 calls per pair: 56 γ × 10 seeds, per [Resolution-selection rules](03-resolution-selection-rules.md))?
- Reuse: neighbouring pairs often give identical graphs. Deduplicate by a graph hash so each distinct graph is scanned once; the Selected Partition depends only on the graph and the settings.
- The cache: key = Build, dataset, fixed settings (including the minimum Multi-Tag Clusters), grid, seeds and method version. Pair Constraints and the tolerance are **not** in the key: the selection is a cheap post-step over the cached per-pair results ([Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md)), and their defaults live in `[parameter_selection]` in `config/network.toml`; incremental per-pair results so a job can resume; how it sits beside `rs_cache.py` in `app_cache/`.
- Background job: the `multiprocess` pool, progress reporting (per dataset, per pair, per validation replicate), cancellation, and running all five datasets vs one.
- Determinism: the same settings always give the same results, whatever the process count or order.
- The scan seed stream: [Exploratory grid run on the current Build](05-exploratory-grid-run.md) assumed `derive_seeds` stream 3 (after NULL_STREAM 1 and NOISE_STREAM 2); fix the number. That run's timings, graph sharing (66 of 765 scans saved) and serial/parallel determinism are in its [results](../prototypes/05-grid-run/results.md) §4–5.
