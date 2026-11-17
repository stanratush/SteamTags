# 15: Comparison core: Cluster Matches, flags, ARI and games in both Clusters

**What to build:** the Dash-free `steamstudy.network.comparison` module. Given the resolved partitions of the included Top-N Datasets (network Tags, edged Tags, labels, games), it returns, for every dataset pair, everything the mode and the export show: Comparable Tags and set-aside Tags, every Cluster Match with its figures and Tag groups, the per-Cluster "No match" flags, the pair overview (ARI on Comparable Tags, Comparable Tag shares, games in common, match count) and the games in both Clusters of each match. It also builds the Comparison State key and `comparison_id`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "Matching", "Games in both Clusters", "Comparison State", "Modules", "Facts this spec rests on". Reference only (never imported): [run.py](../prototypes/04-measures-on-real-builds/run.py), [logic.js](../prototypes/06-look-of-the-mode/logic.js). Decisions: tickets [01](01-similarity-measures.md), [02](02-tags-missing-from-the-other-network.md), [05](05-games-in-both-clusters.md), [09](09-comparison-identity-and-export.md), [11](11-names-and-readings.md), [14](14-defining-tag-in-a-match.md).

- [ ] **Comparable Tags** C = Tags in both networks; a Tag hidden in only one of the two datasets is set aside for the pair (removed from both Clusters' Tag sets before any figure, flag or Tag-group count) and returned separately; Tags hidden or removed in both appear nowhere.
- [ ] **Cluster Matches**: every (a, b) of Multi-Tag Clusters sharing at least one Tag; One-Tag Clusters are never matched.
- [ ] **Figures** per match: Match Jaccard, Shared % of A and of B (whole and comparable forms), Jaccard (comparable) with `None` below two Comparable Tags in either Cluster, Overlap vs. expected and its expected value (E = |a′|·|b′|/N, N = |C| with One-Tag Clusters). No minimum-containment figure.
- [ ] **Tag groups** for each unshared Tag: in another Multi-Tag Cluster of the other dataset (named), One-Tag Cluster there, not in its network (with its game count and the minimum; "0 games" included), hidden there (its defining Tag, set aside).
- [ ] **Flags** per Multi-Tag Cluster and direction: `outside_network`, `only_one_tag_clusters` (with the counts the tooltip needs), and "no match above the minimum" derived from `best_jaccard` and a given minimum. Set-aside Tags are ignored: a Cluster whose only Comparable Tag would be a defining Tag hidden on the other side is `outside_network`.
- [ ] **Pair overview:** ARI with scikit-learn's `adjusted_rand_score` on the Comparable Tags with an edge in at least one network (the `selection.link` set), `None` below two; the Comparable Tags count and share of each network; games in common (both Top-N Datasets, after the shared Minimum Months Filter); match count. No AMI, no mean best Jaccard.
- [ ] **Games in both Clusters** by `cluster_games`' rule (`network/tables.py`): rank in A and B, matched x/|a| and y/|b|, the game's Tags from either Cluster with the shared ones marked; sorted by matched A + matched B descending, then rank in A, then rank in B; plus the counts in both Clusters / only A / only B / neither.
- [ ] Each unordered pair is computed once; swapping A and B is derived without recomputing.
- [ ] **Comparison State key** (Build; shared settings; per included dataset in Build order: on a cell, the Parameter Selection settings key, g, s, Selected Resolution; hand or no run, g, s, γ, main seed; pick vs. cell not in the key) and `comparison_id` = first 12 hex of SHA-256 of its canonical JSON, made as `state_id` is.
- [ ] No new dependency.
- [ ] Tests:
  - Small hand-made partitions covering every figure, each Tag group, each flag, a set-aside defining Tag, a pair with no match and a "—" Jaccard (comparable).
  - `comparison_id` is stable, and changes with every key part and with nothing in the view choices.
  - On the full Build `20261005T062558Z-full/20261008T221504Z-7a23ae9f` (skipped when absent, `ps_cache.NAME_LENGTH` overridden in the test as the prototypes did): 10 pairs, 103 Cluster Matches, ARI 0.07–0.53, Match Jaccard maximum 0.58, games in common as listed in the spec.
