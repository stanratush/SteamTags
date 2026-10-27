# 32: Shipping results in an App Bundle

**What to build:** `steamstudy bundle` recomputes Parameter Selection for every carried Build into the staging Build's app cache and compares it with the maker's cache. It records what shipped in `bundle.json` and offers `--skip-parameter-selection`. This issue also measures the full Run's time, for the Running Guide.

**Blocked by:** 24

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "Shipping in an App Bundle", "Facts this spec rests on" (time).

- [ ] After copying each Build (still without `app_cache`), `make_bundle` calls `ps_run.run` with the shipped default `SelectionSettings`, all datasets, a `multiprocess.Pool` of `[parameter_selection] workers` and the staging cache root. It writes exactly the default grids and the default-constraint validations.
- [ ] Where the maker's cache has the same keys, compare grid manifests, graph files and validation files with timings and `computed_with` aside. On a difference, log a warning that the maker's cache is stale and a method version probably needed a bump. Ship the fresh result either way, and never modify the maker's cache.
- [ ] Log one ETA line per Build, dataset and phase ("Build …, puzzle: grid 87 of 153 pairs, about 1 min left").
- [ ] `--skip-parameter-selection` on the CLI and in `make_bundle`. `bundle.json` gains `parameter_selection`: per Build, the shipped grid and validation key hashes, or `"skipped"`.
- [ ] The acceptance test (`tests/test_bundle_acceptance.py`) uses `--skip-parameter-selection` unless it is explicitly asked to run the full path.
- [ ] **Measure** a full default Run on the current full Build on 12 workers (and the worker-time total as the serial figure). Record both in this issue's Comments for [Running Guide and release checklist](33-running-guide-and-release-checklist.md).
- [ ] Tests:
  - `make_bundle` on the test Build with a small grid-range override writes the cache into the staging Build and records the hashes in `bundle.json`.
  - A seeded stale maker cache logs the warning and isn't shipped.
  - `--skip-parameter-selection` writes `"skipped"` and no cache.
  - In an extracted test bundle, the mode opens on the shipped results with the provenance line when `computed_with` is patched.
