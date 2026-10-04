# Research 04: Official Steam tag taxonomy and store genre values

Ticket: [../issues/04-steam-tag-taxonomy.md](../issues/04-steam-tag-taxonomy.md)
Fetch date: 2026-10-03.
Method: about 35 plain `curl` GETs, one at a time, a few seconds apart, with no login, cookies, browser emulation or challenge solving. No anti-bot challenge or login wall was hit. Requests were: the live Steamworks page, 7 Wayback Machine snapshots of it, 2 first-party tag-list endpoints, about 15 `appdetails` calls (genres only), and about 15 store redirect probes.

## Summary

- **The page is public, but its tag table is gone.** https://partner.steamgames.com/doc/store/tags returns HTTP 200 with no login. It still says "consult the comprehensive table at the bottom of this document", but the live page (2026-10-03) has **no table**. The last section is "Tags and Non-Game Content Types".
- **Archived table.** Wayback snapshots up to **2026-05-08** include a section called "Table of Tags", with 13 categories and 423 entries (400 unique names; some tags are listed in two categories). The 2026-06-07 snapshot and later ones do not have it. The parsed table is identical in the 2022-06-21, 2025-12-08, 2026-04-08 and 2026-05-08 snapshots, so Valve did not maintain it after 2022. **Treat it as a stale categorisation, not the current tag vocabulary.**
- **Current vocabulary.** Valve's own Web API `IStoreService/GetTagList/v1` (public, no key) returns **446 tags** with numeric `tagid`s. Compared with the archived table, 35 table names are not in the live list (retired or renamed) and 81 live tags are not in the table (so they have no official category).
- **Dating Sim** is spelled exactly `Dating Sim` (tagid 9551). The table puts it under *Sub-Genres*.
- **Education** is a tag: `Education` (tagid 1036). The table lists it under both *Sub-Genres* and *Themes & Moods*. `Education` is also a store **genre** value (id 54).
- **Store genre values** come from the `appdetails` `genres` field as `{id, description}` pairs. No Steamworks document listing them was found. 20 values were seen directly; 6 more are recognised by the store's `/genre/` route but were not seen on an app. **`Puzzle` is not a store genre**; it exists only as a tag.
- **Spelling traps:** the genre is `Free To Play` but the tag is `Free to Play`. Some live tag names end in a space (`Dystopian `, `Parody `). Some names differ only by case or plural between sources (`Based on a Novel`/`Based On A Novel`, `Mouse only`/`Mouse Only`, `Vampire`/`Vampires`). **Recommendation:** match on `tagid` where possible, otherwise on `name.strip()`, case-sensitive.

## Sources

| # | Source | What it gave |
|---|---|---|
| S1 | https://partner.steamgames.com/doc/store/tags (live, fetched 2026-10-03) | Prose on how tags work; no table. Publicly readable (HTTP 200, no login). |
| S2 | http://web.archive.org/web/20260508173645/https://partner.steamgames.com/doc/store/tags | Last archived copy of S1 that still has the "Table of Tags" (13 categories). Also checked: snapshots 20220621032440, 20251208044423 and 20260408022414 (same table); 20260607204918 and 20260901185501 (no table, same as live). |
| S3 | https://api.steampowered.com/IStoreService/GetTagList/v1/?language=english | Live list of 446 `{tagid, name}` pairs (`version_hash` 711684454). Valve first-party Web API, no key needed. |
| S4 | https://store.steampowered.com/tagdata/populartags/english | 429 tags sorted by popularity. A strict subset of S3 (S3 has 17 more: Assassin, Blood, Clicker, Coding, Combat Flight Simulator, Conversation, Dog, Dwarf, Elf, Fox, Jet, Kids, Pool, Rail Shooter, Sexual Themes, Snooker, Unforgiving). |
| S5 | `https://store.steampowered.com/api/appdetails?appids={id}&filters=genres&l=english`, for apps 570, 365670, 431960, 1840, 413150, 252490, 223470, 244210, 1623730, 1096900, 993090, 1172470, 1144200, 1145360, 108600 | Genre `{id, description}` values actually returned. |
| S6 | `https://store.steampowered.com/genre/{name}/` redirect probes | Which names the store treats as genres. A genre redirects to `/tags/en/{name}/` or to a hub; a name that is not a genre redirects to the store home page. |
| S7 | `https://store.steampowered.com/tags/en/{NSFW,Mature,Sexual Content}/` | These redirect to the content hubs `/category/adultonly` (NSFW, Sexual Content) and `/category/mature` (Mature). |

