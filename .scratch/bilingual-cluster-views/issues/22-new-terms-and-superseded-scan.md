# 22: Bulgarian terms for the new features, and the superseded-word scan

**What to build:** before any Bulgarian is written, the term table covers the words that features 2–4 introduced, agreed with the researcher. A **Superseded words** section and a test that scans for those words are added. The bulk slices then all start from the same table.

**Blocked by:** 14, 16, 18, 19, 20, 21

**Status:** ready-for-human

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulgarian terms and numbers", "Corrections flow through the term table", "Resolved while writing this spec". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

This is a HITL session. The agent drafts; the researcher decides every row.

- [ ] **The agent drafts rows** with a recommended Bulgarian word and an Avoid cell, from the English that features 2–4 shipped:
  - Domain terms: Connection Ratio, Connection Share, Edge Appearance.
  - Panels and UI names: Connections matrix, Cluster map, pair view, Connections (Inspector section), Games (Inspector section), Edges card, Hide links below, Links between Clusters, Matched, "of its tags", Show all, Ratio | Share, Matrix | Table.
  - Edge Appearance words: width, scaling (linear, square root, log), colour modes (one colour, By Cluster, within vs between, by value), strength.
- [ ] **The researcher accepts or changes each row.** The agent writes the agreed rows into `bg-terms.md`, in the right sections.
- [ ] **Superseded words**: a new section in `bg-terms.md` with a short explanation and a two-column table: stem, and allowed phrases. It starts with *Жакар*, *Лайден*, *сийд* and *билд*, plus anything the researcher adds now.
- [ ] **Scan test** (`tests/test_i18n.py`):
  - It parses the Superseded table and scans every string in `src/steamstudy/i18n/bg/` and every file under `docs/user-guide/bg/`.
  - Each stem is matched at the start of a word, case-insensitively (`\b<stem>\w*`), skipping the occurrences inside an allowed phrase.
  - It fails on a hit, naming the file and the word.
  - It passes on today's (empty) Bulgarian, and fails on a fixture string containing *сийда*.
- [ ] The `bg-terms.md` intro says how a review correction flows: change the row, move the old word to Avoid and to Superseded, then sweep.

## Resolution

<!-- Filled in at the end of the session: the rows agreed, and any the researcher changed. -->
