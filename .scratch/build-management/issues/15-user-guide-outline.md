# What does the User Guide cover for the Build menu and Import Builds?
Type: prototype
Status: resolved
Blocked by: 14

## Question

The User Guide (`docs/user-guide/`, with its `bg/` translation under ADR 0003) has no section for making Builds in the app or for opening imported data. It says "Top-100" 33 times, 20 of them in the metric reference, and its column index (appendix B) is generated from `export/schema.py`, which now has Import variants ([export schema](13-export-schema.md)).

Make a rough outline to react to, and decide:
- which pages gain sections for the Build menu (the steps of a draft, Review, the running-Build strip, switching, Manage Builds) and for Import Builds (the Import file format, what is hidden, the "Game means item, Tag means attribute" note);
- how the Top-100 → Top-N rename sweeps the guide and the bg catalogue, following the glossary decided in [the Top-N glossary ticket](14-top-n-glossary.md);
- what the Running Guide gains for `steamstudy import` and `snapshot lighten`;
- how appendix B shows the Import variants.

The outline is the decision; writing the full text is implementation.

## Answer

Reacted to with the researcher, 2026-11-07, on the [outline prototype](../prototypes/15-user-guide-outline/OUTLINE.md), which holds the per-chapter detail. Every point was accepted as drafted.

1. **Two new chapters, appended:** `07-making-builds.md` (the Build menu, repository only) and `08-imported-data.md` (Imports and Import Builds). Chapters 1–6 get short edits, and nothing is renumbered, because chapter file names are in every help anchor. `README.md` groups the contents as "Reading results" (0–6) and "Making Builds" (7–8).
2. **Chapter 7 is procedural:** the Build tree, Start a draft, one section per draft step (Start, Changes the Top-N, Curation, Reports and analysis, Network defaults, Review), A running Build, Manage and delete Builds, and Raw and lightweight Snapshots. It has no **In short** blocks. Each step's `?` opens its section, and each section is a help anchor with a `test_guide` case. Hover help on a setting opens its chapter-3 entry. What Review says when the preview is stale waits on [the Eligible Pool preview decision](18-eligible-pool-preview.md).
3. **Chapter 8** opens with a reading note ("read game as item and tag as attribute; entries marked *Steam Builds only* do not apply"). It then covers What an Import is, The Import file (with a five-row example), Making an Import, When an Import is refused (a table of code → meaning → what to do, for every error and warning code), and What changes in an Import Build (the rank source, the filter slider, the extra fields, the hidden settings and why).
4. **Top-N wording:** the guide follows the glossary rule, so generic text always says Top-N ("the Top N" as a noun). Defaults are stated as "the default List Size of 100", and worked examples keep 100. `top100_<dataset>.csv` stays, with a sentence on its history. The chapter-5 methods paragraph mirrors the report template, so it shows a `‹top_n›` placeholder.
5. **Chapter 3:** the settings table gains List Size and Tags per game (Tag Depth). Both get new entries with **In short**, and Tag Depth is where "has" is defined. An Import sentence is added only to Rank and ties, Eligible Pool baseline and Tags per game. A `*Steam Builds only.*` line goes under each entry that cannot apply to an Import (Monthly Avg. Players, Mean Monthly Players, Months Observed, Release Month, Release-month gap, Placeholder Rows, Store metadata, Listing rank and the depth check, Archived tag category, Genre frequency). The grid-scaling caveat sentence joins Automatic Parameter Selection.
6. **Chapters 1, 2, 4, 5, 6:**
   - **1:** a new *Switch Builds* section.
   - **2:** a Build row in the control reference, and the Import filter-slider sentence under the Minimum Months Filter.
   - **4:** *Import Builds* and *Import folder* sections, plus the new `build.json` keys.
   - **5:** citations quote the Build's **name** beside the `state_id`, and a new *Cite an Import Build* section uses `import_id` + `import_sha256` and the data's own source.
   - **6:** an *Imported data* section, and a caveat to compare states only at the same Tag Depth and List Size.
7. **Appendix B:** the Steam table stays, followed by a generated *Import Builds* section. It lists only the columns that are new or renamed, then one line of the Steam columns absent from Import Builds, and says "every other column is as above". `would_be_rank_<dataset>` is one row. The bg appendix is generated the same way.
8. **bg:** translated in the same change, since the parity test requires it. Terms for `bg-terms.md`: Top-N Dataset = набор Топ-N, List Size = размер на списъка, Tag Depth / tags per game = дълбочина на таговете / тагове на игра, Import = импорт (pl. импорти; _avoid_ внос), Import Build = компилация от импорт, raw / lightweight Snapshot = сурова / олекотена моментна снимка (_avoid_ пълна), item / attribute = елемент / атрибут (reading note only). Catalogue strings that contain "Top-100" change key and bg value together.
9. **Running Guide (English only):**
   - *Build* says the datasets and List Sizes come from config.
   - New *Lightweight Snapshots* section (after *Collect*) and new *Import* section (after *Build*).
   - *Folder layouts* gains `imports/`, Import Builds, drafts, the lightweight zip, and the job store moving out of `app_cache/`.
   - *The app* links chapter 7.
   - Bundle docs are left to [bundles and in-app Builds](16-bundles-and-in-app-builds.md).
