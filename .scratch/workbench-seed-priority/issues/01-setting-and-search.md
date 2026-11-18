# 01: The setting and the search

**What to build:** the `workbench_seed_priority` Build setting, from `network.toml` to the grid task, and the two search orders. A `closest_gamma` Build must give byte-identical results and cache keys to today's.

**Blocked by:** none

**Status:** ready-for-agent

Spec: [Workbench Seed Priority spec](../spec.md): "Where it lives", "The search", "Cache key", "Tests". Facts: [measurement](../prototypes/01-seed-priority-effect/results.md).

- [ ] `config/network.toml` `[parameter_selection]` has `workbench_seed_priority = "closest_gamma"` with a comment naming both values.
- [ ] `ParameterSelectionDefaults` reads it. A missing key gives `closest_gamma`. Any other value raises `ConfigError` naming `closest_gamma` and `main_seed`, and that error shows on the draft's Network defaults step.
- [ ] `SelectionSettings.workbench_seed_priority`, set by `load_selection_settings`. It is not part of Parameter Selection mode's staged settings (it is untouched by "Use these settings", "Reset to defaults" and "Copy from Workbench").
- [ ] `settings_key()` includes `"workbench_seed_priority": "main_seed"` only for `main_seed`. `METHOD_VERSION` is unchanged.
- [ ] `GraphTask` carries the priority. `_selected_metrics` passes it to `workbench_setting`.
- [ ] A pure function yields the attempts in order for a priority. `closest_gamma`: for each candidate γ, the main seed then the scan seeds. `main_seed`: the main seed at every γ, then for each γ again from the nearest, the scan seeds, without the main seed. `workbench_setting` takes the priority (default `closest_gamma`) and stops at the first exact match. The fallback is unchanged.
- [ ] Tests (`tests/test_selection.py`):
  - With a fake `reproduces`: scan seed 2 matches at the nearest γ and the main seed 0.03 away. `closest_gamma` gives (nearest, scan seed 2, `scan`); `main_seed` gives (γ 0.03 away, main seed, `main`).
  - Tie-break: two equidistant candidates. The lower γ is tried first in both orders.
  - `main_seed` with no main-seed match: the scan seeds start again at the nearest γ.
  - No match: the same fallback, flag and ARI in both orders.
  - On an existing small-graph fixture, `closest_gamma` equals today's `WorkbenchSetting`.
  - `settings_key()` is byte-identical with the default and differs with `main_seed`.
  - Config: missing key, valid values and an unknown value.

## Comments
