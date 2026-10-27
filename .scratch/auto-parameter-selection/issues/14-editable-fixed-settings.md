# Editable fixed settings
Type: grilling
Status: resolved
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
- From [Shipping Parameter Selection results in an App Bundle](13-shipping-results-in-an-app-bundle.md): bundles ship only default-settings results, so a non-default fixed setting always computes locally, and the loading panel gives "Custom settings" as its reason.
- From [Exports and documentation](11-exports-and-documentation.md): `parameter_selection.json` records every fixed setting, and `selection.csv` and `selection_report.md` carry the constraints label. Whatever label this ticket picks for non-default fixed settings goes in those same three places.

## Answer

Decided by grilling with the researcher, 2026-10-26. Checked against `network/model.py` (`Settings`), `network/cluster.py` (`detect`), the Workbench controls in `app/layout.py`, `edit_removed` in `app/callbacks.py` and `config/network.toml`.

**A glossary term:** these are the **Selection Settings** (CONTEXT.md): the choices that fix every Threshold Pair's Selected Partition, so changing one needs a new run, unlike a Pair Constraint. The Controls column's section is renamed "Selection settings"; "fixed settings" is avoided.

**What the user can change** (all used by the calculation, all in `grid_key()`)
- **Hidden tags**: the Workbench's Genre Tag checklist and its "hide each dataset's defining tag" toggle.
- **Removed tags**: a list of tag ids (see below).
- **Minimum Months**: the Workbench's 0–60 slider.
- **Clustering Weight**: Lift (default) or Shared games. The CHAMP and γ̂ formulas do not depend on the weight (Research 01). The guide says Lift is the studied default, and that γ̂ is a heuristic outside unweighted multigraphs whichever weight is used.
- **Minimum Multi-Tag Clusters**: an integer 1–10, default 3. If the Pair Constraints' maximum is on and below a new minimum, it is raised to match and shows under "Custom constraints".
- One set applies to all five datasets. There is no per-dataset override, so Run → All datasets uses one `SelectionSettings`.

**What the user cannot change in the mode**
- **Algorithm**: Leiden only in v1, shown read-only with a one-line reason. The scan path (`leiden_scan` shares `detect`'s igraph construction) and Apply's reproduction search were built and measured on Leiden. This amends the map Note that said the user can change the algorithm.
- **The Parameter Grid** (g 3–20, s 2–12, s ≤ g) and the **10 scan seeds**: shown read-only, changeable only in `[parameter_selection]`.
- **R and S** (100 each): shown read-only, config only, as [Validation design](07-validation-design.md) left them.
- **The γ scan range is no longer a setting at all.** 0.25–3.00 was a convention, never justified from the graph. It is to be **derived per graph** from graph-specific bounds. See [Graph-specific γ bounds](15-graph-specific-gamma-bounds.md) and [Graph-specific γ scan](16-graph-specific-gamma-scan.md), which reopen the scan and CHAMP-range parts of [Resolution-selection rules](03-resolution-selection-rules.md).

**Removed tags**
- The mode keeps its own staged **Removed tags** list, filled three ways:
  - a tag picker in Selection settings;
  - a "Remove" action on a tag in the Pair Inspector's Clusters list;
  - **"Copy from Workbench"**, which copies the Workbench's current hidden tags, Minimum Months, Clustering Weight and removed tags into the staged edits (never g, s, γ or seed).
- There is no live link to the Workbench. A Workbench removal never changes the mode's settings key by itself.
- One list applies to every dataset, as in the Workbench. A tag a dataset lacks is ignored.
- A removed tag is absent from every network the run builds: each pair's network, each null replicate's shuffled table and each subsample. It never counts in Information Retention. Any removal makes the run "Custom settings".

**Editing and confirming** (mirrors the Pair Constraints panel)
- Edits are staged. **"Use these settings"** switches the mode to that settings key, and **"Reset to defaults"** restores the configured defaults.
- After the switch the mode shows what the cache holds for that key (shipped results, or an earlier custom run), or "not run" with Run enabled. An edit never starts a job by itself. Run computes only what is not cached.
- The active Selection Settings last for the session. The app always opens on the defaults.

**Labelling**
- A second label stands next to the constraints label, independent of it: **"Default settings"** or **"Custom settings: …"**, listing each changed value next to its default (for example "Minimum Months 12 (default 0), Clustering Weight Shared games (default Lift), 2 removed tags (Puzzle, Casual)").
- It appears in the selection explanation, in `parameter_selection.json`, in a `settings_label` column in `selection.csv` and in `selection_report.md`.
- The dataset strip's single "custom" marker shows when either label is custom, and its tooltip says which.
- The loading panel's "Custom settings" reason ([Shipping Parameter Selection results in an App Bundle](13-shipping-results-in-an-app-bundle.md)) uses the same test. Custom settings are never shipped.

**Unchanged under custom settings**
- Apply copies every Selection Setting into the Workbench, removed tags included, as [Apply-to-Workbench semantics](09-apply-to-workbench.md) already lists.
- Run validates the pair chosen under the default constraints, and "Validate this pair" covers any other.

**Handed on**
- To [Graph-specific γ bounds](15-graph-specific-gamma-bounds.md) and [Graph-specific γ scan](16-graph-specific-gamma-scan.md): the γ range.
- To the spec: the Selection settings section's controls, "Copy from Workbench", the Pair Inspector's "Remove" action, `settings_label` in the exports, and the guide sentence on weights and γ̂.
