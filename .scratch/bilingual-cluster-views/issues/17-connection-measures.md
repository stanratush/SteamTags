# 17: Connection Ratio and Connection Share in `cluster_connections.csv`

**What to build:** `metrics.connections` gains the Connection Ratio, the Connection Share and the always-filled shared-game total and ratio. `cluster_connections.csv` gains five additive columns under `SCHEMA_VERSION` 4. The English guide documents them. This is a computation and export issue: the existing Cluster quality grid shows the new columns as they arrive, and the views come in issues 18–20.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Connection Ratio and Connection Share", "Exports and the schema version", "Resolved while writing this spec" (older exports). Records: [ADR 0004](../../../docs/adr/0004-connection-ratio-is-the-configuration-model-ratio.md), [research 05](../research/05-normalised-inter-cluster-strength.md). Reference computation, not to import: [`dump_state.py`](../prototypes/07-cluster-connections/dump_state.py).

- [ ] **Strengths**, from existing per-tag values:
  - k_a = 2·`internal_weight` + `cut_weight` in the Clustering Weight, and 2m = 2·`total_weight`;
  - the same in shared games (`strength_shared`);
  - for `one_tag_pool`, k_p is the sum of its members' strengths.
- [ ] **Ratio**: r_ab = w_ab / (k_a·k_b / 2m). Pool–pool uses E_pp = (k_p² − Σ_i k_i²)/4m.
- [ ] **Shared-game total and ratio**: always filled, from shared-game sums. Under shared games they equal `weight` and `ratio`.
- [ ] **Shares**: `share_of_a` = w_ab / cut_a and `share_of_b` = w_ab / cut_b, in the Clustering Weight only. For the pool, cut_p = k_p − w_pp.
- [ ] **Empty, never clamped**:
  - k_p = 0 (a pool of isolated tags only);
  - E_pp = 0 (fewer than two linked pool tags);
  - cut = 0 (no outside links), for that side's share.

  A ratio slightly above γ is kept as computed.
- [ ] **`cluster_connections.csv`**: the four existing columns are unchanged, then `shared_weight`, `ratio`, `shared_ratio`, `share_of_a`, `share_of_b`, at full precision.
  - Each column is declared in `schema.py`, and `SCHEMA_VERSION` goes from 3 to 4.
  - The columns are indexed in `guide_index`, and Appendix B is regenerated.
- [ ] **Older exports**: `recorded_table_hashes_match` compares each table on the columns the original export has, so a version 3 export, and one without a table added later, still matches.
- [ ] **Guide** (`03-metric-reference.md`):
  - The **Cluster connections** entry keeps its anchor and documents the new columns.
  - Its example becomes "seven links whose shared-game counts sum to 58", with the caution that one game can count several times.
  - New sub-entries **Connection Ratio** and **Connection Share**, each with its own anchor and the agreed In short block (spec, verbatim). Then Why it matters, Example, Bounds (including the three empty cases and the hair-above-γ note), Compare with and Exact definition.
  - The Ratio entry's cautions: minimum shared games, the shared-game ratio under Lift, dividing by γ across resolutions, neither similarity nor cause.
  - The Share entry states the pool's share as the one special case.
- [ ] Tests:
  - On a hand-built graph with two Multi-Tag Clusters and a pool, every column matches a brute-force computation.
  - On test-Build states under both Clustering Weights, `ratio` is ≤ γ + 1e-6 for every pair, pool rows included.
  - Each Cluster's shares, and the pool's, sum to 1.
  - Each of the three empty cases is empty.
  - The schema, `guide_index`, Appendix B staleness and guide link tests pass.
  - A version 3 fixture export opens and passes `recorded_table_hashes_match`.