## Statements from the official page (S1, live)

- Developers, players with non-limited accounts, and Steam moderators can all apply tags.
- "Many tags can be applied to your game, but only the top 20 are visible to users and used by Steam to influence visibility." **This matters for the CONTEXT.md definition of "has tag":** the displayed list holds at most 20 tags, ordered by weight.
- At least 5 tags are required before launch, and up to 20 are recommended. "Some store filters prioritize the first 15 tags."
- The Tag Wizard groups tags into "Genres, Visuals & View Points, Themes & Moods, Features, Player support, and more", with a Super-Genre / Genre / Sub-Genre hierarchy (example: Action > Platformer > Precision Platformer).
- Developers can remove tags that do not fit, using the wizard or the store page.
- Tags are localised; the tag order is the same in every language. **The collector must request English** (`l=english`) so the strings match the config.
- Tags can also be applied to non-game app types (applications, soundtracks, videos, tools). A demo inherits its base game's tags.

## Full taxonomy: category → tags (archived table, S2)

Category names and tag spellings are exactly as published. Tags are in the page's order, which is alphabetical except for a few entries appended at the end of Features and Assessments. Three table cells end in a space in the HTML (`Atmospheric `, `Emotional `, `Intentionally Awkward Controls `); the live API spells all three without it, so they are shown stripped here.
**†** = not in the live tag list (S3) on 2026-10-03, so probably retired or renamed. Do not put these in config lists unless they are seen in collected data.

### Top-Level Genres (11)

`Action`, `Adventure`, `Casual`, `Experimental`, `Puzzle`, `Racing`, `RPG`, `Simulation`, `Sports`, `Strategy`, `Tabletop`

### Genres (68)

`Action RPG`, `Action-Adventure`, `Arcade`, `Auto Battler`, `Automobile Sim`, `Base Building`, `Baseball`, `Basketball`, `Battle Royale`, `BMX`, `Board Game`, `Bowling`, `Building`, `Card Game`, `Character Action Game`, `Chess`, `Clicker`, `Cycling`, `Diplomacy`, `eSports`, `Experimental`, `Exploration`, `Farming Sim`, `Fighting`, `Football`†, `God Game`, `Golf`, `Hacking`, `Hidden Object`, `Hockey`, `Idler`, `Interactive Fiction`, `Management`, `Match 3`, `Medical Sim`, `Mini Golf`, `Mining`, `MMORPG`, `MOBA`, `Motocross`, `Open World`, `Outbreak Sim`, `Party-Based RPG`, `Pinball`, `Platformer`, `Point & Click`, `Rhythm`, `Roguelike`, `RTS`, `Sandbox`, `Shooter`, `Skateboarding`, `Skating`, `Skiing`, `Snowboarding`, `Soccer`†, `Space Sim`, `Stealth`, `Strategy RPG`, `Survival`, `Tennis`, `Tower Defense`, `Trivia`, `Turn-Based Strategy`, `Visual Novel`, `Walking Simulator`, `Word Game`, `Wrestling`

### Sub-Genres (61)

`2D Fighter`, `2D Platformer`, `3D Fighter`, `3D Platformer`, `4X`, `Action Roguelike`, `Arena Shooter`, `Beat 'em up`, `Bullet Hell`, `Card Battler`, `Choose Your Own Adventure`, `City Builder`, `Collectathon`, `Colony Sim`, `Combat Racing`, `CRPG`, `Dating Sim`, `Dungeon Crawler`, `Education`, `Flight`, `FPS`, `Grand Strategy`, `Hack and Slash`, `Heist`, `Hero Shooter`, `Horror`, `Immersive Sim`, `Investigation`, `JRPG`, `Life Sim`, `Looter Shooter`, `Metroidvania`, `Mystery Dungeon`, `On-Rails Shooter`, `Open World Survival Craft`, `Political Sim`, `Precision Platformer`, `Programming`, `Real Time Tactics`, `Roguelite`, `Roguevania`†, `Runner`, `Shoot 'Em Up`, `Side Scroller`, `Sokoban`, `Solitaire`, `Souls-like`, `Spectacle fighter`, `Spelling`, `Survival Horror`, `Tactical RPG`, `Third-Person Shooter`, `Time Management`, `Top-Down Shooter`, `Trading`, `Trading Card Game`, `Traditional Roguelike`, `Turn-Based Tactics`, `Twin Stick Shooter`, `Typing`, `Wargame`

