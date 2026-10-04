# Recompute cost benchmark (ticket 23) — SYNTHETIC DATA

Measures what one Tag Network settings change costs on the server. **All data is synthetic** (`syn_tag_NNN` tags, random AppIDs); nothing contacts Steam. The numbers show cost, not real structure.

## Run

    # same recipe as ../22-dash-spike-python-314 (uv 0.12.23), plus scikit-learn
    uv venv --python 3.14.8 .venv
    uv pip install --compile-bytecode -r ../22-dash-spike-python-314/requirements-py314.txt scikit-learn
    .venv/Scripts/python bench.py              # ~4 min; writes results.json (raw numbers)
    .venv/Scripts/python bench.py --stats-only # dataset shape only
    .venv/Scripts/python bench.py --reps 5 --null-reps 3   # smoke run

Options: `--reps` (default 30), `--null-reps` (repetitions of the whole R = 20 baseline, default 20), `--R` (20), `--trades-per-game` (10), `--mmf` (13).

## Environment

Python 3.14.8 (GIL on), Windows 11 10.0.26200, AMD Ryzen 5 7535HS (6C/12T), 14 GB RAM. networkx 3.7, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1, python-igraph/igraph 1.0.0, leidenalg 0.12.0, plotly 7.1.0. Warm process, GC on, one thread.

## Synthetic dataset

- 100 games, vocabulary 400 tags (live Steam list has 446, archived table 400; research/04). 83 games have 20 tags, the rest 5–19 (research/04: max 20 shown, ≥ 5 at launch; most sampled pages showed 20). Mean 18.8 tags/game.
- Zipf (s = 1) tag popularity: top tags are on 95 %, 79 %, 69 %, 59 %, 45 % of games. 327 distinct tags are used, 76 of them on one game only, 55 on ≥ 8 games.
- Assumed, not calibrated: 8 latent "genres", each boosts 30 random tail tags ×6 (mild planted structure).
- `months_observed` uniform 1–60. A Minimum Months Filter of 13 keeps 78 games.

| setting (min games / min shared) | nodes | edges | Louvain clusters (multi + one-tag) | Leiden | Louvain on lift | Q (γ=1) | seed-noise ARI mean (min), K=10 |
|---|---|---|---|---|---|---|---|
| 8/8 (default) | 55 | 216 | 2 + 3 | 2 + 3 | 3 + 3 | 0.087 | 0.86 (0.77) |
| 3/3 | 178 | 1,297 | 5 + 0 | 4 + 0 | 9 + 0 | 0.059 | 0.32 (0.23) |
| 1/1 | 327 | 9,501 | 7 + 0 | 5 + 0 | 14 + 0 | 0.092 | 0.24 (0.15) |

The Minimum Months Filter set to 13 (78 games) gives 42/153 (3 + 2), 142/973 (5 + 2) and 304/7,891 (7 + 0).

## Per-step timings, ms (median / p95 over 30 reps, MMF off, 100 games)

