# Map: Bilingual Interface and Cluster Views

Label: wayfinder:map

## Destination

An **implementation-ready spec** (`.scratch/bilingual-cluster-views/spec.md`) plus numbered `ready-for-agent` implementation issues for four Tag Network app features: (1) an English/Bulgarian language switch across the whole interface and User Guide, (2) customisable edge appearance, (3) size-aware connection strength between Clusters, explorable visually and pair by pair, and (4) the games within each Cluster, ranked by matching tags. Every design decision is fixed, so implementation can start without further design questions. Implementation itself comes after this map, on branch `bilingual-cluster-views`.

## Notes

- **Domain**: the Tag Network app of the Steam Success Study. Glossary: [CONTEXT.md](../../CONTEXT.md). Use its terms: Cluster, One-Tag Cluster, Multi-Tag Cluster, Network State, Clustering Weight, and **edge weight = shared-game count, always**.
- **Skills**: grilling tickets use `grilling` + `domain-modeling`. Research tickets use `research`, with findings in `research/` committed on this branch. Architecture questions also use `codebase-design`. UI questions use `prototype`, with prototypes in `prototypes/`.
- **Tracker**: local markdown, in a git repo with no remote. Branch `bilingual-cluster-views` was cut from `auto-parameter-selection` at `449d7b7`. This effort never touches or commits the researcher's uncommitted changes in the working tree (`config/collection.toml`, the untracked `auto-parameter-selection` prototype files).
- **Hard rule: no scientific change.** No Network State, `state_id`, Cluster, metric, Parameter Selection result or cache key may change. Language and edge appearance are view choices, like the existing "show shared games" switch: they are never part of the Network State, an export or any number. Features 3 and 4 only read the Network State on screen. New columns or tables are additive and never redefine an existing one.
- **Settled while charting** (2026-10-27):
  - The destination is a spec plus issues, as on the earlier maps, and implementation follows. It is one map for all four features. The translation *mechanism* is decided early, so features 2–4 are built with it. The bulk Bulgarian translation comes last, so it also covers their new text.
  - **Translated**: every visible string in all three modes (Workbench, Analysis Report mode, Parameter Selection), error and warning messages, generated explanations (Network State sentence, quality lines, "Why this pair", loading panels), tooltips and help, and the whole User Guide as a Bulgarian copy. Tooltips and help come from the guide (`help.py`), so translating help means translating the guide.
  - **Stays English**: exported files (CSV columns, `selection_report.md`, JSON), the CLI, the Running Guide and the release checklist. Steam tag names, game titles, Steam's Genre values and cluster labels `C1…` are never translated.
  - The agent drafts every translation. A Bulgarian term table is agreed with the researcher before the bulk translation, and the researcher reviews the Bulgarian guide in a final HITL step.
  - Features 3 and 4 live in the **Workbench**, for the Network State on screen, in both the Global and the Cluster-separated layout. Parameter Selection and Analysis Report mode get translation only.
  - Feature 3 **extends** the existing `cluster_connections.csv` / `metrics.connections` (`edge_count` plus `weight` in the Clustering Weight, with One-Tag Clusters pooled as `one_tag_pool`, shown in the Cluster quality tab). It does not compute the same thing again in parallel. "Total inter-cluster edge weight" means the shared-game sum. Under Lift a second total, the Lift sum, is shown and labelled as Lift. A normalised strength is computed for both.
  - Number format: the leaning is language-dependent on screen (Bulgarian decimal comma) with exports unchanged. To be confirmed in [Bulgarian terminology](issues/03-bulgarian-terminology.md).
  - Constraint: [ADR 0001](../../docs/adr/0001-app-bundle-wheels-not-frozen.md). The app runs from an App Bundle, so any new runtime dependency needs wheels for every bundle target.

## Decisions so far

<!-- one line per resolved ticket -->
- [Normalised inter-cluster strength in the literature](issues/05-normalised-inter-cluster-strength.md): the configuration-model ratio w_ab/(k_a k_b/2m) is the degree-corrected SBM affinity and the modularity merge test, so it is at most γ for every pair shown. Density is inflated for two-tag Clusters, game-set Jaccard or Lift is saturated, and PAGA does not fit. The recommendation (ratio as the headline, plus shares of cut) is non-binding; [research](research/05-normalised-inter-cluster-strength.md).

## Not yet specified

- **Bulk translation sequencing and review**: how roughly 3,500 guide lines plus all UI strings get translated in implementation-sized slices, how parity with English is kept when the English guide changes, and how the researcher reviews. Clears once the inventory, the mechanism and the term table are settled.
- **Exports for features 3 and 4**: whether the cluster-games list becomes a new table in the Workbench export, and the exact column shapes. It depends on the measures and games decisions.
- **Spec and implementation issues**: written once the frontier is empty.

## Out of scope

- Features 3 and 4 in the Parameter Selection mode's Pair Inspector or in Analysis Report mode.
- Translating exports, the CLI, the Running Guide or the release checklist.
