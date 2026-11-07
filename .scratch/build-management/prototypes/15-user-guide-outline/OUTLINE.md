# PROTOTYPE: User Guide outline for the Build menu and Import Builds

Throwaway outline for [the User Guide outline ticket](../../issues/15-user-guide-outline.md). It shows *what goes where*, not the final text. Each **D-n** is a decision to react to. The recommendation comes first, then the alternatives.

Constraints it respects: the bg guide is a parallel copy with `{#english-slug}` heading ids, and `test_guide_bg` fails on a missing heading (ADR 0003). The Running Guide is English only. Appendix B is generated from `export/schema.py`. Every declared file needs a paragraph in chapter 4 (`test_guide`). The methods paragraph in chapter 5 must equal the report template.

---

## D-1. Where the new material lives

**Recommended: two new chapters appended as 7 and 8. Short edits to 1–6. No renumbering.**

| # | File | Audience | New / changed |
|---|---|---|---|
| 1 | `01-getting-started.md` | everyone | changed: the Build dropdown, a new *Switch Builds* section |
| 2 | `02-app-controls.md` | everyone | changed: a Build row in the control reference, Dataset row wording |
| 3 | `03-metric-reference.md` | everyone | changed: Top-N sweep, new List Size and Tag Depth entries, Import sentences, Steam-only markers |
| 4 | `04-files.md` | everyone | changed: a new *Import Builds* section and an *Import folder* section, metadata keys |
| 5 | `05-citing-and-reproducing.md` | everyone | changed: Build name in citations, *Cite an Import Build*, template placeholder |
| 6 | `06-known-limitations.md` | everyone | changed: an *Imported data* section, the Tag Depth and List Size caveats |
| **7** | **`07-making-builds.md`** | repository only | **new**: the Build menu |
| **8** | **`08-imported-data.md`** | whoever opens an Import Build | **new**: Imports and Import Builds |
| B | `appendix-b-column-index.md` | everyone | regenerated: an *Import Builds* section |

Why append: chapter file names are in every in-app help anchor and in-guide link (`03-metric-reference.md#…`), and renumbering would touch all of them for no reader gain. The contents list in `README.md` can still group them: "Reading results" 0–6, then "Making Builds" 7–8.

*Alternatives:*
- (a) Put the Build menu inside chapter 2 as `## The Build menu`. Rejected: chapter 2 is for researchers with an App Bundle, who never see the menu, and it is already 643 lines.
- (b) Merge 7 and 8 into one chapter. Possible, but an Import Build may reach a reader who never makes Builds (if [bundles and in-app Builds](../../issues/16-bundles-and-in-app-builds.md) allows bundling them), and chapter 8 is what that reader needs.

---

## D-2. Chapter 7: Making Builds in the app (repository only)

Procedural, like the *Task recipes* in chapter 2: no **In short** blocks. Settings that need interpretation link to their chapter-3 entry, and the dialog's hover help opens that entry, not chapter 7. Each step's `?` button opens its chapter-7 section, so each section is a help anchor and gets a `test_guide` case.

```
# Making Builds in the app
  (one paragraph: only when the app runs from the repository; App Bundles open Builds only;
   a Build never changes once made; why a draft exists)

## The Build tree                         {#the-build-tree}
   header dropdown, one tree per Snapshot, rooted at config/ defaults;
   Build rows (chips: open here, latest, test; date; Top-N summary) and draft rows
   (draft / running % / failed, changed-setting count, last saved); "from a deleted Build"

## Start a draft                          {#start-a-draft}
   from config/ defaults · Duplicate (pick the Snapshot, default the parent's) · Discard;
   drafts save automatically, Close keeps them; identical settings are allowed with a warning

## The steps of a draft                   {#the-steps-of-a-draft}
   green marker = has changes, red = needs a fix
### Start                                 {#draft-start}
   name (unique per Snapshot), description (becomes the changelog entry), started from, Snapshot, last failure
### Changes the Top-N                     {#draft-top-n}
   datasets (defining tag, List Size against Eligible Pool) · Tags per game · ordered Exclusion Rules
   between the fixed rules: links to List Size, Tag Depth, Exclusions and would-be ranks
### Curation                              {#draft-curation}
   Manual Exclusions, Exclusion Overrides, Manual Metadata Entries; reason and evidence required;
   would-be Overall rank as the shortcut to an Override
### Reports and analysis                  {#draft-reports}
### Network defaults                      {#draft-network-defaults}
   the per-dataset warnings (largest g, default g or s, min_support above N); a grid with no pairs is refused
### Review                                {#draft-review}
   changed settings (old struck through), Top-N badges, list size against pool, games entering Overall,
   problems still to fix; Build is pressed only here
   [the "is the preview current?" wording waits on the Eligible Pool preview decision]

## A running Build                        {#a-running-build}
   the strip under the header in every mode, stage, seconds against the estimate;
   server-wide, survives switching; "Open it in this tab"; a failure leaves the draft with its error

## Manage and delete Builds               {#manage-builds}
   sizes; Delete: refused for the open Build; shows bundles that name it, exports that stop opening,
   where latest moves, Builds and drafts that lose their parent; it cannot be undone

## Raw and lightweight Snapshots          {#raw-and-lightweight-snapshots}
   what the Review step's source line means; same snapshot_id; same numbers (only snapshot_form differs);
   pointer to the Running Guide for snapshot lighten
```

