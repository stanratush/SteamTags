# Ticket 15 measurements

Produced by [bounds.py](bounds.py), [scan_extended.py](scan_extended.py) and this script. Build `20261008T221504Z-7a23ae9f`; Genre Tags and the defining tag hidden, Minimum Months 0; 765 pair graphs. Quantile columns: min, 5%, 25%, median, 75%, 95%, max. The last two columns count graphs below 0.25 and above 3.00.

## Lift weights

| Bound | graphs | min | 5% | 25% | median | 75% | 95% | max | < 0.25 | > 3.00 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| γ_max = max 2m·w/(k_i k_j) | 765 | 2.574 | 3.791 | 7.700 | 15.443 | 32.750 | 94.234 | 203.798 | 0 | 758 |
| γ_pos (root of F, Q > 0 ends) | 765 | 1.384 | 1.600 | 2.307 | 3.119 | 4.284 | 7.327 | 13.479 | 0 | 412 |
| GM22 γ_max(K), K = non-isolated tags | 765 | 3.790 | 4.202 | 5.005 | 5.915 | 7.793 | 12.341 | 17.713 | 0 | 765 |
| γ_min lower: (2m/vol)·λ2 | 765 | 0.017 | 0.215 | 0.294 | 0.407 | 0.527 | 0.687 | 0.771 | 88 | 0 |
| γ_min upper: Fiedler sweep cut | 765 | 0.018 | 0.257 | 0.416 | 0.541 | 0.665 | 0.777 | 0.846 | 29 | 0 |
| γ_min upper: Jeub iteration (Leiden, 10 seeds) | 765 | 0.018 | 0.257 | 0.416 | 0.537 | 0.659 | 0.776 | 0.835 | 29 | 0 |
| γ_min upper: min(sweep, Jeub) | 765 | 0.018 | 0.257 | 0.415 | 0.537 | 0.659 | 0.776 | 0.835 | 29 | 0 |
| γ_min exact (brute force, components ≤ 24 tags) | 44 | 0.260 | 0.412 | 0.564 | 0.664 | 0.767 | 0.827 | 0.835 | 0 | 0 |

- Bracket width, upper/lower: median 1.292, max 1.636.
- Exact γ_min on 44 graphs: the sweep cut hits it on 35, Jeub's iteration on 44, either on 44; worst upper/exact 1.0000.
- Sweep cut lower than Jeub on 25 graphs, Jeub lower on 238.
- Graphs with more than one component of ≥ 2 tags: 0; with an isolated tag: 133.
- Jeub iteration: 20–50 Leiden runs per graph (median 30).
- Event sampling, 56 values from β(γ_min upper) to 1: values above 3.00 per graph median 4 (range 0–11); inside [0.25, 3.00] median 52 (range 40–56). Median event γ: 1.243.
- γ_pos/γ_max: median 0.211, range 0.038–0.569.

Extremes:

- γ_max lowest: 2.574 at rpg g=18 s=2 (27 tags); edge 1756–3839, shared 9, w 1.96, strengths 22.8 and 23.9, 2m 717.3
- γ_max highest: 203.798 at rpg g=3 s=3 (128 tags); edge 1676–3813, shared 3, w 20, strengths 24 and 20, 2m 4882
- γ_pos lowest: 1.384 at puzzle g=20 s=2 (21 tags)
- γ_pos highest: 13.479 at puzzle g=3 s=3 (139 tags)
- γ_min lower lowest: 0.017 at strategy g=8 s=8 (65 tags)
- γ_min lower highest: 0.771 at simulation g=20 s=2 (23 tags)

By dataset (medians):

| Dataset | γ_min lower | γ_min upper | γ_pos | γ_max | γ_max(K) |
|---|---:|---:|---:|---:|---:|
| overall | 0.457 | 0.604 | 2.950 | 11.870 | 6.043 |
| puzzle | 0.384 | 0.517 | 3.063 | 17.417 | 5.137 |
| rpg | 0.472 | 0.592 | 2.802 | 15.246 | 5.399 |
| simulation | 0.362 | 0.486 | 3.337 | 13.413 | 6.043 |
| strategy | 0.341 | 0.479 | 3.505 | 21.927 | 6.171 |

## Shared games weights

