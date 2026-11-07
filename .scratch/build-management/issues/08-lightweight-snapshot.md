# What is a lightweight Snapshot?
Type: grilling
Status: resolved
Blocked by: 02

## Question

Charted: a lightweight version of a Snapshot can be made so it moves easily between machines. Builds are created only in the repository, never in an App Bundle.

Using [What does a Build read from a Snapshot?](02-build-inputs-and-timings.md), decide:
- what it holds: exactly the fields every Build setting can read, for every app in the Candidate Pool, or less;
- the guarantee: a Build from the lightweight Snapshot is byte-identical to one from the full Snapshot with the same settings, and how that is tested;
- its identity: the same `snapshot_id` or a derived one, what `build.json` records, and whether both kinds can sit side by side;
- what it cannot do (a logged repair, the SteamDB cross-check, Manual Metadata validation against the store);
- how it is made (a CLI command, the Build menu) and its file format;
- the glossary entry, and how it relates to **Snapshot** ("never changed after collection ends").

## Answer

Grilled with the researcher, 2026-11-07. Facts from [What a Build reads from a Snapshot](../research/02-build-inputs.md).

- **Content: parsed tables, not pages.** Lightweight Snapshots hold the eight tables from the research: listing (every row, so the first-seen name and best rank come out the same), Steam Charts outcomes, **all** month rows up to the window's end, store apps, store tags (with display position), store genres, tag vocabulary, and the eight `snapshot.json` keys a Build reads. They also hold the request-log outcome of every key the Build looks up (including "missing"), the log url/detail/status/timestamp of skipped apps, and SteamDB pages' fields and log `batch` when the Snapshot has them. About 6.3 MB against 447 MB. Every current and charted setting reads only what is inside.
- **Two forms, one Snapshot.** The forms are named **raw** and **lightweight**, not "full", because "full Snapshot" already means the opposite of a test Snapshot. Both keep the **same `snapshot_id`**, and their Builds share `builds/<snapshot_id>/`. `build.json` records `snapshot_form: raw | lightweight` and the extract version.
- **Fast source as well as portable.** A Build from a lightweight Snapshot takes about 24 s, against 99 s (estimated). When both forms are present, a Build reads the lightweight one by default; `--from-raw` forces the raw pages.
- **Guarantee:** a Build from the lightweight form is byte-identical to one from the raw form, given the same settings and the same `build_id`, except for the `snapshot_form` field. Tested by (1) an automated test on the test fixture Snapshot: lighten, build both with a fixed `build_id`, compare every file; and (2) a CLI check, `steamstudy snapshot verify-light <id>`, that runs the same comparison on a real Snapshot (one 99 s Build, so not run on every lighten).
- **Extract version.** It is bumped whenever a parser or the extracted field set changes. If the version is old: with the raw form present, the Build reads the raw form and warns that the lightweight one should be made again; without it, the Build is refused, naming the version gap.
- **Made from a closed Snapshot; never changed.** Repair, collect resume and any SteamDB fetch act on the raw form only. The lightweight one records the raw form's repair count. If that count is behind and the raw form is present, the lightweight one is stale and is not used. Manual Metadata validation still works, because it reads parsed Game fields.
- **Made by:** `steamstudy snapshot lighten [<snapshot_id>]` (default: the latest closed Snapshot). It is also made automatically when collect closes a Snapshot and after every repair (about 80 s). The Build menu shows which forms each Snapshot has, with no button to make one.
- **File format:** one file, `snapshots/<snapshot_id>.light.zip`, holding the CSV tables (deflate) plus a `meta.json`: format and extract version, the eight Snapshot keys, the repair count, and each table's sha256, checked on open. It is written deterministically (fixed member order and timestamps). Copying that one file is the whole move. Like `/snapshots/`, it is Steam data and never committed.
- **Glossary:** **Snapshot** now says it comes in two forms; new entry **Lightweight Snapshot** ([CONTEXT.md](../../../CONTEXT.md)).