### Visuals & Viewpoint (29)

`2.5D`, `2D`, `360 Video`, `3D`, `3D Vision`†, `Abstract`, `Anime`, `Cartoon`, `Cartoony`, `Cinematic`, `Colorful`, `Comic Book`, `Cute`, `First-Person`, `FMV`, `Hand-drawn`, `Isometric`, `Minimalist`, `Noir`, `Pixel Graphics`, `Psychedelic`, `Realistic`, `Split Screen`, `Stylized`, `Text-Based`, `Third Person`, `Top-Down`, `Voxel`, `VR`

### Themes & Moods (105)

`1980s`, `1990's`, `Agriculture`, `Aliens`, `Alternate History`, `America`†, `Atmospheric`, `Assassin`, `Bikes`, `Capitalism`, `Cats`, `Cold War`, `Comic Book`, `Conspiracy`, `Crime`, `Cyberpunk`, `Dark`, `Dark Fantasy`, `Demons`, `Destruction`, `Detective`, `Dinosaurs`, `Diplomacy`, `Dog`, `Dragons`, `Dynamic Narration`, `Economy`, `Education`, `Faith`, `Family Friendly`, `Fantasy`, `Foreign`†, `Futuristic`, `Gambling`, `Game Development`, `Gothic`, `Heist`, `Historical`, `Horses`, `Illuminati`†, `Investigation`, `Jet`, `Lemmings`, `LGBTQ+`, `Logic`, `Loot`, `Lovecraftian`, `Magic`, `Management`, `Mars`, `Mechs`, `Medieval`, `Memes`, `Military`, `Modern`, `Motorbike`, `Mystery`, `Mythology`, `Nature`, `Naval`, `Ninja`, `Offroad`, `Old School`, `Otome`, `Parkour`, `Philosophical`, `Pirates`, `Political`†, `Politics`†, `Pool`, `Post-apocalyptic`, `Programming`, `Retro`, `Robots`, `Romance`, `Rome`, `Satire`, `Science`, `Sci-fi`, `Sniper`, `Snow`, `Space`, `Stealth`, `Steampunk`, `Submarine`, `Superhero`, `Supernatural`, `Surreal`, `Survival`, `Swordplay`, `Tactical`, `Tanks`, `Thriller`, `Time Travel`, `Trains`, `Transhumanism`, `Transportation`, `Underground`, `Underwater`, `Vampire`†, `War`, `Werewolves`, `Western`, `World War I`, `World War II`

### Features (64)

`6DOF`, `Archery`, `Artificial Intelligence`, `Asymmetric VR`, `ATV`, `Automation`, `Base Building`, `Boxing`, `Building`, `Bullet Time`, `Character Customization`, `Choices Matter`, `Class-Based`, `Combat`, `Conversation`, `Crafting`, `Deckbuilding`, `Driving`, `Fishing`, `Flight`, `FMV`, `Grid-Based Movement`, `Gun Customization`, `Hack and Slash`, `Hacking`, `Hex Grid`, `Hunting`, `Inventory Management`, `Level Editor`, `Linear`, `Martial Arts`, `Mining`, `Moddable`, `Multiple Endings`, `Music-Based Procedural Generation`, `Narration`†, `Naval Combat`, `Nonlinear`, `Open World`, `Perma Death`, `Physics`, `Procedural Generation`, `PvE`, `PvP`, `Quick-Time Events`, `Resource Management`, `Sailing`, `Score Attack`, `Stealth`, `Story Rich`, `Tabletop`, `Team-Based`, `Text-Based`, `Time Manipulation`, `Trading`, `Turn-Based Combat`, `Turn-Based Tactics`, `Tutorial`, `Vehicular Combat`, `Female Protagonist`, `Silent Protagonist`, `Villain Protagonist`, `Minigames`, `Intentionally Awkward Controls`

### Players (10)

`4 Player Local`, `Asynchronous Multiplayer`, `Co-op`, `Co-op Campaign`, `Local Co-Op`, `Local Multiplayer`, `Massively Multiplayer`, `Multiplayer`, `Online Co-Op`, `Singleplayer`

### Other Tags (24)

