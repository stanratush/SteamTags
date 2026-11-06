# Switching Builds in one app process

Can the Tag Network app switch between Builds without a restart, and at what cost? As of commit `1961b66` (2026-11-05). Versions from `uv.lock`: **Dash 4.4.1** (`uv.lock:305`), **diskcache 5.6.3** (`uv.lock:349`), Flask 3.1.3, Werkzeug 3.1.9, multiprocess 0.70.19, psutil 7.2.2. Every Dash, diskcache, Flask, Werkzeug and multiprocess claim below comes from the installed source in `.venv/Lib/site-packages/` (paths below are relative to it). The dash.plotly.com pages were not fetched in this session. Repo paths are relative to `src/steamstudy/`.

## Short answer

Yes. The callbacks already find the Build per request: every callback takes `State("build-path", "data")` and calls `load_build(build_path)`. The startup-time bindings are few and listed below. The background job store does not need to be per Build: it holds only short-lived job handles, while the real caches (`rs_cache`, `ps_cache`) are already keyed by the Build path on each call. There is also a latent bug today: **Open Network State… already switches the Build in place** when the export belongs to another Build, and it leaves the page half on the old Build (see §3).

## 1. What the app binds at startup

| # | Binding | Where | Per-request today? |
|---|---|---|---|
| 1 | One `BuildContext` loaded once | `app/server.py:29` | no |
| 2 | Job store `<build>/app_cache/jobs`, one `DiskcacheManager` for the app | `app/server.py:30-32`, `app/server.py:34` | no |
| 3 | Relabel registry filled once from that ctx | `app/server.py:37`; registry `app/relabel.py:26`, first entry wins (`setdefault`, `app/relabel.py:52`) | no |
| 4 | Layout function closes over the startup ctx | `app/server.py:38` | it runs on every page load, but always for the same Build |
| 5 | `build-path` and `builds-root` stores seeded from ctx | `app/layout.py:446-447` | the browser holds them per tab |
| 6 | Build-dependent layout values: dataset options and first dataset, Genre Tag chips, default slider values, defining-tag option, thickness legend | `app/layout.py:235-270`, `:306-327` | no |
| 7 | Header "Build {id}" | `app/layout.py:463` | no |
| 8 | Parameter Selection stores and controls: `ps-active` holds `SelectionSettings` **with `build_id`** (`network/selection.py:46`), `ps-dataset` = first dataset, genre chips, tag names | `app/ps_view.py:987-1031`, `:330-360` | no |
| 9 | Background callbacks bound to the app-level manager | `app/callbacks.py:1248`, `:1304`, `:1310` | no (see §2) |
| 10 | CLI resolves one Build, then runs | `cli.py:136-153`; bundle launcher `bundle/start_tag_network.py:168` | — |

Already Build-safe, with no change needed:
- Every callback re-reads the Build from the `build-path` store (e.g. `app/callbacks.py:97`, `:141`, `:676`, `:862`). `load_build` is a plain function of the folder with no cache (`app/loader.py:1-5`, `:71-83`).
- `rs_cache`, `ps_cache` and `app_cache.clear_all` take `cache_root` on every call (`app/rs_cache.py:43-83`, `app/ps_cache.py:30-187`, `app/app_cache.py:13`). Callers pass `load_build(build_path).app_cache` (`app/callbacks.py:680`, `:689`, `:706`, `:803`).
- The process memos `STATE_TABLES` (`app/callbacks.py:124`) and `LAYOUTS` (`:373`) are keyed by `state_id` or by content hashes, and the Network State key contains `build_id` (`network/model.py:15`, `:85-87`). Entries for two Builds cannot collide.

### The relabel registry (measured)

I ran a probe that builds two real Builds' layouts in one process (`builds/20261005T062558Z-full/20261008T221504Z-7a23ae9f`, then `builds/20261005T062954Z-test/20261026T133927Z-7a23ae9f`). A second probe used a Build cut to 2 datasets and 3 Genre Tags. Results:
- The registry has 210 entries with the **same ids in the same order** in all three cases. The auto ids (`i18n-<n>`) do not depend on the Build's shape, so relabelling never hits the wrong component.
- Three entries close over the Build and are **stale after a switch**. Because `setdefault` keeps the first entry, a language switch after Build B was served sets these from Build A:
  - `brand-build` printed `Build 20261008T221504Z-7a23ae9f` (`app/layout.py:463`)
  - `ps-run-one`: `Run {first dataset label}` (`app/ps_view.py:333`, `:338`)
  - `ps-s-defining`: the defining-tag names (`app/ps_view.py:332`, `:353-354`, `:360`)

The fix is small: either rebuild the registry per page (key it by Build), or make those three messages Build-independent (for example, read the id from a store).

## 2. Background callbacks and the job store (Dash 4.4.1)

