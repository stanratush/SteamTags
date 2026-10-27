# Re-measure under ticket 16's γ scan rule

These are measured facts for [Graph-specific γ scan](../../issues/16-graph-specific-gamma-scan.md). The prototype is throwaway, and nothing imports it.

- **Build:** `20261008T221504Z-7a23ae9f` (the current `latest`), with all 765 Lift pair graphs and 12 workers.
- **Scripts:** [remeasure.py](remeasure.py) runs the phases `ref`, `new` and `search`. [report.py](report.py) produces [report.txt](report.txt). Raw records are in `runs/`.

```
uv run python .scratch/auto-parameter-selection/prototypes/16-remeasure/remeasure.py --phase ref|new|search
PYTHONIOENCODING=utf-8 uv run python .scratch/auto-parameter-selection/prototypes/16-remeasure/report.py
```

## Setup

- **new: the ticket 16 rule.**
  - The scan is γ = `round(0.05·i, 2)` for i = 0 … ⌈γ_max(n_e)/0.05⌉. γ_max(K) comes from `gamma_max_K` in research 16 (an exact 1-D maximisation).
  - It uses the 10 scan seeds.
  - Leiden is `leiden_capped`: passes of `n_iterations=1` until the gain is ≤ 0, at most 1,000 passes.
  - CHAMP runs on [0, last scan γ]. All other steps are ticket 03's `select`, unchanged.
  - The per-pair metrics and the Seed-Noise Floor are ticket 05's. The noise runs also use `leiden_capped`.
- **ref: the reference.** It is ticket 05's `compute_pair` unchanged: 56 γ from 0.25 to 3.00, `n_iterations=-1`, CHAMP on [0.25, 3.00].
  - Ticket 05's raw records are no longer on disk, so I recomputed it.
  - The recomputation reproduces [after-q3.md](../12-neighbour-agreement-bias/after-q3.md) exactly: the same Qualifying counts, maximum NA, near-best sizes, chosen pairs, NA values and n.
- **NA, Pair Constraints and choice:** the `renormalise`, `qualifies` and near-best rule of `after_q3.py` (tickets 06 and 12), with tolerance 0.05.
- **Workbench search:** ticket 09's rule.
  - It tries the two-decimal γ values in the domain, nearest the midpoint first (ties go to the lower value). At each γ it tries the main seed, then the 10 scan seeds.
  - Leiden here is `leiden_capped`.
- **Cross-check:** the new arm's Selected Partitions are identical to research 16's gmK arm (`scan_ends_gmK.json`) on 765 of 765 pairs. That holds even though research 16 ended CHAMP at the unrounded γ_max(K).
- **Determinism:** a second full run of `new` gave identical selections on 765 of 765 pairs, and the same 77 capped runs.

## 1. Selected Partitions

- **Pairs with a Selected Partition:** 764 of 765, unchanged.
  - The pair without one is rpg g=18 s=4 (`too_few_multi_tag_clusters`), as before.
- **3 pairs differ from the reference:**

| Pair | Reference: domain, midpoint, Multi-Tag Clusters, hits | New: domain, midpoint, Multi-Tag Clusters, hits | ARI |
|---|---|---|---:|
| puzzle g=3 s=3 | [2.694, 2.951], 2.822, 23, 1 | [2.448, 2.660], 2.554, 20, 2 | 0.909 |
| puzzle g=4 s=4 | [2.148, 2.362], 2.255, 16, 1 | **[0.064, 0.367], 0.216, 3, 67** | 0.039 |
| rpg g=3 s=3 | [2.532, 2.787], 2.659, 22, 2 | [2.864, 3.317], **3.090**, 26, 1 | 0.795 |

- **puzzle g=4 s=4** is ticket 16's open question 12. The selection is now a low-γ partition with 3 Multi-Tag Clusters and 11 One-Tag Clusters, all isolated. It wins because its domain is the widest.
- **The other two** are high-γ partitions on the two largest graphs: 139 and 128 tags.
- **Flags and estimates:**
  - Clipped-high Selected Partitions: 0. Selected domains starting at 0: 0. `not_representable`: 0.
  - `estimate_above_range`: 0, over all 27,549 Admissible Partitions (the reference had 17,532).
  - The largest γ̂ is 0.374 × the scan end.
  - `estimate_below_range`: 0, as expected.
  - Reasons: `one_group` on 765 partitions (the γ = 0 trivial partition, one per graph), `not_assortative` on 1,267.
  - Stable partitions: 1,531 (the reference had 1,530). None has γ̂ < 0.25 or > 3.0.

## 2. Chosen pairs per dataset

None of the five chosen pairs moved. Their NA, near-best set (same members) and Qualifying set are identical to after-q3:

