# 24: Full-Build acceptance check

**What to build:** a live check of the finished mode on the full Build, in a browser, at every width and in both languages, against the spec's numbers and time budget. Fixes found here go in this ticket or reopen the issue they belong to.

**Blocked by:** 19, 20, 21, 22, 23

**Status:** ready-for-human

Spec: [Cluster Comparison spec](../spec.md): "Goal", "Facts this spec rests on", "Compute and caching" (budget), "Narrow widths".

- [ ] On the full Build `20261005T062558Z-full/20261008T221504Z-7a23ae9f` with its Parameter Selection runs visible (rerun if the 64-digit cache folders still read as "not run"): every dataset on its pick, 10 pairs, 103 Cluster Matches in the export, the pairs ranked by ARI from Strategy × Simulation (0.53) down.
- [x] The Goal's five steps work end to end: include datasets, choose a pair, read the diagram, open a match with its games, export.
- [x] Five datasets resolve cold in under about 5 s; a minimum, pair, match or ⇄ change is immediate.
- [ ] Checked in headless Chrome at wide, medium and narrow widths (sidebar as pill bar, diagram scrolling vertically) and in English and Bulgarian (no untranslated string, every tooltip present).
- [x] "Use in Cluster Comparison" and the row link round-trip with Parameter Selection.
- [x] Findings and screenshots noted under Comments.


## Comments

**2026-11-18, acceptance run (Claude).**

- **Numbers on `20261005T062558Z-full/20261008T221504Z-7a23ae9f`.** Its Parameter Selection cache still has 64-digit folder names, so the app reads its runs as "not run". The runs were **not rerun**: the check read them with `ps_cache.NAME_LENGTH = 64` set in memory, as the prototypes do, through `cc_view.resolve_all` and `cc_export.export_comparison`. Every dataset on its pick: Overall 17·2 (29 Tags / 4 Multi-Tag Clusters, floor 1.00), Puzzle 14·2 (31 / 4, 0.52), RPG 7·5 (71 / 15, 0.80), Strategy 14·2 (39 / 3, 1.00), Simulation 14·5 (38 / 3, 1.00). 10 pairs, 103 Cluster Matches in `matches.csv`, 48 at or above 0.10, median 0.09, maximum 0.58, 116 rows in `cluster_flags.csv`. Pairs by ARI: Strategy × Simulation 0.53, Overall × Strategy 0.32, Puzzle × Strategy 0.30, Overall × Simulation 0.27, Overall × Puzzle 0.23, Overall × RPG 0.17, RPG × Simulation 0.11, RPG × Strategy 0.10, Puzzle × RPG 0.07, Puzzle × Simulation 0.07. All match the spec's "Facts".
- **Time.** Five datasets cold: 2.65 s (budget about 5 s); a second resolve from the memos: 0.03 s. The export of the whole comparison: about 1.2 s cold on the 493c5375 Build. One oddity outside this feature: a Python process that has resolved this Build can take minutes to exit after printing (interpreter teardown); `os._exit` avoids it in scripts. Not seen in the app or the tests.
- **In the browser** (the app's built-in browser, on `20261005T062558Z-full/20261109T064256Z-493c5375`, whose Overall run is readable): the Goal's five steps end to end (include, choose a pair, read the diagram, open a match with its games, Export CSV enabled with no server error); ⇄, a box click, show weaker and a curve click; a row edit setting Puzzle by hand and a weight change resetting it with the notice; the row link opening Parameter Selection on Overall at its ★ cell, and Use in Cluster Comparison putting g 14 · s 10 into the comparison and switching back. Wide, medium (768) and narrow (375) widths: the sidebar is the pill bar at medium and narrow, the diagram keeps two columns and scrolls with the main column. Bulgarian: every string of the mode, the diagram, the badges and the match detail is translated; the slider's marks now follow the language's decimal comma (fixed here).
- **Fixes made here** (all in `tests/test_cc_app.py`; the spec's lines for the row link, Use in Cluster Comparison and Export CSV are amended to match):
  - Minimum Jaccard slider marks follow the language's decimal comma.
  - The link diagram's ResizeObserver watches only the diagram on screen (it disconnects the previous grid).
  - The row link highlights the dataset's cell only while Parameter Selection's settings are the comparison's; otherwise the same g and s would name another run's cell.
  - Use in Cluster Comparison on the ★ cell stores source `pick`, so the dataset follows the Pair Constraints like any pick (other cells stay `cell`).
  - Changing only g or s of a dataset to a by-hand pair keeps its γ unrounded, not its two-decimal display.
  - Export CSV is disabled whenever there is no comparison (fewer than two included datasets), not only while computing.
- **Not done (why this ticket is ready-for-human):** rerunning the five Automatic Parameter Selection runs takes hours and is yours to start; until then the two unticked items stay open. The check used the built-in browser, not headless Chrome, and the acceptance Build's runs were not rerun, so that Build's runs still show as "not run" in the app (a fact of its cache, per the spec).
