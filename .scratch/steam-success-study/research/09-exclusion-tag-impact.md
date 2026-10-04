# Research 09: Exclusion-tag impact on mainstream games and idle/desktop apps

Fetch date: 2026-10-03 (requests ran 19:12–19:20 UTC).

Method: 35 plain `curl` GETs, one at a time, 4–5 seconds apart. No login, no browser emulation, no challenge solving. Store pages were fetched with the cookie header `birthtime=628473600; lastagecheckage=1-0-1990; wants_mature_content=1`. Every request returned HTTP 200. There was no 403/429/503, no anti-bot page and no age-gate page: every store page held the real app page and its `InitAppTagModal(...)` call. The store page's `application_config` reported `COUNTRY: BG`, so prices and regional content reflect a Bulgarian IP. Tags were parsed from the JSON array passed to `InitAppTagModal(<appid>, [...])`, keeping its order: rank = 1-based array position. Every tag seen had `browseable: true`.

Requests: 15 apps × 2 (`appdetails` and the store page) = 30; 3 Steamworks doc pages; 2 store search pages.

## Sources

| # | Source | What it gave |
|---|---|---|
| S1 | `https://store.steampowered.com/api/appdetails?appids={id}&l=english` for the 15 app IDs below | `name`, `type`, `genres`, `content_descriptors` {ids, notes}, `required_age` |
| S2 | `https://store.steampowered.com/app/{id}/?l=english` (age-gate cookies as above), same 15 IDs | Displayed tag list (`InitAppTagModal`), the "Mature Content Description" text block, canonical URL |
| S3 | https://partner.steamgames.com/doc/store/matureContent | HTTP 200 after **2 redirects to https://partner.steamgames.com/doc/home**. The page does not exist (as of 2026-10-03). |
| S4 | https://partner.steamgames.com/doc/gettingstarted/contentsurvey ("Content Survey") | Describes the Content Survey's 3 sections (General Content, Mature Content, Generative AI). **No content-descriptor id→label mapping.** |
| S5 | https://partner.steamgames.com/doc/webapi/IStoreBrowseService | Redirects to the doc home page; the page does not exist. |
| S6 | https://store.steampowered.com/search/?tags=1320952&l=english | Desktop Companion search, default sort "Relevance": "1,005 results match your search. 46 titles have been excluded based on your preferences." |
| S7 | https://store.steampowered.com/search/?tags=150626&l=english | Gaming search, default sort "Relevance": "262 results match your search. 19 titles have been excluded based on your preferences." |

## Redirect check: GTA V

- `https://store.steampowered.com/app/271590/?l=english` did **not** redirect (0 redirects, HTTP 200). The app is now named **"Grand Theft Auto V Legacy"** (canonical `/app/271590/Grand_Theft_Auto_V_Legacy/`), with `type: game`.
- 3240220 is a separate store page, **"Grand Theft Auto V Enhanced"** (canonical `/app/3240220/Grand_Theft_Auto_V_Enhanced/`). The two apps have different tag lists and different `content_descriptors`.

## Per-app summary

Flag list checked (by tagid, plus the names NSFW and Mature): Sexual Content 12095, Nudity 6650, Hentai 9130, Sexual Themes 40500, NSFW, Mature, Dating Sim 9551, Software 8013, Utilities 87, Animation & Modeling 872, Audio Production 1027, Design & Illustration 84, Photo Editing 809, Video Production 784, Software Training 1445, Benchmark 5407, Gaming 150626, Desktop Companion 1320952, Game Development 13906. No tag named "NSFW" or "Mature" appeared in any of the 15 displayed lists. Hentai, Sexual Themes, Audio Production, Video Production, Software Training and Benchmark did not appear either.

