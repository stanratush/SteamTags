# What does a Build read from a Snapshot, and how long does it take?
Type: task
Status: open
Blocked by:

## Question

Facts for [What is a lightweight Snapshot?](08-lightweight-snapshot.md) and the [Build menu](12-build-menu.md). Done AFK. Scripts go in `prototypes/02-build-inputs/`, findings in `research/02-build-inputs.md`.

- For each Build stage (pool, parse, games, exclusion, datasets, assemble, analysis, network stage, reports), which Snapshot records and which fields it reads, and whether it reads them for every app in the Candidate Pool or only some.
- The size of exactly those fields as plain tables (CSV or gzipped CSV) for the full Snapshot `20261005T062558Z-full`, compared with its 509 MB.
- Wall-clock time of each stage for one `steamstudy build` on the full Snapshot, and whether the network stage (Resolution Sweep, null model, seed noise) dominates.
- Whether any Build output depends on something outside those fields (e.g. `requests.sqlite` metadata, raw HTML layout, file timestamps).