| step | 8/8 | 3/3 | 1/1 | first call at 8/8 (cold) |
|---|---|---|---|---|
| 1 build graph (canonical order, + lift attr) | 2.2 / 2.5 | 7.8 / 8.5 | 23.0 / 78.0 | 2.3 |
| 2 Louvain, shared games | 3.0 / 4.0 | 12.4 / 16.8 | 90.1 / 109.6 | 5.8 |
| 3 Leiden: igraph build + partition | 1.1 / 1.6 | 5.2 / 7.0 | 24.2 / 27.3 | 1.1 |
| 3a … igraph build only | 0.13 / 0.16 | 0.68 / 0.87 | 4.9 / 6.3 | 0.26 |
| 4 Louvain, lift | 3.0 / 3.5 | 15.7 / 19.2 | 105.1 / 116.7 | 4.5 |
| 5a Jaccard per state (numpy matmul) | 0.26 / 0.31 | 0.82 / 34.2* | 2.1 / 16.3* | 0.42 |
| 5b Jaccard subset of cached all-tags matrix | 0.02 / 0.03 | 0.12 / 0.13 | 0.34 / 0.40 | 0.08 |
| 5c Jaccard per state, pure-Python sets | 1.1 / 1.8 | 7.5 / 8.1 | 23.1 / 29.9 | 1.1 |
| 5d `silhouette_score(precomputed)` | 0.63 / 0.78 | 0.95 / 1.3 | 1.5 / 1.9 | 10.9 |
| 5e `silhouette_samples(precomputed)` | 0.60 / 0.99 | 0.90 / 1.2 | 1.5 / 2.2 | 0.58 |
| 6 metrics (medoids, Q, coverage, per-cluster, conductance, cut, connection table, strengths, z, participation, connected flag) | 0.88 / 1.3 | 4.3 / 5.5 | 24.7 / 28.9 | 2.8 |
| 6a … `nx.community.modularity` alone | 0.19 / 0.31 | 0.93 / 1.2 | 6.9 / 11.9 | 0.21 |
| 7 null model R = 20, Louvain (20 reps) | 297 / 314 | 785 / 874 | 2,946 / 3,007 | 299 |
| 7 per replicate (median / 20) | 14.8 | 39.3 | 147 | |
| 7b null model R = 20, Leiden (5 reps) | 261 / 272 | 587 / 713 | 1,574 / 1,582 | |
| 7c curveball, 1,000 trades | 9.4 / 11.3 | 14.0 / 15.4 | 15.7 / 16.8 | 9.9 |
| 9 cluster-separated layout (spring per cluster seeded from global + shelf packing) | 8.3 / 9.9 | 27.6 / 30.4 | 58.6 / 66.3 | 9.4 |
| 10 seed-noise floor K = 10 (Louvain + ARI) | 40 / 49 | 155 / 173 | 1,002 / 1,030 | 46 |
| 11 elements build + `to_json_plotly`, no AppIDs | 0.59 / 0.91 | 3.4 / 4.5 | 21.4 / 74.8 | 2.7 |
| 11 same, with AppID lists | 1.3 / 2.2 | 5.6 / 8.0 | 34.1 / 88.4 | 1.3 |

\* p95 outliers (GC / OS scheduling); the medians are stable.

Null model: 10 trades per game = 1,000 curveball trades per replicate, on the same games restricted to the visible tags. Replicate seed = 42·1000 + r, Louvain seed 42. Breakdown of one R = 20 run (ms; shuffle / rebuild / Louvain / Q): 8/8 184 / 45 / 59 / 5; 3/3 288 / 185 / 290 / 25; 1/1 328 / 605 / 1,895 / 153. At 8/8 the shuffle dominates. With the filter on (78 games), R = 20 Louvain takes 220 / 569 / 2,490 ms.

## Global layout (1/1 graph, 327 nodes / 9,501 edges), ms median / p95

| | MMF off | MMF 13 (304 nodes) |
|---|---|---|
| `spring_layout(weight='weight', seed=42)`, 50 it | 215 / 258 | 182 / 205 |
| same, weight = lift | 216 / 240 | |
| re-layout from existing positions, 50 it | 219 / 255 | |
| re-layout from existing positions, 10 it | 49 / 56 | |
| full Jaccard matrix, all tags (once) | 2.1 / 5.1 (first 37) | 1.6 / 17.8 |

## End-to-end totals, ms median / p95 (30 reps, timed as one unit)

"Full recompute" = build → cluster → Jaccard (subset of cached matrix) → `silhouette_samples` once (score = its mean) → metrics → cluster-separated layout → elements + JSON. The global layout and the all-tags Jaccard matrix are cached inputs. It excludes the null model, the seed-noise floor, Dash callback overhead (7–9 ms at 127.0.0.1, ticket 22), transfer and browser render.

