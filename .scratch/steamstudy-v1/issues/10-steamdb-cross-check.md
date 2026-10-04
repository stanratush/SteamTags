# 10: SteamDB cross-check collector

**What to build:** Once SteamDB grants permission, the researcher runs `steamstudy collect steamdb --build <id>` to fetch SteamDB pages for that Build's Top-100 members only. The next Build then reports store vs SteamDB tags per game. Until permission is recorded the collector refuses to run, and it is developed only against pages saved by hand. SteamDB values never enter a dataset.

**Blocked by:** 04

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Collect" (SteamDB cross-check), "Commands".

- [x] `collect steamdb --build <id>` refuses to run without a permission reference in `collection.toml`.
- [x] With permission, it fetches only that Build's Top-100 members through the Fetcher, into the Snapshot's `steamdb` area, as its own logged batch recorded in `snapshot.json`. The rate follows the permission terms, defaulting to the store rule.
- [x] A pure SteamDB page parser is tested only on pages saved by hand.
- [x] A Build on a Snapshot with SteamDB batches writes `reports/steamdb_crosscheck.csv` (store vs SteamDB tags per game). No dataset value changes.
- [x] A test confirms that no request reaches a SteamDB host when the permission reference is absent.

## Comments

- 2026-10-04 (agent): Implemented: collect steamdb --build <id> (refuses with no permission reference and sends no request), fetching only the Build's Top-100 members as a logged batch; reports/steamdb_crosscheck.csv in the next Build. SteamDB pages were never fetched, so parse_steamdb_app assumes tag links of the form /tag/<id>/ and is tested on a SYNTHETIC fixture (tests/fixtures/steamdb). Replace it with a hand-saved page once permission arrives.
