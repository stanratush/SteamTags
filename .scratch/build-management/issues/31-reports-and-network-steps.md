# 31: Reports, Network steps and grid warnings

**What to build:** the Reports and analysis step (Content Flags, Genre Tags, the genre-kind map, `analysis.toml`, `resolution_sweep`) and the Network defaults step (`network.toml`, including the Parameter Selection settings and Pair Constraints). It also adds the per-dataset grid-scaling warnings, the no-pairs refusal, and Network State slider bounds raised to fit the Build's own settings.

**Blocked by:** 29

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "The Build menu" (steps 4 and 5), "Datasets, List Size and Tag Depth" (grid and defaults). Decision ticket: [grid scaling](11-grid-and-defaults-scaling.md).

- [ ] Reports and analysis: Content Flags (the same editor shape as rules, without descriptor ids or rank limits), Genre Tags, the genre-kind map (Steam only), `max_itemset_size`, `min_support`, `release_month_check` (Steam only), `causal_words`, `resolution_sweep`.
- [ ] Network defaults: every `network.toml` key, with the `[parameter_selection]` Selection Settings and Pair Constraints, and today's validation.
- [ ] Warnings per dataset, naming it and its N, shown on the Network step and in Review (never a refusal):
  - the grid's largest g > N;
  - the default g or s > N;
  - `min_support` > N.
- [ ] A grid with no pairs (s_low > g_high) marks the step red and blocks Build.
- [ ] The Workbench and Parameter Selection sliders keep 1–40 (g) and 1–30 (s), raised only to the Build's largest configured value (its network default or the top of its grid range).
- [ ] bg entries for every warning and string.
- [ ] Tests:
  - Each warning appears for a draft with Overall List Size 10, and saving stays allowed.
  - The no-pairs grid blocks Build.
  - A Build with `g_range` up to 50 gets a g slider up to 50.

## Comments
