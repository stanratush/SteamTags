# 24: Cache, Run driver and Clear app cache

**What to build:** the persistent Parameter Selection cache (`app/ps_cache.py`), the Dash-free Run and Validate drivers (`app/ps_run.py`) with weighted progress, ETA and `computed_with`, and one shared `clear_all` behind "Clear app cache" and `steamstudy app --clear-cache`.

**Blocked by:** 22, 23

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "Cache", "Jobs, progress and ETA", "Modules" (app side), "Which pair, and when".

- [ ] `ps_cache.py`, with the layout under `<build>/app_cache/parameter_selection/`:
  - `grids/<grid_key_hash>/manifest.json` and `graphs/<graph_hash>.json`;
  - `validation/<validation_key_hash>.json`;
  - atomic writes (tmp + replace);
  - readers for a grid's state (complete, partial k of 153, or absent) and a pair's validation;
  - listing by settings key;
  - `clear(root) -> count`.
- [ ] Manifest: the grid key, (g, s) → hash, the total and `computed_with`. Once the grid is complete it also holds the neighbour links and NA. Graph files hold the `GraphResult`. Validation files hold the summary plus every replicate record, with `computed_with`. `computed_with` = `software_versions()`, `platform.system()`, `platform.machine()` and UTC.
- [ ] `ps_run.run(builds_root_or_build, settings, datasets, *, map_fn, on_progress, should_stop, cache_root)`:
  - phase 1 runs every requested dataset's grid, resuming from graph files on disk, then NA and `choose` under the **default** constraints;
  - phase 2 validates each chosen pair, skipping cached ones;
  - "All datasets" runs all grids before any validation;
  - it emits one progress record per task with `weight_done`, `weight_total` and `elapsed`, over the whole job;
  - it exposes `eta_text(record)` ("estimating…" until 5% of the weight or 10 s; "about N min left"; "less than a minute").
- [ ] `ps_run.validate_pair(build, settings, dataset, g, s, ...)` needs a complete cached grid. It is all-or-nothing, and a cancel writes nothing.
- [ ] Only the parent writes. The drivers never import Dash.
- [ ] `app/app_cache.py`: `clear_all(root) -> {"removal_sensitivity": n, "parameter_selection": m}`. The button callback and the `--clear-cache` CLI path use it, and their messages report both counts. Correct `rs_cache.py`'s "only persistent cache" docstring.
- [ ] Tests:
  - A run on the test Build (two datasets, a small grid range via settings, small R and S, serial `map`) writes the layout above. A second run computes nothing.
  - Cancelling mid-grid keeps finished graph files, and a resumed run computes only the rest and gives byte-identical files to an uninterrupted run.
  - A cancelled validation writes no file.
  - Progress records are monotonic, end at `weight_done == weight_total`, and `eta_text` follows its thresholds.
  - The byte-identical cache across a serial run and a pool of 2 (timings and `computed_with` aside).
  - `clear_all` removes both kinds and reports counts. The CLI flag prints them.
