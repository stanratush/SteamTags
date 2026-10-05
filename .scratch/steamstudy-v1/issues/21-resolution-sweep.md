# 21: Resolution Sweep

**What to build:** Every Build repeats each dataset's report clustering at a fixed grid of γ values (default 0.50–1.50), with everything else unchanged. It writes cluster counts, modularity, silhouette, ARI against the report's partition, and the Seed-Noise Floor at each γ, so the report can say how much the result depends on γ.

**Blocked by:** 14

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Feature analysis" (Resolution Sweep), "Export schemas".

- [x] The grid comes from config `resolution_sweep`. The config γ is added if missing, so the report's partition is always a row.
- [x] It runs at the report's settings (shared defaults, defining tag out, config algorithm, weight and main seed). Only γ varies, so the node set is identical across rows.
- [x] `resolution_sweep.csv` (sorted by dataset, then resolution): `dataset, resolution, n_multi_tag_clusters, n_one_tag_clusters, modularity, mean_silhouette, silhouette_status, ari_vs_report, seed_ari_min, seed_ari_mean`. The schema description says modularity is not comparable across rows.
- [x] No null model per γ, no centers, no per-tag rows. Not in the app.
- [x] `analysis.json` gains a Resolution Sweep summary: the grid, plus per-dataset ranges of cluster counts and `ari_vs_report`.
- [x] Tests: the config γ row has `ari_vs_report` = 1, and a grid without the config γ gets it added.

## Comments

- 2026-10-04 (agent): Implemented: network/sweep.py and analysis/resolution_sweep.csv (dataset order follows datasets.toml); analysis.json carries the grid and per-dataset ranges.
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
