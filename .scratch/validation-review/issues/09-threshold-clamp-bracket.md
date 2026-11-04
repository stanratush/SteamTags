# Threshold clamp bracket at s = 2
Type: task
Status: open
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
