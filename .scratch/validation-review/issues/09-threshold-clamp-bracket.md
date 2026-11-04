# Threshold clamp bracket at s = 2
Type: task
Status: resolved
Blocked by:

## Question

How much does the s′ = max(2, ⌊0.8 s⌋) clamp move Subsample Stability at s = 2? A proportional threshold (1.6) is impossible there, and the clamped s′ = 2 is stricter than proportional. Decided in [Which sensitivity checks run, and as one-off studies or in-app?](05-sensitivity-checks-and-scope.md).

Do (AFK):
- **Script:** goes in `prototypes/09-clamp-bracket/` and takes the Build path and the pairs as arguments.
- **Where:** Build `20261008T221504Z-7a23ae9f`, at the 5 validated s = 2 pairs: puzzle 12/2 and 14/2, overall 12/2 and 17/2, strategy 14/2.
- **What to run:** Subsample Stability at m = 80, with s′ = 1 next to s′ = 2, using the stored subsample seeds so the two are paired. Both arms: re-selected and at resolution.
- **Budget:** about 10 min of compute.

Record:
- **Per Multi-Tag Cluster, under both s′:**
  - mean Hennig's Jaccard;
  - mean Whole-Cluster Jaccard;
  - the dissolution and recovery frequencies;
  - the **Dissolved in most subsamples** label, by the rules of [Which per-Cluster figures and verdict replace "Dissolved"?](02-cluster-figures-and-verdict.md).
- **The guide's quote:** "the clamp moves k of N labels", dated "on the Build of 2026-10-08".
- **The app doesn't change**, whatever the result.

## Answer

Done 2026-11-04 (AFK) on Build `20261008T221504Z-7a23ae9f`. Script, results and full tables: [prototypes/09-clamp-bracket/](../prototypes/09-clamp-bracket/README.md).

**What ran**
- Every stored validation at the 5 s = 2 pairs ran: puzzle 12/2, puzzle 14/2 (two runs, at min multi 2 and 3), overall 12/2, overall 17/2 and strategy 14/2.
- Each run's 100 subsamples ran at s′ = 2 and at s′ = 1, from the stored stream-5 seeds, so the draws and g′ are paired. Both arms were scored.
- The figures and statuses of [How does tag loss count in Cluster recovery?](01-tag-loss-in-cluster-recovery.md) and [Which per-Cluster figures and verdict replace "Dissolved"?](02-cluster-figures-and-verdict.md) were scored for every Cluster.
- It made 1200 subsample runs in 194 s.
- **Determinism:** the s′ = 2 rerun reproduces all 4952 stored Hennig's Jaccard values exactly.
- **The bracket is real:** s′ = 1 adds 8–22% edges to the median subsample network.

**Result**
- **The clamp moves 0 of 50 Dissolved-in-most-subsamples labels** (25 Cluster-runs × 2 arms):
  - re-selected: 8 labelled under both s′;
  - at resolution: 7 labelled under both s′.
- No Cluster is Not assessable or rarely assessable under either s′.
- **4 of 50 borderline marks move:** puzzle 12/2 re-selected C4 off and C5 on; puzzle 12/2 at resolution C5 off; overall 12/2 at resolution C4 on.
- **Mean Hennig's Jaccard** changes by a median of +0.003 (re-selected) and +0.008 (at resolution), and by at most 0.070: overall 12/2 C4, a 3-tag Cluster, still dissolved. Whole-Cluster Jaccard moves the same way.
- The looser s′ does not lift recovery uniformly: about as many Clusters drop as rise.
- **The closest label:** puzzle 12/2 C3, re-selected, dissolved in 52/92 subsamples at s′ = 2 and 45/87 at s′ = 1. It is borderline under both.

**Guide quote** (for the guide's sentence on the s′ clamp's direction, decided in [Which sensitivity checks run, and as one-off studies or in-app?](05-sensitivity-checks-and-scope.md)): "On the Build of 2026-10-08, rerunning the s = 2 validations with s′ = 1 instead of the clamped s′ = 2 moves 0 of 50 Dissolved-in-most-subsamples labels (25 Multi-Tag Clusters × 2 arms) and changes a mean Hennig's Jaccard by at most 0.07."

**The app doesn't change.** There is no follow-up ticket. The spec lists the rerun on the new Build with the other two studies. The script reads this Build's cache at full-length key hashes, because the cache predates 9aa40e6. It handles both lengths.