*Alternatives:* add **In short** blocks to the step sections. Rejected: the blocks are for values that need interpreting, and the steps are procedures.

---

## D-3. Chapter 8: Imported data

```
# Opening imported data
  > Note box, near the top and repeated as the chapter's first help anchor:
  > "This guide is written for Steam data. In an Import Build, read **game** as item and
  > **tag** as attribute. Entries marked *Steam Builds only* do not apply."

## What an Import is                      {#what-an-import-is}
   a fixed source like a Snapshot; one Import, several Top-N Datasets; a corrected file is a new Import

## The Import file                        {#the-import-file}
   the wide CSV: id, name, attributes (;-separated, in order), optional score, the filter column, extra numeric columns;
   text rules (UTF-8, comma, RFC 4180, header required, . decimals); attributes.csv;
   one small worked example (5 rows)

## Making an Import                       {#making-an-import}
   menu button with file picker, filter dropdown; or `steamstudy import` (Running Guide)
### When an Import is refused             {#when-an-import-is-refused}
   table: code → meaning → what to do (one row per error and warning code);
   errors.csv columns; warnings kept in import.json

## What changes in an Import Build        {#what-changes-in-an-import-build}
   rank = score, else file order · the filter slider is named after the field, takes its range from the data,
   hidden with no filter field · the inspector's item table shows the extra fields ·
   hidden settings and why (app types, content descriptors, Adult Only notice, Manual Metadata, Observation Window) ·
   an attribute missing from the vocabulary fails the Build · fewer reports (link to chapter 4)
```

---

## D-4. The Top-100 → Top-N sweep

The guide follows the **glossary** rule, not the Build-output rule: it is documentation, so it always says **Top-N**, with "the Top N" as a noun.

| Where | Today | After |
|---|---|---|
| Generic text (README, 01, 02, 03 entry bodies, 04, 05 prose) | "Top-100 Dataset", "Top-100 games" | "Top-N Dataset", "games in the Top N" |
| Statements of the default | "N = 100", "100 of 100" | kept, said as the default: "with the default List Size of 100, …" |
| Worked examples | "100 of 100", "94 of 100 games" | kept as they are: they are examples of a default Steam Build |
| File names | `top100_<dataset>.csv` | kept, plus one sentence in chapter 4 saying the name dates from when N was always 100 |
| The five Steam datasets named in a list (01, 02 Dataset row, 04) | "one of the five Top-100 Datasets: Overall, Puzzle, …" | "one of the Build's Top-N Datasets (the default Steam Build has Overall, Puzzle, RPG, Strategy and Simulation)" |
| Methods paragraph (05, equals the report template) | "For each Top-100 Dataset" | whatever the template prints: it writes "Top 100" when every N = 100 and "Top-N" otherwise, so the guide's copy shows the placeholder `‹top_n›` |

**bg (`bg-terms.md` and the bg guide)**, proposed terms for you to correct:

| English | bg proposal | Avoid |
|---|---|---|
| Top-N Dataset | набор Топ-N (replaces набор Топ-100) | — |
| List Size | размер на списъка | праг, граница |
| Tag Depth / tags per game | дълбочина на таговете / тагове на игра | — |
| Import | импорт (pl. импорти) | внос |
| Import Build | компилация от импорт | — |
| Build Draft | чернова на компилация (already used in [the Build menu prototype](../12-build-menu/)) | — |
| raw / lightweight Snapshot | сурова / олекотена моментна снимка | пълна |
| item / attribute (the reading note only) | елемент / атрибут | — |

The bg guide is translated **in the same change** as the English, since the parity test fails otherwise. App catalogue strings that contain "Top-100" change key and bg value together, and the parity test catches any missed one.

---

## D-5. Chapter 3 (metric reference) additions

