# What is the generic dataset contract?
Type: grilling
Status: open
Blocked by: 01

## Question

The seam for Data Independence: what the analysis (network, Parameter Selection, validation, feature analysis, the app) reads, so that Steam Builds and imported datasets both produce it. Charted: items with an id and a name, an ordered attribute list, an optional score, optional numeric item fields; one attribute kind; no weights; Steam wording is kept.

Using [Where does the analysis assume Steam?](01-steam-assumptions-downstream.md), decide:
- the fields and files of the contract, and how a Steam Top-N Dataset maps onto it (`appid` → item id, `months_observed` → a numeric field, the defining tag, Genre Tags);
- which Steam-only facts survive only as optional fields (store links, `is_free`, genres, Content Flags), and how the app shows a dataset that lacks them;
- whether the Eligible Pool baseline (tag frequency against the pool) is part of the contract, and what an import with no score or no pool gives;
- how existing Builds are read through it with no Steam number changing;
- where the seam sits in code (one reader that every consumer uses).