| AppID | Name (appdetails) | type | genres (id: name) | content_descriptors ids | flagged tags (rank: name [tagid]) | # tags shown |
|---|---|---|---|---|---|---|
| 1091500 | Cyberpunk 2077 | game | 3: RPG | [1, 2, 5] | #3: Nudity [6650] | 20 |
| 292030 | The Witcher 3: Wild Hunt — Remastered | game | 3: RPG | [1, 5] | #8: Nudity [6650]; #20: Sexual Content [12095] | 20 |
| 1086940 | Baldur's Gate 3 | game | 25: Adventure, 3: RPG, 2: Strategy | [1, 2, 5] | #6: Sexual Content [12095]; #13: Nudity [6650] | 20 |
| 271590 | Grand Theft Auto V Legacy | game | 1: Action, 25: Adventure | [5] | none | 20 |
| 3240220 | Grand Theft Auto V Enhanced | game | 1: Action, 25: Adventure, 9: Racing | [1, 2, 5] | #2: Sexual Content [12095]; #16: Nudity [6650] | 20 |
| 1174180 | Red Dead Redemption 2 | game | 1: Action, 25: Adventure | [5] | #20: Sexual Content [12095] | 20 |
| 1245620 | ELDEN RING | game | 1: Action, 3: RPG | [2, 5] | none | 20 |
| 990080 | Hogwarts Legacy | game | 1: Action, 25: Adventure, 3: RPG | [] | none | 20 |
| 413150 | Stardew Valley | game | 23: Indie, 3: RPG, 28: Simulation | [] | #17: Dating Sim [9551] | 20 |
| 1172470 | Apex Legends™ | game | 1: Action, 25: Adventure, 37: Free To Play | [] | none | 20 |
| 730 | Counter-Strike 2 | game | 1: Action, 37: Free To Play | [2, 5] | none | 20 |
| 2923300 | Banana | game | 25: Adventure, 4: Casual, 23: Indie, 28: Simulation, 2: Strategy, 37: Free To Play | [] | #18: Dating Sim [9551] | 20 |
| 3419430 | Bongo Cat | game | 4: Casual, 23: Indie, 29: Massively Multiplayer, 28: Simulation, 37: Free To Play | [] | #1: Desktop Companion [1320952]; #18: Software [8013] | 20 |
| 431960 | Wallpaper Engine | game | 4: Casual, 23: Indie, 51: Animation & Modeling, 53: Design & Illustration, 55: Photo Editing, 57: Utilities | [] | #1: Utilities [87]; #3: Software [8013]; #4: Design & Illustration [84]; #5: Animation & Modeling [872]; #13: Photo Editing [809]; #16: Gaming [150626]; #18: Game Development [13906]; #20: Dating Sim [9551] | 20 |
| 993090 | Lossless Scaling | game | 57: Utilities | [] | #1: Utilities [87]; #2: Software [8013] | 9 |

### Cyberpunk 2077 (1091500)

- `type`: game; `required_age`: 17; genres: RPG (3)
- `content_descriptors.ids`: [1, 2, 5]; `notes`: "Cyberpunk 2077 contains strong language, intense violence, blood and gore, as well as nudity and sexual material."
- Store page "Mature Content Description" text: "Cyberpunk 2077 contains strong language, intense violence, blood and gore, as well as nudity and sexual material."

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Cyberpunk | 4115 | 7289 |  |
| 2 | Open World | 1695 | 6878 |  |
| 3 | Nudity | 6650 | 6080 | **FLAG** |
| 4 | RPG | 122 | 5573 |  |
| 5 | Singleplayer | 4182 | 5573 |  |
| 6 | Story Rich | 1742 | 5254 |  |
| 7 | FPS | 1663 | 4977 |  |
| 8 | Sci-fi | 3942 | 4974 |  |
| 9 | Futuristic | 4295 | 4883 |  |
| 10 | First-Person | 3839 | 4579 |  |
| 11 | Atmospheric | 4166 | 4226 |  |
| 12 | Exploration | 3834 | 4053 |  |
| 13 | Action | 19 | 3518 |  |
| 14 | Violent | 4667 | 3076 |  |
| 15 | Great Soundtrack | 1756 | 2738 |  |
| 16 | Action RPG | 4231 | 2673 |  |
| 17 | Adventure | 21 | 2481 |  |
| 18 | Character Customization | 4747 | 2478 |  |
| 19 | Immersive Sim | 9204 | 1384 |  |
| 20 | LGBTQ+ | 44868 | 701 |  |

### The Witcher 3: Wild Hunt — Remastered (292030)

