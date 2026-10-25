# Modules, caching and parallelism
Type: grilling
Status: open
Blocked by: 03

## Question

What are the module boundaries and interfaces, how is work cached and shared, and how does it run in parallel, consistent with the existing architecture? (Also consult `codebase-design`.)

- New modules under `steamstudy.network` (e.g. `champ.py` for the envelope and γ estimate, `selection.py` for the grid, metrics and choice, `validation.py`), and which existing functions they call (`build_network`, `shared_edges`, `to_graph`, `detect`, `metrics`, `curveball`, `ari`, `derive_seeds`). Should `detect` build the igraph once per pair instead of once per run (the scan makes 800 calls per pair)?
- Reuse: neighbouring pairs often give identical graphs. Deduplicate by a graph hash so each distinct graph is scanned once; the Selected Partition depends only on the graph and the settings.
- The cache: key = Build, dataset, fixed settings, grid, seeds, constraint settings and method version; incremental per-pair results so a job can resume; how it sits beside `rs_cache.py` in `app_cache/`.
- Background job: the `multiprocess` pool, progress reporting (per dataset, per pair, per validation replicate), cancellation, and running all five datasets vs one.
- Determinism: the same settings always give the same results, whatever the process count or order.
