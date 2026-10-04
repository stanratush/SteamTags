# 02: Polite Fetcher and Candidate Pool collection

**What to build:** `steamstudy collect pool` reads the full Steam Charts `/top` listing into a new Snapshot. It makes N passes (default 2), unions them by AppID, and keeps every raw page. The run is polite and logged, stops hard on any anti-bot signal, and resumes by rerunning the same command. Every network request in the project goes through the `Fetcher` built here.

**Blocked by:** 01

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Collect" (Fetcher interface, Politeness, Retry and stop policy, Snapshot layout).

- [ ] `Fetcher.fetch(request_key, url) -> StoredResponse` has a live HTTP adapter and a fixture-backed fake adapter.
- [ ] The rate is set per source from config (Steam Charts default 3 req/s; store default 1 req/2 s), with one kept-alive connection per source, sequential requests, and a descriptive User-Agent with contact details.
- [ ] 403, 429, 503 and challenge pages (Cloudflare markers, or the expected structural marker missing) save and log the response, then exit non-zero with no retry.
- [ ] 5 parse-structure failures in a row cause a hard stop.
- [ ] Timeouts (connect 10 s / read 30 s), connection resets and other 5xx responses are retried after 10, 30 and 90 s, then cause a hard stop. All these numbers come from `collection.toml`.
- [ ] Each response is archived as one gzipped file under the Snapshot's raw layout. Each request is logged in `requests.sqlite` with URL, status, final URL, timestamp, sha256 and outcome.
- [ ] Rerunning the command skips requests that have a final outcome and refetches retryable or hard-stopped ones.
- [ ] `collect pool` runs N passes (config, default 2, minimum 1). Each pass ends at the first 404 or empty page, and that is not a hard stop.
- [ ] `parse_top_page` is a pure parser. The pool is the union of the passes by AppID.
- [ ] `snapshot.json` records the id, mode, collection date, Observation Window, per-pass start/end times, row counts, the count of AppIDs seen in only one pass, the rates actually used, the User-Agent, `collection_config_hash` and software versions.
- [ ] Tests through the fake adapter cover rate spacing (injectable clock), every row of the retry/stop table that applies to the listing, resume, and the pass union.