`Based on a Novel`†, `Batman`†, `Documentary`†, `Drama`†, `Dungeons & Dragons`†, `Episodic`, `Experience`†, `Feature Film`†, `Games Workshop`†, `Indie`, `Lara Croft`†, `LEGO`†, `Mod`, `Movie`†, `Music`, `Real-Time`, `Real-Time with Pause`, `Remake`, `Sequel`, `Soundtrack`, `Star Wars`†, `Time Attack`, `Turn-Based`, `Warhammer 40K`†

### Software (13)

`Animation & Modeling`, `Audio Production`, `Benchmark`, `Design & Illustration`, `GameMaker`†, `Gaming`, `Photo Editing`, `RPGMaker`†, `Software`, `Software Training`, `Utilities`, `Video Production`, `Web Publishing`†

### Assessments (20)

`Addictive`, `Beautiful`, `Classic`, `Competitive`, `Cult Classic`†, `Difficult`, `Emotional`, `Epic`, `Fast-Paced`, `Funny`, `Great Soundtrack`, `Lore-Rich`, `Masterpiece`†, `Psychological`, `Relaxing`, `Replay Value`, `Short`, `Unforgiving`, `Comedy`, `Dark Comedy`

### Ratings etc (7)

`Blood`, `Gore`, `Mature`†, `NSFW`†, `Nudity`, `Sexual Content`, `Violent`

### Hardware / Input (7)

`Controller`, `Hardware`, `Mouse only`†, `Steam Machine`†, `Touch-Friendly`, `TrackIR`, `Voice Control`

### Funding etc. (4)

`Crowdfunded`†, `Early Access`, `Free to Play`, `Kickstarter`†

### Tags in the live list (S3) with no official category (81)

These are in `GetTagList` but not in the archived table, so Valve publishes no category for them. Shown as `name` (tagid). Two names end in a space in the API: `Dystopian ` and `Parody `.

`8-bit Music` (117648), `Action RTS` (1723), `Animals` (9626), `Assassins` (97070), `Based On A Novel` (3796), `Billiards` (4852), `Birds` (6214), `Boomer Shooter` (1023537), `Boss Rush` (11095), `Bullet Heaven` (723991), `Capybaras` (1352486), `Cleaning` (23491), `Coding` (42329), `Combat Flight Simulator` (37799), `Cooking` (3920), `Cozy` (97376), `Creature Collector` (916648), `Cricket` (158638), `Cult` (52406), `Dark Humor` (5923), `Decorating` (889937), `Desktop Companion` (1320952), `Dialogue Heavy` (42152), `Dice` (7556), `Dogs` (1637), `Dwarf` (7918), `Dwarves` (4535), `Dystopian ` (5030), `Electronic Music` (61357), `Elf` (102530), `Elves` (6054), `Escape Room` (769306), `Espionage` (1776), `Extraction Shooter` (1199779), `Falling Blocks` (37376), `Farming` (4520), `Football (American)` (1254552), `Football (Soccer)` (1254546), `Fox` (30927), `Foxes` (507423), `Hentai` (9130), `Hobby Sim` (1220528), `Immersive` (3934), `Incremental` (560542), `Instrumental Music` (189941), `Job Simulator` (35079), `Jump Scare` (42089), `Kids` (4162), `Language Learning` (21635), `Mahjong` (33572), `Mouse Only` (11123), `Musou` (323922), `Narrative` (7702), `Nostalgia` (14720), `Organizing` (1239876), `Parody ` (4878), `Party` (7108), `Party Game` (7178), `Poker` (6835), `Psychological Horror` (1721), `Puzzle Platformer` (5537), `Rail Shooter` (3954), `Reboot` (5941), `Rock Music` (337964), `Roguelike Deckbuilder` (1091588), `Rugby` (49213), `Samurai` (10617), `Sexual Themes` (40500), `Shop Keeper` (91114), `Snooker` (363767), `Social Deduction` (745697), `Spaceships` (4291), `Vampires` (12686), `Vikings` (11634), `Volleyball` (847164), `Wholesome` (552282), `Wolves` (20486), `Wuxia` (25959), `Xianxia` (760247), `Zombies` (1659), `Zoo` (46348)

### Table names not in the live list (35)

`3D Vision`, `America`, `Based on a Novel`, `Batman`, `Crowdfunded`, `Cult Classic`, `Documentary`, `Drama`, `Dungeons & Dragons`, `Experience`, `Feature Film`, `Football`, `Foreign`, `GameMaker`, `Games Workshop`, `Illuminati`, `Kickstarter`, `LEGO`, `Lara Croft`, `Masterpiece`, `Mature`, `Mouse only`, `Movie`, `NSFW`, `Narration`, `Political`, `Politics`, `RPGMaker`, `Roguevania`, `Soccer`, `Star Wars`, `Steam Machine`, `Vampire`, `Warhammer 40K`, `Web Publishing`.

