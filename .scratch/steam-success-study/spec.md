# Spec: Steam Success Study

Status: ready-for-agent
Type: spec
Map: [Steam Success Study](map.md) (all 30 tickets resolved; this spec is the map's destination)
Glossary: [CONTEXT.md](../../CONTEXT.md). Every capitalised domain term below is used as defined there.

## Problem Statement

The researcher studies what highly successful commercial Steam games have in common: which **Tags**, tag combinations and store **Genres** recur among the most-played games, and which tags cluster together. The results will later be compared with educational/STEM games. To do that, they need data that can be defended in an academic paper.

Today no such dataset exists in a form they can trust:

- The obvious sources are a problem. SteamDB forbids scraping without permission. Steam Charts publishes no terms. Steam store data is undocumented, varies by region and sits behind age gates. A careless scraper could break site rules or trip anti-bot protection, and the results could not be reproduced.
- "Success" needs a precise, defensible score. Naive treatment of Steam Charts data counts placeholder 0.00 rows and gaps as zeros, picks the wrong release month, and misses games that were huge earlier in the window but have since declined.
- Steam's community tags include joke votes, adult content, software and dating sims. Deciding which games to leave out must be explicit, configurable and documented per game, never silent.
- Network analysis of tag co-occurrence has many hidden degrees of freedom: algorithm, seed, resolution, edge weight, thresholds and filters. Results that cannot be pinned to exact settings cannot be cited or reproduced. Metrics like modularity, silhouette or ARI are easy to over-read, and the researcher's readers have no network-analysis training.
- Frequency and co-occurrence are easily mistaken for causes of success. Clusters are easily given meanings they don't have.

## Solution

One Python package, `steamstudy`, with three parts and two guides:

1. **A resumable, polite data-collection pipeline (Collect).** It reads the whole Steam Charts "Top Games" listing as the **Candidate Pool** and fetches each app's monthly history from Steam Charts. For scored apps only, it fetches tags and details from the Steam store, a confirmed **Source Substitution**. Every raw response is archived in an immutable **Snapshot**. Collection is slow, rate-limited and stops hard on any anti-bot challenge. It resumes from its own request log. A full run refuses to start until the pre-run obligations are recorded.
2. **An offline, deterministic Build.** From one Snapshot plus versioned config it derives the five **Top-100 Datasets** (Overall, Puzzle, RPG, Strategy, Simulation) ranked by **Mean Monthly Players**. Alongside them it writes:
   - the **Exclusion** records with every matching reason, plus the completeness, impact and diagnostic reports;
   - the per-dataset feature analysis: tag and genre frequencies against the **Eligible Pool**, tag combinations, pairwise associations, **Content Flags**, and the network's **Clusters** with stability diagnostics;
   - a generated report whose wording is templated and machine-checked against causal language.
3. **A local interactive Tag Network app** (Dash, offline, `127.0.0.1` only). It loads one Build's Top-100 export and builds the **Tag Network**, then clusters it with Louvain (default) or Leiden at a shown seed and resolution. Next to the clusters it shows:
   - quality metrics against a null model and a standing **Seed-Noise Floor**;
   - **Cluster Centers** and per-tag **Membership Stability**;
   - on-demand **Removal Sensitivity**.

   The app has two modes over one state: a Workbench and an **Analysis Report mode**. Every result is identified by its **Network State** key (`state_id`), can be exported as one self-contained zip, and can be reopened exactly. The app and the Build share one clustering code path, and a test proves they give identical tables.
4. **A User Guide** (Markdown in the repo, also served inside the app) that explains every metric to a non-specialist through bounds, reference points and the project's own comparisons, never through rule-of-thumb bands. It also has a **Running Guide** for whoever runs the pipeline. Code keeps the guide's column index and in-app help in step with the export schema, and tests fail when the guide goes stale.

## User Stories

### Researcher: data collection and sources

1. As the researcher, I want monthly Avg. Players taken only from Steam Charts, so that the success score comes from the named source.
2. As the researcher, I want tags taken from the Steam store page's displayed tag list (tag id, name, votes, display order), so that "has tag" matches what a Steam visitor sees.
3. As the researcher, I want app type, store genres, `is_free`, release date and name taken from the Steam store `appdetails` in English, so that every required field has one confirmed source.
4. As the researcher, I want every source other than Steam Charts and SteamDB used only after my explicit confirmation, so that no Source Substitution happens silently.
5. As the researcher, I want the Candidate Pool to be every row of the Steam Charts `/top` listing with no cutoff by current players, so that games that declined or were delisted during the window are still candidates.
6. As the researcher, I want the listing read in N full passes (default 2), unioned by AppID, so that rows that shift between pages during a pass are not lost.
7. As the researcher, I want per-pass start/end times, row counts and the number of AppIDs seen in only one pass recorded, so that I can judge how stable the listing was.
8. As the researcher, I want the pool size reported but not enforced, so that the pool is never padded from other sources.
9. As the researcher, I want store data fetched only for apps that have a score, so that collection does not waste requests on apps that can never rank.
10. As the researcher, I want the Steam Charts request rate to be a parameter (default 3 requests/s, one kept-alive connection, sequential), so that I can lower it if the site operator asks.
11. As the researcher, I want the store request rate to be a parameter (default 1 request/2 s, one connection shared by store pages and `appdetails`), so that collection stays polite.
12. As the researcher, I want collection to stop hard on 403, 429, 503 or any challenge page, with no browser emulation, proxies or challenge solving, so that the study never bypasses anti-bot protection.
13. As the researcher, I want timeouts and connection errors retried after 10 s, 30 s and 90 s and then stopped, so that transient failures don't end a long run while persistent ones do.
14. As the researcher, I want a descriptive User-Agent with my contact details on every request, so that site operators can reach me.
15. As the researcher, I want the store's age check passed only the way a logged-out visitor passes it (age-check cookie with a birth date 30 years before the collection date), and never by logging in, so that mature titles are collected without circumventing access control.
16. As the researcher, I want apps whose age check still shows after the cookie recorded as `age_gate` and flagged for review, so that no workaround is ever attempted.
17. As the researcher, I want every raw response kept locally and gzipped in the Snapshot, and never redistributed, so that every number can be traced back to what was fetched.
18. As the researcher, I want collection to resume by rerunning the same command, skipping requests that already have a final outcome, so that a hard stop or a crash costs nothing.
19. As the researcher, I want collection stages run strictly in order (pool, history, store, tag list), so that each stage's input is complete before it starts.
20. As the researcher, I want the live `GetTagList` vocabulary snapshotted with its `version_hash` when the store stage starts, so that tag ids are checked against the vocabulary of the collection date.
21. As the researcher, I want a closed Snapshot to change only through a logged repair of one app with a written reason, so that it stays immutable and auditable.
22. As the researcher, I want the store fetched without a country parameter and the country Steam reports recorded in the Snapshot, so that region effects are documented rather than hidden.
23. As the researcher, I want a SteamDB cross-check collector that is disabled until I record a permission reference, and that is tested only on pages saved by hand, so that live SteamDB is never touched without permission.
24. As the researcher, I want the SteamDB cross-check to fetch only the Top-100 members of one Build and to produce a store-vs-SteamDB tag comparison, so that SteamDB values never enter a dataset.
25. As the researcher, I want a small test Snapshot (first 4 listing pages of one pass plus configured edge-case AppIDs) that may run before the operator replies, so that the code is proven on real pages early.
26. As the researcher, I want the full Snapshot to refuse to start unless the Steam Charts operator's reply and the ethics-office check are recorded in config, so that the pre-run obligations are enforced by code.

### Researcher: scoring, exclusions and datasets

27. As the researcher, I want Mean Monthly Players to be the mean of Monthly Avg. Players over the post-release months with data inside the 60-month Observation Window, so that the score matches the study's definition.
28. As the researcher, I want the Observation Window fixed by the Snapshot's collection date, with later month rows ignored, so that a Build is reproducible whenever it runs.
29. As the researcher, I want any 0.00 Avg / 0 Peak row treated as a Placeholder Row (not data, wherever it sits), so that placeholders never become zeros or Release Months.
30. As the researcher, I want rows with 0.00 Avg but Peak ≥ 1 and tiny pre-launch months kept as real data, so that nothing Steam Charts recorded is silently dropped.
31. As the researcher, I want the rolling `Last 30 Days` row always skipped, and unknown row labels or duplicate months treated as parse errors, so that only calendar months are averaged.
32. As the researcher, I want Missing Months to stay missing, never zero, so that months when Steam Charts did not track a game don't lower its score.
33. As the researcher, I want `months_observed` reported for every game, with no minimum applied when ranking, so that the ranking follows the score definition and I can filter later.
34. As the researcher, I want ranking ties broken by `months_observed` (descending) and then AppID (ascending), with every game tied with rank 100 reported, so that each dataset always has exactly 100 rows and ties are visible.
35. As the researcher, I want each Tag-Specific Dataset to contain only games that have the exact defining tag anywhere in the displayed list, so that sub-genre tags don't qualify.
36. As the researcher, I want a game to be able to appear in several datasets, so that each dataset is a true Top 100 of its scope.
37. As the researcher, I want exclusion rules and tag lists in config files, keyed by tag id with names as labels, so that rules are explicit, versioned and independent of tag spelling.
38. As the researcher, I want every rule a game matches recorded with its detail, plus a `primary_reason`, so that exclusion counts can be read both overlapping and partitioned.
39. As the researcher, I want games with no store data excluded as `store_data_unavailable` and games with an empty tag list excluded as `no_tags`, never silently skipped, so that every missing game has a reason.
40. As the researcher, I want adult content identified by Steam's "Adult Only" notice, content descriptor 3, or the `Hentai` tag within its rank limit, with the signals that fired recorded, so that mainstream games with nudity stay in.
41. As the researcher, I want the software tag list and the `Dating Sim` rule applied as configured, with `Game Development`, `Programming`, `Coding`, `Gaming`, `Otome`, `Romance`, maturity tags and `Education` never used as exclusion grounds, so that only the decided rules exclude games.
42. As the researcher, I want one global tag-rank limit (default: anywhere in the displayed 20) with optional tighter per-tag limits, so that I can tighten Dating Sim after reading the impact report without changing "has tag" anywhere else.
43. As the researcher, I want a `manual_exclusion` list and an `exclusion_override` list, each entry with a written reason, evidence URLs and retrieval dates, so that individual decisions are documented and published.
44. As the researcher, I want to add back a game with no store data through a sourced Manual Metadata Entry (full, or tags-only for a `no_tags` game), and I want an unsourced entry or an entry for an app the store does provide to fail the Build, so that hand-supplied data is always cited and never overrides real store data.
45. As the researcher, I want manually sourced games flagged (`manual` / `manual_tags`) and their citations reported, so that readers can see which rows depend on my sourcing.
46. As the researcher, I want Content Flags (Desktop Companion; sexual-content tags) exported per game and counted, but never used to filter, so that characteristics worth reporting stay visible without removing games.
47. As the researcher, I want an impact report before the lists are frozen (removals per rule and per tag with would-be ranks, near-misses beyond rank limits, Adult Only vs descriptor 3 disagreements, unexcluded Top-100 games carrying descriptor 1/4, a software genre or a Content Flag), so that I can review the effect of each rule before publishing.
48. As the researcher, I want a report of every excluded game that would have scored inside a Top 100, so that the cost of the `store_data_unavailable` and `no_tags` exclusions is visible.
49. As the researcher, I want a completeness report (listing rows, scored apps, scored `game` apps, per-pass statistics, exclusion counts per reason, unscored apps split three ways, Placeholder Row count, depth check of each dataset's members' `/top` ranks), so that I can argue that declined games were caught.
50. As the researcher, I want every Placeholder Row listed with its position (leading / interior / trailing), so that the placeholder rule's effect can be audited.
51. As the researcher, I want a diagnostic listing Top-100 games whose Release Month differs from the store release date by more than a configurable number of months (default 3, signed `months_apart`), so that unusual histories are visible without becoming a rule.
52. As the researcher, I want every distinct tag and genre seen logged with app counts, and a configured tag id missing from the vocabulary snapshot to raise a warning, so that config drift is caught.
53. As the researcher, I want a Build to fail on any parse error unless I pass an explicit flag, and Builds made with that flag marked and never published, so that partially parsed data cannot slip into results.
54. As the researcher, I want each Build in its own folder named by timestamp and config hash, never overwriting an earlier one, so that before/after comparisons of config changes are possible.
55. As the researcher, I want every config change logged with its rationale and the config hash stored in every output, so that each result traces to an exact configuration.
56. As the researcher, I want `monthly_players.csv` always written but not published until the Steam Charts operator agrees, so that I respect the source while keeping the data for my own checks.

### Researcher: feature analysis and report

57. As the researcher, I want each full Top-100 Dataset analysed with every game counted once, without the Minimum Months Filter and without weighting by score, so that the analysis describes the published dataset.
58. As the researcher, I want tag and genre frequency tables with the Eligible Pool share as a baseline and a `share_ratio`, with the Eligible Pool size printed, so that I can see which tags are over-represented and what the ceiling of the ratio is.
59. As the researcher, I want every store-genre value reported with its id and a config `kind` (`genre` / `business` / `software`), with headline sentences using `kind = genre` only, so that nothing is dropped and business labels like Free To Play don't headline as genres.
60. As the researcher, I want the Puzzle dataset's genre table to carry a note that Puzzle is not a store genre, so that readers don't misread its absence.
61. As the researcher, I want tag combinations up to a configurable size (default 3) with a configurable minimum support (default 10 games), with support, lift and pair confidence, so that I can see recurring combinations.
62. As the researcher, I want pairwise tag associations (phi, lift, Jaccard, Fisher p, Benjamini–Hochberg q within each dataset) presented as a descriptive screen, so that co-occurrence is quantified without significance claims about Steam in general.
63. As the researcher, I want the defining tag listed at 100% in the frequency table and left out of combination, association and cluster analyses, so that it does not dominate them.
64. As the researcher, I want the report's clusters produced by the same network code and shared defaults as the app, so that the report and the app never disagree.
65. As the researcher, I want the report to state the Seed-Noise Floor, the tags with the lowest Membership Stability, the Resolution Sweep range, and how many tags Removal Sensitivity flags against the number expected by chance, so that the reader sees how settled the clusters are.
66. As the researcher, I want report text built only from fixed sentence templates, opened by a caveat paragraph and closed by a fixed limitations paragraph, and I want the Build to fail if the report contains a configured causal word, so that no causal claim reaches a reader.
67. As the researcher, I want a methods paragraph generated with the report, covering clustering, the null model, silhouette, centers, Removal Sensitivity, seed stability and the Resolution Sweep, so that I can quote it in a paper.

### Researcher: interactive Tag Network app

68. As the researcher, I want to start the app on a chosen Build (default: the latest) and pick one of its five datasets, so that I only ever analyse the pipeline's own exports.
69. As the researcher, I want the app to open in my browser at `127.0.0.1` with no internet access needed, so that it runs offline and responds quickly on Windows.
70. As the researcher, I want sliders for minimum games per tag (default 8, range 1–40), minimum shared games (default 8, range 1–30) and the Minimum Months Filter (default 0, range 0–60), so that I can explore how thresholds shape the network.
71. As the researcher, I want Genre Tags and the defining tag hidden by default with per-tag toggles, so that broad tags don't swamp the network.
72. As the researcher, I want to remove a node from the inspector, restore one, or reset all, without changing the source dataset, so that I can explore "what if" freely.
73. As the researcher, I want every tag left out of the network listed with all its reasons (removed, defining tag hidden, Genre Tag hidden, below minimum games), so that nothing disappears unexplained.
74. As the researcher, I want isolated tags kept as One-Tag Clusters and counted separately ("k multi-tag + s one-tag"), so that the cluster count is not inflated or hidden.
75. As the researcher, I want to choose the Clustering Weight (shared games by default, or lift), the algorithm (Louvain by default, or Leiden), the resolution γ (default 1.00, range 0.1–3.0, step 0.05) and the seed, so that I can show how much results depend on these choices.
76. As the researcher, I want edge thickness and thresholds always based on the shared-game count, whatever the Clustering Weight, so that the drawn network means the same thing in every mode.
77. As the researcher, I want clusters coloured and labelled `C1…` by size, never named, so that no meaning is suggested by the tool.
78. As the researcher, I want Cluster Centers drawn as ◆ with a heavier outline only for clusters of 3+ tags, with the most-frequent alternative (`top_strength_tag`) shown beside each center, so that typicality and frequency are both visible.
79. As the researcher, I want disconnected Louvain clusters flagged (never split) with a suggestion to try Leiden, so that I know when a cluster isn't a connected group.
80. As the researcher, I want to click a node, an edge or a cluster to inspect it: a node's metrics, an edge's shared games (fetched on click) and lift, a cluster's members ranked by medoid score, so that I can see what lies behind every element.
81. As the researcher, I want a Cluster-quality row showing Q against its null model ("Q 0.42 vs null 0.31 ± 0.01, excess 0.11, z 11; null networks average 640 edges vs 702"), coverage, cluster counts, silhouette (labelled as a descriptive diagnostic) and the Seed-Noise Floor line, so that every partition comes with its context.
82. As the researcher, I want Membership Stability shown per tag and per cluster as plain numbers, with no stable/unstable labels, so that I see seed dependence without invented cut-offs.
83. As the researcher, I want `within_z` shown with its cap for the cluster's size ("within-z 1.2 (max 1.7 in a 4-tag cluster)"), so that I don't compare it across cluster sizes.
84. As the researcher, I want tabbed tables (Cluster quality, Clusters, Removal sensitivity, Nodes, Edges, Not in network) that are sortable and filterable, so that I can study the numbers beside the graph.
85. As the researcher, I want to switch the graph between a Global layout and a Cluster-separated layout without reclustering, so that I can see both the overall structure and each cluster's shape.
86. As the researcher, I want the Global layout to depend only on dataset, Minimum Months Filter, Clustering Weight and seed, not on thresholds, so that the graph doesn't jump as I move sliders.
87. As the researcher, I want a Re-layout button that refines positions from the current ones, recorded in exports as `layout_source = relayout`, so that I can tidy a figure and reproduce it later.
88. As the researcher, I want to collapse Controls, Inspector and Tables independently, or show the graph only, with inspection opening as a floating panel when the inspector is collapsed, so that the graph can fill the window.
89. As the researcher, I want an Analysis Report mode (numbered sections: Dataset, Filters, Network + inspector, Cluster quality, Removal sensitivity, All nodes/edges, Export) over the same state as the Workbench, so that I can read one Network State top to bottom.
90. As the researcher, I want sliders to recompute on release and the seed and γ inputs to recompute on Enter or blur, so that queued recomputes don't show stale states.
91. As the researcher, I want Removal Sensitivity run only when I press a button (all visible tags, or "Run for this tag"), with a time estimate, progress, cancel and "Continue (n of N done)", so that the expensive sweep never blocks exploration.
92. As the researcher, I want each removal read two ways (reclustered from scratch, and with the partition fixed) and the ARI flagged when it falls below the lowest seed ARI, labelled a screening flag with the number of flags expected by chance, so that I don't mistake seed noise for dependence.
93. As the researcher, I want Removal Sensitivity results cached per Network State and shown as current when I return to that state, and greyed as stale otherwise, so that I never confuse results from different settings.
94. As the researcher, I want a "Clear app cache" action (button and CLI), so that I control the only persistent cache.
95. As the researcher, I want "Export this state" to download one self-contained zip (all tables, provenance, file hashes, the state key), so that no exported number leaves the app without its settings.
96. As the researcher, I want "Open Network State…" to reload an export zip, refuse it if the Build or `key_version` differs, restore every setting and Re-layout positions, and show ✓/✗ for the recomputed `state_id`, so that I and others can reproduce any cited figure exactly.
97. As the researcher, I want a banner when the loaded Build is a test Build or was made with parse errors allowed, so that I never mistake such a Build for a publishable one.

### Reader of results (non-specialist) and reviewer

98. As a reader without network-analysis training, I want a User Guide that opens with three rules (no number shows a cause; clusters carry no meaning; quote the `state_id` with every network number), so that I avoid the common misreadings from the start.
99. As a reader, I want each metric explained in prose with a worked example, its bounds and reference points (lift 1, phi 0, ARI 1 and ≈0, Q 0), and the project's own comparisons (null model, Seed-Noise Floor, Eligible Pool), followed by one "Exact definition" line, so that I can interpret values without published cut-offs.
100. As a reader, I want an appendix listing published rules of thumb (e.g. "Q > 0.3") and why they don't apply here, so that I'm not misled when I meet them in other papers.
101. As a reader, I want an alphabetical column index linking every exported column to its file, app panel, report section and guide entry, so that I can look up any number I see.
102. As a reader, I want one paragraph per output file saying what one row is, what it joins to and what it is for, so that I can use the files without reading code.
103. As a reader, I want every metric label and column header in the app to show its one-line description as a tooltip, and a `?` on each panel to open the matching guide section offline, so that help is where the number is.
104. As a reader, I want a single Known limitations chapter, so that every caveat is in one place.
105. As a reviewer, I want every export and Build to carry its provenance (Snapshot id, Build id, config hash, Source Substitutions, attribution, seeds, software versions, mode), so that I can check how each number was produced.
106. As a reviewer, I want the guide to cite only sources verified at page level, so that the citations hold up.
107. As a reviewer, I want the attribution "Player data: Steam Charts; tags/metadata: Steam store" on published outputs, so that the sources get proper credit.

### Person running the pipeline

108. As the person running the pipeline, I want a Running Guide covering install (uv, Python 3.14, compiled bytecode), configs, Collect, Build, the test Snapshot, the full-run gate, folder layouts, `--allow-parse-errors` and the Windows notes, so that I can operate the software without reading the code.
109. As the person running the pipeline, I want simple commands (`collect`, `collect <stage>`, `collect steamdb`, `collect --repair`, `build`, `app`), so that every operation is one command.
110. As the person running the pipeline, I want a non-zero exit with a logged reason on every hard stop, so that I know why a run stopped and that rerunning resumes it.

## Implementation Decisions

### Standing constraints (apply everywhere)

- Never fabricate data. Never bypass anti-bot protection. Respect source terms.
- A Source Substitution (any source other than Steam Charts and SteamDB) needs the researcher's explicit confirmation. Confirmed on 2026-10-03: the Steam store page (tags) and `appdetails` (details). A Manual Metadata Entry counts as confirmation for its own source and game.
- Missing Months stay missing. No zeros before release or for gaps.
- Exclusion rules and the Genre Tag list live in config files. Every excluded game records every matching reason.
- Manual filtering in the app never modifies source datasets.
- Frequency and correlation are never presented as causation. Clusters get no automatic semantic names.
- Reproducibility: fixed configurable seeds, with snapshot timestamps and config stored in every export.

### Package, runtime and dependencies

- One `uv`-managed package, `steamstudy`, in a `src/` layout, on **Python 3.14** (`requires-python = ">=3.14,<3.15"`). Python 3.14.8 passed every stack check. Exact versions are frozen in `uv.lock`.
- Subpackages and their dependency rules:
  - `collect`: network I/O only.
  - `build`: parsing, scoring, Manual Metadata, exclusion, ranking, reports.
  - `network`: graph build, clustering, metrics, centers, stability, Removal Sensitivity. Never imports UI code.
  - `analysis`: feature-analysis tables, report and templates.
  - `export`: the schema module (`steamstudy.export.schema`) and the validated writers that `build`, `analysis` and `app` use.
  - `app`: the Dash UI. Depends on `network`, never the reverse.
- Dependencies:
  - App stack: Dash 4 (`dash>=4.4,<5`), `dash-cytoscape==1.0.2` pinned exactly (unmaintained; bundles Cytoscape.js 3.28.1, which is what was tested), `dash-ag-grid>=35.3,<36`, `diskcache`, `multiprocess`, `psutil`.
  - Clustering: `networkx` (3.7), plus `leidenalg` and `python-igraph` as regular pinned dependencies, so every install offers both algorithms.
  - Numerics: numpy, scipy, scikit-learn (ARI, silhouette), pandas.
  - HTML parsing: lxml or selectolax.
  - Any upgrade of dash, dash-cytoscape or dash-ag-grid re-runs the Windows spike checklist first.
- Runtime rules (from the Python 3.14 spike on the researcher's Windows machine):
  - Install with compiled bytecode (`uv sync --compile-bytecode` or `UV_COMPILE_BYTECODE=1`). Nothing may set `PYTHONDONTWRITEBYTECODE`. Without bytecode, each background job's spawn grows from about 2.5 s to about 6.4 s.
  - Every file read and write passes an encoding explicitly: `encoding="utf-8"`, or `"utf-8-sig"` for CSV writes. The machine's locale is cp1251, and tag and game names are not ASCII-safe.
  - The app opens the browser at `http://127.0.0.1:<port>`, never `localhost` (≈300 ms extra per callback on Windows), and listens only on `127.0.0.1`.
  - Tests run with `-W default -X faulthandler`, not `-X dev`, which crashes this machine's interpreters at exit.

### Commands

- `steamstudy collect --mode test|full [--snapshot <id>]`: run every stage in order, resuming if the Snapshot exists. `steamstudy collect <stage>` runs one stage (`pool`, `history`, `store`, `taglist`).
- `steamstudy collect steamdb --build <id>`: the SteamDB cross-check batch for that Build's Top-100 members. Refuses without a permission reference.
- `steamstudy collect --repair <appid> --reason "…"`: refetch one app into a closed Snapshot, logged.
- `steamstudy build [--snapshot <id>] [--allow-parse-errors]`.
- `steamstudy app [--build <id>]`: default is the latest Build.
- A CLI path to clear the app cache, with the same effect as the app's "Clear app cache" button.

### Collect

**Sources and fields**

| Field | Source | Status |
|---|---|---|
| Monthly Avg. Players (and Peak) | Steam Charts `/app/{appid}` HTML table | named source |
| Candidate Pool | Steam Charts `/top/p.N` listing, 25 rows per page | named source |
| Displayed tag list (display order, tag id, name, votes) | Steam store page, `InitAppTagModal` | Source Substitution, confirmed |
| "Adult Only" notice | Steam store page | Source Substitution, confirmed |
| `type`, `name`, `is_free`, `genres[]`, `release_date`, `content_descriptors` | Steam store `appdetails`, `l=english` | Source Substitution, confirmed |
| Tag vocabulary | `IStoreService/GetTagList` (with `version_hash`) | Source Substitution, confirmed (part of the store) |
| Cross-check only | SteamDB | permission-gated, never enters a dataset |

SteamSpy and `IStoreBrowseService/GetItems` are not used.

**Stages**, strictly sequential, no overlap:

1. `pool`: N full listing passes (config, default 2, minimum 1). Each pass stops at the first 404 or empty page; here a 404 means the end of the listing, not a hard stop. Rows are unioned by AppID. The Build records each app's best `/top` rank across passes.
2. `history`: one Steam Charts app page per pool AppID.
3. `store`: store page plus `appdetails`, only for apps that have a score. "Has a score" is decided by the same `score()` function the Build uses.
4. `taglist`: `GetTagList`, fetched once when the store stage starts.

**`Fetcher` interface**: `Fetcher.fetch(request_key, url) -> StoredResponse` hides all request handling:
- per-source rate, and one kept-alive connection per source;
- User-Agent and age-check cookie;
- retries, challenge detection and the hard stop;
- writing the archive file and the request-log entry;
- skipping requests that already have a final outcome on resume.

There are two adapters: live HTTP, and a fixture-backed fake for tests.

**Politeness**
- Steam Charts: rate is a parameter, default 3 requests/s, sequential, one kept-alive connection, no parallelism. If the operator asks for a lower rate, it is lowered and the change is recorded.
- Steam store: rate is a parameter, default 1 request/2 s, one connection shared by store pages and `appdetails`, always `l=english`. No `cc=` parameter.
- SteamDB: follows the terms of the permission when granted; if the permission sets none, the store rule applies.
- Every source uses a descriptive User-Agent with contact details. No browser emulation, proxies or challenge solving.
- Age check: the standard logged-out age-check cookie, with a birth date 30 years before the collection date. Never log in. Nothing that needs a login is bypassed.

**Retry and stop policy** (every number in `collection.toml`)

| Situation | Action |
|---|---|
| 403, 429, 503, a challenge page (Cloudflare markers, or the expected structural marker missing) | Hard stop: save, log, exit non-zero. No automatic retry. |
| 5 parse-structure failures in a row | Hard stop |
| Timeout (connect 10 s / read 30 s), connection reset, other 5xx | Retry after 10 s, 30 s, 90 s; then hard stop |
| `/top` page 404 or empty | End of that listing pass |
| Steam Charts app page 404 | Final outcome `not_found` (unscored) |
| Store page redirects to the home page or to a page with no app | Final outcome `no_store_page` → `store_data_unavailable` |
| Age check still shown after the cookie | Final outcome `age_gate`, flagged for review; no workaround |
| `appdetails` returns `success: false` | Final outcome `no_appdetails` |

**Snapshot layout** (`snapshots/<snapshot_id>/`)
- `raw/`: one gzipped file per response:
  - `steamcharts/top/pass-<n>/p-<NNNN>.html.gz`
  - `steamcharts/app/<appid>.html.gz`
  - `store/page/<appid>.html.gz`
  - `store/appdetails/<appid>.json.gz`
  - `steam_api/GetTagList.json`
  - `steamdb/…`
- `requests.sqlite`: the request log and checkpoint. Each entry holds the URL, status, final URL after redirects, timestamp, sha256 and outcome.
- `snapshot.json` (exact key names are left to implementation):
  - id, mode (`test` / `full`), collection date and Observation Window;
  - per-stage and per-pass start/end times, row counts and one-pass-only AppID counts;
  - request rates actually used, with any change;
  - User-Agent, age-check birth date, store-reported country;
  - `GetTagList` `version_hash`;
  - `collection_config_hash`;
  - operator-reply and ethics-check references;
  - SteamDB permission reference and cross-check batches;
  - repairs;
  - software versions.
- Resume means rerunning the same command. Requests with a final outcome are skipped. Retryable errors and hard-stopped requests are fetched again.
- After collection the Snapshot is closed. The only later changes are `--repair` and SteamDB batches, both logged.

**Test Snapshot** (`--mode test`): the first 4 `/top` pages of one pass (100 apps), plus the edge-case AppIDs listed in `collection.toml`. Known cases:

| Case | App |
|---|---|
| leading Placeholder Row | Scorn 698670 |
| no month rows | Black Hole Simulator 1401150 |
| interior Placeholder Row | Bold Blade 749110 |
| tiny pre-launch rows; Dating Sim farming game | Stardew Valley 413150 |
| Early Access gap between Release Month and store date | Baldur's Gate 3 1086940 |
| only `Last 30 Days` | Dadish 3D 2888870 |
| Desktop Companion; also a Software tag | Bongo Cat 3419430 |
| Dating Sim joke vote; `manual_exclusion` candidate | Banana 2923300 |

Still to pick from the research notes when the code is written: a delisted game (MultiVersus 1818750 is a candidate; confirm it has no store page), a region-locked or login-only app, an Adult Only game, a free-to-play game and a software app. The test Snapshot is built in full. `build.json` and the app banner show `mode: test`. Parser tests run offline on fixtures saved from it.

**Full-run gate**: `--mode full` refuses to start unless `collection.toml` records the Steam Charts operator's reply and the ethics-office check (reference and date for each). Both are copied into `snapshot.json`.

**SteamDB cross-check**: built in v1 and disabled by default. It runs only when `collection.toml` holds a permission reference. It fetches pages only for one Build's Top-100 members, as its own logged batch. The next Build adds `steamdb_crosscheck.csv` (store vs SteamDB tags per game). Until permission is granted it is tested only against pages saved by hand from a browser.

### Pre-run checklist (one-time project obligations, not product features)

1. Contact the Steam Charts operator (Twitter @steamcharts or james4k.com). Ask about an acceptable request rate and whether `monthly_players.csv` may be published. The test Snapshot may run now. The full Steam Charts run waits for the reply, and stops if the operator objects.
2. Ask the institution's ethics / research-integrity office about the Steam Subscriber Agreement "Automation" clause, and record the check. The case in favour: logged out, public pages, academic use.
3. Send the SteamDB academic-permission email (university address plus a project overview, as SteamDB's FAQ requires). It also asks whether publishing the Top-100 exports is acceptable.

Items 1 and 2 are enforced by the full-run gate. The Running Guide links to this checklist. It does not restate it, because people reusing the software will have different obligations.

### Config (TOML files in `config/`)

- `collection.toml`:
  - rates, listing passes, User-Agent contact, timeouts and retry schedule;
  - test-mode edge-case AppIDs;
  - SteamDB permission reference;
  - operator reply and ethics check (reference and date for each);
  - the operator's answer on publishing `monthly_players.csv`.
- `exclusions.toml`:
  - rules and tag lists (tag id plus name);
  - the global rank limit (default 20) and per-tag limits;
  - `allowed_app_types = ["game"]`;
  - `content_flags`.
- `genres.toml`: the Genre Tag list and the store-genre `kind` map.
- `datasets.toml`: one entry per dataset. `overall` has no defining tag. The others each have a defining tag id, checked against the `GetTagList` snapshot.
- `network.toml`: the shared network defaults, read by both the app and the report:
  - `min_games_per_tag` 8, `min_shared_games` 8, `min_months` 0;
  - Genre Tags hidden, defining tag hidden, isolated tags kept;
  - `clustering_weight = "shared_games"`, `algorithm = "louvain"`, `resolution = 1.0`;
  - `seed` (a fixed integer), `null_replicates = 20`, `noise_seeds = 10`;
  - `resolution_sweep = [0.50, 0.75, 1.00, 1.25, 1.50]`.

  Validation requires `noise_seeds ≥ 2` and `null_replicates ≥ 2`.
- `analysis.toml`: `max_itemset_size` (3), `min_support` (10), the causal-word list (*drives, leads to, makes … successful, key to success, predicts, because, effect*), and the `release_month_check` threshold in months (3).
- Researcher-maintained lists: `manual_metadata.toml`, `manual_exclusions.toml`, `exclusion_overrides.toml`. All ship empty.
- `CHANGELOG.md`: every config change with its rationale.
- Two hashes over the parsed, normalised contents:
  - `collection_config_hash`, stored in the Snapshot;
  - `build_config_hash`, over every file a Build reads, stored in `build.json`.

  Collection settings never change dataset output.

### Build

**Interface**: `build(snapshot, config) -> BuildResult` is pure. Its only inputs are a read-only `Snapshot` (`response(key)`, `meta`) and the config, and it never contacts a source. A separate writer lays out the Build folder. Parsers are pure functions from a stored response to a typed record:
- `parse_top_page`;
- `parse_steamcharts_app -> MonthlyHistory`;
- `parse_store_page -> tags + Adult Only notice`;
- `parse_appdetails`;
- `parse_tag_list`.

**Row parsing (Steam Charts)**
- Only rows labelled `<English month name> <YYYY>` are months.
- `Last 30 Days` is always skipped, without comment.
- Rows for months after the Observation Window's last month are ignored. That is not an error.
- Unknown labels and duplicate months go to `parse_errors.csv`.

**Scoring**: `score(history, window) -> Score` is the single scoring function. The Collect store stage uses it too.
- A Placeholder Row (Avg `0.00` **and** Peak `0`, at any position) is treated exactly like an omitted row. A row with Avg `0.00` and Peak ≥ 1 is data. There are no other thresholds.
- Release Month is the first month with a row that is not a Placeholder Row.
- Mean Monthly Players is the mean of Monthly Avg. Players over the months from the Release Month on that have a value and fall inside the Observation Window. `months_observed` is the count of those months.
- An app with no such month is unscored. That is not an Exclusion. `completeness.csv` splits the unscored apps three ways: no month rows; only Placeholder Rows; month rows, but none in the window.

**Manual Metadata Entry** (`manual_metadata.toml`)
- Every field is `{value, source_url, retrieved}`. A field without a source is rejected.
- A full entry requires tags (tag id plus name, in display order), `app_type`, store genres, `is_free`, release date and `adult_only`. Such games are flagged `metadata_source = manual`.
- A tags-only entry is allowed only for a `no_tags` game. Its other fields come from the store, and the game is flagged `manual_tags`.
- An entry for an app the store does provide fails the Build.
- Entries are applied after store parsing, before exclusion. The game then goes through the normal rules. Citations are copied to `manual_metadata.csv`, and the entries used are recorded in `build.json`.

**Exclusion rules**: evaluated in this order. Every matching reason is recorded with its detail, and `primary_reason` is the first match. The first two short-circuit, because without store data nothing else can be checked. Counts are reported both overlapping and partitioned by primary reason.

| Reason code | Default config |
|---|---|
| `store_data_unavailable` | No store data and no Manual Metadata Entry |
| `app_type` | Allowed types `["game"]`. Detail = the actual type. |
| `no_tags` | Store page exists, no tags displayed (and no tags-only entry) |
| `adult_content` | The store page shows the "marked as 'Adult Only'" notice, **or** `appdetails.content_descriptors` contains id 3, **or** tag `Hentai` (9130) within its rank limit. Detail records which signals fired. |
| `software_tag` | `Software` 8013, `Utilities` 87, `Animation & Modeling` 872, `Audio Production` 1027, `Design & Illustration` 84, `Photo Editing` 809, `Video Production` 784, `Software Training` 1445, `Benchmark` 5407. Name-only entries `GameMaker`, `RPGMaker` and `Web Publishing` apply only if seen. |
| `dating_sim_tag` | `Dating Sim` 9551 only |
| `manual` | The `manual_exclusion` list |

- Tags are matched on tag id against the `GetTagList` snapshot. Names are labels only. A configured tag id missing from the snapshot gives a warning, not a failure.
- Rank limit: one global setting, default "anywhere in the displayed 20", plus optional tighter per-tag limits. `Dating Sim` ships on the global default. "Has tag" for datasets and the network is always "anywhere in the 20", whatever the limits.
- Never exclusion grounds: `Sexual Content`, `Nudity`, `Sexual Themes`, maturity tags (Mature, Gore, Violent, Blood), `Romance`, `Otome`, `Education`, `Game Development`, `Programming`, `Coding`, `Gaming`.
- `manual_exclusion` entries: AppID, name, written reason, at least one evidence URL with a retrieval date, date added.
- `exclusion_override` entries: the same fields plus the rule being overridden. An override cancels that rule for that game. Overrides are published.

**Content Flags** (`content_flags`): matched anywhere in the 20 tags. They never filter, are exported per game and are counted in the feature analysis.
- `desktop_companion`: `Desktop Companion` 1320952.
- `sexual_content_tag`: `Sexual Content` 12095, `Nudity` 6650, `Sexual Themes` 40500, `NSFW` (name-only).

**Genre Tags** (network hide/show): the 11 Top-Level Genres `Action`, `Adventure`, `Casual`, `Experimental`, `Puzzle`, `Racing`, `RPG`, `Simulation`, `Sports`, `Strategy`, `Tabletop`. The researcher can extend the list in config.

**Datasets and ranking**
- One Build always produces all five datasets from one shared set of scored, non-excluded games. `build --dataset` only limits what is printed.
- The Eligible Pool is all such games for Overall, and those that have the defining tag for a Tag-Specific Dataset.
- Ranking: `mean_monthly_players` descending, then `months_observed` descending, then `appid` ascending. Always exactly 100 rows. Games outside the top 100 whose score equals rank 100's go to `ties.csv`.
- Free-to-play games are included and flagged `is_free`.

**Build folder**: `builds/<snapshot_id>/<build_id>/`, with `build_id` = UTC timestamp + the first 8 characters of `build_config_hash`. A Build never overwrites another, and `latest` points to the newest.

- `datasets/`:
  - `top100_<dataset>.csv` × 5;
  - `monthly_players.csv`: one row per AppID and month (avg, peak) for every game in any Top-100 Dataset. Placeholder Rows are never included. Always written, but **not published** until the Steam Charts operator agrees;
  - `build.json`.
- `reports/`:
  - `exclusions.csv`: one row per (AppID, matched reason), with detail, `primary_reason`, and would-be rank per dataset (the rank the game would have taken in that dataset had it not been excluded). This file also serves as the "would have scored inside a Top 100" report;
  - `completeness.csv`;
  - `impact_*.csv`: removals per rule and per tag or signal, with would-be ranks; near-misses (exclusion tags present beyond their rank limit); Adult Only vs descriptor 3 disagreements; Top-100 games no rule excluded that carry descriptor 1 or 4, a software store genre or a Content Flag;
  - `ties.csv`;
  - `parse_errors.csv`;
  - `placeholder_rows.csv`: `appid, month, position` (`leading` / `interior` / `trailing`) for every Placeholder Row in the Candidate Pool, with the count added to `completeness.csv`;
  - `release_month_check.csv`: a diagnostic only, never a rule. Lists Top-100 games where |`months_apart`| exceeds the configured threshold. Columns: `appid, release_month, store_release_date, months_apart`. `months_apart` = (year × 12 + month) of the store date minus the same for the Release Month, so a positive value means the store date is later. It is empty when the store date can't be parsed;
  - `tag_vocabulary.csv`: every distinct `(tagid, name)` and `(genre id, description)` seen, with app counts;
  - `manual_metadata.csv`;
  - `steamdb_crosscheck.csv`, when SteamDB batches exist;
  - `reports.html`: a summary rendered from Markdown templates, under the same causal-word test as the feature-analysis report.
- `analysis/`: the feature-analysis and network outputs (see Export schemas).
- `app_cache/`: the app's Removal Sensitivity cache (git-ignored, regenerable).

**`top100_<dataset>.csv`** (the app's loading contract): UTF-8 with BOM, one row per game, sorted by rank.

| Column | Note |
|---|---|
| `dataset`, `rank` | |
| `appid`, `name` | |
| `mean_monthly_players` | 6 decimals, so the rank can be reproduced |
| `months_observed`, `release_month` | `release_month` as `YYYY-MM` |
| `store_release_date` | as given by the store; metadata only |
| `is_free`, `app_type` | |
| `tag_ids`, `tags` | display order, `;`-separated, matching lists. The Build fails if a name contains `;`. |
| `genre_ids`, `genres` | same convention |
| `content_flags` | `;`-separated codes |
| `metadata_source` | `store` / `manual` / `manual_tags` |
| `top_listing_rank` | best `/top` rank across passes |

Tag votes and the monthly series are not in this file.

**`build.json`**:
- Snapshot id and `build_id`;
- `build_config_hash`, plus a copy of the full parsed config and the `CHANGELOG.md` entries up to the Build;
- Source Substitutions used (store page plus `appdetails`, confirmed 2026-10-03);
- the attribution line "Player data: Steam Charts; tags/metadata: Steam store";
- seed and network defaults;
- software versions;
- `mode` and `parse_errors_allowed` (with the count);
- the Manual Metadata Entries used.

CSVs carry no repeated header or metadata rows.

**Parse failures**: any entry in `parse_errors.csv` fails the Build. `--allow-parse-errors` treats those apps as unscored or `store_data_unavailable` and sets `parse_errors_allowed: true` with the count. The app then shows a warning banner. A published Build never has this flag set.

**Publication**: only the derived Top-100 exports, reports and analysis are published. Raw responses and full Candidate Pool data are never published, and `monthly_players.csv` waits for the operator's agreement.

### Network (`steamstudy.network`, shared by the app and the Build)

**Interface**: one pure computation from the loaded dataset rows and the Network State settings to a complete Network State result. It covers the network, clustering, null model, Seed-Noise Floor, silhouette, metrics, centers, Membership Stability and global positions. The app and the feature-analysis report both call it. Removal Sensitivity is a separate entry point over the same state, and so is the Resolution Sweep (Build only).

**Network State key**: canonical JSON (sorted keys, no whitespace) → SHA-256. `state_id` is the first 12 hex characters. Exports store both the full JSON and the `state_id`. Fields:

```
build_id, dataset, min_months, min_games_per_tag, min_shared_games,
hidden_tag_ids   (Genre Tags + defining tag, sorted),
removed_tag_ids  (sorted; separate from hidden because each gets its own "not in network" reason),
clustering_weight, algorithm,
resolution       (fixed 2-decimal string, "1.00"),
seed, null_replicates, noise_seeds,
key_version      (bumped whenever a method or code change would alter results)
```

The layout mode and the isolated-tags policy (always kept) are not part of the key. The same key always gives the same result.

**Network build**
- Games: the loaded Top-100 Dataset after the Minimum Months Filter, which drops games with `months_observed` below the threshold and never re-ranks or backfills. N is the number of these games.
- Nodes: tags with at least `min_games_per_tag` games, excluding hidden and removed tags.
- Edges: pairs of nodes with shared-game count ≥ `min_shared_games`. The edge weight is always the shared-game count. It drives the thresholds, edge thickness and the edge inspector.
- Isolated tags (enough games, but no edge that qualifies) stay as One-Tag Clusters.
- Every tag on at least one game that is not a node goes to "Not in network" with all its reasons, in the fixed order `removed;defining_tag_hidden;genre_tag_hidden;below_min_games`.
- Edge games are the intersection of the two tags' game sets over dataset + filter. They are computed on demand (on click in the app) and written out in full in exports.

**Clustering Weight**
- `shared_games` (default): the edge weight itself.
- `lift`: `shared · N / (n_i · n_j)`, with `n_i` = games having tag i among the N games. Edges with lift < 1 that pass the shared-games threshold are kept with weight = lift, so both modes cluster the same edge set.
- Hiding or removing tags changes neither N nor any remaining edge's lift. At Minimum Months Filter 0, an edge's lift equals the pair's lift in `associations.csv`.
- Follows the mode: community detection, every graph quality metric (Q and its null model, coverage, inter-cluster share, conductance, weighted density, cut weight), `within_z`, `participation`, `top_strength_tag`, the global layout, the Seed-Noise Floor and Removal Sensitivity.
- Does not follow the mode: thresholds, edge thickness, the edge inspector, every Jaccard game-set measure (silhouette, medoid, Membership Stability), and degrees.

**Clustering algorithm**
- `louvain` (default): NetworkX `louvain_communities(weight=<active Clustering Weight>, resolution=γ, seed=seed, threshold=1e-7)`, taking the final (highest-modularity) level.
- `leiden` (optional): `leidenalg.find_partition(g, RBConfigurationVertexPartition, weights=<active Clustering Weight>, resolution_parameter=γ, n_iterations=-1, seed=seed)`. This is modularity with γ, run until stable. CPM is never used.
- Determinism: graphs are built in canonical order (nodes sorted, edges sorted by (u, v)) and library versions are pinned. Algorithm, γ, seed, `clustering_weight` and the versions of both libraries are stored in every export and in `build.json`.
- Disconnected Louvain clusters are flagged `connected = false` and never split. The count appears in the Cluster-quality row, the inspector and Analysis Report mode show a warning that suggests the Leiden mode, and the methods section reports how many the report's runs produced.
- γ: config default 1.0. In the app, a numeric input from 0.1 to 3.0, step 0.05. Q is always reported at the γ that was optimised ("Q (γ = 1.00)"), never at a second γ.

**Cluster labels**: `C1…` by size descending, ties broken by the smallest member `tag_id`. Multi-Tag Clusters come first, then One-Tag Clusters ordered by `tag_id`. Clusters are never named.

**Silhouette**: Jaccard distance on game sets only, d(u,v) = 1 − |G_u ∩ G_v| / |G_u ∪ G_v|, with G_t over the N games.
- Independent of the Clustering Weight and the algorithm. `sample_size=None`. There is no graph-distance silhouette.
- Computed on the full partition: One-Tag Clusters count as "other clusters" for b(i), but their own s = 0 is left out of every mean.
- Reported per node (blank for One-Tag Clusters), per cluster, and overall as the mean over Multi-Tag Cluster members.
- n/a with a reason when there are fewer than 2 Multi-Tag Clusters.
- Labelled "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion".

**Global metrics** (one Cluster-quality row per state)
- Q at γ, with `modularity_status = no_edges` when total weight is 0. Computed over the whole network; isolated tags contribute 0.
- Null-model baseline:
  - Method: a bipartite game–tag shuffle (curveball / swap randomisation) over the same games and visible tags, preserving each game's tag count and each tag's game count. Each replicate rebuilds the network with the same thresholds and reclusters it with the same algorithm, γ and Clustering Weight. R = `null_replicates` (default 20). Replicate seeds come from the main seed through their own stream.
  - Reported: `q_null_mean`, `q_null_sd` (sample SD), `modularity_z` = (Q − mean)/sd (n/a when sd = 0), `q_excess` = Q − `q_null_mean`, and `null_n_edges_mean` beside the real `n_edges`.
  - Headline display: "Q 0.42 vs null 0.31 ± 0.01 (excess 0.11, z 11; null networks average 640 edges vs 702)". `modularity_z` is never shown alone.
  - Computed synchronously in every recompute.
- Weighted coverage (intra-cluster weight / total weight) and `inter_cluster_weight_share` (1 − coverage).
- Cluster counts, always as "k multi-tag + s one-tag", plus `n_disconnected_clusters`.
- Mean silhouette.
- Seed-Noise Floor values (below).
- Not used: `nx.community.partition_quality` (it ignores weights), "performance".

**Per-cluster metrics**:
- `size`, `internal_edges`, `internal_weight`.
- `edge_density` (unweighted internal edges / (n(n−1)/2)) and `weighted_density` (internal weight / (n(n−1)/2)). Both are empty for size 1.
- `cut_weight`.
- `conductance` = cut(C) / min(vol(C), vol(rest)), computed in our own code rather than with NetworkX, which raises at vol(C) = 0. A connected One-Tag Cluster gives 1.0. When it is undefined, `conductance_status` is `isolated_tag` (vol(C) = 0) or `no_edges_outside_cluster` (vol(rest) = 0).
- Mean silhouette, `connected`, `mean_membership_stability`.
- The center fields (below).

**Inter-cluster connectivity**: edge count and summed weight for every unordered pair of Multi-Tag Clusters, including zero-edge pairs. One-Tag Clusters are pooled as the pseudo-cluster `one_tag_pool`.

**Cluster Center**: the Jaccard medoid. Each member's `medoid_score` is its mean Jaccard distance to the other members, and the center is the member with the smallest score.
- Ties: scores are compared rounded to 12 decimals; then more `n_games` wins; then the lower `tag_id`.
- Only clusters of 3+ tags get a center. For one-tag and two-tag clusters, `center_status` is `one_tag_cluster` or `two_tag_cluster`, and there is no ◆. Both members of a two-tag cluster still get a `medoid_score`.
- Independent of the Clustering Weight and the algorithm for a given partition. Works on disconnected clusters.
- `top_strength_tag` is the member with the highest intra-cluster strength on the active Clustering Weight, with the same tie-break and the same n/a rule. `center_is_top_strength` compares the two.

**Per-node metrics**:
- `n_games`, `is_isolated`, `degree`, `degree_intra`.
- `strength_shared`, `strength_lift`, `strength_shared_intra`, `strength_lift_intra`. All four are always computed; the active mode's value is shown first.
- `silhouette`.
- `medoid_score`, `is_center`.
- `within_z`: the Guimerà–Amaral within-module degree z-score on the active weight, using the population SD (ddof = 0). Multi-Tag Clusters only. n/a for One-Tag Clusters, and when every member has the same intra-cluster strength. Its cap for an n-tag cluster is √(n−1), which is derivable from the cluster size.
- `participation` = 1 − Σ_s (k_is / k_i)² on the active weight, with s over every cluster including One-Tag Clusters. n/a at zero strength.
- `membership_stability`.
- Not computed: betweenness, closeness, eigenvector, PageRank. The Guimerà–Amaral role regions and the word "hub" are not used.

**Seed-Noise Floor** (part of every Network State, computed synchronously in every recompute)
- K = `noise_seeds` (default 10, config only). The noise seeds come from the main seed through a stream separate from the null-model replicate seeds, so the two sets never share a seed.
- Each noise seed runs the same clustering on the unchanged network: same algorithm, γ and Clustering Weight. Each is compared with the main partition, never with other seeds.
- Values:
  - `seed_ari_min`, `seed_ari_mean`: ARI of each seed's partition against the main one (`sklearn.metrics.adjusted_rand_score`);
  - `seed_modularity_sd` (sample SD);
  - `seed_silhouette_sd` (sample SD over the seeds that have a silhouette), with `seed_silhouette_status = fewer_than_2_seeds_with_silhouette` when fewer than 2 do;
  - `seed_k_min`, `seed_k_max`: the range of Multi-Tag Cluster counts.
- A network with no edges gives every seed the same partition, so every ARI is 1.
- Display: "Seed-noise floor (K = 10): ARI vs. main min 0.84, mean 0.93 · multi-tag clusters 5–7 · SD Q 0.004 · SD silhouette 0.01". Numbers only: no stable/unstable labels, colours or thresholds.

**Membership Stability**
- For tag v: the mean over the K seeds of |A ∩ B| / |A ∪ B|, where A is v's cluster in the main partition and B is v's cluster in seed s. Both sets include v.
- Empty for every tag with `degree = 0`, and `mean_membership_stability` is empty for their One-Tag Clusters. A connected tag the algorithm left alone keeps its value.
- Per cluster: the mean over its members. Empty values sort last.
- Descriptive only.

**Removal Sensitivity** (a what-if; it never changes the app state)
- For each tested tag v, two readings, compared with the current state over the shared tag set (all tags except v):
  - **Reclustered** (`rc_*`): drop v and its edges, then recluster from scratch (cold restart, no warm start) with the main seed and the active algorithm, γ and Clustering Weight. Columns: `rc_delta_modularity`, `rc_silhouette_after` / status, `rc_delta_silhouette`, `rc_delta_k` (multi-tag clusters), `rc_delta_s` (one-tag clusters), `rc_ari` against the current partition, and `rc_centers_lost` (current Cluster Centers other than v that are no longer centers).
  - **Fixed partition** (`fp_*`): drop v, keep every other tag in its cluster, and recompute Q and silhouette. Deterministic. Columns: `fp_delta_modularity`, `fp_silhouette_after` / status, `fp_delta_silhouette`.
- Every Δ is after − before. A silhouette that switches between a value and n/a leaves the Δ empty; the UI shows "0.21 → n/a" with the reason.
- ΔQ carries the caveat that it also reflects the lost edge weight.
- Not recomputed per removal: the null model, per-cluster metrics, layout.
- Flag: `rc_ari_beyond_noise` = `rc_ari` < `seed_ari_min`, on ARI only. ΔQ and Δsilhouette are plain numbers shown beside `seed_modularity_sd` / `seed_silhouette_sd`, with no flag. When `seed_ari_min` = 1, any removal that moves a tag is flagged.
  - Labelled "screening flag, not a significance test".
  - Shown with the expected chance count: "7 of 50 tags flagged; if removals acted only like another seed, at most about 5 would be (n / (K + 1))".
- It reads the standing Seed-Noise Floor and never computes its own.
- Scope:
  - "Run" covers every visible tag, including One-Tag Clusters. "Run for this tag" covers one.
  - There is no node cap. Before a run starts, an estimate is shown: n × the measured time of the current clustering.
  - Run order: active strength descending, then `tag_id`, so a partial result is a prefix of the full one.
  - No multiprocessing in v1.
- Cache key: the Network State key plus a method-version string.

**Global positions**: a pure function of (dataset, Minimum Months Filter, Clustering Weight, seed). They come from a weighted, seeded `networkx.spring_layout` on the active Clustering Weight, run at the loosest thresholds, so thresholds don't move the graph. Recomputed on each change, not cached.

**Cluster-separated positions**: computed from the elements alone (each node's cluster plus its global position).
- Each Multi-Tag Cluster is laid out from its intra-cluster edges, seeded from the global positions.
- The cluster boxes are packed side by side as labelled, tinted regions ("C1 · 14 tags").
- One-Tag Clusters share one grid region at the end.
- Inter-cluster edges are drawn faint.
- The layout never reclusters.

### Feature analysis (`steamstudy.analysis`, Build only)

- **Input**: each full Top-100 Dataset (no Minimum Months Filter). Each game counts once, with no weighting by score.
- **Tag scope**: all tags are treated alike. `archived_category`, the category from the archived Steamworks table (empty for tags with none), is an information column only.
- **Defining tag**: in the tag-frequency table at 100% with `defining_tag = true`. Left out of combinations, associations, clusters, the Resolution Sweep and the Build's Removal Sensitivity.
- **Baseline**: the share in the Eligible Pool (Top 100 included), for tags and genres only. The tables print the Eligible Pool size, so the `share_ratio` ceiling (pool size / 100) is visible.
- **Tables** (tidy CSVs, five datasets stacked, `dataset` first):
  - Tag frequency: every tag on at least one game. Sorted by count descending, ties by name. `median_position` is the median position in the store tag list among the games that have the tag.
  - Genre frequency: every store-genre value with its id and `kind`. Sorted by count descending. Headline sentences use `kind = genre` rows only. The Puzzle dataset gets an automatic note that Puzzle is not a store genre.
  - Combinations: itemsets of size 2…`max_itemset_size` with support ≥ `min_support`.
    - Support count and share.
    - `lift` = `support_count` × N^(k−1) / (product of the member tags' counts), with N = 100 and k = the itemset size. This equals the pair formula at k = 2.
    - Pairs also get confidence in both directions.
    - A triple is dropped when its support equals one of its sub-pairs'. Every sub-pair of a listed triple is also listed.
    - No baseline columns. Sorted by support descending.
  - Associations: every pair of tags that each reach `min_support`, including pairs with zero co-occurrence.
    - Measures: phi (primary), lift, Jaccard, two-sided Fisher exact `p`, and Benjamini–Hochberg `q` within each dataset. There is no "significant" column.
    - phi is empty when either tag is on all 100 games. That row stays, with lift 1, Jaccard defined, and Fisher p = 1 kept in the BH family.
    - Sorted by |phi| descending, empty last.
  - Content Flags: per flag, the count and the flagged games (AppID, name, rank).
  - Network tables: the Network State at the report's settings (shared defaults, defining tag out, config algorithm / γ / seed / Clustering Weight), written by the same writer as the app export.
  - Removal Sensitivity: a complete table per dataset at the report's settings.
  - Resolution Sweep, one row per dataset × γ:
    - The grid comes from config. The Build adds the config γ if the grid lacks it, so the report's own partition is always a row.
    - Everything is held at the report's settings, so the node set is identical across γ.
    - Columns: cluster counts, modularity at that γ (not comparable across rows), mean silhouette / status, `ari_vs_report`, and `seed_ari_min` / `seed_ari_mean` at that γ.
    - No null model per γ, no centers, no per-tag rows.
- **Report** (`report.html`, rendered from Markdown templates; one section per dataset; every number comes from the CSVs):
  - Opens with a standard caveat paragraph. q-values are described as a descriptive screen ("co-occurrence unlikely under independence within this dataset"), not evidence about Steam in general, because the Top 100 is not a random sample. Templates never mention significance.
  - Per dataset:
    - the `months_observed` distribution and the `is_free` count;
    - templated frequency sentences (e.g. "appears in 63 of the 100 games (Eligible Pool: 21%)", "co-occurs with … in 34 games");
    - the Content Flag counts;
    - the cluster list (labels, members, `center`, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength`);
    - the Q-vs-null line;
    - the stability sentence (e.g. "Across 10 other random seeds, agreement with the reported partition (ARI) ranged from 0.84 to 1.00 (mean 0.93), and the number of multi-tag clusters from 5 to 7."), followed by the bottom-5 Membership Stability tags (or every tag below 1.0 if fewer than 5 are), with no cut-off;
    - the Resolution Sweep sentence (e.g. "Between γ = 0.50 and 1.50 the number of multi-tag clusters ranged from 3 to 9; agreement with the γ = 1.00 partition ranged from 0.61 to 1.00 (ARI)."), never comparing Q across γ in prose;
    - the Removal Sensitivity sentence: how many tags are beyond noise and which, with the expected-chance wording.
  - A methods section assembled from the decided paragraphs. It covers:
    - Louvain by default, Leiden (modularity objective) as the alternative;
    - the game–tag shuffle null model;
    - Jaccard silhouette as a descriptive diagnostic over Multi-Tag Clusters;
    - shared-games edges, with lift as the optional Clustering Weight;
    - Jaccard-medoid centers and the tie rule, with `top_strength_tag` beside them;
    - Removal Sensitivity, with both readings and the screening flag;
    - seed repeats and Membership Stability;
    - the Resolution Sweep;
    - the count of disconnected clusters;
    - the statement that no consensus partition was computed.
  - It ends with a fixed limitations paragraph (not generated from the guide) that links to User Guide chapter 6. The paragraph says: tags are a current snapshot, not historical; the Top 100 is a ranked selection, not a sample; the partition comes from a single clustering run; Steam Charts has coverage gaps.
  - **Causal-word test**: the Build fails if the rendered report contains any word from the configured list. The same test applies to `reports.html`.

### Export schemas (`steamstudy.export.schema`)

**Single source**: one module declares every file, column, type and one-line description (units, convention, what n/a means). Each column declaration also carries:
- `guide_entry`: an anchor in User Guide chapter 3;
- `app_panel`;
- `report_section`.

Every writer validates against the schema. Writing an undeclared column or omitting a declared one is an error. `export.json` and `analysis.json` each embed a `columns` block generated from the schema. Adding, removing or renaming a column bumps `schema_version`, an integer separate from `key_version`. The overrides from tickets 25, 27 and 28 share one bump. Nothing has been published under an earlier schema.

**Conventions** (all app and Build CSVs)
- UTF-8 with BOM, comma-delimited, `\n` line endings, written with an explicit `encoding="utf-8-sig"`. No metadata rows.
- Ids: `tag_id` / `tag_ids` everywhere. Every tag column is an id + name pair (`tag_id` + `tag`). Clusters are given by their `C1…` label.
- Lists are `;`-separated, as matching id and name lists. Edge AppID lists hold AppIDs only, in dataset rank order.
- Booleans are `true` / `false`.
- Floats use the shortest round-trip `repr`, so app and Build values compare exactly. `mean_monthly_players` keeps its 6 decimals.
- n/a is an empty cell. A `<metric>_status` column gives the reason only where the cause varies:
  - `silhouette_status` (also `rc_`/`fp_silhouette_after_status`): `fewer_than_2_multi_tag_clusters`, `one_tag_cluster`;
  - `center_status`: `one_tag_cluster`, `two_tag_cluster`;
  - `modularity_status`: `no_edges`;
  - `conductance_status`: `isolated_tag`, `no_edges_outside_cluster`;
  - `seed_silhouette_status`: `fewer_than_2_seeds_with_silhouette`.
- Fixed-cause n/a values are left empty with no status column; their cause is derivable from other columns:
  - `within_z`;
  - `modularity_z` at sd 0;
  - `participation` at zero strength;
  - densities at size 1;
  - phi at count 100;
  - Membership Stability at degree 0.
- Weighted values without a `_shared` / `_lift` suffix are on the active Clustering Weight.

**App export**: "Export this state" (Workbench export area; Analysis Report mode section 7) downloads `steamstudy_<dataset>_<state_id>_<UTC timestamp>.zip`. There are no loose per-table files, nothing is written into the Build folder, and there is no `network.json` or GraphML.

| File | Rows | Columns (in order) |
|---|---|---|
| `nodes.csv` | one per node; sorted by cluster, `medoid_score`, `tag_id` | `tag_id, tag, cluster, n_games, is_isolated, degree, degree_intra, strength_shared, strength_lift, strength_shared_intra, strength_lift_intra, silhouette, silhouette_status, medoid_score, is_center, within_z, participation, membership_stability, x_global, y_global, x_cluster_separated, y_cluster_separated` (Cluster-separated positions are always computed for export) |
| `edges.csv` | one per edge; sorted by source, target, with source < target | `source_tag_id, source_tag, target_tag_id, target_tag, shared_games, lift, source_cluster, target_cluster, is_intra_cluster, appids` |
| `clusters.csv` | one per cluster; sorted by label | `cluster, kind (multi_tag/one_tag), size, member_tag_ids, members` (by `medoid_score`, then the center tie-break), `connected, internal_edges, internal_weight, edge_density, weighted_density, cut_weight, conductance, conductance_status, mean_silhouette, silhouette_status, center_tag_id, center, center_medoid_score, center_status, top_strength_tag_id, top_strength_tag, center_is_top_strength, mean_membership_stability` |
| `cluster_quality.csv` | one row | `n_dataset_games, n_nodes, n_edges, total_weight, modularity, modularity_status, q_null_mean, q_null_sd, modularity_z, q_excess, null_n_edges_mean, coverage, inter_cluster_weight_share, n_multi_tag_clusters, n_one_tag_clusters, n_disconnected_clusters, mean_silhouette, silhouette_status, seed_ari_min, seed_ari_mean, seed_modularity_sd, seed_silhouette_sd, seed_silhouette_status, seed_k_min, seed_k_max` |
| `cluster_connections.csv` | every unordered pair of Multi-Tag Clusters, plus pairs with `one_tag_pool` | `cluster_a, cluster_b, edge_count, weight` |
| `null_model.csv` | one per replicate | `replicate, seed, modularity, n_edges` |
| `seed_noise.csv` | one per noise seed; always written | `noise_seed_index, seed, modularity, silhouette, silhouette_status, ari_vs_main, n_multi_tag_clusters, n_one_tag_clusters` |
| `not_in_network.csv` | one per tag on ≥1 game of the dataset that is not a node | `tag_id, tag, n_games` (after the filter; 0 if emptied), `reasons` |
| `removal_sensitivity.csv` | one per tested tag, in run order; **omitted** when not run for this exact key | `run_order, tag_id, tag, cluster, is_center, active_strength, rc_delta_modularity, rc_silhouette_after, rc_silhouette_after_status, rc_delta_silhouette, rc_delta_k, rc_delta_s, rc_ari, rc_centers_lost_tag_ids, rc_centers_lost, rc_ari_beyond_noise, fp_delta_modularity, fp_silhouette_after, fp_silhouette_after_status, fp_delta_silhouette` |
| `export.json` | metadata | see below |

`export.json` contains:
- `schema_version`, `state_key` (full canonical JSON), `state_id`, `layout_source`, `exported_at` and the app's software versions;
- a copy of the loaded Build's `build.json` provenance, so the zip stands alone;
- `files`, giving each file's row count and SHA-256;
- method constants: R and the replicate seeds, K and the noise seeds, the Removal Sensitivity method version, the center tie-break rule, the cluster-label rule, and `"silhouette": "jaccard_game_set"`;
- `removal_sensitivity`: `"not_run"`, or `partial` with `done` / `total`. Stale results belong to another key and are never exported;
- `columns`.

**Build `analysis/` folder**
- Feature-analysis tables (`dataset` first):
  - `tag_frequency.csv`: `tag_id, tag, count, share, median_position, defining_tag, baseline_count, baseline_share, share_ratio, archived_category`.
  - `genre_frequency.csv`: `genre_id, genre, kind, count, share, baseline_count, baseline_share, share_ratio`.
  - `combinations.csv`: `size, tag_ids, tags` (both sorted by `tag_id`), `support_count, support_share, lift, confidence_a_to_b, confidence_b_to_a` (the two confidences for pairs only).
  - `associations.csv`: `tag_id_a, tag_a, tag_id_b, tag_b` (a < b), `count_a, count_b, count_ab, phi, lift, jaccard, fisher_p, bh_q`.
  - `content_flags.csv` (long form, one row per dataset × flag × flagged game): `flag, appid, name, rank`.
- Network tables: written by the app export's writer, the five datasets stacked, with `dataset` and `state_id` as the first two columns:
  - `network_nodes.csv`, `network_edges.csv`, `network_clusters.csv`;
  - `network_cluster_quality.csv`, `network_cluster_connections.csv`, `network_null_model.csv`;
  - `network_seed_noise.csv`, `network_not_in_network.csv`;
  - `removal_sensitivity.csv`.
- `resolution_sweep.csv`, sorted by dataset then resolution: `dataset, resolution, n_multi_tag_clusters, n_one_tag_clusters, modularity, mean_silhouette, silhouette_status, ari_vs_report, seed_ari_min, seed_ari_mean`.
- `analysis.json`:
  - `schema_version`, `build_id`;
  - per dataset: its `state_key` and `state_id`, `n_games`, Eligible Pool size, per-flag counts (zeros included) and the Seed-Noise Floor summary;
  - a Resolution Sweep summary: the grid, plus the per-dataset ranges the report sentence uses;
  - `columns`.

  It does not copy `build.json`, which sits next to it.
- `report.html`.

### App (`steamstudy.app`)

**Stack and process**
- Dash 4, dash-cytoscape 1.0.2 and dash-ag-grid, with `DiskcacheManager` background callbacks for Removal Sensitivity only.
- Fully offline: every asset served locally, `debug=False`, no CDN and no version-check calls. If dev tools are ever enabled, `dev_tools_disable_version_check=True`.
- The app module does nothing at import beyond defining its layout: no data loading, no position computation.
- Background-job inputs are plain picklable values (Build path, dataset, settings, seed), never live objects. Up to about 4 s of startup per job is accepted, and there is no long-lived worker.
- The job store is a separate directory and may be culled normally.

**Renderer boundary**: the graph renderer is reached only through one module that takes nodes, edges, stylesheet and positions, so it can be replaced later (planned upgrade: Cytoscape.js 3.34 with WebGL behind our own wrapper). *Overridden by [App readability](../app-readability/spec.md) "Renderer" ([issue 01](../app-readability/issues/01-plain-cytoscape-renderer.md)): the graph is now drawn by a vendored Cytoscape.js 3.34 in our own wrapper (`renderer.py` + `assets/graph.js`), canvas renderer, WebGL off.*
- It sends a `preset` layout with positions computed in Python.
- It re-fits explicitly (clientside `cy.fit()`) once the first elements arrive, rather than relying on the layout's `fit`.
- The payload carries only ids, weights and styling data. AppID lists stay on the server.

**Recompute model**: stateless server. Every settings change recomputes the whole Network State from the loaded dataset: network, clustering, null model, Seed-Noise Floor, silhouette, metrics, centers and global positions. There are no performance caches in v1 (no in-memory LRU, no disk cache of states, null results or layouts).
- Sliders send on release (`updatemode="mouseup"`), with the value label live while dragging.
- Seed and γ inputs send on Enter or blur (`debounce=True`).
- Toggles and checkboxes send immediately.

**Two modes over one state**, switched by a control:
- **Workbench**:
  - Left column: controls, the removed-node list and the export area.
  - Centre: the graph with a cluster legend and a Global / Cluster-separated layout switch.
  - Right: the inspector (node / edge / cluster).
  - Below: tabbed tables: Cluster quality, Clusters, Removal sensitivity, Nodes, Edges, Not in network.
  - Controls, Inspector and Tables each collapse independently, and "Graph only" collapses all three. With the inspector collapsed, a click opens a floating panel closed with ×.
- **Analysis Report mode**: one scrolling page of numbered sections: 1 Dataset · 2 Filters (every left-out tag with its reasons) · 3 Network + inspector · 4 Cluster quality (including the Q-vs-null and Seed-Noise Floor lines) · 5 Removal sensitivity (same table; its noise line refers back to section 4) · 6 All nodes/edges · 7 Export.

**Controls** (both modes; initialised from `network.toml`):
- dataset selector;
- minimum games per tag (1–40), minimum shared games (1–30), Minimum Months Filter (0–60);
- per-tag Genre Tag toggles, and a defining-tag toggle;
- Clustering weight (Shared games / Lift), Clustering algorithm (Louvain / Leiden), γ (0.1–3.0, step 0.05), seed;
- remove (from the inspector), restore, reset all;
- Re-layout;
- Export this state, Open Network State…, Clear app cache.

R and K are config only and have no control.

**Graph**:
- Node colour is the cluster. Colour never encodes anything else, so there are no sensitivity or stability overlays.
- Edge width is mapped from `shared_games`. Edges are drawn as haystack edges.
- Cluster Centers are drawn as ◆ with a heavier outline. One-Tag Clusters are greyed.
- Clicking a node, edge or cluster opens it in the inspector.

**Inspector**
- Node:
  - every node metric, with active-mode strength first;
  - Membership Stability;
  - `within_z` with its cap ("within-z 1.2 (max 1.7 in a 4-tag cluster)"); values are not comparable across cluster sizes;
  - the tag's Removal Sensitivity row, if any, and "Run for this tag";
  - Remove.
- Edge: `shared_games`, `lift`, and the games having both tags (AppID, name, rank), computed on click.
- Cluster:
  - members ranked by `medoid_score`, with intra-cluster strength (active mode first), `within_z` and `participation` as columns;
  - center, `center_medoid_score`, `top_strength_tag`, `center_is_top_strength`;
  - the `connected` flag, with a warning suggesting Leiden when false;
  - `mean_membership_stability`.

**Removal sensitivity tab**
- Buttons: Run (estimate shown first), then progress, Cancel, and "Continue (n of N done)" for a partial result.
- Default sort: `rc_ari` ascending, then |`rc_delta_modularity`| descending. Every column is sortable. Membership Stability is joined in from the node metrics as an extra column.
- Filters: "beyond noise only" and a cluster selector.
- Above the table: the noise line, and a partial or stale banner when relevant. Below it: the expected-chance footer.
- A row click selects the tag in the graph and the inspector.
- Results are cached in `<build>/app_cache/` by the state key plus the method version. Returning to a cached state shows its results as current. Single-tag runs go into the same table, and a later full run skips them.
- Results for another key stay visible, greyed and not clickable, until a re-run.
- Starting or cancelling a job clears the progress bar.
- The cache is never evicted automatically. "Clear app cache" (button and CLI) deletes the results and their Continue offers. Deleting a Build deletes its cache.

**Layout**
- Global positions come from `network` (see above).
- The Global ↔ Cluster-separated switch computes positions from the current elements, with no rebuild and no recluster. Cluster-separated positions are computed only while that mode is shown.
- Re-layout refines the positions on the current graph, starting from the current ones. The result is held in a client-side store and reused for later changes. It is dropped when the dataset, Minimum Months Filter, Clustering Weight or seed changes, or on reload.
- Exports record `layout_source = "default" | "relayout"`.

**Open Network State…**
- Accepts an export zip directly or its `export.json`. Finds the Build by the path in the copied `build.json`, with a file picker if the Build has moved.
- Refuses if the Build's hash differs from the copied `build.json`, or if `key_version` differs.
- Accepts an older `schema_version` as long as the key fields can be read.
- Restores:
  - every key field; then it recomputes and shows ✓ / ✗ for the recomputed vs the recorded `state_id`;
  - the exported x/y as Re-layout positions when `layout_source = relayout`;
  - the zip's Removal Sensitivity results, shown as "loaded from export" and not rerun.

**Help**
- Every metric label and column header shows its schema description as a tooltip.
- A `?` on each panel opens the matching User Guide section inside the app. It is rendered with `dcc.Markdown`, offline, from the guide files shipped as package data.

**Banners**: `mode: test`; `parse_errors_allowed`; "loaded from export" on restored sensitivity results.

### User Guide and Running Guide

- **User Guide**: Markdown files in `docs/user-guide/`, one per part, English only. It is the single source of hand-written guide prose. It addresses a researcher without network-analysis training. The prose is written during implementation, against the real column names. The spec fixes only the outline and the required content:
  - **0. Three rules**: no number shows a cause; clusters carry no meaning; quote the `state_id` with every network number.
  - **1. Getting started**: open the app, load a dataset, the two modes.
  - **2. App controls**:
    - a control-by-control table: what the control does, its range and default, the Network State field it sets, and which numbers change;
    - 4–5 task recipes (e.g. check whether a cluster survives removing its center; compare Louvain vs Leiden; export a state for a paper);
    - no screenshots.
  - **3. Metric reference**, in concept order: ranking and data → feature analysis → network → clusters and partition quality → stability → Removal Sensitivity. Each entry:
    - opens with prose and a worked example;
    - gives theoretical bounds, reference points (lift 1 and phi 0 = independence; ARI 1 = identical and ≈ 0 = chance; Q 0 = no better than random), and the project's own comparisons (null model, Seed-Noise Floor, Eligible Pool);
    - ends with one marked "Exact definition" line.

    No interpretation bands anywhere. Required specific content:
    - the Membership Stability cluster-size effect (one lost companion costs a 2-tag member 0.5 and a 20-tag member 0.05);
    - `within_z` not comparable across cluster sizes, with its √(n−1) cap stated as a derivation;
    - the `share_ratio` pull towards 1 and its ceiling;
    - a high triple lift possibly inherited from one strong pair;
    - ΔQ including lost edge weight;
    - the expected chance flags;
    - `modularity_z` never read alone (Karrer et al. 2008 §I);
    - weighted adaptations noted where the cited originals are unweighted (Fortunato 2010, Guimerà & Amaral 2005);
    - the verified Li & Zhang 2020 facts as the only "typical values" context: Q = 0.414 on a pruned Steam tag network, 0.150 unpruned.

    Source material: the metric-reference draft from ticket 26 (63 entries plus the settings table), with ticket 30's "Required changes" applied before its content enters the guide.
  - **4. What's in each file**: one hand-written paragraph per file (`top100_<dataset>.csv`, each Build CSV, each file in the app zip, `snapshot.json` / `build.json` / `export.json` / `analysis.json`). Each says what one row is, what the file joins to, and what it is for.
  - **5. Citing and reproducing a Network State**: quote the `state_id`, deposit the export zip, cite the software version, reopen with Open Network State.
  - **6. Known limitations**: the single home of the full list (below).
  - **Appendix A. Published rules of thumb and why this guide does not use them**:
    - modularity 0.3–0.7 (Newman & Girvan 2004; Clauset et al. 2004; Fortunato & Barthélemy 2007), plus Newman 2004's "around 0.3 or more";
    - silhouette bands (Struyf, Hubert & Rousseeuw 1997, Table 2, p. 10, cited directly);
    - cluster-wise Jaccard stability (Hennig 2007);
    - node roles (Guimerà & Amaral 2005);
    - phi (Cohen 1992, Table 1, p. 157; w = |phi| marked as a derivation).

    The Steinley 2004 ARI band is **dropped**.
  - **Appendix B. Column index**: alphabetical, generated from the schema and committed. Every column with its file(s), app panel, report section and a link to its guide entry.
  - **Appendix C. References**: only sources verified at page, section or equation level (ticket 30).
    - Not cited: Kaufman & Rousseeuw 1990 (use Struyf et al. 1997 Table 2 and §2.1 for medoids), Steinley 2004, Rousseeuw 1987 (use Struyf et al. pp. 9–10 and the scikit-learn source for s = 0 in one-member clusters), Hubert & Arabie 1985 (use Meilă 2007 §2.1 eq. 6 and the scikit-learn docs), Shiffler 1988 (the z cap is stated as a derivation).
    - Conductance cites Fortunato 2010 eq. (20), not Kannan et al. 2004.
    - The phi maximum cites Warrens 2008 eq. (7).
    - BH under positive dependence cites Benjamini & Yekutieli 2001 Theorem 1.2.
    - The Li & Zhang title carries its subtitle.
- **Running Guide** (`docs/running-guide.md`), for whoever runs the pipeline. It assumes technical skill, and the User Guide links to it in one line. It covers:
  - install (`uv`, Python 3.14, `--compile-bytecode`);
  - the TOML configs;
  - Collect (resuming, rate limits, the hard stop);
  - Build and the test Snapshot;
  - the full-run gate mechanics (what it checks, how a met condition is recorded);
  - the Snapshot and Build layouts;
  - `--allow-parse-errors` (such Builds are never published);
  - the Windows notes (`127.0.0.1`, `-W default`, explicit UTF-8).

  It links to the pre-run checklist in this spec. In both guides, "operator" means only the Steam Charts site operator.
- **Known limitations** (content for chapter 6):
  - Tags are a current snapshot, not historical.
  - The Top 100 is a ranked selection, not a sample.
  - Steam Charts has coverage gaps, and it pauses tracking of low-player apps, so a gap means the app wasn't tracked, not that it had zero players.
  - Delisted games: the `store_data_unavailable` / `no_tags` exclusions and manual add-backs.
  - The `game`-type pool may be under 10,000.
  - Ties at rank 100.
  - Community-voted tags include joke votes (e.g. Dating Sim on Banana).
  - Content descriptor ids 3 and 4 have no official label documentation.
  - Dating Sim rank cannot separate dating sims from romance-heavy farming sims (handled by overrides).
  - Store data depends on the researcher's country (region-locked apps; the country is recorded in `snapshot.json`).
  - Builds made with `--allow-parse-errors` are never published.
  - Tiny pre-launch Steam Charts months are kept as real data.
  - `release_month_check.csv` is noisy for Early Access games.
  - The app is not optimised in v1: at the loosest thresholds a change can take several seconds, mostly for the null model.
  - Removal Sensitivity uses one main-seed run per removed tag; its flag is a screening aid, not a significance test.
  - The partition shown comes from a single run (one seed, one γ); no consensus partition is computed.
  - The Seed-Noise Floor samples K = 10 seeds, not every possible seed.
  - The Resolution Sweep covers a fixed γ grid, at the report's settings only.
  - Any shortfall of the Candidate Pool below 10,000 is reported here.
- **Kept in step by code**: the generated column index, plus the tests listed under Testing Decisions.

## Testing Decisions

**What makes a good test here**: it exercises external behaviour through one of the four agreed seams and asserts on observable outputs: stored responses and log entries, Build files and their contents, Network State results, export zips. It never asserts on private helpers or intermediate data structures. Expected values come from hand-checkable fixtures (a tiny dataset where the right clusters, Jaccard distances or lift values can be worked out on paper), never from snapshots of the code's own output, except where equality between two code paths is the point. Tests run offline with `-W default -X faulthandler`.

**Seam 1: Collect, through `Fetcher` and its fixture-backed fake adapter.** Tests:
- Rate spacing per source, with an injectable clock, and one connection per source.
- Hard stop with a non-zero exit on 403, 429, 503 and challenge pages (Cloudflare markers; missing structural marker).
- The 10/30/90 s retry schedule, then a stop. A stop after 5 parse-structure failures in a row.
- Listing passes end at 404 or an empty page. Passes are unioned by AppID, and the per-pass stats are recorded.
- Final outcomes `not_found`, `no_store_page`, `age_gate` and `no_appdetails`.
- Resume skips final outcomes and refetches retryable or stopped ones.
- Stage order. The store stage only fetches apps that `score()` says are scored.
- The age-check cookie date. No `cc=` parameter.
- The full-run gate refuses without the operator reply and the ethics check.
- `--repair` is logged.
- The SteamDB collector refuses without a permission reference and parses the hand-saved fixture pages.

**Seam 2: Build, through the pure `build(snapshot, config)`**, run against a fixture Snapshot saved from the test Snapshot plus the edge-case apps (Scorn, Black Hole Simulator, Bold Blade, Stardew Valley, Baldur's Gate 3, Dadish 3D, Bongo Cat, Banana, and the cases still to be picked). Tests:
- Parser behaviour: `Last 30 Days` skipped; unknown labels and duplicate months reported as parse errors; months after the window ignored.
- Placeholder Rows at every position. Release Month. Mean Monthly Players and `months_observed`. Unscored apps split three ways.
- The parse-error failure, and `--allow-parse-errors` with its flag.
- Ranking order and ties. Always exactly 100 rows.
- Every exclusion rule, with all reasons and `primary_reason`. Rank limits and per-tag limits. Overrides and manual exclusions.
- Manual Metadata Entry validation: an unsourced field is rejected; an entry for a store-provided app fails the Build; a tags-only entry works.
- Content Flags. The defining tag id checked against the vocabulary. A missing-tag-id warning.
- The `top100_<dataset>.csv` contract, including the `;`-in-name failure.
- The report files (`completeness`, `placeholder_rows`, `release_month_check` with a signed `months_apart`, `exclusions` with would-be ranks, `impact_*`, `ties`, `tag_vocabulary`).
- The provenance in `build.json`.
- Determinism: two Builds of one Snapshot and config give identical dataset and analysis files.
- No network access during a Build.
- Feature-analysis tables (the lift formula at k = 2 and k = 3, triples dropped when support equals a sub-pair's, empty phi at count 100, BH within each dataset, the defining tag out of the analyses).
- The Resolution Sweep includes the config γ.
- The causal-word test fails a report containing a listed word.
- Every report number is traceable to a CSV.

**Seam 3: Network, through `steamstudy.network`'s pure state computation (and its Removal Sensitivity and Resolution Sweep entry points)**, on small hand-built datasets. Tests:
- Thresholds, isolated tags kept as One-Tag Clusters, and the "Not in network" reasons and their order.
- N after the Minimum Months Filter. The lift formula, and lift unchanged by hiding or removing tags. Lift < 1 edges kept.
- Canonical order and seeded determinism for Louvain and Leiden (Leiden uses the modularity objective, never CPM).
- The disconnected-cluster flag. The cluster-label tie rule.
- Silhouette and its n/a rules. Coverage. Densities. Conductance and its statuses.
- Medoid, the tie-break and the 3+-tag rule. `top_strength_tag`.
- `within_z` (population SD) and its cap. Participation.
- The null model preserves every game's and every tag's degree.
- Replicate seeds and noise seeds never overlap.
- Seed-Noise Floor values, including the no-edges case.
- Membership Stability, including empty values for isolated tags.
- Removal Sensitivity: both readings, Δ signs, n/a transitions, the `rc_ari_beyond_noise` rule (including `seed_ari_min` = 1), and a partial run being a prefix of the full one.
- State-key canonical JSON and `state_id` stability. Global positions independent of thresholds. Edge AppIDs equal the intersection of the two tags' game sets.

**Seam 4: App, through its export zip.** Tests:
- **App-equals-Build equality**: opening the app on a Build at the report's settings and exporting gives CSVs equal to that dataset's Build rows, minus `dataset` / `state_id`. This proves the app and the report share one clustering.
- **Open Network State round-trip**: export, reopen, ✓ on the `state_id`; Re-layout positions restored; sensitivity results loaded as "loaded from export"; a refusal on a Build-hash or `key_version` mismatch; an older `schema_version` accepted.
- Zip contents: `export.json` hashes and row counts match the files; the Removal Sensitivity file is left out when not run and is never written from a stale key; `seed_noise.csv` is always present.
- The served page loads nothing from outside `127.0.0.1`.

**Schema and documentation tests** (alongside seam 4):
- A writer that emits an undeclared column, or omits a declared one, fails.
- The committed column index (Appendix B) is not stale.
- Every column has a `guide_entry` whose anchor exists as a heading.
- Every file the schema declares has a paragraph in chapter 4.
- Every in-app `?` anchor has a matching guide heading.

**Prior art**: the repo has no production code or tests yet. Reference material:
- the Dash/dash-cytoscape spike apps and check scripts (tickets 17 and 22), for the app wiring and the Leiden reproducibility check;
- the recompute benchmark (ticket 23), for realistic synthetic graphs and per-step costs;
- the interaction prototype (ticket 14), for the expected UI behaviour;
- the research notes (tickets 01, 09, 16), for the real edge-case AppIDs.

Fixtures for seams 1 and 2 come from the test Snapshot's own raw archive. SteamDB fixtures are pages saved by hand.

## Out of Scope

- Comparison with educational/STEM games (a later effort; the export format must not preclude it).
- Ranking by peak players. Paid-only dataset variants.
- Re-ranking or backfilling games inside the app. Loading arbitrary CSV schemas.
- The hybrid stack (FastAPI over `network` + a Vite/TypeScript front end), and any JS/TS backend, JS clustering or Pyodide build.
- The Cytoscape.js 3.34 WebGL renderer upgrade. It is planned, and its spike runs only if panning feels slow on the first test Build. The `window.cy` speed hack. *(The move to Cytoscape.js 3.34 itself happened in [App readability issue 01](../app-readability/issues/01-plain-cytoscape-renderer.md); WebGL stays off.)*
- Candidate Pool cross-checks (SteamSpy top-100 lists, Valve Best of Steam "Most Played", a hand-picked declined-games list). SteamSpy and `GetItems` as tag sources.
- Performance work in the app: turnaround targets, in-memory or disk caches of Network States, null-model results or layouts, staged null-model computation, a long-lived worker, multiprocessing for Removal Sensitivity. A later version can cache by `state_id`. Multiprocessing is revisited only if a sweep at default thresholds takes over 60 s on the first test Build.
- Consensus clustering, as the displayed partition or as a mode.
- Interpretation bands or stable/unstable labels anywhere. Semantic cluster names. Graph colour overlays for sensitivity or stability.
- Betweenness, closeness, eigenvector and PageRank centralities. Graph-distance silhouette. A null model per γ. The Resolution Sweep in the app.
- `network.json` or GraphML exports. Loose per-table exports from the app.
- Non-English guides. Screenshots in the guide.
- Browser emulation, proxies, challenge solving, logging in, a `cc=` parameter.
- Publishing raw responses or the full Candidate Pool. Publishing `monthly_players.csv` before the operator agrees.

## Further Notes

**Superseded statements in older tickets.** An implementer reading a ticket should apply these replacements:

| Older statement | Replaced by |
|---|---|
| Python 3.12 (ticket 15) | Python 3.14 (tickets 18, 22) |
| Leiden recommended as the algorithm (ticket 05) | Louvain default, Leiden optional mode (ticket 10) |
| Center = max intra-cluster weighted degree (prototype placeholder) | Jaccard medoid; `top_strength_tag` beside it (ticket 11) |
| "Node sensitivity" | Removal Sensitivity (ticket 12) |
| Global positions "computed once and cached" (tickets 18, 19) | Pure function of dataset + filter + weight + seed, recomputed (ticket 23) |
| Cluster-separated positions "cached per (state, layout)" (ticket 14 addendum) | Computed from the elements on switch (ticket 23) |
| `hidden_tagids` / `removed_tagids` (ticket 23) | `hidden_tag_ids` / `removed_tag_ids` (ticket 24) |
| `sensitivity_noise_seeds`; noise floor computed per sensitivity run | `noise_seeds` in the state key; standing Seed-Noise Floor (ticket 25) |
| Sensitivity key = state key + K + method version | State key + method version (ticket 25) |
| `removal_sensitivity_noise.csv` | Always-written `seed_noise.csv` / `network_seed_noise.csv` (ticket 25) |
| Noise summary in `export.json` `removal_sensitivity` block | Network-level summary (ticket 25) |
| `rc_beyond_noise` `;`-list; flags on ΔQ and Δsilhouette | Boolean `rc_ari_beyond_noise`, ARI only (ticket 27) |
| `cluster_quality.csv` `n_games` | `n_dataset_games` (ticket 28) |
| A separate "Clusters" table format in the analysis | The network tables written by the shared writer (ticket 24) |

**Researcher actions after the first test or full Build** (not implementation work):
- review the impact report;
- decide whether to tighten the `Dating Sim` rank limit and/or add `exclusion_override`s (Stardew Valley, Persona, The Sims 4, Monster Hunter Wilds, Fields of Mistria, Coral Island are the known tensions);
- review Banana for `manual_exclusion`;
- log every change in `CHANGELOG.md`;
- judge the panning feel (WebGL spike trigger) and the default-threshold sweep time (multiprocessing trigger).

**Reference costs measured on synthetic data** (not targets), at thresholds 8/8 · 3/3 · 1/1:
- full recompute without the null model: 17 · 61 · 245 ms;
- null model with R = 20 under Louvain: 0.3 · 0.8 · 2.9 s;
- Seed-Noise Floor: 40 ms · 155 ms · 1 s;
- global layout: about 217 ms;
- payload without AppIDs: 29 KB · 152 KB · 984 KB.

At about 400 nodes and 5,000 edges a full redraw takes about 42–55 ms. A background job takes about 4 s to show its first progress.

**Suggested implementation order** (for splitting into tickets):
1. `export.schema` + writers;
2. `collect` (`Fetcher`, parsers on fixtures);
3. `build` (score, exclusion, ranking, reports);
4. `network` (state, metrics, stability, Removal Sensitivity);
5. `analysis` (tables, report, sweep);
6. `app` (Workbench, Analysis Report mode, export, Open Network State);
7. User Guide + Running Guide + doc tests.

Seams 2 and 3 can proceed in parallel once the schema exists.

**Source tickets**: every decision above traces to a resolved ticket in this effort's `issues/` folder (01–30) and its research notes. The [map](map.md) lists them with a one-line gist each. Where a ticket and this spec disagree, this spec wins. It applies the overrides from tickets 23–30 in the order the map prescribes.
