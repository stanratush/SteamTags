# 09: Readable Analysis Report §1

**What to build:** Analysis Report §1 shows the Network State as a short table a reader can cite, with the raw JSON behind a toggle.

**Blocked by:** 02

**Status:** ready-for-agent

Spec: [App readability spec](../spec.md): "Analysis Report mode §1".

- [ ] The `state_id` sits on top, prominent, and copies on click.
- [ ] A table lists:
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
- [ ] When no game of the dataset carries a hidden tag, its name comes from the Build's genre-tag list or the dataset's defining tag (e.g. Experimental 13782 and Tabletop 17389 in Overall).
- [ ] The raw state-key JSON sits behind "Show JSON" (`<details>`) and stays in the export. The page never lists one tag id per line.
- [ ] Tests:
  - Every Network State field is in the table.
  - Hidden tags show names, never bare ids.

## Comments
