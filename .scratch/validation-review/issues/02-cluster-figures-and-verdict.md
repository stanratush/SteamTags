# Which per-Cluster figures and verdict replace "Dissolved"?
Type: grilling
Status: resolved
Blocked by: 01

## Question

Today a Cluster is "Dissolved" when its mean Jaccard is ≤ 0.5, and that is attributed to Hennig (2007 §2), who justifies 0.5 per resample. On stored runs the two rules disagree:
- rpg C7 has mean 0.543 and is dissolved in 52 of 100 subsamples;
- puzzle 12/2 C6 has mean 0.506 and is dissolved in 66 of 92.

The label also flips between two runs that differ only in the replicates' minimum Multi-Tag Clusters (0.490 vs 0.515, s.e. ≈ 0.019). See [Verified review](../research/01-verified-review.md) items 13 and 14. This reopens [Validation design](../../auto-parameter-selection/issues/07-validation-design.md), and it returns to [Validation methods](../../auto-parameter-selection/research/02-validation-methods.md)'s recommendation of mean plus dissolution count plus recovery count.

Decide:
- Which figures are reported per Cluster and arm: mean J, the dissolution frequency (≤ 0.5), and the recovery frequency (> 0.75, quoted as Hennig's "say")?
- Is there an overall label at all? If so, what is its rule (for example majority of resamples dissolved), its name, and its attribution as a study choice?
- Monte Carlo uncertainty:
  - s.e. of the mean (sd/√B*);
  - Wilson or Clopper–Pearson intervals for the frequencies;
  - how these are worded and kept apart from the across-subsample spread (sd or p10–p90);
  - whether a label inside its Monte Carlo error is marked.
- Does the summary sentence ("k of N Multi-Tag Clusters …") stay, and on which figure?

All of these can be rebuilt from stored records.

## Answer

Decided by grilling with the researcher, 2026-11-04. Evidence: [Verified review](../research/01-verified-review.md), items 13–15, and a recount of the 9 stored `ps-validation-1` runs (re-selected arm, Hennig's Jaccard, B* as defined in [How does tag loss count in Cluster recovery?](01-tag-loss-in-cluster-recovery.md)).

**Terms** (now in [CONTEXT.md](../../../CONTEXT.md)): **Dissolved in most subsamples**. The bare "Dissolved" (mean ≤ 0.5) is retired.

**Figures per Multi-Tag Cluster and arm** (the same in both arms)
- **Hennig's Jaccard**, over the B* assessable subsamples:
  - the mean, with its Monte Carlo s.e. sd/√B*;
  - the 10th–90th percentile spread of the per-subsample J;
  - the **dissolution frequency** (J ≤ 0.5), as k of B* with a 95% Wilson interval;
  - the **good-recovery frequency** (J > 0.75, quoted as Hennig's own example: "say"), as k of B* with a 95% Wilson interval.
- **Whole-Cluster Jaccard**, over the non-degenerate subsamples: the mean with its s.e., and the 10th–90th percentile spread. It gets no frequencies and no label: the 0.5 argument (Hennig 2007 §2) assumes a common tag set, which only Hennig's Jaccard has.
- **Wording:** Monte Carlo error reads "± s.e. from S subsamples" (Wilson for frequencies), and the spread is worded separately. Neither is called a confidence interval: the Top 100 is not a sample.
- fpc's 0.6 / 0.75 / 0.85 bands stay out, as in ticket 07.

**Statuses, in display order**
1. **Not assessable** (B* = 0): "fewer than 2 of its tags survive in every subsample".
2. **Dissolved in most subsamples**: Hennig's Jaccard ≤ 0.5 in more than half of B*, decided on the point estimate. The 0.5 per subsample is Hennig's; the majority is this study's rule, and the text says so. It is close to "median J ≤ 0.5".
3. **Borderline**: the 95% Wilson interval of the dissolution frequency contains ½, whether or not the Cluster is labelled.

"Rarely assessable (B* of S)" is shown beside the mean when B* is under half of the non-degenerate subsamples; it is a flag, not a status. Recovery is only ever a figure.

**The summary sentence**, one per arm
- "k of N Multi-Tag Clusters are dissolved in most re-selected subsamples (Hennig's Jaccard ≤ 0.5 in more than half): …", plus "(b borderline)" when b > 0.
- Not-assessable Clusters get a sentence of their own.
- "No Multi-Tag Cluster is dissolved in most subsamples" appears only when no Cluster is labelled and none is not assessable.
- How the two arms' lists combine is for the layout ticket (review item 20).

**Effect on the stored runs**
- 19 Cluster-runs get the new label, against 13 under mean ≤ 0.5. The additions are rpg C7 and C10, puzzle 12/2 C3 and C6, puzzle 11/5 C4, and puzzle 14/2 C3 in its min-multi-3 run.
- Puzzle 14/2 now labels C3 and C4 in both runs; under the mean rule it flipped.
- 8 Clusters are borderline: rpg C3, C4, C7 and C10; puzzle 12/2 C3 and C4; puzzle 11/5 C2 and C4.

**Reopens** [Validation design](../../auto-parameter-selection/issues/07-validation-design.md)'s verdict "mean Jaccard ≤ 0.5 = Dissolved", and returns to [Validation methods](../../auto-parameter-selection/research/02-validation-methods.md)'s recommendation (mean plus dissolution count plus recovery count).

**Hand-offs**
- To [How are versions, reruns and tests staged?](07-versioning-reruns-and-tests.md):
  - everything here except the Whole-Cluster Jaccard can be rebuilt from stored records, so it is a summary-version change;
  - tests for the majority rule (exactly half is not labelled), Wilson-based borderline marking, and the "no Cluster dissolved" sentence being suppressed when one is not assessable.
- To [How should the validation card and the Inspector's Validation section look?](06-validation-card-and-inspector-layout.md):
  - the columns: both means with s.e., the spread, both frequencies with intervals, and the statuses;
  - how the arms' lists combine;
  - the Inspector badge ("Dissolved in most subsamples (re-selected): n").
- The export to-do (map, Not yet specified): the new `validation_clusters.csv` columns.
