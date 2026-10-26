# Exports and documentation
Type: grilling
Status: resolved
Blocked by: 06, 07, 10, 12

## Question

What does Automatic Parameter Selection export and document, so that results are reproducible and read correctly?

- Exported tables (the per-pair grid, Admissible Partitions with their domains, per-direction Neighbour Agreement, validation replicates, the selection report) and a settings JSON (Build, fixed settings, grid, seeds, the Pair Constraints and tolerance with a "Default constraints" / "Custom constraints" label, method version, software versions; per-pair reason codes in the grid table), following `app/export.py` and the `export/schema.py` contracts.
- User Guide pages: what each metric means and doesn't mean; the three kinds of stability; why count-only edges carry no significance; why Q, Coverage and Silhouette are descriptive.
- Methods text with citations (Weir et al. 2017; Newman 2016; Gibson & Mucha 2022; Hennig 2007; Karrer et al. 2008), checked against the sources as in Research 30.
- How the in-app `?` help (`app/help.py`) covers the new mode.
- From [Does Neighbour Agreement favour high g?](12-neighbour-agreement-high-g-bias.md): Edge Overlap as a column of the per-direction Neighbour Agreement table. The User Guide carries the high-g caveat, why identical-graph links are left out of Neighbour Agreement, and what Edge Overlap does and doesn't show.
- From [Apply-to-Workbench semantics](09-apply-to-workbench.md): whether a Workbench export made after Apply records its provenance (pair, reproduced or ARI). How the User Guide explains why an applied Workbench's Seed-Noise Floor can differ from the one Parameter Selection reports.
- From [Shipping Parameter Selection results in an App Bundle](13-shipping-results-in-an-app-bundle.md): the settings JSON records the cache files' `computed_with` block. The User Guide says shipped results were computed when the bundle was made, that "Clear app cache" replaces them with this computer's, and why a recomputation might differ (another Python or OS, practically never). It also gives the loading panel a method section to link to.

## Answer

Decided by the researcher, 2026-10-26, in three rounds of grilling; every recommendation was accepted. The third round took in what [Shipping Parameter Selection results in an App Bundle](13-shipping-results-in-an-app-bundle.md) handed on while this ticket was open.

**The export**
- "Export tables" sits in the Controls column under Run. It writes **one zip per settings key**, `steamstudy_parameter-selection_<grid_key_hash[:12]>_<UTC>.zip`, covering every dataset whose grid is complete. Tables are stacked by a `dataset` column, like the Build's stacked files.
- **Incomplete datasets** (running, cancelled or not run) are left out, and `parameter_selection.json` records their status ("partial, k of 153", "not run"). Partial rows would carry no selection and no Neighbour Agreement on cells whose neighbours aren't computed yet, so they would read as results. A complete grid that hasn't been validated still exports, with validation `not_run`. The button is disabled only when no dataset is complete.
- **Seven tables**, each row per dataset:
  - `pairs.csv`: one row per Threshold Pair, 153 per dataset. It holds:
    - g and s, tags and edges, and the graph hash;
    - the Selected Partition's domain and midpoint, and the Workbench γ and seed with reproduced or ARI;
    - Neighbour Agreement, with its comparable and different-graph neighbour counts;
    - retention, isolated share, LCC share, Multi-Tag and One-Tag Clusters, and the Seed-Noise Floor;
    - the descriptive Q, Coverage and Silhouette;
    - `qualifies`, every failing reason code as a list, `near_best` and `chosen`.
  - `admissible_partitions.csv`: one row per pair and Admissible Partition. It holds Â, P̂, the domain, a clipped flag, γ̂ (or no estimate), stable, Multi-Tag Clusters, the first γ and seed, the hit count and `selected`.
  - `neighbour_links.csv`: one row per directed neighbour link (g−, g+, s−, s+). It holds the status (comparable, missing or identical graph), shared tags, ARI and Edge Overlap.
  - `selected_partitions.csv`: one row per pair and tag, giving its Cluster in the Selected Partition (about 60k rows). With it, Neighbour Agreement can be recomputed without Leiden.
  - `selection.csv`: one row per dataset. It holds the chosen pair or `no_qualifying_pair`, the max NA, the tolerance, the near-best set, the tie-break used, and the constraints label with each changed value.
  - `validation_replicates.csv`: one row per replicate and arm (null, subsample re-selected, subsample at the Selected Resolution). It holds the seed, whether the replicate had a Selected Partition or was degenerate, ARI, Q, and the null's fixed-γ Q.
  - `validation_clusters.csv`: one row per validated pair, arm and Cluster. It holds the median Jaccard, the retention share, the absent count and `dissolved`.
  
  The validation files hold rows only for validated pairs.
