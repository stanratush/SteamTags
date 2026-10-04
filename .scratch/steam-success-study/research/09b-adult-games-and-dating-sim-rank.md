# 09b — Adult-only games without login; rank of `Dating Sim` across dating sims vs. mainstream games

Fetch date: 2026-10-03 (requests 20:00–20:07 UTC). Facts only.

## Method

- Plain `curl` GETs from Git Bash, sequential, ~5–6 s apart, no login, no browser emulation, no redirects followed.
- Cookie on every request except one control: `birthtime=628473600; lastagecheckage=1-0-1990; wants_mature_content=1`.
- Store page: `https://store.steampowered.com/app/<appid>/?l=english`; tags parsed from `InitAppTagModal(<appid>, [...])` (display order, rank 1 = first element).
- App details: `https://store.steampowered.com/api/appdetails?appids=<appid>&l=english`.
- Search: `https://store.steampowered.com/search/?tags=<id>&l=english` and `?term=<name>`.
- Total requests: 47 (slightly above the ~45 budget; the 47th was an appdetails call to map descriptor id 1). All returned HTTP 200 except two expected 302s (below). No 403/429/503, no anti-bot page.
- Server reported `country_code: BG` for the requests.

## 1. Adult-only sexual games, logged out

### 1a. Search filtering (logged-out default)

Every logged-out search page has `data-userinfo` containing `"logged_in":false,...,"excluded_content_descriptors":[3,4]`. The search page then shows a notice:

| Search | Notice text (exact) |
|---|---|
| `?tags=9130` (Hentai) | "1,795 results match your search. 7,609 titles have been excluded based on your preferences." |
| `?tags=12095` (Sexual Content) | "5,366 results match your search. 14,790 titles have been excluded based on your preferences." |
| `?tags=9551` (Dating Sim) | "4,371 results match your search. 6,015 titles have been excluded based on your preferences." |

The page defines `g_strUnfilteredURL = '...&ignore_preferences=1'`. Fetching `https://store.steampowered.com/search/?tags=9130&l=english&ignore_preferences=1` logged out returned 200 with "9,048 results match your search. Your content preferences have not been applied to the search results you see below." The adult games below were picked from that unfiltered list (no external source needed).

### 1b. Store page and appdetails per game

With the age cookies, all five store pages returned 200, rendered fully, and included `InitAppTagModal` with 20 tags. No login or "content preferences" wall appeared. Instead, each page contains this notice (exact):

> `<div class="mature_content_notice">This game is marked as 'Adult Only'. You are seeing this game because you have agreed to continue to this page.</div>`

Control (no cookies): `https://store.steampowered.com/app/1619750/?l=english` returned **302 → `https://store.steampowered.com/agecheck/app/1619750/?l=english`** (20-byte body, no `InitAppTagModal`). The agecheck page itself was not fetched.

`appdetails` returned `success: true` with full `data` for all five, logged out.

| appid | Name | Store page (cookies) | appdetails | `type` | `required_age` | genres (id: description) | `content_descriptors.ids` |
|---|---|---|---|---|---|---|---|
| 1126320 | Being a DIK - Season 1 | 200, tags 20, 'Adult Only' notice | success true | game | 0 | 23: Indie | [1, 2, 3, 4, 5] |
| 1619750 | Karryn's Prison | 200, tags 20, 'Adult Only' notice | success true | game | 0 | 3: RPG; 28: Simulation; 2: Strategy | [1, 3, 5, 4] |
| 1073440 | コイカツ！ / Koikatsu Party | 200, tags 20, 'Adult Only' notice | success true | game | 0 | 28: Simulation | [1, 3, 5, 4] |
| 3576350 | Sex, Secrets & Used Tech | 200, tags 20, 'Adult Only' notice | success true | game | 0 | 4: Casual; 3: RPG; 28: Simulation | [1, 3, 4, 5] |
| 2808930 | Lust Goddess | 200, tags 20, 'Adult Only' notice | success true | game | 0 | 1: Action; 25: Adventure; 29: Massively Multiplayer; 3: RPG; 2: Strategy; 37: Free To Play | [1, 3, 4, 5] |

