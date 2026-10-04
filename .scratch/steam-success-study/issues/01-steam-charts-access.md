# Steam Charts compliant access and coverage
Type: research
Status: resolved
Blocked by: none

## Question

Can monthly player history be collected from Steam Charts (steamcharts.com) for 10,000+ apps without violating its terms or bypassing anti-bot protection, and what exactly does it provide?

- Terms of use, robots.txt, any stated rate limits or API; presence of Cloudflare/anti-bot challenges.
- Per-app page structure: does it expose monthly "Avg. Players" and "Peak Players" back to Oct 2021, and how are the current (incomplete) month and gaps shown?
- Coverage: which apps are tracked, roughly how many, from when; how can the list of tracked apps be enumerated?
- A safe request rate and the resulting wall-clock estimate for 10k+ apps.

## Answer

**Yes, probably, with caveats.** Steam Charts has no terms of use, no robots.txt (404, which under RFC 9309 means no restrictions), no API and no stated rate limit. Its only legal page is a privacy policy. It sits behind Cloudflare, but about 20 plain requests at 3–5 s spacing saw no challenge, cookie or 429.
- **Per-app pages:** `/app/{appid}` carries the full monthly table in raw HTML: Month, Avg. Players (2 decimals), Gain, % Gain, Peak Players. It goes back to July 2012 where data exists. One request per app is enough. `chart-data.json` holds peaks, not averages.
- **Current month:** the first row, `Last 30 Days`, is rolling, not a calendar month, so ignore it. On 2 Oct no October row existed, and the newest month was September 2026.
- **Gaps:** gaps are omitted rows, not zeros. Some apps have a `0.00` placeholder row years before release (Scorn: September 2017, then October 2022). Some listed apps have no month rows at all.
- **Enumeration:** `/top/p.N` gives 25 per page, sorted by current players. It holds about 11,900–13,700 apps (estimate) and includes demos, playtests, servers and tools. It is a subset of the Steam catalog.
- **Rate:** 1 request per 5 s on one connection gives about 14–17 h for 10–12.5k apps, plus about 45 min to enumerate (estimates). Stop on any 403, 429, 503 or challenge.

**Decisions needed:**
1. How to treat 0.00/0 placeholder rows, since they bend the **Release Month** definition.
2. Whether to contact the operator first.
3. Whether `/top` is the enumeration source or IDs come from elsewhere. Elsewhere may be a **Source Substitution**.

Details and citations: [../research/01-steam-charts-access.md](../research/01-steam-charts-access.md)