Some of these look like renames: `Based on a Novel` → `Based On A Novel`, `Mouse only` → `Mouse Only`, `Vampire` → `Vampires`, `Football`/`Soccer` → `Football (American)`/`Football (Soccer)`. **This is inferred from the names and not verified.** Other names (for example `Mature`, `NSFW`) are simply absent from S3, and it is **unverified whether they still appear in any game's displayed tag list.** S3 may leave out some tags that still show on store pages. The collector should log every distinct tag string it sees so that this can be checked against real data.

## Tags that match the Exclusion rules (CONTEXT.md)

### Dating Sim (confirmed)

- Exact string: `Dating Sim`, tagid **9551** (S3). Archived category: Sub-Genres (S2).

### Education (confirmed: a tag, not an exclusion ground)

- Exact string: `Education`, tagid **1036** (S3). Archived categories: Sub-Genres and Themes & Moods (S2). `Education` is also a store genre value (id 54, S5).
- Related live tags that are also not exclusion grounds: `Language Learning` (21635), `Programming` (5432), `Coding` (42329), `Science`, `Typing`, `Spelling`, `Trivia`, `Logic`.

### PROPOSAL for the researcher to confirm: sexual-content tag list

| Tag (exact) | tagid | Source / archived category | Proposed |
|---|---|---|---|
| `Sexual Content` | 12095 | S3; Ratings etc | **exclude** |
| `Nudity` | 6650 | S3; Ratings etc | **exclude** |
| `Hentai` | 9130 | S3; no category (new tag) | **exclude** |
| `NSFW` | n/a | S2 only (Ratings etc); not in S3; `/tags/en/NSFW/` redirects to `/category/adultonly` (S7) | **exclude if seen** (harmless to list, may never match) |
| `Sexual Themes` | 40500 | S3; no category (new tag) | **researcher decides.** The name suggests sexual content, but it may be applied to mainstream games with mild themes. |
| `Mature` | n/a | S2 (Ratings etc); not in S3 | do **not** exclude (CONTEXT.md: maturity tags are not exclusion grounds) |
| `Gore`, `Violent`, `Blood` | 4345, 4667, 5228 | S3; Ratings etc | do **not** exclude (maturity) |
| `Romance`, `Otome`, `LGBTQ+` | 4947, 31579, 44868 | S3; Themes & Moods | do **not** exclude (not sexual content as such; `Dating Sim` is its own rule) |

Risk to confirm: the "has tag anywhere in the displayed list" rule means one community-voted `Nudity` or `Sexual Content` tag excludes a game, even a mainstream AAA title. **This is unverified for specific games.** I suggest the pipeline report, per proposed tag, how many otherwise-top-100 games each tag removes, so the researcher can review before freezing the list. `appdetails` also returns a developer-declared `content_descriptors` field (for example `{"ids":[1,2,5],"notes":"..."}` for app 223470, S5). It could serve as a cross-check, but the meaning of the numeric ids was **not** checked in official docs.

### PROPOSAL for the researcher to confirm: software / non-game tag list

The archived "Software" category, limited to tags still in S3:

| Tag (exact) | tagid | Proposed |
|---|---|---|
| `Software` | 8013 | **exclude** |
| `Utilities` | 87 | **exclude** |
| `Animation & Modeling` | 872 | **exclude** |
| `Audio Production` | 1027 | **exclude** |
| `Design & Illustration` | 84 | **exclude** |
| `Photo Editing` | 809 | **exclude** |
| `Video Production` | 784 | **exclude** |
| `Software Training` | 1445 | **exclude** |
| `Benchmark` | 5407 | **exclude** |
| `Gaming` | 150626 | **researcher decides.** The archived table files it under Software, but the name is ambiguous and it may be voted onto games. |
| `GameMaker`, `RPGMaker`, `Web Publishing` | n/a | in S2 Software but not in S3; list them only if seen |
| `Game Development` | 13906 | do **not** exclude: archived under Themes & Moods; used by games about game development |
| `Desktop Companion` | 1320952 | **researcher decides.** New, uncategorised tag. Covers desktop pets and idlers, which are usually `type: game`. |
| `Programming`, `Coding` | 5432, 42329 | do **not** exclude (game themes/sub-genres) |

