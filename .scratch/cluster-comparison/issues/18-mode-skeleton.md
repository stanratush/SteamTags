# 18: Cluster Comparison mode: shared settings, dataset table and pair list

**What to build:** the fourth app mode, opened from the mode control or `?mode=comparison`. The header holds the shared settings and the `comparison_id`; the sidebar lists the Build's Top-N Datasets with their sources and the dataset pairs ranked by ARI. On first open every dataset is included, each on its pick, and the top pair is chosen. The diagram and match detail are placeholders filled by issues 19 and 20.

**Blocked by:** 15, 16, 17

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "Shared settings", "Compute and caching", "The Cluster Comparison mode" (Header, Sidebar, Naming and colour, Narrow widths, the fewer-than-two empty state), "Moving between modes" (`MODES`). Prototype: [index.html](../prototypes/06-look-of-the-mode/index.html) `?variant=B`. Decisions: tickets [06](06-look-of-the-mode.md), [12](12-compute-and-caching.md), [13](13-moving-between-modes.md).

- [ ] `MODES` gains `"comparison"`; the mode is one more block of the one page (`arrange`) and its components live in `app/cc_view.py`.
- [ ] **Header:** one row of shared settings (Clustering Weight, algorithm, Minimum Months Filter, hidden Genre Tags as `ps-s-genre`'s chip checklist, removed Tags), starting from the Parameter Selection settings, never the Workbench's; no defining-Tag control, no seed control. The `comparison_id`. Space for Export CSV (issue 23).
- [ ] **Datasets table:** one row per Top-N Dataset: include checkbox, name in the dataset's colour, g, s and γ shown, the source line (four forms, by Threshold Pair, never "cell"; the "10 scan seeds" tooltip on the first two), and "Seed-Noise Floor · NA" with each label's tooltip.
- [ ] **Dataset pairs:** every pair of included datasets ranked by ARI (comparable Tags), highest first: ARI with a small bar, the Comparable Tags count and both shares, games in common. Clicking a row chooses the pair.
- [ ] **Each dataset has its own colour**, on its name everywhere; a Cluster alone is written with its dataset ("Overall C3").
- [ ] **Two server-side LRU memos**, small like `STATE_TABLES`: one resolved partition per dataset; every pair's results keyed by `comparison_id`. Changing which datasets are included reuses the others' entries.
- [ ] **While computing**, the previous view dims under one loading overlay for the whole mode.
- [ ] Empty state "Include at least two datasets to compare" for the pairs list and the main column.
- [ ] **Narrow widths:** the sidebar collapses above the main column as the Workbench's pill bar does.
- [ ] Every new string has its bg entry; every label's tooltip comes from `help.py`.
- [ ] Tests (`tests/test_app.py` style, `dash_http` helpers): the mode renders on a Build with an empty cache (every dataset `no_run`) and on a pre-filled cache fixture (datasets on their picks); include/exclude updates the pairs list and the `comparison_id`; the top pair is chosen on first open; the fewer-than-two empty state; five datasets resolve in under about 5 s cold on the full Build (skipped when absent).