- **Genres:** none of the five returned a `Sexual Content` or `Nudity` genre value. Those strings appeared only as user tags (12095, 6650).
- **Tags (top 5, with counts):**
  - Being a DIK S1: Sexual Content 3091, Nudity 2447, Visual Novel 1301, Choices Matter 656, Romance 464. Dating Sim is #11 (202), Hentai #18 (108).
  - Karryn's Prison: Sexual Content 1661, Hentai 1108, Nudity 1030, Female Protagonist 929, JRPG 394.
  - Koikatsu Party: Sexual Content 3104, Nudity 2177, Character Customization 1977, Hentai 1756, Anime 844. Dating Sim is #9 (423).
  - Sex, Secrets & Used Tech: Sexual Content 574, Hentai 465, Nudity 410, Simulation 260, RPG 227. Dating Sim is #9 (181).
  - Lust Goddess: Sexual Content 3440, Nudity 2521, Hentai 1844, Free to Play 1618, Strategy 337.
- **Mature Content Description block:** on all five, the block shows only the developer's own notes (the same text as `content_descriptors.notes`). It does not show Steam-generated descriptor labels. Koikatsu's notes contain the words "Nudity or Sexual Content, General Mature Content", but the developer wrote that text (it is in `notes`), so it is not a Steam label.
- **"Adult Only Sexual Content"** as a label: **not seen** on any of the 31 store pages or the search pages fetched. The only "Adult Only" text seen is the `mature_content_notice` quoted above.

The same 'Adult Only' notice also appeared on HuniePop (339800), HuniePop 2 (930210) and Coming Out on Top (642090). Their appdetails were not fetched.

### 1c. Descriptor id ↔ label evidence

When `notes` is null, the store page shows a Steam-generated sentence in the Mature Content Description block: "This Game may contain content not appropriate for all ages, or may not be appropriate for viewing at work: <labels>".

| Source | ids (appdetails) | Store display text | Inference |
|---|---|---|---|
| Mass Effect LE (1328670) | [1, 2, 5], `notes: null` | "...: Some Nudity or Sexual Content, Frequent Violence or Gore, General Mature Content" | With 2 and 5 already confirmed, **id 1 = "Some Nudity or Sexual Content"** (by elimination, assuming labels map one-to-one to ids) |
| Doki Doki Literature Club (698780) | not fetched | "...: General Mature Content" | consistent with id 5 |

- **Id 3:** no label was displayed. It is present on all 5 adult-only games, and pages carrying it show "This game is marked as 'Adult Only'". It is in the logged-out default exclusion list [3, 4].
- **Id 4:** no label was displayed. It is present on all 5 adult-only games and in the logged-out default exclusion list [3, 4].
- Labels for 3 and 4 are **unconfirmed** from Steam display text.

## 2. Rank of `Dating Sim` (tagid 9551)

Ratio = Dating Sim votes ÷ rank-1 tag votes. Every app below displayed 20 tags.

### Dating sims

| appid | App | Dating Sim rank | DS votes | Rank-1 tag (votes) | Ratio |
|---|---|---|---|---|---|
| 743450 | Monster Prom | **1** | 515 | Dating Sim (515) | 1.000 |
| 310080 | Hatoful Boyfriend | 2 | 411 | Visual Novel (459) | 0.895 |
| 654880 | Dream Daddy: A Dad Dating Simulator | 2 | 556 | LGBTQ+ (599) | 0.928 |
| 339800 | HuniePop | 4 | 1466 | Nudity (2768) | 0.530 |
| 930210 | HuniePop 2: Double Date | 4 | 266 | Sexual Content (488) | 0.545 |
| 674930 | Boyfriend Dungeon | 4 | 425 | Comedy (476) | 0.893 |
| 642090 | Coming Out on Top | 4 | 261 | LGBTQ+ (813) | 0.321 |
| 698780 | Doki Doki Literature Club! | 5 | 5873 | Psychological Horror (9307) | 0.631 |
| 1073440 | Koikatsu Party (adult; from Q1) | 9 | 423 | Sexual Content (3104) | 0.136 |
| 3576350 | Sex, Secrets & Used Tech (adult; from Q1) | 9 | 181 | Sexual Content (574) | 0.315 |
| 1126320 | Being a DIK - Season 1 (adult; from Q1) | 11 | 202 | Sexual Content (3091) | 0.065 |

Mystic Messenger was not checked on Steam (no search done).

### `?tags=9551` search, top 10 (logged out, default relevance sort, filtered by [3,4])

1. Stardew Valley
2. Monster Hunter Wilds
3. The Sims 4
4. Persona 3 Reload
5. VRChat
6. Persona 5 Royal
7. Fields of Mistria
8. inZOI
9. Palia
10. ELDEN RING NIGHTREIGN

