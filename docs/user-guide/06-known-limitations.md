# Known limitations

This chapter is the single home of every caveat the study carries. The reports' limitations paragraph links here.

## Data and sources

- **Tags are a current snapshot, not historical.** Store tags are read on the collection date; a game's tags at release may have differed.
- **The Top 100 is a ranked selection, not a sample.** Nothing generalises to Steam as a whole, and no test result is evidence about Steam in general.
- **Steam Charts has coverage gaps.** It pauses tracking of low-player apps, so a gap means the app was not tracked, not that it had zero players. Missing Months stay missing.
- **Tiny pre-launch Steam Charts months are kept as real data.** They can move a Release Month earlier than the store's release date.
- **`release_month_check.csv` is noisy for Early Access games**, whose store date is the 1.0 release.
- **Delisted games.** Games with no store data are excluded as `store_data_unavailable`, and store pages without tags as `no_tags`, unless the researcher adds them back through a sourced Manual Metadata Entry. `exclusions.csv` shows which of them would have ranked.
- **Store data depends on the researcher's country.** Region-locked apps may show no store page. The country the store reported is recorded in `snapshot.json`.
- **The `game`-type pool may be under 10,000 games.** The Candidate Pool size is reported, never padded from other sources; any shortfall below 10,000 is reported in `completeness.csv`.
- **Ties at rank 100** are resolved by Months Observed and then AppID; tied games outside the list are in `ties.csv`.

## Exclusions and tags

- **Community-voted tags include joke votes**, such as Dating Sim on Banana.
- **Content descriptor ids 3 and 4 have no official label documentation.** The adult-content rule uses id 3 together with the Adult Only notice and the Hentai tag.
- **The Dating Sim rank cannot separate dating sims from romance-heavy farming sims.** The researcher handles known cases with Exclusion Overrides.
- **Builds made with `--allow-parse-errors` are never published.** The app shows a banner for them.

## Network and clustering

- **The partition shown comes from a single run** (one seed, one γ). No consensus partition is computed.
- **The Seed-Noise Floor samples K = 10 seeds**, not every possible seed.
- **The Resolution Sweep covers a fixed γ grid**, at the report's settings only, and only in the Build.
- **Removal Sensitivity uses one main-seed run per removed tag.** Its flag is a screening aid, not a significance test, and some flags are expected by chance.
- **The app is not optimised in v1.** At the loosest thresholds a change can take several seconds, mostly for the null model.
