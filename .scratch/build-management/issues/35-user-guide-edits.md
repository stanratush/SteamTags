# 35: User Guide chapters 1–6, appendix B and bg terms

**What to build:** the edits to User Guide chapters 1–6 and appendix B for Top-N wording, List Size, Tag Depth, Switch Builds, Import Builds and citing by name, in English and Bulgarian together, plus the new bg terms.

**Blocked by:** 22, 26, 27

**Status:** done

Spec: [Build management spec](../spec.md): "Documentation". Decision tickets: [User Guide outline](15-user-guide-outline.md) ([outline](../prototypes/15-user-guide-outline/OUTLINE.md), the per-chapter detail), [Top-N glossary](14-top-n-glossary.md), [grid scaling](11-grid-and-defaults-scaling.md).

- [x] Top-N wording throughout:
  - generic text says Top-N ("the Top N" as a noun);
  - defaults read "the default List Size of 100", and worked examples keep 100;
  - `top100_<dataset>.csv` keeps its name, with one history sentence;
  - the chapter-5 methods paragraph mirrors the report template with a `‹top_n›` placeholder.
- [x] Chapter 3:
  - List Size and Tags per game (Tag Depth) rows in the settings table, and entries with **In short** (Tag Depth defines "has");
  - Import sentences in Rank and ties, Eligible Pool baseline and Tags per game only;
  - a `*Steam Builds only.*` line under each entry the spec lists;
  - the grid-scaling caveat sentence in Automatic Parameter Selection.
- [x] Chapter 1: *Switch Builds*. Chapter 2: a Build row in the control reference, and the Import filter-slider sentence. Chapter 4: *Import Builds*, *Import folder*, and the new `build.json` keys. Chapter 5: citations quote the Build's name beside the `state_id`, and a new *Cite an Import Build* section. Chapter 6: *Imported data*, and the caveat to compare states only at the same Tag Depth and List Size.
- [x] Appendix B: the Steam table stays, followed by a generated *Import Builds* section from issue 22's registry (new or renamed columns, one line of absent Steam columns, and "every other column is as above"; `would_be_rank_<dataset>` is one row). The bg appendix is generated the same way.
- [x] `docs/i18n/bg-terms.md` gains the spec's terms. Catalogue strings containing "Top-100" change key and bg value together.
- [x] `README.md` groups the contents as "Reading results" (0–6) and "Making Builds" (7–8), with links that work once issue 36 lands.
- [x] Tests: `test_guide`, `test_guide_bg` and the parity test pass; the appendix generator test covers the Import section.

## Comments

## Implementation note

- Top-N wording runs through chapters 0–6 (en and bg). "Top 100" stays only where the Steam default is meant. The methods paragraph takes a `{top_n}` placeholder: "Top-100" when every dataset has List Size 100, "Top-N" otherwise (`ps_export`, `selection_text.methods_values`).
- Chapter 3 has new **List Size** and **Tags per game (Tag Depth)** entries, plus ties at the last rank and the Eligible Pool Import sentence. Entries that apply only to Steam carry a `*Steam Builds only.*` line right under their heading (bg `*Само за компилации от Steam.*`). It is a guide marker (`MARKERS["steam_only"]`), and `_in_short` skips it.
- Appendix B's generated *Import Builds* section, en and bg, already came from issue 22, along with its generator test in `test_import_builds`. Nothing needed changing.
- `bg-terms.md` has the List Size, Tag Depth, Import (*внос* added to superseded), Import Build, Build Draft, raw/lightweight and item/attribute terms.
