# 13: Cluster Centers, node roles and the inspector

**What to build:** Every Multi-Tag Cluster of three or more tags gets a Cluster Center (Jaccard medoid), drawn as ◆ with a heavier outline, with the frequency-driven `top_strength_tag` shown beside it. Every tag gets its degrees, strengths in both weightings, `within_z` and `participation`. Clicking a node, edge or cluster opens an inspector with these numbers. An edge's inspector lists the games that have both tags, fetched on click.

**Blocked by:** 12

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Network" (Cluster Center, Per-node metrics), "App" (Graph, Inspector), "Export schemas".

- [ ] `medoid_score` is the mean Jaccard distance to the other members. The center is the smallest score; ties are compared rounded to 12 decimals, then more `n_games`, then lower `tag_id`. One-tag and two-tag clusters get no center (`center_status` `one_tag_cluster` / `two_tag_cluster`), but two-tag members still get `medoid_score`.
- [ ] `top_strength_tag` (highest intra-cluster strength on the active weight, same tie-break and n/a rule) and `center_is_top_strength`.
- [ ] Node metrics: `n_games, is_isolated, degree, degree_intra, strength_shared, strength_lift, strength_shared_intra, strength_lift_intra, medoid_score, is_center, within_z` (population SD; n/a for One-Tag Clusters or equal strengths) and `participation` (over every cluster including One-Tag Clusters; n/a at zero strength).
- [ ] `nodes.csv` and `clusters.csv` gain these columns in the spec's order and sort, with `members` ordered by `medoid_score`. The Build tables follow. `export.json` method constants gain the center tie-break and cluster-label rules. `schema_version` is bumped.
- [ ] Graph: ◆ with a heavier outline on Cluster Centers only. One-Tag Clusters are greyed.
- [ ] Node inspector: every node metric (active-mode strength first), `within_z` shown with its cap ("within-z 1.2 (max 1.7 in a 4-tag cluster)", cap √(n−1)), and Remove.
- [ ] Edge inspector: `shared_games`, `lift`, and the games (AppID, name, rank) computed on click.
- [ ] Cluster inspector: members ranked by `medoid_score`, with intra-cluster strength (active first), `within_z` and `participation`; plus center, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength` and `connected`.
- [ ] Hand-built tests: the medoid with a tie, the two-tag n/a rule, `within_z` against a hand calculation, participation with a One-Tag Cluster neighbour.
