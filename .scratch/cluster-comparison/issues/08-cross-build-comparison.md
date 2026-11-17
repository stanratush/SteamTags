# Can datasets of different Builds be compared?
Type: grilling
Status: resolved
Blocked by:

## Question

Charted: the comparison covers the Top-N Datasets of the open Build. The app gives each browser tab one Build (ADR 0006).

Decide whether comparing a dataset of another Build is part of this spec, a later effort, or ruled out:
- the cases: two Builds of one Snapshot (e.g. before and after an exclusion change, or two Tag Depths), Builds of two Snapshots, a Steam Build and an Import Build;
- whether a Tag is the same Tag across them (same Snapshot: the same ids; an Import: names only);
- what "shared settings" means when the two Builds differ in Tag Depth, hidden Tags or filter field;
- if it is in: how the second Build is chosen without breaking one Build per tab.

If it is out, the answer goes to the map's Out of scope with the reason.

## Answer

**Out of scope** (decided with the researcher, 2026-11-17). Cluster Comparison covers only the Top-N Datasets of the open Build. Comparing datasets of different Builds is not part of this spec. It may come back as a later effort with its own destination, not as a resumption of this map.

Why: every decision on this map assumes one Build. That means one Tag universe for the Common Tags, one Parameter Selection cache for the per-dataset defaults and the stored Selected Partitions, and one Tag Depth, one exclusion list and one set of hidden Tags behind the shared settings. Across Builds, each of these would need its own rules: Tag identity by name for different Snapshots or an Import, a meaning for "shared" when Tag Depth or exclusions differ, and a way to load a second Build into a tab that ADR 0006 ties to one Build. The way to look across Builds stays as ADR 0006 has it: two tabs side by side.
