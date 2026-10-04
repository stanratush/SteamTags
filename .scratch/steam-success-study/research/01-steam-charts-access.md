# Research 01: Steam Charts compliant access and coverage

Ticket: [../issues/01-steam-charts-access.md](../issues/01-steam-charts-access.md)
Fetch date: 2026-10-03 local time (server `Date` headers read Fri, 02 Oct 2026 21:43–21:50 GMT).
Method: about 20 plain `curl` GETs, one at a time, spaced 3–5 s apart. User-Agent was `SteamSuccessStudy-manual-inspection/0.1 (academic research)`. No browser emulation, proxies, cookies or challenge solving.

## Summary

- **Access:** Steam Charts publishes no terms of use, no robots.txt (404), no API and no stated rate limit. The only legal page is a privacy policy. The site sits behind Cloudflare, but plain non-browser requests got HTTP 200 with no challenge during this light test.
- **Per-app data:** each `/app/{appid}` page holds the full monthly table (Month, Avg. Players, Gain, % Gain, Peak Players) in its raw HTML. One request per app gets everything, back to July 2012 where data exists.
- **Gaps:** a missing month has no row at all. Some apps have a 0.00 placeholder row long before release, which affects how **Release Month** is defined (see the pitfalls section).
- **Coverage:** the paginated `/top` list currently holds roughly 11,900–13,700 apps (estimate). It mixes games with demos, playtests, servers and tools. It is a subset of the Steam catalog and can be enumerated at about 500 pages.
- **Wall-clock time:** about 17 h at 1 request per 5 s for 12k apps (estimate).

## Verified facts (observed directly)

### Terms, robots.txt, API, anti-bot

| Item | Finding | Source |
|---|---|---|
| robots.txt | `HTTP 404`, body `404 page not found` (served by Cloudflare, `cf-cache-status: HIT`) | https://steamcharts.com/robots.txt |
| Terms of use | No `/terms` page (404). The site footer links only About, Privacy and Advertise. | https://steamcharts.com/terms, https://steamcharts.com/ |
| Privacy policy | Exists, built from a Docular template. It covers personal data, cookies and analytics only. A keyword search found no mention of scraping, crawling, automated access, bots, licensing or reuse of data. | https://steamcharts.com/privacy |
| About page | The data comes from a collector service that queries the Steam Web API every hour "for every single game in the Steam catalog" and has been collecting since July 2012. Written in Go with PostgreSQL, hosted on DigitalOcean (New York). Contact is via Twitter (@steamcharts) or the operator's personal site (james4k.com). No API is offered. | https://steamcharts.com/about |
| Footer | "All data is powered by Steam. Not affiliated with Valve in any way." | every page |
| Cloudflare | All responses carry `Server: cloudflare` and a `CF-RAY` header. **No challenge page, `Set-Cookie`, `Retry-After` or rate-limit header was seen** across about 20 requests. HTML is `cf-cache-status: DYNAMIC`; `chart-data.json` and robots.txt were `HIT`. | response headers |
| Data freshness | The homepage and `/top` `Last-Modified` values (21:01 and 21:15 GMT) suggest hourly regeneration. The app "playing" timestamp was 20:34Z. | response headers, `/app/1401150` |

### Per-app page structure (`/app/{appid}`)

Example: https://steamcharts.com/app/730 (Counter-Strike 2)

