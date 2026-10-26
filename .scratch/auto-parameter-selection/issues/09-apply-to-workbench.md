# Apply-to-Workbench semantics
Type: grilling
Status: open
Blocked by: 03

## Question

What exactly happens when the user applies a selected (or any inspected) Threshold Pair to the Workbench?

- Which controls change: g, s, Minimum Months, the hidden tags, Clustering Weight = Lift, algorithm = Leiden, γ = the rounded Selected Resolution, the seed.
- The Workbench clusters with one seed at one γ. Leiden at the domain midpoint with the main seed may not reproduce the Selected Partition, which was found at some scan γ and seed. Do we pick the first scan seed that reproduces it at the rounded midpoint? If none does, do we show the ARI between what the Workbench shows and the Selected Partition, or refuse?
- Fixed by [Modules, caching and parallelism](08-modules-caching-parallelism.md): `detect` and the scan's `leiden_scan` share one igraph construction, so Leiden at the Selected Partition's first (γ, seed), which the cache stores with its hit count, reproduces it exactly. The open question is the Workbench's two-decimal γ, not the code path.
- How the Workbench shows that its state came from Automatic Parameter Selection, and whether that changes the Network State key (it shouldn't, if every applied value is an ordinary setting).