- **Settings that change the numbers** table: two new rows, *List Size* (100 per dataset, set in the Build, changes N and every dataset's membership) and *Tags per game (Tag Depth)* (20 = all for Steam, set in the Build, changes what "has" means everywhere except Exclusions and Content Flags). The Exclusion row now says "named Exclusion Rules".
- **New entries** under *Ranking and data*, with **In short** and *Why it matters here*: `### List Size` and `### Tags per game (Tag Depth)`. The second is where "has" is defined, so the existing "A game **has** a tag…" sentence in *Feature analysis* links to it.
- **Import sentence** (one per entry, only where Imports differ, as in the glossary): Rank and ties, Eligible Pool baseline, Tags per game.
- **Steam-only marker**: a line `*Steam Builds only.*` under the heading of each entry that cannot apply to an Import: Monthly Avg. Players, Mean Monthly Players, Months Observed, Release Month, Release-month gap, Placeholder Rows, Store metadata, Listing rank and the depth check, Archived tag category, Genre frequency. It needs no rewording elsewhere.
- **Automatic Parameter Selection** gains the one caveat sentence from [grid scaling](../../issues/11-grid-and-defaults-scaling.md).

*Alternative to the marker:* say nothing and let chapter 8 list the Steam-only entries. Rejected: a reader who clicks in from the app lands on the entry, not on chapter 8.

---

## D-6. Chapters 1, 2, 4, 5 and 6

- **01 Getting started.** *Open the app*: the header's Build name is a dropdown, and `--build` still works. New `## Switch Builds` {#switch-builds}: each tab shows one Build (its address names it); switching keeps language, mode and a same-named dataset, resets the Network State settings, and asks before cancelling the tab's jobs; a Build that was deleted shows a notice with a link to the latest. A bundle with one Build has no dropdown. *Load a dataset*: Top-N wording (D-4).
- **02 App controls.** Control reference: a *Build* row (header dropdown, everyone) and the Dataset row in Top-N wording. The Minimum Months Filter entry gets one sentence: in an Import Build the slider carries the filter field's name and range, see chapter 8.
- **04 Files.** New `## Import Builds` section: `topn_<key>.csv`, `item_fields.csv`, the renaming rule (`appid` → `id`, `mean_monthly_players` → `score`, Steam-only columns dropped), and the list of files an Import Build does not write. New `## Import folder` section: `import.json` and `errors.csv`. Metadata: `build.json` gains `name`, `description`, `parent_build_id`, and for Imports `source`, `import_id`, `import_sha256`, the field facts; `snapshot.json` or `build.json` gains `snapshot_form`.
- **05 Citing.** Quote the Build's name next to the `state_id` (the name is unique per Snapshot, the id stays what reopens it). New `## Cite an Import Build` {#cite-an-import-build}: `import_id` and `import_sha256`, and cite the data's own source, since the study did not collect it.
- **06 Known limitations.** New `## Imported data` section: no weights, one attribute kind, no `;` in names, case-sensitive names, and none of the Steam data checks (release month, placeholders, store metadata). Added to *Network and clustering*: "has" depends on Tag Depth, so compare Network States only at the same Tag Depth and List Size.

---

## D-7. Appendix B

**Recommended:** the Steam table stays as it is, regenerated. A generated `## Import Builds` section follows it with:
1. a table, in the same columns, of only the columns that are **new or renamed** in Import Builds (`id`, `score`, `filter_value`, `field`, `value`, …), each naming its Import files;
2. one line listing the Steam columns **absent** from Import Builds;
3. "Every other column is as in the table above."

`would_be_rank_<dataset>` appears as one row in both tables, described as one column per dataset key.

*Alternatives:*
- (a) A Kind column on one table. Every row would read "both" and the table would get wider.
- (b) A full second table. About 300 rows, mostly duplicates.

The bg appendix is generated the same way, with the new section heading and the "absent" line added to the term table's appendix row.

---

## D-8. Running Guide (English only)

- `## Build`: drop "All five datasets are always built" and "exactly the 100 highest-ranked" in favour of the datasets and List Sizes in the Build's config. A pool smaller than its List Size fails the Build. Builds made in the app read their settings from the draft, and `steamstudy build` uses `config/`, which stays the hand-edited defaults.
- New `## Lightweight Snapshots` (after *Collect*): `snapshot lighten`, made automatically after collect closes or a repair, `verify-light`, the default Build source when present (about 24 s against 99 s), moving one between machines.
- New `## Import` (after *Build*): `steamstudy import <file> [--filter <column>]`, the counts it prints, `imports/failed/`, a byte-identical file is refused, and a pointer to chapter 8 for the format.
- `## Folder layouts`: add `imports/<import_id>/`, `builds/<import_id>/<build_id>/`, `builds/<snapshot>/drafts/`, the lightweight zip's place, and a job store that is no longer in `app_cache/`.
- `## The app`: from the repository it has the Build menu (link chapter 7), and one process switches Builds per tab.
- *Making an App Bundle* and `releasing-an-app-bundle.md`: left to [bundles and in-app Builds](../../issues/16-bundles-and-in-app-builds.md).

---

## Not in this outline (implementation)

The full text, the bg translation, the test cases for the new help anchors, and the generator change to `export/column_index.py`.
