# Dash spike re-run on Python 3.14
Type: task
Status: resolved
Assignee: ciberiyc@gmail.com
Blocked by: 18

## Question

Does the Dash stack chosen in [Web stack selection](18-web-stack-selection.md) pass every check of the [Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md) on **Python 3.14.8** (latest stable as of 2026-09-30)? The Dash packages declare support only up to 3.12, and the original spike ran on 3.13.0.

AFK task: install Python 3.14.8 with `uv`, re-run [the spike app](../prototypes/17-dash-cytoscape-spike/app.py) in a fresh environment with the current versions of dash, dash-cytoscape 1.0.2, dash-ag-grid, diskcache, multiprocess, psutil, networkx, numpy and scipy, and repeat the spike's check table: render at ~400 nodes / ~5,000 edges, node and edge clicks reaching Python, a background callback with progress + cancel under Windows spawn, rapid threshold toggling, preset-layout switching without re-mounting, the #229 mount scenario, and offline in production mode (no non-localhost requests). Also do a clean import of igraph and leidenalg (abi3 wheels) to confirm they load on 3.14.

Record the exact versions, any warnings or deprecations, and the per-job startup time. Pass → the 3.14 pin stands. Any failure → fall back to 3.13 and record why.

Settled by [Silhouette space and cluster-quality metrics](10-silhouette-cluster-quality.md):
- `leidenalg` and `python-igraph` are now regular pinned dependencies (the optional Leiden mode), so their clean import on 3.14 is a pass/fail check like the others, not an informational one. Also run one seeded `leidenalg.find_partition(..., RBConfigurationVertexPartition, n_iterations=-1, seed=...)` on the spike graph twice and confirm identical memberships.

## Answer

**Pass: the Python 3.14 pin stands.** Every check from [Dash + dash-cytoscape Windows spike](17-dash-cytoscape-windows-spike.md) passed on Python 3.14.8, and igraph + leidenalg import cleanly and give identical seeded partitions. Run on 2026-10-04 on the researcher's Windows machine, in a fresh `uv` venv, with the spike app unchanged and the same synthetic graph (400 nodes, 4,964 edges, byte-identical `synthetic_graph.json`). Assets: [../prototypes/22-dash-spike-python-314/](../prototypes/22-dash-spike-python-314/) (check scripts, `requirements-py314.txt`, README).

**Versions:** Python 3.14.8 (uv-managed CPython, MSC v.1944, GIL build) on Windows 11 Pro 10.0.26200, installed with uv 0.12.23. dash 4.4.1, dash-cytoscape 1.0.2, dash-ag-grid 35.3.0, diskcache 5.6.3, multiprocess 0.70.19 (`py314` wheel), psutil 7.2.2 (abi3), networkx 3.7, numpy 2.5.3 (cp314), scipy 1.18.1 (cp314), python-igraph/igraph 1.0.0 (abi3), leidenalg 0.12.0 (abi3), Flask 3.1.3, Werkzeug 3.1.9, plotly 7.1.0, pydantic-core 2.46.5 (cp314). Every compiled package installed from a wheel; nothing was built from source. These are the same Dash-stack versions as the 3.13 spike.

