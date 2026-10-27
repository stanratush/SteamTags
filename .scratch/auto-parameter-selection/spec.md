# Spec: Automatic Parameter Selection

Settled through the [Automatic Parameter Selection map](map.md) (wayfinder, 2026-10-25 to 2026-10-27). Each decision below is the current state of its ticket, with every later amendment already applied. When this spec and a ticket's original Answer disagree, the spec wins. The tickets' Comments record the amendments. Glossary: [CONTEXT.md](../../CONTEXT.md). Constraint: [ADR 0001](../../docs/adr/) (the app runs from an App Bundle). Implementation happens on branch `auto-parameter-selection`.

## Goal

The Tag Network app gains a third mode, **Parameter Selection**, next to the Workbench and Analysis Report mode. For each **Top-100 Dataset** it:

1. searches the **Parameter Grid** (g 3–20, s 2–12, s ≤ g: 153 **Threshold Pairs**);
2. picks a **Selected Partition** for each pair with CHAMP and Gibson & Mucha's **Stable Partitions**;
3. picks one pair by **Neighbour Agreement** among the **Qualifying Pairs**;
4. validates that pair against curveball nulls (**Null Comparison**) and 80% subsamples (**Subsample Stability**);
5. shows all of it, exports it as a record, and can apply any pair's Selected Partition to the Workbench.

The procedure lives in Dash-free `steamstudy.network` modules, so a later effort can call it from the Build. Results ship inside App Bundles.

**What it never claims.** Automatic Parameter Selection is a choice of settings to look at, never a claim that the Clusters are real. It never claims significance for count-only edges, and never uses Q, Coverage or Silhouette to choose between pairs. Three kinds of stability are kept apart and never combined: algorithmic (Seed-Noise Floor), parameter (Neighbour Agreement) and data (Subsample Stability). The Null Comparison is a fourth, separate diagnostic.

## Facts this spec rests on

Measured on Build `20261008T221504Z-7a23ae9f` with the procedure exactly as specified below ([Graph-specific γ scan](issues/16-graph-specific-gamma-scan.md), [results](prototypes/16-remeasure/results.md)), unless a line says otherwise.

- **Chosen pairs** (default Selection Settings and Pair Constraints):

  | Dataset | Chosen | NA | Near-best set | Multi-Tag Clusters | Tags | Retention | Selected / Workbench γ |
  |---|---|---:|---:|---:|---:|---:|---|
  | overall | g=17, s=2 | 0.974 | 7 | 4 | 29 | 0.533 | 1.151 / 1.15 |
  | puzzle | g=14, s=2 | 0.980 | 1 | 4 | 31 | 0.517 | 1.092 / 1.09 |
  | rpg | g=7, s=5 | 0.774 | 9 | 15 | 71 | 0.785 | 2.006 / 2.01 |
  | simulation | g=14, s=5 | 0.981 | 9 | 3 | 38 | 0.610 | 0.865 / 0.86 |
  | strategy | g=14, s=2 | 1.000 | 3 | 3 | 39 | 0.579 | 1.009 / 1.01 |

- 764 of 765 pairs have a Selected Partition. The exception is rpg g=18 s=4, `too_few_multi_tag_clusters`. No `clipped_high`, `not_representable` or γ̂ above the scan end occurs across 27,549 Admissible Partitions.
- The Workbench γ and seed reproduce 758 of 764 Selected Partitions. Six pairs are `not_reproduced`, each found by one scan run only. rpg g=3 s=3 reproduces only at γ = 3.23.
- 699 distinct graphs among 765 pairs: deduplicating by graph saves 66 scans. Puzzle, rpg and simulation have 22 identical-graph g-links each.
- The scan length is 77–356 γ values per graph (median 120), and the scan end runs from 3.80 to 17.75. The grid makes 1,032,800 Leiden runs.
- **Time, grid only, 12 workers:** 329 s (3,943 s of worker time). simulation g=5 s=5 alone takes 136 s (56 runs reach the 1,000-pass cap), so heaviest-first dispatch matters. Validation has not been re-measured since the scan got longer. The pilot's 0.4–0.8 s per replicate is now roughly 2–3.5× that. **The "~3 min / ~23 min" figures in earlier tickets predate the graph-specific scan and must not be quoted.** [Shipping in an App Bundle](#shipping-in-an-app-bundle) measures the full Run.
- `metrics.modularity` equals CHAMP's (Â − γP̂)/2m to ≤ 7e-16. `modularitypruning` 2.0.1 agrees with the numpy formulas to ≤ 1e-12 and runs on Python 3.14 / Windows with `single_threaded=True`.
- Dash's `DiskcacheManager` runs a background job as a non-daemonic `multiprocess.Process`, so the job can start its own `multiprocess.Pool`. Cancel kills the job's children recursively through `psutil`.
- `uv.lock` pins one version of every app library for all Pythons and OSes, so installs differ only in the Python version (3.12–3.14) and the OS/CPU.
- Prototype code that implements most of the procedure, as reference only (never imported):
  - [grid_run.py](prototypes/05-grid-run/grid_run.py) and [remeasure.py](prototypes/16-remeasure/remeasure.py): scan, dedup, CHAMP, γ̂, metrics, Neighbour Agreement;
  - [scan_ends.py](prototypes/16-citable-upper-bound/scan_ends.py): `gamma_max_K` and the capped pass loop;
  - [apply_search.py](prototypes/09-apply-reproduction/apply_search.py): the Workbench γ and seed search;
  - [pilot.py](prototypes/07-validation-pilot/pilot.py): validation;
  - [the mode prototype](prototypes/10-parameter-selection-mode/README.md): layout variant A.

## Decisions

### Scope

