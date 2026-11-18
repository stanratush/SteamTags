# 18: Cluster Comparison mode: shared settings, dataset table and pair list

**What to build:** the fourth app mode, opened from the mode control or `?mode=comparison`. The header holds the shared settings and the `comparison_id`; the sidebar lists the Build's Top-N Datasets with their sources and the dataset pairs ranked by ARI. On first open every dataset is included, each on its pick, and the top pair is chosen. The diagram and match detail are placeholders filled by issues 19 and 20.

**Blocked by:** 15, 16, 17

**Status:** done

Spec: [Cluster Comparison spec](../spec.md): "Shared settings", "Compute and caching", "The Cluster Comparison mode" (Header, Sidebar, Naming and colour, Narrow widths, the fewer-than-two empty state), "Moving between modes" (`MODES`). Prototype: [index.html](../prototypes/06-look-of-the-mode/index.html) `?variant=B`. Decisions: tickets [06](06-look-of-the-mode.md), [12](12-compute-and-caching.md), [13](13-moving-between-modes.md).

- [x] `MODES` gains `"comparison"`; the mode is one more block of the one page (`arrange`) and its components live in `app/cc_view.py`.
- [x] **Header:** one row of shared settings (Clustering Weight, algorithm, Minimum Months Filter, hidden Genre Tags as `ps-s-genre`'s chip checklist, removed Tags), starting from the Parameter Selection settings, never the Workbench's; no defining-Tag control, no seed control. The `comparison_id`. Space for Export CSV (issue 23).
- [x] **Datasets table:** one row per Top-N Dataset: include checkbox, name in the dataset's colour, g, s and γ shown, the source line (four forms, by Threshold Pair, never "cell"; the "10 scan seeds" tooltip on the first two), and "Seed-Noise Floor · NA" with each label's tooltip.
- [x] **Dataset pairs:** every pair of included datasets ranked by ARI (comparable Tags), highest first: ARI with a small bar, the Comparable Tags count and both shares, games in common. Clicking a row chooses the pair.
- [x] **Each dataset has its own colour**, on its name everywhere; a Cluster alone is written with its dataset ("Overall C3").
- [x] **Two server-side LRU memos**, small like `STATE_TABLES`: one resolved partition per dataset; every pair's results keyed by `comparison_id`. Changing which datasets are included reuses the others' entries.
- [x] **While computing**, the previous view dims under one loading overlay for the whole mode.
- [x] Empty state "Include at least two datasets to compare" for the pairs list and the main column.
- [x] **Narrow widths:** the sidebar collapses above the main column as the Workbench's pill bar does.
- [x] Every new string has its bg entry; every label's tooltip comes from `help.py`.
- [x] Tests (`tests/test_app.py` style, `dash_http` helpers): the mode renders on a Build with an empty cache (every dataset `no_run`) and on a pre-filled cache fixture (datasets on their picks); include/exclude updates the pairs list and the `comparison_id`; the top pair is chosen on first open; the fewer-than-two empty state; five datasets resolve in under about 5 s cold on the full Build (skipped when absent).

## Comments

- 2026-11-18, implementation: `app/cc_view.py` (memos, `resolve_all`, `render`, `mode_layout`), `layout.py` (`MODES`, the fourth mode option, `root_class` "workbench comparison"), `callbacks.py` (`cc_render` over the whole mode with `running` on the overlay, `cc_pick_pair`), an `app.css` section, catalogue area `cc_view`. The sidebar is a Controls column of two sections built as pills, so at medium and narrow widths it becomes the Workbench's pill bar (the root keeps the workbench class). Checked live at 800 and 1400 px in English and Bulgarian on Build 20261109T064256Z-493c5375 (Overall on its pick g 16 · s 10, the others with no run): pair click, language switch, no console errors.
- Memo (a) is keyed beyond the spec's list by the Pair Constraints (they fix a pick) and the run's manifest time (a run that finishes shows on the next resolve). Memo (b) is keyed by the `comparison_id` and the partitions themselves, since a finished run can change a dataset's partition without changing its values. Every dataset is resolved whether included or not (its row shows its source), so an include change reuses every partition and only matches again.
- The `cc-shown` store (the shown `comparison_id` and pair) is written for issues 19 and 23.
- The cold budget is tested at the resolver (`tests/test_comparison_real_build.py`: five picks cold in about 2 s); matching all pairs takes milliseconds.
- Code review, fixed: the overlay's dimming rule now covers `#cc-busy`; the scan-seeds note is keyboard-reachable; the pairs pill colours the dataset names; names avoid the glossary's "comparison (unqualified)" and "view". Left: the header's Hidden Genre Tags and Removed tags share the `comparison.shared_settings` help entry; `_pill` and `_static_help` repeat ps_view's with a different id prefix; "ARI", "g", "s", "γ" and `comparison_id` are shown untranslated, as ps_view shows "Q", "γ̂" and "CHAMP".
