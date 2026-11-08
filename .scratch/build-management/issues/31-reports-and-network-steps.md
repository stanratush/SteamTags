# 31: Reports, Network steps and grid warnings

**What to build:** the Reports and analysis step (Content Flags, Genre Tags, the genre-kind map, `analysis.toml`, `resolution_sweep`) and the Network defaults step (`network.toml`, including the Parameter Selection settings and Pair Constraints). It also adds the per-dataset grid-scaling warnings, the no-pairs refusal, and Network State slider bounds raised to fit the Build's own settings.

**Blocked by:** 29

**Status:** done

Spec: [Build management spec](../spec.md): "The Build menu" (steps 4 and 5), "Datasets, List Size and Tag Depth" (grid and defaults). Decision ticket: [grid scaling](11-grid-and-defaults-scaling.md).

- [x] Reports and analysis: Content Flags (the same editor shape as rules, without descriptor ids or rank limits), Genre Tags, the genre-kind map (Steam only), `max_itemset_size`, `min_support`, `release_month_check` (Steam only), `causal_words`, `resolution_sweep`.
- [x] Network defaults: every `network.toml` key, with the `[parameter_selection]` Selection Settings and Pair Constraints, and today's validation.
- [x] Warnings per dataset, naming it and its N, shown on the Network step and in Review (never a refusal):
  - the grid's largest g > N;
  - the default g or s > N;
  - `min_support` > N.
- [x] A grid with no pairs (s_low > g_high) marks the step red and blocks Build.
- [x] The Workbench and Parameter Selection sliders keep 1–40 (g) and 1–30 (s), raised only to the Build's largest configured value (its network default or the top of its grid range).
- [x] bg entries for every warning and string.
- [x] Tests:
  - Each warning appears for a draft with Overall List Size 10, and saving stays allowed.
  - The no-pairs grid blocks Build.
  - A Build with `g_range` up to 50 gets a g slider up to 50.

## Comments

## Implementation note

Reports and analysis and Network defaults edit `analysis`/`reports`/`network` (Steam-only parts hidden for an Import). `preview.grid_warnings` lists per-dataset warnings naming the dataset and its N (largest g, default g/s, min_support above N). They never refuse. A grid with no pairs is a `draft_problems` problem on the Network step: it marks the step red, blocks Build, and replaces the config layer's untranslated message. `layout.slider_tops(ctx)` keeps 40/30 and rises to the Build's largest configured g/s. Tests: warnings for List Size 10 while saving stays allowed, the no-pairs grid blocks Build, and `slider_tops` with g_range up to 50.

These steps are edited as TOML text, with the same validation as the Build. An Import's draft hides `release_month_check` (it keeps the value), and the Content Flags box is here (issue 30).
