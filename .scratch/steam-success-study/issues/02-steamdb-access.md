# SteamDB access and tag/metadata alternatives
Type: research
Status: resolved
Blocked by: none

## Question

Can tags and metadata be obtained from SteamDB compliantly, and if not, which public sources can provide the same fields?

Required fields per app: displayed user tag list (with rank/votes if available), Steam app type (game/DLC/demo/tool...), store developer genre field, `is_free`, store release date, name.

- SteamDB terms, robots.txt, anti-bot protection, any official API or export.
- Candidate substitutes and their terms/rate limits: Steam store `appdetails` endpoint, Steam store page tags, SteamSpy `appdetails`, Steam Web API. Which fields each provides and how closely each matches the tag list shown on the store page.
- Note: substitution needs researcher sign-off; this ticket only gathers facts.

## Answer

**SteamDB: not compliantly, at scale, without permission.**
- Its FAQ says "We also do not allow scraping/crawling on SteamDB". Academic scraping is "Not without permission", which means a university email with a project overview. Access is not guaranteed and there are no dumps.
- SteamDB has no public API and runs behind Cloudflare with automatic bans. Manual human viewing is the only unrestricted use.

**Steam first-party sources cover every required field. SteamDB's own FAQ points to them first.**
- **Store `appdetails` (undocumented):** `type`, `name`, `is_free`, `genres[]` and `release_date` (a localized string). It has **no tags**.
- **Store page HTML:** embeds `InitAppTagModal` with the exact displayed top-20 tag list, giving `{tagid, name, count}` in display order. This is the best match to the **Tag** definition.
- **Web API `IStoreService/GetAppList` (documented, key, 100k calls/day):** for enumeration only.
- **`IStoreBrowseService/GetItems` (undocumented):** tag ids with scaled weights in display order, plus a numeric type and a release timestamp. It has no genre field.

**SteamSpy `appdetails`:** 1 request per second, no stated terms. It gives tags with votes and a genre string, but no release date and no type. Its tags diverged from the store list (for Portal 2 it lacks "Singleplayer", the store's #1 tag).

All non-SteamDB options are **Source Substitutions** and need researcher sign-off. The open items are the SSA "Automation" clause and age gates on mature titles.

Details, matrix and citations: [../research/02-steamdb-access.md](../research/02-steamdb-access.md)