Ranks 11–25 continue: DYNASTY WARRIORS: ORIGINS (11), ULTRAKILL (12), Undertale (13), Persona5: The Phantom X (14), Yakuza 0 Director's Cut (15), World Apart (16), Slay the Princess — The Pristine Cut (17), CODE VEIN II (18), Persona 4 Golden (19), GIRLS' FRONTLINE 2: EXILIUM (20), Date Everything! (21), Ledgerbound (22), DRAGON BALL GEKISHIN SQUADRA (23), STEINS;GATE RE:BOOT (24), Five Hearts Under One Roof season2 (25).

Three of the top 10 were checked:

| appid | App | Dating Sim rank | DS votes | Rank-1 tag (votes) | Ratio |
|---|---|---|---|---|---|
| 2246340 | Monster Hunter Wilds | 11 | 1462 | Hunting (2469) | 0.592 |
| 1222670 | The Sims 4 | 9 | 1914 | Life Sim (2374) | 0.806 |
| 2142790 | Fields of Mistria | 2 | 582 | Farming Sim (636) | 0.915 |

### Mainstream games with romance or dating elements

| appid | App | Dating Sim rank | DS votes | Rank-1 tag (votes) | Ratio |
|---|---|---|---|---|---|
| 1158160 | Coral Island | 3 | 350 | Farming Sim (476) | 0.735 |
| 1084600 | My Time at Sandrock | 6 | 302 | Life Sim (422) | 0.716 |
| 2161700 | Persona 3 Reload | 11 | 490 | JRPG (799) | 0.613 |
| 1113000 | Persona 4 Golden | 14 | 548 | JRPG (1597) | 0.343 |
| 1580240 | Rune Factory 4 Special | 18 | 49 | RPG (252) | 0.194 |
| 1687950 | Persona 5 Royal | 20 (last) | 734 | JRPG (1363) | 0.539 |
| 1328670 | Mass Effect Legendary Edition | absent | – | Story Rich (630) | – |
| 1392960 | STORY OF SEASONS: Pioneers of Olive Town | absent | – | Farming Sim (274) | – |
| 1145360 | Hades | absent | – | Action Roguelike (1457) | – |
| 1091500 | Cyberpunk 2077 | absent | – | Cyberpunk (7291) | – |

For comparison, earlier finding 09: Stardew Valley has Dating Sim at rank 17/20.

#### Notes on individual pages

- **Mass Effect LE:** Romance is #12 (288), Sexual Content #11 (301), Nudity #15 (219).
- **SoS: Pioneers of Olive Town:** Romance is #6 (231).
- **Cyberpunk 2077:** Nudity is #3 (6081), and the 20th tag is LGBTQ+ (701).
- **Hades:** the 20th tag is LGBTQ+ (111).
- **Persona 5 Royal:** ranks 2–19 are tightly bunched (1109 down to 1051). Dating Sim (734) is the 20th displayed tag.

## Appid resolution and wrong guesses

| Guessed appid | Actually is | Resolved via search to |
|---|---|---|
| 693190 | "Survival driver 2: Heavy vehicles" | Dream Daddy **654880** |
| 1095450 | "Puzzle Walker (Demo)" | Boyfriend Dungeon **674930** |
| 397090 | "Wind Child" | Coming Out on Top **642090** |
| 1294720 | "Balloon Blast" | Rune Factory 4 Special **1580240** |
| 1253330 | 302 → store homepage | SoS: Pioneers of Olive Town **1392960** |

The other appids were confirmed from the page `<title>` and from the `InitAppTagModal` appid argument.

## Unverified / not done

- Steam display labels for descriptor ids 3 and 4. "Adult Only Sexual Content" was never seen as a label.
- appdetails for HuniePop, HuniePop 2, Coming Out on Top and DDLC (descriptor ids not fetched).
- The `/agecheck/` page content for logged-out requests without cookies (only the 302 was observed).
- Mystic Messenger presence on Steam.
- Whether results differ by country (all requests were reported as BG).

## Raw files

Scratchpad (not in repo): `C:\Users\Lenovo\AppData\Local\Temp\claude\C--Users-Lenovo-Desktop-Claude-SteamTags\fa7f595b-b268-41d5-b7bb-6ab4b62c0ce9\scratchpad\s09b\` (`app_*.html`, `ad_*.html`, `srch_*.html`, `q_*.html`, `log.txt`).
