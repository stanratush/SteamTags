# Build menu
Type: prototype
Status: resolved
Blocked by: 02, 05, 06, 07, 10

## Question

How the Build menu looks and behaves. The prototype goes in `prototypes/12-build-menu/`, linked from here.

- Where it lives in the app (a third mode, a dialog, a page before the Workbench), and the Build list: name, Snapshot, date, parent, sizes, status.
- Create, duplicate, delete and switch, with the confirmations that [Build identity](07-build-identity-and-lifecycle.md) requires.
- The settings form in three sections (changes the Top-N / reports and analysis / network defaults): inputs, validation, and which edits are marked as changing the Top-N.
- Editing named exclusion rules, Manual Exclusions, Exclusion Overrides and Manual Metadata Entries, with reason and evidence required.
- Progress and failure of a running Build, sized by the [Build timings](02-build-inputs-and-timings.md), and what the user can do meanwhile.
- English and Bulgarian (ADR 0003).

From [tags per game and list size](05-tags-per-game-and-list-size.md): tags per game is one Build-wide input (an integer ≥ 2 or "all", up to 20 for Steam); list size is per dataset (≥ 10). Show each dataset's Eligible Pool size before saving.

From [switching and cache separation](10-switching-and-cache-separation.md): a switch navigates the tab to `/build/<snapshot>/<build_id>` and asks before cancelling that tab's running analysis jobs. A Build run is server-wide, one at a time, and survives a switch. Delete is refused only for the tab's own Build and warns when it will cancel a job on that Build. App Bundles show a switcher only (hidden for one Build). Show the "This Build no longer exists" page.

## Prototype

[PROTOTYPE-build-menu.html](../prototypes/12-build-menu/PROTOTYPE-build-menu.html) (double-click; `?variant=A|B|C`, or ← → keys): A Builds mode, B Switcher + dialog, C Lineage page. Real Builds, Eligible Pools, exclusion counts and config; demo Build and drafts marked. The state box (bottom left) can make the next run fail, start a tab job, or show a deleted-Build URL.

## Answer

Chosen with the researcher, 2026-11-07: **variant B (Switcher + dialog) with the lineage tree from variant C**, drawn as variant D in the prototype. A (a fourth "Builds" mode) and C (a separate page before the Workbench) are not used, except for C's tree.

1. **Where it lives:** no new mode or page. The Build name in the header is a dropdown, and the Workbench, Analysis Report and Parameter Selection modes stay as they are underneath it.
2. **The dropdown is a lineage tree**, one per Snapshot, rooted at `config/` defaults: each Build sits under its parent, and drafts sit under the Build they started from. A Build whose parent was deleted moves to the root and reads "from a deleted Build". Each Build row shows its name, chips (✓ open in this tab, latest, test), date and Top-N summary (list sizes, Tag Depth). Each draft row shows its status (draft / running % / failed), how many settings changed, and when it was last saved. Clicking a Build switches to it; clicking a draft opens its dialog; clicking `config/` starts a draft from the defaults. Duplicate and Delete appear when you hover a Build row, Discard when you hover a draft row. Below the tree: Duplicate the open Build, and Manage Builds….
3. **Manage Builds…** is a dialog with the same tree plus folder and app-cache sizes.
4. **Duplicate** asks which Snapshot to use (default: the parent's), then opens the new draft's dialog.
5. **A draft opens in a full-screen dialog of steps:** Start (name, description, started from, Snapshot, last failure) → Changes the Top-N (datasets with list size and Eligible Pool, Tag Depth, ordered Exclusion Rules between the fixed rules) → Curation (Manual Exclusions, Exclusion Overrides, Manual Metadata Entries, each needing a reason and evidence; would-be Overall ranks of excluded games act as a shortcut for adding an Override) → Reports and analysis → Network defaults → Review. A step's marker turns green when it has changes and red when it needs a fix. The draft is saved automatically; Close keeps it.
6. **Build only from the Review step.** Review lists every changed setting (source value struck through, draft value beside it, Top-N changes badged), each dataset's list size against its Eligible Pool, the games that would enter the Overall list, the warning for identical settings, and the problems still to fix, including the per-dataset warnings from [grid scaling](11-grid-and-defaults-scaling.md) (largest g, default g or s, or `min_support` above N; a grid with no pairs is refused), which also show on the Network defaults step.
7. **A running Build** shows as a strip under the header in every mode: its stage, seconds against the estimate (~24 s lightweight), and a bar. It is server-wide and survives switching. When it finishes, the strip offers "Open it in this tab" (it does not switch on its own); when it fails, it offers "Open the draft", and the dialog shows the failure.
8. **Switch, delete and missing Builds** follow [Build identity](07-build-identity-and-lifecycle.md) and [switching](10-switching-and-cache-separation.md), as drawn in the prototype. Switching asks before cancelling this tab's jobs. Deleting the open Build is refused; deleting another Build shows its sizes, the bundles that name it, exports that will stop opening, where `latest` moves, and the Builds and drafts that will lose their parent. The "This Build no longer exists" page links to the latest Build.
9. **App Bundles** show the same dropdown tree with switching only (no `config/` row, drafts, Duplicate, Delete or Manage), hidden when a bundle ships one Build.
10. **English and Bulgarian:** the menu's own words go through the bg catalogue (ADR 0003). The prototype shows the terms: Build = компилация, Snapshot = моментна снимка, Build Draft = чернова на компилация.

Open, left to the implementation: how quickly the Eligible Pool can be shown during an edit. The prototype only estimates it; the real number needs exclusions run on the lightweight Snapshot (a Build takes about 24 s from it). This is on the map under "Not yet specified".
