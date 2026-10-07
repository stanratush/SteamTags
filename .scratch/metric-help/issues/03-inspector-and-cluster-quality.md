# 03: Inspector labels and the Cluster quality tab

**What to build:** every Inspector label (node, edge, cluster, Removal Sensitivity) and every Cluster quality box and sentence gets the two-layer help, with its guide entries written.

**Blocked by:** 01

**Status:** done

Spec: [Metric help spec](../spec.md): "Content rules", "Layer 1", "Layer 2".

- [x] Each `INSPECTOR_LABELS` label resolves to its guide entry through the Column Index. `label_tip` is replaced by the guide text plus "Column: `name`" on the last line.
- [x] `_kv` `dt`s carry `data-tip`, `data-help` and `tabindex="0"`, still as one HTML block per list.
- [x] Quality boxes (Q, Null-model excess, Coverage, Silhouette, Seed noise) use guide text with **Now:** lines (γ, R, K, null mean ± SD). `SILHOUETTE_TIP` and `ari_tip` are removed.
- [x] Each entry these reach has an In short block and `*Why it matters here.*`. That covers tag game count, degree, strength, per-tag silhouette, medoid score, Cluster Center, top-strength tag, within-cluster z, participation, edge weight, edge lift, Membership Stability, conductance, coverage, ARI and every Removal Sensitivity entry.
- [x] Test: every Inspector label and quality item resolves to an entry with an In short.
- [x] Checked in the browser: a node, an edge, a cluster and a Removal Sensitivity result.

## Comments

- 2026-10-07: Done. `help.py` gains `column_entry` (a label's entry is its first column's schema `guide_entry`), `column_line` ("Column: name (file)" or "Columns: a, b (file)") and `column_attrs`, plus the `quality.*` keys (the five boxes, and the two sentences, which open the `##` sections Clusters and partition quality and Stability). `view.label_help` replaces `label_tip`: each `_kv` `dt` carries `class="term"`, `tabindex`, `data-tip` and `data-help`, still one HTML block per list. The Inspector's table headers that are Inspector labels (connected tags: Shared games, Lift; cluster members: Games, Mean game-set distance, Membership Stability) carry the same. Quality boxes use the guide text with Now lines (γ and null mean ± SD from R for Q; Q − null mean and z for the excess; seed SD for the silhouette; K for seed noise); their "i" icon gave way to the dotted label. `SILHOUETTE_TIP`, `ari_tip` and `label_tip` are gone. `in_short_at` is cached per process. The tooltip styles the Column line like the Now line. Guide: 25 entries got an In short block and a `*Why it matters here.*` paragraph (the 23 the issue lists, plus the two `##` sections for the sentences); Coverage and Adjusted Rand index got "Shown in the app as" lines. After the two-axis review, nine texts were corrected against their entries' own definitions (within-z is in SDs, conductance's denominator, Cluster Center needs 3+ tags, the mechanical part of the removal deltas, the beyond-noise chance count), and wording rules were tightened (no rating words in layer 1, "Network State" not "state", "the most-played games" not "successful games" in the new text). Tests: every Inspector label resolves to an entry with In short and Why; `_kv` and table headers carry both layers and the Column line; quality boxes and sentences carry the right entries and Now lines. Checked in the browser: a node, an edge, a cluster and a single-tag Removal Sensitivity result (every label has help), hover and focus tooltips, Enter and click to the modal. Note: the earlier issue-01 entries still say "successful games"; issue 07's review can settle the phrase for the whole guide.
