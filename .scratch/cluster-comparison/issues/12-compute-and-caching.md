# Where does each dataset's Network State come from, and how long does a comparison take?
Type: grilling
Status: resolved
Blocked by:

## Question

The mode, as fixed in [What does the Cluster Comparison mode look like?](06-look-of-the-mode.md), shows every included dataset's Multi-Tag Clusters with their Tags, and the games of each Cluster in a match's detail. The pair list needs every pair at once (ARI, Comparable Tags, games in common).

Decide, against the code (`src/steamstudy/app/ps_cache.py`, `ps_view.py`, `app_cache.py`, `job_registry.py`, `network/state.py`):
- for a dataset **on a cell**: whether the stored Selected Partition from the Automatic Parameter Selection cache is enough (nodes, edged Tags, labels, as prototype 06 used), or a full Network State has to be built (and so whether the Network is rebuilt from the games at that g and s);
- for a dataset **set by hand or with no run**: it is clustered with the main seed. Whether that reuses the Workbench's cached states, and whether it runs in the request or as a background job with progress, like a Parameter Selection run;
- what is cached and keyed on what, so that switching pairs, moving the minimum or swapping A and B never recomputes;
- what the mode shows while a dataset is still being computed, and when a shared setting changes and every dataset re-resolves (ticket 03, point 11);
- a rough time budget for five datasets on the full Build.

## Comments

- From [What fixes one comparison, and what does its export hold?](09-comparison-identity-and-export.md): the export holds every pair and every match (not only the pair on screen) and its button is disabled while any dataset is still being computed; whatever is decided here must let the export read all pairs at once.

## Answer

Resolved with the researcher, 2026-11-17. Measured on the full Build (5 Top-N Datasets of 100 games, about 60 Tags per network): reading one dataset's Parameter Selection cache with its Selected Partitions takes about 0.3–0.5 s; a full Network State (`compute_state`, 20 null replicates) about 0.6–0.7 s; the network, one clustering with the main seed and the 10 noise seeds about 0.07 s. The Workbench keeps no states (it recomputes per request and memoises only 4 states' tables, `STATE_TABLES`).

1. **A dataset on a cell** uses only its stored Selected Partition from the Automatic Parameter Selection cache: Tags in the network, edged Tags, Cluster labels, γ, Seed-Noise Floor, Neighbour Agreement. No Network State is built and the network is not rebuilt from the games. Tag names and each Cluster's games come from the loaded dataset (as prototype 06 did).
2. **A dataset set by hand or with no run** gets a lighter computation, not a full Network State: the network, one clustering with the main seed, and the noise-seed runs for its Seed-Noise Floor; no null replicates, centres, silhouette or node metrics. It is one small function in `network/state.py` built from the same functions `compute_state` uses (`build_network`, `cluster_graph`, `noise_seeds`), with a test that its partition and floor equal `compute_state`'s at the same settings. The Workbench's memo is not reused.
3. **Everything runs within the request**: no background job, progress bar or cancel. Time budget for the spec: about 0.4 s per dataset on a cell, about 0.1 s per hand-set dataset, matching all pairs takes milliseconds; under about 5 s cold for five datasets on the full Build.
4. **Two server-side LRU memos**, small like `STATE_TABLES`: (a) one resolved partition per dataset, keyed by Build, dataset, the shared settings and the dataset's source with its values (the per-dataset part of the Comparison State); (b) every pair's matches, flags, ARI, Comparable Tags and match games, keyed by `comparison_id`. Matches are stored once per unordered pair. The minimum similarity, chosen pair, chosen match and A/B orientation are view choices derived from (b) with no recompute; swapping A and B only swaps which side's shares appear where. The export reads (b) whole.
5. **While computing**: the previous view dims under one loading overlay for the whole mode and Export is disabled until it returns; no per-dataset "computing" state. A change to a shared setting re-resolves every dataset in that one request; a change to one dataset's g, s or γ reuses the other datasets' memo entries.
6. **Cells are read when the mode resolves** (opening the mode, a settings change, a dataset change); nothing polls for a Parameter Selection run finishing. A dataset whose cell is no longer in the cache (cache cleared, run changed) follows the no-run rule of ticket 03: it starts from the network defaults and the source line says the run is gone; the old g, s and γ are not kept as "set by hand".

No new glossary term; no ADR (cheap to reverse).