| Check | Result | Notes |
|---|---|---|
| Clean import of all packages (incl. igraph, leidenalg) | **Pass** | No DeprecationWarning, PendingDeprecationWarning or FutureWarning at import or in the callbacks (driven through Flask's test client with those as errors). The only output was opt-in `EncodingWarning`s (`-X warn_default_encoding`) from dash/dash-cytoscape/dash-ag-grid/dill opening their own ASCII metadata files without `encoding=`. Harmless. |
| Seeded Leiden reproducibility | **Pass** | `find_partition(g, RBConfigurationVertexPartition, weights="weight", resolution_parameter=1.0, n_iterations=-1, seed=42)` twice: identical memberships (12 clusters, modularity 0.5666). The membership hash was also identical across separate processes and **across 3.13.0 and 3.14.8**. |
| Render ~400 nodes / ~5,000 edges with cluster-centre styling | **Pass** | 400 nodes / 4,964 edges. Forced full redraw: median 42 ms, p95 54 ms (ticket 17: 55 / 77 ms; same browser-side code, so the difference is measurement noise, not Python). |
| Node and edge clicks reach Python | **Pass** | Real mouse clicks: node `t347` and edge `t49–t312` (56 AppIDs) arrived with full data; the AppIDs showed in dash-ag-grid. |
| Background callback with progress + cancel (Windows spawn) | **Pass** | First progress at 4.1 s, 40/40 at 7.5 s, buttons toggled by `running`. Cancel at 20/40 froze progress and restored the buttons. No worker process was left after either the finished or the cancelled job (checked with `Win32_Process`). |
| Rapid threshold toggling | **Pass** | 34 rapid real key steps on the min-games slider; 30 interleaved slider + layout changes at 40 ms; three layout bursts (7, 11, 9 clicks at 25 ms). The final graph always matched the final controls, and an independent Python computation gave the same node, edge and cluster counts (246/1,871/11 and 246/235/60). No JS errors, no dev-tools errors, the same Cytoscape instance throughout. |
| Switch Global / Cluster-separated preset positions without re-mounting | **Pass** | Node `t0` moved (199, −1081) → (1840, 212) → back on one instance. The 11 region nodes appeared (locked, not grabbable) and disappeared. Global positions were identical to first load after many threshold changes. |
| Mount from a callback / hide-show (#229 scenario) | **Pass** | Six real-click remounts of a callback-returned Cytoscape: rendered 400/1,359, no `bb.h` error. Six rapid Workbench/Analysis flips, then min-shared and layout changed while hidden: the graph came back on the same instance at full size, showing the hidden-time state. |
| Offline / no CDN (production mode) | **Pass** | `debug=False`: 28 files, 4.2 MB, all from the local server; dash-cytoscape `.min.js` 484 KB. Nothing requested from any other host. |

**Per-job startup time** (each background job re-imports the app under spawn):
- With bytecode compiled: 3.14.8 = libraries 1.45 s + app module 1.0 s ≈ **2.5 s**. 3.13.0 on the same machine and packages: 1.45 s + 1.05 s ≈ 2.45 s. **No difference.** The ~4 s to first progress in the browser is that plus spawn and diskcache polling, as on 3.13.
- Without bytecode it is **6.4 s on 3.14 vs 5.3 s on 3.13**. The uv-managed CPython ships its stdlib without `.pyc`, and uv doesn't compile site-packages by default. If `.pyc` can't be written (here the shell had `PYTHONDONTWRITEBYTECODE=1`), every spawned job recompiles everything. → The app's install step should compile bytecode (`uv sync --compile-bytecode` / `UV_COMPILE_BYTECODE=1`), and nothing should set `PYTHONDONTWRITEBYTECODE`.

**Other facts surfaced (none are 3.14-specific):**
- **`localhost` vs `127.0.0.1`:** opened via `http://localhost:8050`, every callback took ~270–450 ms even with empty responses. Via `http://127.0.0.1:8050` the same callbacks took 7–9 ms. That's a Windows name-resolution cost (IPv6 first, then a fallback) against a server bound only to IPv4. → The app must open the browser at `http://127.0.0.1:<port>`, never `localhost`. This backs the "listen on `127.0.0.1` only" decision in [Web stack selection](18-web-stack-selection.md).
- **Locale encoding is cp1251** on this machine (`open()` without `encoding=` decoded as cp1251). → Every file read or write in `steamstudy` (CSV, JSON, TOML, raw responses) must pass `encoding="utf-8"` explicitly. Tag and game names are not ASCII-safe. Python 3.14 does not yet default to UTF-8 mode.
- **Initial `fit` is timing-dependent:** on the very first load, `layout={"name": "preset", "fit": True}` left the graph unfitted (47 of 400 nodes in view). After a reload it fitted correctly (zoom 0.21, all 400 in view). This is a front-end race, independent of Python. → The renderer module should re-fit explicitly once the first `elements` arrive (clientside callback calling `cy.fit()`), not rely on the layout's `fit` alone.
- **`-X dev` crashes on this machine:** a bare `python -X dev -c "print('ok')"` crashes at exit (debug-allocator corruption report) on **both** the python.org 3.13.0 and the uv 3.14.8 interpreters, with nothing imported. `PYTHONMALLOC=debug` alone and dev mode without the debug allocator both run fine. Something on this machine trips the debug allocator; it is not a 3.14 issue. Dev mode is unusable here for tests; use `-W default -X faulthandler`.
- `uv python install 3.14.8` reported "Missing expected target directory for Python minor version link" (it could not create the `cpython-3.14` junction in this sandboxed shell). The interpreter itself installed and works, and `uv python find 3.14` resolves it.
- The only browser console warning was again dash-cytoscape's built-in wheel-sensitivity warning. No server-side warnings or errors.
