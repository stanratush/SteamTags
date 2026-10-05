# Test fixtures

`raw/` holds real responses captured on 2026-10-04 for parser and Collect tests, laid out like a Snapshot's `raw/` folder. `raw/capture.json` records each request's URL, HTTP status and final URL. The capture made 31 sequential GETs, 4 s apart, with a descriptive User-Agent and the store's logged-out age-check cookie.

These are raw responses: they stay in this local repository and are never published.

Steam Charts returned HTTP 500 for Black Hole Simulator (1401150), Bold Blade (749110) and Dadish 3D (2888870), including on a retry. Bold Blade's real page has since been copied from the researcher's test Snapshot (2026-10-05); Black Hole Simulator still answers 500. `raw/steamcharts/app/1401150-500.html.gz` is that error page. The tests build the two remaining cases from the real Scorn page, with its monthly table replaced (see `tests/helpers.py`). Replace them with real pages from the first test Snapshot.
