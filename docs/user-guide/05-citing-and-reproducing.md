# Citing and reproducing a Network State

Every network number depends on the full Network State. To let readers check a figure, cite the state, not just the dataset.

## Quote the state_id

Give the 12-character `state_id` next to every network number, figure or table you report, for example "C1 (state 1cf7ac82c8f4)". It is in the export file name, in section 1 of Analysis Report mode, in `export.json` and, for the report's states, in `analysis.json` and the `state_id` column of the Build's network files. The `state_id` is a fingerprint of the Build, the dataset and every setting; two states with the same `state_id` give the same numbers.

## Deposit the export zip

> **In short.** Export this state downloads one zip with every table, the full Network State key and its provenance.
>
> **Here:** lets readers of a study of the most-played games reopen and check the exact clusters it reports.
>
> **Caution:** Removal Sensitivity results are included only if they were computed for exactly this Network State.

Press **Export this state** and deposit the zip with the paper or its supplementary material. It is self-contained: every table, the full state key, file hashes, the method constants and a copy of the Build's provenance (`build.json`, including the config and its changelog). Removal Sensitivity results are included only if they were computed for exactly this state.

*Why it matters here.* Clusters and their numbers belong to one Network State, so the figures and tables of a paper should travel with the state that produced them. The zip opens in the app on another computer that has the same Build, and the recomputed `state_id` confirms that the numbers are the same.

Do not deposit raw Snapshot files: raw responses and the full Candidate Pool are never published, and `monthly_players.csv` waits for the Steam Charts operator's agreement.

## Cite the software and the sources

Cite the `steamstudy` version and the clustering library versions listed under `software_versions` in `export.json` or `build.json`, and the Build id. Credit the sources with the attribution line "Player data: Steam Charts; tags/metadata: Steam store".

## Reopen a state

**Open Network State…** in the app accepts the zip itself or its `export.json`. The app finds the Build by its **identity**, not by the folder path recorded in the export: among the Builds it can see (the `builds/` folder it was started from, in a clone of the repository or in an App Bundle), it looks for the export's `build_id` and checks that the Build's `build.json` is byte-for-byte the one copied into the export. So a state exported on one computer opens on another that has the same Build anywhere. If no such Build is there, it refuses and names the Build (and its Snapshot) it needs; copy that Build folder into `builds/` and open again. It also refuses, with the reason, when a Build with the same id has a different `build.json`, or when the software's `key_version` differs (the methods changed, so the same settings could give different numbers). An export made under an older `schema_version` opens as long as its key can be read.

After opening, the app restores every setting, recomputes the state and shows ✓ when the recomputed `state_id` equals the recorded one (✗ otherwise). If the export was made after Tidy (or after the older Re-layout), the figure's positions are restored too: kept in shape, scaled into the reference canvas, with any tag far from the graph brought back next to it and room for every label. Removal Sensitivity results from the zip are shown marked "loaded from export"; they are not rerun.
