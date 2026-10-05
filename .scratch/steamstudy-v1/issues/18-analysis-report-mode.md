# 18: Analysis Report mode

**What to build:** A control switches the app into Analysis Report mode: one scrolling page of numbered sections over the same Network State as the Workbench. The sections are 1 Dataset · 2 Filters (every left-out tag with its reasons) · 3 Network + inspector · 4 Cluster quality (Q vs null and the seed-noise line) · 5 Removal sensitivity · 6 All nodes/edges · 7 Export. Switching modes keeps every setting, removed tag and result.

**Blocked by:** 16, 17

**Status:** done

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Two modes over one state).

- [x] A mode control switches between the Workbench and Analysis Report mode. Both share one state: dataset, filters, removed tags, weight, algorithm, γ, seed and results.
- [x] The seven numbered sections have the contents listed in the spec. Section 5 shows the same table and noise line as the Workbench tab, with the noise line referring back to section 4.
- [x] Section 3's graph works on the same renderer instance across mode flips: hidden while in the other mode, it shows the current state when it reappears, with no re-mount error.
- [x] Section 7 offers "Export this state", producing the same zip as the Workbench.
- [x] The clustering controls (weight, algorithm, γ, seed) are available in both modes.

## Comments

- 2026-10-04 (agent): App implemented in steamstudy.app (loader, renderer boundary, layout, callbacks, export/open, rs_cache, server). Tested via the export zip (app equals Build, round trip, refusals), the served page (no external URLs) and the callbacks as functions; also exercised live in the browser on a demo Build (node/edge/cluster inspectors, remove, layout switch, Re-layout, background Removal Sensitivity run with stale/current display, Analysis Report mode on the same renderer instance, floating inspector). Open Network State also re-exports and can compare table hashes (recorded_table_hashes_match).
- 2026-10-05 (agent, audit): Audit: every criterion checked against the code and tests; all met.
