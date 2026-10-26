# Does Neighbour Agreement favour high g?
Type: grilling
Status: open
Blocked by: none

## Question

Is Neighbour Agreement systematically higher at large g, so that Automatic Parameter Selection drifts towards small networks for a reason unrelated to parameter stability? And if so, what changes in the method or in how its choice is reported?

- **The evidence** ([Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md), "After unblinding"; per-pair values in [neighbour-agreement-by-pair.md](../prototypes/05-grid-run/neighbour-agreement-by-pair.md)):
  - Neighbour Agreement peaks in the high-g half of the grid in every dataset.
  - Every chosen pair lies at g = 14–17, with 29–39 tags and 3–8 Multi-Tag Clusters.
  - Without the Pair Constraints, rpg would pick g=19, s=4 (NA 1.000).
- **Suspected mechanisms** to confirm or rule out:
  - fewer tags and fewer Multi-Tag Clusters leave less to disagree about;
  - at high g, a g-step removes few tags, so the tag Jaccard is high and the graphs are nearly identical (ticket 05: 66 identical-graph g-links, all in puzzle, rpg and simulation);
  - ARI's behaviour with few, large Clusters;
  - the 3-Cluster minimum binding at g ≥ 12 (184 of 196 such pairs).
- **What would show it:**
  - NA against g, tags and Multi-Tag Clusters per dataset;
  - NA split by link direction (g-links against s-links);
  - a baseline NA under a reference, for example the same comparison with neighbours' Selected Partitions replaced by size-matched random partitions, or a per-g normalisation.
  - Any check is a throwaway script under `prototypes/12-.../` over the ticket 05 results, with no new grid run.
- **Possible responses**, each to be decided or rejected:
  - leave the method as it is and add a fixed caveat to the explanation and the documentation;
  - report NA alongside a size-adjusted or baseline-relative value;
  - change the objective, or the tie-break (smallest g already pushes the other way).
- **Fixed by ticket 06, not reopened here:** the Pair Constraint defaults and the tolerance stay as decided, and are not re-tuned against the selected pairs. A method change that alters which pair is chosen is a change to the objective. If adopted, it is recorded here as such.
