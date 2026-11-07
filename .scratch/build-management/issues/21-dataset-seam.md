# 21: The dataset seam: `read_dataset` and the Steam adapter

**What to build:** one reader, `read_dataset(build, key) -> Dataset`, used by every consumer (the app's `BuildContext`, the network, Parameter Selection, validation). The Steam adapter is today's code. The Tag Depth cut is applied once, the filter field is generic, and the inspector marks tags that aren't counted. No Steam number, `state_id` or cache key moves.

**Blocked by:** 20

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "The dataset seam", "Datasets, List Size and Tag Depth" (files keep full lists). ADR 0005. Decision ticket: [generic dataset contract](04-generic-dataset-contract.md). Findings: [research 01](../research/01-steam-assumptions.md) (P1–P10, N1–N9, "What would change a Steam result").

- [ ] A Dash-free module (e.g. `steamstudy/dataset.py`) with the `Dataset` and item types and `read_dataset`. It picks the adapter by `build.json` `source` (absent = Steam). The import adapter raises `NotImplementedError` until issue 26.
- [ ] The Steam adapter reads `top100_<key>.csv` with today's strict header, `months_observed` as the filter value, the defining tag and Genre Tags from config, and `tag_depth` from `build.json` (absent = 20).
- [ ] Each item keeps its full tag list for display and a counted list cut by issue 20's helper. The network sees only the counted list.
- [ ] `BuildContext.rows/games/context`, every `games_from_rows` caller, `ps_run`, `validation` and the bundle's Parameter Selection pass go through `read_dataset`.
- [ ] The filter slider takes its label and range from the `Dataset` (Steam: "Minimum months", 0–60, unchanged) in the Workbench and in Parameter Selection. With no filter field it is hidden and every item is kept. The state key keeps `min_months`.
- [ ] Defining tag and Genre Tags are optional: with neither, nothing is hidden by default and their toggles are not shown.
- [ ] The inspector table marks tags beyond Tag Depth "not counted (beyond tags per game)", and reads "ID" instead of "AppID" for Import Builds (both bg entries).
- [ ] `app/loader.py` builds its config from the Build's own file set, so the eight-file demand and the Steam Charts stub apply only to Steam Builds.
- [ ] Tests:
  - On the test Build and the full Build (the `test_selection_real_build` pattern), every `state_id`, Network State export and Parameter Selection cache key is unchanged.
  - A Build with `tag_depth = 10` gives networks that ignore tags beyond the 10th, and the inspector marks them.
  - `games_from_rows` has no caller outside the Steam adapter.

## Comments
