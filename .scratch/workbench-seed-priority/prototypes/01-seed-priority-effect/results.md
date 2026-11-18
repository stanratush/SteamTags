# What would "Prefer the main seed" change?

This measurement asks whether a Build setting should let the Workbench search try the main seed at every γ first. It is throwaway and nothing imports it. The search it compares against is described in [Apply-to-Workbench semantics](../../../auto-parameter-selection/issues/09-apply-to-workbench.md).

It was run on Build `20261109T064256Z-493c5375` with the default Selection Settings for all five datasets: 667 pairs with a Selected Partition, on 647 distinct graphs. The overall grid came from the Build's cache. The other four grids were computed in memory, and the cache was not touched. The script first checks that today's `workbench_setting` still gives the cached answer.

```
PYTHONIOENCODING=utf-8 uv run python .scratch/workbench-seed-priority/prototypes/01-seed-priority-effect/measure.py
PYTHONIOENCODING=utf-8 uv run python .scratch/workbench-seed-priority/prototypes/01-seed-priority-effect/report.py
```

The raw numbers are in [report.txt](report.txt), and the per-graph records are in `results.json`.

| | Closest γ (today) | Prefer the main seed |
|---|---:|---:|
| Pairs reproduced exactly (of 667) | 660 | 660 |
| … with the main seed | 503 | 595 |
| … at the two-decimal γ nearest the midpoint | 630 | 546 |

Both modes reproduce the same pairs, as they must, because the set of candidates is the same. The two modes pick a different (γ, seed) for **92 pairs** (90 graphs). On those graphs:

- **γ moves away from the midpoint.** The extra distance has a median of 0.042, a 90th percentile of 0.105 and a maximum of 0.210. Measured as a share of the half-domain, the main-mode γ sits a median 41% of the way from the midpoint to the edge, and at most 98%. The closest mode sits a median 2% from the midpoint.
- **Q changes.** Q of the same partition differs by a median of +0.003, with a range of −0.060 to +0.034.
- **The Workbench Seed-Noise Floor is not systematically better or worse.** Its median is 0.770 in the closest mode and 0.771 in the main mode, but single graphs move by −0.29 to +0.44. The mean ARI is a median 0.025 higher in the main mode. This is likely a selection effect: γ values where one fixed seed reproduces the partition tend to be values where seeds agree.
- **The main mode matches Parameter Selection's floor worse, not better.** The gap |Workbench floor − Parameter Selection floor| has a median of 0.000 (maximum 0.301) in the closest mode and a median of 0.027 (maximum 0.444) in the main mode. Parameter Selection computes its floor at the exact midpoint, and that γ counts for more than which seed stream is used.
- **None of the five default chosen pairs changes.** Overall 16,10, puzzle 11,5, rpg 12,2, strategy 8,3 and simulation 14,11 each reproduce with the main seed at the γ nearest the midpoint.

## Verdict

There is no scientific case for the setting. The main seed has no privileged status: every seed is an equivalent random draw, and the scan seeds are derived from the main seed in a fixed way. Choosing the main seed moves 92 pairs' γ a median 41% of the way from the midpoint towards the edge of the domain. That changes Q and the γ-dependent readings of a partition that is identical in both modes. The one benefit the setting seemed to offer, a Seed-Noise Floor consistent with Parameter Selection's, gets worse instead.
