# Map: Automatic Parameter Selection

Label: wayfinder:map

## Destination

An **implementation-ready spec** (`.scratch/auto-parameter-selection/spec.md`) plus numbered `ready-for-agent` implementation issues for **Automatic Parameter Selection** in the Tag Network app. For each **Top-100 Dataset** it searches the **Parameter Grid**, picks a **Selected Partition** per **Threshold Pair** (CHAMP + Gibson & Mucha **Stable Partitions**), picks a pair by **Neighbour Agreement** under configurable constraints, validates the result against curveball nulls and 80% subsamples, and shows all of it in a new app mode that can apply the result to the Workbench. Every methodological, architectural and UI decision is locked, so implementation can begin without further design questions. Implementation itself comes after this map, on branch `auto-parameter-selection`.

## Notes

- **Domain**: the Tag Network app of the Steam Success Study. Glossary: [CONTEXT.md](../../CONTEXT.md); use its terms (Threshold Pair, not "configuration"; Cluster, not "community"; Multi-Tag Cluster, not "non-singleton community"; Seed-Noise Floor, not "seed stability").
- **Skills**: grilling tickets → `grilling` + `domain-modeling`; research tickets → `research` (findings in `research/`, committed on this branch); architecture → also `codebase-design`; UI → `prototype` (in `prototypes/`).
- **Tracker**: local markdown, git repo with no remote. Branch `auto-parameter-selection`, cut from `graph-readability` (33 commits ahead of `main`, unmerged). The researcher's uncommitted changes in the working tree are never touched or committed by this effort.
- **Source brief**: the researcher's methodology (2026-10-25), sections 1–6, is the authority for every ticket. Prior context: [Research 31](../steam-success-study/research/31-data-driven-clustering-parameters.md) (this effort is its recommendation 3, the grid, with γ from recommendation 1, stable-partition pruning).
- **Settled while charting** (2026-10-25):
  - Destination is a spec plus issues; Build/report adoption of the selected parameters is out of scope, but the procedure lives in one shared `steamstudy.network` module so a later effort can call it from the Build (like `compute_state`).
  - Must run inside an App Bundle (ADR 0001): no new runtime dependency without wheels for Python 3.12–3.14 on every bundle target.
  - Runs in the app as a Dash background job (like Removal Sensitivity), parallel over a `multiprocess` pool, with live progress; results persist in `<build>/app_cache/parameter_selection/`, keyed by settings plus a method version, and are deleted by "Clear app cache".
  - CHAMP and the self-consistent γ estimate are our own numpy code; `modularitypruning` is a dev-only dependency used as a cross-check in tests.
  - The γ scan uses 10 seeds per γ from a new seed stream off the main seed (`derive_seeds`). Seed stability is the existing Seed-Noise Floor: Leiden at the Selected Resolution with the noise seeds, minimum ARI against the Selected Partition.
  - Three kinds of stability are never mixed: algorithmic (Seed-Noise Floor), parameter (Neighbour Agreement), data (Subsample Stability). The null-model comparison is a fourth, separate diagnostic.
  - A third app mode, "Parameter Selection", next to Workbench and Analysis Report mode.
  - Fixed settings default to: Genre Tags and the defining tag hidden, Minimum Months 0, Clustering Weight Lift, Leiden. The user can change them.
  - Count-only edges carry no significance claim; Q, Coverage and Silhouette are descriptive, never selection objectives across graphs.
  - Literature to cite: Weir et al. 2017; Newman 2016; Gibson & Mucha 2022; Hennig 2007; Karrer et al. 2008.
- **Measured while charting** (Build `20261008T221504Z-7a23ae9f`, Leiden on Lift, 80 γ × 5 seeds, one core): 0.2–4.3 s per Threshold Pair. At g=3/s=2: 125–139 tags, ~2,000–2,200 edges, 21–26% of edges with Lift < 1, 200–275 distinct partitions. At g=20/s=12: 21–26 tags, 18–35 distinct partitions. 153 pairs per dataset.

## Decisions so far

<!-- one line per resolved ticket -->

## Not yet specified

- **Shipping results in an App Bundle**: whether `steamstudy bundle` can carry precomputed Parameter Selection caches so a researcher opens finished results offline, and how a cache made on one machine is checked against the bundle's library versions.
- **Cross-dataset comparison**: what the side-by-side view of the five datasets shows beyond each one's chosen pair (shared-tag agreement between datasets? the same pair applied to all five?). Sharpens once the prototype and the metric definitions exist.
- **Changing the fixed settings**: which of the fixed settings (hidden tags, Minimum Months, Clustering Weight, algorithm, γ range, seed count) the mode exposes, and how a run with non-default fixed settings is labelled and cached.

## Out of scope

- **Statistically validated edges** (hypergeometric/Fisher + BH, Tarone): the brief keeps count-only thresholds (Research 31, recommendation 1's edge filter).
- **Bipartite nonparametric SBM cross-check**: graph-tool has no Windows wheels and the brief doesn't ask for it (Research 31, recommendation 2).
- **Adopting the selection in the Build or feature-analysis report**, or changing the `config/network.toml` defaults: a later effort.
