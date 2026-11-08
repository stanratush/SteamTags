# 28: Build tree, Manage Builds and Delete

**What to build:** the header's Build name becomes a dropdown lineage tree, one per Snapshot or Import (rooted at `config/` or "Import defaults"), with switching, Duplicate, Delete and Discard. Manage Builds… is a dialog showing the same tree with sizes. App Bundles get the tree for switching only.

**Blocked by:** 24, 27

**Status:** done

Spec: [Build management spec](../spec.md): "The Build menu" (tree, Manage Builds, Duplicate, Delete), "Build identity and lifecycle" (Delete). Decision ticket: [Build menu](12-build-menu.md); [prototype](../prototypes/12-build-menu/PROTOTYPE-build-menu.html), variant D.

- [x] Tree rows as in the spec:
  - Build rows: name, chips (✓ open in this tab, latest, test), date, Top-N summary.
  - Draft rows: status, number of changed settings, last saved.
  - Root rows. Each Snapshot shows its forms (raw, lightweight).
  - A Build whose parent is gone sits at the root with "from a deleted Build".
- [x] Clicking a Build switches (issue 27). Clicking the root starts a draft (issue 24), and clicking a draft opens it (an empty dialog stub until issue 29).
- [x] Hover actions: Duplicate and Delete on Builds, Discard on drafts. Below the tree: Duplicate the open Build, Import data… (a stub until issue 33), Manage Builds….
- [x] Duplicate asks for the Snapshot (default: the parent's; Import Builds stay within their Import).
- [x] Delete shows `delete_build`'s confirmation data, refuses the tab's own Build ("switch to another Build first"), and cancels jobs on that Build first.
- [x] Manage Builds… shows the same tree with folder and app-cache sizes.
- [x] The menu appears only when the app runs from the repository. App Bundles show the tree with switching only (no root row, drafts, Duplicate, Delete, Manage or Import), hidden for a single-Build bundle.
- [x] bg entries for every string. Terms: Build = компилация, Snapshot = моментна снимка, Build Draft = чернова на компилация.
- [x] Tests:
  - The tree's structure for a fixture builds root (parents, orphans, drafts, two Snapshots, an Import).
  - Delete refuses the open Build and deletes another.
  - A bundle layout hides the editing actions.

## Comments

## Implementation note

`build_tree.py` (Dash-free: `build_tree`, `walk`, `BuildNode`, `SourceTree`, `is_bundle`) feeds `app/build_menu.py` (header button, tree, hover actions, Duplicate/Delete/Discard dialogs, Manage Builds… with folder and app-cache sizes). `editable()` hides every editing control in an App Bundle; `menu_visible()` hides the menu for a single-Build bundle. bg strings are in `i18n/bg/build_menu.py`. Tests are in `tests/test_build_menu.py` (tree lineage/orphans/drafts/two Snapshots/Import, Delete refuses the open Build, a bundle tree only switches).

Delete refuses the tab's own Build, and first stops the jobs other tabs run on it. Removal Sensitivity and Parameter Selection jobs record themselves in `app/job_registry.py` while they run (a file per process in the app's job store). `build_admin.delete_build(..., cancel_jobs=...)` stops them with their worker processes, then removes the folder, retrying while Windows releases files. Draft rows show their number of changed settings. A Build duplicated from another Snapshot names its parent and Snapshot. Test: a job holding a file open in the Build is stopped, and the folder is removed.
