# 03: Inspector labels and the Cluster quality tab

**What to build:** every Inspector label (node, edge, cluster, Removal Sensitivity) and every Cluster quality box and sentence gets the two-layer help, with its guide entries written.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Metric help spec](../spec.md): "Content rules", "Layer 1", "Layer 2".

- [ ] Each `INSPECTOR_LABELS` label resolves to its guide entry through the Column Index. `label_tip` is replaced by the guide text plus "Column: `name`" on the last line.
- [ ] `_kv` `dt`s carry `data-tip`, `data-help` and `tabindex="0"`, still as one HTML block per list.
- [ ] Quality boxes (Q, Null-model excess, Coverage, Silhouette, Seed noise) use guide text with **Now:** lines (γ, R, K, null mean ± SD). `SILHOUETTE_TIP` and `ari_tip` are removed.
- [ ] Each entry these reach has an In short block and `*Why it matters here.*`. That covers tag game count, degree, strength, per-tag silhouette, medoid score, Cluster Center, top-strength tag, within-cluster z, participation, edge weight, edge lift, Membership Stability, conductance, coverage, ARI and every Removal Sensitivity entry.
- [ ] Test: every Inspector label and quality item resolves to an entry with an In short.
- [ ] Checked in the browser: a node, an edge, a cluster and a Removal Sensitivity result.

## Comments
