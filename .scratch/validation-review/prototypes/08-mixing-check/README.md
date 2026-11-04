# 08 Mixing check at the validated pairs

Ticket: [Mixing check at the validated pairs](../../issues/08-mixing-check-at-validated-pairs.md). Run 2026-11-04 on
Build `20261008T221504Z-7a23ae9f` (the Build of 2026-10-08).

## Files

- `mixing_check.py`: the rerunnable script. It rewrites Research 02 §A.4's lost `mixing_check.py` and uses the same
  design: chains start from the observed game × visible-tag table, the project's `curveball()` runs them, seeds are
  `random.Random(1000 + r)` with Leiden seed 7 + r, checkpoints run 0.25–200 trades per game, and the reference is
  the 200 checkpoint. It takes `--build` and `--pairs dataset:g:s`, and reads each pair's settings from the Build's
  configured Parameter Selection defaults. One statistic is new: Q at the pair's observed Selected Resolution γ_obs
  (`q_obs`), the γ of the fixed-γ arm, read from the stored validation.
- `results_100.json` / `results_100.md`: the run as the ticket specified it, 100 chains per pair (46 s on 12 workers).
  This run predates the γ_obs lookup fix, so puzzle 12/2 has no `q_obs` in it.
- `results_400.json` / `results_400.md`: a confirmation with 400 chains per pair, r = 0…399 (153 s). It was added
  because the 100-chain run flagged 3 pairs, and its noise (SE ≈ 0.07 SD) tells drift from chance.

Rerun on a new Build (about 3 min):

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/08-mixing-check/mixing_check.py \
        --build builds/<run>/<build> --chains 400 --out <dir>/results_400.json \
        --pairs rpg:7:5 puzzle:12:2 puzzle:14:2 puzzle:11:5 overall:12:2 overall:17:2 strategy:14:2 simulation:14:5

## Rule

Set before the run, as in Research 02:
- **Within noise:** |z| ≤ 0.3, where z is (mean at T − reference mean) / reference SD. For memory, the slope must be
  at most floor + 2 SE.
- **Memory floor:** at a mixed T the slope is not 0. It is Σ var(reference mean) / Σ x², because both axes subtract
  the same reference mean. This is Research 02's "noise floor ≈ 0.005".
- **Plateau:** the first checkpoint at which every statistic is within noise, with no later move beyond 3 SE.

## Results

| Pair | Tags | 100 chains: within noise from T = | 400 chains: max \|z\| at T = 5 (statistic) | 400: max \|z\| at T = 10 | 400: memory at T = 10 / max at T ≥ 20 | Perturbation share at T = 10 (reference) |
|---|---|---|---|---|---|---|
| rpg 7/5 | 71 | 10 (q_1 3 SE at 20, 50) | 0.65 (perturbation) | 0.12 | −0.000 / 0.001 | 0.695 (0.695 ± 0.009) |
| puzzle 12/2 | 42 | 10 | 0.49 (perturbation) | 0.09 | 0.000 / 0.001 | 0.677 (0.678 ± 0.011) |
| puzzle 14/2 | 31 | 10 | 0.51 (perturbation) | 0.09 | 0.001 / 0.003 | 0.643 (0.644 ± 0.012) |
| puzzle 11/5 | 43 | 100 (2–3 SE wobbles) | 0.45 (perturbation) | 0.12 | −0.000 / 0.002 | 0.681 (0.681 ± 0.012) |
| overall 12/2 | 43 | 10 | 0.58 (perturbation) | 0.08 | 0.002 / 0.001 | 0.633 (0.634 ± 0.010) |
| overall 17/2 | 29 | 10 | 0.58 (perturbation) | 0.19 | 0.004 / 0.003 | 0.581 (0.581 ± 0.011) |
| strategy 14/2 | 39 | 50 (c_score 0.41 at 10) | 0.68 (perturbation) | 0.12 | 0.004 / 0.004 | 0.656 (0.657 ± 0.011) |
| simulation 14/5 | 38 | 10 | 0.54 (perturbation) | 0.14 | 0.001 / 0.001 | 0.623 (0.623 ± 0.010) |

- **The 100-chain flags were noise.** Under 400 chains:
  - rpg 7/5's later q_1 offsets shrink from −0.43/−0.46 to −0.13/−0.16;
  - strategy 14/2's c_score at T = 10 falls from 0.41 to 0.12;
  - puzzle 11/5 is within noise from T = 10.

  At 100 chains every later checkpoint is compared with the same single reference mean, so one noisy reference moves
  them all the same way.
- **Two 400-chain flags are a band artefact.** At 400 chains, overall 17/2 and strategy 14/2 miss the strict rule
  only on memory at T = 10, by 0.0001 and 0.0003. Strategy 14/2 also misses it at T = 50, where the chain is certainly
  mixed. The floor + 2 SE band treats tag pairs as independent, but pairs that share a tag are correlated, so the
  band is too tight. At T = 10, memory is within 0.001 of its value at T = 20–100 at every pair.
- **T = 5 is not yet mixed.** At T = 5 the perturbation share is still 0.45–0.68 SD below the reference at every
  pair, which is 6–10 SE at 400 chains. Every other statistic is within noise there, and memory is 0.006–0.008.
- **T = 10 is mixed at every pair.** Every statistic is within 0.19 SD of the reference, and memory is at most
  0.0045. Q at γ_obs is within 0.16 SD.
- **This agrees with Research 02.** Its 5 grid cases gave "within about 0.8 SD by 5, within noise at 10". The memory
  decay is the same: 0.78 → 0.37 → 0.13 → 0.05 → 0.008 at T = 0.25, 1, 2, 3, 5, about a factor of e per trade
  per game.

**Conclusion.** Every validated pair has plateaued by `TRADES_PER_GAME` = 10. The margin is the gap between the 5 and
10 checkpoints: at most 2×, as Research 02 put it, and nothing in between was measured.

Caveat, as in Research 02: these are first- and pair-moment diagnostics. They cannot prove mixing in total variation.
