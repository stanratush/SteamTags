# Shipping Parameter Selection results in an App Bundle
Type: grilling
Status: resolved
Blocked by: none

## Question

Should `steamstudy bundle` carry precomputed Parameter Selection results, so a researcher opens finished grids and validations offline without a ~3-minute run? If so, how is a cache made on one machine trusted on another?

- Today `bundle/make.py` copies each Build folder **without** `app_cache/`, so nothing cached travels. [Modules, caching and parallelism](08-modules-caching-parallelism.md) fixed the cache layout: `app_cache/parameter_selection/grids/<grid_key_hash>/` and `validation/<validation_key_hash>.json`, keyed by settings and method versions, not by library versions.
- Which results to ship: none, only the default-settings grids and validations, or whatever the maker's cache holds? Is a missing cache produced at bundle time (a new `bundle` option that runs the job) or only copied?
- Trust across machines: `leidenalg==0.12.0` and `python-igraph==1.0.0` are pinned, but numpy and Python vary across the bundle targets (3.12–3.14, ADR 0001). Do library versions go into the keys, get recorded in the manifest and checked on load, or is the result accepted as it is? What does the mode show for a shipped result it can't reproduce locally?
- How "Clear app cache" treats shipped results, and whether the checklist in `docs/releasing-an-app-bundle.md` gains a step.

## Answer

Decided by grilling with the researcher, 2026-10-26. Checked against `bundle/make.py`, `versions.py`, `app/rs_cache.py`, the library-version banner in `app/callbacks.py`, `uv.lock` and `docs/releasing-an-app-bundle.md`.

**Facts checked while deciding**
- `make_bundle` copies each Build with `ignore_patterns("app_cache")`, so no cache travels today, Removal Sensitivity included. In an extracted bundle, `app_cache/` is created inside the bundle's own Build folder.
- `uv.lock` holds one version of every app library for all Pythons and OSes: numpy 2.5.3, scipy 1.18.1, leidenalg 0.12.0, python-igraph 1.0.0, networkx 3.7, scikit-learn 1.9.1. A bundle installs exactly these versions. So the maker's `.venv` and every researcher's install differ only in the Python version (3.12–3.14) and the OS/CPU.
- Apply already recomputes Leiden locally and compares it with the stored Selected Partition ([Apply-to-Workbench semantics](09-apply-to-workbench.md)). Every applied pair is therefore checked on the researcher's computer.
- A full Run takes ~3 min on 12 workers and ~23 min serially.

**Ship: yes.** The selected pair is the result researchers act on, closer to a Build output than to a scratch cache. Everyone holding the same bundle sees the same pick, with no wait on a slow laptop.

**What ships**
- Exactly what **Run → All datasets** produces under the shipped code's default `SelectionSettings`: each dataset's complete grid (manifest with Neighbour Agreement, every graph file) and the validation of its pair chosen under the default constraints.
- This applies to **every Build the bundle carries**, not only the latest.
- Nothing else ships: no custom-settings grids, no extra "Validate this pair" results, nothing partial. The bundle's content depends only on the code and the Builds, never on what the maker explored.

**Always recomputed at bundle time**
- `steamstudy bundle` never copies from the maker's cache. It runs the procedure into the staging Build's `app_cache/parameter_selection/` with a pool of `[parameter_selection] workers`, ~3 min per Build on 12 workers.
- Reason: the steamstudy version stays 0.1.0, so a cache made by older code under the same `METHOD_VERSION` would otherwise ship silently.
- Where the maker's cache holds the same key, the two are compared, with timings aside. A difference logs a warning that the maker's cache is stale and a method version probably needed a bump. The fresh result ships either way. The maker's cache is never touched.
- `--skip-parameter-selection` makes a bundle without results, for quick test bundles (and the acceptance test, which can use it to keep its ~6 minutes).
- `bundle.json` gains `parameter_selection`: per Build, the shipped grid and validation key hashes, or `"skipped"`.

**One driver.** A new Dash-free `app/ps_run.py`, beside `ps_cache.py`, holds the Run orchestration:
- grids of all datasets, then Neighbour Agreement and `choose` under the default constraints, then validation of each chosen pair;
- cache writes in the layout of [Modules, caching and parallelism](08-modules-caching-parallelism.md);
- weighted progress records.

It takes `map_fn`, `on_progress`, `should_stop` and a cache root. The Dash Run job wraps it with its pool and `set_progress`. `bundle/make.py` calls it with its own pool and the staging cache root. The network modules stay cache-free.

