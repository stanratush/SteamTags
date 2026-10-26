# Parameter Selection mode prototype
Type: prototype
Status: open
Blocked by: 04

## Question

How should the Parameter Selection mode look and behave? Build a rough, clickable prototype (`prototypes/10-parameter-selection-mode/`) to react to:

- Start and progress: running one dataset or all five; per-dataset progress; reusing cached results.
- Interactive heatmaps over g × s: one metric at a time (Neighbour Agreement, Information Retention, Fragmentation, Seed-Noise Floor, descriptive metrics), with non-Qualifying Pairs marked by their reason codes, the near-best set highlighted, and the chosen pair marked.
- The Pair Constraints panel ([Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md)): editable values, a confirm button that recomputes the selection, Reset to defaults, the shared set vs an "apply to this dataset only" override, and the "Custom constraints" label.
- Inspecting any pair: its metrics, its Clusters, and a CHAMP plot (each Admissible Partition's Q(γ) line, the envelope, the domains, the γ estimates, the Selected Resolution).
- The selection explained in plain language (the template in ticket 06, including the no-qualifying-pair message), and the validation results with any reported failures.
- Cross-dataset comparison: the five datasets side by side.
- "Apply to Workbench" and "Export tables".
