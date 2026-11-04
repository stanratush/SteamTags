# How are versions, reruns and tests staged?
Type: grilling
Status: open
Blocked by: 01, 02, 03, 04, 05, 08, 10

## Question

The cache stores `summary` next to `records`, and the app reads the stored summary (`ps_view.validation_of`). `VALIDATION_METHOD_VERSION` sits in the validation key, so any change either goes unseen (old summaries) or forces a full replicate rerun. See [Verified review](../research/01-verified-review.md) items 23 and 24.

Decide:
- Whether to split the version into a records version (in the key) and a summary version (re-derived from records on read). Name exactly which decided changes bump which.
- How `steamstudy bundle` and shipped validations handle each bump.
- The export `SCHEMA_VERSION` change and its new columns.
- Which tests are revised: the absent-Cluster expectation, the extrapolation at `gamma_end + 1`, and the golden texts.
- Which regression cases are added:
  - zero or partly defined null Q;
  - wholly absent or low-B* Clusters;
  - single-tag survival;
  - `beyond_scan` or explicit fixed-γ optimisation;
  - width equality;
  - the `no_qualifying_pair` card note.
