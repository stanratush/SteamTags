# How long does computing each dataset's Eligible Pool take on the lightweight Snapshot?
Type: task
Status: open
Blocked by:

## Question

The Build menu shows each dataset's Eligible Pool against its list size ([Build menu](12-build-menu.md)), but the prototype only estimates it. A whole Build takes about 24 s from the [lightweight Snapshot](08-lightweight-snapshot.md), and [Build inputs and timings](02-build-inputs-and-timings.md) measured the stages from the raw Snapshot.

Measure on the full Snapshot, with the script in `prototypes/17-eligible-pool-timing/` and findings in `research/17-eligible-pool-timing.md`:
- loading the lightweight tables once, then (warm) running every Exclusion Rule and computing the Eligible Pool and the Top-N for all datasets;
- how that time changes with one edit: a rule's tags, a rank limit, Tag Depth, one Manual Exclusion or Override, and a list size;
- whether an incremental path (reusing parsed tables or the matched rules) is materially faster than a full recompute;
- the same on the largest Import the warnings allow (50,000 items, 5,000 attributes), using synthetic data.
