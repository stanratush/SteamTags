# 23: Validation: Null Comparison and Subsample Stability

**What to build:** `steamstudy.network.validation`, with one-replicate tasks for curveball nulls and 80% subsamples, each running the full per-pair procedure plus its second arm, and `summarise`, which produces the reported figures and the only two verdicts. The validation block's fixed sentences go into `selection_text`.

**Blocked by:** 21, 22

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "Validation" (all of it), "Seeds", "Parallelism and determinism". Reference code: [pilot.py](../prototypes/07-validation-pilot/pilot.py). Methods: [Research 02](../research/02-validation-methods.md).

- [ ] `METHOD_VERSION = "ps-validation-1"`, `SUBSAMPLE_FRACTION = 0.8`, and reuse of `stability.TRADES_PER_GAME`.
- [ ] `validation_tasks(games, settings, context, g, s, observed, seeds) -> list[ReplicateTask]`: R null tasks (stream 4) and S subsample tasks (stream 5). Each carries the pair's games and settings, the observed Selected Resolution and Selected Partition, and the scan seeds. They are picklable and weighted (pair edges × observed scan length).
- [ ] `null_replicate(task)`:
  - curveball over games × the pair's network tags, with `TRADES_PER_GAME × games` trades and `random.Random(seed)`;
  - rebuilds at the same (g, s);
  - runs the full procedure on its own scan range: a Selected Partition or a reason, the domain width, the Selected Resolution and the Multi-Tag Clusters;
  - the fixed-γ Q at the observed resolution from its own envelope;
  - the edge count, scan length and capped runs.
- [ ] `subsample_replicate(task)`:
  - m = ⌊0.8·n⌋ games without replacement, g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋) in integers;
  - the re-selected arm, and the envelope partition at the observed γ;
  - on the NA comparison set: ARI, Hennig's Jaccard per Multi-Tag Cluster (best match over all subsample Clusters), retention share and absent flags;
  - degenerate reasons.
- [ ] `summarise(observed, records) -> ValidationSummary`: every figure the spec lists for both checks, computed over non-degenerate replicates and present Clusters only (missing is never 0). The verdicts are "Dissolved" per Cluster per arm (mean Jaccard ≤ 0.5) and "Q not above the null" (≥ 1 replicate reaches the observed Q).
- [ ] `run_validation(tasks, *, map_fn, on_result, should_stop)` returns records sorted by index, or `None` if stopped (all-or-nothing).
- [ ] `selection_text.validation_block(summary, pair, chosen_pair, ran_for_default)`: the block word for word, with its variants ("reach it: Q not above the null", "Not validated", "Validation ran for … the pair chosen under the default constraints") and both caveats.
- [ ] Tests:
  - The curveball replicate keeps every tag's game count and every game's tag count.
  - Floor scaling: n = 100 gives g′ = 4g // 5, and s′ never falls below 2.
  - Hennig's Jaccard on a hand-built case: restriction to the set, best match including One-Tag Clusters, absent Clusters left out of the mean, One-Tag Clusters of the Selected Partition never scored.
  - Degenerate subsamples are counted and excluded, never scored 0.
  - The fixed-γ Q is read from the envelope (equal to Â − γP̂ of the envelope partition at γ).
  - Determinism: serial and a pool of 2 give identical summaries for one pair with small R and S.
  - Golden text for the validation block with each variant.