- `type`: game; `required_age`: 18; genres: RPG (3)
- `content_descriptors.ids`: [1, 5]; `notes`: "The Witcher 3: Wild Hunt contains strong language, intense violence, blood and gore, as well as nudity and sexual material."
- Store page "Mature Content Description" text: "The Witcher 3: Wild Hunt contains strong language, intense violence, blood and gore, as well as nudity and sexual material."

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Open World | 1695 | 13284 |  |
| 2 | RPG | 122 | 11182 |  |
| 3 | Story Rich | 1742 | 10387 |  |
| 4 | Atmospheric | 4166 | 7078 |  |
| 5 | Fantasy | 1684 | 6874 |  |
| 6 | Adventure | 21 | 6716 |  |
| 7 | Singleplayer | 4182 | 6574 |  |
| 8 | Nudity | 6650 | 6512 | **FLAG** |
| 9 | Choices Matter | 6426 | 6004 |  |
| 10 | Third Person | 1697 | 4876 |  |
| 11 | Great Soundtrack | 1756 | 4873 |  |
| 12 | Medieval | 4172 | 4801 |  |
| 13 | Action | 19 | 4580 |  |
| 14 | Multiple Endings | 6971 | 4115 |  |
| 15 | Action RPG | 4231 | 4088 |  |
| 16 | Dark Fantasy | 4604 | 3932 |  |
| 17 | Magic | 4057 | 3868 |  |
| 18 | Dark | 4342 | 2325 |  |
| 19 | Sandbox | 3810 | 1419 |  |
| 20 | Sexual Content | 12095 | 1323 | **FLAG** |

### Baldur's Gate 3 (1086940)

- `type`: game; `required_age`: 18; genres: Adventure (25), RPG (3), Strategy (2)
- `content_descriptors.ids`: [1, 2, 5]; `notes`: "This Game may contain content not appropriate for all ages. It contains General Mature Content, and may include Nudity or Sexual Content."
- Store page "Mature Content Description" text: "This Game may contain content not appropriate for all ages. It contains General Mature Content, and may include Nudity or Sexual Content."

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | RPG | 122 | 5771 |  |
| 2 | Character Customization | 4747 | 4381 |  |
| 3 | Choices Matter | 6426 | 4282 |  |
| 4 | Turn-Based Combat | 4325 | 4225 |  |
| 5 | Story Rich | 1742 | 4113 |  |
| 6 | Sexual Content | 12095 | 3400 | **FLAG** |
| 7 | CRPG | 4474 | 3199 |  |
| 8 | Fantasy | 1684 | 3187 |  |
| 9 | Adventure | 21 | 2990 |  |
| 10 | Romance | 4947 | 2962 |  |
| 11 | Online Co-Op | 3843 | 2739 |  |
| 12 | Multiplayer | 3859 | 2642 |  |
| 13 | Nudity | 6650 | 2430 | **FLAG** |
| 14 | Strategy | 9 | 2394 |  |
| 15 | Singleplayer | 4182 | 2368 |  |
| 16 | Co-op Campaign | 4508 | 2217 |  |
| 17 | Class-Based | 4155 | 2129 |  |
| 18 | Dark Fantasy | 4604 | 1896 |  |
| 19 | Combat | 3993 | 1727 |  |
| 20 | LGBTQ+ | 44868 | 1488 |  |

### Grand Theft Auto V Legacy (271590)

- `type`: game; `required_age`: 17; genres: Action (1), Adventure (25)
- `content_descriptors.ids`: [5]; `notes`: null
- Store page "Mature Content Description" text: "This Game may contain content not appropriate for all ages, or may not be appropriate for viewing at work: General Mature Content"

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Open World | 1695 | 32885 |  |
| 2 | Action | 19 | 23692 |  |
| 3 | Multiplayer | 3859 | 21885 |  |
| 4 | Crime | 6378 | 19552 |  |
| 5 | Automobile Sim | 1100687 | 18863 |  |
| 6 | Third Person | 1697 | 18761 |  |
| 7 | First-Person | 3839 | 18366 |  |
| 8 | Shooter | 1774 | 15053 |  |
| 9 | Adventure | 21 | 13739 |  |
| 10 | Singleplayer | 4182 | 12602 |  |
| 11 | Third-Person Shooter | 3814 | 12062 |  |
| 12 | Racing | 699 | 11660 |  |
| 13 | Co-op | 1685 | 10350 |  |
| 14 | Sandbox | 3810 | 10082 |  |
| 15 | Atmospheric | 4166 | 10012 |  |
| 16 | Funny | 4136 | 9466 |  |
| 17 | Great Soundtrack | 1756 | 8798 |  |
| 18 | Comedy | 1719 | 8674 |  |
| 19 | Moddable | 1669 | 7181 |  |
| 20 | RPG | 122 | 4694 |  |

