# Candidate pool enumeration sources
Type: research
Status: resolved
Blocked by: none

## Question

Which compliant sources can enumerate a Candidate Pool of at least 10,000 games that is very likely to contain every true Top-100 game by Mean Monthly Players over Oct 2021 – Sep 2026 (including games that were large earlier in the window but have since declined or been delisted)?

- Options to assess: Steam Charts' own ranked listings, SteamSpy top/all lists, Steam `GetAppList`, others found.
- For each: size, ordering criterion, terms/rate limits, and blind spots (e.g. ranking by current players misses declined games).
- What evidence could show the pool is complete enough (e.g. overlap between proxies, rank of the 100th game vs. pool cutoff)?

## Answer

- **Use the entire Steam Charts `/top` listing as the Candidate Pool.** No Source Substitution is needed.
  - It is ordered by current players, 25 rows per page.
  - It does not stop at a popularity cutoff: it runs on into apps with 0 current players and ends between rank 12,750 and rank 13,750 (page 510 has data, page 550 returns 404).
  - Taken whole, it covers (nearly) every app Steam Charts can score, including declined or delisted games, whose `/app/` pages remain (e.g. MultiVersus).
- **Never take only the first N rows.** By rank 10,000 current players are already about 1, so a top-N cut by current players misses declined games.
- **Risk:** the listing includes demos, DLC and soundtracks. After filtering to type `game`, the pool may fall below 10,000 (not measured).
- **Cross-checks** (enumeration only, never scoring): SteamSpy `top100forever` / `top100owned` / `top100in2weeks`, and Valve's Best of Steam "Most Played" lists for 2021–2025. Every one of those appids should be in the pool, plus a hand-picked spot-check list of declined games.
  - SteamSpy needs Source Substitution confirmation. Its limits are 1 request/s, and 1 per 60 s for `all` (1,000 rows per page, sorted by owners).
- **`IStoreService/GetAppList`** needs an API key and gives no popularity data, so it cannot pick a pool by itself. `ISteamApps/GetAppList/v2` is deprecated and returns 404.
- **SteamDB** returns 403 and its FAQ forbids scraping. It offers academic data only on request by email.
- **Steam Charts** publishes no ToS, robots.txt (404) or rate limit, so the researcher sets the request rate (about 520–550 listing pages).

Details and citations: [../research/03-candidate-pool-sources.md](../research/03-candidate-pool-sources.md)