| total | 8/8 | 3/3 | 1/1 |
|---|---|---|---|
| **Full recompute, Louvain, no null model** | **16.6 / 21.7** | **61.1 / 74.8** | **244.8 / 323.2** |
| same, Jaccard recomputed per state | 17.8 / 23.5 | 70.6 / 115.5 | 271.4 / 337.6 |
| same, Leiden | 14.5 / 17.4 | 60.3 / 75.7 | 165.8 / 235.2 |
| same, Louvain on lift | 17.9 / 26.5 | 69.0 / 80.0 | 258.4 / 342.8 |
| same, MMF 13 (78 games), Louvain | 14.8 / 17.6 | 49.9 / 58.5 | 192.0 / 270.4 |
| + first state after a dataset / filter / weight-mode change: global layout + all-tags Jaccard | +~217 | +~217 | +~217 |
| **Null model R = 20, Louvain** | **297 / 314** | **785 / 874** | **2,946 / 3,007** |
| Null model R = 20, Leiden | 261 / 272 | 587 / 713 | 1,574 / 1,582 |
| **Recluster only (seed/γ change), Louvain**: cluster → silhouette → metrics → cluster layout → JSON on unchanged graph + Jaccard | **15.9 / 18.5** | **55.6 / 67.0** | **212.9 / 282.9** |
| Recluster only, Leiden | 13.2 / 16.4 | 48.4 / 56.5 | 136.2 / 213.0 |
| Seed-noise floor K = 10 (not in the totals above) | 40 / 49 | 155 / 173 | 1,002 / 1,030 |

## Payload, memory, edge lookup

| | 8/8 | 3/3 | 1/1 |
|---|---|---|---|
| `elements` JSON, no AppIDs (`to_json_plotly`, compact) | 28.7 KB | 151.8 KB | 983.5 KB |
| … with short edge ids (`e123` instead of `u\|v`) | 24.5 KB | 127.3 KB | 811.4 KB |
| … gzip | 2.6 KB | 11.9 KB | 67.2 KB |
| `elements` JSON with AppID lists | 56.1 KB | 224.0 KB | 1,219.8 KB |
| … gzip | 6.7 KB | 23.8 KB | 98.1 KB |
| edge AppID lookup `sorted(G_u ∩ G_v)`, µs median / p95 / max | 1.5 / 4.1 / 14.8 | 0.8 / 2.1 / 18.4 | 0.5 / 1.0 / 40.9 |
| one state, tracemalloc (graph, tag game sets, partition, labels, Jaccard, silhouette, metrics, positions) | 0.43 MB | 1.05 MB | 3.89 MB |
| … pickled size, excl. tag game sets (≈ diskcache entry) | 42 KB | 336 KB | 1.27 MB |
| … of which Jaccard matrix (float64) | 24 KB | 253 KB | 855 KB |
| tag game sets (per dataset + filter), pickled | 15 KB | 15 KB | 15 KB |

## First-call and import cost

- Imports in a fresh process, measured 3×: numpy ~175 ms, scipy ~90, networkx ~340, **sklearn.metrics ~1,500** (mostly `scipy.stats` via `sklearn.utils`), igraph ~90, leidenalg ~10, plotly.io.json ~15. Total ~2.2 s. Bare interpreter start is 85 ms.
- First calls after import cost more than warm calls: `silhouette_score` 10.9 ms vs 0.6 ms warm, Louvain 5.8 vs 3.0, metrics 2.8 vs 0.9, payload 2.7 vs 0.6, all-tags Jaccard 37 vs 2. The cold end-to-end recompute at 8/8 is 16.6 ms, the same as warm, because the step benchmarks warmed it up first.

## Caveats

- Synthetic data. Real tag co-occurrence will give different edge counts and cluster structure. Cost is driven mainly by edge count: Louvain, metrics, the null model and the payload all scale with it.
- Results come from one machine, single-threaded. Each p95 is the nearest-rank value of 30 samples (20 for the null model).
