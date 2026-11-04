# 10 Domain-width sensitivity to the scan step

Ticket: [Domain-width sensitivity to the scan step](../../issues/10-scan-step-width-sensitivity.md). Run 2026-11-04 on
Build `20261008T221504Z-7a23ae9f` (the Build of 2026-10-08).

## Files

- `scan_step.py`: the rerunnable script. At each validated pair it rescans the observed network and all 100 nulls, rebuilt from the
  stored stream-4 seeds, at γ steps 0.05, 0.025 and 0.01. It uses the app's own scan, CHAMP and Selected Partition rule.
  The 0.05 run is the determinism check. It takes `--build`, `--pairs dataset:g:s` and `--steps`.
- `results.json` / `results.md`: the run and its per-pair tables.
- `run.log`: the run's stdout.

Rerun on a new Build:

    .venv/Scripts/python.exe .scratch/validation-review/prototypes/10-scan-step/scan_step.py \
        --build builds/<run>/<build> \
        --pairs rpg:7:5 puzzle:12:2 puzzle:14:2 puzzle:11:5 overall:12:2 overall:17:2 strategy:14:2 simulation:14:5

## Rule

This was set before the full run (the 3-null timing test only checked the script). A pair's width verdict **moves materially** when any of these holds
at step 0.025 or 0.01, compared with 0.05:

- the observed Selected Partition changes;
- the observed width falls on the other side of the null median;
- the share k/K of nulls the observed is wider than moves by 0.10 or more.

Under this rule, a move at any pair opens the follow-up ticket on the default `gamma_step`.

## Notes on the method

- **0.025 is uneven.** `champ.scan_gammas` rounds every γ to 2 decimals, so step 0.025 scans 0, 0.03, 0.05, 0.08,
  0.10, …, with gaps of 0.02 and 0.03. That is what `gamma_step = 0.025` would run in the app, so it is kept.
- **γ_end moves with the step.** CHAMP's range ends at the last scan γ, ⌈γ_max(n_e)/step⌉ · step. A finer step can
  end it slightly lower, which narrows only a domain clipped at the top.
- **The exact-γ_obs runs are absent.** The Leiden runs at exactly γ_obs from
  [Does the fixed-γ arm optimise at the observed resolution?](../../issues/03-fixed-gamma-arm.md) are not implemented.
  The Q count in `results.md` is the envelope-only figure at each step's own γ_obs, a by-product only.
- **puzzle 14/2 has two stored validations**, at min_multi_tag_clusters 2 and 3. They share the observed network and
  the null seeds, so each network is scanned once and CHAMP runs for both.

## Result

Full tables are in `results.md`; the summary is in the ticket's Answer.
- **The 0.05 rerun reproduces the stored values:** all 900 stored null widths and all 9 observed partitions.
- **The observed Selected Partition never changes**, and the Q count never moves.
- **Null median widths fall by 3–30%**, so k/K moves by −0.01 to +0.11.
- **The rule triggers at puzzle 11/5:** 50 → 61 of 100 at step 0.01.
