# Where do each dataset's g, s and resolution come from, and the shared settings?
Type: grilling
Status:
Blocked by:

## Question

Charted: each included dataset has its own g, s and resolution; Clustering Weight, algorithm, seed, hidden and removed Tags and the Minimum Months Filter are shared.

Decide:
- the starting values for a dataset when it is included: the pick of its **Automatic Parameter Selection** if a run exists, the Build's network defaults, or what the Workbench last showed for it;
- whether the view says where the values came from, and what it shows when a dataset has no Automatic Parameter Selection run;
- whether the resolution follows g and s (the **Selected Resolution** of that Threshold Pair, when known) or is always entered by hand;
- where the shared settings come from: the Workbench's current ones, or controls of the mode's own;
- whether the Minimum Months Filter can really be shared for an Import Build, where the filter field differs by Import;
- the limits on g and s per dataset (the Build's Parameter Grid ranges, or free).
