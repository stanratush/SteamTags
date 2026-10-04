# 15: Removal Sensitivity method and Build table

**What to build:** The `network` package can say how much the clustering depends on each tag. It removes the tag hypothetically and reads the result two ways:
- **reclustered from scratch**: ΔQ, Δsilhouette, Δk, Δs, ARI, centers lost;
- **partition fixed**: ΔQ, Δsilhouette.

ARI is flagged only when it falls below the lowest seed ARI. Every Build writes the complete table per dataset, so the report can use it.

**Blocked by:** 13, 14

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Removal Sensitivity), "Export schemas" (`removal_sensitivity.csv`).

- [ ] A separate entry point over a Network State that never changes the state. Both readings are compared over the shared tag set.
- [ ] The reclustered reading is a cold restart with the main seed and the active algorithm / γ / weight. The fixed-partition reading keeps every other tag in its cluster.
- [ ] Every Δ is after − before. A silhouette moving between a value and n/a leaves the Δ empty, with the `*_after_status` set.
- [ ] `rc_ari_beyond_noise` = `rc_ari` < `seed_ari_min`, read from the standing Seed-Noise Floor (never recomputed). When `seed_ari_min` = 1, any removal that moves a tag is flagged. ΔQ and Δsilhouette are never flagged.
- [ ] `rc_centers_lost` lists current Cluster Centers other than v that are no longer centers.
- [ ] Run order: active strength desc, then `tag_id`. A run can be limited to one tag or stopped early, and a partial result is a prefix of the full one (tested). The progress callback and cancellation hooks are usable by a background job.
- [ ] `removal_sensitivity.csv` columns follow the spec exactly. A method-version string is exposed for cache keys.
- [ ] The Build writes the complete stacked `removal_sensitivity.csv` per dataset at the report's settings. `analysis.json` notes it.
- [ ] Hand-built tests: a bridge tag whose removal splits a cluster (low ARI, flagged), a peripheral tag (ARI 1), the n/a transition, and the Δ signs.
