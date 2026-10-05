# SteamDB can be a Snapshot's Tag Source

Until now, every game's tags came from the Steam store page, and SteamDB was only a permission-gated cross-check that never reached a dataset. We now let the researcher choose the Tag Source per Snapshot (`steamstudy collect --tag-source steam|steamdb`). With `steamdb`, the store stage also fetches a SteamDB page for every scored app, and the Build reads tags only from those pages.

The choice is fixed when the Snapshot is created and recorded in `snapshot.json` and `build.json`, because a Build must be a deterministic function of one Snapshot: mixing sources within one Snapshot would make "has a tag" mean two different things. Store details (app type, genres, Adult Only, release date) still come from the Steam store in both modes, so the exclusion rules other than `no_tags` behave the same either way. The SteamDB permission gate applies unchanged: a `steamdb` Snapshot is refused before any request without a recorded permission reference.

## Consequences

- SteamDB lists every tag a game has, not only the store's top 20, so Tag-Specific Datasets and the Tag Network differ between sources; compare Builds only within one Tag Source.
- SteamDB tags have no vote counts (`votes` is 0); positions are page order, which the rank-limited exclusion rules use.
- `parse_steamdb_app` is still built on an assumed page structure (the synthetic fixture), never on a saved SteamDB page. Check it against a real page before a full `steamdb` collection.
