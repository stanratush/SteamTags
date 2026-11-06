# What do tags per game and list size apply to?
Type: grilling
Status: resolved
Blocked by:

## Question

Charted: **tags per game** is a number the user enters, a setting of its own beside the exclusion rank limit (`global_rank_limit` stays for exclusions). **List size** is per dataset, default 100. Both can change the Top-N, so both need the Snapshot.

Decide:
- which steps tags per game cuts: Tag-Specific Dataset membership (a game whose Puzzle tag is 15th, at 10), the "no tags" rule, Content Flags (today "anywhere in the displayed 20"), the network, the feature analysis, the Eligible Pool baseline;
- how it sits beside `global_rank_limit` and `per_tag_rank_limit`: e.g. a game excluded for its 14th tag while only 10 are counted, and whether exclusion may look past tags per game;
- its input: bounds, how "all" is entered, the Steam maximum of 20, and imported data with longer lists;
- list size bounds, and the report when the Eligible Pool is smaller than the list size;
- the glossary: **Top-N Dataset**, a name for tags per game, and the new wording of "a game **has** a tag".

## Answer

Settled with the researcher, 2026-11-07. No ADR: nothing is implemented yet, so the choice is cheap to reverse.

- **One meaning of "has".** Tags per game (K) redefines it everywhere: a game has a tag only when the tag is among the first K tags of its displayed list. Every place that asks "has" follows: Tag-Specific Dataset membership (at K = 10, a game whose Puzzle tag is 15th is not in Puzzle), the Eligible Pool and its baselines (`tag_frequency`, `genre_frequency`), the network (nodes, edges, Genre Tag hiding) and the feature analysis (frequency, combinations, associations, `median_position`).
- **Exclusions and Content Flags read the full displayed list.** `global_rank_limit` and `per_tag_rank_limit` keep counting positions in that list, ignoring K. A game with Dating Sim 14th is still excluded at K = 10. The Impact Report may note an exclusion caused by a tag beyond tags per game.
- **"No tags" is unchanged.** It still means the store page shows no tags. With K ≥ 2, any game with a tag has a counted tag.
- **Tags per game is one value per Build,** not per dataset. It takes an integer ≥ 2 or the literal `all`, and `all` is stored as `all`, never as a number.
  - **Steam:** 2–20, where 20 means the same as all. The default is 20, values above 20 are refused, and a Build without the setting reads as 20, so no Steam bytes and no `build_id` change.
  - **Imports:** 2 up to the longest list, or `all` (the default), with no cap.
- **Where the cut happens.** Build files keep each game's **full** displayed list. The Build records K, and the dataset reader applies the cut once, so the network, Parameter Selection, validation and the app all see the same counted tags. The Build-stage feature analysis and pool baselines go through the same helper. In the app's inspector, tags beyond K stay visible, marked "not counted (beyond tags per game)", with a bg entry.
- **Manual Metadata tags-only entries** are treated like a store list: cut at K for "has", full list for exclusions.
- **List size** is an integer ≥ 10 with no fixed maximum, set per dataset, default 100. A Top-N always holds exactly N, so an Eligible Pool smaller than N fails the Build, with an error that names the pool size. The Build menu shows each dataset's pool size before saving. Ties at the cutoff are reported as today. Imports have no "whole pool" shortcut. Whether 10 is a sensible floor for the Parameter Grid is for [Do the Parameter Grid and network defaults scale…](11-grid-and-defaults-scaling.md).
- **Glossary wording, to be written when the wording fog is worked:**
  - **Top-N Dataset** replaces Top-100 Dataset: "the N non-excluded games with the highest ranking score, N being the dataset's **List Size** (100 by default)".
  - **Tag Depth** is the glossary name for tags per game: "the number of leading tags in each game's list that count". The UI and User Guide keep "tags per game".
  - **Tag:** "A game **has** a tag if the tag is within its Tag Depth: among the first K tags of its displayed store list (Steam displays at most 20), regardless of votes. Exclusions and Content Flags read the whole displayed list instead."
  - **Eligible Pool** and **Tag-Specific Dataset** keep "have", now in this sense.
  - **Exclusion** gains a note that rank limits count positions in the displayed list, independent of Tag Depth.