- **The manager is chosen when a callback is registered, never per request.** `callback(..., background=True, manager=...)` exists (`dash/_callback.py:82`, docstring `:117-122`) and is stored in the callback's spec (`:206-207`). At call time, Dash takes `cb.get("manager") or self._background_manager` (`dash/dash.py:1630-1632`; also `dash/_callback.py:409-415`). Nothing lets a request pick a manager. One manager per Build would need either one registered callback per Build (different Output ids, so a different layout per Build) or a custom manager that routes by key. **Not worth it.**
- **A shared store is safe across Builds.** The job key is `sha256(args, fn source, triggered)` (`dash/background_callback/managers/__init__.py:72-98`). The args include `build_path`, so two Builds' jobs get different keys. Without `cache_by` (the app sets none, `app/server.py:32`), a result is deleted when it is read (`diskcache_manager.py:187-204`, `:194-195`). The store holds job results, progress and the handle signing secret (`dash/dash.py:974-1035`; `managers/__init__.py:60-70`, `diskcache_manager.py:121-125`), and no Build data. Several managers can coexist: every registered function goes to every manager (`managers/__init__.py:10-14`, `:100-115`).
- **Pitfall: one cancel input, one manager.** Cancel callbacks are collected in a dict keyed by the cancel Input (`dash/dash.py:1756-1765`). `ps-cancel` serves both `ps_job` and `ps_validate_job` (`app/callbacks.py:1305`, `:1311`), so if they ever had different managers, one would lose its cancel.
- **Pitfall: job handles are bound to a page load.** The cache key and pid sent to the browser are HMAC-signed with a per-page-load `end_id` (`dash/_callback.py:476-490`, `_callback_signing.py:9-17`, `:58-68`). After a reload, the new page cannot cancel or collect a job started by the old page. That job runs to completion and writes its rows into its own Build's cache, which is harmless.
- **Pitfall (measured on this machine): a Build holding the open job store cannot be deleted on Windows.** In a scratch copy, `shutil.rmtree` over `<build>/app_cache/jobs` with an open `diskcache.Cache` failed with `PermissionError` WinError 32 on `cache.db`, and worked after `close()`. Closing is not reliable in a running server, because diskcache keeps one SQLite connection per thread and per pid (`diskcache/core.py:442`, `:609-623`) and `close()` closes only the caller's (`core.py:2337-2349`). Flask serves requests on threads (`flask/app.py:655`), and every job is a separate process (`diskcache_manager.py:143-147`). The map's "Delete a Build" therefore argues, independently of switching, for **moving the job store out of the Build folder**: for example `<root>/app_cache/jobs`, or a temp folder per process. Bundles already leave `app_cache/` out (`bundle/make.py:189`).

## 3. In-place switching: how the layout and callbacks can resolve the Build

- **The layout function runs on every page load**, from the `_dash-layout` route (`dash/dash.py:816`, `:912-972`). But the renderer requests that route with **no query string** (`dash-renderer/build/dash_renderer.dev.js:5682`, `:5984`), so the layout function cannot see `?build=` or the page path. It can see cookies, which is how `served_lang()` already works (`app/server.py:23-25`). It can also see the `Referer` header, but relying on that is fragile and undocumented.
- **Dash Pages can deliver the path and query string per tab.** With `use_pages`, a hidden router callback calls the page layout with `**path_variables, **query_parameters` (`dash/dash.py:2706-2750`; container `:140-156`). A page template like `/build/<build_id>` would make the Build a per-tab choice. Cost: the layout becomes a callback output, which is the multi-page model, plus Pages' registry and validation rules.
- **Callbacks already resolve the Build per request** from the `build-path` store, which is per tab. Today the browser sends an absolute filesystem path, and `load_build` opens whatever it is given. Any switching design should send a Build id instead and resolve it under the builds root (`builds.py:15-31`, or `export.find_build`, `app/export.py:185-199`).
- **Existing half-switch (bug, found by reading, not run in the app).** `do_open` finds the export's Build among every Build under `builds-root` (`app/export.py:202-213`), then writes `build-path` and the control values (`app/callbacks.py:770-796`, registered `:1267-1272`). It does not update:
  - the dataset and Genre Tag options (`app/layout.py:247`, `:261`)
  - the header Build id (`:463`)
  - the Parameter Selection stores: `ps-active` keeps the **startup Build's `build_id`** (`app/ps_view.py:1024`), and `_ps_context` uses it as is (`app/callbacks.py:861-865`), so Parameter Selection keys after such an Open name the wrong Build.

  This is where the design's switching choice will land in any case.
