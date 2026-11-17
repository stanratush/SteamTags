# 19: Link diagram, Minimum Match Jaccard and flags

**What to build:** for the chosen dataset pair, the two-column link diagram of Cluster Matches: A's Multi-Tag Clusters on the left, B's on the right, a curve per match at or above the Minimum Match Jaccard, each Cluster's flag as a badge. The user can swap sides, show weaker matches, focus one Cluster and choose a match.

**Blocked by:** 18

**Status:** ready-for-agent

Spec: [Cluster Comparison spec](../spec.md): "The Cluster Comparison mode" (Main column: title, slider, diagram, One-Tag line, the no-match empty state), "Matching" (flags, minimum similarity), "Comparison State" (view choices). Prototype: [index.html](../prototypes/06-look-of-the-mode/index.html) `?variant=B`. Decision: ticket [06](06-look-of-the-mode.md).

- [ ] **Pair title** with ⇄, which swaps which dataset is A; the default A is the earlier dataset in the Build's order.
- [ ] **Minimum Match Jaccard** slider ("Minimum Jaccard" short), from 0 up, starting at 0.10, with a "show weaker" link that draws hidden matches dashed. Both are view choices: the `comparison_id` does not change and nothing is recomputed.
- [ ] **Boxes:** label, Tag count, Tags clipped to two lines, the flag badge ("No match: outside Overall's network", "No match: only One-Tag Clusters in Overall" with its counts tooltip, "No match above 0.10" with the current minimum), a left border in the dataset's colour, under column headings naming each dataset.
- [ ] **Curves:** width and strength follow Match Jaccard, value written on the curve.
- [ ] Clicking a box shows only its curves and dims the Clusters it doesn't match; clicking again shows all. Clicking a curve chooses the match (shown by issue 20).
- [ ] A line under the diagram: how many One-Tag Clusters each side has, and that they are not matched.
- [ ] Empty state for a pair with no Cluster Match.
- [ ] The diagram keeps its two columns at narrow widths and scrolls vertically.
- [ ] Badges, slider and ⇄ carry their `comparison.*` tooltips; new strings have bg entries.
- [ ] Tests: the diagram lists every Multi-Tag Cluster of both sides and one curve per match at or above the minimum; moving the slider changes the curves and the "No match above" badges but not the `comparison_id`; "show weaker" adds the dashed curves; ⇄ swaps sides and the flags' direction; a box click filters; a curve click records the chosen match; the no-match empty state.
