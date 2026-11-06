# Build menu
Type: prototype
Status: open
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