| Bound | graphs | min | 5% | 25% | median | 75% | 95% | max | < 0.25 | > 3.00 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| γ_max = max 2m·w/(k_i k_j) | 765 | 2.526 | 3.469 | 6.714 | 13.042 | 31.509 | 162.864 | 1316.769 | 0 | 749 |
| γ_pos (root of F, Q > 0 ends) | 765 | 1.243 | 1.345 | 1.670 | 2.047 | 2.399 | 3.028 | 3.987 | 0 | 42 |
| GM22 γ_max(K), K = non-isolated tags | 765 | 3.790 | 4.202 | 5.005 | 5.915 | 7.793 | 12.341 | 17.713 | 0 | 765 |
| γ_min lower: (2m/vol)·λ2 | 765 | 0.121 | 0.436 | 0.516 | 0.586 | 0.662 | 0.758 | 0.818 | 1 | 0 |
| γ_min upper: Fiedler sweep cut | 765 | 0.144 | 0.580 | 0.667 | 0.728 | 0.785 | 0.842 | 0.882 | 1 | 0 |
| γ_min upper: Jeub iteration (Leiden, 10 seeds) | 765 | 0.144 | 0.580 | 0.662 | 0.723 | 0.781 | 0.841 | 0.882 | 1 | 0 |
| γ_min upper: min(sweep, Jeub) | 765 | 0.144 | 0.580 | 0.661 | 0.723 | 0.781 | 0.841 | 0.882 | 1 | 0 |
| γ_min exact (brute force, components ≤ 24 tags) | 44 | 0.582 | 0.654 | 0.735 | 0.801 | 0.844 | 0.877 | 0.882 | 0 | 0 |

- Bracket width, upper/lower: median 1.219, max 1.436.
- Exact γ_min on 44 graphs: the sweep cut hits it on 30, Jeub's iteration on 44, either on 44; worst upper/exact 1.0000.
- Sweep cut lower than Jeub on 22 graphs, Jeub lower on 319.
- Graphs with more than one component of ≥ 2 tags: 0; with an isolated tag: 133.
- Jeub iteration: 20–50 Leiden runs per graph (median 30).
- Event sampling, 56 values from β(γ_min upper) to 1: values above 3.00 per graph median 2 (range 0–6); inside [0.25, 3.00] median 54 (range 49–56). Median event γ: 1.213.
- γ_pos/γ_max: median 0.164, range 0.002–0.494.

Extremes:

- γ_max lowest: 2.526 at rpg g=19 s=2 (25 tags); edge 1662–3810, shared 14, w 14, strengths 192 and 204, 2m 7066
- γ_max highest: 1316.769 at rpg g=3 s=3 (128 tags); edge 1676–3813, shared 3, w 3, strengths 13 and 3, 2m 1.712e+04
- γ_pos lowest: 1.243 at simulation g=20 s=2 (23 tags)
- γ_pos highest: 3.987 at puzzle g=3 s=3 (139 tags)
- γ_min lower lowest: 0.121 at strategy g=8 s=8 (65 tags)
- γ_min lower highest: 0.818 at simulation g=20 s=2 (23 tags)

By dataset (medians):

| Dataset | γ_min lower | γ_min upper | γ_pos | γ_max | γ_max(K) |
|---|---:|---:|---:|---:|---:|
| overall | 0.629 | 0.756 | 1.915 | 9.468 | 6.043 |
| puzzle | 0.558 | 0.707 | 2.054 | 16.637 | 5.137 |
| rpg | 0.631 | 0.756 | 1.860 | 13.735 | 5.399 |
| simulation | 0.552 | 0.699 | 2.095 | 10.357 | 6.043 |
| strategy | 0.513 | 0.660 | 2.325 | 14.085 | 6.171 |

## Extended scan (Lift): fixed [0.25, 3.00] against [scan start, γ_pos]

- Graphs: 765; scan values per graph 24–269 (median 59); scan start below 0.25 on 88 graphs.
- The fixed arm reproduces ticket 05's Selected Resolution (to 1e-5) on 765 of 765.
- Same Selected Partition in both arms: 761; no selection in both: 1; differ: 3.
  - puzzle g=3 s=3: fixed [2.694, 2.951] K=23 (None); extended [2.448, 2.660] K=20 clip_hi=False (None)
  - rpg g=3 s=3: fixed [2.532, 2.787] K=22 (None); extended [2.864, 3.317] K=26 clip_hi=False (None)
  - puzzle g=4 s=4: fixed [2.148, 2.362] K=16 (None); extended [0.064, 0.367] K=3 clip_hi=False (None)
- Extended arm: graphs with a stable domain reaching above 3.00: 1; starting above 3.00: 0; with a stable γ̂ above 3.00: 0.
- Largest γ̂ of any Admissible Partition (extended): median 1.605, max 4.168; graphs with any γ̂ > 3.00: 23.
- Fixed arm `estimate_above_range`: 0, `estimate_below_range`: 0; extended arm: 0 and 0.
- Found envelope zero crossing (max ω_in over Admissible Partitions) / γ_pos: median 0.869, range 0.786–0.954.
- Stable Partitions per graph, fixed vs extended: mean 2.00 vs 2.00; graphs where the count differs: 1.
- Leiden runs that hit the 1000-pass cap (n_iterations=-1 would not stop): 56 on 1 graphs; γ from 6.2 to 6.7; at γ ≤ 3.00: 0.
- Leiden runs: 519850 in total against 428400 for the fixed scan; summed worker time 1499 s.

