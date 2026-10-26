# Validation design
Type: grilling
Status: resolved
Blocked by: 02, 03

## Question

For each dataset's selected Threshold Pair, exactly how are the null-model comparison and Subsample Stability run and reported?

- The null: at least 100 curveball replicates (trades per replicate as [Validation methods](02-validation-methods.md) recommends). Is the "consistent clustering procedure" the full γ scan + CHAMP + stable-partition selection at the same (g, s), or clustering at the Selected Resolution? Which statistics are compared (Q at γ, number of Multi-Tag Clusters, whether a qualifying Stable Partition exists, edge count)? The null-to-observed edge-count ratio is a diagnostic only.
- Subsampling: the number of 80% subsamples (e.g. 100), the threshold scaling rule (round, floor or ceil of 0.8·g and 0.8·s, with a minimum), and whether γ is re-selected per subsample or held at the Selected Resolution.
- Reported: ARI against the Selected Partition on shared tags, Hennig cluster-wise Jaccard per Multi-Tag Cluster, retained-tag coverage.
- What counts as a "failure" that is reported transparently (thresholds or wording), without ever changing the selected parameters.
- Seeds for replicates and subsamples (new seed streams), and the run cost.
- From [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md): users can change the Pair Constraints, which can change the chosen pair. Does validation run for the pair chosen under the default constraints, or for the currently chosen pair with a "re-run validation" action? There is no validation when the status is `no_qualifying_pair`.

## Answer

Decided by grilling with the researcher, 2026-10-26. Evidence: [Validation methods](02-validation-methods.md), and a pilot of 5 nulls and 5 subsamples per dataset's chosen pair ([pilot.py](../prototypes/07-validation-pilot/pilot.py), [output](../prototypes/07-validation-pilot/output.txt)).

