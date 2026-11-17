# 15: Comparison core: Cluster Matches, flags, ARI and games in both Clusters

**What to build:** the Dash-free `steamstudy.network.comparison` module. Given the resolved partitions of the included Top-N Datasets (network Tags, edged Tags, labels, games), it returns, for every dataset pair, everything the mode and the export show: Comparable Tags and set-aside Tags, every Cluster Match with its figures and Tag groups, the per-Cluster "No match" flags, the pair overview (ARI on Comparable Tags, Comparable Tag shares, games in common, match count) and the games in both Clusters of each match. It also builds the Comparison State key and `comparison_id`.

**Blocked by:** None (can start immediately)

**Status:** done

Spec: [Cluster Comparison spec](../spec.md): "Matching", "Games in both Clusters", "Comparison State", "Modules", "Facts this spec rests on". Reference only (never imported): [run.py](../prototypes/04-measures-on-real-builds/run.py), [logic.js](../prototypes/06-look-of-the-mode/logic.js). Decisions: tickets [01](01-similarity-measures.md), [02](02-tags-missing-from-the-other-network.md), [05](05-games-in-both-clusters.md), [09](09-comparison-identity-and-export.md), [11](11-names-and-readings.md), [14](14-defining-tag-in-a-match.md).

- [x] **Comparable Tags** C = Tags in both networks; a Tag hidden in only one of the two datasets is set aside for the pair (removed from both Clusters' Tag sets before any figure, flag or Tag-group count) and returned separately; Tags hidden or removed in both appear nowhere.
- [x] **Cluster Matches**: every (a, b) of Multi-Tag Clusters sharing at least one Tag; One-Tag Clusters are never matched.
- [x] **Figures** per match: Match Jaccard, Shared % of A and of B (whole and comparable forms), Jaccard (comparable) with `None` below two Comparable Tags in either Cluster, Overlap vs. expected and its expected value (E = |a′|·|b′|/N, N = |C| with One-Tag Clusters). No minimum-containment figure.
- [x] **Tag groups** for each unshared Tag: in another Multi-Tag Cluster of the other dataset (named), One-Tag Cluster there, not in its network (with its game count and the minimum; "0 games" included), hidden there (its defining Tag, set aside).
- [x] **Flags** per Multi-Tag Cluster and direction: `outside_network`, `only_one_tag_clusters` (with the counts the tooltip needs), and "no match above the minimum" derived from `best_jaccard` and a given minimum. Set-aside Tags are ignored: a Cluster whose only Comparable Tag would be a defining Tag hidden on the other side is `outside_network`.
- [x] **Pair overview:** ARI with scikit-learn's `adjusted_rand_score` on the Comparable Tags with an edge in at least one network (the `selection.link` set), `None` below two; the Comparable Tags count and share of each network; games in common (both Top-N Datasets, after the shared Minimum Months Filter); match count. No AMI, no mean best Jaccard.
- [x] **Games in both Clusters** by `cluster_games`' rule (`network/tables.py`): rank in A and B, matched x/|a| and y/|b|, the game's Tags from either Cluster with the shared ones marked; sorted by matched A + matched B descending, then rank in A, then rank in B; plus the counts in both Clusters / only A / only B / neither.
- [x] Each unordered pair is computed once; swapping A and B is derived without recomputing.
- [x] **Comparison State key** (Build; shared settings; per included dataset in Build order: on a cell, the Parameter Selection settings key, g, s, Selected Resolution; hand or no run, g, s, γ, main seed; pick vs. cell not in the key) and `comparison_id` = first 12 hex of SHA-256 of its canonical JSON, made as `state_id` is.
- [x] No new dependency.
- [x] Tests:
  - Small hand-made partitions covering every figure, each Tag group, each flag, a set-aside defining Tag, a pair with no match and a "—" Jaccard (comparable).
  - `comparison_id` is stable, and changes with every key part and with nothing in the view choices.
  - On the full Build `20261005T062558Z-full/20261008T221504Z-7a23ae9f` (skipped when absent, `ps_cache.NAME_LENGTH` overridden in the test as the prototypes did): 10 pairs, 103 Cluster Matches, ARI 0.07–0.53, Match Jaccard maximum 0.58, games in common as listed in the spec.

## Comments

- 2026-11-17, implementation: `src/steamstudy/network/comparison.py`, with `tests/test_comparison.py` (hand-made partitions) and `tests/test_comparison_real_build.py` (the full Build on its picks: 10 pairs, 103 matches, every pair's ARI and match count as in prototype 04, maximum Match Jaccard 0.58, games in common, 48 matches at 0.10). Interface: `Partition` in; `compare_pair` / `compare_all` give a `PairResult` per unordered pair (`swapped()` for ⇄); `ClusterFlag.flag_at(minimum)` adds "No match above"; `comparison_key` / `comparison_id`. Unshared Tags are listed by group, then by Tag id.
- 2026-11-17, two readings to confirm (code review):
  - **Hand vs. no run is not in the key.** The spec takes only pick vs. selected cell out ("its source and values … Pick vs. selected cell is not in the key"). A hand-set and a no-run dataset with the same g, s, γ and main seed give the same partition, so they get the same `comparison_id`; the source stays in `datasets.csv`. If the key should tell them apart, add `source` to the off-cell part of `DatasetValues.key()`.
  - **Games in both Clusters use the Clusters with set-aside Tags removed.** `cluster_games` alone would count a game of B for `a` through B's defining Tag when that Tag is hidden in B but sits in `a`, which would put nearly every game in common in both Clusters; Matched in A is read against the same reduced |a|.
