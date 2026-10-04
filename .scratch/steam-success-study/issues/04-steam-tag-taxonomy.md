# Official Steam tag taxonomy extraction
Type: research
Status: resolved
Blocked by: none

## Question

What does the official Steam tag taxonomy at https://partner.steamgames.com/doc/store/tags contain, and which tags fall into the exclusion and genre categories decided while charting?

- Full category structure (category names and their tags), and whether the page is publicly readable.
- Candidate lists: sexual-content tags; software / non-game tags; the exact "Dating Sim" tag name. Confirm "Education" is a tag and which category it sits in.
- The set of values the store developer genre field can take (e.g. Action, Indie, Early Access, Free to Play), and which tags share names with those values.
- Exact spellings, so config lists match collected tag strings.

## Answer

- The page is public (HTTP 200, no login), but its "Table of Tags" was **removed between 2026-05-08 and 2026-06-07**. The text still refers to it. The last archived copy that has it (Wayback, 2026-05-08) lists 13 categories and 400 unique tags. The table has not changed since 2022, so it is stale.
- The current vocabulary is Valve's `IStoreService/GetTagList` (446 tags with ids). 35 table names are gone from it, and 81 live tags have no official category.
- `Dating Sim` (tagid 9551, Sub-Genres) and `Education` (tagid 1036, Sub-Genres and Themes & Moods) are both confirmed. `Education` is also store genre id 54.
- Proposed sexual-content list: `Sexual Content`, `Nudity`, `Hentai`, plus `NSFW` if seen. `Sexual Themes` is open. Not excluded: Mature/Gore/Violent/Blood/Romance.
- Proposed software list: `Software`, `Utilities`, `Animation & Modeling`, `Audio Production`, `Design & Illustration`, `Photo Editing`, `Video Production`, `Software Training`, `Benchmark`. `Gaming` and `Desktop Companion` are open. `Game Development` is kept.
- No official document lists the store genre values. 20 were seen in `appdetails` (Action, Strategy, RPG, Casual, Racing, Sports, Indie, Adventure, Simulation, Massively Multiplayer, Free To Play, Early Access, Education, and software genres), and 6 more were inferred from store redirects. **`Puzzle` is not a genre**, only a tag.
- Spelling traps: genre `Free To Play` vs tag `Free to Play`; trailing spaces (`Dystopian `, `Parody `). Match tags by `tagid` or by `name.strip()`, and always request `l=english`.
- Full taxonomy, ids, sources and open items: [../research/04-steam-tag-taxonomy.md](../research/04-steam-tag-taxonomy.md)
