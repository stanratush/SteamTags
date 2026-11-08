# Known limitations

This chapter is the single home of every caveat the study carries. The reports' limitations paragraph links here.

## Data and sources

- **Tags are a current snapshot, not historical.** Store tags are read on the collection date; a game's tags at release may have differed.
- **The Top N is a ranked selection, not a sample.** Nothing generalises to Steam as a whole, and no test result is evidence about Steam in general.
- **Steam Charts has coverage gaps.** It pauses tracking of low-player apps, so a gap means the app was not tracked, not that it had zero players. Missing Months stay missing.
- **Skipped apps.** An app whose Steam Charts page kept failing to load or parse during collection is skipped rather than stopping collection; it has no score and cannot rank. Every skipped app is listed in `skipped_apps.csv`.
- **Tiny pre-launch Steam Charts months are kept as real data.** They can move a Release Month earlier than the store's release date.
- **`release_month_check.csv` is noisy for Early Access games**, whose store date is the 1.0 release.
- **Delisted games.** Games with no store data are excluded as `store_data_unavailable`, and store pages without tags as `no_tags`, unless the researcher adds them back through a sourced Manual Metadata Entry. `exclusions.csv` shows which of them would have ranked.
- **Store data depends on the researcher's country.** Region-locked apps may show no store page. The country the store reported is recorded in `snapshot.json`.
- **The `game`-type pool may be under 10,000 games.** The Candidate Pool size is reported, never padded from other sources; any shortfall below 10,000 is reported in `completeness.csv`.
- **Ties at the last rank** (rank 100 with the default List Size) are resolved by Months Observed and then AppID; tied games outside the list are in `ties.csv`.

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
- **Compare Network States only at the same Tag Depth and List Size.** Whether a game "has" a tag depends on the Build's [Tags per game](03-metric-reference.md#tags-per-game-tag-depth), and the List Size decides which games are in a dataset, so a change in either changes every network number, not just the ones you are looking at.
- **The app is not optimised in v1.** At the loosest thresholds a change can take several seconds, mostly for the null model.

## Parameter Selection

- **Thresholds are count-only thresholds.** An edge needs s shared games; its count carries no significance claim, and no statistically validated edges are used.
- **Neighbour Agreement tends to be higher at large g**, because a one-step change in the thresholds changes a small network's graph less. Choosing the smallest g among near-best pairs only partly counterbalances it.
- **Lift has no likelihood.** γ̂ is defined through a model of unweighted multigraphs; with Lift or shared-game weights the self-consistent resolution is a heuristic, whichever weight is used.
- **Optimal among the partitions found.** CHAMP and the Stable Partitions work on the partitions the scan found with 10 seeds; a partition no seed found cannot be selected.
- **The widest-domain rule and the Selected Resolution as a midpoint are this study's rules**; the sources give none.
- **A dataset can end with `no_qualifying_pair`.** Nothing is relaxed automatically; the mode then shows the exclusion table.
- **Validation is one 80% fraction and one null model.** No curve of fractions, no other noise type, and no Subsample Stability on null replicates.
- **Validation runs on the data the pair was chosen on.** Subsample Stability may be slightly optimistic; Q played no part in the choice, so the Null Comparison is barely affected. The grid and the choice of pair are not repeated per replicate.
- **One pair per dataset, chosen independently.** No pair common to all five datasets is chosen, and the datasets' Clusters are not compared.

## Imported data

These apply to Builds made from an Import ([Imported data](08-imported-data.md)).

- **No weights.** An item either has an attribute or does not; the attribute's position in the list is used only through the Tags per game cut.
- **One kind of attribute.** All attributes form one vocabulary; there is no separate genre or category kind.
- **No `;` in names.** The `;` separates attributes, so an attribute name cannot contain it.
- **Names are case-sensitive.** "Puzzle" and "puzzle" are two attributes; the import only warns about them.
- **None of the Steam data checks.** An Import Build has no Release Month, no Placeholder Rows, no Observation Window and no store metadata, so none of their checks or reports exist for it.
