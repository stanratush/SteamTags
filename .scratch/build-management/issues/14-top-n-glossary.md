# What does the glossary say for Top-N Dataset, List Size, Tag Depth and "has"?
Type: grilling
Status: resolved
Blocked by:

## Question

[What do tags per game and list size apply to?](05-tags-per-game-and-list-size.md) drafted wording for **Top-N Dataset**, **List Size**, **Tag Depth** and the redefined "has", but `CONTEXT.md` still defines **Top-100 Dataset** (line 204) and uses "Top-100" 11 times. The **Build** entry now names Steam Builds and Import Builds ([export schema](13-export-schema.md)).

Decide:
- the final entries for Top-N Dataset, List Size, Tag Depth and "has", and what each one says for an Import Build (item and attribute);
- whether **Top-100 Dataset** stays as an _Avoid_ alias, and how the entries that mention it (Tag Network, Parameter Grid, Eligible Pool, Exclusion, Tag-Specific Dataset and others) are reworded;
- whether "Top 100" survives anywhere as a phrase for the Steam default (N = 100), for example in report text, or always becomes "Top-N" / "the top N".

## Answer

Settled with the researcher, 2026-11-07, and written into `CONTEXT.md`. No ADR: wording is cheap to change.

- **Top-N Dataset** replaces Top-100 Dataset: one of a Build's ranked lists, Overall or a Tag-Specific Dataset, of the N non-excluded games with the highest score, N being its **List Size**. The score is Mean Monthly Players for Steam, and for an Import its score, or file order without one. "Five ranked lists" is gone, since datasets are a Build setting. No separate "Ranking Score" term.
- **List Size** is its own entry: the N, set per dataset, 100 by default; a pool smaller than it cannot be built. _Avoid_: top count, cutoff, list length.
- **Tag Depth** is its own entry, with the Steam (2–20, default 20 = all) and Import (from 2, default all) ranges. "Tags per game" is noted as the app and User Guide name, not an _Avoid_.
- **Tag** redefines "has" as within Tag Depth; Exclusions and Content Flags read the whole list. **Exclusion** gains that rank limits ignore Tag Depth.
- **Top-100 Dataset** survives only as an _Avoid_ alias (with "top list"). `top-N games` is dropped from Candidate Pool's _Avoid_.
- **Sweep:** Tag Network, Parameter Grid, Automatic Parameter Selection, Lift, Network State, Candidate Pool, Exclusion, Build and Import now say Top-N. Eligible Pool says "the dataset's tag frequencies" and "every non-excluded item, for an Import". Tag-Specific Dataset gives "e.g. Puzzle, RPG" instead of a fixed list.
- **Report and schema text (Build outputs)** writes the actual number: "Top 100" when every dataset in scope has N = 100, "Top-N" when List Sizes differ. Counts like "the five published datasets" follow the same rule. Default Steam Builds keep identical bytes. Glossary, docstrings and comments always say Top-N; file names stay `top100_<key>.csv`. Hyphen as today: "Top-N Dataset" as a modifier, "the Top N" as a noun.
- **Imports:** entries stay in Steam wording (Game means item, Tag means attribute). Only Top-N Dataset, Tag Depth and Eligible Pool add an Import sentence, where Imports behave differently.
