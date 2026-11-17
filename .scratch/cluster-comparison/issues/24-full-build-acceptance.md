# 24: Full-Build acceptance check

**What to build:** a live check of the finished mode on the full Build, in a browser, at every width and in both languages, against the spec's numbers and time budget. Fixes found here go in this ticket or reopen the issue they belong to.

**Blocked by:** 19, 20, 21, 22, 23

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "Goal", "Facts this spec rests on", "Compute and caching" (budget), "Narrow widths".

- [ ] On the full Build `20261005T062558Z-full/20261008T221504Z-7a23ae9f` with its Parameter Selection runs visible (rerun if the 64-digit cache folders still read as "not run"): every dataset on its pick, 10 pairs, 103 Cluster Matches in the export, the pairs ranked by ARI from Strategy × Simulation (0.53) down.
- [ ] The Goal's five steps work end to end: include datasets, choose a pair, read the diagram, open a match with its games, export.
- [ ] Five datasets resolve cold in under about 5 s; a minimum, pair, match or ⇄ change is immediate.
- [ ] Checked in headless Chrome at wide, medium and narrow widths (sidebar as pill bar, diagram scrolling vertically) and in English and Bulgarian (no untranslated string, every tooltip present).
- [ ] "Use in Cluster Comparison" and the row link round-trip with Parameter Selection.
- [ ] Findings and screenshots noted under Comments.
