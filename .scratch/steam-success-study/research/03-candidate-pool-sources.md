# Research 03: Candidate Pool enumeration sources

Ticket: [../issues/03-candidate-pool-sources.md](../issues/03-candidate-pool-sources.md)
Fetched: 2026-10-03 (all URLs below, unless marked otherwise). About 20 single-page fetches in total; no bulk access.

## Question

Which compliant sources can enumerate a **Candidate Pool** of at least 10,000 games that very likely contains every true Top-100 game by **Mean Monthly Players** over Oct 2021 – Sep 2026, including games that have since declined or been delisted?

## Short answer

- **Primary recommendation: the complete Steam Charts `/top` listing.** It is ordered by current players, but it does not stop at a popularity cutoff. It runs on into apps with 0 current players, at about 12,750 to 13,725 rows in total. If the pool is the whole listing rather than its first N rows, then it is, by construction, (nearly) every app Steam Charts can score. Since Steam Charts is also the scoring source, a game missing from it could not be scored anyway. No Source Substitution is needed.
- **Catch:** the listing mixes in non-games (demos, DLC, soundtracks). Once filtered to app type `game`, the count could drop below 10,000 (unmeasured).
- **Cross-checks** (enumeration only, so they never score anything): SteamSpy `top100forever` / `top100owned` / `all`, and Valve's annual "Best of Steam: Most Played" lists. Using SteamSpy counts as Source Substitution and needs researcher confirmation.
- **Not useful as the pool:** Steam `GetAppList`. It is unordered, covers the whole catalogue (well over 10k apps), needs a key, and the v2 endpoint is deprecated.
- **Blocked:** SteamDB returns 403 to automated fetches, and its FAQ forbids scraping.

## Verified facts (by source)

### 1. Steam Charts ranked listing: `https://steamcharts.com/top`

