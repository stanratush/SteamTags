# 02: Polite Fetcher and Candidate Pool collection

**What to build:** `steamstudy collect pool` reads the full Steam Charts `/top` listing into a new Snapshot. It makes N passes (default 2), unions them by AppID, and keeps every raw page. The run is polite and logged, stops hard on any anti-bot signal, and resumes by rerunning the same command. Every network request in the project goes through the `Fetcher` built here.

**Blocked by:** 01

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Collect" (Fetcher interface, Politeness, Retry and stop policy, Snapshot layout).

- [x] `Fetcher.fetch(request_key, url) -> StoredResponse` has a live HTTP adapter and a fixture-backed fake adapter.
- [x] The rate is set per source from config (Steam Charts default 3 req/s; store default 1 req/2 s), with one kept-alive connection per source, sequential requests, and a descriptive User-Agent with contact details.
- [x] 403, 429, 503 and challenge pages (Cloudflare markers, or the expected structural marker missing) save and log the response, then exit non-zero with no retry.
- [x] 5 parse-structure failures in a row cause a hard stop.
- [x] Timeouts (connect 10 s / read 30 s), connection resets and other 5xx responses are retried after 10, 30 and 90 s, then cause a hard stop. All these numbers come from `collection.toml`.
- [x] Each response is archived as one gzipped file under the Snapshot's raw layout. Each request is logged in `requests.sqlite` with URL, status, final URL, timestamp, sha256 and outcome.
- [x] Rerunning the command skips requests that have a final outcome and refetches retryable or hard-stopped ones.
- [x] `collect pool` runs N passes (config, default 2, minimum 1). Each pass ends at the first 404 or empty page, and that is not a hard stop.
- [x] `parse_top_page` is a pure parser. The pool is the union of the passes by AppID.
- [x] `snapshot.json` records the id, mode, collection date, Observation Window, per-pass start/end times, row counts, the count of AppIDs seen in only one pass, the rates actually used, the User-Agent, `collection_config_hash` and software versions.
- [x] Tests through the fake adapter cover rate spacing (injectable clock), every row of the retry/stop table that applies to the listing, resume, and the pass union.

## Comments

- 2026-10-04 (agent): Implemented: Fetcher with LiveTransport/FakeTransport, Snapshot store (raw archive, requests.sqlite, snapshot.json), pool stage with N passes and union stats; real /top and app pages captured as fixtures (tests/fixtures/raw). The contact in collection.toml's User-Agent is a placeholder and Collect refuses until it is filled in. Finding: Steam Charts answered HTTP 500 persistently for 1401150, 749110 and 2888870; under the retry table that is a hard stop, so one such app blocks a run (decision needed).
