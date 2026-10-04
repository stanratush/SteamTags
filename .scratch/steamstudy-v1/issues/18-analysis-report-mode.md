# 18: Analysis Report mode

**What to build:** A control switches the app into Analysis Report mode: one scrolling page of numbered sections over the same Network State as the Workbench. The sections are 1 Dataset · 2 Filters (every left-out tag with its reasons) · 3 Network + inspector · 4 Cluster quality (Q vs null and the seed-noise line) · 5 Removal sensitivity · 6 All nodes/edges · 7 Export. Switching modes keeps every setting, removed tag and result.

**Blocked by:** 16, 17

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "App" (Two modes over one state).

- [ ] A mode control switches between the Workbench and Analysis Report mode. Both share one state: dataset, filters, removed tags, weight, algorithm, γ, seed and results.
- [ ] The seven numbered sections have the contents listed in the spec. Section 5 shows the same table and noise line as the Workbench tab, with the noise line referring back to section 4.
- [ ] Section 3's graph works on the same renderer instance across mode flips: hidden while in the other mode, it shows the current state when it reappears, with no re-mount error.
- [ ] Section 7 offers "Export this state", producing the same zip as the Workbench.
- [ ] The clustering controls (weight, algorithm, γ, seed) are available in both modes.
