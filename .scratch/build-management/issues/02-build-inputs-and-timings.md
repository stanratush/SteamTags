# What does a Build read from a Snapshot, and how long does it take?
Type: task
Status: resolved
Blocked by:

## Question

Facts for [What is a lightweight Snapshot?](08-lightweight-snapshot.md) and the [Build menu](12-build-menu.md). Done AFK. Scripts go in `prototypes/02-build-inputs/`, findings in `research/02-build-inputs.md`.

- For each Build stage (pool, parse, games, exclusion, datasets, assemble, analysis, network stage, reports), which Snapshot records and which fields it reads, and whether it reads them for every app in the Candidate Pool or only some.
- The size of exactly those fields as plain tables (CSV or gzipped CSV) for the full Snapshot `20261005T062558Z-full`, compared with its 509 MB.
- Wall-clock time of each stage for one `steamstudy build` on the full Snapshot, and whether the network stage (Resolution Sweep, null model, seed noise) dominates.
- Whether any Build output depends on something outside those fields (e.g. `requests.sqlite` metadata, raw HTML layout, file timestamps).

## Answer

Findings: [What a Build reads from a Snapshot, and how long it takes](../research/02-build-inputs.md). Scripts and raw numbers: [prototypes/02-build-inputs/](../prototypes/02-build-inputs/).

- **Reads:** only the pool, parse and games stages read the Snapshot, plus a second read of the listing in assemble. They read the `/top` pages, the Steam Charts page of every Candidate Pool app (13,412), the store page and `appdetails` of **every scored app** (10,973, excluded or not), GetTagList, and eight `snapshot.json` keys. Everything after works in memory. The feature analysis needs tags and genres for the whole Eligible Pool; the network stage needs only the Top-N rows. No current or charted setting reads a field outside this set.
- **Size:** those fields as plain tables come to 23.3 MB of CSV, **6.3 MB gzipped**, or 4.6 MB gzipped when month rows are kept only where scoring and the reports use them. The Snapshot's files total 447 MB (509 MB on disk), and 342 MB of that is store HTML, from which only the tag list and the Adult Only notice are read.
- **Time:** one Build takes **99 s**, and **79% (78 s) is reading and parsing raw pages**. The network stage takes 11.6 s (12%), so it **does not dominate**. Reading the extracted tables takes 2.9 s, so a Build from them would take about 24 s (estimated, not run).
- **Other dependencies:** the `build_id` (a timestamp, in every `state_id`), the installed software versions and the config. From the request log: the **outcome of every key looked up**, which has no body to extract, and for skipped apps the url, detail, status and timestamp. A Snapshot of parsed fields fixes the parser version used to make it. The Build never reads file timestamps, `sha256`, `final_url` or HTML outside its parsers.