**Pilot facts** (Build `20261008T221504Z-7a23ae9f`, the five chosen pairs of ticket 06)
- One full-procedure replicate takes 0.4–0.8 s. 100 nulls + 100 subsamples × 5 datasets ≈ 600 s serial, about 60–75 s on 12 workers: roughly the grid's own 95 s.
- 21 of 25 nulls also have a Selected Partition with ≥ 3 Multi-Tag Clusters, so existence alone barely separates observed from null (Peixoto). Their domains are narrower: the observed width beat every null in every dataset (rpg 0.67 vs 0.18–0.30).
- Q at the observed Selected Resolution (the null's own envelope) is far below the observed Q everywhere (simulation 0.14–0.16 vs 0.30). Q at each null's *own* resolution is not comparable: rpg null 3 reached 0.129 vs 0.131.
- Subsamples: re-selected ARI 0.38–1.00, often 0.5–0.7, with the Selected Resolution drifting (rpg 1.75 → 1.24–1.59). At the observed resolution ARI is clearly higher where only γ moved (simulation 0.85 / 0.92 vs 0.57 / 0.50), and it exists even when re-selection fails (strategy subsample 3, `too_few_multi_tag_clusters`).

**Terms** (now in [CONTEXT.md](../../../CONTEXT.md)): **Null Comparison** added; **Subsample Stability** now names its two arms.

**Null Comparison**
- **Construction:** curveball, exactly as the Workbench's `null_model`: shuffle the games (after the Minimum Months Filter) × the pair's network tags (visible, ≥ g games), `TRADES_PER_GAME = 10` × the number of games. Tag frequencies are kept, so g keeps the same tags; s applies unchanged; Lift is recomputed from the shuffled table.
- **R = 100** replicates.
- **Full-procedure arm:** each replicate runs the whole per-pair procedure at the same (g, s): the 56-γ scan with the same 10 scan seeds, CHAMP, γ̂, the Selected Partition rule.
- **Fixed-γ arm:** Q at the exact, unrounded observed Selected Resolution, read from the replicate's own CHAMP envelope (no extra Leiden runs). The observed side is the Selected Partition's Q there, its envelope value, so both sides are the best of 560 runs.
- **Reported:**
  - "k of R" replicates with a Selected Partition, with reason counts for the rest;
  - for those with one: domain width, Selected Resolution and Multi-Tag Cluster count, each as null median and range beside the observed value, and the observed value's rank ("wider than k of R′");
  - fixed-γ Q: observed against the null median and range, and "k of R replicates reach the observed Q" (≥);
  - edge count: observed against the null median as a ratio, labelled a diagnostic.
- No z-scores (KLN: unreliable) and no p-values.

**Subsample Stability**
- **S = 100** subsamples of **m = ⌊0.8·n⌋ games without replacement**, n = games after the Minimum Months Filter. A single fraction; no curve of fractions and no noise scheme in this effort.
- Thresholds in integer arithmetic: **g′ = ⌊g·m/n⌋**, **s′ = max(2, ⌊s·m/n⌋)** (n = 100: 4g // 5). Hidden tags stay hidden. Tags may enter a subsample that the full network lacks; the comparison rule handles them.
- **Two arms:**
  - **Re-selected** (headline): the full procedure at (g′, s′).
  - **At the Selected Resolution**: the subsample's CHAMP envelope partition at the observed γ. Free, and separates "the data changed the Clusters" from "the procedure picked another γ".
- **Comparison set:** tags present in both networks with an edge in at least one (the Neighbour Agreement rule).
  - **ARI** against the Selected Partition on that set.
  - **Hennig's Jaccard** per Multi-Tag Cluster C, with C and every subsample Cluster restricted to that set; the best match may be any subsample Cluster, One-Tag Clusters included. The Selected Partition's One-Tag Clusters are never scored.
  - **Retention share** per Cluster: |C ∩ set| / |C|.
  - A Cluster with no tag in the set is **absent**: left out of its mean (Hennig's B*), with the absent count shown. Missing is never 0.
  - **Degenerate** subsamples (no edges; or no Selected Partition, re-selected arm only) are counted as "k of S" with reasons and left out of the summaries, never scored 0.
- **Reported, per arm, over non-degenerate subsamples:**
  - ARI median, 10th–90th percentile and minimum; "k of S degenerate";
  - per Multi-Tag Cluster: mean Jaccard over B*, "Jaccard ≤ 0.5 in k of B*", mean retention share, absent count;
  - tag coverage: mean share of the Selected Partition's edged tags in the set;
  - re-selected arm only: median and range of the subsample Selected Resolution and Multi-Tag Cluster count.

**Verdict words, the only ones**
- **"Dissolved"** on a Multi-Tag Cluster whose mean Jaccard is ≤ 0.5 in an arm (Hennig's principled bound), per arm.
- **"Q not above the null"** when ≥ 1 replicate reaches the observed Q at the Selected Resolution; otherwise "above all R null replicates".
- Nothing else: no ARI threshold, no overall pass/fail, no flag on widths or counts. fpc's 0.6 / 0.75 / 0.85 bands are not shown in the app; the methods text says they refer to bootstrap and are not applied.
- Validation never changes the chosen pair or its selection explanation.

**Seeds**
- `derive_seeds` streams: **3 = scan seeds** (fixing the grid run's assumption), **4 = null shuffles**, **5 = subsample draws**.
- Replicate r's seed drives its curveball or its game draw through `random.Random(seed)`.
- Every replicate and subsample clusters with the same 10 scan seeds as the observed scan.
- The lists are the same for every dataset and pair.

**Which pair, and when**
- Validation results are cached **per (dataset, pair)**, independent of the Pair Constraints and the tolerance.
- The main background job validates each dataset's pair **chosen under the default constraints**, as a second phase after the grid (the whole run ≈ 3 minutes on 12 workers).
- When custom constraints choose another pair, it shows "Not validated" and a **"Validate this pair"** button that starts a background job. The same button is on any inspected pair with a Selected Partition, also under `no_qualifying_pair` (where nothing is validated automatically).
- Results are always labelled with the pair they ran on.
- R and S live in `[parameter_selection]` in `config/network.toml` and are in the validation cache key. They are not editable in the mode for now (map fog "Changing the fixed settings").

**Wording:** a separate **"Validation of g = …, s = …"** block below the selection explanation, one template for every dataset, each section closing with an always-shown caveat. Illustrative (overall pilot numbers):

> **Null Comparison** (100 shuffled networks, same g and s). Q at resolution 1.151 is 0.067; no shuffled network reaches it (−0.021 to −0.012). 79 of 100 also have a Selected Partition, with narrower domains (median 0.03 against 0.158; wider than all 79).
> *This shows only that the network is not random, not that its Clusters are real.*
>
> **Subsample Stability** (100 random 80% subsets of the games, g′ = 13, s′ = 2). Re-selected: median ARI 0.69 (0.57–0.86) over 99 of 100 subsamples; 1 had no Selected Partition. At resolution 1.151: median ARI 0.86 (0.60–0.90). 1 of 4 Multi-Tag Clusters is dissolved when re-selected (mean Jaccard ≤ 0.5): *Cluster name*.
> *This measures how much the clustering depends on which games are in the dataset. It does not show that the Clusters are real either.*

The block says so when it shows a pair other than the one currently chosen ("Not validated" plus the button).

**Handed on**
- To [Modules, caching and parallelism](08-modules-caching-parallelism.md): validation as a second job phase with per-replicate progress; a per-(dataset, pair) validation cache keyed by fixed settings, R, S, trades, seed and method version, outside the Pair Constraints; the "Validate this pair" job; seed streams 3 / 4 / 5; the fixed-γ arms read from each replicate's envelope (the scan must keep every Admissible Partition's Â, P̂ and membership); cancelling the validation phase.
- To [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md): the validation block and its two arms, the per-Cluster table with "Dissolved", "Not validated" and the "Validate this pair" button.
- To [Exports and documentation](11-exports-and-documentation.md): per-replicate and per-subsample tables for both arms, per-Cluster Jaccard rows, and R, S, m, g′, s′ and the seed streams in the settings JSON; methods text on the B* rule, floor scaling and why fpc's bands aren't applied; the two caveats.
