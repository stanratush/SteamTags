# 08: Summary row, Network State sentence and Cluster quality boxes

**What to build:** the key numbers sit large above the graph, with the Network State in one readable sentence. The Cluster quality tab becomes five boxes with tooltips. The long Q / null-model / noise sentences appear once, in that tab only.

**Blocked by:** 01, 02

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Summary row, Network State sentence and Cluster quality".

- [ ] Summary row (Workbench), each value large with a muted label and a tooltip:
  - Games "N of 100";
  - Tags;
  - Links;
  - Clusters "k + s multi-tag + one-tag";
  - Q "0.17 · excess +0.11";
  - Silhouette "0.04 · descriptive", with the full qualifier in its tooltip.
- [ ] Under it, the Network State sentence: dataset, Months filter, thresholds, hidden Genre Tags (count or names), removed tags, algorithm, weight, γ and seed. It ends with the `state_id`, which copies on click.
- [ ] The quality and noise lines are removed from above the graph. The Cluster quality tab shows:
  1. Five boxes, each with a tooltip: Q (γ), Null-model excess (z, null mean ± SD), Coverage, Silhouette (descriptive), Seed noise (ARI min, mean).
  2. The two full sentences, once, in small muted text.
  3. The connections and replicate grids.
- [ ] ARI is shown as numbers only, with the spec's tooltip. No bands, stable/unstable words or colours anywhere.
- [ ] Tests:
  - The summary and the boxes show the values of `cluster_quality.csv` for the state.
  - The Q text never shows z without the excess and the null mean.
  - The quality sentence appears exactly once in the Workbench.

## Comments
