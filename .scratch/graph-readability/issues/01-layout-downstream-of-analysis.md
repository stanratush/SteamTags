# 01: Layout downstream of analysis

**What to build:** layout becomes a separate step after analysis, so no coordinate can reach a metric. Nothing changes visibly yet; the current layout keeps running, just behind the new seam.

**Blocked by:** none

**Status:** done

Spec: [Graph readability spec](../spec.md): "Analysis and layout are separate (ADR 0002)". ADR: [0002](../../../docs/adr/0002-layout-is-downstream-of-analysis.md).

- [x] `compute_state` no longer computes positions or sizes. `NetworkState.positions` and `NetworkState.sizes` go away, along with the `with_positions` flag.
- [x] A new `layout_state(state, canvas) -> positions, sizes, regions` takes a finished `NetworkState` and only reads it. It covers the Global positions and the Cluster-separated positions and regions. `canvas` is the reference canvas (1440 × 900 Workbench graph area) unless the app passes its own.
- [x] Every caller moves to the new step:
  - the app's `recompute` / `render_graph` / `do_relayout`;
  - `export_zip`;
  - the Build's `network_stage` report tables;
  - `state_tables`, which takes positions as input and never computes them.
- [x] `recorded_table_hashes_match` compares every column except `x_global`, `y_global`, `x_cluster_separated` and `y_cluster_separated`.
- [x] Tests:
  - **Invariance:** for every dataset of the test Build, export the state under two very different layout settings (for example default gravity vs. 10× gravity, a different reference canvas, the clamp off; until issue 02 lands, vary the seed of the layout only and the canvas). Assert that `state_id` and every export file are byte-identical except the four coordinate columns, including `removal_sensitivity.csv` for a few tags.
  - An import check: no module under `network/` except `layout.py` imports `layout`, and `layout.py` is never imported by `metrics`, `cluster`, `stability`, `sensitivity` or `sweep`.
  - The existing layout tests pass through `layout_state`.

## Comments

- 2026-10-07: Done. `layout_state(state, canvas, *, positions=None) -> Layout(positions, sizes, separated, regions)` in `network/layout.py`; `REFERENCE_CANVAS = Canvas(1116, 678)` (the Tables and Inspector closed, see the spec's amendment). `state_tables(state, layout=None)` reads only `layout.positions` / `layout.separated` through a small Protocol, so `tables.py` never imports the layout; without a layout the coordinate columns are empty. `export_zip` takes an optional `layout`. The invariance test (`tests/test_app_export.py::test_layout_settings_change_only_the_coordinates`) varies the canvas only, as this issue allows; issue 02 adds 10× gravity and the clamp off.
