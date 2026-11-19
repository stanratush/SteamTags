# 02: Cluster Comparison: shared settings in a collapsible drawer

**What to build:** the Cluster Comparison top block moves into the left sidebar, and the sidebar collapses to a rail.

**Blocked by:** 01 (reuses its collapse button and rail)

**Status:** done

Spec: [UI Declutter spec](../spec.md): "Cluster Comparison layout", "Docs". Code: `src/steamstudy/app/cc_view.py` (`mode_layout`, `shared_row`, `pair_block`), `callbacks.py`, `assets/app.css`, `assets/workbench.js`.

- [x] `cc-head` is gone from the top of the mode. The sidebar starts with a "Shared settings" section (title, help `?`, the shared settings, `comparison_id`), then Datasets, then Dataset pairs.
- [x] The shared-settings fields fit the sidebar width (stacked; the Hidden Genre Tags chips wrap).
- [x] The sidebar has a « collapse button and collapses to a rail on the left edge, reopened from the rail, with the same look and accessibility as 01.
- [x] The drawer is open on the first visit in a browser session and remembers open/closed in sessionStorage for the session. Storage that throws leaves it open.
- [x] Export CSV sits in the pair header row to the right of the Minimum Jaccard controls, and works as today.
- [x] `cc-notice` shows at the top of the main area and is visible with the drawer closed.
- [x] The busy overlay still covers the whole mode.
- [x] Every new string has a bg entry.
- [x] User Guide `02-app-controls.md` (en and bg) Cluster Comparison section matches.
- [x] Tests (`tests/test_cc_app.py`): component ids still present and wired; the shared settings sit inside `cc-sidebar`; `cc-export` sits in the pair block; `cc-notice` sits in `cc-main`.

## Comments

**2026-11-18, implementation.** `cc-head` is gone. The sidebar now starts with a "Shared settings" section, which is a pill at medium and narrow like the other two. The drawer's state is `cc-panels`, a memory `dcc.Store` that is None until the first click (panels.py `STATE` now names a component and a prop). workbench.js `ccPanels` sets `no-controls` on `#cc-body`, asks the link diagram to redraw, and keeps the state in sessionStorage (`steamstudy_cc_drawer`) inside try/catch. Not Dash's session store: its constructor reads `window.sessionStorage` directly, so blocked storage would break it. `cc-notice` is the first child of `cc-main`; `cc-export` sits in `cc-pair-head` after the Minimum Jaccard controls. `#cc-body` now grows to the full height (`flex:1 1 auto`): without the tall sidebar it had stopped at its content.

Checked in the browser at 1440×900: collapse, rail, reopen; the closed state survives a reload; a shared-setting change after a value set by hand shows the notice at the top of the main column with the drawer closed. At 1100 px: three pills (Shared settings, Datasets, Dataset pairs), « last, a horizontal rail when closed, and the Shared settings popover opens. With `Storage.prototype.getItem` and `setItem` made to throw, `ccPanels(null)` gives an open drawer and `ccPanels([])` still closes it.

