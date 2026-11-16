# Can datasets of different Builds be compared?
Type: grilling
Status:
Blocked by:

## Question

Charted: the comparison covers the Top-N Datasets of the open Build. The app gives each browser tab one Build (ADR 0006).

Decide whether comparing a dataset of another Build is part of this spec, a later effort, or ruled out:
- the cases: two Builds of one Snapshot (e.g. before and after an exclusion change, or two Tag Depths), Builds of two Snapshots, a Steam Build and an Import Build;
- whether a Tag is the same Tag across them (same Snapshot: the same ids; an Import: names only);
- what "shared settings" means when the two Builds differ in Tag Depth, hidden Tags or filter field;
- if it is in: how the second Build is chosen without breaking one Build per tab.

If it is out, the answer goes to the map's Out of scope with the reason.
