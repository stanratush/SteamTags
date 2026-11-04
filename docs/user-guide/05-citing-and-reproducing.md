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

*Why it matters here.* Clusters and their numbers belong to one Network State, so the figures and tables of a paper should travel with the Network State that produced them. The zip opens in the app on another computer that has the same Build, and the recomputed `state_id` confirms that the numbers are the same.

Do not deposit raw Snapshot files: raw responses and the full Candidate Pool are never published, and `monthly_players.csv` waits for the Steam Charts operator's agreement.

## Cite the software and the sources

Cite the `steamstudy` version and the clustering library versions listed under `software_versions` in `export.json` or `build.json`, and the Build id. Credit the sources with the attribution line "Player data: Steam Charts; tags/metadata: Steam store".

## Reopen a state

**Open Network State…** in the app accepts the zip itself or its `export.json`. The app finds the Build by its **identity**, not by the folder path recorded in the export: among the Builds it can see (the `builds/` folder it was started from, in a clone of the repository or in an App Bundle), it looks for the export's `build_id` and checks that the Build's `build.json` is byte-for-byte the one copied into the export. So a state exported on one computer opens on another that has the same Build anywhere. If no such Build is there, it refuses and names the Build (and its Snapshot) it needs; copy that Build folder into `builds/` and open again. It also refuses, with the reason, when a Build with the same id has a different `build.json`, or when the software's `key_version` differs (the methods changed, so the same settings could give different numbers). An export made under an older `schema_version` opens as long as its key can be read.

After opening, the app restores every setting, recomputes the state and shows ✓ when the recomputed `state_id` equals the recorded one (✗ otherwise). If the export was made after Tidy (or after the older Re-layout), the figure's positions are restored too: kept in shape, scaled into the reference canvas, with any tag far from the graph brought back next to it and room for every label. Removal Sensitivity results from the zip are shown marked "loaded from export"; they are not rerun.

## Report a Parameter Selection

> **In short.** Export tables writes one record-only zip per settings key; deposit it, and quote the chosen pair and its settings label with every selection result.
>
> **Here:** lets readers check how each dataset's Threshold Pair was chosen.
>
> **Caution:** a record only: the zip does not open back into the app.

Press **Export tables** in the Parameter Selection mode and deposit the zip with the paper. It holds the eight tables, `parameter_selection.json` (every key, seed and constraint, with the file hashes) and `selection_report.md`. Quote the chosen pair together with the settings and constraints labels ("Default settings", or "Custom settings: …").

To reproduce it, run the same Build under the same Selection Settings: the tables come out byte-identical, so compare their SHA-256 values with those in `parameter_selection.json`. Results computed on another computer can carry a different Python version or operating system; [Run](02-app-controls.md#run) explains why that practically never changes them.

*Why it matters here.* The choice of thresholds shapes every Cluster reported for a dataset, so the evidence for that choice should travel with the paper.

The methods paragraph of `selection_report.md`, with the run's values in place of the placeholders:

> For each Top-100 Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, ‹g_range› games per tag and ‹s_range› shared games with s ≤ g (‹n_pairs› pairs), with ‹weight› as the Clustering Weight, a Minimum Months Filter of ‹min_months› and ‹hidden› hidden. On each distinct graph we ran Leiden (RBConfiguration, at most 1,000 passes) with ‹scan_seeds› seeds at every γ from 0 to Gibson and Mucha's γ_max(K), K being the number of tags with an edge, in steps of ‹gamma_step› (Gibson & Mucha 2022, SI §J); the derivation in SI §J.2 uses only the Cauchy–Schwarz inequality and assortativity, so the bound also holds for Clusters of unequal size and for weighted graphs. The unique partitions found were reduced to the upper envelope of their lines Q(γ) = Â − γP̂, giving the Admissible Partitions and their Optimality Domains (CHAMP; Weir et al. 2017, §2, eqs. 1–4). For each we evaluated once the self-consistent resolution γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) (Newman 2016, §III.A, eqs. 15–18) and called the partition stable when γ̂ lies in its own domain (Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3). Among the Stable Partitions with at least ‹min_multi› Multi-Tag Clusters, the Selected Partition has the widest domain in plain γ units, and the Selected Resolution is the domain's midpoint; the sources give no rule for choosing among Stable Partitions, and we did not rescale the width to log γ or to Gibson and Mucha's γ-scaled area (SI §A.7), whose usefulness the authors leave open. Neighbour Agreement is the mean adjusted Rand index between a pair's Selected Partition and those of its grid neighbours (g ± 1, s ± 1) with a different graph, on the shared tags with an edge in either graph. The chosen pair is the one with the smallest g, then the smallest s, among the pairs whose Neighbour Agreement is within ‹tolerance› of the highest, among pairs with ‹constraints›. We compared each validated Threshold Pair with ‹replicates› networks whose game–tag table was shuffled by curveball trades (every tag and game keeps its count; Strona et al. 2014), each analysed by the identical procedure: the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the Selected Partition rule), not the Parameter Grid or the choice of pair (Karrer, Levina & Newman 2008, abstract, §III and §VI). Q at the observed Selected Resolution was taken as the best of each network's scan envelope and ‹scan_seeds› Leiden runs at exactly that γ, on the observed network and every replicate alike; we report how many of the D shuffled networks with a defined Q reach the observed Q, and give no p-value, because the resolution and the pair were chosen on the observed data. We also compared the pair with ‹subsamples› random subsets of m = ⌊0.8·n⌋ of the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)), once re-selecting by the same per-pair procedure and once reading the partition at the observed resolution. For each Multi-Tag Cluster we report Hennig's (2007, §2) mean best-match Jaccard on its tags present in both networks, over the B* subsamples in which at least two of them survive, with its Monte Carlo standard error and the frequencies of values ≤ 0.5 and > 0.75 with 95% Wilson intervals (Wilson 1927), and a Whole-Cluster Jaccard that counts lost tags as not recovered. We call a Cluster dissolved in most subsamples when its Jaccard is 0.5 or less in more than half of the B* subsamples (the per-subsample cut is Hennig's, the majority our rule); the 0.6, 0.75 and 0.85 bands of the fpc package refer to the bootstrap and are not applied. The pair was chosen on the same data, so Subsample Stability may be slightly optimistic.
