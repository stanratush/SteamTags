# How does the user move between Cluster Comparison and the Workbench?
Type: grilling
Status: resolved
Blocked by:

## Question

[What does the Cluster Comparison mode look like?](06-look-of-the-mode.md) has no route into the Workbench. [Why does the seed change between cells, and should it be the same for every dataset?](10-seed-per-dataset.md) settled that a dataset on a cell shows its stored Selected Partition, which the Workbench reaches only through the two-decimal γ and the reproducing seed ("Apply to Workbench"), and that some cells are flagged "not reproduced".

Decide:
- whether a Cluster box or a match offers "Open in Workbench", and what it opens: the dataset at that cell's g, s, γ and seed, with the Cluster selected in the Inspector;
- what happens for a "not reproduced" cell, where the Workbench cannot show the same partition, and whether the Cluster's label can differ there;
- whether the Workbench's current g, s and resolution can be sent into the comparison for its dataset (it would then count as "set by hand" under ticket 03), and from where;
- whether the mode's state (included datasets, cells, pair, match) survives a trip to another mode and back, as the open mode and dataset survive a Build switch;
- whether the link to Parameter Selection for selecting a cell brings the chosen cell back to the comparison or only opens the dataset there.

## Comments

- From [Where does each dataset's Network State come from, and how long does a comparison take?](12-compute-and-caching.md): a hand-set or no-run dataset is clustered by a light function tested to give the same partition as `compute_state` at the same settings, so the Workbench at those settings shows the same Clusters; a dataset on a cell shows the stored Selected Partition, so only the cell case can differ from the Workbench.

## Answer

Resolved with the researcher, 2026-11-17.

**Facts from the code that shaped the answer**

- Workbench, Analysis Report mode and Parameter Selection are one page: switching mode only shows and hides blocks (`arrange` in `src/steamstudy/app/callbacks.py`), so every store survives a mode switch. A Build switch rebuilds the page and keeps only `?mode=` and `?dataset=` (ADR 0006).
- Apply to Workbench (`ps_apply`) replaces every Workbench setting with the cell's (g, s, the Selection Settings, the two-decimal γ and seed from `workbench_setting`) and switches mode; the `verify` store adds the provenance line.
- Labels follow from the partition alone (`label_clusters`), so a reproduced cell would keep its labels in the Workbench; a "not reproduced" or "not representable" cell would not.
- Parameter Selection holds its own `ps-dataset` and `ps-pair` stores.

**Decisions**

1. **No route from Cluster Comparison into the Workbench.** No "Open in Workbench" on a dataset, a Cluster or a match. Apply to Workbench stays in Parameter Selection only. A user who wants a cell in the Workbench follows the dataset row's link to Parameter Selection and applies it there. So the label question for "not reproduced" cells does not arise in this mode.
2. **No route from the Workbench into the comparison.** The Workbench's g, s and γ are never sent in; the user types values into the dataset row, which counts as "set by hand" ([Where do each dataset's g, s and resolution come from, and the shared settings?](03-per-dataset-defaults.md)). The comparison and the Workbench are separate, each reached from Parameter Selection.
3. **The comparison's state survives every mode switch**: included datasets, each one's source and values, the chosen pair and its orientation, the chosen match, the minimum similarity and "show weaker". It needs no work (one page). **On a Build switch** the mode stays open (`?mode=`) and starts fresh, every dataset on its pick; nothing else carries over.
4. **The dataset row's link to Parameter Selection** opens that mode on the dataset (`ps-dataset`) with the dataset's current cell highlighted (`ps-pair`); for a hand-set or no-run dataset, on its pick or with no cell highlighted.
5. **Parameter Selection gains "Use in Cluster Comparison"** beside Apply to Workbench, always shown (not only after arriving from the comparison). It sets the highlighted cell as that dataset's values in the comparison (source "cell you selected"; the dataset is included if it was not), recomputes and switches to Cluster Comparison. It is enabled under the same rule as Apply to Workbench (a cell with a Selected Partition) and is **disabled, with a reason in its tooltip, when Parameter Selection's current settings differ from the comparison's shared settings**, because the cell would then come from another run.
6. **Pair Constraints changed in Parameter Selection** reach the comparison on return: a dataset still on the ★ pick follows the new pick; a dataset on a selected cell or set by hand keeps its values. (Cells are read on resolve, per [Where does each dataset's Network State come from, and how long does a comparison take?](12-compute-and-caching.md).)

**Wording** (for the bg catalogue; final review at implementation)

- Button: **Use in Cluster Comparison** · *Използвай в сравнението на клъстери*.
- Disabled reason: "The Cluster Comparison uses other shared settings; this cell comes from a different run." · *Сравнението на клъстери използва други общи настройки; тази клетка е от друго изпълнение.*
- In-app help entry `selection.use_in_comparison` (App controls, Parameter Selection mode): "Put this cell into the Cluster Comparison for this dataset and switch there. Available only when Parameter Selection's settings are the comparison's shared settings." · *Поставя тази клетка в сравнението на клъстери за този набор и превключва към него. Достъпно е само когато настройките на избора на параметри съвпадат с общите настройки на сравнението.*
- User Guide: the Datasets subsection of `## Cluster Comparison mode` says the mode has no route into the Workbench and points to Apply to Workbench; Parameter Selection mode's section gains the button.

**Rejected**

- "Open in Workbench" from a Cluster or a dataset (with the Cluster selected in the Inspector, and a warning for "not reproduced" cells): the researcher keeps Apply to Workbench in Parameter Selection only.
- Sending the Workbench's settings into the comparison: its shared settings usually differ, so it would either import incompatible settings or re-resolve every dataset.
