# 27: Heatmap, "Why this pair" and the Pair Constraints panel

**What to build:** the main column's metric picker, the g × s heatmap with its marks and reason letters, and the "Why this pair" card. The Controls column gets the Pair Constraints panel, which re-chooses from the cache on Confirm.

**Blocked by:** 26

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "The Parameter Selection mode" (Controls column item 2, Main column items 2–4, States), "Choosing the pair", "The selection explanation".

- [x] **Metric picker:** Neighbour Agreement, Information Retention, isolated share, Multi-Tag Clusters, Seed-Noise Floor, Q. Q shows the descriptive caption, a grey scale and no best marker. The choice persists across dataset switches.
- [x] **Heatmap:**
  - g × s for the current dataset, with its key;
  - ★ on the chosen pair, orange outlines on the near-best set, a dark outline on the inspected pair;
  - one letter per failing reason (P A N R I L K), spelled out in the key;
  - hover text with the value, NA, tags, Multi-Tag Clusters, and "✓ qualifies" or the reasons in words;
  - a click sets the inspected pair;
  - an unfinished grid shows computed cells, grey pending cells, NA only where all neighbours are computed, and no ★ or outlines.
- [x] **"Why this pair"** renders `selection_text.explanation`, or, under `no_qualifying_pair`, the message and the exclusion table. It shows nothing for an unfinished grid.
- [x] **Pair Constraints panel:**
  - the five constraints and the tolerance, with defaults beside them and "changed" markers;
  - an empty maximum means off, and the maximum must be ≥ the active minimum Multi-Tag Clusters;
  - "Apply to: All five datasets | ‹dataset› only";
  - Confirm, disabled until something changes, with "Unconfirmed changes" shown meanwhile;
  - Reset to defaults;
  - the constraints label below.

  Confirm recomputes `choose` from the cache without a job, and updates the strip, heatmap and explanation. Per-dataset overrides are kept per dataset for the session.
- [x] Help keys on every metric, field and reason letter.
- [x] Tests:
  - On a pre-filled cache fixture: the heatmap figure has one cell per pair with the right letters, ★ and outlines.
  - Confirm with a tighter retention moves the pick and labels "Custom constraints: …".
  - A per-dataset override affects only that dataset and sets its strip marker.
  - Reset restores the defaults.
  - Constraints that exclude everything show the no-qualifying message with correct counts.
  - No background job starts on Confirm.

## Comments

- 2026-10-27, implementation: Implemented in `app/ps_view.py` (`metric_picker`, `heatmap`, `heatmap_key`, `why`) and the constraint callbacks in `app/callbacks.py`.
