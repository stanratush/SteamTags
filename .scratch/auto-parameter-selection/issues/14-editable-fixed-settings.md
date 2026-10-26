# Editable fixed settings
Type: grilling
Status: open
Blocked by: none

## Question

Which fixed settings can the user change in the Parameter Selection mode, and how is a run with non-default fixed settings labelled?

- **Where:** the "Fixed settings" section of the Controls column, read-only in [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md). It sits under Run and Pair Constraints.
- **The candidates** (defaults from the map's Notes, [Resolution-selection rules](03-resolution-selection-rules.md) and [Validation design](07-validation-design.md)):
  - hidden tags (Genre Tags and the defining tag);
  - Minimum Months (0);
  - Clustering Weight (Lift) and algorithm (Leiden);
  - the γ scan's range and step (0.25–3.00, step 0.05) and its seed count (10);
  - the Selected Partition's minimum Multi-Tag Clusters (3);
  - the validation's R null replicates and S subsamples (100 each).
- **Already settled:**
  - caching: every fixed setting is in `SelectionSettings.grid_key()` ([Modules, caching and parallelism](08-modules-caching-parallelism.md)), so a non-default run is just another cache entry;
  - unlike a Pair Constraint, changing a fixed setting needs a new Run.
- **To decide:**
  - which candidates are editable at all. Some defaults rest on decided method: CHAMP's range, γ̂ outside it, the 56-value grid. Some may be meaningless away from their default: Shared games as Clustering Weight, or Louvain, against the scan's assumptions;
  - how edits are made and confirmed. One option is to edit and then press Run, mirroring the Pair Constraints' Confirm;
  - how a non-default run is labelled in the explanation, the dataset strip and exports, next to "Default constraints" / "Custom constraints";
  - whether Apply to Workbench carries non-default hidden tags and Minimum Months. It replaces every setting ([Apply-to-Workbench semantics](09-apply-to-workbench.md)), so presumably yes;
  - whether non-default settings change what validation runs automatically.
