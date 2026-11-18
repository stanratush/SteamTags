# 20: Match detail and games in both Clusters

**What to build:** when a match is chosen in the diagram, the panel under it shows the match's figures, its shared and unshared Tags with each unshared Tag's group, and the games in both Clusters.

**Blocked by:** 19

**Status:** done

Spec: [Cluster Comparison spec](../spec.md): "The Cluster Comparison mode" (Match detail, the no-match-chosen empty state), "Matching" (figures, Tag groups), "Games in both Clusters". Decisions: tickets [05](05-games-in-both-clusters.md), [11](11-names-and-readings.md), [14](14-defining-tag-in-a-match.md).

- [x] With no match chosen, the detail asks the user to click a curve.
- [x] **Heading:** the two Clusters' names, each with its dataset ("Overall C3 ~ Puzzle C1").
- [x] **Figures:** Match Jaccard, Shared % of A, Shared % of B, Jaccard (comparable) with the Comparable Tag counts ("—" below two Comparable Tags), each with its tooltip. The Overlap vs. expected sentence ("3 shared Tags: 2.4× the 1.25 expected from the Cluster sizes (N = 38 Comparable Tags)"); no p-value, never sortable.
- [x] **Three Tag columns:** Shared, Only in ‹A Cluster›, Only in ‹B Cluster›, each unshared Tag with its group ("in Overall C5", "One-Tag Cluster in Overall", "not in Overall's network (2 games, minimum 5)", "hidden in Strategy (its defining Tag)").
- [x] **Games in both Clusters:** the count line ("Of **N** games in both datasets: **k** in both Clusters, **x** only in A, **y** only in B, **z** in neither."); columns Rank in A · Rank in B · Name · Matched in A (x / |a|) · Matched in B (y / |b|) · Tags (shared Tags marked); the spec's sort; the first `GAMES_SHOWN` (10) rows, then "Show all N"; both empty-list sentences.
- [x] ⇄ swaps the columns and A/B in the detail without recomputing.
- [x] New strings have bg entries.
- [x] Tests: a chosen match shows its figures, Tag groups and games as `network.comparison` returns them; "Show all N" reveals every row; the N = 0 and k = 0 sentences; a "—" Jaccard (comparable); a set-aside defining Tag appears in the hidden group and in no figure.