### Grand Theft Auto V Enhanced (3240220)

- `type`: game; `required_age`: 17; genres: Action (1), Adventure (25), Racing (9)
- `content_descriptors.ids`: [1, 2, 5]; `notes`: "This game may contain content not appropriate for all ages, or may not be appropriate for viewing at work: Blood and Gore, Intense Violence, Nudity, Strong Language, Strong Sexual Content, Use of Drugs and Alcohol, and contains User Interactions and In-Game Purchases."
- Store page "Mature Content Description" text: "This game may contain content not appropriate for all ages, or may not be appropriate for viewing at work: Blood and Gore, Intense Violence, Nudity, Strong Language, Strong Sexual Content, Use of Drugs and Alcohol, and contains User Interactions and In-Game Purchases."

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Open World | 1695 | 1353 |  |
| 2 | Sexual Content | 12095 | 1046 | **FLAG** |
| 3 | Action | 19 | 1010 |  |
| 4 | Multiplayer | 3859 | 942 |  |
| 5 | Crime | 6378 | 902 |  |
| 6 | Shooter | 1774 | 793 |  |
| 7 | Third Person | 1697 | 705 |  |
| 8 | Adventure | 21 | 626 |  |
| 9 | First-Person | 3839 | 615 |  |
| 10 | Racing | 699 | 549 |  |
| 11 | Automobile Sim | 1100687 | 548 |  |
| 12 | Sandbox | 3810 | 513 |  |
| 13 | Third-Person Shooter | 3814 | 502 |  |
| 14 | Funny | 4136 | 466 |  |
| 15 | Moddable | 1669 | 462 |  |
| 16 | Nudity | 6650 | 434 | **FLAG** |
| 17 | Co-op | 1685 | 423 |  |
| 18 | Atmospheric | 4166 | 420 |  |
| 19 | PvP | 1775 | 415 |  |
| 20 | Comedy | 1719 | 409 |  |

### Red Dead Redemption 2 (1174180)

- `type`: game; `required_age`: 0; genres: Action (1), Adventure (25)
- `content_descriptors.ids`: [5]; `notes`: null
- Store page "Mature Content Description" text: "This Game may contain content not appropriate for all ages, or may not be appropriate for viewing at work: General Mature Content"

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Open World | 1695 | 4580 |  |
| 2 | Story Rich | 1742 | 3666 |  |
| 3 | Western | 1647 | 3156 |  |
| 4 | Multiplayer | 3859 | 3067 |  |
| 5 | Adventure | 21 | 3056 |  |
| 6 | Action | 19 | 2771 |  |
| 7 | Realistic | 4175 | 2744 |  |
| 8 | Singleplayer | 4182 | 2432 |  |
| 9 | Shooter | 1774 | 2172 |  |
| 10 | Horses | 6041 | 2040 |  |
| 11 | Beautiful | 5411 | 1983 |  |
| 12 | Atmospheric | 4166 | 1969 |  |
| 13 | Third-Person Shooter | 3814 | 1677 |  |
| 14 | Great Soundtrack | 1756 | 1638 |  |
| 15 | Third Person | 1697 | 1495 |  |
| 16 | Gore | 4345 | 1451 |  |
| 17 | Sandbox | 3810 | 1206 |  |
| 18 | First-Person | 3839 | 1074 |  |
| 19 | FPS | 1663 | 1015 |  |
| 20 | Sexual Content | 12095 | 577 | **FLAG** |

### ELDEN RING (1245620)

