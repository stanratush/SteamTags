# 18: Leiden pass loop, shared igraph construction and the γ input

**What to build:** Leiden runs go through one igraph construction and one capped pass loop, shared by the Workbench's `detect` and a new `leiden_scan`. The scan therefore finds exactly the partition the Workbench shows at the same (γ, seed). The Workbench γ input accepts any two-decimal value ≥ 0.01.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "The γ scan and Leiden", "Apply to Workbench" (γ input).

- [ ] `cluster._leiden_graph(graph)` builds the igraph and the weights in `detect`'s current order (nodes sorted, edges sorted by (min, max)). `detect`'s Leiden branch uses it, and its interface is unchanged.
- [ ] One capped pass loop (`PASS_CAP = 1000`): one `RBConfigurationVertexPartition` and one `Optimiser` seeded with the run's seed, looping `optimise_partition(p, n_iterations=1)`. It stops at the first pass that gains ≤ 0, or at the cap, and reports whether the cap was hit. `detect` uses it in place of `find_partition(..., n_iterations=-1)`.
- [ ] `leiden_scan(graph, gammas, seeds)` builds the igraph once and runs the loop for every (γ, seed) in scan order (γ ascending, then seeds in the given order). It returns each run's membership in node order plus a capped flag.
- [ ] Louvain is untouched. `KEY_VERSION` is unchanged, because results below the cap are identical.
- [ ] The Workbench γ input (`app/layout.py`) becomes `min=0.01`, no `max`, `step=0.01`. Any server-side validation or clamping of γ follows suit.
- [ ] Tests:
  - On a small weighted graph where `n_iterations=-1` stops, the loop's membership equals `find_partition(..., n_iterations=-1)` at several γ and seeds.
  - `detect(graph, "leiden", γ, seed)` equals `leiden_scan`'s run at (γ, seed) for every run of a scan over a real test-Build network.
  - A float-noise case that never stops (or a monkeypatched optimiser that always gains) stops at 1,000 passes with the capped flag set.
  - The existing network and app tests still pass. A γ of 1.09 and of 3.23 is accepted by the Workbench input and survives a recompute.
