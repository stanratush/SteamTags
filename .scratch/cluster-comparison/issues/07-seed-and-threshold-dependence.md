# How is a match read against seed and threshold dependence?
Type: grilling
Status: resolved
Blocked by: 04

## Question

Clusters change with the seed and with g and s, so a match can appear, vanish or change its similarity for reasons unrelated to the two datasets. Charted: this is in scope, with no commitment to a new metric.

With the similarity values from [Which measures survive on the real Builds?](04-measures-on-real-builds.md) in hand, decide:
- whether the answer is a number, a written caveat, or both;
- if a number: a floor from reseeding (the similarity of a dataset's Clusters with themselves under other seeds, in the spirit of the **Seed-Noise Floor**), or the **Membership Stability** of the two Clusters shown beside the match;
- whether a match between two Clusters of low Membership Stability is marked;
- what the User Guide must say a match does and does not show, in the manner of the existing "never a claim that the Clusters are real" wording.

## Answer

Resolved with the researcher, 2026-11-17.

**Facts from the code**

- A stored Automatic Parameter Selection cell keeps only a summary of seed noise (`seed_noise` in `src/steamstudy/network/selection.py`: floor, mean, exact, runs). The noise partitions and per-Tag **Membership Stability** are not stored. Membership Stability exists only on a full Network State (`network/state.py`), so for a dataset on a cell it would need a re-clustering with the noise seeds.
- Each cell already has **Neighbour Agreement** (ARI of its Selected Partition with the four neighbouring cells; metric reference: "measures parameter stability, not correctness").

**Decisions**

1. **A written caveat plus figures each dataset already has. No new figure per match.** No reseeding floor for a match's similarity, and no Membership Stability beside a match.
2. **Each dataset row shows its Seed-Noise Floor (from [Why does the seed change between cells, and should it be the same for every dataset?](10-seed-per-dataset.md)) and, for a dataset on a cell, its cell's Neighbour Agreement** as the threshold-dependence figure. A dataset set by hand or with no run shows "—" for Neighbour Agreement.
3. **A match between Clusters of low Membership Stability is not marked.** Cells have no per-Tag stability, and a "low" cut-off would read as a judgement of whether a Cluster is real.
4. **A dataset set by hand gets no extra figure either**, although its Network State has Membership Stability, so both kinds of dataset show the same figures.
5. **The caution's content** (final wording and Bulgarian go to [What are the measures called, and how is each one read?](11-names-and-readings.md)):
   > A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is not evidence that the Clusters are real or that the datasets share a genre structure. A match can appear, vanish or change its similarity with the seed, with g and s, and with the resolution. Read it against each dataset's Seed-Noise Floor and Neighbour Agreement.

   It goes in the User Guide section, the metric reference entry for the mode and the in-app help.

**Passed on**

- [What fixes one comparison, and what does its export hold?](09-comparison-identity-and-export.md): whether the export carries each dataset's Seed-Noise Floor and Neighbour Agreement.
