# Parameter Selection mode prototype
Type: prototype
Status: resolved
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

## Answer

Decided by the researcher, 2026-10-26, from three variants of [the prototype](../prototypes/10-parameter-selection-mode/README.md): **A · Three panes**, unchanged. B (a report page) and C (five heatmaps side by side with a bottom sheet) were rejected. The prototype runs on the real grid and selection of Build `20261008T221504Z-7a23ae9f`, with live CHAMP plots and Clusters.

**Layout: shaped like the Workbench, in three panes**
- **Controls column** (left), top to bottom:
  - **Run**: "Run all datasets", "Run ‹dataset›", and Cancel while a job runs. One row per dataset gives its phase and a progress bar, for example "grid 87 of 153 pairs", "validation 40 of 200 replicates", "grid done, not validated" or "not run". A cache line follows, such as "Results from the app cache: Build …, settings key …, method v1".
  - **Pair Constraints**: always open.
  - **Fixed settings**: read-only for now.
- **Main column**, top to bottom:
  - the **dataset strip**: five buttons, each showing its chosen pair and Neighbour Agreement ("★ 14·2 NA 0.99"), "no qualifying pair", "not run" or "grid k of 153", plus a "custom" marker. Clicking one switches the dataset;
  - the metric picker;
  - one large g × s **heatmap** with its key;
  - a "**Why this pair**" card with the selection explanation;
  - the chosen pair's **validation** card.
- **Pair Inspector** (right), top to bottom:
  - the pair's title and status badges;
  - **Apply to Workbench**;
  - the pair's metrics;
  - the CHAMP plot;
  - the Selected Partition's Clusters;
  - compact validation.
  
  It shows the current dataset's chosen pair until the user clicks a cell.
- **Cross-dataset comparison** in this mode is the dataset strip: five datasets, each with its chosen pair and Neighbour Agreement, one click away from the others. Variant C's "the same pair in every dataset" row was not adopted. Whether anything more is needed stays in the map's fog.

**Heatmap**
- One metric at a time, from a segmented control: Neighbour Agreement, Information Retention, isolated share, Multi-Tag Clusters, Seed-Noise Floor and Q. A descriptive metric carries the tag "Descriptive: not comparable across pairs" and a grey colour scale.
- The marks:
  - ★ the chosen pair;
  - an orange outline on each pair in the near-best set;
  - a dark outline on the inspected pair;
  - on each non-qualifying cell, one letter per failing reason: P no Selected Partition, A no Neighbour Agreement, N too few comparable neighbours, R retention, I isolated share, L LCC share, K too many Clusters. The key spells them out.
- Hovering a cell shows its value, NA, tags and Multi-Tag Clusters, and either "✓ qualifies" or each failing reason in words.
- Clicking a cell inspects it.

**What an unfinished grid shows** (a run in progress, or a cancelled one)
- Computed cells fill in as they arrive; pending cells are grey.
- A cell's Neighbour Agreement appears only once its grid neighbours are computed.
- No ★, near-best outline or explanation is shown until the grid is complete. The card says "No selection yet. k of 153 pairs are computed; the selection needs the whole grid."
- A cancelled run offers "Continue (k of 153 pairs)" in the Run section.
- When nothing has been run, the main column says "No results for these settings yet" and points to Run.

**Pair Constraints panel**
- One field per constraint, each with its default beside it and a "changed" marker. An empty maximum Multi-Tag Clusters means "off".
- "Apply to: All five datasets | ‹dataset› only" chooses between the shared set and a per-dataset override.
- Confirm is disabled until something changes, with "Unconfirmed changes" shown meanwhile. "Reset to defaults" sits next to it.
- Below them is the "Default constraints" label, or "Custom constraints: …" listing each changed value next to its default.

**Apply to Workbench, and the Workbench γ and seed**
- Apply is the Inspector's primary button, at its top, under the title and badges.
- The line beneath it reads either "Workbench γ 1.09, scan seed 2: reproduces the Selected Partition ✓" or, for `not_reproduced`, "Workbench γ 1.23, main seed: not_reproduced, shows a different partition (ARI 0.83)" in warning colours.
- Without a Selected Partition the button is disabled and shows its reason code.

**Validation**
- The chosen pair's full block (ticket 07's template, the per-Cluster table, both caveats) sits under "Why this pair".
- The Inspector has a compact version for any inspected pair: the two verdict tags and the median ARIs.
- An unvalidated pair shows "Not validated" and "Validate this pair". When custom constraints chose it, a note says "Validation ran for g = …, s = …, the pair chosen under the default constraints."

**Not prototyped** (left to the spec):
- the Workbench's medium and narrow forms (pill bar, floating Inspector) for this mode;
- a real job's progress callbacks: the prototype re-renders the whole page on every tick.

**Handed on**
- To [Exports and documentation](11-exports-and-documentation.md): where "Export tables" goes. The obvious home is the Controls column, under Run.
- To a new ticket, [Editable fixed settings](14-editable-fixed-settings.md): the Controls column's read-only "Fixed settings" section is where that question now lands.

## Comments

- 2026-10-26: Prototype built for review: [prototypes/10-parameter-selection-mode/](../prototypes/10-parameter-selection-mode/README.md). It has three layouts (A: three panes, B: report page, C: five side by side) over the real grid and selection, with live CHAMP plots and Clusters. Waiting on the researcher's reaction before resolving.
- 2026-10-26: The researcher chose variant A, "Three panes", as it stands.
- 2026-10-26: [Does Neighbour Agreement favour high g?](12-neighbour-agreement-high-g-bias.md) adds a Pair Inspector table: one row per neighbour link with direction, status, ARI, tag overlap, Edge Overlap and an "identical graph" marker. The "Why this pair" text gains the sentences that ticket lists.
