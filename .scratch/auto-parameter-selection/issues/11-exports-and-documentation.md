# Exports and documentation
Type: grilling
Status: open
Blocked by: 06, 07, 10, 12

## Question

What does Automatic Parameter Selection export and document, so that results are reproducible and read correctly?

- Exported tables (the per-pair grid, Admissible Partitions with their domains, per-direction Neighbour Agreement, validation replicates, the selection report) and a settings JSON (Build, fixed settings, grid, seeds, the Pair Constraints and tolerance with a "Default constraints" / "Custom constraints" label, method version, software versions; per-pair reason codes in the grid table), following `app/export.py` and the `export/schema.py` contracts.
- User Guide pages: what each metric means and doesn't mean; the three kinds of stability; why count-only edges carry no significance; why Q, Coverage and Silhouette are descriptive.
- Methods text with citations (Weir et al. 2017; Newman 2016; Gibson & Mucha 2022; Hennig 2007; Karrer et al. 2008), checked against the sources as in Research 30.
- How the in-app `?` help (`app/help.py`) covers the new mode.
- From [Apply-to-Workbench semantics](09-apply-to-workbench.md): whether a Workbench export made after Apply records its provenance (pair, reproduced or ARI). How the User Guide explains why an applied Workbench's Seed-Noise Floor can differ from the one Parameter Selection reports.
