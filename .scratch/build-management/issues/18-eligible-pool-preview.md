# When does the Build menu show each dataset's Eligible Pool: live, on demand, or only at Review?
Type: grilling
Status: open
Blocked by: 17

## Question

Using the times from [the Eligible Pool timing task](17-eligible-pool-timing.md), decide:
- when the pool sizes (and the games entering the Overall list) are recomputed while a draft is edited: after every change, debounced, on a button, or only at Review;
- where the work runs (in the app process or as a server job like the Build run), and what the menu shows while it runs or when the draft cannot be computed (an invalid rule, a missing Snapshot);
- whether the preview is guaranteed to match the Build, and what Review says if it is stale.
