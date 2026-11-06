# What do tags per game and list size apply to?
Type: grilling
Status: open
Blocked by:

## Question

Charted: **tags per game** is a number the user enters, a setting of its own beside the exclusion rank limit (`global_rank_limit` stays for exclusions). **List size** is per dataset, default 100. Both can change the Top-N, so both need the Snapshot.

Decide:
- which steps tags per game cuts: Tag-Specific Dataset membership (a game whose Puzzle tag is 15th, at 10), the "no tags" rule, Content Flags (today "anywhere in the displayed 20"), the network, the feature analysis, the Eligible Pool baseline;
- how it sits beside `global_rank_limit` and `per_tag_rank_limit`: e.g. a game excluded for its 14th tag while only 10 are counted, and whether exclusion may look past tags per game;
- its input: bounds, how "all" is entered, the Steam maximum of 20, and imported data with longer lists;
- list size bounds, and the report when the Eligible Pool is smaller than the list size;
- the glossary: **Top-N Dataset**, a name for tags per game, and the new wording of "a game **has** a tag".
