# What is the generic dataset contract?
Type: grilling
Status: resolved
Blocked by: 01

## Question

The seam for Data Independence: what the analysis (network, Parameter Selection, validation, feature analysis, the app) reads, so that Steam Builds and imported datasets both produce it. Charted: items with an id and a name, an ordered attribute list, an optional score, optional numeric item fields; one attribute kind; no weights; Steam wording is kept.

Using [Where does the analysis assume Steam?](01-steam-assumptions-downstream.md), decide:
- the fields and files of the contract, and how a Steam Top-N Dataset maps onto it (`appid` → item id, `months_observed` → a numeric field, the defining tag, Genre Tags);
- which Steam-only facts survive only as optional fields (store links, `is_free`, genres, Content Flags), and how the app shows a dataset that lacks them;
- whether the Eligible Pool baseline (tag frequency against the pool) is part of the contract, and what an import with no score or no pool gives;
- how existing Builds are read through it with no Steam number changing;
- where the seam sits in code (one reader that every consumer uses).

## Answer

Settled with the researcher, 2026-11-06. ADR: [The dataset seam is in memory, not a shared file](../../../docs/adr/0005-dataset-seam-is-in-memory.md).

- **The seam is in memory, behind one reader.** `read_dataset(build, key)` returns a `Dataset`: the items in rank order, the defining attribute, the Genre Tags, and the filter field (name and range). Every consumer goes through it: the app (`BuildContext.rows/games/context`, the slider range), the network, Parameter Selection and validation.
- **Two adapters, chosen by a source marker in `build.json`.** No marker means Steam, so old Builds need nothing. The Steam adapter is today's code: `top100_<key>.csv`, the strict 17-column header, `months_observed` as the filter value. The import adapter reads the import Build's own file, whose layout [How does a dataset get imported?](09-dataset-import.md) decides. No file shared by both kinds is introduced; file naming stays with the export-schema fog.
- **Existing Builds and Steam numbers.** Nothing on disk is rewritten, and old Builds are adapted when read (findings 6 and 7). The state key keeps `min_months` as the threshold's field name, so no Steam `state_id`, cache or saved export moves.
- **Items.** A unique positive integer id (`appid` for Steam), a name, a rank and at least one attribute. Imports must bring integer ids; text ids are refused. With a score, rank is score descending, with ties broken by file order. Without a score, file order is the rank. The reader reads `rank` and never recomputes it.
- **Attributes.** Integer ids in a fixed order, each item's list kept in its order (tags per game cuts from the front). Steam keeps its own tag ids. An import may supply ids; otherwise the importer numbers attributes 1…k in sorted name order (Unicode code point), so reordering rows never renumbers them. An import's config refers to attributes by name when ids are numbered.
- **Filter field.** At most one per dataset, named when it is imported and fixed by the Build, not by the Network State. Values may be decimals; every item must have one; the test is `>=`, off at the field's minimum. The slider is labelled with the field's name and takes its range from the data (not 0–60). With no filter field the slider is hidden and every item is kept. Any other numeric fields are carried along and shown in the inspector's item table.
- **Eligible Pool.** Not read by the app. For an import, the pool is the whole imported file minus any Exclusions it has (whether imports have Exclusions is for [How do named exclusion rules work?](06-named-exclusion-rules.md) and the import ticket). The Top-N Dataset is its N highest-ranked items, with or without a score. Pool baselines are computed in the Build stage, as Steam's are from the Snapshot.
- **Steam-only facts stay out of the contract.** Store genres, `is_free`, Content Flags, release dates, `mean_monthly_players` as a named column, `metadata_source`, `top_listing_rank`, `monthly_players.csv` and the 14 Build reports stay in Steam Build files and the Steam feature analysis. An import's feature report keeps the generic sections only: tag frequency, combinations, associations, and the pool baseline. It drops the genre, Content Flag, free-to-play and months sections, the "Puzzle" note and the archived Steamworks categories. The app reads none of these today, so nothing goes missing there. The one visible change: the inspector's "AppID" header reads "ID" for imports (with a bg entry).
- **Defining attribute and Genre Tags.** Both optional: a defining attribute per dataset, and a hideable attribute list per Build, still called Genre Tags. Same behaviour as today, including the `genre_tag_hidden` reason. With neither set, nothing is hidden by default and their toggles don't appear.