- `type`: game; `required_age`: 16; genres: Action (1), RPG (3)
- `content_descriptors.ids`: [2, 5]; `notes`: null
- Store page "Mature Content Description" text: "This Game may contain content not appropriate for all ages, or may not be appropriate for viewing at work: Frequent Violence or Gore, General Mature Content"

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Souls-like | 29482 | 7630 |  |
| 2 | Open World | 1695 | 5584 |  |
| 3 | Dark Fantasy | 4604 | 5320 |  |
| 4 | RPG | 122 | 5085 |  |
| 5 | Difficult | 4026 | 4988 |  |
| 6 | Action RPG | 4231 | 3872 |  |
| 7 | Multiplayer | 3859 | 3698 |  |
| 8 | Third Person | 1697 | 3607 |  |
| 9 | Fantasy | 1684 | 3458 |  |
| 10 | Singleplayer | 4182 | 3356 |  |
| 11 | Online Co-Op | 3843 | 3225 |  |
| 12 | Action | 19 | 3035 |  |
| 13 | Co-op | 1685 | 2602 |  |
| 14 | Atmospheric | 4166 | 2565 |  |
| 15 | Great Soundtrack | 1756 | 2500 |  |
| 16 | PvP | 1775 | 2461 |  |
| 17 | Violent | 4667 | 2418 |  |
| 18 | 3D | 4191 | 2178 |  |
| 19 | Character Customization | 4747 | 1603 |  |
| 20 | Family Friendly | 5350 | 1446 |  |

### Hogwarts Legacy (990080)

- `type`: game; `required_age`: 0; genres: Action (1), Adventure (25), RPG (3)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block.

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Magic | 4057 | 4559 |  |
| 2 | Open World | 1695 | 3915 |  |
| 3 | Fantasy | 1684 | 3826 |  |
| 4 | Singleplayer | 4182 | 3574 |  |
| 5 | Adventure | 21 | 3345 |  |
| 6 | RPG | 122 | 3157 |  |
| 7 | Character Customization | 4747 | 2881 |  |
| 8 | Exploration | 3834 | 2372 |  |
| 9 | Story Rich | 1742 | 2138 |  |
| 10 | Third Person | 1697 | 1993 |  |
| 11 | Action-Adventure | 4106 | 1868 |  |
| 12 | Atmospheric | 4166 | 1702 |  |
| 13 | Action RPG | 4231 | 1689 |  |
| 14 | Action | 19 | 1485 |  |
| 15 | Combat | 3993 | 1481 |  |
| 16 | Choices Matter | 6426 | 1149 |  |
| 17 | Puzzle | 1664 | 1085 |  |
| 18 | Great Soundtrack | 1756 | 945 |  |
| 19 | Dark | 4342 | 897 |  |
| 20 | Family Friendly | 5350 | 679 |  |

### Stardew Valley (413150)

- `type`: game; `required_age`: 0; genres: Indie (23), RPG (3), Simulation (28)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block.

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Farming Sim | 87918 | 8907 |  |
| 2 | Pixel Graphics | 3964 | 8174 |  |
| 3 | Multiplayer | 3859 | 8086 |  |
| 4 | Life Sim | 10235 | 7965 |  |
| 5 | RPG | 122 | 7102 |  |
| 6 | Relaxing | 1654 | 7089 |  |
| 7 | Simulation | 599 | 5754 |  |
| 8 | Agriculture | 22602 | 5697 |  |
| 9 | Crafting | 1702 | 4897 |  |
| 10 | Sandbox | 3810 | 4889 |  |
| 11 | Indie | 492 | 4883 |  |
| 12 | Building | 1643 | 4005 |  |
| 13 | Open World | 1695 | 3786 |  |
| 14 | Casual | 597 | 3781 |  |
| 15 | Singleplayer | 4182 | 3688 |  |
| 16 | 2D | 3871 | 3291 |  |
| 17 | Dating Sim | 9551 | 3272 | **FLAG** |
| 18 | Cute | 4726 | 3114 |  |
| 19 | Great Soundtrack | 1756 | 2763 |  |
| 20 | Fishing | 15564 | 2500 |  |

### Apex Legends™ (1172470)

