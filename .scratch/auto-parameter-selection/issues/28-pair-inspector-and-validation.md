# 28: Pair Inspector, validation card and Validate this pair

**What to build:** the right-hand Pair Inspector for the inspected pair (badges, metrics, neighbour links, CHAMP plot, Clusters, compact validation), the main column's validation card, and the "Validate this pair" background job. Apply's button and line are laid out here but wired in issue 30. The Clusters' Remove action is wired in issue 29.

**Blocked by:** 27

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Pair Inspector (right)", "Main column" item 5, "Validation block wording", "Which pair, and when", "Jobs, progress and ETA" (Validate this pair).

- [x] Title and badges: qualifies or each reason, plus `clipped_high`, `not_representable` and `not_reproduced`. By default the Inspector shows the dataset's ★ pair until a cell is clicked.
- [x] The Apply button and the Workbench γ/seed line beneath it, in their final form. With no Selected Partition the button is disabled with the reason code. A click does nothing until issue 30.
- [x] Metrics:
  - NA with its neighbour counts, Retention, isolated share, LCC share, Multi-Tag and One-Tag Clusters, the Seed-Noise Floor (minimum, mean, exact), hits, domain, Selected Resolution, and the scan range (0 to γ_end, n_e);
  - the descriptive group with its caption.

  Each label has its `selection.*` help.
- [x] Neighbour links table: direction, status, ARI, tag overlap, Edge Overlap (two decimals), identical-graph marker.
- [x] **CHAMP plot** (Plotly, the app's chart style):
  - each Admissible Partition's Q(γ) line and the envelope;
  - shaded domains, with Stable Partitions marked;
  - γ̂ markers with arrows to their map targets;
  - the Selected Resolution;
  - the x-axis from 0 to γ_end.

  It is for inspection only.
- [x] Clusters of the Selected Partition (labels as `label_clusters`), with a Remove control per tag (disabled until issue 29).
- [x] Compact validation: the two verdict tags and the median ARIs, or "Not validated" with **Validate this pair**.
- [x] **Validation card** in the main column: the chosen pair's `validation_block` with the per-Cluster table (arm, mean Jaccard, "≤ 0.5 in k of B*", retention share, absent, Dissolved) and both caveats; "Not validated" with the button; the custom-constraints note.
- [x] **Validate this pair** job:
  - a background callback over `ps_run.validate_pair`, offered on any pair with a Selected Partition in a complete grid (also under `no_qualifying_pair`);
  - exclusive with Run;
  - uses the loading panel;
  - Cancel discards it.
- [x] Tests:
  - The Inspector for a chosen pair, a non-qualifying pair and a pair without a Selected Partition.
  - The CHAMP figure has one line per Admissible Partition and the x-range [0, γ_end].
  - The links table has rows for in-grid links only.
  - A validation fixture renders the block and table, and "Dissolved" appears only for mean Jaccard ≤ 0.5.
  - The Validate job with a serial `map_fn` writes the validation file and updates the card.

## Comments

- 2026-10-27, implementation: Implemented in `app/ps_view.py` (`inspector`, `champ_figure`, `links_table`, `validation_card`) and the Validate job in `app/callbacks.py`. The mode re-renders from a `ps-running` flag and the progress store, not from the jobs' own outputs: Dash holds a callback whose input is a running job's output until the job ends.
