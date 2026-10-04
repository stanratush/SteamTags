# Feature-analysis definitions
Type: grilling
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: none

## Question

For each Top-100 Dataset, how exactly are these computed and reported: most frequent tags; most frequent genres (store genre field); common tag combinations (pairs only or larger itemsets; support/lift/confidence thresholds); relationships between gameplay/style features (which association measure, e.g. lift, Jaccard, phi, and how significance is handled); and "clusters of characteristics" (the network's clustering at default thresholds, or a separate method)? Note: `Puzzle` is a tag but not a store genre (see [Official Steam tag taxonomy extraction](04-steam-tag-taxonomy.md)), so genre counts for the Puzzle dataset will show no "Puzzle" genre. What is the output form (CSV/JSON tables, static report), and what wording guards against causal claims?

Surfaced by [Exclusion and genre-tag config contents](09-exclusion-genre-config.md):
- Genre frequencies report every observed store-genre value (nothing dropped), with a config `kind` column (`genre` / `business` / `software`): how is `kind` used in tables and text?
- Content Flags (`desktop_companion`, `sexual_content_tag`) are reported per dataset: as counts only, or also in tag/combination analyses?

## Answer

Resolved 2026-10-03 with the researcher.

**Across all analyses**
- **Input:** each full exported Top-100 Dataset; the Minimum Months Filter is not applied. The report shows the `months_observed` distribution and the `is_free` count.
- **Counting:** every game counts once; no weighting by Mean Monthly Players.
- **Tag scope:** all tags treated the same, with no gameplay/style split. `archived_category` (archived Steamworks table, empty for uncategorised tags) is an information column only; nothing computes on it.
- **Defining tag** (Tag-Specific Datasets): listed in the tag-frequency table at 100% with `defining_tag = true`; left out of the combination, association and cluster analyses.
- **Baseline** = share in the **Eligible Pool** (scored, non-excluded games in the dataset's scope, Top 100 included). Applies to tags and genres only.

**Tables** (tidy CSVs, one per analysis, the five datasets stacked under a `dataset` column)

| Table | Contents | Sort |
|---|---|---|
| Tag frequency | every tag on ≥1 game: count, share, median position in the store tag list (among games that have it), `defining_tag`, `baseline_share`, `share_ratio` = share / baseline_share | count desc, tie by name |
| Genre frequency | every store-genre value: `genre_id`, name, config `kind` (`genre`/`business`/`software`), count, share, `baseline_share`, `share_ratio`. Headlines and summary sentences use `kind = genre` rows only. Puzzle dataset gets an automatic note that Puzzle is not a store genre. | count desc |
| Combinations | itemsets of size 2…`max_itemset_size` (config, default 3) with support ≥ `min_support` (config, default 10 games): support count/share and lift; pairs also get confidence both ways. A triple is dropped when its support equals one of its sub-pairs. No baseline columns. | support desc |
| Associations | every pair of tags that each reach `min_support` (same parameter), including zero co-occurrence: phi (primary), lift, Jaccard, two-sided Fisher exact `p`, Benjamini–Hochberg `q` corrected within each dataset. No binary "significant" column. | \|phi\| desc |
| Content Flags | per flag: count and flagged games (AppID, name, rank). The flags' underlying tags get no other special treatment. | n/a |
| Clusters | the Tag Network's own clustering code, run headless on the shared network defaults (minus the defining tag) and the fixed seed; labelled `C1…` by size, never named; listed by member tags and center; metrics as decided in [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md) and [Cluster center and centrality measures](11-cluster-center-centrality.md). | n/a |

**Shared network defaults:** one config read by both the app and the report (minimum games per tag, minimum shared games, Genre Tags hidden or shown). Values are set in [Tag network app interaction prototype](14-tag-network-app-prototype.md). The report records the values used in its metadata.

**Output and wording**
- One folder per run: the CSVs, a metadata JSON (config + hash, seed, snapshot timestamps, software versions), and a generated report (Markdown rendered to HTML), one section per dataset. Every number in the report comes from the CSVs.
- Report text comes only from fixed sentence templates (e.g. "appears in 63 of the 100 games (Eligible Pool: 21%)", "co-occurs with … in 34 games"). A standard caveat paragraph opens every report. A test fails the build if the rendered report contains a causal word from a configured list (*drives, leads to, makes … successful, key to success, predicts, because, effect*).
- Templates never mention significance. Column headers and the caveat call q-values a descriptive screen ("co-occurrence unlikely under independence within this dataset"), not evidence about Steam in general, because the Top 100 is not a random sample.

Glossary updated: new **Eligible Pool** ([CONTEXT.md](../../../CONTEXT.md)).
