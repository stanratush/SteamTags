# 35: User Guide chapters 1–6, appendix B and bg terms

**What to build:** the edits to User Guide chapters 1–6 and appendix B for Top-N wording, List Size, Tag Depth, Switch Builds, Import Builds and citing by name, in English and Bulgarian together, plus the new bg terms.

**Blocked by:** 22, 26, 27

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Documentation". Decision tickets: [User Guide outline](15-user-guide-outline.md) ([outline](../prototypes/15-user-guide-outline/OUTLINE.md), the per-chapter detail), [Top-N glossary](14-top-n-glossary.md), [grid scaling](11-grid-and-defaults-scaling.md).

- [ ] Top-N wording throughout:
  - generic text says Top-N ("the Top N" as a noun);
  - defaults read "the default List Size of 100", and worked examples keep 100;
  - `top100_<dataset>.csv` keeps its name, with one history sentence;
  - the chapter-5 methods paragraph mirrors the report template with a `‹top_n›` placeholder.
- [ ] Chapter 3:
  - List Size and Tags per game (Tag Depth) rows in the settings table, and entries with **In short** (Tag Depth defines "has");
  - Import sentences in Rank and ties, Eligible Pool baseline and Tags per game only;
  - a `*Steam Builds only.*` line under each entry the spec lists;
  - the grid-scaling caveat sentence in Automatic Parameter Selection.
- [ ] Chapter 1: *Switch Builds*. Chapter 2: a Build row in the control reference, and the Import filter-slider sentence. Chapter 4: *Import Builds*, *Import folder*, and the new `build.json` keys. Chapter 5: citations quote the Build's name beside the `state_id`, and a new *Cite an Import Build* section. Chapter 6: *Imported data*, and the caveat to compare states only at the same Tag Depth and List Size.
- [ ] Appendix B: the Steam table stays, followed by a generated *Import Builds* section from issue 22's registry (new or renamed columns, one line of absent Steam columns, and "every other column is as above"; `would_be_rank_<dataset>` is one row). The bg appendix is generated the same way.
- [ ] `docs/i18n/bg-terms.md` gains the spec's terms. Catalogue strings containing "Top-100" change key and bg value together.
- [ ] `README.md` groups the contents as "Reading results" (0–6) and "Making Builds" (7–8), with links that work once issue 36 lands.
- [ ] Tests: `test_guide`, `test_guide_bg` and the parity test pass; the appendix generator test covers the Import section.

## Comments