- The header shows current players with a timestamp, the 24-hour peak and the all-time peak.
- The table columns are `Month | Avg. Players | Gain | % Gain | Peak Players`.
- **The values are raw numbers in the HTML.** For example, `<td class="right num-f">805637.82</td>` holds Avg. Players with 2 decimals, and `<td class="right num">1450705</td>` holds Peak Players. Client-side JavaScript (`d3 ... app.formatText`) only reformats them for display, so no JS execution is needed.
- The **first row is `Last 30 Days`** (italic, class `italic`). It is a rolling window, not a calendar month. For app 730 its Avg (805182.63) differs from September 2026 (805637.82), and its Gain (-455.2) equals the difference between them.
- Month rows follow, newest first, labelled `September 2026`, …, `July 2012`.
- **Current month:** at fetch time (2 Oct 2026, about 21:45 UTC) **no `October 2026` row existed** on any page checked. The newest calendar row was September 2026. I did not verify whether an in-progress month row appears later in a month.
- Depth: app 730 has 171 contiguous month rows from July 2012 to September 2026 (checked programmatically). This confirms that history reaches back well before October 2021.
- The first month row shows `-` for Gain and % Gain (e.g. Little Kitty, Big City, May 2024, https://steamcharts.com/app/1177980).
- **Gaps are shown by omitted rows, not zeros.** Scorn (https://steamcharts.com/app/698670) jumps from `October 2022` straight to `September 2017`, with no rows in between. The October 2022 row then shows `% Gain = +Inf%`, which means the site treats the previous value as 0.
- **Placeholder rows exist.** Scorn has a `September 2017` row with Avg `0.00` and Peak `0`, five years before its October 2022 release.
- **Some listed apps have no month rows at all.** Black Hole Simulator (https://steamcharts.com/app/1401150) shows only `Last 30 Days` (Avg 0.07, Peak 1), with an all-time peak of 2.
- Unknown or untracked app IDs return HTTP 404 with a "Page Not Found" body (https://steamcharts.com/app/999999990).
- The page also loads `/app/{appid}/chart-data.json` (https://steamcharts.com/app/730/chart-data.json). It is a JSON array of `[epoch_ms, value]` pairs. The older points match the monthly **Peak** values (1642 for July 2012, 52261 for August 2012), and recent points are dense (about hourly). **It does not contain monthly Avg. Players**, so the HTML table is the required source for the score.

### Coverage and enumeration (`/top`)

- https://steamcharts.com/top shows 25 apps per page, ranked by **current players**. Columns are Current Players, Last 30 Days (avg), Peak Players and Hours Played. Pagination uses `/top/p.N`. Only Previous and Next links are shown, and no total count appears anywhere.
- Probes (one request each):
  - `p.100`: ranks 2476–2500, about 126–128 current players
  - `p.400`: ranks 9976–10000, about 1 current player
  - `p.475`: ranks 11851–11875, 0 current, mostly 0 for 30 days
  - `p.550`, `p.700`, `p.1000` and `p.4000`: **404**
- So at fetch time `/top` held **between 11,875 and 13,750 entries**. I did not pin down the exact count.
- The `/top` list includes non-games and duplicates of a franchise: demos ("Last Train Home Demo", "HitTube Demo"), playtests ("Acclimate Playtest"), servers ("Arma 3 Server"), tools ("OS Engine"), DLC-like items ("Tom Clancy's The Division 2 - Full Game Ownership", "Fantasy Grounds - …") and adult titles.
- A site search exists at `/search/?q=` (form on every page). There is also a compare page at `/cmp/{appid}`. Neither was needed or tested.

## Inferences (not directly verified)

- **No explicit prohibition.** With no ToS, no robots.txt and no stated limits, nothing on the site forbids polite automated reading of public pages. This is the absence of a rule, **not permission**. The operator could still object, and Cloudflare could start challenging sustained traffic. Asking the operator for permission (Twitter or james4k.com) before a 10k+ app run would be prudent, and would support the study's ethics statement.
- **robots.txt 404:** under RFC 9309 §2.3.1.3, an unavailable (4xx) robots.txt means crawlers may access any resource. This permits crawling but does not constitute a licence to reuse the data.
- **`/top` is not the full catalog.** The About page claims "every single game in the Steam catalog" is tracked, yet `/top` ends near 12–13k entries, and some listed apps (Black Hole Simulator) have no monthly history. My best guess is that `/top` lists apps with some recent tracking record. Whether delisted games, or games that were popular in 2021–2023 and are now dead, still appear is **unverified**. Zero-player entries do appear, so inactivity alone does not drop an app.
- **Rate limit.** Nothing is stated. A conservative, defensible setting is a **single connection at 1 request per 5 s**. Use a descriptive User-Agent with contact details, stop on any 403/429/503 or challenge page, back off exponentially, and run off-peak. This is a judgement call, not a published figure.

## Wall-clock estimates (all estimates)

All figures assume one sequential connection and that every request succeeds the first time.

| Step | Requests | 1 req / 3 s | 1 req / 5 s | 1 req / 10 s |
|---|---|---|---|---|
| Enumerate `/top` | about 475–550 | about 25 min | about 45 min | about 1.5 h |
| App pages, 10,000 apps | 10,000 | about 8.3 h | about 13.9 h | about 27.8 h |
| App pages, 12,500 apps | 12,500 | about 10.4 h | about 17.4 h | about 34.7 h |

Each app page is about 5–55 KB of HTML, so total transfer is roughly 0.2–0.6 GB (estimate). The run must be resumable: store each raw HTML response with its fetch timestamp so it never has to be re-fetched.

## Pitfalls for the pipeline and glossary

1. **Release Month vs placeholder rows.** CONTEXT.md defines Release Month as "the first month for which Steam Charts has data". Scorn's `0.00` September 2017 row would make that the release month, which is wrong. If a placeholder like this falls inside the Observation Window, it would also be averaged in as a real 0 and drag the score down. **Decision needed** (see Answer).
2. **Ignore `Last 30 Days`.** It is not a calendar month. Parse only rows whose label matches `<Month> <YYYY>`.
3. **Collect only after the window's last month has closed.** For an October 2026 run, September 2026 is complete. Snapshot the fetch time per app.
4. **Use Avg. Players from the HTML**, not `chart-data.json`, which holds peaks.
5. **Do not use the table's +Inf%/Gain columns.** They assume 0 before gaps and conflict with the Missing Month rule.
6. **Filter `/top` entries.** It mixes non-game apps (demos, servers, tools, DLC-like entries). Filtering by Steam app type, as the Exclusion rules already do, is required anyway.

## Could not verify

- Steam Charts' behaviour (Cloudflare challenge, throttling) under sustained traffic. Only about 20 requests were made.
- The exact size of `/top` and its inclusion rule. Whether delisted apps are included.
- Whether an in-progress current-month row appears mid-month.
- Why some listed apps (e.g. 1401150) have no monthly rows.
- Any off-site statement by the operator about scraping or reuse. Searches turned up only third-party scraper listings, which are not authoritative.
