# Data source selection and substitution sign-off
Type: grilling
Status: resolved
Blocked by: 01, 02

## Question

Given the access findings, which source supplies each required field (monthly Avg. Players, tags, app type, store genre, is_free, release date), and does the researcher confirm any Source Substitution? Includes request rates and politeness rules per source.

Surfaced by SteamDB access and tag/metadata alternatives:
- Request SteamDB academic permission, or substitute Steam first-party sources (or both: substitute now, request in parallel)?
- Tag source if substituting: store page HTML (exact displayed list + votes), `IStoreBrowseService/GetItems` (batched, undocumented, weights only), or SteamSpy (diverges from displayed list).
- Is logged-out automated fetching of store pages acceptable given the Steam Subscriber Agreement "Automation" clause; does this need ethics/institutional review?
- Passing the store age check for mature titles (content gate, not anti-bot): allowed?
- Rate limit to adopt for `appdetails`/store pages in the absence of an official figure.

Surfaced by Steam Charts compliant access and coverage:
- Steam Charts publishes no terms/robots/rate limit (absence ≠ permission). Contact the operator before the full run (helps the ethics statement)?
- Proposed politeness: 1 request / 5 s, single connection, descriptive User-Agent, hard stop on 403/429/503/challenge page (~14–17 h for the full listing). Accept or change?

## Answer

Resolved with the researcher on 2026-10-03.

**Field → source**
| Field | Source | Status |
|---|---|---|
| Monthly Avg. Players | Steam Charts `/app/{appid}` | named source |
| Displayed tag list (order, tagid, votes) | Steam store page `InitAppTagModal` | **Source Substitution, confirmed** |
| App type, store genres, `is_free`, release date, name | Steam store `appdetails` (`l=english`) | **Source Substitution, confirmed** |
| Any field, for games with no store data | Manual Metadata Entry (per-field source URL + retrieval date) | each entry = researcher's sign-off for that source |

SteamSpy and `IStoreBrowseService/GetItems` are not used for tags. (SteamSpy as a pool *cross-check* is still open in [Candidate pool definition](08-candidate-pool-definition.md).)

**SteamDB**
- Not a primary source. The researcher will request academic permission (university email + project overview, as the SteamDB FAQ requires). The email also asks whether publishing the Top-100 exports is acceptable.
- A SteamDB collector is specified now, but its only role is to **cross-check store-sourced tags/metadata for games in the Top-100 Datasets**. It never replaces the store as the main source.
- It is disabled by default. A config flag holding the permission reference must be set before it will run.
- It is built and tested only against SteamDB pages a person saved by hand from a browser. It never touches live SteamDB before permission is granted.
- Once granted, its rate follows whatever terms the permission sets. Absent any, it defaults to the store rule (1 request/2 s).

**Steam Charts politeness**
- **The rate is a parameter the user can change.** The default is 3 requests/s, sequential, over a single kept-alive connection (full listing ≈1.2 h). No parallel connections.
- Descriptive User-Agent with contact details.
- **No browser emulation, proxies or challenge solving.** A hard stop on 403, 429, 503 or any challenge page; resume from the checkpoint.
- Timeouts and connection errors: retry with exponential backoff (about 3 tries), then stop. Exact policy goes to [Pipeline architecture and export schema](15-pipeline-architecture.md).
- If the operator asks for a lower rate, it is lowered and the change is recorded.

**Steam store politeness**
- One request every 2 s, a single connection shared by store pages and `appdetails`. Same User-Agent and hard-stop rule as Steam Charts.
- Always English (`l=english`).
- The store's age check is passed the way a logged-out visitor would, using the standard age-check cookie with a birth date **30 years before the collection date** (the researcher's age). Never log in; anything that needs a login is not bypassed.

**Pre-run conditions** (these gate execution, not design)
- The researcher contacts the Steam Charts operator (Twitter @steamcharts or james4k.com) and asks about an acceptable rate. The small test run may go ahead now. **The full Steam Charts run waits for the operator's reply**; stop if they object.
- The researcher checks the Steam Subscriber Agreement "Automation" question with their institution's ethics/research-integrity office before the full run, and the check is recorded. The reasoning in our favour: logged out, public pages, academic use.

**Retention and publication**
- Every raw response (HTML/JSON) is kept locally as a snapshot that is never redistributed.
- Only the derived Top-100 exports and the analysis are published, attributed "Player data: Steam Charts; tags/metadata: Steam store". The full Candidate Pool data is never published.

**Games with player history but no store data** (delisted, region-locked, login-only):
- Excluded with a new reason, `store_data_unavailable`.
- The pipeline reports every game excluded this way that would have scored inside a Top 100.
- The researcher may add any of them back through a **Manual Metadata Entry**:
  - An overrides config file keyed by AppID supplies the missing fields (tags in display order, app type, store genres, `is_free`, release date), each with a source URL and retrieval date.
  - Entries without a source are rejected.
  - An added game then goes through the normal exclusion rules using the supplied tags, can enter any Top-100 Dataset, and is flagged `metadata_source = manual` in the exports and the provenance record.