- `type`: game; `required_age`: 0; genres: Action (1), Adventure (25), Free To Play (37)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block.

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Free to Play | 113 | 2502 |  |
| 2 | Multiplayer | 3859 | 1652 |  |
| 3 | Battle Royale | 176981 | 1644 |  |
| 4 | FPS | 1663 | 1612 |  |
| 5 | Shooter | 1774 | 1512 |  |
| 6 | First-Person | 3839 | 1195 |  |
| 7 | PvP | 1775 | 1036 |  |
| 8 | Action | 19 | 908 |  |
| 9 | Hero Shooter | 620519 | 852 |  |
| 10 | Team-Based | 5711 | 795 |  |
| 11 | Tactical | 1708 | 600 |  |
| 12 | Sci-fi | 3942 | 549 |  |
| 13 | Co-op | 1685 | 542 |  |
| 14 | Loot | 4236 | 537 |  |
| 15 | Survival | 1662 | 532 |  |
| 16 | Character Customization | 4747 | 508 |  |
| 17 | Funny | 4136 | 480 |  |
| 18 | Cyberpunk | 4115 | 399 |  |
| 19 | Lore-Rich | 3854 | 391 |  |
| 20 | Cinematic | 4145 | 322 |  |

### Counter-Strike 2 (730)

- `type`: game; `required_age`: 0; genres: Action (1), Free To Play (37)
- `content_descriptors.ids`: [2, 5]; `notes`: "Includes intense violence and blood."
- Store page "Mature Content Description" text: "Includes intense violence and blood."

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | FPS | 1663 | 92751 |  |
| 2 | Shooter | 1774 | 66673 |  |
| 3 | Multiplayer | 3859 | 63589 |  |
| 4 | Competitive | 3878 | 54452 |  |
| 5 | Action | 19 | 48250 |  |
| 6 | Team-Based | 5711 | 47131 |  |
| 7 | eSports | 5055 | 44375 |  |
| 8 | Tactical | 1708 | 42040 |  |
| 9 | First-Person | 3839 | 40063 |  |
| 10 | PvP | 1775 | 35120 |  |
| 11 | Online Co-Op | 3843 | 34505 |  |
| 12 | Co-op | 1685 | 30747 |  |
| 13 | Strategy | 9 | 30591 |  |
| 14 | Military | 4168 | 29127 |  |
| 15 | War | 1678 | 28379 |  |
| 16 | Trading | 4202 | 26381 |  |
| 17 | Difficult | 4026 | 26354 |  |
| 18 | Realistic | 4175 | 25840 |  |
| 19 | Fast-Paced | 1734 | 25678 |  |
| 20 | Moddable | 1669 | 6969 |  |

### Banana (2923300)

- `type`: game; `required_age`: 0; genres: Adventure (25), Casual (4), Indie (23), Simulation (28), Strategy (2), Free To Play (37)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block (only an "AI Generated Content Disclosure" block).

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Free to Play | 113 | 819 |  |
| 2 | Incremental | 560542 | 788 |  |
| 3 | Singleplayer | 4182 | 562 |  |
| 4 | 2D | 3871 | 547 |  |
| 5 | Casual | 597 | 534 |  |
| 6 | Family Friendly | 5350 | 532 |  |
| 7 | Idler | 615955 | 517 |  |
| 8 | Funny | 4136 | 506 |  |
| 9 | Simulation | 599 | 492 |  |
| 10 | Colorful | 4305 | 485 |  |
| 11 | Arcade | 1773 | 471 |  |
| 12 | Hidden Object | 1738 | 463 |  |
| 13 | Pixel Graphics | 3964 | 461 |  |
| 14 | Fantasy | 1684 | 458 |  |
| 15 | Crafting | 1702 | 454 |  |
| 16 | First-Person | 3839 | 454 |  |
| 17 | Mystery | 5716 | 453 |  |
| 18 | Dating Sim | 9551 | 449 | **FLAG** |
| 19 | Anime | 4085 | 378 |  |
| 20 | Open World | 1695 | 316 |  |

### Bongo Cat (3419430)