- **Swapping the whole body from a callback** (without a reload) means re-mounting every component. Their non-`prevent_initial_call` callbacks fire again, and `dcc.Store` data resets. The app already runs with `suppress_callback_exceptions=True` (`app/server.py:35`), so ids that appear later raise no errors. The flip side is that misspelt ids are not reported either. With suppression off, Dash would call the layout function once at assignment to validate it (`dash/dash.py:920-930`), and again on the first request (`:1724`).
- **Client-side state.** No `dcc.Store` uses `storage_type` or `persistence`, so a reload resets every store. Browser-side state: two cookies, `steamstudy_lang` (`app/assets/workbench.js:328`) and the Edge Appearance cookie (`app/assets/graph.js:465-473`), both `path=/`, plus one sessionStorage flag (`graph.js:596`, `:704`). None is Build-specific. A cookie that chose the Build would be **shared by every tab**, and by every app on `127.0.0.1` whatever the port, since cookies do not separate ports (RFC 6265 §8.5). Two tabs on different Builds would fight over it at their next reload. Their callbacks would still be correct, because those read the per-tab `build-path`.

## 4. The lighter routes

- **Restart the process.** A Flask app refuses new routes or callbacks after its first request (`flask/sansio/app.py:413-423`), so a Build created later cannot be added to a running app as a new app. A restart needs a parent process. Werkzeug's reloader shows the pattern: the child exits with code 3 and the parent starts it again (`werkzeug/_reloader.py:266-278`). The bundle launcher is already such a parent (`subprocess.call`, `bundle/start_tag_network.py:168`); the repository CLI is not (`cli.py:150-153`). Pitfalls:
  - **A plain `sys.exit` waits for running jobs.** Job processes are not daemons (`multiprocess/process.py:85`, `diskcache_manager.py:143`), and at exit multiprocess joins every child that is not a daemon (`multiprocess/util.py:421-428`). Jobs have to be terminated first, for example with the manager's `terminate_job` (psutil, `diskcache_manager.py:63-91`).
  - The child must keep the same port so the open tab reconnects. The launcher picks "8050 or the next free one", so the port has to be passed on.
  - The page must reload and must wait until the new server answers.
  - Every in-memory memo is lost. That is harmless, because they are pure (`app/callbacks.py:121-122`, `:372`).
- **Serve each Build under a URL prefix.** Dash supports `url_base_pathname` / `requests_pathname_prefix` / `routes_pathname_prefix` (`dash/dash.py:309-323`), and blueprint names follow the prefix (`:771`), so several Dash apps can share one server. Werkzeug's `DispatcherMiddleware` reads its `mounts` dict on every request (`werkzeug/middleware/dispatcher.py:44-76`), so an app for a new Build could be added to that dict at runtime. That relies on the source, not on a documented API. Costs:
  - one full Dash app per Build, each with its own callback map and layout build
  - `RELABEL` is module-level and shared by every app in the process, so the stale closures of §1 apply across apps
  - one job store per app, or one shared store
  - `app.run` would be replaced by `werkzeug.serving.run_simple` on the middleware
  - assets and cookies still share `path=/` unless set per prefix

## Options (for the grilling ticket)

| Option | What changes | Cost | Main risks |
|---|---|---|---|
| **A. Cookie plus reload** (per browser) | Layout resolves the Build from a cookie, like the language. A Build menu sets the cookie and reloads. `build-path` is seeded from it. | Low. Server rows 1, 3-4 and 7 of §1; fix the 3 stale registry entries; move the job store out of the Build; send a Build id instead of a path. | All tabs share one Build at reload. Cookies are shared across ports on 127.0.0.1. |
| **B. Build in the URL** (Dash Pages `/build/<id>`, per tab) | Layout becomes a page callback with `build_id`. Links and bookmarks name the Build. | Medium. Same as A, plus moving to Pages. | Component re-mounts fire initial callbacks. Pages validation rules apply. |
| **C. In-place swap by callback** (no reload) | A "switch Build" callback writes `build-path` and every Build-dependent prop: options, PS stores, header. Fixing `do_open` (§3) needs this anyway. | Medium, and grows with every new Build-dependent prop. | Easy to miss a prop, as `do_open` shows today. |
| **D. Restart via a supervisor** | The parent restarts the app with `--build`. The tab polls, then reloads. | Low in the app, medium in the CLI (it needs a parent loop). The bundle launcher already is one. | Jobs must be terminated before exit. Port handover. Slow (imports and Dash setup on each switch). |
| **E. URL prefix per Build** (`DispatcherMiddleware`) | One Dash app per Build, mounted at `/<build_id>/`. | High: N apps, shared module globals, custom server run. | Undocumented runtime mounting. Registry shared across apps. Memory. |

Shared by every option: move the job store out of `<build>/app_cache/` (Delete on Windows, §2) and resolve the Build by id instead of a client-sent path. Option C's prop list is also the fix for today's cross-Build Open, whatever is chosen.

*Probe scripts (scratch, not in the repo):* `C:\Users\Lenovo\AppData\Local\Temp\claude\666d07de91457ebd\5f5f42ec-3d7b-4acd-9339-7b68e8158029\scratchpad\03\relabel_probe.py`, `relabel_shape.py`, `rmtree_probe.py`.