- **`parameter_selection.json`** mirrors `export.json`. It holds:
  - `schema_version`, the `grid_key` and its hash, and each validated pair's `validation_key`;
  - the fixed settings and the grid (γ 0.25–3.00, step 0.05, 10 scan seeds);
  - every seed stream with its actual seeds: main, scan (stream 3), null (stream 4) and subsample (stream 5);
  - the Pair Constraints and tolerance, with the "Default constraints" / "Custom constraints" label and the per-dataset overrides;
  - the method versions (grid and validation) and the software versions;
  - a copy of `build.json`;
  - per dataset, its status and the `computed_with` block of its grid and of each validated pair, copied from the cache files, so the zip shows whether its numbers came from a bundle maker's machine or this one;
  - each file's rows and SHA-256, and the `columns` block.
- **Schema:** the new files are declared in `export/schema.py` under a new group, `parameter_selection`, and `SCHEMA_VERSION` goes to 3.
- **`selection_report.md`** is in the zip. For each dataset it gives the "Why this pair" text with its caveats and the validation sentences and verdicts, then the methods paragraph with citations. Every sentence comes from a fixed template and every number from the CSVs, the rule the Build's `report.html` follows.
- **Record only:** there is no Open path back into the mode. You reproduce it by running the same Build and settings, which gives byte-identical tables ([Modules, caching and parallelism](08-modules-caching-parallelism.md)). The guide says to compare the SHA-256 values.
- **Workbench exports after Apply:** while the applied provenance line shows (the key still equals the applied key), "Export this state" adds an informational `applied_from` block to `export.json`. It holds the dataset, g, s, the grid key hash, the method version, the Workbench γ and seed, and reproduced or ARI. It stays outside `state_key`, Open ignores it, and it never changes `state_id`.

**Where the documentation goes**: into the existing User Guide chapters, not a new one.
- **Ch. 1:** "The two modes" becomes three.
- **Ch. 2** gains a "Parameter Selection mode" section: Run, Pair Constraints, the heatmap and its reason letters, the Pair Inspector, Apply to Workbench, and Validate this pair.
  - The **Run** entry explains the provenance line: shipped results were computed when the bundle was made. "Clear app cache" replaces them with this computer's. A recomputation could in principle differ on another Python or OS, but practically never, because every library version is locked.
  - The **Apply** entry explains why an applied Workbench's Seed-Noise Floor can differ. The Workbench derives its noise seeds from the seed it was given, which may be a scan seed. Parameter Selection uses the main seed's noise seeds at the exact Selected Resolution.
- **Ch. 3** gains a "Parameter Selection" section. It opens with **"How Automatic Parameter Selection works"**: the steps in order (grid, γ scan, CHAMP, γ̂ and Stable Partitions, Selected Partition, Neighbour Agreement, constraints and choice, validation), each linking to its entry. The loading panel's link and Run's `?` both open it. Eleven entries follow, each with In short, Why it matters here and one exact definition:
  1. Threshold Pair and Parameter Grid;
  2. Admissible Partition and Optimality Domain (CHAMP);
  3. γ̂ and Stable Partition;
  4. Selected Partition and Selected Resolution, with the Workbench γ, seed and `not_reproduced`;
  5. Neighbour Agreement, covering comparable, missing and identical-graph links;
  6. Edge Overlap;
  7. Information Retention;
  8. isolated share and LCC share;
  9. Pair Constraints, Qualifying Pair and the selection rule, covering near-best, tie-break and reason codes;
  10. Null Comparison;
  11. Subsample Stability, covering both arms, Hennig's Jaccard, the retention share and "Dissolved".
  
  The existing Q, Coverage and Silhouette entries each gain a "Descriptive: not comparable across pairs" paragraph. The Seed-Noise Floor entry gains a one-line link to the Apply entry.