- Title: "Top Games by Current Players on Steam". Columns: Name, Current Players, Last 30 Days, Peak Players, Hours Played. Ordered by **current concurrent players**, descending. 25 rows per page. Pagination: `/top/p.N`. (https://steamcharts.com/top)
- At page 400 (`/top/p.400`) the rows are ranks 9,976 to 10,000. The first and last rows ("Last Train Home Demo", "HitTube Demo") each show **1** current player. A Next link is present.
- At page 475 the rows are ranks 11,851 to 11,875, all with **0** current players. One row is "Gal*Gun 2 - Venus Soccer Uniform", which is DLC.
- At page 510 the rows are ranks 12,726 to 12,750, with 0 current players. The rows include "Dragon Hunters Soundtrack" and "BLOODVILLE Demo". A Next link is present.
- Pages 550, 700 and 1000 return **HTTP 404**. So the listing ends between rank 12,750 and rank 13,750 (page 549 or lower). I did not bisect further.
- No anti-bot challenge was encountered on any Steam Charts page.
- About page (https://steamcharts.com/about): the collector "queries the number of concurrent players on an hourly interval" via the Steam Web API and "has been collecting data since July of 2012". It claims to query "every single game in the Steam catalog". It publishes no inclusion criteria, terms of use, scraping policy or API.
- `https://steamcharts.com/robots.txt` returns **404**, so no robots policy is published.
- Per-app page `https://steamcharts.com/app/730` shows a monthly table (Month, Avg. Players, Gain, % Gain, Peak Players) from July 2012 to September 2026, plus a partial "Last 30 Days" row. The pipeline must drop that partial row.
- A declined, later-delisted game keeps its page. `https://steamcharts.com/app/1818750` (MultiVersus) has monthly data from July 2022 and showed "25 playing" at fetch time. Caveat: the fetch summary gave July 2022 = 66,920 avg players but called August 2022 = 41,553 the highest month. That is inconsistent, so re-read it manually before relying on the numbers.

### 2. SteamSpy API: `https://steamspy.com/api.php`

- Requests:
  - `appdetails`, `genre`, `tag`
  - `top100in2weeks` (recent players), `top100forever` (all-time players), `top100owned` (owners)
  - `all`: "Returns 1,000 entries per page", pages start at 0, "sorted by owners".
- Rate limit, quoted: "1 request per second for most requests, 1 request per 60 seconds for the all requests". Data refreshes once a day.
- Fields: appid, name, developer, publisher, score_rank, owners (a range), average/median playtime (forever and 2 weeks), ccu, price, tags, languages, genre.
- No licensing terms are stated on the docs page.
- A live check with `appdetails&appid=730` returned JSON with no challenge (owners "100,000,000 .. 200,000,000", ccu 1,013,936).

### 3. Steam Web API: app lists

- `ISteamApps/GetAppList` is documented as: "Deprecated - this API can no longer scale to the number of items available on Steam. Please use IStoreService/GetAppList instead." (https://partner.steamgames.com/doc/webapi/ISteamApps). The live URL `https://api.steampowered.com/ISteamApps/GetAppList/v2/` returned **404**.
- `IStoreService/GetAppList/v1` (https://partner.steamgames.com/doc/webapi/IStoreService):
  - Requires `key` ("Any web API key").
  - Filters: `include_games` (on by default), `include_dlc`, `include_software`, `include_videos`, `include_hardware`, `if_modified_since`, `have_description_language`.
  - Pagination: `last_appid`, `max_results` ("Default 10k, max 50k").
  - Returns appid, last_modified and price_change_number. There is no player or popularity data, so it gives no ordering.
- Steam Web API Terms (https://steamcommunity.com/dev/apiterms): "You are limited to one hundred thousand (100,000) calls to the Steam Web API per day." Research use is not addressed.

### 4. SteamDB: `https://steamdb.info/charts/`

- Returned **HTTP 403** to a plain fetch. I made no attempt to get around it.
- FAQ (https://steamdb.info/faq/): "We also do not allow scraping/crawling on SteamDB." It has no public API. For academic data, you request it by university email; it is academic-only, with no AI training, and the request can be refused.

### 5. Valve "Best of Steam" annual lists, e.g. `https://store.steampowered.com/sale/BestOf2024`

- The page content is loaded by JavaScript. A plain fetch returned only the navigation, with no game list, so I **could not verify the list or its criteria from the primary source**.
- Secondary reporting (gamegrin.com, "Steam's Best of 2024 — Most Played") says:
  - Most Played = games played in 2024 with more than 40,000 peak concurrent players, excluding free weekends.
  - Games are grouped in tiers, randomly sorted within each tier: Platinum (1–12), Gold (13–24), Silver (25–50), Bronze (51–100).
- **Unverified at primary level.** Someone would need to check this by hand in a normal browser.

## Assessment per option

| Option | Size | Ordering | Terms / limits | Blind spots |
|---|---|---|---|---|
| Steam Charts `/top`, full listing | about 12.75k–13.7k apps (bounded, not exact) | current players | no ToS, robots or rate limit published; about 520–550 page requests | includes non-games (demos, DLC, soundtracks), so the game-only count is unknown and may be under 10k; inclusion rule not documented; listing taken whole is order-independent |
| Steam Charts `/top`, first N rows | N | current players | as above | **misses declined games**; at rank 10,000 current players is already about 1, so ranks there are noise |
| SteamSpy `all` | not measured (pages × 1,000) | estimated owners | 1 request per 60 s; **Source Substitution** | owners ≠ concurrent play; can miss high-play, low-owner games; delisted handling unknown |
| SteamSpy `top100forever` / `top100owned` / `top100in2weeks` | 100 each | all-time players / owners / recent | 1 request per second; Source Substitution | only 100; good as a cross-check only |
| `IStoreService/GetAppList` | entire catalogue (far above 10k; not counted) | appid (none) | API key; 100k calls/day | no popularity, so it cannot pick a pool by itself; may exclude delisted apps (inference) |
| SteamDB | n/a | n/a | scraping forbidden, 403 | only via an academic email request |
| Valve Best of Steam "Most Played" (2021–2025) | about 100 per year | peak-CCU tiers | manual browser view; first-party | annual peaks, not monthly averages; complete only for big games |

## Inference (not verified)

- **Steam Charts does not track the full catalogue.** It claims "every single game", but the listing holds only about 13k apps, while `GetAppList` covers far more. It likely tracks apps that have shown up in Steam's player statistics at some point. Whatever the rule is, a Top-100 game by Mean Monthly Players would be tracked by definition, because it needs Steam Charts data to be scored.
- **The whole `/top` listing should cover every game Steam Charts can score.** It includes apps with 0 current players, and delisted games such as MultiVersus keep pages. Not verified: whether apps that are tracked but delisted or retired ever drop out of `/top` while keeping an `/app/` page.
- **Scale of the 100th game (estimate, not measured).** The 100th game's Mean Monthly Players is probably in the low thousands to about 10k avg players. Any game at that level needs at least one month above the threshold, so it would appear in SteamSpy `top100forever` / `top100owned` and/or in the Best of Steam Most Played tiers for some year. That makes those good independent proxies.

## Evidence that the pool is complete enough (proposed checks)

1. **Containment by construction.** Pool = every row of the Steam Charts `/top` listing. Record the total row count and the snapshot timestamp.
2. **Proxy overlap.** Every appid in these lists should be in the pool:
   - SteamSpy `top100forever`, `top100owned` and `top100in2weeks` (a 3-request snapshot)
   - Valve Best of Steam Most Played lists for 2021–2025 (manual), if confirmed as an allowed source
   Report any misses by name.
3. **Known-declined spot check.** Look up a hand-picked list of games that were large and then declined or were delisted during the window (e.g. MultiVersus, appid 1818750) in the pool.
4. **Margin at the cutoff.** After scoring, compare the 100th score with the highest single-month Avg. Players of any app that was *not* in the pool. Apps outside the pool have no Steam Charts data, so this should be empty or zero.

## Open points / could not verify

- The exact last page of `/top`: 404 at page 550, data at page 510.
- The share of non-games in `/top`, and so whether the type-`game` pool reaches 10,000.
- The Best of Steam criteria at the primary source (the page is JS-rendered).
- SteamSpy `all` total page count, and how it handles delisted apps.
- Steam Charts' terms for automated access: none are published, so a conservative request rate is a researcher decision.
