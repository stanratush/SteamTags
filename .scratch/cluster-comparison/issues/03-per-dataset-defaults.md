# Where do each dataset's g, s and resolution come from, and the shared settings?
Type: grilling
Status: resolved
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

## Answer

Resolved with the researcher, 2026-11-17.

**Facts from the code that shaped the answer**

- Automatic Parameter Selection is Leiden-only and defaults to Lift as the Clustering Weight; the Workbench defaults to Louvain, shared-game count, g = 8, s = 8, γ = 1.0 (`config/network.toml`). A run's cells hold only under that run's Selection Settings.
- "Apply to Workbench" does not take the Selected Resolution itself: it takes the two-decimal γ and the seed at which Leiden reproduces the cell's Selected Partition exactly (`workbench_setting` in `src/steamstudy/network/selection.py`). That seed can differ from cell to cell.
- The defining Tag is hidden per dataset by the `hide_defining_tag` rule, so the hidden set already differs per dataset.
- A Build is made from one Snapshot or one Import, so all its datasets share one filter field.

**Per-dataset values**

1. **The values come from a cell of the dataset's Automatic Parameter Selection run**, taken the way "Apply to Workbench" takes them: the cell's g and s, and the two-decimal γ and seed that reproduce its Selected Partition. What the Workbench last showed is never a source.
2. **The dataset starts on the run's pick** (the starred cell). The user may select any other cell that has a Selected Partition; a cell without one cannot be selected, as "Apply to Workbench" is disabled for it.
3. **The pick is decided by the Pair Constraints currently set in Parameter Selection for the tab**, so the comparison's star is always the star shown there. The comparison has no constraints of its own.
4. **A dataset with no run under the shared settings can still be included.** It starts from the Build's network g, s and resolution with the main seed, is flagged "no Automatic Parameter Selection run", and links to Parameter Selection.
5. **g, s and the resolution stay editable.** Changing g or s to a cell that has a Selected Partition counts as selecting that cell (γ and seed follow). Changing g or s to any other pair, or editing γ, marks the dataset "set by hand": γ stays as typed and the seed is the main seed.
6. **Limits on g and s are the Workbench's**, not the Parameter Grid's. A pair outside the grid simply has no cell to follow.
7. **Each dataset carries one source line with four states:** the pick; a cell the user selected; set by hand; no run. The wording is left to the wording work.

**Shared settings**

8. **The mode has its own controls for the shared settings**, starting from the Parameter Selection settings (Leiden, Lift, its Minimum Months Filter, its removed Tags), not from the Workbench's current ones.
9. **"Shared hidden Tags" means the rules** (Genre Tags hidden; defining Tag hidden) and the removed Tags. Each dataset's actual hidden set follows from the rules, as in Parameter Selection. Whether the defining Tag needs a rule in the matching itself stays in Not yet specified.
10. **The Minimum Months Filter is one shared control.** The Import filter-field mismatch only arises across Builds and belongs to [Can datasets of different Builds be compared?](08-cross-build-comparison.md)
11. **Changing a shared setting re-resolves every dataset** against the run for the new settings: its pick if that run exists, "no run" if not. Stale cell values are never kept. Hand edits are lost, and a notice says so.

**Left open**

- **The seed.** Point 1 makes the seed per-dataset (it travels with the cell), which amends the charted "seed is shared". The researcher accepted this provisionally and asked for it to be examined on its own: [Why does the seed change between cells, and should it be the same for every dataset?](10-seed-per-dataset.md) Points 1, 4 and 5 follow that ticket's answer where they mention the seed.
- **How the user selects a cell** (a grid inside the mode, or a jump to Parameter Selection): [What does the Cluster Comparison mode look like?](06-look-of-the-mode.md)

_Amended by [What happens to a defining Tag in a match when Genre Tags or defining Tags are shown?](14-defining-tag-in-a-match.md): the mode has no "defining Tag hidden" control; each dataset's own defining Tag is always hidden._
