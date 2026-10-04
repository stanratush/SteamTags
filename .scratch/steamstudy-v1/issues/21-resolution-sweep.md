# 21: Resolution Sweep

**What to build:** Every Build repeats each dataset's report clustering at a fixed grid of γ values (default 0.50–1.50), with everything else unchanged. It writes cluster counts, modularity, silhouette, ARI against the report's partition, and the Seed-Noise Floor at each γ, so the report can say how much the result depends on γ.

**Blocked by:** 14

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Feature analysis" (Resolution Sweep), "Export schemas".

- [ ] The grid comes from config `resolution_sweep`. The config γ is added if missing, so the report's partition is always a row.
- [ ] It runs at the report's settings (shared defaults, defining tag out, config algorithm, weight and main seed). Only γ varies, so the node set is identical across rows.
- [ ] `resolution_sweep.csv` (sorted by dataset, then resolution): `dataset, resolution, n_multi_tag_clusters, n_one_tag_clusters, modularity, mean_silhouette, silhouette_status, ari_vs_report, seed_ari_min, seed_ari_mean`. The schema description says modularity is not comparable across rows.
- [ ] No null model per γ, no centers, no per-tag rows. Not in the app.
- [ ] `analysis.json` gains a Resolution Sweep summary: the grid, plus per-dataset ranges of cluster counts and `ari_vs_report`.
- [ ] Tests: the config γ row has `ari_vs_report` = 1, and a grid without the config γ gets it added.
