# What is a lightweight Snapshot?
Type: grilling
Status: open
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