- `type`: game; `required_age`: 0; genres: Casual (4), Indie (23), Massively Multiplayer (29), Simulation (28), Free To Play (37)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block.

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Desktop Companion | 1320952 | 337 | **FLAG** |
| 2 | Free to Play | 113 | 319 |  |
| 3 | Cats | 17894 | 317 |  |
| 4 | Cute | 4726 | 274 |  |
| 5 | Idler | 615955 | 269 |  |
| 6 | Typing | 1674 | 269 |  |
| 7 | Character Customization | 4747 | 255 |  |
| 8 | Casual | 597 | 251 |  |
| 9 | 2D | 3871 | 251 |  |
| 10 | Incremental | 560542 | 243 |  |
| 11 | Singleplayer | 4182 | 241 |  |
| 12 | Relaxing | 1654 | 136 |  |
| 13 | Indie | 492 | 122 |  |
| 14 | Cartoony | 4195 | 118 |  |
| 15 | Simulation | 599 | 93 |  |
| 16 | Multiplayer | 3859 | 87 |  |
| 17 | Colorful | 4305 | 87 |  |
| 18 | Software | 8013 | 84 | **FLAG** |
| 19 | Funny | 4136 | 80 |  |
| 20 | Massively Multiplayer | 128 | 65 |  |

### Wallpaper Engine (431960)

- `type`: game; `required_age`: 0; genres: Casual (4), Indie (23), Animation & Modeling (51), Design & Illustration (53), Photo Editing (55), Utilities (57)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block.

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Utilities | 87 | 2855 | **FLAG** |
| 2 | Anime | 4085 | 2332 |  |
| 3 | Software | 8013 | 2252 | **FLAG** |
| 4 | Design & Illustration | 84 | 1717 | **FLAG** |
| 5 | Animation & Modeling | 872 | 1367 | **FLAG** |
| 6 | First-Person | 3839 | 1290 |  |
| 7 | Indie | 492 | 897 |  |
| 8 | Cute | 4726 | 851 |  |
| 9 | Memes | 10397 | 835 |  |
| 10 | Action | 19 | 772 |  |
| 11 | Singleplayer | 4182 | 747 |  |
| 12 | Funny | 4136 | 666 |  |
| 13 | Photo Editing | 809 | 512 | **FLAG** |
| 14 | Early Access | 493 | 505 |  |
| 15 | Sandbox | 3810 | 435 |  |
| 16 | Gaming | 150626 | 409 | **FLAG** |
| 17 | Horror | 1667 | 367 |  |
| 18 | Game Development | 13906 | 357 | **FLAG** |
| 19 | Souls-like | 29482 | 87 |  |
| 20 | Dating Sim | 9551 | 69 | **FLAG** |

### Lossless Scaling (993090)

- `type`: game; `required_age`: 0; genres: Utilities (57)
- `content_descriptors.ids`: []; `notes`: null
- Store page: no Mature Content Description block.

| Rank | Tag | tagid | Votes | Flag |
|---|---|---|---|---|
| 1 | Utilities | 87 | 155 | **FLAG** |
| 2 | Software | 8013 | 125 | **FLAG** |
| 3 | Pixel Graphics | 3964 | 49 |  |
| 4 | FPS | 1663 | 47 |  |
| 5 | 3D | 4191 | 47 |  |
| 6 | 2D | 3871 | 44 |  |
| 7 | Family Friendly | 5350 | 19 |  |
| 8 | Singleplayer | 4182 | 12 |  |
| 9 | Psychological Horror | 1721 | 5 |  |

Observations (facts only):
- All 15 apps return `type: "game"` from `appdetails`, including Wallpaper Engine and Lossless Scaling. Wallpaper Engine's `genres` include software genres (51 Animation & Modeling, 53 Design & Illustration, 55 Photo Editing, 57 Utilities). Lossless Scaling's only genre is 57 Utilities.
- 10 of the 15 apps carry at least one flagged tag. The 5 without one are all mainstream: GTA V Legacy (271590), ELDEN RING, Hogwarts Legacy, Apex Legends and Counter-Strike 2. All 4 idle/desktop apps carry at least one flagged tag.
- Lossless Scaling shows only 9 tags.
- Vote counts are on very different scales between apps (for example Counter-Strike 2's rank 1 has 92,751 votes; Lossless Scaling's rank 1 has 155).

## Content descriptors

### Official id→label mapping

**Not found** in an official source within this request budget. `https://partner.steamgames.com/doc/store/matureContent` and `.../doc/webapi/IStoreBrowseService` redirect to the Steamworks doc home page. The "Content Survey" page (S4) describes the Mature Content section of the survey but gives no numeric ids or labels.

### What the store page displays (S2)

