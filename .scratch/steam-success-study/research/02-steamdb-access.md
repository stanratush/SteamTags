# Research 02: SteamDB access and tag/metadata alternatives

Ticket: [../issues/02-steamdb-access.md](../issues/02-steamdb-access.md)
Fetch date for every source below: **2026-10-03**. Inspection was manual-scale: about 15 fetches in total, one sample app (Portal 2, AppID 620), and no SteamDB app pages.

## Question

Can we get tags and metadata from SteamDB compliantly? If not, which public sources provide the same fields?

Required fields per app: the displayed user tag list (with rank and votes if available), Steam app type, the store's developer genre field, `is_free`, the store release date, and the name.

## 1. SteamDB

### Verified facts

Source: SteamDB FAQ, <https://steamdb.info/faq/>

- **No scraping.** Entry "Can I use auto-refreshing plugins or automatically scrape/crawl SteamDB?" answers that you may be banned automatically for doing so, and that "We also do not allow scraping/crawling on SteamDB."
- **Academic use needs permission.** Entry "Can I scrape SteamDB for academic purposes?" opens with "Not without permission." Its main points:
  - Check first whether the data can come straight from Steam, using SteamKit or by parsing store pages.
  - Coursework, assignments and class projects involving data scraping or analysis should "seek alternative data sources".
  - Permitted use is academic only, never commercial. Selling or publishing the data in its entirety, or training AI models on it, is prohibited.
  - SteamDB does not provide direct data access or dumps. A granted request only gives a way past their protections, and the scraping is still manual work for the requester.
  - Access is not guaranteed, and SteamDB will not reply to requests it considers invalid or out of scope.
  - Requests go from a university email address and must include a detailed overview of the project. The contact route is the FAQ's "How to contact you?" section (Discord, or an email address revealed after a click-through).
