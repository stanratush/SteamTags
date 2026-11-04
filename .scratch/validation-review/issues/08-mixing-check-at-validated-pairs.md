# Mixing check at the validated pairs
Type: task
Status: resolved
Blocked by:

## Question

Does the Curveball shuffle mix by `TRADES_PER_GAME` = 10 at the pairs that were actually validated? [Validation methods](../../auto-parameter-selection/research/02-validation-methods.md) checked only 5 grid cases, and none of them was a chosen pair. Decided in [Which sensitivity checks run, and as one-off studies or in-app?](05-sensitivity-checks-and-scope.md).

Do (AFK):
- **Rewrite the script:** `mixing_check.py` is lost. Rewrite it from Research 02's description into `prototypes/08-mixing-check/`, taking the Build path and the pairs as arguments.
- **Run Research 02's design:**
  - 100 chains at 0.25–200 trades per game;
  - the same statistics: perturbation share, C-score, edges, Q, Multi-Tag Clusters, memory slope;
  - the same seeding scheme.
- **Where:** Build `20261008T221504Z-7a23ae9f`, at the 8 distinct pairs of the 9 stored validations: rpg 7/5, puzzle 12/2, 14/2 and 11/5, overall 12/2 and 17/2, strategy 14/2, simulation 14/5.
- **Budget:** under 1 h of compute.

Record:
- **Per pair:** the trades per game at which every statistic is within noise.
- **The guide's quote:** one sentence, dated "on the Build of 2026-10-08".
- **A follow-up if needed:** if any pair has not plateaued by 10 trades per game, open a follow-up ticket on `TRADES_PER_GAME`. That would be a records change.

## Answer

Resolved 2026-11-04 (AFK). Script, raw results and the full tables are in [prototypes/08-mixing-check](../prototypes/08-mixing-check/README.md).

**What was done.**
- **Script:** `mixing_check.py` was rewritten to Research 02 §A.4's design. Chains start from the observed game × visible-tag table and run on the project's `curveball()`. Seeds are `random.Random(1000 + r)`, with Leiden seed 7 + r. Checkpoints run 0.25–200 trades per game, and the 200 checkpoint is the reference.
- **Statistics:** the same six (perturbation share, C-score, edges, and Q and Multi-Tag Clusters at γ = 1, plus the memory slope). One was added: Q at the pair's observed Selected Resolution, the fixed-γ arm's γ.
- **Inputs:** the Build path and `dataset:g:s` pairs are arguments, and settings come from the Build's configured Parameter Selection defaults.
- **Runs:** 100 chains per pair, as specified (46 s on 12 workers), then a 400-chain confirmation (153 s), because the 100-chain run flagged 3 pairs. Total under 4 min, well inside the 1 h budget.

**Per pair: the trades per game at which every statistic is within noise.** The checkpoint grid is 0.25, 0.5, 1, 2, 3, 5, 10, 20, 50, 100.

| Pair | Within noise from | At T = 5 | At T = 10 (400 chains) |
|---|---|---|---|
| rpg 7/5 | **10** | perturbation share 0.65 SD low | max \|z\| 0.12 |
| puzzle 12/2 | **10** | 0.49 SD low | 0.09 |
| puzzle 14/2 | **10** | 0.51 SD low | 0.09 |
| puzzle 11/5 | **10** | 0.45 SD low | 0.12 |
| overall 12/2 | **10** | 0.58 SD low | 0.08 |
| overall 17/2 | **10** | 0.58 SD low | 0.19 |
| strategy 14/2 | **10** | 0.68 SD low | 0.12 |
| simulation 14/5 | **10** | 0.54 SD low | 0.14 |

- **T = 5 falls short on one statistic.** At T = 5 every statistic except the perturbation share is within noise, and memory is 0.006–0.008.
- **T = 10 is mixed everywhere.** Memory is ≤ 0.0045 at every pair and within 0.001 of its value at T = 20–100. The perturbation share plateaus at 0.58–0.70, depending on the pair.
- **The three 100-chain flags were noise.** They were rpg 7/5 (q_1 −0.43 SD at 20 and 50), puzzle 11/5 (2–3 SE wobbles) and strategy 14/2 (C-score +0.41 SD at 10). All three vanish at 400 chains.
- **Two 400-chain misses are a band artefact.** Overall 17/2 and strategy 14/2 miss the strict memory band at T = 10 by 0.0001–0.0003. Strategy also misses it at T = 50, where the chain is certainly mixed, so the band (built as if tag pairs were independent) is too tight. The README has the detail.
- **Research 02 holds at the chosen pairs.** Its finding was "within about 0.8 SD by 5, within noise at 10". The margin of `TRADES_PER_GAME` = 10 over the plateau is at most 2×, and nothing between 5 and 10 was measured.

**The guide's quote (one sentence):**

> On the Build of 2026-10-08, at each of the 8 validated Threshold Pairs, 400 shuffle chains per pair matched by 10 trades per game every tracked statistic of chains run to 200 (perturbation share, C-score, edge count, Q and Multi-Tag Clusters within 0.2 SD, and under 0.5% of the observed table's excess co-occurrence left), while at 5 the perturbation share still lagged by about 0.5–0.7 SD.

**No follow-up.** Every pair has plateaued by 10 trades per game, so `TRADES_PER_GAME` stays at 10 and the records do not change on this account.

**Facts for later tickets:**
- **Perturbation Share:** at T = 10 it is 0.58–0.70 per pair (reference mean ± SD in the README). This is the range the in-app records should show on this Build.
- **The new Build:** the rerun command (400 chains, about 3 min) is in the README.
- **Settings lookup:** the stored validations of puzzle 12/2 and of one puzzle 14/2 were made with a different `min_multi_tag_clusters` (5 and 2) from today's default (3). The network is the same, so the script matches stored validations on network settings only.