When `content_descriptors.notes` is `null`, the store page still shows a "Mature Content Description" block. Its text begins "This Game may contain content not appropriate for all ages, or may not be appropriate for viewing at work:" and is followed by labels:

| App | `ids` | `notes` | Store page label text |
|---|---|---|---|
| Grand Theft Auto V Legacy (271590) | [5] | null | "General Mature Content" |
| Red Dead Redemption 2 (1174180) | [5] | null | "General Mature Content" |
| ELDEN RING (1245620) | [2, 5] | null | "Frequent Violence or Gore, General Mature Content" |

From these three pages: id 5 is displayed as "General Mature Content" and id 2 as "Frequent Violence or Gore". Ids 1, 3 and 4 never appeared with `notes: null` in this sample, so the store's label for them was not observed. When `notes` is non-null, the page shows the developer's text instead (see the per-app sections). Examples:
- Cyberpunk 2077 [1, 2, 5]: "...strong language, intense violence, blood and gore, as well as nudity and sexual material."
- Witcher 3 [1, 5]: the same wording.
- Baldur's Gate 3 [1, 2, 5]: "...It contains General Mature Content, and may include Nudity or Sexual Content."
- GTA V Enhanced [1, 2, 5]: "Blood and Gore, Intense Violence, Nudity, Strong Language, Strong Sexual Content, ...".
- Counter-Strike 2 [2, 5]: "Includes intense violence and blood."

Every app with id 1 in this sample (Cyberpunk 2077, Witcher 3, Baldur's Gate 3, GTA V Enhanced) has developer notes that mention nudity and/or sexual content.

Hogwarts Legacy, Stardew Valley, Apex Legends, Banana, Bongo Cat, Wallpaper Engine and Lossless Scaling have `ids: []` and no Mature Content Description block. Banana shows an "AI Generated Content Disclosure" block instead.

## Search samples (S6, S7)

Default sort "Relevance", top 12 rows as served to an anonymous client with the age cookies:

**Desktop Companion (1320952)**, 1,005 results (46 excluded by preferences):
1. Deskrawl: Idle ARPG (4623570)
2. Cast n Chill (3483740)
3. Spirit City: Lofi Sessions (2113850)
4. TBH: Task Bar Hero (3678970)
5. Bongo Cat (3419430)
6. Desktop Mate (3301060)
7. The NOexistenceN of Lilith (4643090)
8. Birdwatching Notebook (4111370)
9. Deskrawl: Idle ARPG - Supporter Pack (5216710)
10. [WoG] War of Genesis: Idle Loot (4891320)
11. Maltese's Fluffy Onsen (3404470)
12. Your Fiancée (4753760)

**Gaming (150626)**, 262 results (19 excluded by preferences):
1. Wallpaper Engine (431960)
2. Governor of Poker (436150)
3. Mahjong Soul (2739990)
4. Beam Eye Tracker (2375780)
5. DSX (1812620)
6. MySims (3328900)
7. Rooftops & Alleys: The Parkour Game (2703850)
8. The Sims 4 Vampires (1235743, DLC)
9. Croc Legend of the Gobbos (3043940)
10. Goose Goose Duck (1568590)
11. framepacer (4874400)
12. Echoes of Elysium (2644050)

The search page excludes some titles "based on your preferences" even with the age cookies. The search results therefore do not show all apps carrying the tag.

## Unverified items

- **Content-descriptor ids 1, 3, 4.** Third-party sources (SteamDB and community mirrors of Valve's client protobufs, `EContentDescriptorID`) are commonly cited as: 1 = Some Nudity or Sexual Content, 2 = Frequent Violence or Gore, 3 = Adult Only Sexual Content, 4 = Frequent Nudity or Sexual Content (gratuitous), 5 = General Mature Content. **These were not fetched in this session and are not from an official Valve document.** Only ids 2 and 5 were confirmed, by store-page display text (above).
- Tag lists and vote counts change over time. Everything above is a 2026-10-03 snapshot from one anonymous client on a Bulgarian IP. Rankings for logged-in users or other regions were not checked.
- `InitAppTagModal`'s array held 20 entries for every app except Lossless Scaling (9). It was not cross-checked against the tags rendered in the page's visible tag strip, which shows a subset plus a "+" button that opens this modal.