- **No API.** Entry "Does SteamDB have an API?" says they will "most likely" build one "at some point" and gives partnerships@steamdb.info for interested developers and publishers. No public API or export exists today.
- **robots.txt** (<https://steamdb.info/robots.txt>):
  - `User-agent: *` gets `Allow: /`. Among the disallowed paths are `/api/PatchnotesRSS/`, `/api/Preview/`, `/api/RenderAppHover/`, `/search/`, `/instantsearch/`, `/calculator/`, `/changelist/`, `/embed/`, `/user/`, `/watching/`, `/cdn-cgi/`, `/*?cc=*`, `/app/*.png`, and the history/branch query patterns.
  - About 20 named SEO and scraper bots (AhrefsBot, SemrushBot, MJ12bot, and others) are fully disallowed.
  - robots.txt does not grant scraping permission. The FAQ prohibition applies independently of it.
- **Anti-bot protection.** The FAQ states that SteamDB uses Cloudflare and bans automatically.
  - Our fetches of `/faq/` and `/robots.txt` returned normally with no challenge.
  - We deliberately did not request SteamDB app or tag pages. Doing so in a pipeline context would be the kind of access the FAQ prohibits.
- **Terms pages.** The FAQ links only a Privacy Policy (<https://steamdb.info/privacy/>) and a Cookie Policy (<https://steamdb.info/cookies/>). We found no separate Terms of Service page. The access policy lives in the FAQ.

### Inference

- **Compliant SteamDB use without permission** is limited to a human viewing pages manually, for example spot-checking a handful of apps.
- **Collecting from SteamDB at Candidate Pool scale** (10,000 or more apps) needs written permission from SteamDB. That permission is discretionary and may never be answered.
- **Publishing a dataset** derived from SteamDB data could conflict with the clause against publishing the data "in its entirety". A Top-100 export is a subset, but whether it is acceptable would need to be confirmed in any permission request.
- **SteamDB itself points to Steam** (SteamKit, store pages) as the first-choice source. Every field this ticket needs is first-party Steam data that SteamDB mirrors, so the original exists at Steam.

## 2. Substitute sources

### 2a. Steam store `appdetails`: `https://store.steampowered.com/api/appdetails?appids=<id>`

- **Official status: undocumented.** Valve's Steamworks Web API docs do not list it. It is the JSON endpoint the store's own front end uses.
- **Verified.** We fetched `appids=620&cc=us&l=english`. The `data` keys include:
  - `type`: `"game"`
  - `name`: `"Portal 2"`
  - `steam_appid`: `620`
  - `is_free`: `false`
  - `release_date`: `{"coming_soon": false, "date": "Apr 18, 2011"}`
  - `genres`: `[{"id":"1","description":"Action"},{"id":"25","description":"Adventure"}]`
  - `developers`, `publishers`, `categories`, `price_overview`, `content_descriptors`, `ratings`, and others
- **There is no `tags` key.**
- **Release date is a localized display string**, not a timestamp, so it needs parsing (and `l=english` should be fixed).
- **Not verified:**
  - Rate limit. No official figure exists. Community sources commonly cite about 200 requests per 5 minutes, which we treat as an unverified estimate.
  - The full list of `type` values. Commonly seen values include `game`, `dlc`, `demo`, `mod`, `music`, `video`, and `advertising`; this is inference, not documented.
  - Behaviour for delisted or region-locked apps. Expected to be `success:false`; not tested.

### 2b. Steam store page HTML: `https://store.steampowered.com/app/<id>/`

- **Verified.** One plain `curl` fetch, default user agent, `?l=english`, returned HTTP 200 with no age gate for Portal 2. The page embeds `InitAppTagModal(620, [...])`, a JSON array of `{tagid, name, count, browseable}`.
  - It contained exactly **20 entries in display order**, starting `{"tagid":4182,"name":"Singleplayer","count":7767}`, then Platformer (7564), Puzzle (7540), and so on.
  - The visible tag list and the visible "Genre:" field (Action, Adventure) match it.
- **This is the displayed store tag list itself**, with rank (array order) and raw vote counts. It is the closest match to the CONTEXT.md definition of **Tag**.
- **Steamworks documentation** (<https://partner.steamgames.com/doc/store/tags>):
  - Tags are applied "by the developer, by players with non-limited accounts, and by Steam moderators".
  - "Only the top 20 are visible to users".
  - Tag weights "may change over time".
  - Developers can remove and reorder tags.
  - So the displayed list is capped at 20 and is a current snapshot, not historical.
- **Store robots.txt** (<https://store.steampowered.com/robots.txt>) disallows only `/share/`, `/news/externalpost/`, `/email/`, `/widget/`, and some account, login and join token URLs. `/app/` is not disallowed.
- **Steam Subscriber Agreement** (<https://store.steampowered.com/subscriber_agreement/>):
  - It has an "Automation" clause: "You may not use any form of scripts, bots, macros, or other non-human-controlled systems ("Automation") to interact with Content and Services on Steam in any manner, including but not limited to" account creation, faked gameplay statistics, unearned rewards, and automated adjudication.
  - We found no clause that specifically addresses crawling public store pages.
- **Not verified or inferred:**
  - Whether anonymous, logged-out fetching of public store pages falls under the Automation clause. The clause binds subscribers, and its examples are account and gameplay abuse. Its applicability to research crawling is ambiguous and should be judged by the researcher, and possibly by an institutional or ethics reviewer.
  - Mature or sexual-content titles may redirect to an age-check page. Passing it (for example with a birth-date cookie) is a deliberate gate, not anti-bot, but whether to do so is a researcher decision. We did not test it.
  - The parsing depends on undocumented page markup, which can change without notice.
  - There is no published rate limit.

### 2c. Steam Web API (official, key-based): `api.steampowered.com`

- **Terms of Use** (<https://steamcommunity.com/dev/apiterms>):
  - "You are limited to one hundred thousand (100,000) calls to the Steam Web API per day."
  - Valve name and logo attribution is licensed.
  - The privacy and storage clauses concern data about Steam *end users*, which does not apply to app metadata.
  - Research use is not specifically addressed.
- **`IStoreService/GetAppList`** (<https://partner.steamgames.com/doc/webapi/IStoreService>, documented):
  - Requires an API key.
  - Filters: `include_games`, `include_dlc`, `include_software`, `include_videos`, `include_hardware`.
  - Paging: `last_appid` and `max_results` (default 10,000, max 50,000).
  - Returns appid, name, `last_modified` and `price_change_number`.
  - **Does not return tags, genres, `is_free`, release date or type.** It is useful only for enumerating the Candidate Pool and for a coarse type filter.
- **`IStoreBrowseService/GetItems`** is undocumented. `https://partner.steamgames.com/doc/webapi/IStoreBrowseService` has no page; it fell back to the doc index.
  - **Verified with one keyless call** for appid 620, using `include_tag_count:20`, `include_basic_info`, and `include_release`. It returned:
    - `type` (numeric, `0`)
    - `name`
    - developers and publishers
    - `tagids` and `tags: [{tagid, weight}]`, 20 entries, **in the same order as the store page** (weights 603, 588, 586...)
    - `release.steam_release_date` (Unix time 1303186800)
    - price info
  - **Weights are scaled values, not the raw vote counts** shown in the store page JSON.
  - The response has **no genre field**, and tag names need a separate lookup.
  - We did not test whether `is_free` appears for free apps.
- **Inference.** Being undocumented, IStoreBrowseService carries a stability risk. Its terms position is presumably the Steam Web API Terms, since it is served from `api.steampowered.com`, but Valve does not state this.

### 2d. SteamSpy API: `https://steamspy.com/api.php`

- **Documented** (<https://steamspy.com/api.php>):
  - Rate limits: "1 request per second for most requests, 1 request per 60 seconds for the *all* requests"; `all` returns 1,000 entries per page.
  - `appdetails` returns appid, name, developer, publisher, owners (a range), playtime averages and medians, ccu, price, initialprice, discount, languages, `genre`, and "tags - game's tags with votes".
  - **No release date and no app type are documented.**
- **Verified** with `request=appdetails&appid=620`:
  - `genre: "Action, Adventure"` (comma-joined string)
  - `price: "999"`
  - `owners: "5,000,000 .. 10,000,000"`
  - 20 tags with votes
- **SteamSpy's tag list differed from the store page** on the same day:
  - SteamSpy **omits "Singleplayer"**, the store's #1 tag.
  - It includes "Adventure", which is absent from the store's top 20.
  - It spells "Puzzle-Platformer" where the store has "Puzzle Platformer".
  - Its counts are systematically lower (Platformer 7477 vs 7564), suggesting a lagged snapshot.
  - Overlap was 19 of 20 tags.
- **No terms of use or data licence** are stated on the API page or on <https://steamspy.com/about>. The about page says its data "isn't 100% correct" and describes extrapolation from user-profile samples. That text appears to predate later changes; we did not verify its currency.
- **Inference.** SteamSpy is a secondary mirror of Steam tags. It does not reproduce the displayed store list exactly, and that matters because "has tag" is defined against the displayed list (it would mis-assign Singleplayer for Portal 2). `is_free` can only be inferred from `price == "0"`, which is not the same as Steam's flag.

## 3. Field-by-source matrix

Legend: Y = provided, verified on 2026-10-03; Y* = provided per docs but not verified in the sample; P = partial or derived; N = not provided; ? = unknown.

| Field | SteamDB | Store `appdetails` | Store page HTML | Web API `GetAppList` | `IStoreBrowseService/GetItems` (undoc.) | SteamSpy `appdetails` |
|---|---|---|---|---|---|---|
| Name | Y (but no compliant automated access) | Y | Y | Y | Y | Y |
| Displayed tag list (top 20, order) | Y (no compliant access) | **N** | **Y**, exact display order | N | Y (ids only; same order in sample; names via lookup) | P (19/20 overlap in sample; different set and order) |
| Tag votes | ? (not inspected) | N | **Y** raw `count` | N | P scaled `weight` | Y* lagged vote counts |
| App type (game/DLC/demo...) | Y | **Y** `type` string | N (not structured) | P (include_* filters only) | P numeric `type` (mapping undocumented) | N |
| Developer genre field | Y | **Y** `genres[]` with ids | Y (visible "Genre:" text) | N | N | P comma string |
| `is_free` | Y | **Y** | P (visible price text) | N | ? (not tested on a free app) | P (`price=="0"` inference) |
| Store release date | Y | Y (localized string) | Y (display string) | N | Y Unix timestamp | N |
| Documented / official | No API | Undocumented | Undocumented markup | **Documented** | Undocumented | Documented (third party) |
| Published rate limit | n/a | None (≈200 req/5 min community estimate, unverified) | None | 100,000 calls/day (Web API ToU) | Presumably Web API ToU (unverified) | 1 req/s; `all` 1 req/60 s |
| Compliance position | Scraping prohibited; academic only by permission | Valve first-party; no explicit terms | Valve first-party; SSA Automation clause ambiguous | Explicit ToU | Unclear | No terms stated |

## 4. Options (for researcher decision, not recommendations)

1. **Request SteamDB academic permission.** Send a university email with a project overview. The outcome is uncertain, and SteamDB still would not give dumps.
2. **Combine Steam first-party sources**, which SteamDB's own FAQ points to:
   - `GetAppList` for enumeration
   - `appdetails` for type, genres, `is_free`, release date and name
   - store page `InitAppTagModal` for the displayed tag list with ranks and votes
   - This counts as a **Source Substitution** under CONTEXT.md, even though it is the upstream source.
3. **Same as option 2, but with `IStoreBrowseService/GetItems`** for tags in batches instead of store pages. It returns weights rather than votes, depends on an undocumented endpoint, and is also a Source Substitution.
4. **Use SteamSpy for tags.** It is the simplest option, but it does not match the displayed list, so it is a methodological deviation from the **Tag** definition.

## 5. Could not verify

- Any official rate limit for `store.steampowered.com/api/appdetails` or for store pages.
- Whether Valve considers anonymous research crawling of store pages covered by the SSA Automation clause.
- The `IStoreBrowseService` type-code mapping, its `is_free` field, and its official status.
- How SteamDB tag pages present vote data. Not inspected, by design.
- The currency of SteamSpy's methodology statements.
- Age-gate behaviour for mature titles on the store page and in `appdetails`.
