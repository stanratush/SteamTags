# The dataset seam is in memory, not a shared file

Steam Builds and imported datasets meet the analysis through one in-memory `Dataset`, returned by one reader, `read_dataset(build, key)`. A source marker in `build.json` picks the adapter; no marker means Steam. Each Build kind keeps its own file on disk: Steam Builds go on writing `top100_<key>.csv` with its strict 17-column header, and import Builds write their own. We did this because any shared file would either change Steam Build bytes or settle the export schema early, while the network and the app already read only six columns through one function (`games_from_rows`), so a read-time adapter costs little.

## Considered Options

- **Import Builds write the Steam file**, with the item id in `appid`, the filter field in `months_observed` and 11 empty Steam columns. Rejected: the published schema would describe Steam facts that aren't there, extra numeric fields have nowhere to go, and an import without a filter field would have to invent values.
- **One new generic file for every Build**, with old Steam Builds adapted. Rejected for now: new Steam Builds would carry a duplicate of `top100_<key>.csv`, and it fixes file naming before Build identity and the export schema are decided.

## Consequences

- Old Builds are adapted at read time, never migrated. Rewriting `build.json` would break the saved exports matched by its hash, and a stricter or renamed `top100` header would make old Builds unreadable.
- The state key keeps `min_months` as the filter threshold's field name for every Build kind, so no Steam `state_id` moves.
- Decided in `.scratch/build-management/issues/04-generic-dataset-contract.md`. Steam assumptions: `.scratch/build-management/research/01-steam-assumptions.md`.
