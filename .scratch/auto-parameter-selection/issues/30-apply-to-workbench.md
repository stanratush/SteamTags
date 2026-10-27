# 30: Apply to Workbench

**What to build:** the Inspector's Apply button replaces the Workbench's Network State with the inspected pair's settings and the cached Workbench γ and seed, then switches to the Workbench. That shows a provenance line checked against the stored membership. A Workbench export made while the line shows records an `applied_from` block.

**Blocked by:** 28

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Apply to Workbench".

- [x] Apply sets the dataset, g, s, Minimum Months, the hidden Genre Tags and defining tag, removed tags, Clustering Weight, algorithm (Leiden), γ and seed. It replaces rather than merges, as `do_open` does. It clears Tidy and the Removal Sensitivity view and switches to the Workbench. There is no confirmation.
- [x] γ and seed are the cached Workbench γ and seed. For `not_reproduced` / `not_representable` pairs: the Selected Resolution rounded to two decimals (at least 0.01) with the main seed.
- [x] Provenance through the `verify` store mechanism. On the first recompute after Apply, the Workbench's Clusters are compared with the stored Selected Partition (ARI over all nodes). The line where `verify-result` sits reads "Applied from Parameter Selection: ‹dataset›, g=…, s=… — Selected Partition reproduced ✓", or "… shows a different partition from the Selected Partition: ARI 0.xx". It stays while the Network State key equals the applied key, and goes as soon as any setting changes. It never enters the key or `state_id`.
- [x] "Export this state" adds `applied_from` to `export.json` while the line shows. It holds the dataset, g, s, the grid key hash, the method version, the Workbench γ and seed, and reproduced or the ARI. It stays outside `state_key`, Open ignores it, and `state_id` is unchanged.
- [x] The Apply help (`selection.apply`) points to ch. 2.
- [x] Tests:
  - Applying a reproducing pair from a cache fixture yields Workbench settings equal to the run's, the reproduced line, and Clusters equal to the stored membership.
  - A patched `not_reproduced` pair applies the fallback and shows the ARI line.
  - Changing g removes the line.
  - An export while the line shows has `applied_from`, with the same `state_id` as an export of the same state without Apply.
  - Opening that export ignores the block.

## Comments

- 2026-10-27, implementation: Implemented in `ps_apply` and `applied_line` (`app/callbacks.py`), and `applied_from` in `app/export.export_zip`. Checked live in the app on a scratch test Build: Apply of overall g=16, s=5 set γ 1.48 and showed "Selected Partition reproduced ✓".
