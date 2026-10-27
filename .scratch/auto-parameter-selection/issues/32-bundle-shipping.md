# 32: Shipping results in an App Bundle

**What to build:** `steamstudy bundle` recomputes Parameter Selection for every carried Build into the staging Build's app cache and compares it with the maker's cache. It records what shipped in `bundle.json` and offers `--skip-parameter-selection`. This issue also measures the full Run's time, for the Running Guide.

**Blocked by:** 24

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Shipping in an App Bundle", "Facts this spec rests on" (time).

- [x] After copying each Build (still without `app_cache`), `make_bundle` calls `ps_run.run` with the shipped default `SelectionSettings`, all datasets, a `multiprocess.Pool` of `[parameter_selection] workers` and the staging cache root. It writes exactly the default grids and the default-constraint validations.
- [x] Where the maker's cache has the same keys, compare grid manifests, graph files and validation files with timings and `computed_with` aside. On a difference, log a warning that the maker's cache is stale and a method version probably needed a bump. Ship the fresh result either way, and never modify the maker's cache.
- [x] Log one ETA line per Build, dataset and phase ("Build …, puzzle: grid 87 of 153 pairs, about 1 min left").
- [x] `--skip-parameter-selection` on the CLI and in `make_bundle`. `bundle.json` gains `parameter_selection`: per Build, the shipped grid and validation key hashes, or `"skipped"`.
- [x] The acceptance test (`tests/test_bundle_acceptance.py`) uses `--skip-parameter-selection` unless it is explicitly asked to run the full path.
- [x] **Measure** a full default Run on the current full Build on 12 workers (and the worker-time total as the serial figure). Record both in this issue's Comments for [Running Guide and release checklist](33-running-guide-and-release-checklist.md).
- [x] Tests:
  - `make_bundle` on the test Build with a small grid-range override writes the cache into the staging Build and records the hashes in `bundle.json`.
  - A seeded stale maker cache logs the warning and isn't shipped.
  - `--skip-parameter-selection` writes `"skipped"` and no cache.
  - In an extracted test bundle, the mode opens on the shipped results with the provenance line when `computed_with` is patched.

## Comments

- 2026-10-27, implementation: Implemented in `bundle/make.py` (`ship_parameter_selection`, `stale_files`, `--skip-parameter-selection`); the acceptance test skips Parameter Selection unless `STEAMSTUDY_BUNDLE_PARAMETER_SELECTION` is set.

**Measured (for [Running Guide and release checklist](33-running-guide-and-release-checklist.md)):** a full default Run (`ps_run.run`, all five datasets, grids then the default-constraint validations) on Build `20261008T221504Z-7a23ae9f`, 12 workers, into a scratch cache: **513 s wall** (grids 298 s, validations 208 s; rpg's validation alone 114 s). Grid worker time totals **2,920 s** (sum of the graph files' `seconds`). Validation replicates record no timing, so the serial figure for validation is only bounded: at most 12 × 208 s ≈ 2,500 s, which puts a serial full Run at under about 1.5 hours. The chosen pairs equal the spec's five.