- **Three kinds of stability:** ch. 3's Stability section opens with this short entry.
  - Algorithmic: the Seed-Noise Floor, same data and settings with other seeds.
  - Parameter: Neighbour Agreement, neighbouring thresholds.
  - Data: Subsample Stability, 80% of the games.
  - The Null Comparison is a fourth, separate check: is there more structure than in random networks with the same tag and game counts?
  - They answer different questions and are never combined into one score. A high value on one says nothing about the others.
  
  The entry is linked from the four metrics' entries and from the mode's validation card.
- **Ch. 4** gains the eight new files.
- **Ch. 5** gains "Report a Parameter Selection": deposit the zip, compare hashes after a rerun, and the methods paragraph. One sentence points to the Run entry for anyone comparing hashes across machines.
- **Ch. 6** gains the new limitations.
- **Hennig's 0.5 is a verdict, not a band.** The Subsample Stability entry states "≤ 0.5 = dissolved" in Hennig's own wording (H07 §2). Appendix A's Cluster-wise Jaccard entry gains a line: this is the only cut used, and only for Subsample Stability; 0.6, 0.75 and 0.85 stay unused. The no-bands test allows that one phrase.

**Statements the tests pin** (the spec fixes each exact phrase)
- `test_required_statements_in_the_metric_reference` gains:
  - count-only edges carry no significance claim;
  - Q, Coverage and Silhouette are "not comparable across pairs" and never select;
  - Neighbour Agreement measures parameter stability, not correctness;
  - the fixed high-g caveat of [Does Neighbour Agreement favour high g?](12-neighbour-agreement-high-g-bias.md), word for word;
  - identical-graph links are left out of the Neighbour Agreement mean, and why;
  - Edge Overlap describes how much the graph changed, not whether the Clusters are right;
  - the Selected Partition is "a defensible choice, not the true structure";
  - with Lift, there is "no likelihood behind" Newman's estimate.
- `test_known_limitations_chapter_holds_the_full_list` gains the high-g caveat, count-only thresholds, Lift without a likelihood, and `no_qualifying_pair`.

**Methods text and citations**
- The methods paragraph is **one template in code**, in the selection report module. It is rendered with the run's numbers into `selection_report.md` and shown with placeholders in ch. 5. A test asserts that the guide's copy equals the template.
- The locators in [Research 01](../research/01-resolution-selection-formulas.md) and [Research 02](../research/02-validation-methods.md) count as the check "as in Research 30", since both read the sources in full. No new research ticket is needed. The locators:
  - Weir et al. 2017: §2, eqs. 1–4;
  - Newman 2016: §III.A, eqs. 15–18;
  - Gibson & Mucha 2022: Fig. 1(d), SI §C.2–C.3;
  - Hennig 2007: §2 (author preprint);
  - Karrer, Levina & Newman 2008: abstract, §III, §VI.
  
  Appendix C gains Weir and Gibson & Mucha with their locators, and Hennig's entry gains the §2 locator it lacks today.

**In-app help**
- The mode uses the Workbench's two-layer `?` help.
- Each heatmap metric, Inspector label, Pair Constraint field, reason letter, verdict tag and the Edge Overlap column maps to a ch. 3 entry. This goes through new `selection.*` keys in `HELP` (`app/help.py`) and `column_attrs` on the new schema columns.
- Run's `?` opens the ch. 3 overview entry. Apply and Validate this pair point to ch. 2.
- The existing help tests extend to the new keys.

**Running Guide**
- A short paragraph covers:
  - run time and cores: a full Run takes about 3 min on 12 workers and about 23 min serially, per [Shipping Parameter Selection results in an App Bundle](13-shipping-results-in-an-app-bundle.md);
  - where the cache lives: `<build>/app_cache/parameter_selection/`;
  - that "Clear app cache" removes it.
- The implementation issue that writes this paragraph waits until the researcher's uncommitted `docs/running-guide.md` changes are committed, so it never edits over them.

## Comments

- 2026-10-26: Resolved in three grilling rounds. The researcher confirmed the summary of the first two rounds and accepted round 3, which handled the hand-on from ticket 13 that arrived meanwhile. The Running Guide figures were corrected to the full Run's, from that ticket. The first two rounds had used the grid-only timing from [Exploratory grid run on the current Build](05-exploratory-grid-run.md).
