# 09: Readable Analysis Report §1

**What to build:** Analysis Report §1 shows the Network State as a short table a reader can cite, with the raw JSON behind a toggle.

**Blocked by:** 02

**Status:** done

Spec: [App readability spec](../spec.md): "Analysis Report mode §1".

- [x] The `state_id` sits on top, prominent, and copies on click.
- [x] A table lists:
  - dataset and Build;
  - games after the Minimum Months Filter (of 100);
  - Minimum Months Filter;
  - minimum games per tag;
  - minimum shared games;
  - hidden tags by name;
  - removed tags by name;
  - Clustering Weight;
  - algorithm;
  - γ;
  - seed;
  - R;
  - K.
- [x] When no game of the dataset carries a hidden tag, its name comes from the Build's genre-tag list or the dataset's defining tag (e.g. Experimental 13782 and Tabletop 17389 in Overall).
- [x] The raw state-key JSON sits behind "Show JSON" (`<details>`) and stays in the export. The page never lists one tag id per line.
- [x] Tests:
  - Every Network State field is in the table.
  - Hidden tags show names, never bare ids.

## Comments

**2026-10-06 (implemented):** `view.state_table` renders §1: the `state_id` large and click-to-copy (the `.copy-id` handler from issue 08), a table with one row per state-key field (each row's tooltip names its key field; plus games after the filter), tags by name from the dataset's games, the Build's genre-tag list and the dataset's defining tag, and the raw key behind "Show JSON" with one field per line (`view.key_json`). The export is unchanged. Browser check in headless Chrome on the real Build: Overall §1 lists "Strategy, Action, …, Puzzle, Experimental, Tabletop" (the last two from the genre-tag list), R 20, K 10, method version 1.
