# Does the Workbench reproduce the Selected Partition?

Fact-finding for [Apply-to-Workbench semantics](../../issues/09-apply-to-workbench.md). Throwaway; nothing imports it.

Build `20261008T221504Z-7a23ae9f`, the procedure of tickets 03–04 via [the grid-run prototype](../05-grid-run/grid_run.py) (56 γ × 10 scan seeds, Lift, Leiden), all 765 pairs, 12 workers.

```
.venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/09-apply-reproduction/apply_repro.py <out.json>
.venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/09-apply-reproduction/apply_search.py <out.json>
```

| How the Workbench is set | Exact reproductions (of 764) |
|---|---:|
| Workbench resolution (two decimals nearest the midpoint, in the domain), main seed | 418 (55%) |
| Workbench resolution, main seed then the 10 scan seeds | 673 (88%) |
| Every two-decimal γ in the domain, nearest the midpoint first, main seed then scan seeds | 758 (99.2%) |
| The scan's first (γ, seed) | 764 (100%), but γ is outside the Optimality Domain in 239 (31%) |

- With the main seed at the Workbench resolution, the non-exact pairs have median ARI 0.758 and minimum 0.309.
- For the 85 pairs recovered only by moving γ, the shift from the midpoint is 0.007–0.184 (median ≈ 0.027).
- All 6 pairs never recovered have a Selected Partition hit only once in 560 scan runs. Their domains hold 10–31 two-decimal values.
- No pair is `not_representable`.

The default-constraint chosen pairs (ticket 06):

| Dataset | Pair | Workbench γ | Main seed exact | Scan seeds exact at that γ | First (γ, seed) in domain |
|---|---|---:|---|---:|---|
| overall | 17, 2 | 1.15 | yes | 10 | yes |
| puzzle | 14, 2 | 1.09 | no (ARI 0.711) | 3 (first: scan seed 2) | no (1.00 < 1.046) |
| rpg | 14, 12 | 1.75 | yes | 10 | no (1.40 < 1.421) |
| simulation | 14, 5 | 0.86 | yes | 10 | yes |
| strategy | 14, 2 | 1.01 | yes | 10 | no (0.80 < 0.878) |
