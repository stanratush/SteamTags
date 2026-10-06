# 08: Summary row, Network State sentence and Cluster quality boxes

**What to build:** the key numbers sit large above the graph, with the Network State in one readable sentence. The Cluster quality tab becomes five boxes with tooltips. The long Q / null-model / noise sentences appear once, in that tab only.

**Blocked by:** 01, 02

**Status:** done

Spec: [App readability spec](../spec.md): "Summary row, Network State sentence and Cluster quality".

- [x] Summary row (Workbench), each value large with a muted label and a tooltip:
  - Games "N of 100";
  - Tags;
  - Links;
  - Clusters "k + s multi-tag + one-tag";
  - Q "0.17 · excess +0.11";
  - Silhouette "0.04 · descriptive", with the full qualifier in its tooltip.
- [x] Under it, the Network State sentence: dataset, Months filter, thresholds, hidden Genre Tags (count or names), removed tags, algorithm, weight, γ and seed. It ends with the `state_id`, which copies on click.
- [x] The quality and noise lines are removed from above the graph. The Cluster quality tab shows:
  1. Five boxes, each with a tooltip: Q (γ), Null-model excess (z, null mean ± SD), Coverage, Silhouette (descriptive), Seed noise (ARI min, mean).
  2. The two full sentences, once, in small muted text.
  3. The connections and replicate grids.
- [x] ARI is shown as numbers only, with the spec's tooltip. No bands, stable/unstable words or colours anywhere.
- [x] Tests:
  - The summary and the boxes show the values of `cluster_quality.csv` for the state.
  - The Q text never shows z without the excess and the null mean.
  - The quality sentence appears exactly once in the Workbench.

## Comments

**2026-10-06 (implemented):** `view.summary_row`, `view.state_sentence` and `view.quality_boxes` replace the two long lines above the graph (now the outputs `summary-row` and `state-sentence`); the full Q and seed-noise sentences appear once, under the boxes in the Cluster quality tab. The Removal Sensitivity tab now points to the Seed-Noise Floor with one short line (ARI min, K) instead of repeating the sentence. The sentence names up to three hidden Genre Tags, otherwise their count, plus the defining tag and removed tags by name; any `.copy-id` copies on click (`workbench.js`, also used by issue 09). Hidden in Analysis Report mode, whose §1 states the Network State (issue 09). Browser check in headless Chrome on the real Build at 1440 × 900: summary "100 of 100 · 59 · 332 · 3 + 4 · 0.17 · excess +0.11 · 0.04 · descriptive", the sentence ending in `4ceb7990d20d`, a click on it puts `4ceb7990d20d` on the clipboard, five boxes then the two sentences.