- **In:** the network modules, the app mode, Apply to Workbench, exports, shipping in App Bundles, the User Guide, in-app help and the Running Guide.
- **Out:** see [Out of scope](#out-of-scope). Most importantly, adopting the selection in the Build or the feature-analysis report, and changing the `config/network.toml` defaults.
- **No new runtime dependency** (ADR 0001). CHAMP, γ̂ and γ_max(K) are our own numpy/scipy code. `modularitypruning` is a **dev-only** dependency, used as a test oracle.
- **Leiden only** in v1.

### The per-pair procedure

#### Networks

- Each pair's network is the ordinary Tag Network (`build_network`) for the dataset under the Selection Settings at that (g, s). Its weight is the Clustering Weight (default Lift).
- Within a dataset, (g+1, s) is (g, s) restricted to tags with ≥ g+1 games, and (g, s+1) has the same tags as (g, s) with some edges removed.
- **n_e** is the number of tags with at least one edge.
- **Graph hash:** a hash of the sorted node list and the sorted (u, v, shared count, weight) edge list. Pairs with equal hashes share every per-pair result except their (g, s).

#### The γ scan and Leiden

- **Scan values:** `round(0.05·i, 2)` for i = 0 … ⌈γ_max(n_e)/0.05 − 1e-9⌉. The step (0.05) is config-only. The γ = 0 runs return the trivial partition, so nothing else is added to CHAMP's input.
- **γ_max(K)** is Gibson & Mucha 2022 SI §J: the maximum of γ̂(ω_in, ω_out) = (ω_in − ω_out)/(ln ω_in − ln ω_out) on the line ω_in + (K − 1)·ω_out = K with ω_out ∈ (0, 1), found by exact one-dimensional bounded maximisation (`scipy.optimize.minimize_scalar`, `xatol` 1e-12).
  - It is undefined for K < 2. A graph with no edges has no scan and gets `no_edges`.
  - It depends only on n_e, so the same rule serves Lift and Shared games and every null and subsample (each from its own graph).
  - A unit test checks it against GM22 Table S5 for K = 2…10 (1.0000 … 2.1931; γ_max(3) = 1.0926).
- **Scan seeds:** 10, the same at every γ (stream 3, see [Seeds](#seeds)). The scan order is γ ascending, then seeds in stream order.
- **Leiden pass loop:** `detect` (Leiden) and `leiden_scan` both build one `RBConfigurationVertexPartition` and one `Optimiser` with the seed. They loop `optimise_partition(p, n_iterations=1)` and stop at the first pass that gains ≤ 0 or after **1,000 passes**.
  - Below the cap this is identical to leidenalg's `n_iterations=-1`. A unit test asserts equality on a graph where `-1` stops.
  - The cap exists because the strict `> 0` test never ends on float-noise gains.
  - Runs that hit the cap are counted per graph as `pass_capped_runs`.
- **One igraph construction:** a private `cluster._leiden_graph(graph)` builds the igraph and weights in `detect`'s current node order (sorted) and edge order (sorted). `detect` keeps its interface and uses it, so the Workbench at (γ, seed) gives exactly the scan's partition there. A test asserts `detect` and `leiden_scan` agree.
- **Dedup:** partitions are equal when they are the same set partition of **all** tags, isolated tags included. They are canonicalised by renumbering labels in order of first occurrence. Each unique partition records its **first (γ, seed)** in scan order and its **hit count** out of the scan's runs (scan length × 10).

#### CHAMP

- Each partition is a line Q(γ) = Â − γP̂, with **Â = 2·(internal weight)** and **P̂ = Σ_c κ_c²/2m**. There is no 1/2m factor and the graph has no self-loops. `leidenalg` quality equals Â − γP̂, and `metrics.modularity` equals (Â − γP̂)/2m.
- The upper envelope runs over **[0, γ_end]**, where γ_end is the last scan γ. Each partition on the envelope over an interval of positive width is an **Admissible Partition**, and that interval is its **Optimality Domain** [a, b].
- **Tolerance:** one relative tolerance, rtol = 1e-12 scaled to the size of Q, for breakpoint ties and zero-width domains.
  - At a breakpoint tie the smallest P̂ wins.
  - Partitions on top at only one point are dropped.
- **Twins:** distinct partitions with identical (Â, P̂) keep the one whose canonical membership sorts first. The number dropped is counted.
- A domain cut off at γ_end keeps its clipped width and midpoint, is flagged **`clipped_high`**, and stays eligible. There is no `clipped_low`: the trivial partition owns [0, first split].

#### γ̂ and Stable Partitions

- For each Admissible Partition: ω_in = Â/P̂, ω_out = (2m − Â)/(2m − P̂), and **γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out)**. This is evaluated **once** per partition, as Gibson & Mucha's fixed-point test. Newman's iteration is never run.
- **No estimate**, so never stable, in these cases. The guards use counts, not floats:

  | Case | Reason code |
  |---|---|
  | No edges | `no_edges` |
  | Fewer than two groups with strength | `one_group` |
  | ω_out = 0 (no cross-group weight) | `no_cross_weight` |
  | Â ≤ P̂ | `not_assortative` |

  The last case differs from `modularitypruning`, which computes a γ̂ there. Oracle tests compare stable sets only on graphs where these cases don't occur.
- A partition is **stable** when a ≤ γ̂ ≤ b (a closed interval).
- An assertion, covered by a unit test, guards **γ̂ ≤ γ_max(n_e) ≤ γ_end** for every assortative partition.
- **Map target** (for the CHAMP plot): the Admissible Partition whose domain contains γ̂, or `none`.

#### Selected Partition, Selected Resolution, Workbench γ and seed

- **Minimum Multi-Tag Clusters** (a Selection Setting, default 3, range 1–10) counts only Clusters with ≥ 2 tags. It is applied **after** stability, as a filter on the Stable Partitions, never on CHAMP's input.
- Among the remaining Stable Partitions the **widest domain wins**, in plain γ units (b − a). Widths equal within tolerance go to the lower midpoint, then to canonical membership order. Log-width and GM22's γ-scaled area were rejected, and the methods text says so.
- There is no low-γ guard. The minimum Multi-Tag Clusters is the user's lever, and Neighbour Agreement marks the odd low-γ pick (puzzle g=4 s=4: NA 0.003).
- **No Selected Partition:** the first matching reason, in the order `no_edges`, `no_stable_partition`, `too_few_multi_tag_clusters`.
- **Selected Resolution:** the exact midpoint (a + b)/2, stored unrounded.
- **Workbench γ and Workbench seed:** a deterministic search inside the grid task, cached with the graph's result.
  - Candidates are the two-decimal values ≥ 0.01 inside [a, b], nearest the Selected Resolution first, ties to the lower value.
  - At each candidate, try the main seed, then the 10 scan seeds in stream order.
  - The first (γ, seed) at which Leiden reproduces the Selected Partition exactly is kept.
- **Flags:** `not_representable` when no two-decimal value ≥ 0.01 lies in the domain; `not_reproduced` when one does but nothing reproduces. There is no minimum domain width.

#### Per-pair metrics

A metric that needs a partition is unavailable when the pair has no Selected Partition. Its status is then `no_selected_partition` plus the pair's reason. Graph-level figures are always available.

- **Seed-Noise Floor:** Leiden at the **exact, unrounded** Selected Resolution with the existing `noise_seeds(main_seed, noise_seeds, null_replicates)`. The ARI is taken over **all nodes** with `stability.ari`, exactly as the Workbench does. Reported: the minimum ARI against the Selected Partition (the floor), the mean, and how many noise runs reproduce it exactly. It is defined for `not_representable` pairs too.
- **Information Retention:** Σ|games of t| over tags with ≥ 1 edge, divided by Σ|games of t| over the **visible** tags (every tag of the dataset except hidden and removed ones, tags below g included). Games are counted after the Minimum Months Filter. The status is `no_visible_tags` when the denominator is 0. Also reported, descriptive only: the share of games with ≥ 1 tag that has an edge.
- **Fragmentation:**
  - isolated tags, as a count and as a share of all nodes;
  - connected components with ≥ 2 tags;
  - the largest connected component's tags, and its share of the **non-isolated** tags (**LCC share**);
  - from the Selected Partition, Multi-Tag Clusters, and One-Tag Clusters split into isolated and connected.
- **Graph counts:** tags, edges, n_e, the share of edges with Lift < 1, γ_max(n_e), γ_end, the scan length, `pass_capped_runs`, the number of unique partitions and the number of twins dropped.
- **Descriptive** (Selected Partition at the exact Selected Resolution): Q (`metrics.modularity`; a test checks it against CHAMP's (Â − γP̂)/2m), weighted Coverage (`metrics.coverage`) and the Jaccard silhouette (`metrics.silhouette`, with its statuses; isolated tags count as "other clusters" for b(i)). The distance matrix is computed once per g.
- **Per Admissible Partition:** canonical membership, Â, P̂, [a, b], `clipped_high`, ω_in, ω_out, γ̂ or its reason, the map target, the stable flag, Multi-Tag and One-Tag Cluster counts, the first (γ, seed) and the hit count. Non-admissible partitions are counted, not kept.

### Neighbour Agreement and Edge Overlap

- **Neighbours** of (g, s): (g−1, s), (g+1, s), (g, s−1), (g, s+1), limited to the grid.
- **One link record per unordered neighbour pair** (ARI is symmetric). It holds:
  - a `status`: `ok`, `outside_grid`, `neighbour_has_no_selected_partition` or `too_few_compared_tags` (fewer than 2 compared tags);
  - the shared tags and their Jaccard overlap;
  - the compared tags: shared tags with ≥ 1 edge in at least one of the two graphs. A tag isolated in both is dropped; a tag isolated in one and clustered in the other is a real disagreement;
  - `identical_graph` (equal graph hashes);
  - the ARI between the two Selected Partitions on the compared tags;
  - **Edge Overlap**: the Jaccard overlap of the two edge sets, unweighted, each tag pair counted once, over all edges. Edges of tags dropped by a g-step count as differences. It is for reporting only and never enters selection.
- **Neighbour Agreement (NA)** is the mean ARI over the links with status `ok` **and a different graph**. Identical-graph links are flagged and counted but left out of the mean: a step that removes nothing perturbs nothing.
  - A neighbour without a Selected Partition is **missing, never 0**.
  - The pair reports neighbours in the grid, comparable ones, comparable ones with a different graph, comparable ones with an identical graph, and missing ones. The minimum ARI over the counted links is reported as a descriptive value.
  - With no comparable different-graph link, NA is unavailable: `no_comparable_neighbours`.
- NA uses each neighbour's Selected Partition whether or not that neighbour qualifies. It never depends on the Pair Constraints, so it is computed once per complete grid and cached.
- No size-adjusted or baseline-relative second NA number is reported.

### Choosing the pair

- **Qualifying Pair:** a pair with a Selected Partition and an NA that meets every **Pair Constraint** (all bounds inclusive):

  | Pair Constraint | Default | Allowed |
  |---|---|---|
  | Minimum Information Retention | 0.50 | 0–1 |
  | Maximum share of isolated tags | 0.10 | 0–1 |
  | Minimum LCC share (of non-isolated tags) | 0.90 | 0–1 |
  | Minimum comparable neighbours with a different graph | 2 | integer 0–4 |
  | Maximum Multi-Tag Clusters | off | off, or an integer ≥ the minimum Multi-Tag Clusters |

- The **Seed-Noise Floor and the hit count are not constraints.** They are reported next to the chosen pair.
- **Choice:**
  1. The **near-best set** is every Qualifying Pair with NA ≥ max NA − tolerance, in absolute ARI, inclusive, with a 1e-12 float tolerance. The tolerance defaults to **0.05** and may be set from 0 to 1.
  2. From the near-best set, the pair with the smallest g is chosen, then the one with the smallest s.
- **Reasons**, recording every failing one, not only the first, as a list of codes: `no_selected_partition`, `no_neighbour_agreement`, `too_few_comparable_neighbours`, `retention_below_min`, `isolated_share_above_max`, `lcc_share_below_min`, `too_many_clusters`.
- **No qualifying pair:** the status is `no_qualifying_pair`, with no chosen pair, no automatic validation and no relaxation. An exclusion table gives, per constraint, the pairs it excludes alone and cumulatively, in the table's order.
- `choose(grid, constraints)` is a cheap pure post-step over cached results. It is never cached. Each result records the constraint values and tolerance it used.

#### The selection explanation ("Why this pair")

One template for every dataset, built only from NA, the constraints and counts. It never cites Q, Coverage or Silhouette. Bracketed sentences appear only when their condition holds. The numbers are illustrative.

> **Selected: g = 14, s = 2**, resolution 1.092 (Workbench 1.09).
> Default constraints · Default settings.
> 153 of 153 pairs have a Selected Partition. 85 qualify under the default constraints: Information Retention ≥ 0.50, isolated tags ≤ 10%, largest component ≥ 90% of the tags with an edge, and ≥ 2 neighbours with a different graph. The LCC constraint excluded no pair.
> The highest Neighbour Agreement among them is 0.98 (g = 14, s = 2). 1 pair is within 0.05 of it, and of these the one with the smallest g, then the smallest s, is selected.
> Its Neighbour Agreement is 0.98 over 3 neighbours with a different graph. [1 more neighbour has an identical graph and is not counted.]
> [Its Selected Partition has the minimum 3 Multi-Tag Clusters; a coarser split was not allowed.]
> [The Seed-Noise Floor at this resolution is 0.42: the clustering also depends noticeably on the seed.]
> *Neighbour Agreement measures how little the clustering changes when g or s moves by one. It does not show that the Clusters are real.*
> *Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, particularly s, generally produces a smaller change in the graph. This can increase agreement independently of the robustness of the Clusters. Choosing the smallest g among near-best pairs partially counterbalances this tendency.*

- Every constraint that excluded no pair is named that way.
- The minimum-Clusters sentence appears when the chosen Selected Partition has exactly the run's configured minimum.
- The Seed-Noise Floor sentence appears when the floor is below 0.5.
- A `not_representable` pick replaces "(Workbench …)" with "(cannot be entered as a two-decimal value)". A `not_reproduced` pick adds "Workbench 1.23 with the main seed shows a different partition."
- With custom values, the label line lists them: "Custom constraints: tolerance 0.10 (default 0.05)" and "Custom settings: Minimum Months 12 (default 0), 2 removed tags (Puzzle, Casual)".
- Both caveat paragraphs are always shown.
- **No qualifying pair:** "**No pair qualifies** under the default constraints. 152 of 153 pairs have a Selected Partition. Excluded by each constraint, alone (cumulative): … Loosen a constraint, or inspect any pair in the grid and apply it by hand."
- **Descriptive group caption**, on Q, Coverage and Silhouette everywhere they appear (Inspector, heatmap): "Descriptive: not comparable across pairs", with the help text *"Describes this pair's Selected Partition on its own network. Pairs differ in tags and edges, so a higher value at one pair does not make it a better choice."* Their heatmaps have a grey scale and no "best" marker.

### Validation

Validation runs for one (dataset, pair) at a time. It never changes the chosen pair or its explanation.

#### Null Comparison

- **Construction:** curveball, exactly as the Workbench's `null_model`. It shuffles the games (after the Minimum Months Filter) × the pair's network tags (visible, ≥ g games) with `TRADES_PER_GAME = 10` × the number of games. Tag frequencies are kept, s applies unchanged, and the weight is recomputed from the shuffled table. Removed tags are absent.
- **R = 100** replicates.
- **Full-procedure arm:** each replicate runs the whole per-pair procedure at the same (g, s): its own scan range from its own n_e, the same 10 scan seeds, CHAMP, γ̂ and the Selected Partition rule.
- **Fixed-γ arm:** Q at the exact observed Selected Resolution, read from the replicate's own CHAMP envelope, with no extra Leiden runs. The observed side is the Selected Partition's envelope value there.
- **Reported:**
  - "k of R" replicates with a Selected Partition, with reason counts for the rest;
  - for those with one: domain width, Selected Resolution and Multi-Tag Clusters, each as null median and range beside the observed value, plus the observed width's rank ("wider than k of R′");
  - the fixed-γ Q: observed against the null median and range, and "k of R replicates reach the observed Q" (≥);
  - the edge count as observed ÷ null median, labelled a diagnostic;
  - the total scan length and capped runs across replicates.
- No z-scores and no p-values.

#### Subsample Stability

- **S = 100** subsamples of **m = ⌊0.8·n⌋ games**, drawn without replacement. n is the number of games after the Minimum Months Filter.
- Thresholds in integer arithmetic: **g′ = ⌊g·m/n⌋**, **s′ = max(2, ⌊s·m/n⌋)**. Hidden and removed tags stay out. A subsample may contain tags the full network lacks.
- **Two arms:**
  - **Re-selected** (the headline): the full procedure at (g′, s′), with the subsample's own scan range.
  - **At the Selected Resolution:** the subsample's CHAMP envelope partition at the observed γ.
- **Comparison set:** tags present in both networks with an edge in at least one (the NA rule).
  - **ARI** against the Selected Partition on that set.
  - **Hennig's Jaccard** per Multi-Tag Cluster C: C and every subsample Cluster restricted to the set, best match over all subsample Clusters (One-Tag ones included). The Selected Partition's One-Tag Clusters are never scored.
  - **Retention share** per Cluster: |C ∩ set| / |C|.
  - A Cluster with no tag in the set is **absent**. It is left out of its mean, and the absent count is shown. Missing is never 0.
  - **Degenerate** subsamples (no edges; or, in the re-selected arm only, no Selected Partition) are counted as "k of S" with reasons and left out of the summaries.
- **Reported per arm**, over non-degenerate subsamples:
  - the ARI median, 10th–90th percentile and minimum, and "k of S degenerate";
  - per Multi-Tag Cluster: the mean Jaccard, "Jaccard ≤ 0.5 in k of B*", the mean retention share and the absent count;
  - the mean share of the Selected Partition's edged tags present in the set;
  - re-selected arm only: the median and range of the subsample's Selected Resolution and Multi-Tag Clusters.

#### Verdicts: the only two

- **"Dissolved"** on a Multi-Tag Cluster whose mean Jaccard is ≤ 0.5 in an arm, shown per arm.
- **"Q not above the null"** when ≥ 1 replicate reaches the observed Q at the Selected Resolution. Otherwise the text says "above all R null replicates".
- There is no ARI threshold, no overall pass/fail, and no fpc 0.6 / 0.75 / 0.85 bands.

#### Validation block wording

A block titled **"Validation of g = …, s = …"** sits below the explanation. The numbers are illustrative.

> **Null Comparison** (100 shuffled networks, same g and s). Q at resolution 1.151 is 0.067; no shuffled network reaches it (−0.021 to −0.012). 79 of 100 also have a Selected Partition, with narrower domains (median 0.03 against 0.158; wider than all 79).
> *This shows only that the network is not random, not that its Clusters are real.*
>
> **Subsample Stability** (100 random 80% subsets of the games, g′ = 13, s′ = 2). Re-selected: median ARI 0.69 (0.57–0.86) over 99 of 100 subsamples; 1 had no Selected Partition. At resolution 1.151: median ARI 0.86 (0.60–0.90). 1 of 4 Multi-Tag Clusters is dissolved when re-selected (mean Jaccard ≤ 0.5): *Cluster name*.
> *This measures how much the clustering depends on which games are in the dataset. It does not show that the Clusters are real either.*

- When some replicates reach Q: "Q at resolution … is …; k of 100 shuffled networks reach it: Q not above the null."
- When the shown pair is not the currently chosen one: "Not validated" plus **Validate this pair**.
- When custom constraints chose the pair: "Validation ran for g = …, s = …, the pair chosen under the default constraints."

#### Which pair, and when

- Validation is cached per (dataset, pair), independent of the Pair Constraints and tolerance.
- Run validates each dataset's pair **chosen under the default constraints**, after all grids.
- **Validate this pair** is offered on any inspected pair that has a Selected Partition in a complete grid, including under `no_qualifying_pair` (where nothing is validated automatically).

### Selection Settings, configuration and keys

#### Selection Settings (CONTEXT.md)

These are the choices that fix every pair's Selected Partition, so changing one needs a new run. **Editable in the mode**, as one set for all five datasets with no per-dataset override:

- hidden tags: the Genre Tag checklist and "hide each dataset's defining tag";
- removed tags: the mode's own list;
- Minimum Months: 0–60;
- Clustering Weight: Lift (default) or Shared games;
- the minimum Multi-Tag Clusters: 1–10, default 3.

**Read-only in the mode, config only:**

- the algorithm, Leiden, with the one-line reason "Leiden only: the scan and Apply's reproduction search are built on it";
- the Parameter Grid;
- the γ step;
- the 10 scan seeds;
- R and S.

The γ range is not a setting: it is derived per graph.

#### `[parameter_selection]` in `config/network.toml`

The table is read by the app and the bundle maker. Hidden tags, the main seed, `null_replicates` and `noise_seeds` come from the existing top-level network defaults.

```toml
[parameter_selection]
clustering_weight = "lift"
min_months = 0
min_multi_tag_clusters = 3
g_range = [3, 20]
s_range = [2, 12]
gamma_step = 0.05
scan_seeds = 10
null_replicates = 100        # R
subsamples = 100             # S
workers = 0                  # 0 = os.cpu_count() - 1
# Pair Constraints and tolerance: never in a cache key
tolerance = 0.05
min_retention = 0.50
max_isolated_share = 0.10
min_lcc_share = 0.90
min_comparable_neighbours = 2
max_multi_tag_clusters = 0   # 0 = off
```

`TRADES_PER_GAME` (10) and the subsample fraction (0.8) are code constants.

#### `SelectionSettings` and keys

`SelectionSettings` is a frozen dataclass. It holds:

- the Build id;
- the hidden-tag choice (the hidden Genre Tag ids and the defining-tag toggle);
- the removed tag ids;
- Minimum Months, the Clustering Weight and the algorithm;
- the main seed, `null_replicates` and `noise_seeds`;
- the g and s ranges, the γ step, the scan seed count and the minimum Multi-Tag Clusters;
- R and S.

`for_dataset(dataset, context)` resolves it into the per-dataset base `Settings`, with the hidden tag ids including that dataset's defining tag when the toggle is on.

| Key | Contents | Used for |
|---|---|---|
| `settings_key()` | everything except R and S, without a dataset, plus `selection.METHOD_VERSION` | the export zip's name and `parameter_selection.json` |
| `grid_key(dataset)` | `settings_key()` plus the dataset and its resolved hidden tag ids | one grid cache directory |
| `validation_key(dataset, g, s)` | `grid_key(dataset)` plus g, s, R, S, `TRADES_PER_GAME`, the fraction and `validation.METHOD_VERSION` | one validation file |

- A grid change therefore also invalidates validation.
- The γ scan contributes only its **step** to the key. The end rule (`gm22_gamma_max_n_e`) is fixed by `selection.METHOD_VERSION`.
- Pair Constraints, tolerance, worker count and software versions **never enter a key**.
- `METHOD_VERSION` is `"parameter-selection-1"` in `selection` and `"ps-validation-1"` in `validation`.
- **Labels:** "Default settings" when every editable Selection Setting equals the configured default, otherwise "Custom settings: …" listing each changed value next to its default. Separately, "Default constraints" or "Custom constraints: …", the same way.

#### Seeds

- Streams off the main seed through `derive_seeds`:
  - 1 = null replicates and 2 = noise seeds (existing, unchanged);
  - **3 = scan seeds** (10);
  - **4 = null shuffles** (R);
  - **5 = subsample draws** (S).
- Exclusion is cumulative: each stream excludes every lower stream's seeds. One helper, `selection_seeds(main, settings) -> (scan, null, subsample)`, computes all three.
- Replicate r's seed drives its curveball or its game draw through `random.Random(seed)`. Every replicate clusters with the same 10 scan seeds as the observed scan. The lists are the same for every dataset and pair.

### Modules

None of the network modules imports Dash, the app, the loader or a cache.

- **`steamstudy.network.cluster`:** gains `_leiden_graph`, the capped pass loop shared by `detect` and `leiden_scan(graph, gammas, seeds) -> runs`, and `PASS_CAP = 1000`.
- **`steamstudy.network.champ`:** pure numpy/scipy, no Leiden. It holds:
  - `gamma_max_K(K)` and `scan_gammas(n_e, step)`;
  - `partition_coefficients(...)`, giving Â and P̂;
  - `admissible(...)`, the envelope with domains, `clipped_high` and twins;
  - `estimate(...)`, giving γ̂ or a reason, the stable flag and the map target;
  - `select(...)`, giving the Selected Partition or a reason.

  It takes a scan's unique memberships and the graph's edge arrays. The `modularitypruning` cross-check tests this module.
- **`steamstudy.network.selection`:**
  - `SelectionSettings` and its keys, `load_selection_settings(config)` and `selection_seeds`;
  - `pair_networks(games, settings, context)`, giving every pair's network and graph hash;
  - `run_graph(task) -> GraphResult`: network, scan, `champ`, the Workbench γ and seed search, the Seed-Noise Floor, Retention, Fragmentation, descriptive metrics and graph counts;
  - `run_grid(games, settings, context, *, map_fn, on_result, should_stop, skip)`, the driver;
  - `neighbour_links(grid)` with Edge Overlap, and `neighbour_agreement(grid)`;
  - `choose(grid, constraints) -> Choice`, with the Qualifying Pairs, reasons, near-best set, pick and exclusion table;
  - `Constraints`, with defaults from config, and the two labels.
- **`steamstudy.network.validation`:**
  - `null_replicate(task)` and `subsample_replicate(task)`, each returning one small record with both arms where they apply;
  - `summarise(observed, records) -> ValidationSummary`, with the verdicts;
  - `validation_tasks(...)`.

  It reuses `curveball` and `run_graph`'s procedure.
- **`steamstudy.network.selection_text`:** every fixed sentence. That is the selection explanation, the no-qualifying message, the validation block, the descriptive caption, the caveats, the dataset-strip sentence, the loading-panel template and **the methods paragraph template**. The app, `selection_report.md` and the guide test all read it.
- **App side**, following Removal Sensitivity:
  - **`app/ps_cache.py`:** the cache layout below (read, write, list, `clear`);
  - **`app/ps_run.py`:** the Dash-free Run and Validate drivers, taking `map_fn`, `on_progress`, `should_stop` and a cache root, with weighted progress, ETA and `computed_with`;
  - **`app/app_cache.py`:** `clear_all(root) -> {kind: count}`, calling `rs_cache.clear` and `ps_cache.clear`. The "Clear app cache" button and `steamstudy app --clear-cache` both use it, and the message reports both counts. `rs_cache.py`'s "only persistent cache" docstring is corrected;
  - **`app/ps_view.py`:** the mode's components;
  - **`callbacks.py`:** the jobs and the mode's callbacks;
  - **`layout.py`:** the third mode.

### Parallelism and determinism

- **Grid work is one task per distinct graph.** The parent builds every pair's network (about 0.6 s per dataset), hashes it and makes one task per hash. Each task carries the dataset's games, the `TagContext`, the pair's `Settings`, the seed lists and the expected hash: self-contained, picklable, a few KB. The worker rebuilds the network (about 4 ms) and checks the hash.
- **Validation work is one task per replicate** (R + S per pair). Each carries its seed, the pair's games and settings, the observed Selected Resolution and the observed Selected Partition.
- **The pool is injected.** Drivers take an unordered `map_fn`. The app job and the bundle maker create one `multiprocess.Pool` with `[parameter_selection] workers` and pass `imap_unordered`. Tests pass the serial `map`. There is no worker initializer.
- **Heaviest first.** Tasks are dispatched in descending weight:
  - a grid task weighs edges × scan length;
  - a validation replicate weighs its pair's edges × observed scan length.
- **Determinism.** Every task is a pure function of its inputs. The parent sorts grid results by graph hash, then (g, s), and replicates by index, before NA, `choose` or `summarise`. The same Build, settings and code give **byte-identical cached JSON**, timings and `computed_with` aside, for any worker count or arrival order. The test runs one dataset at g 15–17, s 2–4 serially and with a pool of 2, and compares the two.

### Cache

Under `<build>/app_cache/parameter_selection/`:

```
grids/<grid_key_hash>/
  manifest.json              grid_key, (g,s) -> graph hash, total, computed_with; NA and links once complete
  graphs/<graph_hash>.json   one per finished distinct graph, written atomically (tmp + replace)
validation/<validation_key_hash>.json   one per (dataset, pair), written only when complete, with computed_with
```

- A graph file holds everything [Per-pair metrics](#per-pair-metrics) lists for that graph: the nodes, the edged tags, the edge list for Edge Overlap, every Admissible Partition, the Selected Partition's index or reason, the Workbench γ and seed with their flags, the metrics and the graph counts.
- **`computed_with`:** `software_versions()`, `platform.system()`, `platform.machine()` and a UTC timestamp. It is recorded, never keyed.
- Only the job's parent process writes. Two tabs running the same job write identical bytes.
- There is no automatic eviction. An old method version's directories stay unreachable until "Clear app cache", which deletes everything here, shipped results included.

### Jobs, progress and ETA

- **Two job kinds**, each a Dash background callback wrapping `ps_run` with its pool and `set_progress`. They exclude each other within the mode but may run beside a Removal Sensitivity job.
  - **Run:** one dataset, or "All datasets" one after another through one pool. Phase 1 is the grid, then NA and `choose` under the default constraints. Phase 2 validates the chosen pair. "All datasets" runs every grid before any validation. Cached work is skipped.
  - **Validate this pair:** only on a complete grid. It reads the pair's Selected Partition and Selected Resolution from the graph file.
- **Progress record**, one per finished task: `{dataset, dataset_index, n_datasets, phase: "grid" | "validation", done, total, weight_done, weight_total, elapsed}`. Grid units are pairs (a graph ticks all its pairs; the total is 153). Validation units are replicates, out of R + S.
- **ETA** = elapsed × (weight_total − weight_done) ÷ weight_done, over the whole job (all datasets, both phases). The panel shows "estimating…" until 5% of the weight or 10 s has passed, then "about N min left" ("less than a minute" under one), plus the elapsed time.
- **Cancel:**
  - Finished graph files survive. The Run section offers **Continue (k of 153 pairs)**, which skips graphs on disk.
  - NA, `choose` and the pick exist only for a complete grid.
  - Validation is all-or-nothing per pair: Cancel discards it, so no summary ever covers fewer than R + S replicates.

### The Parameter Selection mode

The layout is variant A, "Three panes", shaped like the Workbench ([prototype](prototypes/10-parameter-selection-mode/README.md)). The mode is the third option of the existing mode control: "Workbench | Analysis Report mode | Parameter Selection". Its URL and panel state follow the Workbench's conventions. At medium and narrow widths it uses the Workbench's existing forms: the Controls column collapses to the pill bar and the Pair Inspector floats.

#### Controls column (left), top to bottom

1. **Run.**
   - "Run all datasets", "Run ‹dataset›", and Cancel while a job runs.
   - One row per dataset with its phase and a progress bar: "grid 87 of 153 pairs", "validation 40 of 200 replicates", "grid done, not validated" or "not run".
   - The cache line: "Results from the app cache: Build …, settings key …, method v1".
   - The **provenance line** whenever `computed_with` differs from the running environment, for example "Computed when this bundle was made: Python 3.14.0, Windows AMD64, 2026-10-26". It is quiet, not a warning. An app-library mismatch (any of `APP_LIBRARIES`) gets the Workbench's banner style instead, ending "Clear app cache and Run to recompute here".
   - "Continue (k of 153 pairs)" after a cancel.
   - **Export tables**, disabled only when no dataset's grid is complete.
2. **Pair Constraints**, always open.
   - One field per constraint plus the tolerance, each with its default beside it and a "changed" marker. An empty maximum Multi-Tag Clusters means off.
   - "Apply to: All five datasets | ‹dataset› only" chooses between the shared set and a per-dataset override.
   - **Confirm** is disabled until something changes, with "Unconfirmed changes" shown meanwhile. **Reset to defaults** sits beside it.
   - Below sits the constraints label. Confirm recomputes `choose` from the cache, with no job.
3. **Selection settings.** A staged section: the editable settings, then the read-only ones with their values.
   - **Use these settings** switches the mode to that settings key. **Reset to defaults** restores the configured defaults. "Copy from Workbench" copies the Workbench's hidden tags, Minimum Months, Clustering Weight and removed tags into the staged edits, never g, s, γ or seed.
   - Removed tags are filled by a tag picker, by "Copy from Workbench", or by the Pair Inspector's **Remove** action on a Cluster member. There is no live link to the Workbench. A tag a dataset lacks is ignored.
   - After a switch the mode shows what the cache holds for that key, or "not run". An edit never starts a job. Run computes only what is missing.
   - The active Selection Settings last for the session. The app always opens on the defaults.
   - If the constraints' maximum Multi-Tag Clusters is on and below a new minimum, it is raised to match and shows as custom.
   - The settings label appears below the section.

#### Main column, top to bottom

1. **Dataset strip.** Five buttons, each showing "★ 14·2 NA 0.98", "no qualifying pair", "not run" or "grid k of 153". A "custom" marker shows when either label is custom, and its tooltip says which. Clicking a button switches the dataset and resets the heatmap and Inspector to that dataset's ★ pair. The metric picker keeps its choice.
   - This strip is the **only** comparison between datasets. There is no same-pair row and no agreement score between datasets.
   - Its help (`selection.dataset_strip`) carries the pinned sentence: *"Each dataset is selected on its own, from its own games and tags. Different pairs in different datasets are expected and are not a disagreement: the same pair builds networks of different sizes in different datasets."*
2. **Metric picker**, a segmented control: Neighbour Agreement, Information Retention, isolated share, Multi-Tag Clusters, Seed-Noise Floor, Q. Q carries the descriptive caption and a grey scale.
3. **Heatmap**, g × s, one metric at a time, with its key.
   - Marks: ★ on the chosen pair, an orange outline on each near-best pair, a dark outline on the inspected pair.
   - On each non-qualifying cell, one letter per failing reason: **P** no Selected Partition, **A** no Neighbour Agreement, **N** too few comparable neighbours, **R** retention, **I** isolated share, **L** LCC share, **K** too many Clusters. The key spells them out.
   - Hovering shows the value, NA, tags, Multi-Tag Clusters, and "✓ qualifies" or each failing reason in words. Clicking a cell inspects it.
4. **"Why this pair"**, the explanation. Under `no_qualifying_pair` it shows the no-qualifying message and the exclusion table.
5. **Validation card:** the chosen pair's validation block with its per-Cluster table (arm, mean Jaccard, "Jaccard ≤ 0.5 in k of B*", retention share, absent, Dissolved) and both caveats. Otherwise it shows "Not validated" with Validate this pair, or the custom-constraints note.

#### Pair Inspector (right), top to bottom

It shows the current dataset's ★ pair until the user clicks a cell.

1. The pair's title and status badges (qualifies or the reasons; `clipped_high`, `not_representable`, `not_reproduced`).
2. **Apply to Workbench**, the primary button. The line beneath it reads either "Workbench γ 1.09, scan seed 2: reproduces the Selected Partition ✓" or, in warning colours, "Workbench γ 1.23, main seed: not_reproduced, shows a different partition (ARI 0.83)". Without a Selected Partition the button is disabled and shows its reason code.
3. **Metrics.** NA with its neighbour counts, Retention, isolated share, LCC share, Multi-Tag and One-Tag Clusters, the Seed-Noise Floor (minimum, mean, exact reproductions), the hit count, the domain, the Selected Resolution and the scan range (0 to γ_end, n_e). Then the descriptive group with its caption.
4. **Neighbour links table:** one row per link, with direction (g− / g+ / s− / s+), status, ARI, tag overlap, Edge Overlap (two decimals) and an "identical graph" marker.
5. **CHAMP plot:** each Admissible Partition's Q(γ) line, the envelope, the domains, each γ̂ with an arrow to its map target, the Stable Partitions marked, and the Selected Resolution. The x-axis runs from 0 to γ_end. It is for inspection only: other partitions cannot be applied.
6. **Clusters** of the Selected Partition, with members and a **Remove** action per tag (it stages the tag in Selection settings).
7. **Compact validation:** the two verdict tags and the median ARIs, or "Not validated" with Validate this pair.

#### States

- **Unfinished grid** (running or cancelled):
  - computed cells fill in as they arrive and pending cells are grey;
  - a cell's NA appears only once its grid neighbours are computed;
  - no ★, near-best outline or explanation is shown. The card says "No selection yet. k of 153 pairs are computed; the selection needs the whole grid."
- **Nothing run:** "No results for these settings yet", pointing to Run.
- **Loading panel** for every in-app job. While nothing is computed for the shown dataset it fills the main column. Once cells arrive it shrinks to a card at the top, replacing the "No selection yet" card. It is not modal: Cancel stays, and the user can switch datasets, inspect cells or leave the mode. Its template:
  - what is being computed: "Searching 153 Threshold Pairs × 77–356 resolutions × 10 seeds for each dataset, then checking the chosen pair against 100 shuffled networks and 100 subsamples", with the actual scan-length range when known;
  - why now: "No results for these settings on this computer yet", "The app cache was cleared" or "Custom settings";
  - where it is: dataset k of 5, the phase and units;
  - that it is a one-off: results are cached, Cancel keeps finished pairs and Continue resumes, and cancelled validation restarts from the beginning;
  - the ETA and the elapsed time;
  - a link to the User Guide's "How Automatic Parameter Selection works".

### Apply to Workbench

- **What Apply sets:** it **replaces** every Network State setting the Workbench controls, as "Open Network State…" (`do_open`) does, with nothing merged:
  - the dataset, g, s and Minimum Months;
  - the hidden Genre Tags and defining tag, and the removed tags;
  - the Clustering Weight, the algorithm (Leiden), γ and seed.

  `null_replicates` and `noise_seeds` already match. Tidy and the Removal Sensitivity view are cleared, and the app switches to the Workbench. There is no confirmation dialog.
- **γ and seed:** the cached Workbench γ and seed. For `not_reproduced` and `not_representable` pairs, Apply still works with γ = the Selected Resolution rounded to two decimals (at least 0.01) and the main seed.
- **Any pair** with a Selected Partition can be applied: the chosen pair, a near-best pair, any cell.
- **Provenance line:** it sits where `verify-result` is. It is checked once, on the first recompute after Apply, by comparing the Workbench's Clusters with the stored membership through the `verify` store mechanism. It reads "Applied from Parameter Selection: puzzle, g=14, s=2 — Selected Partition reproduced ✓" or "… shows a different partition from the Selected Partition: ARI 0.xx". It stays while the Network State key equals the applied key. It is display only: the key and `state_id` are unchanged.
- **Workbench γ input:** `min=0.01`, no maximum, `step=0.01`. Before, a two-decimal value off the 0.05 grid was invalid in the browser and Dash turned it into `None`.
- **Seed-Noise Floor note:** when the Workbench seed is a scan seed, the Workbench derives its noise seeds from it, so its floor can differ from the one Parameter Selection reports. The guide's Apply entry says so.
- **`applied_from`:** while the provenance line shows, "Export this state" adds an informational `applied_from` block to `export.json`. It holds the dataset, g, s, the grid key hash, the method version, the Workbench γ and seed, and reproduced or the ARI. It stays outside `state_key`, Open ignores it, and it never changes `state_id`.

### Exports

**Export tables** writes **one zip per settings key**, `steamstudy_parameter-selection_<settings_key_hash[:12]>_<UTC>.zip`, covering every dataset whose grid is complete. Tables are stacked by a `dataset` column.

- **Incomplete datasets** are left out, and `parameter_selection.json` records their status ("partial, k of 153" or "not run"). A complete but unvalidated grid exports with validation `not_run`.
- **Seven tables:**
  - `pairs.csv`: one row per pair, 153 per dataset. It holds:
    - g, s, tags, edges, n_e and the graph hash;
    - `gamma_max_n_e`, the last scan γ, the scan length and `pass_capped_runs`;
    - the Selected Partition's domain, midpoint and `clipped_high`, and the Workbench γ and seed with reproduced or ARI, `not_representable` and `not_reproduced`;
    - NA with its comparable, different-graph and identical-graph neighbour counts;
    - retention, isolated share, LCC share, Multi-Tag and One-Tag Clusters, and the Seed-Noise Floor (minimum, mean, exact);
    - the descriptive Q, Coverage and Silhouette;
    - `qualifies`, every failing reason code as a list, `near_best` and `chosen`.
  - `admissible_partitions.csv`: one row per pair and Admissible Partition. It holds Â, P̂, a, b, `clipped_high`, γ̂ or its reason, the map target, stable, Multi-Tag and One-Tag Clusters, the first γ and seed, hits and `selected`.
  - `neighbour_links.csv`: one row per directed link (g−, g+, s−, s+). It holds the status (comparable, missing or identical graph), shared and compared tags, ARI and Edge Overlap.
  - `selected_partitions.csv`: one row per pair and tag, giving its Cluster in the Selected Partition, so NA can be recomputed without Leiden.
  - `selection.csv`: one row per dataset. It holds the chosen pair or `no_qualifying_pair`, the max NA, the tolerance, the near-best set, the tie-break used, the constraints label with each changed value, and `settings_label`.
  - `validation_replicates.csv`: one row per replicate and arm (null, subsample re-selected, subsample at the Selected Resolution). It holds the seed, whether it had a Selected Partition or was degenerate and why, ARI, Q, the null's fixed-γ Q, the scan length and capped runs.
  - `validation_clusters.csv`: one row per validated pair, arm and Cluster. It holds the mean Jaccard, "≤ 0.5 in k of B*", the retention share, the absent count and `dissolved`.

  The validation files hold rows for validated pairs only.
- **`parameter_selection.json`** mirrors `export.json`. It holds:
  - `schema_version`, the `settings_key`, each dataset's `grid_key` and each validated pair's `validation_key`, with their hashes;
  - the Selection Settings and both labels;
  - the grid: g and s ranges, the γ step, the rule name `gm22_gamma_max_n_e`, 10 scan seeds and the pass cap;
  - every seed stream with its actual seeds (main, scan = 3, null = 4, subsample = 5), plus R, S, m rule, g′ and s′ per validated pair;
  - the Pair Constraints, tolerance and per-dataset overrides;
  - the method versions and software versions, and a copy of `build.json`;
  - per dataset, its status and the `computed_with` blocks of its grid and validated pairs;
  - each file's rows and SHA-256, and the `columns` block.
- **Schema:** the files are declared in `export/schema.py` under a new group, `parameter_selection`, with `column_attrs` for help. `SCHEMA_VERSION` goes to **3**.
- **`selection_report.md`** is in the zip. Per dataset: the explanation with its caveats, then the validation sentences and verdicts. Then the methods paragraph with citations. Every sentence comes from `selection_text` and every number from the CSVs.
- **Record only:** there is no Open path back into the mode. You reproduce a zip by running the same Build and settings, which gives byte-identical tables. The guide says to compare the SHA-256 values.

### Shipping in an App Bundle

- **What ships:** for **every Build** the bundle carries, exactly what Run → All datasets produces under the shipped code's default `SelectionSettings`. That is each dataset's complete grid and the validation of its default-constraint pair. Nothing else ships: no custom grids, no extra validations, nothing partial.
- **Always recomputed:** `steamstudy bundle` runs `ps_run` into the staging Build's `app_cache/parameter_selection/` with a pool of `[parameter_selection] workers`, after copying the Build (still with `ignore_patterns("app_cache")`).
  - Where the maker's own cache holds the same keys, the two are compared, with timings and `computed_with` aside. A difference logs a warning that the maker's cache is stale and a method version probably needed a bump. The fresh result ships either way, and the maker's cache is never touched.
  - It logs the ETA, one line per Build, dataset and phase ("Build …, puzzle: grid 87 of 153 pairs, about 1 min left").
- **`--skip-parameter-selection`** makes a bundle without results, for quick test bundles and the acceptance test. It is never used for a release.
- **`bundle.json`** gains `parameter_selection`: per Build, the shipped grid and validation key hashes, or `"skipped"`.
- In an extracted bundle the mode opens on finished results with no Run needed, showing the provenance line. "Clear app cache" deletes them like any entry, and a later Run recomputes locally.

### Documentation and in-app help

The documentation goes into the existing User Guide chapters, not a new one.

- **Ch. 1:** "The two modes" becomes three.
- **Ch. 2** gains a "Parameter Selection mode" section covering Run, Pair Constraints, Selection settings, the dataset strip, the heatmap and its reason letters, the Pair Inspector, Apply to Workbench, Validate this pair and Export tables.
  - **Run** explains the provenance line: shipped results were computed when the bundle was made; "Clear app cache" replaces them with this computer's; a recomputation could in principle differ on another Python or OS, but practically never, because every library version is locked.
  - **Apply** explains why an applied Workbench's Seed-Noise Floor can differ.
  - **Selection settings** says Lift is the studied default and that γ̂ is a heuristic outside unweighted multigraphs, whichever weight is used.
- **Ch. 3** gains a "Parameter Selection" section.
  - It opens with **"How Automatic Parameter Selection works"**: the steps in order (grid, γ scan, CHAMP, γ̂ and Stable Partitions, Selected Partition, Neighbour Agreement, constraints and choice, validation), each linking to its entry, plus the dataset-strip sentence. The loading panel's link and Run's `?` open it.
  - **Eleven entries** follow, each in the chapter's form (In short, Why it matters here, Exact definition, Example, Bounds, Compare with):
    1. Threshold Pair and Parameter Grid;
    2. Admissible Partition and Optimality Domain (CHAMP), with the γ range;
    3. γ̂ and Stable Partition;
    4. Selected Partition and Selected Resolution, with the Workbench γ, seed and `not_reproduced`;
    5. Neighbour Agreement, covering comparable, missing and identical-graph links;
    6. Edge Overlap;
    7. Information Retention;
    8. isolated share and LCC share;
    9. Pair Constraints, Qualifying Pair and the selection rule, covering near-best, tie-break and reason codes;
    10. Null Comparison;
    11. Subsample Stability, covering both arms, Hennig's Jaccard, the retention share and "Dissolved".
  - The existing Q, Coverage and Silhouette entries each gain a "Descriptive: not comparable across pairs" paragraph. The Seed-Noise Floor entry gains a one-line link to the Apply entry.
  - **"Three kinds of stability"** opens ch. 3's Stability section, and the four metrics' entries and the validation card link to it. It covers:
    - algorithmic: the Seed-Noise Floor, the same data and settings with other seeds;
    - parameter: Neighbour Agreement, neighbouring thresholds;
    - data: Subsample Stability, 80% of the games;
    - the Null Comparison as a fourth, separate check: is there more structure than in random networks with the same tag and game counts?
    - They answer different questions and are never combined into one score. A high value on one says nothing about the others.
- **Ch. 4** gains the eight new files.
- **Ch. 5** gains "Report a Parameter Selection": deposit the zip, compare hashes after a rerun, and the methods paragraph shown with placeholders. One sentence points to the Run entry for comparisons across machines.
- **Ch. 6** gains the new limitations.
- **Appendix A**'s Cluster-wise Jaccard entry gains: ≤ 0.5 = dissolved (Hennig 2007 §2) is the only cut used, only for Subsample Stability, and 0.6, 0.75 and 0.85 stay unused. The no-bands test allows that one phrase.
- **Appendix C** gains Weir et al. 2017 and Gibson & Mucha 2022 with their locators. Hennig's entry gains §2.
- **Methods paragraph:** one template in `selection_text`, rendered into `selection_report.md` and shown with placeholders in ch. 5. A test asserts that the guide's copy equals the template.
  - It cites Weir et al. 2017 §2, eqs. 1–4; Newman 2016 §III.A, eqs. 15–18; Gibson & Mucha 2022 Fig. 1(d), SI §C.2–C.3 and §J (the γ range); Hennig 2007 §2; Karrer, Levina & Newman 2008, abstract, §III and §VI.
  - It adds one sentence: the §J.2 derivation uses only Cauchy–Schwarz and assortativity, so the bound holds for unequal Clusters and for weights.
  - It says why log-width and γ-scaled area were rejected, describes the B* rule and floor scaling, and says fpc's bands refer to bootstrap and are not applied.
  - The locators in [Research 01](research/01-resolution-selection-formulas.md), [Research 02](research/02-validation-methods.md) and [Research 16](research/16-citable-gamma-upper-bound.md) count as the citation check.

#### Pinned statements

Tests check these exact strings.

- In `test_required_statements_in_the_metric_reference` (ch. 3):
  - "count alone carries no significance claim"
  - "not comparable across pairs and never select"
  - "Neighbour Agreement measures parameter stability, not correctness"
  - the high-g caveat paragraph, word for word as in the explanation
  - "a step that removes nothing perturbs nothing"
  - "Edge Overlap describes how much the graph changed, not whether the Clusters are right"
  - "a defensible choice, not the true structure"
  - "no likelihood behind"
  - "Different pairs in different datasets are expected and are not a disagreement"
- In `test_known_limitations_chapter_holds_the_full_list` (ch. 6):
  - "Neighbour Agreement tends to be higher at large g"
  - "count-only thresholds"
  - "Lift has no likelihood"
  - "no_qualifying_pair"

#### In-app help

- The mode uses the Workbench's two-layer `?` help.
- Each heatmap metric, Inspector label, Pair Constraint field, Selection Setting, reason letter, verdict tag, the Edge Overlap column and the dataset strip map to a guide entry through new `selection.*` keys in `HELP` (`app/help.py`) and `column_attrs` on the new schema columns.
- Run's `?` opens the ch. 3 overview. Apply and Validate this pair point to ch. 2.
- The existing help tests extend to the new keys.

#### Running Guide and release checklist

- **`docs/running-guide.md`:** a short paragraph giving the full Run's time on 12 workers and serially (as measured by the bundle issue), the cache's location (`<build>/app_cache/parameter_selection/`), and that "Clear app cache" removes it.
- **`docs/releasing-an-app-bundle.md`:**
  - step 4: making a bundle runs Parameter Selection for every carried Build (with the measured time per Build), what the stale-cache warning means, and that `--skip-parameter-selection` is never acceptable for a release;
  - step 5: check that the mode opens with finished results and that the provenance line names the maker's machine.
- Both files carry the researcher's **uncommitted** edits. Their issue starts only after the researcher has committed them.

### Resolved while writing this spec

These choices were implicit in the tickets and are made explicit here.

- **Keys:** the tickets say both "one grid key per grid directory" and "one zip per settings key across datasets". So `SelectionSettings` is dataset-free (`settings_key()`, which names the zip), and `grid_key(dataset)` / `validation_key(dataset, g, s)` add the dataset.
- **Apply fallback γ:** "kept inside [0.25, 3.00]" predates [Graph-specific γ scan](issues/16-graph-specific-gamma-scan.md). It is now "rounded to two decimals, at least 0.01", matching the new γ input.
- **Workbench γ candidates** start at 0.01, because the input's minimum is 0.01.
- **`[parameter_selection]` key names**, with `0` meaning off for the maximum Multi-Tag Clusters and for `workers`' automatic count.
- **Medium and narrow widths** reuse the Workbench's pill bar and floating Inspector.
- **The sentences live in `selection_text`**, so the app, the report and the guide test share one copy.
- **The loading panel** quotes the actual scan-length range instead of "56 resolutions", and no longer promises "at most ~20 s" lost on a cancelled validation.
- **Time figures** are re-measured by the bundle issue. The tickets' "~3 min / ~23 min" figures are void.
- **Exact pinned phrases**, which ticket 11 left to the spec.

## Out of scope

- Statistically validated edges (hypergeometric/Fisher + BH, Tarone). The brief keeps count-only thresholds.
- A bipartite nonparametric SBM cross-check (graph-tool has no Windows wheels).
- Validation extensions: a curve of subsample fractions, a noise-type scheme, Subsample Stability on null replicates, VI next to ARI.
- Adopting the selection in the Build or the feature-analysis report, or changing the `config/network.toml` defaults.
- One Threshold Pair for all five datasets, which is a different selection rule.
- Comparing datasets' Cluster structure, which is a study question.
- Louvain in the mode, an editable γ range, scan seeds, grid, R or S in the mode, an Open path for selection zips, and automatic spot-checks of shipped results.

## Issues

Status `ready-for-agent` unless noted. Numbering continues after the map's decision tickets (01–17).

- [18: Leiden pass loop, shared igraph construction and the γ input](issues/18-leiden-pass-loop.md)
- [19: CHAMP, γ̂ and the Selected Partition (`network.champ`)](issues/19-champ-module.md)
- [20: Selection Settings, configuration, keys and seeds](issues/20-selection-settings-and-keys.md)
- [21: Per-graph procedure and the grid driver](issues/21-run-graph-and-grid-driver.md)
- [22: Neighbour Agreement, Edge Overlap, choosing the pair and its explanation](issues/22-neighbour-agreement-and-choice.md)
- [23: Validation: Null Comparison and Subsample Stability](issues/23-validation-module.md)
- [24: Cache, Run driver and Clear app cache](issues/24-cache-and-run-driver.md)
- [25: User Guide entries and `selection.*` help keys](issues/25-user-guide-and-help.md)
- [26: Parameter Selection mode: Run, jobs, loading panel and dataset strip](issues/26-mode-run-and-strip.md)
- [27: Heatmap, "Why this pair" and the Pair Constraints panel](issues/27-heatmap-and-constraints.md)
- [28: Pair Inspector, validation card and Validate this pair](issues/28-pair-inspector-and-validation.md)
- [29: Selection settings section](issues/29-selection-settings-section.md)
- [30: Apply to Workbench](issues/30-apply-to-workbench.md)
- [31: Export tables](issues/31-export-tables.md)
- [32: Shipping results in an App Bundle](issues/32-bundle-shipping.md)
- [33: Running Guide and release checklist](issues/33-running-guide-and-release-checklist.md) (waits on the researcher's commit)