**Versions: recorded, never keyed**
- Every grid manifest and validation file gains `computed_with`: `software_versions()` (Python, steamstudy, the libraries), `platform.system()` and `platform.machine()`, and a UTC timestamp. Local runs write it too.
- Versions stay out of `grid_key()` and `validation_key()`. With Python in the key, a result shipped from 3.14 would be unreachable on 3.12.

**What the mode shows**
- A quiet **provenance line** beside the Run status whenever `computed_with` differs from the running environment, for example "Computed when this bundle was made: Python 3.14.0, Windows AMD64, 2026-10-26". It is not a warning.
- An **app-library** mismatch (any of `APP_LIBRARIES`) gets the Workbench's banner style instead, ending "Clear app cache and Run to recompute here". In a bundle this cannot happen, because the lock is shared.
- No automatic spot-check re-runs pairs on open. Apply's live comparison checks what researchers act on.

**"Clear app cache"** deletes shipped results like any other entry, since they live in the same layout with one load path. The clear message's count includes them. A later Run recomputes locally, and the provenance line then disappears. The User Guide notes that clearing replaces the bundle's results with this computer's. A separate read-only store was rejected: it would need two lookup paths for reproducible data.

**Loading panel for every in-app job** (Run, one dataset or all, and "Validate this pair"; raised by the researcher)
- **Form:** while nothing is computed for the shown dataset, the panel fills the main column. Once cells arrive it shrinks to a card at the top of the main column, replacing the "No selection yet" card, with the heatmap filling in below as ticket 10 decided. It is not modal: Cancel stays, and the user can switch datasets, inspect finished cells or leave the mode.
- **Explanation** (a fixed template):
  - what is being computed, for example "Searching 153 Threshold Pairs × 56 resolutions × 10 seeds for each dataset, then checking the chosen pair against 100 shuffled networks and 100 subsamples";
  - why it is computing now: "No results for these settings on this computer yet", "The app cache was cleared" or "Custom settings";
  - where it is: dataset k of 5, phase, units ("grid 87 of 153 pairs");
  - that it is a one-off: results are cached, Cancel keeps finished pairs and Continue resumes, and validation restarts (cancelling it loses at most ~20 s);
  - a link to the User Guide's method section.
- **ETA:**
  - each task is weighted by its graph's edge count, which the parent knows before dispatch. A validation replicate is weighted by its pair's edges;
  - ETA = elapsed × remaining weight ÷ finished weight, over the whole job (all datasets, both phases);
  - "estimating…" shows until 5% of the weight or 10 s has passed, then "about N min left" ("less than a minute" under one), plus the elapsed time;
  - tasks are dispatched **heaviest first**, which also shortens wall time. Determinism is unaffected, because results are sorted before use.
- `steamstudy bundle` logs the same ETA, one line per Build, dataset and phase ("Build …, puzzle: grid 87 of 153 pairs, about 1 min left").

**Release checklist** (`docs/releasing-an-app-bundle.md`; the spec's issue owns the edit, since the file is still uncommitted in the researcher's tree)
- Step 4 says making a bundle now runs Parameter Selection for every carried Build (~3 min each on 12 workers), what the stale-cache warning means, and when `--skip-parameter-selection` is acceptable (never for a release).
- Step 5 checks that the mode opens with finished results, with no Run needed, and that the provenance line names the maker's machine.

**Amends**
- [Modules, caching and parallelism](08-modules-caching-parallelism.md):
  - the job's orchestration moves into `app/ps_run.py`;
  - manifests and validation files gain `computed_with`;
  - progress records gain `weight_done` and `weight_total` for the ETA;
  - tasks are dispatched heaviest first.
- [Parameter Selection mode prototype](10-parameter-selection-mode-prototype.md):
  - the loading panel replaces the main column's "No results for these settings yet" and "No selection yet" texts while a job runs;
  - the provenance line joins the Run section's cache line.

**Handed on**
- To [Exports and documentation](11-exports-and-documentation.md):
  - the settings JSON records `computed_with`;
  - the User Guide says shipped results were computed when the bundle was made, that "Clear app cache" replaces them with this computer's, and why a recomputation might differ (another Python or OS, practically never);
  - the loading panel's link needs a method section to point at.
- To [Editable fixed settings](14-editable-fixed-settings.md): a non-default fixed setting is never shipped, so it always computes locally, and the loading panel says "Custom settings".