| Dataset | Qualifying | Max NA (at) | Near-best | Chosen | NA (n) | Multi-Tag Clusters | Selected / Workbench γ |
|---|---:|---|---:|---|---|---:|---|
| overall | 149 | 1.000 (20,3; 20,9) | 7 | g=17, s=2 | 0.974 (3) | 4 | 1.151 / 1.15 |
| puzzle | 85 | 0.980 (14,2) | 1 | g=14, s=2 | 0.980 (2) | 4 | 1.092 / 1.09 |
| rpg | 120 | 0.822 (13,12) | 9 | g=7, s=5 | 0.774 (4) | 15 | 2.006 / 2.01 |
| simulation | 129 | 1.000 (17,2; 17,3; 17,4) | 9 | g=14, s=5 | 0.981 (4) | 3 | 0.865 / 0.86 |
| strategy | 113 | 1.000 (14,2) | 3 | g=14, s=2 | 1.000 (3) | 3 | 1.009 / 1.01 |

- **Qualifying Pair status changed on 0 pairs.**
- **NA changed on 8 Qualifying Pairs.** Each is one of the 3 changed pairs or one of their neighbours, all at g ≤ 5 and far below each dataset's maximum.
  - puzzle: (3,2) 0.576 → 0.572; (3,3) 0.529 → 0.532; (4,3) 0.546 → 0.446; (4,4) **0.696 → 0.003**; (5,4) 0.694 → 0.451.
  - rpg: (3,2) 0.510 → 0.486; (3,3) 0.523 → 0.550; (4,3) 0.525 → 0.550.

## 3. Workbench reproduction (ticket 09)

- **Reproduced:** 758 of 764 (the reference also gives 758).
  - 673 reproduce at the nearest-to-midpoint γ with some seed (reference: 673).
  - 419 reproduce at that γ with the main seed (reference: 418).
- **`not_reproduced`:** the same 6 pairs in both arms. Each Selected Partition was hit once.
  - puzzle 5,3
  - rpg 5,3; rpg 7,3; rpg 13,5
  - simulation 3,2
  - strategy 4,2
- **Workbench input range:**
  - One Selected Resolution is above 3.0: rpg g=3 s=3, at 3.090 (domain [2.864, 3.317]). Its search reproduces at γ = **3.23** with scan seed 1. That is the 28th γ tried, and it lies outside the current Workbench maximum of 3.0.
  - None is below 0.1. The lowest is puzzle g=4 s=4 at 0.216, which reproduces at 0.22 with the main seed on the first try. That is below the old 0.25 Apply fallback clamp, but inside 0.1–3.0.
  - puzzle g=3 s=3 reproduces at 2.50 with scan seed 7, the 11th γ tried.
- **Search cost:** 10,387 Leiden runs, 7.7 s, 0 capped.

## 4. Cost

- **Scan length:** 77 / 120 / 356 γ values per graph (min / median / max), 103,280 in all. The scan end runs from 3.80 to 17.75, median 5.95.
- **Leiden runs:**
  - Scan: 1,032,800 runs, against the reference's 428,400 (2.41×).
  - Seed-Noise Floor: 7,640 runs.
  - Workbench search: 10,387 runs.
- **Wall time on 12 workers:** **329 s** for all 765 pairs, scan and metrics included.
  - That is against ticket 05's 95 s, and 90.7 s for the reference recomputed here: about 3.5×.
  - Worker time was 3,943 s against 1,077 s, of which the scan was 3,857 s against 1,015 s.
  - The slowest pair, simulation g=5 s=5, took 136 s and is the critical path.
  - The first `new` run took 1,000.7 s. About 23 pairs in it were inflated by two machine-wide stalls of roughly 250 s and 210 s. The 329 s figure comes from the clean re-run.
- **Pass-capped runs:** 77, all in simulation and all at γ between 6.2 and 7.25 (the noise and search runs had none).

| Graph | Capped runs | at γ |
|---|---:|---|
| simulation g=5 s=5 | 56 | 6.20, 6.35, 6.45, 6.55, 6.60, 6.70 |
| simulation g=7 s=5 | 9 | 6.70 |
| simulation g=8 s=5 | 7 | 6.30 |
| simulation g=6 s=5 | 5 | 7.25 |

## 5. Surprises

- **The puzzle g=4 s=4 low-γ selection really happens under the decided rule.** It is not only a ticket 15 prediction.
  - With no low-γ guard, it is selected and its NA collapses from 0.696 to 0.003, which also lowers the NA of its neighbours (4,3) and (5,4).
  - It does not affect any chosen pair, because the puzzle maximum is 0.980 at g=14.
- **One Selected Partition now needs a Workbench γ above 3.0** (rpg g=3 s=3, 3.23). Ticket 16's question 9 is no longer hypothetical: Apply on that pair would need a wider Workbench input, or it falls to `not_reproduced` behaviour.
- **The pass cap costs time, not results.** simulation g=5 s=5 takes 136 s, with 56 capped runs, against a median pair of a few seconds. That one graph sets the critical path of the 12-worker run.
- **Everything else is identical:** 762 of 765 Selected Partitions, all five choices and the Workbench reproduction counts. The 2.4× longer scan buys no change in the chosen pairs.
