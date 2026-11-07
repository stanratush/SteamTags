# 28: Build tree, Manage Builds and Delete

**What to build:** the header's Build name becomes a dropdown lineage tree, one per Snapshot or Import (rooted at `config/` or "Import defaults"), with switching, Duplicate, Delete and Discard. Manage Builds… is a dialog showing the same tree with sizes. App Bundles get the tree for switching only.

**Blocked by:** 24, 27

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "The Build menu" (tree, Manage Builds, Duplicate, Delete), "Build identity and lifecycle" (Delete). Decision ticket: [Build menu](12-build-menu.md); [prototype](../prototypes/12-build-menu/PROTOTYPE-build-menu.html), variant D.

- [ ] Tree rows as in the spec:
  - Build rows: name, chips (✓ open in this tab, latest, test), date, Top-N summary.
  - Draft rows: status, number of changed settings, last saved.
  - Root rows. Each Snapshot shows its forms (raw, lightweight).
  - A Build whose parent is gone sits at the root with "from a deleted Build".
- [ ] Clicking a Build switches (issue 27). Clicking the root starts a draft (issue 24), and clicking a draft opens it (an empty dialog stub until issue 29).
- [ ] Hover actions: Duplicate and Delete on Builds, Discard on drafts. Below the tree: Duplicate the open Build, Import data… (a stub until issue 33), Manage Builds….
- [ ] Duplicate asks for the Snapshot (default: the parent's; Import Builds stay within their Import).
- [ ] Delete shows `delete_build`'s confirmation data, refuses the tab's own Build ("switch to another Build first"), and cancels jobs on that Build first.
- [ ] Manage Builds… shows the same tree with folder and app-cache sizes.
- [ ] The menu appears only when the app runs from the repository. App Bundles show the tree with switching only (no root row, drafts, Duplicate, Delete, Manage or Import), hidden for a single-Build bundle.
- [ ] bg entries for every string. Terms: Build = компилация, Snapshot = моментна снимка, Build Draft = чернова на компилация.
- [ ] Tests:
  - The tree's structure for a fixture builds root (parents, orphans, drafts, two Snapshots, an Import).
  - Delete refuses the open Build and deletes another.
  - A bundle layout hides the editing actions.

## Comments
