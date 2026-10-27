# 26: Parameter Selection mode: Run, jobs, loading panel and dataset strip

**What to build:** the third app mode with its three-pane skeleton. The Controls column gets a working Run section (background jobs over `ps_run`, per-dataset progress, Cancel and Continue, cache and provenance lines). The main column gets the loading panel with its ETA and the dataset strip. The heatmap area and the Inspector are placeholders filled by issues 27 and 28.

**Blocked by:** 24, 25

**Status:** ready-for-agent

Spec: [Automatic Parameter Selection spec](../spec.md): "The Parameter Selection mode" (layout, Controls column item 1, Main column item 1, States), "Jobs, progress and ETA". Prototype: [variant A](../prototypes/10-parameter-selection-mode/README.md).

- [ ] The mode control reads "Workbench | Analysis Report mode | Parameter Selection". `block_styles` / `root_class` and `app.css` handle the new mode. The three panes follow the Workbench's conventions, including the pill bar and floating Inspector at medium and narrow widths. The mode's components live in `app/ps_view.py`.
- [ ] The mode opens on the default Selection Settings and Pair Constraints and shows whatever the cache holds for the loaded Build.
- [ ] **Run section:**
  - "Run all datasets", "Run ‹dataset›" and Cancel, as Dash background callbacks wrapping `ps_run.run` with one `multiprocess.Pool` (`[parameter_selection] workers`, 0 = cpu − 1) and `set_progress`;
  - one row per dataset with phase and progress bar ("grid 87 of 153 pairs", "validation 40 of 200 replicates", "grid done, not validated", "not run");
  - "Continue (k of 153 pairs)" after a cancel;
  - the cache line, and the provenance line when `computed_with` differs from the running environment (app-library mismatch: the Workbench banner style, ending "Clear app cache and Run to recompute here").
- [ ] Jobs exclude each other within the mode and may run beside Removal Sensitivity. The Run buttons are disabled while a mode job runs.
- [ ] **Loading panel** (`selection_text` template): it fills the main column while nothing of the shown dataset is computed, then becomes a card at the top. It shows what is computed (actual scan-length range when known), why now, where it is (dataset k of 5, phase, units), the one-off note, the ETA and elapsed time, and a link to "How Automatic Parameter Selection works". It is not modal.
- [ ] States: "No results for these settings yet" (pointing to Run); "No selection yet. k of 153 pairs are computed; the selection needs the whole grid."
- [ ] **Dataset strip:**
  - five buttons ("★ 14·2 NA 0.98", "no qualifying pair", "not run", "grid k of 153") with the "custom" marker and its tooltip;
  - a click switches the dataset and resets the inspected pair to its ★ pair;
  - help `selection.dataset_strip`.
- [ ] Run's `?` uses `selection.run`.
- [ ] Tests (`tests/test_app.py` style, `dash_http` helpers):
  - The mode renders on a Build with an empty cache and with a pre-filled cache (fixture written by `ps_run` with a small grid range).
  - The Run job's callback, driven with a serial `map_fn`, updates rows and fills the cache.
  - Cancel then Continue.
  - The strip shows each status. A click switches the dataset.
  - The provenance line appears when `computed_with` is patched to another Python, and the banner when an app library differs.
