# What happens to a defining Tag in a match when Genre Tags or defining Tags are shown?
Type: grilling
Status: resolved
Blocked by:

## Question

[Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md) gives the mode its own shared controls, including the rules "Genre Tags hidden" and "defining Tag hidden", so the user can show them. Every defining Tag of the full Build is also a Genre Tag; with the defaults it is hidden in every dataset and never enters a match ([Which measures survive on the real Builds?](04-measures-on-real-builds.md)). Shown, it is on every game of its own Tag-Specific Dataset (Puzzle on all 100 games of Puzzle) and on few of another's (Puzzle on 1 game of Overall), so it sits in a Cluster on both sides for reasons of how the datasets were drawn, not of how Tags group.

Decide:
- whether a dataset's defining Tag is kept out of the matching (and out of the Comparable Tags and ARI) even when shown, is matched like any other Tag with a caveat, or whether the mode simply doesn't offer to show it;
- how a match whose shared Tags include a defining Tag is marked, if they are matched;
- whether the same applies to a Genre Tag that is not a defining Tag, when Genre Tags are shown.
Check on the full Build with Genre Tags shown (prototype 06's `export.py` can be rerun with other Selection Settings, if such runs are cached).

## Answer

*Grilled with the researcher, 2026-11-17.* Checked on the full Build: no cached Parameter Selection run has Genre Tags shown, so each dataset was re-clustered at its pick (g, s, γ, main seed) with Genre Tags shown, and with Genre Tags and the defining Tag shown.

**Facts found.**
- Defining Tag shown: it joins a large Cluster in its own dataset (Puzzle in a 16-Tag Cluster, Simulation in a 22-Tag one) and makes 9 matches whose only shared Tag is a defining Tag (Match Jaccard 0.04–0.12); one, RPG C14 ~ Strategy C4 at 0.12, passes the 0.10 minimum on "RPG" alone. ARI on the Comparable Tags falls by up to 0.06 (Overall vs Simulation 0.23 → 0.17).
- Genre Tags shown, defining Tag hidden: each dataset's defining Tag is hidden in its own network but sits in the others' (Strategy in a Simulation Cluster, hidden in Strategy). [How do Tags missing from the other dataset's network enter a match?](02-tags-missing-from-the-other-network.md) assumed a hidden Tag is in neither network; here it is in one, and its rules would list it as "not in Strategy's network (100 games, minimum 14)" and count it against Match Jaccard.
- Other Genre Tags group like any Tag; a few matches rest on one alone (e.g. 2 in Overall vs RPG).

**Decisions.**
1. **The defining Tag is always hidden in its own dataset.** The mode has no "defining Tag hidden" control; each dataset's own defining Tag is hidden, as the rule does today. *(Amends [Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md), point 9: the mode's only hidden-Tag rule control is "Genre Tags hidden".)* A Parameter Selection run made with the defining Tag shown cannot feed the mode: its settings differ from the comparison's, so "Use in Cluster Comparison" is disabled there by the existing rule of [How does the user move between Cluster Comparison and the Workbench?](13-moving-between-modes.md). The Comparison State and export carry no defining-Tag flag.
2. **A Tag hidden in only one dataset of a pair is set aside for that pair.** It is not a Comparable Tag, counts in neither Cluster's measures (Match Jaccard, Jaccard (comparable), the shared shares, Overlap vs. expected, ARI) nor in the "No match:" flags, and is listed under its Cluster as a fourth group: "hidden in Strategy (its defining Tag)" · *„скрит в Strategy (определящият му таг)“*. In the export's match rows it appears in that group, never as "not in the network". *(Amends ticket 02, point 3: "Tags hidden or removed by the shared settings are in neither network and appear in no list" holds for Tags hidden in both; a Tag hidden in one is this group.)* In practice it arises only for a defining Tag while Genre Tags are shown.
3. **A Genre Tag that is not a defining Tag is matched like any Tag** when Genre Tags are shown: no mark, no caveat, including matches that rest on it alone. It is a real Tag on games not drawn for having it, and the Workbench does not mark Genre Tags in Clusters either.

No new glossary term. Scratch check (not kept): re-cluster per dataset with `build_network` + `cluster_graph` at the pick, score pairs as prototype 04.
