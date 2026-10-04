# User Guide metric reference
Type: research
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

For every metric the software computes, displays or exports (pipeline/Build, feature analysis, Tag Network app, Analysis Report mode and the Build's network tables), what should the User Guide say so that a researcher with no specialist knowledge of network analysis interprets the results correctly? For each metric:

- what it measures;
- how it is calculated, in this project's exact definition (column name, inputs, the Network State settings it depends on), with a plain-language worked example where the formula is not obvious;
- how to read high and low values;
- its expected range, where one exists (theoretical bounds, and typical values in comparable published work where the literature gives any);
- why it is relevant to this study;
- important limitations and cases where it may mislead (small samples, One-Tag Clusters, disconnected clusters, n/a statuses, dependence on thresholds, γ, seed or Clustering Weight, the Top-100 selection itself, causal misreadings).

Requested by the researcher on 2026-10-04. Raises the map's destination to include a researcher-facing User Guide alongside the spec.

**Scope of "every metric"** (the inventory must be built from the resolved tickets, not from this list, which is only a starting point):
- Ranking and data: Mean Monthly Players, Monthly Avg. Players, Months Observed, rank, Release Month and the `release_month_check.csv` gap, completeness-report counts. Sources: [Placeholder rows and the Release Month definition](16-placeholder-rows-release-month.md), [Candidate pool definition](08-candidate-pool-definition.md), [Pipeline architecture and export schema](15-pipeline-architecture.md).
- Feature analysis: tag/genre frequency and share, Eligible Pool baseline, `share_ratio`, combination support, phi, lift, Jaccard, Fisher p, BH q. Source: [Feature-analysis definitions](13-feature-analysis-definitions.md).
- Network: edge weight (`shared_games`), edge `lift`, Clustering Weight; node `n_games`, `degree`, `degree_intra`, `strength_shared`, `strength_lift`, `medoid_score`, `is_center`, `top_strength_tag`, `center_is_top_strength`, `within_z`, `participation`, per-node silhouette, `membership_stability`. Sources: [Edge weight used for clustering](19-edge-weight-for-clustering.md), [Cluster center and centrality measures](11-cluster-center-centrality.md).
- Cluster and partition quality: cluster counts (k multi-tag + s one-tag), disconnected flag, Jaccard game-set silhouette, modularity Q, null-model baseline and z-score, edge/weighted density, conductance, cut weight, cluster × cluster connections, `mean_membership_stability`. Source: [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md).
- Stability: Seed-Noise Floor (`seed_ari_min`, `seed_ari_mean`, `seed_modularity_sd`, `seed_silhouette_sd`, `seed_k_min`, `seed_k_max`), Resolution Sweep. Source: [Seed stability reporting and consensus clustering](25-clustering-stability.md).
- Removal Sensitivity: reclustered ΔQ, Δsilhouette, Δk/Δs, ARI, centers lost; fixed-partition ΔQ, Δsilhouette; `beyond_noise`. Source: [Node-removal sensitivity method](12-node-removal-sensitivity.md).
- Exact column names, n/a statuses and units: [Export schemas for the app and the feature analysis](24-export-schemas.md). Glossary: [CONTEXT.md](../../../CONTEXT.md).

**Constraints the guide must respect** (already decided): frequency and correlation are never presented as causation; no semantic cluster names; Seed-Noise Floor and Membership Stability are numbers only, with no stable/unstable labels; the `beyond_noise` flag is a screening aid, not a significance test; BH q values are descriptive only; use the glossary's terms and avoid its "Avoid" words.

**Not decided here** (left to [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md)): whether the guide prints rule-of-thumb bands (e.g. "silhouette above 0.5 = strong"), how much formula notation it shows, and its final structure.

## Answer

Resolved 2026-10-04 (research, AFK). Findings: [research/26-user-guide-metric-reference.md](../research/26-user-guide-metric-reference.md). That file is the draft content of the User Guide's metric reference; the guide's wording and form are decided in [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md).

- **Inventory**: 63 entries (trivially related columns grouped), each with column names, source ticket and the six requested headings, and worked examples computed with scikit-learn 1.6.1 / SciPy 1.15.2. Ranking and data 8; feature analysis 15; network nodes and edges 13; clusters and partition quality 11; stability 7 (incl. Resolution Sweep); Removal Sensitivity 9. A "Settings that change the numbers" table (17 rows) covers γ, seeds, thresholds, Clustering Weight, R, K and the filters.
- **Blanket rules for the guide**: no causal reading, no cluster names, quote the `state_id` with every number.
- **Literature bands** (recorded, not adopted): modularity 0.3–0.7 typical (Newman & Girvan 2004; Clauset et al. 2004; Fortunato & Barthélemy 2007); silhouette (Struyf, Hubert & Rousseeuw 1997, after Kaufman & Rousseeuw 1990); ARI (Steinley 2004); cluster-wise Jaccard stability (Hennig 2007); node roles from `within_z` / `participation` (Guimerà & Amaral 2005); phi (Cohen 1992). No published bands for conductance, densities, coverage, the Q z-score, the seed SDs or `share_ratio`, and no published values for Steam tag networks.
- **Twelve open issues** for the researcher, split between two tickets:
  - spec gaps (undefined triple lift, reused column names, missing n/a rules for conductance/density on One-Tag Clusters and for phi, unstated sign/SD/status conventions) → [Metric definition gaps](28-metric-definition-gaps.md);
  - interpretation and possible method changes (`beyond_noise` on ΔQ/Δsilhouette, expected chance ARI flags, `modularity_z` over-reading, Membership Stability = 1 for isolated tags, `within_z` in small clusters, `share_ratio` baseline including the Top 100, silhouette and ARI bands vs. the no-label rule) → [User Guide metric wording and interpretation bands](27-user-guide-wording-bands.md).
- **Citations**: full text checked for Newman & Girvan 2004, Clauset et al. 2004, Fortunato & Barthélemy 2007, Guimerà et al. 2004, Guimerà & Amaral 2005, Traag et al. 2019, Brandes et al. 2008, Brin et al. 1997, Struyf et al. 1997, Hennig 2007 (preprint) and the library docs. Kaufman & Rousseeuw 1990 not verified; Steinley 2004 and Cohen 1992 band values seen only in secondary sources; Li & Zhang 2020 record only; several others bibliographic or abstract level (listed in the findings' Sources).
