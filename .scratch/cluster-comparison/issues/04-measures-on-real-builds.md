# Which measures survive on the real Builds?
Type: prototype
Status:
Blocked by: 01, 02

## Question

Run Jaccard and the shortlisted candidates from [Which measures can score the similarity of two Clusters from different datasets?](01-similarity-measures.md) on dataset pairs of the full Build (e.g. Overall vs a Tag-Specific Dataset, and two Tag-Specific Datasets), with the Tag universe rule from [How do Tags missing from the other dataset's network enter a match?](02-tags-missing-from-the-other-network.md). A script and a plain table are enough; no app.

With the researcher looking at the output, decide:
- which measures ship beside Jaccard, and which one ranks the matches;
- the default **minimum similarity** and the measure it applies to;
- whether a whole-pair figure (one number for dataset A vs dataset B) is worth showing in the overview, and which;
- whether a chance-corrected figure tells the reader anything the raw ones do not.

Also note what the run shows about two patches of fog on the [map](../map.md): the defining Tag of a Tag-Specific Dataset, and pairs of datasets with very different numbers of Tags and Clusters.

Prototype in `prototypes/04-measures-on-real-builds/`.
