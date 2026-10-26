# Exploratory grid run on the current Build
Type: task
Status: resolved
Blocked by: 03, 04

## Question

Run a throwaway script (in `prototypes/05-grid-run/`) of the decided selection procedure and metrics over the full Parameter Grid for all five datasets of Build `20261008T221504Z-7a23ae9f`. Record:

- per pair: whether a Selected Partition exists, its number of Multi-Tag Clusters, domain width, Information Retention, Fragmentation and Neighbour Agreement, with the numbers of comparable, missing and identical-graph neighbours ([Per-pair metric definitions](04-pair-metric-definitions.md));
- the distribution of each metric per dataset, as heatmaps or tables, as the evidence [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md) needs;
- wall-clock time per dataset, serial and parallel, and how many pairs share an identical graph (the room for caching).

Done when the results file is linked here. It states facts only and makes no choice of defaults.

## Answer

Done 2026-10-26, agent-driven. Results: [prototypes/05-grid-run/results.md](../prototypes/05-grid-run/results.md). It has distributions, g × s heatmaps, timing, graph sharing, and the 56- vs 80-value check. Every pair's numbers are in [pairs.csv](../prototypes/05-grid-run/pairs.csv); the script is [grid_run.py](../prototypes/05-grid-run/grid_run.py) and the report generator [report.py](../prototypes/05-grid-run/report.py). Raw JSON stayed in the session scratchpad, not committed. Facts only; no default is chosen.

**Blinding for ticket 06.** Per-pair Neighbour Agreement values would show which pair a set of constraints selects. They are therefore kept apart, in [neighbour-agreement-by-pair.md](../prototypes/05-grid-run/neighbour-agreement-by-pair.md) and its CSV, to be opened only after [Eligibility constraints and selection defaults](06-eligibility-and-selection-defaults.md) has fixed its defaults. `results.md` and `pairs.csv` show Neighbour Agreement only as distributions and neighbour counts.

**Facts** (Build `20261008T221504Z-7a23ae9f`, 5 datasets × 153 pairs, procedure exactly as tickets 03 and 04)
- 764 of 765 pairs have a Selected Partition. The exception is rpg g=18 s=4, with reason `too_few_multi_tag_clusters`. No pair has `no_stable_partition` or `no_edges`. No selected domain is clipped, and none is `not_representable`.
- The largest connected component holds every non-isolated tag in all 765 pairs, so the LCC share is always 1.000. 632 pairs have no isolated tag; the largest isolated share is 0.333 (puzzle).
- Information Retention ranges 0.407–0.928; per-dataset medians are 0.52–0.61.
- The Selected Partition's Multi-Tag Clusters range from 3 to 23. 196 pairs sit exactly at the minimum of 3, 184 of them at g ≥ 12.
- Selected domain widths range 0.037–0.670, with medians 0.14–0.23. 52 Selected Partitions were found by only 1 of the 560 scan runs.
- The Seed-Noise Floor at the Selected Resolution ranges 0.25–1.00, with medians 0.68–0.83.
- Neighbour Agreement: every pair with a Selected Partition has 2–4 comparable neighbours, never 1. The pooled median ARI over non-identical links is 0.80 along g and 0.66 along s. 66 g-links (none along s) join identical graphs; no pair's comparable neighbours are all identical-graph ones.
- Graph sharing: 699 distinct graphs among 765 pairs. Puzzle, rpg and simulation each have 22 pairs of g-neighbours with identical graphs; overall and strategy have none. Deduplicating by graph saves 66 scans (9%).
- Time: 761 s serial and 95 s on a 12-worker `multiprocess` pool for all five datasets, an 8.0× speed-up. That is 18–20 s per dataset in parallel and 0.55–0.84 s per pair median serially, 4.6 s at most. The Leiden scan is 94–95% of the time. Results are identical record for record, serial and parallel.
- 56 vs 80 γ values (same seeds): 720 of 765 pairs select the identical partition. Elsewhere the ARI goes as low as 0.456 (rpg). One rpg pair loses its Selected Partition on the 80-value set. Stable sets mostly coincide: 1,439 of 1,530 stable partitions on the 56-value set are also stable on the 80-value one.
- `metrics.modularity` equals CHAMP's (Â − γP̂)/2m to ≤ 7e-16. A direct `leidenalg` call on an igraph built once per pair gives memberships identical to `cluster.detect`'s.

**Assumption to fix elsewhere.** The scan seeds came from `derive_seeds` stream 3. No ticket has fixed that number; it is handed to [Modules, caching and parallelism](08-modules-caching-parallelism.md).
