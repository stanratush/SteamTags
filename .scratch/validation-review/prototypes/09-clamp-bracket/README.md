# 09 Threshold clamp bracket at s = 2

Ticket: [Threshold clamp bracket at s = 2](../../issues/09-threshold-clamp-bracket.md). Run 2026-11-04 on Build
`20261008T221504Z-7a23ae9f` (the Build of 2026-10-08).

## Files

- `clamp_bracket.py`: the rerunnable script. It takes `--build` and `--pairs dataset:g:s` and runs **every stored
  validation** of those pairs. For each one it rebuilds the app's subsample tasks: the Build's configured defaults
  plus the stored run's `min_multi_tag_clusters`, the observed partition from the cached grid, and the subsample
  seeds of stream 5. Before running, it checks the grid key, the seeds and the observed Multi-Tag Clusters against
  what was stored. Each of the 100 subsamples then runs twice, at s′ = 2 (the clamp) and at s′ = 1 (the looser
  bracket). The draw and g′ are the same in both runs, so they are paired. It scores the figures and statuses
  decided in tickets 01 and 02, which the app does not compute yet: Hennig's Jaccard at |C′| ≥ 2, Whole-Cluster
  Jaccard, the dissolution and recovery frequencies with Wilson intervals, and Not assessable / Dissolved in most
  subsamples / borderline.
- `results.json` / `results.md`: the full run. It made 1200 subsample runs in 194 s on 12 workers.

The script reads this Build's cache at the full 64-hex key hash. The cache was written before "Short Parameter
Selection cache names" (9aa40e6), and the current app looks for 16-character names.

Rerun on a new Build (about 3–4 min):

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/09-clamp-bracket/clamp_bracket.py \
        --build builds/<run>/<build> --pairs <every validated pair with s = 2, as dataset:g:s>

## Checks

- **Determinism:** the s′ = 2 rerun reproduces every stored Hennig's Jaccard exactly, 4952 of 4952 values over the
  6 runs and both arms.
- **The bracket is real:** the median subsample network gains 8–22% edges at s′ = 1 (puzzle 12/2: 642 → 784;
  overall 17/2: 440 → 476).

## Results

Six stored runs at the 5 validated s = 2 pairs. Puzzle 14/2 has two runs, at min multi 2 and 3. That makes
25 Cluster-runs per arm.

| Pair | Clusters | Labelled (re-selected), s′ = 2 → 1 | Labelled (at resolution), s′ = 2 → 1 | Borderline marks that move |
|---|---|---|---|---|
| puzzle 12/2 | 6 | C3, C6 → C3, C6 | C3, C6 → C3, C6 | re-selected C4 off, C5 on; at resolution C5 off |
| puzzle 14/2 (min multi 2) | 4 | C3, C4 → C3, C4 | C3, C4 → C3, C4 | – |
| puzzle 14/2 (min multi 3) | 4 | C3, C4 → C3, C4 | C3, C4 → C3, C4 | – |
| overall 12/2 | 4 | C4 → C4 | C4 → C4 | at resolution C4 on |
| overall 17/2 | 4 | C4 → C4 | – → – | – |
| strategy 14/2 | 3 | – → – | – → – | – |

- **No label moves.** The clamp moves 0 of 50 Dissolved-in-most-subsamples labels (25 Cluster-runs × 2 arms):
  - re-selected: 8 labelled under both s′;
  - at resolution: 7 labelled under both s′.

  No Cluster is Not assessable, and none is rarely assessable, under either s′.
- **The closest call:** puzzle 12/2 C3, re-selected, dissolved in 52/92 subsamples at s′ = 2 and 45/87 at s′ = 1
  (52% against 57%). It is borderline under both.
- **The means barely move.** The mean Hennig's Jaccard changes (s′ = 1 minus s′ = 2):
  - re-selected: median +0.003, range −0.045 to +0.035;
  - at resolution: median +0.008, range −0.026 to +0.070.

  Whole-Cluster Jaccard moves the same way. The largest move is overall 12/2 C4, a 3-tag Cluster, at resolution:
  0.404 → 0.474, still dissolved.
- **The changes have no direction.** s′ = 1 is looser, but it does not uniformly raise recovery. About as many
  Clusters drop as rise, for example puzzle 12/2 C2, re-selected, 0.670 → 0.625.
- **Degenerate subsamples:** only puzzle 12/2 re-selected has any. It has 8 at s′ = 2 and 13 at s′ = 1, all with no
  Selected Partition.
- **ARI:** the median moves by at most 0.042 (strategy 14/2, re-selected: 0.766 → 0.724).

**Guide quote:** "On the Build of 2026-10-08, rerunning the s = 2 validations with s′ = 1 instead of the clamped
s′ = 2 moves 0 of 50 Dissolved-in-most-subsamples labels (25 Multi-Tag Clusters × 2 arms) and changes a mean
Hennig's Jaccard by at most 0.07."

Caveat: this brackets only the threshold. g′ = ⌊0.8 g⌋ and the 80% fraction stay fixed.
