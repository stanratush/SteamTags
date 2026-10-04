# Candidate pool definition
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 03, 07

## Question

How exactly is the Candidate Pool of 10,000+ games defined and assembled (source(s), ordering, cutoff, union rules), and what completeness check is reported alongside the datasets?

Surfaced by Candidate pool enumeration sources:
- Pool = the entire Steam Charts `/top` listing (~12.7k–13.7k apps)? It mixes in demos/DLC/soundtracks, so the `game`-only count may fall below 10,000. Does the "≥10,000" requirement apply before or after app-type filtering, given Steam Charts cannot score anything outside its listing?
- Cross-check lists (SteamSpy top-100 lists, Valve Best of Steam "Most Played" 2021–2025, a hand-picked declined-games list): confirm SteamSpy use for verification only (a Source Substitution), and what to do if a cross-check appid is missing from the pool.

## Answer

Resolved 2026-10-03 with the researcher.

- **Pool = every row of the Steam Charts `/top` listing**, no cutoff by current players. "At least 10,000" is reported, not enforced: Steam Charts cannot score anything outside its listing, so nothing is padded from other sources. Any shortfall goes into Known limitations.
- **Unscored apps** (no Monthly Avg. Players value in the Observation Window) simply never rank. They are not an Exclusion and get no separate status; they only appear in the counts.
- **Listing passes:** the listing is read in N full passes and unioned by AppID (dedupe). N is a user parameter like the request rate: **default 2, minimum 1**. Each pass stops at the first 404 or empty page (here a 404 is the end of the listing, not a hard stop). Per pass, record start/end timestamps and row count, plus the number of AppIDs seen in only one pass.
- **No cross-checks in v1:** no SteamSpy, no Valve Best of Steam lists, no hand-picked declined-games list. Declined games can still rank high (e.g. MultiVersus), but reading the whole listing already includes them; the depth check below is the evidence.
- **SteamDB** unchanged from [Data source selection and substitution sign-off](07-data-source-signoff.md): the scraper is built in v1 but disabled until the permission reference is recorded, and it only cross-checks Top-100 tags. The Steam store is the tag source.
- **Games without tags are Exclusions with a recorded reason**, never silent skips:
  - `store_data_unavailable`: no store data (delisted, region-locked, login-only);
  - `no_tags` (new): the store page exists but displays no tags.
  - Both appear in the "would have scored inside a Top 100" report.
  - The Manual Metadata Entry add-back path for `store_data_unavailable` stays as decided in the sign-off ticket (not revisited here).
- **Store data (store page + `appdetails`) is fetched only for scored apps.** The store request rate becomes a user parameter, **default 1 request / 2 s** (one shared connection, same hard-stop rule).
- **Completeness report**, published alongside the datasets:
  - counts: listing rows, scored apps, scored apps of type `game`;
  - per-pass statistics (above);
  - exclusion counts per reason;
  - **depth check**: for each Top-100 Dataset, the `/top` (current-players) ranks of its members, especially the deepest one, showing whether declined games were caught.

Glossary updated: **Candidate Pool** redefined; `no_tags` added to **Exclusion** ([CONTEXT.md](../../../CONTEXT.md)).
