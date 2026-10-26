# Parameter Selection mode prototype
Type: prototype
Status: open
Blocked by: 04, 07

## Question

How should the Parameter Selection mode look and behave? Build a rough, clickable prototype (`prototypes/10-parameter-selection-mode/`) to react to:

- Start and progress: running one dataset or all five; per-dataset progress; reusing cached results. Fixed by [Modules, caching and parallelism](08-modules-caching-parallelism.md):
  - two mutually exclusive job kinds, Run and "Validate this pair", the latter only on a complete grid;
  - "All datasets" runs every grid before any validation;
  - one progress record per task (`dataset`, `dataset_index`, `n_datasets`, `phase`, `done`, `total`), with pairs out of 153 for the grid and replicates out of R + S for validation;
  - a cancelled grid offers "Continue (k of 153 pairs)", and a cancelled validation is discarded.

  Still open here: what, if anything, a partial grid shows.
- Interactive heatmaps over g × s: one metric at a time (Neighbour Agreement, Information Retention, Fragmentation, Seed-Noise Floor, descriptive metrics), with non-Qualifying Pairs marked by their reason codes, the near-best set highlighted, and the chosen pair marked.
- The Pair Constraints panel ([Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md)): editable values, a confirm button that recomputes the selection, Reset to defaults, the shared set vs an "apply to this dataset only" override, and the "Custom constraints" label.
- Inspecting any pair: its metrics, its Clusters, and a CHAMP plot (each Admissible Partition's Q(γ) line, the envelope, the domains, the γ estimates, the Selected Resolution).
- The selection explained in plain language (the template in ticket 06, including the no-qualifying-pair message), and the validation results with any reported failures.
- Cross-dataset comparison: the five datasets side by side.
- "Apply to Workbench" and "Export tables". Apply's behaviour is fixed by [Apply-to-Workbench semantics](09-apply-to-workbench.md): available on any pair with a Selected Partition, disabled with the reason code otherwise. The Workbench shows a provenance line after Apply. Still open here: where the button sits, and how the pair panel shows the Workbench γ and seed or the `not_reproduced` flag.
