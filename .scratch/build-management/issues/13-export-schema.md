# What do the Top-N rename and Import Builds change in the export schema?
Type: grilling
Status: open
Blocked by: 04, 07, 09

## Question

Steam Builds keep writing `top100_<key>.csv` with its strict 17-column header ([generic dataset contract](04-generic-dataset-contract.md), ADR 0005). An Import Build has its own inputs, the Import's normalised tables ([How does a dataset get imported?](09-dataset-import.md)), and `build.json` gains `name`, `description` and `parent_build_id` ([Build identity](07-build-identity-and-lifecycle.md)).

Decide:
- the Import Build's dataset file: its name and columns (id, name, rank, score, filter field, extra numeric fields, attributes), and whether `top100_` gives way to a Top-N name for imports only or for new Steam Builds too;
- what the published export schema (`export/schema.py`) documents for each Build kind, and whether the schema version is bumped;
- the `dataset` column and `build_id` references in Network State exports: what changes when the Build is an Import Build, and that saved Steam exports still open (matched by the hash of `build.json`);
- which reports an Import Build writes (generic sections only), and their file names.
