# 16: Resolving each dataset's partition

**What to build:** given a Build, the shared settings and one dataset's source and values, return its resolved partition ready for matching, with its Seed-Noise Floor, Neighbour Agreement and provenance. A dataset on a cell (pick or selected) reads its stored Selected Partition from the Parameter Selection cache; a dataset set by hand or with no run is clustered once with the Build's main seed by a new light function in `network/state.py`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "Datasets and their values", "Shared settings", "Compute and caching". Decisions: tickets [03](03-per-dataset-defaults.md), [10](10-seed-per-dataset.md), [12](12-compute-and-caching.md), [14](14-defining-tag-in-a-match.md).

- [ ] **On a cell:** the pick is the run's starred cell under the Pair Constraints currently set in Parameter Selection for the tab; a selected cell is any other cell with a Selected Partition. Both read network Tags, edged Tags, labels, Selected Resolution, Seed-Noise Floor and Neighbour Agreement from the cache, never re-clustered and with no seed ("not reproduced" cells included). No Network State is built.
- [ ] **Hand or no run:** the light function (from `build_network`, `cluster_graph` and `noise_seeds`) gives the network, one clustering with the main seed and the noise-seed runs for its Seed-Noise Floor; no null replicates, centres, silhouette or node metrics. It also yields the `state_id` of those settings.
- [ ] A no-run dataset starts from the Build's network g, s and resolution.
- [ ] Each dataset's own defining Tag is always hidden (`hide_defining_tag` on); a run made with it shown never feeds the comparison.
- [ ] **A cell that vanishes** (cache cleared, run changed) falls to the no-run rule with network defaults, and the result says the run is gone; old values are not kept as hand-set.
- [ ] The result carries its source code (`pick` / `cell` / `hand` / `no_run`), g, s, γ, the seed (hand / no run only), the selection key and Threshold Pair (cell only) or the `state_id` (hand / no run only).
- [ ] Tests:
  - The light function's partition and Seed-Noise Floor equal `compute_state`'s at the same settings.
  - Pick, selected cell, hand and no run each resolve from a small cache fixture written by `ps_run`; the pick follows a change of Pair Constraints.
  - A vanished cell falls to network defaults and reports the run as gone.
  - Timing on the full Build (skipped when absent): about 0.4 s per dataset on a cell, 0.1 s per hand-set dataset.