Note: these tags matter mainly for apps whose `type` is `game` but which are really tools (for example Wallpaper Engine, app 431960, has the genres Utilities, Photo Editing and others in S5). The non-`game` app type rule catches the rest.

## Store genre field (`appdetails.genres`)

There is **no official Steamworks page that lists the genre values**. I looked at /doc/store/tags, /doc/store/page, /doc/store/page/description, /doc/store/editing and /doc/store/categories, and none of them lists genres. The values below were observed directly.

**Seen in `appdetails` responses (S5): id → description**

| id | description | id | description |
|---|---|---|---|
| 1 | `Action` | 37 | `Free To Play` |
| 2 | `Strategy` | 51 | `Animation & Modeling` |
| 3 | `RPG` | 53 | `Design & Illustration` |
| 4 | `Casual` | 54 | `Education` |
| 9 | `Racing` | 55 | `Photo Editing` |
| 18 | `Sports` | 57 | `Utilities` |
| 23 | `Indie` | 58 | `Video Production` |
| 25 | `Adventure` | 59 | `Web Publishing` |
| 28 | `Simulation` | 60 | `Game Development` |
| 29 | `Massively Multiplayer` | 70 | `Early Access` |

**Recognised by the store's `/genre/{name}/` route but not seen on a sampled app (S6), so their ids are unverified:** `Audio Production`, `Software Training`, `Accounting`, `Sexual Content`, `Nudity`, `Gore`.
**Rejected by the `/genre/` route (redirect to the store home page), so not genres:** `Puzzle`, `Violent`.
The set may have more values; S5/S6 cannot prove the list is complete. The collector should log every distinct `(id, description)` pair it sees. Store the numeric `id` along with the description.

### Names shared by genres and tags (exact spelling of each)

| Genre (`appdetails`) | Tag (S3) | Same string? |
|---|---|---|
| `Action`, `Adventure`, `Casual`, `RPG`, `Racing`, `Simulation`, `Sports`, `Strategy`, `Indie`, `Massively Multiplayer`, `Early Access`, `Education`, `Animation & Modeling`, `Design & Illustration`, `Photo Editing`, `Utilities`, `Video Production`, `Game Development` | same | yes |
| `Audio Production`, `Software Training`, `Sexual Content`, `Nudity`, `Gore` (genre status from S6 only) | same | yes |
| `Free To Play` | `Free to Play` (tagid 113) | **no: capital T in the genre** |
| `Web Publishing` | not in S3 (only in archived S2) | n/a |
| `Accounting` | no tag | n/a |
| (not a genre) | `Puzzle` (1664), `Violent` (4667) | tag only |

Consequences for the study:
- The **Puzzle** Top-100 Dataset has to come from the `Puzzle` tag (as already decided). Genre-based feature analysis will never show "Puzzle", because it is not a store genre. `RPG`, `Strategy` and `Simulation` exist as both a genre and a tag, so each dataset should label which one it uses.
- `Free To Play` (genre) and `is_free` (appdetails flag) are separate signals from the `Free to Play` tag. Keep all three distinct.
- The genre field also has values for software (`Utilities`, `Video Production`, …) and for content (`Sexual Content`, `Nudity`, `Gore`, if confirmed). These could double as exclusion cross-checks, but CONTEXT.md bases exclusions on tags, so that would be a new decision.

## Candidate default Genre Tag list (for hiding from the Tag Network): PROPOSAL

The archived "Top-Level Genres" category, all present in S3: `Action`, `Adventure`, `Casual`, `Experimental`, `Puzzle`, `Racing`, `RPG`, `Simulation`, `Sports`, `Strategy`, `Tabletop`. Optionally add the tags that share a name with a store genre: `Indie`, `Massively Multiplayer`, `Early Access`, `Free to Play`. The researcher decides.

## Open items / unverified

- Whether `Mature`, `NSFW` and the other 33 names missing from S3 still appear in displayed store tag lists. Check this against collected data.
- The complete set of genre ids, and the ids for `Audio Production`, `Software Training`, `Accounting`, `Sexual Content`, `Nudity` and `Gore`.
- What the `content_descriptors` ids mean.
- Why the table was removed from S1 between 2026-05-08 and 2026-06-07 is unknown. The page text still refers to it.
