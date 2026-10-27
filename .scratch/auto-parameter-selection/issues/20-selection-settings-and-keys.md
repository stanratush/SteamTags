# 20: Selection Settings, configuration, keys and seeds

**What to build:** `SelectionSettings` with its three keys and two labels, the `[parameter_selection]` config table, `Constraints` with its defaults, the three new seed streams, and `pair_networks`, which builds every pair's network and graph hash for one dataset.

**Blocked by:** none

**Status:** done

Spec: [Automatic Parameter Selection spec](../spec.md): "Selection Settings, configuration and keys", "Seeds", "Networks", "Choosing the pair" (constraint table and allowed values).

- [x] `config/network.toml` gains the `[parameter_selection]` table exactly as in the spec, with comments. `steamstudy.config` loads and validates it: ranges, 0 = off / automatic, and the maximum Multi-Tag Clusters ≥ the minimum when on. The existing top-level keys are untouched.
- [x] `steamstudy.network.selection` starts with:
  - a frozen `SelectionSettings`;
  - `load_selection_settings(config, build_id)` for the defaults (Lift, Leiden, Minimum Months 0, the network's hidden-tag defaults, main seed, `null_replicates`, `noise_seeds`);
  - `for_dataset(dataset, context) -> Settings` (resolves the defining tag);
  - `settings_key()`, `grid_key(dataset)` and `validation_key(dataset, g, s)` as canonical JSON with hashes, through `model.canonical_key_json`;
  - `METHOD_VERSION = "parameter-selection-1"`.
- [x] Key contents follow the spec's table. Only the γ **step** enters, never the range. Pair Constraints, tolerance, workers and versions never enter.
- [x] `settings_label(settings, defaults)` returns "Default settings" or "Custom settings: …" (each changed editable value next to its default; removed tags named). `constraints_label(constraints, defaults)` does the same for constraints. Both come with a structured form for the exports.
- [x] `Constraints` (frozen): the five Pair Constraints and the tolerance, with defaults from config.
- [x] `selection_seeds(main, settings) -> (scan, null, subsample)`: streams 3, 4 and 5 through `derive_seeds`, with cumulative exclusion of all lower streams (1 = `replicate_seeds`, 2 = `noise_seeds`).
- [x] `pair_networks(games, settings, context)` yields, for every grid pair, its network (`build_network` with the pair's `Settings`) and graph hash (sorted nodes and sorted (u, v, shared count, weight)). Removed tags are absent.
- [x] Tests:
  - Keys: the same settings give the same hashes; changing any keyed field changes `grid_key`; changing R or S changes only `validation_key`; changing a constraint changes no key; `grid_key` differs per dataset; `settings_key` doesn't.
  - Labels: defaults; one changed value; removed tags named.
  - Seeds: the three lists are disjoint from each other and from streams 1–2, and stable across calls (golden values for one main seed).
  - `pair_networks` on the test Build: 153 pairs; the (g+1, s) node set ⊆ the (g, s) node set; s-neighbours share node sets; equal hashes for equal graphs.
  - Config: the shipped table loads; invalid values raise clear errors.

## Comments

- 2026-10-27, implementation: Implemented in `config.py` (`[parameter_selection]`, optional in old Builds' `build.json`, defaulting to the shipped table) and `network/selection.py`. `load_selection_settings(network, genre_tag_ids, build_id)` and `pair_networks(games, settings, dataset, context)` take the dataset and genre ids explicitly. Tests in `tests/test_config.py` and `tests/test_selection.py`.
